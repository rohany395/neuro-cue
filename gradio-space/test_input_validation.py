import tempfile
import unittest
from pathlib import Path

import input_validation


class InputValidationTest(unittest.TestCase):
    def setUp(self):
        self._old_upload_root = input_validation.UPLOAD_ROOT
        self.temp_dir = tempfile.TemporaryDirectory()
        self.upload_root = Path(self.temp_dir.name) / "gradio"
        self.upload_root.mkdir()
        input_validation.UPLOAD_ROOT = self.upload_root

    def tearDown(self):
        input_validation.UPLOAD_ROOT = self._old_upload_root
        self.temp_dir.cleanup()

    def _upload_file(self, relative_path="abc/blob", content=b"video"):
        path = self.upload_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_normalize_timestep_limit_caps_large_requests(self):
        self.assertEqual(input_validation.normalize_timestep_limit(10), 10)
        self.assertEqual(input_validation.normalize_timestep_limit(10_000), 30)

    def test_normalize_timestep_limit_rejects_invalid_values(self):
        with self.assertRaisesRegex(ValueError, "positive integer"):
            input_validation.normalize_timestep_limit(0)

        with self.assertRaisesRegex(ValueError, "positive integer"):
            input_validation.normalize_timestep_limit("not-a-number")

    def test_resolve_uploaded_video_path_accepts_matching_gradio_path_and_url(self):
        uploaded = self._upload_file()
        file_ref = {
            "path": str(uploaded),
            "url": f"https://rohany395-neuro-cue.hf.space/file={uploaded}",
        }

        self.assertEqual(
            input_validation.resolve_uploaded_video_path(file_ref),
            str(uploaded.resolve()),
        )

    def test_resolve_uploaded_video_path_rejects_path_outside_upload_root(self):
        outside = Path(self.temp_dir.name) / "secret.mp4"
        outside.write_bytes(b"secret")

        with self.assertRaisesRegex(ValueError, "outside the Gradio upload directory"):
            input_validation.resolve_uploaded_video_path({"path": str(outside)})

    def test_resolve_uploaded_video_path_rejects_wrong_space_host(self):
        uploaded = self._upload_file()

        with self.assertRaisesRegex(ValueError, "configured Space"):
            input_validation.resolve_uploaded_video_path(
                {"url": f"https://attacker.hf.space/file={uploaded}"}
            )

    def test_resolve_uploaded_video_path_rejects_mismatched_path_and_url(self):
        uploaded = self._upload_file("abc/blob")
        other = self._upload_file("def/blob")

        with self.assertRaisesRegex(ValueError, "same file"):
            input_validation.resolve_uploaded_video_path(
                {
                    "path": str(uploaded),
                    "url": f"https://rohany395-neuro-cue.hf.space/file={other}",
                }
            )

    def test_ensure_video_extension_uses_original_extension(self):
        uploaded = self._upload_file()
        with_ext = input_validation.ensure_video_extension(str(uploaded), "clip.webm")

        self.assertTrue(with_ext.endswith(".webm"))
        self.assertEqual(Path(with_ext).read_bytes(), b"video")


if __name__ == "__main__":
    unittest.main()
