"""
fusion_forecaster.py — a GENERIC testbed that composes the three plugins.
=====================================================================

This is deliberately NOT presented as a published architecture. It exists so
that TextEncoder x FusionModule can be exercised end-to-end through the same
ForecastBackbone contract, WITHOUT pretending it is a paper model.

Pipeline:  x (B,N,T)
             -> TimeTokenEncoder  -> htime (B, P, D)      (P = N * n_patches)
             -> text_proj(ctx)    -> htext (B, K, D)  or None
             -> FusionModule      -> fused (B, P, D)
             -> Linear head       -> y_hat (B, N, L)

When ctx is None (text_encoder="none") the fusion returns htime unchanged, so
the same object degenerates to a plain non-text backbone.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from innovation import fidelity as FID
from innovation.interfaces import ForecastBackbone

NAME = "fusion_forecaster"


class TimeTokenEncoder(nn.Module):
    def __init__(self, T: int, d_model: int, patch_len: int = 16, stride: int = 8):
        super().__init__()
        self.T, self.d_model = int(T), int(d_model)
        self.patch_len, self.stride = int(patch_len), int(stride)
        self.n_patches = (self.T - self.patch_len) // self.stride + 1
        self.embed = nn.Linear(self.patch_len, self.d_model)

    def forward(self, x):                        # (B,N,T) -> (B, N*P, D)
        B, N, T = x.shape
        patches = x.reshape(B * N, T).unfold(-1, self.patch_len, self.stride)
        h = self.embed(patches)                  # (B*N, P, D)
        return h.reshape(B, N * self.n_patches, self.d_model)


class TextFusionForecaster(ForecastBackbone):
    name = NAME

    def __init__(self, T: int, N: int, L: int, fusion, text_dim: int | None = None,
                 d_model: int = 64, patch_len: int = 16, stride: int = 8):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.time_enc = TimeTokenEncoder(T, d_model, patch_len, stride)
        self.P = self.N * self.time_enc.n_patches
        self.d_model = int(d_model)
        self.text_proj = (nn.Linear(int(text_dim), d_model)
                          if text_dim else None)
        self.fusion = fusion
        self.head = nn.Linear(self.P * d_model, self.N * self.L)

    def forward(self, x, ctx=None):
        htime = self.time_enc(x)                             # (B, P, D)
        htext = None
        if ctx is not None and self.text_proj is not None:
            htext = self.text_proj(ctx)                      # (B, K, D)
        fused = self.fusion(htime, htext)                    # (B, P, D)
        y = self.head(fused.reshape(htime.shape[0], -1))
        return y.reshape(htime.shape[0], self.N, self.L)

    def architecture_report(self) -> dict:
        return {
            "name": self.name,
            "display_name": "fusion_forecaster-inspired (plugin testbed; NOT a "
                            "paper architecture)",
            "published": None,
            "fidelity": FID.INSPIRED_SIMPLIFICATION,
            "evidence": [
                "backbones/fusion_forecaster.py:29-41 TimeTokenEncoder (patch + Linear)",
                "backbones/fusion_forecaster.py:54-57 text_proj + FusionModule + Linear head",
            ],
            "deviations": [
                {"component": "provenance",
                 "deviation": "not derived from any published architecture; it is a scaffold to exercise the plugin interfaces",
                 "file_line": "backbones/fusion_forecaster.py:5-7", "disclosed": True},
            ],
            "notes": ("generic fusion testbed (NOT a paper architecture): patch "
                      "time-encoder + TextEncoder + FusionModule + linear head; "
                      "used only to exercise the plugin interfaces and smoke tests"),
        }
