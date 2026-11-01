#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""train_regional.py — Table VI harness (US regional HHS-10, a DIFFERENT config).

WHY THIS FILE EXISTS
--------------------
Table VI of the paper is the **regional** task, and it does not use the national
configuration. `docs/WORK_BREAKDOWN.md` §13.D records it as ❌ with the exact
parameters that distinguish it:

    T = 20, L ∈ {2, 3, 5, 10, 13, 15, 20}, K = 4 GPT-2 layers,
    50 epochs, batch 32

`scripts/train_regional_miflu.py` (the pre-existing file) cannot produce a Table
VI cell: it has no CLI, no seeds, no checkpoint, no per-window predictions and no
manifest, it writes one aggregate RMSE/PCC pair for the whole 10-region block, and
its `DATA_PATH` (`<scripts>/data/us_region_raw.csv`) does not exist. A rule-11
run is impossible with it, so no GPU could have produced Table VI either.

This harness reuses the existing plumbing instead of re-implementing it:

* **window construction** — `train_nlinear_966.build_windows` (the A2 code, incl.
  `containment="strict"`), imported verbatim;
* **the model zoo** — `train_backbone_966.BACKBONES` / `build_model` for the
  neural arms, and `miflu_model.MIFlu` for the paper model;
* **the evaluation-window rule** — `eval_windows.eval_slice` / `check_cell_layout`
  (`(W//16)*16`), so a regional cell is scored on the same *rule* as every
  national cell;
* **provenance** — `train_backbone_966._measured_hardware` / `_code_identity`
  (AGENTS.md rule 12).

WHAT ONE CELL IS
----------------
    scripts/train_regional.py --model miflu --region all --horizon 2 --seed 42

writes the full rule-11 set into

    hpc_results/regional/<region>/<model>_L<L>_s<seed>/
        pred_<model>_L<L>_s<seed>.npz      pred/target (W, V, L) + target_start_row
        pred_<model>_L<L>_s<seed>.csv      the same arrays, long format (CSV twin)
        results_<model>_L<L>_s<seed>.csv   aggregate + per-region MSE/MAE/RMSE/PCC,
                                           in z-space **and** physical (patients)
        manifest_<model>_L<L>_s<seed>.json rule-11(d)/12: hardware, Slurm ids,
                                           library versions, config, ckpt sha256
        ckpt_<model>_L<L>_s<seed>.pth      best-validation checkpoint

`<region>` is `all` for the paper's configuration (one multivariate model over
the 10 HHS channels) or `hhs1`…`hhs10` for a single-region univariate run. The
variable axis `V` is therefore **10** or **1** — not 7. The rule-11 contract's
`(W, 7, L)` is the *national* instantiation; the regional task has ten target
series and no 7-channel regional data, so the same layout is used with `V =
n_hhs_regions`. Every artefact records `var_cols` and `n_vars`, and
`eval_windows.check_cell_layout(..., n_vars=V)` asserts it, so a 7-channel
national cell can never be confused with a 10-channel regional one.

PROTOCOL DETAILS THAT MUST BE STATED IN THE TABLE VI CAPTION
-----------------------------------------------------------
* **Split 50/10/40** (train/val/test) of the 1 084 weekly rows, which is the
  convention already baked into `scripts/train_regional_miflu.py` and
  `scripts/train_regional_baseline.py` (the paper does not state its regional
  split). Override with `--train-frac/--val-frac`.
* **Scaler** = train-rows-only mean/std (population, `+1e-8`), the same
  convention as the pre-existing regional scripts.
* **Selection** = best *validation* RMSE (de-normalised), the paper's regional
  metric — never test (AGENTS.md rule 4).
