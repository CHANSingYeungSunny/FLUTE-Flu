"""
gpt2_encoder.py — the existing frozen GPT-2 textual embedder, as a TextEncoder.
==============================================================================

Re-uses `scripts/textual_embedder.TextualInputEmbedder` (frozen GPT-2-small,
last hidden state, D=768). The prompt statistics come from `train_df` ONLY.

Availability requires the local gpt2 cache; nothing is downloaded.
"""

from __future__ import annotations

from innovation.backbones.gpt2_miflu_adapter import gpt2_cache_available
from innovation.interfaces import TextEncoder
from textual_embedder import DEFAULT_MIFLU_PROMPT_COMPONENTS


class GPT2TextEncoder(TextEncoder):
    name = "gpt2"

    def __init__(self, device: str = "cpu",
                 prompt_components=DEFAULT_MIFLU_PROMPT_COMPONENTS,
                 text_mode: str = "normal"):
        self.device = device
        self.prompt_components = tuple(prompt_components)
        # gpt2_miflu fixed-parent negative controls.
        #   zero    -> htext replaced by exact zeros, shape/dtype/device kept
        #   shuffle -> MIFlu prompt TOKEN order permuted (seed 20260917), the
        #              real prompt path is still used; special tokens and padding
        #              are never permuted; no target/label/Test information used.
        self.text_mode = str(text_mode)
        self.embedder = None
        self._htext: dict[int, "object"] = {}
        if not gpt2_cache_available():
            self.availability_note = (
                "UNAVAILABLE_LOCAL_DEPENDENCY: local gpt2 cache not found")

    def is_available(self) -> bool:
        try:
            import transformers  # noqa: F401
        except Exception:
            return False
        return gpt2_cache_available()

    def fit_on_train_only(self, train_df, horizon: int, seed: int) -> None:
        if not self.is_available():
            raise RuntimeError("UNAVAILABLE_LOCAL_DEPENDENCY: gpt2 unavailable")
        import torch

        from textual_embedder import (TextualInputEmbedder, build_prompt,
                                      DEFAULT_MIFLU_PROMPT_COMPONENTS)

        if self.embedder is None:
            self.embedder = TextualInputEmbedder(device=self.device)
        prompt = build_prompt(train_df, T=104, L=horizon,
                              components=self.prompt_components)
        if self.text_mode == "shuffle":
            prompt = self._shuffled_prompt(prompt)
        with torch.no_grad():
            htext = self.embedder(prompt).detach().cpu()
        if self.text_mode == "zero":
            # exact zeros: shape, dtype, device and capacity unchanged
            htext = torch.zeros_like(htext)
        self._htext[int(horizon)] = htext

    def _shuffled_prompt(self, prompt: str) -> str:
        """Token-level shuffle of the REAL MIFlu prompt (seed 20260917).

        BOS / EOS and any padding are held in place; only content tokens are
        permuted, within the single prompt (no cross-sample mixing). No target,
        validation label, Test or holdout information is used.
        """
        import torch as _t
        ids = self.embedder.tokenizer(prompt)["input_ids"]
        n = len(ids)
        if n <= 3:
            return prompt
        inner = ids[1:-1]                       # exclude BOS and EOS
        g = _t.Generator().manual_seed(20260917)
        perm = _t.randperm(len(inner), generator=g).tolist()
        shuffled = [ids[0]] + [inner[i] for i in perm] + [ids[-1]]
        return self.embedder.tokenizer.decode(shuffled)

    def encode(self, batch_size: int, device: str = "cpu",
               horizon: int | None = None):
        if self.embedder is None:
            return None
        h = int(horizon) if horizon is not None else next(iter(self._htext))
        t = self._htext[h].to(device)
        if t.shape[0] == 1 and batch_size > 1:
            t = t.expand(batch_size, -1, -1)
        return t

    def context_dim(self):
        return 768
