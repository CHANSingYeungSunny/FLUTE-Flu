"""none_encoder.py — the "no text" TextEncoder (always available)."""

from __future__ import annotations

from innovation.interfaces import TextEncoder


class NoneTextEncoder(TextEncoder):
    name = "none"
    availability_note = "no text by construction"

    def is_available(self) -> bool:
        return True

    def fit_on_train_only(self, train_df, horizon: int, seed: int) -> None:
        return None

    def encode(self, batch_size: int, device: str = "cpu", horizon: int | None = None):
        return None

    def context_dim(self):
        return None
