#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Benchmark analysis over the expanded cells (16 models x 4 horizons x 3 seeds,
plus MIFlu when its predictions have been imported).

Inputs : hpc_results/expanded_runs/<model>_L<L>_s<seed>/pred_*.npz
Scaler : data/scaler_miflu_author966.json (train-only fit)
Outputs: paper_tables/BENCH_*.csv  and a console ranking.

Metric split (see docs/METHODOLOGY_METRICS_AND_SPLIT.md):
  * MSE/MAE of the 7-variable aggregate in z-space  -> reproduction-comparable
  * PTE/PIE on ILITOTAL (de-normalised to patients) -> operational comparison

EVALUATION WINDOWS — one rule, MIFlu's (see scripts/eval_windows.py)
--------------------------------------------------------------------
The reproduction scores only the first `(W // 16) * 16` test windows, because
`train_miflu.train_L` builds its test loader with `drop_last=True`. Every model
and every horizon here is scored on exactly that same set, so the table is
comparable with MIFlu: 160/144/144/128 windows at L = 24/36/48/60 out of the
170/158/146/134 stored in the npz. `n_eval_windows` records the number for every
row, `n_windows_available` the export size, and the script asserts that both are
uniform across arms at each horizon.

Array layout: every cell stores `pred` and `target` shaped **(W, 7, L)** — window
axis 0, variable axis 1, lead axis 2 — which `eval_windows.check_cell_layout()`
asserts before slicing.

