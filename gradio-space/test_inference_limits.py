import unittest

from inference_limits import MAX_TIMESTEPS, normalize_timestep_limit


class NormalizeTimestepLimitTest(unittest.TestCase):
    def test_caps_large_requests_to_max_timesteps(self):
        self.assertEqual(
            normalize_timestep_limit(10_000, MAX_TIMESTEPS + 5),
            MAX_TIMESTEPS,
        )

    def test_does_not_exceed_available_predictions(self):
        self.assertEqual(normalize_timestep_limit(MAX_TIMESTEPS, 4), 4)

    def test_negative_requests_keep_one_timestep_when_available(self):
        self.assertEqual(normalize_timestep_limit(-10, 8), 1)

    def test_invalid_requests_fall_back_to_max_window(self):
        self.assertEqual(
            normalize_timestep_limit("not-a-number", MAX_TIMESTEPS + 10),
            MAX_TIMESTEPS,
        )

    def test_empty_predictions_return_zero(self):
        self.assertEqual(normalize_timestep_limit(10, 0), 0)


if __name__ == "__main__":
    unittest.main()
