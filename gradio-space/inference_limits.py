DEFAULT_TIMESTEPS = 10
MAX_TIMESTEPS = 30


def normalize_timestep_limit(value, available_timesteps=None):
    """Return a safe, positive timestep count for response generation."""
    try:
        requested = int(value)
    except (TypeError, ValueError):
        requested = DEFAULT_TIMESTEPS

    requested = max(1, min(requested, MAX_TIMESTEPS))

    if available_timesteps is None:
        return requested

    return min(requested, max(0, int(available_timesteps)))
