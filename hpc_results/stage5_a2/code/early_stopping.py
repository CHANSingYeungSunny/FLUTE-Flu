#!/usr/bin/env python
"""
early_stopping.py — Early stopping on validation loss (patience-based)
======================================================================

WHAT THIS IS
------------
A standard, literature-conventional early stopper: monitor validation loss;
when it stops improving for `patience` epochs, stop training and roll back to
the best weights (which are checkpointed as they are seen).

PROVENANCE OF THE STOPPING CRITERION  (Advisor Q5 — DO NOT BLUR THESE)
---------------------------------------------------------------------
(a) FROM THE LITERATURE — this is the whole criterion now:
    Early stopping on validation loss, monitoring validation MSE/RMSE with a
    patience of 5–10 epochs and rolling back to the best weights, is the
    standard, widely-reported practice in the ILI / epidemic-forecasting
    literature. It is not novel and carries no special numeric attribution.

(b) REMOVED (2026-09) — the "peak gate" / dual-gate design:
    This module previously implemented `PeakAwareEarlyStopping`, which
    checkpointed only when BOTH (1) val_loss improved AND (2) Peak Hit Rate >
    0.7. That design depended on the `peak_hit_rate` indicator, which was
    removed when the project's supplementary diagnostics were reduced to two
    indicators — PTE (Peak Timing Error) and PIE (Peak Intensity Error).
    The dual gate was project-specific custom engineering with no published
    precedent, and could not survive the removal of `peak_hit_rate`.
    None of it should be re-claimed as literature-derived.

(c) CONSEQUENCE FOR REPORTING:
    `full__earlystop` runs produced BEFORE 2026-09 used the dual gate and are
    NOT comparable to runs produced after it. The variant was re-run after the
    change; cite only the post-change numbers.

USAGE
-----
    stopper = EarlyStopping(patience=5, save_dir=out_dir)
    for ep in range(epochs):
        ...train...
        val_loss = ...
        res = stopper(val_loss, model, epoch=ep)
        if res["stop"]:
            break
"""

from __future__ import annotations

import json
import os

import numpy as np


class EarlyStopping:
    """Stop when validation loss stops improving; keep the best weights."""

    def __init__(self, patience: int = 5, min_delta: float = 0.0,
                 save_dir: str | None = None,
                 filename: str = "best_early_stop.pth"):
        self.patience = int(patience)
        self.min_delta = float(min_delta)
        self.save_dir = save_dir
        self.filename = filename

        self.best_val_loss = float("inf")
        self.best_epoch: int | None = None
        self.num_bad_epochs = 0
        self.history: list[dict] = []
        self.best_path: str | None = None

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)

    # ------------------------------------------------------------------ #
    def __call__(self, val_loss: float, model, epoch: int) -> dict:
        """Evaluate one epoch. Returns a decision dict."""
        val_loss = float(val_loss)
        if not np.isfinite(val_loss):
            return {"improved": False, "saved": False, "stop": False,
                    "reason": "non-finite val_loss",
                    "best_val_loss": self.best_val_loss,
                    "best_epoch": self.best_epoch,
                    "num_bad_epochs": self.num_bad_epochs}

        improved = val_loss < (self.best_val_loss - self.min_delta)

        saved = False
        if improved:
            self.best_val_loss = val_loss
            self.best_epoch = int(epoch)
            self.num_bad_epochs = 0
            if self.save_dir and model is not None:
                import torch
                self.best_path = os.path.join(self.save_dir, self.filename)
                torch.save(model.state_dict(), self.best_path)
                saved = True
        else:
            self.num_bad_epochs += 1

        stop = self.num_bad_epochs >= self.patience

        rec = {"epoch": int(epoch), "val_loss": val_loss,
               "improved": improved, "saved": saved, "stop": stop,
               "reason": ("val_loss improved" if improved
                          else f"no improvement ({self.num_bad_epochs}"
                               f"/{self.patience})")}
        self.history.append(rec)
        return {k: rec[k] for k in ("improved", "saved", "stop")} | {
            "reason": rec["reason"],
            "best_val_loss": self.best_val_loss,
            "best_epoch": self.best_epoch,
            "num_bad_epochs": self.num_bad_epochs,
        }

    # ------------------------------------------------------------------ #
    def state_dict(self) -> dict:
        return {
            "patience": self.patience, "min_delta": self.min_delta,
            "best_val_loss": self.best_val_loss,
            "best_epoch": self.best_epoch,
            "best_path": self.best_path,
            "history": self.history,
        }

    def save_report(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.state_dict(), f, indent=2, default=float)
        return path


# --------------------------------------------------------------------------- #
def _self_check() -> None:
    # ---- first observation always improves --------------------------------
    s = EarlyStopping(patience=2)
    r = s(val_loss=1.0, model=None, epoch=0)
    assert r["improved"] is True and r["saved"] is False, r
    assert "val_loss improved" in r["reason"], r["reason"]

    # ---- a worse loss must NOT improve, and counts against patience ------
    r = s(val_loss=1.5, model=None, epoch=1)
    assert r["improved"] is False and r["stop"] is False, r
    assert s.num_bad_epochs == 1, s.num_bad_epochs

    # ---- patience exhausted -> stop --------------------------------------
    r = s(val_loss=1.6, model=None, epoch=2)
    assert r["stop"] is True, r

    # ---- a fresh improvement resets the patience counter -----------------
    s2 = EarlyStopping(patience=2)
    s2(1.0, None, 0)
    s2(1.5, None, 1)
    assert s2.num_bad_epochs == 1
    r = s2(0.5, None, 2)
    assert r["improved"] is True and s2.num_bad_epochs == 0, s2.num_bad_epochs
    assert s2.best_epoch == 2 and s2.best_val_loss == 0.5, s2.state_dict()

    # ---- min_delta: a tiny improvement below min_delta is NOT an improve --
    s3 = EarlyStopping(patience=2, min_delta=0.1)
    s3(1.0, None, 0)
    r = s3(0.95, None, 1)          # only 0.05 better -> below min_delta
    assert r["improved"] is False, r

    # ---- non-finite loss is rejected without touching state --------------
    s4 = EarlyStopping(patience=2)
    s4(1.0, None, 0)
    r = s4(float("nan"), None, 1)
    assert r["improved"] is False and r["stop"] is False, r
    assert s4.num_bad_epochs == 0, "non-finite must not consume patience"
    assert "non-finite" in r["reason"], r["reason"]

    print("[early_stopping] self-check OK")


if __name__ == "__main__":
    _self_check()
