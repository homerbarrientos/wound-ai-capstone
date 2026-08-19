from __future__ import annotations

import csv
import hashlib
import random
import shutil
from pathlib import Path

SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

# Repository root:
# wound-ai-capstone/
#   ai-service/app/prepare_binary_dataset.py
#   datasets/wound_v1/...
REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "datasets" / "wound_v1"
RAW_ROOT = DATASET_ROOT / "raw" / "Wound Image Dataset"

SOURCE_DIRS = {
    "normal": RAW_ROOT / "Nomal",
    "wound": RAW_ROOT / "wound_main",
}

OUTPUT_SPLITS = ["train", "val", "test"]
MANIFEST_PATH = DATASET_ROOT / "metadata" / "binary_split_manifest.csv"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_images(folder: Path) -> list[Path]:
    if not folder.exists():
        raise FileNotFoundError(f"Source folder not found: {folder}")

    files = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]

    if not files:
        raise RuntimeError(f"No supported images found in: {folder}")

    return sorted(files)


def split_files(files: list[Path], rng: random.Random):
    files = files.copy()
    rng.shuffle(files)

    total = len(files)
    train_end = int(total * TRAIN_RATIO)
    val_end = train_end + int(total * VAL_RATIO)

    train_files = files[:train_end]
    val_files = files[train_end:val_end]
    test_files = files[val_end:]

    return {
        "train": train_files,
        "val": val_files,
        "test": test_files,
    }


def ensure_output_dirs():
    for split in OUTPUT_SPLITS:
        for label in SOURCE_DIRS:
            (DATASET_ROOT / split / label).mkdir(parents=True, exist_ok=True)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)


def clear_existing_binary_outputs():
    for split in OUTPUT_SPLITS:
        for label in SOURCE_DIRS:
            folder = DATASET_ROOT / split / label
            if not folder.exists():
                continue

            for item in folder.iterdir():
                if item.is_file():
                    item.unlink()


def main():
    if abs((TRAIN_RATIO + VAL_RATIO + TEST_RATIO) - 1.0) > 1e-9:
        raise ValueError("Train/val/test ratios must add up to 1.0")

    print("WoundAI Phase 4A - Binary Dataset Preparation")
    print("=" * 55)
    print(f"Dataset root : {DATASET_ROOT}")
    print(f"Random seed  : {SEED}")
    print(f"Split        : {TRAIN_RATIO:.0%}/{VAL_RATIO:.0%}/{TEST_RATIO:.0%}")
    print()

    ensure_output_dirs()
    clear_existing_binary_outputs()

    rng = random.Random(SEED)
    manifest_rows = []

    summary = {}

    for label, source_dir in SOURCE_DIRS.items():
        images = collect_images(source_dir)
        split_map = split_files(images, rng)

        summary[label] = {
            split: len(paths)
            for split, paths in split_map.items()
        }

        print(f"{label.upper()}: {len(images)} source images")

        for split, paths in split_map.items():
            destination_dir = DATASET_ROOT / split / label

            for source_path in paths:
                destination_path = destination_dir / source_path.name

                # Copy, never move. Raw data remains untouched.
                shutil.copy2(source_path, destination_path)

                manifest_rows.append({
                    "source_file": str(source_path.relative_to(REPO_ROOT)),
                    "copied_file": str(destination_path.relative_to(REPO_ROOT)),
                    "label": label,
                    "split": split,
                    "sha256": sha256_file(source_path),
                })

    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "source_file",
                "copied_file",
                "label",
                "split",
                "sha256",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    print()
    print("Split summary")
    print("-" * 55)

    grand_total = 0

    for label in SOURCE_DIRS:
        counts = summary[label]
        label_total = sum(counts.values())
        grand_total += label_total

        print(
            f"{label:>6}: "
            f"train={counts['train']:4d} | "
            f"val={counts['val']:4d} | "
            f"test={counts['test']:4d} | "
            f"total={label_total:4d}"
        )

    print("-" * 55)
    print(f"TOTAL : {grand_total}")
    print()
    print(f"Manifest written to: {MANIFEST_PATH}")
    print()
    print("Raw dataset was NOT modified.")
    print("You can now train an EfficientNet-B0 binary classifier using:")
    print(f"  {DATASET_ROOT / 'train'}")
    print(f"  {DATASET_ROOT / 'val'}")
    print(f"  {DATASET_ROOT / 'test'}")


if __name__ == "__main__":
    main()
