#!/usr/bin/env python
"""Prove whether the seed actually reaches the LLM-arm training path.

Why this exists
---------------
A queue log showed `ds_r1_distill_qwen1_5b_L24_s42|s43|s44` all reporting the
*identical* gate value (4.443883356674532, 15 significant digits). If the three
seeds produce bit-identical `pred` arrays then the seed never entered the
training path and every "mean +- sd over seeds" quoted for an LLM arm is
meaningless. This script measures that directly, on the artefacts that were
actually written, instead of reasoning about the code.

What it does
------------
For one or more arm labels it loads `pred_<label>_L<L>_s<seed>.npz` for every
seed present at every horizon present, and reports, for each unordered seed
pair:

  * `np.array_equal(pred_a, pred_b)`  -- bit identity of the predictions
  * `max|pred_a - pred_b|`            -- the magnitude of the difference
  * the same two checks on `target` and `target_start_row` -- these must ALWAYS
    be identical across seeds (same test split, same windows); a difference
    there means the cells are not comparable at all, which is a different and
    worse bug.
  * the stored `seed` field inside each npz (guards against a file whose name
    says s43 while its payload says 42 -- the `find_ckpt` trust-order bug).

Also reports `best_val` / `mse_all` from the sibling `manifest_*.json` when
present, because that is where an "identical gate" would show up.

Exit codes
----------
0  seeds were checked and at least one pair differs  (seed enters the path)
4  every checked pair is bit-identical              (seed does NOT reach the path)
2  nothing to check (no complete triple found)

Usage
-----
  python scripts/verify_llm_seed_effect.py --root <expanded_runs> \
      --label ds_r1_distill_qwen1_5b --label qwen25_1_5b --horizon 24 --horizon 36
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
import sys

import numpy as np

DEFAULT_SEEDS = (42, 43, 44)


def cell_paths(root, label, L, seed):
    d = os.path.join(root, f"{label}_L{L}_s{seed}")
    npz = os.path.join(d, f"pred_{label}_L{L}_s{seed}.npz")
    man = os.path.join(d, f"manifest_{label}_L{L}_s{seed}.json")
    return npz, man


def load_cell(npz):
    with np.load(npz, allow_pickle=True) as z:
        out = {k: z[k] for k in z.files}
    return out


def as_scalar(v):
    a = np.asarray(v).ravel()
    return a[0].item() if a.size else None


def compare_pair(a, b, la, lb):
    """Return a dict of the measurements for one seed pair."""
    row = {"pair": f"{la}/{lb}"}
    for key in ("pred", "target"):
        x, y = np.asarray(a[key]), np.asarray(b[key])
        if x.shape != y.shape:
            row[f"{key}_shape"] = f"{x.shape} vs {y.shape}"
            row[f"{key}_equal"] = False
            row[f"{key}_maxdiff"] = float("nan")
            continue
        row[f"{key}_equal"] = bool(np.array_equal(x, y))
        row[f"{key}_maxdiff"] = float(np.max(np.abs(x.astype(np.float64) - y.astype(np.float64)))) if x.size else 0.0
    if "target_start_row" in a and "target_start_row" in b:
        ts_a, ts_b = np.asarray(a["target_start_row"]), np.asarray(b["target_start_row"])
        row["start_equal"] = bool(np.array_equal(ts_a, ts_b))
    return row


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="expanded_runs directory")
    ap.add_argument("--label", action="append", required=True,
                    help="arm label, repeatable (e.g. ds_r1_distill_qwen1_5b)")
    ap.add_argument("--horizon", action="append", type=int, default=None,
                    help="horizon L, repeatable; default = every L found with >=2 seeds")
    ap.add_argument("--seeds", default=",".join(str(s) for s in DEFAULT_SEEDS))
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args(argv)
    seeds = [int(s) for s in a.seeds.split(",") if s.strip()]

    report = {"root": a.root, "labels": {}, "any_diff": False, "n_pairs": 0,
              "n_identical_pairs": 0}
    for label in a.label:
        # Which horizons actually exist for this label?
        found = set()
        for p in glob.glob(os.path.join(a.root, f"{label}_L*_s*")):
            base = os.path.basename(p)
            try:
                L = int(base.rsplit("_L", 1)[1].split("_")[0])
            except Exception:
                continue
            found.add(L)
        horizons = sorted(found) if a.horizon is None else sorted(set(a.horizon))
        report["labels"][label] = {}
        for L in horizons:
            cells = {}
            for s in seeds:
                npz, man = cell_paths(a.root, label, L, s)
                if os.path.exists(npz):
                    cells[s] = (load_cell(npz), man)
            entry = {"n_seeds_present": sorted(cells), "pairs": [], "per_seed": {},
                     "manifests": {}}
            for s, (z, man) in cells.items():
                entry["per_seed"][str(s)] = {
                    "file_seed": as_scalar(z["seed"]) if "seed" in z else None,
                    "pred_shape": list(np.asarray(z["pred"]).shape),
                    "pred_sum": float(np.asarray(z["pred"], dtype=np.float64).sum()),
                    "pred_std": float(np.asarray(z["pred"], dtype=np.float64).std()),
                }
                if os.path.exists(man):
                    try:
                        with open(man, encoding="utf-8") as f:
                            m = json.load(f)
                        entry["manifests"][str(s)] = {
                            k: m.get(k) for k in ("seed", "L", "best_val", "best_epoch",
                                                  "mse_all", "mae_all", "wall_seconds",
                                                  "probe_only", "model_id", "revision")
                            if k in m
                        }
                    except Exception as exc:  # pragma: no cover - evidence only
                        entry["manifests"][str(s)] = {"_error": repr(exc)}
            for sa, sb in itertools.combinations(sorted(cells), 2):
                row = compare_pair(cells[sa][0], cells[sb][0], f"s{sa}", f"s{sb}")
                entry["pairs"].append(row)
                report["n_pairs"] += 1
                if row["pred_equal"]:
                    report["n_identical_pairs"] += 1
                else:
                    report["any_diff"] = True
            report["labels"][label][str(L)] = entry

    # ── human-readable ────────────────────────────────────────────────────
    print(f"ROOT {a.root}")
    for label, per_L in report["labels"].items():
        for L, e in sorted(per_L.items(), key=lambda kv: int(kv[0])):
            print(f"\n== {label}  L={L}  seeds present={e['n_seeds_present']}")
            for s, d in sorted(e["per_seed"].items(), key=lambda kv: int(kv[0])):
                print(f"   s{s}: file_seed={d['file_seed']} pred{d['pred_shape']} "
                      f"sum={d['pred_sum']:.10g} std={d['pred_std']:.10g}")
            for s, m in sorted(e["manifests"].items(), key=lambda kv: int(kv[0])):
                print(f"   manifest s{s}: {m}")
            if not e["pairs"]:
                print("   (fewer than 2 complete cells -- nothing to compare)")
            for r in e["pairs"]:
                print(f"   {r['pair']}: pred_equal={r['pred_equal']} "
                      f"max|dpred|={r['pred_maxdiff']:.6g} | "
                      f"target_equal={r['target_equal']} start_equal={r.get('start_equal')}")

    print(f"\nSUMMARY pairs={report['n_pairs']} identical={report['n_identical_pairs']} "
          f"any_diff={report['any_diff']}")
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True)
        print(f"wrote {a.json_out}")
    if report["n_pairs"] == 0:
        return 2
    return 0 if report["any_diff"] else 4


if __name__ == "__main__":
    sys.exit(main())
