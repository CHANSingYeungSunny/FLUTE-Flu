#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_s1_earlystop_trainer.py
============================
Generate `s1_earlystop_train.py` from the frozen Track C trainer
`miflu_strict966_train.py` by patching ONLY the stopping rule.

Everything else — data, split, windows, model, optimiser, lr, epochs ceiling,
scoring, artefact format — is byte-identical to the Track C trainer, so the
only variable is the stopping rule. That is the whole point of the experiment.

Patches applied:
  1. new args  --early-stop / --patience
  2. patience counter around the best-validation update
  3. early-stopping fields recorded in the run manifest

It does NOT touch Track C and does NOT add a candidate to the frozen R1-C
matrix. It is a separate question (supervisor question 5, condition 2).
"""
from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "hpc_results", "official_repo_reproduction_20261006",
                   "r1_v2_verification_20261007", "miflu_strict966_train.py")
DST = os.path.join(ROOT, "hpc_results", "official_repo_reproduction_20261006",
                   "r1_v2_verification_20261007", "s1_earlystop_train.py")

OLD_ARGS = '''    ap.add_argument("--out", required=True)
    a = ap.parse_args()'''

NEW_ARGS = '''    ap.add_argument("--out", required=True)
    ap.add_argument("--early-stop", type=int, default=0,
                    help="1 = stop when validation MSE has not improved for "
                         "--patience epochs, then roll back to the best weights")
    ap.add_argument("--patience", type=int, default=5)
    a = ap.parse_args()'''

OLD_LOOP = '''    best = {"val": float("inf"), "state": None, "epoch": -1}
    t0 = time.time()'''

NEW_LOOP = '''    best = {"val": float("inf"), "state": None, "epoch": -1}
    bad_epochs, stopped_at = 0, None
    t0 = time.time()'''

OLD_SEL = '''        if v < best["val"]:
            best = {"val": v, "epoch": ep + 1,
                    "state": {k: t.detach().cpu().clone()
                              for k, t in model.state_dict().items()}}
    if best["state"] is not None:'''

NEW_SEL = '''        if v < best["val"]:
            best = {"val": v, "epoch": ep + 1,
                    "state": {k: t.detach().cpu().clone()
                              for k, t in model.state_dict().items()}}
            bad_epochs = 0
            print(f"[strict966]   SAVED (val improved)")
        else:
            bad_epochs += 1
            print(f"[strict966]   no improvement ({bad_epochs}/{a.patience})")
        if a.early_stop and bad_epochs >= a.patience:
            stopped_at = ep + 1
            print(f"[strict966] EARLY-STOP patience exhausted at epoch {ep + 1}")
            break
    if best["state"] is not None:'''

OLD_MAN = '''        "best_val_mse": best["val"], "best_epoch": best["epoch"],'''

NEW_MAN = '''        "best_val_mse": best["val"], "best_epoch": best["epoch"],
        "early_stopping_enabled": bool(a.early_stop),
        "patience": a.patience, "stopped_at_epoch": stopped_at,
        "epochs_run": (stopped_at if stopped_at else a.epochs),
        "selection": ("validation-loss early stopping, patience "
                      f"{a.patience}, rolled back to best weights"
                      if a.early_stop else
                      "fixed-epoch budget, best validation checkpoint"),'''


def main():
    src = open(SRC, encoding="utf-8").read()
    for old, new, label in ((OLD_ARGS, NEW_ARGS, "args"),
                            (OLD_LOOP, NEW_LOOP, "loop init"),
                            (OLD_SEL, NEW_SEL, "selection"),
                            (OLD_MAN, NEW_MAN, "manifest")):
        if old not in src:
            raise SystemExit(f"[patch] anchor not found: {label}")
        src = src.replace(old, new, 1)
        print(f"[patch] applied: {label}")
    src = src.replace('print(f"[strict966] L={L} seed={a.seed}',
                      'print(f"[strict966] S1 early_stop={a.early_stop} '
                      'patience={a.patience} L={L} seed={a.seed}', 1)
    open(DST, "w", encoding="utf-8").write(src)
    print(f"[write] {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
