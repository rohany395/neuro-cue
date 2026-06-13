import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

from input_validation import (
    MAX_TEXT_CHARS,
    MAX_TIMESTEPS,
    ensure_video_extension,
    normalize_timestep_limit,
    resolve_uploaded_video_path,
    validate_text_input,
)


class InputValidationTest(unittest.TestCase):
    def setUp(self):
        Path("/tmp/gradio").mkdir(parents=True, exist_ok=True)
        self.upload_dir = Path(tempfile.mkdtemp(prefix="neuro-cue-", dir="/tmp/gradio"))
        self.upload = self.upload_dir / "blob"
        self.upload.write_bytes(b"video")

    def tearDown(self):
        shutil.rmtree(self.upload_dir)

    def test_timestep_limit_is_capped(self):
        self.assertEqual(normalize_timestep_limit(1), 1)
        self.assertEqual(normalize_timestep_limit(10), 10)
        self.assertEqual(normalize_timestep_limit(10_000), MAX_TIMESTEPS)

    def test_timestep_limit_rejects_invalid_values(self):
        for value in (0, -1, "abc", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_timestep_limit(value)

    def test_text_validation_caps_public_input_size(self):
        self.assertEqual(validate_text_input(" hello "), "hello")
        with self.assertRaises(ValueError):
            validate_text_input("x" * (MAX_TEXT_CHARS + 1))

    def test_video_path_must_resolve_under_gradio_upload_root(self):
        with self.assertRaises(ValueError):
            resolve_uploaded_video_path({"path": "/etc/passwd", "orig_name": "passwd.mp4"})

    def test_video_url_and_path_must_match_same_upload(self):
        other_upload = self.upload_dir / "other"
        other_upload.write_bytes(b"other")

        with self.assertRaises(ValueError):
            resolve_uploaded_video_path({
                "path": str(self.upload),
                "url": f"/file={quote(str(other_upload))}",
                "orig_name": "clip.mp4",
            })

    def test_extensionless_upload_is_copied_with_safe_suffix(self):
        resolved, orig_name = resolve_uploaded_video_path({
            "path": str(self.upload),
            "url": f"/file={quote(str(self.upload))}",
            "orig_name": "clip.mov",
        })
        normalized = ensure_video_extension(resolved, orig_name)

        self.assertTrue(normalized.endswith(".mov"))
        self.assertTrue(Path(normalized).is_file())
        self.assertEqual(Path(normalized).read_bytes(), b"video")


if __name__ == "__main__":
    unittest.main()
