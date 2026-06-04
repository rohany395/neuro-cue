import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from video_validation import validate_video_reference


SPACE_URL = "https://rohany395-neuro-cue.hf.space"


class VideoValidationTest(unittest.TestCase):
    def setUp(self):
        self.upload_root = Path("/tmp/gradio")
        self.upload_root.mkdir(parents=True, exist_ok=True)
        self.upload_dir = Path(tempfile.mkdtemp(dir=self.upload_root))
        self.video_path = self.upload_dir / "blob"
        self.video_path.write_bytes(b"video")

    def test_accepts_configured_space_upload_reference(self):
        path, orig_name = validate_video_reference({
            "path": str(self.video_path),
            "url": f"{SPACE_URL}/file={self.video_path}",
            "orig_name": "sample.mp4",
        })

        self.assertEqual(path, str(self.video_path.resolve()))
        self.assertEqual(orig_name, "sample.mp4")

    def test_rejects_path_traversal_outside_upload_root(self):
        with self.assertRaisesRegex(ValueError, "Hugging Face upload"):
            validate_video_reference({"path": "/tmp/gradio/../../etc/passwd"})

    def test_rejects_foreign_space_url(self):
        with self.assertRaisesRegex(ValueError, "configured Hugging Face Space"):
            validate_video_reference({
                "url": f"https://attacker-space.hf.space/file={self.video_path}",
            })

    def test_rejects_mismatched_path_and_url(self):
        other = self.upload_dir / "other"
        other.write_bytes(b"video")

        with self.assertRaisesRegex(ValueError, "do not reference the same upload"):
            validate_video_reference({
                "path": str(self.video_path),
                "url": f"{SPACE_URL}/file={other}",
            })

    def test_rejects_symlink_to_file_outside_upload_root(self):
        outside_fd, outside_path = tempfile.mkstemp()
        os.close(outside_fd)
        link_path = self.upload_dir / "link"
        link_path.symlink_to(outside_path)
        self.addCleanup(lambda: os.path.exists(outside_path) and os.unlink(outside_path))

        with self.assertRaisesRegex(ValueError, "Hugging Face upload"):
            validate_video_reference({"path": str(link_path)})


if __name__ == "__main__":
    unittest.main()
