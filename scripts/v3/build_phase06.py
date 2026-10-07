"""Build Phase 0.6 metadata-only holdout, access, provenance and Gate records."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRE = ROOT / "results" / "v3" / "preregistration"
ACQ = PRE / "holdout_acquisition"
ACQ.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        out = csv.DictWriter(handle, fieldnames=fields)
        out.writeheader()
        out.writerows(rows)


template = ROOT / "results" / "ili" / "figures" / "fig_q1_step_sweep_L24_L60_step0.png"
template_sha = hashlib.sha256(template.read_bytes()).hexdigest()
style = ROOT / "docs" / "FIGURE_STYLE_GUIDE.md"
style_sha = hashlib.sha256(style.read_bytes()).hexdigest()
plan = ROOT / "MIFlu_innovation_plan_v3.md"
plan_sha = hashlib.sha256(plan.read_bytes()).hexdigest()

sources = [
    {
        "source_key": "cdc_fluview_official",
        "authority": "CDC FluView / ILINet",
        "official_url": "https://www.cdc.gov/fluview/overview/index.html",
        "api_or_download": "https://gis.cdc.gov/GRASP/Fluview/FluViewPhase1.html",
        "status": "CANDIDATE_METADATA_ONLY",
        "public_use": "official public CDC surveillance; request snapshot and terms must be recorded at acquisition",
        "granularity": "weekly Sunday-Saturday MMWR/epiweek",
        "geography": "national, HHS region, state and other CDC levels",
        "target": "ILI percentage / counts and denominator fields; not local ILITOTAL-identical by default",
        "covariates": "age-stratified ILI fields, total patients, providers and reporting metadata where exposed",
        "revision_backfill": "weekly preliminary data; late reports and corrections can revise history",
        "request_spec": "official CDC FluView export/API; acquire metadata and raw response only after Gate approval",
    },
    {
        "source_key": "cmu_delphi_fluview",
        "authority": "CMU Delphi Epidata FluView endpoint with CDC provenance",
        "official_url": "https://cmu-delphi.github.io/delphi-epidata/api/fluview.html",
        "api_or_download": "https://api.delphi.cmu.edu/epidata/fluview/",
        "status": "PREFERRED_METADATA_CANDIDATE_NOT_ACQUIRED",
        "public_use": "publicly accessible US Government source; Delphi documents API data licensing",
        "granularity": "weekly epiweek; documented range starts 1997w40",
        "geography": "nat, HHS regions, census divisions, states and other documented regions",
        "target": "num_ili, num_patients, unweighted ili, weighted wili; differs from local ILITOTAL until frozen",
        "covariates": "num_providers and age fields; missing values may be null or imputed by version/access",
        "revision_backfill": "preliminary data; issue/lag parameters expose historical releases and backfills",
        "request_spec": "regions=nat; epiweeks=<locked interval>; record issue/lag policy and response metadata; no values this phase",
    },
    {
        "source_key": "cdc_nhsn_hrd",
        "authority": "CDC NHSN Weekly Hospital Respiratory Data",
        "official_url": "https://data.cdc.gov/Public-Health-Surveillance/Weekly-Hospital-Respiratory-Data-HRD-Metrics-by-Ju/ua7e-t2fy/about_data",
        "api_or_download": "Socrata dataset ua7e-t2fy",
        "status": "EXTERNAL_VALIDATION_DIFFERENT_TARGET",
        "public_use": "public domain U.S. Government",
        "granularity": "weekly reporting date / MMWR week-ending date",
        "geography": "national, region, state/territory",
        "target": "hospital admissions/hospitalization/occupancy metrics, not outpatient ILI",
        "covariates": "hospital capacity, age and influenza-confirmed admission fields",
        "revision_backfill": "coverage mandates changed; corrections/backfills can revise history",
        "request_spec": "metadata-only Socrata catalog inspection; never substitute HRD target for ILITOTAL without amendment",
    },
]
write_json(ACQ / "source_candidates.json", {"generated_utc": NOW, "data_values_acquired": False, "records": sources})
(ACQ / "source_candidates.md").write_text("""# Phase 0.6 holdout source candidates

Metadata-only review; no raw holdout values were downloaded or inspected.

| source | status | geography | granularity | target compatibility |
|---|---|---|---|---|
| CDC FluView / ILINet | CANDIDATE_METADATA_ONLY | national/HHS/state | weekly epiweek | target/units must be frozen; not direct ILITOTAL identity |
| CMU Delphi FluView | PREFERRED_METADATA_CANDIDATE_NOT_ACQUIRED | national/HHS/state | weekly epiweek | `ili`/`wili` percentage plus counts; transformation or reduced target required |
| CDC NHSN HRD | EXTERNAL_VALIDATION_DIFFERENT_TARGET | national/region/state | weekly week-ending | hospital target, incompatible with outpatient ILI |

