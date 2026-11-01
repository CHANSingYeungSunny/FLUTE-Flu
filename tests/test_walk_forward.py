"""test_walk_forward.py — the rolling-origin splitter (CPU only, no training).

What is tested, and why each test exists
---------------------------------------
1. **Geometry** — `make_folds(966, k=5)` produces five expanding folds whose test
   segments are disjoint and strictly ordered in time. The test recomputes the
   row sets itself instead of trusting `assert_folds`.
2. **The published split is inside the fold set** — fold 5 is exactly
   `(676, 773, 966)`, and its strict-containment window counts are
   `549 / 74 / 170` at `L=24`, i.e. the same numbers as the stored benchmark cell
   `hpc_results/expanded_runs/nlinear_L24_s42/metrics.csv`. Rolling origin
   therefore *contains* the protocol behind every published number.
3. **Infeasibility is reported, not hidden** — `K=5` with a pure 10 % validation
   block cannot work at `L>=36` on 966 rows (arithmetic in the module docstring);
   the splitter must raise `FoldError` with the reason and the largest feasible
   `k`.
4. **The leakage guard is structural** — `restrict_data` truncates the series to
   `rows[0:test_end]`, and `build_windows` on the truncated series reproduces the
   fold's own window counts (i.e. a fold cannot be scored on rows past its
   origin).
5. **The CLI hook exists and does not change the default** — `--fold 0` returns
   the profile's own borders; `--fold 3` runs through
   `scripts/train_backbone_966.py` and writes a cell whose npz carries the fold
   metadata and whose test block ends where the fold says it does.

Run:  python -m pytest -q tests/test_walk_forward.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(PROJECT_ROOT, "scripts")
for _p in (SCRIPTS, PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import walk_forward as wf                       # noqa: E402
from configs import split_for_profile           # noqa: E402

N_ROWS = 966


# ── 1. geometry ─────────────────────────────────────────────────────────────
def test_make_folds_k5_has_the_documented_shape():
    folds = wf.make_folds(N_ROWS, k=5)
    assert len(folds) == 5
    assert [f.index for f in folds] == [1, 2, 3, 4, 5]
    assert all(f.n_rows == N_ROWS for f in folds)
    assert folds[-1].test_end == N_ROWS, "the last fold must reach the last row"
    # expanding: every border grows with the fold index
    for prev, cur in zip(folds, folds[1:]):
        assert cur.train_end > prev.train_end
        assert cur.val_end > prev.val_end
        assert cur.test_end > prev.test_end


def test_test_segments_are_disjoint_and_strictly_ordered():
    """Recomputed here, not delegated to `assert_folds`."""
    folds = wf.make_folds(N_ROWS, k=5)
    covered = []
    for f in folds:
        covered.append(set(range(f.val_end, f.test_end)))
    for i in range(len(covered) - 1):
        assert not (covered[i] & covered[i + 1]), \
            f"folds {i+1} and {i+2} share test rows"
    # strictly ordered: each test block starts after the previous one ended
    for prev, cur in zip(folds, folds[1:]):
        assert cur.val_end > prev.test_end
    # and globally: no row is scored twice
    all_rows = [r for block in covered for r in block]
    assert len(all_rows) == len(set(all_rows))


def test_each_fold_is_20_percent_test_and_at_least_10_percent_val():
    for f in wf.make_folds(N_ROWS, k=5):
        assert abs(f.n_test - int(f.test_end * 0.20)) <= 1
        assert f.n_val >= int(f.test_end * 0.10) - 1
        assert f.n_train + f.n_val + f.n_test == f.test_end


def test_growth_below_the_disjointness_floor_is_rejected():
    with pytest.raises(wf.FoldError) as ei:
        wf.make_folds(N_ROWS, k=5, growth=1.10)
    assert "disjoint" in str(ei.value)


def test_k5_with_a_pure_ten_percent_validation_block_is_infeasible():
    """The arithmetic the module docstring describes: 4 val windows at L=36."""
    with pytest.raises(wf.FoldError) as ei:
        wf.make_folds(N_ROWS, k=5, val_floor_rows=0)
    msg = str(ei.value)
    assert "too short for L" in msg and "val yields" in msg


def test_max_feasible_k_reports_the_alternative():
    assert wf.max_feasible_k(N_ROWS, val_floor_rows=0) >= 2
    assert wf.max_feasible_k(N_ROWS, val_floor_rows=wf.val_floor_for()) == 5


# ── 2. the published split is inside the fold set ──────────────────────────
def test_last_fold_equals_the_published_split():
    folds = wf.make_folds(N_ROWS, k=5)
    assert folds[-1].split() == split_for_profile("author_966", N_ROWS)
    assert folds[-1].split() == (676, 773)
    assert (folds[-1].train_end, folds[-1].val_end, folds[-1].test_end) == (676, 773, 966)
    # a pure-shape k=2 layout also lands exactly on the published split
    assert wf.make_folds(N_ROWS, k=2, val_floor_rows=0)[-1].split() == (676, 773)


def test_fold5_window_counts_match_the_stored_benchmark_cell():
    """External anchor: the numbers must equal the cell already on disk."""
    metrics = os.path.join(PROJECT_ROOT, "hpc_results", "expanded_runs",
                           "nlinear_L24_s42", "metrics.csv")
    if not os.path.exists(metrics):
        pytest.skip("stored benchmark cell absent")
    import csv
    with open(metrics, newline="", encoding="utf-8") as fh:
        row = next(csv.DictReader(fh))
    f = wf.make_folds(N_ROWS, k=5)[-1]
    wc = f.window_counts(104, 24)
    assert wc["n_train_windows"] == int(row["n_train"]) == 549
    assert wc["n_val_windows"] == int(row["n_val"]) == 74
    assert wc["n_test_windows"] == int(row["n_test"]) == 170


# ── 3. resolve_split / --fold 0 keeps the default ──────────────────────────
def test_resolve_split_without_a_fold_is_the_profile_split():
    train_end, val_end, fold = wf.resolve_split("author_966", N_ROWS, fold=None)
    assert (train_end, val_end, fold) == (676, 773, None)
    assert wf.resolve_split("author_966", N_ROWS, fold=0)[:2] == (676, 773)


def test_resolve_split_with_a_fold_uses_the_fold_borders():
    train_end, val_end, fold = wf.resolve_split("author_966", N_ROWS, fold=3)
    assert fold.index == 3
    assert (train_end, val_end) == fold.split()
    assert val_end < fold.test_end


def test_resolve_fold_rejects_an_out_of_range_index():
    with pytest.raises(wf.FoldError):
        wf.resolve_split("author_966", N_ROWS, fold=6)


# ── 4. the leakage guard is structural ─────────────────────────────────────
def test_restrict_data_truncates_to_the_fold_window_and_windows_match():
    from train_nlinear_966 import build_windows, load_and_normalize
    f = wf.make_folds(N_ROWS, k=5)[0]
    dd = load_and_normalize("author_966", split=f.split())
    assert dd["split_source"] == "walk_forward_fold"
    assert (dd["train_end"], dd["val_end"]) == f.split()
    dd = wf.restrict_data(dd, f)
    assert dd["data_norm"].shape[0] == f.test_end == dd["n"]
    assert len(dd["train_df"]) <= f.train_end
    for L in (24, 36, 48, 60):
        Xt, Yt, Xv, Yv, Xte, Yte, _ = build_windows(
            dd["data_norm"], 104, L, dd["train_end"], dd["val_end"],
            containment="strict")
        wc = f.window_counts(104, L)
        assert (len(Xt), len(Xv), len(Xte)) == (
            wc["n_train_windows"], wc["n_val_windows"], wc["n_test_windows"])
        # the last scored target must end inside the fold window
        assert Yte.shape[0] == wc["n_test_windows"]
    # the untruncated series would give a MUCH larger "test" split — the guard
    # is what prevents that
    dd_full = load_and_normalize("author_966", split=f.split())
    Xt, Yt, Xv, Yv, Xte_full, Yte_full, _ = build_windows(
        dd_full["data_norm"], 104, 24, dd_full["train_end"], dd_full["val_end"],
        containment="strict")
    assert len(Xte_full) > len(Yte), "truncation must shrink the test split"


# ── 5. CLI ─────────────────────────────────────────────────────────────────
def test_cli_prints_the_fold_table():
    out = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "walk_forward.py"),
         "--rows", "966", "--k", "5"],
        capture_output=True, text=True, cwd=PROJECT_ROOT)
    assert out.returncode == 0, out.stderr
    assert "5 folds" in out.stdout
    assert "all assertions passed" in out.stdout
    assert "f5" in out.stdout


def test_cli_reports_infeasibility_with_a_nonzero_exit():
    out = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "walk_forward.py"),
         "--rows", "966", "--k", "5", "--pure-shape"],
        capture_output=True, text=True, cwd=PROJECT_ROOT)
    assert out.returncode == 2
    assert "INFEASIBLE" in out.stdout
    assert "largest feasible k" in out.stdout


def test_backbone_runner_accepts_fold_and_writes_fold_metadata(tmp_path):
    """End-to-end: one 1-epoch NLinear fold cell (CPU, a few seconds)."""
    export = tmp_path / "f3"
    cmd = [sys.executable, os.path.join(SCRIPTS, "train_backbone_966.py"),
           "--backbone", "nlinear", "--horizon", "24", "--seed", "42",
           "--profile", "author_966", "--containment", "strict",
           "--fold", "3", "--epochs", "1",
           "--export-dir", str(export), "--ckpt-dir", str(tmp_path / "ckpt")]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="-1")
    out = subprocess.run(cmd, capture_output=True, text=True,
                         cwd=PROJECT_ROOT, env=env)
    assert out.returncode == 0, out.stdout + out.stderr
    npz = export / "pred_nlinear_L24_s42.npz"
    assert npz.exists()
    d = np.load(npz, allow_pickle=True)
    assert int(d["fold"]) == 3
    f = wf.make_folds(N_ROWS, k=5)[2]
    assert int(d["fold_test_end"]) == f.test_end
    assert d["pred"].shape == (f.window_counts(104, 24)["n_test_windows"], 7, 24)
    manifest = export / "manifest_nlinear_L24_s42.json"
    assert manifest.exists()
    m = json.loads(manifest.read_text(encoding="utf-8"))
    assert m["fold"]["fold"] == 3
    assert m["fold"]["test_end"] == f.test_end
    assert m["config"]["split_source"] == "walk_forward_fold"


def test_backbone_runner_refuses_to_write_a_fold_cell_into_expanded_runs(tmp_path):
    cmd = [sys.executable, os.path.join(SCRIPTS, "train_backbone_966.py"),
           "--backbone", "nlinear", "--horizon", "24", "--seed", "42",
           "--profile", "author_966", "--containment", "strict",
           "--fold", "2", "--epochs", "1",
           "--export-dir", str(tmp_path / "expanded_runs" / "x")]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="-1")
    out = subprocess.run(cmd, capture_output=True, text=True,
                         cwd=PROJECT_ROOT, env=env)
    assert out.returncode != 0
    assert "refusing to write a fold cell under expanded_runs" in (out.stdout + out.stderr)


if __name__ == "__main__":       # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
