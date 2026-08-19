# Dataset Governance

## Storage separation

### Supabase Storage
Used for application-uploaded images, inference history, and review workflows.

### Local research dataset
Used for model training, validation, testing, preprocessing, and reproducibility experiments.

## Initial research classes
- Diabetic
- Pressure
- Surgical
- Venous
- Other / Unknown

## Proposed source-label mapping
- Diabetic -> diabetic
- Pressure -> pressure
- Surgical -> surgical
- Venous -> venous
- Trauma -> other_unknown
- Arterial -> other_unknown
- Cellulitis -> other_unknown
- Miscellaneous -> other_unknown

Record source dataset, source image ID, original label, mapped label, patient/group ID, split, license/source citation, and checksum where available.

Do not split multiple images from the same patient across train and test when patient/group identifiers are available.
