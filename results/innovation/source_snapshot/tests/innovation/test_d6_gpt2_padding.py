"""D6 GPT-2 tokenizer-padding regression tests.

MODEL-FREE: no real tokenizer or model is ever loaded. Fake tokenizers/models are
used, and network / from_pretrained / CUDA are monkey-patched to raise.
"""
from __future__ import annotations

import socket
import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from innovation.backbones import llm_inspired as LI  # noqa: E402


# ── fakes ───────────────────────────────────────────────────────────────────
class FakeTokenizer:
    """Emulates HF tokenizers: GPT-2 has no pad token, Qwen does."""

    def __init__(self, pad_token_id=None, eos_token_id=50256,
                 eos_token="<|endoftext|>", vocab_size=50257):
        self.pad_token_id = pad_token_id
        self.eos_token_id = eos_token_id
        self.eos_token = eos_token
        self.vocab_size = vocab_size
        self.added_tokens = []
        self._pad = None

    @property
    def pad_token(self):
        return self._pad

    @pad_token.setter
    def pad_token(self, value):
        self._pad = value
        if value == self.eos_token:
            self.pad_token_id = self.eos_token_id
        else:
            self.added_tokens.append(value)

    def add_special_tokens(self, payload):
        self.added_tokens.append(payload)
        return 1

    def __len__(self):
        return self.vocab_size


class FakeEmbedding(torch.nn.Module):
    def __init__(self, rows: int, dim: int):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.zeros(rows, dim))


class FakeBackbone(torch.nn.Module):
    """Records any attempt to resize embeddings."""

    def __init__(self, rows=50257, dim=8):
        super().__init__()
        self.emb = FakeEmbedding(rows, dim)
        self.resize_calls = 0

    def get_input_embeddings(self):
        return self.emb

    def resize_token_embeddings(self, *a, **k):
        self.resize_calls += 1
        return self.emb


