#!/usr/bin/env python3
"""
paired_stats_corrected.py — paired cell statistics with a CORRECT win counter,
plus the unit tests that pin the convention down.

THE BUG THIS FIXES
------------------
`hpc_results/stage6/scoring/paired_stats.py` prints a column it labels

    "n_win = cells where A beats B"

but its counter increments on the OPPOSITE condition. Measured on the real
data, for `miflu - nlinear` it reports "A better in 5/12" when MIFlu is in fact
better in 7/12 cells, and for `notext - nlinear` it reports "A better in 1/12"
when no-text is better in 11/12 cells. The mean difference and the t statistic
are correct; only the win count is inverted. That wrong number was copied into
the Stage-6 report §0 ("5/12 胜"), while the same report §4.3 quotes the correct
"11/12" — the report contradicts itself.

CONVENTION (fixed here, tested below)
-------------------------------------
    diff_c          = mse(A, cell) - mse(B, cell)
    lower MSE wins
    A wins cell     <=>  diff_c < 0
    n_win(A)        = #cells with diff_c < 0
    n_win(B)        = #cells with diff_c > 0
    ties            = #cells with diff_c == 0
    n_win(A) + n_win(B) + ties == n_cells        (always)

Usage:
  python scripts/paired_stats_corrected.py --self-test
  python scripts/paired_stats_corrected.py --cells <indep_scorer_cells.csv> \
      --out-dir <dir> --pairs miflu:nlinear,notext:nlinear,...
"""
import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict

HORIZONS = [24, 36, 48, 60]


# ─────────────────────────────────────────────────────────────────────────────
def paired_stats(diffs):
    """diffs: list of (A_mse - B_mse). Lower MSE is better, so A wins on <0."""
    n = len(diffs)
    if n == 0:
        return None
    wins_a = sum(1 for d in diffs if d < 0)
    wins_b = sum(1 for d in diffs if d > 0)
    ties = sum(1 for d in diffs if d == 0)
    assert wins_a + wins_b + ties == n, "win/ties must partition the cells"

    mean = sum(diffs) / n
    if n > 1:
        var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
        sd = math.sqrt(var)
        se = sd / math.sqrt(n)
        t = mean / se if se > 0 else float("nan")
    else:
        sd = se = t = float("nan")
    return {
        "n_cells": n,
        "mean_diff": mean,
        "sd": sd,
        "t": t,
        "wins_A": wins_a,
        "wins_B": wins_b,
        "ties": ties,
        "A_better": wins_a > wins_b,
        "B_better": wins_b > wins_a,
    }


# ─────────────────────────────────────────────────────────────────────────────
def self_test():
    """Three cases demanded by the spec. Two are exhaustive, one is hand-checked."""
    ok = True
    print("=" * 70)
    print("paired_stats unit tests")
    print("=" * 70)

    # --- case 1: A strictly better in every cell ---------------------------
    d1 = [-1.0, -2.0, -0.5, -3.0]
    r1 = paired_stats(d1)
    print(f"\n[case 1] A strictly lower MSE everywhere: diffs={d1}")
    print(f"         -> wins_A={r1['wins_A']} wins_B={r1['wins_B']} "
          f"ties={r1['ties']} mean={r1['mean_diff']:+.4f}")
    c1 = (r1["wins_A"] == 4 and r1["wins_B"] == 0 and r1["ties"] == 0
          and r1["A_better"] and not r1["B_better"])
    print(f"         {'PASS' if c1 else 'FAIL'}: expected A wins all cells")
    ok &= c1

    # --- case 2: A strictly worse in every cell ----------------------------
    d2 = [1.0, 2.0, 0.5, 3.0]
    r2 = paired_stats(d2)
    print(f"\n[case 2] A strictly higher MSE everywhere: diffs={d2}")
    print(f"         -> wins_A={r2['wins_A']} wins_B={r2['wins_B']} "
          f"ties={r2['ties']} mean={r2['mean_diff']:+.4f}")
    c2 = (r2["wins_A"] == 0 and r2["wins_B"] == 4 and r2["ties"] == 0
          and r2["B_better"] and not r2["A_better"])
    print(f"         {'PASS' if c2 else 'FAIL'}: expected A wins zero cells")
    ok &= c2

    # --- case 3: mixed, hand-computed --------------------------------------
    d3 = [-0.4, +0.6, -0.2, +0.1, -3.0, +0.0]
    #      A     B     A     B     A     tie
    r3 = paired_stats(d3)
    exp_wins_a, exp_wins_b, exp_ties = 3, 2, 1
    exp_mean = sum(d3) / 6
    print(f"\n[case 3] mixed: diffs={d3}")
    print(f"         by hand: A wins {exp_wins_a}, B wins {exp_wins_b}, "
          f"ties {exp_ties}, mean {exp_mean:+.6f}")
    print(f"         -> wins_A={r3['wins_A']} wins_B={r3['wins_B']} "
          f"ties={r3['ties']} mean={r3['mean_diff']:+.6f}")
    c3 = (r3["wins_A"] == exp_wins_a and r3["wins_B"] == exp_wins_b
          and r3["ties"] == exp_ties
          and abs(r3["mean_diff"] - exp_mean) < 1e-12
          and r3["wins_A"] + r3["wins_B"] + r3["ties"] == len(d3))
    print(f"         {'PASS' if c3 else 'FAIL'}: hand-computed values match")
    ok &= c3

    # --- case 4: the exact historical bug, reproduced and rejected ---------
    # MIFlu is better in 7 of 12 cells; the old counter would print 5.
    d4 = [-0.2001, -0.1701, -0.3188, -0.2829, -0.1050, -0.3206, -0.0115,
          +0.3837, +0.3598, +0.2858, +0.0952, +0.1882]
    r4 = paired_stats(d4)
    old_counter = sum(1 for d in d4 if d > 0)     # the inverted condition
    print(f"\n[case 4] regression guard on the real miflu-nlinear cell diffs")
    print(f"         correct wins_A={r4['wins_A']}  inverted counter would say "
          f"{old_counter}")
    c4 = (r4["wins_A"] == 7 and old_counter == 5)
    print(f"         {'PASS' if c4 else 'FAIL'}: correct=7, historical bug=5")
    ok &= c4

    print("\n" + "=" * 70)
    print("ALL TESTS PASS" if ok else "SOME TESTS FAILED")
    print("=" * 70)
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────────────
def load_cells(path):
    by = defaultdict(dict)
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            by[r["model"]][(int(r["L"]), int(r["seed"]))] = float(r["mse_all"])
    return by


