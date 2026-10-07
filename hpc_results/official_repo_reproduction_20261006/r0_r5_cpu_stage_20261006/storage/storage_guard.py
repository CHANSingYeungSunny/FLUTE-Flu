#!/usr/bin/env python3
"""
storage_guard.py — S3/S4: storage preflight, postflight, atomic saves and the
retention policy that every future R1-B / replacement job must honour.

WHY THIS EXISTS
---------------
Scratch is **413 GB against a 300 GB quota, grace expired**, and a 10 KB `scp` was
already rejected with `Disk quota exceeded`. Meanwhile the F1 storage projection
was wrong by 85x (3.9 MB predicted per checkpoint, 329 MB actual) because the
projection assumed the locked-checkpoint path while the trainer used the full
`state_dict`.

So the guard does three things the earlier ad-hoc checks did not:
  1. it measures the ACTUAL checkpoint size empirically, or takes a measured
     value, and never relies on a projection;
  2. it refuses to write to scratch unless scratch is verified healthy;
  3. it saves atomically, so an interrupted write cannot leave a truncated
     artefact that later looks valid.

CPU-only. No GPU, no HPC compute. Safe to unit-test locally.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile

# ── measured constants (NOT projections) ─────────────────────────────────────
MEASURED_CKPT_BYTES = {
    # measured this project; see STORAGE_TRACK_S0_S1.md
    "full_state_dict_gpt2_6layer": 328_585_240,   # train_miflu.py / F1        ~329 MB
    "locked_trainable_only":       4_100_000,     # save_locked_ckpt()         ~3.9 MB
    "qwen_full":                   6_176_478_657, # historical, for reference
    "qwen_compact_export":         1_482_128,     # historical reduced export
}
PREDICTION_BYTES_PER_L = {24: 110_000, 36: 160_000, 48: 210_000, 60: 265_000}  # measured in F1

MIN_HEADROOM_BYTES = 1 << 30          # 1 GiB absolute floor
HEADROOM_MULTIPLE = 10                # and 10x the projected output


class StorageRefused(RuntimeError):
    """Raised when a write must not proceed."""


# ─────────────────────────────────────────────────────────────────────────────
def measure_checkpoint_bytes(trainer: str = "locked") -> int:
    """Return the measured per-checkpoint size for a given trainer path.

    `trainer` is 'locked' (save_locked_ckpt: trainable tensors only) or
    'full' (torch.save(model.state_dict())). Returns a MEASURED value, never a
    guess; the F1 experience is the reason this distinction exists.
    """
    key = "locked_trainable_only" if trainer == "locked" else "full_state_dict_gpt2_6layer"
    return MEASURED_CKPT_BYTES[key]


def project_output_bytes(n_fits: int, horizons, trainer: str = "locked",
                         keep_predictions: bool = True, log_bytes_per_fit: int = 60_000,
                         manifest_bytes_per_fit: int = 1_000) -> dict:
    """Projected peak output for a run matrix. Every term is measured-derived."""
    ck = measure_checkpoint_bytes(trainer)
    pred = sum(PREDICTION_BYTES_PER_L.get(int(L), 200_000) for L in horizons) \
        if keep_predictions else 0
    per_fit = ck + log_bytes_per_fit + manifest_bytes_per_fit
    per_L_pred = pred
    total = n_fits * per_fit + per_L_pred
    return {
        "trainer": trainer,
        "n_fits": n_fits,
        "checkpoint_bytes_each": ck,
        "checkpoint_bytes_total": n_fits * ck,
        "prediction_bytes_total": per_L_pred,
        "log_bytes_total": n_fits * log_bytes_per_fit,
        "manifest_bytes_total": n_fits * manifest_bytes_per_fit,
        "projected_total_bytes": total,
        "projected_total_gib": round(total / 2 ** 30, 4),
        "projected_total_mib": round(total / 2 ** 20, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
def fs_stats(path: str) -> dict:
    """Free/total bytes for the filesystem holding `path`.

    Walks up to the nearest EXISTING ancestor, so a not-yet-created target (or a
    path that exists only on the HPC, such as /gpfs1/scratch, which does not exist
    on the local dev box) does not raise. When nothing on the path exists the
    usage is reported as UNKNOWN rather than guessed -- and the caller must then
    rely on the explicit scratch-health declaration instead of a measurement.
    """
    p = os.path.abspath(path)
    probe, guard = p, 0
    while not os.path.exists(probe) and guard < 40:
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe, guard = parent, guard + 1
    if not os.path.exists(probe):
        return {"path": p, "resolved": None, "free_bytes": None, "total_bytes": None,
                "free_gib": None, "known": False}
    try:
        u = shutil.disk_usage(probe)
    except OSError:
        return {"path": p, "resolved": probe, "free_bytes": None, "total_bytes": None,
                "free_gib": None, "known": False}
    return {"path": p, "resolved": probe, "total_bytes": u.total,
            "used_bytes": u.used, "free_bytes": u.free,
            "free_gib": round(u.free / 2 ** 30, 2), "known": True}


def preflight(target_dir: str, projected: dict, scratch_declared_healthy: bool = False,
              min_headroom: int = MIN_HEADROOM_BYTES,
              multiple: int = HEADROOM_MULTIPLE) -> dict:
    """PREFLIGHT: may we write `projected` into `target_dir`?

    Refuses when:
      * the path is on scratch and scratch has not been explicitly declared healthy;
      * free space is below max(min_headroom, multiple x projected).
    """
    p = os.path.abspath(target_dir)
    # Detect scratch by inspecting path COMPONENTS, so the check behaves the same
    # on POSIX (where it is a real mount) and on a Windows dev box (where
    # os.path.abspath rewrites "/gpfs1/scratch/..." to "C:\gpfs1\scratch\...").
    # The guard is meant for the HPC; making it host-agnostic means the tests
    # exercise the same branch that will run there.
    parts = [q.lower() for q in p.replace("\\", "/").split("/") if q]
    on_scratch = ("gpfs1" in parts and "scratch" in parts) or "scratch" in parts[:3]
    st = fs_stats(p)
    need = max(min_headroom, multiple * projected["projected_total_bytes"])
    reasons = []

    if on_scratch and not scratch_declared_healthy:
        reasons.append("target is on scratch and scratch is NOT declared healthy "
                       "(quota 413/300 GB, grace expired)")

    # on the local dev box the "filesystem" is large; the HPC quota is enforced
    # by the scheduler, so compare against the declared headroom when available
    if not st.get("known"):
        reasons.append(f"free space UNKNOWN for {p} (no existing ancestor on this "
                       f"host); cannot verify the required headroom of "
                       f"{round(need / 2 ** 30, 2)} GiB")
    elif st["free_bytes"] < need:
        reasons.append(f"free {st['free_gib']} GiB < required "
                       f"{round(need / 2 ** 30, 2)} GiB")

    ok = not reasons
    return {"ok": ok, "target": p, "on_scratch": on_scratch,
            "free_known": st.get("known", False),
            "free_bytes": st["free_bytes"], "required_bytes": need,
            "projected_bytes": projected["projected_total_bytes"],
            "reasons": reasons,
            "verdict": "STORAGE_PREFLIGHT_PASS" if ok else "STORAGE_PREFLIGHT_REFUSED"}


# ─────────────────────────────────────────────────────────────────────────────
def atomic_save_npz(path: str, **arrays) -> int:
    """S4: write an NPZ atomically (temp file in the same directory + rename).

    An interrupted write leaves the original untouched rather than a truncated
    file that later passes an existence check.
    """
    import numpy as np
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".part")
    os.close(fd)
    try:
        with open(tmp, "wb") as fh:
            np.savez_compressed(fh, **arrays)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)          # atomic on POSIX and Windows
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return os.path.getsize(path)


def atomic_save_torch(path: str, obj) -> int:
    """S4: write a torch checkpoint atomically."""
    import torch
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".part")
    os.close(fd)
    try:
        torch.save(obj, tmp)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return os.path.getsize(path)


# ─────────────────────────────────────────────────────────────────────────────
RETENTION_POLICY = {
    "keep": [
        "best validation-selected checkpoint, one per (model, horizon, repetition)",
        "final predictions and targets (7-channel NPZ)",
        "run manifest and provenance",
        "slurm stdout/stderr and per-fit logs",
        "the scoring outputs and the gate report",
    ],
    "never_keep": [
        "optimizer state after selection",
        "scheduler state",
        "per-epoch checkpoints",
        "intermediate training tensors",
        "the HuggingFace cache inside the output tree (it is shared and external)",
    ],
    "lifecycle": {
        "during_training": "at most 2 checkpoints exist: the rolling best and a temp",
        "on_selection": "the best is promoted atomically; the temp is deleted",
        "on_completion": "only the retained set above remains",
    },
}


def postflight(target_dir: str, expected_files: int | None = None) -> dict:
    """POSTFLIGHT: what is actually there, and does it match the retention policy?"""
    p = os.path.abspath(target_dir)
    if not os.path.isdir(p):
        return {"ok": False, "reason": "target does not exist", "target": p}
    files, total = [], 0
    for root, _dirs, fs in os.walk(p):
        for f in fs:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
            files.append(os.path.relpath(fp, p))
    stray = [f for f in files if f.endswith(".part")]
    return {"ok": not stray, "target": p, "n_files": len(files),
            "total_bytes": total, "total_mib": round(total / 2 ** 20, 2),
            "partial_files_left_behind": stray,
            "matches_expected_count": (expected_files is None or len(files) == expected_files),
            "verdict": "STORAGE_POSTFLIGHT_PASS" if not stray else "STORAGE_POSTFLIGHT_FAIL"}


if __name__ == "__main__":
    print(json.dumps({
        "measured_checkpoint_bytes": MEASURED_CKPT_BYTES,
        "retention_policy": RETENTION_POLICY}, indent=2))

# ─────────────────────────────────────────────────────────────────────────────
def quota_free_bytes(path: str = None):
    """Free bytes under the USER QUOTA, not the filesystem.

    On GPFS, `shutil.disk_usage` reports the filesystem (hundreds of TB) while the
    binding constraint is the per-user quota — which is exactly the thing that is
    over on scratch (413 GB against 300 GB). A guard that only asked the
    filesystem would pass on a filesystem that cannot accept a single byte.
    Returns (free_bytes, source) or (None, reason).
    """
    import subprocess
    fs = "scratch" if (path and "scratch" in path.replace("\\", "/")) else "home"
    try:
        out = subprocess.run(["mmlsquota", "-u", os.environ.get("USER", "sychan552"), fs],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception as e:
        return None, f"mmlsquota unavailable: {e}"
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0] == fs:
            try:
                used_kb, quota_kb = int(parts[2]), int(parts[3])
                grace = parts[6] if len(parts) > 6 else "?"
                free = (quota_kb - used_kb) * 1024
                return free, f"mmlsquota {fs}: used={used_kb/1048576:.1f}GB "                              f"quota={quota_kb/1048576:.1f}GB grace={grace}"
            except (ValueError, IndexError):
                pass
    return None, "mmlsquota output not parseable"


def quota_preflight(target_dir: str, projected: dict,
                    min_headroom: int = MIN_HEADROOM_BYTES,
                    multiple: int = HEADROOM_MULTIPLE) -> dict:
    """Preflight against the USER QUOTA. Use this on the HPC."""
    free, src = quota_free_bytes(target_dir)
    need = max(min_headroom, multiple * projected["projected_total_bytes"])
    reasons = []
    if free is None:
        reasons.append(f"quota unknown ({src})")
    elif free < need:
        reasons.append(f"quota free {free/2**30:.2f} GiB < required {need/2**30:.2f} GiB")
    return {"ok": not reasons, "target": target_dir, "quota_source": src,
            "quota_free_bytes": free, "required_bytes": need,
            "projected_bytes": projected["projected_total_bytes"],
            "reasons": reasons,
            "verdict": "STORAGE_PREFLIGHT_PASS" if not reasons else "STORAGE_PREFLIGHT_REFUSED"}
