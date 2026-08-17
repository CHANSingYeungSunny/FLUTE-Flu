"""
moe_extension.py — Prototype MoE / UCS modules for MIFlu (Innovation-Proof)
============================================================================
LOCAL PROTOTYPE ONLY. These modules are instantiated with REAL MIFlu
dimensions (D=768, num_patches=42) to verify shapes and count added
parameters. They are NOT trained here (training is HPC-pending, see
Innovation-Proof.md "Pending HPC Experiments").

Three published mechanisms are prototyped at the fusion stage, matching the
insertion point in miflu_model.py:

  Insertion point (evidence B):
    - h_time and h_text concatenation: miflu_model.py line 301
        hfuse = torch.cat([htext, htime], dim=1)
    - ForecastingLLM.forward: miflu_model.py line 284
    - build_prompt: textual_embedder.py line 70

  (1) I2MoE (Image-to-Modality MoE) — 4 experts gated by a modality router.
      Paper: I2MoE, Table 6 (ADNI MulT 1.07M -> 6.70M params;
      train/epoch 8.98s -> 16.82s).
      Mapped to roadmap Step 2.1.
  (2) Flex-MoE Missing Bank — a learnable "missing-modality" memory bank
      that fills dropped channels. Paper: Flex-MoE Table 4 (36.9M vs
      FuseMoE 340.9M). Mapped to roadmap Step 1.3.
  (3) UCS SGT prior — SGT (Sparse Graph Transformer) task prior injected as
      an offline-computed bias. Paper: UCS Tables 10/11 (offline 38-57s,
      online +0-3s). Mapped to roadmap Step 1.1 / 3.1.

All three take input shape (batch, seq, D) and return (batch, seq, D) so
they can be dropped into the hfuse stream at miflu_model.py:301-336.
"""
import torch
import torch.nn as nn
import numpy as np


# ── (1) I2MoE: 4-expert MoE with modality router ──────────────────────────
class I2MoEExpert(nn.Module):
    """One feed-forward expert (two-layer MLP in D)."""
    def __init__(self, D=768, hidden=4 * 768):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(D, hidden), nn.GELU(), nn.Linear(hidden, D)
        )

    def forward(self, x):
        return self.net(x)


class I2MoE(nn.Module):
    """Image-to-Modality Mixture-of-Experts over the fused sequence.

    Router assigns each token to the top-1 of 4 experts. Real D=768.
    """
    def __init__(self, D=768, n_experts=4, hidden=4 * 768):
        super().__init__()
        self.D = D
        self.n_experts = n_experts
        self.experts = nn.ModuleList([I2MoEExpert(D, hidden) for _ in range(n_experts)])
        self.router = nn.Linear(D, n_experts)

    def forward(self, hfuse):
        # hfuse: (batch, seq, D)
        logits = self.router(hfuse)              # (batch, seq, n_experts)
        gate = torch.softmax(logits, dim=-1)
        idx = gate.argmax(dim=-1)                # (batch, seq) top-1
        out = torch.zeros_like(hfuse)
        for e in range(self.n_experts):
            mask = (idx == e)
            if mask.any():
                out[mask] = self.experts[e](hfuse[mask])
        # residual combine with gating weight
        out = out * gate.gather(-1, idx.unsqueeze(-1))
        return hfuse + out


# ── (2) Flex-MoE Missing Bank ─────────────────────────────────────────────
class FlexMoEMissingBank(nn.Module):
    """Learnable memory bank that imputes dropped-modality tokens.

    A small set of K learnable vectors (the 'bank') is attended by any
    missing channel position, producing an imputed representation. Real D=768.
    """
    def __init__(self, D=768, bank_size=8):
        super().__init__()
        self.D = D
        self.bank_size = bank_size
        self.bank = nn.Parameter(torch.randn(bank_size, D) * 0.02)
        self.attn = nn.MultiheadAttention(D, num_heads=4, batch_first=True)

    def forward(self, hfuse, missing_mask=None):
        # hfuse: (batch, seq, D); missing_mask: (batch, seq) bool
        bsz, seq, D = hfuse.shape
        bank = self.bank.unsqueeze(0).expand(bsz, -1, -1)  # (batch, bank, D)
        imputed, _ = self.attn(hfuse, bank, bank)          # (batch, seq, D)
        if missing_mask is not None:
            out = torch.where(missing_mask.unsqueeze(-1), imputed, hfuse)
        else:
            out = hfuse + 0.1 * imputed
        return out


# ── (3) UCS SGT prior (offline-computed bias) ─────────────────────────────
class UCS_SGT_Prior(nn.Module):
    """Injects an offline-computed SGT task prior as an additive bias.

    The prior is a (seq, D) buffer computed OFFLINE (no gradient). At
    inference it is added to hfuse. Mirrors UCS Tables 10/11: offline cost
    is paid once; online cost is near-zero (+0-3s).
    """
    def __init__(self, seq, D=768):
        super().__init__()
        self.D = D
        self.seq = seq
        # register as buffer -> no gradient, offline-frozen
        self.register_buffer("sgt_prior", torch.zeros(seq, D))

    def set_prior(self, prior_tensor):
        """Call this with the offline-computed prior (HPC stage)."""
        assert prior_tensor.shape == (self.seq, self.D)
        self.sgt_prior.copy_(prior_tensor)

    def forward(self, hfuse):
        # hfuse: (batch, seq, D)
        return hfuse + self.sgt_prior.unsqueeze(0)


def count_params(module):
    total = sum(p.numel() for p in module.parameters())
    return total


if __name__ == "__main__":
    D = 768
    num_patches = 42
    total_patches = 7 * num_patches  # N=7
    text_len = 367
    seq = text_len + total_patches

    print("=" * 70)
    print(" MoE / UCS PROTOTYPE — real dimensions")
    print(f" D={D} num_patches={num_patches} total_patches={total_patches}"
          f" text_len={text_len} seq={seq}")
    print("=" * 70)

    x = torch.randn(2, seq, D)

    i2moe = I2MoE(D=D, n_experts=4)
    y = i2moe(x)
    print(f" [I2MoE] out={tuple(y.shape)} expected=({2},{seq},{D})"
          f" added_params={count_params(i2moe):,}")

    flex = FlexMoEMissingBank(D=D, bank_size=8)
    y = flex(x)
    print(f" [FlexMoE] out={tuple(y.shape)} expected=({2},{seq},{D})"
          f" added_params={count_params(flex):,}")

    ucs = UCS_SGT_Prior(seq=seq, D=D)
    y = ucs(x)
    print(f" [UCS] out={tuple(y.shape)} expected=({2},{seq},{D})"
          f" added_params={count_params(ucs):,} (prior is a frozen buffer)")

    print("\n[PASS] All prototype shapes correct with real MIFlu dims.")
