"""gap_consequence_check.py — Stage 3 §2 static check (CPU-only, no training).

Corrects the earlier (flawed) gap analysis that treated week-53 label
transitions as real calendar gaps. The authoritative calendar is
`scripts/cdc_calendar.py`: it canonicalises week-53 labels and reports the ONE
real missing-week hole (2002 w21..w39, 19 weeks, at abs_week 20).

For each dataset (project 1025-row raw, author 966-row paper_exact) and each
horizon L in {24,36,48,60}, report, per split:
  * total eligible origins
  * origins whose T=104 input window crosses a REAL calendar gap
  * origins whose target window crosses a REAL calendar gap
  * origins whose nominal lead (L) != elapsed calendar weeks between input-end
    and target-end
  * seasonal-naive lag-52 validity (target row t vs reference row t-52)
"""
from __future__ import annotations
import os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from cdc_calendar import canonicalize_epiweeks, mmwr_week_start  # noqa: E402

T = 104
HORIZONS = [24, 36, 48, 60]


def calendar_for(path):
    raw = pd.read_csv(path)
    ew = raw["epiweek"].astype(int).tolist()
    canon, offset_anoms = canonicalize_epiweeks(ew)
    dates = pd.to_datetime([mmwr_week_start(y, w) for y, w in canon])
    # real gaps: canonical date jumps by more than 7 days
    gap_rows = [i for i in range(1, len(dates))
                if (dates[i] - dates[i - 1]).days > 7]
    return dates, gap_rows, len(ew), len(offset_anoms)


def gap_consequences(path, label, train_end, val_end):
    dates, gap_rows, n, n_label_off = calendar_for(path)
    print(f"\n=== {label} ===")
    print(f"  n_rows={n}  train_end={train_end}  val_end={val_end}  "
          f"T={T}")
    print(f"  REAL calendar gaps (row index where a gap begins): {gap_rows}")
    print(f"  week53 label-offset years (calendar-dense, no date change): "
          f"{n_label_off}")
    if not gap_rows:
        for L in HORIZONS:
            print(f"  L={L:2d}: dense dataset — 0 input/target/lead "
                  f"crossings; seasonal-naive lag-52 fully calendar-valid")
        return
    g = gap_rows[0]  # single real gap, between rows g-1 and g
    print(f"  (single gap between rows {g-1} and {g}; "
          f"{(dates[g]-dates[g-1]).days//7-1} weeks absent)")
    for L in HORIZONS:
        max_i = n - T - L  # last valid origin (target fully in-range)
        tot = max_i + 1
        input_cross = [i for i in range(tot)
                       if i <= g - 1 and i + T - 1 >= g]
        target_cross = [i for i in range(tot)
                        if i + T <= g - 1 and i + T + L - 1 >= g]
        # nominal lead != elapsed calendar weeks: the (input-end, target-end)
        # interval crosses the gap
        lead_mis = [i for i in range(tot)
                    if i + T - 1 <= g - 1 and i + T + L - 1 >= g]
        # split assignment by target_start = i + T
        def split(i):
            s = i + T
            return "train" if s < train_end else ("val" if s <= val_end
                                                  else "test")
        from collections import Counter
        in_cross_split = Counter(split(i) for i in input_cross)
        # seasonal naive: target rows t in [i+T, i+T+L), reference t-52;
        # invalid iff t-52 <= g-1 < g <= t  ->  t in [g, g+51]
        sn_bad_target_rows = list(range(g, min(g + 52, n)))
        sn_bad = []
        for i in range(tot):
            trange = range(i + T, i + T + L)
            if any(t in sn_bad_target_rows for t in trange):
                sn_bad.append(i)
        print(f"  L={L:2d}: total_origins={tot} | "
              f"input_cross_gap={len(input_cross)} {dict(in_cross_split)} | "
              f"target_cross_gap={len(target_cross)} | "
              f"lead_mismatch={len(lead_mis)} | "
              f"seasonal_naive_invalid_origins={len(sn_bad)}")
        if sn_bad_target_rows:
            print(f"        seasonal-naive invalid target rows (lag-52 "
                  f"crosses gap): {sn_bad_target_rows[0]}.."
                  f"{sn_bad_target_rows[-1]} "
                  f"(split={split(min(sn_bad_target_rows)-T) if min(sn_bad_target_rows)>=T else 'pre-window'})")


if __name__ == "__main__":
    proj = os.path.join(ROOT, "data", "raw", "national_illness_raw.csv")
    auth = os.path.join(ROOT, "data", "raw", "national_illness_raw_paper_exact.csv")
    # project 1025 split (train_miflu.py convention): 70/10/20 -> 717/102/206
    gap_consequences(proj, "PROJECT 1025-row (track B snapshot)",
                     train_end=717, val_end=819)
    # author 966 split (project convention on 966, per job 514859 log):
    # Train=676 | Val=96 | Test=194  ->  train_end=676, val_end=772
    gap_consequences(auth, "AUTHOR 966-row (track A, paper_exact)",
                     train_end=676, val_end=772)
    # author split under the author's own num_vali=remainder convention: 676/97/193
    gap_consequences(auth, "AUTHOR 966-row (author num_vali convention 676/97/193)",
                     train_end=676, val_end=773)
