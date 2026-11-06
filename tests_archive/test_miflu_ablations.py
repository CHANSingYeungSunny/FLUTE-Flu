"""test_miflu_ablations.py — Table VIII flags on `scripts/train_miflu.py` (CPU only).

The flag contract this file locks down
--------------------------------------
* **Defaults unchanged** — `resolve_variant` with no ablation flag returns
  `CONFIG` unchanged, so every published number stays reproducible from the
  default command line.
* `--no-lora` toggles **only** `use_lora` (the GPT-2 blocks stay frozen but lose
  their LoRA adapters).
* `--no-text` removes the text branch (`use_text=False` **and**
  `text_embedder="none"`), and refuses to be combined with an embedder that would
  still build one.
* `--num-layers K` sets the ForecastingLLM depth only, with range guards.
* `--text-embedder {author_file,prompt,none}` selects the text source; `none`
  implies `--no-text`.
* Each variant is **recorded** (a manifest entry), so the queue can name the
  variants as separate task kinds.
* The model-level truth: `use_text=False` makes the forward pass *ignore* the
  text tensor (two different text tensors give bit-identical predictions), and
  `use_lora=False` removes the LoRA parameters.
* The legacy text-batch expression is reproduced bit-identically by `_text_batch`,
  so the default path's numerics cannot drift.

Run:  python -m pytest -q tests/test_miflu_ablations.py
"""
from __future__ import annotations

import argparse
import os
import sys

