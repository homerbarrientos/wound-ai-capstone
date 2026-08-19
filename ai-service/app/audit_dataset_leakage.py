from pathlib import Path
import csv
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    REPO_ROOT
    / "datasets"
    / "wound_v1"
    / "metadata"
    / "binary_split_manifest_deduplicated.csv"
)

print("WoundAI Phase 4C - Dataset Leakage Audit")
print("=" * 60)
print(f"Manifest: {MANIFEST}")
print()

if not MANIFEST.exists():
    raise FileNotFoundError(
        f"Manifest not found: {MANIFEST}"
    )

hash_records = defaultdict(list)

with MANIFEST.open(
    "r",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        hash_records[row["sha256"]].append({
            "split": row["split"],
            "label": row["label"],
            "source_file": row["source_file"],
            "copied_file": row["copied_file"],
        })


duplicate_groups = []
cross_split_leaks = []

for sha256, records in hash_records.items():

    if len(records) > 1:
        duplicate_groups.append(
            (sha256, records)
        )

    splits = {
        record["split"]
        for record in records
    }

    if len(splits) > 1:
        cross_split_leaks.append(
            (sha256, records)
        )


print(f"Unique image hashes : {len(hash_records)}")
print(f"Duplicate groups    : {len(duplicate_groups)}")
print(f"Cross-split leaks   : {len(cross_split_leaks)}")
print()


if cross_split_leaks:

    print("WARNING: IDENTICAL IMAGES FOUND ACROSS SPLITS")
    print("=" * 60)

    for number, (sha256, records) in enumerate(
        cross_split_leaks,
        start=1
    ):

        print()
        print(f"Leak #{number}")
        print(f"SHA256: {sha256}")

        for record in records:
            print(
                f"  [{record['split']}] "
                f"{record['label']} -> "
                f"{record['copied_file']}"
            )

else:

    print("PASS")
    print("No exact duplicate images were found across")
    print("train, validation, and test splits.")