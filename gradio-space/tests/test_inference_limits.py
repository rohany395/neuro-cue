import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inference_limits import DEFAULT_TIMESTEPS, MAX_TIMESTEPS, normalize_timestep_limit


class NormalizeTimestepLimitTest(unittest.TestCase):
    def test_caps_large_requests(self):
        self.assertEqual(normalize_timestep_limit(100, 200), MAX_TIMESTEPS)

    def test_rejects_non_positive_requests(self):
        self.assertEqual(normalize_timestep_limit(-5, 20), 1)
        self.assertEqual(normalize_timestep_limit(0, 20), 1)

    def test_uses_default_for_invalid_requests(self):
        self.assertEqual(
            normalize_timestep_limit("not-a-number", 20),
            min(DEFAULT_TIMESTEPS, 20),
        )

    def test_does_not_exceed_available_predictions(self):
        self.assertEqual(normalize_timestep_limit(10, 3), 3)
        self.assertEqual(normalize_timestep_limit(10, 0), 0)


if __name__ == "__main__":
    unittest.main()