* **Seeds 42/43/44** (rule 9's benchmark seed set), 3 seeds per cell, reported as
  a mean ± sd with `n_seeds` in the caption.
* **Evaluation windows** = the first `(W // 16) * 16` test windows
  (`eval_windows.eval_slice`), the shared rule from `SKILL.md` §3.

Usage::

    python scripts/train_regional.py --self-check          # CPU, no training
    python scripts/train_regional.py --preflight           # CPU shape/CSV checks
    python scripts/train_regional.py --model nlinear --region all \
        --horizon 2 --seed 42 --export-root _dryrun/regional
    python scripts/train_regional.py --model miflu --region all --horizon 2 \
        --seed 42            # the paper cell (needs a GPU for a real number)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from configs import (REGIONAL_CONFIG, REGIONAL_DATA_PATH, HHS_COLS)
from train_nlinear_966 import build_windows
from eval_windows import eval_slice, check_cell_layout

# The paper model and the neural arms are imported from their existing homes —
# this file must not re-implement either.
from miflu_model import MIFlu

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The regional CSV is produced by `scripts/download_us_region.py`, which writes
#: to `data/raw/`; `configs.REGIONAL_DATA_PATH` points at `data/` (a historical
#: inconsistency). Resolution order: the configs path, then `data/raw/`.
DATA_CANDIDATES = (REGIONAL_DATA_PATH,
                   os.path.join(PROJECT_ROOT, "data", "raw", "us_region_raw.csv"))

#: Epweek filter used by every pre-existing regional script
#: (`train_regional_miflu.load_and_normalize`), i.e. week 40 1997 – week 18 2020.
EPIWEEK_MIN, EPIWEEK_MAX = 199740, 202018

#: Test-loader batch used for the SHARED evaluation-window rule. `eval_slice`
#: is defined with batch 16 (MIFlu's national test loader), and this harness
#: keeps that one definition rather than inventing a second one.
EVAL_BATCH = 16

#: Default output root. One directory per (region, model, L, seed).
EXPORT_ROOT = os.path.join(PROJECT_ROOT, "hpc_results", "regional")

#: The neural arms this harness can drive (the paper model is added separately).
BACKBONE_NAMES = ("dlinear", "nlinear", "patchtst", "itransformer", "dnn", "cnn",
                  "rnn", "lstm", "gru", "qwen_time_llm", "calf_llm", "timecma_llm")


# ──────────────────────────────────────────────────────────────────────────
# data
# ──────────────────────────────────────────────────────────────────────────
def resolve_data_path(explicit: str = None) -> str:
    """Return the regional CSV path, or raise with the exact command to create it."""
    if explicit:
        if not os.path.exists(explicit):
            raise FileNotFoundError(f"--data {explicit} does not exist")
        return explicit
    for cand in DATA_CANDIDATES:
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError(
        "the US regional dataset is absent. Create it with\n"
        "    python scripts/download_us_region.py --check   # is it already there?\n"
        "    python scripts/download_us_region.py           # fetch it (CPU, internet)")


def load_regional(path: str, train_frac: float = 0.50, val_frac: float = 0.10,
                  log=print):
    """Load the 10 HHS series, fit the scaler on TRAIN rows only, return z-space data.

    The 50/10/40 split is the pre-existing regional convention (see the module
    docstring); `containment="strict"` windowing is applied later by
    `build_windows`, exactly as on the national task.
    """
    df = pd.read_csv(path)
    if "epiweek" not in df.columns:
        raise ValueError(f"{path} has no `epiweek` column: {list(df.columns)}")
    df = df[(df["epiweek"] >= EPIWEEK_MIN) & (df["epiweek"] <= EPIWEEK_MAX)]
    df = df.sort_values("epiweek").reset_index(drop=True)
    missing = [c for c in HHS_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing HHS columns {missing}")
    data = df[HHS_COLS].values.astype(np.float32)
    if not np.isfinite(data).all():
        raise ValueError(f"{path} contains non-finite values in the HHS columns")
    n = len(data)
    train_end = int(n * float(train_frac))
    val_end = train_end + int(n * float(val_frac))
    mean = data[:train_end].mean(axis=0, keepdims=True)
    scale = data[:train_end].std(axis=0, keepdims=True) + 1e-8
    data_norm = ((data - mean) / scale).astype(np.float32)
    log(f"[regional] {os.path.basename(path)}: {n} weeks "
        f"({int(df['epiweek'].min())}-{int(df['epiweek'].max())}), "
        f"train={train_end} val={val_end - train_end} test={n - val_end} "
        f"(train_frac={train_frac}, val_frac={val_frac})")
    return {"df": df, "data_norm": data_norm, "train_end": train_end,
            "val_end": val_end, "n": n, "train_mean": mean, "train_std": scale,
            "var_cols": list(HHS_COLS), "profile": "us_region_hhs10",
            "split_source": "regional_50_10_40"}


def select_region(data_dict, region: str, log=print):
    """Restrict a loaded dataset to one HHS region (`all` keeps all ten).

    Accepts `HHS5` or `hhs5` (case-insensitive) and always returns the canonical
    upper-case column name, so a path segment can be written either way.
    """
    if str(region).lower() == "all":
        return data_dict
    canon = str(region).upper()
    if canon not in HHS_COLS:
        raise SystemExit(f"--region must be 'all' or one of {HHS_COLS} "
                         f"(case-insensitive), got {region!r}")
    j = HHS_COLS.index(canon)
    out = dict(data_dict)
    out["data_norm"] = data_dict["data_norm"][:, j:j + 1]
    out["train_mean"] = data_dict["train_mean"][:, j:j + 1]
    out["train_std"] = data_dict["train_std"][:, j:j + 1]
    out["var_cols"] = [canon]
    out["region"] = canon
    log(f"[regional] single-region mode: {canon} (variable axis V=1)")
    return out


# ──────────────────────────────────────────────────────────────────────────
# models
# ──────────────────────────────────────────────────────────────────────────
def build_regional_model(name: str, T: int, N: int, L: int, device: str,
                         layers: int, text_embedder: str = "prompt"):
    """Return `(model, kind)`; `kind` selects the forward/loss convention."""
    if name == "miflu":
        model = MIFlu(N=N, T=T, L=L, Lp=REGIONAL_CONFIG["Lp"],
                      S=REGIONAL_CONFIG["S"], K=int(layers),
                      lora_r=REGIONAL_CONFIG["lora_r"], device=device,
                      use_text_ln=False,
                      use_text=(text_embedder != "none"))
        return model, "miflu"
    if name not in BACKBONE_NAMES:
        raise SystemExit(f"unknown --model {name!r}; known: miflu, "
                         f"{', '.join(BACKBONE_NAMES)}")
    # The neural arms come from the EXISTING registry, loaded by file path.
    from train_backbone_966 import build_model
    return build_model(name, T, N, L, device), "backbone"


def build_regional_prompt(data_dict, L: int, lookback: int):
    """Table I-style prompt for the regional task (the pre-existing template).

    Kept byte-compatible with `train_regional_miflu.build_regional_prompt` so a
    regional MIFlu run is comparable with the earlier attempt, and it uses TRAIN
    rows only (no validation/test statistic enters the prompt).
    """
    tr = data_dict["df"].iloc[:data_dict["train_end"]]
    cols = data_dict["var_cols"]
    lines = ["[Dataset information] This time series dataset includes %d feature(s) "
             "that recorded influenza-like illness (ILI) patient counts in the HHS "
             "region(s) of the United States from week 40, 1997 to week 18, 2020. "
             "Below (1) to (%d) is the information about each feature:"
             % (len(cols), len(cols)),
             "*** [Input variable description]"]
    for i, c in enumerate(cols):
        lines.append("(%d) ILI patient count for %s. Minimum value: %.0f, maximum "
                     "value: %.0f. This variable peaks 1 time for 1 year."
                     % (i + 1, c, tr[c].min(), tr[c].max()))
    lines.append("*** [Task instruction]")
    lines.append("Predict the next %d steps given the previous %d steps for the "
                 "information attached." % (int(L), int(lookback)))
    return "\n".join(lines)


def forward_cell(model, kind, bx, device, htext=None):
    """Run one batch and return predictions in StandardScaler (z) space, (B, N, L)."""
    bx = bx.to(device)
    if kind == "miflu":
        y, _, _, _ = model(bx, htext=htext)
        return y
    return model(bx)


# ──────────────────────────────────────────────────────────────────────────
# metrics
# ──────────────────────────────────────────────────────────────────────────
def _pcc(p, t):
    """Pearson correlation over flattened arrays (0.0 when either side is constant)."""
    p = np.asarray(p, dtype=np.float64).reshape(-1)
    t = np.asarray(t, dtype=np.float64).reshape(-1)
    if p.std() == 0 or t.std() == 0:
        return float("nan")
    return float(np.corrcoef(p, t)[0, 1])


def score_cell(pred_z, target_z, mean, scale, var_cols):
    """Full metric block: aggregate + per variable, in z space AND physical units.

    Satisfies rule 11(a): MSE/MAE for the aggregate, per variable, and in the
    de-normalised (patient-count) units, plus the paper's regional RMSE/PCC.
    Row layout: one `scope="aggregate"` row for the whole (V, L) block, then one
    `scope="per_variable"` row per HHS region — the per-region rows ARE Table VI's
    per-region column.
    """
    pred_z = np.asarray(pred_z, dtype=np.float64)
    target_z = np.asarray(target_z, dtype=np.float64)
    p_phys = pred_z * scale.reshape(1, -1, 1) + mean.reshape(1, -1, 1)
    t_phys = target_z * scale.reshape(1, -1, 1) + mean.reshape(1, -1, 1)

    def _row(p, t, scope, variable, n_vars):
        err = p - t
        return {"scope": scope, "variable": variable,
                "n_windows": int(p.shape[0]), "n_variables": int(n_vars),
                "n_leads": int(p.shape[-1]),
                "mse_z": float(np.mean(err ** 2)),
                "mae_z": float(np.mean(np.abs(err))),
                "rmse_z": float(np.sqrt(np.mean(err ** 2))),
                "pcc_z": _pcc(p, t)}

    def _phys(p, t):
        err = p - t
        return {"mse_phys": float(np.mean(err ** 2)),
                "mae_phys": float(np.mean(np.abs(err))),
                "rmse_phys": float(np.sqrt(np.mean(err ** 2))),
                "pcc_phys": _pcc(p, t)}

    # aggregate: average over every (region, lead) element
    agg = _row(pred_z.reshape(len(pred_z), -1), target_z.reshape(len(target_z), -1),
               "aggregate", "ALL", pred_z.shape[1])
    agg.update(_phys(p_phys.reshape(len(p_phys), -1),
                     t_phys.reshape(len(t_phys), -1)))
    rows = [agg]
    for j, c in enumerate(var_cols):
        r = _row(pred_z[:, j, :], target_z[:, j, :], "per_variable", c, 1)
        r.update(_phys(p_phys[:, j, :], t_phys[:, j, :]))
        rows.append(r)
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────
# provenance
# ──────────────────────────────────────────────────────────────────────────
def _sha256(path):
    if not path or not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _jsonable(value):
    """Keep scalars and JSON structures, stringify anything else (numpy, Path…)."""
    if isinstance(value, (int, float, str, bool, type(None))):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return str(value)


def write_manifest(path, *, model, region, L, seed, config, wall_seconds,
                   ckpt_path, artefacts, data_path, n_vars, split, probe_only,
                   device="cpu"):
    """Rule-11(d) + rule-12 manifest for one regional cell."""
    from train_backbone_966 import _measured_hardware
    payload = {
        "table": "VI (regional HHS-10)",
        "model": model, "region": region, "L": int(L), "seed": int(seed),
        "n_vars": int(n_vars), "var_cols": HHS_COLS if n_vars == 10 else [region],
        "profile": "us_region_hhs10",
        "data_file": os.path.abspath(data_path),
        "data_sha256": _sha256(data_path),
        "split": dict(split),
        "containment": "strict",
        "eval_space": "standardized_train_fit_z",
        "n_eval_windows_rule": "eval_slice(W, batch=16) = (W // 16) * 16",
        "probe_only": bool(probe_only),
        "artefact_is_a_result": not bool(probe_only),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "wall_seconds": None if wall_seconds is None else round(float(wall_seconds), 3),
        "hardware": _measured_hardware(device),
        "slurm": {k: os.environ[k] for k in
                  ("SLURM_JOB_ID", "SLURM_JOB_PARTITION", "SLURM_NODELIST")
                  if k in os.environ},
        "library_versions": {"python": platform.python_version(),
                             "torch": torch.__version__,
                             "numpy": np.__version__,
                             "pandas": pd.__version__},
        "code": {"runner": {"file": os.path.abspath(__file__),
                            "sha256": _sha256(os.path.abspath(__file__))}},
        "checkpoint": {"path": ckpt_path, "sha256": _sha256(ckpt_path)},
        "artefacts": artefacts,
        "config": {k: _jsonable(v) for k, v in config.items()},
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return path


# ──────────────────────────────────────────────────────────────────────────
# one cell
# ──────────────────────────────────────────────────────────────────────────
def cell_dir_name(model, L, seed):
    return f"{model}_L{int(L)}_s{int(seed)}"


def train_cell(data_dict, *, model_name, region, L, seed, epochs, batch, lr,
               layers, device, export_root, ckpt_root, text_embedder="prompt",
               max_train=None, max_val=None, probe_only=False, log=print):
    """Train + evaluate ONE regional cell and write the full rule-11 artefact set."""
    t_start = time.time()
    T = int(REGIONAL_CONFIG["T"])
    V = int(data_dict["data_norm"].shape[1])
    var_cols = list(data_dict["var_cols"])
    mean = np.asarray(data_dict["train_mean"]).reshape(1, -1)
    scale = np.asarray(data_dict["train_std"]).reshape(1, -1)

    Xt, Yt, Xv, Yv, Xte, Yte, sinfo = build_windows(
        data_dict["data_norm"], T, L, data_dict["train_end"],
        data_dict["val_end"], containment="strict")
    if max_train is not None:
        Xt, Yt = Xt[:int(max_train)], Yt[:int(max_train)]
    if max_val is not None:
        Xv, Yv = Xv[:int(max_val)], Yv[:int(max_val)]
    log(f"[regional] {model_name} L={L} seed={seed} region={region}: "
        f"train={len(Xt)} val={len(Xv)} test={len(Xte)} windows (V={V}, T={T})")

    # ── text for the paper model (train-rows-only prompt) ──────────────────
    htext = None
    if model_name == "miflu" and text_embedder == "prompt":
        from textual_embedder import TextualInputEmbedder
        embedder = TextualInputEmbedder(device=device)
        htext = embedder(build_regional_prompt(data_dict, L, T))
        log(f"[regional] L={L}: regional prompt -> {tuple(htext.shape)} tokens")

    torch.manual_seed(int(seed) + int(L))          # A2 convention
    model, kind = build_regional_model(model_name, T, V, L, device, layers,
                                       text_embedder=text_embedder)
    params = {"total_parameters": int(sum(p.numel() for p in model.parameters())),
              "trainable_parameters": int(sum(p.numel() for p in model.parameters()
                                              if p.requires_grad))}
    log(f"[regional] {model_name}: params total={params['total_parameters']:,} "
        f"trainable={params['trainable_parameters']:,}")

    tl = DataLoader(TensorDataset(torch.from_numpy(Xt), torch.from_numpy(Yt)),
                    batch_size=batch, shuffle=True)
    vl = DataLoader(TensorDataset(torch.from_numpy(Xv), torch.from_numpy(Yv)),
                    batch_size=batch, shuffle=False)
    el = DataLoader(TensorDataset(torch.from_numpy(Xte), torch.from_numpy(Yte)),
                    batch_size=EVAL_BATCH, shuffle=False)   # shared window rule
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad],
                           lr=float(lr))
    crit = nn.MSELoss()

    def _predict(loader):
        model.eval()
        preds, targets = [], []
        with torch.no_grad():
            for bx, by in loader:
                preds.append(forward_cell(model, kind, bx, device, htext)
                             .detach().cpu().numpy())
                targets.append(by.numpy())
        return np.concatenate(preds), np.concatenate(targets)

    def _val_rmse():
        p, t = _predict(vl)
        rmse = float(np.sqrt(np.mean(((p - t) * scale.reshape(1, -1, 1)) ** 2)))
        return rmse, p, t

    best = {"rmse": float("inf"), "state": None, "epoch": -1}
    ep_rows = []
    for ep in range(int(epochs)):
        model.train()
        tot, nb = 0.0, 0
        for bx, by in tl:
            bx, by = bx.to(device), by.to(device)
            opt.zero_grad()
            loss = crit(forward_cell(model, kind, bx, device, htext), by)
            loss.backward()
            opt.step()
            tot += float(loss.detach())
            nb += 1
        v_rmse, _, _ = _val_rmse()
        ep_rows.append({"epoch": ep + 1, "train_loss": tot / max(nb, 1),
                        "val_rmse_phys": v_rmse})
        if v_rmse < best["rmse"]:
            best.update({"rmse": v_rmse, "epoch": ep,
                         "state": {k: v.detach().clone()
                                   for k, v in model.state_dict().items()}})
        log(f"    ep {ep+1:>2}/{epochs} | train_loss={tot/max(nb,1):.6f} "
            f"| val_rmse={v_rmse:.3f} patients")
    if best["state"] is not None:
        model.load_state_dict(best["state"])

    # ── TEST: every available window, so the stored cell matches the national
    #    convention (store available, crop on read) ────────────────────────────
    test_pred, test_true = _predict(el)
    W = int(test_pred.shape[0])
    check_cell_layout(test_pred, test_true, sinfo["target_starts"][
        np.asarray(sinfo["splits"]) == 2][:W], L=L, n_vars=V)
    n_eval = eval_slice(W)
    tsr = np.asarray(sinfo["target_starts"])[np.asarray(sinfo["splits"]) == 2][:W]

    # Metrics are computed on the SHARED evaluation windows only.
    pred_eval, target_eval = test_pred[:n_eval], test_true[:n_eval]
    results = score_cell(pred_eval, target_eval, mean, scale, var_cols)
    results.insert(0, "seed", int(seed))
    results.insert(0, "L", int(L))
    results.insert(0, "model", model_name)
    results.insert(0, "region", region)
    results["n_eval_windows"] = n_eval
    results["n_windows_available"] = W
    results["n_windows_discarded"] = W - n_eval

    # ── artefacts ─────────────────────────────────────────────────────────
    cell = cell_dir_name(model_name, L, seed)
    out_dir = os.path.join(export_root, region, cell)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(ckpt_root, exist_ok=True)
    ckpt_path = os.path.join(ckpt_root, f"ckpt_{model_name}_L{L}_s{seed}.pth")
    torch.save(model.state_dict(), ckpt_path)

    npz_path = os.path.join(out_dir, f"pred_{model_name}_L{L}_s{seed}.npz")
    np.savez_compressed(
        npz_path,
        pred=test_pred.astype(np.float32),
        target=test_true.astype(np.float32),
        target_start_row=tsr.astype(np.int32),
        L=np.int32(L), seed=np.int32(seed),
        var_cols=np.array(var_cols), model=np.array(model_name),
        profile=np.array("us_region_hhs10"), containment=np.array("strict"),
        space=np.array("standardized_train_fit_z"),
        n_eval_windows=np.int32(n_eval), region=np.array(region))

    csv_path = os.path.join(out_dir, f"pred_{model_name}_L{L}_s{seed}.csv")
    rows = []
    p_phys = pred_eval * scale.reshape(1, -1, 1) + mean.reshape(1, -1, 1)
    t_phys = target_eval * scale.reshape(1, -1, 1) + mean.reshape(1, -1, 1)
    for w in range(n_eval):
        for j, c in enumerate(var_cols):
            for s in range(int(L)):
                rows.append({"window": w, "target_start_row": int(tsr[w]),
                             "region": c, "step": s,
                             "pred_z": float(pred_eval[w, j, s]),
                             "target_z": float(target_eval[w, j, s]),
                             "pred_phys": float(p_phys[w, j, s]),
                             "target_phys": float(t_phys[w, j, s])})
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    res_path = os.path.join(out_dir, f"results_{model_name}_L{L}_s{seed}.csv")
    results.to_csv(res_path, index=False)
    ep_path = os.path.join(out_dir, f"epochs_{model_name}_L{L}_s{seed}.csv")
    pd.DataFrame(ep_rows).to_csv(ep_path, index=False)

    manifest_path = write_manifest(
        os.path.join(out_dir, f"manifest_{model_name}_L{L}_s{seed}.json"),
        model=model_name, region=region, L=L, seed=seed,
        config={"T": T, "L_list": REGIONAL_CONFIG["L_list"], "Lp": REGIONAL_CONFIG["Lp"],
                "S": REGIONAL_CONFIG["S"], "K": int(layers), "epochs": int(epochs),
                "batch": int(batch), "lr": float(lr),
                "lora_r": REGIONAL_CONFIG["lora_r"],
                "text_embedder": text_embedder, "n_vars": V,
                "train_frac": data_dict.get("train_frac"),
                "val_frac": data_dict.get("val_frac"),
                "epochs_log": os.path.basename(ep_path),
                "n_train_windows": int(len(Xt)), "n_val_windows": int(len(Xv)),
                "n_test_windows": W, "n_eval_windows": n_eval,
                "best_epoch": best["epoch"], "best_val_rmse_phys": best["rmse"],
                "params": params},
        wall_seconds=time.time() - t_start, ckpt_path=ckpt_path,
        artefacts={"npz": os.path.basename(npz_path),
                   "csv": os.path.basename(csv_path),
                   "results": os.path.basename(res_path)},
        data_path=resolve_data_path(), n_vars=V,
        split={"train_end": int(data_dict["train_end"]),
               "val_end": int(data_dict["val_end"]),
               "n_rows": int(data_dict["n"])},
        probe_only=probe_only, device=device)

    agg = results[results["scope"] == "aggregate"].iloc[0]
    log(f"[regional] {cell}: n_eval={n_eval}/{W}  RMSE_phys={agg['rmse_phys']:.3f} "
        f"PCC_phys={agg['pcc_phys']:.4f}  MSE_z={agg['mse_z']:.6f}  "
        f"({time.time()-t_start:.1f}s)")
    return {"cell": cell, "out_dir": out_dir, "npz": npz_path,
            "results": res_path, "manifest": manifest_path,
            "ckpt": ckpt_path, "n_eval_windows": n_eval,
            "n_windows_available": W, "epochs_log": ep_path}


# ──────────────────────────────────────────────────────────────────────────
# CPU checks
# ──────────────────────────────────────────────────────────────────────────
def self_check():
    """CPU: dataset presence/shape + one forward for every arm this file drives."""
    path = resolve_data_path()
    dd = load_regional(path)
    ok = True
    print(f"[self-check] data OK: {path} -> {dd['n']} weeks x "
          f"{len(dd['var_cols'])} regions")
    for name in ("nlinear", "dnn") + ("miflu",):
        try:
            T, V, L = REGIONAL_CONFIG["T"], len(dd["var_cols"]), 2
            m, kind = build_regional_model(name, T, V, L, "cpu", layers=1,
                                          text_embedder="prompt")
            x = torch.randn(2, V, T)
            y = (m(x, htext=None)[0] if kind == "miflu" else m(x))
            shape_ok = tuple(y.shape) == (2, V, L)
            ok &= shape_ok
            print(f"[self-check] {name:<12} forward={tuple(y.shape)} "
                  f"{'OK' if shape_ok else 'SHAPE-FAIL'}")
        except Exception as exc:
            ok = False
            print(f"[self-check] {name:<12} UNAVAILABLE: {type(exc).__name__}: {exc}")
    print(f"[self-check] {'PASS' if ok else 'FAIL'}")
    return ok


def preflight():
    """CPU: prove the window/split/rule plumbing without training."""
    dd = load_regional(resolve_data_path())
    T = REGIONAL_CONFIG["T"]
    for L in REGIONAL_CONFIG["L_list"]:
        Xt, Yt, Xv, Yv, Xte, Yte, sinfo = build_windows(
            dd["data_norm"], T, L, dd["train_end"], dd["val_end"],
            containment="strict")
        ts, sp = sinfo["target_starts"], sinfo["splits"]
        assert ((sp == 0) == (ts + L <= dd["train_end"])).all()
        assert ((sp == 1) == ((ts >= dd["train_end"]) & (ts + L <= dd["val_end"]))).all()
        assert ((sp == 2) == ((ts >= dd["val_end"]) & (ts + L <= dd["n"]))).all()
        n_eval = eval_slice(len(Xte))
        print(f"[preflight] L={L:>2}: train={len(Xt):>4} val={len(Xv):>3} "
              f"test={len(Xte):>3} -> n_eval={n_eval:>3} "
              f"(discarded {len(Xte) - n_eval})")
        assert n_eval >= 16, f"L={L}: only {n_eval} evaluation windows"
        assert len(Xt) > 0 and len(Xv) > 0
    m = build_regional_model("nlinear", T, len(dd["var_cols"]), 2, "cpu", layers=4)[0]
    with torch.no_grad():
        y = m(torch.randn(4, len(dd["var_cols"]), T))
    assert tuple(y.shape) == (4, len(dd["var_cols"]), 2)
    print("[preflight] PASS")
    return True


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Table VI harness: US regional HHS-10 (T=20, K=4, 50 epochs, "
                    "batch 32). Writes the full rule-11 artefact set per cell.")
    ap.add_argument("--model", default="miflu",
                    choices=("miflu",) + BACKBONE_NAMES)
    ap.add_argument("--region", default="all",
                    help="'all' (paper config, V=10) or hhs1..hhs10 (V=1).")
    ap.add_argument("--horizon", type=int, default=None,
                    help="One horizon from %s (default: all seven)."
                         % (REGIONAL_CONFIG["L_list"],))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seeds", default=None,
                    help="Comma-separated seed grid, e.g. 42,43,44 (overrides "
                         "--seed).")
    ap.add_argument("--epochs", type=int, default=REGIONAL_CONFIG["epochs"])
    ap.add_argument("--batch", type=int, default=REGIONAL_CONFIG["batch_size"])
    ap.add_argument("--lr", type=float, default=REGIONAL_CONFIG["learning_rate"])
    ap.add_argument("--layers", type=int, default=REGIONAL_CONFIG["K"],
                    help="ForecastingLLM depth K (paper regional config: 4).")
    ap.add_argument("--text-embedder", choices=("prompt", "none"), default="prompt",
                    help="Regional MIFlu text source: `prompt` (Table I template, "
                         "live GPT-2) or `none` (no-text arm).")
    ap.add_argument("--data", default=None, help="Path to us_region_raw.csv.")
    ap.add_argument("--train-frac", type=float, default=0.50)
    ap.add_argument("--val-frac", type=float, default=0.10)
    ap.add_argument("--export-root", default=EXPORT_ROOT)
    ap.add_argument("--ckpt-root", default=None,
                    help="Checkpoint root (default: <export-root>/_ckpt).")
    ap.add_argument("--max-train-windows", type=int, default=None,
                    help="Cap the TRAIN windows (wiring tests only; the test split "
                         "is never capped).")
    ap.add_argument("--max-val-windows", type=int, default=None)
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    a = ap.parse_args(argv)

    if a.self_check:
        return 0 if self_check() else 1
    if a.preflight:
        return 0 if preflight() else 1

    data_path = resolve_data_path(a.data)
    dd = load_regional(data_path, a.train_frac, a.val_frac)
    dd["train_frac"], dd["val_frac"] = a.train_frac, a.val_frac
    dd = select_region(dd, a.region)
    if a.horizon is not None and int(a.horizon) not in REGIONAL_CONFIG["L_list"]:
        raise SystemExit(f"--horizon {a.horizon} is not one of the paper's regional "
                         f"horizons {REGIONAL_CONFIG['L_list']}")
    L_list = [int(a.horizon)] if a.horizon is not None else list(REGIONAL_CONFIG["L_list"])
    seeds = ([int(s) for s in a.seeds.split(",") if s.strip()]
             if a.seeds else [int(a.seed)])

    device = "cuda" if torch.cuda.is_available() else "cpu"
    ckpt_root = a.ckpt_root or os.path.join(a.export_root, "_ckpt")
    print(f"[regional] device={device} model={a.model} region={a.region} "
          f"L={L_list} seeds={seeds} epochs={a.epochs} batch={a.batch} "
          f"lr={a.lr} K={a.layers} text={a.text_embedder}")

    done, failed = [], []
    for L in L_list:
        for seed in seeds:
            cell = cell_dir_name(a.model, L, seed)
            out_dir = os.path.join(a.export_root, a.region, cell)
            need = [os.path.join(out_dir, f) for f in (
                f"pred_{a.model}_L{L}_s{seed}.npz",
                f"results_{a.model}_L{L}_s{seed}.csv",
                f"manifest_{a.model}_L{L}_s{seed}.json")]
            if all(os.path.exists(p) for p in need):
                print(f"[regional] {cell}: already complete, skipping (resume)")
                done.append(cell)
                continue
            try:
                r = train_cell(
                    dd, model_name=a.model, region=a.region, L=L, seed=seed,
                    epochs=a.epochs, batch=a.batch, lr=a.lr, layers=a.layers,
                    device=device, export_root=a.export_root, ckpt_root=ckpt_root,
                    text_embedder=a.text_embedder,
                    max_train=a.max_train_windows, max_val=a.max_val_windows)
                done.append(r["cell"])
            except Exception as exc:               # a failed cell must not kill the run
                failed.append((cell, f"{type(exc).__name__}: {exc}"))
                print(f"[regional] {cell}: FAILED {type(exc).__name__}: {exc}")
    print(f"[regional] DONE {len(done)} cells, {len(failed)} failed -> "
          f"{os.path.join(a.export_root, a.region)}")
    for cell, why in failed:
        print(f"  FAILED {cell}: {why}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
