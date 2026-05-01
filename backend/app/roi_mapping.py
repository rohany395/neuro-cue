"""
ROI mapping logic — port of the Colab atlas work from Step 4.
Translates TRIBE v2's vertex-level predictions into clinically
meaningful per-region engagement scores.
"""
import numpy as np
from nilearn import datasets


# Clinical ROI definitions (from Step 4)
ROI_DEFINITIONS = {
    "broca": {
        "full_name": "Broca's Area",
        "function": "Speech production",
        "destrieux_labels": ["G_front_inf-Triangul", "G_front_inf-Opercular"],
    },
    "wernicke": {
        "full_name": "Wernicke's Area",
        "function": "Language comprehension",
        "destrieux_labels": ["G_temp_sup-Plan_tempo", "G_temporal_middle"],
    },
    "sma": {
        "full_name": "Supplementary Motor Area",
        "function": "Speech motor planning",
        "destrieux_labels": ["G_and_S_paracentral"],
    },
    "angular": {
        "full_name": "Angular Gyrus",
        "function": "Semantic processing",
        "destrieux_labels": ["G_pariet_inf-Angular"],
    },
}


class ROIMapper:
    """Loads the Destrieux atlas once and computes ROI scores."""

    def __init__(self):
        print("Loading Destrieux atlas...")
        atlas = datasets.fetch_atlas_surf_destrieux()
        labels = [
            l.decode() if isinstance(l, bytes) else l
            for l in atlas["labels"]
        ]
        self.map_left = atlas["map_left"]
        self.map_right = atlas["map_right"]
        self.n_left = len(self.map_left)
        self.n_total = self.n_left + len(self.map_right)

        # Build a boolean mask per ROI
        self.roi_masks = {}
        for roi_name, roi_info in ROI_DEFINITIONS.items():
            mask = np.zeros(self.n_total, dtype=bool)
            for label_name in roi_info["destrieux_labels"]:
                if label_name in labels:
                    label_idx = labels.index(label_name)
                    mask[: self.n_left] |= self.map_left == label_idx
                else:
                    print(f"⚠️  Label '{label_name}' not found in atlas")
            self.roi_masks[roi_name] = mask
            print(f"  {roi_name}: {mask.sum()} vertices")

    def compute_scores(self, preds: np.ndarray) -> dict:
        """
        preds: shape (n_timesteps, n_vertices)
        returns: dict of roi_name -> mean score
        """
        return {
            roi: float(preds[:, mask].mean())
            for roi, mask in self.roi_masks.items()
        }

    def compute_temporal_curves(self, preds: np.ndarray) -> dict:
        """
        Per-ROI time series.
        returns: dict of roi_name -> 1D array of length n_timesteps
        """
        return {
            roi: preds[:, mask].mean(axis=1).tolist()
            for roi, mask in self.roi_masks.items()
        }

    @staticmethod
    def interpret(score: float) -> str:
        """Translate a raw score into a clinical interpretation level."""
        if score > 0.5:
            return "high"
        elif score > 0.2:
            return "moderate"
        else:
            return "low"