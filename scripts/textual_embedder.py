"""
textual_embedder.py — MIFlu Step 2
==================================
Builds the input text prompt per Appendix Table X and encodes it using
a full 12-layer GPT2 (text-embedding LLM).

Reference: MIFlu paper, Section IV-A, Section VI-C, Appendix Table X.

Output: htext ∈ R^{len(tokens) × D}  where D = 768 (GPT2-small hidden dim)
"""

import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import os
from transformers import GPT2Model, GPT2Tokenizer


# ── Prompt Template Constants ──────────────────────────────────────────────
# Verbatim from Appendix Table X — placeholders {min_i}, {max_i} filled at runtime

# ── 7-variable template (PRIMARY / N=7 training & inference) ────────────────
# Per the ChatTime-protocol restructure, OT is RESTORED as the 7th channel.
# NOTE: The paper (MIFlu_paper.md, Table X) lists "(7) 'OT' feature for
# long-term forecasting task" but gives NO formula and does NOT define it as a
# black box. Our choice OT = num_patients（CDC 总就诊人次/分母，全量未缩放）
# is our OWN implementation decision, NOT something the paper defines. The real
# PDF only describes it as a long-term-forecasting feature. StandardScaler is
# scale-invariant to a constant divisor, so this choice does not affect training
# numerics. Documented here as an implementation choice, not a paper definition.
# 免责声明：论文原文（Table X）仅称 'OT feature for long-term forecasting task'，
# 未给出明确计算公式；OT=num_patients（全量）是基于 Fig 2(a) 图表量级反推出的
# 强证据支持的实现选择，不是论文明文定义。
PROMPT_TEMPLATE_7 = (
    "[Dataset information]\n"
    "This multivariate time series dataset includes 7 features that recorded "
    "influenza patients data from Centers for Disease Control and Prevention "
    "of the United States between 2002 and 2021.\n"
    "Below(1) to(7) is the information about each feature:\n"
    "***\n"
    "[Input variable description]\n"
    "(1) Percentage of patient visits in the healthcare system attributed to "
    "influenza, adjusted for the proportion of each reporting centers total "
    "patient visits. Minimum value:{min1}, maximum value:{max1}. This variable "
    "peaks 1 time for 1 year.\n"
    "(2) Percentage of unweighted influenza, not adjusted for the proportion "
    "of each reporting total patient visits. Minimum value:{min2}, maximum "
    "value:{max2}. This variable peaks 1 time for 1 year.\n"
    "(3) Total number of influenza patients between age 0 and 4. Minimum "
    "value:{min3}, maximum value:{max3}. This variable peaks 1 time for "
    "1 year.\n"
    "(4) Total number of influenza patients between age 5 and 24. Minimum "
    "value:{min4}, maximum value:{max4}. This variable peaks 1 time for "
    "1 year.\n"
    "(5) Total number of influenza patients. Minimum value:{min5}, maximum "
    "value:{max5}. This variable peaks 1 time for 1 year.\n"
    "(6) A number of influenza providers. Minimum value:{min6}, maximum "
    "value:{max6}. This variable peaks 1 time for 1 year. The overall trend "
    "is upward.\n"
    "(7) 'OT' feature for long-term forecasting task. Minimum value:{min7}, "
    "maximum value:{max7}. This variable peaks 2 times for 1 year. The overall "
    "trend is upward.\n"
    "***\n"
    "[Task instruction]\n"
    "Predict the next {L} steps given the previous 104 steps for the "
    "information attached."
)

# ── 6-variable template (OT-FREE fallback; NOT used by the default N=7 run) ──
# Kept for completeness / ablation comparisons. Only the 6 reliably-sourced
# CDC ILINet channels remain.
PROMPT_TEMPLATE_6 = (
    "[Dataset information]\n"
    "This multivariate time series dataset includes 6 features that recorded "
    "influenza patients data from Centers for Disease Control and Prevention "
    "of the United States between 2002 and 2021.\n"
    "Below(1) to(6) is the information about each feature:\n"
    "***\n"
    "[Input variable description]\n"
    "(1) Percentage of patient visits in the healthcare system attributed to "
    "influenza, adjusted for the proportion of each reporting centers total "
    "patient visits. Minimum value:{min1}, maximum value:{max1}. This variable "
    "peaks 1 time for 1 year.\n"
    "(2) Percentage of unweighted influenza, not adjusted for the proportion "
    "of each reporting total patient visits. Minimum value:{min2}, maximum "
    "value:{max2}. This variable peaks 1 time for 1 year.\n"
    "(3) Total number of influenza patients between age 0 and 4. Minimum "
    "value:{min3}, maximum value:{max3}. This variable peaks 1 time for "
    "1 year.\n"
    "(4) Total number of influenza patients between age 5 and 24. Minimum "
    "value:{min4}, maximum value:{max4}. This variable peaks 1 time for "
    "1 year.\n"
    "(5) Total number of influenza patients. Minimum value:{min5}, maximum "
    "value:{max5}. This variable peaks 1 time for 1 year.\n"
    "(6) A number of influenza providers. Minimum value:{min6}, maximum "
    "value:{max6}. This variable peaks 1 time for 1 year. The overall trend "
    "is upward.\n"
    "***\n"
    "[Task instruction]\n"
    "Predict the next {L} steps given the previous 104 steps."
)

# 6-variable column list used by the OT-free pipeline (ILITOTAL at index 4).
VAR_COLS_6 = [
    "% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
    "ILITOTAL", "NUM. OF PROVIDERS",
]

