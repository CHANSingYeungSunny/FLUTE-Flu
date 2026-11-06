"""test_compact_input_normalization.py — D14 regression tests.

Reproduces Gate 571800 exactly: the Gate called
    compact_checkpoint.export_compact(run_dir, ckpt, <FULL RUN KEY>, ...)
in-process, and the old code evaluated
    CR.PRIMARY_MODELS["primary__nlinear__L24__seed42__w1"]
-> KeyError.

These tests are MODEL-FREE: no torch, no model construction, no weights. They
only exercise run-key resolution against the immutable 598-row registry.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import compact_checkpoint as CC        # noqa: E402
from innovation import clean_runner as CR              # noqa: E402

REG = json.loads((REPO / "results" / "v3_clean" / "runs"
                  / "complete_specs_598.json").read_text(encoding="utf-8"))
IMMEDIATE = [s for s in REG["specs"]
             if s.get("wave") == 1 and s.get("submittable")
             and s.get("executable_binding")]
DEFERRED = [s for s in REG["specs"] if not (s.get("submittable")
                                            and s.get("executable_binding"))]

# the exact run key that failed in Gate 571800
GATE_571800_KEY = "primary__nlinear__L24__seed42__w1"

# deterministic baselines are their own families: they are NOT members of
# PRIMARY_MODELS / VARIANTS, but they are legitimate resolved model tokens.
KNOWN_MODELS = set(CR.PRIMARY_MODELS) | set(CR.VARIANTS) | set(CR.BASELINES)


def _code_only(path: Path) -> str:
    """Executable lines only — comments may legitimately MENTION the old
    fragile cut when documenting why it was removed."""
    return "\n".join(l for l in path.read_text(encoding="utf-8").splitlines()
                     if not l.strip().startswith("#"))


@pytest.fixture(autouse=True)
def _deployment_root(monkeypatch):
    monkeypatch.setenv("INNOVATION_DEPLOYMENT_ROOT", str(REPO))


# ── the exact Gate 571800 failure ────────────────────────────────────────
def test_gate_571800_run_key_no_longer_raises_keyerror():
    """The regression itself: a full run key must resolve, not KeyError."""
    info = CC.normalise_spec_input(GATE_571800_KEY)
    assert info["model"] == "nlinear"
    assert info["horizon"] == 24


def test_old_fragile_path_would_have_failed():
    """Documented proof of the defect: PRIMARY_MODELS has no run-key entry."""
    with pytest.raises(KeyError):
        _ = CR.PRIMARY_MODELS[GATE_571800_KEY]
    assert GATE_571800_KEY not in CR.PRIMARY_MODELS
    assert GATE_571800_KEY not in CR.VARIANTS


def test_library_source_contains_no_run_key_string_cut():
    src = _code_only(REPO / "scripts" / "innovation" / "compact_checkpoint.py")
    assert 'spec.split("__")' not in src
    assert 'split("__")[1]' not in src
    assert 'split("__")' not in src


# ── resolution over the whole frozen order ───────────────────────────────
def test_every_immediate_run_key_resolves():
    assert len(IMMEDIATE) == 580
    for s in IMMEDIATE:
        info = CC.resolve_run_key(s["run_key"])
        assert info["model"] == s["model"]
        assert info["horizon"] == int(s["horizon"])
        assert info["run_key"] == s["run_key"]


def test_resolved_model_is_always_a_known_model_token():
    for s in IMMEDIATE:
        info = CC.resolve_run_key(s["run_key"])
        assert info["model"] in KNOWN_MODELS, (s["run_key"], info["model"])


def test_deferred_run_keys_are_rejected():
    assert DEFERRED, "the frozen registry must carry 18 deferred rows"
    for s in DEFERRED:
        with pytest.raises(CC.CompactInputError) as e:
            CC.resolve_run_key(s["run_key"])
        assert "deferred" in str(e.value)


# ── rejection classes ────────────────────────────────────────────────────
@pytest.mark.parametrize("bad", [
    "", "   ", "unknown__model__L24__seed42__w1",
    "../etc/passwd", "a/b", "a\\b", ".hidden", "/abs/key", "..",
])
def test_malformed_unknown_pathlike_rejected(bad):
    with pytest.raises(CC.CompactInputError):
        CC.resolve_run_key(bad)


def test_non_string_rejected():
    with pytest.raises(CC.CompactInputError):
        CC.resolve_run_key(None)          # type: ignore[arg-type]
    with pytest.raises(CC.CompactInputError):
        CC.resolve_run_key(42)            # type: ignore[arg-type]


def test_ambiguous_run_key_rejected(monkeypatch, tmp_path):
    """A registry with two identical run keys must be refused, not guessed."""
    root = tmp_path / "dep"
    (root / "results" / "v3_clean" / "runs").mkdir(parents=True)
    reg = {"specs": [
        {"run_key": "dup__w1", "model": "nlinear", "horizon": 24,
         "arm": "primary", "wave": 1, "submittable": True,
         "executable_binding": True},
        {"run_key": "dup__w1", "model": "dlinear", "horizon": 24,
         "arm": "primary", "wave": 1, "submittable": True,
         "executable_binding": True},
    ]}
    (root / "results" / "v3_clean" / "runs"
     / "complete_specs_598.json").write_text(json.dumps(reg), encoding="utf-8")
    with pytest.raises(CC.CompactInputError) as e:
        CC.resolve_run_key("dup__w1", deployment_root=str(root))
    assert "ambiguous" in str(e.value)


# ── shared entry: bare model names and CLI delegation ────────────────────
def test_bare_model_name_without_horizon_rejected():
    with pytest.raises(CC.CompactInputError) as e:
        CC.normalise_spec_input("nlinear")
    assert "horizon" in str(e.value)


def test_bare_model_name_with_horizon_resolves():
    info = CC.normalise_spec_input("nlinear", 60)
    assert info["model"] == "nlinear" and info["horizon"] == 60


def test_unverified_alias_rejected():
    with pytest.raises(CC.CompactInputError):
        CC.normalise_spec_input("nlinear_like_but_not_a_model", 24)


def test_export_and_restore_share_one_resolution():
    """Requirement: export_compact() and restore_and_compare() must use the
    SAME parsing. Verified by signature/source, not by running torch."""
    import inspect
    src = inspect.getsource(CC.export_compact)
    src2 = inspect.getsource(CC.restore_and_compare)
    assert "normalise_spec_input" in src
    assert "normalise_spec_input" in src2
    assert "normalise_spec_input" in inspect.getsource(CC.build_base_model)


def test_cli_delegates_to_the_same_entry():
    import inspect
    assert "normalise_spec_input" in inspect.getsource(CC.main)
    assert 'split("__")' not in _code_only(
        REPO / "scripts" / "innovation" / "compact_checkpoint.py")


# ── quota cases the Gate must get right ──────────────────────────────────
def test_no_registry_means_no_guess(monkeypatch, tmp_path):
    monkeypatch.setenv("INNOVATION_DEPLOYMENT_ROOT", str(tmp_path))
    with pytest.raises(CC.CompactInputError) as e:
        CC.resolve_run_key(GATE_571800_KEY)
    assert "registry not found" in str(e.value)
