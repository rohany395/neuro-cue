import tempfile
import unittest
from pathlib import Path

from video_validation import VideoReferenceError, normalize_uploaded_video_path


class VideoValidationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.upload_root = Path(self.tempdir.name) / "gradio"
        self.upload_root.mkdir()
        self.upload = self.upload_root / "session" / "blob"
        self.upload.parent.mkdir()
        self.upload.write_bytes(b"video")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_accepts_file_under_upload_root(self):
        self.assertEqual(
            normalize_uploaded_video_path(
                {"path": str(self.upload), "orig_name": "clip.mp4"},
                upload_root=self.upload_root,
            ),
            str(self.upload.resolve()),
        )

    def test_rejects_file_outside_upload_root(self):
        outside = Path(self.tempdir.name) / "outside.mp4"
        outside.write_bytes(b"video")

        with self.assertRaisesRegex(VideoReferenceError, "Gradio upload"):
            normalize_uploaded_video_path(str(outside), upload_root=self.upload_root)

    def test_rejects_url_path(self):
        with self.assertRaisesRegex(VideoReferenceError, "local upload path"):
            normalize_uploaded_video_path(
                {"path": "https://attacker.example/huge.mp4"},
                upload_root=self.upload_root,
            )

    def test_rejects_symlink_escape(self):
        outside = Path(self.tempdir.name) / "outside.mp4"
        outside.write_bytes(b"video")
        link = self.upload_root / "session" / "link"
        link.symlink_to(outside)

        with self.assertRaisesRegex(VideoReferenceError, "Gradio upload"):
            normalize_uploaded_video_path(str(link), upload_root=self.upload_root)

    def test_rejects_oversized_upload(self):
        with self.assertRaisesRegex(VideoReferenceError, "MB or smaller"):
            normalize_uploaded_video_path(
                str(self.upload),
                upload_root=self.upload_root,
                max_bytes=1,
            )


if __name__ == "__main__":
    unittest.main()
