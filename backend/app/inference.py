"""
TRIBE v2 inference wrapper.

Supports two modes:
- USE_MOCK=True: returns fake predictions (for local dev without GPU)
- USE_MOCK=False: runs real TRIBE v2 (for deployment)
"""
import os
import numpy as np

# Toggle this with an env var. Default = mock mode for local dev.
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


class InferenceEngine:
    def __init__(self):
        self.model = None
        if USE_MOCK:
            print("🎭 Running in MOCK mode — no real TRIBE v2 inference")
        else:
            print("🧠 Loading real TRIBE v2 model...")
            from tribev2 import TribeModel
            self.model = TribeModel.from_pretrained(
                "facebook/tribev2", cache_folder="./cache"
            )
            print("✅ TRIBE v2 loaded")

    def predict(self, file_path: str, stimulus_type: str) -> tuple:
        """
        Run inference and return (preds, duration_seconds).

        preds: numpy array of shape (n_timesteps, n_vertices)
        """
        if USE_MOCK:
            return self._mock_predict(stimulus_type)
        return self._real_predict(file_path, stimulus_type)

    def _mock_predict(self, stimulus_type: str) -> tuple:
        """Generate plausible-looking fake predictions."""
        n_timesteps = np.random.randint(15, 30)
        n_vertices = 20484
        # Random Gaussian noise centered at zero, mimics BOLD signal range
        preds = np.random.randn(n_timesteps, n_vertices) * 0.3
        duration = n_timesteps * 1.5  # assume TR=1.5s
        return preds, duration

    def _real_predict(self, file_path: str, stimulus_type: str) -> tuple:
        """Real TRIBE v2 inference."""
        import torch

        if stimulus_type == "video":
            df = self.model.get_events_dataframe(video_path=file_path)
        elif stimulus_type == "audio":
            df = self.model.get_events_dataframe(audio_path=file_path)
        else:  # text
            df = self.model.get_events_dataframe(text_path=file_path)

        with torch.no_grad():
            preds, _ = self.model.predict(events=df)

        if hasattr(preds, "cpu"):  # convert torch tensor → numpy
            preds = preds.cpu().numpy()

        duration = preds.shape[0] * 1.5
        return preds, duration