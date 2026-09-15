"""
cnn_patch_model.py
-------------------
A small CNN that learns directly from raw Sentinel-2 patches (6 bands, 64x64)
instead of hand-engineered indices — this is the genuine "beyond the cited
literature" move: Zhao et al. 2025 (Malkansu) and Singh et al. 2023 both rely
on hand-engineered band ratios / PCA components fed into RF/XGBoost/NB.
A CNN can pick up spatial texture patterns (structural density, alteration
halos) that a human never explicitly encoded as a formula.

IMPORTANT — why this does NOT replace your RF/XGBoost prospectivity model:
Real, confidently-labeled manganese points are scarce (the Malkansu study
itself trained on only 100 points, 20 of them positive). A CNN with millions
of parameters will overfit on a dataset that small. So this model is trained
with heavy regularization + data augmentation on your combined real+synthetic
patch set, and its OUTPUT IS ONE MORE VOTE in the ensemble overlay — not a
replacement. This mirrors the Malkansu paper's own approach of combining
multiple models (RF + NB + XGBoost) rather than trusting a single algorithm.

pip install torch --break-system-packages
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class ManganesePatchCNN(nn.Module):
    """Input: (batch, 6, 64, 64) -> Output: scalar prospectivity logit."""

    def __init__(self, in_channels=6):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.dropout = nn.Dropout(0.4)  # aggressive — dataset is small
        self.fc1 = nn.Linear(64 * 8 * 8, 64)
        self.fc2 = nn.Linear(64, 1)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))   # 64 -> 32
        x = self.pool(F.relu(self.conv2(x)))   # 32 -> 16
        x = self.pool(F.relu(self.conv3(x)))   # 16 -> 8
        x = x.flatten(1)
        x = self.dropout(F.relu(self.fc1(x)))
        return torch.sigmoid(self.fc2(x))      # 0-1 prospectivity score


def normalize_patch(patch: np.ndarray) -> np.ndarray:
    """Sentinel-2 SR reflectance is ~0-10000 scaled; normalize to 0-1."""
    return np.clip(patch / 10000.0, 0, 1)


def predict_cnn_score(model: ManganesePatchCNN, patch: np.ndarray) -> float:
    """
    patch: (64, 64, 6) numpy array from satellite_extraction.export_patch_array()
    Returns a single 0-1 prospectivity score from the CNN branch.
    """
    model.eval()
    x = normalize_patch(patch)
    x = torch.tensor(x, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)  # (1,6,64,64)
    with torch.no_grad():
        score = model(x).item()
    return score


def ensemble_score(rf_score, xgb_score, nb_score, cnn_score, weights=None):
    """
    Combines all four model outputs into one consensus prospectivity score —
    same principle as the Malkansu paper's algebraic overlay of RF/NB/XGBoost,
    extended with a 4th, spatially-aware CNN vote.

    weights: optional dict, e.g. {"rf": 0.3, "xgb": 0.25, "nb": 0.2, "cnn": 0.25}
    Defaults to equal weighting; tune once you have validation AUCs per model
    (give more weight to whichever model scores highest AUC, same logic the
    Malkansu paper used to justify favoring their NB model's output).
    """
    if weights is None:
        weights = {"rf": 0.25, "xgb": 0.25, "nb": 0.25, "cnn": 0.25}

    scores = {"rf": rf_score, "xgb": xgb_score, "nb": nb_score, "cnn": cnn_score}
    combined = sum(scores[k] * weights[k] for k in weights)
    return {
        "combined_score": round(combined, 4),
        "individual_scores": scores,
        "weights_used": weights,
    }


def train_stub(train_loader, val_loader, epochs=30, lr=1e-3, device="cpu"):
    """
    Skeleton training loop — plug in your DataLoader built from patches +
    binary mine/no-mine labels (real MOIL points + synthetic negatives,
    same 1:4 positive:negative ratio the Malkansu paper used to avoid
    class imbalance issues).
    """
    model = ManganesePatchCNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.BCELoss()

    best_val_loss = float("inf")
    for epoch in range(epochs):
        model.train()
        for patches, labels in train_loader:
            patches, labels = patches.to(device), labels.to(device).float()
            optimizer.zero_grad()
            preds = model(patches).squeeze(1)
            loss = criterion(preds, labels)
            loss.backward()
            optimizer.step()

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for patches, labels in val_loader:
                patches, labels = patches.to(device), labels.to(device).float()
                preds = model(patches).squeeze(1)
                val_loss += criterion(preds, labels).item()
        val_loss /= max(len(val_loader), 1)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), "cnn_patch_v1.pt")

        print(f"epoch {epoch+1}/{epochs}  val_loss={val_loss:.4f}")

    return model
