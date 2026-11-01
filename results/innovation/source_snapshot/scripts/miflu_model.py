"""
miflu_model.py — MIFlu Steps 3 & 4
===================================
Step 3: Time-Series Input Embedder
  - Instance Normalization (reversible, per variable)
  - Patching (Lp=24, S=2) → num_patches = floor((T-Lp)/S) + 2
  - Linear Embedder: patch (dim Lp) → D (768)

Step 4: Forecasting LLM with LoRA Fine-tuning
  - GPT2 first K=6 layers (National) / K=4 (Regional)
  - LoRA (r=4) on Multi-Head Attention only
  - Output Projection: Linear layer for final predictions

Full MIFlu Model: Text Embedder + Time Embedder → Concatenate → GPT2+LoRA → Output

Reference: MIFlu paper, Section IV-B, IV-C, V-C.
"""

import os
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from transformers import GPT2Model, GPT2Config
import numpy as np

# ── Centralised configuration (single source of truth) ──
# Every architectural default below now comes from configs.py instead of being
# a literal in this file. Values are IDENTICAL to the previous literals, so
# this is a pure refactor: the parameter counts must not move.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from configs import CONFIG, N_HEADS


# ═══════════════════════════════════════════════════════════════════════════
# LoRA Module (Manual Implementation)
# ═══════════════════════════════════════════════════════════════════════════

class LoRALinear(nn.Module):
    """
    Low-Rank Adaptation add-on for a frozen linear layer.
    W'x = Wx + (x @ A^T @ B^T) * scaling

    Does NOT include the base weight; the base forward is done by the
    original layer. This module only computes the LoRA delta.

    Reference: Hu et al. 2021, Section IV-C of MIFlu.
    """

    def __init__(self, in_features, out_features, r=4, alpha=1.0, dropout=0.0):
        super().__init__()
        self.r = r
        self.in_features = in_features
        self.out_features = out_features

        # LoRA weights A (r × in) and B (out × r)
        self.lora_A = nn.Parameter(torch.zeros(r, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, r))
        self.scaling = alpha / r

        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)

        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

    def forward(self, x):
        """
        Args:
            x: input to the base layer (..., in_features)
        Returns:
            LoRA delta: (..., out_features)
        """
        # x: (batch, in_features)
        # A: (r, in_features) → A @ x? No, x @ A^T
        # x @ A^T: (batch, in) @ (in, r) = (batch, r)
        # (batch, r) @ B^T: (batch, r) @ (r, out) = (batch, out)
        delta = (self.dropout(x) @ self.lora_A.T @ self.lora_B.T) * self.scaling
        return delta


def apply_lora_to_gpt2_attention(block, r=4, alpha=4.0, dropout=0.05):
    """
    Apply LoRA to the multi-head attention layer of a GPT2 transformer block.

    GPT2Attention uses Conv1D for c_attn (combined QKV projection).
    Conv1D weight shape: (nx, nf) = (hidden_dim, 3*hidden_dim)
    We add a LoRA delta module that computes (x @ A^T @ B^T) * scale.

    Args:
        block: GPT2Block from transformers
        r: LoRA rank (default 4 per MIFlu)
        alpha: LoRA alpha scaling
    Returns:
        LoRALinear module (trainable)
    """
    attn = block.attn
    conv1d = attn.c_attn

    # Freeze Conv1D weights and bias
    conv1d.weight.requires_grad = False
    if conv1d.bias is not None:
        conv1d.bias.requires_grad = False

    # Conv1D stores weight as (nx, nf) = (in_features, out_features)
    in_features = conv1d.weight.shape[0]   # nx = 768
    out_features = conv1d.weight.shape[1]  # nf = 2304

    lora = LoRALinear(
        in_features=in_features,
        out_features=out_features,
        r=r,
        alpha=alpha,
        dropout=dropout,
    )

    attn._lora = lora
    attn._lora_applied = True

    return lora


# ═══════════════════════════════════════════════════════════════════════════
# Step 3: Time-Series Input Embedder
# ═══════════════════════════════════════════════════════════════════════════