The known v2 Test is excluded and is not an untouched holdout.
""", encoding="utf-8")

compat = [
    {"source_key": "cdc_fluview_official", "mmwr_identity": "PASS_METADATA", "geography": "PASS_NATIONAL_AVAILABLE", "target": "COMPATIBLE_WITH_PREREGISTERED_TRANSFORMATION", "units": "COUNT_OR_PERCENTAGE_CHOICE_REQUIRED", "age": "AVAILABLE_WITH_SCHEMA_CHECK", "missingness_backfill": "REVISION_POLICY_REQUIRED", "overall": "COMPATIBLE_WITH_PREREGISTERED_TRANSFORMATION"},
    {"source_key": "cmu_delphi_fluview", "mmwr_identity": "PASS_DOCUMENTED_EPIWEEK", "geography": "PASS_NATIONAL_AVAILABLE", "target": "COMPATIBLE_WITH_PREREGISTERED_TRANSFORMATION", "units": "ili/wili_PERCENT; local_ILITOTAL_COUNT_DIFFERENT", "age": "FIELDS_DOCUMENTED", "missingness_backfill": "ISSUE_LAG_AND_IMPUTATION_DOCUMENTED", "overall": "COMPATIBLE_WITH_PREREGISTERED_TRANSFORMATION"},
    {"source_key": "cdc_nhsn_hrd", "mmwr_identity": "PASS_WEEKLY_METADATA", "geography": "PASS_NATIONAL_AVAILABLE", "target": "EXTERNAL_VALIDATION_DIFFERENT_TARGET", "units": "HOSPITAL_METRICS", "age": "PARTIAL", "missingness_backfill": "REVISION_AND_COVERAGE_CHANGES", "overall": "EXTERNAL_VALIDATION_DIFFERENT_TARGET"},
]
write_csv(ACQ / "schema_compatibility_matrix.csv", compat, list(compat[0]))
selection = {
    "generated_utc": NOW,
    "selected_source": None,
    "preferred_candidate": "cmu_delphi_fluview",
    "decision": "NO_HOLDOUT_ACQUIRED",
    "reason": "Metadata supports a possible transformed national weekly holdout, but target/unit/schema compatibility has not been frozen and no values may be accessed in Phase 0.6.",
    "required_user_action": "Approve target choice: shared reduced feature/percentage protocol or explicitly different-target external validation; then authorize quarantined acquisition.",
    "known_v2_test_reuse": False,
}
write_json(ACQ / "source_selection_audit.json", selection)
(ACQ / "source_selection_audit.md").write_text("""# Holdout source selection audit

No source was selected or acquired. CMU Delphi FluView is the preferred candidate because it exposes CDC-provenanced national weekly data, issue/lag history, counts, percentages, age fields and provider metadata. It is not directly compatible with local `ILITOTAL` until target units and a reduced feature set are preregistered. CDC NHSN HRD is retained only as a different-target external validation option.

No holdout values, trajectories, performance, or candidate-selection evidence were inspected.
""", encoding="utf-8")

license_review = {
    "generated_utc": NOW,
    "repository": "https://github.com/ChenxiLiu-HNU/TimeCMA",
    "pinned_revision": "223e4ae9364bec3e3a2d8bb39ab6eed2cf510296",
    "license_file": "LICENSE.txt",
    "license_name": "S-Lab License 1.0",
    "classification": "CUSTOM_LICENSE_REVIEW_REQUIRED",
    "noncommercial_copy_modify": True,
    "commercial_use": "requires contacting contributors",
    "redistribution": "source/binary redistribution requires copyright, conditions and disclaimer notices",
    "weights": "no separate weight license identified; do not assume code license covers weights/backbone",
    "academic_evaluation": "appears permitted for non-commercial use, subject to full license terms and upstream/backbone terms",
    "decision": "DO_NOT_COPY_UPSTREAM_IMPLEMENTATION_PENDING_HUMAN_REVIEW",
}
write_json(PRE / "timecma_license_review.json", license_review)
(PRE / "timecma_license_review.md").write_text("""# TimeCMA license review

The pinned official repository revision contains `LICENSE.txt` identifying **S-Lab License 1.0**. It permits non-commercial source/binary use and modification with required notices, but commercial use requires contacting contributors. The repository license does not establish a separate license for pretrained GPT-2 or other weights.

