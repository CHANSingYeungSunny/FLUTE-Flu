#!/usr/bin/env python
"""
q6_text_attention_audit.py — does the model ACTUALLY attend to the text?
========================================================================

WHY THIS SCRIPT EXISTS
----------------------
A strong claim has been circulating in this project (it is hard-coded into the
caption of `plot_attention_proof.py`):

    "the original MIFlu gain came from a LayerNorm statistical shortcut,
     not genuine text understanding"

`plot_attention_proof.py` does NOT actually measure that. It plots `full` as
having ZERO text attention purely because `full` has no dedicated cross-attention
module to hook — but in `full` the text is concatenated as a PREFIX
(`hfuse = [htext || htime]`, miflu_model.py:376) precisely so that time patches
CAN attend to it through GPT-2's causal self-attention. "No hookable module"
is a measurement limitation, not evidence of disuse.

This script measures the real thing, per variant:

  * For `full`-style variants (text as prefix): hook GPT-2 self-attention and
    measure how much attention mass each TIME query puts on TEXT keys.
  * For `gated_inject` (ModalityAligner): hook the cross-attention instead,
    because that variant has no text prefix by construction.

THE STATISTIC THAT MATTERS
--------------------------
`mean_text_attention` from `extract_attention.py` is a MATHEMATICAL IDENTITY,
not a measurement: softmax rows sum to 1, so the mean over n_k keys is always
exactly 1/n_k no matter what the model does. It carries zero information.

The informative statistic is the attention mass on text RELATIVE TO CHANCE.
Under causal masking, a query at position q can see q+1 keys, of which n_text
are text, so the chance-level text mass is n_text / (q + 1). We report

    ratio = observed_text_mass / chance_text_mass

ratio ~ 1  -> text is ignored (indistinguishable from chance)
ratio >> 1 -> the model actively concentrates attention on text
ratio  < 1 -> the model actively AVOIDS text

Output: results/ili/metrics/q6_text_attention_audit.csv
"""

from __future__ import annotations

import csv
import glob
import math
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from configs import CONFIG, set_seed                        # noqa: E402
from miflu_model import MIFlu, ForecastingLLM               # noqa: E402
from textual_embedder import TextualInputEmbedder           # noqa: E402
from train_ablation import load_and_normalize, build_prompt  # noqa: E402

OUT_CSV = os.path.join(PROJECT_ROOT, "results", "ili", "metrics",
                       "q6_text_attention_audit.csv")

# Run on GPU when one is allocated (HPC), else CPU (local).
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Works both on HPC (hpc_results/) and locally (results/ili/).
_HPC = os.path.join(PROJECT_ROOT, "hpc_results", "journal_evidence")
_LOCAL = os.path.join(PROJECT_ROOT, "results", "ili", "journal_evidence")
CKPT_ROOT = _HPC if os.path.isdir(_HPC) else _LOCAL

# name -> (variant flags, checkpoint sub-directory)
#
# IMPORTANT: `full/reps_1_to_10` retains the LAST horizon of the L sweep
# (its output head is 7*60 = 420 wide, i.e. L=60), so the L=24 baseline must be
# read from `full_H24`, whose file is named best_model_L24.pt. The horizon is
# inferred from the checkpoint itself, so this cannot silently mismatch again.
VARIANTS = {
    "full_L24": (dict(use_text_ln=True, use_lora=True,
                      gated_inject=False, unfreeze_first_k=0), "full_H24"),
    "no_text_ln": (dict(use_text_ln=False, use_lora=True,
                        gated_inject=False, unfreeze_first_k=0), "no_text_ln"),
    "no_lora": (dict(use_text_ln=True, use_lora=False,
                     gated_inject=False, unfreeze_first_k=0), "no_lora"),
    "gated_inject": (dict(use_text_ln=True, use_lora=True,
                          gated_inject=True, unfreeze_first_k=2),
                     "gated_inject"),
}
BENIGN = ("attn.bias", "attn.masked_bias")

_BLANK = {"path": "", "L": "", "n_text": "", "n_time": "",
          "observed_text_mass": "", "chance_text_mass": "",
          "mass_ratio_vs_chance": "", "peak_text_attention": "",
          "peak_chance_per_key": "", "peak_ratio_vs_chance": "",
          "n_queries": ""}


