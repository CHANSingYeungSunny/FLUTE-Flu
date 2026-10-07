#!/usr/bin/env python3
"""
naive_leakage_safe.py — leakage-safe naive references for the F1 pilot.

WHY THIS FILE EXISTS
--------------------
`scripts/train_naive_966.py::naive_predictions` computes the seasonal-naive
reference as

        ref = ts + s - SEASONAL_LAG

where `ts` is the FIRST TARGET row, so the forecast origin is `o = ts - 1`, and
`s` is the zero-based lead index. The guard in that file is

        assert ts + s - SEASONAL_LAG < ts + s

which is trivially true for any positive lag and therefore checks NOTHING about
whether the reference is available at the origin.

Verified consequence for the F1 horizons (SEASONAL_LAG = 52):

    L=24  leaking leads: none
    L=36  leaking leads: none
    L=48  leaking leads: none
    L=60  leaking leads: 8   (s = 52..59, referencing rows ts+0 .. ts+7)

Those referenced rows are ACTUAL TARGET ROWS inside the forecast window, i.e.
values that do not exist at the origin. `scripts/train_naive_966.py` is NOT
modified (append-only rule); this module supplies a corrected implementation and
a unit test that would fail on the old behaviour.

CORRECT DEFINITION (recovery plan, section "Forecast-window contract")
---------------------------------------------------------------------
For an origin at `o` and a 52-week seasonal lag, the repetition must come from
the LAST OBSERVED CYCLE only:

        pred[lead s] = y[o - 51 + (s mod 52)]

equivalently, in `ts` terms:

        ref = ts - 52 + (s mod 52)

which satisfies `ref <= ts - 1 = o` for every s >= 0, hence never reads a row
after the origin.

Handling of an insufficient history: if `ref < 0` the observation does not exist.
Silently clamping to row 0 (as the old code does) fabricates a forecast from the
first available row. This module makes the policy EXPLICIT and configurable, and
defaults to marking those leads INVALID rather than inventing a value, so the
scorer can exclude them instead of scoring a fabricated forecast.

Reporting: the 52/53-week epidemiological-year question is NOT resolved here.
The benchmark is defined on a ROW-based grid (see F1_TARGET_CONTRACT.md), so the
seasonal lag is 52 ROWS, not 52 epiweeks. This is declared, not assumed.
"""
from __future__ import annotations

import numpy as np

SEASONAL_LAG_ROWS = 52

# How to treat a lead whose reference row does not exist (ref < 0).
#   "invalid" (default) - the lead is marked invalid; the scorer must exclude it
#   "clamp_first"       - reproduce the legacy behaviour (forecast from row 0)
INSUFFICIENT_HISTORY_POLICY = "invalid"


def last_value(data_norm, ts, L, N):
    """Last-observation-carried-forward. Origin row is ts-1, always available."""
    last = data_norm[ts - 1]
    return np.repeat(last[:, None], L, axis=1).astype(np.float32), np.ones(L, bool)


def seasonal_naive(data_norm, ts, L, N, lag=SEASONAL_LAG_ROWS,
                   policy=INSUFFICIENT_HISTORY_POLICY):
    """52-row repeating forecast from the last observed cycle.

    Returns (pred, valid) where `valid` is a length-L boolean mask.
    """
    origin = ts - 1
    pred = np.zeros((N, L), dtype=np.float32)
    valid = np.ones(L, dtype=bool)
    for s in range(L):
        ref = ts - lag + (s % lag)
        if ref > origin:                      # must never happen; assert it
            raise AssertionError(
                f"leakage: ref={ref} > origin={origin} at lead {s} (L={L})")
        if ref < 0:
            if policy == "clamp_first":
                ref = 0
            else:
                valid[s] = False
                continue
        pred[:, s] = data_norm[ref]
    return pred, valid


def build_naive(data_norm, target_starts, mask, L, name, lag=SEASONAL_LAG_ROWS,
                policy=INSUFFICIENT_HISTORY_POLICY):
    """Vectorised wrapper mirroring the signature of the legacy helper.

    Returns (pred, target, valid_mask, n_invalid_leads)
      pred, target : (n_win, N, L)
      valid_mask   : (n_win, L)  - False where the forecast must not be scored
    """
    N = data_norm.shape[1]
    idx = np.where(mask)[0]
    ts_all = target_starts[idx]
    pred = np.zeros((len(idx), N, L), dtype=np.float32)
    target = np.zeros((len(idx), N, L), dtype=np.float32)
    valid = np.ones((len(idx), L), dtype=bool)
    n_invalid = 0
    for j, ts in enumerate(ts_all):
        target[j] = data_norm[ts:ts + L].T
        if name == "last_value_naive":
            p, v = last_value(data_norm, ts, L, N)
        elif name == "seasonal_naive":
            p, v = seasonal_naive(data_norm, ts, L, N, lag=lag, policy=policy)
        else:
            raise ValueError(f"unknown naive name {name!r}")
        pred[j], valid[j] = p, v
        n_invalid += int((~v).sum())
    return pred, target, valid, n_invalid


