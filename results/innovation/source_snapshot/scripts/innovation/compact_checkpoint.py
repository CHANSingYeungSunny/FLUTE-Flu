"""compact_checkpoint.py — v3.13 reconstruction-complete compact checkpoints.

WHY: every per-row checkpoint currently stores the FROZEN pretrained backbone
in full (qwen_time_llm: 5888.8 MiB of 5890.3 MiB is the frozen `text.*` encoder;
calf/timecma: 474.7 MiB of ~482 MiB; gpt2_miflu: the frozen encoder inside
`inner.*`). That duplication is what exhausted the home quota.

DESIGN (provably complete, no heuristics):
    base_sd  = state_dict of a FRESHLY built, untrained model
               (`make_backbone(base_model, T, N, L, **bkw)` — exactly what
                clean_runner.py does, so the architecture AND the pretrained
                backbone are reproduced bit-for-bit)
    full_sd  = the row's trained checkpoint
    compact  = {k: v for k, v in full_sd.items()
                if k not in base_sd or not torch.equal(v, base_sd[k])}

Anything frozen and therefore identical to the base is dropped; everything the
training actually changed is kept. `verify` then rebuilds
`dict(base_sd) | compact` and requires it to be EQUAL to `full_sd` for every
key and every element (`torch.equal`), which makes the reconstruction exact by
construction rather than by tolerance.

This module changes ONLY persistence. No model, loss, optimizer, early
stopping, seed, horizon, split, scaler, metric or threshold is touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from innovation.backbones.registry import make_backbone          # noqa: E402
from innovation import clean_runner as CR                        # noqa: E402
from innovation import architecture_contract as AC               # noqa: E402

QWEN_ID = "Qwen/Qwen2.5-1.5B"
GPT2_ID = "gpt2"

# The immutable 598-row registry is the ONLY authority for run-key meaning.
REGISTRY_REL = ("results", "v3_clean", "runs", "complete_specs_598.json")


class CompactInputError(ValueError):
    """Raised for any malformed, unknown, ambiguous, deferred or path-like
    compact-checkpoint input. Never silently coerced."""


def _registry_path(deployment_root: str | None = None) -> Path:
    from pathlib import Path as _P
    root = deployment_root or os.environ.get("INNOVATION_DEPLOYMENT_ROOT")
    if not root:
        raise CompactInputError(
            "INNOVATION_DEPLOYMENT_ROOT must be set to resolve a run key")
    # Amendment-B (append-only): honour INNOVATION_REGISTRY_REL exactly like
    # clean_runner.load_registry; the default remains the frozen 598 registry.
    rel = os.environ.get("INNOVATION_REGISTRY_REL")
    parts = tuple(rel.split("/")) if rel else REGISTRY_REL
    p = _P(root).joinpath(*parts)
    if not p.is_file():
        raise CompactInputError(f"immutable registry not found: {p}")
    return p


def _load_registry(deployment_root: str | None = None) -> dict:
    import json
    return json.loads(_registry_path(deployment_root).read_text(encoding="utf-8"))


def _reject_path_like(k: str) -> None:
    """Requirement: reject path-like input before any registry lookup."""
    if ("/" in k or "\\" in k or ".." in k or k.startswith(".")
            or os.path.isabs(k) or os.sep in k):
        raise CompactInputError(f"path-like run key rejected: {k!r}")


def resolve_run_key(run_key: str, deployment_root: str | None = None) -> dict:
    """Authoritative, registry-backed run-key resolution.

    Returns {run_key, model, arm, horizon, seed, wave}. Raises
    CompactInputError for malformed / unknown / ambiguous / deferred input.
    """
    if not isinstance(run_key, str):
        raise CompactInputError("run key must be a string")
    k = run_key.strip()
    if not k:
        raise CompactInputError("empty run key")
    _reject_path_like(k)

    reg = _load_registry(deployment_root)
    specs = [s for s in reg.get("specs", []) if s.get("run_key") == k]
    if not specs:
        raise CompactInputError(f"unknown run key: {k}")
    if len(specs) > 1:
        raise CompactInputError(f"ambiguous run key: {k} ({len(specs)} matches)")
    s = specs[0]
    # Eligibility mirrors clean_runner.resolve_spec: submittable AND executable
    # binding are the authority. `wave==2` is NOT a disqualifier by itself (the
    # amendment rebinds deferred rows into executable bindings while keeping
    # their original wave=2 provenance).
    if not s.get("submittable") or not s.get("executable_binding"):
        raise CompactInputError(f"deferred run key not executable: {k}")
    for field in ("model", "horizon", "arm"):
        if field not in s:
            raise CompactInputError(f"malformed spec {k}: missing {field}")
    return {"run_key": k, "model": s["model"], "arm": s["arm"],
            "horizon": int(s["horizon"]), "seed": s.get("seed"),
            "wave": s.get("wave"), "control": s.get("control"),
            "parent_model": s.get("parent_model"),
            "amended_action": s.get("amended_action")}


def normalise_spec_input(spec_input: str,
                         horizon: int | None = None,
                         deployment_root: str | None = None) -> dict:
    """THE single normalisation entry point (D14).

    Order of authority:
      1. a run key present in the immutable registry  -> fully resolved
      2. a bare model name that is provably a member of PRIMARY_MODELS or
         VARIANTS (verified alias, never guessed)      -> needs a horizon
    Anything else is rejected. No fragile string splitting is used anywhere.
    """
    if not isinstance(spec_input, str) or not spec_input.strip():
        raise CompactInputError("spec input must be a non-empty string")
    k = spec_input.strip()
    _reject_path_like(k)

    try:
        return resolve_run_key(k, deployment_root)
    except CompactInputError as primary_err:
        known = set(CR.PRIMARY_MODELS) | set(CR.VARIANTS)
        if k in known:
            if horizon is None:
                raise CompactInputError(
                    f"bare model name {k!r} requires an explicit horizon"
                ) from primary_err
            return {"run_key": None, "model": k,
                    "arm": "ablation" if k in CR.VARIANTS else "primary",
                    "horizon": int(horizon), "seed": None, "wave": None}
        raise


def _bkw_for(model_name: str):
    """Reproduce the runner's backbone-kwarg resolution EXACTLY.
    `model_name` must already be a normalised model token."""
    if model_name in CR.VARIANTS:
        base_model, enc_name, bkw, ekw = CR.VARIANTS[model_name]
    else:
        base_model, enc_name, bkw, ekw = model_name, CR.PRIMARY_MODELS[model_name], {}, {}
    if base_model == "qwen_time_llm":
        bkw = dict(bkw, model_id=QWEN_ID, load_backbone=True)
    elif base_model in ("calf_llm", "timecma_llm"):
        bkw = dict(bkw, model_id=GPT2_ID, load_backbone=True)
    return base_model, enc_name, bkw


def build_base_model(spec_name: str, horizon: int | None = None,
                     device: str = "cpu"):
    # D14: the SAME unique entry point is used by every caller (CLI, Gate,
    # migration), so a full run key can never reach PRIMARY_MODELS[...] again.
    info = normalise_spec_input(spec_name, horizon)
    spec_name, horizon = info["model"], int(info["horizon"])
    base_model, enc_name, bkw = _bkw_for(spec_name)
    model = make_backbone(base_model, T=CR.T_WINDOW, N=CR.N_VARIABLES,
                          L=horizon, **bkw)
    if hasattr(model, "set_train_statistics"):
        model.set_train_statistics({"target_name": "ILITOTAL",
                                    "horizon": horizon,
                                    "channel_count": CR.N_VARIABLES})
    model = model.to(device)
    model.eval()
    return model, base_model, enc_name, bkw


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# ---- canonical TENSOR-SEMANTIC hash (v3.16) --------------------------------
# `sha256_file` proves FILE-BYTE integrity. It is NOT stable across serializer
# header/offset ordering: the same tensors written by safetensors can produce
# different bytes (observed: identical values and byte length, different SHA).
# `canonical_tensor_sha256` therefore hashes the TENSORS, not the container:
#   sorted by key, and for each key: dtype, shape, byte length and the raw
#   little-endian tensor buffer, each length-prefixed, under a schema version.
# It never feeds pickle output into the digest.
CANONICAL_HASH_SCHEMA = "canonical-tensor-v1"


def canonical_tensor_sha256(sd: dict) -> str:
    h = hashlib.sha256()
    h.update(CANONICAL_HASH_SCHEMA.encode("utf-8") + b"\x00")
    for k in sorted(sd):
        t = sd[k]
        if not torch.is_tensor(t):
            continue
        t = t.detach().cpu()
        if not t.is_contiguous():
            t = t.contiguous()
        shape = ",".join(str(d) for d in tuple(t.shape)).encode("utf-8")
        for blob in (k.encode("utf-8"), str(t.dtype).encode("utf-8"), shape):
            h.update(len(blob).to_bytes(8, "big"))
            h.update(blob)
        raw = t.numpy().tobytes()
        h.update(len(raw).to_bytes(8, "big"))
        h.update(raw)
    return h.hexdigest()


def _load_compact(path: str) -> dict:
    """Read a compact file written by `_save_compact` — which may be either
    safetensors OR torch.save. `torch.load` on a safetensors file fails with
    'UnpicklingError: Memo value not found', so try safetensors first."""
    try:
        from safetensors.torch import load_file
        return {k: v for k, v in load_file(path).items()}
    except Exception:                                          # noqa: BLE001
        return _load_sd(path)


def _load_sd(path: str) -> dict:
    obj = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(obj, dict):
        for k in ("state_dict", "model_state_dict", "model"):
            if k in obj and isinstance(obj[k], dict):
                return obj[k]
        if obj and all(torch.is_tensor(v) for v in obj.values()):
            return obj
        return {k: v for k, v in obj.items() if torch.is_tensor(v)}
    raise SystemExit(f"unsupported checkpoint container in {path}")


def _save_compact(sd: dict, out_path: str) -> str:
    """safetensors when possible (no shared storage / no non-contiguous), else
    torch.save. Returns the format actually used."""
    try:
        from safetensors.torch import save_file
        flat = {}
        for k, v in sd.items():
            t = v.detach().cpu()
            if not t.is_contiguous():
                t = t.contiguous()
            flat[k] = t
        save_file(flat, out_path)
        return "safetensors"
    except Exception:                                          # noqa: BLE001
        torch.save(sd, out_path)
        return "torch.save"


def export_compact(run_dir: str, ckpt: str, spec_name: str, horizon: int | None,
                   out_path: str) -> dict:
    t0 = time.time()
    info = normalise_spec_input(spec_name, horizon)      # D14 shared entry
    spec_name, horizon = info["model"], int(info["horizon"])
    full_sd = _load_sd(ckpt)
    model, base_model, enc_name, bkw = build_base_model(spec_name, horizon)
    base_sd = {k: v.detach().cpu() for k, v in model.state_dict().items()}

    compact, kept_trained, dropped_frozen = {}, [], []
    for k, v in full_sd.items():
        v_cpu = v.detach().cpu() if torch.is_tensor(v) else v
        if k not in base_sd:
            compact[k] = v_cpu
            kept_trained.append({"key": k, "why": "not_in_base",
                                 "bytes": v_cpu.numel() * v_cpu.element_size()})
        elif not torch.equal(v_cpu, base_sd[k]):
            compact[k] = v_cpu
            kept_trained.append({"key": k, "why": "differs_from_base",
                                 "bytes": v_cpu.numel() * v_cpu.element_size()})
        else:
            dropped_frozen.append(k)

    # ---- EXACT reconstruction check (bit-level, not tolerance based) ------
    rebuilt = dict(base_sd)
    rebuilt.update(compact)
    missing = [k for k in full_sd if k not in rebuilt]
    extra = [k for k in rebuilt if k not in full_sd]
    unequal = [k for k in full_sd if k in rebuilt
               and not torch.equal(rebuilt[k], full_sd[k].detach().cpu())]
    exact = not missing and not extra and not unequal

    # ---- D15: structural backbone accounting + applicability-aware invariant
    contract = AC.probe_contract(model, bkw)
    bb_prefixes = AC.backbone_key_prefixes(model)
    bb_keys = [k for k in full_sd if AC.is_backbone_key(k, bb_prefixes)]
    bb_total = sum(full_sd[k].numel() * full_sd[k].element_size()
                   for k in bb_keys)
    bb_excluded = 0
    bb_unexpected = 0
    bb_changed_dropped = 0
    for k in bb_keys:
        nb = full_sd[k].numel() * full_sd[k].element_size()
        if k in compact:
            # a RETAINED backbone tensor must be provably CHANGED vs the base
            if k in base_sd and torch.equal(full_sd[k].detach().cpu(),
                                            base_sd[k]):
                bb_unexpected += nb
        else:
            bb_excluded += nb
            # a DROPPED backbone tensor must be provably UNCHANGED
            if k in base_sd and not torch.equal(full_sd[k].detach().cpu(),
                                                base_sd[k]):
                bb_changed_dropped += nb
    no_duplication = AC.evaluate_duplication(
        contract["has_pretrained_backbone"], bb_unexpected, exact, True)
    # a changed-yet-dropped backbone tensor would break reconstruction, so it
    # must also be zero; guard it explicitly rather than relying on inference.
    if bb_changed_dropped:
        no_duplication = False

    fmt = _save_compact(compact, out_path)
    full_bytes = os.path.getsize(ckpt)
    comp_bytes = os.path.getsize(out_path)
    rep = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_dir": run_dir, "spec_name": spec_name, "base_model": base_model,
        "text_encoder": enc_name, "horizon": horizon, "format": fmt,
        "source_checkpoint": ckpt, "source_sha256": sha256_file(ckpt),
        "source_bytes": full_bytes,
        "compact_path": out_path, "compact_sha256": sha256_file(out_path),
        # v3.16: file-byte hash AND tensor-semantic hash (both are reported)
        "canonical_tensor_sha256": canonical_tensor_sha256(compact),
        "canonical_hash_schema": CANONICAL_HASH_SCHEMA,
        "canonical_key_count": len(compact),
        "compact_bytes": comp_bytes,
        "compression_ratio": round(full_bytes / max(comp_bytes, 1), 2),
        "n_full_keys": len(full_sd), "n_base_keys": len(base_sd),
        "n_compact_keys": len(compact),
        "n_dropped_frozen_keys": len(dropped_frozen),
        "dropped_frozen_bytes":
            sum(base_sd[k].numel() * base_sd[k].element_size()
                for k in dropped_frozen),
        "kept_trained": kept_trained,
        "kept_trained_bytes": sum(x["bytes"] for x in kept_trained),
        "frozen_backbone_excluded": len(dropped_frozen) > 0,
        # --- D15 structured contract evidence ---
        "has_pretrained_backbone": contract["has_pretrained_backbone"],
        "pretrained_backbone_contract_source": contract["contract_source"],
        "pretrained_backbone_module_paths":
            contract["pretrained_backbone_module_paths"],
        "base_model_id": contract["base_model_id"],
        "base_model_revision": contract["base_model_revision"],
        "frozen_backbone_key_count": contract["frozen_backbone_key_count"],
        "frozen_backbone_bytes_total": int(bb_total),
        "frozen_backbone_bytes_excluded": int(bb_excluded),
        "unexpected_frozen_backbone_bytes_retained": int(bb_unexpected),
        "changed_frozen_backbone_bytes_dropped": int(bb_changed_dropped),
        "no_frozen_backbone_duplication": bool(no_duplication),
        "predicate_applicable": contract["storage_predicate_applicable"],
        "reconstruction_exact": exact,
        "missing_keys": missing[:20], "extra_keys": extra[:20],
        "unequal_keys": unequal[:20],
        "n_missing": len(missing), "n_extra": len(extra),
        "n_unequal": len(unequal),
        "seconds": round(time.time() - t0, 2),
    }
    return rep


def restore_and_compare(run_dir: str, spec_name: str, horizon: int | None,
                        compact_path: str) -> dict:
    """Rebuild from the compact state alone and compare against the original
    checkpoint loaded into a fresh model — strict key accounting."""
    info = normalise_spec_input(spec_name, horizon)      # D14 shared entry
    spec_name, horizon = info["model"], int(info["horizon"])
    model, base_model, _, _ = build_base_model(spec_name, horizon)
    full_sd = _load_sd(os.path.join(run_dir, "checkpoints", "best_val_mse.pt"))
    comp = _load_compact(compact_path)
    rebuilt = dict(model.state_dict())
    rebuilt.update({k: v for k, v in comp.items()})
    rep = model.load_state_dict(rebuilt, strict=True)
    diff = [k for k in full_sd
            if not torch.equal(rebuilt[k].detach().cpu(),
                               full_sd[k].detach().cpu())]
    return {"strict_load_ok": True, "missing_keys": list(rep.missing_keys),
            "unexpected_keys": list(rep.unexpected_keys),
            "n_keys_compared": len(full_sd), "n_keys_unequal": len(diff),
            "unequal_keys": diff[:20], "restoration_exact": not diff}


def schema_report() -> dict:
    """Prove every schema is CONSTRUCTIBLE and report its module split without
    needing any checkpoint (covers all ablations / controls)."""
    out = {}
    names = sorted(set(list(CR.PRIMARY_MODELS) + list(CR.VARIANTS)))
    for n in names:
        try:
            model, base_model, enc_name, bkw = build_base_model(n, 24)
            sd = model.state_dict()
            out[n] = {
                "ok": True, "base_model": base_model, "text_encoder": enc_name,
                "n_keys": len(sd),
                "bytes": sum(v.numel() * v.element_size() for v in sd.values()),
                "top_prefixes": sorted({k.split(".")[0] for k in sd}),
                "trainable_keys": [k for k, p in model.named_parameters()
                                   if p.requires_grad][:12],
                "n_trainable_keys": sum(1 for _, p in
                                        model.named_parameters()
                                        if p.requires_grad),
            }
        except Exception as e:                                 # noqa: BLE001
            out[n] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["export", "export-verify", "schema"])
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--spec", required=True, help="run key or model name")
    ap.add_argument("--horizon", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()

    if a.mode == "schema":
        rep = schema_report()
        os.makedirs(os.path.dirname(a.report) or ".", exist_ok=True)
        with open(a.report, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2)
        ok = sum(1 for v in rep.values() if v.get("ok"))
        print(f"[schema] {ok}/{len(rep)} schemas constructible", flush=True)
        for k, v in rep.items():
            if v.get("ok"):
                print(f"[schema]   {k}: keys={v['n_keys']} "
                      f"trainable={v['n_trainable_keys']} "
                      f"prefixes={v['top_prefixes']}", flush=True)
            else:
                print(f"[schema]   {k}: FAILED {v['error']}", flush=True)
        return 0 if ok == len(rep) else 1

    # D14: the CLI delegates to the SAME resolution entry point; the old
    # fragile `spec.split("__")[1]` string cut is gone.
    spec = normalise_spec_input(a.spec, a.horizon)["model"]
    ckpt = os.path.join(a.run_dir, "checkpoints", "best_val_mse.pt")
    rep = export_compact(a.run_dir, ckpt, spec, a.horizon, a.out)
    if a.mode == "export-verify":
        rep["restoration"] = restore_and_compare(a.run_dir, spec, a.horizon,
                                                 a.out)
    os.makedirs(os.path.dirname(a.report) or ".", exist_ok=True)
    with open(a.report, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"[compact] {spec} L{a.horizon}: {rep['source_bytes']} -> "
          f"{rep['compact_bytes']} bytes "
          f"(x{rep['compression_ratio']}), exact={rep['reconstruction_exact']}",
          flush=True)
    if "restoration" in rep:
        print(f"[compact]   restoration_exact="
              f"{rep['restoration']['restoration_exact']} "
              f"unequal={rep['restoration']['n_keys_unequal']}", flush=True)
    return 0 if rep["reconstruction_exact"] else 1


if __name__ == "__main__":
    sys.exit(main())
