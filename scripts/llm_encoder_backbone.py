#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""llm_encoder_backbone.py — the missing adapter: frozen LLM encoder + shared head.

WHY THIS FILE EXISTS
--------------------
`docs/LLM_ARMS.md` lists the LLM roster, but until now **nothing converted an
LLM's frozen representation into the array the benchmark expects**, so no LLM
arm could enter the comparison. This module is that conversion, and only that:

    x (B, 7, 104)  --[per-channel text prompt]-->  frozen causal/instruct LLM
                   --[mean-pooled last hidden state]-->  z (B, 7, D)
                   --[ONE shared nn.Linear(D, L)]-->  y_hat (B, 7, L)

No training of the encoder happens here, and no benchmark number is produced by
this file on its own. The GPU runs happen later; this file plus
`tests/test_llm_encoder_backbone.py` prove the code path on CPU with a mock
encoder (no GPU, no model download).

BENCHMARK CONTRACT (mirrors `scripts/train_backbone_966.py`)
-----------------------------------------------------------
`forward(x) -> y_hat` with `x = (B, N=7, T=104)` and `y_hat = (B, 7, L)`, both in
the train-fitted z-space. The exported cell (`pred_*.npz`) stores **`(W, 7, L)`**
— window axis **0**, variable axis 1, lead axis 2 — which is exactly what
`scripts/eval_windows.py::check_cell_layout` asserts; a transposed export is
rejected loudly. `save_pred_cell()` below writes the same key set as
`train_backbone_966.py`, so a cell written through this module is
indistinguishable from any other arm's cell.

CHANNEL INDEPENDENCE (why the head is legitimate)
-------------------------------------------------
`forward` reshapes `(B, N, T)` to `(B*N, T)`, applies the *same* `nn.Linear(D, L)`
to every row and reshapes back to `(B, N, L)`. This is the identical convention
as `innovation/backbones/classic_nn.py::_ChannelIndependent` (shared weights
across variables, DLinear `individual=False`), so the 7-variable forecast cannot
mix channels: permuting the 7 input channels permutes the 7 output rows and
nothing else. `docs/LLM_ARMS.md` methodology ③ ("shared head + frozen base") is
therefore enforced structurally, not by convention.

MEMORY DISCIPLINE (docs/LLM_ARMS.md: Qwen3.8-27B = 54.73 GB in bf16 on A100)
---------------------------------------------------------------------------
* the encoder is only ever run under `torch.no_grad()`, so **no autograd graph
  over encoder activations is ever retained** — the graph that is kept alive is
  the head's, whose size is `B*N*D`, i.e. megabytes;
* the encoder pass is **chunked** by `encoder_batch_size` (CLI
  `--encoder-batch-size`), so the peak live tensor set is one chunk, never every
  window in the dataset;
* pooled vectors are cached on **CPU** (float32), so after the first pass the
  encoder itself can be parked back on the host
  (`release_encoder_to_cpu()`); training then touches only cached vectors and
  the head.

DETERMINISM
-----------
`torch.manual_seed(seed)` is fixed before the head is created (and re-applied
just before `nn.Linear`, because the encoder may consume RNG), the encoder is
put in `eval()` mode with every parameter `requires_grad=False`, no sampling /
`generate()` is used (a single forward pass with `use_cache=False`), and pooled
vectors are cached by `(model_id, revision, prompt_sha256)`, so a repeated run
returns bit-identical vectors without touching the model again. The prompt
itself is deterministic: z-space values rounded to 4 dp, comma-separated.

PROVENANCE (for the run manifest — AGENTS.md rule 12)
-----------------------------------------------------
`provenance()` returns the model id, the pinned revision sha, torch /
transformers / python versions, the encoder's parameter count (total and
trainable), the pooling rule, the device it ran on and the cache statistics.
`train_backbone_966.py --backbone llm_encoder` writes this into
`manifest_llm_encoder_L{L}_s{seed}.json` next to the cell.

ENVIRONMENTS (docs/LLM_ARMS.md: two venvs, never one)
-----------------------------------------------------
The adapter does not assume an environment. `qwen3_5` needs `mlflu_llm`
(transformers 5.22.1, Python 3.11); everything else uses `mlflu_hpc`
(transformers 4.57.6, Python 3.9). The HF loader below therefore accepts both
the 4.x `torch_dtype=` and the 5.x `dtype=` keyword and reports which one it
used; `transformers` is imported **lazily** inside the real-encoder constructor,
so importing this module (or building the mock arm) never imports it — which
also keeps it safe on a login node.

Usage
-----
    # end-to-end CPU proof, no GPU / no download (writes a probe-only cell)
    python scripts/train_backbone_966.py --backbone llm_encoder --dry-run \
        --horizon 24 --seed 42 --export-dir _dryrun/llm_encoder

    # a real arm (compute node, offline cache, publication partition)
    python scripts/train_backbone_966.py --backbone llm_encoder \
        --llm-model-id Qwen/Qwen2.5-1.5B --llm-revision <sha40> \
        --encoder-batch-size 8 --horizon 24 --seed 42
