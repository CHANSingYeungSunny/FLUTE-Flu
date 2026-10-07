"""Compute the finalized deferred-control statistical interpretation.

Family A (equivalents, descriptive): gpt2_miflu zero_text / shuffled_text vs
  gpt2_miflu parent (12 Wave-1 accepted rows, no rerun).
Family B (confirmatory, newly executed): timecma_llm llm_removed_or_alignment_only
  vs timecma_llm parent (6 newly executed + ACCEPTED rows, L24/L60 x seed 42/43/44).

Matched-parent paired comparisons only. Families A and B are NEVER pooled.
"""
from __future__ import annotations

import json
import os

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL_DIR = os.path.join(HERE, "..", "..", "results", "v3_clean", "final")
FINAL_DIR = os.path.abspath(FINAL_DIR)

# ---------------------------------------------------------------------------
# Family A: read the already-frozen paired control_effects.csv
# columns: control,horizon,seed,control_mse,parent_mse,delta
# parent = gpt2_miflu
# ---------------------------------------------------------------------------
import csv


def load_family_a() -> dict:
    p = os.path.join(FINAL_DIR, "..", "analysis", "control_effects.csv")
    p = os.path.abspath(p)
    rows = {"zero_text": {}, "shuffled_text": {}}
    with open(p, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            control = row["control"]
            horizon = int(row["horizon"])
            seed = int(row["seed"])
            delta = float(row["delta"])
            control_mse = float(row["control_mse"])
            parent_mse = float(row["parent_mse"])
            rows[control][(horizon, seed)] = {
                "control_mse": control_mse,
                "parent_mse": parent_mse,
                "delta": delta,
            }
    return rows


# ---------------------------------------------------------------------------
# Family B: exact primary metric values from HPC durable packages (verified
# 2026-09-21). parent = timecma_llm (values from primary_seed_level.csv).
# ---------------------------------------------------------------------------
FAMILY_B_REMOVED = {
    (24, 42): 1.0617970015376361,
    (24, 43): 1.0935101779911076,
    (24, 44): 1.1312947924059518,
    (60, 42): 1.330458261101273,
    (60, 43): 1.3387222700144845,
    (60, 44): 1.3210884716023277,
}
FAMILY_B_PARENT = {
    (24, 42): 1.0742802545783101,
    (24, 43): 1.0892946616418109,
    (24, 44): 1.0524248813672634,
    (60, 42): 1.2308210009471248,
    (60, 43): 1.2441614613151044,
    (60, 44): 1.23398598508727,
}


def paired_stats(deltas: list[float], parent_means: list[float]) -> dict:
    d = np.asarray(deltas, dtype=float)
    p = np.asarray(parent_means, dtype=float)
    n = int(d.size)
    mean_d = float(np.mean(d))
    median_d = float(np.median(d))
    sd_d = float(np.std(d, ddof=1)) if n > 1 else float("nan")
    sem = float(sd_d / np.sqrt(n)) if n > 1 else float("nan")
    # paired t-test (two-sided)
    if n > 1 and sd_d > 0:
        tstat = float(mean_d / sem)
        pval = float(stats.t.sf(abs(tstat), df=n - 1) * 2)
    else:
        tstat = float("nan")
        pval = float("nan")
    # 95% CI on the mean paired difference (t, df=n-1)
    if n > 1:
        tcrit = stats.t.ppf(0.975, df=n - 1)
        ci_lo = float(mean_d - tcrit * sem)
        ci_hi = float(mean_d + tcrit * sem)
    else:
        ci_lo = float("nan")
        ci_hi = float("nan")
    # Cohen's d_z for paired data (mean / SD of differences)
    d_z = float(mean_d / sd_d) if (n > 1 and sd_d > 0) else float("nan")
    # relative change: mean delta / mean parent * 100 (parent MSE baseline)
    mean_parent = float(np.mean(p))
    rel_pct = float(mean_d / mean_parent * 100.0) if mean_parent != 0 else float("nan")
    return {
        "n_pairs": n,
        "mean_delta": mean_d,
        "median_delta": median_d,
        "sample_sd": sd_d,
        "sem": sem,
        "ci95_low": ci_lo,
        "ci95_high": ci_hi,
        "cohens_dz": d_z,
        "paired_t": tstat,
        "p_value": pval,
        "mean_parent_mse": mean_parent,
        "mean_control_mse": float(mean_parent + mean_d),
        "relative_change_pct": rel_pct,
    }


def holm_bonferroni(pvals: dict[str, float]) -> dict:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out = {}
    prev = 1.0
    for i, (name, p) in enumerate(items, start=1):
        adj = p * (m - i + 1)
        adj = min(adj, 1.0)
        # enforce monotonicity
        adj = max(adj, prev)
        prev = adj
        out[name] = {"raw_p": p, "holm_p": adj, "rank": i, "m": m}
    return out


def main() -> int:
    fam_a = load_family_a()

    results = {
        "generated_utc": "2026-09-21T00:00:00Z",
        "purpose": (
            "Finalized statistical interpretation of the deferred controls after "
            "DEFERRED_CONTROLS_PROTOCOL_AMENDMENT_2026-09-21 closure. "
            "Family A (descriptive equivalents) and Family B (confirmatory newly "
            "executed controls) are kept strictly separate; matched-parent paired "
            "comparisons only."
        ),
        "family_A": {
            "label": "DESCRIPTIVE / EXPLORATORY (equivalents, no rerun, no new observation)",
            "parent_model": "gpt2_miflu",
            "controls": {},
        },
        "family_B": {
            "label": "CONFIRMATORY (6 newly executed + ACCEPTED rows)",
            "parent_model": "timecma_llm",
            "control": "llm_removed_or_alignment_only",
            "horizons": [24, 60],
            "seeds": [42, 43, 44],
            "comparisons": {},
        },
    }

    # ---- Family A per control: L24, L60, pooled ---------------------------
    for control in ("zero_text", "shuffled_text"):
        rows = fam_a[control]
        by_h = {24: [], 60: []}
        for (h, s), v in rows.items():
            by_h[h].append(v)
        entry = {"label": control, "per_horizon": {}, "pooled": None}
        for h in (24, 60):
            vals = by_h[h]
            deltas = [v["delta"] for v in vals]
            parents = [v["parent_mse"] for v in vals]
            controls = [v["control_mse"] for v in vals]
            entry["per_horizon"][str(h)] = paired_stats(deltas, parents)
            entry["per_horizon"][str(h)]["paired_differences"] = [
                round(c - p, 10) for c, p in zip(controls, parents)
            ]
        all_deltas = [v["delta"] for v in rows.values()]
        all_parents = [v["parent_mse"] for v in rows.values()]
        all_controls = [v["control_mse"] for v in rows.values()]
        entry["pooled"] = paired_stats(all_deltas, all_parents)
        entry["pooled"]["paired_differences"] = [
            round(c - p, 10) for c, p in zip(all_controls, all_parents)
        ]
        results["family_A"]["controls"][control] = entry

    # ---- Family B ----------------------------------------------------------
    b = results["family_B"]
    by_h = {24: [], 60: []}
    for (h, s), rm in FAMILY_B_REMOVED.items():
        par = FAMILY_B_PARENT[(h, s)]
        by_h[h].append((s, par, rm, rm - par))
    for h in (24, 60):
        vals = by_h[h]
        deltas = [v[3] for v in vals]
        parents = [v[1] for v in vals]
        controls = [v[2] for v in vals]
        comp = paired_stats(deltas, parents)
        comp["paired_differences"] = [round(v[3], 10) for v in vals]
        comp["seeds"] = [v[0] for v in vals]
        b["comparisons"][f"L{h}"] = comp
    all_deltas = [rm - FAMILY_B_PARENT[(h, s)] for (h, s), rm in FAMILY_B_REMOVED.items()]
    all_parents = [FAMILY_B_PARENT[(h, s)] for (h, s), rm in FAMILY_B_REMOVED.items()]
    all_controls = [rm for rm in FAMILY_B_REMOVED.values()]
    pooled = paired_stats(all_deltas, all_parents)
    pooled["paired_differences"] = [round(d, 10) for d in all_deltas]
    b["comparisons"]["pooled"] = pooled

    # ---- Multiple-comparison treatment (confirmatory family B) ------------
    raw_confirmatory = {
        "familyB_L24": b["comparisons"]["L24"]["p_value"],
        "familyB_L60": b["comparisons"]["L60"]["p_value"],
    }
    b["multiple_comparison"] = {
        "method": "Holm-Bonferroni (step-down)",
        "family": "Family B confirmatory horizon-specific paired t-tests (m=2)",
        "alpha": 0.05,
        "tests": holm_bonferroni(raw_confirmatory),
    }

    # ---- Interpretation labels --------------------------------------------
    b["interpretation"] = {
        "L24": "Removing the LLM/text branch does not significantly change "
                "short-horizon 7-variable z-space MSE (small, non-significant "
                "positive delta).",
        "L60": "Removing the LLM/text branch significantly increases long-horizon "
               "7-variable z-space MSE; interpreted as evidence supporting a "
               "long-horizon contribution of the text/LLM branch, NOT proof of a "
               "universal causal mechanism.",
        "caveat": "n=3 per horizon; paired t-tests have low power. Treat as "
                  "supporting evidence, not conclusive causal proof.",
    }

    # ---- Write JSON --------------------------------------------------------
    json_path = os.path.join(FINAL_DIR, "deferred_controls_statistical_interpretation.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # ---- Write Markdown ----------------------------------------------------
    md_path = os.path.join(FINAL_DIR, "deferred_controls_statistical_interpretation.md")
    lines = []
    lines.append("# Deferred Controls — Finalized Statistical Interpretation")
    lines.append("")
    lines.append("Generated after `DEFERRED_CONTROLS_PROTOCOL_AMENDMENT_2026-09-21` closure. "
                 "Matched-parent paired comparisons only. Families A and B are never pooled.")
    lines.append("")

    lines.append("## Family A — gpt2_miflu zero_text / shuffled_text (DESCRIPTIVE / EXPLORATORY)")
    lines.append("")
    lines.append("12 deferred specifications satisfied by exactly equivalent Wave-1 accepted rows. "
                 "No rerun, no duplicated statistical observation. Parent = `gpt2_miflu`.")
    lines.append("")
    lines.append("| control | horizon | n | mean delta | median delta | sample SD | 95% CI | Cohen d_z | paired-t | p |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for control in ("zero_text", "shuffled_text"):
        e = results["family_A"]["controls"][control]
        for h in ("24", "60", "pooled"):
            if h == "pooled":
                s = e["pooled"]
                hlabel = "pooled (24+60)"
            else:
                s = e["per_horizon"][h]
                hlabel = f"L{h}"
            ci = f"[{s['ci95_low']:.4f}, {s['ci95_high']:.4f}]"
            lines.append(f"| {control} | {hlabel} | {s['n_pairs']} | {s['mean_delta']:+.4f} | "
                         f"{s['median_delta']:+.4f} | {s['sample_sd']:.4f} | {ci} | "
                         f"{s['cohens_dz']:+.3f} | {s['paired_t']:+.3f} | {s['p_value']:.4f} |")
    lines.append("")
    lines.append("Family A is reported descriptively: these are Wave-1 negative controls already "
                 "accepted in the primary matrix, not newly executed confirmatory tests.")
    lines.append("")

    lines.append("## Family B — timecma_llm llm_removed_or_alignment_only (CONFIRMATORY)")
    lines.append("")
    lines.append("6 newly executed + ACCEPTED rows (L24/L60 x seed 42/43/44). Parent = `timecma_llm`.")
    lines.append("")
    lines.append("| comparison | n | mean delta | median delta | sample SD | 95% CI | Cohen d_z | paired-t | p |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for h in ("L24", "L60", "pooled"):
        s = b["comparisons"][h]
        hlabel = h if h != "pooled" else "pooled (24+60)"
        ci = f"[{s['ci95_low']:.4f}, {s['ci95_high']:.4f}]"
        lines.append(f"| {hlabel} | {s['n_pairs']} | {s['mean_delta']:+.4f} | "
                     f"{s['median_delta']:+.4f} | {s['sample_sd']:.4f} | {ci} | "
                     f"{s['cohens_dz']:+.3f} | {s['paired_t']:+.3f} | {s['p_value']:.4f} |")
    lines.append("")
    lines.append("### Multiple-comparison treatment (confirmatory family)")
    lines.append("")
    lines.append("Holm-Bonferroni step-down across the two Family B horizon-specific paired "
                 "t-tests (m=2), alpha=0.05:")
    lines.append("")
    lines.append("| test | raw p | Holm-adjusted p |")
    lines.append("|---|---|---|")
    for name, v in b["multiple_comparison"]["tests"].items():
        lines.append(f"| {name} | {v['raw_p']:.4f} | {v['holm_p']:.4f} |")
    lines.append("")
    lines.append("### Interpretation")
    lines.append("")
    lines.append(f"- **L24**: {b['interpretation']['L24']}")
    lines.append(f"- **L60**: {b['interpretation']['L60']}")
    lines.append(f"- **Caveat**: {b['interpretation']['caveat']}")
    lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("WROTE", json_path)
    print("WROTE", md_path)
    print(json.dumps(results["family_B"]["comparisons"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
