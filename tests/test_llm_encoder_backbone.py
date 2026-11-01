"""test_llm_encoder_backbone.py — unit tests for the frozen-LLM adapter.

NO GPU, NO model download and NO `import transformers`: every test drives the
arm through `MockLLMEncoder` / `MockTokenizer` (pure torch) or asserts on the
functions around them. The real encoder is only constructed on a compute node.

Covered (the six required properties plus the guards around them):

1. shape            — `(B, 7, L)` for several `L` and several batch sizes;
2. channel independence — permuting the 7 input channels permutes the 7 output
   rows identically, and the head is ONE `nn.Linear(D, L)` (no per-variable
   parameters, no mixing);
3. frozen encoder   — after `optimizer.step()` every encoder parameter is
   **bitwise** identical (`torch.equal`, not `allclose`) and only head
   parameters moved;
4. layout           — the emitted cell passes
   `scripts/eval_windows.py::check_cell_layout` (window axis 0, variable axis
   1 = 7), and a deliberately transposed array is rejected;
5. determinism      — two runs with the same seed and the mock encoder are
   bit-identical;
6. cache            — the second forward with the same prompts does not increase
   the mock encoder's call count.

Run:
    python -m pytest -q tests/test_llm_encoder_backbone.py
"""
from __future__ import annotations

import importlib.util
import math
import os
import re
import sys

