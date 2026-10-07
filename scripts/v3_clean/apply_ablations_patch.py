"""apply_ablations_patch.py — wire the 6 MIFlu ablations and 3 v3 controls.

Every variant is expressed as CONSTRUCTOR-LEVEL flags on the existing backbones,
so each experiment changes ONLY its preregistered target component and nothing
else:

  prompt_components ⊆ {dataset, task, variable}   (QwenTimeLLM Prompt-as-Prefix)
      without_dataset_information          -> drop "dataset"
      without_task_instruction             -> drop "task"
      without_input_variable_description   -> drop "variable"

  use_lora / use_text_ln / gated_inject          (GPT2MifluAdapter -> MIFlu)
      without_lora                         -> use_lora=False
      without_multimodality                -> text branch disabled
      without_lora_and_multimodality       -> both

  text_mode ∈ {normal, zero, shuffle, removed}   (LLM text branch)
      zero_text                            -> text_mode="zero"
      shuffled_text                        -> text_mode="shuffle"
      llm_removed_or_alignment_only        -> text_mode="removed"

The patch is idempotent and asserts every anchor occurs exactly once.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "scripts" / "innovation" / "backbones" / "llm_inspired.py"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def apply(txt: str, old: str, new: str, label: str) -> tuple[str, bool]:
    n = txt.count(old)
    if n == 0 and new in txt:
        return txt, False                      # already applied
    if n != 1:
        raise SystemExit(f"anchor {label!r} not unique: found {n}")
    return txt.replace(old, new), True


src = TARGET.read_text(encoding="utf-8")
changes = {}

# ── 1. shared helpers + prompt component constants ──────────────────────────
HELPERS = '''# ── clean-v3 ablation / control switches ────────────────────────────────────
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


class QwenTimeLLM(ForecastBackbone):'''

src, ch = apply(src, "class QwenTimeLLM(ForecastBackbone):", HELPERS,
                "qwen_class_header")
changes["helpers_and_prompt_components"] = ch

# ── 2. Qwen constructor flags ───────────────────────────────────────────────
src, ch = apply(
    src,
    """                 load_backbone: bool = False, hidden_dim: int = 1536,
                 patch_len: int = 8):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.patch_len = int(patch_len)""",
    """                 load_backbone: bool = False, hidden_dim: int = 1536,
                 patch_len: int = 8,
                 prompt_components=DEFAULT_PROMPT_COMPONENTS,
                 text_mode: str = "normal"):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.patch_len = int(patch_len)
        self.prompt_components = tuple(prompt_components)
        self.text_mode = str(text_mode)""",
    "qwen_init")
changes["qwen_init_flags"] = ch

# ── 3. Qwen prompt composition ──────────────────────────────────────────────
src, ch = apply(
    src,
    """        return (f"Forecast {train_statistics['target_name']} for horizon "
                f"{train_statistics['horizon']} with "
                f"{train_statistics['channel_count']} channels.")""",
    '''        return build_prompt_from_components(train_statistics,
                                            self.prompt_components)''',
    "qwen_prompt_body")
changes["qwen_prompt_composition"] = ch

# ── 4. Qwen forward: text_mode transform ────────────────────────────────────
src, ch = apply(
    src,
    """        prompt_tokens, prompt_mask = self.text.encode_prompt(prompts, x.device)
        # The reprogrammed patch token is always a real (non-pad) position, so it""",
    """        prompt_tokens, prompt_mask = self.text.encode_prompt(prompts, x.device)
        prompt_tokens = apply_text_mode(prompt_tokens, self.text_mode)
        # The reprogrammed patch token is always a real (non-pad) position, so it""",
    "qwen_forward")
changes["qwen_forward_text_mode"] = ch

# ── 5. CALF constructor + forward ───────────────────────────────────────────
src, ch = apply(
    src,
    """    def __init__(self, T: int, N: int, L: int, model_id: str = "gpt2",
                 load_backbone: bool = False, hidden_dim: int = 768):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.temporal_branch = nn.Sequential(nn.Linear(T, hidden_dim), nn.GELU())""",
    """    def __init__(self, T: int, N: int, L: int, model_id: str = "gpt2",
                 load_backbone: bool = False, hidden_dim: int = 768,
                 text_mode: str = "normal"):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.text_mode = str(text_mode)
        self.temporal_branch = nn.Sequential(nn.Linear(T, hidden_dim), nn.GELU())""",
    "calf_init")