class TimeSeriesEmbedder(nn.Module):
    """
    Time-Series Input Embedder (Section IV-B).

    Pipeline: InstanceNorm → Patching → Linear Projection → htime

    Args:
        N: number of variables (7 for National, 10 for Regional)
        T: input window size (104 for National)
        Lp: patch length (24 for National, 4 for Regional)
        S: stride (2 for both)
        D: target embedding dimension (768 for GPT2-small)
    """

    def __init__(self, N=CONFIG["N"], T=CONFIG["T"], Lp=CONFIG["Lp"],
                 S=CONFIG["S"], D=CONFIG["D"]):
        super().__init__()
        self.N = N
        self.T = T
        self.Lp = Lp
        self.S = S
        self.D = D

        # Number of patches per variable: floor((T - Lp) / S) + 2
        self.num_patches = (T - Lp) // S + 2

        # Total time-series tokens
        self.total_patches = N * self.num_patches

        # Linear embedder: projects each patch (length Lp) → D dimensions
        # One embedder shared across all variables (as per GPT4TS)
        self.linear_embedder = nn.Linear(Lp, D)

        print(f"[TimeEmbedder] N={N}, T={T}, Lp={Lp}, S={S}")
        print(f"[TimeEmbedder] num_patches={self.num_patches}, total={self.total_patches}")

    def forward(self, x, means=None, stdevs=None):
        """
        Args:
            x: input time series (batch, N, T)
            means: per-variable means for instance norm (batch, N) or None
            stdevs: per-variable stdevs for instance norm (batch, N) or None
        Returns:
            htime: (batch, total_patches, D)
            means: computed means (for reversible instance norm)
            stdevs: computed stdevs (for reversible instance norm)
        """
        batch_size = x.shape[0]

        # ── Instance Normalization (per variable, per sample) ──
        if means is None:
            means = x.mean(dim=-1, keepdim=True)  # (batch, N, 1)
        if stdevs is None:
            # Author GPT4TS_lora.py L111: stdev = torch.sqrt(torch.var(x, dim=1, keepdim=True, unbiased=False) + 1e-5)
            stdevs = torch.sqrt(x.var(dim=-1, keepdim=True, unbiased=False) + 1e-5)  # (batch, N, 1)

        x_norm = (x - means) / stdevs  # (batch, N, T)

        # ── Patching (author-faithful) ──
        # recovery/author_repo/models/GPT4TS_lora.py:
        #   self.padding_patch_layer = nn.ReplicationPad1d((0, self.stride))
        #   self.patch_num += 1
        #   x = self.padding_patch_layer(x)                        # (B, N, T+stride)
        #   x = x.unfold(dimension=-1, size=patch_size, step=stride)
        # With T=104, Lp=24, S=2: pad -> 106, unfold -> (106-24)//2+1 = 42 patches.
        # The final patch is x[82:106] where x[104:106] REPLICATE the last value.
        # (Earlier variant unfolded to 41 patches then duplicated the last one —
        #  a different last-patch content. This matches the author exactly.)
        x_pad = torch.nn.functional.pad(
            x_norm, (0, self.S), mode="replicate")       # (batch, N, T + S)
        patches = x_pad.unfold(dimension=-1, size=self.Lp, step=self.S)
        # patches shape: (batch, N, num_patches, Lp)   num_patches == 42

        # Flatten variables and patches: (batch, N*num_patches, Lp)
        patches = patches.reshape(batch_size, self.total_patches, self.Lp)

        # ── Linear Embedder ──
        htime = self.linear_embedder(patches)  # (batch, total_patches, D)

        return htime, means, stdevs


# ═══════════════════════════════════════════════════════════════════════════
# Step 4: Forecasting LLM with LoRA
# ═══════════════════════════════════════════════════════════════════════════

class ModalityAligner(nn.Module):
    """
    ModalityAligner — Gated cross-modal injection (the "Third Way" architecture).

    Aligns the text modality into the time-series stream *before* the forecasting
    LLM via a cross-attention where the time patches are queries and the text
    tokens are keys/values. A single learnable scalar gate (sigmoid) controls how
    much aligned text context is injected, and the result is LayerNorm-ed.

    Replaces the default `[htext || htime]` concatenation for the `gated_inject`
    variant, so no text prefix is fed to the LLM and cross-modal attention is
    activated inside the aligner itself.

    Args:
        D: embedding dimension (768)
        n_heads: number of attention heads
    """

    def __init__(self, D=CONFIG["D"], n_heads=N_HEADS):
        super().__init__()
        self.cross_attn = nn.MultiheadAttention(D, n_heads, batch_first=True)
        self.gate = nn.Parameter(torch.zeros(1))  # sigmoid -> ~0.5 at init
        self.ln = nn.LayerNorm(D)

    def forward(self, htime, htext):
        """
        Args:
            htime: (batch, total_patches, D) — time-series stream (queries)
            htext: (batch, text_tokens, D)  — text stream (keys/values)
        Returns:
            fused: (batch, total_patches, D)
        """
        aligned, _ = self.cross_attn(query=htime, key=htext, value=htext)
        g = torch.sigmoid(self.gate)
        return self.ln(htime + g * aligned)


