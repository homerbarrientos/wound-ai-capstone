from __future__ import annotations

import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import (
    MobileNet_V3_Small_Weights,
    mobilenet_v3_small,
)

SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

REPO_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = REPO_ROOT / "datasets" / "wound_type_v1"

TRAIN_DIR = DATASET_ROOT / "train"
VAL_DIR = DATASET_ROOT / "val"
TEST_DIR = DATASET_ROOT / "test"

MODEL_DIR = REPO_ROOT / "ai-service" / "models"

MODEL_PATH = (
    MODEL_DIR
    / "wound-type-mobilenet-v3-small-v1.pt"
)

METRICS_PATH = (
    MODEL_DIR
    / "wound-type-mobilenet-v3-small-v1-metrics.json"
)

EXPECTED_CLASSES = [
    "diabetic",
    "pressure",
    "surgical",
    "venous",
]

IMAGE_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 20
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4
NUM_WORKERS = 0
PATIENCE = 5

weights = MobileNet_V3_Small_Weights.DEFAULT

imagenet_mean = weights.transforms().mean
imagenet_std = weights.transforms().std

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(10),
    transforms.ColorJitter(
        brightness=0.12,
        contrast=0.12,
        saturation=0.08,
        hue=0.02,
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=imagenet_mean,
        std=imagenet_std,
    ),
])

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=imagenet_mean,
        std=imagenet_std,
    ),
])


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def multiclass_metrics(
    y_true: list[int],
    y_pred: list[int],
    class_names: list[str],
) -> dict:
    n = len(class_names)

    cm = [
        [0 for _ in range(n)]
        for _ in range(n)
    ]

    for true_label, predicted_label in zip(
        y_true,
        y_pred,
    ):
        cm[true_label][predicted_label] += 1

    total = sum(sum(row) for row in cm)
    correct = sum(cm[i][i] for i in range(n))

    accuracy = safe_div(correct, total)

    precisions = []
    recalls = []
    f1s = []
    per_class = {}

    for i, name in enumerate(class_names):
        tp = cm[i][i]

        fp = sum(
            cm[row][i]
            for row in range(n)
            if row != i
        )

        fn = sum(
            cm[i][col]
            for col in range(n)
            if col != i
        )

        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)

        f1 = safe_div(
            2 * precision * recall,
            precision + recall,
        )

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

        per_class[name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(cm[i]),
        }

    return {
        "accuracy": accuracy,
        "macro_precision": sum(precisions) / n,
        "macro_recall": sum(recalls) / n,
        "macro_f1": sum(f1s) / n,
        "per_class": per_class,
        "confusion_matrix": {
            "labels": class_names,
            "matrix": cm,
        },
    }


def make_loaders():
    train_ds = datasets.ImageFolder(
        TRAIN_DIR,
        transform=train_transform,
    )

    val_ds = datasets.ImageFolder(
        VAL_DIR,
        transform=eval_transform,
    )

    test_ds = datasets.ImageFolder(
        TEST_DIR,
        transform=eval_transform,
    )

    for split_name, ds in [
        ("train", train_ds),
        ("val", val_ds),
        ("test", test_ds),
    ]:
        if ds.classes != EXPECTED_CLASSES:
            raise RuntimeError(
                f"Unexpected {split_name} class order: "
                f"{ds.classes}. "
                f"Expected: {EXPECTED_CLASSES}"
            )

    train_loader = DataLoader(
        train_ds,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
    )

    test_loader = DataLoader(
        test_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
    )

    return (
        train_ds,
        val_ds,
        test_ds,
        train_loader,
        val_loader,
        test_loader,
    )


def build_model(device: torch.device):
    model = mobilenet_v3_small(
        weights=weights
    )

    in_features = model.classifier[3].in_features

    model.classifier[3] = nn.Linear(
        in_features,
        len(EXPECTED_CLASSES),
    )

    return model.to(device)


