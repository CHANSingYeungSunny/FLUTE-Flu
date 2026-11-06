"""test_canonical_tensor_hash.py — v3.16 canonical tensor-semantic hash tests.

Model-free: synthetic tensors only, no model construction, no weights.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest
import torch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import compact_checkpoint as CC          # noqa: E402
from innovation import architecture_contract as AC       # noqa: E402


def _sd():
    return {"a": torch.arange(6, dtype=torch.float32).reshape(2, 3),
            "b": torch.ones(4, dtype=torch.float32),
            "c": torch.zeros(2, dtype=torch.int64)}


# ── determinism / order independence ─────────────────────────────────────
def test_same_tensors_same_hash():
    assert CC.canonical_tensor_sha256(_sd()) == \
        CC.canonical_tensor_sha256(_sd())


def test_key_insertion_order_does_not_change_hash():
    a = {"a": torch.ones(2), "b": torch.zeros(3)}
    b = {"b": torch.zeros(3), "a": torch.ones(2)}
    assert CC.canonical_tensor_sha256(a) == CC.canonical_tensor_sha256(b)


def test_container_reordering_same_hash_like_safetensors_offsets():
    """Simulates a serializer writing the same tensors in a different order."""
    a = {f"k{i}": torch.full((3,), float(i)) for i in range(8)}
    items = list(a.items())[::-1]
    b = {k: v for k, v in items}
    assert CC.canonical_tensor_sha256(a) == CC.canonical_tensor_sha256(b)


# ── any change must change the hash ──────────────────────────────────────
def test_key_change_changes_hash():
    a = {"x": torch.ones(2)}
    b = {"y": torch.ones(2)}
    assert CC.canonical_tensor_sha256(a) != CC.canonical_tensor_sha256(b)


def test_dtype_change_changes_hash():
    a = {"x": torch.ones(2, dtype=torch.float32)}
    b = {"x": torch.ones(2, dtype=torch.float64)}
    assert CC.canonical_tensor_sha256(a) != CC.canonical_tensor_sha256(b)


def test_shape_change_changes_hash():
    a = {"x": torch.ones(6)}
    b = {"x": torch.ones(2, 3)}
    assert CC.canonical_tensor_sha256(a) != CC.canonical_tensor_sha256(b)


def test_value_change_changes_hash():
    a = {"x": torch.ones(3)}
    b = {"x": torch.tensor([1.0, 1.0, 2.0])}
    assert CC.canonical_tensor_sha256(a) != CC.canonical_tensor_sha256(b)


def test_adding_a_key_changes_hash():
    a = {"x": torch.ones(2)}
    b = {"x": torch.ones(2), "y": torch.ones(2)}
    assert CC.canonical_tensor_sha256(a) != CC.canonical_tensor_sha256(b)


# ── unambiguous length-prefixed encoding ─────────────────────────────────
def test_length_prefix_prevents_concatenation_collisions():
    """Without length prefixes {'ab','c'} and {'a','bc'} could collide."""
    a = {"ab": torch.ones(1), "c": torch.zeros(1)}
    b = {"a": torch.ones(1), "bc": torch.zeros(1)}
    assert CC.canonical_tensor_sha256(a) != CC.canonical_tensor_sha256(b)


def test_noncontiguous_tensor_is_normalised():
    t = torch.arange(12, dtype=torch.float32).reshape(3, 4).t()  # non-contiguous
    assert not t.is_contiguous()
    c = t.contiguous()
    assert CC.canonical_tensor_sha256({"x": t}) == \
        CC.canonical_tensor_sha256({"x": c})


# ── schema versioning + no pickle ────────────────────────────────────────
def test_hash_schema_is_versioned_and_feeds_the_digest():
    assert CC.CANONICAL_HASH_SCHEMA.startswith("canonical-tensor-")
    sd = _sd()
    base = CC.canonical_tensor_sha256(sd)
    orig = CC.CANONICAL_HASH_SCHEMA
    try:
        CC.CANONICAL_HASH_SCHEMA = "canonical-tensor-v999"
        assert CC.canonical_tensor_sha256(sd) != base
    finally:
        CC.CANONICAL_HASH_SCHEMA = orig


def test_no_pickle_in_canonical_hash_source():
    src = (REPO / "scripts" / "innovation"
           / "compact_checkpoint.py").read_text(encoding="utf-8")
    body = src[src.index("def canonical_tensor_sha256"):]
    body = body[:body.index("\ndef ", 5)]
    for banned in ("pickle", "torch.save", "dumps"):
        assert banned not in body


def test_canonical_hash_is_not_the_file_hash():
    """The two hashes serve different purposes and must both be reported."""
    assert CC.CANONICAL_HASH_SCHEMA != "file-bytes"


# ── dominant-cluster backbone detection (pure function) ──────────────────
def test_dominant_cluster_ancestor_ignores_a_stray_module():
    """The D15b defect: one stray HF-namespace module must not collapse the
    answer to empty."""
    paths = ["inner.forecasting_llm.blocks.0",
             "inner.forecasting_llm.blocks.0.attn",
             "inner.forecasting_llm.blocks.1",
             "lm_head"]
    # the stray top-level `lm_head` must NOT collapse the answer
    assert AC._dominant_cluster_ancestor(paths) == \
        ["inner.forecasting_llm.blocks"]


def test_dominant_cluster_ancestor_single_cluster():
    assert AC._dominant_cluster_ancestor(["text.model.layers.0"]) == \
        ["text.model.layers.0"]


def test_dominant_cluster_ancestor_returns_the_groups_level():
    """It returns the deepest shared level; the caller steps one level up so
    sibling pieces such as wte/wpe are covered too."""
    paths = ["inner.forecasting_llm.blocks.0",
             "inner.forecasting_llm.blocks.0.attn",
             "inner.forecasting_llm.blocks.1"]
    anc = AC._dominant_cluster_ancestor(paths)
    assert anc == ["inner.forecasting_llm.blocks"]
    assert anc[0].rsplit(".", 1)[0] == "inner.forecasting_llm"


def test_dominant_cluster_ancestor_empty():
    assert AC._dominant_cluster_ancestor([]) == []


def test_hf_namespaces_include_pytorch_utils():
    """Conv1D lives in transformers.pytorch_utils, not transformers.models."""
    assert "transformers.pytorch_utils." in AC.HF_MODULE_NS
    assert "transformers.models." in AC.HF_MODULE_NS


def test_identity_attrs_cover_the_declared_ids():
    assert "model_id" in AC.IDENTITY_ATTRS
    assert "base_model_id" in AC.IDENTITY_ATTRS


def test_reference_mapping_declares_the_blocks_rename():
    src = (REPO / "scripts" / "innovation"
           / "architecture_contract.py").read_text(encoding="utf-8")
    assert '.h.' in src and '.blocks.' in src


# ── contract evaluation unchanged ────────────────────────────────────────
def test_backbone_invariant_still_holds():
    assert AC.evaluate_duplication(True, 0, True, True) is True
    assert AC.evaluate_duplication(True, 1, True, True) is False
    assert AC.evaluate_duplication(False, 0, True, True) is True
    assert AC.evaluate_duplication(None, 0, True, True) is False


def test_storage_verdict_still_requires_exactness_and_publication():
    rep = {"reconstruction_exact": True, "no_frozen_backbone_duplication": True}
    rest = {"restoration_exact": True, "missing_keys": [],
            "unexpected_keys": []}
    assert AC.storage_verdict(rep, rest, True, True) is True
    assert AC.storage_verdict(rep, rest, False, True) is False
    assert AC.storage_verdict(rep, dict(rest, missing_keys=["k"]),
                              True, True) is False
