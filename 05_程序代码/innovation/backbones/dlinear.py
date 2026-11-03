"""
dlinear.py — DLinear / NLinear (channel-agnostic or per-channel, non-text).
=========================================================================

ARCHITECTURE EQUIVALENCE
------------------------
Published reference: DLinear / NLinear (Zeng et al., "Are Transformers Effective
for Time Series Forecasting?", AAAI 2023).
  * DLinear : series decomposition (moving-average trend) + two linear maps
              T -> L (one over the seasonal part, one over the trend), summed.
  * NLinear : subtract the last observed value, one linear map T -> L, add back.
Both apply the linear map ALONG THE TIME AXIS and share weights across channels
(`individual=False`, the default), matching the paper's channel-agnostic design.
`architecture_report()` records the kernel size and `individual` choice; any
deviation is surfaced there rather than hidden.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from innovation import fidelity as FID
from innovation.interfaces import ForecastBackbone


class _MovingAvg(nn.Module):
    def __init__(self, kernel_size: int):
        super().__init__()
        self.kernel_size = int(kernel_size)
        self.avg = nn.AvgPool1d(kernel_size=self.kernel_size, stride=1)

    def forward(self, x):                       # x: (B, T, N) -> (B, T, N)
        pad = (self.kernel_size - 1) // 2
        front = x[:, :1, :].repeat(1, pad, 1)
        end = x[:, -1:, :].repeat(1, self.kernel_size - 1 - pad, 1)
        x = torch.cat([front, x, end], dim=1)
        return self.avg(x.permute(0, 2, 1)).permute(0, 2, 1)


class DLinear(ForecastBackbone):
    name = "dlinear"

    def __init__(self, T: int, N: int, L: int, kernel_size: int = 25,
                 individual: bool = False):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.individual = bool(individual)
        self.decomp = _MovingAvg(kernel_size)
        make = (lambda: nn.ModuleList([nn.Linear(T, L) for _ in range(N)])) \
            if self.individual else None
        if self.individual:
            self.lin_seasonal = make()
            self.lin_trend = make()
        else:
            self.lin_seasonal = nn.Linear(T, L)
            self.lin_trend = nn.Linear(T, L)

    def _decompose(self, x):                    # x: (B, N, T)
        seq = x.permute(0, 2, 1)                # (B, T, N)
        trend = self.decomp(seq).permute(0, 2, 1)   # (B, N, T)
        return x - trend, trend

    def forward(self, x, ctx=None):
        seasonal, trend = self._decompose(x)    # both (B, N, T)
        if self.individual:
            ys = torch.stack([self.lin_seasonal[i](seasonal[:, i, :])
                              for i in range(self.N)], dim=1)
            yt = torch.stack([self.lin_trend[i](trend[:, i, :])
                              for i in range(self.N)], dim=1)
        else:
            ys = self.lin_seasonal(seasonal)    # (B, N, L)
            yt = self.lin_trend(trend)
        return ys + yt

    def architecture_report(self) -> dict:
        """Component-level provenance vs Zeng et al., AAAI 2023 (DLinear)."""
        return {
            "name": self.name,
            "display_name": "DLinear (Zeng et al., AAAI 2023)",
            "published": "DLinear (Zeng et al., AAAI 2023)",
            "fidelity": FID.REFERENCE_FAITHFUL,
            "kernel_size": self.decomp.kernel_size,
            "individual": self.individual,
            "evidence": [
                "backbones/dlinear.py:26-37 moving-average decomposition (AvgPool1d stride 1, replication padding)",
                "backbones/dlinear.py:58-61 seasonal = x - trend",
                "backbones/dlinear.py:47-56 Linear(T->L) applied along the TIME axis, weights shared across channels (individual=False default)",
                "backbones/dlinear.py:43 kernel_size=25 (the paper default)",
            ],
            "deviations": [],
            "notes": ("moving-average decomposition + shared Linear(T->L) over "
                      "the time axis; weights shared across channels. No "
                      "material deviation."),
        }


class NLinear(ForecastBackbone):
    name = "nlinear"

    def __init__(self, T: int, N: int, L: int, individual: bool = False):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)
        self.individual = bool(individual)
        if self.individual:
            self.lin = nn.ModuleList([nn.Linear(T, L) for _ in range(N)])
        else:
            self.lin = nn.Linear(T, L)

    def forward(self, x, ctx=None):
        last = x[:, :, -1:]                     # (B, N, 1)
        s = x - last                            # (B, N, T)
        if self.individual:
            y = torch.stack([self.lin[i](s[:, i, :]) for i in range(self.N)],
                            dim=1)
        else:
            y = self.lin(s)                     # (B, N, L)
        return y + last

    def architecture_report(self) -> dict:
        """Component-level provenance vs Zeng et al., AAAI 2023 (NLinear)."""
        return {
            "name": self.name,
            "display_name": "NLinear (Zeng et al., AAAI 2023)",
            "published": "NLinear (Zeng et al., AAAI 2023)",
            "fidelity": FID.REFERENCE_FAITHFUL,
            "individual": self.individual,
            "evidence": [
                "backbones/dlinear.py:97-98 last = x[:, :, -1:] (last-value subtraction)",
                "backbones/dlinear.py:92-94 shared Linear(T->L) along the time axis",
                "backbones/dlinear.py:104 last value added back",
            ],
            "deviations": [],
            "notes": "last-value normalisation + shared Linear(T->L) over time. "
                     "No material deviation.",
        }
