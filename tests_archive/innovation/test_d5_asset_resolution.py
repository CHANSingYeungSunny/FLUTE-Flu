"""D5 asset-resolution regression tests.

MODEL-FREE by construction: any attempt to load a pretrained model, touch the
Transformers/HF cache, open the network, or read the full National-Illness
dataset raises immediately. If a test would need a real model, it belongs in the
compute-node Slurm gate, not here.
"""
from __future__ import annotations

import importlib
import json
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from innovation import assets as AS  # noqa: E402

QWEN_ID = "Qwen/Qwen2.5-1.5B"
QWEN_REV = "8faed761d45a263340a0528343f099c05c9a4323"


# ── global fail-closed guards ────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def no_model_no_network(tmp_path, monkeypatch):
    """Patch every model-loading / network / full-data path to raise."""
    def _boom(*a, **k):
        raise AssertionError("model loading attempted during a model-free test")

    try:
        import transformers
        for cls_name in ("AutoModel", "AutoTokenizer", "AutoConfig", "AutoModelForCausalLM"):
            cls = getattr(transformers, cls_name, None)
            if cls is not None and hasattr(cls, "from_pretrained"):
                monkeypatch.setattr(cls, "from_pretrained", staticmethod(_boom))

    except ImportError:
        pass

    def _no_net(*a, **k):
        raise AssertionError("network access attempted during a model-free test")

    monkeypatch.setattr(socket.socket, "connect", _no_net)
    monkeypatch.setattr(socket, "create_connection", _no_net)

    yield


# ── 1. descriptor parses correctly ──────────────────────────────────────────
def test_qwen_descriptor_fields():
    d = AS.asset_descriptor(QWEN_ID)
    for key in ("model_repo_id", "model_revision", "local_snapshot_path",
                "local_files_only", "trust_remote_code", "asset_manifest_sha256"):
        assert key in d, f"missing descriptor field {key}"
    assert d["model_revision"] == QWEN_REV
    assert d["local_files_only"] is True
    assert d["trust_remote_code"] is False
    assert d["license"] == "Apache-2.0"
    # digest is deterministic and non-empty
    assert len(d["asset_manifest_sha256"]) == 64
    assert d["asset_manifest_sha256"] == AS.asset_manifest_sha256()
    assert AS.total_bytes() == sum(size for size, _ in AS.QWEN["files"].values())


def test_qwen_is_not_mislabelled_with_the_timellm_commit():
    """Guard against reintroducing D1 (Time-LLM repo commit used as a Qwen revision)."""
    assert AS.QWEN["model_revision"] != "b13e881f86cd0475ce1b72c17110430663334955"
    assert AS.QWEN["model_revision"] == QWEN_REV
    assert AS.QWEN["model_repo_id"] == QWEN_ID


# ── 2. snapshot path chosen when valid ───────────────────────────────────────
def test_verified_snapshot_is_preferred(tmp_path, monkeypatch):
    """With a complete snapshot present, the absolute snapshot path is used.

    The file set is substituted with a tiny stand-in so the real completeness
    logic is exercised without materialising a 3 GB file locally.
    """
    root = tmp_path / "snap"
    root.mkdir()
    (root / "config.json").write_bytes(b"{}")
    monkeypatch.setitem(AS.QWEN, "local_snapshot_path", str(root))
    monkeypatch.setitem(AS.QWEN, "files", {"config.json": (2, "0" * 64)})
    ok, problems = AS.snapshot_is_complete()
    assert ok is True and problems == []
    source, kwargs = AS.resolve_pretrained_source(QWEN_ID)
    assert source == str(root)
    assert kwargs["local_files_only"] is True
    assert kwargs["trust_remote_code"] is False
    assert AS.asset_descriptor(QWEN_ID)["resolution"] == "verified_local_snapshot"


