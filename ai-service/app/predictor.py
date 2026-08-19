from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Dict

from PIL import Image

CLASSES = ["normal", "wound"]


class Predictor:
    def __init__(self, mode: str, model_path: str, confidence_threshold: float = 0.70):
        self.mode = mode
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.model_name = "EfficientNet-B0"
        self.model_version = "mock-v0.1" if mode == "mock" else "binary-v1"
        self.model = None
        self.transform = None

        if self.mode == "torch":
            self._load_torch_model()

    def _load_torch_model(self):
        import torch
        from torch import nn
        from torchvision import transforms
        from torchvision.models import efficientnet_b0

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"MODEL_MODE=torch but weights were not found at {self.model_path.resolve()}"
            )

        model = efficientnet_b0(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, len(CLASSES))

        checkpoint = torch.load(self.model_path, map_location="cpu")

        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
            checkpoint_classes = checkpoint.get("classes")

            if checkpoint_classes and list(checkpoint_classes) != CLASSES:
                raise ValueError(
                    "Checkpoint class order does not match predictor. "
                    f"Checkpoint={checkpoint_classes}, Predictor={CLASSES}"
                )

            self.model_version = checkpoint.get("model_version", "binary-v1")
        else:
            state_dict = checkpoint

        model.load_state_dict(state_dict)
        model.eval()

        self.model = model
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        print(
            f"Loaded {self.model_name} {self.model_version} from "
            f"{self.model_path.resolve()}"
        )

    def _mock_predict(self, seed: str) -> Dict:
        rnd = random.Random(int(seed[:16], 16))
        logits = [rnd.uniform(-0.5, 1.5) for _ in CLASSES]
        exps = [math.exp(v) for v in logits]
        total = sum(exps)
        probs = [v / total for v in exps]
        ranked = sorted(zip(CLASSES, probs), key=lambda x: x[1], reverse=True)
        category, confidence = ranked[0]
        return self._response(category, confidence, ranked)

    def _torch_predict(self, image: Image.Image) -> Dict:
        import torch

        assert self.model is not None and self.transform is not None

        image = image.convert("RGB")
        x = self.transform(image).unsqueeze(0)

        with torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=1)[0].tolist()

        ranked = sorted(zip(CLASSES, probs), key=lambda x: x[1], reverse=True)
        category, confidence = ranked[0]
        return self._response(category, confidence, ranked)

    def _response(self, category: str, confidence: float, ranked) -> Dict:
        uncertain = confidence < self.confidence_threshold

        return {
            "predicted_class": category.title(),
            "confidence": float(confidence),
            "is_uncertain": uncertain,
            "scores": [
                {"category": name.title(), "probability": float(prob)}
                for name, prob in ranked
            ],
            "model_name": self.model_name,
            "model_version": self.model_version,
            "model_mode": self.mode,
        }

    def predict(self, image: Image.Image, seed: str) -> Dict:
        if self.mode == "mock":
            return self._mock_predict(seed)
        if self.mode == "torch":
            return self._torch_predict(image)
        raise ValueError(f"Unsupported MODEL_MODE: {self.mode}")
