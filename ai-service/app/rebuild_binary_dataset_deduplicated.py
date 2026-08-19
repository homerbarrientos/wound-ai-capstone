from __future__ import annotations

import csv
import hashlib
import random
import shutil
from collections import defaultdict
from pathlib import Path

SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "datasets" / "wound_v1"
RAW_ROOT = DATASET_ROOT / "raw" / "Wound Image Dataset"

SOURCE_DIRS = {
    "normal": RAW_ROOT / "Nomal",
    "wound": RAW_ROOT / "wound_main",
}

MANIFEST_PATH = DATASET_ROOT / "metadata" / "binary_split_manifest_deduplicated.csv"
DUPLICATES_PATH = DATASET_ROOT / "metadata" / "exact_duplicates_removed.csv"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_images(folder: Path) -> list[Path]:
    if not folder.exists():
        raise FileNotFoundError(f"Source folder not found: {folder}")
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    if not files:
        raise RuntimeError(f"No supported images found in: {folder}")
    return sorted(files)


def deduplicate(files: list[Path]):
    by_hash = defaultdict(list)
    for p in files:
        by_hash[sha256_file(p)].append(p)

    unique = []
    duplicates = []

    for digest, paths in by_hash.items():
        paths = sorted(paths)
        canonical = paths[0]
        unique.append((digest, canonical, len(paths)))
        for duplicate in paths[1:]:
            duplicates.append((digest, canonical, duplicate))

    return unique, duplicates


def split_records(records, rng):
    records = list(records)
    rng.shuffle(records)
    total = len(records)
    train_end = int(total * TRAIN_RATIO)
    val_end = train_end + int(total * VAL_RATIO)

    return {
        "train": records[:train_end],
        "val": records[train_end:val_end],
        "test": records[val_end:],
    }


def recreate_split_dirs():
    for split in ("train", "val", "test"):
        split_dir = DATASET_ROOT / split
        if split_dir.exists():
            shutil.rmtree(split_dir)
        for label in SOURCE_DIRS:
            (split_dir / label).mkdir(parents=True, exist_ok=True)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def main():
    if abs(TRAIN_RATIO + VAL_RATIO + TEST_RATIO - 1.0) > 1e-9:
        raise ValueError("Ratios must add up to 1.0")

    print("WoundAI Phase 4C.2 - Deduplicated Binary Dataset Rebuild")
    print("=" * 66)
    print(f"Raw root : {RAW_ROOT}")
    print(f"Seed     : {SEED}")
    print(f"Split    : {TRAIN_RATIO:.0%}/{VAL_RATIO:.0%}/{TEST_RATIO:.0%}")
    print()

    recreate_split_dirs()
    rng = random.Random(SEED)

    manifest_rows = []
    duplicate_rows = []
    summary = {}

    for label, source_dir in SOURCE_DIRS.items():
        source_files = collect_images(source_dir)
        unique_records, duplicates = deduplicate(source_files)
        split_map = split_records(unique_records, rng)

        summary[label] = {
            "source": len(source_files),
            "unique": len(unique_records),
            "duplicates": len(duplicates),
            "train": len(split_map["train"]),
            "val": len(split_map["val"]),
            "test": len(split_map["test"]),
        }

        for digest, kept, duplicate in duplicates:
            duplicate_rows.append({
                "label": label,
                "sha256": digest,
                "kept_file": rel(kept),
                "removed_duplicate": rel(duplicate),
            })

        for split, records in split_map.items():
            dest_dir = DATASET_ROOT / split / label
            for digest, source_path, group_size in records:
                dest = dest_dir / source_path.name
                shutil.copy2(source_path, dest)

                manifest_rows.append({
                    "source_file": rel(source_path),
                    "copied_file": rel(dest),
                    "label": label,
                    "split": split,
                    "sha256": digest,
                    "duplicate_group_size": group_size,
                })

    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_file",
                "copied_file",
                "label",
                "split",
                "sha256",
                "duplicate_group_size",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    with DUPLICATES_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["label", "sha256", "kept_file", "removed_duplicate"],
        )
        writer.writeheader()
        writer.writerows(duplicate_rows)

    print("Split summary")
    print("-" * 66)
    total_unique = 0
    total_dupes = 0
    for label, s in summary.items():
        total_unique += s["unique"]
        total_dupes += s["duplicates"]
        print(
            f"{label:>6}: train={s['train']:4d} | val={s['val']:4d} | "
            f"test={s['test']:4d} | unique={s['unique']:4d} | "
            f"duplicates removed={s['duplicates']:4d}"
        )
    print("-" * 66)
    print(f"UNIQUE IMAGES TOTAL     : {total_unique}")
    print(f"EXACT DUPLICATES REMOVED: {total_dupes}")
    print()
    print(f"Manifest          : {MANIFEST_PATH}")
    print(f"Duplicates report : {DUPLICATES_PATH}")
    print()
    print("Raw dataset was NOT modified.")
    print("Next: rerun the exact-leakage audit using the new manifest.")


if __name__ == "__main__":
    main()
