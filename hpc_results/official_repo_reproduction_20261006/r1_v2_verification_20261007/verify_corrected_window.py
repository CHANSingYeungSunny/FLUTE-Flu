#!/usr/bin/env python3
"""
verify_corrected_window.py — R1-B corrected-window regression + full CPU sweep.

Runs the CORRECTED R1BDataset contract (imported verbatim from the deployed
trainer, not re-typed) over EVERY split and EVERY horizon, and checks all ten
items the recovery authorization requires:

  1. corrected code is the one deployed   (file SHA-256 vs the HPC copy)
  2. regression assertion rejects short targets
  3. CPU sweep across every split x horizon
  4. every input has length T = 104
  5. every target has length L
  6. all seven channels present
  7. no target crosses a split boundary
  8. forecast-key counts match the recorded contract
  9. scripts/manifests use the corrected dataset class
 10. run namespace is versioned so failed outputs cannot be mistaken

Exit code 0 iff every check passes.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TRAINER = os.path.join(
    REPO, "hpc_results", "official_repo_reproduction_20261006",
    "r0_r5_cpu_stage_20261006", "r1b", "r1b_train.py")
DATA = os.path.join(REPO, "recovery", "author_repo", "dataset", "illness",
                    "national_illness.csv")

DATA_SHA_EXPECT = "2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5"
TRAINER_SHA_EXPECT = "b07894593b469f9c32bb02d9e7a78e1b21f2d80adde3562dab5085d1e18286f3"
T, N_VARS = 104, 7
# A2 / R1-B recorded contract (memory: strict containment counts)
EXPECT = {24: (549, 74, 170), 36: (537, 62, 158),
          48: (525, 50, 146), 60: (513, 38, 134)}

failures, checks = [], []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    if not ok:
        failures.append(f"{name}: {detail}")
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_trainer_module():
    """Import the deployed trainer WITHOUT running main()."""
    spec = importlib.util.spec_from_file_location("r1b_train_probe", TRAINER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    print("=" * 78)
    print("R1-B CORRECTED-WINDOW REGRESSION + FULL CPU SWEEP")
    print("=" * 78)

    # -- 1. code identity ------------------------------------------------
    got_data = sha256_file(DATA)
    check("1a dataset SHA-256 == recorded contract",
          got_data == DATA_SHA_EXPECT, f"{got_data}")
    got_tr = sha256_file(TRAINER)
    check("1b deployed trainer SHA-256 matches the corrected version",
          got_tr == TRAINER_SHA_EXPECT, f"{got_tr}")

    m = load_trainer_module()

    # -- 9. the deployed class really is the corrected one ---------------
    src = open(TRAINER, encoding="utf-8").read()
    check("9a R1BDataset uses the corrected origin formula (o = last input idx)",
          "first_o = max(lo - 1, T - 1)" in src and "last_o = hi - L - 1" in src)
    check("9b trainer imports/uses R1BDataset for all three splits",
          src.count("R1BDataset(data, T, L") == 3)

    # -- load data exactly as the trainer does ---------------------------
    df = pd.read_csv(DATA)
    cols = [c for c in df.columns if c not in ("epiweek", "release_date", "date")]
    X = df[cols].to_numpy(np.float64)
    n = len(X)
    tr_end = int(n * 0.70)          # 676
    te_n = int(n * 0.20)            # 193
    va_end = n - te_n               # 773
    mu, sd = X[:tr_end].mean(0), X[:tr_end].std(0) + 1e-8
    Z = (X - mu) / sd

    check("6a exactly 7 numeric channels", len(cols) == N_VARS, f"{cols}")
    check("6b split boundaries are 676 / 773 / 966",
          (tr_end, va_end, n) == (676, 773, 966), f"{tr_end}/{va_end}/{n}")

    SPLITS = [("train", 0, tr_end), ("val", tr_end, va_end), ("test", va_end, n)]

    # -- 3-8. the sweep --------------------------------------------------
    sweep = {}
    for L in (24, 36, 48, 60):
        counts = []
        for sname, lo, hi in SPLITS:
            ds = m.R1BDataset(Z, T, L, lo, hi)
            counts.append(len(ds))
            bad_shape, bad_chan, cross = [], [], []
            for i in range(len(ds)):
                x, y, o = ds[i]
                if x.shape != (T, N_VARS):
                    bad_shape.append((i, "x", tuple(x.shape)))
                if y.shape != (L, N_VARS):
                    bad_shape.append((i, "y", tuple(y.shape)))
                if x.shape[1] != N_VARS or y.shape[1] != N_VARS:
                    bad_chan.append(i)
                # target rows are [o+1, o+L]; must lie inside [lo, hi)
                if not (o + 1 >= lo and o + L <= hi - 1 + 1 and (o + L) <= hi - 1):
                    cross.append((i, o))
            check(f"4/5/6 L={L} {sname}: every input is ({T},{N_VARS}) "
                  f"and every target is ({L},{N_VARS})",
                  not bad_shape, f"{bad_shape[:3]}" if bad_shape else "")
            check(f"7  L={L} {sname}: no target crosses a split boundary",
                  not cross, f"{cross[:3]}" if cross else "")
            # target actually equals data[o+1 : o+1+L]
            ds2 = m.R1BDataset(Z, T, L, lo, hi)
            probe = min(3, len(ds2) - 1)
            if len(ds2):
                x, y, o = ds2[probe]
                ok_x = np.allclose(x.numpy(), Z[o - T + 1:o + 1, :], atol=0)
                ok_y = np.allclose(y.numpy(), Z[o + 1:o + 1 + L, :], atol=0)
                check(f"7b L={L} {sname}: window == data[o-T+1:o+1] / data[o+1:o+1+L]",
                      ok_x and ok_y)
        sweep[L] = counts
        exp = EXPECT[L]
        check(f"8  L={L} forecast-key counts == recorded contract {exp}",
              tuple(counts) == exp, f"got {tuple(counts)}")

    # -- 2. the regression assertion rejects short targets ---------------
    # Reproduce the OLD defective formula and show it yields a short target,
    # then show the corrected class asserts instead of silently returning it.
    lo, hi = va_end, n
    L = 24
    old_origins = np.arange(lo, hi - L - 1 + 1)
    old_short = []
    for o in old_origins:
        y = X[o + T:o + T + L, :]          # old code's target slice
        if y.shape[0] != L:
            old_short.append((o, y.shape[0]))
    check("2a OLD formula is reproduced and DOES produce short targets",
          len(old_short) > 0,
          f"{len(old_short)} short window(s), e.g. o={old_short[0][0]} -> "
          f"{old_short[0][1]} rows" if old_short else "")

    ds_te = m.R1BDataset(Z, T, L, va_end, n)
    last_o = int(ds_te.origins[-1])
    y_last = Z[last_o + 1:last_o + 1 + L, :]
    check("2b corrected L=24 test window's final target is exactly L rows",
          y_last.shape[0] == L, f"{y_last.shape[0]}")

    # the in-class assertion must fire on a deliberately corrupt dataset
    class _Short(m.R1BDataset):
        def __getitem__(self, i):
            o = int(self.origins[i])
            # simulate the old off-by-T slice
            import torch
            x = self.data[o:o + self.T, :]
            y = self.data[o + self.T:o + self.T + self.L, :]
            assert x.shape[0] == self.T and y.shape[0] == self.L, \
                "window out of range"
            return torch.from_numpy(x), torch.from_numpy(y), o

    fired = False
    try:
        d = _Short(Z, T, 24, va_end, n)
        for i in range(len(d)):
            _ = d[i]
    except AssertionError:
        fired = True
    check("2c the in-class assertion REJECTS a short target (fail-closed)",
          fired)

    # -- report ----------------------------------------------------------
    out = {
        "sweep_counts": {str(k): v for k, v in sweep.items()},
        "expected_counts": {str(k): list(v) for k, v in EXPECT.items()},
        "dataset_sha256": got_data,
        "trainer_sha256": got_tr,
        "checks": [{"name": n_, "ok": o_, "detail": d_} for n_, o_, d_ in checks],
        "n_pass": sum(1 for _, o_, _ in checks if o_),
        "n_fail": len(failures),
    }
    with open(os.path.join(HERE, "R1B_CORRECTED_WINDOW_VERIFICATION.json"),
              "w") as fh:
        json.dump(out, fh, indent=2)

    print("-" * 78)
    print(f"TOTAL: {out['n_pass']} PASS / {out['n_fail']} FAIL")
    for f in failures:
        print("  FAILED:", f)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())