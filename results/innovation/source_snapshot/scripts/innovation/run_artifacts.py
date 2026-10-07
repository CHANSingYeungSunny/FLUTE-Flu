"""
run_artifacts.py — create-only artifact trees, append-only registry, hashing.
=============================================================================

Enforces the plan's hard rules (§5):
  * every run gets its OWN directory; creation REFUSES to overwrite an existing
    one (create-only, not "overwrite by default");
  * the top-level registry is APPEND-ONLY;
  * checkpoints carry a SHA-256 and a restore test, plus the full config that
    produced them;
  * failures/interruptions are still recorded (run_status.json + registry row).

Test artifacts are NOT written here — see `create_test_eval_dir()` and the
runner's `phase="test"` path, which is the only place `test_predictions.csv`
may be produced (revision 1).
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import csv
import datetime
import hashlib
import json
import os

import numpy as np

from innovation.paths import (INNOVATION_ROOT, REGISTRY_PATH,
                              REQUIRED_METADATA_FIELDS, RUNS_ROOT,
                              TEST_EVAL_ROOT)

RUN_SUBDIRS = ("checkpoints", "logs", "predictions", "metrics", "figures")

# LEGACY schema (frozen: the 14 historical rows are never rewritten)
REGISTRY_COLUMNS = [
    "run_id", "status", "run_dir", "checkpoint_sha256", "best_val_mse",
    "created_utc", "git_sha", "plan_sha256", "notes",
]

# VERSIONED schema (innov-v2.3): complete governance + provenance columns.
REGISTRY_V2_PATH = os.path.join(INNOVATION_ROOT, "registry_v2.csv")
REGISTRY_SCHEMA_VERSION = 2
REGISTRY_V2_CORE = [
    "schema_version", "run_id", "status", "run_dir", "checkpoint_sha256",
    "state_dict_sha256", "best_val_mse", "best_epoch", "created_utc",
    "git_sha", "notes",
]
REGISTRY_V2_COLUMNS = (REGISTRY_V2_CORE + list(REQUIRED_METADATA_FIELDS))


# ── time ────────────────────────────────────────────────────────────────────
def utc_now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# ── JSON / YAML writers (no third-party deps) ───────────────────────────────
def sanitize(obj):
    """Recursively make an object JSON-safe (NaN/Inf -> null, numpy -> python)."""
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        return None if not np.isfinite(f) else f
    if isinstance(obj, (str, int, bool)) or obj is None:
        return obj
    return str(obj)


def write_json(path: str, obj) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sanitize(obj), f, indent=2)
    return path


def _yaml_scalar(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int) and not isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        if not np.isfinite(v):
            return "null"
        return repr(v)
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_min_yaml(path: str, obj, indent: int = 0) -> str:
    """Write a minimal YAML file (dicts / lists / scalars) with the stdlib only."""
    lines: list[str] = []

    def emit(o, ind: int) -> None:
        pad = "  " * ind
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    lines.append(f"{pad}{k}:")
                    emit(v, ind + 1)
                else:
                    lines.append(f"{pad}{k}: {_yaml_scalar(v)}")
        elif isinstance(o, (list, tuple)):
            for v in o:
                if isinstance(v, (dict, list)):
                    lines.append(f"{pad}-")
                    emit(v, ind + 1)
                else:
                    lines.append(f"{pad}- {_yaml_scalar(v)}")
        else:
            lines.append(f"{pad}{_yaml_scalar(o)}")

    emit(sanitize(obj), indent)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


# ── hashing ─────────────────────────────────────────────────────────────────
def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def state_dict_sha256(state_dict) -> str:
    """Order-independent, dtype-exact hash of a (tensor) state_dict."""
    import torch

    h = hashlib.sha256()
    for k in sorted(state_dict.keys()):
        h.update(k.encode("utf-8"))
        v = state_dict[k]
        if isinstance(v, torch.Tensor):
            arr = v.detach().to("cpu").contiguous().numpy()
            h.update(str(arr.dtype).encode("utf-8"))
            h.update(str(tuple(arr.shape)).encode("utf-8"))
            h.update(arr.tobytes())
        else:
            h.update(repr(v).encode("utf-8"))
    return h.hexdigest()


# ── create-only directories ─────────────────────────────────────────────────
def _create_tree(root: str, name: str) -> str:
    path = os.path.join(root, name)
    if os.path.exists(path):
        raise FileExistsError(
            f"refusing to overwrite existing directory (create-only): {path}")
    os.makedirs(path)
    for sub in RUN_SUBDIRS:
        os.makedirs(os.path.join(path, sub), exist_ok=True)
    return path


def create_run_dir(run_id: str) -> str:
    return _create_tree(RUNS_ROOT, run_id)


def create_test_eval_dir(test_eval_id: str) -> str:
    return _create_tree(TEST_EVAL_ROOT, test_eval_id)


# ── registry (append-only) ──────────────────────────────────────────────────
def append_registry(row: dict) -> str:
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    is_new = not os.path.exists(REGISTRY_PATH)
    with open(REGISTRY_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REGISTRY_COLUMNS,
                           extrasaction="ignore")
        if is_new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in REGISTRY_COLUMNS})
    return REGISTRY_PATH


def append_registry_v2(row: dict) -> str:
    """Append to the VERSIONED registry (innov-v2.3).

    The legacy `registry.csv` is NEVER rewritten: adding 12 governance columns to
    it would make the existing 14 historical rows ambiguous. New runs therefore go
    to `registry_v2.csv`, which is append-only and carries the complete schema.
    """
    path = REGISTRY_V2_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    is_new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REGISTRY_V2_COLUMNS,
                           extrasaction="ignore")
        if is_new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in REGISTRY_V2_COLUMNS})
    return path


def read_registry_v2() -> list[dict]:
    if not os.path.exists(REGISTRY_V2_PATH):
        return []
    with open(REGISTRY_V2_PATH, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_registry() -> list[dict]:
    if not os.path.exists(REGISTRY_PATH):
        return []
    with open(REGISTRY_PATH, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── run status ──────────────────────────────────────────────────────────────
def write_run_status(run_dir: str, **fields) -> str:
    payload = {"updated_utc": utc_now()}
    payload.update(sanitize(fields))
    return write_json(os.path.join(run_dir, "run_status.json"), payload)


# ── checkpoint manifest + restore test ──────────────────────────────────────
def write_checkpoint_manifest(run_dir: str, *, ckpt_path: str, best_epoch: int,
                              best_val_mse: float, config: dict,
                              extra: dict | None = None) -> dict:
    import torch

    sd = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    man = {
        "checkpoint_file": os.path.relpath(ckpt_path, run_dir).replace(os.sep, "/"),
        "sha256_file": sha256_file(ckpt_path),
        "state_dict_sha256": state_dict_sha256(sd),
        "best_epoch": int(best_epoch),
        "best_val_mse": sanitize(float(best_val_mse)),
        "config": sanitize(config),
        "created_utc": utc_now(),
    }
    if extra:
        man.update(sanitize(extra))
    write_json(os.path.join(run_dir, "checkpoints", "checkpoint_manifest.json"), man)
    return man


def restore_test(model_factory, ckpt_path: str,
                 expected_state_dict_sha256: str | None = None) -> dict:
    """Rebuild a FRESH model, load the checkpoint, and prove it round-trips."""
    import torch

    sd = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    model = model_factory()
    res = model.load_state_dict(sd, strict=True)
    after = state_dict_sha256(model.state_dict())
    ok = after == state_dict_sha256(sd)
    if expected_state_dict_sha256:
        ok = ok and after == expected_state_dict_sha256
    return {
        "ok": bool(ok),
        "state_dict_sha256_after_load": after,
        "missing_keys": list(res.missing_keys),
        "unexpected_keys": list(res.unexpected_keys),
    }


if __name__ == "__main__":  # pragma: no cover
    ensure = os.makedirs(INNOVATION_ROOT, exist_ok=True)
    print("[run_artifacts] innovation root:", INNOVATION_ROOT)
    print("[run_artifacts] runs root      :", RUNS_ROOT)
    print("[run_artifacts] registry       :", REGISTRY_PATH)