NaN-tolerant by design (MIFlu merge)
------------------------------------
A cell whose npz carries `partial=True` was exported with fewer than 7 channels
(the reproduction runner exports ILITOTAL only), so every channel except index 4
is NaN. Such a cell must NEVER receive a 7-variable number: its `mse_7var_z` /
`mae_7var_z` are written as NaN and `n_channels_used` records how many channels
actually contributed. Full 7-channel cells report `n_channels_used = 7` and their
numbers are computed with plain `np.mean`.
"""
from __future__ import annotations
import glob, json, os, re, sys
import numpy as np, pandas as pd
from scipy.signal import find_peaks

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)                 # makes `eval_windows` importable from anywhere
from eval_windows import eval_slice, crop, assert_uniform, report  # noqa: E402

EXP = os.path.join(ROOT, "hpc_results", "expanded_runs")
SC = json.load(open(os.path.join(ROOT, "data", "scaler_miflu_author966.json")))
MEAN = np.array(SC["mean"], float); STD = np.array(SC["std"], float)
VAR = SC["var_cols"]
FAMILY = {
    "nlinear": "linear",   # sole linear model; DLinear is EXCLUDED entirely
    "patchtst": "transformer", "itransformer": "transformer",
    "dnn": "neural", "cnn": "neural", "rnn": "neural", "lstm": "neural", "gru": "neural",
    "decision_tree": "classical_ml", "random_forest": "classical_ml",
    "gradient_boosting": "classical_ml", "svr": "classical_ml", "knn": "classical_ml",
    "miflu": "llm", "timecma_llm": "llm", "qwen_time_llm": "llm", "calf_llm": "llm",
}
STEPS = [0, 1, 2, 3]
ILI = 4
EXCLUDE = {"dlinear"}          # HARD RULE 3: never in a ranking, table or figure
NAN = float("nan")


def _mean(a):
    """Mean that is bit-identical to np.mean when nothing is NaN.

    MIFlu's ILITOTAL-only export leaves 6 of 7 channels NaN, so a plain mean would
    return NaN. Using nanmean only when NaNs are actually present keeps every full
    cell's number bit-identical to a plain mean.
    """
    a = np.asarray(a, float)
    return float(np.mean(a)) if np.isfinite(a).all() else float(np.nanmean(a))


def _absmean(a):
    a = np.asarray(a, float)
    return float(np.mean(np.abs(a))) if np.isfinite(a).all() else float(np.nanmean(np.abs(a)))


def _n_channels(err):
    """How many of the 7 variable channels carry at least one finite error.

    `err` is `(S, W, 7, L)` for a cell, or `(S, W, 7, 1)` for a single step (the
    caller keeps a length-1 lead axis so the last two axes are ALWAYS
    (variable, lead) — passing `err[:, :, :, s]` instead would reinterpret the
    window axis as variables and report `n_channels_used == W`).
    """
    e = np.asarray(err, float)
    e = e.reshape(-1, e.shape[-2], e.shape[-1])
    return int(sum(bool(np.isfinite(e[:, c, :]).any()) for c in range(e.shape[1])))


def load():
    """Load every cell, cropped to the shared evaluation windows.

    Returns {(model, L): [(pred, target, target_start_row, partial,
                           W_available, n_eval), ...]} with pred/target already
    sliced to `eval_slice(W)` on the window axis.
    """
    cells = {}
    for p in sorted(glob.glob(os.path.join(EXP, "**", "pred_*.npz"), recursive=True)):
        m = re.search(r"pred_(.+)_L(\d+)_s(\d+)\.npz$", p)
        if not m: continue
        if m.group(1) in EXCLUDE: continue          # DLinear: never a competitor
        if m.group(1) not in FAMILY: continue
        L = int(m.group(2))
        d = np.load(p)
        partial = bool(np.asarray(d["partial"]).ravel()[0]) if "partial" in d.files else False
        pred, target, ts, W_avail, n_ev = crop(
            d["pred"], d["target"], d["target_start_row"], L=L, label=os.path.basename(p))
        if n_ev == 0:
            raise ValueError(f"{p}: eval_slice({W_avail}) == 0 — fewer windows than one "
                             f"test batch; refusing to write an empty row")
        cells.setdefault((m.group(1), L), []).append(
            (pred, target, ts, partial, W_avail, n_ev))
    return cells

def seasonal_pte_pie(wk, gt, pr):
    rng = float(gt.max() - gt.min())
    if rng <= 0: return None
    gi, _ = find_peaks(gt, prominence=0.15 * rng, distance=15)
    if len(gi) == 0: gi = np.array([int(np.argmax(gt))])
    P, E = [], []
    for g in gi:
        wg, vg = int(wk[g]), float(gt[g])
        mask = np.abs(wk - wg) <= 8
        if not mask.any() or vg == 0: continue
        k = int(np.argmax(pr[mask]))
        P.append(abs(int(wk[mask][k]) - wg))
        E.append(abs(float(pr[mask][k]) - vg) / abs(vg) * 100)
    if not P: return None
    return float(np.mean(P)), float(np.mean(E))

cells = load()
_avail = {L: max(v[4] for v in lst) for (mo, L), lst in cells.items()}
print(f"[eval-window] rule applies to every model and horizon; "
      f"available windows measured on disk:")
report(horizons=tuple(sorted(_avail)), available=_avail)

rows, steprows, pterows = [], [], []
for (model, L), lst in sorted(cells.items()):
    P = np.stack([a for a, _, _, _, _, _ in lst])
    T = np.stack([b for _, b, _, _, _, _ in lst])
    W = np.stack([c for _, _, c, _, _, _ in lst])
    W_avail = {v[4] for v in lst}
    N_EV = {v[5] for v in lst}
    assert len(W_avail) == 1 and len(N_EV) == 1, (model, L, W_avail, N_EV)
    W_avail, n_ev = W_avail.pop(), N_EV.pop()
    # layout guard on the STACKED tensor: (S, W, 7, L) -> window axis 1
    assert P.shape[1] == n_ev and P.shape[2] == 7 and P.shape[3] == L, \
        f"{model} L={L}: stacked shape {P.shape} != (S,{n_ev},7,{L})"
    assert T.shape == P.shape and W.shape == (P.shape[0], n_ev)
    err = P - T
    nch = _n_channels(err)
    complete7 = (nch == 7)
    # A cell with fewer than 7 channels must never be given a 7-variable number.
    mse = _mean(err ** 2) if complete7 else NAN
    mae = _absmean(err) if complete7 else NAN
    rows.append({"model": model, "family": FAMILY.get(model, "?"), "L": L,
                 "n_seeds": len(lst), "mse_7var_z": mse, "mae_7var_z": mae,
                 "n_channels_used": nch,
                 "n_windows_available": W_avail, "n_eval_windows": n_ev,
                 "windows_discarded": W_avail - n_ev,
                 "mse_ilitotal_z": _mean(err[:, :, ILI, :] ** 2),
                 "mae_ilitotal_z": _absmean(err[:, :, ILI, :]),
                 "mse_ilitotal_phys": _mean(err[:, :, ILI, :] ** 2) * STD[ILI] ** 2,
                 "mae_ilitotal_phys": _absmean(err[:, :, ILI, :]) * STD[ILI],
                 "partial_export": (not complete7)})
    for s in STEPS:
        if s >= L: continue
        e = err[:, :, :, s]                      # (S, W, 7) — NOT a channel slice
        steprows.append({"model": model, "family": FAMILY.get(model, "?"), "L": L,
                         "step": s, "weeks_ahead": s + 1,
                         "mse_7var_z": _mean(e ** 2) if complete7 else NAN,
                         "mae_7var_z": _absmean(e) if complete7 else NAN,
                         "n_channels_used": _n_channels(e[:, :, :, None]),
                         "n_windows_available": W_avail, "n_eval_windows": n_ev})
        # PTE/PIE on the de-normalised ILITOTAL series, mean over seeds
        Ps, Es = [], []
        for i in range(P.shape[0]):
            wk = W[i] + s
            gt = T[i, :, ILI, s] * STD[ILI] + MEAN[ILI]
            pr = P[i, :, ILI, s] * STD[ILI] + MEAN[ILI]
            r = seasonal_pte_pie(wk, gt, pr)
            if r: Ps.append(r[0]); Es.append(r[1])
        if Ps:
            pte, pie = float(np.mean(Ps)), float(np.mean(Es))
            pterows.append({"model": model, "family": FAMILY.get(model, "?"),
                            "L": L, "step": s, "weeks_ahead": s + 1,
                            "PTE_wk": pte, "PIE_pct": pie,
                            "kramer_shaman_pass": bool(pte <= 1.0 and pie <= 25.0),
                            "n_windows_available": W_avail, "n_eval_windows": n_ev})

os.makedirs(os.path.join(ROOT, "paper_tables"), exist_ok=True)
df = pd.DataFrame(rows);  df.to_csv(os.path.join(ROOT, "paper_tables", "BENCH_MSE_BY_MODEL_L.csv"), index=False)
ds = pd.DataFrame(steprows); ds.to_csv(os.path.join(ROOT, "paper_tables", "BENCH_MSE_BY_STEP.csv"), index=False)
dp = pd.DataFrame(pterows)
dp.to_csv(os.path.join(ROOT, "paper_tables", "BENCH_PTE_PIE_BY_STEP.csv"), index=False)


def assert_no_dlinear(*frames):
    """HARD RULE 3: DLinear is excluded everywhere -- assert it never leaks in."""
    for name, f in frames:
        if f is None or not len(f):
            continue
        for col in ("model", "family"):
            if col in f.columns:
                hit = f[col].astype(str).str.lower().str.contains("dlinear|linear_ref")
                assert not hit.any(), f"DLinear found in {name} column {col}"
        if isinstance(f.index, pd.MultiIndex) or (f.index.name in ("family", "side")):
            hit = f.index.astype(str).str.lower().str.contains("dlinear|linear_ref")
            assert not hit.any(), f"DLinear found in {name} index"


# family / side summaries (NaN-safe: a partial export cannot drag a family mean)
d = df.copy(); d["side"] = np.where(d.family == "llm", "LLM", "non-LLM")
fam = d.groupby(["family", "L"])["mse_7var_z"].mean().unstack("L").round(4)
fam["mean"] = fam.mean(axis=1)
side = d.groupby(["side", "L"])["mse_7var_z"].mean().unstack("L").round(4)
side["mean"] = side.mean(axis=1)
fam.to_csv(os.path.join(ROOT, "paper_tables", "BENCH_MSE_BY_FAMILY.csv"))
side.to_csv(os.path.join(ROOT, "paper_tables", "BENCH_MSE_BY_SIDE.csv"))

assert_no_dlinear(("BENCH_MSE_BY_MODEL_L", df), ("BENCH_MSE_BY_STEP", ds),
                  ("BENCH_PTE_PIE_BY_STEP", dp), ("BENCH_MSE_BY_FAMILY", fam),
                  ("BENCH_MSE_BY_SIDE", side))
print("[ok] DLinear absent from every table written")

# ── the evaluation-window invariant: same count for every arm at a given L ────
assert_uniform(df, by=("L",), col="n_eval_windows", what="models")
assert_uniform(ds, by=("L",), col="n_eval_windows", what="model x step rows")
if len(dp):
    assert_uniform(dp, by=("L",), col="n_eval_windows", what="model x step rows")
per_L = df.groupby("L")[["n_windows_available", "n_eval_windows"]].agg(
    lambda s: sorted(set(int(v) for v in s)))
print("\n[eval-window] n_eval_windows is uniform across all "
      f"{df.model.nunique()} models at every horizon:")
for L, r in per_L.iterrows():
    assert len(r.n_eval_windows) == 1 and len(r.n_windows_available) == 1
    print(f"   L={int(L):2d}  available={r.n_windows_available[0]:3d}  "
          f"evaluated={r.n_eval_windows[0]:3d}  "
          f"(= eval_slice)  models={df[df.L == L].model.nunique()}")
    assert r.n_eval_windows[0] == eval_slice(r.n_windows_available[0])

# rounded convenience copies that previously had no writer in this repo; they are
# regenerated here so no stale table can disagree with the numbers above.
rank_full = df[["model", "family", "L", "n_seeds", "mse_7var_z", "mae_7var_z",
                "mse_ilitotal_z", "mae_ilitotal_z", "mse_ilitotal_phys",
                "mae_ilitotal_phys"]].round(4)
rank_full.to_csv(os.path.join(ROOT, "paper_tables", "BENCH_MSE_RANK_FULL.csv"), index=False)
step_clean = ds[["model", "family", "L", "step", "weeks_ahead",
                 "mse_7var_z", "mae_7var_z"]].round(4)
step_clean.to_csv(os.path.join(ROOT, "paper_tables", "BENCH_MSE_BY_STEP_CLEAN.csv"), index=False)
if len(dp):
    ks = dp[["model", "family", "L", "step", "weeks_ahead", "PTE_wk", "PIE_pct"]].round(3)
    ks["verdict"] = np.where(dp.kramer_shaman_pass.to_numpy(), "PASS", "FAIL")
    ks.to_csv(os.path.join(ROOT, "paper_tables", "BENCH_KS_CHAMPION_DETAIL.csv"), index=False)

if df["partial_export"].any():
    part = df[df.partial_export][["model", "L", "n_channels_used", "mse_ilitotal_z"]]
    print("\n[note] partial-channel exports (7-var metrics written as NaN on purpose):")
    print(part.to_string(index=False))

pd.set_option("display.width", 200)
print("cells:", len(cells), "| rows:", len(df))
print("\n=== MSE 7-var (z) on the shared evaluation windows, mean over seeds, per horizon ===")
piv = d.pivot_table(index=["family", "model"], columns="L", values="mse_7var_z")
piv["mean"] = piv.mean(axis=1)
print(piv.round(4).sort_values("mean").to_string())
print("\n=== by family ==="); print(fam.to_string())
print("\n=== by side ===");  print(side.to_string())
print("\n=== PTE/PIE pass counts (ILITOTAL, all L/step) ===")
if len(dp):
    g = dp.groupby(["family"]).agg(n=("kramer_shaman_pass", "size"),
                                   passed=("kramer_shaman_pass", "sum"),
                                   PTE=("PTE_wk", "mean"), PIE=("PIE_pct", "mean")).round(3)
    g["pass_rate_%"] = (g["passed"] / g["n"] * 100).round(1)
    print(g.to_string())
    print("\nbest PTE/PIE models (any cell fully passing):")
    wins = dp[dp.kramer_shaman_pass].groupby("model").size().sort_values(ascending=False)
    print(wins.to_string() if len(wins) else "  (none)")
