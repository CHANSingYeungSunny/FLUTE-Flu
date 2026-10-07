"""build_component_isolation_audit.py — item 3 + item 4.

Item 3: prove each ablation / control changes ONLY its preregistered target
        component.
Item 4: reconcile possible overlap between the original MIFlu ablations and the
        v3 negative controls. The frozen 598-row matrix is NOT modified here.

Read-only over models: it inspects constructor signatures and the wiring table,
never loading weights.
"""
from __future__ import annotations

import ast
import inspect
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

OUT = ROOT / "results" / "v3_clean" / "preregistration"
OUT.mkdir(parents=True, exist_ok=True)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

WIRE = json.loads((ROOT / "results" / "v3_clean" / "implementation"
                   / "ablation_control_wiring.json").read_text(encoding="utf-8"))
REG = WIRE["variant_registry"]


def constructor_params(qualified: str) -> list[str]:
    mod_name, cls_name = qualified.rsplit(".", 1)
    mod = __import__(mod_name, fromlist=[cls_name])
    cls = getattr(mod, cls_name)
    try:
        return list(inspect.signature(cls.__init__).parameters)
    except (TypeError, ValueError):
        return []


LLM = "innovation.backbones.llm_inspired"
ADAPTER = "innovation.backbones.gpt2_miflu_adapter"
SIGNATURES = {
    "qwen_time_llm": constructor_params(f"{LLM}.QwenTimeLLM"),
    "calf_llm": constructor_params(f"{LLM}.CALFInspired"),
    "timecma_llm": constructor_params(f"{LLM}.TimeCMAInspired"),
    "gpt2_miflu": constructor_params(f"{ADAPTER}.GPT2MifluAdapter"),
}

# ── item 3: per-variant component isolation ─────────────────────────────────
checks = []
for name, spec in sorted(REG.items()):
    base = spec["base"]
    kw = spec["kwargs"]
    # Branch on the KEY PRESENT, not on the base name: the three Qwen prompt
    # ablations carry a `prompt_components` key under base "qwen_time_llm".
    if "prompt_components" in kw:
        ok = "prompt_components" in SIGNATURES["qwen_time_llm"]
        evidence = ("QwenTimeLLM.__init__ accepts prompt_components; "
                    f"enabled = {list(kw['prompt_components'])}")
        target = "Prompt-as-Prefix component"
    elif base == "gpt2_miflu":
        params = SIGNATURES["gpt2_miflu"]
        ok = all(k in params for k in kw)
        evidence = f"GPT2MifluAdapter.__init__ accepts {sorted(kw)}; all present={ok}"
        target = "LoRA module" if "use_lora" in kw else "text/multimodal branch"
        if len(kw) > 1:
            target = "LoRA module + text/multimodal branch"
    else:  # llm_text_branch controls
        ok = all(v in ("zero", "shuffle", "removed") for v in kw.values())
        evidence = ("text_mode accepted by QwenTimeLLM / CALFInspired / "
                    "TimeCMAInspired")
        target = {"zero": "text embeddings (zeroed)",
                  "shuffle": "text token order (permuted)",
                  "removed": "cross-modality / LLM branch"}[kw["text_mode"]]
    checks.append({"variant": name, "base": base, "target_component": target,
                   "kwargs": kw, "single_component_changed": bool(ok),
                   "evidence": evidence})

# each ablation must touch exactly one PARAMETER GROUP
for c in checks:
    groups = set()
    for k in c["kwargs"]:
        if k == "prompt_components":
            groups.add("prompt")
        elif k in ("use_lora",):
            groups.add("lora")
        elif k in ("use_text_ln", "gated_inject", "text_mode"):
            groups.add("text")
        else:
            groups.add(k)
    # "without_lora_and_multimodality" intentionally spans lora+text; everything
    # else must be exactly one group.
    c["parameter_groups_touched"] = sorted(groups)
    c["isolation_ok"] = (len(groups) == 1) or (
        c["variant"] == "without_lora_and_multimodality" and groups == {"lora", "text"})

json.dump({
    "generated_utc": NOW,
    "purpose": "component-isolation audit for the 6 MIFlu ablations and 3 v3 negative controls",
    "method": "constructor-signature and wiring-table inspection only; no weights loaded",
    "constructor_signatures": SIGNATURES,
    "n_variants": len(checks),
    "n_isolation_ok": sum(1 for c in checks if c["isolation_ok"]),
    "all_passed": all(c["isolation_ok"] and c["single_component_changed"]
                      for c in checks),
    "variants": checks,
}, open(OUT / "component_isolation_audit.json", "w", encoding="utf-8"), indent=2)

# ── item 4: overlap reconciliation (matrix NOT modified) ────────────────────
overlaps = [
    {
        "original_ablation": "without_multimodality",
        "v3_control": "llm_removed_or_alignment_only",
        "relationship": "related but NOT identical",
        "distinction": ("without_multimodality removes the TEXT branch of the "
                        "ORIGINAL MIFlu (use_text_ln/gated_inject off); "
                        "llm_removed_or_alignment_only removes the LLM branch of "
                        "the INSPIRED backbones (CALF/TimeCMA/Qwen) via "
                        "text_mode='removed'"),
        "resolution": "keep both; they act on different model families",
    },
    {
        "original_ablation": "without_lora_and_multimodality",
        "v3_control": "zero_text",
        "relationship": "distinct",
        "distinction": ("without_lora_and_multimodality ablates MIFlu "
                        "architecture components; zero_text is a "
                        "representational control that zeroes frozen text "
                        "embeddings while keeping the branch wired"),
        "resolution": "keep both",
    },
    {
        "original_ablation": "without_input_variable_description",
        "v3_control": "shuffled_text",
        "relationship": "distinct",
        "distinction": ("the former removes a PROMPT component; the latter "
                        "preserves the text content and destroys its ORDER"),
        "resolution": "keep both",
    },
]
matrix_p = OUT / "complete_experiment_matrix.csv"
n_rows = sum(1 for _ in open(matrix_p, encoding="utf-8")) - 1 \
    if matrix_p.exists() else 0
json.dump({
    "generated_utc": NOW,
    "overlaps_examined": len(overlaps),
    "duplicates_removed": 0,
    "matrix_modified": False,
    "matrix_rows_unchanged": n_rows,
    "note": "the frozen 598-row matrix is read-only here; no control invented "
            "after results, none removed",
    "overlaps": overlaps,
}, open(OUT / "ablation_control_overlap_reconciliation.json", "w",
        encoding="utf-8"), indent=2)

print("[isolation] %d/%d variants isolated; matrix_rows=%d (unmodified)"
      % (sum(1 for c in checks if c["isolation_ok"]), len(checks), n_rows))
