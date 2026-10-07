"""test_d15_storage_predicate.py — D15 applicability-aware invariant tests.

Model-free (no torch, no model construction). The key case replays the ACTUAL
Gate 571855 records: the four failing families had reconstruction/restoration
exact and only `frozen_backbone_excluded == False`; under the applicability-
aware invariant they must now evaluate as PASS without changing their compact
files or any scientific output.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import architecture_contract as AC         # noqa: E402

GATE_571855 = REPO / "results" / "v3_clean" / "runs" / "gate_571855_report.json"

# proven architecture contract (from compute-node probes: the four Non-LLM
# families load no HF backbone; every gpt2/qwen-derived family does)
NO_BACKBONE = ("nlinear", "dlinear", "patchtst", "itransformer")
HAS_BACKBONE = ("gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm",
                "without_dataset_information", "without_task_instruction",
                "without_input_variable_description", "without_lora",
                "without_multimodality", "without_lora_and_multimodality",
                "zero_text", "shuffled_text")


# ── 1-5. no-backbone architectures pass vacuously, but ONLY if exact ──────
@pytest.mark.parametrize("fam", NO_BACKBONE)
def test_no_backbone_passes_when_exact(fam):
    assert AC.evaluate_duplication(has_pretrained_backbone=False,
                                   unexpected_retained_bytes=0,
                                   reconstruction_exact=True,
                                   restoration_exact=True) is True


@pytest.mark.parametrize("fam", NO_BACKBONE)
def test_no_backbone_fails_if_reconstruction_fails(fam):
    assert AC.evaluate_duplication(False, 0, reconstruction_exact=False,
                                   restoration_exact=True) is False


@pytest.mark.parametrize("fam", NO_BACKBONE)
def test_no_backbone_fails_if_restoration_fails(fam):
    assert AC.evaluate_duplication(False, 0, reconstruction_exact=True,
                                   restoration_exact=False) is False


def test_unknown_backbone_state_fails_closed():
    assert AC.evaluate_duplication(None, 0, True, True) is False


# ── 6-9. backbone architectures ───────────────────────────────────────────
@pytest.mark.parametrize("fam", HAS_BACKBONE)
def test_backbone_passes_when_unchanged_frozen_state_excluded(fam):
    assert AC.evaluate_duplication(True, unexpected_retained_bytes=0,
                                   reconstruction_exact=True,
                                   restoration_exact=True) is True


@pytest.mark.parametrize("fam", HAS_BACKBONE)
def test_backbone_fails_if_unchanged_frozen_state_retained(fam):
    assert AC.evaluate_duplication(True, unexpected_retained_bytes=4096,
                                   reconstruction_exact=True,
                                   restoration_exact=True) is False


def test_genuinely_changed_backbone_tensor_is_not_duplication():
    """A retained backbone tensor that is PROVEN changed is legitimate state,
    not redundant duplication: `unexpected` counts only UNCHANGED retained bytes."""
    assert AC.evaluate_duplication(True, unexpected_retained_bytes=0,
                                   reconstruction_exact=True,
                                   restoration_exact=True) is True


def test_backbone_still_requires_exactness():
    assert AC.evaluate_duplication(True, 0, reconstruction_exact=False,
                                   restoration_exact=True) is False


# ── 10. zero missing/unexpected trained keys is mandatory ─────────────────
def test_storage_verdict_requires_zero_missing_and_unexpected():
    rep = {"reconstruction_exact": True, "no_frozen_backbone_duplication": True}
    rest = {"restoration_exact": True, "missing_keys": [],
            "unexpected_keys": []}
    assert AC.storage_verdict(rep, rest, True, True) is True
    assert AC.storage_verdict(
        rep, dict(rest, missing_keys=["w"]), True, True) is False
    assert AC.storage_verdict(
        rep, dict(rest, unexpected_keys=["b"]), True, True) is False


def test_storage_verdict_requires_publication_and_containment():
    rep = {"reconstruction_exact": True, "no_frozen_backbone_duplication": True}
    rest = {"restoration_exact": True, "missing_keys": [], "unexpected_keys": []}
    assert AC.storage_verdict(rep, rest, published=False, contained=True) is False
    assert AC.storage_verdict(rep, rest, published=True, contained=False) is False


def test_storage_verdict_fails_closed_on_empty_evidence():
    assert AC.storage_verdict({}, {}, True, True) is False
    assert AC.storage_verdict(None, None, True, True) is False


# ── 13. baselines remain no-checkpoint paths ──────────────────────────────
def test_baseline_is_a_no_checkpoint_path_and_fails_closed_on_missing_input():
    from innovation import clean_gate as CG
    out = CG.verify_storage(Path("/nonexistent"), "baseline__x__L24__seedna__w1",
                            "baseline", 24, Path("/tmp/stage"))
    assert out["mode"] == "baseline_no_checkpoint"
    # v3.19 (D15): the baseline path is no longer a vacuous pass — it must run
    # the REAL deterministic-baseline finalization (innovation.finalize_row
    # .finalize_baseline) and therefore FAILS CLOSED on a missing run dir /
    # unknown registry key (instead of silently passing).
    assert out["passed"] is False


# ── 15-16. replay the ACTUAL Gate 571855 records ──────────────────────────
def _replay():
    if not GATE_571855.exists():
        pytest.skip("gate_571855_report.json not present")
    return json.loads(GATE_571855.read_text(encoding="utf-8"))


def test_gate_571855_four_failing_rows_now_pass():
    rep_json = _replay()
    failed = [m for m in rep_json["results"] if not m.get("passed")]
    assert {m["model"] for m in failed} == {"nlinear", "dlinear", "patchtst",
                                            "itransformer"}
    for m in failed:
        st = m["storage"]
        # recorded exactness evidence (unchanged compact files)
        assert st["reconstruction_exact"] is True
        assert st["restoration_exact"] is True
        assert st["n_keys_unequal"] == 0
        assert st["atomic_publish_ok"] is True
        assert st["contained"] is True
        # the ONLY previously failing condition, now correctly vacuous
        assert st["frozen_backbone_excluded"] is False
        no_dup = AC.evaluate_duplication(
            has_pretrained_backbone=False, unexpected_retained_bytes=0,
            reconstruction_exact=st["reconstruction_exact"],
            restoration_exact=st["restoration_exact"])
        assert no_dup is True
        verdict = AC.storage_verdict(
            {"reconstruction_exact": st["reconstruction_exact"],
             "no_frozen_backbone_duplication": no_dup},
            {"restoration_exact": st["restoration_exact"],
             "missing_keys": [], "unexpected_keys": []},
            st["atomic_publish_ok"], st["contained"])
        assert verdict is True


def test_gate_571855_passing_llm_rows_still_pass():
    rep_json = _replay()
    llm = [m for m in rep_json["results"]
           if m.get("passed") and (m.get("storage") or {}).get("mode")
           == "compact"]
    assert llm, "expected passing compact rows in the Gate record"
    for m in llm:
        st = m["storage"]
        no_dup = AC.evaluate_duplication(
            has_pretrained_backbone=True, unexpected_retained_bytes=0,
            reconstruction_exact=st["reconstruction_exact"],
            restoration_exact=st["restoration_exact"])
        assert no_dup is True
        assert AC.storage_verdict(
            {"reconstruction_exact": st["reconstruction_exact"],
             "no_frozen_backbone_duplication": no_dup},
            {"restoration_exact": st["restoration_exact"],
             "missing_keys": [], "unexpected_keys": []},
            st["atomic_publish_ok"], st["contained"]) is True


# ── 17. unknown / ambiguous contract entries fail closed ──────────────────
def test_contract_with_unknown_backbone_flag_fails_closed():
    contract = {"has_pretrained_backbone": None}
    assert AC.evaluate_duplication(contract["has_pretrained_backbone"], 0,
                                   True, True) is False


# ── 18. no name-substring or compression-ratio heuristics ─────────────────
def test_predicates_use_no_name_or_ratio_heuristics():
    ac_src = (REPO / "scripts" / "innovation"
              / "architecture_contract.py").read_text(encoding="utf-8")
    gate_src = (REPO / "scripts" / "innovation"
                / "clean_gate.py").read_text(encoding="utf-8")
    # the DECISION lives in architecture_contract.storage_verdict; the ratio is
    # recorded for reporting only and must not appear in the deciding function.
    verdict = ac_src[ac_src.index("def storage_verdict"):]
    assert "compression_ratio" not in verdict
    # the D15 bug: the universal `frozen_backbone_excluded` predicate is gone
    assert "frozen_backbone_excluded" not in verdict
    # v3.17 (D16): the Gate delegates to the STRONGLY-TYPED verification
    # result, whose verdict is the single decision entry (and fails closed).
    assert "StorageVerification(" in gate_src
    assert 'res["passed"] = sv.passed' in gate_src
    for bad in ('startswith("qwen")', '"llm" in ', 'name.endswith("_llm")'):
        assert bad not in ac_src
        assert bad not in gate_src
    # the detection rule is structural, not lexical
    assert "PreTrainedModel" in ac_src
    assert "isinstance(mod, PreTrainedModel)" in ac_src


def test_contract_source_is_declared():
    assert AC.CONTRACT_SOURCE.startswith("runtime_module_introspection")
