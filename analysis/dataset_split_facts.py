"""
dataset_split_facts.py — Tutor Q2 (Dataset facts for 70:10:20 split)
=====================================================================
Local. Reads data/national_illness_raw.csv and prints the EXACT row counts
and epiweek start/end for Train / Val / Test under the strict chronological
70:10:20 split used by make_forecast_figure.py and miflu_model.py.

Also demonstrates the "tail L=60 removed for target shift" logic:
the last L weeks of each partition cannot serve as forecast origins
because there is no full L-step target after them.

This output is REAL evidence (type C) for Tutor_QA_Report.md Q2.
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "national_illness_raw.csv")


def main():
    df = pd.read_csv(DATA)
    n = len(df)
    print("=" * 72)
    print(" DATASET SPLIT FACTS (Tutor Q2) — chronological 70:10:20")
    print("=" * 72)
    print(f"Total rows (weeks): {n}")
    print(f"epiweek range: {int(df['epiweek'].iloc[0])} .. {int(df['epiweek'].iloc[-1])}\n")

    t_end = int(n * 0.70)
    v_end = t_end + int(n * 0.10)

    train = df.iloc[:t_end]
    val = df.iloc[t_end:v_end]
    test = df.iloc[v_end:]

    print(f"TRAIN : rows {len(train):>4d}  ({len(train)/n*100:4.1f}%)  "
          f"epiweeks {int(train['epiweek'].iloc[0])} .. {int(train['epiweek'].iloc[-1])}")
    print(f"VAL   : rows {len(val):>4d}  ({len(val)/n*100:4.1f}%)  "
          f"epiweeks {int(val['epiweek'].iloc[0])} .. {int(val['epiweek'].iloc[-1])}")
    print(f"TEST  : rows {len(test):>4d}  ({len(test)/n*100:4.1f}%)  "
          f"epiweeks {int(test['epiweek'].iloc[0])} .. {int(test['epiweek'].iloc[-1])}\n")

    # target-shift: remove tail L=60 within each partition as forecast origins
    L = 60  # most restrictive horizon
    print(f"Usable forecast-origin windows after removing tail L={L} for target shift:")
    print(f"  TRAIN origins: {max(0, len(train) - L)}")
    print(f"  VAL   origins: {max(0, len(val) - L)}")
    print(f"  TEST  origins: {max(0, len(test) - L)}")
    print("\n[DONE] dataset_split_facts.py — numbers above are REAL (local run).")


if __name__ == "__main__":
    main()
