#!/usr/bin/env python3
"""
f1_score_all.py — the F1 pilot's single scoring entry point.

Validates every artefact against the F1 contract, then computes the metrics with
the independent scorer and emits the pilot ranking plus the success-gate report.

It is deliberately strict: a single malformed or off-contract artefact makes the
run report FAILED gates rather than quietly scoring whatever it found.

NOTHING here trains or simulates a model. Every number comes from a persisted
(pred, target) array written by a real run.

Usage:
  python f1_score_all.py --pred-root <dir> --out-dir <dir> --expect-seed 42
"""
from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import math
import os
import socket
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scorer_f1 as S                      # noqa: E402

HORIZONS = [24, 36, 48, 60]
F1_MODELS = ["miflu", "notext", "nlinear", "dlinear",
             "last_value_naive", "seasonal_naive"]
# Declared F1 variable keys - see F1_TARGET_CONTRACT.md.
# These are the project's own keys, taken verbatim from scripts/configs.py
# VAR_COLS, which is what every arm writes into its artefact. Using sanitized
# aliases here would have broken key-identity checking against the trained arms.
F1_VAR_COLS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
               "ILITOTAL", "NUM. OF PROVIDERS", "OT"]


def refuse_on_login_node():
    h = socket.gethostname().lower()
    if h.startswith("hpclogin") or "login" in h:
        print(f"[f1score] REFUSING to run on a login node ({h})")
        sys.exit(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--expect-seed", type=int, default=42)
    ap.add_argument("--allow-partial", action="store_true",
                    help="score what exists instead of requiring all 24 cells")
    args = ap.parse_args()
    refuse_on_login_node()
    os.makedirs(args.out_dir, exist_ok=True)

    # ---- collect ------------------------------------------------------------
    cells, rejects = [], []
    for p in sorted(glob.glob(os.path.join(args.pred_root, "**", "*.npz"),
                              recursive=True)):
        rec, errs = S.load_cell_validated(p)
        if rec is None:
            rejects.append({"path": os.path.relpath(p, args.pred_root),
                            "reason": "; ".join(errs)})
        else:
            cells.append(rec)

    # ---- duplicate (model, L, seed) keys -----------------------------------
    # Added after Phase 3 of the first F1 run exposed 8 duplicate keys that the
    # original gate set did NOT detect: score_test_stage5.py dumps its own naive
    # baselines, which collided with the leakage-safe ones. Averaging two cells
    # that share a key silently mixes two different references, so this is a
    # hard failure, not a warning.
    _keycount = {}
    for c in cells:
        _k = (c["model"], c["L"], c["seed"])
        _keycount.setdefault(_k, []).append(c["path"])
    dups = {k: v for k, v in _keycount.items() if len(v) > 1}
    if dups:
        print(f"[f1score] DUPLICATE (model,L,seed) keys: {len(dups)}")
        for k, v in sorted(dups.items())[:10]:
            print(f"    ! {k} -> {v}")
        # keep the FIRST occurrence per key and drop the rest, but record it
        seen, kept = set(), []
        for c in cells:
            k = (c["model"], c["L"], c["seed"])
            if k in seen:
                rejects.append({"path": c["path"],
                                "reason": f"duplicate key {k}; a cell for this key "
                                          f"was already accepted"})
                continue
            seen.add(k)
            kept.append(c)
        cells = kept
        print(f"[f1score] after de-duplication: {len(cells)} cells kept, "
              f"{len(rejects)} rejected as duplicates")

    print(f"[f1score] artefacts found : {len(cells) + len(rejects)}")
    print(f"[f1score] accepted         : {len(cells)}")
    print(f"[f1score] REJECTED         : {len(rejects)}")
    for r in rejects:
        print(f"    ! {r['path']}: {r['reason']}")

    # ---- coverage -----------------------------------------------------------
    present = defaultdict(set)
    for c in cells:
        present[c["model"]].add(c["L"])
    missing = []
    for m in F1_MODELS:
        for L in HORIZONS:
            if L not in present.get(m, set()):
                missing.append({"model": m, "horizon": L})
    print(f"[f1score] missing (model,horizon) cells: {len(missing)}")
    for x in missing[:12]:
        print(f"    - {x['model']} L={x['horizon']}")

    # ---- key-consistency check (contract S7/S8/S9) ---------------------------
    key_viol = S.cross_check_keys(cells, F1_VAR_COLS)
    print(f"[f1score] forecast-key violations: {len(key_viol)}")
    for v in key_viol[:10]:
        print(f"    ! {v}")

    # ---- seed consistency ---------------------------------------------------
    seeds = defaultdict(set)
    for c in cells:
        seeds[c["model"]].add(c["seed"])
    seed_viol = {m: sorted(s) for m, s in seeds.items()
                 if s != {args.expect_seed}}
    print(f"[f1score] models with off-contract seeds: {len(seed_viol)}"
          + (f" {seed_viol}" if seed_viol else ""))

    # ---- aggregate ----------------------------------------------------------
    agg = S.aggregate(cells)
    rows = []
    for m, a in agg.items():
        rows.append({"model": m, "average_MSE_4L": a["average_MSE_4L"],
                     "seeds_balanced": a["seeds_balanced"], "n_cells": a["n_cells"],
                     **{f"MSE_L{L}": a["L_mse"][L] for L in HORIZONS}})
    rows.sort(key=lambda r: r["average_MSE_4L"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    # ---- corrected pairwise statistics --------------------------------------
    def paired(a, b):
        ka = {(c["L"], c["seed"]): c["mse_all"] for c in cells if c["model"] == a}
        kb = {(c["L"], c["seed"]): c["mse_all"] for c in cells if c["model"] == b}
        common = sorted(set(ka) & set(kb))
        if len(common) < 2:
            return None
        d = [ka[k] - kb[k] for k in common]
        n = len(d)
        mean = sum(d) / n
        sd = math.sqrt(sum((x - mean) ** 2 for x in d) / (n - 1))
        se = sd / math.sqrt(n) if n > 1 else float("nan")
        t = mean / se if se and se > 0 else float("nan")
        wa = sum(1 for x in d if x < 0)      # A wins iff diff < 0
        wb = sum(1 for x in d if x > 0)
        ti = sum(1 for x in d if x == 0)
        assert wa + wb + ti == n, "win/ties must partition the cells"
        return {"model_A": a, "model_B": b, "n_cells": n, "mean_diff": mean,
                "sd": sd, "t": t, "wins_A": wa, "wins_B": wb, "ties": ti,
                "partition_ok": True}

    pairs = []
    for a, b in [("miflu", "notext"), ("miflu", "nlinear"), ("miflu", "dlinear"),
                 ("notext", "nlinear"), ("notext", "dlinear"),
                 ("nlinear", "dlinear"), ("miflu", "seasonal_naive"),
                 ("miflu", "last_value_naive")]:
        r = paired(a, b)
        if r:
            pairs.append(r)

    # ---- success gates (see F1_SUCCESS_GATES.md) ----------------------------
    gates = {
        "G1_all_six_models_present":
            all(present.get(m) for m in F1_MODELS),
        "G2_all_four_horizons_present":
            all(present.get(m) == set(HORIZONS) for m in F1_MODELS),
        "G3_no_rejected_artefacts": len(rejects) == 0,
        "G3b_no_duplicate_keys": len(dups) == 0,
        "G4_forecast_keys_consistent": len(key_viol) == 0,
        "G5_single_pilot_seed_only": len(seed_viol) == 0,
        "G6_no_missing_cells": len(missing) == 0,
        "G7_partition_invariant_holds":
            all(p["partition_ok"] for p in pairs) and len(pairs) > 0,
    }
    all_pass = all(gates.values())
    integrity_ok = (gates["G3_no_rejected_artefacts"]
                    and gates["G4_forecast_keys_consistent"]
                    and gates["G5_single_pilot_seed_only"])
    completeness_ok = (gates["G1_all_six_models_present"]
                       and gates["G2_all_four_horizons_present"]
                       and gates["G6_no_missing_cells"])
    # F1 is COMPLETE only when BOTH hold. A dry run over a subset can be
    # integrity-clean but is never COMPLETE, and must say so plainly.
    status = ("COMPLETE" if (completeness_ok and integrity_ok)
              else "INCOMPLETE_INTEGRITY_OK" if integrity_ok
              else "FAILED_INTEGRITY")
    if args.allow_partial and integrity_ok and not completeness_ok:
        status = "PARTIAL_DRY_RUN_INTEGRITY_OK"

    # ---- write --------------------------------------------------------------
    def wcsv(name, data):
        if not data:
            return
        with io.open(os.path.join(args.out_dir, name), "w", newline="",
                     encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(data[0].keys()),
                                extrasaction="ignore")
            wr.writeheader()
            wr.writerows(data)

    wcsv("f1_ranking_average_4L.csv", rows)
    wcsv("f1_paired_stats.csv", pairs)
    wcsv("f1_rejected_artefacts.csv", rejects)
    wcsv("f1_missing_cells.csv", missing)

    with io.open(os.path.join(args.out_dir, "f1_gate_report.json"), "w") as fh:
        json.dump({"gates": gates, "all_gates_pass": all_pass,
                   "integrity_ok": integrity_ok,
                   "completeness_ok": completeness_ok, "status": status,
                   "n_accepted": len(cells), "n_rejected": len(rejects),
                   "n_missing_cells": len(missing),
                   "key_violations": key_viol,
                   "off_contract_seeds": seed_viol,
                   "note": "one-seed pilot; NOT a final A2-F comparison"},
                  fh, indent=2)

    print("\n[f1score] ranking (equal-weight four-horizon average MSE, lower better)")
    for r in rows:
        print(f"    {r['rank']:>2}. {r['model']:<20} {r['average_MSE_4L']:.6f}")
    print("\n[f1score] paired statistics (A wins iff diff < 0)")
    for p in pairs:
        print(f"    {p['model_A']:>18} - {p['model_B']:<20} "
              f"mean={p['mean_diff']:+.4f} t={p['t']:+.2f} "
              f"A wins {p['wins_A']}/{p['n_cells']} (B {p['wins_B']}, ties {p['ties']})")
    print("\n[f1score] SUCCESS GATES")
    for k, v in gates.items():
        print(f"    [{'PASS' if v else 'FAIL'}] {k}")
    print()
    print(f"[f1score] integrity gates (G3,G4,G5) ok : {integrity_ok}")
    print(f"[f1score] completeness gates (G1,G2,G6) ok : {completeness_ok}")
    print(f"[f1score] F1 STATUS = {status}")
    print("[f1score] REMINDER: one seed only - no significance, no robustness, "
          "no 'best model' claim. See F1_SUCCESS_GATES.md.")
    return 0 if status.startswith(("COMPLETE", "PARTIAL_DRY_RUN")) else 1


if __name__ == "__main__":
    raise SystemExit(main())