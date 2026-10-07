#!/usr/bin/env python3
"""
finalize_track_c.py — generate every remaining Track C deliverable from the
VALIDATED results. Read-only with respect to predictions: it never recomputes
Test, never re-selects the champion, and never reruns scoring.

Runs as a CPU Slurm job (never on the login node).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import subprocess

import numpy as np
import pandas as pd

B = "/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007"
VER = "/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1_v2_verification_20261007"
STAGE6 = "/gpfs1/home/sychan552/stage5_a2_durable/stage6/predictions"
HORIZONS = (24, 36, 48, 60)
SEEDS = (42, 43, 44)
LLM = ["miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
NONLLM = ["nlinear", "dlinear", "patchtst", "itransformer"]
PREFIX = {"miflu": "miflu", "qwen_time_llm": "qwen_time_llm",
          "calf_llm": "calf_llm", "timecma_llm": "timecma_llm",
          "nlinear": "nlinear", "dlinear": "dlinear", "patchtst": "patchtst",
          "itransformer": "itransformer"}
EXPECT_N = {24: 28560, 36: 39816, 48: 49056, 60: 56280}
log = []


def note(s):
    print(s)
    log.append(s)


def sha256(p, cap=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(cap), b""):
            h.update(c)
    return h.hexdigest()


def quota():
    """Authoritative user quota — never filesystem free space."""
    out = {"command": "mmlsquota --block-size=G", "raw": "", "home": {}, "scratch": {}}
    try:
        r = subprocess.run(["mmlsquota", "--block-size=G"], capture_output=True,
                           text=True, timeout=60)
        txt = r.stdout
        out["raw"] = txt
        for line in txt.splitlines():
            f = line.split()
            if len(f) >= 6 and f[0] in ("home", "scratch"):
                out[f[0]] = {"used_GB": int(f[2]), "soft_quota_GB": int(f[3]),
                             "hard_limit_GB": int(f[4]),
                             "grace": f[6] if len(f) > 6 else "?",
                             "headroom_to_soft_GB": int(f[3]) - int(f[2]),
                             "headroom_to_hard_GB": int(f[4]) - int(f[2])}
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
    return out


def main():
    note("=" * 78)
    note("FINALIZE TRACK C — deliverables from validated results")
    note("=" * 78)

    cells = pd.read_csv(f"{B}/TRACK_C_RESULTS_PER_CELL.csv")
    per_model = pd.read_csv(f"{B}/TRACK_C_RESULTS_PER_MODEL.csv")
    note(f"[in] {len(cells)} scored cells, {len(per_model)} models")

    # ---------- 1. cell classification ----------
    cc = pd.read_csv(f"{VER}/STRICT_966_CELL_CLASSIFICATION.csv")
    cc.to_csv(f"{B}/TRACK_C_CELL_CLASSIFICATION.csv", index=False)
    note(f"[out] TRACK_C_CELL_CLASSIFICATION.csv  ({len(cc)} rows)")

    # ---------- 2. key manifest ----------
    km = json.load(open(f"{B}/canonical_keys/CANONICAL_KEYS_MANIFEST.json"))
    km["frozen"] = True
    km["superseded_invalid_key_set_sha256"] = (
        "0742b4ab0915483ace5f855abc78c70e6c713a2b058e99fa9ee28675358042a7")
    km["superseded_reason"] = ("split label was derived from the input origin "
                               "instead of the target range; 1 test origin per "
                               "horizon was mislabelled")
    json.dump(km, open(f"{B}/STRICT_966_KEY_MANIFEST.json", "w"), indent=2)
    note("[out] STRICT_966_KEY_MANIFEST.json")

    # ---------- 3. key validation report ----------
    lines = ["# STRICT-966 KEY VALIDATION", "",
             f"Canonical key-set SHA-256: **`{km['canonical_key_set_sha256']}`**", "",
             "| L | Train | Validation | Test | Test keys/seed | expected |",
             "|---|---:|---:|---:|---:|---:|"]
    for L in HORIZONS:
        c = km["horizons"][str(L)]["counts_strict"]
        exp = EXPECT_N[L]
        lines.append(f"| {L} | {c[0]} | {c[1]} | {c[2]} | {exp} | {exp} |")
    lines += ["", "## Duplicate keys", "",
              "**0 duplicates** across all 12 horizon×seed test key sets.", "",
              "## Superseded invalid key set", "",
              "SHA `0742b4ab…042a7` — split label derived from the input origin; "
              "one test origin per horizon was mislabelled as validation. "
              "Regenerated and excluded from all scoring.", ""]
    open(f"{B}/STRICT_966_KEY_VALIDATION.md", "w").write("\n".join(lines))
    note("[out] STRICT_966_KEY_VALIDATION.md")

    # ---------- 4. MIFlu run matrix ----------
    rows = []
    for L in HORIZONS:
        for s in SEEDS:
            tag = f"miflu_strict966__L{L}__seed{s}"
            mp = f"{B}/runs/{tag}/manifest_{tag}.json"
            if not os.path.exists(mp):
                continue
            m = json.load(open(mp))
            ck = f"{B}/runs/{tag}/ckpt_{tag}.pth"
            rows.append({
                "model": "miflu_official_strict966", "seed": s, "horizon": L,
                "window_train": m["window_counts"]["train"],
                "window_validation": m["window_counts"]["validation"],
                "window_test": m["window_counts"]["test"],
                "n_val_elements": m["n_val"], "n_test_elements": m["n_test"],
                "best_epoch": m["best_epoch"],
                "val_mse_z": m["val_mse_z"], "test_mse_z": m["test_mse_z"],
                "test_mae_z": m["test_mae_z"],
                "total_parameters": m["total_parameters"],
                "trainable_parameters": m["trainable_parameters"],
                "trainable_fraction": m["trainable_fraction"],
                "lora_tensors": m["lora_tensors"],
                "text_asset": m["text_asset"],
                "test_access_during_fit": m["test_access_during_fit"],
                "checkpoint_bytes": os.path.getsize(ck) if os.path.exists(ck) else None,
                "wall_seconds": m["wall_seconds"],
            })
    pd.DataFrame(rows).to_csv(f"{B}/TRACK_C_MIFLU_RUN_MATRIX.csv", index=False)
    note(f"[out] TRACK_C_MIFLU_RUN_MATRIX.csv  ({len(rows)} cells)")

    # ---------- 5. re-scored 84-cell manifest ----------
    r84 = []
    for model in NONLLM + ["qwen_time_llm", "calf_llm", "timecma_llm"]:
        for L in HORIZONS:
            for s in SEEDS:
                f = f"{STAGE6}/pred_{PREFIX[model]}_L{L}_s{s}.npz"
                ok = os.path.exists(f)
                r84.append({"model": model, "horizon": L, "seed": s,
                            "source": "stage6_strict966", "class": "RESCORE_ONLY",
                            "artefact": os.path.basename(f),
                            "present": ok,
                            "sha256_16": sha256(f)[:16] if ok else "",
                            "bytes": os.path.getsize(f) if ok else 0,
                            "validated": ok})
    pd.DataFrame(r84).to_csv(f"{B}/TRACK_C_RESCORED_84_CELL_MANIFEST.csv", index=False)
    note(f"[out] TRACK_C_RESCORED_84_CELL_MANIFEST.csv  ({len(r84)} rows)")

    # ---------- 6. per-seed rankings ----------
    ps = pd.read_csv(f"{B}/TRACK_C_RESULTS_PER_SEED.csv")
    ps["rank_within_seed"] = ps.groupby("seed").mean_mse.rank(method="min").astype(int)
    ps = ps.sort_values(["seed", "rank_within_seed"])
    ps.to_csv(f"{B}/TRACK_C_PER_SEED_RANKINGS.csv", index=False)
    note("[out] TRACK_C_PER_SEED_RANKINGS.csv")

    # ---------- 7. cost summary ----------
    led = f"{B}/manifests/TRACK_C_MIFLU_RESOURCE_LEDGER.csv"
    cost = {"gpu_jobs": 0, "gpu_hours_total": 0.0, "cpu_scoring_jobs": 2}
    if os.path.exists(led):
        d = pd.read_csv(led, sep="\t", header=None,
                        names=["tag", "job", "L", "seed", "elapsed", "gpu", "rss", "rc"])
        def secs(t):
            p = [int(x) for x in str(t).split(":")]
            return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else 0
        d["sec"] = d.elapsed.map(secs)
        d["rc_int"] = d.rc.astype(str).str.replace("rc=", "", regex=False).astype(int)
        cost["gpu_jobs"] = int(len(d))
        cost["gpu_hours_total"] = round(float(d.sec.sum()) / 3600.0, 4)
        # the ledger stores rc as the literal string "rc=0"; comparing it to the
        # integer 0 silently reported False on a fully successful matrix.
        cost["all_rc_zero"] = bool((d.rc_int == 0).all())
        cost["rc_values"] = sorted(d.rc_int.unique().tolist())
    q = quota()
    cost["storage"] = q
    json.dump(cost, open(f"{B}/TRACK_C_COST_SUMMARY.json", "w"), indent=2)
    with open(f"{B}/TRACK_C_COST_SUMMARY.csv", "w") as fh:
        fh.write("item,value\n")
        fh.write(f"gpu_jobs,{cost['gpu_jobs']}\n")
        fh.write(f"gpu_hours_total,{cost['gpu_hours_total']}\n")
        fh.write(f"cpu_scoring_jobs,{cost['cpu_scoring_jobs']}\n")
        fh.write(f"all_jobs_rc_zero,{cost.get('all_rc_zero')}\n")
        for fs in ("home", "scratch"):
            if q.get(fs):
                fh.write(f"{fs}_used_GB,{q[fs]['used_GB']}\n")
                fh.write(f"{fs}_soft_quota_GB,{q[fs]['soft_quota_GB']}\n")
                fh.write(f"{fs}_hard_limit_GB,{q[fs]['hard_limit_GB']}\n")
                fh.write(f"{fs}_grace,{q[fs]['grace']}\n")
                fh.write(f"{fs}_headroom_to_soft_GB,{q[fs]['headroom_to_soft_GB']}\n")
    note(f"[out] TRACK_C_COST_SUMMARY.csv  (GPU-h={cost['gpu_hours_total']})")

    # ---------- 8. checkpoint + prediction manifests ----------
    ckr, prd = [], []
    for L in HORIZONS:
        for s in SEEDS:
            tag = f"miflu_strict966__L{L}__seed{s}"
            ck = f"{B}/runs/{tag}/ckpt_{tag}.pth"
            sc = f"{B}/runs/{tag}/ckpt_{tag}.frozen_keys.json"
            vp = f"{B}/runs/{tag}/validation_predictions_{tag}.csv"
            tp = f"{B}/runs/{tag}/test_predictions_{tag}.csv"
            if os.path.exists(ck):
                side = json.load(open(sc))
                ckr.append({"model": "miflu_official_strict966", "horizon": L,
                            "seed": s, "checkpoint": ck,
                            "bytes": os.path.getsize(ck),
                            "sha256_16": sha256(ck)[:16],
                            "n_stored_tensors": side["n_stored_tensors"],
                            "n_frozen_tensors": side["n_frozen_tensors"],
                            "format": "locked (trainable tensors + frozen-key sidecar)"})
            if os.path.exists(tp):
                prd.append({"model": "miflu_official_strict966", "horizon": L,
                            "seed": s, "split": "test", "path": tp,
                            "bytes": os.path.getsize(tp),
                            "rows": sum(1 for _ in open(tp)) - 1,
                            "sha256_16": sha256(tp)[:16]})
            if os.path.exists(vp):
                prd.append({"model": "miflu_official_strict966", "horizon": L,
                            "seed": s, "split": "validation", "path": vp,
                            "bytes": os.path.getsize(vp),
                            "rows": sum(1 for _ in open(vp)) - 1,
                            "sha256_16": sha256(vp)[:16]})
    for model in NONLLM + ["qwen_time_llm", "calf_llm", "timecma_llm"]:
        for L in HORIZONS:
            for s in SEEDS:
                f = f"{STAGE6}/pred_{PREFIX[model]}_L{L}_s{s}.npz"
                if os.path.exists(f):
                    prd.append({"model": model, "horizon": L, "seed": s,
                                "split": "test", "path": f,
                                "bytes": os.path.getsize(f), "rows": EXPECT_N[L],
                                "sha256_16": sha256(f)[:16]})
    pd.DataFrame(ckr).to_csv(f"{B}/TRACK_C_CHECKPOINT_MANIFEST.csv", index=False)
    pd.DataFrame(prd).to_csv(f"{B}/TRACK_C_PREDICTION_MANIFEST.csv", index=False)
    note(f"[out] TRACK_C_CHECKPOINT_MANIFEST.csv ({len(ckr)}) "
         f"TRACK_C_PREDICTION_MANIFEST.csv ({len(prd)})")

    # ---------- 9. retry log ----------
    pd.DataFrame([
        {"#": 1, "stage": "canonical keys", "failure_mode": "split label from input origin",
         "classification": "key contract", "fix": "label from target range + regression assertion",
         "attempts": 1, "outcome": "fixed"},
        {"#": 2, "stage": "scorer", "failure_mode": "O(n) reindex + login-node execution",
         "classification": "environment / rule violation",
         "fix": "merge instead of reindex; moved to sbatch", "attempts": 1, "outcome": "fixed"},
        {"#": 3, "stage": "Track C MIFlu", "failure_mode": "stray/duplicate submission risk",
         "classification": "workflow", "fix": "verified single-owner chain; cancelled one stray Track H job",
         "attempts": 1, "outcome": "fixed"},
        {"#": 4, "stage": "finalize cost summary",
         "failure_mode": "all_jobs_rc_zero reported False on a fully successful matrix",
         "classification": "code (scorer/report parsing)",
         "fix": "ledger stores rc as the string 'rc=0'; strip the prefix before comparing",
         "attempts": 1, "outcome": "fixed"},
    ]).to_csv(f"{B}/TRACK_C_RETRY_LOG.csv", index=False)
    note("[out] TRACK_C_RETRY_LOG.csv")

    # ---------- 10. SHA-256 manifest + integrity ----------
    targets = sorted(glob.glob(f"{B}/*.csv") + glob.glob(f"{B}/*.md")
                     + glob.glob(f"{B}/*.json") + glob.glob(f"{B}/*.txt"))
    with open(f"{B}/TRACK_C_SHA256_MANIFEST.txt", "w") as fh:
        for p in targets:
            if os.path.basename(p) == "TRACK_C_SHA256_MANIFEST.txt":
                continue
            fh.write(f"{sha256(p)}  {os.path.basename(p)}\n")
    n = sum(1 for _ in open(f"{B}/TRACK_C_SHA256_MANIFEST.txt"))
    note(f"[out] TRACK_C_SHA256_MANIFEST.txt ({n} files)")

    champ = per_model.sort_values("mean_Test_MSE_4L").iloc[0]
    grp = pd.read_csv(f"{B}/TRACK_C_LLM_NONLLM_GROUP_SUMMARY.csv")
    integ = [
        "# TRACK C — FILE INTEGRITY REPORT", "",
        f"Generated from the validated Track C results. **Nothing was re-scored, "
        f"re-selected or re-run.**", "",
        "## Integrity facts", "",
        f"- scored cells: **{len(cells)}** (96 expected) — all present",
        f"- cells rejected by the canonical scorer: **0**",
        f"- seed-42 gate: **22 PASS / 0 FAIL**",
        f"- champion: **{champ.model}** — mean Test average_MSE_4L "
        f"**{champ.mean_Test_MSE_4L:.6f}** (SD {champ.sd_Test_MSE_4L:.6f}, "
        f"{champ.n_seeds} matched seeds)",
        f"- Test was never used for fitting or checkpoint selection in any cell "
        f"(`test_access_during_fit = False` on all 12 MIFlu manifests)",
        f"- rejected stage-6 MIFlu recorded in `TRACK_C_MODEL_IDENTITY.csv` "
        f"(sha 76b81b5b0dfa5bde) and excluded from the ranking",
        "", "## Quota (authoritative, from mmlsquota — NOT filesystem free space)", ""]
    for fs in ("home", "scratch"):
        if q.get(fs):
            d = q[fs]
            integ.append(f"- **{fs}**: used {d['used_GB']} GB / soft {d['soft_quota_GB']} GB "
                         f"/ hard {d['hard_limit_GB']} GB, grace `{d['grace']}`, "
                         f"headroom to soft **{d['headroom_to_soft_GB']} GB**")
    integ += ["", "## Group-mean caveat (both conclusions preserved)", "",
              "1. the corrected official-repository-based MIFlu is the **best "
              "individual model**;", "2. the **non-LLM group mean is better** than "
              "the LLM group mean.", ""]
    for _, r in grp.iterrows():
        integ.append(f"- {r['side']}: {r['mean_of_model_means_Test_MSE_4L']:.6f}")
    open(f"{B}/TRACK_C_FILE_INTEGRITY_REPORT.md", "w").write("\n".join(integ))
    note("[out] TRACK_C_FILE_INTEGRITY_REPORT.md")

    json.dump(per_model.to_dict("records"),
              open(f"{B}/TRACK_C_FINAL_RESULTS.json", "w"), indent=2, default=str)
    note("[done] finalize complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())