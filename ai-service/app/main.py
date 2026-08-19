import base64
import hashlib
import io
import os
from io import BytesIO
from typing import List, Optional

import torch
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

from .predictor import Predictor
from .wound_type_predictor import WoundTypePredictor


load_dotenv()

TORCH_NUM_THREADS = max(
    1,
    int(os.getenv("TORCH_NUM_THREADS", "2")),
)

torch.set_num_threads(TORCH_NUM_THREADS)
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

print(
    f"PyTorch CPU threads: {torch.get_num_threads()}, "
    f"interop threads: {torch.get_num_interop_threads()}",
    flush=True,
)


MODEL_MODE = os.getenv(
    "MODEL_MODE",
    "torch",
)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "./models/wound-efficientnet-b0-binary.pt",
)

CONFIDENCE_THRESHOLD = float(
    os.getenv(
        "CONFIDENCE_THRESHOLD",
        "0.70",
    )
)

WOUND_TYPE_MODEL_PATH = os.getenv(
    "WOUND_TYPE_MODEL_PATH",
    "./models/wound-type-efficientnet-b0-v1.pt",
)

WOUND_TYPE_CONFIDENCE_THRESHOLD = float(
    os.getenv(
        "WOUND_TYPE_CONFIDENCE_THRESHOLD",
        "0.60",
    )
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000",
    ).split(",")
    if origin.strip()
]


predictor = Predictor(
    mode=MODEL_MODE,
    model_path=MODEL_PATH,
    confidence_threshold=CONFIDENCE_THRESHOLD,
)

wound_type_predictor = WoundTypePredictor(
    model_path=WOUND_TYPE_MODEL_PATH,
    confidence_threshold=WOUND_TYPE_CONFIDENCE_THRESHOLD,
)


app = FastAPI(
    title="WoundAI Inference API",
    version="1.0.0",
    description=(
        "Research-only wound image classification "
        "inference service."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

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

    wound_type: Optional[str] = None
    wound_type_confidence: Optional[float] = None
    wound_type_uncertain: Optional[bool] = None
    wound_type_scores: Optional[List[Score]] = None
    wound_type_model_name: Optional[str] = None
    wound_type_model_version: Optional[str] = None

    gradcam_image_base64: Optional[str] = None


@app.get("/")
def root():
    return {
        "service": "WoundAI Inference API",
        "version": "1.0.0",
        "status": "running",
        "usage": "Research and decision-support only",
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_mode": predictor.mode,
        "binary_model": {
            "name": predictor.model_name,
            "version": predictor.model_version,
            "file": os.path.basename(MODEL_PATH),
            "confidence_threshold": CONFIDENCE_THRESHOLD,
        },
        "wound_type_model": {
            "file": os.path.basename(
                WOUND_TYPE_MODEL_PATH
            ),
            "confidence_threshold": (
                WOUND_TYPE_CONFIDENCE_THRESHOLD
            ),
            "classes": [
                "diabetic",
                "pressure",
                "surgical",
                "venous",
            ],
        },
    }


@app.post(
    "/v1/predict",
    response_model=PredictionResponse,
)
async def predict(
    image: UploadFile = File(...),
    include_gradcam: bool = False,
):
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                "Only JPG, PNG and WEBP images "
                "are accepted."
            ),
        )

    raw = await image.read()

    if len(raw) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Image must be 8 MB or smaller.",
        )

    try:
        pil_image = Image.open(
            io.BytesIO(raw)
        ).convert("RGB")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file.",
        ) from exc

    seed = hashlib.sha256(raw).hexdigest()

    result = predictor.predict(
        pil_image,
        seed=seed,
    )

    if (
        result["predicted_class"] == "Wound"
        and not result["is_uncertain"]
    ):
        if include_gradcam:
            wound_type_result, gradcam_image = (
                wound_type_predictor.predict_with_gradcam(
                    pil_image
                )
            )
        else:
            wound_type_result = wound_type_predictor.predict(
                pil_image
            )

        result.update(wound_type_result)

    if include_gradcam and result.get("wound_type"):
        buffer = BytesIO()

        gradcam_image.save(
            buffer,
            format="JPEG",
            quality=90,
        )

        gradcam_base64 = base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

        result["gradcam_image_base64"] = (
            gradcam_base64
        )

    return result