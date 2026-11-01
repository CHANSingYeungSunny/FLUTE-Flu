#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""compare_evalwindow.py — what the shared evaluation-window rule changed.

Reads the frozen `*.pre_evalwindow16.csv` (170/158/146/134 windows) and
`*.post_evalwindow16.csv` (160/144/144/128 windows, MIFlu's set) tables and
prints, per model:

  * the 7-variable aggregate MSE mean before/after, and the ratio;
  * the per-horizon values, so the crossover (if any) is visible;
  * the Kramer & Shaman counts before/after: pass/16, PTE <= 1 wk count,
    PIE <= 25% count, mean PTE, mean PIE;
  * the MSE ranking and the K&S ranking, before and after, plus whether the
    champions changed.

This is the evidence file behind the ledger rows of the ruling; it writes
nothing, it only reports. Usage:

    python scripts/compare_evalwindow.py
"""
from __future__ import annotations

import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PT = os.path.join(ROOT, "paper_tables")
TAG_OLD, TAG_NEW = "pre_evalwindow16", "post_evalwindow16"
KS = ("kramer_shaman_pass",)


def load(table, tag):
    p = os.path.join(PT, f"{table}.{tag}.csv")
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    return pd.read_csv(p)


def mse_view():
    old, new = load("BENCH_MSE_BY_MODEL_L", TAG_OLD), load("BENCH_MSE_BY_MODEL_L", TAG_NEW)
    o = old.pivot_table(index="model", columns="L", values="mse_7var_z")
    n = new.pivot_table(index="model", columns="L", values="mse_7var_z")
    rows = []
    for mo in sorted(set(o.index) | set(n.index)):
        ro, rn = o.loc[mo], n.loc[mo]
        r = {"model": mo}
        for L in sorted(o.columns):
            r[f"L{L}_old"] = ro.get(L)
            r[f"L{L}_new"] = rn.get(L)
        r["mean_old"] = ro.mean()
        r["mean_new"] = rn.mean()
        r["ratio_old_over_new"] = r["mean_old"] / r["mean_new"]
        rows.append(r)
    df = pd.DataFrame(rows).sort_values("mean_new")
    df["rank_old"] = df["mean_old"].rank().astype(int)
    df["rank_new"] = df["mean_new"].rank().astype(int)
    return df, new


def ks_view():
    old, new = load("BENCH_PTE_PIE_BY_STEP", TAG_OLD), load("BENCH_PTE_PIE_BY_STEP", TAG_NEW)
    out = {}
    for label, d in (("old", old), ("new", new)):
        g = d.groupby("model").agg(
            n=("PTE_wk", "size"),
            passed=(KS[0], "sum"),
            pte_ok=("PTE_wk", lambda s: int((s <= 1.0).sum())),
            pie_ok=("PIE_pct", lambda s: int((s <= 25.0).sum())),
            pte=("PTE_wk", "mean"),
            pie=("PIE_pct", "mean"))
        out[label] = g
    rows = []
    for mo in sorted(set(out["old"].index) | set(out["new"].index)):
        r = {"model": mo}
        for label, g in out.items():
            if mo not in g.index:
                continue
            row = g.loc[mo]
            r[f"n_{label}"] = int(row.n)
            r[f"pass_{label}"] = int(row.passed)
            r[f"pte_ok_{label}"] = int(row.pte_ok)
            r[f"pie_ok_{label}"] = int(row.pie_ok)
            r[f"pte_{label}"] = float(row.pte)
            r[f"pie_{label}"] = float(row.pie)
        rows.append(r)
    return pd.DataFrame(rows).sort_values(["pass_new", "pte_new"], ascending=[False, True])


def main():
    pd.set_option("display.width", 250)
    df, new = mse_view()
    print("=== 7-variable aggregate MSE: pre_evalwindow16 (170/158/146/134) vs "
          "post (160/144/144/128) ===")
    cols = ["model", "L24_old", "L24_new", "L36_old", "L36_new", "L48_old", "L48_new",
            "L60_old", "L60_new", "mean_old", "mean_new", "ratio_old_over_new",
            "rank_old", "rank_new"]
    print(df[cols].round(4).to_string(index=False))

    print("\n=== MSE ranking (7-var aggregate, mean over L) ===")
    print("OLD:", " > ".join(f"{r.model} {r.mean_old:.4f}"
                             for r in df.sort_values('mean_old').itertuples()))
    print("NEW:", " > ".join(f"{r.model} {r.mean_new:.4f}"
                             for r in df.sort_values('mean_new').itertuples()))
    champ_old = df.sort_values("mean_old").iloc[0]
    champ_new = df.sort_values("mean_new").iloc[0]
    print(f"MSE champion: OLD {champ_old.model} {champ_old.mean_old:.4f} -> "
          f"NEW {champ_new.model} {champ_new.mean_new:.4f} "
          f"({'UNCHANGED' if champ_old.model == champ_new.model else 'CHANGED'})")
    print(f"full-window / eval-window ratio, per model mean: "
          f"{df.ratio_old_over_new.mean():.4f} (range "
          f"{df.ratio_old_over_new.min():.4f}-{df.ratio_old_over_new.max():.4f})")

    ks = ks_view()
    print("\n=== Kramer & Shaman (PTE <= 1 wk AND PIE <= 25%), 16 cells per model ===")
    print(ks.round(3).to_string(index=False))
    print("\nK&S ranking (pass count, then mean PTE):")
    for label in ("old", "new"):
        top = ks.sort_values([f"pass_{label}", f"pte_{label}"],
                             ascending=[False, True]).head(4)
        print(f"  {label:>4s}: " + "; ".join(
            f"{r.model} {getattr(r, f'pass_{label}')}/{getattr(r, f'n_{label}')} "
            f"(PTE {getattr(r, f'pte_{label}'):.2f}, PIE {getattr(r, f'pie_{label}'):.1f})"
            for r in top.itertuples()))
    ks_old = ks.sort_values(["pass_old", "pte_old"], ascending=[False, True]).iloc[0]
    ks_new = ks.sort_values(["pass_new", "pte_new"], ascending=[False, True]).iloc[0]
    print(f"K&S champion: OLD {ks_old.model} -> NEW {ks_new.model} "
          f"({'UNCHANGED' if ks_old.model == ks_new.model else 'CHANGED'})")

    print("\n=== n_eval_windows recorded in the new tables ===")
    print(new.groupby("L")[["n_windows_available", "n_eval_windows"]]
          .agg(lambda s: sorted(set(int(v) for v in s))).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
