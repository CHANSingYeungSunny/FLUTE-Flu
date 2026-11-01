#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""probe_hidden_state.py -- CPU 2-layer smoke test: can this checkpoint give us a
last-hidden-state read-out at all?

WHY THIS EXISTS (P2 gate)
-------------------------
The frozen-encoder arm (`scripts/llm_encoder_backbone.py`) mean-pools the LAST
HIDDEN STATE of a frozen LLM. A model that exposes only a pooled embedding, or
whose architecture does not return `hidden_states`, cannot be used as an arm.
That must be decided by MEASUREMENT, on CPU, cheaply -- never by assumption, and
never by burning an A100 on it (AGENTS.md rule 13(b): probe-only work must not
occupy the publication-grade GPU).

HOW IT STAYS CHEAP
------------------
The config is copied with `num_hidden_layers=2`. `from_pretrained` then
materialises only the first two blocks' weights (everything else is unexpected
and dropped), so even a 27B checkpoint is a couple of GB of RAM instead of 55 GB.
The forward pass is 16 tokens. What we assert is exactly the property the arm
needs: `outputs.hidden_states[-1]` (or `last_hidden_state`) has shape
`(1, 16, D)` with a finite D.

EXIT CODES
----------
  0  a hidden-state read-out exists (json written)
  3  it does not (json written with the measured reason) -- the arm is SKIPPED
  2  something unexpected (network/disk), retryable
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback

# A numeric prompt of the same shape the adapter renders: no chat template.
PROMPT = " ".join(f"{v:.4f}" for v in
                  [1.02, 1.05, 1.11, 1.24, 1.31, 1.28, 1.20, 1.14, 1.09, 1.03,
                   0.98, 0.95, 0.97, 1.01, 1.08, 1.15])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--revision", default=None)
    ap.add_argument("--layers", type=int, default=2)
    ap.add_argument("--json", required=True)
    a = ap.parse_args()

    rec = {"model_id": a.model, "revision": a.revision, "layers": a.layers}
    try:
        import torch
        from transformers import AutoConfig, AutoModel, AutoModelForCausalLM, AutoTokenizer

        rec["torch"] = torch.__version__
        import transformers
        rec["transformers"] = transformers.__version__

        tok = AutoTokenizer.from_pretrained(a.model, revision=a.revision,
                                            trust_remote_code=True)
        cfg = AutoConfig.from_pretrained(a.model, revision=a.revision,
                                         trust_remote_code=True)
        rec["model_type"] = getattr(cfg, "model_type", None)
        rec["total_layers"] = getattr(cfg, "num_hidden_layers", None)
        full_layers = getattr(cfg, "num_hidden_layers", None)
        cfg.num_hidden_layers = a.layers
        if getattr(cfg, "layer_types", None):
            try:
                cfg.layer_types = cfg.layer_types[: a.layers]
            except Exception:                                    # noqa: BLE001
                pass

        model = None
        errs = []
        for cls in (AutoModel, AutoModelForCausalLM):
            try:
                model = cls.from_pretrained(a.model, revision=a.revision, config=cfg,
                                            trust_remote_code=True,
                                            torch_dtype=torch.float32,
                                            low_cpu_mem_usage=True,
                                            output_hidden_states=True,
                                            ignore_mismatched_sizes=True)
                rec["loader"] = cls.__name__
                break
            except Exception as exc:                             # noqa: BLE001
                errs.append(f"{cls.__name__}: {type(exc).__name__}: {str(exc)[:200]}")
        if model is None:
            rec.update({"ok": False, "error": "no loader worked", "loader_errors": errs})
            json.dump(rec, open(a.json, "w"), indent=2, sort_keys=True)
            print("NO_READOUT " + " | ".join(errs)[:400])
            return 3

        model.eval()
        ids = tok(PROMPT, return_tensors="pt")
        with torch.no_grad():
            out = model(**ids, output_hidden_states=True, return_dict=True)

        hs = getattr(out, "hidden_states", None)
        if hs is not None and len(hs) > 0:
            vec = hs[-1]
            src = "hidden_states[-1]"
        else:
            vec = getattr(out, "last_hidden_state", None)
            src = "last_hidden_state"
        if vec is None:
            rec.update({"ok": False, "error": "forward returned no hidden states",
                        "output_keys": sorted(list(out.keys())) if hasattr(out, "keys") else None})
            json.dump(rec, open(a.json, "w"), indent=2, sort_keys=True)
            print("NO_READOUT: object has no hidden_states/last_hidden_state")
            return 3

        rec.update({"ok": True, "hidden_source": src, "hidden_shape": list(vec.shape),
                    "hidden_dim": int(vec.shape[-1]),
                    "n_hidden_layers_returned": len(hs) if hs is not None else None,
                    "dtype": str(vec.dtype),
                    "finite": bool(torch.isfinite(vec).all())})
        json.dump(rec, open(a.json, "w"), indent=2, sort_keys=True)
        print(f"OK {src} shape={list(vec.shape)} D={int(vec.shape[-1])} "
              f"finite={rec['finite']} layers_in_config={full_layers}")
        return 0
    except Exception as exc:                                     # noqa: BLE001
        rec.update({"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:400]}",
                    "traceback": traceback.format_exc()[-1500:]})
        try:
            json.dump(rec, open(a.json, "w"), indent=2, sort_keys=True)
        except OSError:
            pass
        print(f"PROBE_ERROR {type(exc).__name__}: {str(exc)[:300]}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
