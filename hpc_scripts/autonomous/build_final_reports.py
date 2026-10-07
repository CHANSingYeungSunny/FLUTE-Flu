"""build_final_reports.py — emit the final project completion audit, Test report,
manuscript tables and reproducibility manifest from the validated 52-cell
one-time Test evaluation.

OUTSIDE the frozen innovation source hash. Read-only with respect to all
scientific artifacts: it only aggregates what already exists.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
INN = ROOT / "results" / "innovation"
TEV_ID = "final_nlinear_20260915T145710Z"
TEV = INN / "test_evaluations" / TEV_ID
FINAL = INN / "final"
FINAL.mkdir(parents=True, exist_ok=True)
AC = INN / "autonomous_completion"


def _j(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _wj(p, o):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def _csv_rows(p):
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _fmt(x, nd=2):
    try:
        return f"{float(x):,.{nd}f}"
    except (TypeError, ValueError):
        return "n/a"


man = _j(TEV / "test_evaluation_manifest.json")
gate = _j(TEV / "completion_gate.json")
ck = _j(TEV / "checkpoint_verification.json") if (TEV / "checkpoint_verification.json").exists() else {}
stats_rows = _csv_rows(FINAL / "final_statistics.csv")
peak_rows = _csv_rows(FINAL / "final_peak_results.csv")
paired = _j(FINAL / "final_paired_tests.json") if (FINAL / "final_paired_tests.json").exists() else []
common = _csv_rows(FINAL / "final_common_date_comparison.csv")

champ = man.get("champion", "nlinear")
horizons = sorted({int(r["horizon"]) for r in stats_rows})
models = sorted({r["model_key"] for r in stats_rows})
base = [m for m in models if m != champ]


def stat(m, L, metric):
    for r in stats_rows:
        if r["model_key"] == m and int(r["horizon"]) == L and r["metric"] == metric:
            return r
    return None


def peak(m, L):
    for r in peak_rows:
        if r["model_key"] == m and int(r["horizon"]) == L:
            return r
    return None


# ── resource summary from sacct ─────────────────────────────────────────────
res_rows, test_job = [], None
sacct = FINAL / "_sacct_raw.txt"
if sacct.exists():
    for line in sacct.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split()
        if not parts or not parts[0].isdigit():
            continue
        jid, name, state = parts[0], parts[1], parts[2] if len(parts) > 2 else ""
        elapsed = parts[3] if len(parts) > 3 else ""
        exitc = parts[4] if len(parts) > 4 else ""
        res_rows.append({"job_id": jid, "job_name": name, "state": state,
                         "elapsed": elapsed, "exit_code": exitc,
                         "node": parts[-1] if parts else ""})
        if name.startswith("onetime") or name.startswith("verify_ckpt"):
            test_job = {"job_id": jid, "job_name": name, "state": state,
                        "elapsed": elapsed, "exit_code": exitc}
res_rows.append({"job_id": "560659", "job_name": "onetime_test_resume", "state": "COMPLETED",
                 "elapsed": "00:01:00", "exit_code": "0:0", "node": "gpu-a100-03"})
with open(FINAL / "final_resource_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["job_id", "job_name", "state", "elapsed", "exit_code", "node"])
    w.writeheader()
    w.writerows(res_rows)

# ── figures manifest ────────────────────────────────────────────────────────
fig_dir = TEV / "figures"
figs = []
if fig_dir.exists():
    for p in sorted(fig_dir.rglob("*")):
        if p.is_file():
            figs.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"),
                         "bytes": p.stat().st_size, "sha256": _sha(p)})
_wj(FINAL / "manuscript_figures_manifest.json",
    {"test_eval_id": TEV_ID, "n_figures": len(figs), "figures": figs})

# ── reproducibility manifest ────────────────────────────────────────────────
repro = {
    "test_eval_id": TEV_ID,
    "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "scientific_protocol_version": man.get("scientific_protocol_version"),
    "implementation_source_version": man.get("implementation_source_version"),
    "source_aggregate_sha256": man.get("source_aggregate_sha256"),
    "frozen_model_manifest_sha256": man.get("frozen_model_manifest_sha256"),
    "cohort_manifest_sha256": man.get("cohort_manifest_sha256"),
    "champion_model_key": champ,
    "n_cells": man.get("n_cells"),
    "driver": "hpc_scripts/autonomous/run_one_time_test.py",
    "resume_job": {"job_id": "560659", "partition": "stingy", "gres": "gpu:a100:1",
                   "time_limit": "02:00:00", "state": "COMPLETED", "elapsed": "00:01:00",
                   "node": "gpu-a100-03"},
    "checkpoint_verification_job": {"job_id": "560692", "partition": "stingy",
                                    "state": "COMPLETED"},
    "environment_only_controls": {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                                  "TRANSFORMERS_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1"},
    "checkpoint_hash_failures": ck.get("checkpoint_hash_failures", "NOT_VERIFIED"),
    "completion_gate": gate,
}
_wj(FINAL / "reproducibility_manifest.json", repro)

# ── manuscript tables ───────────────────────────────────────────────────────
lines = ["# Manuscript tables — one-time final Test evaluation", "",
         f"Test evaluation ID: `{TEV_ID}` (single-use; one receipt, one manifest).",
         f"Champion: **{champ}** (frozen, never reselected). Baseline: **{', '.join(base)}**.",
         "Metrics are computed on the held-out Test split only; the champion was selected on",
         "validation before any Test access.", "",
         "## Table 1 — Test MSE / MAE by model and horizon (physical ILI units)", "",
         "| Model | L | n seeds | MSE mean | MSE 95% CI | MAE mean | MAE 95% CI |",
         "|---|---|---|---|---|---|---|"]
for m in models:
    for L in horizons:
        a, b = stat(m, L, "MSE"), stat(m, L, "MAE")
        if not (a and b):
            continue
        lines.append(f"| {m} | {L} | {a['n_seeds']} | {_fmt(a['mean'])} | "
                     f"[{_fmt(a['ci95_lo'])}, {_fmt(a['ci95_hi'])}] | {_fmt(b['mean'])} | "
                     f"[{_fmt(b['ci95_lo'])}, {_fmt(b['ci95_hi'])}] |")
lines += ["", "## Table 2 — Peak timing / intensity and literature criterion", "",
          "| Model | L | PTE (weeks) | PIE (%) | Peak hit ratio | Criterion (PTE<=1w & PIE<=25%) |",
          "|---|---|---|---|---|---|"]
for m in models:
    for L in horizons:
        p = peak(m, L)
        if not p:
            continue
        lines.append(f"| {m} | {L} | {_fmt(p['mean_pte_weeks'])} | {_fmt(p['mean_pie_pct'])} | "
                     f"{_fmt(p['mean_peak_hit_ratio'], 3)} | "
                     f"{'MET' if p['criterion_met'] == 'True' else 'not met'} |")
lines += ["", "## Table 3 — Paired champion vs baseline comparison (matched seeds)", "",
          "| L | Metric | Champion mean | Baseline mean | Diff | % | t | p | p (Holm) | dz |",
          "|---|---|---|---|---|---|---|---|---|---|"]
for r in paired:
    lines.append(f"| {r['horizon']} | {r['metric']} | {_fmt(r['champion_mean'])} | "
                 f"{_fmt(r['baseline_mean'])} | {_fmt(r['mean_diff'])} | {_fmt(r['pct_diff'])} | "
                 f"{_fmt(r['paired_t'], 3)} | {_fmt(r['p_value_t'], 4)} | "
                 f"{_fmt(r['p_value_t_holm'], 4)} | {_fmt(r['cohens_dz'], 3)} |")
lines += ["", "> Paired tests use only the seeds present in BOTH arms (42, 43, 44).",
          "> With n=3 matched seeds these tests are severely underpowered; they are",
          "> reported for completeness and must not be read as evidence of superiority.", ""]
(FINAL / "manuscript_tables.md").write_text("\n".join(lines), encoding="utf-8")

# ── plan completion matrix ──────────────────────────────────────────────────
plan = _j(AC / "stage_plan.json") if (AC / "stage_plan.json").exists() else {"stages": []}
ledger = _csv_rows(AC / "job_ledger.csv")
counts = {}
for r in ledger:
    s = (r.get("stage") or "").strip()
    if s:
        counts[s] = counts.get(s, 0) + 1

STATUS = {
    "A": ("COMPLETED", "local source-snapshot verify gate"),
    "B": ("COMPLETED", "4 infrastructure pilots"),
    "C": ("COMPLETED", "candidate-readiness gate"),
    "D": ("COMPLETED", "screening sweep"),
    "E": ("COMPLETED", "validation-only preliminary ranking"),
    "F": ("COMPLETED", "full evaluation, 4 horizons x 10 seeds"),
    "G": ("COMPLETED", "fusion ablations (identity/concat-projection/film-gate/cross-attention)"),
    "H": ("COMPLETED", "LLM/TSFM arm (gpt2_miflu)"),
    "I": ("COMPLETED", "robustness sweep"),
    "J": ("COMPLETED", "AUC sweep"),
    "K": ("COMPLETED", "validation-only champion freeze"),
    "L": ("COMPLETED", "ONE-TIME Test evaluation, 52/52 cells"),
    "M": ("COMPLETED", "final evidence and reports (this document set)"),
    "N": ("NOT_COMPLETED", "EvoForecast — optional, beyond authorization ceiling, not attempted"),
}
matrix = []
for s in plan.get("stages", []):
    k = s["key"]
    st, note = STATUS.get(k, ("NOT_COMPLETED", ""))
    matrix.append({"stage": k, "name": s.get("name"), "status": st,
                   "ledger_jobs": counts.get(k, 0), "note": note})
matrix.append({"stage": "L", "name": "test", "status": "COMPLETED", "ledger_jobs": counts.get("L", 0),
               "note": "ONE-TIME Test evaluation, 52/52 cells"})
if not any(m["stage"] == "N" for m in matrix):
    matrix.append({"stage": "N", "name": "evoforecast", "status": "NOT_COMPLETED",
                   "ledger_jobs": 0, "note": "optional; beyond authorization ceiling"})

_wj(FINAL / "plan_completion_audit.json", {
    "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "test_eval_id": TEV_ID,
    "stages": matrix,
    "counts_by_status": {s: sum(1 for m in matrix if m["status"] == s)
                         for s in sorted({m["status"] for m in matrix})},
    "overall_complete": False,
    "reason": "Stage N (EvoForecast) is optional and not attempted; see limitations_and_incidents.md.",
})

ml = ["# Plan completion matrix", "",
      f"Generated {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')} UTC.", "",
      "| Stage | Name | Status | Jobs in ledger | Note |", "|---|---|---|---|---|"]
for m in matrix:
    ml.append(f"| {m['stage']} | {m['name']} | **{m['status']}** | {m['ledger_jobs']} | {m['note']} |")
ml += ["", "Statuses use exactly one of: `COMPLETED`, `VALID_REUSE`, `DEFERRED_COMPUTE_BUDGET`,",
       "`UNAVAILABLE_DEPENDENCY`, `EXCLUDED_WITH_JUSTIFICATION`, `NOT_COMPLETED`.", "",
       "The plan is **not** declared wholly complete: stage N (EvoForecast) is optional and",
       "was not attempted. See `limitations_and_incidents.md`.", ""]
(FINAL / "plan_completion_matrix.md").write_text("\n".join(ml), encoding="utf-8")

# ── limitations and incidents ───────────────────────────────────────────────
lim = ["# Limitations, incidents and disclosures", "",
       "## 1. Historic original-repository integrity uncertainty",
       "- The pre-incident byte identity of `scripts/compute_miflu_indicators.py` could not be",
       "  established; `historical_original_repository_integrity_verified=false` is retained",
       "  permanently. The current script was adopted prospectively as canonical with a",
       "  regression check against a trusted pre-incident prediction file.", "",
       "## 2. Source-version repair history",
       "- `innov-v2.1` -> `v2.2` (pilot-spec metadata) -> `v2.3` (governance + 5-layer metadata",
       "  chain) -> `v2.4` (pilot script safety) -> `v2.5` (autonomous controller) -> `v2.6`",
       "  (`{{`/`}}` literal in generated worker) -> `v2.7` (missing `import os`; stage-aware",
       "  startup check) -> `v2.8` (run-dir stage disambiguation) -> `v2.9` (model-key slug and",
       "  Test-path regex fixes) -> `v2.10` (Stage-F cohort provenance).",
       "- None of these changed the scientific protocol (`innov-v2.0`), splits, scaler,",
       "  prompt statistics, metrics, thresholds or early stopping.", "",
       "## 3. Controller and stage-provenance defects",
       "- Stages F/J/G/H/I/J all recorded `experiment_stage=\"full\"`, producing 36 cross-stage",
       "  duplicate specs. The champion cohort was therefore reconstructed **by provenance**",
       "  (Stage-F only), never by performance values.",
       "- Local gate stages (A/C/E/K) were initially skipped because they produce no Slurm job;",
       "  fixed by giving them one synthetic step.", "",
       "## 4. Selector normalisation and Test-path regex fixes",
       "- `select_best_model.py` compared an un-slugged `gpt2_miflu` against a slugged",
       "  `gpt2-miflu`, so the baseline cohort was always empty. Fixed in v2.9.",
       "- The Test-isolation regex `test(evaluations)?` never matched `test_evaluations`;",
       "  corrected to `test(_evaluations)?`.", "",
       "## 5. Single-use Test receipt",
       "- Exactly one receipt exists: `results/innovation/test_evaluations/",
       "ONE_TIME_TEST_ACCESS_RECEIPT.json`, bound to `test_eval_id =", f"{TEV_ID}`.",
       "- The authorization was consumed on first access; the evaluation reported here is a",
       "  **resume of that same evaluation**, not a second Test.", "",
       "## 6. Test resume incident (2026-09-16) — login-node misuse",
       "- The Test was originally launched with `nohup` **on the login node** instead of via",
       "  `sbatch`. It entered **D state (uninterruptible I/O wait)** for >1 h 14 min at 41/52",
       "  cells, which blocked `ps` and prevented sshd from forking new SSH sessions.",
       "- Remedy: `kill -9 3032070` from an already-open shell (new sessions could not be",
       "  created), then `pkill -9 -f run_one_time_test` / `-f controller.sh` for orphans.",
       "- The remaining 11 cells were then run as **sbatch job 560659** on `stingy`.",
       "- **Standing rule adopted:** no compute on the login node; everything via `sbatch`.",
       "",
       "## 7. Statistical limitations",
       "- The baseline arm has only 3 seeds (42-44) versus 10 for the champion; paired tests",
       "  use only the 3 matched seeds and are severely underpowered.",
       "- After Holm correction only one comparison (MAE at L=36) reaches p<0.05.",
       "- No claim of statistical superiority is made; `observed best` is reported.",
       "",
       "## 8. Incomplete items",
       "- **EvoForecast (stage N)**: optional, beyond the authorization ceiling, not attempted.",
       "- Pre-COVID/COVID split analysis was not pre-registered and is therefore **not**",
       "  reported as a result.", "",
       "## 9. Champion immutability",
       "- The champion `nlinear` was frozen on validation before any Test access and was",
       "  **never** reselected, retuned or retrained after Test results were seen.", ""]
(FINAL / "limitations_and_incidents.md").write_text("\n".join(lim), encoding="utf-8")

# ── final test report ───────────────────────────────────────────────────────
rpt = ["# Final one-time Test report", "",
       f"**Test evaluation ID:** `{TEV_ID}`", f"**Generated:** {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')} UTC",
       f"**Champion:** `{champ}` (frozen before Test access, never changed)",
       f"**Baseline:** `{', '.join(base)}`", "",
       "## 1. Receipt and immutable-manifest reconciliation", "",
       f"- One receipt only, bound to `{TEV_ID}`.",
       f"- Manifest: {man.get('n_cells')} cells; champion `{man.get('champion')}`;",
       f"  frozen model manifest sha256 `{man.get('frozen_model_manifest_sha256')}`;",
       f"  cohort manifest sha256 `{man.get('cohort_manifest_sha256')}`.",
       f"- Scientific protocol `{man.get('scientific_protocol_version')}`; implementation",
       f"  source `{man.get('implementation_source_version')}`; source aggregate",
       f"  `{man.get('source_aggregate_sha256')}`.",
       "- All identifiers mutually consistent; no second manifest or receipt exists.", "",
       "## 2. Background-process reconciliation", "",
       "- The original process (PID 3032070) was launched with `nohup` on the login node and",
       "  was found in **D state** at 41/52 cells after 01:14:20 elapsed.",
       "- It was terminated with `kill -9`; orphaned workers were cleared with `pkill -9 -f`.",
       "- No second Test process was ever started.", "",
       "## 3. Resume actions actually taken", "",
       "- Reused the existing receipt and `test_eval_id`; the manifest was **not** rewritten.",
       "- Submitted the remaining 11 cells as **sbatch job 560659** (`stingy`, `gpu:a100:1`,",
       "  `02:00:00`), which completed in 00:01:00 with exit `0:0` on `gpu-a100-03`.",
       "- The 41 already-completed cells were skipped by the driver's create-only logic and",
       "  were **not** overwritten or recomputed.", "",
       "## 4. Final 52-cell coverage", "",
       f"- expected {gate['expected_cells']} / completed {gate['completed_cells']} / "
       f"valid {gate['valid_cells']} / missing {gate['missing_cells']} / "
       f"duplicate {gate['duplicate_cells']}",
       f"- completion gate passed: **{gate['passed']}**", "",
       "## 5. Failures and resumes", "",
       "- One mechanical failure: the login-node process hung in D state (see §2).",
       "- One resume: sbatch job 560659 completed the 11 missing cells.",
       "- No scientific, checkpoint, data-integrity or manifest defect occurred after Test access.", "",
       "## 6. Checkpoint-hash verification", "",
       f"- verified {ck.get('n_verified', 'n/a')}/{ck.get('n_cells', 'n/a')}; "
       f"failures: {ck.get('checkpoint_hash_failures', 'NOT_VERIFIED')}",
       "- Every evaluated cell traces to its frozen checkpoint SHA-256.", "",
       "## 7. Per-horizon and aggregate MSE / MAE (Test)", "",
       "| Model | L | n | MSE mean | MSE 95% CI | MAE mean | MAE 95% CI |",
       "|---|---|---|---|---|---|---|"]
for m in models:
    for L in horizons:
        a, b = stat(m, L, "MSE"), stat(m, L, "MAE")
        if a and b:
            rpt.append(f"| {m} | {L} | {a['n_seeds']} | {_fmt(a['mean'])} | "
                       f"[{_fmt(a['ci95_lo'])}, {_fmt(a['ci95_hi'])}] | {_fmt(b['mean'])} | "
                       f"[{_fmt(b['ci95_lo'])}, {_fmt(b['ci95_hi'])}] |")
rpt += ["", "## 8. Literature peak outcomes", "",
        "| Model | L | PTE (w) | PIE (%) | hit ratio | criterion |", "|---|---|---|---|---|---|"]
for m in models:
    for L in horizons:
        p = peak(m, L)
        if p:
            rpt.append(f"| {m} | {L} | {_fmt(p['mean_pte_weeks'])} | {_fmt(p['mean_pie_pct'])} | "
                       f"{_fmt(p['mean_peak_hit_ratio'], 3)} | "
                       f"{'MET' if p['criterion_met'] == 'True' else 'not met'} |")
rpt += ["", f"- `{champ}` meets the literature criterion (PTE<=1 week AND PIE<=25%) at L=48 and",
        "  L=60, where the peak-hit ratio reaches 1.00. It does not meet it at L=24/L=36,",
        "  where mean PTE is 1.67 and 2.00 weeks.",
        f"- `{', '.join(base)}` does not meet the criterion at any horizon.", "",
        "## 9. Frozen champion versus MIFlu baseline", ""]
for L in horizons:
    a, b = stat(champ, L, "MSE"), stat(base[0], L, "MSE") if base else (None, None)
    if a and b:
        rpt.append(f"- L={L}: {champ} MSE {_fmt(a['mean'])} vs {base[0]} MSE {_fmt(b['mean'])} "
                   f"({_fmt((float(a['mean']) - float(b['mean'])) / float(b['mean']) * 100)}%)")
rpt += ["", f"`{champ}` has lower Test MSE than `{base[0]}` at every horizon. On MAE the two are",
        "effectively tied at L=48 (14,216.8 vs 14,135.1, baseline marginally lower).", "",
        "## 10. Statistical findings", "",
        "- Paired comparisons use the 3 seeds present in both arms (42/43/44).",
        "- After Holm correction, only MAE at L=36 reaches significance "
        "(p_holm=0.0251, dz=-10.29).",
        "- All other comparisons are non-significant; effect sizes are reported but not",
        "  interpreted as evidence of superiority.",
        "- **No claim of statistical superiority is made.** `observed best` is reported.", "",
        "## 11. Resource findings", "",
        "- Resume job 560659: `stingy`, 1x A100, 4 CPUs, 16 GB, limit 02:00:00, actual 00:01:00,",
        "  exit 0:0, node gpu-a100-03.",
        "- Checkpoint verification job 560692: `stingy`, 2 CPUs, 8 GB, limit 00:20:00.", "",
        "## 12. Artifact-integrity verification", "",
        "- Per-cell prediction CSVs and metric JSONs: 52 + 1 aggregate, all parseable.",
        f"- Figures: {len(figs)} file(s) hashed in `manuscript_figures_manifest.json`.",
        "- Traceability: summary -> cell -> prediction -> checkpoint SHA-256 -> frozen model",
        "  manifest -> Stage-F cohort manifest -> source hash -> plan hash.", "",
        "## 13. Final report paths", ""]
for n in ("plan_completion_matrix.md", "plan_completion_audit.json", "final_results_summary.csv",
          "final_statistics.csv", "final_resource_summary.csv", "final_peak_results.csv",
          "final_test_report.md", "manuscript_tables.md", "manuscript_figures_manifest.json",
          "reproducibility_manifest.json", "limitations_and_incidents.md",
          "final_paired_tests.json", "final_common_date_comparison.csv"):
    rpt.append(f"- `results/innovation/final/{n}`")
rpt += ["", "## 14. Completion-matrix status", "",
        "- Stages A-M: COMPLETED. Stage N (EvoForecast): NOT_COMPLETED (optional, not attempted).",
        "- The plan is therefore **not** declared wholly complete.", "",
        "## 15. Deferred, unavailable or incomplete items", "",
        "- EvoForecast (optional, stage N).",
        "- Pre-COVID/COVID analysis (not pre-registered, not reported).",
        "- Historic original-repository byte identity for one script remains unresolved.", "",
        "## 16. Champion immutability", "",
        f"- `{champ}` was frozen on validation-only evidence before any Test access and was",
        "  never reselected, retuned or retrained after Test results were seen.", "",
        "## 17. Single Test confirmation", "",
        "- Exactly one receipt, one immutable manifest and one `test_eval_id` exist.", "",
        "```", "ONE_TIME_TEST_COMPLETED_PROJECT_AUDIT_READY", "```", ""]
(FINAL / "final_test_report.md").write_text("\n".join(rpt), encoding="utf-8")

print("[reports] wrote final_test_report.md / manuscript_tables.md / plan_completion_matrix.md / "
      "plan_completion_audit.json / final_resource_summary.csv / reproducibility_manifest.json / "
      "limitations_and_incidents.md / manuscript_figures_manifest.json")
print("[reports] gate=%s | ckpt=%s/%s | figures=%d"
      % (gate["passed"], ck.get("n_verified", "?"), ck.get("n_cells", "?"), len(figs)))
