"""test_clean_ablations_controls.py — model-free hand-checked tests.

No real model is loaded: importing the module constructs no weights, no
checkpoint is restored and no dataset is read. Only pure tensor/string logic is
exercised, with every expected value computed BY HAND in the test.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation.backbones import llm_inspired as LI  # noqa: E402

STATS = {"horizon": 24, "channel_count": 7, "target_name": "ILITOTAL"}
DATASET_SENTENCE = "Dataset: National-Illness (weekly influenza-like illness)."
TASK_SENTENCE = "Task: forecast the next 24 weeks."
VARIABLE_SENTENCE = "Variables: 7 channels; target ILITOTAL."


# ── prompt-component ablations ──────────────────────────────────────────────
def test_full_prompt_contains_all_three_components():
    p = LI.build_prompt_from_components(STATS, ("dataset", "task", "variable"))
    assert p == f"{DATASET_SENTENCE} {TASK_SENTENCE} {VARIABLE_SENTENCE}"


def test_without_dataset_information_removes_only_dataset():
    p = LI.build_prompt_from_components(STATS, ("task", "variable"))
    assert DATASET_SENTENCE not in p
    assert TASK_SENTENCE in p
    assert VARIABLE_SENTENCE in p
    assert p == f"{TASK_SENTENCE} {VARIABLE_SENTENCE}"


def test_without_task_instruction_removes_only_task():
    p = LI.build_prompt_from_components(STATS, ("dataset", "variable"))
    assert TASK_SENTENCE not in p
    assert DATASET_SENTENCE in p
    assert VARIABLE_SENTENCE in p


def test_without_input_variable_description_removes_only_variable():
    p = LI.build_prompt_from_components(STATS, ("dataset", "task"))
    assert VARIABLE_SENTENCE not in p
    assert DATASET_SENTENCE in p
    assert TASK_SENTENCE in p


def test_component_isolation_each_drop_removes_exactly_one_sentence():
    full = LI.build_prompt_from_components(STATS, LI.DEFAULT_PROMPT_COMPONENTS)
    n_full = full.count(".")                      # three sentences
    assert n_full == 3
    for dropped in LI.DEFAULT_PROMPT_COMPONENTS:
        kept = tuple(c for c in LI.DEFAULT_PROMPT_COMPONENTS if c != dropped)
        ablated = LI.build_prompt_from_components(STATS, kept)
        assert ablated.count(".") == 2, dropped
        assert len(ablated) < len(full), dropped
        # the two retained sentences are still present verbatim
        for c in kept:
            assert LI._PROMPT_PARTS[c].format(**STATS) in ablated


def test_empty_component_set_yields_empty_prompt():
    assert LI.build_prompt_from_components(STATS, ()) == ""


def test_unknown_component_rejected():
    with pytest.raises(ValueError):
        LI.build_prompt_from_components(STATS, ("dataset", "bogus"))


# ── text-branch negative controls ───────────────────────────────────────────
def _tokens():
    return torch.arange(24, dtype=torch.float32).reshape(2, 4, 3)


def test_zero_text_control_zeroes_every_embedding():
    t = _tokens()
    out = LI.apply_text_mode(t, "zero")
    assert torch.all(out == 0)
    assert out.shape == t.shape


def test_normal_text_mode_is_identity():
    t = _tokens()
    assert torch.equal(LI.apply_text_mode(t, "normal"), t)


def test_shuffled_text_control_is_deterministic_and_preserves_values():
    t = _tokens()
    a = LI.apply_text_mode(t, "shuffle")
    b = LI.apply_text_mode(t, "shuffle")
    assert torch.equal(a, b)                       # same seed -> same order
    # same multiset of token vectors, different order along the token axis
    assert torch.equal(torch.sort(a, dim=1).values,
                       torch.sort(t, dim=1).values)
    assert not torch.equal(a, t)


def test_unknown_text_mode_rejected():
    with pytest.raises(ValueError):
        LI.apply_text_mode(_tokens(), "removed")   # "removed" is handled in forward


# ── variant wiring registry ─────────────────────────────────────────────────
def test_variant_registry_maps_every_variant_to_one_component():
    wiring = (REPO / "results" / "v3_clean" / "implementation"
              / "ablation_control_wiring.json")
    assert wiring.exists()
    import json
    reg = json.loads(wiring.read_text(encoding="utf-8"))["variant_registry"]
    expected = {"without_dataset_information", "without_task_instruction",
                "without_input_variable_description", "without_lora",
                "without_multimodality", "without_lora_and_multimodality",
                "zero_text", "shuffled_text", "llm_removed_or_alignment_only"}
    assert set(reg) == expected
    # LoRA ablations must disable LoRA and nothing else
    assert reg["without_lora"]["kwargs"] == {"use_lora": False}
    assert reg["without_lora_and_multimodality"]["kwargs"]["use_lora"] is False
    # text controls must set exactly one text_mode
    for k in ("zero_text", "shuffled_text", "llm_removed_or_alignment_only"):
        assert list(reg[k]["kwargs"]) == ["text_mode"]


def test_frozen_protocol_untouched():
    """The selector contract must not have been altered by the ablations."""
    import json
    rule = json.loads((REPO / "results" / "v3_clean" / "preregistration"
                       / "paper_aligned_selection_rule.json").read_text(
        encoding="utf-8"))
    assert rule["ranking_metric"] == \
        "average_MSE_4L (seven-variable, full-horizon, z-space)"
    assert rule["normalisation"] == "none"
    for forbidden in ("peak_hit_ratio tie-breaker", "baseline-relative ratio",
                      "(r24+r60)/2"):
        assert forbidden in rule["forbidden"]
    eh = json.loads((REPO / "results" / "v3_clean" / "preregistration"
                     / "endpoint_hierarchy.json").read_text(encoding="utf-8"))
    assert eh["primary_champion_selector"]["metric"] == \
        "mse_all_7vars_full_horizon_z"
    assert eh["disease_specific_secondary"]["rules"][0] == \
        "never average predictions across lead times"
