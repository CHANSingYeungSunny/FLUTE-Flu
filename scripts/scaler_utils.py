#!/usr/bin/env python
"""
scaler_utils.py — StandardScaler persistence & inverse transform (Advisor Q3)
=============================================================================

WHY THIS MODULE EXISTS
----------------------
Figures exported by `train_miflu.py` carry ILITOTAL in **StandardScaler (z)
space** (range ~ -1 .. +12), which is unreadable to a clinician. The paper
(MIFlu_paper.md §V-B) requires National MSE/MAE to STAY in z space, but the
figure and the exported CSV must show **patient counts**.

So we need a single, auditable place that:
  * fits the scaler on the TRAIN split only (leakage-safe, matches
    `train_miflu.load_and_normalize`);
  * persists mean_/scale_ to JSON so a TEST-time / plotting-time process can
    invert predictions without re-reading the raw CSV or re-deriving the split;
  * inverts z -> physical units with the EXACT same numerics used at fit time.

NUMERIC CONVENTION (do not "improve")
-------------------------------------
`train_miflu.load_and_normalize` uses:

    train_mean = data[:train_end].mean(axis=0, keepdims=True)
    train_std  = data[:train_end].std(axis=0, keepdims=True) + 1e-8

numpy `.std` is the POPULATION std (ddof=0). The epsilon is added to the std.
This module reproduces that byte-for-byte; introducing sklearn would silently
change ddof and shift every published number.

PAPER ANCHOR (MIFlu_paper.md §V-B, lines 254-260)
-------------------------------------------------
  * National ILI  -> MSE / MAE, computed on StandardScaler-normalized data
                     (NO de-normalization).
  * Regional ILI  -> RMSE / PCC, "used after de-normalizing values to the
                     original range".

The advisor's quotation belongs to the REGIONAL branch. Therefore this module's
`inverse()` is used for FIGURES and for a clearly-labelled SUPPLEMENTARY
physical-unit metric column -- never to replace the primary z-space Table V
numbers.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
DEFAULT_SCALER_PATH = os.path.join(PROJECT_ROOT, "data", "scaler_miflu_national.json")
DEFAULT_RAW_CSV = os.path.join(PROJECT_ROOT, "data", "raw", "national_illness_raw.csv")

DEFAULT_VAR_COLS = [
    "% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
    "ILITOTAL", "NUM. OF PROVIDERS", "OT",
]

EPS = 0.0  # Author uses sklearn StandardScaler (NO epsilon). Matched exactly.


class ScalerBundle:
    """Train-only StandardScaler statistics + inverse transform.

    Attributes mirror sklearn's naming (`mean_`, `scale_`) so the maths is
    recognisable, but the JSON schema matches the file already committed at
    `data/scaler_miflu_national.json` (`mean` / `std` / `train_end` /
    `val_end` / `var_cols`).
    """

    def __init__(self, mean_, scale_, train_end, val_end, var_cols):
        self.mean_ = np.asarray(mean_, dtype=np.float64).ravel()
        self.scale_ = np.asarray(scale_, dtype=np.float64).ravel()
        self.train_end = int(train_end)
        self.val_end = int(val_end)
        self.var_cols = list(var_cols)
        if self.mean_.shape != self.scale_.shape:
            raise ValueError("mean_/scale_ shape mismatch")
        if len(self.var_cols) != self.mean_.shape[0]:
            raise ValueError(
                f"var_cols has {len(self.var_cols)} entries but mean_ has "
                f"{self.mean_.shape[0]} channels")

    # ---------------------------------------------------------------- fit ---
    @classmethod
    def fit_from_train(cls, df: pd.DataFrame, var_cols=DEFAULT_VAR_COLS,
                       train_frac: float = 0.70, val_frac: float = 0.10,
                       train_end: int | None = None,
                       val_end: int | None = None,
                       dtype=np.float32) -> "ScalerBundle":
        """Fit on the first `train_end` rows ONLY.

        Defaults reproduce `train_miflu.load_and_normalize` exactly:
            t_end = int(n*0.70); v_end = t_end + int(n*0.10)

        `dtype` MUST stay float32: the published baseline was normalised from a
        float32 array, and switching to float64 would change every reported
        MSE/MAE in the last decimal (silently invalidating Table V comparison).
        """
        data = df[list(var_cols)].values.astype(dtype)
        n = len(data)
        if train_end is None:
            train_end = int(n * train_frac)
        if val_end is None:
            val_end = train_end + int(n * val_frac)
        train_end = int(train_end)
        val_end = int(val_end)
        if not (0 < train_end < val_end <= n):
            raise ValueError(f"bad split: n={n} train_end={train_end} val_end={val_end}")

        mean_ = data[:train_end].mean(axis=0, keepdims=True)
        scale_ = data[:train_end].std(axis=0, keepdims=True) + EPS
        return cls(mean_, scale_, train_end, val_end, var_cols)

    @classmethod
    def fit_from_raw_csv(cls, raw_csv: str = DEFAULT_RAW_CSV,
                         var_cols=DEFAULT_VAR_COLS, **kw) -> "ScalerBundle":
        return cls.fit_from_train(pd.read_csv(raw_csv), var_cols=var_cols, **kw)

    def assert_consistent_with(self, other: "ScalerBundle", rtol: float = 1e-5) -> None:
        """Guard against a test-time process using different statistics than
        the one that trained the model."""
        if self.train_end != other.train_end or self.val_end != other.val_end:
            raise ValueError(f"split mismatch: {self.train_end}/{self.val_end} vs "
                             f"{other.train_end}/{other.val_end}")
        if self.var_cols != other.var_cols:
            raise ValueError("var_cols mismatch")
        if not np.allclose(self.mean_, other.mean_, rtol=rtol):
            raise ValueError("mean_ mismatch — scaler was refit with different data")
        if not np.allclose(self.scale_, other.scale_, rtol=rtol):
            raise ValueError("scale_ mismatch — scaler was refit with different data")

    # ------------------------------------------------------------- persist ---
    def to_dict(self) -> dict:
        return {
            "mean": self.mean_.tolist(),
            "std": self.scale_.tolist(),
            "train_end": self.train_end,
            "val_end": self.val_end,
            "var_cols": self.var_cols,
        }

    def save_json(self, path: str = DEFAULT_SCALER_PATH) -> str:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return path

    @classmethod
    def load_json(cls, path: str = DEFAULT_SCALER_PATH) -> "ScalerBundle":
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return cls(d["mean"], d["std"], d["train_end"], d["val_end"], d["var_cols"])

    @classmethod
    def load_or_fit(cls, path: str = DEFAULT_SCALER_PATH,
                    raw_csv: str = DEFAULT_RAW_CSV,
                    var_cols=DEFAULT_VAR_COLS) -> "ScalerBundle":
        """Load the persisted scaler; if absent, fit from raw and save it.

        Always prefers the persisted file so that a TEST-time process can never
        silently recompute different statistics than the TRAIN-time process.
        """
        if os.path.exists(path):
            return cls.load_json(path)
        bundle = cls.fit_from_raw_csv(raw_csv, var_cols=var_cols)
        bundle.save_json(path)
        return bundle

    # --------------------------------------------------------------- maths ---
    def channel_index(self, name: str) -> int:
        return self.var_cols.index(name)

    def inverse(self, z, ch: int | str) -> np.ndarray:
        """z -> physical units for ONE channel.

        Args:
            z:  array-like, StandardScaler-space values.
            ch: channel index (int) or column name (str).
        Returns:
            np.ndarray of the same shape, in original units (e.g. patients).
        """
        if isinstance(ch, str):
            ch = self.channel_index(ch)
        return np.asarray(z, dtype=np.float64) * self.scale_[ch] + self.mean_[ch]

    def inverse_all(self, z) -> np.ndarray:
        """z -> physical units for ALL channels. `z` shape (..., N)."""
        z = np.asarray(z, dtype=np.float64)
        return z * self.scale_.reshape((1,) * (z.ndim - 1) + (-1,)) \
            + self.mean_.reshape((1,) * (z.ndim - 1) + (-1,))

    def transform(self, x, ch: int | str) -> np.ndarray:
        """physical -> z for ONE channel (inverse of `inverse`)."""
        if isinstance(ch, str):
            ch = self.channel_index(ch)
        return (np.asarray(x, dtype=np.float64) - self.mean_[ch]) / self.scale_[ch]

    # ------------------------------------------------------------- torch ----
    def torch_mean_std(self, device=None, dtype=None):
        """Return (train_mean, train_std) tensors shaped (1, N, 1).

        These are the `train_mean` / `train_std` arguments accepted by
        `MIFlu.forward`, which computes `y_phys = y_hat_rev * std + mean`
        on-GPU before the data ever reaches the CPU.
        """
        import torch
        tm = torch.as_tensor(self.mean_, dtype=dtype, device=device).view(1, -1, 1)
        ts = torch.as_tensor(self.scale_, dtype=dtype, device=device).view(1, -1, 1)
        return tm, ts

    def __repr__(self) -> str:  # pragma: no cover
        return (f"ScalerBundle(train_end={self.train_end}, val_end={self.val_end}, "
                f"n_channels={len(self.var_cols)})")


# --------------------------------------------------------------------------- #
def _self_check() -> None:
    bundle = ScalerBundle.load_or_fit()
    assert bundle.train_end == 717, bundle.train_end
    assert bundle.val_end == 819, bundle.val_end
    assert bundle.channel_index("ILITOTAL") == 4

    # Round-trip: physical -> z -> physical must be the identity.
    raw = pd.read_csv(DEFAULT_RAW_CSV)
    phys = raw["ILITOTAL"].values.astype(np.float64)
    z = bundle.transform(phys, "ILITOTAL")
    back = bundle.inverse(z, "ILITOTAL")
    assert np.allclose(phys, back, rtol=1e-9, atol=1e-6), "round-trip failed"

    # Numbers quoted in the advisor report.
    print("[scaler_utils] self-check OK")
    print(f"  train_end={bundle.train_end} val_end={bundle.val_end}")
    print(f"  ILITOTAL train mean={bundle.mean_[4]:.1f} std={bundle.scale_[4]:.1f}")
    lo, hi = float(z.min()), float(z.max())
    print(f"  ILITOTAL z-range: [{lo:.3f}, {hi:.3f}]  <- the 0..12 axis the advisor saw")
    print(f"  ILITOTAL physical range: [{phys.min():.0f}, {phys.max():.0f}] patients")


if __name__ == "__main__":
    _self_check()
