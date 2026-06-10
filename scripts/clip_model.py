# Vendored from CardioMap models/clip_model.py (MLP only) so stage2_embed.py
# doesn't depend on the CardioMap repo's location on the cluster.

from __future__ import annotations

import torch
import torch.nn as nn


class MLP(nn.Module):
    """Two-layer projection MLP: in_dim -> hidden_dim -> out_dim."""

    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, out_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
