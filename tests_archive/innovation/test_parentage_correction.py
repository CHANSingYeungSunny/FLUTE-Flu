"""test_parentage_correction.py — prove the re-parenting is behaviour-preserving.

Model-free: no weights, no checkpoint, no dataset, no network. The MIFlu prompt
sections are obtained by SPLITTING the existing template, so the unablated
parent is provably byte-identical.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from textual_embedder import (DEFAULT_MIFLU_PROMPT_COMPONENTS,  # noqa: E402
                              PROMPT_COMPONENT_ORDER,
                              PROMPT_TEMPLATE_7,
                              build_miflu_prompt_template,
                              miflu_prompt_sections)


# ── requirement 1: the unablated parent is unchanged ───────────────────────
def test_default_template_is_byte_identical_to_original():
    rebuilt = build_miflu_prompt_template(DEFAULT_MIFLU_PROMPT_COMPONENTS)
    assert rebuilt == PROMPT_TEMPLATE_7


def test_explicit_all_components_also_identical():
    assert build_miflu_prompt_template(("dataset", "variable", "task")) == \
        PROMPT_TEMPLATE_7


def test_sections_partition_the_template_exactly():
    sec = miflu_prompt_sections()
    assert set(sec) == set(PROMPT_COMPONENT_ORDER) == {"dataset", "variable",
                                                       "task"}
    # re-joining all three reproduces the template; nothing lost, nothing added
    joined = "***\n".join(sec[c] for c in PROMPT_COMPONENT_ORDER)
    assert joined == PROMPT_TEMPLATE_7
    assert sec["dataset"].startswith("[Dataset information]")
    assert sec["variable"].startswith("[Input variable description]")
    assert sec["task"].startswith("[Task instruction]")


# ── requirement: each ablation removes exactly its own section ─────────────
@pytest.mark.parametrize("dropped,marker",
                         [("dataset", "[Dataset information]"),
                          ("variable", "[Input variable description]"),
                          ("task", "[Task instruction]")])
def test_each_ablation_removes_only_its_section(dropped, marker):
    kept = tuple(c for c in PROMPT_COMPONENT_ORDER if c != dropped)
    ablated = build_miflu_prompt_template(kept)
    assert marker not in ablated
    # the other two sections remain, verbatim
    for c in kept:
        section_text = miflu_prompt_sections()[c]
        assert section_text in ablated
    assert len(ablated) < len(PROMPT_TEMPLATE_7)


def test_ablation_is_a_removal_not_a_reorder():
    """Dropping a section must not reorder or rewrite the survivors."""
    sec = miflu_prompt_sections()
    kept = ("dataset", "task")
    ablated = build_miflu_prompt_template(kept)
    assert ablated == "***\n".join([sec["dataset"], sec["task"]])


def test_unknown_component_ignored_safely():
    # unknown names are simply not matched; the known ones still assemble
    assert build_miflu_prompt_template(("dataset", "task", "nonsense")) == \
        build_miflu_prompt_template(("dataset", "task"))


# ── requirement: corrected parentage ───────────────────────────────────────
def test_all_six_original_ablations_parented_to_gpt2_miflu():
    reg = json.loads((REPO / "results" / "v3_clean" / "implementation"
                      / "ablation_control_wiring_v2.json").read_text(
        encoding="utf-8"))["variant_registry"]
    originals = {"without_dataset_information", "without_task_instruction",
                 "without_input_variable_description", "without_lora",
                 "without_multimodality", "without_lora_and_multimodality"}
    for name in originals:
        assert reg[name]["parent"] == "gpt2_miflu", name
        assert "qwen" not in json.dumps(reg[name]).lower(), name


def test_multimodality_removal_is_a_real_removal():
    reg = json.loads((REPO / "results" / "v3_clean" / "implementation"
                      / "ablation_control_wiring_v2.json").read_text(
        encoding="utf-8"))["variant_registry"]
    spec = reg["without_multimodality"]
    assert spec["kwargs"] == {"multimodal": False}
    assert "zero" in spec["intervention_point"].lower()
    # the adapter must actually zero the text contribution in forward
    src = (REPO / "scripts" / "innovation" / "backbones"
           / "gpt2_miflu_adapter.py").read_text(encoding="utf-8")
    assert "not self.multimodal" in src
    assert "torch.zeros_like(ctx)" in src


def test_controls_are_parent_scoped_not_generic():
    reg = json.loads((REPO / "results" / "v3_clean" / "implementation"
                      / "ablation_control_wiring_v2.json").read_text(
        encoding="utf-8"))["variant_registry"]
    assert reg["llm_removed_or_alignment_only"]["applies_to"] == \
        ["calf_llm", "timecma_llm"]
    assert "qwen_time_llm" not in \
        reg["llm_removed_or_alignment_only"]["applies_to"]
    for k in ("zero_text", "shuffled_text"):
        assert set(reg[k]["applies_to"]) == {"calf_llm", "timecma_llm",
                                             "qwen_time_llm"}


def test_shuffled_text_semantics_frozen():
    reg = json.loads((REPO / "results" / "v3_clean" / "implementation"
                      / "ablation_control_wiring_v2.json").read_text(
        encoding="utf-8"))["variant_registry"]
    fs = reg["shuffled_text"]["frozen_semantics"]
    assert fs["shuffle_unit"] == "token"
    assert fs["dimension"] == "token axis (dim=1)"
    assert fs["scope"] == "per sample, within the text sequence only"
    assert fs["seed"] == 20260917
    assert "target" in fs["train_validation_handling"]
    assert "Test" in fs["train_validation_handling"]


# ── requirement 5/6: corrected audit + old one preserved ───────────────────
def test_corrected_audit_fixes_the_wording_error():
    v2 = json.loads((REPO / "results" / "v3_clean" / "preregistration"
                     / "component_isolation_audit_v2.json").read_text(
        encoding="utf-8"))
    entry = next(v for v in v2["variants"] if v["variant"]
                 == "without_multimodality")
    assert entry["target_component"] == "text/multimodal branch"
    assert entry["parameter_groups_touched"] == ["text"]
    assert v2["all_passed"] is True


def test_old_audit_preserved_and_correction_recorded():
    pr = REPO / "results" / "v3_clean" / "preregistration"
    assert (pr / "component_isolation_audit_v1_superseded.json").exists()
    corr = json.loads((pr / "parentage_correction_audit.json").read_text(
        encoding="utf-8"))
    assert corr["matrix_modified"] is False
    assert len(corr["correction"]["re_parented_to_gpt2_miflu"]) == 6
