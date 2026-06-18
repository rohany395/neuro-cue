import tempfile
import unittest
from pathlib import Path

from input_validation import (
    InputValidationError,
    normalize_timestep_limit,
    resolve_uploaded_video_path,
)


SPACE_URL = "https://rohany395-neuro-cue.hf.space/"


class InputValidationTest(unittest.TestCase):
    def test_normalize_timestep_limit_caps_public_requests(self):
        self.assertEqual(normalize_timestep_limit(999), 30)
        self.assertEqual(normalize_timestep_limit("2"), 2)

    def test_normalize_timestep_limit_rejects_nonpositive_values(self):
        with self.assertRaises(InputValidationError):
            normalize_timestep_limit(0)

    def test_resolve_uploaded_video_path_accepts_matching_gradio_upload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            upload_root = Path(tmpdir)
            upload = upload_root / "session" / "blob"
            upload.parent.mkdir()
            upload.write_bytes(b"video")
            url = f"https://rohany395-neuro-cue.hf.space/file={upload}"

            path, orig_name = resolve_uploaded_video_path(
                {"path": str(upload), "url": url, "orig_name": "clip.webm"},
                upload_root=upload_root,
                space_url=SPACE_URL,
            )

        self.assertEqual(path, str(upload.resolve()))
        self.assertEqual(orig_name, "clip.webm")

    def test_resolve_uploaded_video_path_rejects_paths_outside_upload_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            upload_root = Path(tmpdir)
            outside = Path(tempfile.NamedTemporaryFile(delete=False).name)
            self.addCleanup(lambda: outside.unlink(missing_ok=True))

            with self.assertRaises(InputValidationError):
                resolve_uploaded_video_path(
                    {"path": str(outside)},
                    upload_root=upload_root,
                    space_url=SPACE_URL,
                )

    def test_resolve_uploaded_video_path_rejects_wrong_file_url_host(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            upload_root = Path(tmpdir)
            upload = upload_root / "blob"
            upload.write_bytes(b"video")

            with self.assertRaises(InputValidationError):
                resolve_uploaded_video_path(
                    {
                        "path": str(upload),
                        "url": f"https://attacker.hf.space/file={upload}",
                    },
                    upload_root=upload_root,
                    space_url=SPACE_URL,
                )

    def test_resolve_uploaded_video_path_rejects_mismatched_path_and_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            upload_root = Path(tmpdir)
            path_upload = upload_root / "path_blob"
            url_upload = upload_root / "url_blob"
            path_upload.write_bytes(b"path")
            url_upload.write_bytes(b"url")

            with self.assertRaises(InputValidationError):
                resolve_uploaded_video_path(
                    {
                        "path": str(path_upload),
                        "url": f"https://rohany395-neuro-cue.hf.space/file={url_upload}",
                    },
                    upload_root=upload_root,
                    space_url=SPACE_URL,
                )


if __name__ == "__main__":
    unittest.main()
