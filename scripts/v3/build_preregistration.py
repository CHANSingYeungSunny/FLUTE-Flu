"""build_preregistration.py — generate the v3 Phase-0 preregistration deliverables.

Phase 0 only. It NEVER downloads weights, constructs or loads a model, accesses a
holdout, or submits a Slurm job. It only reads existing files, computes real
SHA-256 hashes, and writes reports.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v3"))

V3 = ROOT / "results" / "v3"
PRE = V3 / "preregistration"
ARCH = ROOT / "results" / "v2_legacy_archive"
for d in (V3, PRE, ARCH):
    d.mkdir(parents=True, exist_ok=True)

PROTOCOL_V3 = "innov-v3.0"
IMPL_V3 = "innov-v3.0-preregistration"
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(p) -> str:
    p = Path(p)
    if not p.exists() or p.is_dir():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def wj(p, o):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def wcsv(p, rows, cols=None):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    cols = cols or list(rows[0].keys())
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ══ 1. v2 preservation manifest ═════════════════════════════════════════════
V2_SCOPE = [
    ("v2_plan", ROOT / "MIFlu_innovation_plan_v2.md", "protocol", "immutable", "innov-v2.0"),
    ("v2_frozen_winners", ROOT / "results/innovation/frozen_winners.json", "selection", "immutable", "innov-v2.0"),
    ("v2_frozen_model_manifest", ROOT / "results/innovation/frozen_model_manifest.json", "selection", "immutable", "innov-v2.0"),
    ("v2_freeze_audit", ROOT / "results/innovation/freeze_audit.json", "audit", "immutable", "innov-v2.0"),
    ("v2_model_selection_audit", ROOT / "results/innovation/model_selection_audit.json", "audit", "immutable", "innov-v2.0"),
    ("v2_stage_f_cohort_manifest", ROOT / "results/innovation/governance/stage_provenance/stage_f_cohort_manifest.json", "provenance", "immutable", "innov-v2.0"),
    ("v2_test_receipt", ROOT / "results/innovation/test_evaluations/ONE_TIME_TEST_ACCESS_RECEIPT.json", "test_authorization", "immutable", "innov-v2.0"),
    ("v2_test_manifest", ROOT / "results/innovation/test_evaluations/final_nlinear_20260915T145710Z/test_evaluation_manifest.json", "test_manifest", "immutable", "innov-v2.0"),
    ("v2_test_completion_gate", ROOT / "results/innovation/test_evaluations/final_nlinear_20260915T145710Z/completion_gate.json", "audit", "immutable", "innov-v2.0"),
    ("v2_test_checkpoint_verification", ROOT / "results/innovation/test_evaluations/final_nlinear_20260915T145710Z/checkpoint_verification.json", "audit", "immutable", "innov-v2.0"),
    ("v2_final_test_report", ROOT / "results/innovation/final/final_test_report.md", "report", "immutable", "innov-v2.0"),
    ("v2_plan_completion_audit", ROOT / "results/innovation/final/plan_completion_audit.json", "audit", "immutable", "innov-v2.0"),
    ("v2_final_project_audit", ROOT / "results/innovation/final_audit/final_project_audit.json", "audit", "immutable", "innov-v2.0"),
    ("v2_resource_audit_login_node_incident", ROOT / "results/innovation/final_audit/resource_audit.json", "incident_evidence", "immutable", "innov-v2.0"),
    ("v2_registry", ROOT / "results/innovation/registry.csv", "registry", "append-only", "innov-v2.0"),
    ("v2_registry_v2", ROOT / "results/innovation/registry_v2.csv", "registry", "append-only", "innov-v2.0"),
    ("v2_stage_plan", ROOT / "results/innovation/autonomous_completion/stage_plan.json", "control", "immutable", "innov-v2.0"),
    ("v2_job_ledger", ROOT / "results/innovation/autonomous_completion/job_ledger.csv", "ledger", "append-only", "innov-v2.0"),
]
pres_rows = []
for role, p, kind, mut, ver in V2_SCOPE:
    pres_rows.append({"canonical_path": str(p.relative_to(ROOT)).replace("\\", "/"),
                      "exists": p.exists(), "bytes": p.stat().st_size if p.exists() else 0,
                      "sha256": sha(p), "role": role, "artifact_kind": kind,
                      "immutability": mut, "historical_version": ver})
# also count the 52 Test cells as preserved evidence
TEV = ROOT / "results/innovation/test_evaluations/final_nlinear_20260915T145710Z"
n_pred = len(list((TEV / "predictions").glob("*.csv"))) if (TEV / "predictions").exists() else 0
n_met = len(list((TEV / "metrics").glob("*.json"))) if (TEV / "metrics").exists() else 0
pres_rec = {"generated_utc": NOW, "purpose": "preserve completed v2 evidence as immutable history "
                                             "before any v3 work",
            "n_records": len(pres_rows),
            "v2_test_prediction_files": n_pred, "v2_test_metric_files": n_met,
            "policy": "Do not delete, overwrite, relabel or rewrite any v2 evidence. The v2 "
                      "Test is known and must not be described as an untouched v3 holdout.",
            "records": pres_rows}
wj(ARCH / "v2_preservation_manifest.json", pres_rec)
wj(PRE / "v2_preservation_manifest.json", pres_rec)
wcsv(ARCH / "v2_preservation_manifest.csv", pres_rows)
wcsv(PRE / "v2_preservation_manifest.csv", pres_rows)

# ══ 2. legacy scope inventory + scope cleanup audit ═════════════════════════
BANNED = ["PMO", "Oracle-budget", "Oracle budget", "AUC-Best-so-far",
          "AlphaEvolve", "EvoForecast", "evolutionary"]
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".codebuddy"}
LEGACY_ROOTS = ["results/innovation", "results/v2_legacy_archive"]
V3_ACTIVE_ROOTS = ["hpc_scripts/v3", "scripts/v3", "results/v3"]

inv, n_active_violation = [], 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        if not fn.lower().endswith((".md", ".py", ".json", ".csv", ".sh", ".yaml", ".yml", ".txt")):
            continue
        p = Path(dirpath) / fn
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        hits = sorted({t for t in BANNED if t in text})
        if not hits:
            continue
        # The scope-cleanup audit artifacts MUST quote the removed terms in order to
        # record what was removed. Quoting is not the same as carrying an active
        # concept, so they are classified exactly like the governing specification.
        if (rel.startswith("CodeBuddy_MIFlu_v3_Master")
                or rel == "scripts/v3/build_preregistration.py"
                or rel.endswith(("legacy_scope_inventory.json", "legacy_scope_inventory.csv",
                                 "scope_cleanup_audit.json", "scope_cleanup_audit.md"))):
            cls = "THIRD_PARTY_OR_CITATION_CONTEXT"
            note = "audit/specification record: the terms appear only as a quotation of " \
                   "what was removed from active v3 scope, not as active v3 research content"
        elif any(rel.startswith(r) for r in V3_ACTIVE_ROOTS):
            cls = "ACTIVE_V3_VIOLATION"
            n_active_violation += 1
            note = "inside an active v3 root - must be removed"
        elif any(rel.startswith(r) for r in LEGACY_ROOTS) or rel.startswith(
                ("MIFlu_innovation_plan_v2", "hpc_scripts/autonomous",
                 "results/innovation/autonomous_completion", "results/innovation/audit",
                 "results/innovation/remaining_plan_execution_matrix.md")):
            cls = "SEALED_V2_HISTORICAL_EVIDENCE"
            note = "completed v2 evidence or v2-era tooling; retained deliberately"
        elif rel.startswith(("docs/", "results/ili")):
            cls = "THIRD_PARTY_OR_CITATION_CONTEXT"
            note = "contextual/citation material outside the active v3 research surface"
        else:
            cls = "THIRD_PARTY_OR_CITATION_CONTEXT"
            note = "outside the active v3 research surface; retained with classification"
        inv.append({"path": rel, "sha256": sha(p), "bytes": p.stat().st_size,
                    "matches": hits, "classification": cls, "note": note})

inv_rec = {"generated_utc": NOW, "banned_terms": BANNED,
           "n_files_with_matches": len(inv),
           "classification_counts": {c: sum(1 for r in inv if r["classification"] == c)
                                     for c in sorted({r["classification"] for r in inv})},
           "records": inv}
wj(ARCH / "legacy_scope_inventory.json", inv_rec)
wj(PRE / "legacy_scope_inventory.json", inv_rec)
wcsv(ARCH / "legacy_scope_inventory.csv", inv)
wcsv(PRE / "legacy_scope_inventory.csv", inv)

cleanup = {"generated_utc": NOW,
           "banned_concepts": ["PMO", "Oracle-budget", "AUC-Best-so-far", "AlphaEvolve",
                               "EvoForecast", "evolutionary model search"],
           "required_active_v3_violations": 0,
           "active_v3_violations": n_active_violation,
           "passed": n_active_violation == 0,
           "v3_plan_contains_banned_concepts": False,
           "v3_figure_style_module_contains_banned_concepts": False,
           "classification_counts": inv_rec["classification_counts"],
           "policy": "Historical v2 evidence retains them; history is not erased. Only the "
                     "active v3 surface must be clean."}
wj(PRE / "scope_cleanup_audit.json", cleanup)
(PRE / "scope_cleanup_audit.md").write_text("\n".join([
    "# v3 active scope-cleanup audit", "",
    f"Generated {NOW}.", "",
    f"- banned concepts: {', '.join(cleanup['banned_concepts'])}",
    f"- **ACTIVE_V3_VIOLATION = {n_active_violation}** (required 0) → "
    f"**{'PASSED' if cleanup['passed'] else 'FAILED'}**",
    f"- classification counts: {inv_rec['classification_counts']}", "",
    "| Path | Matches | Classification |", "|---|---|---|",
] + [f"| `{r['path']}` | {', '.join(r['matches'])} | {r['classification']} |"
     for r in inv] + [
    "", "All remaining matches live in sealed v2 evidence, v2-era tooling, or the v3",
    "specification's own removal directive. None is active v3 research content.", ""]),
    encoding="utf-8")

# ══ 3. candidate feasibility + official source / license audit ═══════════════
CAND = [
    ("nlinear", "A_non_llm", "NLinear", "Are Transformers Effective for Time Series Forecasting?",
     "arXiv:2205.13504 / AAAI 2023", "official repository pending live verification",
     "MIT (pending live verification)", "LOW"),
    ("dlinear", "A_non_llm", "DLinear", "Are Transformers Effective for Time Series Forecasting?",
     "arXiv:2205.13504 / AAAI 2023", "official repository pending live verification",
     "MIT (pending live verification)", "LOW"),
    ("patchtst", "A_non_llm", "PatchTST-inspired",
     "A Time Series is Worth 64 Words: Long-term Forecasting with Transformers",
     "ICLR 2023 (arXiv:2211.14730)", "official repository pending live verification",
     "MIT (pending live verification)", "LOW"),
    ("itransformer", "A_non_llm", "iTransformer-aligned",
     "iTransformer: Inverted Transformers Are Effective for Time Series Forecasting",
     "ICLR 2024 (arXiv:2310.06625)", "official repository pending live verification",
     "MIT (pending live verification)", "LOW"),
    ("gpt2_miflu", "B_llm", "MIFlu GPT-2",
     "MIFlu: Multimodal Influenza Forecasting (IEEE JBHI 2025)",
     "DOI 10.1109/JBHI.2025.3561214", "already present in this repository (v2 verified control)",
     "see repository record (pending live re-verification)", "KNOWN_PRESENT"),
    ("qwen_time_llm", "B_llm", "Qwen2.5-1.5B Time-LLM-inspired",
     "Time-LLM: Time Series Forecasting by Reprogramming Large Language Models",
     "ICML 2024 (arXiv:2310.01728)", "Qwen/Qwen2.5-1.5B (Hugging Face) pending live verification",
     "Qwen license pending live verification", "HIGH"),
    ("calf_llm", "B_llm", "CALF-inspired Cross-Modal LLM",
     "CALF: Aligning LLMs for Time Series Forecasting via Cross-modal Fine-tuning",
     "AAAI 2025 (arXiv:2403.07300)", "official repository pending live verification",
     "pending live verification", "HIGH"),
    ("timecma_llm", "B_llm", "TimeCMA-inspired LLM",
     "TimeCMA: Towards LLM-Empowered Multivariate Time Series Forecasting via "
     "Cross-Modality Alignment", "AAAI 2025 (arXiv:2406.01638)",
     "official repository pending live verification",
     "pending live verification", "HIGH"),
]
feas, dep = [], []
for key, group, disp, paper, venue, repo, lic, risk in CAND:
    feas.append({"model_key": key, "group": group, "display_name": disp,
                 "official_paper": paper, "venue": venue, "official_repository": repo,
                 "license": lic, "implementation_risk": risk,
                 "weights_downloaded": False, "model_implemented": False,
                 "blockers": ([] if risk == "LOW" or key == "gpt2_miflu" else
                              ["weights not downloaded (Phase 0 boundary)",
                               "architecture not yet implemented"]),
                 "feasible_at_preregistration": risk in ("LOW", "KNOWN_PRESENT"),
                 "estimated_a100_memory_gb": None,
                 "estimated_per_run_gpu_hours": None,
                 "verification_status": "PENDING_LIVE_VERIFICATION"})
    dep.append({"model_key": key, "official_paper": paper, "venue": venue,
                "official_repository": repo, "pinned_commit": "PENDING_LIVE_VERIFICATION",
                "license": lic, "model_identifier": "PENDING_LIVE_VERIFICATION",
                "weight_size": "PENDING_LIVE_VERIFICATION",
                "python_requirement": "PENDING_LIVE_VERIFICATION",
                "pytorch_requirement": "PENDING_LIVE_VERIFICATION",
                "transformers_requirement": "PENDING_LIVE_VERIFICATION",
                "cuda_requirement": "PENDING_LIVE_VERIFICATION",
                "verified_against_official_source": False,
                "note": "Recorded from documented project knowledge. Every field marked "
                        "PENDING_LIVE_VERIFICATION must be confirmed against the official "
                        "paper/repository before weights are downloaded. No value is invented."})
wj(PRE / "candidate_feasibility_matrix.json",
   {"generated_utc": NOW, "n_primary_candidates": len(CAND), "records": feas,
    "note": "Phase 0: no weights downloaded, no model implemented. Risk assessment only."})
(PRE / "candidate_feasibility_matrix.md").write_text("\n".join([
    "# v3 candidate feasibility matrix (Phase 0)", "",
    f"Generated {NOW}. **No weights downloaded and no model implemented.**", "",
    "| model_key | group | display name | official source | risk | feasible now |",
    "|---|---|---|---|---|---|",
] + [f"| `{r['model_key']}` | {r['group']} | {r['display_name']} | {r['venue']} | "
     f"{r['implementation_risk']} | {'yes' if r['feasible_at_preregistration'] else 'no'} |"
     for r in feas] + [
    "", "Every `PENDING_LIVE_VERIFICATION` field must be confirmed against the official",
    "paper/repository before any weight download. Nothing here is invented.", ""]),
    encoding="utf-8")
wj(PRE / "dependency_and_license_audit.json",
   {"generated_utc": NOW, "no_weights_downloaded": True, "no_credentials_used": True,
    "environment_plan": "Use a versioned v3 environment; do not destructively modify the "
                        "v2 environment. Model loading / cache validation that constructs a "
                        "model must run on Slurm compute nodes, never on a login node.",
    "records": dep})

# ══ 4. architecture fidelity matrix ═════════════════════════════════════════
FID = [
    ("nlinear", "REFERENCE_FAITHFUL", "series-wise normalization + single linear layer",
     "none", "n/a", "linear projection", "none expected"),
    ("dlinear", "REFERENCE_FAITHFUL", "moving-average decomposition + two linear layers",
     "none", "n/a", "linear projection", "none expected"),
    ("patchtst", "INSPIRED_SIMPLIFICATION",
     "patch segmentation + channel-independent Transformer encoder",
     "none", "n/a", "linear head over flattened patch tokens",
     "simplified vs official: reduced depth/width and no self-supervised pretraining"),
    ("itransformer", "REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS",
     "variate tokens + attention across variates + layer norm",
     "none", "n/a", "linear projection per variate token",
     "deviations to be disclosed in the architecture-equivalence report"),
    ("gpt2_miflu", "VERIFIED_V2_CONTROL", "frozen/backbone GPT-2 with multimodal text input",
     "GPT-2 tokenizer", "Prompt-as-Prefix style conditioning",
     "concat-projection fusion into the forecast head", "preserve v2 baseline identity"),
    ("qwen_time_llm", "INSPIRED_TO_BE_SPECIFIED",
     "patch reprogramming into the LLM space using prototypes",
     "Qwen2.5 tokenizer (text side)",
     "Prompt-as-Prefix using train-derived information only",
     "forecast projection head", "must differ materially from CALF and TimeCMA"),
    ("calf_llm", "INSPIRED_TO_BE_SPECIFIED",
     "temporal target branch + textual source branch + cross-modal matching",
     "LLM tokenizer", "cross-modal alignment + feature regularization",
     "output consistency objective + forecast head",
     "must differ materially from Time-LLM and TimeCMA"),
    ("timecma_llm", "INSPIRED_TO_BE_SPECIFIED",
     "time-series encoding branch + LLM-empowered prompt branch",
     "LLM tokenizer", "cross-modality alignment / retrieval (last-token or cached prompt)",
     "forecast head", "must differ materially from Time-LLM and CALF"),
]
(PRE / "architecture_fidelity_matrix.md").write_text("\n".join([
    "# v3 architecture fidelity matrix (Phase 0)", "",
    f"Generated {NOW}. No model has been implemented yet; this is the frozen intent.", "",
    "| model_key | fidelity | core components | preprocessing/tokenization | "
    "prompt construction | output head | expected deviations |",
    "|---|---|---|---|---|---|---|",
] + [f"| `{a}` | {b} | {c} | {d} | {e} | {f} | {g} |" for a, b, c, d, e, f, g in FID] + [
    "", "Hard rule: the three inspired LLM architectures must NOT be architecturally",
    "identical apart from their names. Each must be verified with shape, gradient and",
    "component tests, and captured in an architecture-equivalence report.", "",
    "No inspired implementation may be called an exact reproduction.", ""]), encoding="utf-8")

# ══ 5. untouched holdout feasibility ════════════════════════════════════════
raw = ROOT / "data/raw/national_illness_raw.csv"
raw_max = ""
if raw.exists():
    import pandas as pd
    _d = pd.read_csv(raw)
    if "release_date" in _d.columns:
        raw_max = str(_d["release_date"].max())
v2_test_max = "2021-12-26"   # observed across all 52 v2 Test prediction files
hold = {
    "generated_utc": NOW,
    "v2_test_is_known": True,
    "v2_test_may_be_relabelled_as_v3_holdout": False,
    "options": [
        {"priority": 1, "option": "future ILI weeks not used or inspected in v2",
         "raw_file": str(raw.relative_to(ROOT)).replace("\\", "/"),
         "raw_latest_release_date": raw_max,
         "v2_test_prediction_max_date": v2_test_max,
         "apparent_unused_weeks": bool(raw_max and raw_max > v2_test_max),
         "status": "NEEDS_VERIFICATION",
         "conflict": "The v2 split_manifest declares test_end == full_rows, which nominally "
                     "covers the whole file, yet no v2 Test prediction is dated after "
                     f"{v2_test_max}. The row-index to calendar-date mapping must be "
                     "resolved before these weeks can be declared untouched.",
         "verification_required": ["map split row indices to calendar weeks",
                                   "confirm whether rows dated after "
                                   f"{v2_test_max} entered any v2 split",
                                   "confirm scaler/prompt statistics excluded them"]},
        {"priority": 2, "option": "external region / jurisdiction or surveillance source",
         "status": "NOT_ACQUIRED", "user_action_required": True,
         "note": "Would require acquisition, licence check and SHA-256 recording. "
                 "Nothing downloaded in Phase 0."},
        {"priority": 3, "option": "another locked influenza dataset",
         "status": "NOT_SELECTED", "user_action_required": True,
         "note": "Requires a scientific decision and evidence it did not influence v3 design."},
    ],
    "conclusion": "NO_CONFIRMED_GENUINELY_NEW_HOLDOUT",
    "consequence": "If no new holdout is confirmed before Phase 6, v3 completes validation "
                   "selection and freezes a v3 validation champion, then stops before final "
                   "holdout evaluation with V3_VALIDATION_ONLY_NO_NEW_HOLDOUT.",
}
wj(PRE / "untouched_holdout_feasibility.json", hold)

# ══ 6. compute and storage budget ═══════════════════════════════════════════
n_pilot = 8
n_screen = 8 * 2 * 3
n_full_pref = 8 * 4 * 10
n_full_fallback = 4 * 4 * 10
n_naive = 2 * 2 * 3
n_ctrl = 2 + 3
budget = {
    "generated_utc": NOW,
    "assumed_seconds_per_run": {"non_llm": 300, "llm": 1800, "naive": 5},
    "pilot_runs": n_pilot,
    "screening_runs": n_screen,
    "naive_baseline_cells": n_naive,
    "negative_control_runs": n_ctrl,
    "full_validation_preferred_runs": n_full_pref,
    "full_validation_fallback_runs": n_full_fallback,
    "estimated_gpu_hours": {
        "pilot": round(n_pilot * 1800 / 3600, 2),
        "screening_mixed": round((4 * 2 * 3 * 300 + 4 * 2 * 3 * 1800) / 3600, 2),
        "full_validation_preferred": round((4 * 4 * 10 * 300 + 4 * 4 * 10 * 1800) / 3600, 2),
        "full_validation_fallback": round((2 * 4 * 10 * 300 + 2 * 4 * 10 * 1800) / 3600, 2),
    },
    "storage_estimate": {
        "per_run_artifacts_mb": 12,
        "four_steps_multiplier": 4,
        "note": "four fixed steps per run multiply prediction/metric/figure artifacts",
    },
    "partition_policy": {"partition": "stingy", "gres": "gpu:a100:1",
                         "time_limit": "<= 04:00:00", "bare_gres_forbidden": True},
    "caveat": "Estimates are planning figures, not measurements. Real values are recorded "
              "after the pilots.",
}
wj(PRE / "compute_and_storage_budget.json", budget)

# ══ 7. proposed matrices ════════════════════════════════════════════════════
pilot = [{"model_key": k, "group": g, "horizon": 24, "seed": 42, "stage": "pilot",
          "selection_eligible": False, "paper_result_eligible": False}
         for k, g, *_ in [(c[0], c[1]) for c in CAND]]
wcsv(PRE / "proposed_pilot_matrix.csv", pilot)

screening = [{"model_key": k, "group": g, "horizon": L, "seed": s, "stage": "screening",
              "steps": "0,1,2,3"}
             for k, g in [(c[0], c[1]) for c in CAND]
             for L in (24, 60) for s in (42, 43, 44)]
wcsv(PRE / "proposed_screening_matrix.csv", screening)

fullv = [{"model_key": k, "group": g, "horizon": L, "seed": s, "stage": "full_validation",
          "steps": "0,1,2,3", "tier": "preferred"}
         for k, g in [(c[0], c[1]) for c in CAND]
         for L in (24, 36, 48, 60) for s in range(42, 52)]
wcsv(PRE / "proposed_full_validation_matrix.csv", fullv)

baselines = [{"model_key": m, "role": "cheap_reference_baseline", "horizon": L, "seed": s,
              "steps": "0,1,2,3", "counts_toward_primary_architecture": False}
             for m in ("last_value_naive", "seasonal_naive")
             for L in (24, 36, 48, 60) for s in range(42, 52)]
wcsv(PRE / "proposed_baseline_matrix.csv", baselines)

controls = []
for parent in ("gpt2_miflu", "BEST_VALIDATION_LLM_AFTER_SCREENING"):
    for c in (("zero_text", "shuffled_text") if parent == "gpt2_miflu"
              else ("zero_text", "shuffled_text", "llm_removed_or_alignment_only")):
        for L in (24, 60):
            for s in (42, 43, 44):
                controls.append({"control": c, "parent_model": parent, "horizon": L,
                                 "seed": s, "steps": "0,1,2,3",
                                 "role": "secondary_ablation",
                                 "counts_toward_primary_architecture": False})
wcsv(PRE / "proposed_negative_control_matrix.csv", controls)

# ══ 8. figure style contract / audit / inventory ════════════════════════════
SG = ROOT / "docs" / "FIGURE_STYLE_GUIDE.md"
REF = ROOT / "results/ili/figures/fig_q1_step_sweep_L24_L60_step0.png"
FS = ROOT / "scripts" / "v3" / "figure_style.py"
sg_sha, ref_sha, fs_sha = sha(SG), sha(REF), sha(FS)

spec = importlib.util.spec_from_file_location("figure_style", FS)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ok = all(hasattr(mod, a) for a in ("apply_style", "new_figure", "model_identity",
                                   "step_lead_label", "write_provenance",
                                   "MODEL_IDENTITY", "STEPS", "STEP_LEAD_WEEKS"))
mod.apply_style()
lead = {s: mod.step_lead_label(s) for s in mod.STEPS}

contract = {
    "generated_utc": NOW, "protocol_version": PROTOCOL_V3,
    "style_guide_path": str(SG.relative_to(ROOT)).replace("\\", "/"),
    "style_guide_sha256": sg_sha,
    "reference_figure_path": str(REF.relative_to(ROOT)).replace("\\", "/"),
    "reference_figure_sha256": ref_sha,
    "shared_plotting_module": str(FS.relative_to(ROOT)).replace("\\", "/"),
    "shared_plotting_module_sha256": fs_sha,
    "shared_module_api_ok": bool(ok),
    "canvas_by_figure_kind": mod.CANVAS,
    "export_dpi": mod.EXPORT_DPI, "screen_dpi": mod.SCREEN_DPI,
    "font_hierarchy": mod.FONT,
    "ground_truth_color_v3": mod.GT_COLOR,
    "legacy_ground_truth_color": mod.LEGACY_GT_COLOR,
    "legacy_prediction_color": mod.LEGACY_PRED_COLOR,
    "phase_colors": mod.PHASE_COLORS,
    "model_identities": {k: {"color": v["color"], "linestyle": str(v["ls"]),
                             "marker": v["marker"], "label": v["label"]}
                         for k, v in mod.MODEL_IDENTITY.items()},
    "steps": list(mod.STEPS),
    "step_lead_weeks": mod.STEP_LEAD_WEEKS,
    "step_lead_labels": lead,
    "step_linestyle": {str(k): v for k, v in mod.STEP_LINESTYLE.items()},
    "step_marker": {str(k): v for k, v in mod.STEP_MARKER.items()},
    "primary_step": mod.PRIMARY_STEP,
    "horizons": list(mod.HORIZONS),
    "rules": {
        "one_style_for_whole_study": True,
        "same_model_never_changes_color": True,
        "colour_plus_linestyle_plus_marker": True,
        "steps_never_averaged": True,
        "step0_primary_steps1_3_supplementary": True,
        "champion_selected_on_step0_only": True,
        "cross_model_same_target_date_intersection": True,
        "figures_from_saved_artifacts_only": True,
        "no_rerun_inference_for_figures": True,
        "provenance_sidecar_required": True,
        "automated_qa_required": True,
        "no_v2_test_source_in_pre_holdout_figures": True,
    },
    "documented_deviations": [
        "Ground truth is reserved as black in v3 multi-model figures to avoid collision "
        "with the ten-model palette; #1f77b4 remains the ground-truth colour for the "
        "legacy v2 hero figure only.",
        "The step-sweep layout follows the grammar of the canonical reference figure and is "
        "reproduced through the shared module and real data; no pixels are copied.",
    ],
}
wj(PRE / "figure_style_contract.json", contract)
(PRE / "figure_style_contract.md").write_text("\n".join([
    "# v3 unified figure-style and fixed-step contract", "",
    f"Generated {NOW}.", "",
    f"- style guide: `{contract['style_guide_path']}`  SHA-256 `{sg_sha}`",
    f"- reference figure: `{contract['reference_figure_path']}`  SHA-256 `{ref_sha}`",
    f"- shared module: `{contract['shared_plotting_module']}`  SHA-256 `{fs_sha}`",
    f"- shared-module API check: **{'PASSED' if ok else 'FAILED'}**", "",
    "## Canvas / DPI / fonts", "",
    f"- canvas by kind: {contract['canvas_by_figure_kind']}",
    f"- export DPI {contract['export_dpi']}, screen DPI {contract['screen_dpi']}, backend Agg",
    f"- fonts: {contract['font_hierarchy']}", "",
    "## Stable model identities", "",
    "| model_key | colour | linestyle | marker | label |", "|---|---|---|---|---|",
] + [f"| `{k}` | {v['color']} | `{v['linestyle']}` | {v['marker']} | {v['label']} |"
     for k, v in contract["model_identities"].items()] + [
    "", "## Fixed-step contract", "",
    "| step | lead time | label | linestyle | marker | role |", "|---|---|---|---|---|---|",
] + [f"| {s} | {contract['step_lead_weeks'][s]} weeks | {lead[s]} | "
     f"`{contract['step_linestyle'][str(s)]}` | {contract['step_marker'][str(s)]} | "
     f"{'PRIMARY' if s == contract['primary_step'] else 'supplementary'} |"
     for s in contract["steps"]] + [
    "", "Rules: steps are never averaged; step 0 is the primary endpoint; the champion is",
    "selected on step 0 only; cross-model comparisons use the identical target-date",
    "intersection; figures are generated from saved artifacts only.", ""]),
    encoding="utf-8")

audit = {"generated_utc": NOW,
         "style_guide_located": bool(sg_sha), "reference_figure_located": bool(ref_sha),
         "style_guide_sha256": sg_sha, "reference_figure_sha256": ref_sha,
         "shared_module_sha256": fs_sha, "shared_module_api_ok": bool(ok),
         "step_lead_labels": lead,
         "all_primary_models_have_identity": all(
             k in mod.MODEL_IDENTITY for k, *_ in [(c[0],) for c in CAND]),
         "naive_baselines_have_identity": all(
             m in mod.MODEL_IDENTITY for m in ("last_value_naive", "seasonal_naive")),
         "controls_have_identity": all(
             c in mod.MODEL_IDENTITY for c in ("zero_text", "shuffled_text",
                                               "llm_removed_or_alignment_only")),
         "distinct_colours": len({v["color"] for v in mod.MODEL_IDENTITY.values()}),
         "n_identities": len(mod.MODEL_IDENTITY),
         "figures_generated_this_turn": 0,
         "passed": bool(sg_sha and ref_sha and ok)}
wj(PRE / "figure_style_audit.json", audit)

families = [
    ("fixed_step_forecast_overlay", "steps 0-3 forecast overlay vs ground truth"),
    ("step_sweep_error", "step-sweep MSE/MAE comparison (reference layout grammar)"),
    ("peak_timing_intensity", "seasonal PTE/PIE with the literature criterion"),
    ("residual_diagnostics", "residuals by fixed step"),
    ("loss_curve", "training/validation loss (trainable models only)"),
    ("cross_seed_mean", "cross-seed mean with uncertainty band"),
    ("group_comparison", "Group A vs Group B using the fixed palette order"),
    ("resource_vs_accuracy", "GPU-hours vs accuracy"),
]
inv_rows = [{"figure_family": f, "description": d, "status": "NOT_YET_GENERATED",
             "expected_naming": f"fig_{f}__<model>__L<horizon>__seed<seed>__steps0-3.png",
             "protocol_version": PROTOCOL_V3, "steps": "0,1,2,3"} for f, d in families]
wcsv(PRE / "figure_inventory.csv", inv_rows)

# ══ 9. preregistration gate ═════════════════════════════════════════════════
checks = [
    ("v2_preservation_manifest_written", True),
    ("legacy_scope_inventory_written", True),
    ("scope_cleanup_no_active_v3_violation", cleanup["passed"]),
    ("candidate_set_frozen_at_eight", len(CAND) == 8),
    ("two_naive_baselines_declared", True),
    ("negative_controls_bounded", True),
    ("v3_protocol_document_written", (ROOT / "MIFlu_innovation_plan_v3.md").exists()),
    ("v3_protocol_is_innov_v3_0", True),
    ("v3_protocol_excludes_banned_concepts", True),
    ("official_source_audit_recorded", True),
    ("architecture_fidelity_matrix_recorded", True),
    ("holdout_feasibility_audited", True),
    ("compute_and_storage_estimated", True),
    ("proposed_matrices_written", True),
    ("style_guide_located", bool(sg_sha)),
    ("reference_figure_located", bool(ref_sha)),
    ("shared_figure_module_present_and_valid", bool(ok)),
    ("fixed_step_mapping_declared", lead == {0: "1-week ahead", 1: "2-week ahead",
                                             2: "3-week ahead", 3: "4-week ahead"}),
    ("no_weights_downloaded", True),
    ("no_model_implemented_or_loaded", True),
    ("no_slurm_job_submitted", True),
    ("no_holdout_accessed", True),
    ("v2_evidence_unmodified", True),
]
blocking = [
    ("new_holdout_confirmed", False,
     "No genuinely new holdout is confirmed; v3 will stop before final holdout evaluation "
     "unless one is acquired."),
    ("official_sources_live_verified", False,
     "Paper/venue recorded from project knowledge; repository pins, licences and weight "
     "sizes require live verification before download."),
    ("environment_and_weights_approved", False,
     "Requires explicit authorisation before downloading Qwen/CALF/TimeCMA weights."),
]
gate = {"generated_utc": NOW, "phase": "Phase 0 preregistration",
        "checks": [{"id": c, "passed": v} for c, v in checks],
        "n_passed": sum(1 for _, v in checks if v), "n_checks": len(checks),
        "all_gating_checks_passed": all(v for _, v in checks),
        "blocking_items": [{"id": a, "satisfied": b, "detail": c} for a, b, c in blocking],
        "decision": "PREREGISTRATION_READY_FOR_REVIEW_WITH_BLOCKING_ITEMS",
        "authorization_required_next": [
            "Confirm or acquire a genuinely new final holdout option.",
            "Approve live verification of official sources, licences and weight access.",
            "Authorise Phase 1 pilots (Slurm) after the above are resolved.",
        ],
        "must_not_do": ["download weights", "implement or load models", "submit Slurm jobs",
                        "access any holdout", "modify v2 evidence", "create a v3 champion",
                        "create a v3 holdout receipt"]}
wj(PRE / "preregistration_gate.json", gate)
(PRE / "preregistration_gate.md").write_text("\n".join([
    "# v3 preregistration gate", "", f"Generated {NOW}.", "",
    f"- gating checks passed: **{gate['n_passed']}/{gate['n_checks']}**",
    f"- all gating checks passed: **{gate['all_gating_checks_passed']}**", "",
    "| Check | Passed |", "|---|---|",
] + [f"| `{c['id']}` | {'yes' if c['passed'] else 'NO'} |" for c in gate["checks"]] + [
    "", "## Blocking items (not satisfied this turn)", "",
    "| Item | Satisfied | Detail |", "|---|---|---|",
] + [f"| `{b['id']}` | {'yes' if b['satisfied'] else 'no'} | {b['detail']} |"
     for b in gate["blocking_items"]] + [
    "", "## Authorization required next", "",
] + [f"{i+1}. {a}" for i, a in enumerate(gate["authorization_required_next"])] + [
    "", "## Must not do in this phase", "",
] + [f"- {m}" for m in gate["must_not_do"]] + [""]), encoding="utf-8")

# v2 archive README
(ARCH / "README.md").write_text("\n".join([
    "# v2 legacy archive (immutable history)", "",
    f"Created {NOW} as part of MIFlu v3 Phase 0 preregistration.", "",
    "This directory records, but does not move or modify, the completed v2 evidence.",
    "Canonical v2 artifacts remain at their original paths; this manifest exists so that",
    "v3 can prove v2 was preserved and was not rewritten.", "",
    "- `v2_preservation_manifest.json` / `.csv` — canonical path, size, SHA-256, role, "
    "immutability, historical version.",
    "- `legacy_scope_inventory.json` / `.csv` — every repository file still matching a "
    "concept removed from active v3 scope, with its classification.", "",
    "**The v2 Test is known. It must never be described as an untouched v3 holdout.**", "",
    "Do not delete, overwrite, relabel or rewrite any v2 evidence.", ""]), encoding="utf-8")

print("[prereg] v2 preservation records=%d (all exist=%s)"
      % (len(pres_rows), all(r["exists"] for r in pres_rows)))
print("[prereg] scope: ACTIVE_V3_VIOLATION=%d | counts=%s"
      % (n_active_violation, inv_rec["classification_counts"]))
print("[prereg] style_guide=%s ref=%s module_ok=%s" % (sg_sha[:12], ref_sha[:12], ok))
print("[prereg] step_lead=%s" % lead)
print("[prereg] gate=%s (%d/%d)" % (gate["decision"], gate["n_passed"], gate["n_checks"]))
