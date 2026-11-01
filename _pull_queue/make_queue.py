#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""make_queue.py -- generate/maintain `master_queue.tsv`, the durable work queue.

WHY A GENERATOR AND NOT A HAND-WRITTEN FILE
-------------------------------------------
The queue is *state*: the controller rewrites columns 7-10 in place during the
night. `--force` writes the canonical task list from scratch; **without**
`--force` the script merges -- it keeps the state/attempts/last_job of every
task_id that already exists and only appends genuinely new ids. So the task
list can be corrected without ever destroying the record of what already ran
(the same append-only principle as `docs/LEDGER.md`, AGENTS.md R3).

THE QUEUE IS COMPLETE UP FRONT
------------------------------
Every cell of the 14-arm LLM roster is in the file, including the ones whose
weights do not exist yet, marked `BLOCKED_MISSING_WEIGHTS`. A granted GPU
window must never be wasted on an empty queue, and nobody should have to
re-author the queue at 4 a.m. The CPU probe job flips an arm's 12 cells from
BLOCKED_MISSING_WEIGHTS to TODO once (and only once) its checkpoint is local,
its revision is pinned, and a 2-layer CPU smoke test has proved a hidden-state
read-out. If the model cannot yield hidden states, the 12 cells become SKIPPED
with the measured reason.

LAYOUT
------
  P0  22 missing MIFlu reproduction cells (7-var export + per-seed oracle gate)
  P1  Qwen/Qwen2.5-1.5B, 12 cells -- the first real LLM benchmark row
  P2  13 probe rows (CPU, revision pin + download + 2-layer smoke) and
      13 arms x 12 cells = 156 LLM cells, all BLOCKED_MISSING_WEIGHTS at birth
  P3  leftovers from docs/WORK_BREAKDOWN.md 13.D, as placeholders only
