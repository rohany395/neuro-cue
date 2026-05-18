MAX_TIMESTEPS = 30


def normalize_timestep_limit(
    requested_timesteps,
    available_timesteps: int,
    max_timesteps: int = MAX_TIMESTEPS,
) -> int:
    """Clamp timestep requests to the safe visualization window."""
    if available_timesteps <= 0:
        return 0

    try:
        requested = int(requested_timesteps)
    except (TypeError, ValueError, OverflowError):
        requested = max_timesteps

    requested = max(1, requested)
    return min(requested, available_timesteps, max_timesteps)
