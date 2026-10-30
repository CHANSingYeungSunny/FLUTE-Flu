"""Independent paper-derived LLM forecasting contracts for v3 Phase 1.

The three classes intentionally do not share an architecture wrapper:
QwenTimeLLM uses patch prototype reprogramming and Prompt-as-Prefix; CALF uses
parallel temporal/text branches with two alignment losses; TimeCMA uses a
parallel branch plus retrieval alignment and a last-token representation.
Real Transformers loading is opt-in through ``load_backbone=True`` and must be
performed on a Slurm compute node by the Phase 1 runner.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from innovation import assets as AS
from innovation import fidelity as FID
from innovation.interfaces import ForecastBackbone


class _FrozenTextModel(nn.Module):
    def __init__(self, model_id: str, load_backbone: bool, hidden_dim: int):
        super().__init__()
        self.model_id = model_id
        self.hidden_dim = int(hidden_dim)
        self.loaded = False
        self.model = None
        self.tokenizer = None
        self.pretrained_source = None
        self.loader_kwargs = {}
        # D5: resolve through the authoritative asset descriptor so the verified
        # local snapshot directory is used with local_files_only=True instead of
        # a repository-id cache lookup (which fails when the snapshot has no ref).
        self.asset = AS.asset_descriptor(model_id)
        if load_backbone:
            from transformers import AutoModel, AutoTokenizer
            source, kwargs = AS.resolve_pretrained_source(model_id)
            self.pretrained_source = str(source)
            self.loader_kwargs = dict(kwargs)
            self.tokenizer = AutoTokenizer.from_pretrained(source, **kwargs)
            self.model = AutoModel.from_pretrained(source, **kwargs)
            self.hidden_dim = int(self.model.config.hidden_size)
            self.loaded = True
            for parameter in self.model.parameters():
                parameter.requires_grad = False
            # ── D6: GPT-2 padding compatibility ──────────────────────────────
            # GPT-2's tokenizer has no pad token, while Qwen's does. Requesting
            # padding without one raises ValueError. The safe repair reuses the
            # EXISTING eos token as the pad token: no new vocabulary entry is
            # added and no embedding matrix is resized, so pretrained weights and
            # the token-id space are untouched. Padded positions are then
            # excluded by the attention mask wherever a pooled/last-token
            # representation is taken.
            self.pad_token_reused_eos = False
            self.tokenizer_vocab_size = None
            self.model_embedding_rows = None
            self._ensure_pad_token()
            self.tokenizer_vocab_size = int(len(self.tokenizer))
            self.model_embedding_rows = int(
                self.model.get_input_embeddings().weight.shape[0])

    # ── D6 helpers ──────────────────────────────────────────────────────────
    def _ensure_pad_token(self) -> None:
        """Reuse the existing EOS token as the pad token when none is defined.

        Never adds a vocabulary entry and never resizes embeddings. Fails closed
        when the tokenizer provides neither a pad nor an eos token.
        """
        tok = self.tokenizer
        if getattr(tok, "pad_token_id", None) is None:
            if getattr(tok, "eos_token_id", None) is None:
                raise RuntimeError(
                    f"tokenizer for {self.model_id!r} has neither pad_token_id nor "
                    "eos_token_id; cannot pad safely (refusing to invent a token id)")
            # reuse the EXISTING eos token string/id — no vocabulary growth
            tok.pad_token = tok.eos_token
            self.pad_token_reused_eos = True
        else:
            self.pad_token_reused_eos = False

    @staticmethod
    def last_non_pad(hidden, attention_mask):
        """Hidden state of the LAST NON-PADDING token for each sample.

        Right-padding is assumed (the frozen rule). Never selects a padded slot.
        """
        lengths = (attention_mask.sum(dim=1) - 1).clamp(min=0)
        idx = lengths.view(-1, 1, 1).expand(-1, 1, hidden.size(-1))
        return hidden.gather(1, idx).squeeze(1)

    def pad_report(self) -> dict:
        return {"model_id": self.model_id,
                "pad_token_reused_eos": bool(self.pad_token_reused_eos),
                "pad_token_id": (None if self.tokenizer is None
                                 else self.tokenizer.pad_token_id),
                "eos_token_id": (None if self.tokenizer is None
                                 else self.tokenizer.eos_token_id),
                "vocab_size": self.tokenizer_vocab_size,
                "embedding_rows": self.model_embedding_rows,
                "vocab_grown": False,
                "embedding_resized": False}

    def encode_prompt(self, prompts: list[str], device: torch.device) -> torch.Tensor:
        if not self.loaded:
            raise RuntimeError("text backbone is not loaded; compute-node load required")
        batch = self.tokenizer(prompts, return_tensors="pt", padding=True,
                               truncation=True)
        batch = {key: value.to(device) for key, value in batch.items()}
        attention_mask = batch["attention_mask"]
        # The attention mask is returned alongside the hidden states so every
        # consumer can exclude padded positions (D6 requirement).
        hidden = self.model(**batch).last_hidden_state
        return hidden, attention_mask


# ── clean-v3 ablation / control switches ────────────────────────────────────
# Each switch targets EXACTLY ONE preregistered component. Nothing else in the
# model, the data path, the loss or the metric layer changes.
DEFAULT_PROMPT_COMPONENTS = ("dataset", "task", "variable")

_PROMPT_PARTS = {
    "dataset": "Dataset: National-Illness (weekly influenza-like illness).",
    "task": "Task: forecast the next {horizon} weeks.",
    "variable": "Variables: {channel_count} channels; target {target_name}.",
}


def build_prompt_from_components(statistics: dict, components) -> str:
    """Compose the Prompt-as-Prefix string from the ENABLED components only."""
    required = {"horizon", "channel_count", "target_name"}
    if not required.issubset(statistics):
        raise ValueError("Prompt-as-Prefix requires train-only statistics")
    parts = []
    for c in components:
        if c not in _PROMPT_PARTS:
            raise ValueError(f"unknown prompt component {c!r}")
        parts.append(_PROMPT_PARTS[c].format(**statistics))
    return " ".join(parts) if parts else ""


def apply_text_mode(tokens, text_mode: str, generator_seed: int = 20260917):
    """Apply a negative-control transform to frozen text embeddings.

    normal  -> unchanged
    zero    -> all text embeddings set to zero (zero_text control)
    shuffle -> token order permuted deterministically (shuffled_text control)
    removed -> caller must bypass the text branch entirely (handled in forward)
    """
    if text_mode == "normal":
        return tokens
    if text_mode == "zero":
        return torch.zeros_like(tokens)
    if text_mode == "shuffle":
        g = torch.Generator(device=tokens.device).manual_seed(generator_seed)
        perm = torch.randperm(tokens.shape[1], generator=g, device=tokens.device)
        return tokens[:, perm, :]
    raise ValueError(f"unknown text_mode {text_mode!r}")


class QwenTimeLLM(ForecastBackbone):
    name = "qwen_time_llm"

    def __init__(self, T: int, N: int, L: int,
                 model_id: str = "Qwen/Qwen2.5-1.5B",
                 load_backbone: bool = False, hidden_dim: int = 1536,
                 patch_len: int = 8,
                 prompt_components=DEFAULT_PROMPT_COMPONENTS,
                 text_mode: str = "normal"):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.patch_len = int(patch_len)
        self.prompt_components = tuple(prompt_components)
        self.text_mode = str(text_mode)
        self.text = _FrozenTextModel(model_id, load_backbone, hidden_dim)
        self.hidden_dim = self.text.hidden_dim
        self.patch_count = (self.T + self.patch_len - 1) // self.patch_len
        self.patch_projection = nn.Linear(self.patch_len, self.hidden_dim)
        self.prototype_bank = nn.Parameter(torch.randn(32, self.hidden_dim) * 0.02)
        self.prototype_query = nn.Linear(self.hidden_dim, 32)
        self.forecast_projection = nn.Linear(self.hidden_dim, self.N * self.L)
        self.train_statistics = None

    def set_train_statistics(self, statistics: dict) -> None:
        required = {"horizon", "channel_count", "target_name"}
        if not required.issubset(statistics):
            raise ValueError("Prompt-as-Prefix requires train-only statistics")
        self.train_statistics = dict(statistics)

    def build_prompt_as_prefix(self, train_statistics: dict) -> str:
        required = {"horizon", "channel_count", "target_name"}
        if not required.issubset(train_statistics):
            raise ValueError("Prompt-as-Prefix requires train-only statistics")
        return build_prompt_from_components(train_statistics,
                                            self.prompt_components)

    def forward(self, x, ctx=None):
        if not self.text.loaded:
            raise RuntimeError("Qwen backbone unavailable; run on compute node with cache")
        batch, channels, steps = x.shape
        pad = self.patch_count * self.patch_len - steps
        if pad:
            x = F.pad(x, (0, pad), mode="replicate")
        patches = x.reshape(batch, channels, self.patch_count, self.patch_len)
        patch_tokens = self.patch_projection(patches)
        weights = self.prototype_query(patch_tokens).softmax(-1)
        patch_tokens = patch_tokens + weights @ self.prototype_bank
        if self.train_statistics is None:
            raise RuntimeError("train-only Prompt-as-Prefix statistics were not set")
        prompts = [self.build_prompt_as_prefix(self.train_statistics)] * batch
        prompt_tokens, prompt_mask = self.text.encode_prompt(prompts, x.device)
        prompt_tokens = apply_text_mode(prompt_tokens, self.text_mode)
        # The reprogrammed patch token is always a real (non-pad) position, so it
        # carries mask 1 and remains the last token used for the forecast.
        patch_mask = torch.ones((batch, 1), device=x.device, dtype=prompt_mask.dtype)
        combined_mask = torch.cat((prompt_mask, patch_mask), dim=1)
        hidden = self.text.model(
            inputs_embeds=torch.cat((prompt_tokens, patch_tokens.mean(1)), dim=1),
            attention_mask=combined_mask).last_hidden_state[:, -1]
        return self.forecast_projection(hidden).reshape(batch, self.N, self.L)

    def architecture_report(self):
        return {"name": self.name, "display_name": "Qwen2.5-1.5B Time-LLM-inspired",
                "fidelity": FID.INSPIRED_SIMPLIFICATION, "contract_status": "INSPIRED_WITH_COMPONENT_CONTRACT", "published": "Time-LLM (ICLR 2024)",
                "components": ["patching", "prototype_reprogramming", "Prompt-as-Prefix", "frozen_Qwen_backbone", "forecast_projection"],
                "backbone_loaded": self.text.loaded}


class CALFInspired(ForecastBackbone):
    name = "calf_llm"

    def __init__(self, T: int, N: int, L: int, model_id: str = "gpt2",
                 load_backbone: bool = False, hidden_dim: int = 768,
                 text_mode: str = "normal"):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.text_mode = str(text_mode)
        self.temporal_branch = nn.Sequential(nn.Linear(T, hidden_dim), nn.GELU())
        self.text = _FrozenTextModel(model_id, load_backbone, hidden_dim)
        self.text_projection = nn.Linear(self.text.hidden_dim, hidden_dim)
        self.temporal_projection = nn.Linear(hidden_dim, hidden_dim)
        self.match_query = nn.Linear(hidden_dim, hidden_dim)
        self.forecast_head = nn.Linear(hidden_dim, self.N * self.L)
        self._last_auxiliary_loss = None

    def _text_pool(self, textual, text_mask=None):
        """Masked text pooling (D6): when a mask is supplied the LAST NON-PADDING
        token is used, so padded positions can never enter the cross-modal
        representation, the alignment or either auxiliary loss."""
        if text_mask is None:
            return textual[:, -1]
        return self.text.last_non_pad(textual, text_mask)

    def cross_modal_match(self, temporal, textual, text_mask=None):
        query = self.match_query(temporal)
        key = self.text_projection(self._text_pool(textual, text_mask))
        return F.normalize(query, dim=-1), F.normalize(key, dim=-1)

    def feature_regularization_loss(self, temporal, textual, text_mask=None):
        return F.mse_loss(
            self.temporal_projection(temporal),
            self.text_projection(self._text_pool(textual, text_mask)).detach())

    def output_consistency_loss(self, temporal_output, textual_output):
        return F.mse_loss(temporal_output, textual_output.detach())

    def forward(self, x, ctx=None):
        if not self.text.loaded:
            raise RuntimeError("CALF text backbone unavailable; run on compute node with cache")
        temporal = self.temporal_branch(x.mean(1))
        prompts = ["Forecast ILITOTAL from the training protocol."] * x.shape[0]
        textual, text_mask = self.text.encode_prompt(prompts, x.device)
        textual = apply_text_mode(textual, self.text_mode)
        temporal_repr, text_repr = self.cross_modal_match(temporal, textual, text_mask)
        fused = temporal_repr + text_repr
        temporal_output = self.forecast_head(temporal_repr)
        textual_output = self.forecast_head(text_repr)
        self._last_auxiliary_loss = (
            self.feature_regularization_loss(temporal, textual, text_mask)
            + self.output_consistency_loss(temporal_output, textual_output)
        )
        return self.forecast_head(fused).reshape(x.shape[0], self.N, self.L)

    def auxiliary_loss(self):
        if self._last_auxiliary_loss is None:
            return torch.zeros((), device=next(self.parameters()).device)
        return self._last_auxiliary_loss

    def architecture_report(self):
        return {"name": self.name, "display_name": "CALF-inspired Cross-Modal LLM",
                "fidelity": FID.INSPIRED_SIMPLIFICATION, "contract_status": "INSPIRED_WITH_COMPONENT_CONTRACT", "published": "CALF (AAAI 2025)",
                "components": ["temporal_target_branch", "textual_source_branch", "cross_modal_match", "feature_regularization", "output_consistency"],
                "backbone_loaded": self.text.loaded}


class TimeCMAInspired(ForecastBackbone):
    name = "timecma_llm"

    def __init__(self, T: int, N: int, L: int, model_id: str = "gpt2",
                 load_backbone: bool = False, hidden_dim: int = 768,
                 text_mode: str = "normal"):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.text_mode = str(text_mode)
        self.time_series_branch = nn.Linear(T, hidden_dim)
        self.text = _FrozenTextModel(model_id, load_backbone, hidden_dim)
        self.prompt_projection = nn.Linear(self.text.hidden_dim, hidden_dim)
        self.retrieval_query = nn.Linear(hidden_dim, hidden_dim)
        self.forecast_head = nn.Linear(hidden_dim, self.N * self.L)

    def retrieve_aligned_prompt(self, series_repr, prompt_tokens, prompt_mask=None):
        # D6: select the LAST NON-PADDING token via the attention mask, never the
        # final padded array slot.
        if prompt_mask is None:
            pooled = prompt_tokens[:, -1:, :]
        else:
            pooled = self.text.last_non_pad(prompt_tokens, prompt_mask).unsqueeze(1)
        prompt_repr = self.prompt_projection(pooled)
        scores = torch.einsum("bd,bkd->bk", F.normalize(self.retrieval_query(series_repr), dim=-1), F.normalize(prompt_repr, dim=-1))
        index = scores.argmax(dim=-1)
        return prompt_repr[torch.arange(prompt_repr.shape[0], device=prompt_repr.device), index]

    def forward(self, x, ctx=None):
        series_repr = self.time_series_branch(x.mean(1))
        if self.text_mode == "removed":
            # negative control llm_removed_or_alignment_only: bypass the
            # cross-modality retrieval branch entirely and forecast from the
            # numeric time-series branch alone.
            return self.forecast_head(series_repr).reshape(x.shape[0], self.N, self.L)
        if not self.text.loaded:
            raise RuntimeError("TimeCMA text backbone unavailable; run on compute node with cache")
        prompts = ["Encode the temporal context and forecast ILITOTAL."] * x.shape[0]
        prompt_tokens, prompt_mask = self.text.encode_prompt(prompts, x.device)
        prompt_tokens = apply_text_mode(prompt_tokens, self.text_mode)
        aligned = self.retrieve_aligned_prompt(series_repr, prompt_tokens, prompt_mask)
        fused = series_repr + aligned
        return self.forecast_head(fused).reshape(x.shape[0], self.N, self.L)

    def architecture_report(self):
        return {"name": self.name, "display_name": "TimeCMA-inspired LLM",
                "fidelity": FID.INSPIRED_SIMPLIFICATION,
                "contract_status": "CLEAN_ROOM_PAPER_DERIVED_INSPIRED_IMPLEMENTATION",
                "published": "TimeCMA (AAAI 2025)",
                "components": ["independent_time_series_branch", "independent_prompt_branch", "cross_modality_retrieval", "last_token_or_cached_prompt", "forecast_head"],
                "backbone_loaded": self.text.loaded}