# ─────────────────────────────────────────────────────────────────────────────
def _self_test():
    """Synthetic unit test. Proves the corrected implementation never reads a
    row after the origin, and that the LEGACY formula would."""
    ok = True
    N, L = 3, 60
    n_rows = 400
    rng = np.random.RandomState(0)
    data = rng.randn(n_rows, N).astype(np.float32)
    ts = 300                      # target rows 300..359; origin = 299

    print("=" * 68)
    print("naive_leakage_safe self-test  (SYNTHETIC arrays, not model results)")
    print("=" * 68)

    # 1. seasonal naive: no reference may exceed the origin
    pred, valid = seasonal_naive(data, ts, L, N)
    refs = [ts - SEASONAL_LAG_ROWS + (s % SEASONAL_LAG_ROWS) for s in range(L)]
    worst = max(refs)
    print(f"\n[1] seasonal_naive refs: min={min(refs)} max={worst} origin={ts-1}")
    c1 = worst <= ts - 1
    print(f"    {'PASS' if c1 else 'FAIL'}: every reference <= origin")
    ok &= c1

    # 2. values must equal the referenced rows exactly
    c2 = all(np.allclose(pred[:, s], data[refs[s]]) for s in range(L))
    print(f"[2] {'PASS' if c2 else 'FAIL'}: predictions equal the referenced rows")
    ok &= c2

    # 3. the LEGACY formula leaks at L=60 - demonstrate it
    legacy_refs = [ts + s - SEASONAL_LAG_ROWS for s in range(L)]
    leaks = [s for s, r in enumerate(legacy_refs) if r >= ts]
    print(f"[3] legacy formula leaking leads at L=60: {leaks[:8]}... n={len(leaks)}")
    c3 = len(leaks) == 8
    print(f"    {'PASS' if c3 else 'FAIL'}: 8 leaking leads reproduced (s=52..59)")
    ok &= c3

    # 4. last_value uses the origin row only
    lv, lv_valid = last_value(data, ts, L, N)
    c4 = np.allclose(lv, np.repeat(data[ts - 1][:, None], L, axis=1))
    print(f"[4] {'PASS' if c4 else 'FAIL'}: last_value repeats the origin row")
    ok &= c4

    # 5. insufficient history -> those leads are marked INVALID rather than
    #    fabricated from row 0. With ts=10 (origin 9) and lag 52:
    #      ref = -42 + (s mod 52); valid iff ref >= 0 iff (s mod 52) >= 42
    #      => s in {42..51} valid (10 leads), everything else invalid (50 leads)
    p5, v5 = seasonal_naive(data, 10, 60, N)
    n_valid, n_invalid = int(v5.sum()), int((~v5).sum())
    c5 = (n_valid == 10 and n_invalid == 50
          and np.allclose(p5[:, ~v5], 0)          # invalid slots stay zero
          and all(np.allclose(p5[:, s], data[10 - 52 + (s % 52)])
                  for s in range(60) if v5[s]))
    print(f"[5] {'PASS' if c5 else 'FAIL'}: insufficient history -> {n_invalid} leads "
          f"INVALID, {n_valid} valid, no clamped fabrication")
    ok &= c5

    # 6. structural safety: with the (s mod lag) formulation, ref <= origin for
    #    EVERY lag >= 1 and every lead, so the internal leakage guard is
    #    unreachable by construction. Verify by exhaustion rather than by trying
    #    to trigger it.
    worst_all = None
    for lag in (1, 2, 7, 12, 52, 53, 104):
        for s in range(60):
            r = ts - lag + (s % lag)
            assert r <= ts - 1, (lag, s, r)
            worst_all = r if worst_all is None else max(worst_all, r)
    c6 = worst_all <= ts - 1
    print(f"[6] {'PASS' if c6 else 'FAIL'}: ref <= origin for all lags in "
          f"(1,2,7,12,52,53,104) x leads 0..59 -> formula is safe by construction")
    ok &= c6

    print("\n" + "=" * 68)
    print("ALL TESTS PASS" if ok else "SOME TESTS FAILED")
    print("=" * 68)
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())