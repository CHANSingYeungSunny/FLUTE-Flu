#!/usr/bin/env python
"""audit_parameters.py — instantiate `full` and `gated_inject` MIFlu models and
record their trainable parameter counts as hard evidence for the journal audit."""
import os
import sys
import csv
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from configs import CONFIG, set_seed   # noqa: E402
from miflu_model import MIFlu          # noqa: E402

OUT = os.path.join(PROJECT_ROOT, "results", "ili", "metrics",
                   "param_audit_evidence.csv")


def audit(variant, **flags):
    set_seed(42)
    model = MIFlu(device="cpu", **flags)
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    lora_modules = getattr(model.forecasting_llm, "lora_modules", [])
    lora_params = sum(p.numel() for m in lora_modules for p in m.parameters())
    aligner = model.forecasting_llm.modality_aligner
    aligner_params = sum(p.numel() for p in aligner.parameters()) if aligner is not None else 0
    del model
    return {
        "variant": variant,
        "total_params": total,
        "trainable_params": trainable,
        "num_lora_modules": len(lora_modules),
        "lora_params": lora_params,
        "has_modality_aligner": aligner is not None,
        "modality_aligner_params": aligner_params,
    }


rows = [
    audit("full",
          use_text_ln=True, use_lora=True, gated_inject=False, unfreeze_first_k=0),
    audit("gated_inject",
          use_text_ln=True, use_lora=True, gated_inject=True, unfreeze_first_k=2),
]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
fields = ["variant", "total_params", "trainable_params", "num_lora_modules",
          "lora_params", "has_modality_aligner", "modality_aligner_params"]
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"[audit] wrote {OUT}")
for r in rows:
    print(r)
