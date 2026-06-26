import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import input_validation


class InputValidationTests(unittest.TestCase):
    def setUp(self):
        self.previous_space_url = os.environ.get("HF_SPACE_URL")
        os.environ["HF_SPACE_URL"] = "https://rohany395-neuro-cue.hf.space/"
        input_validation.UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
        self.upload_dir = Path(tempfile.mkdtemp(dir=input_validation.UPLOAD_ROOT))
        self.video_path = self.upload_dir / "blob"
        self.video_path.write_bytes(b"video")

    def tearDown(self):
        for path in sorted(self.upload_dir.glob("*"), reverse=True):
            path.unlink()
        self.upload_dir.rmdir()

        if self.previous_space_url is None:
            os.environ.pop("HF_SPACE_URL", None)
        else:
            os.environ["HF_SPACE_URL"] = self.previous_space_url

    def test_normalize_timestep_limit_caps_response_size(self):
        self.assertEqual(input_validation.normalize_timestep_limit(1000), 30)
        self.assertEqual(input_validation.normalize_timestep_limit("12"), 12)

    def test_normalize_timestep_limit_rejects_non_positive_values(self):
        with self.assertRaisesRegex(ValueError, "positive integer"):
            input_validation.normalize_timestep_limit(0)

    def test_resolve_uploaded_video_path_accepts_matching_space_url(self):
        path, orig_name = input_validation.resolve_uploaded_video_path(
            {
                "path": str(self.video_path),
                "url": f"https://rohany395-neuro-cue.hf.space/file={self.video_path}",
                "orig_name": "clip.mp4",
            }
        )

        self.assertEqual(path, str(self.video_path.resolve()))
        self.assertEqual(orig_name, "clip.mp4")

    def test_resolve_uploaded_video_path_rejects_non_upload_paths(self):
        with self.assertRaisesRegex(ValueError, "Gradio upload directory"):
            input_validation.resolve_uploaded_video_path(
                {"path": "/etc/passwd", "orig_name": "clip.mp4"}
            )

    def test_resolve_uploaded_video_path_rejects_other_space_hosts(self):
        with self.assertRaisesRegex(ValueError, "configured Hugging Face Space"):
            input_validation.resolve_uploaded_video_path(
                {
                    "path": str(self.video_path),
                    "url": f"https://attacker.hf.space/file={self.video_path}",
                    "orig_name": "clip.mp4",
                }
            )

    def test_resolve_uploaded_video_path_rejects_path_url_mismatch(self):
        other_video = self.upload_dir / "other"
        other_video.write_bytes(b"other")

        with self.assertRaisesRegex(ValueError, "same file"):
            input_validation.resolve_uploaded_video_path(
                {
                    "path": str(self.video_path),
                    "url": f"https://rohany395-neuro-cue.hf.space/file={other_video}",
                    "orig_name": "clip.mp4",
                }
            )

    def test_ensure_video_extension_copies_extensionless_blob(self):
        normalized = Path(
            input_validation.ensure_video_extension(str(self.video_path), "clip.mov")
        )

        self.assertEqual(normalized.suffix, ".mov")
        self.assertTrue(normalized.is_file())
        self.assertEqual(normalized.read_bytes(), b"video")


if __name__ == "__main__":
    unittest.main()
