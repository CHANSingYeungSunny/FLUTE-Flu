"""test_train_regional.py ??the Table VI harness (CPU only).

What is tested
--------------
1. **Data + split** ??the 10 HHS series load, the 1 084-week window is the one
   every regional script filters to, and the 50/10/40 split borders hold.
2. **Windows** ??for all seven paper horizons (`L ??{2,3,5,10,13,15,20}`) the
   strict-containment window counts are positive and the shared rule
   `eval_slice(W) = (W//16)*16` leaves at least one batch to score.
3. **A whole cell** ??one cheap cell (`nlinear`, 1 epoch, capped train windows)
   writes the **five** rule-11 artefacts with the documented shapes:
   `pred`/`target` `(W, V, L)`, the CSV twin, the per-variable results table (in
   z space **and** patients), the checkpoint and a manifest carrying the measured
   hardware block, the data sha256, the split and the checkpoint sha256.
4. **The layout guard** ??a 7-channel national array is REJECTED by
   `check_cell_layout(..., n_vars=10)`; the regional task cannot silently borrow
   the national shape.
5. **Single-region mode** ??`--region hhs5` produces `V=1` and says so in the
   manifest.

Run:  python -m pytest -q tests/test_train_regional.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(PROJECT_ROOT, "scripts")
for _p in (SCRIPTS, PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import train_regional as tr                      # noqa: E402
from configs import REGIONAL_CONFIG, HHS_COLS    # noqa: E402
from eval_windows import check_cell_layout, eval_slice   # noqa: E402

DATA = tr.resolve_data_path()
pytestmark = pytest.mark.skipif(not os.path.exists(DATA),
                                reason="US regional dataset absent")


def test_paper_regional_config_is_the_one_in_configs():
    """The harness must not fork the paper's regional hyper-parameters."""
    assert REGIONAL_CONFIG["T"] == 20
    assert tuple(REGIONAL_CONFIG["L_list"]) == (2, 3, 5, 10, 13, 15, 20)
    assert REGIONAL_CONFIG["K"] == 4
    assert REGIONAL_CONFIG["epochs"] == 50
    assert REGIONAL_CONFIG["batch_size"] == 32
    assert REGIONAL_CONFIG["N"] == 10
    assert list(HHS_COLS) == [f"HHS{i}" for i in range(1, 11)]


def test_load_regional_split_and_columns():
    dd = tr.load_regional(DATA, log=lambda *a, **k: None)
    assert dd["n"] == 1084
    assert dd["data_norm"].shape == (1084, 10)
    assert dd["train_end"] == 542 and dd["val_end"] == 650
    assert dd["var_cols"] == list(HHS_COLS)
    assert np.isfinite(dd["data_norm"]).all()
    # the scaler used only the training rows: their z-space mean is ~0
    assert abs(float(dd["data_norm"][:dd["train_end"]].mean())) < 1e-3


def test_every_regional_horizon_has_windows_under_the_shared_rule():
    from train_nlinear_966 import build_windows
    dd = tr.load_regional(DATA, log=lambda *a, **k: None)
    T = REGIONAL_CONFIG["T"]
    for L in REGIONAL_CONFIG["L_list"]:
        Xt, Yt, Xv, Yv, Xte, Yte, _ = build_windows(
            dd["data_norm"], T, L, dd["train_end"], dd["val_end"],
            containment="strict")
        assert len(Xt) > 0 and len(Xv) > 0
        n_eval = eval_slice(len(Xte))
        assert n_eval >= 16, f"L={L}: only {n_eval} evaluation windows"
        assert n_eval % 16 == 0


def test_check_cell_layout_rejects_the_national_seven_channel_shape():
    pred = np.zeros((40, 7, 2), dtype=np.float32)
    with pytest.raises(ValueError):
        check_cell_layout(pred, pred, None, L=2, n_vars=10)
    # and accepts the regional shape
    reg = np.zeros((40, 10, 2), dtype=np.float32)
    assert check_cell_layout(reg, reg, None, L=2, n_vars=10) == (40, 32)


