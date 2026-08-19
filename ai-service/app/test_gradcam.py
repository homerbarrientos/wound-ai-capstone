from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms
from torchvision.models import efficientnet_b0
from torch import nn

from app.gradcam import GradCAM, overlay_gradcam


REPO_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    REPO_ROOT
    / "ai-service"
    / "models"
    / "wound-type-efficientnet-b0-v1.pt"
)

TEST_IMAGE = (
    REPO_ROOT
    / "datasets"
    / "wound_type_v1"
    / "test"
    / "pressure"
    / "36_0.jpg"
)

OUTPUT_PATH = (
    REPO_ROOT
    / "ai-service"
    / "gradcam_test_output.jpg"
)

CLASSES = [
    "diabetic",
    "pressure",
    "surgical",
    "venous",
]


def main():
    device = torch.device("cpu")

    model = efficientnet_b0(weights=None)

    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(
        in_features,
        len(CLASSES),
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.eval()

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    image = Image.open(TEST_IMAGE).convert("RGB")
    input_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        logits = model(input_tensor)
        predicted_index = int(
            torch.argmax(logits, dim=1).item()
        )

    predicted_class = CLASSES[predicted_index]

    print(f"Predicted class: {predicted_class}")

    # EfficientNet-B0 final convolutional feature block
    target_layer = model.features[-1]

    gradcam = GradCAM(
        model=model,
        target_layer=target_layer,
    )

    cam = gradcam.generate(
        input_tensor,
        class_index=predicted_index,
    )

    overlay = overlay_gradcam(
        image=image,
        cam=cam,
        alpha=0.45,
    )

    overlay.save(OUTPUT_PATH)

    gradcam.close()

    print(f"Grad-CAM saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()