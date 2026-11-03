"""encoders — text encoder registry (availability-aware)."""

from __future__ import annotations

_ENCODERS: dict[str, dict] = {}


def register_encoder(name: str, factory, note: str = "") -> None:
    _ENCODERS[name] = {"factory": factory, "note": note}


def get_encoder(name: str):
    if name not in _ENCODERS:
        raise KeyError(f"unknown encoder {name!r}; known: {sorted(_ENCODERS)}")
    return _ENCODERS[name]["factory"]


def make_encoder(name: str, **kwargs):
    return get_encoder(name)(**kwargs)


def list_encoders() -> list[str]:
    return sorted(_ENCODERS)


def available_encoders() -> dict:
    out = {}
    for k, v in _ENCODERS.items():
        try:
            out[k] = {"available": bool(v["factory"]().is_available()),
                      "note": v["note"]}
        except Exception as e:  # pragma: no cover
            out[k] = {"available": False, "note": f"probe failed: {e}"}
    return out
