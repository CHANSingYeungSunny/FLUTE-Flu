"""
a0_compat — MINIMAL, DOCUMENTED compatibility layer for replaying the author's
released MIFlu code (A0) on the current `mlflu_hpc` environment.

WHY THIS EXISTS
---------------
`models/GPT4TS_lora.py` (released commit 6ed2101) fails to import on this stack
for three reasons, all of which are **import-time only**:

  B1  `from einops import rearrange`                         (einops not installed)
  B2  `from embed import DataEmbedding, DataEmbedding_wo_time`
                                                            (embed.py absent from
                                                             the released tree; only
                                                             __pycache__/embed.cpython-39.pyc
                                                             survives, and a lone
                                                             __pycache__ pyc is not
                                                             importable in Python 3)
  B3  `from peft import prepare_model_for_int8_training`     (removed in peft 0.17.1)

PROVABLY NON-BEHAVIOURAL
------------------------
Each blocked name is DEAD in the released execution path:

  * `rearrange` IS used, so `einops.rearrange` is provided as a real
    implementation of exactly the three patterns the file uses
    ('b l m -> b m l', 'b m n p -> (b m) n p', '(b m) l -> b l m').
    This one DOES affect behaviour, so it is implemented, not stubbed.
  * `DataEmbedding` / `DataEmbedding_wo_time` are imported at line 10 and then
    NEVER referenced. The real input projection is `nn.Linear(patch_size,
    d_model)` (line 92) and the head is `nn.Linear(d_model*patch_num, pred_len)`
    (line 93). The class bodies below therefore only need to exist.
  * `prepare_model_for_int8_training` is referenced ONLY inside a comment
    (line 85: `# self.llmmodel = prepare_model_for_int8_training(self.llmmodel)`),
    and `configs.PEFT` defaults to 0 so the whole LoRA branch (lines 74-90) is
    skipped. A no-op callable is sufficient.

Any number produced under this layer must be labelled
"A0 diagnostic replay under a recorded compatibility layer" and must NOT be
presented as an exact reproduction of the paper. The layer is kept OUT of the
author's tree: it is placed on sys.path ahead of it, so the released files
themselves are byte-for-byte untouched.
"""
import math

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils import weight_norm

__all__ = ["rearrange", "DataEmbedding", "DataEmbedding_wo_pos",
           "DataEmbedding_wo_time", "PositionalEmbedding", "TokenEmbedding",
           "FixedEmbedding", "TemporalEmbedding", "TimeFeatureEmbedding"]


# ── einops.rearrange — only the three patterns GPT4TS_lora.py uses ──────────
def rearrange(tensor, pattern, **axes):
    """Permute/reshape for the exact subset of einops patterns used by the
    released model. Raises on any other pattern so a silent wrong-permutation
    can never masquerade as a faithful run."""
    if pattern == "b l m -> b m l":
        return tensor.permute(0, 2, 1)
    if pattern == "b m n p -> (b m) n p":
        b, m, n, p = tensor.shape
        return tensor.reshape(b * m, n, p)
    if pattern == "(b m) l -> b l m":
        b = axes.get("b")
        m = axes.get("m")
        if b is None:
            raise ValueError("rearrange '(b m) l -> b l m' needs b=<batch>")
        bm, l = tensor.shape
        if bm % b:
            raise ValueError(f"cannot split {bm} into (b={b}, m)")
        # einops infers the unnamed factor; the released code passes only b=B.
        m = (bm // b) if m is None else m
        if (b * m) != bm:
            raise ValueError(f"b*m={b*m} != leading dim {bm}")
        return tensor.reshape(b, m, l).permute(0, 2, 1)
    if pattern == "b l m -> b m l" or pattern == "b ... -> b ...":
        raise NotImplementedError(pattern)
    raise NotImplementedError(
        f"a0_compat.rearrange implements only the 3 patterns used by the "
        f"released GPT4TS_lora.py; got {pattern!r}")


# ── embed.py reconstructions (structure recovered from the author's own
#    __pycache__/embed.cpython-39.pyc: class/def inventory, argnames, co_names
#    and co_consts all match). Bodies below follow the disassembly. ──────────
class PositionalEmbedding(nn.Module):
    def __init__(self, d_model, max_len):
        super().__init__()
        pe = torch.zeros(max_len, d_model).float()
        pe.require_grad = False
        position = torch.arange(0, max_len).float().unsqueeze(1)
        div_term = (torch.arange(0, d_model, 2).float()
                    * -(math.log(10000.0) / d_model)).exp()
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        return self.pe[:, :x.size(1)]


class TokenEmbedding(nn.Module):
    def __init__(self, c_in, d_model):
        super().__init__()
        padding = 1 if torch.__version__ >= '1.5.0' else 2
        self.tokenConv = nn.Conv1d(in_channels=c_in, out_channels=d_model,
                                   kernel_size=3, padding=padding,
                                   padding_mode='circular', bias=False)
        for m in self.modules():
            if isinstance(m, nn.Conv1d):
                nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='leaky_relu')

    def forward(self, x):
        return self.tokenConv(x.permute(0, 2, 1)).transpose(1, 2)