"""
from __future__ import annotations

import argparse
import json
import os
import sys

QUEUE_DIR = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(QUEUE_DIR)
QUEUE = os.path.join(QUEUE_DIR, "master_queue.tsv")
REGISTRY = os.path.join(QUEUE_DIR, "arms_registry.json")

COLUMNS = ["task_id", "kind", "model", "L", "seed", "priority", "env",
           "state", "attempts", "last_job", "note"]

# ---- P0: the 22 MIFlu cells still missing (oracle = export_miflu_all7.ORACLE) --
MIFLU_MISSING = {
    36: [2027, 2028, 2029, 2030],
    48: [2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030],
    60: [2021, 2022, 2023, 2024, 2026, 2027, 2028, 2029, 2030],
}

# ---- P3: placeholders for docs/WORK_BREAKDOWN.md 13.D (NOT implemented) -----
FINALISE = [
    ("final_import_miflu",
     "scripts/import_miflu_predictions.py over every DONE MIFlu cell; records n_cells. Idempotent."),
    ("final_miflu_oracle",
     "scripts/verify_miflu_oracle.py - MUST print PASS with per-seed |d| <= 1e-5; output stored verbatim."),
    ("final_analysis_chain",
     "analysis_expanded -> analysis_postprocess -> seasonal_naive_baseline -> plot_bench -> plot_pareto: MSE/MAE, PTE/PIE, K&S, CRPS/WIS, every figure."),
    ("final_verify_bench",
     "verify_bench_unchanged.py; re-freeze the expected table when rows legitimately grow (keep the pre-freeze copy)."),
    ("final_llm_import",
     "per-LLM-group import + analysis refresh as LLM cells land; tolerates missing arms and reports n_arms."),
]

P3_PLACEHOLDERS = [
    ("p3_table6_hhs10_regional",
     "Table VI (regional HHS-10) run harness does not exist; placeholder from WORK_BREAKDOWN 13.D"),
    ("p3_table8_ablations",
     "Table VIII ablation arms have no runner; placeholder from WORK_BREAKDOWN 13.D"),
    ("p3_table9_training_time",
     "Table IX regional training time depends on the Table VI config; placeholder"),
    ("p3_rolling_origin_5fold",
     "rolling-origin (5 folds) needs a walk-forward split + retraining loop; placeholder"),
]


def oracle_check() -> int:
    sys.path.insert(0, CODE)
    import export_miflu_all7 as EX
    bad = 0
    total = 0
    for L, seeds in MIFLU_MISSING.items():
        for S in seeds:
            total += 1
            if EX.oracle_mse(L, S) is None:
                print(f"[oracle] MISSING L={L} seed={S}")
                bad += 1
        print(f"[oracle] L={L}: {len(seeds)} missing cells, oracles "
              + " ".join(f"s{S}={EX.oracle_mse(L, S):.6f}" for S in seeds))
    print(f"[oracle] missing cells = {total} (expected 22), unresolved = {bad}")
    return 1 if bad else 0


def rows() -> list:
    sys.path.insert(0, CODE)
    import export_miflu_all7 as EX

    reg = json.load(open(REGISTRY, encoding="utf-8"))
    horizons = reg["cells"]["horizons"]
    seeds = reg["cells"]["seeds"]
    out = []

    def add(tid, kind, model, L, seed, pri, st, note, env="hpc"):
        out.append([tid, kind, model, str(L), str(seed), pri, env, st, "0", "-", note])

    for L in (36, 48, 60):
        for S in MIFLU_MISSING[L]:
            add(f"miflu_L{L}_s{S}", "miflu_cell", "MIFlu", L, S, "P0", "TODO",
                f"retrain+7var export+oracle gate; expected test_mse_all={EX.oracle_mse(L, S):.6f}")

    for arm in reg["arms"]:
        label, mid, pri = arm["label"], arm["hf_id"], arm["priority"]
        state = "TODO" if arm["weights"] == "downloaded" and arm["revision"] else "BLOCKED_MISSING_WEIGHTS"
        if pri == "P1":
            state = "TODO"
        if pri == "P2":
            add(f"probe_{label}", "llm_probe", mid, "-", "-", "P2", "TODO", env="hpc",
                note=f"CPU only: pin revision + download if missing + 2-layer "
                     f"hidden-state smoke ({arm['note']})")
        for L in horizons:
            for S in seeds:
                add(f"{label}_L{L}_s{S}", "llm_cell", mid, L, S, pri, state, env=arm["venv"],
                    note=f"{arm['note']}; params_b={arm['params_b']} bs={arm['encoder_batch_size']}"
                    + ("" if arm["revision"] else "; revision unpinned until the probe runs"))

    for tid, note in P3_PLACEHOLDERS:
        add(tid, "unimplemented", "-", "-", "-", "P3", "TODO", note, env="-")

    # ---- P4: finalisation. Ordinary, idempotent tasks: each one no-ops when the
    # on-disk cell signature has not changed, so it is cheap to re-arm after every
    # batch of new cells (the controller does exactly that).
    for tid, note in FINALISE:
        add(tid, "finalise", "-", "-", "-", "P4", "TODO", note, env="hpc")

    return out


def read_existing() -> dict:
    if not os.path.exists(QUEUE):
        return {}
    keep = {}
    with open(QUEUE, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        if header != COLUMNS:
            raise SystemExit(f"existing header {header} != {COLUMNS}; use --force")
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) == len(COLUMNS):
                keep[f[0]] = f
    return keep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="discard all existing state and rewrite every row at its birth state")
    ap.add_argument("--check-oracle", action="store_true")
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args()

    if a.check_oracle:
        return oracle_check()

    keep = {} if a.force else read_existing()
    merged, kept, added = [], 0, 0
    for r in rows():
        old = keep.get(r[0])
        if old is None:
            merged.append(r)
            added += 1
        else:
            merged.append(old[:6] + [old[6], old[7], old[8], r[9]])
            kept += 1

    tmp = QUEUE + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(COLUMNS) + "\n")
        for r in merged:
            assert len(r) == len(COLUMNS), r
            assert all("\t" not in str(c) for c in r), r
            fh.write("\t".join(str(c) for c in r) + "\n")
    os.replace(tmp, QUEUE)

    from collections import Counter
    c = Counter((r[5], r[6]) for r in merged)
    print(f"[queue] wrote {QUEUE}: {len(merged)} rows (kept {kept} rows' state, {added} new)")
    for (pri, st), n in sorted(c.items()):
        print(f"[queue]   {pri} {st}: {n}")
    if a.print:
        for r in merged:
            print("\t".join(str(x) for x in r))
    return 0


if __name__ == "__main__":
    sys.exit(main())