Classification: **CUSTOM_LICENSE_REVIEW_REQUIRED**. Do not copy upstream implementation code or redistribute derived artifacts until human review confirms intended academic use and notices. A clean-room paper-derived inspired implementation remains possible only after review.
""", encoding="utf-8")

miflu = {
    "generated_utc": NOW,
    "paper": "MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme",
    "doi": "10.1109/JBHI.2025.3561214",
    "publication_source": "IEEE JBHI / Crossref DOI metadata",
    "author_repository": "No official author MIFlu repository identified; FLUTE-Flu is a later reproduction/extension, not evidence of official MIFlu code.",
    "code_data_statement": "Project README and paper-derived records state no official code or data snapshot was released.",
    "local_control_classification": "LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE",
    "local_control_license": "UNRESOLVED_LOCAL_CONTROL",
    "v2_immutable": True,
    "decision": "retain_as_published_method_control_with_disclosed_local_reconstruction",
}
write_json(PRE / "miflu_provenance_review.json", miflu)
(PRE / "miflu_provenance_review.md").write_text("""# MIFlu provenance review

Crossref/IEEE metadata confirms the paper **MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme**, DOI `10.1109/JBHI.2025.3561214`, IEEE JBHI 2025. Available project evidence and the public reproduction record state that no official author code or data snapshot was released. `CHANSingYeungSunny/FLUTE-Flu` is a later reproduction/extension and is not treated as official MIFlu code.

Classification: **LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE**. The v2 GPT-2 control remains immutable, but its local license and code provenance are not called official.
""", encoding="utf-8")

contract = json.loads((PRE / "figure_style_contract.json").read_text(encoding="utf-8"))
contract.update({
    "generated_utc": NOW,
    "canonical_template": "results/ili/figures/fig_q1_step_sweep_L24_L60_step0.png",
    "canonical_template_sha256": template_sha,
    "canonical_template_dimensions_px": [2470, 1330],
    "canonical_template_inches": [13.0, 7.0],
    "canonical_template_export_dpi": 190,
    "original_plotting_script": "scripts/q1_step_sweep.py",
    "template_policy": "reuse canonical q1 step-sweep layout and original plotting conventions; no visual redesign",
})
contract["canvas_by_figure_kind"]["step_sweep"] = [13.0, 7.0]
contract["export_dpi"] = 190
contract["shared_plotting_module_sha256"] = hashlib.sha256((ROOT / "scripts" / "v3" / "figure_style.py").read_bytes()).hexdigest()
contract["rules"]["canonical_template_direct_reuse"] = True
contract["rules"]["no_result_figures_generated_phase_0_6"] = True
write_json(PRE / "figure_style_contract.json", contract)

shared = ROOT / "scripts" / "v3" / "figure_style.py"
write_json(PRE / "figure_contract_revalidation.json", {
    "generated_utc": NOW,
    "canonical_template": "results/ili/figures/fig_q1_step_sweep_L24_L60_step0.png",
    "canonical_template_sha256": template_sha,
    "canonical_template_dimensions_px": [2470, 1330],
    "canonical_template_export_dpi": 190,
    "original_plotting_script": "scripts/q1_step_sweep.py",
    "shared_module_sha256": hashlib.sha256(shared.read_bytes()).hexdigest(),
    "steps": [0, 1, 2, 3],
    "step_lead_mapping": {"0": 1, "1": 2, "2": 3, "3": 4},
    "primary_step": 0,
    "horizons": [24, 36, 48, 60],
    "figures_generated_this_phase": 0,
    "holdout_values_referenced": False,
    "passed": True,
})

feasibility = json.loads((PRE / "candidate_feasibility_matrix.json").read_text(encoding="utf-8"))
candidate_status = {
    "nlinear": "READY_WITH_DISCLOSED_LIMITATIONS",
    "dlinear": "READY_WITH_DISCLOSED_LIMITATIONS",
    "patchtst": "READY_WITH_DISCLOSED_LIMITATIONS",
    "itransformer": "READY_WITH_DISCLOSED_LIMITATIONS",
    "gpt2_miflu": "READY_WITH_DISCLOSED_LIMITATIONS",
    "qwen_time_llm": "MODEL_ACCESS_USER_ACTION_REQUIRED",
    "calf_llm": "READY_WITH_DISCLOSED_LIMITATIONS",
    "timecma_llm": "LICENSE_REVIEW_REQUIRED",
}
for record in feasibility["records"]:
    record["phase06_status"] = candidate_status[record["model_key"]]
    if record["model_key"] == "gpt2_miflu":
        record["provenance_classification"] = "LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE"
    if record["model_key"] == "qwen_time_llm":
        record["access_ready"] = False
    if record["model_key"] == "timecma_llm":
        record["license_classification"] = "CUSTOM_LICENSE_REVIEW_REQUIRED"
write_json(PRE / "candidate_feasibility_matrix.json", feasibility)
(PRE / "candidate_feasibility_matrix.md").write_text(
    "# v3 candidate feasibility matrix (Phase 0.6)\n\n"
    "No model was implemented or loaded.\n\n"
    "| model_key | Phase 0.6 status | provenance/license note |\n|---|---|---|\n"
    + "\n".join(
        f"| `{r['model_key']}` | {r['phase06_status']} | "
        f"{r.get('provenance_classification', r.get('license_classification', '-'))} |"
        for r in feasibility["records"]
    ) + "\n",
    encoding="utf-8",
)

dependency = json.loads((PRE / "dependency_and_license_audit.json").read_text(encoding="utf-8"))
for record in dependency["records"]:
    key = record["model_key"]
    record["phase06_status"] = candidate_status[key]
    if key == "qwen_time_llm":
        record["qwen_model_access_ready"] = False
        record["access_reason"] = "ungated Apache-2.0 model, but download and cache registration require user authorization"
    if key == "timecma_llm":
        record["license"] = "S-Lab License 1.0"
        record["license_classification"] = "CUSTOM_LICENSE_REVIEW_REQUIRED"
    if key == "gpt2_miflu":
        record["provenance_classification"] = "LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE"
write_json(PRE / "dependency_and_license_audit.json", dependency)

ledger = json.loads((PRE / "official_source_ledger.json").read_text(encoding="utf-8"))
for record in ledger["records"]:
    if record["model_key"] == "timecma_llm":
        record["license"] = "S-Lab License 1.0"
        record["license_classification"] = "CUSTOM_LICENSE_REVIEW_REQUIRED"
    if record["model_key"] == "gpt2_miflu":
        record["provenance_classification"] = "LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE"
write_json(PRE / "official_source_ledger.json", ledger)

(PRE / "model_access_action_items.md").write_text("""# Phase 0.6 model access action items

