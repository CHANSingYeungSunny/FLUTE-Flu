"""
classic_nn.py — classical deep-forecasting baselines (non-LLM).
===============================================================

Five generic neural baseline families, all **channel-independent with shared
weights** (the same convention as `DLinear(individual=False)`), so that they are
directly comparable with the other non-LLM backbones under the identical A2
protocol (`build_windows` / strict containment / 20 epochs / val-selected
checkpoint):

  * DNN  — per-channel MLP  T -> hidden -> hidden -> L
  * CNN  — per-channel 1-D convolutions over time, global average pooling, -> L
  * RNN  — per-channel vanilla RNN, last hidden state -> L
  * LSTM — per-channel LSTM, last hidden state -> L
  * GRU  — per-channel GRU, last hidden state -> L

FIDELITY
--------
None of these is a specific published paper architecture; they are standard
baseline families. Every class therefore declares
`INSPIRED_SIMPLIFICATION` and states its capacity in `architecture_report()`.
That prevents the failure mode that broke PatchTST earlier (a silently
reduced-capacity variant being compared against full-scale models as if it were
the published method).

Contract (see `innovation/interfaces.py`):
    forward(x: (B, N, T)) -> (B, N, L), both in the global train-fitted z-space.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from innovation import fidelity as FID
from innovation.interfaces import ForecastBackbone


class _ChannelIndependent(ForecastBackbone):
    """Applies a shared per-channel module to every variable independently."""

    def __init__(self, T: int, N: int, L: int):
        super().__init__()
        self.T, self.N, self.L = int(T), int(N), int(L)

    def _run(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError

    def forward(self, x: torch.Tensor, ctx: torch.Tensor | None = None) -> torch.Tensor:
        B, N, T = x.shape
        # (B, N, T) -> (B*N, 1, T): one series per row, weights shared across channels
        flat = x.reshape(B * N, 1, T)
        out = self._run(flat)                      # (B*N, L)
        return out.reshape(B, N, self.L)

    def architecture_report(self) -> dict:
        raise NotImplementedError


class DNN(_ChannelIndependent):
    """Per-channel MLP: flatten T -> two hidden layers -> L."""

    name = "dnn"

    def __init__(self, T: int, N: int, L: int, hidden: int = 128):
        super().__init__(T, N, L)
        self.hidden = int(hidden)
        self.net = nn.Sequential(
            nn.Flatten(start_dim=1),
            nn.Linear(self.T, self.hidden), nn.ReLU(),
            nn.Linear(self.hidden, self.hidden), nn.ReLU(),
            nn.Linear(self.hidden, self.L),
        )

    def _run(self, x):
        return self.net(x)

    def architecture_report(self):
        return {
            "name": self.name,
            "display_name": "DNN (multi-layer perceptron baseline)",
            "published": "generic baseline family (no specific paper architecture)",
            "fidelity": FID.INSPIRED_SIMPLIFICATION,
            "hidden": self.hidden,
            "channel_independent": True,
            "evidence": [
                "backbones/classic_nn.py DNN: Flatten -> Linear(T,hidden) -> ReLU -> "
                "Linear(hidden,hidden) -> ReLU -> Linear(hidden,L)",
                "backbones/classic_nn.py _ChannelIndependent.forward: (B,N,T) -> "
                "(B*N,1,T) so weights are shared across channels",
            ],
            "deviations": [
                "not a published architecture: a standard MLP baseline",
                f"capacity fixed at hidden={self.hidden} (no hyper-parameter search)",
                "no variable-specific parameters (channel-independent) to match DLinear",
            ],
            "notes": "Generic MLP baseline. Compare only as a baseline family, "
                     "never as a reproduction of a paper.",
        }


class CNN(_ChannelIndependent):
    """Per-channel 1-D convolutions over time + global average pooling -> L."""

    name = "cnn"

    def __init__(self, T: int, N: int, L: int, channels: int = 64,
                 kernel: int = 5):
        super().__init__(T, N, L)
        self.channels, self.kernel = int(channels), int(kernel)
        pad = self.kernel // 2
        self.net = nn.Sequential(
            nn.Conv1d(1, self.channels, self.kernel, padding=pad), nn.ReLU(),
            nn.Conv1d(self.channels, self.channels, self.kernel, padding=pad), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(start_dim=1),
            nn.Linear(self.channels, self.L),
        )

    def _run(self, x):
        return self.net(x)

    def architecture_report(self):
        return {
            "name": self.name,
            "display_name": "CNN (1-D convolutional baseline)",
            "published": "generic baseline family (no specific paper architecture)",
            "fidelity": FID.INSPIRED_SIMPLIFICATION,
            "channels": self.channels,
            "kernel": self.kernel,
            "channel_independent": True,
            "evidence": [
                "backbones/classic_nn.py CNN: Conv1d(1,channels,k) x2 with ReLU, "
                "AdaptiveAvgPool1d(1), Linear(channels, L)",
                "backbones/classic_nn.py _ChannelIndependent.forward: shared weights",
            ],
            "deviations": [
                "not a published architecture: a standard 1-D CNN baseline",
                "global average pooling discards temporal position before the head",
                f"capacity fixed at channels={self.channels}, kernel={self.kernel}",
            ],
            "notes": "Generic CNN baseline, channel-independent.",
        }


class _Recurrent(_ChannelIndependent):
    """Shared scaffolding for RNN / LSTM / GRU last-hidden-state baselines."""

    rnn_cls: type = nn.RNN
    kind = "rnn"

    def __init__(self, T: int, N: int, L: int, hidden: int = 64, layers: int = 1):
        super().__init__(T, N, L)
        self.hidden, self.layers = int(hidden), int(layers)
        self.rnn = self.rnn_cls(1, self.hidden,
                                num_layers=self.layers, batch_first=True)
        # input size is 1 because each row is a single channel's series
        self.head = nn.Linear(self.hidden, self.L)

    def _run(self, x):
        # x: (B*N, 1, T); recurrent nets expect (batch, seq, feature)
        seq = x.transpose(1, 2)                    # (B*N, T, 1)
        out, _ = self.rnn(seq)                     # (B*N, T, hidden)
        return self.head(out[:, -1, :])            # last time step -> (B*N, L)

    def architecture_report(self):
        return {
            "name": self.name,
            "display_name": f"{self.kind.upper()} (recurrent baseline)",
            "published": "generic baseline family (no specific paper architecture)",
            "fidelity": FID.INSPIRED_SIMPLIFICATION,
            "hidden": self.hidden,
            "layers": self.layers,
            "channel_independent": True,
            "evidence": [
                f"backbones/classic_nn.py {self.__class__.__name__}: "
                f"{self.kind.upper()}(input=1, hidden={self.hidden}, "
                f"layers={self.layers}), last hidden state -> Linear(hidden, L)",
                "backbones/classic_nn.py _ChannelIndependent.forward: shared weights",
            ],
            "deviations": [
                "not a published architecture: a standard recurrent baseline",
                "uses only the final hidden state (no attention pooling)",
                f"capacity fixed at hidden={self.hidden}, layers={self.layers}",
            ],
            "notes": "Generic recurrent baseline, channel-independent.",
        }


class RNN(_Recurrent):
    name = "rnn"
    kind = "rnn"
    rnn_cls = nn.RNN


class LSTM(_Recurrent):
    name = "lstm"
    kind = "lstm"
    rnn_cls = nn.LSTM


class GRU(_Recurrent):
    name = "gru"
    kind = "gru"
    rnn_cls = nn.GRU
