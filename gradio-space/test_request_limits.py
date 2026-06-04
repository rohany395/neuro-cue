import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from request_limits import MAX_TEXT_CHARS, normalize_timestep_limit, validate_text_input


class RequestLimitsTest(unittest.TestCase):
    def test_normalize_timestep_limit_caps_public_requests(self):
        self.assertEqual(normalize_timestep_limit(10), 10)
        self.assertEqual(normalize_timestep_limit(100), 30)

    def test_normalize_timestep_limit_respects_available_predictions(self):
        self.assertEqual(normalize_timestep_limit(30, available=7), 7)

    def test_normalize_timestep_limit_defaults_invalid_values(self):
        self.assertEqual(normalize_timestep_limit("not-a-number"), 10)
        self.assertEqual(normalize_timestep_limit(0), 1)

    def test_validate_text_input_strips_and_caps_text(self):
        self.assertEqual(validate_text_input("  hello  "), "hello")
        with self.assertRaisesRegex(ValueError, str(MAX_TEXT_CHARS)):
            validate_text_input("x" * (MAX_TEXT_CHARS + 1))


if __name__ == "__main__":
    unittest.main()
