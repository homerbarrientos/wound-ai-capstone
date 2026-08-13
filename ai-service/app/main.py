import io
import os
import hashlib
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from PIL import Image

from .predictor import Predictor

app = FastAPI(
    title="WoundAI Inference API",
    version="0.1.0",
    description="Research-only wound image classification inference service."
)

predictor = Predictor(
    mode=os.getenv("MODEL_MODE", "mock"),
    model_path=os.getenv("MODEL_PATH", "./models/wound-efficientnet-b0.pt"),
    confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.70")),
)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 8 * 1024 * 1024


class Score(BaseModel):
    category: str
    probability: float


class PredictionResponse(BaseModel):
    predicted_class: str
    confidence: float
    is_uncertain: bool
    scores: List[Score]
    model_name: str
    model_version: str
    model_mode: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_mode": predictor.mode,
        "model_name": predictor.model_name,
        "model_version": predictor.model_version,
    }


@app.post("/v1/predict", response_model=PredictionResponse)
async def predict(image: UploadFile = File(...)):
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only JPG, PNG and WEBP images are accepted.")

    raw = await image.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 8 MB or smaller.")

    try:
        pil_image = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image file.") from exc

    seed = hashlib.sha256(raw).hexdigest()
    return predictor.predict(pil_image, seed=seed)
