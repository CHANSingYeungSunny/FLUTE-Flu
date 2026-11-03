"""Seed-provenance gate for the frozen-LLM arms (single source of truth).

Why this exists
--------------
Every LLM cell on disk before 2026-11-02 ~04:00 was trained with the seed
**ignored**: `train_backbone_966.build_model` did not pass `seed` into
`FrozenLLMEncoder`, the adapter fell back to its default `seed=42`, and its
`torch.manual_seed(...)` calls overrode the runner's `set_seed(seed + L)`.
The result was `pred` bit-identical across seeds 42/43/44 (max|dpred| = 0) and
a cross-seed standard deviation of **exactly zero by construction**. The npz
files still recorded the right `seed`, so the file NAME could not reveal it.

The only field that distinguishes a real draw from the bug is the run manifest:
a correctly seeded cell of this arm records
`encoder.determinism.manual_seed == seed + L` (the arm's seed convention, the
same `set_seed(seed + L)` every other arm uses). So the invariant is:

    is an LLM cell  =>  manifest.encoder.determinism.manual_seed == L + seed

This module implements that check once, so that

  * `scripts/analysis_expanded.py` can REFUSE a cell whose provenance fails
    (the gate lives in the pipeline, not in a human's memory), and
  * `hpc_experiments/quarantine_unseeded_cells.py` can find and quarantine
    every poisoned directory without hard-coding a list of labels.

Non-LLM arms have no `encoder` block in their manifest and are always OK here:
they each receive their own `set_seed(seed + L)` with no later reset, and that
was verified by measurement on 2026-11-02 (max|dpred| = 2.1-6.5 for
patchtst/nlinear across seeds, i.e. genuinely different draws).
"""
from __future__ import annotations

import json
import os
import re

#: The manifest key that only the frozen-encoder arms carry.
ENCODER_KEY = "encoder"

_NPZ_RE = re.compile(r"pred_(?P<label>.+)_L(?P<L>\d+)_s(?P<seed>\d+)\.npz$")


def expected_manual_seed(L, seed) -> int:
    """The arm's seed convention: `seed + L` (identical to `set_seed(seed + L)`)."""
    return int(seed) + int(L)


def manifest_path_for(npz_path: str) -> str:
    """`pred_<label>_L<L>_s<seed>.npz` -> `manifest_<label>_L<L>_s<seed>.json`."""
    d = os.path.dirname(npz_path)
    base = os.path.basename(npz_path)
    m = _NPZ_RE.search(base)
    if not m:
        return ""
    return os.path.join(d, "manifest_{label}_L{L}_s{seed}.json".format(**m.groupdict()))


def read_manifest(npz_path: str):
    p = manifest_path_for(npz_path)
    if not p or not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def cell_seed_status(npz_path: str, manifest=None) -> dict:
    """Classify one cell's seed provenance.

    Returns a dict with:
      is_llm      : bool  -- the manifest carries an `encoder` block
      ok          : bool  -- safe to aggregate
      recorded    : int|None -- manual_seed actually recorded
      expected    : int|None -- L + seed
      reason      : str   -- why it failed ('' when ok)
    """
    m = _NPZ_RE.search(os.path.basename(npz_path))
    out = {"npz": npz_path, "is_llm": False, "ok": True, "recorded": None,
           "expected": None, "reason": ""}
    if not m:
        out.update({"ok": False, "reason": "filename is not pred_<label>_L<L>_s<seed>.npz"})
        return out
    L, seed = int(m.group("L")), int(m.group("seed"))
    out["expected"] = expected_manual_seed(L, seed)
    man = manifest if manifest is not None else read_manifest(npz_path)
    if not isinstance(man, dict):
        # No manifest: a non-LLM cell may legitimately predate manifests, and a
        # missing file cannot be judged. Allow, but say so -- the quarantine
        # tool reports these separately so they are never silently trusted.
        out["reason"] = "no manifest: seed provenance unprovable"
        return out
    enc = man.get(ENCODER_KEY)
    if not isinstance(enc, dict):
        return out                      # a trained arm: seed is applied normally
    out["is_llm"] = True
    det = enc.get("determinism") or {}
    rec = det.get("manual_seed")
    out["recorded"] = rec
    if rec is None:
        out.update({"ok": False, "reason": "LLM manifest records no manual_seed"})
        return out
    try:
        rec_i = int(rec)
    except (TypeError, ValueError):
        out.update({"ok": False, "reason": f"manual_seed {rec!r} is not an integer"})
        return out
    if rec_i != out["expected"]:
        out.update({"ok": False,
                    "reason": (f"seed did not enter the training path: manifest "
                               f"manual_seed={rec_i} but seed+L={out['expected']} "
                               f"(L={L}, seed={seed})")})
    return out


def audit(root: str):
    """Yield `cell_seed_status` for every `pred_*.npz` under `root`."""
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            if fn.startswith("pred_") and fn.endswith(".npz"):
                yield cell_seed_status(os.path.join(dirpath, fn))


def refused_labels(root: str):
    """Set of arm labels that have at least one provenance-invalid LLM cell."""
    bad = set()
    for st in audit(root):
        if st["is_llm"] and not st["ok"]:
            m = _NPZ_RE.search(os.path.basename(st["npz"]))
            if m:
                bad.add(m.group("label"))
    return bad
