"""
Neuro Cue — Neural Stimulus Optimizer for SLP
A clinical wrapper around Meta's TRIBE v2 brain encoding model.
Built for speech-language pathology research and education.
"""

import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["PYVISTA_OFF_SCREEN"] = "true"
os.environ["DISPLAY"] = ""
os.environ["VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN"] = "true"

import tempfile
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")

import gradio as gr
import spaces
import subprocess

from input_validation import (
    extension_from_name,
    has_video_extension,
    normalize_timestep_limit,
    resolve_uploaded_video_path,
)

# ── Constants ─────────────────────────────────────────────────────────────────
CACHE_FOLDER = Path("./cache")
CACHE_FOLDER.mkdir(parents=True, exist_ok=True)

# Clinical ROI definitions (Destrieux atlas regions, left hemisphere only)
# Language is left-lateralized in ~95% of right-handed individuals
ROI_DEFINITIONS = {
    "broca": {
        "label": "Broca's Area",
        "function": "Speech production, expressive language, syntactic processing",
        "destrieux_labels": ["G_front_inf-Triangul", "G_front_inf-Opercular"],
    },
    "wernicke": {
        "label": "Wernicke's Area",
        "function": "Language comprehension, semantic processing",
        "destrieux_labels": ["G_temporal_middle", "G_temp_sup-Plan_tempo", "S_temporal_sup"],
    },
    "sma": {
        "label": "Supplementary Motor Area",
        "function": "Speech motor planning, articulation sequencing",
        "destrieux_labels": ["G_front_sup", "G_and_S_paracentral"],
    },
    "angular": {
        "label": "Angular Gyrus",
        "function": "Reading, written language, semantic integration",
        "destrieux_labels": ["G_pariet_inf-Angular"],
    },
}

# ── Singletons (lazy-loaded) ──────────────────────────────────────────────────
_model = None
_roi_masks = None
_mesh_cache = None

MAX_VIDEO_SECONDS = 15.0
# Keep public @gradio/client calls within ZeroGPU's current per-request limit.
ZERO_GPU_DURATION_SECONDS = 120

def _probe_duration(path: str) -> float | None:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, check=True, timeout=15,
        )
        return float(out.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired) as e:
        print(f"⚠️  ffprobe failed on {path}: {e}")
        return None


def trim_video_if_needed(path: str, max_seconds: float = MAX_VIDEO_SECONDS) -> str:
    """If longer than max_seconds, trim and return new path. Otherwise return path unchanged.
    Falls back to original path on any ffmpeg failure."""
    dur = _probe_duration(path)
    if dur is None or dur <= max_seconds:
        if dur is not None:
            print(f"🔵 video {dur:.1f}s ≤ {max_seconds}s — no trim")
        return path

    base, _, ext = path.rpartition(".")
    out_path = f"{base}_trim{int(max_seconds)}s.{ext}" if ext else f"{path}_trim.mp4"
    print(f"🔵 trimming {dur:.1f}s → {max_seconds}s ({out_path})")

    # Stream copy first (fast, no re-encode). Falls back to re-encode if keyframe placement
    # makes -t copy fail or produce something downstream rejects.
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", "0", "-i", path,
             "-t", str(max_seconds), "-c", "copy",
             "-avoid_negative_ts", "make_zero", out_path],
            capture_output=True, check=True, timeout=30,
        )
        return out_path
    except subprocess.CalledProcessError as e:
        print(f"⚠️  stream copy failed: {e.stderr.decode('utf-8', 'replace')[:300]}")

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", path, "-t", str(max_seconds),
             "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
             "-c:a", "aac", out_path],
            capture_output=True, check=True, timeout=120,
        )
        return out_path
    except subprocess.CalledProcessError as e:
        print(f"🔴 re-encode failed: {e.stderr.decode('utf-8', 'replace')[:300]}")
        return path  # give up; downstream will handle or error

def _load_model():
    """Load TRIBE v2 (only inside GPU function due to ZeroGPU)."""
    global _model
    if _model is None:
        from tribev2.demo_utils import TribeModel

        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            from huggingface_hub import login
            login(token=hf_token, add_to_git_credential=False)

        _model = TribeModel.from_pretrained("facebook/tribev2", cache_folder=CACHE_FOLDER)
    return _model


