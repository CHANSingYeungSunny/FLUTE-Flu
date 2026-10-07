"""
data_pipeline.py — data / split / scaler / windows (train-only fitting).
=======================================================================

This module RE-USES the existing single sources of truth:

  * `configs.py`      -> FULL_ROWS / TRAIN_END / VAL_END / NATIONAL_CONFIG / VAR_COLS
  * `scaler_utils.py` -> ScalerBundle (fit on data[:TRAIN_END] ONLY)

and reproduces `train_ablation.build_windows` EXACTLY (stride 1, split decided
by the target start week with `<= val_end`), so the innovation runner sees
byte-identical windows to the existing main protocol. No val/test fitting of the
scaler happens anywhere here.
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from innovation.paths import ILI_CHANNEL, ILI_COL, RAW_CSV, SCALER_JSON

from configs import (FULL_ROWS, TRAIN_END, VAL_END, VAR_COLS, NATIONAL_CONFIG,
                     assert_full_window, derive_split)  # noqa: E402
from scaler_utils import ScalerBundle  # noqa: E402

CONFIG = dict(NATIONAL_CONFIG)
T = int(CONFIG["T"])
N = int(CONFIG["N"])


def load_raw_df() -> pd.DataFrame:
    return pd.read_csv(RAW_CSV)


def load_scaler() -> ScalerBundle:
    """Load the persisted train-only scaler (or fit+persist if absent).

    If the file exists we NEVER refit: we re-fit from train and assert the two
    agree (`assert_consistent_with`), so a stale/hand-edited scaler can never
    silently move the numbers used by the innovation runs.
    """
    import os

    if os.path.exists(SCALER_JSON):
        persisted = ScalerBundle.load_json(SCALER_JSON)
        fresh = ScalerBundle.fit_from_train(load_raw_df(), VAR_COLS,
                                            train_end=TRAIN_END, val_end=VAL_END)
        fresh.assert_consistent_with(persisted)
        return persisted
    bundle = ScalerBundle.fit_from_train(load_raw_df(), VAR_COLS,
                                         train_end=TRAIN_END, val_end=VAL_END)
    bundle.save_json(SCALER_JSON)
    return bundle


def to_array(df: pd.DataFrame) -> np.ndarray:
    return df[VAR_COLS].values.astype(np.float32)


def normalize(arr: np.ndarray, scaler: ScalerBundle) -> np.ndarray:
    mean = scaler.mean_.reshape(1, -1).astype(np.float32)
    std = scaler.scale_.reshape(1, -1).astype(np.float32)
    return ((arr - mean) / std).astype(np.float32)


def build_windows(data_norm: np.ndarray, L: int, T_in: int = T,
                  train_end: int = TRAIN_END, val_end: int = VAL_END) -> dict:
    """Sliding windows at stride 1 — EXACT mirror of train_ablation.build_windows."""
    total = data_norm.shape[0]
    nw = total - T_in - L + 1
    X = np.zeros((nw, N, T_in), dtype=np.float32)
    Y = np.zeros((nw, N, L), dtype=np.float32)
    splits = np.zeros(nw, dtype=np.int8)
    target_starts = np.arange(nw) + T_in
    for i in range(nw):
        X[i] = data_norm[i:i + T_in].T
        Y[i] = data_norm[i + T_in:i + T_in + L].T
        ts = i + T_in
        splits[i] = 0 if ts < train_end else (1 if ts <= val_end else 2)
    return {
        "X_train": X[splits == 0], "Y_train": Y[splits == 0],
        "X_val": X[splits == 1], "Y_val": Y[splits == 1],
        "X_test": X[splits == 2], "Y_test": Y[splits == 2],
        # global window indices per split (needed to recover each window's
        # absolute target start = idx + T, so predictions carry real dates)
        "idx_train": np.where(splits == 0)[0],
        "idx_val": np.where(splits == 1)[0],
        "idx_test": np.where(splits == 2)[0],
        "splits": splits, "target_starts": target_starts,
        "L": int(L), "T": int(T_in),
    }


def make_split_manifest(scaler: ScalerBundle, L: int) -> dict:
    """Machine-checkable record of the exact split used for one horizon."""
    n = len(load_raw_df())
    return {
        "dataset": "national_ili",
        "raw_csv": RAW_CSV,
        "full_rows": int(n),
        "expected_full_rows": int(FULL_ROWS),
        "train_end": int(scaler.train_end),
        "val_end": int(scaler.val_end),
        "test_end": int(n),
        "train_frac": 0.70,
        "val_frac": 0.10,
        "horizon_L": int(L),
        "T": int(T),
        "n_channels": int(N),
        "var_cols": list(VAR_COLS),
        "ili_channel": int(ILI_CHANNEL),
        "ili_col": ILI_COL,
        "window_stride": 1,
        "split_rule": "split by target start week; train if <train_end, val if <=val_end else test",
        "scaler_fit": "train rows only (data[:train_end])",
        "prompt_stats_fit": "train rows only",
    }


def make_loaders(windows: dict, split: str, batch_size: int, shuffle: bool):
    import torch
    import torch.utils.data as td

    X = windows[f"X_{split}"] if split in ("train", "val", "test") else windows[split]
    Y = windows[f"Y_{split}"] if split in ("train", "val", "test") else windows[split.replace("X_", "Y_")]
    ds = td.TensorDataset(torch.from_numpy(X), torch.from_numpy(Y))
    return td.DataLoader(ds, batch_size=batch_size, shuffle=shuffle,
                         drop_last=False)


def _self_check() -> None:
    scaler = load_scaler()
    assert scaler.train_end == TRAIN_END == 717, scaler.train_end
    assert scaler.val_end == VAL_END == 819, scaler.val_end
    n = assert_full_window(len(load_raw_df()))
    assert derive_split(n) == (TRAIN_END, VAL_END)
    w = build_windows(normalize(to_array(load_raw_df()), scaler), L=24)
    print("[data_pipeline] self-check OK")
    print(f"  windows  train={len(w['X_train'])}  val={len(w['X_val'])}  "
          f"test={len(w['X_test'])}")
    print(f"  T={T} N={N} ILI_CHANNEL={ILI_CHANNEL}")


if __name__ == "__main__":  # pragma: no cover
    _self_check()
