"""Input limits shared by the public Gradio API."""


MAX_TEXT_CHARS = 5000
MAX_TIMESTEPS = 30


def normalize_timestep_limit(value, available: int | None = None) -> int:
    """Clamp public API requests so Plotly responses stay bounded."""
    try:
        requested = int(value)
    except (TypeError, ValueError):
        requested = 10

    requested = max(1, requested)
    requested = min(requested, MAX_TIMESTEPS)
    if available is not None:
        requested = min(requested, available)
    return requested


def validate_text_input(text: str) -> str:
    raw = text if isinstance(text, str) else ("" if text is None else str(text))
    cleaned = raw.strip()
    if len(cleaned) > MAX_TEXT_CHARS:
        raise ValueError(f"Text input must be {MAX_TEXT_CHARS} characters or fewer.")
    return cleaned
