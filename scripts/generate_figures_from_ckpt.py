#!/usr/bin/env python
"""generate_figures_from_ckpt.py — fast figure generation directly from a
checkpoint, proving the artifact can be loaded and evaluated WITHOUT re-training.

Loads results/ili/journal_evidence/full/horizon_L24/rep_01/checkpoints/
best_model_full_L24_rep01.pt, runs ONE forward-eval pass over the test window
(fixed_step aggregation = constant 1-week-ahead lead), and plots the continuous
evaluation in physical patient units with real CDC epiweek dates.
"""
import os
import sys
import time
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from configs import CONFIG, set_seed                       # noqa: E402
from textual_embedder import TextualInputEmbedder          # noqa: E402
from train_ablation import (load_and_normalize, build_prompt,  # noqa: E402
                            export_prediction_csv)
import make_submission_figures as msf                      # noqa: E402

import argparse
CKPT_DEFAULT = os.path.join(PROJECT_ROOT, "results", "ili", "journal_evidence",
                    "full", "horizon_L24", "rep_01", "checkpoints",
                    "best_model_full_L24_rep01.pt")
OUT_DEFAULT = os.path.join(PROJECT_ROOT, "results", "ili", "figures",
                   "fig_miflu_eval_continuous_L24_from_ckpt.png")
_ap = argparse.ArgumentParser()
_ap.add_argument("--ckpt", default=CKPT_DEFAULT)
_ap.add_argument("--device", default="cpu")
_ap.add_argument("--out", default=OUT_DEFAULT)
_ap.add_argument("--L", type=int, default=24)
_args = _ap.parse_args()
CKPT = _args.ckpt
OUT = _args.out
device = _args.device
L = _args.L

t0 = time.perf_counter()
set_seed(42)
T = CONFIG["T"]

data = load_and_normalize()
prompt = build_prompt(data["train_df"], T=T, L=L)
prompt_cache = TextualInputEmbedder(device=device)(prompt)

# Single forward-eval pass from the checkpoint (NO training).
OUT_DIR = os.path.dirname(os.path.dirname(CKPT))   # .../full/horizon_L24/rep_01
csv_path = export_prediction_csv(
    data, L, CONFIG, device, prompt_cache,
    CKPT, OUT_DIR,
    variant_name="full",
    use_text_ln=True, use_lora=True, gated_inject=False, unfreeze_first_k=0)
print(f"[eval]   inference done in {time.perf_counter()-t0:.2f}s  csv={csv_path}")

# Continuous evaluation via the canonical figure generator (fixed_step, real dates,
# COVID shading, peak + hallucination annotations). Returns the saved PNG path.
os.makedirs(msf.FIG_DIR, exist_ok=True)
out_path = msf.make_continuous(L, csv_path)
print(f"[fig]    saved {out_path}")
t1 = time.perf_counter()
print(f"RUNTIME_SECONDS_TOTAL={t1-t0:.2f}")
