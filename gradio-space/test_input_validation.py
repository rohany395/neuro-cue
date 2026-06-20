import tempfile
import unittest
from pathlib import Path

from input_validation import normalize_timestep_limit, resolve_uploaded_video_path


class InputValidationTests(unittest.TestCase):
    def test_timestep_limit_is_capped(self):
        self.assertEqual(normalize_timestep_limit(100), 30)

    def test_timestep_limit_rejects_non_positive_values(self):
        with self.assertRaisesRegex(ValueError, "positive integer"):
            normalize_timestep_limit(0)

    def test_resolves_existing_upload_path_under_root(self):
        with tempfile.TemporaryDirectory() as root:
            video_path = Path(root) / "upload" / "blob"
            video_path.parent.mkdir()
            video_path.write_bytes(b"video")

            resolved = resolve_uploaded_video_path({"path": str(video_path)}, upload_root=root)

        self.assertEqual(resolved, str(video_path.resolve()))

    def test_rejects_path_outside_upload_root(self):
        with tempfile.TemporaryDirectory() as root:
            with tempfile.NamedTemporaryFile() as outside:
                with self.assertRaisesRegex(ValueError, "Gradio upload directory"):
                    resolve_uploaded_video_path({"path": outside.name}, upload_root=root)

    def test_rejects_mismatched_path_and_url(self):
        with tempfile.TemporaryDirectory() as root:
            first = Path(root) / "first" / "blob"
            second = Path(root) / "second" / "blob"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_bytes(b"one")
            second.write_bytes(b"two")

            with self.assertRaisesRegex(ValueError, "different uploaded files"):
                resolve_uploaded_video_path(
                    {
                        "path": str(first),
                        "url": f"https://rohany395-neuro-cue.hf.space/file={second}",
                    },
                    upload_root=root,
                )

    def test_rejects_file_url_from_unconfigured_space(self):
        with tempfile.TemporaryDirectory() as root:
            video_path = Path(root) / "blob"
            video_path.write_bytes(b"video")

            with self.assertRaisesRegex(ValueError, "configured Hugging Face Space"):
                resolve_uploaded_video_path(
                    {"url": f"https://attacker.hf.space/file={video_path}"},
                    upload_root=root,
                )


if __name__ == "__main__":
    unittest.main()
