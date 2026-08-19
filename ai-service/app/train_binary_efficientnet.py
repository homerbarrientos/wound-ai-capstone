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
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

# ----------------------------
# Reproducibility
# ----------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

# ----------------------------
# Paths
# ----------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "datasets" / "wound_v1"
TRAIN_DIR = DATASET_ROOT / "train"
VAL_DIR = DATASET_ROOT / "val"
TEST_DIR = DATASET_ROOT / "test"

MODEL_DIR = REPO_ROOT / "ai-service" / "models"
MODEL_PATH = MODEL_DIR / "wound-efficientnet-b0-binary.pt"
METRICS_PATH = MODEL_DIR / "wound-efficientnet-b0-binary-metrics.json"

# ----------------------------
# Training configuration
# ----------------------------
IMAGE_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 12
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4
NUM_WORKERS = 0  # safest default on Windows
PATIENCE = 4

# Expected ImageFolder alphabetical order.
EXPECTED_CLASSES = ["normal", "wound"]

# ----------------------------
# Transforms
# ----------------------------
weights = EfficientNet_B0_Weights.DEFAULT
imagenet_mean = weights.transforms().mean
imagenet_std = weights.transforms().std

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(8),
    transforms.ColorJitter(
        brightness=0.10,
        contrast=0.10,
        saturation=0.05,
        hue=0.02,
    ),
    transforms.ToTensor(),
    transforms.Normalize(mean=imagenet_mean, std=imagenet_std),
])

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=imagenet_mean, std=imagenet_std),
])


def confusion_counts(y_true: list[int], y_pred: list[int]) -> dict:
    # Class 0 = normal, class 1 = wound
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def binary_metrics(y_true: list[int], y_pred: list[int]) -> dict:
    counts = confusion_counts(y_true, y_pred)
    tp = counts["tp"]
    tn = counts["tn"]
    fp = counts["fp"]
    fn = counts["fn"]

    accuracy = safe_div(tp + tn, tp + tn + fp + fn)

    wound_precision = safe_div(tp, tp + fp)
    wound_recall = safe_div(tp, tp + fn)
    wound_f1 = safe_div(
        2 * wound_precision * wound_recall,
        wound_precision + wound_recall,
    )

    normal_precision = safe_div(tn, tn + fn)
    normal_recall = safe_div(tn, tn + fp)
    normal_f1 = safe_div(
        2 * normal_precision * normal_recall,
        normal_precision + normal_recall,
    )

    macro_precision = (normal_precision + wound_precision) / 2
    macro_recall = (normal_recall + wound_recall) / 2
    macro_f1 = (normal_f1 + wound_f1) / 2

    return {
        "accuracy": accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "normal": {
            "precision": normal_precision,
            "recall": normal_recall,
            "f1": normal_f1,
        },
        "wound": {
            "precision": wound_precision,
            "recall": wound_recall,
            "f1": wound_f1,
        },
        "confusion_matrix": {
            "labels": ["normal", "wound"],
            "matrix": [
                [tn, fp],
                [fn, tp],
            ],
        },
        **counts,
    }


def make_loaders():
    train_ds = datasets.ImageFolder(TRAIN_DIR, transform=train_transform)
    val_ds = datasets.ImageFolder(VAL_DIR, transform=eval_transform)
    test_ds = datasets.ImageFolder(TEST_DIR, transform=eval_transform)

    if train_ds.classes != EXPECTED_CLASSES:
        raise RuntimeError(
            f"Unexpected train class order: {train_ds.classes}. "
            f"Expected: {EXPECTED_CLASSES}"
        )

    if val_ds.classes != EXPECTED_CLASSES:
        raise RuntimeError(
            f"Unexpected val class order: {val_ds.classes}. "
            f"Expected: {EXPECTED_CLASSES}"
        )

    if test_ds.classes != EXPECTED_CLASSES:
        raise RuntimeError(
            f"Unexpected test class order: {test_ds.classes}. "
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

    return train_ds, val_ds, test_ds, train_loader, val_loader, test_loader


def build_model(device: torch.device):
    model = efficientnet_b0(weights=weights)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, 2)
    return model.to(device)


def run_epoch(model, loader, criterion, device, optimizer=None):
    training = optimizer is not None
    model.train(training)

    total_loss = 0.0
    y_true: list[int] = []
    y_pred: list[int] = []

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        if training:
            optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)

        if training:
            loss.backward()
            optimizer.step()

        total_loss += loss.item() * images.size(0)

        preds = torch.argmax(outputs, dim=1)
        y_true.extend(labels.detach().cpu().tolist())
        y_pred.extend(preds.detach().cpu().tolist())

    avg_loss = total_loss / len(loader.dataset)
    metrics = binary_metrics(y_true, y_pred)

    return avg_loss, metrics


