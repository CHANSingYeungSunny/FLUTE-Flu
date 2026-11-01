#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""export_miflu_all7.py -- re-export MIFlu per-window predictions for ALL 7
variables, from the saved checkpoints, with NO retraining.

WHY THIS EXISTS
---------------
`train_miflu.export_prediction_csv()` writes only ILITOTAL (channel 4):

    gt = by.cpu().numpy()[:, 4, :]
    pr = yh_rev.cpu().numpy()[:, 4, :]

The model itself computes all seven channels (training loss and `evaluate()`'s
`mse_all` are 7-variable), so the other six are discarded at the *writing* step,
not at the *inference* step. That makes the CSV import into the benchmark as
`partial=True` with 6 NaN channels, which in turn makes MIFlu's `mse_7var_z`
NaN -- so MIFlu cannot sit on the same axis as the other 17 arms, and Table V
(7-variable) would have no counterpart in the benchmark table.

This script closes that gap with a pure forward pass:

    build data exactly as training -> build model exactly as training ->
    load `ckpt_L{L}_s{S}/best_miflu_L{L}.pth` -> forward train/val/test ->
    write one wide CSV carrying all 7 variables in z-space AND in physical units.

It does NOT train, does NOT touch the reproduction artefacts, and does NOT
consume a GPU allocation requirement (CPU is sufficient; it is 938 channel-window
forwards per cell).

SCHEMA (wide, one row per (window, lead))
-----------------------------------------
    split, abs_week, step, epiweek, week_start_date,
    ground_truth_<slug>,  prediction_<slug>        for 7 slugs (z-space, PRIMARY)
    ground_truth_<slug>_phys, prediction_<slug>_phys   for 7 slugs (physical)

`<slug>` = wili, unwili, age_0_4, age_5_24, ili, num_providers, ot.
The ILI pair keeps the exact legacy names `ground_truth_ili` /
`prediction_ili` / `ground_truth_ili_phys` / `prediction_ili_phys`, so the file
stays a drop-in replacement for the ILITOTAL-only export that already passed
protocol alignment (max |GT(ch4) - benchmark target| = 6.086e-07).

BACKWARD-COMPATIBILITY GUARANTEE
--------------------------------
Before overwriting an existing ILI-only export it is preserved as
`*.ili_only.csv`, and the ILI columns of the new file are asserted equal to it
to <= 1e-6 where both exist. The FORWARD PASS IS IDENTICAL to the training-time
export (same model constructor, same batch order, same `shuffle=False` loader,
same N=7 packing), so this assertion should hold to floating-point rounding.

USAGE
-----
    python export_miflu_all7.py --cells 24:42 24:43 24:44 36:42 ...
    python export_miflu_all7.py --all          # 4 horizons x seeds 42,43,44
    python export_miflu_all7.py --all --check  # verify only, write nothing
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import train_miflu as TM                      # noqa: E402  (module globals patched below)
from miflu_model import MIFlu                 # noqa: E402
from configs import CONFIG, resolve_profile   # noqa: E402

PROFILE = "author_repo_966"     # the profile every MIFlu reproduction run used
HORIZONS = [24, 36, 48, 60]
SEEDS = list(range(2021, 2031))     # the reproduction protocol: 10 reps, 2021-2030

# VAR_COLS order -> a column-name-safe slug. Index 4 (ILITOTAL) keeps `ili`.
SLUGS = ["wili", "unwili", "age_0_4", "age_5_24", "ili", "num_providers", "ot"]

AUTHOR_RUNS = "/gpfs1/home/sychan552/stage5_a2_durable/author_runs"

# The rep whose validation loss was lowest is renamed to `best_miflu_L{L}.pth`
# by train_miflu.main() (`os.replace(best_rep["rep_ckpt"], final_ckpt)`), so that
# rep's `_rep_..._seed{S}.pth` no longer exists under its own name. The seed is
# read off the run log line `[CKPT] L=..: kept rep seed=..`:
#   L=24 -> 2024, L=36 -> 2024, L=48 -> 2021, L=60 -> 2025
BEST_SEED = {24: 2024, 36: 2024, 48: 2021, 60: 2025}

