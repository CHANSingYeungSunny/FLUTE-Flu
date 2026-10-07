"""fusion — fusion module registry."""

from __future__ import annotations

_FUSIONS: dict[str, dict] = {}


def register_fusion(name: str, factory, note: str = "") -> None:
    _FUSIONS[name] = {"factory": factory, "note": note}


def get_fusion(name: str):
    if name not in _FUSIONS:
        raise KeyError(f"unknown fusion {name!r}; known: {sorted(_FUSIONS)}")
    return _FUSIONS[name]["factory"]


def make_fusion(name: str, **kwargs):
    return get_fusion(name)(**kwargs)


def list_fusions() -> list[str]:
    return sorted(_FUSIONS)


def available_fusions() -> dict:
    return {k: {"note": v["note"]} for k, v in _FUSIONS.items()}