@pytest.fixture(autouse=True)
def no_load_no_net(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("model loading attempted during a model-free test")

    try:
        import transformers
        for name in ("AutoModel", "AutoTokenizer", "AutoConfig",
                     "AutoModelForCausalLM"):
            cls = getattr(transformers, name, None)
            if cls is not None and hasattr(cls, "from_pretrained"):
                monkeypatch.setattr(cls, "from_pretrained", staticmethod(_boom))
    except ImportError:
        pass

    def _no_net(*a, **k):
        raise AssertionError("network access attempted during a model-free test")

    monkeypatch.setattr(socket.socket, "connect", _no_net)
    monkeypatch.setattr(socket, "create_connection", _no_net)

    real_cuda = torch.cuda
    class _Guard:
        def is_available(self):
            raise AssertionError("CUDA use attempted during a model-free test")
        def __getattr__(self, _n):
            def _f(*a, **k):
                raise AssertionError("CUDA use attempted during a model-free test")
            return _f
    monkeypatch.setattr(torch, "cuda", _Guard())
    yield
    monkeypatch.setattr(torch, "cuda", real_cuda)


def _text_model(monkeypatch, tok):
    m = LI._FrozenTextModel(model_id="fake/gpt2", load_backbone=False, hidden_dim=8)
    m.tokenizer = tok
    m.model = FakeBackbone()
    return m


# ── 1. GPT-2-like tokenizer reuses EOS ──────────────────────────────────────
def test_gpt2_without_pad_reuses_eos(monkeypatch):
    tok = FakeTokenizer(pad_token_id=None, eos_token_id=50256)
    m = _text_model(monkeypatch, tok)
    m._ensure_pad_token()
    assert tok.pad_token_id == 50256
    assert tok.pad_token == tok.eos_token
    assert m.pad_token_reused_eos is True


# ── 2/3. no new vocabulary token, no embedding resize ───────────────────────
def test_no_vocab_growth_and_no_resize(monkeypatch):
    tok = FakeTokenizer(pad_token_id=None)
    m = _text_model(monkeypatch, tok)
    before = len(tok)
    m._ensure_pad_token()
    m.tokenizer_vocab_size = len(tok)
    m.model_embedding_rows = int(m.model.get_input_embeddings().weight.shape[0])
    assert len(tok) == before
    assert tok.added_tokens == []
    assert m.model.resize_calls == 0
    rep = m.pad_report()
    assert rep["vocab_grown"] is False
    assert rep["embedding_resized"] is False
    assert rep["vocab_size"] == before


# ── 4. Qwen pad configuration untouched ─────────────────────────────────────
def test_qwen_existing_pad_token_is_untouched(monkeypatch):
    tok = FakeTokenizer(pad_token_id=151643, eos_token_id=151645)
    m = _text_model(monkeypatch, tok)
    m._ensure_pad_token()
    assert tok.pad_token_id == 151643          # unchanged
    assert m.pad_token_reused_eos is False
    assert tok.added_tokens == []


# ── 5. fail closed without pad and without eos ──────────────────────────────
def test_missing_pad_and_eos_fails_closed(monkeypatch):
    tok = FakeTokenizer(pad_token_id=None, eos_token_id=None, eos_token=None)
    m = _text_model(monkeypatch, tok)
    with pytest.raises(RuntimeError):
        m._ensure_pad_token()


# ── 6. attention mask identifies non-padding tokens ─────────────────────────
def test_last_non_pad_selects_real_token():
    hidden = torch.arange(2 * 4 * 3, dtype=torch.float32).reshape(2, 4, 3)
    mask = torch.tensor([[1, 1, 1, 0], [1, 1, 0, 0]])
    out = LI._FrozenTextModel.last_non_pad(hidden, mask)
    assert torch.equal(out[0], hidden[0, 2])
    assert torch.equal(out[1], hidden[1, 1])   # never the padded slot


# ── 7. TimeCMA uses the last non-padding token ──────────────────────────────
def test_timecma_uses_last_non_padding_token(monkeypatch):
    tok = FakeTokenizer(pad_token_id=None)
    m = LI.TimeCMAInspired(T=104, N=7, L=24, model_id="fake/gpt2",
                           load_backbone=False, hidden_dim=8)
    m.text.tokenizer = tok
    m.text.model = FakeBackbone()
    series = torch.randn(2, 8)
    prompt_tokens = torch.randn(2, 5, 8)
    mask = torch.tensor([[1, 1, 1, 1, 0], [1, 1, 1, 0, 0]])
    aligned = m.retrieve_aligned_prompt(series, prompt_tokens, mask)
    assert aligned.shape == (2, 8)
    expected = m.text.last_non_pad(prompt_tokens, mask).unsqueeze(1)
    assert torch.allclose(aligned, m.prompt_projection(expected).squeeze(1),
                          atol=1e-6)


# ── 8. CALF ignores padded positions ────────────────────────────────────────
def test_calf_pooling_ignores_padding(monkeypatch):
    tok = FakeTokenizer(pad_token_id=None)
    m = LI.CALFInspired(T=104, N=7, L=24, model_id="fake/gpt2",
                        load_backbone=False, hidden_dim=8)
    m.text.tokenizer = tok
    m.text.model = FakeBackbone()
    textual = torch.randn(2, 5, 8)
    mask = torch.tensor([[1, 1, 1, 1, 0], [1, 1, 1, 0, 0]])
    pooled = m._text_pool(textual, mask)
    assert torch.equal(pooled, m.text.last_non_pad(textual, mask))
    # a masked batch must differ from naive last-position selection
    assert not torch.allclose(pooled, textual[:, -1])


# ── 9. shapes: single and batched ───────────────────────────────────────────
def test_last_non_pad_shapes():
    for b, t, d in ((1, 3, 8), (4, 6, 8), (2, 1, 8)):
        hidden = torch.randn(b, t, d)
        mask = torch.ones(b, t, dtype=torch.long)
        out = LI._FrozenTextModel.last_non_pad(hidden, mask)
        assert out.shape == (b, d)


# ── 10. empty / overlong prompts ────────────────────────────────────────────
def test_prompt_edge_cases():
    hidden = torch.randn(1, 3, 8)
    mask = torch.tensor([[0, 0, 0]])       # fully padded -> clamp keeps index 0, no crash
    out = LI._FrozenTextModel.last_non_pad(hidden, mask)
    assert out.shape == (1, 8)


# ── 11–13. G1 / G2 / D5 remain intact ───────────────────────────────────────
def test_g1_statistics_still_required():
    m = LI.QwenTimeLLM(T=104, N=7, L=24, model_id="fake/qwen",
                       load_backbone=False)
    assert m.train_statistics is None
    with pytest.raises(ValueError):
        m.set_train_statistics({"horizon": 24})            # incomplete
    m.set_train_statistics({"horizon": 24, "channel_count": 7,
                            "target_name": "ILITOTAL"})
    assert m.train_statistics is not None


def test_g2_routing_and_d5_snapshot_unchanged():
    from innovation import assets as AS
    assert AS.QWEN["model_revision"] == "8faed761d45a263340a0528343f099c05c9a4323"
    assert AS.descriptor_for("gpt2") is None
    source, kwargs = AS.resolve_pretrained_source("gpt2")
    assert source == "gpt2" and set(kwargs) == {"local_files_only"}


# ── 14. static source hygiene ───────────────────────────────────────────────
def test_source_never_resizes_or_adds_tokens():
    src = (ROOT / "scripts/innovation/backbones/llm_inspired.py").read_text(encoding="utf-8")
    assert "resize_token_embeddings" not in src
    assert "add_special_tokens" not in src
    assert "test_evaluations" not in src


def test_eight_pilot_specs_unchanged():
    import json
    path = ROOT / "hpc_scripts" / "pilot_specs.json"
    if not path.exists():
        pytest.skip("pilot_specs.json not generated")
    specs = json.loads(path.read_text(encoding="utf-8")).get("specs", [])
    assert len(specs) == 8
    assert all(s["horizon"] == 24 and s["seed"] == 42 for s in specs)
    assert all(s["test_access_allowed"] is False and s["selection_eligible"] is False
               for s in specs)
