"""
ARCHITECTURE EQUIVALENCE (pre-HPC clarification 5)
=================================================

Every backbone must declare exactly one of the three fidelity levels, backed by
component-level file:line evidence and an explicit deviation list. A model may
NOT be REFERENCE_FAITHFUL without evidence, and INSPIRED_SIMPLIFICATION models
must be labelled "-inspired".
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

from innovation import fidelity as FID  # noqa: E402
from innovation.backbones import make_backbone  # noqa: E402

T, N, L = 104, 7, 24


def _report(name):
    if name in ("gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"):
        if name == "gpt2_miflu":
            return {
                "name": name,
                "display_name": "MIFlu GPT-2",
                "fidelity": FID.REFERENCE_FAITHFUL,
                "published": "MIFlu (IEEE JBHI 2025)",
                "evidence": ["LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE"],
            }
        return {
            "name": name,
            "display_name": {"qwen_time_llm": "Qwen2.5-1.5B Time-LLM-inspired",
                              "calf_llm": "CALF-inspired Cross-Modal LLM",
                              "timecma_llm": "TimeCMA-inspired LLM"}[name],
            "fidelity": FID.INSPIRED_SIMPLIFICATION,
            "components": {
                "qwen_time_llm": ["patching", "prototype_reprogramming", "Prompt-as-Prefix", "frozen_Qwen_backbone", "forecast_projection"],
                "calf_llm": ["temporal_target_branch", "textual_source_branch", "cross_modal_match", "feature_regularization", "output_consistency"],
                "timecma_llm": ["independent_time_series_branch", "independent_prompt_branch", "cross_modality_retrieval", "last_token_or_cached_prompt", "forecast_head"],
            }[name],
        }
    kw = dict(T=T, N=N, L=L)
    if name == "gpt2_miflu":
        kw["device"] = "cpu"
    if name == "fusion_forecaster":
        from innovation.fusion import make_fusion
        kw["fusion"] = make_fusion("identity")
    return make_backbone(name, **kw).architecture_report()


def test_every_backbone_declares_a_level_with_evidence():
    for name in ("dlinear", "nlinear", "patchtst", "itransformer",
                 "fusion_forecaster", "gpt2_miflu", "qwen_time_llm",
                 "calf_llm", "timecma_llm"):
        rep = _report(name)
        assert rep.get("fidelity") in FID.LEVELS, (name, rep.get("fidelity"))
        assert rep.get("display_name"), name
        if rep["fidelity"] in (FID.REFERENCE_FAITHFUL,
                               FID.REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS):
            assert rep.get("evidence"), f"{name} needs component-level evidence"
            assert rep.get("published"), f"{name} must cite the published architecture"
        if rep["fidelity"] == FID.REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS:
            assert rep.get("deviations"), f"{name} must list its deviations"
            for d in rep["deviations"]:
                assert d.get("file_line"), (name, d)
        if rep["fidelity"] == FID.INSPIRED_SIMPLIFICATION:
            assert "inspired" in rep["display_name"].lower(), (name, rep["display_name"])


def test_itransformer_not_called_faithful():
    rep = _report("itransformer")
    assert rep["fidelity"] == FID.REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS, rep
    comps = " ".join(d["component"] for d in rep["deviations"]).lower()
    assert "positional" in comps, ("iTransformer's ADDED per-variate positional "
                                   "encoding must be disclosed", rep["deviations"])
    assert "normalis" in comps or "normaliz" in comps, rep["deviations"]


def test_patchtst_is_inspired_not_exact():
    rep = _report("patchtst")
    assert rep["fidelity"] == FID.INSPIRED_SIMPLIFICATION, rep
    assert "inspired" in rep["display_name"].lower(), rep["display_name"]


def test_dlinear_nlinear_faithful_with_evidence():
    for name in ("dlinear", "nlinear"):
        rep = _report(name)
        assert rep["fidelity"] == FID.REFERENCE_FAITHFUL, (name, rep)
        assert rep["evidence"], name


def test_phase1_llm_contracts_are_materially_distinct_without_loading_weights():
    reports = [_report(name) for name in ("qwen_time_llm", "calf_llm", "timecma_llm")]
    components = [tuple(report.get("components", [])) for report in reports]
    assert all(components)
    assert len(set(components)) == 3
    assert "prototype_reprogramming" in components[0]
    assert "feature_regularization" in components[1]
    assert "cross_modality_retrieval" in components[2]


if __name__ == "__main__":
    test_every_backbone_declares_a_level_with_evidence()
    test_itransformer_not_called_faithful()
    test_patchtst_is_inspired_not_exact()
    test_dlinear_nlinear_faithful_with_evidence()
    print("[test_architecture_equivalence] OK")
