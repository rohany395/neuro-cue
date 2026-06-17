import unittest

from input_validation import (
    MAX_TIMESTEPS,
    normalize_timestep_limit,
    resolve_uploaded_video_path,
    validate_text_input,
)


SPACE_URL = "https://rohany395-neuro-cue.hf.space/"


class InputValidationTest(unittest.TestCase):
    def test_normalize_timestep_limit_caps_public_requests(self):
        self.assertEqual(normalize_timestep_limit(MAX_TIMESTEPS + 1000), MAX_TIMESTEPS)
        self.assertEqual(normalize_timestep_limit("12"), 12)

    def test_normalize_timestep_limit_rejects_invalid_values(self):
        with self.assertRaisesRegex(ValueError, "positive integer"):
            normalize_timestep_limit(0)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            normalize_timestep_limit("not-a-number")

    def test_validate_text_input_rejects_empty_and_oversized_text(self):
        with self.assertRaisesRegex(ValueError, "Text input is required"):
            validate_text_input("   ")
        with self.assertRaisesRegex(ValueError, "5000 characters"):
            validate_text_input("x" * 5001)

    def test_resolve_uploaded_video_path_accepts_configured_space_upload(self):
        path, orig_name = resolve_uploaded_video_path(
            {
                "path": "/tmp/gradio/abc123/blob",
                "url": "https://rohany395-neuro-cue.hf.space/file=/tmp/gradio/abc123/blob",
                "orig_name": "clip.mp4",
            },
            space_url=SPACE_URL,
        )

        self.assertEqual(path, "/tmp/gradio/abc123/blob")
        self.assertEqual(orig_name, "clip.mp4")

    def test_resolve_uploaded_video_path_rejects_arbitrary_local_paths(self):
        with self.assertRaisesRegex(ValueError, "outside the Gradio upload directory"):
            resolve_uploaded_video_path({"path": "/etc/passwd"}, space_url=SPACE_URL)

        with self.assertRaisesRegex(ValueError, "outside the Gradio upload directory"):
            resolve_uploaded_video_path({"path": "/tmp/gradio_evil/blob"}, space_url=SPACE_URL)

    def test_resolve_uploaded_video_path_rejects_other_hf_space_hosts(self):
        with self.assertRaisesRegex(ValueError, "configured Hugging Face Space"):
            resolve_uploaded_video_path(
                {
                    "url": "https://attacker-neuro-cue.hf.space/file=/tmp/gradio/abc123/blob",
                },
                space_url=SPACE_URL,
            )

    def test_resolve_uploaded_video_path_rejects_path_url_mismatch(self):
        with self.assertRaisesRegex(ValueError, "do not reference the same file"):
            resolve_uploaded_video_path(
                {
                    "path": "/tmp/gradio/abc123/blob",
                    "url": "https://rohany395-neuro-cue.hf.space/file=/tmp/gradio/other/blob",
                },
                space_url=SPACE_URL,
            )


if __name__ == "__main__":
    unittest.main()