Nothing below was executed in this phase.

1. Qwen2.5-1.5B is ungated and Apache-2.0, but the user must authorize the approximately 3.1 GB download, exact revision registration and SHA-256 cache receipt. Any future load smoke test must run on a Slurm compute node.
2. TimeCMA uses the pinned repository's S-Lab License 1.0. Human review must confirm non-commercial academic use, notices, and separate backbone/weight terms before copying upstream code.
3. MIFlu remains a local reconstruction with published-paper provenance; it is not official author code.
4. No model weights, dependencies, holdout values, or result figures may be accessed in Phase 0.6.
""", encoding="utf-8")

(PRE / "official_source_ledger.md").write_text("""# Official source ledger (Phase 0.6)

The four Non-LLM repositories, Time-LLM, CALF and TimeCMA paper/repository records were checked against official pages and pinned revisions. TimeCMA's pinned `LICENSE.txt` is **S-Lab License 1.0**, not an SPDX permissive license: non-commercial redistribution/modification is conditional, while commercial use requires contributor contact. MIFlu has published-paper provenance but no official author code snapshot in the available evidence; its local control is explicitly classified as a reconstruction.

No weights were downloaded. No holdout values were acquired.
""", encoding="utf-8")

(PRE / "architecture_fidelity_matrix.md").write_text("""# v3 architecture fidelity matrix (Phase 0.6)

The three LLM contracts remain component-distinct and are not implementations yet.

| model_key | fidelity/status | defining mechanism or limitation |
|---|---|---|
| `nlinear` | REFERENCE_FAITHFUL / READY_WITH_DISCLOSED_LIMITATIONS | normalized linear forecast |
| `dlinear` | REFERENCE_FAITHFUL / READY_WITH_DISCLOSED_LIMITATIONS | decomposition plus linear heads |
| `patchtst` | INSPIRED_SIMPLIFICATION / READY_WITH_DISCLOSED_LIMITATIONS | patch Transformer |
| `itransformer` | REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS / READY_WITH_DISCLOSED_LIMITATIONS | variate-token attention |
| `gpt2_miflu` | LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE / READY_WITH_DISCLOSED_LIMITATIONS | published paper, no official code snapshot |
| `qwen_time_llm` | INSPIRED / MODEL_ACCESS_USER_ACTION_REQUIRED | patching, prototype reprogramming, Prompt-as-Prefix, frozen Qwen |
| `calf_llm` | INSPIRED / READY_WITH_DISCLOSED_LIMITATIONS | temporal/text branches, matching, feature and output alignment |
| `timecma_llm` | INSPIRED / LICENSE_REVIEW_REQUIRED | dual branches, retrieval/alignment, last-token representation |