"""
from __future__ import annotations

import hashlib
import importlib.metadata as _md
import os
import platform
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn

# The canonical 7-channel order. `configs.VAR_COLS` is authoritative; the literal
# fallback only keeps this module importable in isolation (no sys.path juggling).
try:  # pragma: no cover - the runner and the tests both put `scripts/` on sys.path
    from configs import VAR_COLS as _CONFIG_VAR_COLS
except Exception:  # pragma: no cover
    _CONFIG_VAR_COLS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4",
                        "AGE 5-24", "ILITOTAL", "NUM. OF PROVIDERS", "OT"]

try:
    from innovation import fidelity as FID
    from innovation.interfaces import ForecastBackbone
except Exception as _exc:  # pragma: no cover - fails closed with a clear message
    raise ImportError(
        "llm_encoder_backbone.py needs `scripts/` on sys.path so that "
        "`innovation.interfaces` resolves (train_backbone_966.py inserts it; "
        "tests/test_llm_encoder_backbone.py does the same)"
    ) from _exc

#: The 7 numeric channels, in the order used by every benchmark cell.
VAR_COLS: Tuple[str, ...] = tuple(str(c) for c in _CONFIG_VAR_COLS)

#: Prompt template identity. Change it only with a matching cache-key version.
PROMPT_TEMPLATE_VERSION = "v1"

#: Decimal places used to render a z-space value into the prompt (4 dp).
PROMPT_DECIMALS = 4

#: The pinned checkpoint already verified in `innovation/assets.py`.
DEFAULT_MODEL_ID = "Qwen/Qwen2.5-1.5B"
DEFAULT_REVISION = "8faed761d45a263340a0528343f099c05c9a4323"

#: On-disk cache format tag (bump when the stored payload changes).
CACHE_FORMAT = "llm_encoder_cache_v1"

#: Set to True only inside `FrozenCausalLM.__init__`. Tests assert it stays
#: False on the mock path, i.e. that no unit test can ever import transformers.
TRANSFORMERS_IMPORTED = False


# ────────────────────────────────────────────────────────────────────────────
# Prompt construction (deterministic, human-readable, no timestamps)
# ────────────────────────────────────────────────────────────────────────────
def render_channel_prompt(values: Sequence[float]) -> str:
    """Render ONE channel's look-back window as a deterministic text prompt.

    Parameters
    ----------
    values : sequence of float
        The `T` (104) z-space values of a *single* channel, oldest first.

    Returns
    -------
    str
        A prompt with every value rounded to `PROMPT_DECIMALS` and
        comma-separated. Rendering is a pure function of the values: no clock,
        no locale, no channel identity.

    Notes
    -----
    Two deliberate omissions:

    * **no channel name / index.** The arm's contract is *channel independence*:
      permuting the 7 channels must permute the 7 output rows and nothing else
      (the same convention as `classic_nn._ChannelIndependent` and DLinear
      `individual=False`). Naming the channel would break that equivariance —
      channel *i* and channel *j* would be encoded by different strings — so the
      prompt is a function of the series values only ("same series -> same
      representation").
    * **no horizon `L`.** The frozen representation describes the context only;
      the horizon is carried by the per-`L` head. That also keeps the vector
      cache hot across the four horizon fits.
    """
    vals = [float(v) for v in values]
    rendered = ", ".join(f"{v:.{PROMPT_DECIMALS}f}" for v in vals)
    return (
        f"Standardized weekly series, oldest first, {len(vals)} values: "
        f"{rendered}. Forecast the next values of this series."
    )


def prompt_sha256(prompt: str) -> str:
    """SHA-256 of the exact prompt string (hex digest)."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def cache_key(model_id: str, revision: Optional[str], prompt: str) -> str:
    """Content address of one encoder vector: `model_id@revision|prompt_sha256`.

    Both components matter: the same text encoded by a different checkpoint (or
    a different revision of the same checkpoint) is a different vector and must
    never be served from another model's cache entry.
    """
    rev = revision if revision else "unpinned"
    return f"{model_id}@{rev}|{prompt_sha256(prompt)}"


# ────────────────────────────────────────────────────────────────────────────
# Hidden-state handling
# ────────────────────────────────────────────────────────────────────────────
def extract_last_hidden_state(output: Any) -> torch.Tensor:
    """Return the LAST-LAYER hidden states from any HF-style model output.

    Resolution order, chosen so that a tuple can never be mistaken for logits:

    1. an object with `.last_hidden_state` (e.g. `BaseModelOutputWithPooling`);
    2. an object with `.hidden_states` — its **last** element;
    3. a bare 3-D tensor;
    4. a `tuple`/`list` containing a nested tuple/list of 3-D tensors — the
       **last** element of that nested stack. This is HF's
       `(logits, hidden_states, ...)` shape with `return_dict=False`, where the
       nested tuple is the unambiguous layer stack and element 0 is *logits*;
    5. a flat `tuple`/`list` whose elements are all 3-D tensors — the **last**
       element (a per-layer stack);
    6. otherwise the first 3-D tensor in the tuple.

    Raises
    ------
    TypeError
        When no 3-D hidden-state tensor can be found. Failing loudly is
        deliberate: silently falling back to logits would mean the head was
        trained on vocabulary scores.
    """
    if output is None:
        raise TypeError("model returned None; expected hidden states")

    last = getattr(output, "last_hidden_state", None)
    if isinstance(last, torch.Tensor):
        return last

    hidden_states = getattr(output, "hidden_states", None)
    if isinstance(hidden_states, (tuple, list)) and hidden_states:
        if isinstance(hidden_states[-1], torch.Tensor):
            return hidden_states[-1]

    if isinstance(output, torch.Tensor):
        if output.dim() != 3:
            raise TypeError(f"model returned a {output.dim()}-D tensor, "
                            f"expected (B, T, D) hidden states")
        return output

    if isinstance(output, (tuple, list)):
        # 4. a nested per-layer stack wins — element 0 of the outer tuple may be
        #    logits (HF `return_dict=False` + `output_hidden_states=True`).
        for item in output:
            if isinstance(item, (tuple, list)) and item:
                if all(isinstance(t, torch.Tensor) and t.dim() == 3 for t in item):
                    return item[-1]
        tensors = [o for o in output if isinstance(o, torch.Tensor)]
        if tensors and len(tensors) == len(output) and all(t.dim() == 3 for t in tensors):
            return tensors[-1]                      # 5. flat stack of per-layer states
        for item in tensors:                        # 6. (last_hidden_state, ...)
            if item.dim() == 3:
                return item
    raise TypeError(f"could not locate hidden states in {type(output).__name__}")


def masked_mean_pool(hidden: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    """Mean-pool `(B, T, D)` over the non-padding positions of `(B, T)`.

    Padded positions are excluded by the mask (right padding is assumed, but the
    mask makes the pooling independent of the padding side).
    """
    mask = attention_mask.to(hidden.dtype).unsqueeze(-1)          # (B, T, 1)
    denom = mask.sum(dim=1).clamp(min=1.0)                        # (B, 1)
    return (hidden * mask).sum(dim=1) / denom                     # (B, D)


def _package_version(name: str) -> Optional[str]:
    """Installed version of `name` **without importing it** (login-node safe)."""
    try:
        return _md.version(name)
    except Exception:
        return None


# ────────────────────────────────────────────────────────────────────────────
# Cache of pooled encoder vectors (CPU float32, keyed by content address)
# ────────────────────────────────────────────────────────────────────────────
class EncoderVectorCache:
    """Content-addressed store of frozen encoder vectors.

    One entry per `(model_id, revision, prompt_sha256)`; values are **CPU
    float32** tensors so that (a) the GPU never holds more than one chunk of
    activations and (b) a second forward with the same prompts is a dict lookup,
    not a model call. `hits` / `misses` are exposed for the cache unit test and
    for the run manifest.
    """

    def __init__(self) -> None:
        self._store: Dict[str, torch.Tensor] = {}
        self.hits = 0
        self.misses = 0

    def key(self, model_id: str, revision: Optional[str], prompt: str) -> str:
        """Content address for `prompt` under `model_id@revision`."""
        return cache_key(model_id, revision, prompt)

    def get(self, key: str) -> Optional[torch.Tensor]:
        """Cached vector for `key`, or `None` (counting a hit / miss)."""
        vec = self._store.get(key)
        if vec is None:
            self.misses += 1
            return None
        self.hits += 1
        return vec

    def peek(self, key: str) -> Optional[torch.Tensor]:
        """Cached vector for `key`, or `None` — **without** touching the counters.

        Used when assembling a batch that was just looked up: counting those
        reads again would double every hit in the manifest.
        """
        return self._store.get(key)

    def put(self, key: str, vector: torch.Tensor) -> None:
        """Store `vector` (moved to CPU float32) under `key`."""
        self._store[key] = vector.detach().to("cpu", torch.float32)

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def stats(self) -> Dict[str, int]:
        """`{'entries', 'hits', 'misses'}` for the manifest."""
        return {"entries": len(self._store), "hits": int(self.hits),
                "misses": int(self.misses)}

    def save(self, path: str, *, model_id: str, revision: Optional[str],
             hidden_dim: int) -> str:
        """Persist the cache (so a later run need not re-run the encoder)."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        torch.save({"format": CACHE_FORMAT, "model_id": str(model_id),
                    "revision": None if revision is None else str(revision),
                    "hidden_dim": int(hidden_dim),
                    "vectors": {k: v.clone() for k, v in self._store.items()}},
                   path)
        return path

    def load(self, path: str, *, model_id: str, revision: Optional[str],
             hidden_dim: int) -> int:
        """Load a cache written by `save`; refuse a cache from another model.

        Returns the number of entries loaded. Raises `ValueError` when the file
        belongs to a different `(model_id, revision, hidden_dim)` — serving
        another model's vectors would silently corrupt the arm.
        """
        payload = torch.load(path, map_location="cpu", weights_only=True)
        if not isinstance(payload, dict) or payload.get("format") != CACHE_FORMAT:
            raise ValueError(f"{path} is not an llm_encoder cache ({CACHE_FORMAT})")
        if (str(payload.get("model_id")) != str(model_id)
                or (payload.get("revision") or None) != (revision or None)
                or int(payload.get("hidden_dim", -1)) != int(hidden_dim)):
            raise ValueError(
                f"{path} belongs to {payload.get('model_id')}@"
                f"{payload.get('revision')} (D={payload.get('hidden_dim')}), not "
                f"{model_id}@{revision} (D={hidden_dim})")
        vectors = payload.get("vectors") or {}
        for k, v in vectors.items():
            self._store[str(k)] = v.detach().to("cpu", torch.float32)
        return len(self._store)


# ────────────────────────────────────────────────────────────────────────────
# Mock tokenizer / mock encoder — CPU only, no download, no transformers
# ────────────────────────────────────────────────────────────────────────────
class MockTokenizer:
    """Deterministic, dependency-free stand-in for a HuggingFace tokenizer.

    It extracts the rendered numeric tokens from a prompt with a regex and maps
    each to a vocabulary id by hashing it, so **different prompts get different
    id sequences** and channel independence is testable rather than vacuous.
    The API matches the small slice of the HF tokenizer contract this adapter
    uses: `__call__(prompts, return_tensors="pt", padding=True,
    truncation=True)` -> `{"input_ids", "attention_mask"}`, plus
    `pad_token_id` / `eos_token_id`.
    """

    _NUMBER = re.compile(r"-?\d+\.\d+")

    def __init__(self, vocab_size: int = 4096, max_tokens: int = 128,
                 pad_token_id: int = 0, bos_token_id: int = 1) -> None:
        self.vocab_size = int(vocab_size)
        self.max_tokens = int(max_tokens)
        self.pad_token_id = int(pad_token_id)
        self.bos_token_id = int(bos_token_id)
        self.eos_token_id = int(bos_token_id)
        self.pad_token = "<pad>"
        self.eos_token = "<eos>"

    def _ids(self, prompt: str) -> List[int]:
        numbers = self._NUMBER.findall(prompt)
        ids = [self.bos_token_id]
        for num in numbers[: self.max_tokens - 2]:
            digest = hashlib.sha256(num.encode("utf-8")).hexdigest()
            ids.append(2 + int(digest[:8], 16) % max(1, self.vocab_size - 2))
        return ids

    def __call__(self, prompts: Sequence[str], return_tensors: str = "pt",
                 padding: bool = True, truncation: bool = True,
                 max_length: Optional[int] = None) -> Dict[str, torch.Tensor]:
        """Tokenise `prompts` into padded `input_ids` / `attention_mask`."""
        if return_tensors != "pt":
            raise ValueError("MockTokenizer only supports return_tensors='pt'")
        limit = int(max_length or self.max_tokens)
        rows = [self._ids(p)[:limit] for p in prompts]
        width = max((len(r) for r in rows), default=1)
        input_ids = torch.zeros((len(rows), width), dtype=torch.long)
        attention_mask = torch.zeros((len(rows), width), dtype=torch.long)
        for i, row in enumerate(rows):
            if not row:
                row = [self.pad_token_id]
            input_ids[i, : len(row)] = torch.tensor(row, dtype=torch.long)
            attention_mask[i, : len(row)] = 1
        return {"input_ids": input_ids, "attention_mask": attention_mask}


class MockLLMEncoder(nn.Module):
    """Tiny frozen stand-in for a causal LLM: no download, no tokenizer, no GPU.

    Two modes:

    * ``mode="fixed"`` — **ignores its input** and returns a constant
      `(B, T, D)` tensor (the contract the shape test is written against);
    * ``mode="embedding"`` — a frozen token-embedding lookup, so different
      prompts (different channels) get different vectors. This is what the
      channel-independence test and the CPU dry-run use, because with a truly
      input-independent encoder a channel-permutation test would pass vacuously.

    It carries real frozen `nn.Parameter`s (`embedding`, `norm.*`, `constant`)
    so the frozen-encoder test is non-vacuous: those tensors must be
    bit-identical after an optimizer step that moves the head.
    """

    def __init__(self, hidden_dim: int = 64, vocab_size: int = 4096,
                 max_tokens: int = 128, mode: str = "embedding",
                 seed: int = 1234) -> None:
        super().__init__()
        if mode not in ("fixed", "embedding"):
            raise ValueError(f"mock mode must be 'fixed' or 'embedding', got {mode!r}")
        self.hidden_dim = int(hidden_dim)
        self.vocab_size = int(vocab_size)
        self.max_tokens = int(max_tokens)
        self.mode = str(mode)
        # Frozen weights drawn from an EXPLICIT generator: the mock never depends
        # on, nor perturbs, the global RNG that seeds the head.
        gen = torch.Generator().manual_seed(int(seed))
        emb = torch.randn(self.vocab_size, self.hidden_dim, generator=gen)
        emb = emb / float(np.sqrt(self.hidden_dim))
        self.embedding = nn.Parameter(emb, requires_grad=False)
        self.constant = nn.Parameter(torch.randn(self.hidden_dim, generator=gen) * 0.02,
                                     requires_grad=False)
        self.norm = nn.LayerNorm(self.hidden_dim)
        self.tokenizer = MockTokenizer(vocab_size=self.vocab_size,
                                       max_tokens=self.max_tokens)
        for param in self.parameters():
            param.requires_grad = False
        self.eval()
        #: Number of forward calls — the cache test asserts this does not grow.
        self.calls = 0

    def forward(self, input_ids: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Return `(B, T, D)` hidden states; `mode="fixed"` ignores `input_ids`."""
        self.calls += 1
        batch, steps = int(input_ids.shape[0]), int(input_ids.shape[1])
        if attention_mask is None:
            attention_mask = torch.ones((batch, steps), dtype=torch.long)
        if self.mode == "fixed":
            base = self.constant.view(1, 1, -1).expand(batch, steps, self.hidden_dim)
        else:
            ids = input_ids.clamp(min=0) % self.vocab_size
            base = self.embedding[ids]                              # (B, T, D)
        hidden = self.norm(base)
        return hidden * attention_mask.unsqueeze(-1).to(hidden.dtype)


class FrozenCausalLM(nn.Module):
    """A real causal/instruct LLM loaded frozen, in `eval()` mode, no dropout.

    `transformers` is imported inside this constructor — never at module import
    — so unit tests and the CPU dry-run are provably independent of it, and no
    login node ever pays the import. Both the transformers-4 `torch_dtype=` and
    the transformers-5 `dtype=` keyword are attempted, and whatever worked is
    recorded in `self.loader_kwargs_used` for the manifest.
    """

    def __init__(self, model_id: str, revision: Optional[str] = None,
                 device: str = "cpu", dtype: Optional[Any] = None,
                 local_files_only: bool = True, trust_remote_code: bool = False,
                 max_length: int = 512,
                 tokenizer_kwargs: Optional[Dict[str, Any]] = None,
                 model_kwargs: Optional[Dict[str, Any]] = None) -> None:
        super().__init__()
        global TRANSFORMERS_IMPORTED
        import transformers                                        # lazy, by design
        from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer
        TRANSFORMERS_IMPORTED = True

        self.model_id = str(model_id)
        self.revision = revision
        self.max_length = int(max_length)
        common: Dict[str, Any] = {
            "revision": revision,
            "local_files_only": bool(local_files_only),
            "trust_remote_code": bool(trust_remote_code),
        }
        tok_kwargs = dict(common)
        tok_kwargs.update(tokenizer_kwargs or {})
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, **tok_kwargs)
        if getattr(self.tokenizer, "pad_token_id", None) is None:
            if getattr(self.tokenizer, "eos_token_id", None) is None:
                raise RuntimeError(
                    f"{model_id}: tokenizer has neither pad nor eos token; refusing "
                    "to invent a token id (that would resize the embeddings)")
            self.tokenizer.pad_token = self.tokenizer.eos_token

        base = dict(common)
        base["low_cpu_mem_usage"] = True
        base.update(model_kwargs or {})
        want_dtype = dtype if dtype is not None else torch.bfloat16
        self.model = None
        self.loader_error: Optional[str] = None
        for factory in (AutoModelForCausalLM, AutoModel):
            for key in ("torch_dtype", "dtype"):
                try:
                    self.model = factory.from_pretrained(model_id, **base,
                                                         **{key: want_dtype})
                    self.loader_kwargs_used = {"factory": factory.__name__,
                                               "dtype_keyword": key,
                                               "dtype": str(want_dtype)}
                    break
                except (TypeError, ValueError) as exc:
                    self.loader_error = f"{factory.__name__}/{key}: {exc}"
            if self.model is not None:
                break
        if self.model is None:
            raise RuntimeError(
                f"could not load {self.model_id}@{self.revision} with any of "
                f"AutoModelForCausalLM / AutoModel (last error: {self.loader_error})")

        self.model.to(device)
        self.model.eval()
        for param in self.model.parameters():
            param.requires_grad = False
        self.hidden_dim = int(getattr(self.model.config, "hidden_size", 0))
        if self.hidden_dim <= 0:
            raise RuntimeError(f"{self.model_id}: config.hidden_size is unusable")
        self.transformer_version = _package_version("transformers")

    def forward(self, input_ids: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """One deterministic forward pass; returns `(B, T, D)` hidden states."""
        out = self.model(input_ids=input_ids, attention_mask=attention_mask,
                         output_hidden_states=True, use_cache=False,
                         return_dict=True)
        return extract_last_hidden_state(out)

    def parameter_count(self) -> int:
        """Total (frozen) parameters of the loaded checkpoint."""
        return int(sum(p.numel() for p in self.model.parameters()))


# ────────────────────────────────────────────────────────────────────────────
# The arm
# ────────────────────────────────────────────────────────────────────────────
class FrozenLLMEncoder(ForecastBackbone):
    """Frozen-LLM encoder + ONE shared `nn.Linear(D, L)` head (channel-independent).

    The forward pass mirrors `innovation/backbones/classic_nn.py::
    _ChannelIndependent`: `(B, N, T)` is flattened to `(B*N, T)`, every row is
    encoded independently, the same head maps `D -> L` for every variable, and
    the result is reshaped to `(B, N, L)`. Only `head` has `requires_grad=True`.

    Parameters
    ----------
    T, N, L : int
        Look-back (104), channels (7) and horizon — the same `(T, N, L)` the
        other arms receive from `train_backbone_966.build_model`.
    model_id, revision : str
        The checkpoint and its **pinned** revision sha (recorded in provenance;
        an unpinned revision is refused unless `allow_unpinned_revision=True`).
    encoder_batch_size : int
        Number of prompts per encoder forward. The knob that makes a 55 GB
        model usable: the encoder pass is chunked, never the whole dataset.
    device : str
        Torch device for the encoder (and, after `build_model(...).to(device)`,
        for the head as well).
    seed : int
        Seeds `torch.manual_seed` before the head is built, so the trainable
        part is reproducible. The encoder is frozen, so it has no seed.
    mock_encoder : bool
        Use `MockLLMEncoder` instead of a real checkpoint — CPU, no download.
    cache_path : str, optional
        If given and present, the cache is loaded at construction; call
        `save_cache()` to persist new entries.
    """

    name = "llm_encoder"

    def __init__(self, T: int = 104, N: int = 7, L: int = 24,
                 model_id: str = DEFAULT_MODEL_ID,
                 revision: Optional[str] = DEFAULT_REVISION,
                 encoder_batch_size: int = 8, device: str = "cpu",
                 dtype: Optional[Any] = None, seed: int = 42,
                 mock_encoder: bool = False, mock_hidden_dim: int = 64,
                 mock_vocab_size: int = 4096, mock_max_tokens: int = 128,
                 mock_mode: str = "embedding", mock_seed: int = 1234,
                 local_files_only: bool = True, trust_remote_code: bool = False,
                 allow_unpinned_revision: bool = False,
                 max_length: int = 512, cache_path: Optional[str] = None,
                 tokenizer_kwargs: Optional[Dict[str, Any]] = None,
                 model_kwargs: Optional[Dict[str, Any]] = None) -> None:
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        if self.T <= 0 or self.N <= 0 or self.L <= 0:
            raise ValueError(f"T, N, L must be positive, got {(T, N, L)}")
        self.encoder_batch_size = int(encoder_batch_size)
        if self.encoder_batch_size < 1:
            raise ValueError("encoder_batch_size must be >= 1 "
                             f"(got {encoder_batch_size})")
        if len(VAR_COLS) < self.N:
            raise ValueError(f"VAR_COLS has {len(VAR_COLS)} names for N={self.N}")
        self.model_id = str(model_id)
        rev = None if revision in (None, "", "none", "None") else str(revision)
        if rev is None and not mock_encoder and not allow_unpinned_revision:
            raise ValueError(
                "a pinned revision sha is required for a real encoder run "
                "(pass allow_unpinned_revision=True only for a probe)")
        self.revision = rev
        self.mock_encoder = bool(mock_encoder)
        self.seed = int(seed)
        self.device = torch.device(device)
        torch.manual_seed(self.seed)               # requirement: fix the seed first

        if self.mock_encoder:
            self.encoder: nn.Module = MockLLMEncoder(
                hidden_dim=mock_hidden_dim, vocab_size=mock_vocab_size,
                max_tokens=mock_max_tokens, mode=mock_mode, seed=mock_seed)
            self.hidden_dim = int(mock_hidden_dim)
        else:
            self.encoder = FrozenCausalLM(
                model_id=self.model_id, revision=self.revision, device=str(self.device),
                dtype=dtype, local_files_only=local_files_only,
                trust_remote_code=trust_remote_code, max_length=max_length,
                tokenizer_kwargs=tokenizer_kwargs, model_kwargs=model_kwargs)
            self.hidden_dim = int(self.encoder.hidden_dim)
        self._tokenizer = self.encoder.tokenizer
        self.max_length = int(max_length)

        # The head is built AFTER the encoder; re-seed so its init can never
        # depend on how much RNG the encoder constructor happened to consume.
        torch.manual_seed(self.seed)
        self.head = nn.Linear(self.hidden_dim, self.L)
        self.cache = EncoderVectorCache()
        self._cache_path = cache_path
        if cache_path and os.path.exists(cache_path):
            self.cache.load(cache_path, model_id=self.model_id,
                            revision=self.revision, hidden_dim=self.hidden_dim)

    # ── frozen-encoder invariants ───────────────────────────────────────────
    def train(self, mode: bool = True) -> "FrozenLLMEncoder":
        """Keep the FROZEN encoder in `eval()` even while the arm "trains".

        `train_backbone_966.train_one` calls `model.train()` every epoch; for a
        frozen backbone that must not re-enable dropout (it would both change
        the representation and break the determinism guarantee). Only the head
        follows the requested mode.
        """
        super().train(mode)
        self.encoder.eval()
        return self

    def _current_encoder_device(self) -> torch.device:
        """Device the encoder currently lives on (may be CPU after release)."""
        params = list(self.encoder.parameters())
        return params[0].device if params else self.device

    def _head_device(self) -> torch.device:
        """Device the trainable head lives on."""
        return self.head.weight.device

    def encoder_parameter_count(self) -> int:
        """Total parameters held by the frozen encoder (not just trainable)."""
        return int(sum(p.numel() for p in self.encoder.parameters()))

    def encoder_trainable_parameters(self) -> int:
        """Trainable parameters inside the encoder — must always be 0."""
        return int(sum(p.numel() for p in self.encoder.parameters() if p.requires_grad))

    def head_parameters(self) -> int:
        """Parameters of the single shared head (`D * L + L`)."""
        return int(sum(p.numel() for p in self.head.parameters()))

    def trainable_parameters(self) -> int:
        """Trainable parameters of the whole arm (the head only)."""
        return int(sum(p.numel() for p in self.parameters() if p.requires_grad))

    def total_parameters(self) -> int:
        """Encoder + head parameters."""
        return int(sum(p.numel() for p in self.parameters()))

    # ── tokenisation / pooling ──────────────────────────────────────────────
    def _tokenize(self, prompts: Sequence[str]) -> Dict[str, torch.Tensor]:
        """Tokenise prompts with the encoder's own tokenizer (mock or real)."""
        return self._tokenizer(list(prompts), return_tensors="pt", padding=True,
                               truncation=True, max_length=self.max_length)

    @staticmethod
    def _flatten(x: torch.Tensor, N: int) -> torch.Tensor:
        """`(B, N, T)` -> `(B*N, T)` (window-major, so row `i` is channel `i % N`)."""
        return x.detach().reshape(x.shape[0] * N, x.shape[-1])

    def encode_prompts(self, prompts: Sequence[str]) -> torch.Tensor:
        """Encode prompts to pooled vectors `(len(prompts), D)` on the head device.

        Cache-first: only the prompts whose `(model_id, revision, prompt_sha256)`
        key is absent are actually run through the encoder, and they are run in
        `encoder_batch_size` chunks under `torch.no_grad()`. Pooled vectors are
        stored on CPU, so the encoder may be parked off the GPU afterwards.
        """
        if not prompts:
            return torch.zeros((0, self.hidden_dim), dtype=torch.float32,
                               device=self._head_device())
        keys = [self.cache.key(self.model_id, self.revision, p) for p in prompts]
        missing: List[int] = [i for i, k in enumerate(keys) if self.cache.get(k) is None]
        if missing:
            dev = self._current_encoder_device()
            for start in range(0, len(missing), self.encoder_batch_size):
                chunk = missing[start: start + self.encoder_batch_size]
                batch = [prompts[i] for i in chunk]
                with torch.no_grad():                     # no graph over the encoder
                    encoded = self._tokenize(batch)
                    encoded = {k: v.to(dev) for k, v in encoded.items()}
                    hidden = self.encoder(input_ids=encoded["input_ids"],
                                          attention_mask=encoded.get("attention_mask"))
                    hidden = extract_last_hidden_state(hidden)
                    pooled = masked_mean_pool(hidden, encoded["attention_mask"])
                pooled = pooled.detach().to("cpu", torch.float32)
                for offset, index in enumerate(chunk):
                    self.cache.put(keys[index], pooled[offset].clone())
        vectors = []
        for key in keys:
            vec = self.cache.peek(key)
            if vec is None:                              # pragma: no cover - defensive
                raise RuntimeError(f"cache miss after encode for key {key}")
            vectors.append(vec)
        return torch.stack(vectors).to(self._head_device())

    # ── memory discipline ───────────────────────────────────────────────────
    def release_encoder_to_cpu(self) -> None:
        """Park the frozen encoder on the host after its outputs are cached.

        With the vectors cached, training only needs the head, so a 55 GB
        encoder no longer has to share the GPU with the (tiny) head graph.
        """
        self.encoder.to("cpu")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def prefill_cache(self, x: torch.Tensor) -> int:
        """Encode every channel of `x` once and return the number of new entries.

        Intended as a one-off pass over the windows that will be trained on:
        afterwards the encoder can be released and the cache served from RAM.
        """
        before = len(self.cache)
        flat = self._flatten(x, self.N).cpu().numpy()
        prompts = [render_channel_prompt(flat[i]) for i in range(flat.shape[0])]
        self.encode_prompts(prompts)
        return len(self.cache) - before

    def save_cache(self, path: Optional[str] = None) -> Optional[str]:
        """Persist the cache to `path` (or the path given at construction)."""
        target = path or self._cache_path
        if not target:
            return None
        return self.cache.save(target, model_id=self.model_id,
                               revision=self.revision, hidden_dim=self.hidden_dim)

    def load_cache(self, path: str) -> int:
        """Load a cache written by a previous run of the same model/revision."""
        return self.cache.load(path, model_id=self.model_id,
                               revision=self.revision, hidden_dim=self.hidden_dim)

    # ── forward: the benchmark contract ─────────────────────────────────────
    def forward(self, x: torch.Tensor, ctx: torch.Tensor | None = None) -> torch.Tensor:
        """`x` `(B, N, T)` z-space -> `y_hat` `(B, N, L)` z-space.

        Channel-independent by construction: each of the `B*N` rows is encoded
        on its own and mapped by the SAME `nn.Linear(D, L)`, so permuting the 7
        channels permutes the output rows identically. `ctx` is ignored (this
        arm has no text-context injection — the encoder *is* the text path).
        """
        if x.dim() != 3:
            raise ValueError(f"x must be (B, N, T), got shape {tuple(x.shape)}")
        B, N, T = int(x.shape[0]), int(x.shape[1]), int(x.shape[2])
        if N != self.N:
            raise ValueError(f"expected N={self.N} variables, got {N} "
                             "(check --profile / VAR_COLS)")
        if T != self.T:
            raise ValueError(f"expected T={self.T} look-back steps, got {T}")
        flat = self._flatten(x, N).cpu().numpy()
        prompts = [render_channel_prompt(flat[i]) for i in range(flat.shape[0])]
        z = self.encode_prompts(prompts)                   # (B*N, D)
        return self.head(z).reshape(B, N, self.L)          # (B, N, L)

    # ── provenance / reports ────────────────────────────────────────────────
    def provenance(self) -> Dict[str, Any]:
        """Everything the run manifest must record about the frozen encoder.

        Model id, pinned revision, torch/transformers/python versions, the
        encoder's parameter count, the pooling rule, the device actually used,
        the encoder batch size and the cache statistics (AGENTS.md rule 12).
        """
        enc_params = self.encoder_parameter_count()
        enc_trainable = self.encoder_trainable_parameters()
        transformers_version = (
            getattr(self.encoder, "transformer_version", None)
            if not self.mock_encoder else None)
        return {
            "arm": self.name,
            "model_id": self.model_id,
            "revision": self.revision,
            "revision_pinned": self.revision is not None,
            "mock_encoder": bool(self.mock_encoder),
            "encoder": {
                "class": type(self.encoder).__name__,
                "parameters": enc_params,
                "trainable_parameters": enc_trainable,
                "frozen": enc_trainable == 0,
                "eval_mode": not self.encoder.training,
                "hidden_dim": self.hidden_dim,
                "pooling": "masked_mean_last_hidden_state",
                "loader": getattr(self.encoder, "loader_kwargs_used", None),
            },
            "head": {
                "class": "nn.Linear",
                "in_features": self.hidden_dim,
                "out_features": self.L,
                "parameters": self.head_parameters(),
                "shared_across_variables": True,
            },
            "encoder_batch_size": self.encoder_batch_size,
            "prompt_template_version": PROMPT_TEMPLATE_VERSION,
            "prompt_decimals": PROMPT_DECIMALS,
            "device": str(self._current_encoder_device()),
            "torch_version": torch.__version__,
            "transformers_version": transformers_version if transformers_version
            else _package_version("transformers"),
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "determinism": {
                "manual_seed": self.seed,
                "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
                "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
                "sampling": "disabled (single forward, use_cache=False)",
            },
            "cache": self.cache.stats(),
        }

    def architecture_report(self) -> Dict[str, Any]:
        """Architecture/fidelity report (protocol hook used by every backbone)."""
        return {
            "name": self.name,
            "display_name": f"Frozen {self.model_id} encoder + shared linear head",
            "published": ("cross-scale frozen-encoder probe (methodology item 3: "
                          "shared head + frozen base); not a reproduction of a "
                          "published forecasting architecture"),
            "fidelity": FID.INSPIRED_SIMPLIFICATION,
            "components": ["per-channel text prompt", "frozen causal/instruct LLM",
                           "mean-pooled last hidden state", "shared Linear(D, L) head"],
            "channel_independent": True,
            "encoder_loaded": not self.mock_encoder,
            "evidence": [
                "scripts/llm_encoder_backbone.py FrozenLLMEncoder.forward: "
                "(B,N,T) -> (B*N,T) so one head maps every variable identically",
                "scripts/llm_encoder_backbone.py FrozenLLMEncoder.encode_prompts: "
                "encoder runs under torch.no_grad() in encoder_batch_size chunks",
                "scripts/llm_encoder_backbone.py render_channel_prompt: values "
                "rounded to 4 dp, comma-separated, no clock/locale dependence",
            ],
            "deviations": [
                "not a published architecture: only the shared head is trained",
                "representation = mean of the last hidden layer over the prompt "
                "(no patching, reprogramming, retrieval or alignment branch)",
                "horizon is not in the prompt; it is carried by the per-L head",
                "the prompt carries no channel identity by design, so permuting "
                "the 7 channels permutes the 7 output rows (channel independence)",
                "prompt renders z-space numbers, so the encoder sees standardized "
                "values rather than raw patients",
            ],
            "notes": ("Legitimate only as a frozen-encoder probe under the shared "
                      "head + frozen base methodology; never compare its capacity "
                      "with the trained arms' as if it were a tuned model."),
        }


# ────────────────────────────────────────────────────────────────────────────
# Cell writer — the same key set as train_backbone_966.py
# ────────────────────────────────────────────────────────────────────────────
#: Keys every benchmark cell carries (AGENTS.md rule 11(b); STATE §1.2).
PRED_CELL_KEYS: Tuple[str, ...] = ("pred", "target", "target_start_row", "L", "seed",
                                   "var_cols", "model", "profile", "containment",
                                   "space")


def save_pred_cell(path: str, pred: np.ndarray, target: np.ndarray,
                   target_start_row: np.ndarray, *, L: int, seed: int, model: str,
                   profile: str, containment: str,
                   space: str = "standardized_train_fit_z",
                   var_cols: Sequence[str] = VAR_COLS) -> str:
    """Write a benchmark cell `pred_*.npz` and assert its layout first.

    Mirrors `train_backbone_966.py`'s `np.savez_compressed(...)` block exactly,
    and calls `eval_windows.check_cell_layout` **before** writing, so a
    transposed `(7, W, L)` array can never reach the disk through this path.

    Returns
    -------
    str
        The path written.
    """
    from eval_windows import check_cell_layout           # lazy: shared definition

    pred = np.asarray(pred, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    ts = np.asarray(target_start_row).ravel().astype(np.int32)
    check_cell_layout(pred, target, ts, L=L, label=f"{model}_L{L}_s{seed}")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    np.savez_compressed(
        path,
        pred=pred,
        target=target,
        target_start_row=ts,
        L=np.int32(L),
        seed=np.int32(seed),
        var_cols=np.array(list(var_cols)),
        model=np.array(str(model)),
        profile=np.array(str(profile)),
        containment=np.array(str(containment)),
        space=np.array(str(space)),
    )
    return path


__all__ = [
    "DEFAULT_MODEL_ID",
    "DEFAULT_REVISION",
    "EncoderVectorCache",
    "FrozenCausalLM",
    "FrozenLLMEncoder",
    "MockLLMEncoder",
    "MockTokenizer",
    "PRED_CELL_KEYS",
    "PROMPT_TEMPLATE_VERSION",
    "TRANSFORMERS_IMPORTED",
    "extract_last_hidden_state",
    "masked_mean_pool",
    "prompt_sha256",
    "render_channel_prompt",
    "save_pred_cell",
]