# --------------------------------------------------------------------------- #
# Capture GPT-2 self-attention weights (baseline architecture)
# --------------------------------------------------------------------------- #
def install_self_attn_capture(store: list):
    """Replace ForecastingLLM._lora_attention with a weight-recording clone.

    The body is copied line-for-line from the original so the numerics are
    bit-identical; the only addition is `store.append(aw.detach().cpu())`.
    """
    def _capturing(self, block, hidden):
        attn = block.attn
        lora = getattr(attn, "_lora", None)

        qkv = attn.c_attn(hidden)
        if lora is not None:
            qkv = qkv + lora(hidden)

        embed_dim = attn.embed_dim
        query, key, value = qkv.split(embed_dim, dim=2)
        num_heads = attn.num_heads
        head_dim = embed_dim // num_heads

        query = query.view(query.shape[0], query.shape[1], num_heads, head_dim)
        key = key.view(key.shape[0], key.shape[1], num_heads, head_dim)
        value = value.view(value.shape[0], value.shape[1], num_heads, head_dim)

        query = query.permute(0, 2, 1, 3)
        key = key.permute(0, 2, 1, 3)
        value = value.permute(0, 2, 1, 3)

        seq_len = query.shape[2]
        causal_mask = torch.tril(
            torch.ones(seq_len, seq_len, device=hidden.device)
        ).view(1, 1, seq_len, seq_len)

        aw = (query @ key.transpose(-2, -1)) / math.sqrt(head_dim)
        aw = aw.masked_fill(causal_mask == 0, float("-inf"))
        aw = F.softmax(aw, dim=-1)
        store.append(aw.detach().cpu())               # <-- the only addition
        attn_output = aw @ value

        attn_output = attn_output.permute(0, 2, 1, 3).contiguous()
        attn_output = attn_output.view(attn_output.shape[0], seq_len, embed_dim)
        attn_output = attn.c_proj(attn_output)
        return attn_output

    ForecastingLLM._lora_attention = _capturing


def install_cross_attn_capture(model, store: list):
    """Capture ModalityAligner cross-attention (gated_inject only)."""
    aligner = model.forecasting_llm.modality_aligner
    if aligner is None:
        raise RuntimeError("no ModalityAligner in this variant")

    def _hook(module, args, output):
        if isinstance(output, tuple) and len(output) == 2 and output[1] is not None:
            store.append(output[1].detach().cpu())

    return aligner.cross_attn.register_forward_hook(_hook)


# --------------------------------------------------------------------------- #
def analyse_prefix_attention(weights, n_text: int, n_time: int) -> dict:
    """weights: list of (1, heads, seq, seq). Text = positions [:n_text]."""
    observed, chance, ratios, peaks, peak_chance = [], [], [], [], []
    for aw in weights:
        w = aw[0].float()                       # (heads, seq, seq)
        if w.shape[-1] < n_text + n_time:
            continue
        for qi in range(n_text, w.shape[-1]):
            row = w[:, qi, :]                   # (heads, seq)
            text_row = row[:, :n_text]          # (heads, n_text)
            obs = float(text_row.sum(dim=-1).mean())       # mass on text
            chc = n_text / float(qi + 1)                   # chance level
            observed.append(obs)
            chance.append(chc)
            ratios.append(obs / chc if chc > 0 else float("nan"))
            peaks.append(float(text_row.max(dim=-1).values.mean()))
            peak_chance.append(1.0 / float(qi + 1))

    return {
        "path": "GPT2 causal self-attention over [text || time]",
        "n_text": n_text,
        "n_time": n_time,
        "observed_text_mass": float(np.mean(observed)),
        "chance_text_mass": float(np.mean(chance)),
        "mass_ratio_vs_chance": float(np.nanmean(ratios)),
        "peak_text_attention": float(np.mean(peaks)),
        "peak_chance_per_key": float(np.mean(peak_chance)),
        "peak_ratio_vs_chance": float(np.mean(peaks) / np.mean(peak_chance)),
        "n_queries": len(ratios),
    }


def analyse_cross_attention(weights, n_text: int, n_time: int) -> dict:
    """weights: list of (1, n_q time patches, n_k text tokens)."""
    aw = weights[0].float()
    if aw.dim() == 4:
        aw = aw.mean(dim=1)
    aw = aw[0]                                   # (n_q, n_k)
    obs = float(aw.mean())
    peek = float(aw.max(dim=-1).values.mean())
    chance = 1.0 / aw.shape[1]
    return {
        "path": "ModalityAligner cross-attention (time queries -> text keys)",
        "n_text": int(aw.shape[1]),
        "n_time": int(aw.shape[0]),
        "observed_text_mass": obs,
        "chance_text_mass": chance,
        "mass_ratio_vs_chance": obs / chance,
        "peak_text_attention": peek,
        "peak_chance_per_key": chance,
        "peak_ratio_vs_chance": peek / chance,
        "n_queries": int(aw.shape[0]),
    }


