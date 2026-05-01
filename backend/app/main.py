import tempfile
import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import PredictionResponse, ROIScore, TemporalPoint
from app.roi_mapping import ROIMapper, ROI_DEFINITIONS
from app.inference import InferenceEngine, USE_MOCK


app = FastAPI(
    title="Resonate API",
    description="Predict brain engagement for speech therapy stimuli",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize once at startup (avoids reloading the atlas on every request)
print("=" * 60)
print("Starting Resonate API")
print("=" * 60)
roi_mapper = ROIMapper()
inference_engine = InferenceEngine()
print("=" * 60)
print("✅ Ready")
print("=" * 60)


SUPPORTED_TYPES = {
    "video/mp4": "video",
    "video/quicktime": "video",
    "audio/mpeg": "audio",
    "audio/wav": "audio",
    "audio/x-wav": "audio",
    "text/plain": "text",
}


def make_recommendation(scores: dict) -> str:
    """Turn raw scores into a clinical-sounding recommendation."""
    top_roi = max(scores, key=scores.get)
    top_score = scores[top_roi]
    full_name = ROI_DEFINITIONS[top_roi]["full_name"]
    function = ROI_DEFINITIONS[top_roi]["function"]
    interp = ROIMapper.interpret(top_score)

    if interp == "high":
        return (
            f"Strong activation in {full_name} ({function}). "
            f"Recommended for therapy targeting this region."
        )
    elif interp == "moderate":
        return (
            f"Moderate activation across language regions, "
            f"strongest in {full_name}. May be a good warmup stimulus."
        )
    return (
        "Low activation across language regions. "
        "Consider a more linguistically rich stimulus."
    )


@app.get("/")
def root():
    return {"name": "Resonate API", "status": "running", "mock_mode": USE_MOCK}


@app.get("/health")
def health():
    return {"status": "healthy", "mock_mode": USE_MOCK}


@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}",
        )
    stimulus_type = SUPPORTED_TYPES[file.content_type]

    # Save upload to a temp file
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # Run inference
        preds, duration = inference_engine.predict(tmp_path, stimulus_type)

        # Compute ROI scores + curves
        scores = roi_mapper.compute_scores(preds)
        curves = roi_mapper.compute_temporal_curves(preds)

        # Format ROI scores for response
        roi_scores = [
            ROIScore(
                name=name,
                full_name=ROI_DEFINITIONS[name]["full_name"],
                score=score,
                interpretation=ROIMapper.interpret(score),
            )
            for name, score in scores.items()
        ]

        # Format temporal curves for response
        n_steps = preds.shape[0]
        temporal_points = [
            TemporalPoint(
                timestep=t,
                broca=curves["broca"][t],
                wernicke=curves["wernicke"][t],
                sma=curves["sma"][t],
                angular=curves["angular"][t],
            )
            for t in range(n_steps)
        ]

        return PredictionResponse(
            stimulus_type=stimulus_type,
            duration_seconds=duration,
            n_timesteps=n_steps,
            roi_scores=roi_scores,
            temporal_curves=temporal_points,
            recommendation=make_recommendation(scores),
            is_mock=USE_MOCK,
        )
    finally:
        os.unlink(tmp_path)