def run_epoch(
    model,
    loader,
    criterion,
    device,
    optimizer=None,
):
    training = optimizer is not None
    model.train(training)

    total_loss = 0.0
    y_true = []
    y_pred = []

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        if training:
            optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(
            outputs,
            labels,
        )

        if training:
            loss.backward()
            optimizer.step()

        total_loss += (
            loss.item()
            * images.size(0)
        )

        preds = torch.argmax(
            outputs,
            dim=1,
        )

        y_true.extend(
            labels.detach().cpu().tolist()
        )

        y_pred.extend(
            preds.detach().cpu().tolist()
        )

    avg_loss = (
        total_loss
        / len(loader.dataset)
    )

    metrics = multiclass_metrics(
        y_true,
        y_pred,
        EXPECTED_CLASSES,
    )

    return avg_loss, metrics


def evaluate_with_latency(
    model,
    loader,
    criterion,
    device,
):
    model.eval()

    total_loss = 0.0
    y_true = []
    y_pred = []

    total_images = 0
    total_inference_seconds = 0.0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            if device.type == "cuda":
                torch.cuda.synchronize()

            start = time.perf_counter()

            outputs = model(images)

            if device.type == "cuda":
                torch.cuda.synchronize()

            total_inference_seconds += (
                time.perf_counter() - start
            )

            total_images += images.size(0)

            loss = criterion(
                outputs,
                labels,
            )

            total_loss += (
                loss.item()
                * images.size(0)
            )

            preds = torch.argmax(
                outputs,
                dim=1,
            )

            y_true.extend(
                labels.cpu().tolist()
            )

            y_pred.extend(
                preds.cpu().tolist()
            )

    avg_loss = (
        total_loss
        / len(loader.dataset)
    )

    metrics = multiclass_metrics(
        y_true,
        y_pred,
        EXPECTED_CLASSES,
    )

    metrics["inference_ms_per_image"] = (
        total_inference_seconds
        / total_images
        * 1000
        if total_images
        else 0.0
    )

    return avg_loss, metrics


def print_test_results(
    loss: float,
    metrics: dict,
):
    print()

    print(
        "FINAL HELD-OUT TEST RESULTS - "
        "MOBILENETV3-SMALL"
    )

    print("-" * 72)

    print(f"loss              : {loss:.4f}")
    print(f"accuracy          : {metrics['accuracy']:.4f}")
    print(f"macro precision   : {metrics['macro_precision']:.4f}")
    print(f"macro recall      : {metrics['macro_recall']:.4f}")
    print(f"macro F1          : {metrics['macro_f1']:.4f}")

    print(
        f"inference ms/image: "
        f"{metrics['inference_ms_per_image']:.2f}"
    )

    print()

    print("Per-class metrics")
    print("-" * 72)

    for name in EXPECTED_CLASSES:
        m = metrics["per_class"][name]

        print(
            f"{name:>8}: "
            f"precision={m['precision']:.4f} | "
            f"recall={m['recall']:.4f} | "
            f"F1={m['f1']:.4f} | "
            f"support={m['support']}"
        )

    print()

    print("Confusion matrix")
    print("rows=true, cols=predicted")

    print(
        "labels:",
        " | ".join(EXPECTED_CLASSES),
    )

    for name, row in zip(
        EXPECTED_CLASSES,
        metrics["confusion_matrix"]["matrix"],
    ):
        print(f"{name:>8}: {row}")


