"""concat_projection.py — pool the text context and concatenate + project."""

from __future__ import annotations

import torch
import torch.nn as nn

from innovation.interfaces import FusionModule


class ConcatProjectionFusion(FusionModule):
    name = "concat_projection"

    def __init__(self, d_model: int):
        super().__init__()
        self.d_model = int(d_model)
        self.proj = nn.Linear(2 * self.d_model, self.d_model)

    def forward(self, htime, htext=None):
        if htext is None:
            return htime
        pooled = htext.mean(dim=1, keepdim=True)                 # (B,1,D)
        pooled = pooled.expand(-1, htime.shape[1], -1)           # (B,P,D)
        return self.proj(torch.cat([htime, pooled], dim=-1))     # (B,P,D)