def test_score_cell_has_aggregate_and_per_region_rows_in_both_spaces():
    rng = np.random.default_rng(0)
    pred = rng.normal(0, 1, (64, 10, 3))
    targ = rng.normal(0, 1, (64, 10, 3))
    mean = np.zeros((1, 10)) + 100.0
    scale = np.ones((1, 10)) * 10.0
    out = tr.score_cell(pred, targ, mean, scale, HHS_COLS)
    assert len(out) == 11                      # aggregate + 10 regions
    agg = out[out["scope"] == "aggregate"].iloc[0]
    assert agg["n_variables"] == 10
    assert np.isfinite(agg["rmse_phys"]) and np.isfinite(agg["pcc_phys"])
    assert np.isfinite(agg["rmse_z"]) and np.isfinite(agg["pcc_z"])
    per = out[out["scope"] == "per_variable"]
    assert list(per["variable"]) == list(HHS_COLS)
    for col in ("mse_z", "mae_z", "rmse_z", "pcc_z",
                "mse_phys", "mae_phys", "rmse_phys", "pcc_phys"):
        assert np.isfinite(agg[col])
        assert np.isfinite(per[col]).all()
    # the physical MSE must be the z MSE scaled by sigma^2 (10^2 here)
    assert abs(agg["mse_phys"] - agg["mse_z"] * 100.0) < 1e-6


def test_one_full_cell_writes_the_rule11_artefact_set(tmp_path):
    dd = tr.load_regional(DATA, log=lambda *a, **k: None)
    r = tr.train_cell(
        dd, model_name="nlinear", region="all", L=2, seed=42, epochs=1,
        batch=32, lr=5e-4, layers=4, device="cpu",
        export_root=str(tmp_path / "regional"), ckpt_root=str(tmp_path / "ckpt"),
        max_train=64, max_val=16, log=lambda *a, **k: None)
    cell = "nlinear_L2_s42"
    for name in (f"pred_{cell}.npz", f"pred_{cell}.csv", f"results_{cell}.csv",
                 f"manifest_{cell}.json", f"epochs_{cell}.csv"):
        assert os.path.exists(os.path.join(r["out_dir"], name)), name
    assert os.path.exists(r["ckpt"])

    d = np.load(r["npz"], allow_pickle=True)
    W = int(d["pred"].shape[0])
    assert d["pred"].shape == (W, 10, 2) and d["target"].shape == (W, 10, 2)
    assert d["target_start_row"].shape == (W,)
    assert int(d["n_eval_windows"]) == eval_slice(W)
    assert str(d["region"]) == "all"
    assert check_cell_layout(d["pred"], d["target"], d["target_start_row"],
                             L=2, n_vars=10) == (W, eval_slice(W))

    import pandas as pd
    res = pd.read_csv(r["results"])
    assert len(res) == 11
    assert set(res["scope"]) == {"aggregate", "per_variable"}
    assert (res["n_eval_windows"] == eval_slice(W)).all()
    assert (res["n_windows_available"] == W).all()

    m = json.loads(open(r["manifest"], encoding="utf-8").read())
    assert m["table"].startswith("VI")
    assert m["n_vars"] == 10
    assert m["containment"] == "strict"
    assert m["split"]["n_rows"] == 1084
    assert m["data_sha256"] and len(m["data_sha256"]) == 64
    assert m["checkpoint"]["sha256"] and len(m["checkpoint"]["sha256"]) == 64
    assert "hardware" in m and "run_device" in m["hardware"]
    assert m["config"]["K"] == 4 and m["config"]["batch"] == 32
    assert m["probe_only"] is False


def test_single_region_mode_gives_one_channel(tmp_path):
    dd = tr.load_regional(DATA, log=lambda *a, **k: None)
    single = tr.select_region(dd, "hhs5", log=lambda *a, **k: None)
    assert single["data_norm"].shape == (1084, 1)
    assert single["var_cols"] == ["HHS5"]
    r = tr.train_cell(
        single, model_name="nlinear", region="HHS5", L=3, seed=42, epochs=1,
        batch=32, lr=5e-4, layers=4, device="cpu",
        export_root=str(tmp_path / "regional"), ckpt_root=str(tmp_path / "ckpt"),
        max_train=32, max_val=16, log=lambda *a, **k: None)
    d = np.load(r["npz"], allow_pickle=True)
    assert d["pred"].shape[1] == 1 and d["pred"].shape[2] == 3
    assert list(d["var_cols"]) == ["HHS5"]
    m = json.loads(open(r["manifest"], encoding="utf-8").read())
    assert m["n_vars"] == 1 and m["var_cols"] == ["HHS5"]


if __name__ == "__main__":       # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