import pytest
import torch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(PROJECT_ROOT, "scripts")
for _p in (SCRIPTS, PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import train_miflu as tm                        # noqa: E402
from configs import CONFIG                      # noqa: E402


def make_args(**overrides):
    """The exact default namespace `train_miflu.main` builds (no ablation flags)."""
    base = dict(horizon=24, reps=CONFIG["num_repetitions"],
                epochs=CONFIG["epochs"], batch=CONFIG["batch_size"],
                seed=2021, learning_rate=CONFIG["learning_rate"],
                text_source="author_file", text_embedder=None,
                no_lora=False, no_text=False, num_layers=None,
                ablation_label=None, fold=0, containment="start",
                profile="author_966")
    base.update(overrides)
    return argparse.Namespace(**base)


# ── defaults ───────────────────────────────────────────────────────────────
def test_default_flags_reproduce_config_exactly():
    eff, embedder, rec = tm.resolve_variant(make_args(), CONFIG)
    assert embedder == "author_file"
    assert rec["variant"] == "full"
    assert rec["is_default_config"] is True
    for key in ("T", "L_list", "N", "Lp", "S", "K", "lora_r", "lora_alpha", "D",
                "attn_heads"):
        assert eff[key] == CONFIG[key], key
    assert eff["use_lora"] is True and eff["use_text"] is True
    assert eff["num_repetitions"] == CONFIG["num_repetitions"]
    assert eff["epochs"] == CONFIG["epochs"]
    assert eff["batch_size"] == CONFIG["batch_size"]
    assert eff["learning_rate"] == CONFIG["learning_rate"]


def test_legacy_text_source_alias_still_works():
    _, embedder, _ = tm.resolve_variant(make_args(text_source="prompt"), CONFIG)
    assert embedder == "prompt"
    # an explicit --text-embedder wins over the deprecated alias
    _, embedder2, _ = tm.resolve_variant(
        make_args(text_source="prompt", text_embedder="author_file"), CONFIG)
    assert embedder2 == "author_file"


# ── --no-lora ──────────────────────────────────────────────────────────────
def test_no_lora_toggles_only_use_lora():
    eff, embedder, rec = tm.resolve_variant(make_args(no_lora=True), CONFIG)
    assert eff["use_lora"] is False
    assert eff["use_text"] is True and embedder == "author_file"
    assert eff["K"] == CONFIG["K"] and eff["epochs"] == CONFIG["epochs"]
    assert rec["variant"] == "no_lora" and rec["is_default_config"] is False
    assert rec["lora_r"] == 0


# ── --no-text / --text-embedder none ───────────────────────────────────────
def test_no_text_removes_the_text_branch():
    eff, embedder, rec = tm.resolve_variant(make_args(no_text=True), CONFIG)
    assert eff["use_text"] is False
    assert embedder == "none"
    assert eff["use_lora"] is True
    assert rec["variant"] == "no_text"


def test_text_embedder_none_implies_no_text():
    eff, embedder, rec = tm.resolve_variant(
        make_args(text_embedder="none"), CONFIG)
    assert embedder == "none" and eff["use_text"] is False
    assert rec["variant"] == "no_text"


def test_no_text_with_a_real_embedder_is_refused():
    with pytest.raises(SystemExit):
        tm.resolve_variant(make_args(no_text=True, text_embedder="prompt"), CONFIG)
    with pytest.raises(SystemExit):
        tm.resolve_variant(make_args(no_text=True, text_embedder="author_file"),
                           CONFIG)


def test_two_switches_at_once_is_refused():
    with pytest.raises(SystemExit):
        tm.resolve_variant(make_args(no_lora=True, no_text=True), CONFIG)


# ── --num-layers ───────────────────────────────────────────────────────────
def test_num_layers_sets_k_only():
    eff, _, rec = tm.resolve_variant(make_args(num_layers=4), CONFIG)
    assert eff["K"] == 4
    assert eff["lora_r"] == CONFIG["lora_r"]
    assert rec["num_layers"] == 4 and rec["base_num_layers"] == CONFIG["K"]
    assert rec["variant"] == "K4"


@pytest.mark.parametrize("bad", [0, -1, 13])
def test_num_layers_is_range_checked(bad):
    with pytest.raises(SystemExit):
        tm.resolve_variant(make_args(num_layers=bad), CONFIG)


# ── the text-batch helper must not change the default numerics ─────────────
def test_text_batch_matches_the_legacy_expression_bit_for_bit():
    pc = torch.randn(1, 7, 16)
    batch = 4
    legacy = pc.expand(batch, -1, -1) if pc.shape[0] == 1 else pc[:batch]
    assert torch.equal(tm._text_batch(pc, batch), legacy)
    pc_many = torch.randn(6, 7, 16)
    assert torch.equal(tm._text_batch(pc_many, 4), pc_many[:4])
    assert tm._text_batch(None, 4) is None


# ── model-level toggles (real MIFlu class, tiny shapes, no training) ───────
def _build(**kwargs):
    try:
        return tm.MIFlu(N=1, T=104, L=24, Lp=24, S=2, K=2, lora_r=4,
                        device="cpu", use_text_ln=False, **kwargs)
    except Exception as exc:                    # pragma: no cover - env dependent
        pytest.skip(f"GPT-2 weights unavailable for the model-level check: {exc}")


def test_num_layers_reaches_the_transformer_stack():
    m = _build(use_lora=True, use_text=True)
    assert len(m.forecasting_llm.blocks) == 2


def test_no_lora_removes_the_lora_parameters():
    with_lora = _build(use_lora=True, use_text=True)
    without = _build(use_lora=False, use_text=True)
    n_with = sum(p.numel() for p in with_lora.forecasting_llm.parameters()
                 if p.requires_grad)
    n_without = sum(p.numel() for p in without.forecasting_llm.parameters()
                    if p.requires_grad)
    assert n_with > n_without, "disabling LoRA must remove trainable parameters"


def test_no_text_makes_the_forward_pass_ignore_the_text_tensor():
    """`use_text=False` must make the prediction independent of the text tensor.

    This is the *structural* contract of the ablation. It is asserted on the real
    class, not inferred from the flag.

    The companion assertion (that the DEFAULT arm still depends on the text) is
    deliberately **not** made: with `author_faithful=True` the text tokens are
    appended after the time patches and the attention mask is causal
    (`_lora_attention` builds a `tril` mask, the head reads the first
    `num_patches` positions), so the forecast cannot see the text — which is
    exactly the unresolved contradiction of `AGENTS.md` §2 rule 6. That is
    asserted below as the documented state so a future fix fails loudly instead
    of silently changing a published number.
    """
    x = torch.randn(1, 1, 104)
    ht_a = torch.randn(1, 8, 768)
    ht_b = torch.randn(1, 8, 768)
    off = _build(use_lora=True, use_text=False).eval()
    with torch.no_grad():
        y_a = off(x, htext=ht_a)[0]
        y_b = off(x, htext=ht_b)[0]
    assert torch.equal(y_a, y_b), "the no-text arm still depends on the text tensor"


def test_default_text_pathway_is_masked_out_documented_state():
    """ASSERTED CURRENT STATE (AGENTS.md §2 rule 6): the text branch cannot move
    a prediction because the causal mask hides it from the forecast positions.

    If this test ever starts failing, someone changed the fusion and the text
    pathway became live — which is a *finding*, not a regression: record it in
    `docs/LEDGER.md` and re-run every text-related number.
    """
    x = torch.randn(1, 1, 104)
    on = _build(use_lora=True, use_text=True).eval()
    with torch.no_grad():
        z_a = on(x, htext=torch.randn(1, 8, 768))[0]
        z_b = on(x, htext=torch.randn(1, 8, 768))[0]
    assert torch.equal(z_a, z_b), (
        "the default arm now DEPENDS on the text input: the causal-mask "
        "explanation of rule 6 no longer holds — record this in docs/LEDGER.md")


def test_no_text_and_full_arms_agree_bitwise_on_cpu():
    """The consequence for Table VIII: `--no-text` cannot move a number here."""
    x = torch.randn(1, 1, 104)
    ht = torch.randn(1, 8, 768)
    torch.manual_seed(0)
    full = _build(use_lora=True, use_text=True).eval()
    torch.manual_seed(0)          # same initial weights for both arms
    notext = _build(use_lora=True, use_text=False).eval()
    with torch.no_grad():
        a = full(x, htext=ht)[0]
        b = notext(x, htext=ht)[0]
    assert torch.equal(a, b), (
        "the two arms differ: the text branch is live, so the Table VIII "
        "'w/o multimodality' row can move — update the QUEUE_ROWS doc")


# ── the variant is recorded in the manifest ───────────────────────────────
def test_manifest_records_the_variant_and_the_fold(tmp_path):
    _, _, rec = tm.resolve_variant(make_args(no_lora=True), CONFIG)
    path = tmp_path / "manifest_miflu_L24_s2021_no_lora.json"
    tm.write_run_manifest(
        str(path), L=24, seed=2021, config={"K": CONFIG["K"], "epochs": 1},
        variant_record=rec, fold=None, profile="author_966",
        containment="strict", wall_seconds=1.25, ckpt_path=None,
        artefacts={"npz": None}, best_rep=None)
    import json
    m = json.loads(path.read_text(encoding="utf-8"))
    assert m["variant"]["variant"] == "no_lora"
    assert m["ablation_variant"] == "no_lora"
    assert m["variant"]["use_lora"] is False
    assert m["fold"] is None
    assert m["hardware"]["run_device"] in ("cpu", "cuda")
    assert m["library_versions"]["torch"] and m["library_versions"]["python"]
    assert m["code"]["runner"]["sha256"] and len(m["code"]["runner"]["sha256"]) == 64
    assert m["checkpoint"]["sha256"] is None      # no checkpoint path given


def test_cli_exposes_every_ablation_flag(capsys):
    with pytest.raises(SystemExit) as ei:
        tm.main(["--help"])
    assert ei.value.code == 0
    help_text = capsys.readouterr().out
    for flag in ("--no-lora", "--no-text", "--num-layers", "--text-embedder",
                 "--ablation-label", "--fold"):
        assert flag in help_text, flag
    assert "author_file,prompt,none" in help_text


if __name__ == "__main__":       # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