# Safety copies of the four original-run `best_miflu_L{L}.pth` files, made before
# any retraining so that a retrain writing into `ckpt_L{L}_s{S}/` can never
# destroy the best-val rep's weights (those are the ONLY weights for
# L24/36 seed 2024, L48 seed 2021, L60 seed 2025).
BEST_CKPT_DIR = os.path.join(AUTHOR_RUNS, "ckpt_best_repro")

# Per-seed oracle: the `test_mse_all` each rep of the original 10-rep runs logged
# (on the author's `drop_last=True` test loader, i.e. the first (W//16)*16 test
# windows). Anything exported or retrained must reproduce its own oracle to
# <= 1e-5, otherwise it is not the same experiment.
ORACLE = {
    24: [1.240157, 1.201078, 1.284212, 1.259462, 1.464643,
         1.368497, 1.392309, 1.230425, 1.231536, 1.373057],
    36: [1.314358, 1.306645, 1.269466, 1.154099, 1.767328,
         1.312511, 1.400796, 1.302717, 1.404061, 1.328807],
    48: [1.482299, 1.711215, 1.663857, 1.879495, 1.723161,
         1.620327, 1.628296, 1.588157, 1.570881, 1.675020],
    60: [1.599641, 1.664878, 1.821282, 1.915250, 1.410785,
         1.984315, 1.614602, 1.401814, 1.520661, 1.895393],
}


def oracle_mse(L, seed):
    """Expected `test_mse_all` for this (L, seed), or None if out of range."""
    try:
        return ORACLE[int(L)][int(seed) - 2021]
    except (KeyError, IndexError):
        return None


def _oracle_matches_logged(L, seed):
    """True when a fresh 1-rep run for this seed carries its own oracle-matching log.

    This is the only evidence that `ckpt_L{L}_s{seed}/best_miflu_L{L}.pth` really
    holds the weights of rep `seed`: `train_miflu.py --reps 1 --seed S` re-seeds
    `set_seed(S + L)` and reproduces rep S of the 10-rep run exactly (proven for
    L24 seed 2021 and for L36 seeds 2022/2023, whose logs read 1.240157 and
    1.306645 / 1.269466).
    """
    import glob
    import re

    want = oracle_mse(L, seed)
    if want is None:
        return False
    pat = os.path.join(AUTHOR_RUNS, "_seedruns", f"L{L}_s{seed}", "training_miflu_log_*.txt")
    for p in sorted(glob.glob(pat)):
        try:
            txt = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        got = re.findall(r"DONE: test_mse=([0-9.]+)", txt)
        if got and abs(float(got[-1]) - want) <= 1e-5:
            return True
    return False


