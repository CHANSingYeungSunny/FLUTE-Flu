#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""make_queue.py (queue v2) -- generate/maintain `master_queue.tsv`.

WHY A GENERATOR AND NOT A HAND-WRITTEN FILE
-------------------------------------------
The queue is *state*: the controller rewrites the state/attempts/last_job/note
columns in place during the night. `--force` writes the canonical task list from
scratch; **without** `--force` the script merges -- it keeps the state of every
task_id that already exists and only appends genuinely new ids. So the task list
can be corrected without destroying the record of what already ran (the same
append-only principle as `docs/LEDGER.md`, AGENTS.md R3).

`--migrate` upgrades a v1 10-column queue (no `env`) to the v2 11-column layout
IN PLACE, backfilling `env` on every row from `arms_registry.json` and keeping
state/attempts/last_job/note untouched.

LAYOUT
------
  P0  22 missing MIFlu reproduction cells (7-var export + per-seed oracle gate)
  P1  Qwen/Qwen2.5-1.5B, 12 cells -- the first real LLM benchmark row
  P2  13 probe rows (CPU: revision pin + download + 2-layer smoke) and
      13 arms x 12 cells = 156 LLM cells, BLOCKED_MISSING_WEIGHTS at birth
  P3  leftovers from docs/WORK_BREAKDOWN.md 13.D, as placeholders only
  P4  F1-F5 finalisation (the whole point of the night: cells -> tables/figures)
      f1_import_miflu   import_miflu_predictions.py over the DONE MIFlu cells
      f2_miflu_oracle   verify_miflu_oracle.py -- must print RESULT: PASS
      f3_analysis_chain analysis_expanded -> analysis_postprocess ->
                        seasonal_naive_baseline -> plot_bench -> plot_pareto
      f4_verify         verify_bench_unchanged.py + pre-freeze backup/re-freeze
      f5_llm_import     the same import/analysis/figure path per LLM arm group
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
V1_COLUMNS = ["task_id", "kind", "model", "L", "seed", "priority",
              "state", "attempts", "last_job", "note"]

# ---- P0: the 22 MIFlu cells still missing (oracle = export_miflu_all7.ORACLE) --
MIFLU_MISSING = {
    36: [2027, 2028, 2029, 2030],
    48: [2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030],
    60: [2021, 2022, 2023, 2024, 2026, 2027, 2028, 2029, 2030],
}

# ---- P3: placeholders for docs/WORK_BREAKDOWN.md 13.D (NOT implemented) -----
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

# ---- P4: F1-F5. Real queue work, executed by the same runner as a cell ------
FINALISE = [
    ("final_import_miflu", "f1_import_miflu",
     "F1: scripts/import_miflu_predictions.py over every MIFlu cell on disk; gate=n_cells. Idempotent."),
    ("final_miflu_oracle", "f2_miflu_oracle",
     "F2: scripts/verify_miflu_oracle.py - MUST print RESULT: PASS with per-seed |d| <= 1e-5; stdout kept in queue/logs/."),
    ("final_analysis_chain", "f3_analysis_chain",
     "F3: analysis_expanded -> analysis_postprocess -> seasonal_naive_baseline -> plot_bench -> plot_pareto: MSE/MAE, PTE/PIE, K&S, CRPS/WIS, every figure."),
    ("final_verify_bench", "f4_verify",
     "F4: verify_bench_unchanged.py; pre-freeze BENCH_*.post_evalwindow16.csv copied aside; re-freeze only on legitimate growth."),
    ("final_llm_import", "f5_llm_import",
     "F5: per-LLM-arm-group import + analysis refresh; tolerates missing arms and reports n_arms."),
]

#: env per arm is the registry's `venv`; every non-LLM row runs in `hpc`.
DEFAULT_ENV = "hpc"


def oracle_check() -> int:
    sys.path.insert(0, CODE)
    import export_miflu_all7 as EX
    bad = 0
    total = 0
    for L, seeds in MIFLU_MISSING.items():
        for S in seeds:
            total += 1
            if EX.oracle_mse(L, S) is None:
                print("[oracle] MISSING L=%s seed=%s" % (L, S))
                bad += 1
        print("[oracle] L=%s: %d missing cells, oracles " % (L, len(seeds))
              + " ".join("s%s=%.6f" % (S, EX.oracle_mse(L, S)) for S in seeds))
    print("[oracle] missing cells = %d (expected 22), unresolved = %d" % (total, bad))
    return 1 if bad else 0


def registry():
    return json.load(open(REGISTRY, encoding="utf-8"))


def env_by_hf_id() -> dict:
    return {a["hf_id"]: a.get("venv", DEFAULT_ENV) for a in registry()["arms"]}


