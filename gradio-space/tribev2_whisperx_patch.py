"""
Patch tribev2's WhisperX subprocess call for HF Spaces.

Upstream tribev2 runs `uvx whisperx` with no version pin. That pulls the latest
whisperx + pyannote 4.x, which breaks VAD with:
  AttributeError: 'generator' object has no attribute 'data'

We pin whisperx==3.1.5 and run it from the main Space environment (not uvx).
uvx tried to compile av==11.* against FFmpeg 7 on every text prediction; the
deps in requirements.txt use prebuilt PyAV wheels instead.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import torch

logger = logging.getLogger(__name__)

WHISPERX_VERSION = "3.1.5"
_PATCHED = False


def _ensure_whisperx_installed() -> None:
    """Install whisperx CLI without pulling av==11.* from faster-whisper 1.0.1."""
    for module in ("nltk", "transformers", "pandas"):
        if importlib.util.find_spec(module) is None:
            raise RuntimeError(
                f"Missing whisperx runtime dependency {module!r}; "
                "rebuild the Space so requirements.txt is applied."
            )
    if importlib.util.find_spec("whisperx") is not None:
        return
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
        env={k: v for k, v in os.environ.items() if k != "MPLBACKEND"},
    )


def _whisperx_executable() -> list[str]:
    """Run pinned whisperx from the main environment (reuses torch 2.8)."""
    return [sys.executable, "-m", "whisperx"]


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
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
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
