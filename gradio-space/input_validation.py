import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse


DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
MAX_TEXT_CHARS = 5000
MAX_TIMESTEPS = 30
UPLOAD_ROOT = Path(os.environ.get("GRADIO_UPLOAD_ROOT", Path(tempfile.gettempdir()) / "gradio"))
VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv", ".avi")


def normalize_text_input(text: str | None) -> str:
    normalized = (text or "").strip()
    if len(normalized) > MAX_TEXT_CHARS:
        raise ValueError(f"Text input must be {MAX_TEXT_CHARS} characters or fewer.")
    return normalized


def normalize_timestep_limit(value) -> int:
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError):
        raise ValueError("n_timesteps must be a positive integer.") from None

    if n_timesteps < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(n_timesteps, MAX_TIMESTEPS)


def get_original_name(file_ref) -> str | None:
    if not isinstance(file_ref, dict):
        return None

    if isinstance(file_ref.get("orig_name"), str):
        return file_ref["orig_name"]

    meta = file_ref.get("meta")
    if isinstance(meta, dict) and isinstance(meta.get("name"), str):
        return meta["name"]

    return None


def _allowed_space_host(space_url: str | None = None) -> str:
    parsed = urlparse(space_url or os.environ.get("SPACE_URL") or DEFAULT_SPACE_URL)
    return (parsed.hostname or "").lower()


def _path_from_file_url(url: str, space_url: str | None = None) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Uploaded video URL must use HTTPS.")

    allowed_host = _allowed_space_host(space_url)
    if parsed.hostname is None or parsed.hostname.lower() != allowed_host:
        raise ValueError("Uploaded video URL must point to the configured Space.")

    decoded_path = unquote(parsed.path)
    marker = "/file="
    marker_index = decoded_path.find(marker)
    if marker_index == -1:
        raise ValueError("Uploaded video URL must reference a Space file.")

    return decoded_path[marker_index + len(marker):]


def _resolve_upload_path(path: str) -> Path:
    if not path:
        raise ValueError("Uploaded video path is missing.")

    candidate = Path(path)
    if not candidate.is_absolute():
        raise ValueError("Uploaded video path must be absolute.")

    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        raise ValueError("Uploaded video file was not found.") from None

    upload_root = UPLOAD_ROOT.resolve()
    try:
        resolved.relative_to(upload_root)
    except ValueError:
        raise ValueError("Uploaded video path is outside the Gradio upload directory.") from None

    return resolved


def resolve_uploaded_video_path(file_ref, space_url: str | None = None) -> str:
    """Return a verified local path for a Gradio-uploaded video reference."""
    if isinstance(file_ref, dict):
        raw_path = file_ref.get("path") if isinstance(file_ref.get("path"), str) else ""
        raw_url = file_ref.get("url") if isinstance(file_ref.get("url"), str) else ""
    elif isinstance(file_ref, str):
        raw_path = ""
        raw_url = file_ref if file_ref.startswith(("http://", "https://")) else ""
        if not raw_url:
            raw_path = file_ref
    elif hasattr(file_ref, "name"):
        raw_path = file_ref.name
        raw_url = ""
    else:
        raise ValueError(f"Unrecognized video input type: {type(file_ref).__name__}")

    resolved_path = _resolve_upload_path(raw_path) if raw_path else None
    resolved_url_path = _resolve_upload_path(_path_from_file_url(raw_url, space_url)) if raw_url else None

    if resolved_path and resolved_url_path and resolved_path != resolved_url_path:
        raise ValueError("Uploaded video path and URL do not refer to the same file.")

    resolved = resolved_path or resolved_url_path
    if resolved is None:
        raise ValueError("Uploaded video reference must include a path or URL.")

    return str(resolved)


def ensure_video_extension(path: str, orig_name: str | None = None) -> str:
    if path.lower().endswith(VIDEO_EXTENSIONS):
        return path

    ext = ".mp4"
    if orig_name and orig_name.lower().endswith(VIDEO_EXTENSIONS):
        ext = "." + orig_name.rsplit(".", 1)[-1].lower()

    new_path = path + ext
    shutil.copy(path, new_path)
    return new_path