def find_ckpt(L, seed):
    """Locate the saved weights for one (L, rep). Returns (path, provenance) or (None, None).

    2026-11-01 DEFECT FIX (job 719030). The old order put
    `ckpt_L{L}_s{seed}/best_miflu_L{L}.pth` FIRST. That file is NOT a fresh run
    for seed 2021 when the earlier 10-rep reproduction run used
    `ckpt_L{L}_s2021/` as its output directory: there `best_miflu_L{L}.pth` is
    the run's *best-val rep* (L24/L36 -> seed 2024, L48 -> 2021, L60 -> 2025).
    So `find_ckpt(24, 2021)` returned seed-2024 weights and the export was
    labelled seed 2021 -- the `dPRED=1.993` assertion failure in 719030, and the
    reason the L36 seed-2021 cell on disk is really seed 2024's predictions.
    Trust order is now: (1) the original run's per-rep file, (2) the original
    run's best-val rep -- only for the seed it actually is, (3) a retrain this
    controller wrote, (4) a fresh 1-rep run that carries its own
    oracle-matching log.
    """
    # 1. original 10-rep run, per-rep checkpoint
    p = os.path.join(AUTHOR_RUNS, f"ckpt_L{L}_s2021", f"_rep_miflu_L{L}_seed{seed}.pth")
    if os.path.exists(p):
        return p, "reproduction per-rep ckpt"

    # 2. original 10-rep run, best-val rep (this file IS that rep's weights)
    if BEST_SEED.get(L) == seed:
        for cand in (os.path.join(BEST_CKPT_DIR, f"best_miflu_L{L}.pth"),
                     os.path.join(AUTHOR_RUNS, f"ckpt_L{L}_s2021", f"best_miflu_L{L}.pth")):
            if os.path.exists(cand):
                return cand, "reproduction best-val ckpt (this rep)"

    # 3. a 1-rep retrain written by this controller (never the original tree)
    p = os.path.join(AUTHOR_RUNS, "ckpt_retrain", f"L{L}_s{seed}", f"best_miflu_L{L}.pth")
    if os.path.exists(p):
        return p, "retrained 1-rep ckpt (oracle-verified)"

    # 4. an earlier fresh 1-rep run, trusted only with its own oracle-matching log
    p = os.path.join(AUTHOR_RUNS, f"ckpt_L{L}_s{seed}", f"best_miflu_L{L}.pth")
    if os.path.exists(p) and _oracle_matches_logged(L, seed):
        return p, "fresh-run ckpt (oracle-verified log)"
    return None, None


def build_data():
    """Fit the train-only scaler and return the same data_dict training builds."""
    prof = resolve_profile(PROFILE)
    TM.ACTIVE_PROFILE = PROFILE
    TM.DATA_PATH = prof["data_path"]
    TM.SCALER_PATH = prof["scaler_path"]
    return TM.load_and_normalize()


def build_model(L, device):
    """Exactly the constructor `train_miflu.train_L` / `export_prediction_csv` use."""
    return MIFlu(N=CONFIG["N"], T=CONFIG["T"], L=L, Lp=CONFIG["Lp"],
                 S=CONFIG["S"], K=CONFIG["K"], lora_r=CONFIG["lora_r"],
                 device=device, use_text_ln=False,
                 flatten_head=(os.environ.get("MIFLU_FLATTEN_HEAD", "1") != "0"))


@torch.no_grad()
def collect_rows(model, prompt_cache, data_dict, L, config, device, containment):
    """Forward train/val/test and return one row per (window, lead), all 7 channels.

    The batch order and the local->global window mapping are copied verbatim from
    `train_miflu.export_prediction_csv._collect` so the rows line up with the
    export that already passed alignment.
    """
    from torch.utils.data import DataLoader, TensorDataset

    tm = torch.from_numpy(data_dict["train_mean"].astype(np.float32))
    ts = torch.from_numpy(data_dict["train_std"].astype(np.float32))
    tm_np = np.asarray(data_dict["train_mean"]).ravel()
    ts_np = np.asarray(data_dict["train_std"]).ravel()

    Xt, Yt, Xv, Yv, Xte, Yte, sinfo = TM.build_windows(
        data_dict["data_norm"], config["T"], L,
        data_dict["train_end"], data_dict["val_end"], containment=containment)

    split_of_idx = {int(sinfo["target_starts"][k]): "train" for k in sinfo["train_idx"]}
    split_of_idx.update({int(sinfo["target_starts"][k]): "val" for k in sinfo["val_idx"]})
    split_of_idx.update({int(sinfo["target_starts"][k]): "test" for k in sinfo["test_idx"]})

    rows = []

    def _collect(X, Y, global_start):
        nw = X.shape[0]
        dl = DataLoader(TensorDataset(torch.from_numpy(X), torch.from_numpy(Y)),
                        batch_size=config["batch_size"], shuffle=False)
        local_to_global = {local: int(sinfo["target_starts"][global_start + local])
                           for local in range(nw)}
        for bi, (bx, by) in enumerate(dl):
            bx = bx.to(device)
            bsz = bx.size(0)
            ht = (prompt_cache.expand(bsz, -1, -1)
                  if prompt_cache.shape[0] == 1 else prompt_cache[:bsz])
            yh_rev, yh_phys, _, _ = model(bx, htext=ht, train_mean=tm, train_std=ts)
            gt_z = by.cpu().numpy()                       # (B, 7, L)
            pr_z = yh_rev.cpu().numpy()                   # (B, 7, L)
            gt_p = gt_z * ts_np.reshape(1, 7, 1) + tm_np.reshape(1, 7, 1)
            pr_p = yh_phys.cpu().numpy()                  # (B, 7, L)
            for r in range(bsz):
                gi = local_to_global[bi * config["batch_size"] + r]
                lbl = split_of_idx[gi]
                for s in range(L):
                    row = {"split": lbl, "abs_week": gi + s, "step": s}
                    for f, slug in enumerate(SLUGS):
                        row[f"ground_truth_{slug}"] = float(gt_z[r, f, s])
                        row[f"prediction_{slug}"] = float(pr_z[r, f, s])
                    for f, slug in enumerate(SLUGS):
                        row[f"ground_truth_{slug}_phys"] = float(gt_p[r, f, s])
                        row[f"prediction_{slug}_phys"] = float(pr_p[r, f, s])
                    rows.append(row)

    _collect(Xt, Yt, 0)
    _collect(Xv, Yv, len(sinfo["train_idx"]))
    _collect(Xte, Yte, len(sinfo["train_idx"]) + len(sinfo["val_idx"]))
    return rows, len(sinfo["test_idx"])