def run_pairs(cells, pairs, out_dir):
    rows = []
    for spec in pairs:
        a, b = spec.split(":")
        if a not in cells or b not in cells:
            print(f"  ! skip {spec}: missing model")
            continue
        common = sorted(set(cells[a]) & set(cells[b]))
        if not common:
            print(f"  ! skip {spec}: no common cells")
            continue
        diffs = [cells[a][k] - cells[b][k] for k in common]
        st = paired_stats(diffs)
        # per-horizon breakdown, so a symbol flip across L is visible
        per_L = {}
        for L in HORIZONS:
            dl = [cells[a][k] - cells[b][k] for k in common if k[0] == L]
            per_L[L] = paired_stats(dl)
        row = {
            "model_A": a, "model_B": b, **st,
            "mean_mse_A": sum(cells[a][k] for k in common) / len(common),
            "mean_mse_B": sum(cells[b][k] for k in common) / len(common),
        }
        for L in HORIZONS:
            row[f"wins_A_L{L}"] = per_L[L]["wins_A"]
            row[f"n_L{L}"] = per_L[L]["n_cells"]
            row[f"mean_diff_L{L}"] = per_L[L]["mean_diff"]
        rows.append(row)

    csv_path = os.path.join(out_dir, "paired_stats_corrected.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    md = ["# Paired statistics (CORRECTED win direction)", "",
          "Convention: `diff = mse(A) - mse(B)`; lower MSE wins; "
          "**A wins iff diff < 0**. `n_win(A) + n_win(B) + ties == n_cells` "
          "holds for every row.", "",
          "| A | B | mean MSE A | mean MSE B | mean diff | t | A wins | B wins | ties | n |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        md.append(f"| {r['model_A']} | {r['model_B']} | {r['mean_mse_A']:.4f} | "
                  f"{r['mean_mse_B']:.4f} | {r['mean_diff']:+.4f} | {r['t']:+.2f} | "
                  f"**{r['wins_A']}** | {r['wins_B']} | {r['ties']} | {r['n_cells']} |")
    md += ["", "## Per-horizon win counts (A wins / n cells)", "",
           "| A | B | L=24 | L=36 | L=48 | L=60 |", "|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['model_A']} | {r['model_B']} | "
                  + " | ".join(f"{r[f'wins_A_L{L}']}/{r[f'n_L{L}']}" for L in HORIZONS)
                  + " |")
    with open(os.path.join(out_dir, "paired_stats_corrected.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")

    print(f"wrote {csv_path} and paired_stats_corrected.md")
    for r in rows:
        print(f"  {r['model_A']:>14s} - {r['model_B']:<14s} "
              f"mean={r['mean_diff']:+.4f} t={r['t']:+.2f} "
              f"A wins {r['wins_A']}/{r['n_cells']}  "
              f"(B wins {r['wins_B']}, ties {r['ties']})")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cells", default="")
    ap.add_argument("--out-dir", default="")
    ap.add_argument("--pairs", default="")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())
    if not args.cells or not args.out_dir:
        ap.error("--cells and --out-dir are required unless --self-test")

    cells = load_cells(args.cells)
    print(f"[paired] {len(cells)} models, "
          f"{sum(len(v) for v in cells.values())} cells")
    pairs = [p for p in args.pairs.split(",") if p]
    if not pairs:
        models = sorted(cells)
        prim = "miflu" if "miflu" in cells else models[0]
        pairs = [f"{m}:{prim}" for m in models if m != prim]
    os.makedirs(args.out_dir, exist_ok=True)
    run_pairs(cells, pairs, args.out_dir)


if __name__ == "__main__":
    main()