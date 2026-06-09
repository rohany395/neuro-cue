import tempfile
import unittest
from pathlib import Path

from input_validation import (
    MAX_TIMESTEPS,
    ensure_video_extension,
    normalize_timestep_limit,
    resolve_uploaded_video_path,
)


class InputValidationTest(unittest.TestCase):
    def test_normalize_timestep_limit_clamps_large_values(self):
        self.assertEqual(normalize_timestep_limit(MAX_TIMESTEPS + 500), MAX_TIMESTEPS)

    def test_normalize_timestep_limit_rejects_non_positive_values(self):
        with self.assertRaises(ValueError):
            normalize_timestep_limit(0)

    def test_resolve_uploaded_video_path_accepts_file_under_upload_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            uploaded = root / "session" / "blob"
            uploaded.parent.mkdir()
            uploaded.write_bytes(b"video")

            path, orig_name = resolve_uploaded_video_path(
                {"path": str(uploaded), "orig_name": "clip.webm"},
                upload_root=root,
            )

            self.assertEqual(path, str(uploaded.resolve()))
            self.assertEqual(orig_name, "clip.webm")

    def test_resolve_uploaded_video_path_rejects_url_only_reference(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                resolve_uploaded_video_path(
                    {"url": "https://example.com/clip.mp4"},
                    upload_root=tmpdir,
                )

    def test_resolve_uploaded_video_path_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            outside = Path(tmpdir).parent / "outside.mp4"
            outside.write_bytes(b"video")
            try:
                with self.assertRaises(ValueError):
                    resolve_uploaded_video_path(
                        {"path": str(outside)},
                        upload_root=Path(tmpdir) / "uploads",
                    )
            finally:
                outside.unlink()

    def test_ensure_video_extension_uses_safe_original_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            uploaded = Path(tmpdir) / "blob"
            uploaded.write_bytes(b"video")

            path = ensure_video_extension(str(uploaded), "clip.mov")

            self.assertEqual(Path(path).suffix, ".mov")
            self.assertEqual(Path(path).read_bytes(), b"video")


if __name__ == "__main__":
    unittest.main()