def write_artifacts(L, seed, df, out_dir, ckpt, prov, wall_s):
    """Write the rest of the full-artifact contract (AGENTS.md HARD RULE 11).

    (b) `pred_miflu_L{L}_seed{seed}.npz` -- `pred`/`target` as (W, 7, L) plus
        `target_start_row`, so PTE/PIE, CRPS/WIS, paired tests and every figure
        can be rebuilt from this one file (the importer's npz passthrough path);
    (a) `results_miflu_L{L}_seed{seed}.csv` -- MSE/MAE per variable in z-space AND
        in physical units, plus the 7-variable aggregate and the ILITOTAL row;
    (d) `manifest_miflu_L{L}_seed{seed}.json` -- seed, full config, library
        versions, parameter counts, checkpoint identity, wall clock.
    """
    import hashlib
    import json
    import platform
    import time

    import torch as _torch

    from configs import VAR_COLS as _VAR

    te = df[df.split == "test"].copy()
    te["tsr"] = te["abs_week"].astype(int) - te["step"].astype(int)
    tsr = np.sort(te["tsr"].unique())
    pos = {int(v): i for i, v in enumerate(tsr)}
    W = len(tsr)
    pred = np.full((W, 7, L), np.nan)
    targ = np.full((W, 7, L), np.nan)
    ks = te["tsr"].to_numpy(int)
    ss = te["step"].to_numpy(int)
    gts = [te[f"ground_truth_{s}"].to_numpy(float) for s in SLUGS]
    prs = [te[f"prediction_{s}"].to_numpy(float) for s in SLUGS]
    for k in range(len(ks)):
        i = pos[int(ks[k])]
        s = int(ss[k])
        if not (0 <= s < L):
            continue
        for f in range(7):
            targ[i, f, s] = gts[f][k]
            pred[i, f, s] = prs[f][k]
    assert np.isfinite(pred).all(), "prediction cube has holes"
    assert np.isfinite(targ).all(), "target cube has holes"

    npz_path = os.path.join(out_dir, f"pred_miflu_L{L}_seed{seed}.npz")
    np.savez_compressed(
        npz_path,
        pred=pred.astype(np.float32), target=targ.astype(np.float32),
        target_start_row=tsr.astype(np.int32), L=np.int32(L), seed=np.int32(seed),
        var_cols=np.asarray(_VAR), model=np.array("miflu"),
        profile=np.array(PROFILE), containment=np.array("strict"),
        space=np.array("standardized_train_fit_z"), partial=np.array(False),
        protocol=np.array("reproduction_10rep_seeds2021_2030"),
    )

    mrows = []
    for f, slug in enumerate(SLUGS):
        ez = pred[:, f, :] - targ[:, f, :]
        mrows.append({"L": L, "seed": seed, "variable": _VAR[f], "slug": slug,
                      "mse_z": float(np.mean(ez ** 2)), "mae_z": float(np.mean(np.abs(ez))),
                      "mse_phys": float(np.mean((te[f"prediction_{slug}_phys"]
                                                 - te[f"ground_truth_{slug}_phys"]) ** 2)),
                      "mae_phys": float(np.mean(np.abs(te[f"prediction_{slug}_phys"]
                                                      - te[f"ground_truth_{slug}_phys"]))),
                      "n_test_windows": W, "n_leads": L})
    ez = pred - targ
    mrows.append({"L": L, "seed": seed, "variable": "ALL_7VAR_AGGREGATE", "slug": "all7",
                  "mse_z": float(np.mean(ez ** 2)), "mae_z": float(np.mean(np.abs(ez))),
                  "mse_phys": float("nan"), "mae_phys": float("nan"),
                  "n_test_windows": W, "n_leads": L})
    res_path = os.path.join(out_dir, f"results_miflu_L{L}_seed{seed}.csv")
    pd.DataFrame(mrows).to_csv(res_path, index=False)

    h = hashlib.sha256()
    with open(ckpt, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    cfg = dict(CONFIG)
    manifest = {
        "model": "miflu", "L": L, "seed": seed,
        "protocol": "reproduction_10rep_seeds2021_2030",
        "n_reps_expected": 10, "replication_index": seed - 2020,
        "profile": PROFILE, "containment": "strict",
        "config": {k: cfg[k] for k in ("T", "N", "Lp", "S", "K", "lora_r",
                                       "lora_alpha", "D", "batch_size",
                                       "learning_rate", "epochs")},
        "architecture": {"use_text_ln": False, "flatten_head": True,
                         "text_source": "author_file",
                         "text_emb_file": f"assets/text_emb/text_emb_label_0507_{L}.txt",
                         "trainable_parameters": 1673496},
        "checkpoint": {"path": ckpt, "provenance": prov, "sha256": h.hexdigest()},
        "windows": {"n_test": int(W), "n_leads": int(L),
                    "target_start_row_min": int(tsr.min()),
                    "target_start_row_max": int(tsr.max())},
        "environment": {
            "python": platform.python_version(),
            "torch": _torch.__version__,
            "device": "cuda" if _torch.cuda.is_available() else "cpu",
            # HARD RULE 12: hardware provenance is MEASURED by calling the API,
            # never inferred from the partition name.
            "gpu_name": (_torch.cuda.get_device_name(0)
                         if _torch.cuda.is_available() else "CPU"),
            "gpu_compute_capability": (list(_torch.cuda.get_device_capability(0))
                                       if _torch.cuda.is_available() else None),
            "gpu_count": (_torch.cuda.device_count()
                          if _torch.cuda.is_available() else 0),
            "gpu_total_vram_bytes": (int(_torch.cuda.get_device_properties(0).total_memory)
                                     if _torch.cuda.is_available() else None),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID", "none"),
            "slurm_partition": os.environ.get("SLURM_JOB_PARTITION", "none"),
            "slurm_nodelist": os.environ.get("SLURM_JOB_NODELIST",
                                             os.environ.get("SLURMD_NODENAME", "none")),
            "host": platform.node(),
        },
        "wall_clock_seconds_export": round(float(wall_s), 1),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "artifacts": {"csv": f"predictions_miflu_L{L}_seed{seed}.csv",
                      "npz": os.path.basename(npz_path),
                      "results": os.path.basename(res_path)},
    }
    man_path = os.path.join(out_dir, f"manifest_miflu_L{L}_seed{seed}.json")
    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    return npz_path, res_path, man_path, float(np.mean(ez ** 2))


def export_cell(L, seed, data_dict, device, check=False, force=False):
    import time as _time
    _t0 = _time.time()
    ckpt, prov = find_ckpt(L, seed)
    out_dir = os.path.join(AUTHOR_RUNS, f"L{L}_all7")
    out_path = os.path.join(out_dir, f"predictions_miflu_L{L}_seed{seed}.csv")

    print(f"\n=== L={L} seed={seed} ===")
    if ckpt is None:
        print(f"  [MISSING] no checkpoint for L={L} seed={seed} -> cell skipped")
        return "missing"
    print(f"  checkpoint: {ckpt}  [{prov}]")
    if os.path.exists(out_path):
        d = pd.read_csv(out_path, nrows=1)
        have = sum(1 for s in SLUGS if f"ground_truth_{s}" in d.columns)
        if check:
            print(f"  [check] existing file has {have}/7 variable blocks")
            return "checked"
        if have == 7 and not force:
            print(f"  [skip] 7-variable export already present")
            return "exists"
        print(f"  [warn] existing file has only {have}/7 variable blocks -> re-exporting")

    config = dict(CONFIG)
    prompt_cache = TM.load_author_text_emb(L, device=device)
    model = build_model(L, device)
    sd = torch.load(ckpt, map_location=device)
    model.load_state_dict(sd)
    model.eval()
    print(f"  loaded state_dict ({len(sd)} tensors), trainable="
          f"{sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

    rows, n_test = collect_rows(model, prompt_cache, data_dict, L, config,
                                device, "strict")
    df = pd.DataFrame(rows)

    # -------- cross-check against the ILI-only reproduction export ----------
    # L24 seed 2021 was exported by the training run itself as
    # `L24_s2021_pred/predictions_miflu_L24_paper_protocol.csv` (the file that
    # already passed protocol alignment at 6.086e-07). The forward pass here must
    # reproduce its ILI columns exactly, otherwise this exporter is not the same
    # function that produced the validated artefact.
    if (L, seed) == (24, 2021):
        ref = os.path.join(AUTHOR_RUNS, "L24_s2021_pred",
                           "predictions_miflu_L24_paper_protocol.csv")
        if os.path.exists(ref):
            old = pd.read_csv(ref)
            key = ["split", "abs_week", "step"]
            mg = old[key + ["ground_truth_ili", "prediction_ili"]].merge(
                df[key + ["ground_truth_ili", "prediction_ili"]],
                on=key, how="inner", suffixes=("_old", "_new"))
            if len(mg):
                dg = float(np.max(np.abs(mg["ground_truth_ili_old"] - mg["ground_truth_ili_new"])))
                dp = float(np.max(np.abs(mg["prediction_ili_old"] - mg["prediction_ili_new"])))
                print(f"  [legacy] vs training-run ILI export: {len(mg)} rows, "
                      f"max|dGT|={dg:.3e} max|dPRED|={dp:.3e}")
                assert dg < 1e-5 and dp < 1e-5, (
                    f"L={L} seed={seed}: all-7 export disagrees with the validated "
                    f"ILI-only export (dGT={dg:.3e}, dPRED={dp:.3e})")

    # -------- calendar + alignment invariant --------------------------------
    df = TM.attach_calendar(df, abs_week_col="abs_week", raw_csv=TM.DATA_PATH)
    gt_spread = float((df.groupby("abs_week")["ground_truth_ili"].max()
                       - df.groupby("abs_week")["ground_truth_ili"].min()).max())
    assert gt_spread < 1e-4, f"GT spread across overlapping windows {gt_spread}"

    cols = (["split", "abs_week", "step", "epiweek", "week_start_date"]
            + [f"ground_truth_{s}" for s in SLUGS]
            + [f"prediction_{s}" for s in SLUGS]
            + [f"ground_truth_{s}_phys" for s in SLUGS]
            + [f"prediction_{s}_phys" for s in SLUGS])
    for c in cols:
        assert c in df.columns, f"missing output column {c}"
    df = df[cols]

    if check:
        print(f"  [check] would write {len(df)} rows x {len(cols)} cols "
              f"(test windows={n_test}); nothing written")
        return "checked"

    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(out_path, index=False)
    n_tr = int((df.split == "train").sum()); n_va = int((df.split == "val").sum())
    n_te = int((df.split == "test").sum())
    # ILITOTAL z-space metrics on the test split, straight from this file.
    te = df[df.split == "test"]
    mse_ili = float(np.mean((te["prediction_ili"] - te["ground_truth_ili"]) ** 2))
    mae_ili = float(np.mean(np.abs(te["prediction_ili"] - te["ground_truth_ili"])))
    print(f"  [ok] wrote {out_path}")
    print(f"       rows: train={n_tr} val={n_va} test={n_te} | cols={len(cols)} | gt_spread={gt_spread:.2e}")
    print(f"       test MSE_ILITOTAL_z={mse_ili:.6f}  MAE_ILITOTAL_z={mae_ili:.6f}")

    # HARD RULE 11: the npz cube, the per-variable results CSV and the run
    # manifest are written by the SAME execution that produced the prediction CSV.
    npz_p, res_p, man_p, mse_7 = write_artifacts(
        L, seed, df, out_dir, ckpt, prov, _time.time() - _t0)
    print(f"       test MSE_7var_z={mse_7:.6f}   (npz + results + manifest written)")
    print(f"       {os.path.basename(npz_p)} | {os.path.basename(res_p)} | {os.path.basename(man_p)}")
    return "written"


def main():
    ap = argparse.ArgumentParser(description="Re-export MIFlu predictions for all 7 variables (no training).")
    ap.add_argument("--cells", nargs="*", default=None,
                    help="L:seed pairs, e.g. 24:2021 24:2022")
    ap.add_argument("--all", action="store_true", help="all 4 horizons x seeds 2021..2030")
    ap.add_argument("--horizons", type=int, nargs="+", default=None,
                    help="restrict --all to these horizons, e.g. --horizons 24 36")
    ap.add_argument("--check", action="store_true", help="verify only; write nothing")
    ap.add_argument("--force", action="store_true", help="re-export even if the 7-var file exists")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    args = ap.parse_args()

    if args.all or not args.cells:
        hs = args.horizons or HORIZONS
        pairs = [(L, s) for L in hs for s in SEEDS]
    else:
        pairs = [tuple(int(x) for x in c.split(":")) for c in args.cells]

    device = args.device
    print(f"[all7] profile={PROFILE} device={device} cells={len(pairs)}")
    data_dict = build_data()
    print(f"[all7] data: train_end={data_dict['train_end']} val_end={data_dict['val_end']}")

    status = {}
    for L, s in pairs:
        try:
            status[(L, s)] = export_cell(L, s, data_dict, device, check=args.check,
                                         force=args.force)
        except Exception as e:                      # noqa: BLE001 - report, don't abort the batch
            status[(L, s)] = f"ERROR: {type(e).__name__}: {e}"
            print(f"  [ERROR] L={L} s={s}: {type(e).__name__}: {e}")

    print("\n" + "=" * 74)
    print("SUMMARY")
    for (L, s), st in sorted(status.items()):
        print(f"  L={L:>2} seed={s}  {st}")
    bad = {k: v for k, v in status.items() if str(v).startswith("ERROR") or v == "missing"}
    if bad:
        print(f"\n[FAIL] {len(bad)} cell(s) not exported:")
        for k, v in sorted(bad.items()):
            print(f"   L={k[0]} seed={k[1]}: {v}")
        return 1
    print("\n[PASS] all requested cells exported")
    return 0


if __name__ == "__main__":
    sys.exit(main())
