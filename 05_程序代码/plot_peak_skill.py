#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""plot_peak_skill.py — the 28-arm PTE/PIE heat map used in the reports.

Reads `02_数字表格/BENCH_PTE_PIE_BY_STEP.csv` (one row per model x horizon x
step, already a mean over the three seeds) and draws two panels:

    left  : mean PTE (weeks) per fixed step, pass threshold 1 week
    right : mean PIE (%)    per fixed step, pass threshold 25 %

A cell is a pass only if BOTH hold; passing cells are boxed in blue.  The rows
are ordered by the four-horizon mean MSE, so the accuracy ranking can be read
top-down and the calibration inversion is visible against it.

    python 05_程序代码/plot_peak_skill.py
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PT = os.path.join(ROOT, "02_数字表格")
OUT = os.path.join(ROOT, "01_最终报告", "figures", "fig_pte_pie_heatmap.png")

NAMES = {
    "miflu": "MIFlu", "patchtst": "PatchTST", "nlinear": "NLinear", "dnn": "DNN",
    "timecma_llm": "TimeCMA", "gradient_boosting": "Gradient Boosting", "knn": "KNN",
    "random_forest": "Random Forest", "itransformer": "iTransformer",
    "decision_tree": "Decision Tree", "gru": "GRU", "lstm": "LSTM", "rnn": "RNN",
    "qwen_time_llm": "Qwen-Time", "svr": "SVR", "calf_llm": "CALF", "cnn": "CNN",
    "qwen25_1_5b": "Qwen2.5-1.5B",
    "ds_r1_distill_qwen1_5b": "R1-Distill-Qwen-1.5B",
    "ds_r1_distill_qwen7b": "R1-Distill-Qwen-7B",
    "ds_r1_distill_llama8b": "R1-Distill-Llama-8B",
    "ds_r1_distill_qwen14b": "R1-Distill-Qwen-14B",
    "ds_r1_distill_32b": "R1-Distill-Qwen-32B",
    "tencent_contextpilot_8b": "ContextPilot-8B",
    "tencent_contextpilot_14b": "ContextPilot-14B",
    "tencent_hunyuan_1p8b_instruct": "Hunyuan-1.8B",
    "tencent_hunyuan_4b_instruct": "Hunyuan-4B",
    "tencent_hunyuan_7b_instruct": "Hunyuan-7B",
}


def main():
    pte = pd.read_csv(os.path.join(PT, "BENCH_PTE_PIE_BY_STEP.csv"))
    mse = pd.read_csv(os.path.join(PT, "BENCH_MSE_BY_MODEL_L.csv"))
    mean_mse = mse.groupby("model")["mse_7var_z"].mean()
    order = list(mean_mse.sort_values().index)

    P = pte.pivot_table(index="model", columns="step", values="PTE_wk", aggfunc="mean").loc[order]
    I = pte.pivot_table(index="model", columns="step", values="PIE_pct", aggfunc="mean").loc[order]
    # A box marks a (model, step) whose four-horizon MEAN meets both thresholds.
    # The per-horizon counts (4/16 for NLinear and for MIFlu) are stated in the
    # subtitle and in the tables; a mean-level box is a description, not a count.
    ok = (P <= 1.0) & (I <= 25.0)

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 7.9),
                             gridspec_kw={"width_ratios": [1, 1], "wspace": 0.05})
    for ax, M, title, vmax, fmt in (
            (axes[0], P.values, "mean PTE (weeks)   [pass: \u2264 1 week]", 5.0, "{:.2f}"),
            (axes[1], I.values, "mean PIE (%)   [pass: \u2264 25 %]", 82.0, "{:.1f}")):
        im = ax.imshow(M, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=vmax)
        ax.set_xticks(range(4))
        ax.set_xticklabels(["s0\n1 wk", "s1\n2 wk", "s2\n3 wk", "s3\n4 wk"], fontsize=7)
        ax.set_yticks(range(len(order)))
        if ax is axes[0]:
            ax.set_yticklabels([NAMES.get(m, m) for m in order], fontsize=7)
            ax.tick_params(axis="y", pad=1)
        else:
            ax.set_yticklabels([])
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                ax.text(j, i, fmt.format(M[i, j]), ha="center", va="center", fontsize=6.4,
                        color=("white" if M[i, j] > 0.72 * vmax else "black"))
                if ok.values[i, j]:
                    ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                           edgecolor="#123B8C", lw=2.0))
        ax.set_title(title, fontsize=8.2, fontweight="bold", pad=4)
        ax.tick_params(length=0)

    n_pass = int(ok.values.sum())
    fig.suptitle("Peak skill by fixed step \u2014 28 benchmark arms\n"
                 "mean over L = 24/36/48/60; seeds 42/43/44.  A box marks a (model, step) whose mean meets "
                 "PTE \u2264 1 wk AND PIE \u2264 25 %.",
                 fontsize=8.6, fontweight="bold", y=0.985)
    fig.text(0.5, 0.012,
             "Rows ordered by the four-horizon mean 7-variable MSE (best at the top); green = low error, "
             "red = high.  Per-cell passes: NLinear 4/16 (all step 0) \u00b7 MIFlu 4/16 (3 step-0 + L48 step 1) "
             "\u00b7 PatchTST 0/16.\n"
             "Windows (W//16)*16 = 160/144/144/128; A100-SXM4-80GB, partition stingy, CityU HPC Burgundy.",
             ha="center", fontsize=6.2, color="#444444")
    fig.subplots_adjust(top=0.90, bottom=0.075, left=0.20, right=0.985, wspace=0.06)
    fig.savefig(OUT, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}  ({n_pass} passing cells of {ok.size})")


if __name__ == "__main__":
    main()
