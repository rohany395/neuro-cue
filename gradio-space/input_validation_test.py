import unittest

from input_validation import (
    MAX_TIMESTEPS,
    extension_from_name,
    normalize_timestep_limit,
    resolve_uploaded_video_path,
)


class InputValidationTest(unittest.TestCase):
    def test_normalize_timestep_limit_caps_public_requests(self):
        self.assertEqual(normalize_timestep_limit(10), 10)
        self.assertEqual(normalize_timestep_limit(100), MAX_TIMESTEPS)

    def test_normalize_timestep_limit_rejects_non_positive_values(self):
        with self.assertRaisesRegex(ValueError, "positive integer"):
            normalize_timestep_limit(0)

    def test_resolve_uploaded_video_path_accepts_matching_gradio_file_ref(self):
        video = {
            "path": "/tmp/gradio/session/blob",
            "url": "https://rohany395-neuro-cue.hf.space/gradio_api/file=/tmp/gradio/session/blob",
            "orig_name": "therapy.mov",
        }

        path, orig_name = resolve_uploaded_video_path(video)

        self.assertEqual(path, "/tmp/gradio/session/blob")
        self.assertEqual(orig_name, "therapy.mov")

    def test_resolve_uploaded_video_path_rejects_path_outside_upload_root(self):
        with self.assertRaisesRegex(ValueError, "Gradio upload directory"):
            resolve_uploaded_video_path({"path": "/etc/passwd", "orig_name": "x.mp4"})

    def test_resolve_uploaded_video_path_rejects_other_space_hosts(self):
        video = {
            "url": "https://attacker-space.hf.space/gradio_api/file=/tmp/gradio/session/blob",
            "orig_name": "therapy.mp4",
        }

        with self.assertRaisesRegex(ValueError, "configured Hugging Face Space"):
            resolve_uploaded_video_path(video)

    def test_resolve_uploaded_video_path_rejects_path_url_mismatch(self):
        video = {
            "path": "/tmp/gradio/session/blob-a",
            "url": "https://rohany395-neuro-cue.hf.space/gradio_api/file=/tmp/gradio/session/blob-b",
            "orig_name": "therapy.mp4",
        }

        with self.assertRaisesRegex(ValueError, "same upload"):
            resolve_uploaded_video_path(video)

    def test_extension_from_name_uses_known_video_extensions_only(self):
        self.assertEqual(extension_from_name("clip.webm"), ".webm")
        self.assertEqual(extension_from_name("not-video.txt"), ".mp4")


if __name__ == "__main__":
    unittest.main()