import numpy as np
import pytest
import torch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
for _path in (SCRIPTS_DIR, PROJECT_ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import llm_encoder_backbone as llm                       # noqa: E402
from eval_windows import check_cell_layout, eval_slice    # noqa: E402

T, N = 104, 7


# ── helpers ─────────────────────────────────────────────────────────────────
def make_arm(L: int = 24, batch: int = 8, seed: int = 42, mode: str = "embedding",
             **kwargs) -> llm.FrozenLLMEncoder:
    """Build the arm on the CPU with the tiny mock encoder."""
    return llm.FrozenLLMEncoder(T=T, N=N, L=L, mock_encoder=True,
                                encoder_batch_size=batch, seed=seed,
                                mock_mode=mode, mock_hidden_dim=32,
                                mock_vocab_size=512, **kwargs)


def fixed_x(batch: int, seed: int = 0) -> torch.Tensor:
    """`(B, 7, 104)` input from an explicit generator (repeatable in a test)."""
    gen = torch.Generator().manual_seed(seed)
    return torch.randn(batch, N, T, generator=gen)


def load_runner_module():
    """Import `scripts/train_backbone_966.py` under a private module name."""
    path = os.path.join(SCRIPTS_DIR, "train_backbone_966.py")
    spec = importlib.util.spec_from_file_location("_runner_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── 1. shape ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("L", [24, 36, 48, 60])
@pytest.mark.parametrize("batch", [1, 3, 8])
def test_output_shape_is_batch_by_channels_by_horizon(L: int, batch: int):
    """Forward is `(B, 7, 104) -> (B, 7, L)` for every horizon and batch size."""
    arm = make_arm(L=L, batch=4, mode="fixed")
    y = arm(fixed_x(batch))
    assert tuple(y.shape) == (batch, N, L)
    assert y.dtype == torch.float32
    assert torch.isfinite(y).all()


# ── 2. channel independence ─────────────────────────────────────────────────
def test_channel_permutation_permutes_output_rows_identically():
    """Permuting the 7 channels permutes the 7 output rows — the head is shared."""
    arm = make_arm(L=24, batch=8)
    x = fixed_x(2)
    y = arm(x)

    perm = torch.tensor([3, 0, 6, 1, 5, 2, 4])
    y_perm = arm(x[:, perm, :])
    assert torch.equal(y_perm, y[:, perm, :]), "channel permutation changed more than row order"

    # Non-vacuity: the encoder IS channel-sensitive, so the equality above is a
    # real statement about the head rather than a constant-output artefact.
    assert not torch.equal(y[:, 0, :], y[:, 1, :])

    # The head is exactly one Linear(D, L), i.e. it cannot mix variables.
    assert isinstance(arm.head, torch.nn.Linear)
    assert tuple(arm.head.weight.shape) == (arm.L, arm.hidden_dim)
    assert arm.head_parameters() == arm.hidden_dim * arm.L + arm.L
    assert arm.trainable_parameters() == arm.head_parameters()


# ── 3. frozen encoder ───────────────────────────────────────────────────────
def test_encoder_parameters_are_bit_identical_after_an_optimizer_step():
    """Only head parameters may move; every encoder tensor must stay bitwise equal."""
    arm = make_arm(L=24, batch=4)
    encoder_before = {name: param.detach().clone()
                      for name, param in arm.encoder.named_parameters()}
    head_before = {name: param.detach().clone()
                   for name, param in arm.head.named_parameters()}
    assert encoder_before, "the mock encoder must own parameters for this test to bite"
    assert all(not p.requires_grad for p in arm.encoder.parameters())

    x, target = fixed_x(2), torch.randn(2, N, 24)
    optimizer = torch.optim.Adam(
        [p for p in arm.parameters() if p.requires_grad], lr=1e-2)
    loss = torch.nn.functional.mse_loss(arm(x), target)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    for name, param in arm.encoder.named_parameters():
        assert torch.equal(param, encoder_before[name]), (
            f"frozen encoder tensor {name!r} changed (must be bit-identical)")
        assert param.grad is None, f"frozen encoder tensor {name!r} received a gradient"
    head_moved = [not torch.equal(param, head_before[name])
                  for name, param in arm.head.named_parameters()]
    assert any(head_moved), "the optimizer step moved nothing — test is vacuous"


def test_train_mode_never_unfreezes_the_encoder():
    """`model.train()` must not put the frozen encoder back into training mode."""
    arm = make_arm(L=24)
    arm.train()
    assert arm.head.training is True
    assert arm.encoder.training is False, "frozen encoder must stay in eval() (no dropout)"
    assert arm.encoder_trainable_parameters() == 0


# ── 4. layout ───────────────────────────────────────────────────────────────
def test_emitted_cell_passes_the_layout_guard_and_a_transposed_cell_is_rejected(tmp_path):
    """The written `pred_*.npz` is `(W, 7, L)`; a transposed one fails loudly."""
    W, L = 170, 24
    rng = np.random.RandomState(0)
    pred = rng.randn(W, N, L).astype(np.float32)
    target = rng.randn(W, N, L).astype(np.float32)
    starts = (np.arange(W, dtype=np.int32) + 773)

    path = llm.save_pred_cell(str(tmp_path / "pred_llm_encoder_L24_s42.npz"),
                              pred, target, starts, L=L, seed=42,
                              model="llm_encoder", profile="author_966",
                              containment="strict")
    cell = np.load(path, allow_pickle=False)

    assert set(cell.files) == set(llm.PRED_CELL_KEYS)
    assert cell["pred"].shape == (W, N, L) == cell["target"].shape
    assert cell["target_start_row"].shape == (W,)
    assert int(cell["L"]) == L and int(cell["seed"]) == 42
    assert str(cell["model"]) == "llm_encoder"
    assert str(cell["profile"]) == "author_966"
    assert str(cell["containment"]) == "strict"
    assert str(cell["space"]) == "standardized_train_fit_z"

    n_windows, n_eval = check_cell_layout(cell["pred"], cell["target"],
                                          cell["target_start_row"], L=L,
                                          label="llm_encoder_L24_s42")
    assert (n_windows, n_eval) == (170, 160)
    assert n_eval == eval_slice(W), "the shared (W//16)*16 evaluation rule must hold"

    # (a) a deliberately transposed variable/window array is rejected on read
    bad_path = str(tmp_path / "transposed_vars.npz")
    np.savez_compressed(bad_path,
                        pred=np.transpose(pred, (1, 0, 2)),
                        target=np.transpose(target, (1, 0, 2)),
                        target_start_row=starts)
    bad = np.load(bad_path, allow_pickle=False)
    with pytest.raises(ValueError):
        check_cell_layout(bad["pred"], bad["target"], bad["target_start_row"], L=L)
    # (b) a transposed lead axis is rejected too
    with pytest.raises(ValueError):
        check_cell_layout(np.transpose(pred, (0, 2, 1)), np.transpose(target, (0, 2, 1)),
                          starts, L=L)
    # (c) the writer refuses to emit it in the first place
    with pytest.raises(ValueError):
        llm.save_pred_cell(str(tmp_path / "never_written.npz"),
                           np.transpose(pred, (1, 0, 2)), np.transpose(target, (1, 0, 2)),
                           starts, L=L, seed=42, model="llm_encoder",
                           profile="author_966", containment="strict")
    assert not os.path.exists(tmp_path / "never_written.npz")


# ── 5. determinism ──────────────────────────────────────────────────────────
def test_two_runs_with_the_same_seed_are_bit_identical():
    """Same seed + same mock encoder => bit-identical predictions."""
    first, second = make_arm(L=24, seed=42), make_arm(L=24, seed=42)
    x = fixed_x(2)
    y_first, y_second = first(x), second(x)
    assert torch.equal(y_first, y_second)

    # Non-vacuity: a different head seed really does change the prediction.
    other = make_arm(L=24, seed=43)
    assert not torch.equal(y_first, other(x))


# ── 6. cache ────────────────────────────────────────────────────────────────
def test_second_forward_hits_the_cache_and_does_not_call_the_encoder():
    """The same prompts twice must not increase the encoder's call count."""
    arm = make_arm(L=24, batch=4, mode="fixed")
    x = fixed_x(2)

    y_first = arm(x)
    calls_after_first = arm.encoder.calls
    entries_after_first = len(arm.cache)
    assert calls_after_first == math.ceil(2 * N / 4), "chunked encoder pass is not exact"
    assert entries_after_first == 2 * N

    y_second = arm(x)
    assert arm.encoder.calls == calls_after_first, "second forward re-ran the encoder"
    assert len(arm.cache) == entries_after_first
    assert torch.equal(y_first, y_second)
    assert arm.cache.hits >= 2 * N


@pytest.mark.parametrize("batch", [1, 3, 8, 64])
def test_encoder_batch_size_is_exact_and_does_not_change_predictions(batch: int):
    """`--encoder-batch-size` only chunks the pass; predictions are identical."""
    reference = make_arm(L=24, batch=1)
    arm = make_arm(L=24, batch=batch)
    x = fixed_x(2)
    assert torch.equal(reference(x), arm(x))
    assert arm.encoder.calls == math.ceil(2 * N / batch)


def test_cache_persists_and_refuses_another_models_vectors(tmp_path):
    """A saved cache is reusable, and never serves a different model's vectors."""
    arm = make_arm(L=24)
    x = fixed_x(1)
    arm(x)
    cache_path = str(tmp_path / "encoder_cache.pt")
    assert arm.save_cache(cache_path) == cache_path
    assert os.path.exists(cache_path)

    fresh = make_arm(L=24)
    assert fresh.load_cache(cache_path) == len(arm.cache) > 0
    calls_before = fresh.encoder.calls
    fresh(x)
    assert fresh.encoder.calls == calls_before, "loaded cache was not used"

    foreign = llm.FrozenLLMEncoder(T=T, N=N, L=24, model_id="other/model",
                                   revision="0" * 40, mock_encoder=True,
                                   mock_hidden_dim=32, mock_vocab_size=512)
    with pytest.raises(ValueError):
        foreign.load_cache(cache_path)


# ── prompt / hidden-state / provenance guards ──────────────────────────────
def test_prompt_rendering_is_deterministic_comma_separated_and_4dp():
    """The prompt is a pure 4-dp, comma-separated rendering of the 104 values."""
    values = [0.0, 0.123456, -2.0] + [0.5] * (T - 3)
    prompt = llm.render_channel_prompt(values)
    assert prompt == llm.render_channel_prompt(list(values))
    assert f"{T} values" in prompt
    numbers = re.findall(r"-?\d+\.\d{4}", prompt)
    assert len(numbers) == T, f"expected {T} rendered values, found {len(numbers)}"
    assert "0.1235" in numbers and "-2.0000" in numbers
    assert ", " in prompt
    assert llm.prompt_sha256(prompt) == llm.prompt_sha256(prompt)
    assert len(llm.prompt_sha256(prompt)) == 64
    assert prompt not in llm.cache_key("m", "rev", prompt), "cache key must hash, not embed"

    # The cache key binds model id, revision and prompt together.
    keys = {llm.cache_key("m", "rev", prompt), llm.cache_key("m", "rev2", prompt),
            llm.cache_key("m2", "rev", prompt)}
    assert len(keys) == 3


def test_extract_last_hidden_state_handles_every_hf_output_shape():
    """A hidden-state tuple must yield its LAST layer, never logits."""
    layers = [torch.randn(2, 5, 3) for _ in range(4)]

    class Output:  # stand-in for `BaseModelOutputWithPoolingAndCrossAttentions`
        pass

    with_last = Output()
    with_last.last_hidden_state = layers[-1]
    assert llm.extract_last_hidden_state(with_last) is layers[-1]

    with_tuple = Output()
    with_tuple.hidden_states = tuple(layers)
    assert llm.extract_last_hidden_state(with_tuple) is layers[-1]

    assert llm.extract_last_hidden_state(tuple(layers)) is layers[-1]
    # HF `return_dict=False` + `output_hidden_states=True`:
    #   (logits, hidden_states_tuple, ...)  -> the nested layer stack wins.
    logits = torch.randn(2, 5, 11)
    assert llm.extract_last_hidden_state((logits, tuple(layers))) is layers[-1]
    # ...and never the logits, even though logits are also 3-D.
    assert llm.extract_last_hidden_state((logits, tuple(layers))).shape[-1] == 3
    # `(last_hidden_state, ...)` with no nested stack -> the 3-D tensor itself.
    assert llm.extract_last_hidden_state((layers[-1], None)) is layers[-1]

    plain = torch.randn(2, 5, 6)
    assert llm.extract_last_hidden_state(plain) is plain

    for bad in (None, (1, 2), torch.randn(2, 5)):
        with pytest.raises(TypeError):
            llm.extract_last_hidden_state(bad)


def test_mask_excludes_padding_from_the_mean_pool():
    """Mean pooling must ignore padded positions, whatever the padding side."""
    hidden = torch.tensor([[[1.0, 1.0], [3.0, 3.0], [99.0, 99.0]]])
    mask = torch.tensor([[1, 1, 0]])
    pooled = llm.masked_mean_pool(hidden, mask)
    assert torch.equal(pooled, torch.tensor([[2.0, 2.0]]))


def test_provenance_records_everything_the_manifest_needs():
    """Model id, pinned revision, versions, parameter counts and device."""
    arm = make_arm(L=24)
    provenance = arm.provenance()
    for field in ("model_id", "revision", "revision_pinned", "torch_version",
                  "transformers_version", "python_version", "device", "encoder",
                  "head", "encoder_batch_size", "prompt_template_version",
                  "determinism", "cache"):
        assert field in provenance, f"provenance is missing {field!r}"

    assert provenance["encoder"]["parameters"] == arm.encoder_parameter_count() > 0
    assert provenance["encoder"]["trainable_parameters"] == 0
    assert provenance["encoder"]["frozen"] is True
    assert provenance["encoder"]["eval_mode"] is True
    assert provenance["head"]["parameters"] == arm.hidden_dim * arm.L + arm.L
    assert provenance["head"]["shared_across_variables"] is True
    assert provenance["revision_pinned"] is True
    assert len(provenance["revision"]) == 40
    assert provenance["device"] == "cpu"


def test_mock_path_never_imports_transformers():
    """Unit tests must not depend on `transformers` (and neither must a dry run)."""
    assert llm.TRANSFORMERS_IMPORTED is False
    arm = make_arm(L=24)
    arm(fixed_x(1))
    arm.provenance()
    assert llm.TRANSFORMERS_IMPORTED is False


def test_real_encoder_requires_a_pinned_revision():
    """A publication run may not load an unpinned checkpoint."""
    with pytest.raises(ValueError, match="pinned revision"):
        llm.FrozenLLMEncoder(T=T, N=N, L=24, revision=None)
    mock_arm = llm.FrozenLLMEncoder(T=T, N=N, L=24, revision=None, mock_encoder=True,
                                    mock_hidden_dim=32, mock_vocab_size=512)
    assert mock_arm.provenance()["revision_pinned"] is False


def test_forward_rejects_wrong_channel_count_or_lookback():
    """Wrong N or T is a loud error, never a silent reshape."""
    arm = make_arm(L=24)
    with pytest.raises(ValueError, match="N=7"):
        arm(torch.randn(1, 5, T))
    with pytest.raises(ValueError, match="T=104"):
        arm(torch.randn(1, N, 99))
    with pytest.raises(ValueError, match="must be"):
        arm(torch.randn(N, T))


# ── runner wiring (end-to-end on CPU, no download) ─────────────────────────
def test_runner_registry_resolves_the_arm_and_train_one_emits_real_window_count(tmp_path):
    """`train_backbone_966.py` can build the arm and run a fit that exports (170, 7, 24)."""
    runner = load_runner_module()
    assert runner.BACKBONES["llm_encoder"][1] == "FrozenLLMEncoder"
    arm_class = runner.load_backbone_class("llm_encoder")
    assert arm_class.__name__ == "FrozenLLMEncoder"
    assert tuple(arm_class(T=T, N=N, L=24, mock_encoder=True,
                           mock_hidden_dim=32).forward(torch.zeros(1, N, T)).shape) == (1, N, 24)

    runner.LLM_ENCODER_OPTS.update({"mock_encoder": True, "encoder_batch_size": 8,
                                    "mock_hidden_dim": 32, "mock_vocab_size": 512,
                                    "device": "cpu"})
    rng = np.random.RandomState(0)
    data_dict = {"data_norm": rng.randn(966, N).astype(np.float32),
                 "train_end": 676, "val_end": 773, "n": 966, "train_df": None}
    out = runner.train_one(data_dict, "llm_encoder", 24, 42, 1, 16, "cpu",
                           str(tmp_path), "strict", log=lambda *a, **k: None,
                           max_train=8, max_val=8)
    assert out["test_pred"].shape == (170, N, 24)
    assert out["test_true"].shape == (170, N, 24)
    assert out["test_start"].shape == (170,)
    assert out["provenance"]["mock_encoder"] is True
    assert out["provenance"]["encoder"]["trainable_parameters"] == 0
    assert out["n_test"] == 170


if __name__ == "__main__":  # pragma: no cover - convenience only
    sys.exit(pytest.main([__file__, "-q"]))
