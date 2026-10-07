#!/usr/bin/env python3
"""
scorer_acceptance_tests.py — proves the independent scorer REJECTS malformed
inputs and COMPUTES the required metrics correctly, before any F1 GPU time is
spent.

All arrays here are SYNTHETIC. No model result is simulated or fabricated; the
only purpose is to exercise the scorer's validation and arithmetic.

Drives `scripts/score_predictions_independent.py` by writing synthetic NPZ
artefacts into a temporary directory and calling its own functions.

Run:
    python scorer_acceptance_tests.py
"""
from __future__ import annotations

import importlib.util
import io
import os
import shutil
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SCORER = os.path.join(PROJ, "scripts", "score_predictions_independent.py")

VAR_COLS = ["_WEIGHTED_ILI", "_UNWEIGHTED_ILI", "AGE_04", "AGE_524",
            "ILITOTAL", "NUM_OF_PROVIDERS", "OT"]


def load_scorer():
    """Load the HARDENED F1 scorer.

    The original `scripts/score_predictions_independent.py` is not used directly
    here because it raises on a shape mismatch instead of rejecting it (see
    F1_SCORER_ACCEPTANCE_TESTS.md). `scorer_f1.py` validates first and delegates
    the arithmetic to the original, so the metrics are still the original's.
    """
    spec = importlib.util.spec_from_file_location(
        "_scorer_f1", os.path.join(HERE, "scorer_f1.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.load_cell = mod.load_cell_validated      # uniform call site
    return mod


def write_npz(dirpath, model, L, seed, n_origins=20, n_vars=7, nan=False,
              inf=False, var_cols=None, space="standardized_train_fit_z",
              profile="author_966", containment="strict", dup_suffix="",
              seed_label=None, horizon_label=None):
    pred = np.random.RandomState(0).randn(n_origins, n_vars, L).astype(np.float32)
    targ = np.random.RandomState(1).randn(n_origins, n_vars, L).astype(np.float32)
    if nan:
        pred[0, 0, 0] = np.nan
    if inf:
        pred[1, 0, 0] = np.inf
    p = os.path.join(dirpath, f"pred_{model}_L{L}_s{seed}{dup_suffix}.npz")
    np.savez_compressed(
        p, pred=pred, target=targ,
        target_start_row=np.arange(n_origins, dtype=np.int32) + 700,
        L=np.int32(horizon_label if horizon_label is not None else L),
        seed=np.int32(seed_label if seed_label is not None else seed),
        var_cols=np.array(var_cols if var_cols is not None else VAR_COLS),
        train_mean=np.zeros((1, n_vars), np.float32),
        train_std=np.ones((1, n_vars), np.float32),
        model=model, profile=profile, containment=containment, space=space)
    return p


def main():
    scorer = load_scorer()
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}"
              + (f"  -- {detail}" if detail else ""))

    tmp = tempfile.mkdtemp(prefix="f1_scorer_accept_")
    try:
        print("=" * 74)
        print("SCORER ACCEPTANCE TESTS  (all arrays SYNTHETIC - no model results)")
        print("=" * 74)

        # ── A. REJECTION cases -------------------------------------------
        print("\nA. the scorer must REJECT malformed artefacts\n")

        # A1 missing pred/target
        p = os.path.join(tmp, "bad_missing.npz")
        np.savez_compressed(p, seed=np.int32(42), L=np.int32(24))
        rec, errs = scorer.load_cell(p)
        check("A1 missing prediction arrays rejected", rec is None and len(errs) > 0,
              errs[0] if errs else "")

        d1 = tempfile.mkdtemp(dir=tmp)
        p = write_npz(d1, "m", 24, 42, n_vars=6)
        rec, errs = scorer.load_cell(p)
        check("A2 wrong variable count rejected",
              any("expected 7 variables" in e for e in errs), errs[0] if errs else "")

        d2 = tempfile.mkdtemp(dir=tmp)
        p = write_npz(d2, "m", 24, 42, nan=True)
        rec, errs = scorer.load_cell(p)
        check("A3 NaN rejected", any("non-finite" in e for e in errs), errs[0] if errs else "")

        d3 = tempfile.mkdtemp(dir=tmp)
        p = write_npz(d3, "m", 24, 42, inf=True)
        rec, errs = scorer.load_cell(p)
        check("A4 Inf rejected", any("non-finite" in e for e in errs), errs[0] if errs else "")

        # A5 shape mismatch
        d4 = tempfile.mkdtemp(dir=tmp)
        p = os.path.join(d4, "pred_m_L24_s42.npz")
        np.savez_compressed(p, pred=np.zeros((5, 7, 24), np.float32),
                            target=np.zeros((4, 7, 24), np.float32),
                            L=np.int32(24), seed=np.int32(42), model="m",
                            var_cols=np.array(VAR_COLS))
        rec, errs = scorer.load_cell(p)
        check("A5 pred/target shape mismatch rejected",
              any("!=" in e for e in errs), errs[0] if errs else "")

        # A6 duplicate keys
        d5 = tempfile.mkdtemp(dir=tmp)
        write_npz(d5, "m", 24, 42, dup_suffix="")
        write_npz(d5, "m", 24, 42, dup_suffix="")   # same name overwrites...
        # create a genuine duplicate key under a different filename
        write_npz(d5, "m", 24, 42, dup_suffix="_copy")
        import glob
        cells = []
        for f in sorted(glob.glob(os.path.join(d5, "*.npz"))):
            r, e = scorer.load_cell(f)
            if r:
                cells.append(r)
        cov = scorer.coverage_report(cells, ["m"])
        check("A6 duplicate (model,L,seed) keys detected",
              len(cov["duplicated_keys"]) == 1,
              f"{len(cov['duplicated_keys'])} duplicated key group(s)")

        # A7 missing model relative to the expectation
        cov = scorer.coverage_report(cells, ["m", "never_trained"])
        check("A7 expected-but-absent model reported",
              cov["models_expected_but_absent"] == ["never_trained"],
              str(cov["models_expected_but_absent"]))

        # A8 mixed horizons cannot form a 4-horizon average
        d6 = tempfile.mkdtemp(dir=tmp)
        for L in (24, 36, 48):                     # 60 deliberately absent
            write_npz(d6, "m", L, 42)
        cs = []
        for f in sorted(glob.glob(os.path.join(d6, "*.npz"))):
            r, e = scorer.load_cell(f)
            if r:
                cs.append(r)
        agg = scorer.aggregate(cs)
        check("A8 incomplete horizon set yields NO aggregate", "m" not in agg,
              f"aggregate keys={list(agg)}")

        # A9 mixed seed counts across horizons -> flagged unbalanced
        d7 = tempfile.mkdtemp(dir=tmp)
        for L in (24, 36, 48, 60):
            write_npz(d7, "m", L, 42)
            if L == 24:                            # extra seed on ONE horizon only
                write_npz(d7, "m", L, 43, dup_suffix="_s43")
        cs = []
        for f in sorted(glob.glob(os.path.join(d7, "*.npz"))):
            r, e = scorer.load_cell(f)
            if r:
                cs.append(r)
        agg = scorer.aggregate(cs)
        check("A9 unbalanced seed counts flagged",
              agg.get("m", {}).get("seeds_balanced") is False,
              str(agg.get("m", {}).get("L_seed_counts")))

        # A10 Historical Track B artefacts are REJECTED outright
        d8 = tempfile.mkdtemp(dir=tmp)
        p = write_npz(d8, "m", 24, 42, profile="historical_track_b", containment="start")
        rec, errs = scorer.load_cell(p)
        check("A10 Historical Track B artefact rejected",
              rec is None and any("Track B" in e for e in errs),
              errs[0] if errs else "NOT REJECTED")

        # A11 non-F1 scaling space rejected
        d9 = tempfile.mkdtemp(dir=tmp)
        p = write_npz(d9, "m", 24, 42, space="physical")
        rec, errs = scorer.load_cell(p)
        check("A11 incompatible scaling space rejected",
              rec is None and any("scaling space" in e for e in errs),
              errs[0] if errs else "NOT REJECTED")

        # A12 containment other than the F1 rule rejected
        d12 = tempfile.mkdtemp(dir=tmp)
        p = write_npz(d12, "m", 24, 42, containment="start")
        rec, errs = scorer.load_cell(p)
        check("A12 non-strict containment rejected",
              rec is None and any("containment" in e for e in errs),
              errs[0] if errs else "NOT REJECTED")

        # A13 Test-assisted checkpoint selection rejected
        d13 = tempfile.mkdtemp(dir=tmp)
        pr = np.zeros((2, 7, 24), np.float32); tg = np.zeros((2, 7, 24), np.float32)
        p = os.path.join(d13, "pred_m_L24_s42.npz")
        np.savez_compressed(p, pred=pr, target=tg, L=np.int32(24), seed=np.int32(42),
                            model="m", var_cols=np.array(VAR_COLS),
                            target_start_row=np.arange(2, dtype=np.int32),
                            train_mean=np.zeros((1, 7), np.float32),
                            train_std=np.ones((1, 7), np.float32),
                            profile="author_966", containment="strict",
                            space="standardized_train_fit_z",
                            checkpoint_selection="best TEST mse")
        rec, errs = scorer.load_cell(p)
        check("A13 Test-selected checkpoint metadata rejected",
              rec is None and any("Test-assisted" in e for e in errs),
              errs[0] if errs else "NOT REJECTED")

        # A14 missing variable keys rejected
        d14 = tempfile.mkdtemp(dir=tmp)
        p = os.path.join(d14, "pred_m_L24_s42.npz")
        np.savez_compressed(p, pred=pr, target=tg, L=np.int32(24), seed=np.int32(42),
                            model="m", target_start_row=np.arange(2, dtype=np.int32),
                            train_mean=np.zeros((1, 7), np.float32),
                            train_std=np.ones((1, 7), np.float32),
                            profile="author_966", containment="strict",
                            space="standardized_train_fit_z")
        rec, errs = scorer.load_cell(p)
        check("A14 missing variable keys rejected",
              rec is None and any("var_cols" in e for e in errs),
              errs[0] if errs else "NOT REJECTED")

        # A15 mixed seed identifiers across models in one horizon -> visible as
        #     distinct cells, so a pairing check can detect the mismatch
        d15 = tempfile.mkdtemp(dir=tmp)
        write_npz(d15, "m", 24, 42)
        write_npz(d15, "other", 24, 43)
        cs = []
        for f in sorted(glob.glob(os.path.join(d15, "*.npz"))):
            rr, ee = scorer.load_cell(f)
            if rr:
                cs.append(rr)
        import collections as _c
        seeds = _c.defaultdict(set)
        for cc in cs:
            seeds[cc["model"]].add(cc["seed"])
        check("A15 mixed seed identifiers across models detectable for pairing",
              seeds["m"] != seeds["other"], f"{dict(seeds)}")

        # ── B. CORRECTNESS cases -----------------------------------------
        print("\nB. the scorer must COMPUTE correctly\n")

        # B1 per-horizon MSE / MAE against a hand-computed value
        d10 = tempfile.mkdtemp(dir=tmp)
        pred = np.full((2, 7, 24), 1.0, np.float32)   # error 1.0 in EVERY cell
        targ = np.zeros((2, 7, 24), np.float32)
        p = os.path.join(d10, "pred_m_L24_s42.npz")
        np.savez_compressed(p, pred=pred, target=targ, L=np.int32(24),
                            seed=np.int32(42), model="m", var_cols=np.array(VAR_COLS),
                            target_start_row=np.arange(2, dtype=np.int32),
                            train_mean=np.zeros((1, 7), np.float32),
                            train_std=np.ones((1, 7), np.float32),
                            profile="author_966", containment="strict",
                            space="standardized_train_fit_z")
        r, e = scorer.load_cell(p)
        check("B1 MSE/MAE hand-computed (all-ones error -> 1.0/1.0)",
              abs(r["mse_all"] - 1.0) < 1e-6 and abs(r["mae_all"] - 1.0) < 1e-6,
              f"mse={r['mse_all']:.6f} mae={r['mae_all']:.6f}")

        # B2 per-variable decomposition
        check("B2 per-variable MSE list length == n_vars",
              len(r["per_variable_mse"]) == 7,
              f"{len(r['per_variable_mse'])} entries")

        # B3 per-lead decomposition
        check("B3 per-lead MSE list length == the lead dimension",
              len(r["per_lead_mse"]) == 24, f"{len(r['per_lead_mse'])} entries")

        # B4 equal-weight four-horizon average, hand-computed
        d11 = tempfile.mkdtemp(dir=tmp)
        for L, val in ((24, 1.0), (36, 2.0), (48, 3.0), (60, 4.0)):
            pr = np.full((2, 7, L), np.sqrt(val), np.float32)   # error^2 = val
            tg = np.zeros((2, 7, L), np.float32)
            np.savez_compressed(os.path.join(d11, f"pred_m_L{L}_s42.npz"),
                                pred=pr, target=tg, L=np.int32(L), seed=np.int32(42),
                                model="m", var_cols=np.array(VAR_COLS),
                                target_start_row=np.arange(2, dtype=np.int32),
                                train_mean=np.zeros((1, 7), np.float32),
                                train_std=np.ones((1, 7), np.float32),
                                profile="author_966", containment="strict",
                                space="standardized_train_fit_z")
        cs = []
        for f in sorted(glob.glob(os.path.join(d11, "*.npz"))):
            rr, ee = scorer.load_cell(f)
            if rr:
                cs.append(rr)
        agg = scorer.aggregate(cs)
        expected = (1.0 + 2.0 + 3.0 + 4.0) / 4
        got = agg["m"]["average_MSE_4L"]
        check("B4 equal-weight 4-horizon average (expect 2.5)", abs(got - expected) < 1e-6,
              f"got {got:.6f}, expected {expected:.6f}")
        check("B5 per-horizon values are kept separately (aggregation is the equal-weight "
              "mean of four horizon means, not a flat mean over cells)",
              abs(got - (1.0 + 2.0 + 3.0 + 4.0) / 4) < 1e-6
              and abs(agg["m"]["L_mse"][60] - 4.0) < 1e-6
              and abs(agg["m"]["L_mse"][24] - 1.0) < 1e-6,
              f"L_mse={ {k: round(v, 4) for k, v in agg['m']['L_mse'].items()} }")

        print("\n" + "=" * 74)
        npass = sum(1 for _, c, _ in results if c)
        print(f"RESULT: {npass}/{len(results)} checks passed")
        print("=" * 74)
        return 0 if npass == len(results) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())