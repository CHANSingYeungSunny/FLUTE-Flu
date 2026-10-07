"""
patchtst.py — PatchTST (channel-independent patching + Transformer encoder).
===========================================================================

ARCHITECTURE EQUIVALENCE
------------------------
Faithful to the published PatchTST (Nie et al., ICLR 2023) core:
  * channel-independent processing (each univariate series patched separately);
  * patch embedding via a shared Linear(patch_len -> d_model);
  * a Transformer encoder over patch tokens with learned positional embedding;
  * a flatten + Linear head to the horizon.

Deviations (explicitly recorded, all capacity/size choices):
  * this is NOT a pretrained / self-supervised model — it is trained
    end-to-end from scratch on the ILI task;
  * head is a single Linear over flattened tokens rather than a per-token
    "flatten head" variant of the reference repo.
Because the training regime differs from the pretrained variants, the runner
labels it "PatchTST (supervised re-implementation)" — see `architecture_report`.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from innovation import fidelity as FID
from innovation.interfaces import ForecastBackbone


class PatchTST(ForecastBackbone):
    name = "patchtst"

    def __init__(self, T: int, N: int, L: int, patch_len: int = 16, stride: int = 8,
                 d_model: int = 64, n_heads: int = 4, n_layers: int = 2,
                 dropout: float = 0.1):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.patch_len, self.stride = int(patch_len), int(stride)
        if self.T < self.patch_len:
            raise ValueError("patch_len must be <= T")
        self.n_patches = (self.T - self.patch_len) // self.stride + 1
        self.d_model = int(d_model)
        self.embed = nn.Linear(self.patch_len, self.d_model)
        self.pos = nn.Parameter(torch.zeros(1, self.n_patches, self.d_model))
        layer = nn.TransformerEncoderLayer(
            d_model=self.d_model, nhead=n_heads,
            dim_feedforward=self.d_model * 2, dropout=dropout,
            batch_first=True, activation="gelu")
        self.encoder = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.head = nn.Linear(self.n_patches * self.d_model, self.L)

    def forward(self, x, ctx=None):
        B, N, T = x.shape
        patches = x.reshape(B * N, T).unfold(
            dimension=-1, size=self.patch_len, step=self.stride)   # (B*N, P, pl)
        h = self.embed(patches) + self.pos
        h = self.encoder(h)                                        # (B*N, P, D)
        y = self.head(h.reshape(B * N, -1))                        # (B*N, L)
        return y.reshape(B, N, self.L)

    def architecture_report(self) -> dict:
        """Component-level provenance vs Nie et al., ICLR 2023 (PatchTST)."""
        return {
            "name": self.name,
            "display_name": "PatchTST-inspired (supervised, reduced-capacity "
                            "re-implementation)",
            "published": "PatchTST (Nie et al., ICLR 2023)",
            "fidelity": FID.INSPIRED_SIMPLIFICATION,
            "patch_len": self.patch_len, "stride": self.stride,
            "d_model": self.d_model, "n_patches": self.n_patches,
            "evidence": [
                "backbones/patchtst.py:54-55 channel-independent patching via unfold",
                "backbones/patchtst.py:43 shared Linear(patch_len -> d_model) patch embedding",
                "backbones/patchtst.py:44 learnable per-patch positional embedding",
                "backbones/patchtst.py:45-49 TransformerEncoder (dim_feedforward=2*d_model, gelu)",
                "backbones/patchtst.py:50,58 flatten head Linear(n_patches*d_model -> L)",
            ],
            "deviations": [
                {"component": "training regime",
                 "deviation": "no self-supervised pretraining (paper: pretrain + fine-tune)",
                 "file_line": "backbones/patchtst.py:14-19,68-71", "disclosed": True},
                {"component": "instance normalisation",
                 "deviation": "no RevIN / InstanceNorm applied before patching",
                 "file_line": "backbones/patchtst.py:53-55", "disclosed": True},
                {"component": "patching",
                 "deviation": "no end-padding to cover the tail of the series",
                 "file_line": "backbones/patchtst.py:41", "disclosed": True},
                {"component": "capacity",
                 "deviation": "d_model=64, n_heads=4, n_layers=2 (below paper scale)",
                 "file_line": "backbones/patchtst.py:33-35", "disclosed": True},
            ],
            "notes": ("core mechanism (channel-independent patches + Transformer "
                      "encoder + flatten head) matches PatchTST, but it is "
                      "trained from scratch with reduced capacity and no RevIN "
                      "-> labelled '-inspired', NOT the pretrained reference model"),
        }
