#!/usr/bin/env python3
"""
verify_stage6_reuse.py — can the existing stage-6 author-966 predictions be
reused for Track C, or must each cell be retrained?

Assigns every (model, horizon, seed) cell one of:
  RESCORE_ONLY / REINFERENCE_ONLY / GPU_RETRAIN / BLOCKED
based on measured compatibility with the canonical strict-966 key contract.
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np
import pandas as pd

STAGE6 = "/gpfs1/home/sychan552/stage5_a2_durable/stage6/predictions"
KEYS = ("/gpfs1/home/sychan552/official_repo_reproduction_20261006/"
        "strict966_championship_20261007/canonical_keys")
EXPECT_ORIG = {24: (549, 74, 170), 36: (537, 62, 158),
               48: (525, 50, 146), 60: (513, 38, 134)}
# canonical model name -> the prefix used in the stage-6 artefact filenames
MODELS_8 = ["miflu", "qwen", "calf", "timecma", "nlinear", "dlinear",
            "patchtst", "itransformer"]
FILE_PREFIX = {"miflu": "miflu", "qwen": "qwen_time_llm", "calf": "calf_llm",
               "timecma": "timecma_llm", "nlinear": "nlinear",
               "dlinear": "dlinear", "patchtst": "patchtst",
               "itransformer": "itransformer"}
SEEDS = (42, 43, 44)


def canon_test_origins(L, seed):
    d = pd.read_csv(f"{KEYS}/canonical_keys_L{L}_seed{seed}.csv")
    t = d[d.split == "test"]
    return sorted(t.forecast_origin.unique()), len(t)


rows = []
for model in MODELS_8:
    for L in (24, 36, 48, 60):
        for seed in SEEDS:
            cands = glob.glob(f"{STAGE6}/pred_{FILE_PREFIX[model]}_L{L}_s{seed}.npz")
            rec = {"model": model, "L": L, "seed": seed, "file": "",
                   "class": "", "reason": ""}
            if not cands:
                rec["class"] = "GPU_RETRAIN"
                rec["reason"] = "no existing prediction artefact"
                rows.append(rec)
                continue
            f = cands[0]
            rec["file"] = os.path.basename(f)
            try:
                z = np.load(f, allow_pickle=True)
                keys = set(z.files)
                reasons = []
                # containment
                cont = str(z["containment"]) if "containment" in keys else "MISSING"
                if cont != "strict":
                    reasons.append(f"containment={cont}")
                # profile / dataset
                prof = str(z["profile"]) if "profile" in keys else "MISSING"
                if prof != "author_966":
                    reasons.append(f"profile={prof}")
                # space
                sp = str(z["space"]) if "space" in keys else "MISSING"
                if sp != "standardized_train_fit_z":
                    reasons.append(f"space={sp}")
                # shapes / origin match
                o_exp, n_exp = canon_test_origins(L, seed)
                if "pred" not in keys or "target_start_row" not in keys:
                    reasons.append("missing pred/target_start_row")
                else:
                    pred = z["pred"]
                    tsr = z["target_start_row"]
                    if pred.shape != (len(o_exp), 7, L):
                        reasons.append(f"pred shape {pred.shape} != "
                                       f"{(len(o_exp), 7, L)}")
                    # origins in this artefact are TARGET STARTS; canonical
                    # forecast_origin = target_start - 1
                    got_origins = sorted(int(x) - 1 for x in tsr)
                    if got_origins != o_exp:
                        reasons.append("origin set mismatch vs canonical")
                # var cols
                if "var_cols" in keys:
                    vc = list(z["var_cols"])
                    if vc != ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4",
                              "AGE 5-24", "ILITOTAL", "NUM. OF PROVIDERS", "OT"]:
                        reasons.append("var_cols mismatch")
                # IMPLEMENTATION IDENTITY (§6). The stage-6 `miflu` artefact is
                # byte-identical to the A2 artefact (sha 76b81b5b0dfa5bde) and is
                # therefore the PROJECT'S RECONSTRUCTION, not the official-
                # repository-based implementation that Track C requires.
                # Key compatibility is NOT sufficient: the wrong implementation
                # would silently substitute the model the brief forbids.
                if model == "miflu":
                    reasons.append("implementation is the project reconstruction "
                                   "(== A2 artefact, sha 76b81b5b…), not the "
                                   "official-repository MIFlu required by §6")
                if reasons:
                    rec["class"] = "GPU_RETRAIN"
                    rec["reason"] = "; ".join(reasons)
                else:
                    rec["class"] = "RESCORE_ONLY"
                    rec["reason"] = ("strict-966, author_966, z-space, canonical "
                                     "origins, var_cols and shape all match")
            except Exception as e:  # noqa: BLE001
                rec["class"] = "BLOCKED"
                rec["reason"] = f"read error: {e}"
            rows.append(rec)

df = pd.DataFrame(rows)
print(df.to_string(index=False))
print()
print("=== class summary ===")
print(df.groupby("class").size().to_string())
print()
print("=== per model ===")
print(df.pivot_table(index="model", columns="class", values="L",
                     aggfunc="count", fill_value=0).to_string())
out = "/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1_v2_verification_20261007/STRICT_966_CELL_CLASSIFICATION.csv"
df.to_csv(out, index=False)
print(f"\nwrote {out}")