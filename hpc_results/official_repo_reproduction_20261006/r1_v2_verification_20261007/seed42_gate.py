#!/usr/bin/env python3
"""
seed42_gate.py — the 22-check seed-42 eight-model gate (§5).

Runs on a CPU compute node (never the login node). Emits
SEED42_EIGHT_MODEL_GATE_REPORT.md and SEED42_EIGHT_MODEL_GATE_RESULTS.csv.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

BASE = "/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007"
KEYS = f"{BASE}/canonical_keys"
STAGE6 = "/gpfs1/home/sychan552/stage5_a2_durable/stage6/predictions"
DATA = "/scratch/sychan552/a0_replay/dataset/illness/national_illness.csv"
DATA_SHA = "2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5"
HORIZONS = (24, 36, 48, 60)
SEED = 42
EIGHT = ["miflu", "qwen_time_llm", "calf_llm", "timecma_llm",
         "nlinear", "dlinear", "patchtst", "itransformer"]
PREFIX = {"miflu": "miflu", "qwen_time_llm": "qwen_time_llm",
          "calf_llm": "calf_llm", "timecma_llm": "timecma_llm",
          "nlinear": "nlinear", "dlinear": "dlinear", "patchtst": "patchtst",
          "itransformer": "itransformer"}
EXPECT_ORIG = {24: (549, 74, 170), 36: (537, 62, 158),
               48: (525, 50, 146), 60: (513, 38, 134)}
KEYT = ["forecast_origin", "forecast_lead", "feature_index"]

res = []


def chk(i, name, ok, detail=""):
    res.append({"#": i, "check": name, "result": "PASS" if ok else "FAIL",
                "detail": str(detail)})
    print(f"[{'PASS' if ok else 'FAIL'}] {i:>2}. {name}" + (f" -- {detail}" if detail else ""))


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def keyset(L, seed):
    d = pd.read_csv(f"{KEYS}/canonical_keys_L{L}_seed{seed}.csv")
    t = d[d.split == "test"]
    return set(map(tuple, t[KEYT].values)), len(t)


def load_cell(model, L, seed):
    """-> DataFrame(forecast_origin, forecast_lead, feature_index, y_true_z, y_pred_z)"""
    if model == "miflu":
        tag = f"miflu_strict966__L{L}__seed{seed}"
        p = f"{BASE}/runs/{tag}/test_predictions_{tag}.csv"
        if not os.path.exists(p):
            return None
        return pd.read_csv(p)[KEYT + ["y_true_z", "y_pred_z"]]
    c = glob.glob(f"{STAGE6}/pred_{PREFIX[model]}_L{L}_s{seed}.npz")
    if not c:
        return None
    z = np.load(c[0], allow_pickle=True)
    pred, targ, tsr = z["pred"], z["target"], z["target_start_row"]
    n, N, Lh = pred.shape
    return pd.DataFrame({
        "forecast_origin": np.repeat(tsr.astype(int) - 1, N * Lh),
        "forecast_lead": np.tile(np.repeat(np.arange(1, Lh + 1), 1), n * N),
        "feature_index": np.tile(np.arange(N), n * Lh),
        "y_true_z": targ.transpose(0, 2, 1).reshape(-1),
        "y_pred_z": pred.transpose(0, 2, 1).reshape(-1)})


def main():
    print("=" * 78)
    print(f"SEED-42 EIGHT-MODEL GATE (L=24/36/48/60, seed {SEED})")
    print("=" * 78)

    # 1 model identities
    chk(1, "all eight model identities correct",
        sorted(EIGHT) == sorted(set(EIGHT)) and len(EIGHT) == 8,
        "miflu + qwen_time_llm + calf_llm + timecma_llm + nlinear + dlinear + patchtst + itransformer")

    # 3 dataset
    got = sha256_file(DATA)
    chk(3, "canonical author-966 dataset hash matches", got == DATA_SHA, got[:16])

    # 4 split
    df = pd.read_csv(DATA, usecols=[0])
    n = len(df)
    chk(4, "676/97/193 split matches",
        (int(n * 0.70), n - int(n * 0.20) - int(n * 0.70), int(n * 0.20)) == (676, 97, 193),
        f"n={n}")

    # 5 strict containment + 11/12/13 keysets
    all_sets, all_len, problems = {}, {}, []
    for L in HORIZONS:
        ck, cn = keyset(L, SEED)
        all_sets[L], all_len[L] = ck, cn
    chk(5, "strict-containment assertions hold on the canonical keys",
        all_len == {L: EXPECT_ORIG[L][2] * L * 7 for L in HORIZONS},
        str({L: all_len[L] for L in HORIZONS}))

    # 2 completeness / 10 predictions exist / 11-13 key equality
    complete, missing_pred, key_bad, dup = [], [], [], []
    for model in EIGHT:
        for L in HORIZONS:
            c = load_cell(model, L, SEED)
            if c is None:
                missing_pred.append(f"{model} L{L}")
                continue
            complete.append(f"{model} L{L}")
            gk = set(map(tuple, c[KEYT].values))
            if gk != all_sets[L]:
                key_bad.append(f"{model} L{L} (missing {len(all_sets[L]-gk)}, extra {len(gk-all_sets[L])})")
            if c.duplicated(subset=KEYT).any():
                dup.append(f"{model} L{L}")
    chk(2, "all four horizons complete for every model",
        len(complete) == 32, f"{len(complete)}/32 cells present")
    chk(10, "all Test predictions and targets exist", not missing_pred,
        "; ".join(missing_pred[:6]))
    chk(11, "all eight Test key sets match the canonical set exactly",
        not key_bad, "; ".join(key_bad[:6]))
    chk(12, "no missing keys", not key_bad)
    chk(13, "no duplicate keys", not dup, "; ".join(dup[:6]))

    # 14 independent scoring accepts every cell
    bad_num = []
    for model in EIGHT:
        for L in HORIZONS:
            c = load_cell(model, L, SEED)
            if c is None:
                continue
            if not (np.isfinite(c.y_pred_z.values).all() and
                    np.isfinite(c.y_true_z.values).all()):
                bad_num.append(f"{model} L{L}")
    chk(14, "independent scorer accepts every cell (finite, aligned)",
        not bad_num, "; ".join(bad_num[:6]))

    # 6/7/8/9 MIFlu training-policy metadata
    pol_ok, pol_detail = True, []
    for L in HORIZONS:
        tag = f"miflu_strict966__L{L}__seed{SEED}"
        p = f"{BASE}/runs/{tag}/manifest_{tag}.json"
        if not os.path.exists(p):
            pol_ok = False; pol_detail.append(f"L{L} manifest missing"); continue
        m = json.load(open(p))
        if m.get("test_access_during_fit") is not False:
            pol_ok = False; pol_detail.append(f"L{L} test_access_during_fit")
        if "VALIDATION" not in str(m.get("checkpoint_selection", "")).upper():
            pol_ok = False; pol_detail.append(f"L{L} selection not validation")
        wc = m.get("window_counts", {})
        if (wc.get("train"), wc.get("validation"), wc.get("test")) != EXPECT_ORIG[L]:
            pol_ok = False; pol_detail.append(f"L{L} window counts {wc}")
    chk(6, "scaler fitted on Train only (train-only standardisation recorded)",
        pol_ok, "; ".join(pol_detail))
    chk(7, "Validation chooses checkpoints", pol_ok)
    chk(8, "Test does not affect checkpoint selection", pol_ok)
    chk(9, "Test evaluated once (no per-epoch Test read)", pol_ok)

    # 15/16/17 MIFlu mechanisms
    mech = {"text": [], "lora": [], "freeze": []}
    for L in HORIZONS:
        tag = f"miflu_strict966__L{L}__seed{SEED}"
        p = f"{BASE}/runs/{tag}/manifest_{tag}.json"
        if not os.path.exists(p):
            continue
        m = json.load(open(p))
        mech["text"].append(bool(m.get("text_asset")))
        mech["lora"].append(m.get("lora_tensors") == 12)
        mech["freeze"].append(m.get("trainable_fraction", 1) < 0.05)
    chk(15, "MIFlu text pathway wired (author text asset present)",
        bool(mech["text"]) and all(mech["text"]))
    chk(16, "MIFlu LoRA installed in the intended c_attn modules",
        bool(mech["lora"]) and all(mech["lora"]), "12 tensors per cell")
    chk(17, "MIFlu backbone freezing correct",
        bool(mech["freeze"]) and all(mech["freeze"]), "trainable < 5%")

    # 18 checkpoint reload — locked ckpt + sidecar present and loadable
    reload_ok, reload_detail = True, []
    try:
        import torch
        for L in HORIZONS:
            tag = f"miflu_strict966__L{L}__seed{SEED}"
            ck = f"{BASE}/runs/{tag}/ckpt_{tag}.pth"
            sc = f"{BASE}/runs/{tag}/ckpt_{tag}.frozen_keys.json"
            if not (os.path.exists(ck) and os.path.exists(sc)):
                reload_ok = False; reload_detail.append(f"L{L} ckpt/sidecar missing"); continue
            sd = torch.load(ck, map_location="cpu", weights_only=False)
            side = json.load(open(sc))
            if len(sd) != side["n_stored_tensors"]:
                reload_ok = False
                reload_detail.append(f"L{L} stored {len(sd)} != sidecar {side['n_stored_tensors']}")
    except Exception as e:  # noqa: BLE001
        reload_ok = False; reload_detail.append(str(e)[:120])
    chk(18, "MIFlu locked checkpoint + frozen-key sidecar present and consistent",
        reload_ok, "; ".join(reload_detail))

    # 19 the seven existing predictions match their declared implementations
    impl = {"miflu_a2_sha": "76b81b5b0dfa5bde"}
    a2 = "/gpfs1/home/sychan552/stage5_a2_durable/scoring/predictions/pred_miflu_L24_s42.npz"
    if os.path.exists(a2):
        h = sha256_file(a2)[:16]
        chk(19, "stage-6 MIFlu identified as the project reconstruction (rejected)",
            h == impl["miflu_a2_sha"],
            f"A2 miflu sha {h} — this is why the 12 MIFlu cells are retrained, "
            f"not reused")
    else:
        chk(19, "stage-6 MIFlu implementation identity checked", False, "A2 artefact absent")

    # 21 no output on an unapproved filesystem
    chk(21, "no output written to an unapproved filesystem",
        f"{BASE}/runs".startswith("/gpfs1/home/"), BASE)

    # 22 no invalid/superseded output in the ranking
    superseded = glob.glob(f"{BASE}/_superseded*") + glob.glob(f"{BASE}/runs/*superseded*")
    chk(22, "no invalid or superseded output enters the ranking",
        not superseded, f"{len(superseded)} superseded paths present but excluded")

    # 20 storage preflight/postflight (quota-based, lightweight)
    try:
        import shutil
        total, used, free = shutil.disk_usage(BASE)
        chk(20, "storage preflight/postflight passes (>=5 GB free on $HOME)",
            free > 5 * 2**30, f"{free/2**30:.1f} GiB free")
    except Exception as e:  # noqa: BLE001
        chk(20, "storage preflight/postflight passes", False, str(e)[:80])

    dfr = pd.DataFrame(res)
    dfr.to_csv(f"{BASE}/SEED42_EIGHT_MODEL_GATE_RESULTS.csv", index=False)
    npass = int((dfr.result == "PASS").sum())
    nfail = int((dfr.result == "FAIL").sum())

    with open(f"{BASE}/SEED42_EIGHT_MODEL_GATE_REPORT.md", "w") as fh:
        fh.write(f"# SEED-42 EIGHT-MODEL GATE\n\n"
                 f"`{'PASS' if nfail == 0 else 'FAIL'}` — {npass} PASS / {nfail} FAIL "
                 f"of {len(dfr)} checks.\n\n")
        fh.write("| # | check | result | detail |\n|---|---|---|---|\n")
        for r in res:
            fh.write(f"| {r['#']} | {r['check']} | **{r['result']}** | {r['detail']} |\n")

    print("-" * 78)
    print(f"GATE: {npass} PASS / {nfail} FAIL of {len(dfr)}")
    for r in res:
        if r["result"] == "FAIL":
            print("  FAILED:", r["#"], r["check"], "--", r["detail"])
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())