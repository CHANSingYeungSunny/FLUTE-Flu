"""
build_reuse_map.py — classify the Stage-3 45-row matrix against completed runs.

Reads recovery/stage3/run_matrix.csv and emits:
  * reuse_map.csv        — one row per proposed run with reuse classification
  * reduced_run_matrix.csv — the executable subset (excludes BLOCKED A0)

Classification is uniform per variant (no run in the completed set used the
proposed 676/97/193 split, the 3-seed [42,43,44] set, or val-based selection on
author-966 data):

  A0-01            BLOCKED   released-code replay never run (needs GPU + author
                             gpt2 cache + author-repo env)
  A2-MIFlu (12)    NEW_FIT   job 514859 is a data-leg landmark (TSLib 966,
                             676/96/194, 10 reps, fixed-20-epoch) — the proposed
                             676/97/193 + 3-seed val-selection is unrun and the
                             7-var per-window predictions + checkpoints needed to
                             re-evaluate are not stored locally
  A2-NOTEXT (12)   NEW_FIT   no_multi never run on author 966
  A2-NLIN  (12)    NEW_FIT   NLinear never run on author 966 (innovation harness
                             NLinear is 1025-row 598-spec, different data/protocol)
  A2-LV    (4)     NEW_FIT   deterministic eval, not yet computed on author 966
  A2-SN    (4)     NEW_FIT   deterministic eval, not yet computed on author 966
"""

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "stage3", "run_matrix.csv")

CLASS = {
    "A0": ("BLOCKED",
           "released-code replay never run; needs GPU node + author gpt2 cache "
           "+ author-repo env (D-a0-env)"),
    "A2-MIFlu": ("NEW_FIT",
                 "job 514859 = TSLib 966 split 676/96/194, 10 reps, fixed-20-epoch; "
                 "proposed 676/97/193 + 3-seed val-selection unrun; 7-var per-window "
                 "predictions/checkpoints not stored locally"),
    "A2-NOTEXT": ("NEW_FIT", "no_multi (no-text) never run on author 966"),
    "A2-NLIN": ("NEW_FIT",
                "NLinear never run on author 966 via train_miflu protocol "
                "(innovation harness NLinear is 1025-row 598-spec)"),
    "A2-LV": ("NEW_FIT", "deterministic last-value eval, not yet computed on author 966"),
    "A2-SN": ("NEW_FIT", "deterministic seasonal-naive eval, not yet computed on author 966"),
}


def variant_key(run_id):
    if run_id.startswith("A0-"):
        return "A0"
    if run_id.startswith("A2-MIFlu-"):
        return "A2-MIFlu"
    if run_id.startswith("A2-NOTEXT-"):
        return "A2-NOTEXT"
    if run_id.startswith("A2-NLIN-"):
        return "A2-NLIN"
    if run_id.startswith("A2-LV-"):
        return "A2-LV"
    if run_id.startswith("A2-SN-"):
        return "A2-SN"
    raise ValueError(f"unrecognised run_id {run_id!r}")


def main():
    with open(SRC, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    reuse_rows = []
    for r in rows:
        cls, reason = CLASS[variant_key(r["run_id"])]
        reuse_rows.append({
            "run_id": r["run_id"],
            "track": r["track"],
            "variant": r["variant"],
            "horizon": r["horizon"],
            "seed": r["seed"],
            "data_profile": r["data_profile"],
            "split_convention": r["split_convention"],
            "reuse_class": cls,
            "reason": reason,
        })

    with open(os.path.join(HERE, "reuse_map.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(reuse_rows[0].keys()))
        w.writeheader()
        w.writerows(reuse_rows)

    # Reduced execution matrix: everything except BLOCKED A0.
    reduced = [r for r in rows if variant_key(r["run_id"]) != "A0"]
    with open(os.path.join(HERE, "reduced_run_matrix.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(reduced[0].keys()))
        w.writeheader()
        w.writerows(reduced)

    from collections import Counter
    c = Counter(variant_key(r["run_id"]) for r in rows)
    print("reuse classification counts:")
    for k in sorted(CLASS):
        print(f"  {k:12s} {c.get(k, 0):3d}  -> {CLASS[k][0]}")
    print(f"  TOTAL        {len(rows):3d}")
    print(f"  reduced (executable, excl. A0): {len(reduced)}")


if __name__ == "__main__":
    main()
