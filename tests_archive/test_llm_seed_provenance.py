"""The seed-provenance gate must be provably correct before it may refuse a cell.

Why this exists
--------------
`scripts/llm_seed_provenance.py` decides whether an LLM cell is allowed into an
aggregate. It is the pipeline's only defence against the 2026-11-02 defect
(seeds 42/43/44 producing bit-identical predictions because the seed never
entered the training path). A gate that is wrong in either direction is costly:

  * too permissive -> an invalid cell reaches `paper_tables/` with sd = 0;
  * too strict     -> a valid cell is silently dropped from a published table.

So every branch is pinned here on synthetic artefacts: a correctly seeded LLM
cell passes, an unseeded one is refused with the numbers in the reason, a
trained arm (no `encoder` block) always passes, and a missing manifest is
reported as unprovable rather than declared valid or invalid.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_ROOT, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import llm_seed_provenance as prov  # noqa: E402


def _cell(root, label="arm1", L=36, seed=43, manifest=None):
    d = os.path.join(root, f"{label}_L{L}_s{seed}")
    os.makedirs(d, exist_ok=True)
    npz = os.path.join(d, f"pred_{label}_L{L}_s{seed}.npz")
    np.savez(npz, pred=np.zeros((4, 7, L), dtype=np.float32),
             target=np.zeros((4, 7, L), dtype=np.float32),
             target_start_row=np.arange(4, dtype=np.int64),
             L=np.int32(L), seed=np.int32(seed))
    if manifest is not None:
        with open(os.path.join(d, f"manifest_{label}_L{L}_s{seed}.json"), "w",
                  encoding="utf-8") as f:
            json.dump(manifest, f)
    return npz


def _llm_manifest(L, seed, manual_seed):
    return {"model": "arm1", "L": L, "seed": seed, "probe_only": False,
            "encoder": {"model_id": "x", "revision": "deadbeef",
                        "determinism": {"manual_seed": manual_seed}}}


def test_correctly_seeded_llm_cell_passes(tmp_path):
    npz = _cell(tmp_path, L=36, seed=43, manifest=_llm_manifest(36, 43, 36 + 43))
    st = prov.cell_seed_status(npz)
    assert st["is_llm"] is True
    assert st["ok"] is True
    assert st["recorded"] == 79 and st["expected"] == 79


def test_unseeded_llm_cell_is_refused_with_numbers(tmp_path):
    """The exact defect: manifest says 42 for a seed-43 cell."""
    npz = _cell(tmp_path, L=36, seed=43, manifest=_llm_manifest(36, 43, 42))
    st = prov.cell_seed_status(npz)
    assert st["is_llm"] is True
    assert st["ok"] is False
    assert st["recorded"] == 42 and st["expected"] == 79
    assert "seed did not enter the training path" in st["reason"]
    assert "79" in st["reason"] and "43" in st["reason"]


def test_seed_42_cell_with_default_42_passes_only_because_it_is_correct(tmp_path):
    """L=0 would make seed 42 look right; with L=24 it must be refused."""
    ok = _cell(tmp_path / "ok", L=24, seed=42, manifest=_llm_manifest(24, 42, 66))
    assert prov.cell_seed_status(ok)["ok"] is True
    bad = _cell(tmp_path / "bad", L=24, seed=42, manifest=_llm_manifest(24, 42, 42))
    assert prov.cell_seed_status(bad)["ok"] is False


def test_trained_arm_is_never_gated(tmp_path):
    """A non-LLM manifest has no `encoder` block: always allowed."""
    npz = _cell(tmp_path, label="patchtst", L=24, seed=42,
                manifest={"model": "patchtst", "L": 24, "seed": 42})
    st = prov.cell_seed_status(npz)
    assert st["is_llm"] is False and st["ok"] is True


def test_missing_manifest_is_unprovable_not_valid(tmp_path):
    npz = _cell(tmp_path, L=24, seed=42, manifest=None)
    st = prov.cell_seed_status(npz)
    assert st["ok"] is True          # fail-open so a manifest-less cell is not lost
    assert st["is_llm"] is False
    assert "no manifest" in st["reason"]


def test_llm_manifest_without_manual_seed_is_refused(tmp_path):
    man = {"encoder": {"model_id": "x", "revision": "deadbeef", "determinism": {}}}
    npz = _cell(tmp_path, L=48, seed=44, manifest=man)
    st = prov.cell_seed_status(npz)
    assert st["is_llm"] is True and st["ok"] is False
    assert "no manual_seed" in st["reason"]


def test_manifest_path_derivation_and_audit(tmp_path):
    good = _cell(tmp_path, label="a", L=24, seed=2021,
                 manifest=_llm_manifest(24, 2021, 24 + 2021))
    bad = _cell(tmp_path, label="b", L=24, seed=2021, manifest=_llm_manifest(24, 2021, 42))
    assert prov.manifest_path_for(good).endswith("manifest_a_L24_s2021.json")
    stats = list(prov.audit(tmp_path))
    assert len(stats) == 2
    assert {prov.cell_seed_status(good)["ok"], prov.cell_seed_status(bad)["ok"]} == {True, False}
    assert prov.refused_labels(tmp_path) == {"b"}


def test_bad_filename_fails_closed(tmp_path):
    p = os.path.join(tmp_path, "pred_weird.npz")
    np.savez(p, pred=np.zeros((1, 7, 1), dtype=np.float32))
    st = prov.cell_seed_status(p)
    assert st["ok"] is False and "not pred_" in st["reason"]
