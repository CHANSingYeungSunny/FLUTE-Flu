"""
registry.py — backbone registry (lazy, availability-aware).
===========================================================

Registration is lazy: importing this module does not import torch models of
candidate backbones. `UNAVAILABLE_LOCAL_DEPENDENCY` is recorded for anything
that cannot be built locally (revision: never download, never fake).
"""

from __future__ import annotations

from innovation.paths import HORIZONS  # noqa: F401

_BACKBONES: dict[str, dict] = {}


def register_backbone(name: str, factory, note: str = "") -> None:
    _BACKBONES[name] = {"factory": factory, "note": note}


def get_backbone(name: str):
    if name not in _BACKBONES:
        raise KeyError(f"unknown backbone {name!r}; known: {sorted(_BACKBONES)}")
    return _BACKBONES[name]["factory"]


def make_backbone(name: str, **kwargs):
    return get_backbone(name)(**kwargs)


def list_backbones() -> list[str]:
    return sorted(_BACKBONES)


def available_backbones() -> dict:
    return {k: {"note": v["note"]} for k, v in _BACKBONES.items()}
