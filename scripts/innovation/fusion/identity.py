"""identity.py — the "no text" fusion: returns the time stream unchanged."""

from __future__ import annotations

from innovation.interfaces import FusionModule


class IdentityFusion(FusionModule):
    name = "identity"

    def forward(self, htime, htext=None):
        return htime
