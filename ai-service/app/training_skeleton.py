"""
Training skeleton only.

Before training:
- finalize class definitions;
- verify dataset rights/consent and ethics requirements;
- ensure train/validation/test splits avoid patient/source leakage;
- document all preprocessing and augmentation choices.
"""

from pathlib import Path
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

CLASSES = [
    "abrasion",
    "laceration",
    "burn",
    "puncture",
    "surgical_wound",
    "other_unknown",
]

DATA_DIR = Path("./dataset")
OUTPUT = Path("./models/wound-efficientnet-b0.pt")
BATCH_SIZE = 16
EPOCHS = 10
LR = 1e-4

train_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(8),
    transforms.ColorJitter(brightness=0.10, contrast=0.10),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])

val_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def build_model():
    weights = EfficientNet_B0_Weights.DEFAULT
    model = efficientnet_b0(weights=weights)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(CLASSES))
    return model


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_ds = datasets.ImageFolder(DATA_DIR / "train", transform=train_tf)
    val_ds = datasets.ImageFolder(DATA_DIR / "val", transform=val_tf)

    if train_ds.classes != CLASSES:
        print("WARNING: ImageFolder alphabetical class order differs from CLASSES.")
        print("Dataset:", train_ds.classes)
        print("Expected:", CLASSES)
        print("Update the class mapping before using trained weights.")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)

    model = build_model().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()

    best_val = float("inf")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * x.size(0)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                loss = criterion(model(x), y)
                val_loss += loss.item() * x.size(0)

        train_loss /= len(train_ds)
        val_loss /= len(val_ds)
        print(f"epoch={epoch+1} train_loss={train_loss:.4f} val_loss={val_loss:.4f}")

        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), OUTPUT)

    print(f"Saved best weights to {OUTPUT}")


if __name__ == "__main__":
    train()
