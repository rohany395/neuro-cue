import unittest

from inference_limits import DEFAULT_TIMESTEPS, MAX_TIMESTEPS, normalize_timestep_limit


class NormalizeTimestepLimitTest(unittest.TestCase):
    def test_caps_large_requests(self):
        self.assertEqual(normalize_timestep_limit(100, 100), MAX_TIMESTEPS)

    def test_never_exceeds_available_predictions(self):
        self.assertEqual(normalize_timestep_limit(MAX_TIMESTEPS, 12), 12)

    def test_invalid_values_fall_back_to_default(self):
        self.assertEqual(normalize_timestep_limit("bad", 100), DEFAULT_TIMESTEPS)

    def test_non_positive_values_are_clamped(self):
        self.assertEqual(normalize_timestep_limit(0, 100), 1)
        self.assertEqual(normalize_timestep_limit(-5, 100), 1)

    def test_zero_available_predictions_returns_zero(self):
        self.assertEqual(normalize_timestep_limit(10, 0), 0)


if __name__ == "__main__":
    unittest.main()
