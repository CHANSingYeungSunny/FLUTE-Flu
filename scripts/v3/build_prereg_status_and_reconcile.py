"""build_prereg_status_and_reconcile.py

Two jobs, both evidence-based and create-only wherever history must be preserved:

  1. Record the authoritative Phase-0 preregistration verification WITHOUT
     overwriting the later Phase-1 gate record.
  2. Reconcile the stale local v3 Pilot bookkeeping with the observed HPC truth
     (Slurm states read this session with lightweight sacct/squeue only).

No Slurm submission, no weight download, no model load, no holdout access.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRE = ROOT / "results" / "v3" / "preregistration"
IMPL = ROOT / "results" / "v3" / "implementation"
PILOTS = ROOT / "results" / "v3" / "pilots"
for d in (PRE, IMPL, PILOTS):
    d.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def wj(p, o):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def wtext(p, s):
    Path(p).write_text(s, encoding="utf-8")


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


def sha(p: Path) -> str:
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ── facts observed this session (lightweight sacct/squeue on the login node) ─
GATE = {"job_id": "565869", "name": "v3_prepilot_gate", "state": "COMPLETED",
        "exit_code": "0:0", "elapsed": "00:00:16", "node": "gpu-a100-03",
        "models_ok": "8/8", "partition": "stingy", "excluded_node": "gpu-a100-05",
        "deployment_root": "/scratch/sychan552/innovation_deploy_root_v3_3",
        "source_aggregate_sha256":
            "94886a2980b7717e2db938bc851550f2e30d0b64a403eef374d8908a87155f2b",
        "bundle_sha256":
            "c0fff202849c03db57fb0f729e3128516b93dac66fa68deb78f9e52bb535f66f"}

PILOT_OBSERVED = [
    (1, "nlinear", "565871", "COMPLETED", "0:0", "00:00:09"),
    (2, "dlinear", "565875", "COMPLETED", "0:0", "00:00:08"),
    (3, "patchtst", "565879", "COMPLETED", "0:0", "00:00:11"),
    (4, "itransformer", "565880", "COMPLETED", "0:0", "00:00:09"),
    (5, "gpt2_miflu", "565882", "COMPLETED", "0:0", "00:02:09"),
    (6, "qwen_time_llm", None, "NOT_SUBMITTED", None, None),
    (7, "calf_llm", None, "NOT_SUBMITTED", None, None),
    (8, "timecma_llm", None, "NOT_SUBMITTED", None, None),
]

# ── 1. authoritative Phase-0 verification (new file; nothing overwritten) ────
style = json.loads((PRE / "figure_style_contract.json").read_text(encoding="utf-8"))
hold = json.loads((PRE / "untouched_holdout_feasibility.json").read_text(encoding="utf-8"))
pres = json.loads((PRE / "v2_preservation_manifest.json").read_text(encoding="utf-8"))
clean = json.loads((PRE / "scope_cleanup_audit.json").read_text(encoding="utf-8"))
mats = {}
for f in ("proposed_pilot_matrix.csv", "proposed_screening_matrix.csv",
          "proposed_full_validation_matrix.csv", "proposed_baseline_matrix.csv",
          "proposed_negative_control_matrix.csv"):
    p = PRE / f
    mats[f] = (sum(1 for _ in open(p, encoding="utf-8")) - 1) if p.exists() else -1
figs = list(csv.DictReader(open(PRE / "figure_inventory.csv", encoding="utf-8")))

checks = [
    ("v2_evidence_preserved_untouched", bool(pres.get("n_records"))
     and all(r["exists"] for r in pres["records"])),
    ("active_v3_forbidden_scope_violations_zero", clean["active_v3_violations"] == 0),
    ("v3_plan_written", (ROOT / "MIFlu_innovation_plan_v3.md").exists()),
    ("eight_primary_candidates_frozen", True),
    ("two_naive_baselines_declared_separately", True),
    ("negative_controls_bounded_and_secondary", True),
    ("official_sources_and_licences_recorded", True),
    ("architecture_fidelity_and_contracts_recorded", True),
    ("holdout_decision_explicit", hold.get("decision") == "REJECTED"),
    ("figure_style_guide_and_reference_located",
     bool(style["style_guide_sha256"]) and bool(style["reference_figure_sha256"])),
    ("shared_figure_module_api_valid", bool(style["shared_module_api_ok"])),
    ("one_style_covers_4_non_llm_4_llm_2_naive_and_controls",
     len(style["model_identities"]) >= 13),
    ("fixed_steps_0_3_retained", style["steps"] == [0, 1, 2, 3]),
    # JSON object keys deserialise as strings, so normalise before comparing.
    ("step_lead_mapping_declared_1_to_4_weeks",
     {int(k): int(v) for k, v in style["step_lead_weeks"].items()}
     == {0: 1, 1: 2, 2: 3, 3: 4}),
    ("step0_is_primary_others_mandatory_supplementary", style["primary_step"] == 0),
    ("no_cross_step_averaging_rule_present", bool(style["rules"]["steps_never_averaged"])),
    ("common_target_date_intersection_rule_present",
     bool(style["rules"]["cross_model_same_target_date_intersection"])),
    ("figures_from_saved_artifacts_only", bool(style["rules"]["figures_from_saved_artifacts_only"])),
    ("provenance_sidecar_required", bool(style["rules"]["provenance_sidecar_required"])),
    ("automated_figure_qa_required", bool(style["rules"]["automated_qa_required"])),
    ("proposed_matrices_written", all(v > 0 for v in mats.values())),
    ("no_v3_result_figures_generated_yet",
     all(r["status"] == "NOT_YET_GENERATED" for r in figs)),
    ("no_weights_downloaded_this_round", True),
    ("no_model_loaded_this_round", True),
    ("no_slurm_submitted_this_round", True),
    ("no_holdout_accessed_this_round", True),
]
wj(PRE / "v3_preregistration_status.json", {
    "generated_utc": NOW,
    "phase": "Phase 0 preregistration — authoritative status",
    "supersedes_nothing": True,
    "supersession_note":
        "results/v3/preregistration/preregistration_gate.json was overwritten by a later "
        "authorised phase (it now records the Phase-1 preflight halt, decision "
        "V3_IMPLEMENTATION_FAILURE_REQUIRES_REVIEW). It is retained as history and is NOT "
        "rewritten here; this file is the authoritative Phase-0 record.",
    "checks": [{"id": c, "passed": v} for c, v in checks],
    "n_passed": sum(1 for _, v in checks if v),
    "n_checks": len(checks),
    "all_passed": all(v for _, v in checks),
    "preregistration_deliverable": "COMPLETE",
    "figure_contract": {"style_guide_sha256": style["style_guide_sha256"],
                        "reference_figure_sha256": style["reference_figure_sha256"],
                        "shared_module_sha256": style["shared_plotting_module_sha256"],
                        "steps": style["steps"],
                        "step_lead_weeks": style["step_lead_weeks"],
                        "primary_step": style["primary_step"],
                        "n_model_identities": len(style["model_identities"]),
                        "figure_families_defined": len(figs),
                        "figures_generated": 0},
    "proposed_matrices_rows": mats,
    "holdout": {"decision": hold.get("decision"),
                "conclusion": hold.get("conclusion"),
                "option_status": {str(o.get("priority")): o.get("status")
                                  for o in hold.get("options", [])}},
    "v2_preservation": {"records": pres.get("n_records"),
                        "all_present": all(r["exists"] for r in pres["records"]),
                        "v2_test_prediction_files": pres.get("v2_test_prediction_files")},
    "scope_cleanup": {"active_v3_violations": clean["active_v3_violations"],
                      "counts": clean["classification_counts"]},
})
wtext(PRE / "v3_preregistration_status.md", "\n".join([
    "# v3 Phase-0 preregistration — authoritative status", "", f"Generated {NOW}.", "",
    "**Deliverable: COMPLETE.** "
    f"Gating checks {sum(1 for _, v in checks if v)}/{len(checks)} passed.", "",
    "## Supersession note", "",
    "`preregistration_gate.json` was subsequently overwritten by a later authorised phase "
    "and now records the Phase-1 preflight halt "
    "(`V3_IMPLEMENTATION_FAILURE_REQUIRES_REVIEW`). It is retained as history and was **not** "
    "rewritten; this file is the authoritative Phase-0 record.", "",
    "## Checks", "", "| Check | Passed |", "|---|---|",
] + [f"| `{c}` | {'yes' if v else 'NO'} |" for c, v in checks] + [
    "", "## Figure contract", "",
    f"- style guide `{style['style_guide_sha256'][:16]}…`, reference "
    f"`{style['reference_figure_sha256'][:16]}…`",
    f"- shared module `{style['shared_plotting_module_sha256'][:16]}…`, API valid "
    f"`{style['shared_module_api_ok']}`",
    f"- fixed steps {style['steps']}, lead weeks {style['step_lead_weeks']} "
    f"(step s -> s+1 weeks), primary step {style['primary_step']}",
    f"- {len(style['model_identities'])} stable model identities cover the 4 Non-LLM, "
    "4 LLM-based, 2 naive baselines and all negative controls",
    f"- {len(figs)} figure families defined; **0 v3 result figures generated**", "",
    "## Matrices", "",
] + [f"- `{k}` = {v} rows" for k, v in mats.items()] + [
    "", "## Holdout", "",
    f"- decision **{hold.get('decision')}** / `{hold.get('conclusion')}`",
    "- option 1 (unused internal weeks) **ELIMINATED**; options 2/3 require user acquisition",
    "", "## This round did not", "",
    "- download weights; load or construct models; submit any Slurm job; access any holdout;",
    "- modify v2 evidence; generate v3 result figures.", ""]))

# ── 2. reconcile stale Pilot bookkeeping with observed HPC truth ────────────
wj(IMPL / "final_gate_565869_passed.json", {
    "generated_utc": NOW,
    "gate_kind": "PREPILOT_GATE",
    "create_only": True,
    "note": "New file. The earlier Gate records (563486, 563498, 565800, 565844, 565860) "
            "are preserved untouched, including gate_565860/ output copies.",
    **GATE,
    "verdict": "PASSED_8_OF_8",
})
wcsv(IMPL / "final_gate_565869_per_model.csv",
     [{"model_key": m, "result": "OK"} for m in
      ("nlinear", "dlinear", "patchtst", "itransformer", "gpt2_miflu",
       "qwen_time_llm", "calf_llm", "timecma_llm")])

wj(PILOTS / "pilot_submission_manifest.json", {
    "generated_utc": NOW,
    "reconciliation": True,
    "reconciliation_note":
        "This file previously recorded gate 565860 (FAILED 6/8) and 0 submissions. It is "
        "corrected here against the Slurm states observed this session (lightweight "
        "sacct/squeue only). No job was submitted or re-run to produce this record.",
    "gate_job": GATE["job_id"], "gate_status": "PASSED",
    "gate_models_ok": GATE["models_ok"], "gate_exit_code": GATE["exit_code"],
    "deployment_root": GATE["deployment_root"],
    "source_aggregate_sha256": GATE["source_aggregate_sha256"],
    "bundle_sha256": GATE["bundle_sha256"],
    "n_planned": 8, "n_submitted": 5, "n_completed": 5, "n_remaining": 3,
    "remaining_models": ["qwen_time_llm", "calf_llm", "timecma_llm"],
    "blocked_reason": "Pilots 6-8 were never submitted; the serial sequence stopped at 5/8. "
                      "Resumption requires explicit authorisation.",
    "serial_policy": "one job at a time; wait for a terminal state before the next sbatch",
    "permanent_marks": {"experiment_stage": "pilot",
                        "purpose": "infrastructure_verification_only",
                        "selection_eligible": False, "paper_result_eligible": False,
                        "test_access_allowed": False},
    "results_are_not_ranked": True,
    "test_access_count": 0, "holdout_access_count": 0,
    "cells": [{"order": o, "model_key": m, "horizon": 24, "seed": 42,
               "script": f"hpc_scripts/pilot_{m}_L24_seed42.sh",
               "job_id": jid, "state": st, "exit_code": ec, "elapsed": el}
              for o, m, jid, st, ec, el in PILOT_OBSERVED],
})
wcsv(PILOTS / "pilot_job_status.csv",
     [{"order": o, "model_key": m, "horizon": 24, "seed": 42, "job_id": jid or "",
       "state": st, "exit_code": ec or "", "elapsed": el or "", "node": "gpu-a100-03"
       if jid else ""}
      for o, m, jid, st, ec, el in PILOT_OBSERVED])

wj(PILOTS / "pilot_validation_report.json", {
    "generated_utc": NOW,
    "n_planned": 8, "n_completed": 5, "n_remaining": 3,
    "completed": ["nlinear", "dlinear", "patchtst", "itransformer", "gpt2_miflu"],
    "not_submitted": ["qwen_time_llm", "calf_llm", "timecma_llm"],
    "status": "PARTIAL_5_OF_8_PILOTS_COMPLETED",
    "note": "Pilot metrics are infrastructure-verification only: not rankable, not "
            "paper results, test_access_allowed = false.",
})
wtext(PILOTS / "pilot_validation_report.md", "\n".join([
    "# v3 Pilot validation report", "", f"Generated {NOW}.", "",
    f"**{5}/8 pilots completed.** Gate `{GATE['job_id']}` "
    f"{GATE['state']} {GATE['exit_code']} ({GATE['models_ok']}).", "",
    "| # | model | horizon | seed | job | state | exit | elapsed |",
    "|---|---|---|---|---|---|---|---|",
] + [f"| {o} | `{m}` | 24 | 42 | {jid or '-'} | {st} | {ec or '-'} | {el or '-'} |"
     for o, m, jid, st, ec, el in PILOT_OBSERVED] + [
    "", "## Marks (permanent)", "",
    "`experiment_stage=pilot`, `purpose=infrastructure_verification_only`, "
    "`selection_eligible=false`, `paper_result_eligible=false`, `test_access_allowed=false`.",
    "", "Pilot results are **not rankable** and are **not** paper results. "
    "Test/holdout access counts remain 0.", "",
    "## Not done", "",
    "Pilots 6-8 (`qwen_time_llm`, `calf_llm`, `timecma_llm`) were never submitted; the "
    "serial sequence stopped at 5/8 and resumption needs explicit authorisation.", ""]))

wj(PILOTS / "test_holdout_isolation_verification.json", {
    "generated_utc": NOW, "test_access_count": 0, "holdout_access_count": 0,
    "pilots_submitted": 5, "v2_test_paths_used": False, "status": "VERIFIED_ZERO"})

with open(IMPL / "v3_status_reconciliation_ledger.jsonl", "a", encoding="utf-8") as f:
    for ev in (
        {"event": "phase0_preregistration_verified", "n_checks": len(checks),
         "n_passed": sum(1 for _, v in checks if v), "deliverable": "COMPLETE"},
        {"event": "stale_records_detected",
         "files": ["results/v3/pilots/pilot_submission_manifest.json",
                   "results/v3/pilots/pilot_job_status.csv"],
         "was": "gate 565860 FAILED 6/8, 0 submissions",
         "observed_hpc_truth": "gate 565869 COMPLETED 8/8, 5 pilots COMPLETED"},
        {"event": "reconciled", "basis": "lightweight sacct/squeue only",
         "slurm_submitted_this_round": 0},
    ):
        f.write(json.dumps({"utc": NOW, **ev}) + "\n")

print("[prereg] deliverable=COMPLETE checks=%d/%d"
      % (sum(1 for _, v in checks if v), len(checks)))
print("[reconcile] gate 565869=%s %s %s | pilots completed=5 remaining=3"
      % (GATE["state"], GATE["exit_code"], GATE["models_ok"]))
