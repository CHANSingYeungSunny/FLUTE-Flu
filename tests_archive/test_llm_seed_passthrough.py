"""The seed must reach the LLM arm's training path — a regression test.

Why this exists
--------------
On 2026-11-02 three seeds (42/43/44) of `ds_r1_distill_qwen1_5b` and
`qwen25_1_5b` were found to be **bit-identical**: `np.array_equal(pred_a,
pred_b) is True` and `max|dpred| == 0` for all 24 seed pairs across four
horizons, while the npz files still recorded the correct seed. The cause was
that `LLM_ENCODER_OPTS` (filled once in `main()`) never carried `seed`, so
`FrozenLLMEncoder` fell back to its default `seed=42` and re-seeded the global
RNG (`torch.manual_seed`) after `train_one` had called `set_seed(seed + L)`.
Head initialisation and the DataLoader shuffle order were therefore the same
for every seed, and any "mean +- sd over seeds" reported for an LLM arm had a
standard deviation of exactly zero **by construction**.

These tests pin the invariant that makes the defect impossible to reintroduce
silently:

  * `build_model("llm_encoder", ..., seed=s)` gives a head that depends on `s`;
  * the same `s` twice is reproducible;
  * the process RNG left behind by construction is seeded with `s + L`, i.e.
    the arm follows the same `set_seed(seed + L)` convention as the other arms;
  * the recorded provenance says `manual_seed == s + L`, which is the field the
    pipeline gate keys on.

They use the CPU mock encoder, so no checkpoint, no GPU and no `transformers`
import is involved.
"""
from __future__ import annotations

import importlib.util
import os
import sys

import pytest

torch = pytest.importorskip("torch")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_ROOT, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


def _load_runner():
    path = os.path.join(_SCRIPTS, "train_backbone_966.py")
    spec = importlib.util.spec_from_file_location("_runner_seedtest", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def runner():
    mod = _load_runner()
    # Mock encoder: CPU, deterministic, no download, no real checkpoint.
    mod.LLM_ENCODER_OPTS.clear()
    mod.LLM_ENCODER_OPTS.update({
        "mock_encoder": True,
        "mock_hidden_dim": 32,
        "mock_mode": "embedding",
        "device": "cpu",
        "local_files_only": True,
        "cache_path": None,
        "allow_unpinned_revision": True,
    })
    return mod


def _head(runner, seed, L=24):
    m = runner.build_model("llm_encoder", 104, 7, L, "cpu", seed=seed)
    return m, m.head.weight.detach().clone(), m.head.bias.detach().clone()


def test_seed_reaches_the_head(runner):
    """Different seeds must produce different heads — the actual defect."""
    _m42, w42, b42 = _head(runner, 42)
    _m43, w43, b43 = _head(runner, 43)
    assert not torch.equal(w42, w43), (
        "seed 42 and 43 produced an identical head weight: the seed is not "
        "reaching FrozenLLMEncoder (LLM_ENCODER_OPTS missing 'seed')")
    assert not torch.equal(b42, b43)


def test_same_seed_is_reproducible(runner):
    """The fix must not cost determinism: one seed, one head."""
    _a, wa, ba = _head(runner, 43)
    _b, wb, bb = _head(runner, 43)
    assert torch.equal(wa, wb) and torch.equal(ba, bb)


def test_horizon_enters_the_seed(runner):
    """`seed + L` convention: the same seed at two horizons is two draws."""
    _a, w24, _ = _head(runner, 42, L=24)
    _b, w60, _ = _head(runner, 42, L=60)
    # heads of different shapes cannot be compared directly; compare the first
    # 24 output rows, which both horizons have.
    assert not torch.equal(w24, w60[:24, :])


def test_process_rng_is_left_on_seed_plus_horizon(runner):
    """The arm must leave the global RNG at `seed + L`, like the other arms.

    This is what makes the DataLoader shuffle order seed-dependent. Before the
    fix the adapter left it at its own default (42) for every cell.
    """
    runner.build_model("llm_encoder", 104, 7, 24, "cpu", seed=43)
    assert torch.initial_seed() == 43 + 24


def test_provenance_records_the_real_seed(runner):
    """`determinism.manual_seed` is the field the pipeline gate reads."""
    m, _w, _b = _head(runner, 44)
    prov = m.provenance()
    assert prov["determinism"]["manual_seed"] == 44 + 24


def test_other_arms_are_unaffected(runner):
    """The fix is confined to `mode == "llm"`: a trained arm ignores the kwarg."""
    nlinear = runner.build_model("nlinear", 104, 7, 24, "cpu")
    assert not hasattr(nlinear, "provenance")
    # and the legacy call signature still works (preflight passes no seed)
    nlinear2 = runner.build_model("nlinear", 104, 7, 24, "cpu", seed=None)
    assert type(nlinear2).__name__ == type(nlinear).__name__
