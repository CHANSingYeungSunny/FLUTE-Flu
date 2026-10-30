"""
paths.py — import bootstrap + canonical paths for the innovation package.
==========================================================================

WHY
---
The innovation experiments are a NEW, minimal-intrusion package that RE-USES
the existing, already-validated MIFlu machinery (`configs.py`,
`scaler_utils.py`, `miflu_model.py`, `textual_embedder.py`,
`compute_miflu_indicators.py`). Those modules live in `scripts/` and are not a
package, so this module puts the right directories on `sys.path` once, for every
entry point and every test.

It also fixes the authoritative-plan hash contract (revision 10): the plan's
SHA-256 is RECOMPUTED at runtime and compared against the expected value that
was frozen when the plan was approved.
"""

from __future__ import annotations

import json
import os
import sys

# scripts/innovation/paths.py -> dirname = scripts/innovation ; parent = scripts
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(HERE)
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)

for _p in (SCRIPTS_DIR, PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Data ────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_CSV = os.path.join(DATA_DIR, "raw", "national_illness_raw.csv")
SCALER_JSON = os.path.join(DATA_DIR, "scaler_miflu_national.json")

# ── Innovation artifact root ────────────────────────────────────────────────
INNOVATION_ROOT = os.path.join(PROJECT_ROOT, "results", "innovation")
RUNS_ROOT = os.path.join(INNOVATION_ROOT, "runs")
TEST_EVAL_ROOT = os.path.join(INNOVATION_ROOT, "test_evaluations")
AUDIT_DIR = os.path.join(INNOVATION_ROOT, "audit")
REGISTRY_PATH = os.path.join(INNOVATION_ROOT, "registry.csv")
SELECTION_AUDIT_PATH = os.path.join(INNOVATION_ROOT, "model_selection_audit.json")
FROZEN_WINNERS_PATH = os.path.join(INNOVATION_ROOT, "frozen_winners.json")
# pre-HPC gate + legacy eligibility annotation (never mutate existing run dirs)
PREHPC_GATE_PATH = os.path.join(INNOVATION_ROOT, "pre_hpc_gate.json")
LEGACY_ELIGIBILITY_PATH = os.path.join(INNOVATION_ROOT,
                                       "legacy_runs_eligibility.json")
FIX_FINGERPRINT_PATH = os.path.join(AUDIT_DIR, "fix_fingerprint.json")
# ── Source freeze (pre-pilot) ───────────────────────────────────────────────
SOURCE_SNAPSHOT_DIR = os.path.join(INNOVATION_ROOT, "source_snapshot")
SOURCE_SNAPSHOT_MANIFEST = os.path.join(INNOVATION_ROOT,
                                        "source_snapshot_manifest.json")
HUMAN_REVIEW_CHECKLIST = os.path.join(INNOVATION_ROOT,
                                      "human_review_checklist.md")

# ── Authoritative plan freeze (revision 10) ─────────────────────────────────
PLAN_MD = os.path.join(PROJECT_ROOT, "docs", "protocol_freeze",
                       "MIFlu_innovation_plan_v2.md")
PLAN_SHA256_EXPECTED = (
    "AA4AB1C8842E893A4690787E17ADD0CA193C86825FFF9FD89F46952C7F9E7961"
)

# ── Protocol version + run eligibility (revision 5) ─────────────────────────
# Every run records the protocol it was produced under; the selector requires a
# match, so a run produced under an older protocol can never be selected.
PROTOCOL_VERSION = "innov-v2.0"

# ── Implementation source version (verification tooling) ────────────────────
# Bumped when the verification/snapshot TOOLING changes. This is NOT the
# scientific protocol: the dataset split, scaler, prompt-statistics rules,
# horizons, seeds, early stopping, PTE/PIE, model-selection rules, model
# implementations and test-access policy are UNCHANGED by this bump.
#
# v2.2 (D1 repair) — explicit pilot-spec metadata emission.
# v2.3 (governance closure) — prospective canonical-indicator adoption, the full
# 12-field runtime metadata chain across all five evidence layers, the versioned
# registry, and the runtime-path exclusion of the original reproduction repo.
# v2.4 (pilot script safety repair) — generated Pilot/Worker/Submit scripts now
# run only from an explicit isolated deployment root (no silent fallback, no
# forbidden `cd`), and the submit driver is serial + afterok + fail-stop.
# v2.5 (autonomous controller) — added hpc_scripts/autonomous/{state.py,lib.sh,
# controller.sh} (a login-node background auto-submit loop, OUTSIDE the frozen
# source hash) and tests/innovation/test_autonomous_controller.py. No scientific
# parameter changed.
# v3.4 (screening artifact contract) — formal Screening runs must emit three
# additional artefacts (metrics/fixed_step_metrics.json,
# prompt_statistics_metadata.json, resource_usage.json) and MUST carry the full
# key set on every prediction row (model_key/horizon/seed/variable/lead_weeks)
# so each fixed step is independently reconstructible. `paper_result_eligible`
# may now carry the governed string "screening_only" for the screening stage.
# Dataset, split, scaler, prompt-statistics rules, horizons, seeds, early
# stopping, PTE/PIE thresholds, candidate identities, metrics and test-access
# policy are all UNCHANGED by this bump.
# No bump ever moved a single scientific parameter.
IMPLEMENTATION_SOURCE_VERSION = "innov-v3.19-baseline-no-checkpoint-finalization"

# ── Test-access policy (D1) ─────────────────────────────────────────────────
# A validation-phase run NEVER touches the test split. The value is written
# into every run_status.json so the policy is machine-checkable at runtime
# instead of being an implicit convention.
TEST_ACCESS_ALLOWED = False

# ── Pilot-spec metadata contract (D1 repair, innov-v2.2) ────────────────────
# Defect D1: `hpc_scripts/pilot_specs.json` carried neither `experiment_stage`
# nor `test_access_allowed` nor a per-spec `protocol_version`. Emitting them
# from ONE source of truth (here) means the generator and the regression test
# `tests/innovation/test_pilot_spec_metadata.py` can never drift apart again.
PILOT_EXPERIMENT_STAGE = "pilot"


def pilot_spec_metadata() -> dict:
    """The metadata fields EVERY pilot spec (and the top-level object) carries."""
    return {
        "experiment_stage": PILOT_EXPERIMENT_STAGE,
        "test_access_allowed": TEST_ACCESS_ALLOWED,
        "protocol_version": PROTOCOL_VERSION,
    }


# ── Governance metadata contract (innov-v2.3) ───────────────────────────────
# Every one of these must be present and EQUAL across all five evidence layers:
#   pilot_specs.json, config_resolved.yaml, run_status.json,
#   checkpoint_manifest.json, registry_v2.csv
REQUIRED_METADATA_FIELDS = (
    "experiment_stage", "purpose", "selection_eligible",
    "paper_result_eligible", "test_access_allowed", "protocol_version",
    "implementation_source_version", "source_snapshot_sha256",
    "authoritative_plan_sha256", "model_key", "display_name",
    "architecture_fidelity",
)

# Fail-closed: a MISSING value means False, never True.
FAIL_CLOSED_FALSE_FIELDS = ("selection_eligible", "paper_result_eligible",
                            "test_access_allowed")

STAGE_PURPOSE = {
    "smoke": "runtime_metadata_contract_verification",
    "pilot": "infrastructure_verification_only",
    "screening": "model_screening",
    "full": "full_evaluation",
    "validation": "validation_only",
    "adhoc": "ad_hoc",
    "test": "frozen_winner_test_evaluation",
}

# The original reproduction repository is PERMANENTLY excluded from the
# innovation execution path (incident 2026-09-15). No innovation job may resolve
# a Python source path under it.
BANNED_RUNTIME_ROOT = "/home/sychan552/scratch/CHATTIME/Chattime"
BANNED_RUNTIME_MARKERS = ("CHATTIME/Chattime",)

GOVERNANCE_DIR = os.path.join(INNOVATION_ROOT, "governance")
CANONICAL_INDICATOR_REL = "scripts/compute_miflu_indicators.py"

# Stable display names for the four pilot model keys (§7). The backbone's own
# `architecture_report()` still carries the longer citation-style name; this
# table is the governed SHORT name used in every metadata layer. (The cosmetic
# difference is the long-standing D2 item and is disclosed, not overwritten.)
MODEL_DISPLAY_NAMES = {
    "gpt2_miflu": "MIFlu GPT-2 control",
    "dlinear": "DLinear",
    "nlinear": "NLinear",
    "patchtst": "PatchTST-inspired",
    "itransformer": "iTransformer-aligned",
    "fusion_forecaster": "Fusion forecaster (plugin testbed)",
}

# ── ONE canonical model-key normalisation (innov-v2.9) ──────────────────────
# A run_id encodes the model with a slug (non-alphanumerics -> "-"), so
# `gpt2_miflu` appears as `gpt2-miflu` in run_id-derived metadata while every
# other layer uses the underscore key. Scientific identity/grouping must use ONE
# spelling; slugging is only for filesystem / run-ID representation.
CANONICAL_MODEL_KEYS = tuple(MODEL_DISPLAY_NAMES)


def canonical_model_key(value):
    """Map any spelling of a model key to the ONE canonical internal key.

    ``canonical_model_key("gpt2-miflu") == canonical_model_key("gpt2_miflu")
    == "gpt2_miflu"``. Unknown keys are returned in slug form (stable).
    """
    import re
    if value is None:
        return None
    v = str(value)
    if v in CANONICAL_MODEL_KEYS:
        return v

    def _slug(s):
        return re.sub(r"[^A-Za-z0-9]+", "-", str(s).strip()).strip("-") or "na"

    sv = _slug(v)
    for c in CANONICAL_MODEL_KEYS:
        if _slug(c) == sv:
            return c
    return sv


def display_name_for(model_key: str | None,
                     architecture_report: dict | None = None) -> str | None:
    """Governed display name: the stable table wins, the model report is fallback.

    NOTE (disclosed discrepancy): the v2.3 brief asks for
    `WRAPPER_FAITHFUL` for `gpt2_miflu`, but that level is NOT part of the
    declared taxonomy `fidelity.LEVELS`. Introducing it would change
    architecture-fidelity classification, which the same brief forbids (§6), so
    the fidelity recorded in every layer remains the model's DECLARED level.
    """
    if model_key in MODEL_DISPLAY_NAMES:
        return MODEL_DISPLAY_NAMES[model_key]
    rep = architecture_report or {}
    return rep.get("display_name")


def fail_closed_bool(record: dict, key: str) -> bool:
    """Read a boolean governance field FAIL-CLOSED: a missing value is False."""
    v = (record or {}).get(key)
    if v is None or v == "":
        return False
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes")
    return bool(v)


def assert_test_access_gate(*, frozen_winner_manifest_exists: bool,
                            checkpoint_hash_matches: bool,
                            explicit_test_gate_authorized: bool) -> None:
    """The ONLY way `test_access_allowed=true` may ever be set."""
    if not (frozen_winner_manifest_exists and checkpoint_hash_matches
            and explicit_test_gate_authorized):
        raise RuntimeError(
            "TEST_GATE_NOT_AUTHORIZED: requires frozen_winner_manifest_exists, "
            "checkpoint_hash_matches and explicit_test_gate_authorized "
            f"(got {frozen_winner_manifest_exists}, {checkpoint_hash_matches}, "
            f"{explicit_test_gate_authorized})")


def current_snapshot_sha256() -> str | None:
    """Aggregate SHA-256 of the frozen source snapshot, read at runtime."""
    try:
        with open(SOURCE_SNAPSHOT_MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f).get("aggregate_sha256")
    except Exception:
        return None


def governance_fields(*, stage: str, purpose: str | None = None,
                      model_key: str | None = None,
                      display_name: str | None = None,
                      architecture_fidelity: str | None = None,
                      source_snapshot_sha256: str | None = None,
                      authoritative_plan_sha256: str | None = None,
                      test_access_allowed: bool = TEST_ACCESS_ALLOWED,
                      selection_eligible: bool | None = None,
                      paper_result_eligible: bool | None = None,
                      require_no_test_access: bool = True) -> dict:
    """Build the 12-field governance block for ONE run.

    Fail-closed rules enforced here:
      * any non-`test` stage that requests test access is REJECTED;
      * `selection_eligible` / `paper_result_eligible` default to False for
        pilot / smoke and to the stage rule otherwise, never to True;
      * a missing value can never be interpreted as True.
    """
    stage = str(stage or "adhoc")
    if require_no_test_access and test_access_allowed and stage != "test":
        raise ValueError(
            f"INVALID_TEST_ACCESS_FOR_EXPERIMENT_STAGE: test_access_allowed=true "
            f"is only permitted for the frozen-winner test-evaluation stage; "
            f"got stage={stage!r}")
    if selection_eligible is None:
        selection_eligible = stage in ELIGIBLE_STAGES
    if paper_result_eligible is None:
        paper_result_eligible = stage in ELIGIBLE_STAGES
    if stage in ("pilot", "smoke", "adhoc", "validation"):
        selection_eligible = False
        paper_result_eligible = False
    return {
        "experiment_stage": stage,
        "purpose": purpose or STAGE_PURPOSE.get(stage, "ad_hoc"),
        "selection_eligible": bool(selection_eligible),
        # v3.4: the screening stage carries the governed eligibility LABEL
        # "screening_only" (a string), because its results may be reported for
        # advancement but are not publication-level final results. Every other
        # stage keeps the strict boolean (fail-closed: missing -> False).
        "paper_result_eligible": (paper_result_eligible
                                  if isinstance(paper_result_eligible, str)
                                  else bool(paper_result_eligible)),
        "test_access_allowed": bool(test_access_allowed),
        "protocol_version": PROTOCOL_VERSION,
        "implementation_source_version": IMPLEMENTATION_SOURCE_VERSION,
        "source_snapshot_sha256": source_snapshot_sha256,
        "authoritative_plan_sha256": authoritative_plan_sha256,
        "model_key": model_key,
        "display_name": display_name,
        "architecture_fidelity": architecture_fidelity,
    }

# Which experiment stages may enter champion selection. Smoke/pilot/adhoc may
# NOT — they exist for pipeline/infrastructure verification only.
ELIGIBLE_STAGES = ("screening", "full")
STAGE_VALUES = ("smoke", "pilot", "screening", "full", "adhoc", "validation")

# ── Fixed scientific constants (must match the existing main protocol) ──────
DATASET_NAME = "national_ili"
SEEDS_FULL = tuple(range(42, 52))          # seeds 42..51
SEEDS_SCREEN = (42, 43, 44)
HORIZONS = (24, 36, 48, 60)
ILI_CHANNEL = 4
ILI_COL = "ILITOTAL"


def plan_sha256() -> str:
    """Recompute the authoritative plan SHA-256 from disk at runtime."""
    import hashlib

    h = hashlib.sha256()
    with open(PLAN_MD, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def plan_sha256_status() -> dict:
    """Compare the runtime plan hash against the frozen expected value.

    The comparison is case-insensitive: Get-FileHash prints upper-case hex while
    hashlib emits lower-case hex for the SAME digest, so a naive == would
    falsely report a mismatch.
    """
    actual = plan_sha256()
    matches = actual.lower() == PLAN_SHA256_EXPECTED.lower()
    return {
        "plan_md": PLAN_MD,
        "sha256_expected": PLAN_SHA256_EXPECTED,
        "sha256_runtime": actual,
        "matches": matches,
    }


def ensure_innovation_dirs() -> None:
    for d in (INNOVATION_ROOT, RUNS_ROOT, TEST_EVAL_ROOT, AUDIT_DIR):
        os.makedirs(d, exist_ok=True)


if __name__ == "__main__":  # pragma: no cover
    st = plan_sha256_status()
    print("[paths] plan:", st["plan_md"])
    print("[paths] sha256 expected:", st["sha256_expected"])
    print("[paths] sha256 runtime :", st["sha256_runtime"])
    print("[paths] matches        :", st["matches"])
