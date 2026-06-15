import unittest

from input_validation import (
    extension_from_orig_name,
    normalize_timestep_limit,
    resolve_uploaded_video_path,
)


class InputValidationTest(unittest.TestCase):
    def test_timestep_limit_is_positive_and_capped(self):
        self.assertEqual(normalize_timestep_limit("10"), 10)
        self.assertEqual(normalize_timestep_limit(1000), 30)

        with self.assertRaises(ValueError):
            normalize_timestep_limit(0)

    def test_uploaded_video_path_must_stay_under_gradio_tmp(self):
        self.assertEqual(
            resolve_uploaded_video_path({"path": "/tmp/gradio/session/blob"}),
            "/tmp/gradio/session/blob",
        )

        with self.assertRaises(ValueError):
            resolve_uploaded_video_path({"path": "/tmp/gradio/../secret.mp4"})

        with self.assertRaises(ValueError):
            resolve_uploaded_video_path({"path": "/etc/passwd"})

    def test_video_url_must_be_space_file_route(self):
        self.assertEqual(
            resolve_uploaded_video_path(
                {
                    "url": "https://rohany395-neuro-cue.hf.space/file=/tmp/gradio/session/blob",
                },
            ),
            "/tmp/gradio/session/blob",
        )

        with self.assertRaises(ValueError):
            resolve_uploaded_video_path(
                {
                    "url": "https://attacker.example/file=/tmp/gradio/session/blob",
                },
            )

        with self.assertRaises(ValueError):
            resolve_uploaded_video_path(
                {
                    "url": "https://rohany395-neuro-cue.hf.space/file=/etc/passwd",
                },
            )

    def test_video_path_and_url_must_match(self):
        with self.assertRaises(ValueError):
            resolve_uploaded_video_path(
                {
                    "path": "/tmp/gradio/session/a",
                    "url": "https://rohany395-neuro-cue.hf.space/file=/tmp/gradio/session/b",
                },
            )

    def test_extension_comes_from_original_name_when_safe(self):
        self.assertEqual(extension_from_orig_name("clip.webm"), ".webm")
        self.assertEqual(extension_from_orig_name("clip.txt"), ".mp4")
        self.assertEqual(extension_from_orig_name(None), ".mp4")


if __name__ == "__main__":
    unittest.main()
