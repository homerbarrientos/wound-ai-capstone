from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = (
    REPO_ROOT
    / "datasets"
    / "wound_type_v1"
    / "metadata"
    / "wound_type_split_manifest.csv"
)

print("WoundAI Stage 2 - Case and Exact Image Leakage Audit")
print("=" * 64)
print(f"Manifest: {MANIFEST}")
print()

if not MANIFEST.exists():
    raise FileNotFoundError(f"Manifest not found: {MANIFEST}")

case_records = defaultdict(list)
hash_records = defaultdict(list)

with MANIFEST.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        record = {
            "case_id": row["case_id"],
            "split": row["split"],
            "label": row["label"],
            "copied_file": row["copied_file"],
            "sha256": row["sha256"],
        }

        case_records[row["case_id"]].append(record)
        hash_records[row["sha256"]].append(record)

case_leaks = []
exact_image_leaks = []

for case_id, records in case_records.items():
    splits = {r["split"] for r in records}
    if len(splits) > 1:
        case_leaks.append((case_id, records))

for digest, records in hash_records.items():
    splits = {r["split"] for r in records}
    if len(splits) > 1:
        exact_image_leaks.append((digest, records))

print(f"Unique cases        : {len(case_records)}")
print(f"Unique image hashes : {len(hash_records)}")
print(f"Case leakage        : {len(case_leaks)}")
print(f"Exact image leakage : {len(exact_image_leaks)}")
print()

if case_leaks:
    print("WARNING: CASE IDs FOUND ACROSS MULTIPLE SPLITS")
    print("=" * 64)

    for i, (case_id, records) in enumerate(case_leaks, start=1):
        print()
        print(f"Case leak #{i}: {case_id}")
        for r in records:
            print(
                f"  [{r['split']}] {r['label']} -> {r['copied_file']}"
            )

if exact_image_leaks:
    print()
    print("WARNING: IDENTICAL IMAGES FOUND ACROSS MULTIPLE SPLITS")
    print("=" * 64)

    for i, (digest, records) in enumerate(exact_image_leaks, start=1):
        print()
        print(f"Exact-image leak #{i}")
        print(f"SHA256: {digest}")
        for r in records:
            print(
                f"  [{r['split']}] {r['label']} -> {r['copied_file']}"
            )

if not case_leaks and not exact_image_leaks:
    print("PASS")
    print("No case IDs cross train/validation/test.")
    print("No exact duplicate images cross train/validation/test.")