def evaluate_with_latency(model, loader, criterion, device):
    model.eval()

    total_loss = 0.0
    y_true: list[int] = []
    y_pred: list[int] = []
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

            elapsed = time.perf_counter() - start
            total_inference_seconds += elapsed
            total_images += images.size(0)

            loss = criterion(outputs, labels)
            total_loss += loss.item() * images.size(0)

            preds = torch.argmax(outputs, dim=1)
            y_true.extend(labels.cpu().tolist())
            y_pred.extend(preds.cpu().tolist())

    avg_loss = total_loss / len(loader.dataset)
    metrics = binary_metrics(y_true, y_pred)
    metrics["inference_ms_per_image"] = (
        total_inference_seconds / total_images * 1000
        if total_images
        else 0.0
    )

    return avg_loss, metrics


def print_metrics(title: str, loss: float, metrics: dict):
    print(title)
    print("-" * 60)
    print(f"loss              : {loss:.4f}")
    print(f"accuracy          : {metrics['accuracy']:.4f}")
    print(f"macro precision   : {metrics['macro_precision']:.4f}")
    print(f"macro recall      : {metrics['macro_recall']:.4f}")
    print(f"macro F1          : {metrics['macro_f1']:.4f}")
    print(f"normal F1         : {metrics['normal']['f1']:.4f}")
    print(f"wound F1          : {metrics['wound']['f1']:.4f}")

    if "inference_ms_per_image" in metrics:
        print(
            f"inference ms/image: "
            f"{metrics['inference_ms_per_image']:.2f}"
        )

    cm = metrics["confusion_matrix"]["matrix"]
    print()
    print("Confusion matrix")
    print("rows=true, cols=predicted")
    print("              normal   wound")
    print(f"true normal   {cm[0][0]:6d} {cm[0][1]:7d}")
    print(f"true wound    {cm[1][0]:6d} {cm[1][1]:7d}")
    print()


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("WoundAI Phase 4B - EfficientNet-B0 Binary Training")
    print("=" * 60)
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

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=1,
    )

    best_val_f1 = -1.0
    epochs_without_improvement = 0
    history = []

    for epoch in range(1, EPOCHS + 1):
        epoch_start = time.time()

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

        scheduler.step(val_metrics["macro_f1"])

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

        elapsed = time.time() - epoch_start

        print(
            f"Epoch {epoch:02d}/{EPOCHS} | "
            f"{elapsed:6.1f}s | "
            f"train loss={train_loss:.4f} "
            f"F1={train_metrics['macro_f1']:.4f} | "
            f"val loss={val_loss:.4f} "
            f"F1={val_metrics['macro_f1']:.4f}"
        )

        if val_metrics["macro_f1"] > best_val_f1:
            best_val_f1 = val_metrics["macro_f1"]
            epochs_without_improvement = 0

            torch.save({
                "model_state_dict": model.state_dict(),
                "model_name": "EfficientNet-B0",
                "model_version": "binary-v1",
                "classes": train_ds.classes,
                "image_size": IMAGE_SIZE,
                "seed": SEED,
                "validation_macro_f1": best_val_f1,
            }, MODEL_PATH)

            print(
                f"  -> saved new best checkpoint "
                f"(val macro F1={best_val_f1:.4f})"
            )
        else:
            epochs_without_improvement += 1

        if epochs_without_improvement >= PATIENCE:
            print(
                f"Early stopping: no validation macro-F1 improvement "
                f"for {PATIENCE} epochs."
            )
            break

    print()
    print("Loading best checkpoint for final held-out test evaluation...")
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])

    test_loss, test_metrics = evaluate_with_latency(
        model,
        test_loader,
        criterion,
        device,
    )

    print()
    print_metrics("FINAL HELD-OUT TEST RESULTS", test_loss, test_metrics)

    output = {
        "model_name": "EfficientNet-B0",
        "model_version": "binary-v1",
        "classes": train_ds.classes,
        "seed": SEED,
        "image_size": IMAGE_SIZE,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        "best_validation_macro_f1": best_val_f1,
        "train_count": len(train_ds),
        "val_count": len(val_ds),
        "test_count": len(test_ds),
        "test_loss": test_loss,
        "test_metrics": test_metrics,
        "history": history,
    }

    METRICS_PATH.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    print(f"Best model saved to : {MODEL_PATH}")
    print(f"Metrics saved to    : {METRICS_PATH}")


if __name__ == "__main__":
    main()
