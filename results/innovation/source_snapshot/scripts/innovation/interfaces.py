"""
interfaces.py — unified plugin contracts for the innovation experiments.
=========================================================================

Three swappable components are defined, so that text encoder / forecast
backbone / fusion module are recorded SEPARATELY (scientific constraint #1):

  * ForecastBackbone : x (B,N,T) z-space  ->  y_hat (B,N,L) z-space
  * TextEncoder      : prompt / train-only stats -> htext (B,K,D) or None
  * FusionModule     : htime (B,P,D), htext -> fused (B,P,D)

Contracts are intentionally small. Non-text backbones simply ignore `ctx`; the
"none" text encoder returns None; the "identity" fusion returns htime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import torch
import torch.nn as nn


class ForecastBackbone(nn.Module, ABC):
    """Base class for every forecast backbone.

    Contract
    --------
    forward(x, ctx=None) -> y_hat
        x    : (B, N, T) float tensor in the GLOBAL z-space produced by the
               train-fitted scaler (same space as the existing MIFlu pipeline).
        ctx  : optional text context (B, K, D) or None.
        y_hat: (B, N, L) in the SAME global z-space, so physical units are
               recovered with `z * scaler.scale_ + scaler.mean_`.
    """

    name: str = "abstract"

    @abstractmethod
    def forward(self, x: torch.Tensor, ctx: torch.Tensor | None = None) -> torch.Tensor:
        raise NotImplementedError

    def trainable_parameters(self) -> int:
        return int(sum(p.numel() for p in self.parameters() if p.requires_grad))

    def total_parameters(self) -> int:
        return int(sum(p.numel() for p in self.parameters()))


class TextEncoder(ABC):
    """Base class for a text encoder producing an optional context tensor.

    Contract
    --------
    is_available()        -> bool     : False => UNAVAILABLE_LOCAL_DEPENDENCY
    fit_on_train_only()   -> None     : may only see TRAIN data (leakage gate)
    encode()              -> Tensor|None : (B, K, D) or None when no text
    """

    name: str = "abstract"
    availability_note: str = ""

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def fit_on_train_only(self, train_df, horizon: int, seed: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def encode(self, batch_size: int, device: str = "cpu"):
        raise NotImplementedError

    def context_dim(self) -> int | None:
        return None

    def describe(self) -> dict:
        return {"name": self.name, "available": bool(self.is_available()),
                "note": self.availability_note}


class FusionModule(nn.Module, ABC):
    """Combines a time representation with a text context.

    Contract
    --------
    forward(htime, htext) -> fused
        htime : (B, P, D)
        htext : (B, K, D) or None
        fused : (B, P, D)   (identity when htext is None)
    """

    name: str = "abstract"

    @abstractmethod
    def forward(self, htime: torch.Tensor, htext: torch.Tensor | None) -> torch.Tensor:
        raise NotImplementedError
