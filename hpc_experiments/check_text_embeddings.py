#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_text_embeddings.py — Are the MIFlu text embeddings constant?

The audit claims the text pathway is degenerate ("constant vectors"). If our text
embeddings are constant across the series, MIFlu cannot use its multimodal pathway,
which is the paper's core contribution — and that would be a plausible cause of the
remaining ~26% MSE gap. Verify directly.
"""
import os

import numpy as np

BASE = r"c:/Users/Asus/Desktop/FYP code/MLFlu/recovery/author_repo/dataset/illness/text_emb"

for L in (24, 36, 48, 60):
    path = os.path.join(BASE, f"text_emb_label_0507_{L}.txt")
    if not os.path.exists(path):
        print(f"L={L}: MISSING")
        continue
    a = np.loadtxt(path)
    print(f"\nL={L}: shape={a.shape}  size={os.path.getsize(path)/1e6:.2f} MB")
    # constant across rows?
    row_std = a.std(axis=0).mean()          # variation ACROSS time steps
    col_std = a.std(axis=1).mean()          # variation WITHIN a step
    print(f"  mean std ACROSS rows (steps): {row_std:.6f}")
    print(f"  mean std WITHIN a row       : {col_std:.6f}")
    n_unique_rows = len(np.unique(a, axis=0))
    print(f"  unique rows: {n_unique_rows} / {a.shape[0]}")
    if a.shape[0] > 1:
        print(f"  first row  : {a[0][:5]}")
        print(f"  second row : {a[1][:5]}")
        print(f"  row0 == row1 ? {np.allclose(a[0], a[1])}")
    if row_std < 1e-8:
        print("  => CONSTANT across time steps (degenerate text pathway)")
    else:
        print("  => VARIES across time steps (text pathway carries information)")
