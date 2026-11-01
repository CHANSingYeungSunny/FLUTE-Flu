#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verify both output-head variants run and produce correct shapes."""
import os
import sys

sys.path.insert(0, r"c:/Users/Asus/Desktop/FYP code/MLFlu/scripts")
os.environ.setdefault("HF_HUB_OFFLINE", "0")

import torch
from miflu_model import MIFlu

torch.manual_seed(0)
T, N, L, B = 104, 7, 24, 2

for head in (True, False):
    m = MIFlu(N=N, T=T, L=L, Lp=24, S=2, K=6, lora_r=4, device="cpu",
              flatten_head=head)
    x = torch.randn(B, N, T)
    htext = torch.randn(B, 367, 768)
    y, y_phys, means, stdevs = m(x, htext)
    ok = tuple(y.shape) == (B, N, L)
    n_head = sum(p.numel() for p in m.forecasting_llm.output_projection.parameters())
    print(f"flatten_head={str(head):<5} out={tuple(y.shape)} "
          f"expected={(B, N, L)} {'OK' if ok else 'FAIL'}  head_params={n_head:,}")
    assert ok

print("\nBOTH HEAD VARIANTS OK")
