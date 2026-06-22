import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

from input_validation import (
    MAX_TIMESTEPS,
    normalize_timestep_limit,
    resolve_uploaded_video_path,
)


class InputValidationTest(unittest.TestCase):
    def test_caps_timestep_limit(self):
        self.assertEqual(normalize_timestep_limit(100), MAX_TIMESTEPS)
        self.assertEqual(normalize_timestep_limit("7"), 7)

    def test_rejects_invalid_timestep_limit(self):
        with self.assertRaises(ValueError):
            normalize_timestep_limit(0)

    def test_accepts_file_under_gradio_upload_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            upload_root = Path(tmpdir)
            uploaded = upload_root / "session" / "blob"
            uploaded.parent.mkdir()
            uploaded.write_bytes(b"video")

            resolved, orig_name = resolve_uploaded_video_path(
                {"path": str(uploaded), "orig_name": "clip.mp4"},
                upload_root=upload_root,
            )

            self.assertEqual(resolved, str(uploaded.resolve()))
            self.assertEqual(orig_name, "clip.mp4")

    def test_rejects_paths_outside_gradio_upload_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            outside = Path(tmpdir) / "outside.mp4"
            outside.write_bytes(b"video")
            upload_root = Path(tmpdir) / "uploads"
            upload_root.mkdir()

            with self.assertRaises(ValueError):
                resolve_uploaded_video_path({"path": str(outside)}, upload_root=upload_root)

    def test_rejects_url_for_different_space_host(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            upload_root = Path(tmpdir)
            uploaded = upload_root / "blob"
            uploaded.write_bytes(b"video")

            with self.assertRaises(ValueError):
                resolve_uploaded_video_path(
                    {
                        "path": str(uploaded),
                        "url": f"https://attacker.hf.space/file={quote(str(uploaded))}",
                    },
                    upload_root=upload_root,
                )

    def test_rejects_mismatched_path_and_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            upload_root = Path(tmpdir)
            uploaded = upload_root / "blob"
            other = upload_root / "other"
            uploaded.write_bytes(b"video")
            other.write_bytes(b"video")

            with self.assertRaises(ValueError):
                resolve_uploaded_video_path(
                    {
                        "path": str(uploaded),
                        "url": "https://rohany395-neuro-cue.hf.space"
                        f"/file={quote(str(other))}",
                    },
                    upload_root=upload_root,
                )


if __name__ == "__main__":
    unittest.main()
