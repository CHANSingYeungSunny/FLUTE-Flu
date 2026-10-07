"""ckpt_schema_probe.py — READ-ONLY checkpoint structure probe (v3.13 step 6).

Runs on a stingy COMPUTE node (it loads torch checkpoints). It does NOT train,
evaluate, or modify anything: it only loads each checkpoint, reports its
structure (top-level container type, key prefixes, dtypes, byte sizes) and
writes a JSON report.

Purpose: determine, per model/checkpoint schema, WHICH keys are the frozen
pretrained backbone (the per-row duplication we must eliminate) and which keys
are the trainable reconstruction-critical state.

Usage:
  python ckpt_schema_probe.py --out report.json path1.pt path2.pt ...
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import time

import torch


def _unwrap(obj):
    """Return (state_dict_like, container_description)."""
    if isinstance(obj, dict):
        keys = list(obj.keys())
        for k in ("state_dict", "model_state_dict", "model"):
            if k in obj and isinstance(obj[k], dict):
                return obj[k], f"dict[{k}] (top keys={keys[:8]})"
        # a plain state_dict has only tensor values
        if keys and all(torch.is_tensor(v) for v in obj.values()):
            return obj, f"plain state_dict (n={len(keys)})"
        # mixed dict: report and take the tensor subset
        tens = {k: v for k, v in obj.items() if torch.is_tensor(v)}
        if tens:
            return tens, (f"mixed dict (non-tensor keys="
                          f"{[k for k in keys if k not in tens][:10]})")
        return {}, f"no tensors found (top keys={keys[:10]})"
    return {}, f"unexpected type {type(obj).__name__}"


def probe(path: str) -> dict:
    rec = {"path": path, "exists": os.path.exists(path)}
    if not rec["exists"]:
        rec["error"] = "missing"
        return rec
    rec["file_bytes"] = os.path.getsize(path)
    try:
        obj = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as e:                                    # noqa: BLE001
        rec["error"] = f"{type(e).__name__}: {e}"
        return rec
    sd, desc = _unwrap(obj)
    rec["container"] = desc
    rec["n_keys"] = len(sd)

    prefixes = collections.defaultdict(lambda: {"n": 0, "bytes": 0,
                                                "dtypes": set()})
    total = 0
    for k, v in sd.items():
        if not torch.is_tensor(v):
            continue
        nbytes = v.numel() * v.element_size()
        total += nbytes
        pre = k.split(".")[0]
        p = prefixes[pre]
        p["n"] += 1
        p["bytes"] += nbytes
        p["dtypes"].add(str(v.dtype))
    rec["total_tensor_bytes"] = total
    rec["top_level_prefixes"] = {
        k: {"n_keys": v["n"], "bytes": v["bytes"],
            "mib": round(v["bytes"] / 1048576, 3),
            "dtypes": sorted(v["dtypes"])}
        for k, v in sorted(prefixes.items(), key=lambda kv: -kv[1]["bytes"])}
    # the largest single tensors tell us where the frozen backbone sits
    big = sorted(((v.numel() * v.element_size(), k) for k, v in sd.items()
                  if torch.is_tensor(v)), reverse=True)[:8]
    rec["largest_tensors"] = [{"bytes": b, "key": k} for b, k in big]
    rec["sample_keys"] = list(sd.keys())[:25]
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("paths", nargs="+")
    a = ap.parse_args()
    rep = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "torch": torch.__version__, "n_paths": len(a.paths), "probes": []}
    for p in a.paths:
        print(f"[probe] {p}", flush=True)
        r = probe(p)
        print(f"[probe]   keys={r.get('n_keys')} "
              f"bytes={r.get('total_tensor_bytes')} "
              f"err={r.get('error')}", flush=True)
        if r.get("top_level_prefixes"):
            for k, v in list(r["top_level_prefixes"].items())[:6]:
                print(f"[probe]     {k}: {v['n_keys']} keys "
                      f"{v['mib']} MiB", flush=True)
        rep["probes"].append(r)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"[probe] wrote {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
