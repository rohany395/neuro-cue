import shutil
import tempfile
import unittest
from pathlib import Path

from input_validation import (
    MAX_TIMESTEPS,
    normalize_timestep_limit,
    resolve_uploaded_video_path,
    video_extension_for,
)


class InputValidationTest(unittest.TestCase):
    def setUp(self):
        Path("/tmp/gradio").mkdir(parents=True, exist_ok=True)
        self.upload_dir = Path(tempfile.mkdtemp(dir="/tmp/gradio"))
        self.upload_path = self.upload_dir / "blob"
        self.upload_path.write_bytes(b"video")

    def tearDown(self):
        shutil.rmtree(self.upload_dir, ignore_errors=True)

    def test_resolves_gradio_upload_path(self):
        resolved, orig_name = resolve_uploaded_video_path(
            {"path": str(self.upload_path), "orig_name": "clip.mov"}
        )

        self.assertEqual(resolved, str(self.upload_path.resolve()))
        self.assertEqual(orig_name, "clip.mov")
        self.assertEqual(video_extension_for(resolved, orig_name), ".mov")

    def test_rejects_paths_outside_gradio_upload_root(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            resolve_uploaded_video_path({"path": "/etc/passwd", "orig_name": "clip.mp4"})

    def test_rejects_orig_name_as_path(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            resolve_uploaded_video_path({"orig_name": str(self.upload_path)})

    def test_rejects_mismatched_file_url_host(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            resolve_uploaded_video_path(
                {
                    "path": str(self.upload_path),
                    "url": f"https://attacker.hf.space/file={self.upload_path}",
                    "orig_name": "clip.mp4",
                }
            )

    def test_rejects_path_url_mismatch(self):
        other_path = self.upload_dir / "other"
        other_path.write_bytes(b"other")

        with self.assertRaisesRegex(ValueError, "invalid"):
            resolve_uploaded_video_path(
                {
                    "path": str(self.upload_path),
                    "url": f"https://rohany395-neuro-cue.hf.space/file={other_path}",
                    "orig_name": "clip.mp4",
                }
            )

    def test_timestep_limit_is_capped(self):
        self.assertEqual(normalize_timestep_limit(1000), MAX_TIMESTEPS)

        with self.assertRaisesRegex(ValueError, "positive integer"):
            normalize_timestep_limit(0)


if __name__ == "__main__":
    unittest.main()
