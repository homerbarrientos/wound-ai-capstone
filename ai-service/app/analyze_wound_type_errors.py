from __future__ import annotations

import csv
import shutil
from collections import Counter
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

OUTPUT_ROOT = DATASET_ROOT / "error_analysis"
CSV_PATH = OUTPUT_ROOT / "wound_type_v1_test_predictions.csv"
SUMMARY_PATH = OUTPUT_ROOT / "wound_type_v1_error_summary.txt"

EXPECTED_CLASSES = [
    "diabetic",
    "pressure",
    "surgical",
    "venous",
]

IMAGE_SIZE = 224
BATCH_SIZE = 16
NUM_WORKERS = 0


def clear_output():
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def build_model(device: torch.device):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    model = efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(
        in_features,
        len(EXPECTED_CLASSES),
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
    )

    if (
        not isinstance(checkpoint, dict)
        or "model_state_dict" not in checkpoint
    ):
        raise RuntimeError(
            "Expected checkpoint dictionary with model_state_dict."
        )

    checkpoint_classes = checkpoint.get("classes")
    if (
        checkpoint_classes
        and list(checkpoint_classes) != EXPECTED_CLASSES
    ):
        raise RuntimeError(
            "Checkpoint classes do not match expected classes. "
            f"Checkpoint={checkpoint_classes}, "
            f"Expected={EXPECTED_CLASSES}"
        )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )
    model.to(device)
    model.eval()

    return model, checkpoint


def main():
    clear_output()

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("WoundAI Stage 2 - Error Analysis")
    print("=" * 68)
    print(f"Device      : {device}")
    print(f"Model       : {MODEL_PATH}")
    print(f"Test root   : {TEST_DIR}")
    print(f"Output root : {OUTPUT_ROOT}")
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

    # Keep original source file paths aligned with ImageFolder samples.
    sample_paths = [
        Path(path)
        for path, _ in test_ds.samples
    ]

    test_loader = DataLoader(
        test_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
    )

    model, checkpoint = build_model(device)

    print(
        f"Model version: "
        f"{checkpoint.get('model_version', 'unknown')}"
    )
    print(f"Test images  : {len(test_ds)}")
    print()

    rows = []
    error_counter = Counter()
    total_correct = 0
    global_index = 0

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)

            logits = model(images)
            probs = torch.softmax(
                logits,
                dim=1,
            )

            confidences, preds = torch.max(
                probs,
                dim=1,
            )

            for i in range(len(labels)):
                true_idx = int(labels[i].item())
                pred_idx = int(preds[i].item())
                confidence = float(
                    confidences[i].item()
                )

                actual = EXPECTED_CLASSES[true_idx]
                predicted = EXPECTED_CLASSES[pred_idx]

                source_path = sample_paths[global_index]
                global_index += 1

                correct = actual == predicted
                if correct:
                    total_correct += 1
                else:
                    key = f"{actual}_as_{predicted}"
                    error_counter[key] += 1

                    error_dir = OUTPUT_ROOT / key
                    error_dir.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    destination = (
                        error_dir
                        / source_path.name
                    )

                    if destination.exists():
                        destination = (
                            error_dir
                            / (
                                f"{source_path.stem}_"
                                f"{global_index}"
                                f"{source_path.suffix}"
                            )
                        )

                    shutil.copy2(
                        source_path,
                        destination,
                    )

                class_probabilities = {
                    cls: float(
                        probs[i][idx].item()
                    )
                    for idx, cls in enumerate(
                        EXPECTED_CLASSES
                    )
                }

                rows.append({
                    "image": str(
                        source_path.relative_to(
                            REPO_ROOT
                        )
                    ),
                    "actual": actual,
                    "predicted": predicted,
                    "correct": correct,
                    "confidence": confidence,
                    "prob_diabetic": class_probabilities["diabetic"],
                    "prob_pressure": class_probabilities["pressure"],
                    "prob_surgical": class_probabilities["surgical"],
                    "prob_venous": class_probabilities["venous"],
                })

    with CSV_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image",
                "actual",
                "predicted",
                "correct",
                "confidence",
                "prob_diabetic",
                "prob_pressure",
                "prob_surgical",
                "prob_venous",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    total_errors = total - total_correct
    accuracy = (
        total_correct / total
        if total
        else 0.0
    )

    summary_lines = [
        "WoundAI Stage 2 v1 Error Analysis",
        "=" * 68,
        f"Model: {MODEL_PATH}",
        f"Test images: {total}",
        f"Correct: {total_correct}",
        f"Errors: {total_errors}",
        f"Accuracy: {accuracy:.4f}",
        "",
        "Misclassification counts:",
    ]

    if error_counter:
        for key, count in sorted(
            error_counter.items()
        ):
            summary_lines.append(
                f"  {key}: {count}"
            )
    else:
        summary_lines.append("  None")

    SUMMARY_PATH.write_text(
        "\n".join(summary_lines),
        encoding="utf-8",
    )

    print(f"Correct       : {total_correct}")
    print(f"Errors        : {total_errors}")
    print(f"Accuracy      : {accuracy:.4f}")
    print()
    print("Misclassification counts")

    if error_counter:
        for key, count in sorted(
            error_counter.items()
        ):
            print(
                f"  {key}: {count}"
            )
    else:
        print("  None")

    print()
    print(f"Predictions CSV : {CSV_PATH}")
    print(f"Summary         : {SUMMARY_PATH}")
    print()
    print(
        "Misclassified images were copied into "
        "error_analysis/<actual>_as_<predicted>/ folders."
    )


if __name__ == "__main__":
    main()
