#!/usr/bin/env python3
"""Aggregate Wave-1 accepted durable metrics into a single JSONL dataset.

Reads every ``*__w1`` durable run directory under
``/home/sychan552/innovation_durable/screening`` and extracts the four frozen
metric families plus resource/storage fields:

  1. paper_aligned_full_output_metrics.json  -> mse/mae_all_7vars_full_horizon_z
  2. ilitotal_fixed_step_metrics.json        -> ILITOTAL steps 0/1/2/3
  3. ilitotal_full_horizon_metrics.json      -> ILITOTAL full horizon
  4. pte_pie_metrics.json                    -> PTE/PIE (1-week / 25% thresholds)
  + resource_usage.json / compact_manifest.json / finalize_manifest.json

Pure I/O + JSON parsing: no model loads, no inference, no test/holdout access.
"""
import json
from pathlib import Path

DU = Path("/home/sychan552/innovation_durable/screening")
OUT = Path("/scratch/sychan552/wave1_analysis_dataset.jsonl")

NON_LLM = {"nlinear", "dlinear", "patchtst", "itransformer"}
LLM = {"gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"}


def family(arm: str, model: str) -> str:
    if arm == "primary":
        if model in NON_LLM:
            return "non_llm"
        if model in LLM:
            return "llm"
        return "primary_other"
    return arm  # ablation / baseline / negative_control


def jload(d: Path, rel: str) -> dict:
    p = d / rel
    try:
        return json.loads(p.read_text()) if p.exists() else {}
    except Exception as e:
        return {"__error__": f"{type(e).__name__}: {e}"}


rows = []
errors = []
for d in sorted(DU.glob("*__w1")):
    rk = d.name[:-4]  # strip "__w1"
    parts = rk.split("__")
    if len(parts) < 4:
        errors.append(f"malformed run_key {rk}")
        continue
    arm, model = parts[0], parts[1]
    horizon = int(parts[2][1:]) if parts[2].startswith("L") else None
    seed_s = parts[3]
    seed = int(seed_s[4:]) if seed_s.startswith("seed") and seed_s[4:].isdigit() else "na"

    rec = {"run_key": rk, "arm": arm, "model": model, "horizon": horizon,
           "seed": seed, "family": family(arm, model)}

    pm = jload(d, "metrics/paper_aligned_full_output_metrics.json")
    rec["mse_all_7vars_full_horizon_z"] = pm.get("mse_all_7vars_full_horizon_z")
    rec["mae_all_7vars_full_horizon_z"] = pm.get("mae_all_7vars_full_horizon_z")
    rec["n_elements"] = pm.get("n_elements")
    rec["complete_seven_variable_output"] = pm.get("complete_seven_variable_output")

    ih = jload(d, "metrics/ilitotal_full_horizon_metrics.json")
    rec["ilitotal_full_mse_z"] = ih.get("mse_z")
    rec["ilitotal_full_mae_z"] = ih.get("mae_z")
    rec["ilitotal_full_mse_phys"] = ih.get("mse_physical")
    rec["ilitotal_full_mae_phys"] = ih.get("mae_physical")
    rec["ilitotal_full_n"] = ih.get("n")

    fs = jload(d, "metrics/ilitotal_fixed_step_metrics.json")
    for s in ("0", "1", "2", "3"):
        st = fs.get("steps", {}).get(s, {})
        rec[f"step{s}_mse_z"] = st.get("mse_z")
        rec[f"step{s}_mae_z"] = st.get("mae_z")
        rec[f"step{s}_mse_phys"] = st.get("mse_physical")
        rec[f"step{s}_mae_phys"] = st.get("mae_physical")
        rec[f"step{s}_n"] = st.get("n")

    pp = jload(d, "metrics/pte_pie_metrics.json")
    for s in ("0", "1", "2", "3"):
        st = pp.get("steps", {}).get(s, {})
        rec[f"step{s}_pte"] = st.get("PTE_weeks")
        rec[f"step{s}_pie"] = st.get("PIE_percent")
        rec[f"step{s}_peak_timing"] = st.get("accurate_peak_timing")
        rec[f"step{s}_peak_intensity"] = st.get("accurate_peak_intensity")

    ru = jload(d, "resource_usage.json")
    rec["best_epoch"] = ru.get("best_epoch")
    rec["best_val_mse"] = ru.get("best_val_mse")
    rec["train_seconds"] = ru.get("train_seconds")
    rec["trainable_parameters"] = ru.get("trainable_parameters")

    cm = jload(d, "compact_manifest.json")
    fm = jload(d, "finalize_manifest.json")
    rec["compact_bytes"] = cm.get("compact_bytes", fm.get("compact_bytes"))
    rec["source_bytes"] = cm.get("source_bytes")
    rec["compression_ratio"] = cm.get("compression_ratio")

    rows.append(rec)

with OUT.open("w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")

print("aggregated", len(rows), "rows ->", OUT)
if errors:
    print("ERRORS:", len(errors))
    for e in errors:
        print("  ", e)
