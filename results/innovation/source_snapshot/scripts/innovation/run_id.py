"""
run_id.py — unique, parseable run identifiers.
==============================================

Format (authoritative plan v2, §5):

    run_id = dataset__model__text_encoder__fusion__L{horizon}__seed{seed}__{timestamp}__{gitsha}

The timestamp makes every run unique even when the scientific specification
repeats, which is what allows the artifact tree to be create-only (no overwrite).
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import datetime
import os
import re
import subprocess

from innovation.paths import PROJECT_ROOT

_SEP = "__"
_SLUG_RE = re.compile(r"[^A-Za-z0-9]+")
_COMPONENTS = ("dataset", "model", "text_encoder", "fusion")


def slug(value) -> str:
    s = _SLUG_RE.sub("-", str(value).strip())
    return s.strip("-") or "na"


def utc_timestamp() -> str:
    return datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def git_sha(short: bool = True, cwd: str | None = None) -> str:
    """Return the current commit (short by default); 'nogit' if unavailable."""
    args = (["git", "rev-parse", "--short", "HEAD"] if short
            else ["git", "rev-parse", "HEAD"])
    try:
        out = subprocess.check_output(
            args, cwd=cwd or PROJECT_ROOT, stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or "nogit"
    except Exception:
        return "nogit"


def make_run_id(dataset: str, model: str, text_encoder: str, fusion: str,
                horizon: int, seed: int, timestamp: str | None = None,
                gitsha: str | None = None) -> str:
    ts = timestamp or utc_timestamp()
    sha = gitsha if gitsha is not None else git_sha()
    return _SEP.join([
        slug(dataset), slug(model), slug(text_encoder), slug(fusion),
        f"L{int(horizon)}", f"seed{int(seed)}", ts, slug(sha),
    ])


def make_test_eval_id(run_id: str, timestamp: str | None = None) -> str:
    ts = timestamp or utc_timestamp()
    return f"testeval__{slug(run_id)}__{ts}"


def parse_run_id(run_id: str) -> dict:
    parts = run_id.split(_SEP)
    if len(parts) != 8:
        raise ValueError(f"malformed run_id (expected 8 fields): {run_id!r}")
    dataset, model, text_encoder, fusion, lfield, sfield, ts, sha = parts
    if not lfield.startswith("L") or not sfield.startswith("seed"):
        raise ValueError(f"malformed run_id horizon/seed fields: {run_id!r}")
    return {
        "dataset": dataset, "model": model, "text_encoder": text_encoder,
        "fusion": fusion, "horizon": int(lfield[1:]), "seed": int(sfield[4:]),
        "timestamp": ts, "gitsha": sha,
    }


if __name__ == "__main__":  # pragma: no cover
    rid = make_run_id("national_ili", "dlinear", "none", "identity", 24, 42)
    print("[run_id]", rid)
    print("[run_id] parsed:", parse_run_id(rid))
