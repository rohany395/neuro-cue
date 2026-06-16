import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "input_validation.py"
SPEC = importlib.util.spec_from_file_location("input_validation", MODULE_PATH)
input_validation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(input_validation)


class InputValidationTest(unittest.TestCase):
    def setUp(self):
        self.original_upload_root = input_validation.UPLOAD_ROOT
        self.original_space_url = os.environ.get("HF_SPACE_URL")

    def tearDown(self):
        input_validation.UPLOAD_ROOT = self.original_upload_root
        if self.original_space_url is None:
            os.environ.pop("HF_SPACE_URL", None)
        else:
            os.environ["HF_SPACE_URL"] = self.original_space_url

    def test_normalize_timestep_limit_caps_public_requests(self):
        self.assertEqual(input_validation.normalize_timestep_limit(999), 30)
        self.assertEqual(input_validation.normalize_timestep_limit("0"), 1)
        self.assertEqual(input_validation.normalize_timestep_limit("bad"), 10)

    def test_resolve_uploaded_video_path_rejects_non_upload_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_validation.UPLOAD_ROOT = Path(tmp).resolve()
            outside = Path(tmp).parent / "secret.mp4"
            outside.write_text("not a real video", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "upload directory"):
                input_validation.resolve_uploaded_video_path({"path": str(outside)})

    def test_resolve_uploaded_video_path_requires_configured_space_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_validation.UPLOAD_ROOT = Path(tmp).resolve()
            uploaded = Path(tmp) / "blob"
            uploaded.write_text("not a real video", encoding="utf-8")
            os.environ["HF_SPACE_URL"] = "https://rohany395-neuro-cue.hf.space/"

            with self.assertRaisesRegex(ValueError, "configured Hugging Face Space"):
                input_validation.resolve_uploaded_video_path({
                    "url": f"https://attacker.hf.space/file={uploaded}",
                })

    def test_resolve_uploaded_video_path_accepts_matching_gradio_upload_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_validation.UPLOAD_ROOT = Path(tmp).resolve()
            uploaded = Path(tmp) / "blob"
            uploaded.write_text("not a real video", encoding="utf-8")
            os.environ["HF_SPACE_URL"] = "https://rohany395-neuro-cue.hf.space/"

            path, orig_name = input_validation.resolve_uploaded_video_path({
                "path": str(uploaded),
                "url": f"https://rohany395-neuro-cue.hf.space/file={uploaded}",
                "orig_name": "stimulus.mp4",
            })

            self.assertEqual(path, str(uploaded.resolve()))
            self.assertEqual(orig_name, "stimulus.mp4")


if __name__ == "__main__":
    unittest.main()
