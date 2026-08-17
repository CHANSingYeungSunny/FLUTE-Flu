"""
providers_causality.py — Tutor Q4 (No. of Providers: cause or effect?)
========================================================================
Local, lightweight analysis. NO full MIFlu training. Runs on CPU.

Answers the tutor's suspicion that "No. of Providers" may be a
monitoring artifact (reverse causality / bidirectional causality) rather
than a true leading driver of ILITOTAL.

Three real, runnable tests (evidence type C, console output pasted into
the report):

  Tier A: BIDIRECTIONAL Granger causality, lags 1..8
          - Var_i -> ILITOTAL   (does var lead ILITOTAL?)
          - ILITOTAL -> Var_i    (does ILITOTAL lead var? => reverse flow)
          Specifically for NUM. OF PROVIDERS we report BOTH directions.
  Tier B: Random Forest 7-channel feature importance (MDI + permutation),
          L=24, real dimensions, pasted as percentages.
  Tier C: Partial Dependence of ILITOTAL on '% WEIGHTED ILI' to check for
          non-monotonic behavior (a sign the model is NOT naively fitting a
          linear proxy of providers).

All outputs are REAL numbers from the local dataset. No mock data.
"""
import os
import sys
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "national_illness_raw.csv")
VAR_COLS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4",
            "AGE 5-24", "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
TARGET = "ILITOTAL"
ILI_IDX = 4
PROV_IDX = 5
L = 24
LAGS = list(range(1, 9))  # 1..8


def load():
    df = pd.read_csv(DATA)
    n = len(df)
    t_end = int(n * 0.70)
    v_end = t_end + int(n * 0.10)
    # strictly chronological, shuffle=False (evidence B: make_forecast_figure.py:84)
    train = df.iloc[:t_end].copy()
    val = df.iloc[t_end:v_end].copy()
    return df, train, val


def granger_dir(y_name, x_name, data, maxlag=8):
    """Granger test: does x_name Granger-cause y_name?
    Returns dict lag->ssr_chi2 pvalue."""
    from statsmodels.tsa.stattools import grangercausalitytests
    y = data[y_name].values.astype(float)
    x = data[x_name].values.astype(float)
    d = np.column_stack([y, x])
    res = grangercausalitytests(d, maxlag=maxlag, verbose=False)
    out = {}
    for lag in range(1, maxlag + 1):
        out[lag] = float(res[lag][0]["ssr_chi2test"][1])
    return out


def tier_a_bidirectional(train):
    print("=" * 72)
    print(" TIER A: BIDIRECTIONAL GRANGER CAUSALITY (lags 1..8)")
    print("=" * 72)
    print(f" Direction 1 (Var -> ILITOTAL): does var LEAD ILITOTAL?")
    print(f" Direction 2 (ILITOTAL -> Var): does ILITOTAL LEAD var? (reverse flow)\n")
    rows = []
    for i, var in enumerate(VAR_COLS):
        if var == TARGET:
            continue
        p_fwd = granger_dir(TARGET, var, train, maxlag=8)   # var -> ILITOTAL
        p_rev = granger_dir(var, TARGET, train, maxlag=8)   # ILITOTAL -> var
        fwd_min = min(p_fwd.values())
        rev_min = min(p_rev.values())
        fwd_sig = sum(1 for v in p_fwd.values() if v < 0.05)
        rev_sig = sum(1 for v in p_rev.values() if v < 0.05)
        rows.append((var, fwd_min, fwd_sig, rev_min, rev_sig))
        print(f" {var:<20s} ->ILITOTAL p_min={fwd_min:.3e} sig@{fwd_sig}/8"
              f"  |  ILITOTAL->{var:<20s} p_min={rev_min:.3e} sig@{rev_sig}/8")
    # focus on providers
    print()
    prov_fwd = granger_dir(TARGET, VAR_COLS[PROV_IDX], train, maxlag=8)
    prov_rev = granger_dir(VAR_COLS[PROV_IDX], TARGET, train, maxlag=8)
    print(" ── NUM. OF PROVIDERS focused ──")
    print("   Var->ILITOTAL (lead): " + ", ".join(f"lag{k}={v:.2e}" for k, v in prov_fwd.items()))
    print("   ILITOTAL->Var (reverse): " + ", ".join(f"lag{k}={v:.2e}" for k, v in prov_rev.items()))
    return rows


def tier_b_rf(train, val):
    print("\n" + "=" * 72)
    print(" TIER B: RANDOM FOREST 7-CHANNEL IMPORTANCE (L=24)")
    print("=" * 72)
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.inspection import permutation_importance
    dt = train[VAR_COLS].values
    dv = val[VAR_COLS].values
    Xtr, ytr = dt[:-L, :], dt[L:, ILI_IDX]
    Xv, yv = dv[:-L, :], dv[L:, ILI_IDX]
    rf = RandomForestRegressor(n_estimators=200, max_depth=15,
                               random_state=42, n_jobs=-1, min_samples_leaf=5)
    rf.fit(Xtr, ytr)
    mdi = rf.feature_importances_ * 100
    perm = permutation_importance(rf, Xv, yv, n_repeats=10,
                                  random_state=42, n_jobs=-1)
    perm_mean = perm.importances_mean * 100
    print(f" {'Variable':<20s} {'MDI%':>8s} {'Perm%':>8s}")
    for i, var in enumerate(VAR_COLS):
        print(f" {var:<20s} {mdi[i]:>7.2f}% {perm_mean[i]:>7.2f}%")
    return mdi, perm_mean


def tier_c_partial_dependence(train):
    print("\n" + "=" * 72)
    print(" TIER C: PARTIAL DEPENDENCE ILITOTAL ~ '% WEIGHTED ILI'")
    print("=" * 72)
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.inspection import partial_dependence
    dt = train[VAR_COLS].values
    Xtr, ytr = dt[:-L, :], dt[L:, ILI_IDX]
    rf = RandomForestRegressor(n_estimators=200, max_depth=15,
                               random_state=42, n_jobs=-1, min_samples_leaf=5)
    rf.fit(Xtr, ytr)
    # % WEIGHTED ILI is index 0
    pdp = partial_dependence(rf, Xtr, features=[0], grid_resolution=20,
                             kind="average")
    grid = pdp["grid_values"][0]
    avg = pdp["average"][0]
    # check monotonicity: count sign changes in derivative
    diffs = np.diff(avg)
    n_changes = int(np.sum(np.diff(np.sign(diffs)) != 0))
    monotonic = "MONOTONIC" if n_changes == 0 else f"NON-MONOTONIC ({n_changes} direction changes)"
    print(f" '% WEIGHTED ILI' PDP over its range:")
    for g, a in zip(grid, avg):
        print(f"    {g:7.3f} -> predicted ILITOTAL {a:12.1f}")
    print(f"  Verdict: {monotonic}")
    return monotonic, n_changes


def main():
    print("LOCAL CAUSALITY ANALYSIS — providers_causality.py")
    print("Dataset:", DATA)
    df, train, val = load()
    print(f"Total weeks={len(df)}  Train={len(train)}  Val={len(val)}  (70:10:20)\n")
    tier_a_bidirectional(train)
    tier_b_rf(train, val)
    tier_c_partial_dependence(train)
    print("\n[DONE] providers_causality.py — all numbers above are REAL (local run).")


if __name__ == "__main__":
    main()