def _load_roi_masks():
    """Load Destrieux atlas and build ROI masks."""
    global _roi_masks
    if _roi_masks is None:
        from nilearn import datasets
        atlas = datasets.fetch_atlas_surf_destrieux()
        print(atlas,"atlas log in load_roi_masks")
        # left hemisphere annotations
        labels = atlas["labels"]
        lh_map = atlas["map_left"]  # vertex → label index
        label_names = [l.decode() if isinstance(l, bytes) else l for l in labels]

        masks = {}
        for roi_key, roi_def in ROI_DEFINITIONS.items():
            indices = []
            for region_name in roi_def["destrieux_labels"]:
                if region_name in label_names:
                    label_idx = label_names.index(region_name)
                    indices.append(np.where(lh_map == label_idx)[0])
            if indices:
                masks[roi_key] = np.concatenate(indices)
            else:
                masks[roi_key] = np.array([], dtype=int)
        _roi_masks = masks
    return _roi_masks


def _load_mesh():
    """Load fsaverage5 'half-inflated' mesh + smoothing adjacency.
    Returns 6-tuple: (coords_L, faces_L, adj_L, coords_R, faces_R, adj_R)."""
    global _mesh_cache
    if _mesh_cache is None:
        import nibabel as nib
        from nilearn import datasets
        fsaverage = datasets.fetch_surf_fsaverage("fsaverage5")

        ALPHA = 0.5
        out = []
        for hemi in ("left", "right"):
            infl_xyz, _ = nib.load(getattr(fsaverage, f"infl_{hemi}")).darrays
            pial_xyz, faces = nib.load(getattr(fsaverage, f"pial_{hemi}")).darrays
            coords = infl_xyz.data * ALPHA + pial_xyz.data * (1 - ALPHA)
            out.append((np.array(coords), np.array(faces.data)))

        (coords_L, faces_L), (coords_R, faces_R) = out
        adj_L = _build_smooth_adjacency(faces_L, len(coords_L))
        adj_R = _build_smooth_adjacency(faces_R, len(coords_R))
        _mesh_cache = (coords_L, faces_L, adj_L, coords_R, faces_R, adj_R)
    return _mesh_cache

def _build_smooth_adjacency(faces, n_verts):
    """Row-normalized neighbor adjacency. adj @ v gives mean of neighbors per vertex."""
    import scipy.sparse as sp
    e = np.concatenate([
        faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]],
        faces[:, [1, 0]], faces[:, [2, 1]], faces[:, [0, 2]],
    ])
    e = np.unique(e, axis=0)
    adj = sp.csr_matrix(
        (np.ones(len(e), dtype=np.float32), (e[:, 0], e[:, 1])),
        shape=(n_verts, n_verts),
    )
    deg = np.asarray(adj.sum(axis=1)).flatten()
    deg[deg == 0] = 1.0
    return (sp.diags(1.0 / deg) @ adj).tocsr()

def _smooth_on_surface(values, adj, n_iter: int = 4, alpha: float = 0.5):
    """Laplacian smoothing. values: (n_t, n_verts) or (n_verts,)."""
    out = values.astype(np.float32, copy=True)
    if out.ndim == 1:
        for _ in range(n_iter):
            out = (1 - alpha) * out + alpha * (adj @ out)
    else:
        for _ in range(n_iter):
            out = (1 - alpha) * out + alpha * (adj @ out.T).T
    return out

