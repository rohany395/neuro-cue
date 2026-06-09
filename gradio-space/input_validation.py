"""Input validation helpers for public Gradio API requests."""

from pathlib import Path
from typing import Any

MAX_TIMESTEPS = 30
DEFAULT_TIMESTEPS = 10
GRADIO_UPLOAD_ROOT = Path("/tmp/gradio")
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}


def normalize_timestep_limit(value: Any, default: int = DEFAULT_TIMESTEPS) -> int:
    """Return a bounded positive timestep count for API visualizations."""
    if value is None or value == "":
        return default

    try:
        requested = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("n_timesteps must be a positive integer.") from exc

    if requested < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(requested, MAX_TIMESTEPS)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _extract_video_path_and_name(video: Any) -> tuple[str | None, str | None]:
    if isinstance(video, dict):
        path = video.get("path")
        orig_name = video.get("orig_name")
        if not orig_name and isinstance(video.get("meta"), dict):
            orig_name = video["meta"].get("name")
        return (
            path if isinstance(path, str) else None,
            orig_name if isinstance(orig_name, str) else None,
        )

    if isinstance(video, str):
        return video, None

    if hasattr(video, "name"):
        return str(video.name), None

    return None, None


def resolve_uploaded_video_path(
    video: Any,
    upload_root: str | Path = GRADIO_UPLOAD_ROOT,
) -> tuple[str, str | None]:
    """Resolve a Gradio-uploaded video path and reject arbitrary local/remote files."""
    path_value, orig_name = _extract_video_path_and_name(video)
    if not path_value:
        raise ValueError("Uploaded video path is required.")

    if "://" in path_value:
        raise ValueError("Uploaded video must reference a local Gradio upload path.")

    upload_root = Path(upload_root).resolve()
    video_path = Path(path_value).resolve()

    if not _is_relative_to(video_path, upload_root):
        raise ValueError("Uploaded video path is outside the Gradio upload directory.")

    if not video_path.is_file():
        raise ValueError("Uploaded video file was not found.")

    return str(video_path), orig_name


def ensure_video_extension(path: str, orig_name: str | None = None) -> str:
    """Return a path with a video extension, copying extensionless uploads if needed."""
    video_path = Path(path)
    suffix = video_path.suffix.lower()
    if suffix in ALLOWED_VIDEO_EXTENSIONS:
        return str(video_path)

    if suffix:
        raise ValueError("Uploaded video file type is not supported.")

    ext = ".mp4"
    if orig_name:
        orig_ext = Path(orig_name).suffix.lower()
        if orig_ext in ALLOWED_VIDEO_EXTENSIONS:
            ext = orig_ext

    target = video_path.with_name(f"{video_path.name}{ext}")
    target.write_bytes(video_path.read_bytes())
    return str(target)