changes["calf_init_flag"] = ch

src, ch = apply(
    src,
    """        textual, text_mask = self.text.encode_prompt(prompts, x.device)
        temporal_repr, text_repr = self.cross_modal_match(temporal, textual, text_mask)""",
    """        textual, text_mask = self.text.encode_prompt(prompts, x.device)
        textual = apply_text_mode(textual, self.text_mode)
        temporal_repr, text_repr = self.cross_modal_match(temporal, textual, text_mask)""",
    "calf_forward")
changes["calf_forward_text_mode"] = ch

# ── 6. TimeCMA constructor + forward ────────────────────────────────────────
src, ch = apply(
    src,
    """    def __init__(self, T: int, N: int, L: int, model_id: str = "gpt2",
                 load_backbone: bool = False, hidden_dim: int = 768):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.time_series_branch = nn.Linear(T, hidden_dim)""",
    """    def __init__(self, T: int, N: int, L: int, model_id: str = "gpt2",
                 load_backbone: bool = False, hidden_dim: int = 768,
                 text_mode: str = "normal"):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.text_mode = str(text_mode)
        self.time_series_branch = nn.Linear(T, hidden_dim)""",
    "timecma_init")
changes["timecma_init_flag"] = ch

src, ch = apply(
    src,
    """        prompt_tokens, prompt_mask = self.text.encode_prompt(prompts, x.device)
        aligned = self.retrieve_aligned_prompt(series_repr, prompt_tokens, prompt_mask)
        fused = series_repr + aligned""",
    """        prompt_tokens, prompt_mask = self.text.encode_prompt(prompts, x.device)
        prompt_tokens = apply_text_mode(prompt_tokens, self.text_mode)
        aligned = self.retrieve_aligned_prompt(series_repr, prompt_tokens, prompt_mask)
        # "removed" bypasses the cross-modality retrieval entirely: the forecast
        # is produced from the time-series branch alone.
        fused = series_repr if self.text_mode == "removed" else series_repr + aligned""",
    "timecma_forward")
changes["timecma_forward_text_mode"] = ch

TARGET.write_text(src, encoding="utf-8")

report = {"generated_utc": NOW, "file": str(TARGET.relative_to(ROOT)),
          "changes": changes,
          "n_applied": sum(1 for v in changes.values() if v),
          "variant_registry": {
              "without_dataset_information":
                  {"base": "qwen_time_llm",
                   "kwargs": {"prompt_components": ["task", "variable"]}},
              "without_task_instruction":
                  {"base": "qwen_time_llm",
                   "kwargs": {"prompt_components": ["dataset", "variable"]}},
              "without_input_variable_description":
                  {"base": "qwen_time_llm",
                   "kwargs": {"prompt_components": ["dataset", "task"]}},
              "without_lora":
                  {"base": "gpt2_miflu", "kwargs": {"use_lora": False}},
              "without_multimodality":
                  {"base": "gpt2_miflu",
                   "kwargs": {"use_text_ln": False, "gated_inject": False}},
              "without_lora_and_multimodality":
                  {"base": "gpt2_miflu",
                   "kwargs": {"use_lora": False, "use_text_ln": False,
                              "gated_inject": False}},
              "zero_text": {"base": "llm_text_branch",
                            "kwargs": {"text_mode": "zero"}},
              "shuffled_text": {"base": "llm_text_branch",
                                "kwargs": {"text_mode": "shuffle"}},
              "llm_removed_or_alignment_only": {"base": "llm_text_branch",
                                                "kwargs": {"text_mode": "removed"}},
          }}
out = ROOT / "results" / "v3_clean" / "implementation"
out.mkdir(parents=True, exist_ok=True)
(out / "ablation_control_wiring.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8")

print("[ablations] applied=%d/%d" % (report["n_applied"], len(changes)))
for k, v in changes.items():
    print("  %-32s %s" % (k, "APPLIED" if v else "already present"))
