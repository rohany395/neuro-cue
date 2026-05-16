MAX_TIMESTEPS = 30
DEFAULT_TIMESTEPS = 10


def normalize_timestep_limit(value, available_timesteps: int) -> int:
    """Return a safe number of timesteps to render in API/UI responses."""
    try:
        requested = int(value)
    except (TypeError, ValueError):
        requested = DEFAULT_TIMESTEPS

    available = max(int(available_timesteps), 0)
    return min(max(requested, 1), MAX_TIMESTEPS, available)