def rows() -> list:
    sys.path.insert(0, CODE)
    import export_miflu_all7 as EX

    reg = registry()
    horizons = reg["cells"]["horizons"]
    seeds = reg["cells"]["seeds"]
    out = []

    def add(tid, kind, model, L, seed, pri, st, note, env=DEFAULT_ENV):
        out.append([tid, kind, model, str(L), str(seed), pri, env, st, "0", "-", note])

    for L in (36, 48, 60):
        for S in MIFLU_MISSING[L]:
            add("miflu_L%s_s%s" % (L, S), "miflu_cell", "MIFlu", L, S, "P0", "TODO",
                "retrain+7var export+oracle gate; expected test_mse_all=%.6f"
                % EX.oracle_mse(L, S))

    for arm in reg["arms"]:
        label, mid, pri = arm["label"], arm["hf_id"], arm["priority"]
        state = "TODO" if arm["weights"] == "downloaded" and arm["revision"] \
            else "BLOCKED_MISSING_WEIGHTS"
        if pri == "P1":
            state = "TODO"
        if pri == "P2":
            add("probe_%s" % label, "llm_probe", mid, "-", "-", "P2", "TODO",
                "CPU only: pin revision + download if missing + 2-layer "
                "hidden-state smoke (%s)" % arm["note"], env="hpc")
        for L in horizons:
            for S in seeds:
                add("%s_L%s_s%s" % (label, L, S), "llm_cell", mid, L, S, pri, state,
                    "%s; params_b=%s bs=%s%s"
                    % (arm["note"], arm["params_b"], arm["encoder_batch_size"],
                       "" if arm["revision"] else "; revision unpinned until the probe runs"),
                    env=arm.get("venv", DEFAULT_ENV))

    for tid, note in P3_PLACEHOLDERS:
        add(tid, "unimplemented", "-", "-", "-", "P3", "TODO", note, env=DEFAULT_ENV)

    for tid, kind, note in FINALISE:
        add(tid, kind, "-", "-", "-", "P4", "TODO", note, env=DEFAULT_ENV)

    return out


def read_existing() -> dict:
    if not os.path.exists(QUEUE):
        return {}
    with open(QUEUE, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        if header != COLUMNS:
            raise SystemExit("existing header %s != v2 %s; run --migrate (10-col) "
                             "or --force (rebuild)" % (header, COLUMNS))
        keep = {}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) == len(COLUMNS):
                keep[f[0]] = f
    return keep


def migrate() -> int:
    """v1 (10 columns, no env) -> v2 (11 columns), state preserved verbatim."""
    with open(QUEUE, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    header = lines[0].split("\t")
    if header == COLUMNS:
        print("[migrate] already v2 (11 columns) - nothing to do")
        return 0
    if header != V1_COLUMNS:
        raise SystemExit("cannot migrate unknown header %s" % header)
    env_of = env_by_hf_id()
    out = []
    fixed = 0
    for line in lines[1:]:
        f = line.split("\t")
        if len(f) != len(V1_COLUMNS):
            continue
        tid, kind, model = f[0], f[1], f[2]
        env = env_of.get(model, DEFAULT_ENV) if kind == "llm_cell" else DEFAULT_ENV
        if kind in ("unimplemented",) or model == "-":
            env = "-" if kind == "unimplemented" else DEFAULT_ENV
        out.append([f[0], f[1], f[2], f[3], f[4], f[5], env,
                    f[6], f[7], f[8], f[9]])
        fixed += 1
    tmp = QUEUE + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(COLUMNS) + "\n")
        for r in out:
            fh.write("\t".join(r) + "\n")
    os.replace(tmp, QUEUE)
    print("[migrate] wrote %s: %d rows, env backfilled on every row" % (QUEUE, fixed))
    return 0


def backfill_env() -> int:
    """Ensure every row has a legal env (idempotent; used after a hand edit)."""
    with open(QUEUE, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    header = lines[0].split("\t")
    if header != COLUMNS:
        raise SystemExit("header is not v2; run --migrate first")
    env_of = env_by_hf_id()
    n = 0
    out = []
    for line in lines[1:]:
        f = line.split("\t")
        if len(f) != len(COLUMNS):
            continue
        if f[6] not in ("hpc", "llm", "-", ""):
            f[6] = DEFAULT_ENV
            n += 1
        elif f[6] == "":
            f[6] = env_of.get(f[2], DEFAULT_ENV) if f[1] == "llm_cell" else DEFAULT_ENV
            n += 1
        elif f[1] == "llm_cell" and f[6] not in ("hpc", "llm"):
            f[6] = env_of.get(f[2], DEFAULT_ENV)
            n += 1
        out.append(f)
    tmp = QUEUE + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(COLUMNS) + "\n")
        for r in out:
            fh.write("\t".join(r) + "\n")
    os.replace(tmp, QUEUE)
    print("[backfill-env] %d row(s) updated; every row now names its interpreter" % n)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="discard all existing state and rewrite every row at its birth state")
    ap.add_argument("--migrate", action="store_true",
                    help="upgrade a v1 10-column queue to the v2 11-column layout in place")
    ap.add_argument("--backfill-env", action="store_true",
                    help="repair the env column on an already-v2 queue")
    ap.add_argument("--check-oracle", action="store_true")
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args()

    if a.check_oracle:
        return oracle_check()
    if a.migrate:
        return migrate()
    if a.backfill_env:
        return backfill_env()

    keep = {} if a.force else read_existing()
    merged, kept, added = [], 0, 0
    for r in rows():
        old = keep.get(r[0])
        if old is None:
            merged.append(r)
            added += 1
        else:
            # keep the live state, but let this file own the static identity
            # columns (kind/model/L/seed/priority) so a corrected kind propagates
            merged.append([r[0], r[1], r[2], r[3], r[4], r[5],
                           old[6] if old[6] in ("hpc", "llm") else r[6],
                           old[7], old[8], old[9], old[10]])
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
    c = Counter((r[5], r[7]) for r in merged)
    print("[queue] wrote %s: %d rows (kept %d rows' state, %d new)" % (QUEUE, len(merged), kept, added))
    for (pri, st), n in sorted(c.items()):
        print("[queue]   %s %s: %d" % (pri, st, n))
    envc = Counter(r[6] for r in merged)
    print("[queue] env: " + " ".join("%s=%d" % kv for kv in sorted(envc.items())))
    if a.print:
        for r in merged:
            print("\t".join(str(x) for x in r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