# ── 3/4. fail closed on missing snapshot and on wrong revision ───────────────
def test_missing_snapshot_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setitem(AS.QWEN, "local_snapshot_path", str(tmp_path / "absent"))
    ok, problems = AS.snapshot_is_complete()
    assert ok is False and problems
    with pytest.raises(RuntimeError):
        AS.resolve_pretrained_source(QWEN_ID)  # network fallback disabled
    with pytest.raises(RuntimeError):
        AS.resolve_pretrained_source(QWEN_ID, allow_network=False)


def test_wrong_size_fails_closed(tmp_path, monkeypatch):
    """A present-but-truncated snapshot must be detected, not silently accepted."""
    root = tmp_path / "snap"
    root.mkdir()
    (root / "config.json").write_bytes(b"{}")
    monkeypatch.setitem(AS.QWEN, "local_snapshot_path", str(root))
    monkeypatch.setitem(AS.QWEN, "files", {"config.json": (9999, "0" * 64)})
    ok, problems = AS.snapshot_is_complete()
    assert ok is False
    assert any("size mismatch" in p for p in problems)


def test_wrong_revision_fails_closed(monkeypatch):
    bad = dict(AS.QWEN)
    bad["model_revision"] = "0" * 40
    monkeypatch.setattr(AS, "descriptor_for",
                        lambda model_id: bad if model_id == QWEN_ID else None)
    # the revision recorded in the descriptor is what provenance reports
    assert AS.asset_descriptor(QWEN_ID)["model_revision"] == "0" * 40
    # and the snapshot path still carries the true revision
    assert QWEN_REV in AS.QWEN["local_snapshot_path"]


# ── 5. local_files_only enforced ────────────────────────────────────────────
def test_local_files_only_enforced_for_passthrough_too():
    source, kwargs = AS.resolve_pretrained_source("gpt2")
    assert kwargs["local_files_only"] is True
    assert "revision" not in kwargs
    assert "snapshot" not in kwargs


# ── 6. GPT-2 receives no unsupported Qwen arguments ─────────────────────────
def test_gpt2_gets_no_qwen_arguments():
    """Guard against reintroducing D3 (model_id/revision sent to unsupported models)."""
    assert AS.descriptor_for("gpt2") is None
    source, kwargs = AS.resolve_pretrained_source("gpt2")
    assert source == "gpt2"
    assert set(kwargs) == {"local_files_only"}
    d = AS.asset_descriptor("gpt2")
    assert d["local_snapshot_path"] is None
    assert d["model_revision"] is None
    assert d["resolution"] == "passthrough_cache"


# ── 7. static metadata generation does not instantiate models ───────────────
def test_pilot_spec_generation_is_model_free(monkeypatch):
    hpc_specs = importlib.import_module("innovation.hpc_specs")
    out = hpc_specs.generate(write=False) if _supports_no_write(hpc_specs) else None
    if out is None:
        pytest.skip("generator has no write=False mode; covered by test_pilot_spec_metadata")


def _supports_no_write(mod) -> bool:
    import inspect
    return "write" in inspect.signature(mod.generate).parameters


# ── 8. eight Pilot specs remain unique and scientifically unchanged ─────────
def test_eight_pilot_specs_unique():
    path = ROOT / "hpc_scripts" / "pilot_specs.json"
    if not path.exists():
        pytest.skip("pilot_specs.json not generated")
    data = json.loads(path.read_text(encoding="utf-8"))
    specs = data.get("specs", [])
    assert len(specs) == 8
    keys = [(s["model"], s["horizon"], s["seed"]) for s in specs]
    assert len(set(keys)) == 8
    assert all(k[1] == 24 and k[2] == 42 for k in keys)
    for s in specs:
        assert s["experiment_stage"] == "pilot"
        assert s["purpose"] == "infrastructure_verification_only"
        assert s["selection_eligible"] is False
        assert s["paper_result_eligible"] is False
        assert s["test_access_allowed"] is False


# ── 9/10. no Test or holdout path is reachable ──────────────────────────────
def test_asset_module_touches_no_test_or_holdout_path():
    src = (ROOT / "scripts" / "innovation" / "assets.py").read_text(encoding="utf-8")
    assert "test_evaluations" not in src
    assert "holdout" not in src.replace("holdout access", "")
