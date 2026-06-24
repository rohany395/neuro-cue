import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from input_validation import (
    extension_for_video_path,
    normalize_timestep_limit,
    resolve_uploaded_video_path,
    validate_text_input,
)


class InputValidationTest(unittest.TestCase):
    def test_normalize_timestep_limit_caps_large_values(self):
        self.assertEqual(normalize_timestep_limit(500), 30)
        self.assertEqual(normalize_timestep_limit("5"), 5)

        with self.assertRaisesRegex(ValueError, "positive integer"):
            normalize_timestep_limit(0)

    def test_validate_text_input_rejects_empty_and_oversized_text(self):
        self.assertEqual(validate_text_input("  hello  "), "hello")

        with self.assertRaisesRegex(ValueError, "required"):
            validate_text_input("   ")

        with self.assertRaisesRegex(ValueError, "5000"):
            validate_text_input("a" * 5001)

    def test_resolve_uploaded_video_path_accepts_matching_path_and_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            upload_root = Path(tmp)
            upload_dir = upload_root / "abc"
            upload_dir.mkdir()
            upload = upload_dir / "blob"
            upload.write_bytes(b"video")
            url = f"https://rohany395-neuro-cue.hf.space/file={upload}"

            resolved, orig_name = resolve_uploaded_video_path(
                {"path": str(upload), "url": url, "orig_name": "clip.mov"},
                upload_root=upload_root,
            )

            self.assertEqual(resolved, str(upload.resolve()))
            self.assertEqual(orig_name, "clip.mov")

    def test_resolve_uploaded_video_path_rejects_outside_upload_root(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.NamedTemporaryFile() as outside:
            upload_root = Path(tmp)

            with self.assertRaisesRegex(ValueError, "inside the Gradio upload directory"):
                resolve_uploaded_video_path(outside.name, upload_root=upload_root)

    def test_resolve_uploaded_video_path_rejects_other_space_hosts(self):
        with tempfile.TemporaryDirectory() as tmp:
            upload_root = Path(tmp)
            upload = upload_root / "blob"
            upload.write_bytes(b"video")

            with self.assertRaisesRegex(ValueError, "configured Hugging Face Space"):
                resolve_uploaded_video_path(
                    {"url": f"https://attacker-space.hf.space/file={upload}"},
                    upload_root=upload_root,
                )

    def test_resolve_uploaded_video_path_rejects_path_url_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            upload_root = Path(tmp)
            first = upload_root / "first"
            second = upload_root / "second"
            first.write_bytes(b"first")
            second.write_bytes(b"second")

            with self.assertRaisesRegex(ValueError, "same upload"):
                resolve_uploaded_video_path(
                    {
                        "path": str(first),
                        "url": f"https://rohany395-neuro-cue.hf.space/file={second}",
                    },
                    upload_root=upload_root,
                )

    def test_resolve_uploaded_video_path_honors_configured_space_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            upload_root = Path(tmp)
            upload = upload_root / "blob"
            upload.write_bytes(b"video")

            with patch.dict("os.environ", {"HF_SPACE_URL": "https://custom-space.hf.space/"}):
                resolved, _ = resolve_uploaded_video_path(
                    {"url": f"https://custom-space.hf.space/file={upload}"},
                    upload_root=upload_root,
                )
                with self.assertRaisesRegex(ValueError, "configured Hugging Face Space"):
                    resolve_uploaded_video_path(
                        {"url": f"https://rohany395-neuro-cue.hf.space/file={upload}"},
                        upload_root=upload_root,
                    )

            self.assertEqual(resolved, str(upload.resolve()))

    def test_extension_for_video_path_uses_safe_original_extension(self):
        self.assertEqual(extension_for_video_path("/tmp/gradio/abc/blob", "clip.webm"), ".webm")
        self.assertEqual(extension_for_video_path("/tmp/gradio/abc/blob", "clip.exe"), ".mp4")
        self.assertEqual(extension_for_video_path("/tmp/gradio/abc/clip.mp4", None), "")


if __name__ == "__main__":
    unittest.main()