class FixedEmbedding(nn.Module):
    def __init__(self, c_in, d_model):
        super().__init__()
        w = torch.zeros(c_in, d_model).float()
        w.require_grad = False
        position = torch.arange(0, c_in).float().unsqueeze(1)
        div_term = (torch.arange(0, d_model, 2).float()
                    * -(math.log(10000.0) / d_model)).exp()
        w[:, 0::2] = torch.sin(position * div_term)
        w[:, 1::2] = torch.cos(position * div_term)
        self.emb = nn.Parameter(w, requires_grad=False)

    def forward(self, x):
        return self.emb[x]


class TemporalEmbedding(nn.Module):
    def __init__(self, d_model, embed_type, freq):
        super().__init__()
        minute_size, hour_size = 4, 24
        weekday_size, day_size, month_size = 7, 32, 13
        MinuteEmbedding = nn.Embedding(minute_size, d_model)
        HourEmbedding = nn.Embedding(hour_size, d_model)
        WeekdayEmbedding = nn.Embedding(weekday_size, d_model)
        DayEmbedding = nn.Embedding(day_size, d_model)
        MonthEmbedding = nn.Embedding(month_size, d_model)
        self.embed = nn.ModuleList([MinuteEmbedding, HourEmbedding,
                                    WeekdayEmbedding, DayEmbedding, MonthEmbedding])

    def forward(self, x):
        x = x.long()
        minute_x = self.embed[0](x[:, :, 4])
        hour_x = self.embed[1](x[:, :, 3])
        weekday_x = self.embed[2](x[:, :, 2])
        day_x = self.embed[3](x[:, :, 1])
        month_x = self.embed[4](x[:, :, 0])
        return hour_x + weekday_x + day_x + month_x + minute_x


class TimeFeatureEmbedding(nn.Module):
    def __init__(self, d_model, embed_type, freq):
        super().__init__()
        freq_map = {'h': 4, 't': 5, 's': 6, 'm': 1, 'a': 1, 'w': 2, 'd': 3, 'b': 3}
        d_inp = freq_map[freq]
        self.embed = nn.Linear(d_inp, d_model, bias=False)

    def forward(self, x):
        return self.embed(x)


class DataEmbedding(nn.Module):
    def __init__(self, c_in, d_model, embed_type='fixed', freq='h', dropout=0.1):
        super().__init__()
        self.value_embedding = (TokenEmbedding(c_in, d_model) if c_in > 1
                                else FixedEmbedding(c_in, d_model))
        self.position_embedding = PositionalEmbedding(d_model, d_model)
        self.temporal_embedding = (TemporalEmbedding(d_model, embed_type, freq)
                                   if embed_type != 'timeF'
                                   else TimeFeatureEmbedding(d_model, embed_type, freq))
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, x, x_mark):
        x = self.value_embedding(x) + self.position_embedding(x)
        x = x + self.temporal_embedding(x_mark)
        return self.dropout(x)


class DataEmbedding_wo_pos(nn.Module):
    def __init__(self, c_in, d_model, embed_type='fixed', freq='h', dropout=0.1):
        super().__init__()
        self.value_embedding = (TokenEmbedding(c_in, d_model) if c_in > 1
                                else FixedEmbedding(c_in, d_model))
        self.temporal_embedding = (TemporalEmbedding(d_model, embed_type, freq)
                                   if embed_type != 'timeF'
                                   else TimeFeatureEmbedding(d_model, embed_type, freq))
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, x, x_mark):
        x = self.value_embedding(x)
        x = x + self.temporal_embedding(x_mark)
        return self.dropout(x)


class DataEmbedding_wo_time(nn.Module):
    def __init__(self, c_in, d_model, embed_type='fixed', freq='h', dropout=0.1):
        super().__init__()
        self.value_embedding = (TokenEmbedding(c_in, d_model) if c_in > 1
                                else FixedEmbedding(c_in, d_model))
        self.position_embedding = PositionalEmbedding(d_model, d_model)
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, x):
        x = self.value_embedding(x) + self.position_embedding(x)
        return self.dropout(x)


# ── peft compatibility no-ops (dead-import shims) ──────────────────────────
def prepare_model_for_int8_training(model, *a, **k):
    """peft>=0.8 removed this symbol. The released code calls it only inside a
    comment and only under `PEFT == 1` (default 0). No-op keeps the import
    valid and provably cannot change the released execution path."""
    return model
