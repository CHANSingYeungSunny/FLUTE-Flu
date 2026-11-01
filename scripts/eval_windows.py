#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""eval_windows.py — THE single definition of "which test windows are evaluated".

WHY THIS FILE EXISTS (user ruling, 2026-11-01, non-negotiable)
--------------------------------------------------------------
The MIFlu reproduction does **not** score every available test window. Its test
loader is built in `train_miflu.train_L` as

    el = DataLoader(TensorDataset(Xte, Yte), batch_size=16, shuffle=False,
                    drop_last=True)

with `drop_last=True`, so the final partial batch (fewer than 16 windows) is
silently discarded. Number of test windows actually scored is therefore

    (W // 16) * 16          # W = windows available at that horizon

which for the current A-track split (`containment="strict"`, 966 rows) gives

    L    available W    evaluated (W//16)*16    discarded
    ---  -----------    --------------------    ---------
    24   170            160                     10
    36   158            144                     14
    48   146            144                      2
    60   134            128                      6

Those discarded windows are **anomalously hard**: measured on four L=24 seeds,
the full-170 MSE is **1.4111x** the first-160 MSE (per-seed ratios
1.3929-1.4423). Comparing a model scored on 170 windows with MIFlu scored on
160 would therefore make the table incomparable and can reorder the ranking.

THE RULE
--------
Every model, every horizon, every table and every figure in this project is
scored on exactly the same **first `(W // 16) * 16` test windows** — MIFlu's
set. One definition, imported everywhere; the literal 160 must never be
hard-coded anywhere else.

Usage
-----
    from eval_windows import eval_slice, crop, assert_uniform
    n = eval_slice(pred.shape[0])         # window axis is axis 0 of (W, 7, L)
    pred, target, ts = crop(pred, target, target_start_row)

Array layout (asserted, never assumed): every exported benchmark cell stores
`pred` and `target` with shape **(W, 7, L)** — window axis **0**, variable axis
1, lead axis 2 — plus `target_start_row` of length W. `crop()` and
`check_cell_layout()` assert this before slicing, because a transposed array
would silently slice leads instead of windows.
"""
from __future__ import annotations

import numpy as np

#: The author's test-loader batch size. `train_miflu.train_L` hard-codes
#: `batch_size=16` for the test loader; it is the same 16 used by the training
#: loader, and it is the only reason the evaluation set is truncated.
BATCH = 16

#: The window axis of a stored cell array, i.e. `pred.shape[WINDOW_AXIS] == W`.
WINDOW_AXIS = 0

#: Variable axis and lead axis (documented, asserted by `check_cell_layout`).
VAR_AXIS = 1
LEAD_AXIS = 2

#: Number of numeric channels in every full cell.
N_VARS = 7


def eval_slice(W: int, batch: int = BATCH) -> int:
    """Number of test windows actually evaluated when `W` are available.

    This is MIFlu's own count: `train_miflu.train_L` builds its test loader with
    `DataLoader(..., batch_size=16, shuffle=False, drop_last=True)`, so the last
    partial batch is dropped and only `(W // batch) * batch` windows are scored.

    Parameters
    ----------
    W : int
        Windows available for this horizon (e.g. 170 at L=24).
    batch : int
        Test-loader batch size; 16 unless the author code changes.

    Returns
    -------
    int
        Windows to evaluate — the first `(W // batch) * batch` of them, in the
        order stored in the npz (test split is chronological, `shuffle=False`).
    """
    W = int(W)
    batch = int(batch)
    if W < 0:
        raise ValueError(f"negative window count: {W}")
    if batch <= 0:
        raise ValueError(f"batch must be positive, got {batch}")
    return (W // batch) * batch


def n_discarded(W: int, batch: int = BATCH) -> int:
    """Windows present in the export but never scored (the author's remainder)."""
    return int(W) - eval_slice(W, batch)


def check_cell_layout(pred, target, target_start_row=None, L=None, label: str = "",
                      n_vars: int = N_VARS):
    """Assert the documented `(W, 7, L)` layout and return `(W, n_eval)`.

    `n_vars` defaults to the national 7 channels. The regional Table VI task has
    **ten** target series (the HHS regions) and no 7-channel equivalent, so
    `train_regional.py` passes `n_vars=10` (or 1 for a single-region run). The
    check is otherwise identical: the point is that a transposed array fails
    loudly instead of being sliced on the wrong axis.

    Raises
    ------
    ValueError
        If the arrays are not `(W, n_vars, L)` with a matching
        `target_start_row`. This is the guard that makes a transposed export loud
        instead of silent: slicing axis 0 of a `(7, W, L)` array would remove
        variables, not windows.
    """
    pred = np.asarray(pred)
    target = np.asarray(target)
    where = f" [{label}]" if label else ""
    n_vars = int(n_vars)
    if pred.ndim != 3:
        raise ValueError(f"pred must be 3-D (W,n_vars,L), got shape {pred.shape}{where}")
    if pred.shape != target.shape:
        raise ValueError(f"pred shape {pred.shape} != target shape {target.shape}{where}")
    if pred.shape[VAR_AXIS] != n_vars:
        raise ValueError(f"variable axis 1 must have length {n_vars}, "
                         f"got {pred.shape[VAR_AXIS]} in {pred.shape}{where}")
    if L is not None and pred.shape[LEAD_AXIS] != int(L):
        raise ValueError(f"lead axis 2 must have length L={L}, "
                         f"got {pred.shape[LEAD_AXIS]} in {pred.shape}{where}")
    W = int(pred.shape[WINDOW_AXIS])
    if target_start_row is not None:
        ts = np.asarray(target_start_row).ravel()
        if ts.size != W:
            raise ValueError(f"target_start_row has {ts.size} entries for W={W}{where}")
    return W, eval_slice(W)


def crop(pred, target, target_start_row=None, L=None, label: str = "",
         n_vars: int = N_VARS):
    """Slice `(W, n_vars, L)` arrays down to the shared evaluation windows.

    Returns `(pred, target, target_start_row, W_available, n_eval)`, with the
    window axis cropped to `eval_slice(W)` and `target_start_row` cropped to the
    same length. Nothing else is touched: the variable and lead axes are
    preserved verbatim, so the result is the author's evaluation set exactly.
    """
    W, n = check_cell_layout(pred, target, target_start_row, L, label, n_vars)
    p = np.asarray(pred)[:n]
    t = np.asarray(target)[:n]
    if target_start_row is None:
        return p, t, None, W, n
    ts = np.asarray(target_start_row).ravel()[:n]
    return p, t, ts, W, n


def assert_uniform(frame, by=("L",), col="n_eval_windows", what="arms"):
    """Assert every arm at a given horizon was scored on the SAME window count.

    This is the invariant the ruling buys: for each horizon, `n_eval_windows`
    must have exactly one value across all models, and it must equal
    `eval_slice(W_available)` — i.e. MIFlu's number.
    """
    if col not in frame.columns:
        raise ValueError(f"table has no `{col}` column")
    for key, grp in frame.groupby(list(by)):
        vals = sorted(set(int(v) for v in grp[col]))
        if len(vals) != 1:
            raise AssertionError(
                f"non-uniform {col} at {dict(zip(by, (key,) if not isinstance(key, tuple) else key))}: "
                f"{vals} across {len(grp)} {what}")
        if "n_windows_available" in frame.columns:
            avail = sorted(set(int(v) for v in grp["n_windows_available"]))
            if avail != [vals[0]] and eval_slice(avail[0]) != vals[0]:
                raise AssertionError(f"{col}={vals[0]} != eval_slice({avail[0]})")
    return True


def report(horizons=(24, 36, 48, 60), available=None) -> list:
    """Console table of the rule: available / evaluated / discarded per horizon.

    `available` maps L -> W (windows on disk). When omitted, the measured A-track
    counts 170/158/146/134 for L=24/36/48/60 are used **for display only** — the
    authoritative W comes from each npz (`target_start_row` length), and every
    script asserts its own file against `eval_slice`.
    """
    available = available or {24: 170, 36: 158, 48: 146, 60: 134}
    rows = []
    for L in horizons:
        W = int(available[L])
        n = eval_slice(W)
        rows.append((L, W, n, W - n))
        print(f"[eval-window] L={L:2d}  available={W:3d}  evaluated={n:3d}  "
              f"discarded={W - n:2d}  (drop_last=True, batch={BATCH})")
    return rows
