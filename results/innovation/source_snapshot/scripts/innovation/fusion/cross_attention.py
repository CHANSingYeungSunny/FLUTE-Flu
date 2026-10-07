"""cross_attention.py — time patches attend to text tokens (residual + LN)."""

from __future__ import annotations

import torch
import torch.nn as nn

from innovation.interfaces import FusionModule


class CrossAttentionFusion(FusionModule):
    name = "cross_attention"

    def __init__(self, d_model: int, n_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.d_model = int(d_model)
        self.attn = nn.MultiheadAttention(self.d_model, n_heads,
                                          dropout=dropout, batch_first=True)
        self.ln = nn.LayerNorm(self.d_model)

    def forward(self, htime, htext=None):
        if htext is None:
            return htime
        out, _ = self.attn(query=htime, key=htext, value=htext,
                           need_weights=False)
        return self.ln(htime + out)
