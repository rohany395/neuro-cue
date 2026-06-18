"""Validation helpers for public prediction requests."""

from pathlib import Path
from urllib.parse import unquote, urlparse


DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
GRADIO_UPLOAD_ROOT = Path("/tmp/gradio")
MAX_TEXT_CHARS = 5000
MAX_TIMESTEPS = 30
ALLOWED_VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv", ".avi")


class InputValidationError(ValueError):
    """Raised when a public request contains invalid user-controlled input."""


def normalize_timestep_limit(value: int | str, max_timesteps: int = MAX_TIMESTEPS) -> int:
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError) as exc:
        raise InputValidationError("n_timesteps must be a positive integer.") from exc

    if n_timesteps < 1:
        raise InputValidationError("n_timesteps must be a positive integer.")

    return min(n_timesteps, max_timesteps)


def validate_text_input(text: str | None, max_chars: int = MAX_TEXT_CHARS) -> str:
    if text is None:
        return ""

    if not isinstance(text, str):
        raise InputValidationError("Text input must be a string.")

    stripped = text.strip()
    if len(stripped) > max_chars:
        raise InputValidationError(f"Text input must be {max_chars} characters or fewer.")
    return stripped


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _space_hostname(space_url: str) -> str:
    hostname = urlparse(space_url).hostname
    return hostname.lower() if hostname else ""


def _extract_file_route_path(url: str, space_url: str) -> str:
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise InputValidationError("video_ref url is invalid.") from exc

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise InputValidationError("video_ref url is invalid.")

    expected_host = _space_hostname(space_url)
    if expected_host and parsed.hostname.lower() != expected_host:
        raise InputValidationError("video_ref url must point to this Hugging Face Space.")

    decoded_path = unquote(parsed.path)
    marker = "/file="
    if marker not in decoded_path:
        raise InputValidationError("video_ref url must be a Gradio file URL.")

    return decoded_path.split(marker, 1)[1]


def _coerce_file_path(raw_path: str) -> str:
    decoded = unquote(raw_path)
    if decoded.startswith(("http://", "https://")):
        return ""
    if decoded.startswith("file="):
        return decoded[len("file="):]
    if "/file=" in decoded:
        return decoded.split("/file=", 1)[1]
    return decoded


def _validate_uploaded_path(raw_path: str, upload_root: Path) -> Path:
    candidate_value = _coerce_file_path(raw_path)
    if not candidate_value:
        raise InputValidationError("video_ref must include an uploaded file path.")

    candidate = Path(candidate_value).resolve(strict=False)
    root = upload_root.resolve(strict=False)
    if not _is_relative_to(candidate, root):
        raise InputValidationError("video_ref path must reference a Gradio upload.")
    if not candidate.is_file():
        raise InputValidationError("video_ref path does not exist.")

    return candidate


def _extract_video_fields(video: object) -> tuple[str, str, str | None]:
    if isinstance(video, dict):
        raw_path = video.get("path") if isinstance(video.get("path"), str) else ""
        url = video.get("url") if isinstance(video.get("url"), str) else ""
        orig_name = (
            video.get("orig_name")
            if isinstance(video.get("orig_name"), str)
            else video.get("meta", {}).get("name")
            if isinstance(video.get("meta"), dict)
            and isinstance(video.get("meta", {}).get("name"), str)
            else None
        )
    elif isinstance(video, str):
        raw_path = video
        url = video if video.startswith(("http://", "https://")) else ""
        orig_name = None
    elif hasattr(video, "name"):
        raw_path = str(video.name)
        url = ""
        orig_name = None
    else:
        raise InputValidationError(f"Unrecognized video input type: {type(video).__name__}.")

    if raw_path.startswith(("http://", "https://")):
        url = url or raw_path
        raw_path = ""

    return raw_path, url, orig_name


def resolve_uploaded_video_path(
    video: object,
    upload_root: Path = GRADIO_UPLOAD_ROOT,
    space_url: str = DEFAULT_SPACE_URL,
) -> tuple[str, str | None]:
    raw_path, url, orig_name = _extract_video_fields(video)

    if not raw_path and url:
        raw_path = _extract_file_route_path(url, space_url)
    if not raw_path:
        raise InputValidationError("video_ref must include an uploaded file path.")

    candidate = _validate_uploaded_path(raw_path, upload_root)

    if url:
        url_path = _extract_file_route_path(url, space_url)
        url_candidate = _validate_uploaded_path(url_path, upload_root)
        if candidate != url_candidate:
            raise InputValidationError("video_ref path and url do not match.")

    return str(candidate), orig_name


def choose_video_extension(orig_name: str | None) -> str:
    if orig_name:
        suffix = Path(orig_name).suffix.lower()
        if suffix in ALLOWED_VIDEO_EXTENSIONS:
            return suffix
    return ".mp4"
