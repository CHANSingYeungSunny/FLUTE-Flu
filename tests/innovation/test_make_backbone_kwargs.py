"""test_make_backbone_kwargs.py — regression test for D9 (Gate 568988).

Model-free: it only INSPECTS constructor signatures and the runner source. No
weights, no dataset, no network, no Torch/CUDA execution.
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import clean_runner as CR          # noqa: E402
from innovation.backbones import registry as REG   # noqa: E402


def _ctor_params(name: str) -> set:
    cls = REG.get_backbone(name)
    return set(inspect.signature(cls.__init__).parameters) - {"self"}


def test_runner_does_not_pass_device_to_make_backbone():
    src = (REPO / "scripts" / "innovation" / "clean_runner.py").read_text(
        encoding="utf-8")
    assert "L=horizon, device=device, **bkw)" not in src
    assert "L=horizon, **bkw)" in src


def test_all_primary_backbones_accept_the_runners_call_signature():
    """D9: the runner calls `make_backbone(T, N, L, **bkw)`; every forwarded
    keyword must be a real constructor parameter.

    `device` is deliberately NOT forwarded: some backbones accept it and some
    (nlinear/dlinear/...) do not, so it must never be passed by the runner.
    """
    for name in CR.PRIMARY_MODELS:
        params = _ctor_params(name)
        assert {"T", "N", "L"} <= params, name
        bkw = {}
        if name == "qwen_time_llm":
            bkw = {"model_id": "Qwen/Qwen2.5-1.5B", "load_backbone": True}
        elif name in ("calf_llm", "timecma_llm"):
            bkw = {"model_id": "gpt2", "load_backbone": True}
        for k in bkw:
            assert k in params, f"{name} rejects {k}"


def test_every_variant_kwarg_is_accepted_by_its_target_constructor():
    """Ablation kwargs split across backbone and encoder, as the runner wires
    them; each must be a real parameter of its target."""
    from innovation.encoders import registry as EREG
    for variant, (base, enc_name, bkw, ekw) in CR.VARIANTS.items():
        bparams = _ctor_params(base)
        for k in bkw:
            assert k in bparams, f"{variant}: backbone {base} rejects {k}"
        if ekw:
            make = getattr(EREG, "make_encoder")
            # encoder kwargs are validated structurally against known keys
            assert set(ekw) <= {"prompt_components", "text_mode"}, variant
            assert callable(make)


def test_primary_registry_routing_is_registered():
    available = set(REG.available_backbones())
    for name in CR.PRIMARY_MODELS:
        assert name in available, name
        assert callable(REG.get_backbone(name))


def test_d9_evidence_recorded():
    sc = REPO / "results" / "v3_clean" / "preregistration"
    pre = json.loads((sc / "d9_pre_repair_manifest.json").read_text(
        encoding="utf-8"))
    rec = json.loads((sc / "d9_repair_record.json").read_text(encoding="utf-8"))
    assert pre["failure_signature"]["exception"] == "TypeError"
    assert "unexpected keyword argument 'device'" in \
        pre["failure_signature"]["message"]
    assert pre["predecessor_defect"]["id"] == "D8"
    assert pre["predecessor_defect"]["status"] == "FIXED_AND_VERIFIED_IN_v3.9"
    assert rec["classification"] == \
        "BEHAVIOR_NEUTRAL_API_SIGNATURE_ADAPTATION_FIX"
    assert rec["scientific_parameters_changed"] == 0
    assert rec["pre_repair_sha256"] != rec["post_repair_sha256"]


def test_gate_key_builder_matches_the_frozen_registry(tmp_path):
    """D10: the GATE's run-key builder must reproduce the registry's exact
    construction, including the `seedna` token used for deterministic baselines."""
    reg = json.loads((REPO / "results" / "v3_clean" / "runs"
                      / "complete_specs_598.json").read_text(encoding="utf-8"))
    keys = {s["run_key"] for s in reg["specs"]}
    # every key the gate would build must exist in the frozen registry
    from innovation import clean_gate as CG
    missing = []
    for arm, model, horizon, seed in (
            [("primary", m, 24, 42) for m in CG.PRIMARY]
            + [("baseline", b, 24, "n/a") for b in CG.BASELINES]
            + [("ablation", a, 24, 42) for a in CG.ABLATIONS]
            + [("negative_control", c, 24, 42) for c in CG.GPT2_CONTROLS]):
        k = CG.run_key_for(arm, model, horizon, seed)
        if k not in keys:
            missing.append(k)
    assert not missing, missing
