#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit_miflu_cells.py -- the contamination gate in front of the import step.

WHY THIS EXISTS
---------------
A cell that was exported from the WRONG checkpoint (the historical `find_ckpt`
trust-order bug: seed 2024's weights used for the s2021 cell) produces a
perfectly well-formed npz with a plausible MSE. Nothing downstream can tell it
apart from a correct cell, and once it is imported into `paper_tables/` the paper
is wrong with no error anywhere. So every cell is re-derived here, on the same
shared `(W//16)*16` windows the tables use, and compared with its per-seed
oracle to <= 1e-5. Anything that does not match is deleted (npz, manifest,
results, wide CSV, verify marker) so the writer can never import it.

RULES
-----
* PASS        |mse - oracle| <= 1e-5           -> keep
* CONTAMINATED|mse - oracle| >  1e-5           -> delete + queue row back to TODO
* NO_ORACLE   the per-seed oracle is unknown   -> UNVERIFIABLE: delete + TODO
              (never carry an unverified cell into the tables)
* NO_CELL     npz has no pred/target/shape     -> UNVERIFIABLE: delete + TODO

USAGE
    python audit_miflu_cells.py                 # report only
    python audit_miflu_cells.py --apply         # delete the failures, reset rows
    python audit_miflu_cells.py --apply --json queue/miflu_audit.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time

QUEUE_DIR = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(QUEUE_DIR)
RUNS = "/gpfs1/home/sychan552/stage5_a2_durable"
EXPANDED = os.path.join(RUNS, "expanded_runs")
AUTHOR_RUNS = os.path.join(RUNS, "author_runs")
TOL = 1e-5
sys.path.insert(0, QUEUE_DIR)

PAT_ALL7 = re.compile(r"L(\d+)_all7/pred_miflu_L(\d+)_seed(\d+)\.npz$")


def eval_slice(W, batch=16):
    return (W // batch) * batch


def oracle_mse(L, S):
    """The per-seed oracle, from the same module the MIFlu controller uses."""
    sys.path.insert(0, CODE)
    try:
        import export_miflu_all7 as EX
        return EX.oracle_mse(L, S)
    except Exception as exc:                                    # noqa: BLE001
        print("[audit] cannot load oracle: %s: %s" % (type(exc).__name__, exc))
        return None


def rederive(path):
    """(mse, W, n_eval, note) for one npz, or (None, ...) if unreadable."""
    try:
        import numpy as np
        z = np.load(path, allow_pickle=False)
        if "pred" not in z.files or "target" not in z.files:
            return None, 0, 0, "keys=%s" % (z.files,)
        pred, target = z["pred"], z["target"]
        if pred.shape != target.shape or pred.ndim != 3:
            return None, 0, 0, "shape pred=%s target=%s" % (pred.shape, target.shape)
        W = pred.shape[0]
        n = eval_slice(W)
        err = pred[:n].astype("float64") - target[:n].astype("float64")
        return float((err ** 2).mean()), W, n, "shape=%s" % (pred.shape,)
    except Exception as exc:                                    # noqa: BLE001
        return None, 0, 0, "%s: %s" % (type(exc).__name__, exc)


def cells():
    """(path, layout, L, seed) for every MIFlu npz on disk."""
    out = []
    for p in glob.glob(os.path.join(AUTHOR_RUNS, "L*_all7", "pred_miflu_L*_seed*.npz")):
        m = PAT_ALL7.search(p.replace(os.sep, "/"))
        if m:
            out.append((p, "author_all7", int(m.group(1)), int(m.group(3))))
    for p in glob.glob(os.path.join(EXPANDED, "miflu_L*_s*", "pred_*.npz")):
        m = re.search(r"miflu_L(\d+)_s(\d+)/pred_", p.replace(os.sep, "/"))
        if m:
            out.append((p, "expanded", int(m.group(1)), int(m.group(2))))
    return sorted(out, key=lambda t: (t[2], t[3], t[1]))


def sidecars(cell_dir, label, L, seed):
    """Best-effort list of companion artefacts for one cell (never a wildcard)."""
    out = []
    if label == "expanded":
        out += glob.glob(os.path.join(cell_dir, "*"))
    else:                                   # author_runs/L{L}_all7: per-cell files
        stem = "pred_miflu_L%d_seed%d" % (L, seed)
        out += glob.glob(os.path.join(cell_dir, stem + ".*"))
        out += glob.glob(os.path.join(cell_dir, "*_L%d_seed%d_*" % (L, seed)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="delete the failures")
    ap.add_argument("--json", default=os.path.join(QUEUE_DIR, "miflu_audit.json"))
    a = ap.parse_args()

    rows = []
    n_pass = n_bad = n_unv = 0
    for path, layout, L, S in cells():
        mse, W, n, note = rederive(path)
        want = oracle_mse(L, S)
        if want is None:
            verdict, delta = "NO_ORACLE", None
            n_unv += 1
        elif mse is None:
            verdict, delta = "NO_CELL", None
            n_unv += 1
        else:
            delta = abs(mse - want)
            if delta <= TOL:
                verdict = "PASS"
                n_pass += 1
            else:
                verdict = "CONTAMINATED"
                n_bad += 1
        rows.append({"path": path, "layout": layout, "L": L, "seed": S,
                     "W": W, "n_eval": n, "mse": mse, "oracle": want,
                     "delta": delta, "verdict": verdict, "note": note})
        print("[audit] %-14s L=%-3s s=%-5s W=%-4s n=%-4s mse=%s oracle=%s d=%s %s"
              % (verdict, L, S, W or "-", n or "-",
                 "%.6f" % mse if mse is not None else "-",
                 "%.6f" % want if want is not None else "-",
                 "%.2e" % delta if delta is not None else "-", path))

    print("[audit] %d cell(s): %d PASS, %d CONTAMINATED, %d UNVERIFIABLE"
          % (len(rows), n_pass, n_bad, n_unv))

    if a.apply:
        deleted, reset = [], []
        for r in rows:
            if r["verdict"] == "PASS":
                continue
            d = os.path.dirname(r["path"])
            for p in sidecars(d, r["layout"], r["L"], r["seed"]):
                try:
                    if os.path.isdir(p):
                        continue
                    os.remove(p)
                    deleted.append(p)
                except OSError as exc:
                    print("[audit] could not delete %s: %s" % (p, exc))
            # drop the verify marker so nothing re-uses this (L, seed)
            for mk in glob.glob(os.path.join(AUTHOR_RUNS, ".miflu_verify",
                                             "*L%d*s%d*" % (r["L"], r["seed"]))):
                try:
                    os.remove(mk)
                    deleted.append(mk)
                except OSError:
                    pass
            try:
                import queue_store
                queue_store.set_state("miflu_L%d_s%d" % (r["L"], r["seed"]), "TODO",
                                      "CONTAMINATED/UNVERIFIABLE (%s, delta=%s): "
                                      "artefacts deleted by audit_miflu_cells.py"
                                      % (r["verdict"], r["delta"]))
                reset.append("miflu_L%d_s%d" % (r["L"], r["seed"]))
            except Exception as exc:                            # noqa: BLE001
                print("[audit] queue reset failed for L%s s%s: %s" % (r["L"], r["seed"], exc))
        print("[audit] deleted %d file(s), reset %d queue row(s) to TODO"
              % (len(deleted), len(reset)))
        for p in deleted:
            print("  DELETED %s" % p)
        for t in reset:
            print("  TODO    %s" % t)

    # legacy ILI-only CSV: keep it out of the merge path for good
    legacy = os.path.join(AUTHOR_RUNS, "L24_s2021_pred",
                          "predictions_miflu_L24_paper_protocol.csv")
    if os.path.exists(legacy):
        dst_dir = os.path.join(AUTHOR_RUNS, "_superseded_not_a_benchmark_row")
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, os.path.basename(legacy))
        if not os.path.exists(dst):
            os.replace(legacy, dst) if a.apply else None
            print("[audit] legacy ILI-only CSV %s %s"
                  % ("MOVED to" if a.apply else "should be moved to", dst))

    payload = {"when": time.strftime("%F %T"), "tol": TOL,
               "n": len(rows), "pass": n_pass, "contaminated": n_bad,
               "unverifiable": n_unv, "cells": rows}
    tmp = a.json + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    os.replace(tmp, a.json)
    print("[audit] wrote %s" % a.json)
    # exit non-zero if anything is still suspect and we were not allowed to fix it
    if not a.apply and (n_bad or n_unv):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
