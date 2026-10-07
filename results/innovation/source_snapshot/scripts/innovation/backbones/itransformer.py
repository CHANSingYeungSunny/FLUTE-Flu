"""
itransformer.py — iTransformer (inverted: channels as tokens).
=============================================================

ARCHITECTURE EQUIVALENCE
------------------------
Faithful to the published iTransformer (Liu et al., ICLR 2024 Spotlight) core:
  * INVERT the axes: each VARIATE becomes a token whose embedding is the whole
    look-back series mapped by a shared Linear(T -> d_model);
  * a Transformer encoder attends ACROSS variates (not across time);
  * a shared Linear(d_model -> L) per variate token produces the horizon.

Deviations (capacity choices only, recorded in `architecture_report`):
  * trained from scratch on the ILI task (no pretraining);
  * no LayerNorm-over-variates variant beyond the encoder's own norms.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from innovation import fidelity as FID
from innovation.interfaces import ForecastBackbone


class ITransformer(ForecastBackbone):
    name = "itransformer"

    def __init__(self, T: int, N: int, L: int, d_model: int = 64,
                 n_heads: int = 4, n_layers: int = 2, dropout: float = 0.1):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.d_model = int(d_model)
        self.embed = nn.Linear(self.T, self.d_model)      # shared across variates
        self.pos = nn.Parameter(torch.zeros(1, self.N, self.d_model))
        layer = nn.TransformerEncoderLayer(
            d_model=self.d_model, nhead=n_heads,
            dim_feedforward=self.d_model * 2, dropout=dropout,
            batch_first=True, activation="gelu")
        self.encoder = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.head = nn.Linear(self.d_model, self.L)

    def forward(self, x, ctx=None):
        B, N, T = x.shape
        h = self.embed(x) + self.pos                     # (B, N, D) channels = tokens
        h = self.encoder(h)
        return self.head(h)                              # (B, N, L)

    def architecture_report(self) -> dict:
        """Component-level provenance vs Liu et al., ICLR 2024 (iTransformer).

        NOT labelled REFERENCE_FAITHFUL: two components deviate from the
        published model (one previously undisclosed), so the honest level is
        ALIGNED_WITH_DISCLOSED_DEVIATIONS.
        """
        return {
            "name": self.name,
            "display_name": "iTransformer (Liu et al., ICLR 2024) — aligned, "
                            "with disclosed deviations",
            "published": "iTransformer (Liu et al., ICLR 2024 Spotlight)",
            "fidelity": FID.REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS,
            "d_model": self.d_model,
            "evidence": [
                "backbones/itransformer.py:34 variate embedding = shared Linear(T -> d_model)",
                "backbones/itransformer.py:43-47 TransformerEncoder over variate TOKENS => cross-variate attention",
                "backbones/itransformer.py:41,47 shared Linear(d_model -> L) head per variate",
                "backbones/itransformer.py:36-40 norms are only the encoder layer's own LayerNorms",
            ],
            "deviations": [
                {"component": "normalisation",
                 "deviation": "no per-variate InstanceNorm/RevIN layer (paper normalises the variate representations)",
                 "file_line": "backbones/itransformer.py:36-40", "disclosed": True},
                {"component": "positional encoding",
                 "deviation": "adds a learnable PER-VARIATE positional embedding; the published iTransformer uses NO positional encoding (it is permutation-invariant over variates)",
                 "file_line": "backbones/itransformer.py:35", "disclosed": True},
                {"component": "capacity",
                 "deviation": "d_model=64, n_heads=4, n_layers=2",
                 "file_line": "backbones/itransformer.py:28-30", "disclosed": True},
            ],
            "notes": ("core inversion (variate-as-token) + cross-variate "
                      "attention + shared Linear(D->L) head match the paper, but "
                      "the missing instance normalisation and the ADDED "
                      "per-variate positional encoding are deviations; the PE "
                      "deviation is recorded here explicitly."),
        }
