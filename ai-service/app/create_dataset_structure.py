from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "datasets" / "wound_v1"
CLASSES = ["diabetic", "pressure", "surgical", "venous", "other_unknown"]

def main():
    for folder in ["raw", "processed", "metadata"]:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)

    for split in ["train", "val", "test"]:
        for class_name in CLASSES:
            (ROOT / split / class_name).mkdir(parents=True, exist_ok=True)

    manifest = ROOT / "metadata" / "dataset_manifest.csv"
    if not manifest.exists():
        manifest.write_text(
            "image_id,source_dataset,source_file,source_label,research_label,"
            "patient_or_group_id,split,sha256\n",
            encoding="utf-8"
        )

    print(f"Created: {ROOT}")
    print("datasets/ is ignored by Git.")

if __name__ == "__main__":
    main()