def main():
    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "WoundAI Stage 2 - "
        "MobileNetV3-Small Wound Type Training"
    )

    print("=" * 72)

    print(f"Device        : {device}")
    print(f"Dataset root  : {DATASET_ROOT}")
    print(f"Model path    : {MODEL_PATH}")
    print(f"Seed          : {SEED}")

    print()

    (
        train_ds,
        val_ds,
        test_ds,
        train_loader,
        val_loader,
        test_loader,
    ) = make_loaders()

    print(f"Classes       : {train_ds.classes}")
    print(f"Train images  : {len(train_ds)}")
    print(f"Val images    : {len(val_ds)}")
    print(f"Test images   : {len(test_ds)}")

    print()

    model = build_model(device)

    class_counts = [
        0
    ] * len(EXPECTED_CLASSES)

    for _, label in train_ds.samples:
        class_counts[label] += 1

    total_train = sum(class_counts)

    class_weights = [
        total_train
        / (
            len(EXPECTED_CLASSES)
            * count
        )
        for count in class_counts
    ]

    weight_tensor = torch.tensor(
        class_weights,
        dtype=torch.float32,
        device=device,
    )

    print(
        f"Train class counts : {class_counts}"
    )

    print(
        "Class weights      : "
        + ", ".join(
            f"{weight:.3f}"
            for weight in class_weights
        )
    )

    print()

    criterion = nn.CrossEntropyLoss(
        weight=weight_tensor
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    scheduler = (
        torch.optim.lr_scheduler
        .ReduceLROnPlateau(
            optimizer,
            mode="max",
            factor=0.5,
            patience=1,
        )
    )

    best_val_f1 = -1.0
    epochs_without_improvement = 0
    history = []

    for epoch in range(
        1,
        EPOCHS + 1,
    ):
        start = time.time()

        train_loss, train_metrics = run_epoch(
            model,
            train_loader,
            criterion,
            device,
            optimizer=optimizer,
        )

        val_loss, val_metrics = run_epoch(
            model,
            val_loader,
            criterion,
            device,
            optimizer=None,
        )

        scheduler.step(
            val_metrics["macro_f1"]
        )

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_accuracy": train_metrics["accuracy"],
            "train_macro_f1": train_metrics["macro_f1"],
            "val_loss": val_loss,
            "val_accuracy": val_metrics["accuracy"],
            "val_macro_f1": val_metrics["macro_f1"],
            "learning_rate": optimizer.param_groups[0]["lr"],
        })

        elapsed = time.time() - start

        print(
            f"Epoch {epoch:02d}/{EPOCHS} | "
            f"{elapsed:6.1f}s | "
            f"train loss={train_loss:.4f} "
            f"F1={train_metrics['macro_f1']:.4f} | "
            f"val loss={val_loss:.4f} "
            f"F1={val_metrics['macro_f1']:.4f}"
        )

        if (
            val_metrics["macro_f1"]
            > best_val_f1
        ):
            best_val_f1 = (
                val_metrics["macro_f1"]
            )

            epochs_without_improvement = 0

            torch.save(
                {
                    "model_state_dict":
                        model.state_dict(),

                    "model_name":
                        "MobileNetV3-Small",

                    "model_version":
                        "wound-type-mobilenet-v3-small-v1",

                    "classes":
                        train_ds.classes,

                    "image_size":
                        IMAGE_SIZE,

                    "seed":
                        SEED,

                    "validation_macro_f1":
                        best_val_f1,
                },
                MODEL_PATH,
            )

            print(
                "  -> saved new best checkpoint "
                f"(val macro F1="
                f"{best_val_f1:.4f})"
            )

        else:
            epochs_without_improvement += 1

        if (
            epochs_without_improvement
            >= PATIENCE
        ):
            print(
                "Early stopping: "
                "no validation macro-F1 "
                "improvement for "
                f"{PATIENCE} epochs."
            )
            break

    print()

    print(
        "Loading best MobileNetV3-Small "
        "checkpoint for final held-out "
        "test evaluation..."
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    test_loss, test_metrics = (
        evaluate_with_latency(
            model,
            test_loader,
            criterion,
            device,
        )
    )

    print_test_results(
        test_loss,
        test_metrics,
    )

    output = {
        "model_name":
            "MobileNetV3-Small",

        "model_version":
            "wound-type-mobilenet-v3-small-v1",

        "classes":
            train_ds.classes,

        "seed":
            SEED,

        "image_size":
            IMAGE_SIZE,

        "batch_size":
            BATCH_SIZE,

        "learning_rate":
            LEARNING_RATE,

        "weight_decay":
            WEIGHT_DECAY,

        "best_validation_macro_f1":
            best_val_f1,

        "train_count":
            len(train_ds),

        "val_count":
            len(val_ds),

        "test_count":
            len(test_ds),

        "train_class_counts":
            class_counts,

        "test_loss":
            test_loss,

        "test_metrics":
            test_metrics,

        "history":
            history,
    }

    METRICS_PATH.write_text(
        json.dumps(
            output,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()

    print(
        "Best MobileNetV3-Small model saved to : "
        f"{MODEL_PATH}"
    )

    print(
        "Metrics saved to                      : "
        f"{METRICS_PATH}"
    )


if __name__ == "__main__":
    main()