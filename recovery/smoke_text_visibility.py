# -*- coding: utf-8 -*-
"""Deterministic CPU smoke check for the text-visibility finding (Stage 2).

Author code path (models/GPT4TS_lora.py):
  1. time-series patches -> in_layer -> [B, patch_num, d_model]          (outputs)
  2. if multimodal: outputs = cat((outputs, text_emb), axis=1)            (text APPENDED after patches)
  3. outputs = gpt2_causal(inputs_embeds=outputs).last_hidden_state        (CAUSAL attention)
  4. outputs = outputs[:, :patch_num, :]                                  (only PREFIX retained)

Under causal attention, position i attends only to positions <= i. Text tokens occupy
positions patch_num..(patch_num+K-1), which are all > any retained patch position
(0..patch_num-1). Therefore the retained prefix cannot depend on the text.

This script reproduces that mechanism with a tiny single-head causal attention module
(fixed weights, identical time-series inputs, two different text tokens) and asserts the
retained prefix is bit-identical. CPU-only, no downloads, no GPU.
"""
import torch
import torch.nn as nn

torch.manual_seed(0)

N = 42          # patch_num
K = 4           # text token count
D = 16          # model dim
B = 2           # batch


class TinyCausal(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.wq = nn.Linear(d, d, bias=False)
        self.wk = nn.Linear(d, d, bias=False)
        self.wv = nn.Linear(d, d, bias=False)

    def forward(self, x):
        # x: [B, T, D]
        q, k, v = self.wq(x), self.wk(x), self.wv(x)
        scale = D ** -0.5
        attn = (q @ k.transpose(-2, -1)) * scale          # [B, T, T]
        T = x.size(1)
        mask = torch.triu(torch.ones(T, T, dtype=torch.bool), diagonal=1)
        attn = attn.masked_fill(mask, float("-inf"))
        attn = torch.softmax(attn, dim=-1)
        return attn @ v


model = TinyCausal(D).eval()
for p in model.parameters():
    p.requires_grad = False

# identical time-series patches
patches = torch.randn(B, N, D)

# two clearly different text token embeddings
text_a = torch.randn(B, K, D) * 10.0 + 100.0
text_b = torch.randn(B, K, D) * 10.0 - 100.0

with torch.no_grad():
    out_a = model(torch.cat([patches, text_a], dim=1))[:, :N, :]
    out_b = model(torch.cat([patches, text_b], dim=1))[:, :N, :]

diff = (out_a - out_b).abs().max().item()
print(f"max |retained-prefix difference| between text A and text B = {diff:.3e}")

assert diff == 0.0, "prefix NOT invariant to text -> text-visibility finding refuted"
print("CONFIRMED: text appended after patches has zero influence on retained prefix.")