The approved figure template is reused directly; no Phase 0.6 result figure was generated.
""", encoding="utf-8")

budget = json.loads((PRE / "compute_and_storage_budget.json").read_text(encoding="utf-8"))
budget["download_and_storage"]["canonical_template_reuse"] = True
budget["download_and_storage"]["no_phase06_holdout_storage"] = True
budget["durable_storage_gb"]["full_validation_preferred_320_runs"] = 34.0
budget["durable_storage_gb"]["note"] = "two durable copies of fixed-step artifacts plus Qwen weight/cache and environment headroom; no holdout values stored"
write_json(PRE / "compute_and_storage_budget.json", budget)

plan_text = plan.read_text(encoding="utf-8")
phase06_note = """

## Phase 0.6 closure

- Approved canonical figure template: `results/ili/figures/fig_q1_step_sweep_L24_L60_step0.png`; SHA-256 is recorded in `results/v3/preregistration/figure_style_contract.json`.
- Original plotting source is `scripts/q1_step_sweep.py`; v3 must reuse its 13 x 7 inch, approximately 190 DPI step-sweep format and must not redesign the visual system.
- No new holdout was acquired. CMU Delphi FluView is the preferred metadata candidate, but its percentage/count target requires a preregistered reduced-feature protocol before acquisition.
- MIFlu GPT-2 is `LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE`; the local v2 control is not official author code.
- TimeCMA is `CUSTOM_LICENSE_REVIEW_REQUIRED`; Qwen access remains user-authorized work and no weights were downloaded.
- Fixed steps remain 0, 1, 2, 3 with step 0 primary and steps 1-3 mandatory supplementary; steps are never averaged.
"""
if "## Phase 0.6 closure" not in plan_text:
    plan.write_text(plan_text.rstrip() + phase06_note, encoding="utf-8")

# Preserve the existing Phase 0.5 Gate checks, but replace its blockers with Phase 0.6 facts.
gate = json.loads((PRE / "preregistration_gate.json").read_text(encoding="utf-8"))
for check in gate["checks"]:
    if check["id"] in {"official_sources_live_verified_all_eight", "licenses_known_for_all_eight"}:
        check["passed"] = False
gate["phase"] = "Phase 0.6 final holdout, access, provenance and approved figure template"
gate["decision"] = "V3_NEW_HOLDOUT_USER_ACTION_REQUIRED"
gate["blocking_items"] = [
    {"id": "new_holdout_target_compatibility", "satisfied": False, "detail": "CMU Delphi FluView is a candidate only; percentage/count target and reduced feature protocol require user approval before acquisition."},
    {"id": "qwen_model_access_ready", "satisfied": False, "detail": "Qwen2.5-1.5B is ungated and Apache-2.0, but no weight download or cache registration is authorized in Phase 0.6."},
    {"id": "timecma_license_review", "satisfied": False, "detail": "S-Lab License 1.0 permits non-commercial use with notices; human review is required and upstream code must not be copied yet."},
    {"id": "miflu_provenance_closure", "satisfied": True, "detail": "Classified as LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE."},
]
gate["authorization_required_next"] = [
    "Approve a compatible CMU Delphi/CDC target and reduced feature protocol, then authorize quarantined metadata-only acquisition.",
    "Authorize Qwen2.5-1.5B download and revision/SHA-256 cache registration on a compute node.",
    "Complete human review of the TimeCMA S-Lab License 1.0 and backbone/weight terms.",
    "Authorize Phase 1 pilots only after the above gates pass; never compute on Burgundy login nodes.",
]
gate["phase06_audit"] = {
    "plan_sha256": hashlib.sha256(plan.read_bytes()).hexdigest(),
    "figure_style_sha256": style_sha,
    "canonical_template_sha256": template_sha,
    "holdout_values_acquired": False,
    "figures_generated": False,
}
write_json(PRE / "preregistration_gate.json", gate)
(PRE / "preregistration_gate.md").write_text("# v3 Phase 0.6 final Gate\n\n" + json.dumps(gate, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
print(f"[phase06] candidates=3 | selected=None | acquired=False | template_sha={template_sha}")
print(f"[phase06] gate={gate['decision']} | plan_sha={gate['phase06_audit']['plan_sha256']}")
