"""
Patch tribev2's WhisperX subprocess call for HF Spaces.

Upstream tribev2 runs `uvx whisperx` with no version pin. That pulls the latest
whisperx + pyannote 4.x, which breaks VAD with:
  AttributeError: 'generator' object has no attribute 'data'

We pin whisperx==3.1.5 + faster-whisper==1.0.1 and run from the main Space env.
av==12.3.0 (prebuilt wheels) substitutes for av==11.*; faster-whisper 1.2+
breaks whisperx 3.1.5's TranscriptionOptions API.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import torch

logger = logging.getLogger(__name__)

WHISPERX_VERSION = "3.1.5"
FASTER_WHISPER_VERSION = "1.0.1"
_PATCHED = False
DEFAULT_VAD_MODEL = "pyannote/segmentation-3.0"


def _pip_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k != "MPLBACKEND"}


def _package_version(dist_name: str) -> str | None:
    try:
        from importlib.metadata import version

        return version(dist_name)
    except Exception:
        return None


def _ensure_whisperx_installed() -> None:
    """Install whisperx + faster-whisper without pulling av==11.*."""
    for module in ("nltk", "transformers", "pandas"):
        if importlib.util.find_spec(module) is None:
            raise RuntimeError(
                f"Missing whisperx runtime dependency {module!r}; "
                "rebuild the Space so requirements.txt is applied."
            )

    fw_version = _package_version("faster-whisper")
    if fw_version != FASTER_WHISPER_VERSION:
        if fw_version:
            logger.info(
                "Replacing faster-whisper %s with %s for whisperx 3.1.5 compatibility",
                fw_version,
                FASTER_WHISPER_VERSION,
            )
        else:
            logger.info("Installing faster-whisper==%s (--no-deps)...", FASTER_WHISPER_VERSION)
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "--no-deps",
                "--force-reinstall",
                f"faster-whisper=={FASTER_WHISPER_VERSION}",
            ],
            env=_pip_env(),
        )

    if importlib.util.find_spec("whisperx") is None:
        logger.info("Installing whisperx==%s (--no-deps)...", WHISPERX_VERSION)
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "--no-deps",
                f"whisperx=={WHISPERX_VERSION}",
            ],
            env=_pip_env(),
        )


def _whisperx_executable() -> list[str]:
    """Run pinned whisperx from the main environment (reuses torch 2.8).

    whisperx 3.1.5 downloads its VAD checkpoint from a hard-coded S3 URL whose
    bucket now reports the wrong region as a 301 without a Location header. Start
    the CLI through this module so we can patch the VAD loader first.
    """
    return [
        sys.executable,
        "-c",
        (
            "from tribev2_whisperx_patch import _run_patched_whisperx_cli; "
            "_run_patched_whisperx_cli()"
        ),
    ]


def _patch_whisperx_vad_loader() -> None:
    """Make whisperx use a current pyannote VAD model instead of the dead S3 URL."""
    import whisperx.asr as asr
    import whisperx.vad as vad

    def _load_vad_model(
        device,
        vad_onset=0.500,
        vad_offset=0.363,
        use_auth_token=None,
        model_fp=None,
    ):
        token = (
            use_auth_token
            or os.environ.get("HF_TOKEN")
            or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        )
        model_id = os.environ.get("WHISPERX_VAD_MODEL", DEFAULT_VAD_MODEL)
        logger.info("Loading WhisperX VAD model from %s", model_id)
        hyperparameters = {
            "onset": vad_onset,
            "offset": vad_offset,
            "min_duration_on": 0.1,
            "min_duration_off": 0.1,
        }
        try:
            vad_pipeline = vad.VoiceActivitySegmentation(
                segmentation=model_id,
                use_auth_token=token,
                device=torch.device(device),
            )
        except AttributeError as exc:
            if "'NoneType' object has no attribute 'eval'" in str(exc):
                raise RuntimeError(
                    f"Could not load WhisperX VAD model {model_id!r}. "
                    "On Hugging Face Spaces this usually means HF_TOKEN is missing, "
                    "invalid, or has not accepted the pyannote model terms."
                ) from exc
            raise
        vad_pipeline.instantiate(hyperparameters)
        return vad_pipeline

    vad.load_vad_model = _load_vad_model
    asr.load_vad_model = _load_vad_model


def _run_patched_whisperx_cli() -> None:
    _patch_whisperx_vad_loader()
    from whisperx.transcribe import cli

    cli()


def _probe_audio_duration(path: Path) -> float | None:
    try:
        out = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        return float(out.stdout.strip())
    except Exception:
        return None


def _fallback_transcript_from_text_cache(wav_filename: Path) -> pd.DataFrame | None:
    """Approximate word timings for TRIBE text-to-TTS cache entries.

    TRIBE stores TTS audio under a cache directory containing a sanitized text
    slug, e.g. ``text=the-cat-sat-on-the-mat-801d824c/audio.mp3``. If WhisperX
    cannot load VAD because pyannote access is unavailable, this keeps text
    predictions working. Video/audio inputs still require WhisperX.
    """
    match = re.search(r"text=([^/\\]+)", str(wav_filename))
    if not match:
        return None

    slug = re.sub(r"-[0-9a-f]{8,}$", "", match.group(1), flags=re.IGNORECASE)
    words = [w for w in slug.split("-") if w]
    if not words:
        return None

    duration = _probe_audio_duration(wav_filename)
    if duration is None or duration <= 0:
        duration = max(len(words) * 0.35, 1.0)

    word_duration = duration / len(words)
    sentence = " ".join(words)
    return pd.DataFrame(
        [
            {
                "text": word,
                "start": i * word_duration,
                "duration": word_duration,
                "sequence_id": 0,
                "sentence": sentence,
            }
            for i, word in enumerate(words)
        ]
    )


def _get_transcript_from_audio(wav_filename: Path, language: str) -> pd.DataFrame:
    language_codes = {
        "english": "en",
        "french": "fr",
        "spanish": "es",
        "dutch": "nl",
        "chinese": "zh",
    }
    if language not in language_codes:
        raise ValueError(f"Language {language} not supported")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"

    with tempfile.TemporaryDirectory() as output_dir:
        logger.info("Running whisperx (pinned %s)...", WHISPERX_VERSION)
        cmd = [
            *_whisperx_executable(),
            str(wav_filename),
            "--model",
            "large-v3",
            "--language",
            language_codes[language],
            "--device",
            device,
            "--compute_type",
            compute_type,
            "--batch_size",
            "16",
            "--align_model",
            "WAV2VEC2_ASR_LARGE_LV60K_960H" if language == "english" else "",
            "--output_dir",
            output_dir,
            "--output_format",
            "json",
        ]
        cmd = [c for c in cmd if c]
        env = {k: v for k, v in os.environ.items() if k != "MPLBACKEND"}
        patch_dir = str(Path(__file__).resolve().parent)
        env["PYTHONPATH"] = (
            patch_dir
            if not env.get("PYTHONPATH")
            else f"{patch_dir}{os.pathsep}{env['PYTHONPATH']}"
        )
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            fallback = _fallback_transcript_from_text_cache(wav_filename)
            if fallback is not None:
                logger.warning(
                    "whisperx failed; using approximate text-cache word timings. stderr=%s",
                    result.stderr[-2000:],
                )
                return fallback
            raise RuntimeError(f"whisperx failed:\n{result.stderr}")

        json_path = Path(output_dir) / f"{wav_filename.stem}.json"
        transcript = json.loads(json_path.read_text())

    words = []
    for i, segment in enumerate(transcript["segments"]):
        sentence = segment["text"].replace('"', "")
        for word in segment["words"]:
            if "start" not in word:
                continue
            words.append(
                {
                    "text": word["word"].replace('"', ""),
                    "start": word["start"],
                    "duration": word["end"] - word["start"],
                    "sequence_id": i,
                    "sentence": sentence,
                }
            )

    return pd.DataFrame(words)


def apply_tribev2_whisperx_patch() -> None:
    global _PATCHED
    if _PATCHED:
        return

    _ensure_whisperx_installed()

    import tribev2.eventstransforms as eventstransforms

    eventstransforms.ExtractWordsFromAudio._get_transcript_from_audio = staticmethod(
        _get_transcript_from_audio
    )
    _PATCHED = True
    print(f"🟢 Patched tribev2 WhisperX to use whisperx=={WHISPERX_VERSION} (main env)")
