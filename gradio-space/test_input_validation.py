import tempfile
import unittest
from pathlib import Path

from input_validation import (
    normalize_timestep_limit,
    resolve_uploaded_video_path,
    validate_space_file_url,
)


class InputValidationTests(unittest.TestCase):
    def test_normalize_timestep_limit_caps_and_rejects_invalid_values(self):
        self.assertEqual(normalize_timestep_limit(5), 5)
        self.assertEqual(normalize_timestep_limit("100"), 30)

        for invalid in (0, -1, "abc", None):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    normalize_timestep_limit(invalid)

    def test_resolve_uploaded_video_path_requires_file_under_upload_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            uploaded = root / "session" / "blob"
            uploaded.parent.mkdir()
            uploaded.write_bytes(b"video")

            self.assertEqual(
                resolve_uploaded_video_path({"path": str(uploaded)}, upload_root=root),
                str(uploaded.resolve()),
            )

            with self.assertRaisesRegex(ValueError, "outside the Gradio upload directory"):
                resolve_uploaded_video_path({"path": "/etc/passwd"}, upload_root=root)

            with self.assertRaisesRegex(ValueError, "missing a local path"):
                resolve_uploaded_video_path(
                    {"url": "https://rohany395-neuro-cue.hf.space/gradio_api/file=blob"},
                    upload_root=root,
                )

    def test_resolve_uploaded_video_path_rejects_foreign_space_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            uploaded = root / "session" / "blob"
            uploaded.parent.mkdir()
            uploaded.write_bytes(b"video")

            with self.assertRaisesRegex(ValueError, "configured Hugging Face Space"):
                resolve_uploaded_video_path(
                    {
                        "path": str(uploaded),
                        "url": "https://attacker.hf.space/gradio_api/file=blob",
                    },
                    upload_root=root,
                )

    def test_validate_space_file_url_requires_exact_configured_host(self):
        validate_space_file_url(
            "https://rohany395-neuro-cue.hf.space/gradio_api/file=blob",
        )

        with self.assertRaisesRegex(ValueError, "configured Hugging Face Space"):
            validate_space_file_url("https://other.hf.space/gradio_api/file=blob")


if __name__ == "__main__":
    unittest.main()
