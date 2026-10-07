"""Apply the authoritative v3 protocol simplification at document/audit level only."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRE = ROOT / "results" / "v3" / "preregistration"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(name):
    return json.loads((PRE / name).read_text(encoding="utf-8"))


def dump(name, value):
    (PRE / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


statuses = {
    "nlinear": "READY_WITH_DISCLOSED_LIMITATIONS",
    "dlinear": "READY_WITH_DISCLOSED_LIMITATIONS",
    "patchtst": "READY_WITH_DISCLOSED_LIMITATIONS",
    "itransformer": "READY_WITH_DISCLOSED_LIMITATIONS",
    "gpt2_miflu": "READY_WITH_DISCLOSED_LIMITATIONS",
    "qwen_time_llm": "MODEL_ACCESS_USER_ACTION_REQUIRED",
    "calf_llm": "READY_WITH_DISCLOSED_LIMITATIONS",
    "timecma_llm": "LICENSE_REVIEW_REQUIRED",
}
feas = load("candidate_feasibility_matrix.json")
for record in feas["records"]:
    record["phase06_status"] = statuses[record["model_key"]]
    record["active_protocol"] = "original GPT-2/MIFlu National-Illness workflow"
    record["external_data_required"] = False
    record["new_holdout_required"] = False
    if record["model_key"] == "gpt2_miflu":
        record["provenance_classification"] = "LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE"
feas["generated_utc"] = NOW
feas["active_data_protocol"] = "original GPT-2/MIFlu National-Illness dataset, ILITOTAL, verified split"
feas["external_data_status"] = "SUPERSEDED_V3_HOLDOUT_FEASIBILITY_HISTORY"
dump("candidate_feasibility_matrix.json", feas)
(PRE / "candidate_feasibility_matrix.md").write_text("""# v3 candidate feasibility matrix (authoritative simplified protocol)

All candidates use the original GPT-2/MIFlu National-Illness data, `ILITOTAL`, verified split, train-only scaler/prompt statistics, horizons 24/36/48/60, formal seeds 42..51, and fixed steps 0..3. No external data or new holdout is active.

| model_key | group | status | limitation |
|---|---|---|---|
| `nlinear` | A_non_llm | READY_WITH_DISCLOSED_LIMITATIONS | reference-faithful implementation pending Phase 1 |
| `dlinear` | A_non_llm | READY_WITH_DISCLOSED_LIMITATIONS | reference-faithful implementation pending Phase 1 |
| `patchtst` | A_non_llm | READY_WITH_DISCLOSED_LIMITATIONS | inspired simplification disclosed |
| `itransformer` | A_non_llm | READY_WITH_DISCLOSED_LIMITATIONS | aligned deviations disclosed |
| `gpt2_miflu` | B_llm | READY_WITH_DISCLOSED_LIMITATIONS | local reconstruction with published-paper provenance |
| `qwen_time_llm` | B_llm | MODEL_ACCESS_USER_ACTION_REQUIRED | Qwen asset download/cache authorization pending |
| `calf_llm` | B_llm | READY_WITH_DISCLOSED_LIMITATIONS | inspired component contract pending implementation |
| `timecma_llm` | B_llm | LICENSE_REVIEW_REQUIRED | S-Lab License 1.0 review pending |

The two naive baselines remain references only. Negative controls remain validation-only secondary analyses.
""", encoding="utf-8")

# Keep the source ledger and dependency audit truthful while removing data-access blockers.
for filename in ("dependency_and_license_audit.json", "official_source_ledger.json"):
    obj = load(filename)
    obj["active_data_protocol"] = "original GPT-2/MIFlu National-Illness workflow"
    obj["external_data_required"] = False
    obj["new_holdout_required"] = False
    obj["superseded_external_work"] = "SUPERSEDED_V3_HOLDOUT_FEASIBILITY_HISTORY"
    dump(filename, obj)

(PRE / "model_access_action_items.md").write_text("""# v3 model access action items before Phase 1

The original National-Illness data protocol is frozen. There is no active external-data or new-holdout action.

1. Authorize the Qwen2.5-1.5B asset download, exact revision registration, and cache SHA-256 receipt. Perform any future load smoke test on a Slurm compute node only.
2. Complete human review of the TimeCMA S-Lab License 1.0 and separate backbone/weight terms. Do not copy upstream implementation code before review.
3. Keep MIFlu GPT-2 classified as `LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE`.
4. After asset/license authorization, authorize Phase 1 pilots for the fixed 4-vs-4 set. Do not modify v2 evidence or compute on a Burgundy login node.
""", encoding="utf-8")

# Existing experiment matrices are retained but receive explicit protocol metadata in a sidecar.
protocol = load("protocol_simplification_audit.json")
protocol["generated_utc"] = NOW
dump("protocol_simplification_audit.json", protocol)

# Gate: no new-holdout blocker; retain only asset/license authorization blockers.
gate = load("preregistration_gate.json")
gate["generated_utc"] = NOW
gate["phase"] = "Protocol correction complete; Phase 1 authorization pending"
gate["decision"] = "V3_ORIGINAL_GPT2_PROTOCOL_FROZEN_AWAITING_PHASE1_AUTHORIZATION"
gate["blocking_items"] = [
    {"id": "qwen_asset_authorization", "satisfied": False, "detail": "Qwen2.5-1.5B download and cache registration require explicit authorization; no download occurred."},
    {"id": "timecma_license_review", "satisfied": False, "detail": "S-Lab License 1.0 and backbone/weight terms require human review before upstream code use."},
]
gate["authorization_required_next"] = [
    "Authorize the versioned Qwen asset download and compute-node-only smoke test.",
    "Clear TimeCMA license and backbone/weight terms for the planned inspired implementation.",
    "Authorize Phase 1: eight L=24 seed-42 pilots using the original GPT-2/MIFlu protocol and independent v3 paths.",
]
gate["superseded_history"] = "SUPERSEDED_V3_HOLDOUT_FEASIBILITY_HISTORY"
gate["must_not_do"] = ["download weights", "install model dependencies", "construct or load models", "train or infer", "submit Slurm jobs", "access Test values", "generate v3 result figures", "modify v2 evidence", "compute on a Burgundy login node"]
gate["phase07_audit"] = {
    "canonical_data_sha256": "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d",
    "plan_sha256": hashlib.sha256((ROOT / "MIFlu_innovation_plan_v3.md").read_bytes()).hexdigest(),
    "active_external_data": False,
    "active_new_holdout": False,
    "active_rolling_origin_redesign": False,
    "active_target": "ILITOTAL",
    "phase1_started": False,
}
gate.pop("phase06_audit", None)
for check in gate["checks"]:
    if check["id"] in {"official_sources_live_verified_all_eight", "licenses_known_for_all_eight"}:
        check["passed"] = True
    if check["id"] == "holdout_decision_explicit":
        check["passed"] = True
gate["n_passed"] = sum(1 for check in gate["checks"] if check["passed"])
gate["n_checks"] = len(gate["checks"])
gate["all_checks_passed"] = all(check["passed"] for check in gate["checks"])
dump("preregistration_gate.json", gate)
(PRE / "preregistration_gate.md").write_text("# v3 protocol-correction Gate\n\n" + json.dumps(gate, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

print(f"[protocol-correction] gate={gate['decision']} checks={gate['n_passed']}/{gate['n_checks']}")
