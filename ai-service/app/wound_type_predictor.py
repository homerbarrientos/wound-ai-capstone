from __future__ import annotations

from pathlib import Path
from typing import Dict

from PIL import Image

from .gradcam import GradCAM, overlay_gradcam


CLASSES = [
    "diabetic",
    "pressure",
    "surgical",
    "venous",
]


class WoundTypePredictor:
    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.60,
    ):
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold

        self.model_name = "EfficientNet-B0"
        self.model_version = "wound-type-v1"

        self.model = None
        self.transform = None

        self._load_model()

    def _load_model(self):
        import torch
        from torch import nn
        from torchvision import transforms
        from torchvision.models import efficientnet_b0

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Wound type model not found at "
                f"{self.model_path.resolve()}"
            )

        model = efficientnet_b0(weights=None)

        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(
            in_features,
            len(CLASSES),
        )

        checkpoint = torch.load(
            self.model_path,
            map_location="cpu",
        )

        if (
            isinstance(checkpoint, dict)
            and "model_state_dict" in checkpoint
        ):
            state_dict = checkpoint["model_state_dict"]

            checkpoint_classes = checkpoint.get("classes")

            if (
                checkpoint_classes
                and list(checkpoint_classes) != CLASSES
            ):
                raise ValueError(
                    "Wound type checkpoint class order mismatch. "
                    f"Checkpoint={checkpoint_classes}, "
                    f"Expected={CLASSES}"
                )

            self.model_version = checkpoint.get(
                "model_version",
                "wound-type-v1",
            )

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
            f"Loaded {self.model_name} "
            f"{self.model_version} from "
            f"{self.model_path.resolve()}"
        )

    def predict(self, image: Image.Image) -> Dict:
        import torch

        if self.model is None or self.transform is None:
            raise RuntimeError(
                "Wound type model is not loaded."
            )

        image = image.convert("RGB")

        x = self.transform(image).unsqueeze(0)

        with torch.no_grad():
            logits = self.model(x)

            probs = torch.softmax(
                logits,
                dim=1,
            )[0].tolist()

        ranked = sorted(
            zip(CLASSES, probs),
            key=lambda x: x[1],
            reverse=True,
        )

        category, confidence = ranked[0]

        uncertain = (
            confidence < self.confidence_threshold
        )

        return {
            "wound_type": category.title(),
            "wound_type_confidence": float(confidence),
            "wound_type_uncertain": uncertain,
            "wound_type_scores": [
                {
                    "category": name.title(),
                    "probability": float(prob),
                }
                for name, prob in ranked
            ],
            "wound_type_model_name": self.model_name,
            "wound_type_model_version": self.model_version,
        }

    def generate_gradcam(
        self,
        image: Image.Image,
        class_index: int | None = None,
    ) -> Image.Image:
        import torch

        if self.model is None or self.transform is None:
            raise RuntimeError(
                "Wound type model is not loaded."
            )

        image = image.convert("RGB")

        input_tensor = (
            self.transform(image)
            .unsqueeze(0)
        )

        # If no class is supplied, use the model's
        # highest-probability predicted class.
        if class_index is None:
            with torch.no_grad():
                logits = self.model(input_tensor)

                class_index = int(
                    torch.argmax(
                        logits,
                        dim=1,
                    ).item()
                )

        # Final convolutional feature block
        # of EfficientNet-B0.
        target_layer = self.model.features[-1]

        gradcam = GradCAM(
            model=self.model,
            target_layer=target_layer,
        )

        try:
            cam = gradcam.generate(
                input_tensor=input_tensor,
                class_index=class_index,
            )

            overlay = overlay_gradcam(
                image=image,
                cam=cam,
                alpha=0.45,
            )

            return overlay

        finally:
            gradcam.close()