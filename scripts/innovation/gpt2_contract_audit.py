"""gpt2_contract_audit.py — structural audit of the GPT-2 family contract.

WHY: Gate 571905 reported `has_pretrained_backbone=False` for gpt2_miflu and
its 6 ablations / 2 controls, even though the compact step removed ~79x of the
bytes. That means the nested frozen GPT-2 backbone was NOT being identified by
the `isinstance(mod, transformers.PreTrainedModel)` rule.

This audit, run ON A STINGY COMPUTE NODE, determines the true structure:
  * every module path + class name (looking for the nested backbone)
  * whether any module IS a PreTrainedModel
  * which state_dict keys match a reference GPT-2 state_dict (i.e. are the
    frozen pretrained backbone), and under which prefix
  * `requires_grad` per matched group

It changes nothing: read-only introspection of freshly built models.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from innovation import compact_checkpoint as CC                 # noqa: E402
from innovation import architecture_contract as AC              # noqa: E402


def module_type_histogram(model) -> dict:
    hist = {}
    for name, mod in model.named_modules():
        t = type(mod).__name__
        hist.setdefault(t, []).append(name or "<root>")
    return {k: {"n": len(v), "sample": v[:3]} for k, v in
            sorted(hist.items(), key=lambda kv: -len(kv[1]))}


def pretrained_instances(model) -> list:
    try:
        from transformers import PreTrainedModel
    except Exception:                                          # noqa: BLE001
        return []
    return [n or "<root>" for n, m in model.named_modules()
            if isinstance(m, PreTrainedModel)]


def reference_gpt2_state() -> dict:
    """Immutable HF GPT-2 reference state (the frozen base)."""
    from transformers import GPT2Model
    return {k: v.detach().cpu() for k, v in
            GPT2Model.from_pretrained("gpt2").state_dict().items()}


def match_reference(model, ref: dict) -> dict:
    """Find which model keys correspond to reference GPT-2 keys (by suffix)."""
    sd = model.state_dict()
    ref_keys = set(ref)
    matched, prefixes = [], {}
    for k in sd:
        # the wrapper usually prefixes the reference key chain
        parts = k.split(".")
        for i in range(len(parts)):
            cand = ".".join(parts[i:])
            if cand in ref_keys:
                matched.append(k)
                prefixes.setdefault(".".join(parts[:i]) or "<root>", []).append(k)
                break
    groups = []
    for p, ks in prefixes.items():
        groups.append({"prefix": p, "n_keys": len(ks),
                       "bytes": sum(sd[k].numel() * sd[k].element_size()
                                    for k in ks)})
    return {"n_matched": len(matched),
            "n_total": len(sd),
            "matched_prefixes": sorted(groups, key=lambda g: -g["bytes"]),
            "sample_matched": matched[:6]}


def audit_one(name: str, horizon: int = 24) -> dict:
    out = {"model": name}
    try:
        model, base_model, enc_name, bkw = CC.build_base_model(name, horizon)
    except Exception as e:                                     # noqa: BLE001
        out["error"] = f"{type(e).__name__}: {e}"
        return out
    sd = model.state_dict()
    out["n_state_keys"] = len(sd)
    out["state_bytes"] = sum(v.numel() * v.element_size() for v in sd.values())
    out["pretrained_instances_by_type"] = pretrained_instances(model)
    out["module_type_histogram"] = module_type_histogram(model)
    out["module_paths_top"] = sorted({k.split(".")[0] for k in sd})
    try:
        ref = reference_gpt2_state()
        out["reference_gpt2_keys"] = len(ref)
        out["match"] = match_reference(model, ref)
    except Exception as e:                                     # noqa: BLE001
        out["reference_error"] = f"{type(e).__name__}: {e}"
    out["current_detected_prefixes"] = list(AC.backbone_key_prefixes(model))
    out["current_has_pretrained_backbone"] = \
        bool(AC.backbone_key_prefixes(model))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--horizon", type=int, default=24)
    a = ap.parse_args()
    rep = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "torch": torch.__version__, "audits": []}
    for m in a.models:
        print(f"[audit] {m}", flush=True)
        r = audit_one(m, a.horizon)
        print(f"[audit]   keys={r.get('n_state_keys')} bytes="
              f"{r.get('state_bytes')} PT_instances="
              f"{r.get('pretrained_instances_by_type')} "
              f"refmatch={ (r.get('match') or {}).get('n_matched') } "
              f"detected={r.get('current_detected_prefixes')}", flush=True)
        rep["audits"].append(r)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"[audit] wrote {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
