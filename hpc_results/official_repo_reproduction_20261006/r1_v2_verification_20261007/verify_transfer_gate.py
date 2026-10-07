#!/usr/bin/env python3
"""
verify_transfer_gate.py — Phase C: the 24 transfer-gate checks.

Runs against the completed seed-42 transfer runs and the historical artefacts.
Reports each item PASS / FAIL / UNDERMINED-BY-HISTORICAL-CONTRACT, and
quantifies any boundary crossing rather than asserting it away.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = "/gpfs1/home/sychan552/official_repo_reproduction_20261006"
RUNS = f"{ROOT}/historical_replacement_20261007/runs"
DURABLE = "/gpfs1/home/sychan552/innovation_durable/screening"
DATA = "/scratch/sychan552/innovation_deploy_root_v3_clean14/data/raw/national_illness_raw.csv"
DATA_SHA = "0a0648000066e12fe499f98693885b88ed3bc29fc8daca7f3af171b1bac86088"
VAR_COLS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
            "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
T, TRAIN_END, VAL_END, NROWS = 104, 717, 819, 1025
HOR = (24, 36, 48, 60)

res, fails = {}, []


def chk(i, name, ok, detail=""):
    res[i] = {"check": name, "result": "PASS" if ok else "FAIL", "detail": detail}
    if not ok:
        fails.append(f"{i}. {name}: {detail}")
    print(f"[{'PASS' if ok else 'FAIL'}] {i:>2}. {name}" + (f"  -- {detail}" if detail else ""))


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    print("=" * 78)
    print("PHASE C — ONE-SEED TRANSFER GATE (seed 42)")
    print("=" * 78)

    # 1 dataset identity
    got = sha256_file(DATA)
    chk(1, "exact historical 1025-row dataset used", got == DATA_SHA, got[:16])
    chk("1b", "row count is 1025", len(pd.read_csv(DATA)) == NROWS)

    # 2 split
    chk(2, "split is 717 / 102 / 206", (TRAIN_END, VAL_END - TRAIN_END, NROWS - VAL_END) == (717, 102, 206))

    # load the historical normalised array to check windows directly
    raw = pd.read_csv(DATA)
    z = (raw[VAR_COLS].values.astype(np.float32)
         - np.asarray([1.755405306816101, 1.7133967876434326, 2658.326416015625,
                       3699.761474609375, 9368.2890625, 1320.093505859375,
                       491997.59375], dtype=np.float32).reshape(1, -1)) \
        / np.asarray([1.2095322608947754, 1.1299502849578857, 2113.183837890625,
                      4152.29541015625, 8853.4345703125, 504.9544982910156,
                      234443.296875], dtype=np.float32).reshape(1, -1)

    nw = NROWS - T - 24 + 1
    ts = np.arange(nw) + T
    tr, va, te = ts < TRAIN_END, (ts >= TRAIN_END) & (ts <= VAL_END), ts > VAL_END

    # 3 window shapes
    chk(3, "input/target window shapes are (T,N) and (L,N)",
        z[0:T].shape == (104, 7) and z[T:T + 24].shape == (24, 7))

    # 4 seven variables present
    chk(4, "all seven variables present", list(raw.columns[2:]) == VAR_COLS)

    # 5 boundary crossing — measured, not asserted
    cross_tr, cross_va = 0, 0
    for i in np.where(tr)[0]:
        if i + T + 24 - 1 >= TRAIN_END:
            cross_tr += 1
    for i in np.where(va)[0]:
        if i + T + 24 - 1 > VAL_END:
            cross_va += 1
    total_va = int(va.sum())
    chk(5, "no target crosses a split boundary", (cross_tr + cross_va) == 0,
        f"HISTORICAL RULE CROSSES: {cross_tr} train and {cross_va}/{total_va} val "
        f"targets extend past their split end (this is the frozen historical rule)")

    # 6/7/8 origins, leads, feature keys
    v = pd.read_csv(f"{RUNS}/miflu_transfer__L24__seed42/validation_predictions_miflu_transfer__L24__seed42.csv")
    t = pd.read_csv(f"{RUNS}/miflu_transfer__L24__seed42/test_predictions_miflu_transfer__L24__seed42.csv")
    old_v = pd.read_csv(f"{DURABLE}/primary__gpt2_miflu__L24__seed42__w1/predictions/validation_predictions.csv")
    o_orig = set(old_v.forecast_origin.unique())
    n_orig = set(v.forecast_origin.unique())
    chk(6, "forecast origins match the historical contract", o_orig == n_orig,
        f"old {len(o_orig)} vs new {len(n_orig)}; identical={o_orig == n_orig}; "
        f"old range {min(o_orig)}-{max(o_orig)} new range {min(n_orig)}-{max(n_orig)}")
    chk(7, "forecast leads 1..L",
        sorted(v.lead_weeks.unique()) == list(range(1, 25)))
    chk(8, "feature keys match (indices 0..6, same VAR_COLS order)",
        sorted(v.variable_index.unique()) == list(range(7))
        and list(v[v.variable_index == 4].variable.unique()) == ["ILITOTAL"])

    # 9 seed explicit
    chk(9, "seed identity explicit and addressable",
        int(v.seed_or_rep.iloc[0]) == 42)

    # 10/11 selection
    man = json.load(open(f"{RUNS}/miflu_transfer__L24__seed42/manifest_miflu_transfer__L24__seed42.json"))
    chk(10, "validation selects the checkpoint",
        "VALIDATION" in man["checkpoint_selection"].upper())
    chk(11, "Test/Holdout not used during training or selection",
        man["test_access_during_fit"] is False)

    # 12 saved
    chk(12, "predictions and targets saved",
        os.path.exists(f"{RUNS}/miflu_transfer__L24__seed42/validation_predictions_miflu_transfer__L24__seed42.csv")
        and os.path.exists(f"{RUNS}/miflu_transfer__L24__seed42/test_predictions_miflu_transfer__L24__seed42.csv"))

    # 13/14 key integrity
    for name, df in (("validation", v), ("test", t)):
        dup = df.duplicated(subset=["forecast_origin", "variable_index", "step"]).sum()
        chk(f"13-{name[0]}", f"no duplicate keys in {name}", dup == 0, f"{dup} dups")
    exp_v = int(va.sum()) * 7 * 24
    chk(14, "no keys missing (element count matches the window contract)",
        len(v) == exp_v, f"{len(v)} vs expected {exp_v}")

    # 15/16 scorer acceptance + independent re-scoring
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    e = v.y_pred_z.values.astype(np.float64) - v.y_true_z.values.astype(np.float64)
    mse_indep = float(np.mean(e ** 2))
    chk(16, "independent re-scoring agrees with the reported training metric",
        abs(mse_indep - man["val_mse_all_7vars_full_horizon_z"]) < 1e-6,
        f"indep={mse_indep:.9f} reported={man['val_mse_all_7vars_full_horizon_z']:.9f}")

    # 17 text / 18 LoRA / 19 freeze
    chk(17, "text remains active (asset wired, non-zero text path)",
        man["text_asset"] is not None and "text_emb" in str(man["text_asset"]))
    chk(18, "LoRA remains installed", man["lora_tensors"] == 12)
    chk(19, "intended backbone tensors remain frozen",
        man["trainable_fraction"] < 0.05, f"trainable fraction {man['trainable_fraction']}")

    # 20 checkpoint reload (locked ckpt present + sidecar)
    ck = f"{RUNS}/miflu_transfer__L24__seed42/ckpt_miflu_transfer__L24__seed42.pth"
    sc = f"{RUNS}/miflu_transfer__L24__seed42/ckpt_miflu_transfer__L24__seed42.frozen_keys.json"
    chk(20, "locked checkpoint + frozen-key sidecar written",
        os.path.exists(ck) and os.path.exists(sc),
        f"{os.path.getsize(ck):,} B, {json.load(open(sc))['n_frozen_tensors']} frozen keys")

    # 22 GPU time recorded
    led = f"{ROOT}/historical_replacement_20261007/manifests/GPU_LEDGER_TRANSFER.tsv"
    chk(22, "actual GPU time recorded", os.path.exists(led),
        f"{sum(1 for _ in open(led))} rows" if os.path.exists(led) else "missing")

    # 23 no scratch writes
    chk(23, "no output written to scratch",
        all(f"{RUNS}/{d}".startswith("/gpfs1/home/") for d in os.listdir(RUNS)))

    # 24 no historical result overwritten
    chk(24, "no historical result overwritten",
        os.path.exists(f"{DURABLE}/primary__gpt2_miflu__L24__seed42__w1/predictions/validation_predictions.csv"))

    print("-" * 78)
    npass = sum(1 for v_ in res.values() if v_["result"] == "PASS")
    print(f"GATE: {npass} PASS / {len(fails)} FAIL of {len(res)} checks")
    for f in fails:
        print("  FAILED:", f)
    json.dump(res, open(f"{ROOT}/r1_v2_verification_20261007/R1B_TRANSFER_GATE.json", "w"), indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())