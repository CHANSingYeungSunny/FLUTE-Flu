"""
gpt2_miflu_adapter.py — control group: the ORIGINAL MIFlu, wrapped.
===================================================================

WHY AN ADAPTER
--------------
The innovation experiments must compare against the repo's existing MIFlu
WITHOUT maintaining a second copy of it (a second copy would drift). This
adapter subclasses nothing and re-implements nothing: it builds the existing
`scripts/miflu_model.MIFlu` and exposes it through the ForecastBackbone
contract, returning the z-space forecast (`yh_rev`).

`htext` handed to MIFlu is the frozen-GPT2 context produced by the gpt2 text
encoder. `train_mean`/`train_std` are only needed for MIFlu's physical branch,
which we do not use here (we invert with the scaler ourselves).

Availability: requires the local gpt2 cache + transformers (offline). If the
cache is missing, the backbone reports unavailable (never downloads).
"""

from __future__ import annotations

import os

import torch

from innovation import fidelity as FID
from innovation.interfaces import ForecastBackbone

NAME = "gpt2_miflu"


def gpt2_cache_available() -> bool:
    hub = os.path.expanduser(os.path.join("~", ".cache", "huggingface", "hub"))
    return os.path.isdir(os.path.join(hub, "models--gpt2"))


class GPT2MifluAdapter(ForecastBackbone):
    name = NAME

    def __init__(self, T: int, N: int, L: int, device: str = "cpu",
                 K: int = 6, lora_r: int = 4, Lp: int = 24, S: int = 2,
                 use_text_ln: bool = True, use_lora: bool = True,
                 gated_inject: bool = False, unfreeze_first_k: int = 0,
                 multimodal: bool = True):
        super().__init__()
        from miflu_model import MIFlu  # existing, already-validated model
        # without_multimodality must remove EVERY text/multimodal contribution,
        # not merely switch off a LayerNorm or gating switch.
        self.multimodal = bool(multimodal)

        self.T, self.N, self.L = int(T), int(N), int(L)
        self.device = device
        self.inner = MIFlu(N=N, T=T, L=L, Lp=Lp, S=S, K=K, lora_r=lora_r,
                           device=device, use_text_ln=use_text_ln,
                           use_lora=use_lora, gated_inject=gated_inject,
                           unfreeze_first_k=unfreeze_first_k)

    def forward(self, x, ctx=None):
        tm = torch.zeros(1, self.N, 1, device=x.device)
        ts = torch.ones(1, self.N, 1, device=x.device)
        if not self.multimodal and ctx is not None:
            # true removal: the text contribution is replaced by exact zeros
            ctx = torch.zeros_like(ctx)
        yh_rev, _yh_phys, _m, _s = self.inner(x, htext=ctx,
                                              train_mean=tm, train_std=ts)
        return yh_rev

    def architecture_report(self) -> dict:
        return {
            "name": self.name,
            "display_name": "MIFlu (IEEE JBHI 2025) — exact adapter",
            "published": "MIFlu (IEEE JBHI 2025, DOI 10.1109/JBHI.2025.3561214)",
            "fidelity": FID.REFERENCE_FAITHFUL,
            "evidence": [
                "backbones/gpt2_miflu_adapter.py:45 imports the existing miflu_model.MIFlu",
                "backbones/gpt2_miflu_adapter.py:49-52 builds the existing MIFlu unchanged",
                "backbones/gpt2_miflu_adapter.py:54-59 unpacks the 4-tuple and returns yh_rev (z-space) only",
                "miflu_model.py:522-575 MIFlu.forward returns (y_hat_rev, y_phys, means, stdevs)",
            ],
            "deviations": [
                {"component": "physical branch",
                 "deviation": "adapter passes train_mean=0/train_std=1 placeholders and discards y_phys (the runner inverts with the scaler instead)",
                 "file_line": "backbones/gpt2_miflu_adapter.py:55-59", "disclosed": True},
            ],
            "notes": ("adapter around the repo's existing, already-validated "
                      "MIFlu; forward delegates to MIFlu and returns the z-space "
                      "prediction unchanged"),
        }
