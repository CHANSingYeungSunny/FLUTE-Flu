"""
metrics.py — error metrics + the SINGLE literature peak criterion.
==================================================================

Two layers, matching the project's two-tier standard (§4 of the plan):

  1. Error metrics: MSE / MAE (z-space = PRIMARY, per the MIFlu paper §V-B;
     physical = supplementary).
  2. Peak acceptance: PTE = |predicted peak week - true peak week| (weeks),
     PIE = |predicted peak intensity - true peak intensity| / true peak
     intensity (%), and the ONLY hit criterion implemented here:

         peak hit  <=>  PTE <= 1 week  AND  PIE <= 25 %

  No project-custom thresholds (0.75 / 2.0wk / 20% / 0.60) are implemented or
  reported anywhere in this package.

DEFINITIONS FROZEN BEFORE COMPUTATION (revision 9) — see
`results/innovation/audit/peak_criteria_spec.md`:
  * target variable : ILITOTAL (physical patient counts, channel 4)
  * season boundary : MMWR week 40 of year Y .. week 20 of year Y+1
                      (weeks 21..39 are off-season and not scored)
  * peak            : argmax within the season window; TIES -> earliest week
  * incomplete      : a season with < 26 observed weeks is NOT scored
                      (status="incomplete_season"); its peaks are not counted
  * zero denominator: if the TRUE peak intensity is 0, PIE is undefined and is
                      reported as null (never 0.0); such a season is not a hit
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:  # scipy is present locally; degrade gracefully if not
    from scipy.signal import find_peaks
    _HAVE_SCIPY = True
except Exception:  # pragma: no cover
    find_peaks = None
    _HAVE_SCIPY = False

# ── the one and only acceptance threshold set ───────────────────────────────
PEAK_PTE_MAX_WEEKS = 1
PEAK_PIE_MAX_PCT = 25.0

# ── season definitions (frozen) ─────────────────────────────────────────────
SEASON_START_WEEK = 40          # first week of an influenza season
SEASON_END_WEEK = 20            # last week of an influenza season
MIN_SEASON_WEEKS = 26           # fewer observed weeks => incomplete, not scored


# ── basic errors ────────────────────────────────────────────────────────────
def mse(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return float(np.mean((a - b) ** 2))


def mae(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return float(np.mean(np.abs(a - b)))


# ── peak detection (mirror of compute_miflu_indicators.detect_peaks) ────────
def detect_peaks(values, prominence_frac: float = 0.08, distance: int = 8):
    """Same prominence/distance applied to BOTH series (fair comparison)."""
    values = np.asarray(values, dtype=float)
    if not _HAVE_SCIPY or len(values) == 0:
        return np.array([], dtype=int)
    prom = prominence_frac * (values.max() - values.min())
    if prom <= 0:
        return np.array([], dtype=int)
    idx, _ = find_peaks(values, prominence=prom, distance=distance)
    return idx


# ── lead-time aggregation (mirror of aggregate_lead_time fixed_step) ────────
def aggregate_fixed_step(df: pd.DataFrame, step: int = 0,
                         gt_col: str = "ground_truth_ili_phys",
                         pred_col: str = "prediction_ili_phys") -> pd.DataFrame:
    """Keep ONLY forecast step == `step`; collapse overlapping windows.

    Mirrors `compute_miflu_indicators.aggregate_lead_time(mode="fixed_step")`
    exactly (groupby abs_week, mean gt/pred, first calendar). Every point then
    has a CONSTANT lead time of (step+1) weeks — no cross-lead mixing.
    """
    if gt_col not in df.columns or pred_col not in df.columns:
        raise KeyError(f"aggregate needs '{gt_col}' / '{pred_col}'")
    d = df.copy()
    if "week_start_date" in d.columns:
        d["week_start_date"] = pd.to_datetime(d["week_start_date"])
    d = d[d["step"] == int(step)]
    if d.empty:
        raise ValueError(f"no rows with step == {step}")
    grp = d.groupby("abs_week").agg(gt=(gt_col, "mean"), pred=(pred_col, "mean"),
                                    n_windows=(pred_col, "size")).sort_index()
    for col in ("epiweek", "week_start_date"):
        if col in d.columns:
            grp[col] = d.groupby("abs_week")[col].first()
    grp = grp.reset_index()
    ordered = (["abs_week"] + [c for c in ("epiweek", "week_start_date")
                               if c in grp.columns] + ["gt", "pred", "n_windows"])
    grp.attrs["lead_mode"] = "fixed_step"
    grp.attrs["lead_step"] = int(step)
    return grp[ordered]


def split_frame(df: pd.DataFrame, split: str) -> pd.DataFrame:
    if "split" not in df.columns:
        raise KeyError("prediction frame has no `split` column")
    return df[df["split"] == split].copy()


# ── season utilities ────────────────────────────────────────────────────────
def season_start_year(epiweek: int):
    """Season label for a YYYYWW epiweek; None for off-season (weeks 21..39)."""
    y, w = int(epiweek) // 100, int(epiweek) % 100
    if w >= SEASON_START_WEEK:
        return y
    if w <= SEASON_END_WEEK:
        return y - 1
    return None


def season_bounds(season_year: int) -> tuple[int, int]:
    """(first_epiweek, last_epiweek) of the season starting in `season_year`."""
    return season_year * 100 + SEASON_START_WEEK, (season_year + 1) * 100 + SEASON_END_WEEK


# ── series-level peaks (used ONLY for the numeric regression cross-check) ───
def series_peak_metrics(gt, pred, match_tol: int = 2) -> dict:
    """Whole-series peaks, mirroring compute_miflu_indicators.compute_peak_indicators.

    This exists so `tests/innovation/test_numeric_regression.py` can prove the
    innovation metrics layer reproduces the EXISTING pipeline bit-for-bit on the
    same series. The REPORTED peak criterion is `seasonal_peak_metrics`, not this.
    """
    gt = np.asarray(gt, dtype=float)
    pred = np.asarray(pred, dtype=float)
    true_pk = detect_peaks(gt)
    pred_pk = detect_peaks(pred)
    deltas, rels = [], []
    for ti in true_pk:
        best, best_d = None, None
        for pj in pred_pk:
            d = abs(int(pj) - int(ti))
            if d <= match_tol and (best_d is None or d < best_d):
                best, best_d = int(pj), d
        if best is not None:
            deltas.append(abs(best - int(ti)))
            if gt[ti] > 0:
                rels.append(abs(pred[best] - gt[ti]) / gt[ti] * 100.0)
    return {
        "n_true_peaks": int(len(true_pk)),
        "n_hit": int(len(deltas)),
        "peak_hit_count": f"{len(deltas)}/{len(true_pk)}",
        "peak_timing_error_weeks": (float(np.mean(deltas)) if deltas else None),
        "mean_peak_magnitude_rel_err_pct": (float(np.mean(rels)) if rels else None),
    }


# ── seasonal peaks — THE reported literature criterion ──────────────────────
def seasonal_peak_metrics(series: pd.DataFrame,
                          epiweek_col: str = "epiweek",
                          absweek_col: str = "abs_week",
                          gt_col: str = "gt", pred_col: str = "pred"):
    """Per-season peak timing/intensity error with the literature hit criterion.

    Returns (by_season_df, agg). `series` is the output of
    `aggregate_fixed_step(...)`.

    Handling rules (all frozen, see peak_criteria_spec.md):
      * off-season weeks (21..39) excluded;
      * a season with < MIN_SEASON_WEEKS observed weeks -> status
        "incomplete_season", not scored;
      * gt peak value <= 0 -> status "zero_denominator", PIE = null, not a hit;
      * ties at the maximum -> earliest week wins (np.argmax semantics).
    """
    if epiweek_col not in series.columns:
        raise KeyError("seasonal_peak_metrics needs an `epiweek` column")
    d = series.copy()
    d["season"] = [season_start_year(e) for e in d[epiweek_col]]
    rows = []
    for season, g in d[d["season"].notna()].groupby("season"):
        g = g.sort_values(absweek_col)
        n_weeks = int(len(g))
        if n_weeks < MIN_SEASON_WEEKS:
            rows.append({"season": int(season), "n_weeks": n_weeks,
                         "status": "incomplete_season", "hit": False,
                         "gt_peak_week": np.nan, "gt_peak_value": np.nan,
                         "pred_peak_week": np.nan, "pred_peak_value": np.nan,
                         "pte_weeks": None, "pie_pct": None})
            continue
        gi = int(np.argmax(g[gt_col].to_numpy()))       # ties -> earliest
        pi = int(np.argmax(g[pred_col].to_numpy()))
        gtw = int(g[absweek_col].iloc[gi])
        pw = int(g[absweek_col].iloc[pi])
        gtv = float(g[gt_col].iloc[gi])
        pv = float(g[pred_col].iloc[pi])
        pte = abs(pw - gtw)
        if gtv > 0:
            pie = abs(pv - gtv) / gtv * 100.0
            status = "evaluable"
        else:
            pie = None
            status = "zero_denominator"
        hit = bool(pte <= PEAK_PTE_MAX_WEEKS and pie is not None
                   and pie <= PEAK_PIE_MAX_PCT)
        rows.append({"season": int(season), "n_weeks": n_weeks, "status": status,
                     "hit": hit, "gt_peak_week": gtw, "gt_peak_value": gtv,
                     "pred_peak_week": pw, "pred_peak_value": pv,
                     "pte_weeks": int(pte), "pie_pct": (float(pie) if pie is not None else None)})

    by_season = pd.DataFrame(rows)
    ev = by_season[by_season["status"] == "evaluable"] if len(by_season) else by_season
    n_eval = int(len(ev))
    n_hit = int(ev["hit"].sum()) if n_eval else 0
    agg = {
        "n_seasons_total": int(len(by_season)),
        "n_seasons_evaluable": n_eval,
        "n_seasons_incomplete": int((by_season["status"] == "incomplete_season").sum())
        if len(by_season) else 0,
        "n_hits": n_hit,
        "peak_hit_ratio": (float(n_hit / n_eval) if n_eval else None),
        "mean_pte_weeks": (float(ev["pte_weeks"].mean()) if n_eval else None),
        "mean_pie_pct": (float(ev["pie_pct"].dropna().mean())
                         if n_eval and ev["pie_pct"].notna().any() else None),
        "thresholds": {"PTE_max_weeks": PEAK_PTE_MAX_WEEKS,
                       "PIE_max_pct": PEAK_PIE_MAX_PCT},
    }
    return by_season, agg


# ── full metric bundle for one split ────────────────────────────────────────
def evaluate_predictions(pred_df: pd.DataFrame, split: str,
                         scaler=None, step: int = 0) -> dict:
    """MSE/MAE (z + physical) + seasonal literature peak metrics for a split."""
    sub = split_frame(pred_df, split)
    z_gt = sub["ground_truth_ili"].to_numpy(float)
    z_pr = sub["prediction_ili"].to_numpy(float)
    p_gt = sub["ground_truth_ili_phys"].to_numpy(float)
    p_pr = sub["prediction_ili_phys"].to_numpy(float)

    out = {
        "split": split,
        "n_rows": int(len(sub)),
        "mse_all_z": mse(z_gt, z_pr),
        "mae_all_z": mae(z_gt, z_pr),
        "mse_ili_phys": mse(p_gt, p_pr),
        "mae_ili_phys": mae(p_gt, p_pr),
    }
    try:
        series = aggregate_fixed_step(sub, step=step,
                                      gt_col="ground_truth_ili_phys",
                                      pred_col="prediction_ili_phys")
        by_season, peak_agg = seasonal_peak_metrics(series)
        out["peak"] = peak_agg
    except Exception as e:  # short smoke windows may have no step==0 rows
        out["peak"] = {"error": str(e)}
    return out


if __name__ == "__main__":  # pragma: no cover
    print("[metrics] thresholds:", PEAK_PTE_MAX_WEEKS, "wk /",
          PEAK_PIE_MAX_PCT, "%")
    print("[metrics] season:", SEASON_START_WEEK, "->", SEASON_END_WEEK,
          "min_weeks:", MIN_SEASON_WEEKS)
    print("[metrics] season(202101)=", season_start_year(202101),
          " season(202047)=", season_start_year(202047),
          " season(202130)=", season_start_year(202130))