def _tribe_colorscale(threshold_frac: float, cmap_name: str = "hot"):
    """Plotly colorscale matching TRIBE's get_thresholded_sm:
    flat gray below `threshold_frac`, then matplotlib `cmap_name` above.
    threshold_frac is in [0, 1] of the normalized data range."""
    import matplotlib.pyplot as plt
    cmap = plt.get_cmap(cmap_name)
    GRAY = "rgb(128,128,128)"
    cs = [[0.0, GRAY], [max(threshold_frac - 1e-4, 0.0), GRAY]]
    n = 24
    for i in range(n + 1):
        t = i / n
        x = threshold_frac + (1 - threshold_frac) * t
        r, g, b, _ = cmap(t)
        cs.append([min(x, 1.0), f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"])
    return cs


# ── Clinical scoring ──────────────────────────────────────────────────────────
def compute_roi_scores(preds: np.ndarray) -> dict:
    """
    Compute per-ROI activation scores from TRIBE predictions.
    preds: shape (n_timesteps, 20484) — fsaverage5 vertices
    """
    masks = _load_roi_masks()
    print(masks,"masks log in compute_roi_scores")
    n_lh_verts = 10242  # left hemisphere has 10,242 vertices on fsaverage5
    lh_preds = preds[:, :n_lh_verts]  # only use LH (language is left-lateralized)

    print(lh_preds,"lh_preds log in compute_roi_scores")

    scores = {}
    for roi_key, vertex_indices in masks.items():
        if len(vertex_indices) == 0:
            scores[roi_key] = {"mean": 0.0, "peak": 0.0, "n_vertices": 0}
            continue
        # Filter for valid LH indices
        valid_idx = vertex_indices[vertex_indices < n_lh_verts]
        roi_activations = lh_preds[:, valid_idx]
        scores[roi_key] = {
            "mean": float(roi_activations.mean()),
            "peak": float(roi_activations.max()),
            "n_vertices": int(len(valid_idx)),
        }
    return scores


def format_clinical_insights(scores: dict) -> str:
    """Build HTML showing clinical ROI breakdown."""
    rows = []
    for roi_key, data in scores.items():
        roi_def = ROI_DEFINITIONS[roi_key]
        # Color coding based on activation strength
        peak = data["peak"]
        if peak > 1.0:
            color = "#ff5544"
            indicator = "● High"
        elif peak > 0.3:
            color = "#ffaa44"
            indicator = "● Moderate"
        else:
            color = "#5588dd"
            indicator = "● Low"

        rows.append(f"""
        <div class="roi-card">
            <div class="roi-header">
                <span class="roi-name">{roi_def['label']}</span>
                <span class="roi-indicator" style="color:{color}">{indicator}</span>
            </div>
            <div class="roi-function">{roi_def['function']}</div>
            <div class="roi-stats">
                <span class="stat">peak: <b>{data['peak']:+.3f}</b></span>
                <span class="stat">mean: <b>{data['mean']:+.3f}</b></span>
                <span class="stat">vertices: {data['n_vertices']}</span>
            </div>
        </div>
        """)

    return f'<div class="clinical-panel">{"".join(rows)}</div>'


# ── 3-D brain figure ──────────────────────────────────────────────────────────
def build_3d_figure(preds: np.ndarray, threshold_frac: float = 0.3) -> str:
    """Interactive 3D brain heatmap, TRIBE-style."""
    import plotly.graph_objects as go
    import html as _html

    coords_L, faces_L, adj_L, coords_R, faces_R, adj_R = _load_mesh()
    n_verts_L = coords_L.shape[0]
    n_t = preds.shape[0]

    # Smooth ONLY for visualization; ROI scoring elsewhere uses raw preds.
    preds_L = _smooth_on_surface(preds[:, :n_verts_L], adj_L, n_iter=4, alpha=0.5)
    preds_R = _smooth_on_surface(preds[:, n_verts_L:], adj_R, n_iter=4, alpha=0.5)
    preds = np.concatenate([preds_L, preds_R], axis=1)

    # One-sided positive activation; robust vmax (matches TRIBE's
    # robust_normalize default of 99th percentile).
    vmin = 0.0
    vmax = float(np.percentile(preds, 99))
    threshold_frac = float(np.clip(threshold_frac, 0.0, 1.0))

    BG = "#1a1a2e"
    colorscale = _tribe_colorscale(threshold_frac, cmap_name="YlOrRd")

    mesh_kw = dict(
        colorscale=colorscale, cmin=0, cmax=1, showscale=False,
        flatshading=False, hoverinfo="skip",
        lighting=dict(ambient=0.40, diffuse=0.85, specular=0.20, roughness=0.55),
        lightposition=dict(x=80, y=180, z=200),
    )

    def _vals(t):
        v = preds[t]
        return np.clip((v - vmin) / max(vmax - vmin, 1e-8), 0, 1)

    def _traces(t):
        vn = _vals(t)
        offset = 0.0
        tL = go.Mesh3d(
            x=coords_L[:, 0] - offset, y=coords_L[:, 1], z=coords_L[:, 2],
            i=faces_L[:, 0], j=faces_L[:, 1], k=faces_L[:, 2],
            intensity=vn[:n_verts_L], name="Left", **mesh_kw)
        tR = go.Mesh3d(
            x=coords_R[:, 0] + offset, y=coords_R[:, 1], z=coords_R[:, 2],
            i=faces_R[:, 0], j=faces_R[:, 1], k=faces_R[:, 2],
            intensity=vn[n_verts_L:], name="Right", **mesh_kw)
        return tL, tR

    def _intensity_only(t):
        vn = _vals(t)
        return [go.Mesh3d(intensity=vn[:n_verts_L]),
                go.Mesh3d(intensity=vn[n_verts_L:])]

    tL0, tR0 = _traces(0)
    frames = [
        go.Frame(data=_intensity_only(t), name=str(t),
                 layout=go.Layout(title_text=f"t = {t} s"))
        for t in range(n_t)
    ]

    slider_steps = [
        dict(args=[[str(t)], dict(frame=dict(duration=0, redraw=True),
                                   mode="immediate", transition=dict(duration=0))],
             label=str(t), method="animate")
        for t in range(n_t)
    ]

    fig = go.Figure(
        data=[tL0, tR0],
        frames=frames,
        layout=go.Layout(
            height=500,
            paper_bgcolor=BG, plot_bgcolor=BG,
            scene=dict(
                bgcolor=BG,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                camera=dict(
                    eye=dict(x=-1.4, y=0, z=0),
                    center=dict(x=-0, y=0, z=0),   # look-at shifted toward LH
                    up=dict(x=0, y=0, z=1),
                ),
                aspectmode="data",
            ),
            margin=dict(l=0, r=0, t=8, b=70),
            sliders=[dict(
                active=0, steps=slider_steps,
                currentvalue=dict(prefix="t = ", suffix=" s",
                                  font=dict(color="#9ca3af", size=11), visible=True),
                pad=dict(b=8, t=8),
                len=0.85, x=0.5, xanchor="center", y=0,
            )],
        ),
    )

    inner_html = fig.to_html(
        include_plotlyjs=True,
        full_html=True,
        config={
            "responsive": True,
            "displayModeBar": False,
            "scrollZoom": True,
            "doubleClick": "reset",
        },
    )
    srcdoc = _html.escape(inner_html, quote=True)
    return (f'<iframe srcdoc="{srcdoc}" '
            f'style="width:100%;height:520px;border:none;background:{BG};'
            f'touch-action:auto;" '
            f'scrolling="no"></iframe>')

# ── JSON API endpoint (for React frontend) ───────────────────────────────────
@spaces.GPU(duration=ZERO_GPU_DURATION_SECONDS)
def predict_json(
    text: str = "",
    n_timesteps: int = 10,
    video: gr.File | None = None,
) -> dict:
    """
    JSON API endpoint for external clients (React frontend).
    Accepts EITHER text input OR a video file. Returns ROI scores +
    per-timestep temporal data + brain HTML.
    """
    import traceback
    try:
        print(f"🔵 [predict_json] Called with text={text[:50]!r}, video={video!r}, n_timesteps={n_timesteps}")
        model = _load_model()
        print("🔵 [predict_json] Model loaded")

        # Build events dataframe based on input type
        if video is not None:
            print(f"🔵 [predict_json] Video input type: {type(video).__name__}")
            print(f"🔵 [predict_json] Video input value: {video!r}")

            try:
                video_path, orig_name = resolve_uploaded_video_path(video)
            except ValueError as exc:
                return {"success": False, "error": str(exc)}

            print(f"🔵 [predict_json] Extracted video_path: {video_path!r}")

            # TRIBE validates by extension. Gradio uploads strip the extension
            # (saves as /tmp/gradio/.../blob), so we need to add one back.
            # Try to detect from orig_name first, fall back to .mp4.
            import shutil
            if not has_video_extension(video_path):
                ext = extension_from_name(orig_name)
                new_path = video_path + ext
                shutil.copy(video_path, new_path)
                video_path = new_path
                print(f"🔵 [predict_json] Renamed for extension: {video_path}")
            video_path = trim_video_if_needed(video_path)
            df = model.get_events_dataframe(video_path=video_path)
            stimulus_type = "video"
        elif text and text.strip():
            print("🔵 [predict_json] Using text")
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
                tmp.write(text.strip())
                fpath = tmp.name
            try:
                df = model.get_events_dataframe(text_path=fpath)
            finally:
                os.unlink(fpath)
            stimulus_type = "text"
        else:
            return {"success": False, "error": "Provide either text or video input."}

        print(f"🔵 [predict_json] Events dataframe: {len(df)} rows")

        # ZeroGPU DataLoader patch
        import torch.utils.data
        _orig = torch.utils.data.DataLoader.__init__
        def _patched(self, *a, **kw):
            kw["num_workers"] = 0
            _orig(self, *a, **kw)
        torch.utils.data.DataLoader.__init__ = _patched

        try:
            preds, segments = model.predict(events=df)
        finally:
            torch.utils.data.DataLoader.__init__ = _orig

        if hasattr(preds, "cpu"):
            preds = preds.cpu().numpy()

        try:
            requested_timesteps = normalize_timestep_limit(n_timesteps)
        except ValueError as exc:
            return {"success": False, "error": str(exc)}

        n = min(requested_timesteps, len(preds))
        if n == 0:
            return {"success": False, "error": "Model returned no predictions."}

        preds_n = preds[:n]
        brain_html = build_3d_figure(preds_n, threshold_frac=0.3)
        print(f"🔵 [predict_json] Brain HTML generated ({len(brain_html)} bytes)")

        roi_scores = compute_roi_scores(preds_n)

        # Per-timestep ROI scores
        masks = _load_roi_masks()
        n_lh_verts = 10242
        lh_preds = preds_n[:, :n_lh_verts]
        temporal_scores = []
        for t in range(n):
            ts_point = {
                "timestep": int(t),
                "time_seconds": float(t * 1.0),
            }
            for roi_key, vertex_indices in masks.items():
                valid_idx = vertex_indices[vertex_indices < n_lh_verts]
                if len(valid_idx) > 0:
                    ts_point[roi_key] = float(lh_preds[t, valid_idx].mean())
                else:
                    ts_point[roi_key] = 0.0
            temporal_scores.append(ts_point)

        # ROI recommendations
        recommendations = []
        for roi_key, scores in roi_scores.items():
            roi_def = ROI_DEFINITIONS[roi_key]
            peak = scores["peak"]
            level = "high" if peak > 1.0 else ("moderate" if peak > 0.3 else "low")
            recommendations.append({
                "roi_key": roi_key,
                "roi_name": roi_def["label"],
                "function": roi_def["function"],
                "peak": float(peak),
                "mean": float(scores["mean"]),
                "n_vertices": int(scores["n_vertices"]),
                "engagement_level": level,
            })

        result = {
            "success": True,
            "metadata": {
                "n_timesteps": int(n),
                "n_vertices": int(preds.shape[1]),
                "tr_seconds": 1.0,
                "stimulus_type": stimulus_type,
            },
            "roi_scores": recommendations,
            "temporal_scores": temporal_scores,
            "brain_html": brain_html,
        }
        print(f"🟢 [predict_json] Returning {len(recommendations)} ROIs, {len(temporal_scores)} timesteps")
        return result

    except Exception as e:
        tb = traceback.format_exc()
        print(f"🔴 [predict_json] EXCEPTION: {e}\n{tb}")
        return {
            "success": False,
            "error": "Prediction failed. Check server logs for details.",
        }

# ── Core inference (GPU-decorated) ────────────────────────────────────────────
@spaces.GPU(duration=ZERO_GPU_DURATION_SECONDS)
def run_prediction(input_type, video_file, audio_file, text_input,
                   n_timesteps, vmin_val):
    """Main inference function. Runs on ZeroGPU."""
    model = _load_model()

    # Build events dataframe based on input modality
    if input_type == "Video" and video_file is not None:
        video_file = trim_video_if_needed(video_file)
        df = model.get_events_dataframe(video_path=video_file)
    elif input_type == "Audio" and audio_file is not None:
        df = model.get_events_dataframe(audio_path=audio_file)
    elif input_type == "Text" and text_input.strip():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
            tmp.write(text_input.strip())
            fpath = tmp.name
        try:
            df = model.get_events_dataframe(text_path=fpath)
        finally:
            os.unlink(fpath)
    else:
        raise gr.Error("Please provide an input for the selected modality.")

    # ZeroGPU runs in a daemon process — DataLoader can't spawn workers
    import torch.utils.data
    _orig = torch.utils.data.DataLoader.__init__
    def _patched(self, *a, **kw):
        kw["num_workers"] = 0
        _orig(self, *a, **kw)
    torch.utils.data.DataLoader.__init__ = _patched

    try:
        preds, segments = model.predict(events=df)
    finally:
        torch.utils.data.DataLoader.__init__ = _orig

    # Convert to numpy if torch tensor
    if hasattr(preds, "cpu"):
        preds = preds.cpu().numpy()

    try:
        requested_timesteps = normalize_timestep_limit(n_timesteps)
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc

    n = min(requested_timesteps, len(preds))
    if n == 0:
        raise gr.Error("Model returned no predictions for this input.")

    preds_n = preds[:n]

    # Generate outputs
    brain_3d_html = build_3d_figure(preds_n, threshold_frac=vmin_val)
    roi_scores = compute_roi_scores(preds_n)
    clinical_html = format_clinical_insights(roi_scores)

    status = (f"✓ {preds.shape[0]} timesteps × {preds.shape[1]:,} vertices | "
              f"Showing first {n} timesteps")

    return brain_3d_html, clinical_html, status


# ── HTML blocks ────────────────────────────────────────────────────────────────
HEADER = """
<div id="neuro-cue-header">
  <div class="neuro-cue-wordmark">NEURO CUE</div>
  <p class="neuro-cue-subtitle">
    Interactive brain-encoding visualizer · Meta TRIBE v2
  </p>
  <p class="neuro-cue-tagline">
    Submit a video, audio, or text stimulus and see what TRIBE v2 predicts
    cortical activation would look like in a neurotypical adult — with
    anatomical highlighting of canonical language regions.
    Educational tool. Not a medical device.
  </p>
</div>
"""

NOTICE = """
<div class="neuro-cue-notice">
  <span class="notice-label">Note</span>
  This demo runs on ZeroGPU (shared H200). First-run model download takes ~2–4 min.
  Subsequent runs in the same session are much faster (~10s).
</div>
"""

# ── CSS (compact, dark theme inspired by beta3) ───────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

body, .gradio-container {
  background: #0b0e17 !important;
  color: #c9d4e8 !important;
  font-family: 'Inter', system-ui, sans-serif !important;
}

#neuro-cue-header {
  padding: 36px 0 22px;
  text-align: center;
  border-bottom: 1px solid #1a2235;
}
.neuro-cue-wordmark {
  font-size: 2.4rem; font-weight: 600;
  letter-spacing: 0.1em; color: #edf2ff;
  line-height: 1; margin-bottom: 10px;
}
.neuro-cue-subtitle {
  font-size: 0.95rem; color: #5a7aaa;
  margin: 0 0 8px; font-weight: 500;
}
.neuro-cue-tagline {
  font-size: 0.82rem; color: #5a6a88;
  margin: 0; line-height: 1.6;
}

.neuro-cue-notice {
  background: #0d1120;
  border: 1px solid #1a2235;
  border-left: 3px solid #1b4f8a;
  border-radius: 4px;
  padding: 11px 16px;
  font-size: 0.79rem; color: #5a7aaa;
  line-height: 1.6; margin: 16px 0 0;
}
.notice-label {
  font-weight: 600; color: #4a9fd4;
  margin-right: 8px; text-transform: uppercase;
  font-size: 0.66rem; letter-spacing: 0.1em;
}

.tribe-box {
  background: #0d1120 !important;
  border: 1px solid #1a2235 !important;
  border-radius: 6px !important;
  padding: 16px !important;
}

.btn-run button {
  background: #edf2ff !important;
  color: #0b0e17 !important;
  font-weight: 600 !important;
  border: none !important;
  border-radius: 4px !important;
  padding: 11px 0 !important;
  width: 100% !important;
}
.btn-run button:hover { background: #c0cfe8 !important; }

/* Clinical insights cards */
.clinical-panel { display: flex; flex-direction: column; gap: 10px; }
.roi-card {
  background: #080c18;
  border: 1px solid #1a2235;
  border-radius: 6px;
  padding: 14px 16px;
}
.roi-header {
  display: flex; justify-content: space-between;
  align-items: center; margin-bottom: 6px;
}
.roi-name { font-weight: 600; color: #edf2ff; font-size: 0.92rem; }
.roi-indicator { font-size: 0.75rem; font-weight: 500; }
.roi-function {
  font-size: 0.78rem; color: #7a8aa8;
  line-height: 1.5; margin-bottom: 10px;
}
.roi-stats {
  display: flex; gap: 16px;
  font-size: 0.74rem; color: #5a6a88;
  font-family: ui-monospace, monospace;
}
.roi-stats b { color: #c9d4e8; }
"""

# ── UI ─────────────────────────────────────────────────────────────────────────
with gr.Blocks() as demo:

    gr.HTML(HEADER)
    gr.HTML(NOTICE)

    with gr.Row():
        # Left col: inputs
        with gr.Column(scale=1, elem_classes=["tribe-box"]):
            gr.Markdown("### Input Stimulus")

            input_type = gr.Radio(
                choices=["Video", "Audio", "Text"], value="Text",
                label="Modality"
            )

            with gr.Group(visible=False) as video_group:
                video_file = gr.Video(label="Upload video (mp4, mov)")
            with gr.Group(visible=False) as audio_group:
                audio_file = gr.Audio(label="Upload audio (wav, mp3)", type="filepath")
            with gr.Group(visible=True) as text_group:
                text_input = gr.Textbox(
                    label="Therapy text",
                    placeholder="e.g., 'The cat sat on the mat. The dog ran fast.'",
                    lines=4,
                )

            with gr.Accordion("Settings", open=False):
                n_timesteps = gr.Slider(1, 30, value=10, step=1,
                                         label="Timesteps to visualize")
                vmin_slider = gr.Slider(0.0, 1.0, value=0.3, step=0.05,
                         label="Activation threshold (fraction of peak)")

            run_btn = gr.Button("Generate Brain Prediction",
                                elem_classes=["btn-run"])
            status_md = gr.Markdown(value="")

        # Middle col: 3D brain
        with gr.Column(scale=2, elem_classes=["tribe-box"]):
            gr.Markdown("### Cortical Activation Map")
            brain_3d = gr.HTML(value="""
                <div style="height:500px; display:flex; align-items:center;
                           justify-content:center; color:#3a4f6a;">
                    Submit a stimulus to visualize predicted brain activity
                </div>
            """)

        # Right col: clinical insights
        with gr.Column(scale=1, elem_classes=["tribe-box"]):
            gr.Markdown("### Clinical Insights")
            gr.Markdown("*Language ROI scores (left hemisphere)*",
                        elem_classes=["subtitle"])
            clinical_panel = gr.HTML(value="""
                <div style="color:#3a4f6a; font-size:0.85rem; line-height:1.6;">
                    Scores will appear here showing predicted activation in:<br>
                    • Broca's Area (production)<br>
                    • Wernicke's Area (comprehension)<br>
                    • SMA (motor planning)<br>
                    • Angular Gyrus (semantic integration)
                </div>
            """)

    # Toggle input visibility
    def toggle_inputs(choice):
        return (
            gr.update(visible=choice == "Video"),
            gr.update(visible=choice == "Audio"),
            gr.update(visible=choice == "Text"),
        )

    input_type.change(
        fn=toggle_inputs, inputs=[input_type],
        outputs=[video_group, audio_group, text_group],
    )

    run_btn.click(
        fn=run_prediction,
        inputs=[input_type, video_file, audio_file, text_input,
                n_timesteps, vmin_slider],
        outputs=[brain_3d, clinical_panel, status_md],
        api_name="predict",
    )

    # ─── JSON API for external clients (React frontend) ───────────────────────
    gr.api(predict_json, api_name="predict_json")


demo.launch(
    ssr_mode=False,
    css=CSS,
    theme=gr.themes.Base(
        primary_hue="slate",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    ),
)