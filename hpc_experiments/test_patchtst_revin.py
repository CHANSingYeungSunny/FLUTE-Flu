#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smoke test for the RevIN-enabled PatchTST fix.

Run from the scripts/ directory so `innovation` is importable:
    cd scripts && python ../hpc_experiments/test_patchtst_revin.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import torch
from innovation.backbones.patchtst import PatchTST

torch.manual_seed(0)

T, N, L, B = 104, 7, 24, 4

# --- default (RevIN on, paper-scale capacity) ---
m = PatchTST(T=T, N=N, L=L)
x = torch.randn(B, N, T)
y = m(x)
print(f"default  : in={tuple(x.shape)} out={tuple(y.shape)}  (expect {(B, N, L)})")
assert tuple(y.shape) == (B, N, L), f"shape mismatch {tuple(y.shape)}"

# RevIN should put the forecast back on the input's scale:
# a shifted/scaled input should produce a correspondingly shifted/scaled forecast.
x2 = x * 3.0 + 10.0
y2 = m(x2)
scale_ok = (y2 - 10.0).abs().mean() / (y * 3.0).abs().mean()
print(f"revin scale check: ratio={scale_ok.item():.4f} (expect ~1.0 if denorm works)")
assert 0.5 < scale_ok.item() < 2.0, "RevIN denorm did not restore input scale"

# --- RevIN off (old behaviour) for comparison ---
m0 = PatchTST(T=T, N=N, L=L, use_revin=False, d_model=64, n_heads=4, n_layers=2)
y0 = m0(x)
print(f"revin=off: out={tuple(y0.shape)} OK")

rep = m.architecture_report()
print(f"\nreport: {rep['display_name']}")
print(f"  patch_len={rep['patch_len']} stride={rep['stride']} "
      f"d_model={rep['d_model']} n_patches={rep['n_patches']} revin={rep['use_revin']}")
print(f"  deviations remaining: {[d['component'] for d in rep['deviations']]}")

n_params = sum(p.numel() for p in m.parameters())
print(f"  trainable params: {n_params:,}")
print("\nPATCHTST REVIN FIX SMOKE TEST PASSED")