# 7-variable list (PRIMARY; matches N=7 model input and PROMPT_TEMPLATE_7).
# OT = num_patients（CDC 总就诊人次/分母，全量未缩放）.
# NOTE: This is our OWN implementation choice; the paper (MIFlu_paper.md Table X)
# only calls it "'OT' feature for long-term forecasting task" with no formula.
# Not a paper-defined quantity. StandardScaler neutralizes the constant-scale diff.
# 免责声明：论文原文（Table X）仅称 'OT feature for long-term forecasting task'，
# 未给出明确计算公式；OT=num_patients（全量）是基于 Fig 2(a) 图表量级反推出的
# 强证据支持的实现选择，不是论文明文定义。
VAR_COLS = [
    "% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
    "ILITOTAL", "NUM. OF PROVIDERS", "OT",
]


def compute_prompt_stats(train_df, var_cols=VAR_COLS):
    """Compute min/max per variable from the training set for prompt filling.

    Keys match the template placeholders: min1..minK, max1..maxK.
    Default uses the full 7-variable list (N=7, OT included).
    """
    stats = {}
    for i, col in enumerate(var_cols):
        stats[f"min{i+1}"] = train_df[col].min()
        stats[f"max{i+1}"] = train_df[col].max()
    return stats


def build_prompt(train_df, T=104, L=24):
    """Primary 7-variable prompt (N=7, OT included)."""
    return _format_prompt(PROMPT_TEMPLATE_7, train_df, T=T, L=L,
                          var_cols=VAR_COLS)


def build_prompt_6var(train_df, T=104, L=24):
    """
    OT-FREE prompt (N=6). Build from the 6 reliably-sourced CDC ILINet channels.

    Args:
        train_df: DataFrame with the 6 ILI variable columns (training set only)
        T: input window size (template hardcodes 104)
        L: prediction horizon (24/36/48/60)
    Returns:
        str: complete OT-free prompt.
    """
    return _format_prompt(PROMPT_TEMPLATE_6, train_df, T=T, L=L,
                          var_cols=VAR_COLS_6)


def _format_prompt(template, train_df, T=104, L=24, var_cols=VAR_COLS_6):
    stats = compute_prompt_stats(train_df, var_cols=var_cols)
    fmt_stats = {}
    for k, v in stats.items():
        if v < 100:   # percentages
            fmt_stats[k] = f"{v:.4f}"
        else:          # absolute counts
            fmt_stats[k] = f"{v:.0f}"
    fmt_stats["L"] = L
    return template.format(**fmt_stats)


class TextualInputEmbedder(nn.Module):
    """
    Textual Input Embedder (Section IV-A).

    Uses full 12-layer GPT2 to encode the text prompt into embedding vectors.
    The GPT2 weights are frozen (no fine-tuning of text embedder).
    """

    def __init__(self, gpt2_model_name="gpt2", device="cpu"):
        super().__init__()
        self.device = device
        self.tokenizer = GPT2Tokenizer.from_pretrained(gpt2_model_name)
        self.gpt2 = GPT2Model.from_pretrained(gpt2_model_name)

        # GPT2 tokenizer has no pad token by default; use eos_token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Freeze all GPT2 parameters (text embedder is not fine-tuned)
        for param in self.gpt2.parameters():
            param.requires_grad = False

        self.hidden_dim = self.gpt2.config.hidden_size  # 768
        self.to(device)

    def forward(self, prompt_text):
        """
        Encode a text prompt into embeddings.

        Args:
            prompt_text: str — the complete prompt
        Returns:
            htext: Tensor of shape (1, len_tokens, D) — last hidden states
        """
        tokens = self.tokenizer(
            prompt_text,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
            padding=True,
        )
        tokens = {k: v.to(self.device) for k, v in tokens.items()}

        with torch.no_grad():
            outputs = self.gpt2(**tokens)

        # Last hidden state: (batch, seq_len, hidden_dim)
        return outputs.last_hidden_state

    def get_token_count(self, prompt_text):
        """Return number of tokens for a given prompt (for dimension calc)."""
        tokens = self.tokenizer(prompt_text, return_tensors="pt")
        return tokens["input_ids"].shape[1]


# ── Quick test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Load training data
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "national_illness_raw.csv")
    df = pd.read_csv(data_path)
    n = len(df)
    train = df.iloc[: int(n * 0.70)]

    # Build prompt
    prompt = build_prompt(train, T=104, L=24)
    print("=" * 70)
    print("PROMPT SAMPLE")
    print("=" * 70)
    print(prompt)
    print("=" * 70)

    # Save prompt sample
    sample_path = os.path.join(os.path.dirname(__file__), "data", "prompt_sample.txt")
    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    print(f"\n[SAVED] {sample_path}")

    # Test embedder
    print("\n[INFO] Loading GPT2 text embedder...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embedder = TextualInputEmbedder(device=device)

    htext = embedder(prompt)
    n_tokens = embedder.get_token_count(prompt)
    print(f"[TEST] Prompt tokens: {n_tokens}")
    print(f"[TEST] htext shape:  {htext.shape}  (batch={htext.shape[0]}, tokens={htext.shape[1]}, D={htext.shape[2]})")
    print(f"[TEST] Expected:     (1, {n_tokens}, 768)")
    print(f"[TEST] Device: {htext.device}")
    print("\n[DONE] Step 2: Textual Input Embedder implemented.")
