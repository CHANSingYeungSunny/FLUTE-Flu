"""film_gate.py — FiLM-style (gamma, beta) modulation from the text context."""

from __future__ import annotations

import torch
import torch.nn as nn

from innovation.interfaces import FusionModule


class FilmGateFusion(FusionModule):
    name = "film_gate"

    def __init__(self, d_model: int):
        super().__init__()
        self.d_model = int(d_model)
        self.to_gb = nn.Linear(self.d_model, 2 * self.d_model)

    def forward(self, htime, htext=None):
        if htext is None:
            return htime
        pooled = htext.mean(dim=1)                     # (B, D)
        gamma, beta = self.to_gb(pooled).chunk(2, dim=-1)
        return (1.0 + gamma).unsqueeze(1) * htime + beta.unsqueeze(1)
