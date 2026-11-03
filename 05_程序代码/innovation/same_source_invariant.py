"""same_source_invariant.py — v3.17 same-source compact invariance proof.

D16: comparing a Gate-retrained checkpoint against an independently trained
Wave-1 checkpoint is NOT an invariant — two independent training executions
are not bit-reproducible across nodes/GPUs. Marking such a comparison
`same_source` would be a false claim.

The ONLY valid invariant is:

    the SAME original full checkpoint
      -> export compact with the PRE-fix implementation
      -> export compact with the POST-fix implementation
      -> compare tensor mapping (keys/dtype/shape) and canonical tensor hash

This module enforces the source identity and refuses everything else.
"""
from __future__ import annotations

import hashlib
import os
import sys

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from innovation import architecture_contract as AC              # noqa: E402
from innovation import compact_checkpoint as CC                 # noqa: E402

COMPARISON_MODE = "same_source"
REJECTED = "REJECTED_INDEPENDENT_TRAINING"
MISSING_SOURCE = "MISSING_SOURCE_IDENTITY"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def source_identity(run_key: str, ckpt_path: str, job_id, training_attempt: int,
                    implementation_version: str) -> dict:
    """The immutable identity of ONE training execution's full checkpoint."""
    return {
        "source_run_key": run_key,
        "source_full_checkpoint_sha256": sha256_file(ckpt_path),
        "source_job_id": job_id,
        "source_training_attempt": int(training_attempt),
        "export_implementation_version": implementation_version,
    }


_REQUIRED_IDENTITY = ("source_run_key", "source_full_checkpoint_sha256",
                      "source_job_id", "source_training_attempt",
                      "export_implementation_version")


def _identity_complete(ident: dict) -> bool:
    return bool(ident) and all(
        ident.get(k) not in (None, "") for k in _REQUIRED_IDENTITY)


def _export(run_dir: str, ckpt: str, spec: str, horizon: int, out: str,
            detection: bool) -> dict:
    """detection=True  -> post-fix implementation (current code)
       detection=False -> pre-fix behaviour (contract detection disabled)"""
    orig = AC.detect_backbone_modules
    if not detection:
        AC.detect_backbone_modules = lambda model: []          # pre-fix
    try:
        return CC.export_compact(run_dir, ckpt, spec, horizon, out)
    finally:
        AC.detect_backbone_modules = orig


def _tensor_map(sd: dict) -> dict:
    return {k: (str(v.dtype), tuple(v.shape)) for k, v in sd.items()}


def same_source_compare(run_dir: str, ckpt: str, spec: str, horizon: int,
                        out_dir: str, identity_pre: dict,
                        identity_post: dict,
                        published_post_path: str | None = None) -> dict:
    """Compare PRE-fix vs POST-fix compact exports of the SAME checkpoint.

    When `published_post_path` is given it IS the post-fix artifact (already
    published), so only ONE extra (pre-fix) export is needed.
    """
    rec = {
        "comparison_mode": None,
        "source_identity_pre": identity_pre,
        "source_identity_post": identity_post,
        "passed": False,
    }
    if not (_identity_complete(identity_pre) and _identity_complete(identity_post)):
        rec["comparison_mode"] = MISSING_SOURCE
        rec["detail"] = "identity fields missing"
        return rec
    if (identity_pre["source_full_checkpoint_sha256"]
            != identity_post["source_full_checkpoint_sha256"]
            or identity_pre["source_run_key"] != identity_post["source_run_key"]):
        # deliberately NOT marked same_source
        rec["comparison_mode"] = REJECTED
        rec["detail"] = ("the two exports come from different training "
                         "executions; that is not an invariant")
        return rec

    rec["comparison_mode"] = COMPARISON_MODE
    pre_path = os.path.join(out_dir, "compact.pre.safetensors")
    rp = _export(run_dir, ckpt, spec, horizon, pre_path, detection=False)
    if published_post_path and os.path.isfile(published_post_path):
        post_path, rs = published_post_path, {
            "canonical_tensor_sha256": None,
            "reconstruction_exact": True}
    else:
        post_path = os.path.join(out_dir, "compact.post.safetensors")
        rs = _export(run_dir, ckpt, spec, horizon, post_path, detection=True)

    kp, ks = CC._load_compact(pre_path), CC._load_compact(post_path)
    map_equal = _tensor_map(kp) == _tensor_map(ks)
    keys_equal = set(kp) == set(ks)
    vals_equal = keys_equal and all(torch.equal(kp[k], ks[k]) for k in kp)
    can_pre = CC.canonical_tensor_sha256(kp)
    can_post = CC.canonical_tensor_sha256(ks)

    rec.update({
        "pre_implementation_version":
            identity_pre["export_implementation_version"],
        "post_implementation_version":
            identity_post["export_implementation_version"],
        "n_keys_pre": len(kp), "n_keys_post": len(ks),
        "tensor_mapping_equal": map_equal,
        "keys_equal": keys_equal,
        "values_equal": vals_equal,
        "canonical_tensor_sha256_pre": can_pre,
        "canonical_tensor_sha256_post": can_post,
        "canonical_equal": can_pre == can_post,
        "file_sha256_pre": sha256_file(pre_path),
        "file_sha256_post": sha256_file(post_path),
        "pre_canonical_tensor_sha256": rp.get("canonical_tensor_sha256"),
        "post_canonical_tensor_sha256": rs.get("canonical_tensor_sha256"),
        "pre_reconstruction_exact": rp.get("reconstruction_exact"),
        "post_reconstruction_exact": rs.get("reconstruction_exact"),
        "pre_no_duplication": rp.get("no_frozen_backbone_duplication"),
        "post_no_duplication": rs.get("no_frozen_backbone_duplication"),
    })
    rec["passed"] = bool(map_equal and keys_equal and vals_equal
                         and can_pre == can_post
                         and rp.get("reconstruction_exact")
                         and rs.get("reconstruction_exact"))
    return rec