class ForecastingLLM(nn.Module):
    """
    Forecasting LLM (Section IV-C).

    Takes first K layers of pretrained GPT2, applies LoRA (r=4) to MHA,
    freezes all other parameters except LayerNorm and Positional Encoding.

    Args:
        K: number of GPT2 layers to use (6 for National, 4 for Regional)
        D: hidden dimension (768 for GPT2-small)
        lora_r: LoRA rank (4 per paper)
        L: prediction horizon
        N: number of variables
        total_patches: total time-series tokens (N × num_patches)
    """

    def __init__(self, K=CONFIG["K"], D=CONFIG["D"], lora_r=CONFIG["lora_r"],
                 lora_alpha=CONFIG["lora_alpha"], L=CONFIG["L_list"][0],
                 N=CONFIG["N"], total_patches=294, use_text_ln=True,
                 use_lora=True, gated_inject=False, unfreeze_first_k=0,
                 flatten_head=True, author_faithful=True, use_text=True):
        super().__init__()
        self.K = K
        self.D = D
        self.N = N
        self.L = L
        self.total_patches = total_patches
        # ── Purity flags (defaults = exactly the ORIGINAL behaviour) ──
        self.use_text_ln = use_text_ln
        self.use_lora = use_lora
        self.gated_inject = gated_inject
        self.flatten_head = flatten_head
        self.author_faithful = bool(author_faithful)
        self.use_text = bool(use_text)
        self.unfreeze_first_k = unfreeze_first_k

        # Load pretrained GPT2
        gpt2_full = GPT2Model.from_pretrained("gpt2")

        # ── Positional Encoding & Token Embedding ──
        # Reuse GPT2's wpe (positional) and wte (token) embeddings
        self.wpe = nn.Embedding.from_pretrained(
            gpt2_full.wpe.weight[:2048].clone(), freeze=False
        )  # Trainable per paper
        self.wte = nn.Embedding.from_pretrained(
            gpt2_full.wte.weight.clone(), freeze=True
        )  # Not used directly, but kept for completeness

        # ── Transformer Blocks (first K layers) ──
        self.blocks = nn.ModuleList()
        self.lora_modules = nn.ModuleList()

        for i in range(K):
            block = gpt2_full.h[i]
            if i < unfreeze_first_k:
                # BRANCH A: Fully Unfreeze (NO LoRA allowed here!)
                for param in block.parameters():
                    param.requires_grad = True
            else:
                # BRANCH B: Freeze backbone, apply LoRA conditionally
                for param in block.parameters():
                    param.requires_grad = False
                block.ln_1.weight.requires_grad = True
                block.ln_1.bias.requires_grad = True
                block.ln_2.weight.requires_grad = True
                block.ln_2.bias.requires_grad = True
                if use_lora:
                    lora = apply_lora_to_gpt2_attention(block, r=lora_r, alpha=lora_alpha)
                    self.lora_modules.append(lora)
            self.blocks.append(block)

        # ── Text Embedding Normalization ──
        # GPT2 last_hidden_state has no output LayerNorm → raw scale ~9.73 std
        # Normalize to match time embedding scale (~0.59 std) for stable fusion.
        # Disabled (Identity) when use_text_ln=False (ablation) OR when the
        # ModalityAligner handles alignment instead (gated_inject).
        if use_text_ln and not gated_inject:
            self.text_ln = nn.LayerNorm(D, eps=gpt2_full.config.layer_norm_epsilon)
        else:
            self.text_ln = nn.Identity()

        # ── ModalityAligner (gated cross-modal injection) ──
        # Only instantiated for the gated_inject variant. When active, text is
        # aligned into the time-series stream BEFORE the forecasting LLM, so no
        # text prefix is concatenated in forward().
        self.modality_aligner = (
            ModalityAligner(D, n_heads=N_HEADS) if gated_inject else None
        )

        # ── GPT2 Dropouts (attn_pdrop=0.1, resid_pdrop=0.1) ──
        self.attn_dropout = nn.Dropout(0.1)
        self.resid_dropout = nn.Dropout(0.1)
        # GPT2Model also applies embd_pdrop=0.1 to the embedding tensor right
        # after adding wpe (transformers GPT2Model.forward: `hidden_states =
        # self.drop(hidden_states)`). Omitting it silently reduced the
        # regularisation relative to the author's model.
        self.embd_dropout = nn.Dropout(0.1)

        # ── Final LayerNorm ──
        # Author GPT4TS_lora.py uses GPT2Model's ln_f (the standard final LayerNorm),
        # NOT h[K-1].ln_2. These are DIFFERENT parameters.
        self.final_ln = nn.LayerNorm(D, eps=gpt2_full.config.layer_norm_epsilon)
        self.final_ln.load_state_dict(gpt2_full.ln_f.state_dict())

        # ── Output Projection ──
        # Two head variants (see forward()):
        #   flatten_head=True  (reference-faithful, Time-Series-Library Flatten_Head):
        #       keep each variable's patch sequence, flatten PER VARIABLE, then
        #       Linear(num_patches * D, L). Preserves variable identity AND patch order.
        #   flatten_head=False (legacy):
        #       mean-pool over ALL (variable x patch) tokens -> Linear(D, N*L).
        #       This collapses 7 variables x 42 patches into ONE 768-d vector before
        #       projecting to 168 outputs, which discards variable identity and the
        #       temporal order of patches — a severe information bottleneck.
        self.num_patches = total_patches // N
        if self.num_patches * N != total_patches:
            raise ValueError(
                f"total_patches={total_patches} is not divisible by N={N}; "
                "cannot reshape into (N, num_patches, D)")
        if self.flatten_head or self.author_faithful:
            self.output_projection = nn.Linear(self.num_patches * D, L)
        else:
            self.output_projection = nn.Linear(D, N * L)

        # Free the full model to save memory
        del gpt2_full

        print(f"[ForecastingLLM] K={K}, lora_r={lora_r}, D={D}, total_patches={total_patches}")
        print(f"[ForecastingLLM] Output: (N={N}) × (L={L}) = {N*L}")

    def forward(self, htime, htext):
        """
        Args:
            htime: time-series embeddings (batch, total_patches, D)
            htext: text embeddings (batch, text_tokens, D)
        Returns:
            y_hat: predictions (batch, N, L)
        """
        batch_size = htime.shape[0]
        text_len = htext.shape[1] if htext is not None else 0

        # ── Concatenate / fuse embeddings ──
        if self.author_faithful:
            # EXACT author architecture (recovery/author_repo/models/GPT4TS_lora.py):
            #   x = rearrange(x, 'b m n p -> (b m) n p')      # channel independent
            #   outputs = torch.cat((outputs, text_emb), axis=1)   # TEXT APPENDED
            #   outputs = outputs[:, :self.patch_num, :]      # take FIRST patch_num
            #   outputs = self.out_layer(outputs.reshape(B*M, -1))
            # Channel-independence is the key: each of the N variables is pushed
            # into the BATCH dim and runs through GPT2 on its own. Our earlier
            # variant kept all N*P tokens in ONE sequence, letting variables attend
            # to each other — a materially different computation.
            htime_ci = htime.reshape(
                batch_size * self.N, self.num_patches, self.D)      # (B*N, P, D)
            if htext is not None and self.use_text:
                htext_n = self.text_ln(htext) if self.use_text_ln else htext
                # tile text across the channel dim -> (B*N, text_len, D)
                if htext_n.shape[0] == batch_size:
                    htext_ci = (htext_n.unsqueeze(1)
                                .expand(batch_size, self.N, htext_n.shape[1], self.D)
                                .reshape(batch_size * self.N, htext_n.shape[1], self.D))
                else:
                    htext_ci = htext_n.repeat(batch_size * self.N // htext_n.shape[0], 1, 1)
                # TEXT APPENDED AFTER TIME PATCHES (author order)
                hfuse = torch.cat([htime_ci, htext_ci], dim=1)      # (B*N, P+T, D)
            else:
                hfuse = htime_ci
        elif self.gated_inject and self.modality_aligner is not None:
            # Gated cross-modal injection: text aligned into time stream.
            hfuse = self.modality_aligner(htime, htext)  # (batch, total_patches, D)
        else:
            # LEGACY: TEXT FIRST so time patches can attend to text.
            # NOTE: this differs from the released author code, which appends text.
            htext_n = self.text_ln(htext) if self.use_text_ln else htext
            hfuse = torch.cat([htext_n, htime], dim=1)   # (batch, T + total_patches, D)
        total_len = hfuse.shape[1]

        # ── Add positional encodings ──
        positions = torch.arange(total_len, device=hfuse.device).unsqueeze(0)
        pos_embeds = self.wpe(positions)  # (1, total_len, D)
        hfuse = hfuse + pos_embeds
        # Author path uses GPT2Model, which drops (embd_pdrop=0.1) here.
        hfuse = self.embd_dropout(hfuse)

        # ── Pass through GPT2 transformer blocks ──
        hidden = hfuse
        for block in self.blocks:
            # Manual forward through GPT2Block with LoRA
            residual = hidden
            hidden = block.ln_1(hidden)

            # Apply attention with LoRA
            attn_output = self._lora_attention(block, hidden)
            hidden = residual + attn_output

            # Feed-forward
            residual = hidden
            hidden = block.ln_2(hidden)
            hidden = residual + block.mlp(hidden)

        hidden = self.final_ln(hidden)

        # ── Extract the forecast portion ──
        if self.author_faithful:
            # Author: outputs[:, :self.patch_num, :] — take the FIRST patch_num
            # tokens, which are the time patches (text was appended after them).
            hforecast = hidden[:, :self.num_patches, :]     # (B*N, P, D)
        elif self.gated_inject and self.modality_aligner is not None:
            # No text prefix was concatenated → keep the FULL sequence.
            hforecast = hidden[:, :self.total_patches, :]  # (batch, total_patches, D)
        else:
            # Text came first, so time patches are at the END
            hforecast = hidden[:, -self.total_patches:, :]  # (batch, total_patches, D)

        # ── Output Projection ──
        if self.author_faithful:
            # Author: out_layer = Linear(d_model * patch_num, pred_len), applied to
            # outputs.reshape(B*M, -1) — per-variable flatten of the first patch_num
            # time-patch tokens (already channel-independent here).
            y_flat = self.output_projection(
                hforecast.reshape(batch_size * self.N, -1))   # (B*N, L)
            y_hat = y_flat.reshape(batch_size, self.N, self.L)
        elif self.flatten_head:
            # Reference-faithful (TSL Flatten_Head): the token order produced by
            # TimeSeriesEmbedder is [var0_p0..var0_pP, var1_p0..var1_pP, ...],
            # i.e. index = var_idx * num_patches + patch_idx. Undo that to get
            # (batch, N, num_patches, D), then flatten PER VARIABLE so each
            # variable keeps its own patch sequence before the linear head.
            h = hforecast.reshape(batch_size, self.N, self.num_patches, self.D)
            h = h.reshape(batch_size, self.N, self.num_patches * self.D)
            y_hat = self.output_projection(h)          # (batch, N, L)
        else:
            # Legacy mean-pool head (kept for A/B comparison only).
            h_agg = hforecast.mean(dim=1)              # (batch, D)
            y_flat = self.output_projection(h_agg)     # (batch, N * L)
            y_hat = y_flat.reshape(batch_size, self.N, self.L)

        return y_hat

    def _lora_attention(self, block, hidden):
        """
        Apply multi-head attention with LoRA.
        Base QKV projection runs through frozen Conv1D; LoRA delta is added.
        """
        attn = block.attn
        lora = getattr(attn, "_lora", None)

        # QKV projection: base (frozen Conv1D) + LoRA delta
        qkv = attn.c_attn(hidden)  # Conv1D base forward
        if lora is not None:
            qkv = qkv + lora(hidden)  # Add LoRA delta
        # Note: Conv1D already includes bias internally

        # Split into query, key, value
        # GPT2 uses combined QKV: (batch, seq, 3*hidden)
        embed_dim = attn.embed_dim
        query, key, value = qkv.split(embed_dim, dim=2)

        # Reshape for multi-head: (batch, seq, num_heads, head_dim)
        num_heads = attn.num_heads
        head_dim = embed_dim // num_heads

        query = query.view(query.shape[0], query.shape[1], num_heads, head_dim)
        key = key.view(key.shape[0], key.shape[1], num_heads, head_dim)
        value = value.view(value.shape[0], value.shape[1], num_heads, head_dim)

        # Transpose to (batch, num_heads, seq, head_dim)
        query = query.permute(0, 2, 1, 3)
        key = key.permute(0, 2, 1, 3)
        value = value.permute(0, 2, 1, 3)

        # Scaled dot-product attention with causal mask
        seq_len = query.shape[2]
        causal_mask = torch.tril(
            torch.ones(seq_len, seq_len, device=hidden.device)
        ).view(1, 1, seq_len, seq_len)

        attn_weights = (query @ key.transpose(-2, -1)) / math.sqrt(head_dim)
        attn_weights = attn_weights.masked_fill(causal_mask == 0, float("-inf"))
        attn_weights = F.softmax(attn_weights, dim=-1)
        # Author GPT2: attn_pdrop=0.1 (dropout on attention weights after softmax)
        attn_weights = self.attn_dropout(attn_weights)
        attn_output = attn_weights @ value

        # Reshape back: (batch, seq, embed_dim)
        attn_output = attn_output.permute(0, 2, 1, 3).contiguous()
        attn_output = attn_output.view(attn_output.shape[0], seq_len, embed_dim)

        # Output projection + resid dropout (GPT2 resid_pdrop=0.1)
        attn_output = attn.c_proj(attn_output)
        attn_output = self.resid_dropout(attn_output)

        return attn_output


# ═══════════════════════════════════════════════════════════════════════════
# Full MIFlu Model
# ═══════════════════════════════════════════════════════════════════════════

class MIFlu(nn.Module):
    """
    MIFlu: Multimodal Influenza Forecasting Scheme.

    Components:
      1. TextualInputEmbedder (full GPT2, frozen) → htext
      2. TimeSeriesEmbedder (InstanceNorm + Patching + Linear) → htime
      3. ForecastingLLM (GPT2 K layers + LoRA) → y_hat

    Args:
        N: number of variables (7 for National)
        T: input window (104 for National)
        L: prediction horizon (24, 36, 48, or 60)
        Lp: patch length (24 for National, 4 for Regional)
        S: patch stride (2)
        K: GPT2 layers for forecasting LLM (6 for National, 4 for Regional)
        lora_r: LoRA rank (4)
        D: hidden dim (768)
        device: torch device
    """

    def __init__(
        self, N=CONFIG["N"], T=CONFIG["T"], L=CONFIG["L_list"][0],
        Lp=CONFIG["Lp"], S=CONFIG["S"], K=CONFIG["K"], lora_r=CONFIG["lora_r"],
        D=CONFIG["D"], device="cpu", use_text_ln=True, use_lora=True,
        gated_inject=False, unfreeze_first_k=0, flatten_head=True,
        author_faithful=True, use_text=True
    ):
        super().__init__()
        self.flatten_head = flatten_head
        self.author_faithful = author_faithful
        self.N = N
        self.T = T
        self.L = L
        self.device = device

        # ── Time-Series Embedder ──
        self.time_embedder = TimeSeriesEmbedder(N=N, T=T, Lp=Lp, S=S, D=D)
        total_patches = self.time_embedder.total_patches

        # ── Forecasting LLM ──
        self.forecasting_llm = ForecastingLLM(
            K=K, D=D, lora_r=lora_r, L=L, N=N, total_patches=total_patches,
            use_text_ln=use_text_ln, use_lora=use_lora,
            gated_inject=gated_inject, unfreeze_first_k=unfreeze_first_k,
            flatten_head=flatten_head,
            author_faithful=author_faithful, use_text=use_text
        )

        self.to(device)

    def forward(self, x, htext, means=None, stdevs=None,
                 train_mean=None, train_std=None):
        """
        Forward pass.

        Args:
            x: time-series input (batch, N, T)  — ALREADY in StandardScaler space
            htext: pre-computed text embeddings (batch, text_tokens, D)
            means: instance norm means (or None)
            stdevs: instance norm stdevs (or None)
            train_mean: GLOBAL train mean (1, N) for inverse StandardScaler -> physical
            train_std:  GLOBAL train std  (1, N) for inverse StandardScaler -> physical

        Returns:
            y_hat_rev: predictions in StandardScaler space (batch, N, L)
                       = Inverse RevIN (y_hat_norm * inst_std + inst_mean).
                       THIS is the target space for loss & Table V metrics
                       (Section V-B: metrics computed on StandardScaler-normalized data).
            y_phys:    predictions in physical space (batch, N, L),
                       = y_hat_rev * train_std + train_mean, clamped at >= 0.
                       ONLY for Q1 figures / physical CSV.
            means, stdevs: for reversible instance norm (diagnostics)
        """
        # Time-series embedding
        htime, means, stdevs = self.time_embedder(x, means, stdevs)

        # If no text embeddings provided, use zeros with matching batch size
        bsz = htime.shape[0]
        if htext is None:
            htext = torch.zeros(bsz, 1, htime.shape[-1], device=htime.device)
        elif htext.shape[0] == 1 and bsz > 1:
            # Expand single prompt to match batch
            htext = htext.expand(bsz, -1, -1)

        # Forecasting LLM
        y_hat_norm = self.forecasting_llm(htime, htext)  # in instance-norm space

        # ── Reverse Instance Normalization (RevIN) ──
        # Convert predictions from instance-norm space back to StandardScaler space.
        # This is the canonical prediction space: metrics & loss live here.
        # means/stdevs shape: (batch, N, 1), y_hat_norm shape: (batch, N, L)
        y_hat_rev = y_hat_norm * stdevs + means

        # ── Inverse StandardScaler -> physical space (for figures / CSV only) ──
        if train_mean is not None and train_std is not None:
            # Accept (N,) or (1,N) or (1,N,1); reshape to (1,N,1) for broadcast over (B,N,L)
            tm = train_mean.to(y_hat_rev.device, y_hat_rev.dtype).view(1, -1, 1)
            ts = train_std.to(y_hat_rev.device, y_hat_rev.dtype).view(1, -1, 1)
            y_phys = y_hat_rev * ts + tm
            y_phys = torch.clamp(y_phys, min=0.0)   # ILI counts cannot be negative
        else:
            y_phys = y_hat_rev

        return y_hat_rev, y_phys, means, stdevs

    def count_parameters(self):
        """Count trainable vs total parameters."""
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        print(f"[MIFlu] Total params: {total:,}")
        print(f"[MIFlu] Trainable params: {trainable:,} ({trainable/total*100:.2f}%)")
        return total, trainable


# ═══════════════════════════════════════════════════════════════════════════
# Test
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[TEST] Device: {device}")
    print()

    # ── Step 3: Time-Series Embedder test ──
    print("=" * 60)
    print("STEP 3: Time-Series Input Embedder")
    print("=" * 60)
    ts_embedder = TimeSeriesEmbedder(N=7, T=104, Lp=24, S=2, D=768).to(device)

    # Dummy input: (batch=2, N=7, T=104)
    x_dummy = torch.randn(2, 7, 104, device=device)
    htime, means, stdevs = ts_embedder(x_dummy)

    num_patches = (104 - 24) // 2 + 2  # = 42
    expected = (2, 7 * num_patches, 768)
    print(f"x     shape: {x_dummy.shape}   expected: (2, 7, 104)")
    print(f"htime shape: {htime.shape}   expected: {expected}")
    print(f"means shape: {means.shape}   expected: (2, 7, 1)")
    assert htime.shape == expected, f"Shape mismatch! {htime.shape} != {expected}"
    print("[PASS] Time-Series Embedder shapes correct.\n")

    # ── Step 4: Forecasting LLM test ──
    print("=" * 60)
    print("STEP 4: Forecasting LLM with LoRA")
    print("=" * 60)
    total_patches = ts_embedder.total_patches
    fllm = ForecastingLLM(K=6, D=768, lora_r=4, L=24, N=7, total_patches=total_patches).to(device)

    # Dummy text embeddings
    htext_dummy = torch.randn(2, 367, 768, device=device)

    y_hat = fllm(htime, htext_dummy)
    print(f"y_hat shape: {y_hat.shape}   expected: (2, 7, 24)")
    assert y_hat.shape == (2, 7, 24), f"Shape mismatch! {y_hat.shape} != (2, 7, 24)"
    print("[PASS] Forecasting LLM shapes correct.\n")

    # ── Full MIFlu test ──
    print("=" * 60)
    print("FULL MIFlu MODEL")
    print("=" * 60)
    model = MIFlu(N=7, T=104, L=24, Lp=24, S=2, K=6, lora_r=4, device=device)
    model.count_parameters()

    y_hat, y_phys, means, stdevs = model(x_dummy, htext_dummy)
    print(f"y_hat shape: {y_hat.shape}   expected: (2, 7, 24)")
    assert y_hat.shape == (2, 7, 24)
    print("\n[PASS] Full MIFlu model forward pass successful!")
    print("[DONE] Steps 3 & 4 implemented.")
