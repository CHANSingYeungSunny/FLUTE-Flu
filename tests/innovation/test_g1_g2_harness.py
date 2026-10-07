"""G1/G2 Gate-harness regression tests.

MODEL-FREE: model loading, CUDA, network and full-dataset access are monkey-patched
to raise. These tests only inspect the harness's declared routing and statistics
plumbing; real runtime behaviour is proven by the compute-node Slurm Gate.
"""
from __future__ import annotations

import importlib.util
import json
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

HARNESS = ROOT / "hpc_scripts" / "v3_prepilot_gate.py"
QWEN_REV = "8faed761d45a263340a0528343f099c05c9a4323"


def _load(monkeypatch, tmp_path):
    """Import the harness with a sandboxed deployment root."""
    monkeypatch.setenv("INNOVATION_DEPLOYMENT_ROOT", str(tmp_path))
    cwd = Path.cwd()
    try:
        spec = importlib.util.spec_from_file_location("v3_prepilot_gate_under_test", HARNESS)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        import os
        os.chdir(cwd)


@pytest.fixture(autouse=True)
def no_model_no_cuda_no_network(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("model loading attempted during a model-free test")

    try:
        import transformers
        for cls_name in ("AutoModel", "AutoTokenizer", "AutoConfig",
                         "AutoModelForCausalLM"):
            cls = getattr(transformers, cls_name, None)
            if cls is not None and hasattr(cls, "from_pretrained"):
                monkeypatch.setattr(cls, "from_pretrained", staticmethod(_boom))
    except ImportError:
        pass

    def _no_net(*a, **k):
        raise AssertionError("network access attempted during a model-free test")

    monkeypatch.setattr(socket.socket, "connect", _no_net)
    monkeypatch.setattr(socket, "create_connection", _no_net)

    try:
        import torch
        monkeypatch.setattr(torch, "cuda", _NoCuda())
    except ImportError:
        pass
    yield


class _NoCuda:
    """Any use of torch.cuda from a local test is an error."""
    @property
    def is_available(self):
        def _f():
            raise AssertionError("CUDA use attempted during a model-free test")
        return _f

    def __getattr__(self, _name):
        def _f(*a, **k):
            raise AssertionError("CUDA use attempted during a model-free test")
        return _f


# ── G2: per-model backbone routing ──────────────────────────────────────────
def test_only_qwen_time_llm_receives_the_qwen_asset(monkeypatch, tmp_path):
    mod = _load(monkeypatch, tmp_path)
    assert set(mod.MODEL_ORDER) == {"nlinear", "dlinear", "patchtst", "itransformer",
                                    "gpt2_miflu", "qwen_time_llm", "calf_llm",
                                    "timecma_llm"}
    kw = mod.MODEL_ROUTING["qwen_time_llm"]["backbone_kwargs"]
    assert kw["model_id"] == "Qwen/Qwen2.5-1.5B"
    assert kw["load_backbone"] is True
    assert mod.MODEL_ROUTING["qwen_time_llm"]["expected_backbone"] == "Qwen/Qwen2.5-1.5B"
    for other in ("calf_llm", "timecma_llm", "gpt2_miflu", "nlinear", "dlinear",
                  "patchtst", "itransformer"):
        okw = mod.MODEL_ROUTING[other]["backbone_kwargs"] or {}
        assert "model_id" not in okw, f"{other} must not receive a model_id"
        assert "revision" not in okw
        assert "local_snapshot_path" not in okw


def test_calf_timecma_and_miflu_retain_gpt2(monkeypatch, tmp_path):
    mod = _load(monkeypatch, tmp_path)
    assert mod.MODEL_ROUTING["calf_llm"]["expected_backbone"] == "gpt2"
    assert mod.MODEL_ROUTING["timecma_llm"]["expected_backbone"] == "gpt2"
    assert mod.MODEL_ROUTING["gpt2_miflu"]["expected_backbone"] == "gpt2_miflu_control"
    # they still need the backbone loaded, but must not name Qwen
    assert mod.MODEL_ROUTING["calf_llm"]["backbone_kwargs"] == {"load_backbone": True}
    assert mod.MODEL_ROUTING["timecma_llm"]["backbone_kwargs"] == {"load_backbone": True}
    assert mod.MODEL_ROUTING["gpt2_miflu"]["backbone_kwargs"] is None


def test_broad_kwargs_cannot_override_a_preregistered_backbone(monkeypatch, tmp_path):
    """The leak guard must pass, and must actually detect an injected leak."""
    mod = _load(monkeypatch, tmp_path)
    assert mod.assert_no_qwen_leakage() == []
    # inject a forbidden Qwen argument into CALF and prove the guard catches it
    monkeypatch.setitem(mod.MODEL_ROUTING["calf_llm"], "backbone_kwargs",
                        {"load_backbone": True, "model_id": "Qwen/Qwen2.5-1.5B"})
    problems = mod.assert_no_qwen_leakage()
    assert problems and any("calf_llm" in p for p in problems)


# ── G1: train-only Prompt-as-Prefix statistics ──────────────────────────────
def test_train_statistics_come_from_the_training_split_only(monkeypatch, tmp_path):
    mod = _load(monkeypatch, tmp_path)
    import pandas as pd
    from innovation.paths import ILI_COL

    train = pd.DataFrame({ILI_COL: [1.0, 2.0, 3.0, 4.0]})
    stats = mod.train_only_prompt_statistics(train, horizon=24, channel_count=7)
    assert stats["horizon"] == 24
    assert stats["channel_count"] == 7
    assert stats["target_name"] == ILI_COL
    assert stats["train_rows"] == 4
    assert stats["target_min"] == 1.0
    assert stats["target_max"] == 4.0
    assert stats["target_mean"] == pytest.approx(2.5)
    assert stats["contains_validation_or_test"] is False
    # required keys accepted by QwenTimeLLM.set_train_statistics
    assert {"horizon", "channel_count", "target_name"}.issubset(stats)


def test_missing_train_statistics_fail_closed(monkeypatch, tmp_path):
    """The runtime contract rejects an incomplete statistics dict."""

    class _QwenLike:
        def __init__(self):
            self.train_statistics = None

        def set_train_statistics(self, statistics: dict) -> None:
            required = {"horizon", "channel_count", "target_name"}
            if not required.issubset(statistics):
                raise ValueError("Prompt-as-Prefix requires train-only statistics")
            self.train_statistics = dict(statistics)

    m = _QwenLike()
    with pytest.raises(ValueError):
        m.set_train_statistics({"horizon": 24})          # incomplete
    assert m.train_statistics is None
    m.set_train_statistics({"horizon": 24, "channel_count": 7,
                            "target_name": "ILITOTAL"})
    assert m.train_statistics is not None


def test_validation_or_test_statistics_cannot_be_selected(monkeypatch, tmp_path):
    """The helper names the training split and flags no val/Test contamination."""
    mod = _load(monkeypatch, tmp_path)
    import pandas as pd
    from innovation.paths import ILI_COL
    train = pd.DataFrame({ILI_COL: [5.0, 6.0]})
    stats = mod.train_only_prompt_statistics(train, horizon=24, channel_count=7)
    assert "train" in stats["source"]
    assert stats["contains_validation_or_test"] is False
    # the train-frame mean must reflect the training values, not any other split
    assert stats["target_mean"] == pytest.approx(5.5)


# ── harness hygiene ────────────────────────────────────────────────────────
def test_harness_writes_to_a_create_only_job_directory(monkeypatch, tmp_path):
    mod = _load(monkeypatch, tmp_path)
    assert mod.OUT.parent.name == "implementation"
    assert mod.OUT.name.startswith("gate_")
    # a second load with a different job id must not collide
    monkeypatch.setenv("SLURM_JOB_ID", "999999")
    mod2 = _load(monkeypatch, tmp_path)
    assert mod2.OUT.name == "gate_999999"
    assert mod2.OUT != mod.OUT


def test_no_metadata_generation_and_no_test_paths(monkeypatch, tmp_path):
    src = HARNESS.read_text(encoding="utf-8")
    assert "test_evaluations" not in src
    # metadata/specs must not be fabricated inside the harness
    assert "pilot_specs" not in src
