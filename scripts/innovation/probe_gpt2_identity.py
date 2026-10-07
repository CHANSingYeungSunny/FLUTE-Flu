"""probe_gpt2_identity.py — decisive structural probe for the MIFlu backbone.

Answers, on a stingy compute node:
  1. where do the GPT-2-ish classes actually come from (`__module__`)?
  2. is the frozen GPT-2 actually LOADED from the pretrained reference?
     (value-based match: for every state_dict tensor, does its value equal a
      reference GPT-2 tensor value? Name-based matching failed because MIFlu
      renames `h.N` -> `blocks.N`.)
  3. which declared identity attributes exist on the model (base_model_id,
     model_id, llm name, backbone path, ...)?
  4. the resulting structural contract prefix.

Read-only: builds models and introspects. Writes only its own JSON.
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

IDENTITY_ATTRS = ("base_model_id", "model_id", "llm_name", "backbone",
                  "backbone_path", "pretrained_model_name_or_path",
                  "model_name", "hf_model_id", "text_model_id")


def attrs_of(model) -> dict:
    out = {}
    for a in IDENTITY_ATTRS:
        if hasattr(model, a):
            try:
                v = getattr(model, a)
                out[a] = v if isinstance(v, (str, int, float, bool, type(None))) \
                    else type(v).__name__
            except Exception:                                  # noqa: BLE001
                out[a] = "<error>"
    return out


def nested_attr_scan(model, maxdepth=3) -> list:
    """Look a few levels down for a stated base-model identity."""
    hits = []
    for name, mod in model.named_modules():
        if name.count(".") > maxdepth:
            continue
        for a in IDENTITY_ATTRS:
            if hasattr(mod, a):
                try:
                    v = getattr(mod, a)
                except Exception:                              # noqa: BLE001
                    continue
                if isinstance(v, str) and v:
                    hits.append({"module": name, "attr": a, "value": v})
    return hits


def class_namespaces(model, needles=("gpt2", "conv1d", "attention", "block")) -> dict:
    out = {}
    for name, mod in model.named_modules():
        cn = type(mod).__name__
        if any(x in cn.lower() for x in needles):
            out.setdefault(cn, {"n": 0, "module_ns": type(mod).__module__,
                                "sample": name})
            out[cn]["n"] += 1
    return out


def value_match(model, ref: dict) -> dict:
    """Match by VALUE against the reference GPT-2 state (name-agnostic)."""
    sd = model.state_dict()
    ref_by_hash = {}
    for k, v in ref.items():
        h = hash((tuple(v.shape), str(v.dtype),
                  hashlib_digest(v)))
        ref_by_hash.setdefault(h, []).append(k)
    matched = []
    for k, v in sd.items():
        h = hash((tuple(v.shape), str(v.dtype), hashlib_digest(v)))
        if h in ref_by_hash:
            matched.append(k)
    return {"n_model_keys": len(sd), "n_ref_keys": len(ref),
            "n_value_matched": len(matched),
            "value_matched_sample": matched[:8],
            "fraction": round(len(matched) / max(1, len(sd)), 4)}


def hashlib_digest(t: torch.Tensor) -> str:
    import hashlib
    b = t.detach().cpu().contiguous()
    return hashlib.sha256(b.numpy().tobytes()).hexdigest()[:24]


def one(name: str, horizon: int = 24) -> dict:
    out = {"model": name}
    try:
        model, base_model, enc_name, bkw = CC.build_base_model(name, horizon)
    except Exception as e:                                     # noqa: BLE001
        out["error"] = f"{type(e).__name__}: {e}"
        return out
    out["top_attrs"] = attrs_of(model)
    out["nested_identity_hits"] = nested_attr_scan(model)
    out["gpt2_class_namespaces"] = class_namespaces(model)
    try:
        from transformers import GPT2Model
        ref = {k: v.detach().cpu() for k, v in
               GPT2Model.from_pretrained("gpt2").state_dict().items()}
        out["value_match_vs_gpt2_reference"] = value_match(model, ref)
    except Exception as e:                                     # noqa: BLE001
        out["reference_error"] = f"{type(e).__name__}: {e}"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", nargs="+", required=True)
    a = ap.parse_args()
    rep = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "probes": []}
    for m in a.models:
        print(f"[probe2] {m}", flush=True)
        r = one(m)
        vm = r.get("value_match_vs_gpt2_reference") or {}
        ns = [(k, v["module_ns"])
              for k, v in (r.get("gpt2_class_namespaces") or {}).items()]
        nested = (r.get("nested_identity_hits") or [])
        print("[probe2]   value_matched=%s/%s frac=%s ns=%s attrs=%s "
              "nested=%s" % (vm.get("n_value_matched"), vm.get("n_model_keys"),
                             vm.get("fraction"), ns[:4],
                             r.get("top_attrs"), nested[:3]), flush=True)
        rep["probes"].append(r)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"[probe2] wrote {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
