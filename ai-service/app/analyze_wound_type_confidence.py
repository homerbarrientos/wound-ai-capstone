from __future__ import annotations

import csv
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import efficientnet_b0

REPO_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = REPO_ROOT / "datasets" / "wound_type_v1"
TEST_DIR = DATASET_ROOT / "test"

MODEL_PATH = (
    REPO_ROOT
    / "ai-service"
    / "models"
    / "wound-type-efficientnet-b0-v1.pt"
)

OUTPUT_DIR = DATASET_ROOT / "error_analysis"
CSV_PATH = OUTPUT_DIR / "wound_type_v1_confidence_analysis.csv"
SUMMARY_PATH = OUTPUT_DIR / "wound_type_v1_confidence_summary.txt"

EXPECTED_CLASSES = [
    "diabetic",
    "pressure",
    "surgical",
    "venous",
]

IMAGE_SIZE = 224
BATCH_SIZE = 16
NUM_WORKERS = 0


def build_model(device: torch.device):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    model = efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, len(EXPECTED_CLASSES))

    checkpoint = torch.load(MODEL_PATH, map_location=device)

    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        raise RuntimeError(
            "Expected checkpoint dictionary with model_state_dict."
        )

    checkpoint_classes = checkpoint.get("classes")
    if checkpoint_classes and list(checkpoint_classes) != EXPECTED_CLASSES:
        raise RuntimeError(
            "Checkpoint classes do not match expected classes. "
            f"Checkpoint={checkpoint_classes}, Expected={EXPECTED_CLASSES}"
        )

    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    return model, checkpoint


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("WoundAI Stage 2 - Confidence Analysis")
    print("=" * 68)
    print(f"Device    : {device}")
    print(f"Model     : {MODEL_PATH}")
    print(f"Test root : {TEST_DIR}")
    print()

    eval_transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    test_ds = datasets.ImageFolder(
        TEST_DIR,
        transform=eval_transform,
    )

    if test_ds.classes != EXPECTED_CLASSES:
        raise RuntimeError(
            f"Unexpected test class order: {test_ds.classes}. "
            f"Expected: {EXPECTED_CLASSES}"
        )

    sample_paths = [Path(path) for path, _ in test_ds.samples]

    loader = DataLoader(
        test_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
    )

    model, checkpoint = build_model(device)

    print(f"Model version: {checkpoint.get('model_version', 'unknown')}")
    print(f"Test images  : {len(test_ds)}")
    print()

    rows = []
    global_index = 0
    correct_count = 0
    incorrect_count = 0
    incorrect_high_conf = 0
    incorrect_low_margin = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)

            logits = model(images)
            probs = torch.softmax(logits, dim=1)

            top2_probs, top2_indices = torch.topk(
                probs,
                k=2,
                dim=1,
            )

            for i in range(len(labels)):
                true_idx = int(labels[i].item())
                actual = EXPECTED_CLASSES[true_idx]

                top1_idx = int(top2_indices[i][0].item())
                top2_idx = int(top2_indices[i][1].item())

                predicted = EXPECTED_CLASSES[top1_idx]
                second_best = EXPECTED_CLASSES[top2_idx]

                top1_conf = float(top2_probs[i][0].item())
                top2_conf = float(top2_probs[i][1].item())
                margin = top1_conf - top2_conf
                correct = actual == predicted

                if correct:
                    correct_count += 1
                else:
                    incorrect_count += 1
                    if top1_conf >= 0.80:
                        incorrect_high_conf += 1
                    if margin <= 0.10:
                        incorrect_low_margin += 1

                source_path = sample_paths[global_index]
                global_index += 1

                all_probs = {
                    cls: float(probs[i][idx].item())
                    for idx, cls in enumerate(EXPECTED_CLASSES)
                }

                rows.append({
                    "image": str(source_path.relative_to(REPO_ROOT)),
                    "actual": actual,
                    "predicted": predicted,
                    "correct": correct,
                    "top1_confidence": top1_conf,
                    "second_best": second_best,
                    "top2_confidence": top2_conf,
                    "confidence_margin": margin,
                    "prob_diabetic": all_probs["diabetic"],
                    "prob_pressure": all_probs["pressure"],
                    "prob_surgical": all_probs["surgical"],
                    "prob_venous": all_probs["venous"],
                })

    rows.sort(
        key=lambda r: (
            r["correct"],
            -r["top1_confidence"],
        )
    )

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image",
                "actual",
                "predicted",
                "correct",
                "top1_confidence",
                "second_best",
                "top2_confidence",
                "confidence_margin",
                "prob_diabetic",
                "prob_pressure",
                "prob_surgical",
                "prob_venous",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    accuracy = correct_count / total if total else 0.0

    summary_lines = [
        "WoundAI Stage 2 v1 Confidence Analysis",
        "=" * 68,
        f"Model: {MODEL_PATH}",
        f"Test images: {total}",
        f"Correct: {correct_count}",
        f"Incorrect: {incorrect_count}",
        f"Accuracy: {accuracy:.4f}",
        "",
        f"Incorrect predictions with >=80% confidence: {incorrect_high_conf}",
        f"Incorrect predictions with <=10% top1-top2 margin: {incorrect_low_margin}",
        "",
        "Interpretation:",
        "- High-confidence errors may indicate systematic confusion or difficult examples.",
        "- Low-margin errors indicate the model saw two classes as similarly plausible.",
    ]

    SUMMARY_PATH.write_text(
        "\n".join(summary_lines),
        encoding="utf-8",
    )

    print(f"Correct       : {correct_count}")
    print(f"Incorrect     : {incorrect_count}")
    print(f"Accuracy      : {accuracy:.4f}")
    print()
    print(f"Incorrect >=80% confidence : {incorrect_high_conf}")
    print(f"Incorrect <=10% margin     : {incorrect_low_margin}")
    print()
    print(f"CSV     : {CSV_PATH}")
    print(f"Summary : {SUMMARY_PATH}")
    print()
    print(
        "The CSV is sorted with incorrect, high-confidence "
        "predictions near the top."
    )


if __name__ == "__main__":
    main()
