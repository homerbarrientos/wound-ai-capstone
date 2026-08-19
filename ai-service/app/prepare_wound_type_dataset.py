from __future__ import annotations

import csv
import hashlib
import random
import re
import shutil
from collections import defaultdict
from pathlib import Path

SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "datasets" / "wound_type_v1"
RAW_TRAIN_ROOT = DATASET_ROOT / "raw" / "Train" / "Train"
RAW_TEST_ROOT = DATASET_ROOT / "raw" / "Test" / "Test"

CLASS_MAP = {
    "D": "diabetic",
    "P": "pressure",
    "S": "surgical",
    "V": "venous",
}

MANIFEST_PATH = DATASET_ROOT / "metadata" / "wound_type_split_manifest.csv"
DUPLICATES_PATH = DATASET_ROOT / "metadata" / "wound_type_exact_duplicates.csv"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_images(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def case_id_from_filename(path: Path, class_code: str) -> str:
    match = re.match(r"^(\d+)(?:_\d+)?$", path.stem)
    if not match:
        raise ValueError(f"Unable to determine case id from filename: {path.name}")
    return f"{class_code}:{match.group(1)}"


def recreate_output_dirs():
    for split in ("train", "val", "test"):
        split_dir = DATASET_ROOT / split
        if split_dir.exists():
            shutil.rmtree(split_dir)
        for label in CLASS_MAP.values():
            (split_dir / label).mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)


def relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def split_cases(case_ids: list[str], rng: random.Random) -> dict[str, set[str]]:
    case_ids = list(case_ids)
    rng.shuffle(case_ids)
    total = len(case_ids)
    train_count = int(total * TRAIN_RATIO)
    val_count = int(total * VAL_RATIO)
    return {
        "train": set(case_ids[:train_count]),
        "val": set(case_ids[train_count:train_count + val_count]),
        "test": set(case_ids[train_count + val_count:]),
    }


def main():
    if abs(TRAIN_RATIO + VAL_RATIO + TEST_RATIO - 1.0) > 1e-9:
        raise ValueError("Train/val/test ratios must add up to 1.0")

    print("WoundAI Stage 2 - Wound Type Dataset Preparation")
    print("=" * 68)
    print(f"Dataset root : {DATASET_ROOT}")
    print(f"Seed         : {SEED}")
    print(f"Split        : {TRAIN_RATIO:.0%}/{VAL_RATIO:.0%}/{TEST_RATIO:.0%}")
    print()

    recreate_output_dirs()
    rng = random.Random(SEED)
    all_records = []
    duplicate_rows = []
    summary = {}

    for class_code, label in CLASS_MAP.items():
        source_files = (
            collect_images(RAW_TRAIN_ROOT / class_code)
            + collect_images(RAW_TEST_ROOT / class_code)
        )

        if not source_files:
            raise FileNotFoundError(
                f"No images found for class {class_code} in "
                f"{RAW_TRAIN_ROOT / class_code} or {RAW_TEST_ROOT / class_code}"
            )

        by_hash = defaultdict(list)
        for path in source_files:
            by_hash[sha256_file(path)].append(path)

        canonical_files = []
        for digest, paths in by_hash.items():
            paths = sorted(paths)
            kept = paths[0]
            canonical_files.append((digest, kept))
            for duplicate in paths[1:]:
                duplicate_rows.append({
                    "class_code": class_code,
                    "label": label,
                    "sha256": digest,
                    "kept_file": relative(kept),
                    "duplicate_file": relative(duplicate),
                })

        cases = defaultdict(list)
        for digest, path in canonical_files:
            case_id = case_id_from_filename(path, class_code)
            cases[case_id].append((digest, path))

        split_case_ids = split_cases(list(cases.keys()), rng)

        counts = {
            "cases_total": len(cases),
            "images_total": len(canonical_files),
            "duplicates_removed": len(source_files) - len(canonical_files),
            "train_images": 0,
            "val_images": 0,
            "test_images": 0,
        }

        for split, case_ids in split_case_ids.items():
            dest_dir = DATASET_ROOT / split / label
            for case_id in case_ids:
                for digest, source_path in cases[case_id]:
                    dest = dest_dir / source_path.name
                    if dest.exists():
                        dest = dest_dir / f"{source_path.stem}_{digest[:8]}{source_path.suffix.lower()}"
                    shutil.copy2(source_path, dest)
                    all_records.append({
                        "class_code": class_code,
                        "label": label,
                        "case_id": case_id,
                        "split": split,
                        "source_file": relative(source_path),
                        "copied_file": relative(dest),
                        "sha256": digest,
                    })
                    counts[f"{split}_images"] += 1

        summary[label] = counts

    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "class_code",
                "label",
                "case_id",
                "split",
                "source_file",
                "copied_file",
                "sha256",
            ],
        )
        writer.writeheader()
        writer.writerows(all_records)

    with DUPLICATES_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "class_code",
                "label",
                "sha256",
                "kept_file",
                "duplicate_file",
            ],
        )
        writer.writeheader()
        writer.writerows(duplicate_rows)

    print("Split summary")
    print("-" * 68)
    total_images = 0
    total_cases = 0
    total_dupes = 0

    for label, s in summary.items():
        total_images += s["images_total"]
        total_cases += s["cases_total"]
        total_dupes += s["duplicates_removed"]
        print(
            f"{label:>8}: "
            f"cases={s['cases_total']:3d} | "
            f"train={s['train_images']:3d} | "
            f"val={s['val_images']:3d} | "
            f"test={s['test_images']:3d} | "
            f"images={s['images_total']:3d} | "
            f"duplicates removed={s['duplicates_removed']:3d}"
        )

    print("-" * 68)
    print(f"TOTAL CASES              : {total_cases}")
    print(f"TOTAL UNIQUE IMAGES      : {total_images}")
    print(f"EXACT DUPLICATES REMOVED : {total_dupes}")
    print()
    print(f"Manifest          : {MANIFEST_PATH}")
    print(f"Duplicates report : {DUPLICATES_PATH}")
    print()
    print("Excluded classes: BG and N")
    print("Raw Train/Test folders were NOT modified.")


if __name__ == "__main__":
    main()