# --------------------------------------------------------------------------- #
def run_variant(name: str, x, T: int, htext_for_L) -> dict:
    flags, subdir = VARIANTS[name]
    ck_dir = os.path.join(CKPT_ROOT, subdir, "reps_1_to_10", "rep_01",
                          "checkpoints")
    found = sorted(glob.glob(os.path.join(ck_dir, "best_model*.pt")))
    if not found:
        print(f"\n=== {name} ===  checkpoint not found under {ck_dir}")
        return {"variant": name, "status": "checkpoint not found", **_BLANK}
    ckpt = found[0]

    state = torch.load(ckpt, map_location="cpu")
    # Infer the horizon the checkpoint was trained with: the output head is
    # shaped [N*L, D]. This prevents a silent L mismatch (full/ holds L=60).
    L = int(state["forecasting_llm.output_projection.weight"].shape[0]
            // CONFIG["N"])

    model = MIFlu(N=CONFIG["N"], T=T, L=L, Lp=CONFIG["Lp"], S=CONFIG["S"],
                  K=CONFIG["K"], lora_r=CONFIG["lora_r"], device=DEVICE,
                  **flags)
    res = model.load_state_dict(state, strict=False)
    missing = [k for k in res.missing_keys if not k.endswith(BENIGN)]
    assert not missing and not res.unexpected_keys, \
        f"{name}: ckpt mismatch missing={missing[:3]} " \
        f"unexp={res.unexpected_keys[:3]}"
    model.eval()

    htext = htext_for_L(L)                 # prompt text depends on L
    store: list = []
    handle = None
    if flags["gated_inject"]:
        handle = install_cross_attn_capture(model, store)
    else:
        install_self_attn_capture(store)

    try:
        with torch.no_grad():
            model(x.to(DEVICE), htext.to(DEVICE))
    finally:
        if handle is not None:
            handle.remove()

    n_text = int(htext.shape[1])
    n_time = int(model.forecasting_llm.total_patches)
    if flags["gated_inject"]:
        stats = analyse_cross_attention(store, n_text, n_time)
    else:
        stats = analyse_prefix_attention(store, n_text, n_time)
    stats["L"] = L

    print(f"\n=== {name} ===   (checkpoint: {os.path.basename(ckpt)}, L={L})")
    print(f"  path                 : {stats['path']}")
    print(f"  n_text / n_time      : {stats['n_text']} / {stats['n_time']}")
    print(f"  text mass observed   : {stats['observed_text_mass']:.6f}")
    print(f"  text mass by chance  : {stats['chance_text_mass']:.6f}")
    print(f"  MASS RATIO vs chance : {stats['mass_ratio_vs_chance']:.3f}x")
    print(f"  peak text attention  : {stats['peak_text_attention']:.6f}")
    print(f"  peak chance per key  : {stats['peak_chance_per_key']:.6f}")
    print(f"  PEAK RATIO vs chance : {stats['peak_ratio_vs_chance']:.2f}x")
    return {"variant": name, "status": "ok", **stats}


def main() -> None:
    set_seed(42)
    T = CONFIG["T"]

    data = load_and_normalize()
    k = data["val_end"] - T
    window = data["data_norm"][k:data["val_end"]]
    x = torch.from_numpy(np.ascontiguousarray(window.T))[None]

    # The prompt text embeds L, so build (and cache) one embedding per horizon.
    _cache = {}

    def htext_for_L(L: int):
        if L not in _cache:
            print(f"[q6] building real text embedding for L={L} "
                  f"(GPT-2, frozen, device={DEVICE})...")
            prompt = build_prompt(data["train_df"], T=T, L=L)
            _cache[L] = TextualInputEmbedder(device=DEVICE)(prompt)
            print(f"[q6]   htext shape {tuple(_cache[L].shape)}")
        return _cache[L]

    rows = [run_variant(v, x, T, htext_for_L) for v in VARIANTS]

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    fields = ["variant", "status", "path", "L", "n_text", "n_time",
              "observed_text_mass", "chance_text_mass",
              "mass_ratio_vs_chance", "peak_text_attention",
              "peak_chance_per_key", "peak_ratio_vs_chance", "n_queries"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\n[q6] wrote {OUT_CSV}")

    print("\n" + "=" * 72)
    print("READING GUIDE")
    print("=" * 72)
    print("mass_ratio_vs_chance ~ 1.0  -> text ignored (chance level)")
    print("mass_ratio_vs_chance  > 1.0 -> model concentrates attention ON text")
    print("mass_ratio_vs_chance  < 1.0 -> model actively AVOIDS text")


if __name__ == "__main__":
    main()
