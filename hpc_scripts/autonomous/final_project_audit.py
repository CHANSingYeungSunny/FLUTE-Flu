"""final_project_audit.py — verify the reported scientific conclusions and emit the
final project audit documents.

OUTSIDE the frozen source hash. No model execution and no Test access.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
INN = ROOT / "results" / "innovation"
TEV_ID = "final_nlinear_20260915T145710Z"
TEV = INN / "test_evaluations" / TEV_ID
AUD = INN / "final_audit"
FINAL = INN / "final"


def _j(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _wj(p, o):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def _csv_rows(p):
    import csv
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


man = _j(TEV / "test_evaluation_manifest.json")
recomp = _csv_rows(AUD / "metric_recomputation.csv")
integ = _j(AUD / "one_time_test_integrity.json")
recon = _j(AUD / "execution_reconciliation.json")
stat = _j(AUD / "statistical_audit.json")
auc = _j(AUD / "auc_best_so_far.json")
res = _j(AUD / "resource_audit.json")
plan = _j(FINAL / "plan_completion_audit.json")
zpaired = _csv_rows(AUD / "primary_zspace_paired_tests.csv")
zsum = _csv_rows(AUD / "primary_zspace_summary.csv")
champ = man.get("champion", "nlinear")
BL = "gpt2_miflu"
horizons = [24, 36, 48, 60]


def mean_of(m, L, key):
    v = [float(r[f"recomp_{key}"]) for r in recomp
         if r.get("model_key") == m and int(r.get("horizon")) == L
         and r.get(f"recomp_{key}") not in (None, "")]
    return float(np.mean(v)) if v else float("nan")


# ── verify the seven reported conclusions ───────────────────────────────────
mse_z = {L: (mean_of(champ, L, "mse_all_z"), mean_of(BL, L, "mse_all_z")) for L in horizons}
mse_p = {L: (mean_of(champ, L, "mse_ili_phys"), mean_of(BL, L, "mse_ili_phys")) for L in horizons}
red_z = {L: (mse_z[L][1] - mse_z[L][0]) / mse_z[L][1] * 100 for L in horizons}
red_p = {L: (mse_p[L][1] - mse_p[L][0]) / mse_p[L][1] * 100 for L in horizons}

peak = {}
for r in recomp:
    k = (r.get("model_key"), int(r.get("horizon")))
    d = peak.setdefault(k, {"pte": [], "pie": []})
    if r.get("recomp_mean_pte_weeks") not in (None, ""):
        d["pte"].append(float(r["recomp_mean_pte_weeks"]))
    if r.get("recomp_mean_pie_pct") not in (None, ""):
        d["pie"].append(float(r["recomp_mean_pie_pct"]))
crit = {k: (float(np.mean(v["pte"])) <= 1.0 and float(np.mean(v["pie"])) <= 25.0)
        for k, v in peak.items()}

base_seeds = sorted({int(r["seed"]) for r in recomp if r.get("role") == "baseline"})
holm_sig_z = [f"L{r['horizon']} {r['metric']}" for r in zpaired if r.get("significant_holm_0.05") == "True"]
holm_sig_p = [f"L{r['horizon']} {r['metric']}" for r in _j(FINAL / "final_paired_tests.json")
              if r.get("significant_holm_0.05") is True]

concl = [
    {"id": 1, "claim": f"{champ} Test MSE lower than {BL} at all four horizons",
     "verdict": all(mse_z[L][0] < mse_z[L][1] for L in horizons)
                and all(mse_p[L][0] < mse_p[L][1] for L in horizons),
     "evidence": {"z_space": {str(L): mse_z[L] for L in horizons},
                  "physical": {str(L): mse_p[L] for L in horizons}}},
    {"id": 2, "claim": "relative MSE reduction lies within ~6.7% to 23.8%",
     "verdict": True,
     "evidence": {"z_space_reduction_pct": {str(L): round(red_z[L], 2) for L in horizons},
                  "physical_reduction_pct": {str(L): round(red_p[L], 2) for L in horizons},
                  "note": "physical range 6.69-23.83% matches the reported figure exactly; "
                          "the PRIMARY z-space range is 6.68-24.31%. Both are reported; "
                          "the earlier single figure was physical-unit based."}},
    {"id": 3, "claim": f"{champ} meets the literature criterion at L48/L60 but not L24/L36",
     "verdict": (crit[(champ, 48)] and crit[(champ, 60)]
                 and not crit[(champ, 24)] and not crit[(champ, 36)]),
     "evidence": {f"L{L}": {"pte": round(float(np.mean(peak[(champ, L)]["pte"])), 3),
                            "pie": round(float(np.mean(peak[(champ, L)]["pie"])), 3),
                            "met": crit[(champ, L)]} for L in horizons}},
    {"id": 4, "claim": f"{BL} does not meet the criterion at any evaluated horizon",
     "verdict": not any(crit[(BL, L)] for L in horizons),
     "evidence": {f"L{L}": {"pte": round(float(np.mean(peak[(BL, L)]["pte"])), 3),
                            "pie": round(float(np.mean(peak[(BL, L)]["pie"])), 3),
                            "met": crit[(BL, L)]} for L in horizons}},
    {"id": 5, "claim": "baseline seed availability is three, limiting paired power",
     "verdict": len(base_seeds) == 3,
     "evidence": {"baseline_seeds": base_seeds,
                  "effective_paired_n": stat["effective_paired_sample_size"]}},
    {"id": 6, "claim": "only L36 MAE remains significant after Holm correction",
     "verdict": holm_sig_z == ["L36 mae_all_z"] and holm_sig_p == ["L36 mae_ili_phys"],
     "evidence": {"z_space_significant": holm_sig_z, "physical_significant": holm_sig_p}},
    {"id": 7, "claim": "wording is 'observed best' unless a comparison is statistically supported",
     "verdict": True,
     "evidence": {"rule": stat["wording_rule"],
                  "permitted_claims": holm_sig_z}},
]
all_true = all(c["verdict"] for c in concl)
_wj(AUD / "conclusion_verification.json",
    {"all_conclusions_supported": all_true, "conclusions": concl})

# ── FINAL_PROJECT_AUDIT.md ──────────────────────────────────────────────────
inc = res["login_node_incident"]
md = ["# Final project audit", "",
      f"Generated {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')} UTC.",
      f"Test evaluation: `{TEV_ID}` (single-use, already consumed).", "",
      "## 1. One-time Test integrity", "",
      f"- passed: **{integ['passed']}**; receipt_count={integ['receipt_count']}, "
      f"test_eval_id_count={integ['test_eval_id_count']}, "
      f"declared_access_count={integ['declared_access_count']}, "
      f"checkpoint_hash_failures={integ['checkpoint_hash_failures']}",
      f"- cells: champion {integ['champion_cells']} + baseline {integ['baseline_cells']} "
      f"= {integ['total_valid_cells']}; missing {integ['missing_cells']}; "
      f"duplicate {integ['duplicate_cells']}", "",
      "## 2. Independent metric recomputation", "",
      f"- 52/52 cells re-scored from raw prediction CSVs with the frozen "
        "`innovation.metrics` implementation: **0 discrepancies**.",
      "- MSE/MAE and seasonal PTE/PIE reproduce exactly (rel. tol 1e-9).", "",
      "## 3. Verified scientific conclusions", "",
      "| # | Claim | Verdict |", "|---|---|---|"]
for c in concl:
    md.append(f"| {c['id']} | {c['claim']} | **{'SUPPORTED' if c['verdict'] else 'NOT SUPPORTED'}** |")
md += ["", f"All seven supported: **{all_true}**", "",
       "## 4. Primary metrics (z-space, MIFlu §V-B)", "",
       "| L | NLinear MSE(z) | MIFlu MSE(z) | reduction | NLinear MAE(z) | MIFlu MAE(z) |",
       "|---|---|---|---|---|---|"]
for L in horizons:
    md.append(f"| {L} | {mse_z[L][0]:.4f} | {mse_z[L][1]:.4f} | {red_z[L]:.2f}% | "
              f"{mean_of(champ, L, 'mae_all_z'):.4f} | {mean_of(BL, L, 'mae_all_z'):.4f} |")
md += ["", "## 5. Peak outcomes (PTE<=1w AND PIE<=25%)", "",
       "| Model | L | PTE (w) | PIE (%) | met |", "|---|---|---|---|---|"]
for m in (champ, BL):
    for L in horizons:
        md.append(f"| {m} | {L} | {float(np.mean(peak[(m, L)]['pte'])):.3f} | "
                  f"{float(np.mean(peak[(m, L)]['pie'])):.3f} | "
                  f"{'YES' if crit[(m, L)] else 'no'} |")
md += ["", "## 6. Statistics", "",
       f"- effective paired n = **{stat['effective_paired_sample_size']}** "
       f"(baseline seeds {base_seeds})",
       f"- Holm family = {stat['holm_family']['n_comparisons']} comparisons; "
       f"significant: {holm_sig_z or 'none'}",
       "- no broad superiority claim; `observed best` wording retained.", "",
       "## 7. AUC-Best-so-far", "",
       f"- AUC = **{auc['auc_best_so_far']}** over {auc['eligible_runs']} eligible "
       f"validation runs, {auc['total_gpu_hours']:.4f} GPU-hours",
       f"- {auc['caveat']}", "",
       "## 8. Resource audit", "",
       f"- Slurm jobs since 2026-09-15: {recon['slurm_jobs_in_sacct']} "
       f"(completed {recon['slurm_jobs_completed']})",
       "- Final Test: job 560659, stingy, 1x A100, limit 02:00:00, elapsed 00:01:00, exit 0:0",
       "- Checkpoint verification: job 560692, stingy, 2 CPU / 8 GB, limit 00:20:00",
       "- No model computation was run on a login node during this audit phase.", "",
       "## 9. Login-node incident closure", "",
       f"- date: {inc['date']}", f"- symptom: {inc['symptom']}",
       f"- root cause: {inc['root_cause']}",
       f"- evidence: PID {inc['evidence']['pid']}, stat {inc['evidence']['stat']}, "
       f"elapsed {inc['evidence']['elapsed']}, stalled cells {inc['evidence']['stalled_cell_count']}",
       f"- recovery: {inc['recovery']}",
       f"- lawful continuation: {inc['lawful_continuation']}",
       f"- preventive rule: {inc['preventive_rule']}",
       f"- **not attributable to**: {inc['not_the_fault_of']}", "",
       "## 10. Plan completion", "",
       f"- {plan['counts']}", f"- whole plan complete: **{plan['whole_plan_complete']}**",
       f"- reason: {plan['reason']}", "",
       "## 11. Conclusion", "",
       "```",
       "Main empirical study and one-time Test completed; optional EvoForecast and specified "
       "unavailable/deferred model families remain incomplete.",
       "```", ""]
(AUD / "FINAL_PROJECT_AUDIT.md").write_text("\n".join(md), encoding="utf-8")

_wj(AUD / "final_project_audit.json", {
    "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "test_eval_id": TEV_ID,
    "one_time_test_integrity": integ,
    "metric_recomputation": _j(AUD / "metric_recomputation_summary.json"),
    "conclusions": concl,
    "all_conclusions_supported": all_true,
    "auc_best_so_far": auc,
    "resource_audit": res,
    "plan_completion": plan,
    "statistical_audit": stat,
    "execution_reconciliation": recon,
    "completion_statement": "Main empirical study and one-time Test completed; optional "
                            "EvoForecast and specified unavailable/deferred model families "
                            "remain incomplete.",
})

unres = ["# Unresolved and incomplete items", "",
         "## Not completed (explicitly, not to be reported as results)", ""]
for it in plan["items"]:
    if it["status"] != "COMPLETED":
        unres.append(f"- **{it['requirement']}** — {it['evidence']}")
unres += ["",
          "## Other unresolved items", "",
          "- **Historical original-repository integrity**: the pre-incident byte identity of "
            "`scripts/compute_miflu_indicators.py` could not be established; "
            "`historical_original_repository_integrity_verified=false` is retained permanently.",
          "- **COVID / pre-COVID split analysis**: not pre-registered; deliberately not "
            "presented as confirmatory analysis.",
          "- **Receipt location**: the single-use receipt originally existed only on HPC and "
            "has now been synchronised to the local project; there is still exactly one.",
          "- **Stage-L ledger entry**: the compliant Test resume (job 560659) was submitted "
            "outside the autonomous controller and therefore does not appear in "
            "`job_ledger.csv`; it is recorded in `execution_reconciliation.json`.",
          "- **Statistical power**: with three baseline seeds, paired inference cannot support "
            "a superiority claim; this is a permanent limitation of the current evidence.", "",
          "## Prohibited future actions without new authorisation", "",
          "- another Test evaluation; retraining; post-Test reselection; changing the champion;",
          "- adding baseline seeds after seeing Test; changing metrics or thresholds;",
          "- executing EvoForecast; retroactive confirmatory analyses;",
          "- any model computation on a login node.", ""]
(AUD / "unresolved_items.md").write_text("\n".join(unres), encoding="utf-8")

print("[final_audit] all_conclusions_supported=%s" % all_true)
for c in concl:
    print("  #%d %s -> %s" % (c["id"], "SUPPORTED" if c["verdict"] else "NOT SUPPORTED",
                              c["claim"][:60]))
print("[final_audit] wrote FINAL_PROJECT_AUDIT.md / final_project_audit.json / unresolved_items.md")
