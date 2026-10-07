#!/usr/bin/env python3
"""
build_canonical_keys_966.py — Track C foundation.

Builds the ONE canonical strict-containment key set for the author-966
eight-model championship. Every model must match these keys exactly; the scorer
rejects anything that does not.

Contract
--------
  dataset      recovery/author_repo/dataset/illness/national_illness.csv, 966 rows
  sha256       2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5
  split        train [0,676) · validation [676,773) · test [773,966)
  T            104
  strict       target_start >= split_start  AND  target_end <= split_end - 1
               o = last input index;  input = data[o-103 : o];  target = data[o+1 : o+L]
               origins = [max(split_start-1, T-1), split_end-L-1]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os

import numpy as np
import pandas as pd

DATA_SHA_EXPECT = "2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5"
T = 104
N_VARS = 7
SPLITS = {"train": (0, 676), "validation": (676, 773), "test": (773, 966)}
EXPECTED = {24: (549, 74, 170), 36: (537, 62, 158),
            48: (525, 50, 146), 60: (513, 38, 134)}
# verified in recovery/feature_mapping.csv
FEATURE_NAMES = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
                 "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
AUTHOR_COLS = ["1", "2", "3", "4", "5", "6", "OT"]

KEY_COLS = ["dataset_hash", "seed", "horizon", "split", "forecast_origin",
            "target_start_row", "target_end_row", "forecast_lead",
            "feature_index", "corrected_feature_name"]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def origins_for(L, lo, hi):
    first = max(lo - 1, T - 1)
    last = hi - L - 1
    return np.arange(first, last + 1) if last >= first else np.arange(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", default="42,43,44")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    got = sha256_file(a.data)
    if got != DATA_SHA_EXPECT:
        raise SystemExit(f"ABORT dataset sha {got} != {DATA_SHA_EXPECT}")
    df = pd.read_csv(a.data)
    if len(df) != 966:
        raise SystemExit(f"ABORT expected 966 rows, got {len(df)}")
    missing = [c for c in AUTHOR_COLS if c not in df.columns]
    if missing:
        raise SystemExit(f"ABORT missing author columns {missing}")
    seeds = [int(s) for s in a.seeds.split(",")]

    manifest = {"dataset_hash": got, "dataset_rows": len(df), "T": T,
                "splits": {k: list(v) for k, v in SPLITS.items()},
                "feature_names": FEATURE_NAMES, "seeds": seeds,
                "horizons": {}}

    total_rows = 0
    for L in (24, 36, 48, 60):
        frames, counts = [], []
        for sname, (lo, hi) in SPLITS.items():
            orig = origins_for(L, lo, hi)
            counts.append(len(orig))
            # the load-bearing assertion: NO target may cross a boundary
            ts_start = orig + 1
            ts_end = orig + L
            assert np.all(ts_start >= lo), f"{sname} L={L}: target starts before split"
            assert np.all(ts_end <= hi - 1), f"{sname} L={L}: target crosses split end"
            assert np.all(ts_end == ts_start + L - 1)
            for o in orig:
                for fi in range(N_VARS):
                    for k in range(L):
                        # the split is the one this window was GENERATED for.
                        # Re-deriving it from `o` is wrong: under strict
                        # containment the boundary window o = lo-1 has its
                        # target staring at lo, so it belongs to THIS split even
                        # though o itself sits one row earlier.
                        frames.append((sname, o, int(o) + 1, int(o) + L, k + 1, fi))
        counts = tuple(counts)
        assert counts == EXPECTED[L], f"L={L} counts {counts} != {EXPECTED[L]}"

        # REGRESSION (2026-10-07): the split label must follow the TARGET, not
        # `o`. Under strict containment the boundary window o = lo-1 belongs to
        # the later split even though o < lo. Deriving the label from `o` moved
        # 1 window per horizon out of test (169 instead of 170 at L=24).
        for sname, o, t_start, t_end, _k, _fi in frames:
            lo_s, hi_s = SPLITS[sname]
            assert t_start >= lo_s and t_end <= hi_s - 1, \
                f"{sname} L={L}: target [{t_start},{t_end}] outside [{lo_s},{hi_s})"
            derived = ("train" if t_start < 676 else
                       "validation" if t_start < 773 else "test")
            assert derived == sname, \
                f"split label mismatch: labelled {sname} but target_start " \
                f"{t_start} implies {derived}"

        # materialise per (seed) — keys repeat across seeds identically
        for seed in seeds:
            rows = [{
                "dataset_hash": got, "seed": seed, "horizon": L,
                "split": s[0],
                "forecast_origin": int(s[1]),
                "target_start_row": int(s[2]),
                "target_end_row": int(s[3]),
                "forecast_lead": int(s[4]),
                "feature_index": int(s[5]),
                "corrected_feature_name": FEATURE_NAMES[s[5]],
            } for s in frames]
            keydf = pd.DataFrame(rows, columns=KEY_COLS)
            p = os.path.join(a.out, f"canonical_keys_L{L}_seed{seed}.csv")
            keydf.to_csv(p, index=False)
            total_rows += len(keydf)

        manifest["horizons"][str(L)] = {
            "counts_strict": list(counts),
            "expected": list(EXPECTED[L]),
            "match": list(counts) == list(EXPECTED[L]),
            "keys_per_seed": len(frames),
            "no_boundary_crossing": True,
        }
        print(f"[keys] L={L} strict counts {counts} == {EXPECTED[L]}  "
              f"keys/seed={len(frames)}")

    manifest["total_key_rows"] = total_rows
    json.dump(manifest, open(os.path.join(a.out, "CANONICAL_KEYS_MANIFEST.json"), "w"),
              indent=2)

    # a single hash that every model's artefacts must reproduce
    h = hashlib.sha256()
    for L in (24, 36, 48, 60):
        for seed in seeds:
            p = os.path.join(a.out, f"canonical_keys_L{L}_seed{seed}.csv")
            h.update(open(p, "rb").read())
    manifest["canonical_key_set_sha256"] = h.hexdigest()
    json.dump(manifest, open(os.path.join(a.out, "CANONICAL_KEYS_MANIFEST.json"), "w"),
              indent=2)
    print(f"[keys] canonical key-set sha256 = {h.hexdigest()}")
    print(f"[keys] total key rows = {total_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())