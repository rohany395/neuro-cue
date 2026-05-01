from pydantic import BaseModel
from typing import List, Dict


class ROIScore(BaseModel):
    """Engagement score for a single brain region."""
    name: str
    full_name: str
    score: float
    interpretation: str  # "low" / "moderate" / "high"


class TemporalPoint(BaseModel):
    """One point on the engagement-over-time curve."""
    timestep: int
    broca: float
    wernicke: float
    sma: float
    angular: float


class PredictionResponse(BaseModel):
    """Full response from /predict endpoint."""
    stimulus_type: str  # "video" / "audio" / "text"
    duration_seconds: float
    n_timesteps: int
    roi_scores: List[ROIScore]
    temporal_curves: List[TemporalPoint]
    recommendation: str
    is_mock: bool  # flag for development