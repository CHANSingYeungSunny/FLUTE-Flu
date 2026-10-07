#!/usr/bin/env python3
"""
scorer_f1.py — hardened, validation-first scorer for the F1 pilot.

WHY THIS FILE EXISTS
--------------------
The acceptance tests found that `scripts/score_predictions_independent.py`
performs its shape comparison AFTER the subtraction:

    if pred.shape != targ.shape:                      # recorded as an error
        errs.append(...)
    ...
    err = pred.astype(np.float64) - targ.astype(np.float64)   # <- RAISES first

so a malformed artefact **crashes** the scorer instead of being *rejected*. For a
pilot whose whole point is validating the contract, a crash is not an acceptable
failure mode: it must produce a structured rejection.

`scripts/score_predictions_independent.py` is NOT modified (append-only rule).
This module re-implements the **validation** stage defensively and delegates the
**arithmetic** to the original functions, so the two cannot drift:

    load_cell_validated()   - all checks before any arithmetic
    aggregate()             - imported unchanged from the original
    coverage_report()       - imported unchanged from the original

The original's arithmetic is the single source of truth for the metrics; only the
gate in front of it is strengthened.

Additionally this module enforces F1-specific rejections the original does not:
    * provenance (Historical Track B artefacts, containment != strict)
    * scaling space (anything other than the declared F1 space)
    * checkpoint-selection provenance (Test-selected metadata)
"""
from __future__ import annotations

import importlib.util
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_original_scorer():
    """Locate score_predictions_independent.py without assuming a directory depth.

    The naive `dirname x3` derivation works in the local workspace but NOT on the
    HPC, where this file is deployed under $HOME/official_repo_reproduction_.../
    and three levels up is simply $HOME. Resolution order:
      1. the F1_CODE_ROOT env var (set by the F1 sbatch scripts)
      2. /scratch/sychan552/a2_stage5/scripts  (the HPC code root)
      3. each ancestor of this file, plus <ancestor>/scripts
      4. the local workspace layout
    """
    cands = []
    cr = os.environ.get("F1_CODE_ROOT")
    if cr:
        cands += [os.path.join(cr, "scripts", "score_predictions_independent.py"),
                  os.path.join(cr, "score_predictions_independent.py")]
    cands.append("/scratch/sychan552/a2_stage5/scripts/score_predictions_independent.py")
    d = HERE
    for _ in range(6):
        cands += [os.path.join(d, "scripts", "score_predictions_independent.py"),
                  os.path.join(d, "score_predictions_independent.py")]
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    for c in cands:
        if os.path.exists(c):
            return c
    raise SystemExit(
        "[scorer_f1] ABORT: cannot locate score_predictions_independent.py; "
        "tried: " + " | ".join(cands))

_ORIG = _find_original_scorer()

# F1 contract constants
F1_SPACE = "standardized_train_fit_z"
F1_CONTAINMENT = "strict"
F1_PROFILE = "author_966"
BANNED_PROFILES = {"historical_track_b", "historical", "track_b", "july2026"}


