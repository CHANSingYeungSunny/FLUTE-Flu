"""Authoritative model-asset descriptors for v3 (D5 asset-resolution repair).

Why this module exists
----------------------
The three new LLM branches load a frozen text backbone. Two deterministic
failures occurred when that backbone was resolved by *repository id*:

* the Qwen snapshot was downloaded with an explicit revision, so the hub cache
  contains the snapshot but no ``refs/main`` entry; a repo-id lookup with
  ``local_files_only=True`` therefore cannot resolve it and raises
  ``OSError ... couldn't find them in the cached files``;
* ``gpt2`` is already present in the v2 verified cache, so it only resolves
  while ``HF_HOME`` points at that cache.

The repair is to pass the **verified local snapshot directory** to
``from_pretrained`` with ``local_files_only=True`` and ``trust_remote_code``
left at ``False``, and to leave every other backbone to resolve normally.

Scope of the repair: asset resolution only. It does not change the dataset,
split, target formulation, scaler, prompt statistics, architecture-defining
mechanisms, dimensions, hyperparameters, training loss, early stopping,
metrics, fixed-step policy, model set, or search budget.

This module must never construct or load a model; it only describes assets.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

# ── Qwen2.5-1.5B (verified on the HPC cache, 2026-09-16) ────────────────────
QWEN = {
    "model_repo_id": "Qwen/Qwen2.5-1.5B",
    "model_revision": "8faed761d45a263340a0528343f099c05c9a4323",
    "local_snapshot_path": (
        "/gpfs1/scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B"
        "/snapshots/8faed761d45a263340a0528343f099c05c9a4323"),
    "local_files_only": True,
    "trust_remote_code": False,
    "license": "Apache-2.0",
    "gated": False,
    # file -> (bytes, sha256) measured on the compute/cache filesystem
    "files": {
        "config.json": (684,
                        "0e8c8aa86468aba09c9d32157ff4bc2301c7e6c50e4398960425b2ea71e66f77"),
        "generation_config.json": (138,
                        "8c970692323e3ea0e9b8b0a4dca79388d31226e41f83c9fd6014804280ebf6e8"),
        "merges.txt": (1671839,
                        "599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3"),
        "model.safetensors": (3087467144,
                        "a961db72e75d52b18e6b0c9d379e51a26973b233385e0e127fdda7d648aec796"),
        "tokenizer.json": (7031645,
                        "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539"),
        "tokenizer_config.json": (7228,
                        "c91efca15ceff6e9ee9424db58a6f59cd41294e550a86cbd07e3c1fb500b34f9"),
        "vocab.json": (2776833,
                        "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910"),
    },
}

# Backbones resolved through the ordinary HF cache (v2 verified cache).
PASSTHROUGH = ("gpt2",)


def total_bytes(descriptor: dict | None = None) -> int:
    d = descriptor or QWEN
    return sum(size for size, _sha in d["files"].values())


def asset_manifest_sha256(descriptor: dict | None = None) -> str:
    """Deterministic digest over the sorted name/size/sha256 triples."""
    d = descriptor or QWEN
    payload = "\n".join(f"{name}:{size}:{sha}" for name, (size, sha) in sorted(d["files"].items()))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def snapshot_is_complete(descriptor: dict | None = None) -> tuple[bool, list[str]]:
    """Fail-closed completeness check: every file present, readable, correct size."""
    d = descriptor or QWEN
    root = Path(d["local_snapshot_path"])
    problems: list[str] = []
    if not root.is_dir():
        return False, [f"snapshot directory missing: {root}"]
    for name, (size, _sha) in sorted(d["files"].items()):
        p = root / name
        if not p.exists():
            problems.append(f"missing: {name}")
            continue
        try:
            if p.stat().st_size != size:
                problems.append(f"size mismatch: {name} got {p.stat().st_size} want {size}")
        except OSError as e:
            problems.append(f"unreadable: {name} ({type(e).__name__})")
    return (not problems), problems


def descriptor_for(model_id: str) -> dict | None:
    """Return the authoritative descriptor for a model id, or None if none applies."""
    if model_id and model_id == QWEN["model_repo_id"]:
        return QWEN
    return None


def resolve_pretrained_source(model_id: str, *, allow_network: bool = False):
    """Resolve `(source, kwargs)` for ``from_pretrained``.

    * known asset with a verified local snapshot -> absolute snapshot path,
      ``local_files_only=True``, ``trust_remote_code=False``;
    * anything else -> the id unchanged, resolved through the normal cache.

    Never falls back silently to a network lookup for a known asset: formal
    runs must FAIL CLOSED if the verified snapshot is unusable.
    """
    desc = descriptor_for(model_id)
    if desc is None:
        return model_id, {"local_files_only": True}
    ok, problems = snapshot_is_complete(desc)
    if not ok:
        if not allow_network:
            raise RuntimeError(
                "verified local snapshot unusable and network fallback is disabled "
                f"for {model_id}: " + "; ".join(problems))
        return desc["model_repo_id"], {"revision": desc["model_revision"],
                                       "local_files_only": False,
                                       "trust_remote_code": desc["trust_remote_code"]}
    return desc["local_snapshot_path"], {"local_files_only": desc["local_files_only"],
                                         "trust_remote_code": desc["trust_remote_code"]}


def asset_descriptor(model_id: str) -> dict:
    """Provenance record for specification/config/status/report propagation."""
    desc = descriptor_for(model_id)
    if desc is None:
        return {"model_repo_id": model_id, "model_revision": None,
                "local_snapshot_path": None, "local_files_only": True,
                "trust_remote_code": False, "asset_manifest_sha256": None,
                "resolution": "passthrough_cache"}
    ok, problems = snapshot_is_complete(desc)
    return {
        "model_repo_id": desc["model_repo_id"],
        "model_revision": desc["model_revision"],
        "local_snapshot_path": desc["local_snapshot_path"],
        "local_files_only": desc["local_files_only"],
        "trust_remote_code": desc["trust_remote_code"],
        "asset_manifest_sha256": asset_manifest_sha256(desc),
        "license": desc["license"],
        "total_bytes": total_bytes(desc),
        "n_files": len(desc["files"]),
        "snapshot_complete": ok,
        "problems": problems,
        "resolution": "verified_local_snapshot" if ok else "unavailable",
    }


def cache_root() -> str:
    """HF cache root used for passthrough backbones (the v2 verified cache)."""
    return os.environ.get("HF_HOME", "/gpfs1/scratch/sychan552/CHATTIME/.cache")


def to_json() -> str:
    return json.dumps({"qwen": asset_descriptor(QWEN["model_repo_id"]),
                       "passthrough": list(PASSTHROUGH)}, indent=2)