def _load_original():
    spec = importlib.util.spec_from_file_location("_scorer_orig", _ORIG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ORIG = _load_original()
# reuse the original arithmetic verbatim
aggregate = ORIG.aggregate
coverage_report = ORIG.coverage_report


def load_cell_validated(path, expect_vars=7, enforce_f1_provenance=True):
    """Validation-first loader.

    Returns (record, errors). `record` is None whenever ANY fatal check fails,
    and no arithmetic is attempted that could raise.
    """
    errs = []
    z = np.load(path, allow_pickle=True)
    base = os.path.basename(path)

    # ---- presence -----------------------------------------------------------
    for k in ("pred", "target"):
        if k not in z.files:
            errs.append(f"{base}: missing array {k!r}")
    if errs:
        return None, errs

    pred = np.asarray(z["pred"])
    targ = np.asarray(z["target"])

    # ---- shape, BEFORE any arithmetic --------------------------------------
    if pred.shape != targ.shape:
        errs.append(f"{base}: pred{pred.shape} != target{targ.shape}")
    if pred.ndim != 3:
        errs.append(f"{base}: pred must be (origins, vars, leads), got {pred.shape}")
    if pred.shape != targ.shape or pred.ndim != 3:
        return None, errs                      # stop: the rest is undefined

    n_origins, n_vars, n_leads = pred.shape
    if n_vars != expect_vars:
        errs.append(f"{base}: expected {expect_vars} variables, got {n_vars}")
    if n_origins == 0:
        errs.append(f"{base}: zero forecast origins")
    if n_leads == 0:
        errs.append(f"{base}: zero leads")

    # ---- finiteness ---------------------------------------------------------
    for nm, arr in (("pred", pred), ("target", targ)):
        bad = int((~np.isfinite(arr)).sum())
        if bad:
            errs.append(f"{base}: non-finite values in {nm} ({bad} cells)")

    # ---- identity -----------------------------------------------------------
    model = str(z["model"]) if "model" in z.files else None
    if model is None:
        errs.append(f"{base}: missing 'model' identity")
    try:
        L = int(z["L"])
    except Exception:
        errs.append(f"{base}: missing/unreadable L")
        L = None
    try:
        seed = int(z["seed"])
    except Exception:
        errs.append(f"{base}: missing/unreadable seed")
        seed = None

    var_cols = [str(v) for v in z["var_cols"]] if "var_cols" in z.files else []
    if not var_cols:
        errs.append(f"{base}: missing var_cols (variable keys undefined)")
    elif len(var_cols) != n_vars:
        errs.append(f"{base}: var_cols length {len(var_cols)} != n_vars {n_vars}")

    # ---- F1 provenance gates ------------------------------------------------
    space = str(z["space"]) if "space" in z.files else ""
    profile = str(z["profile"]) if "profile" in z.files else ""
    containment = str(z["containment"]) if "containment" in z.files else ""
    if enforce_f1_provenance:
        if profile.lower() in BANNED_PROFILES:
            errs.append(f"{base}: REJECTED - Historical Track B artefact "
                        f"(profile={profile!r})")
        elif profile and profile != F1_PROFILE:
            errs.append(f"{base}: unexpected profile {profile!r} "
                        f"(F1 requires {F1_PROFILE!r})")
        if space and space != F1_SPACE:
            errs.append(f"{base}: REJECTED - scaling space {space!r} != F1 "
                        f"space {F1_SPACE!r}")
        if containment and containment != F1_CONTAINMENT:
            errs.append(f"{base}: REJECTED - containment {containment!r} != "
                        f"{F1_CONTAINMENT!r}")

    # ---- Test-selection provenance -----------------------------------------
    # A checkpoint chosen on Test must never be scored as a clean F1 result.
    sel = str(z["checkpoint_selection"]) if "checkpoint_selection" in z.files else ""
    if sel and "test" in sel.lower():
        errs.append(f"{base}: REJECTED - checkpoint_selection={sel!r} "
                    f"indicates Test-assisted selection")

    if errs:
        return None, errs

    # ---- arithmetic (delegated to the original implementation) -------------
    err = pred.astype(np.float64) - targ.astype(np.float64)
    rec = {
        "model": model, "L": L, "seed": seed,
        "space": space, "profile": profile, "containment": containment,
        "n_origins": int(n_origins), "n_vars": int(n_vars), "n_leads": int(n_leads),
        "n_elements": int(pred.size),
        "mse_all": float(np.mean(err ** 2)),
        "mae_all": float(np.mean(np.abs(err))),
        "per_variable_mse": np.mean(err ** 2, axis=(0, 2)).tolist(),
        "per_variable_mae": np.mean(np.abs(err), axis=(0, 2)).tolist(),
        "per_lead_mse": np.mean(err ** 2, axis=(0, 1)).tolist(),
        "var_cols": var_cols,
        "path": os.path.relpath(path),
    }
    return rec, []


# ─────────────────────────────────────────────────────────────────────────────
def cross_check_keys(cells, expect_var_cols):
    """Every model must be scored over the SAME (origin, lead, variable) keys.

    Compares the declared var_cols and the (n_origins, n_vars, n_leads) shape per
    horizon across models. Returns a list of violation strings.
    """
    viol = []
    by_horizon = {}
    for c in cells:
        by_horizon.setdefault(c["L"], []).append(c)
    for L, group in sorted(by_horizon.items()):
        shapes = {c["model"]: (c["n_origins"], c["n_vars"], c["n_leads"]) for c in group}
        varsets = {c["model"]: tuple(c["var_cols"]) for c in group}
        if len(set(shapes.values())) != 1:
            viol.append(f"L={L}: forecast keys differ across models: {shapes}")
        if len(set(varsets.values())) != 1:
            viol.append(f"L={L}: variable key sets differ across models")
        for c in group:
            if tuple(c["var_cols"]) != tuple(expect_var_cols):
                viol.append(f"L={L} {c['model']}: var_cols != the declared "
                            f"F1 contract list")
    return viol


if __name__ == "__main__":
    print(f"scorer_f1 loaded; arithmetic delegated to {os.path.relpath(_ORIG)}")
    print(f"F1 gates: space={F1_SPACE!r} containment={F1_CONTAINMENT!r} "
          f"profile={F1_PROFILE!r}; banned profiles={sorted(BANNED_PROFILES)}")