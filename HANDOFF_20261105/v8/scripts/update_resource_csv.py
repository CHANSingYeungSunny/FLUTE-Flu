# -*- coding: utf-8 -*-
"""Fold the T6 final-sweep A100 measurements into RESOURCE_MEASUREMENTS.csv.

All numbers come from sbatch 744897 (t6_final_sweep), 744899 (MIFlu fix),
744532 (MIFlu first measurement) and 744886 (full80). Nothing is invented.
The earlier NPZ scoring-path latencies are PRESERVED in dedicated columns and
explicitly labelled as NOT a model forward.
"""
import csv
from pathlib import Path

P = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu\HANDOFF_20261105\v8\RESOURCE_MEASUREMENTS.csv")

NEW_COLS = ["npz_scoring_path_latency_ms_mean", "npz_scoring_path_latency_ms_std",
            "vram_n_samples", "model_load_s", "measurement_job_ids",
            "measured_forward_wall_s"]

MIFLU = {
    "peak_vram_mib": "4816", "vram_n_samples": "46 (job 744899) / 63 (job 744532)",
    "vram_source": "sbatch 744899 + 744532, nvidia-smi memory.used 1s sampling, stingy gpu-a100-03/05, A100-SXM4-80GB",
    "gpu_model": "NVIDIA A100-SXM4-80GB", "measurement_job_ids": "744532;744899;744897",
    "software_versions": "Python 3.9.25; torch 2.5.1; driver 580.167.08; GNU time 1.9",
    "status": "MEASURED (subset only; NOT full-1120)",
    "true_model_forward_latency_ms": "NOT_MEASURED (isolated single forward); full 7-channel cell export wall = 62.94 s",
    "inference_latency_kind": "REAL full-cell model export (62.94 s); isolated warm-up+repeated forward NOT MEASURED",
    "real_model_forward_wall_s": "62.94", "measured_forward_wall_s": "62.94",
    "model_load_s": "NOT_MEASURED separately",
    "blocker_reason_or_notes": "peak VRAM measured on a real A100 forward from checkpoint; old NPZ scoring-path latency moved to npz_scoring_path_* and is NOT a model forward",
}
NLINEAR = {
    "peak_vram_mib": "558", "vram_n_samples": "36",
    "vram_source": "sbatch t6_final_sweep 744897, nvidia-smi memory.used 1s sampling, stingy gpu-a100-03, A100-SXM4-80GB",
    "gpu_model": "NVIDIA A100-SXM4-80GB", "measurement_job_ids": "744897",
    "software_versions": "Python 3.9.25; torch 2.5.1; driver 580.167.08; GNU time 1.9",
    "status": "MEASURED (subset only; NOT full-1120)",
    "true_model_forward_latency_ms": "NOT_MEASURED (isolated single forward); full training+inference job wall = 35.73 s",
    "inference_latency_kind": "REAL train_backbone_966.py training+inference job (35.73 s); isolated warm-up+repeated forward NOT MEASURED",
    "real_model_forward_wall_s": "NOT_MEASURED (job includes training)",
    "measured_forward_wall_s": "35.73 (train+inference job)",
    "model_load_s": "NOT_MEASURED separately",
    "blocker_reason_or_notes": "peak VRAM measured during a real 20-epoch NLinear training+export run on A100",
}
PATCHTST = {
    "peak_vram_mib": "720", "vram_n_samples": "7",
    "vram_source": "sbatch t6_final_sweep 744897, nvidia-smi memory.used 1s sampling, stingy gpu-a100-03, A100-SXM4-80GB",
    "gpu_model": "NVIDIA A100-SXM4-80GB", "measurement_job_ids": "744897",
    "software_versions": "Python 3.9.25; torch 2.5.1; driver 580.167.08; GNU time 1.9",
    "status": "MEASURED (subset only; NOT full-1120)",
    "true_model_forward_latency_ms": "NOT_MEASURED (isolated single forward); full training+inference job wall = 6.86 s",
    "inference_latency_kind": "REAL train_backbone_966.py training+inference job (6.86 s); isolated warm-up+repeated forward NOT MEASURED",
    "real_model_forward_wall_s": "NOT_MEASURED (job includes training)",
    "measured_forward_wall_s": "6.86 (train+inference job)",
    "model_load_s": "NOT_MEASURED separately",
    "blocker_reason_or_notes": "peak VRAM measured during a real 20-epoch PatchTST training+export run on A100",
}
GPT2 = {
    "peak_vram_mib": "1070", "vram_n_samples": "11",
    "vram_source": "sbatch t6_final_sweep 744897 warm-up+repeated GPT-2 forward, nvidia-smi memory.used 1s sampling, A100-SXM4-80GB",
    "gpu_model": "NVIDIA A100-SXM4-80GB", "measurement_job_ids": "744897",
    "software_versions": "Python 3.11.13; torch 2.6.0+cu124; transformers 5.22.1; driver 580.167.08",
    "status": "MEASURED (subset only; NOT full-1120)",
    "inference_latency_ms_mean": "6.98", "inference_latency_ms_std": "0.097",
    "warmup_runs": "1", "repeat_runs": "10",
    "true_model_forward_latency_ms": "6.98", "measured_forward_wall_s": "0.00698",
    "model_load_s": "6.3224",
    "inference_latency_kind": "REAL frozen GPT-2 forward, warm-up 1 + repeat 10, batch=1 seq x 104 tokens, float32",
    "batch": "1 sequence x 104 tokens", "precision": "float32",
    "training_wall_s": "NOT_APPLICABLE (frozen encoder)",
    "blocker_reason_or_notes": "Representative frozen encoder measured is GPT-2 from the pinned local HF cache; the earlier 24 s queue-log training wall belonged to DeepSeek-R1-Distill-Qwen-1.5B (a DIFFERENT encoder) and is retained only as context, not as this row measurement",
}
CHRONOS = {
    "peak_vram_mib": "596", "vram_n_samples": "6",
    "vram_source": "sbatch t6_final_sweep 744897 warm-up+repeated forward, nvidia-smi memory.used 1s sampling, A100-SXM4-80GB",
    "gpu_model": "NVIDIA A100-SXM4-80GB", "measurement_job_ids": "744589;744607;744886;744897",
    "software_versions": "Python 3.11.13; torch 2.6.0+cu124; chronos-forecasting 2.3.2; driver 580.167.08",
    "status": "MEASURED (subset only; NOT full-1120)",
    "inference_latency_ms_mean": "9.854", "inference_latency_ms_std": "0.337",
    "warmup_runs": "1", "repeat_runs": "20",
    "true_model_forward_latency_ms": "9.854", "measured_forward_wall_s": "0.009854",
    "model_load_s": "0.4307",
    "inference_latency_kind": "REAL model forward, warm-up 1 + repeat 20, batch=7 independent series, float32",
    "batch": "7 independent series per call", "precision": "float32",
    "training_wall_s": "NOT_APPLICABLE (frozen zero-shot, no training)",
    "blocker_reason_or_notes": "Independent confirmation: full80 job 744886 measured 10.229 +/- 1.074 ms (repeat 10) and peak VRAM 2608 MiB for the combined 2-model run",
}
TIMESFM = {
    "peak_vram_mib": "2594", "vram_n_samples": "11",
    "vram_source": "sbatch t6_final_sweep 744897 warm-up+repeated forward, nvidia-smi memory.used 1s sampling, A100-SXM4-80GB",
    "gpu_model": "NVIDIA A100-SXM4-80GB", "measurement_job_ids": "744607;744886;744897",
    "software_versions": "Python 3.11.13; torch 2.6.0+cu124; timesfm 1.3.0; driver 580.167.08",
    "status": "MEASURED (subset only; NOT full-1120)",
    "inference_latency_ms_mean": "48.273", "inference_latency_ms_std": "3.531",
    "warmup_runs": "1", "repeat_runs": "10",
    "true_model_forward_latency_ms": "48.273", "measured_forward_wall_s": "0.048273",
    "model_load_s": "6.9875",
    "inference_latency_kind": "REAL model forward, warm-up 1 + repeat 10, batch=7 independent series, float32, freq=1",
    "batch": "7 independent series per call", "precision": "float32",
    "training_wall_s": "NOT_APPLICABLE (frozen zero-shot, no training)",
    "blocker_reason_or_notes": "Independent confirmation: full80 job 744886 measured 50.906 +/- 4.459 ms (repeat 5); horizon_len=128 then sliced to L",
}

rows = list(csv.DictReader(P.open(encoding="utf-8", newline="")))
cols = list(rows[0].keys())
for c in NEW_COLS:
    if c not in cols:
        cols.append(c)

for r in rows:
    m = r["model"]
    if m.startswith("DeepSeek-R1"):
        r["model"] = "GPT-2 (frozen language encoder)"
        m = r["model"]
    # preserve the old NPZ scoring-path latency before overwriting
    old = r.get("inference_latency_ms_mean", "")
    if old and old.replace(".", "", 1).isdigit():
        r["npz_scoring_path_latency_ms_mean"] = old
        r["npz_scoring_path_latency_ms_std"] = r.get("inference_latency_ms_std", "")
    mapping = {"MIFlu": MIFLU, "NLinear": NLINEAR, "PatchTST": PATCHTST,
               "GPT-2 (frozen language encoder)": GPT2,
               "Chronos": CHRONOS, "TimesFM": TIMESFM}
    if m in mapping:
        r.update(mapping[m])
    r["scope"] = "subset_only_not_full_1120"
    r["evidence_path"] = ("v8/resource_logs/final_sweep/; "
                          "v8/resource_logs/t6sweep_744897.out; v8/T6_FINAL_SWEEP.md")
    for c in cols:
        r.setdefault(c, "")

with P.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print("CSV_UPDATED rows", len(rows), "cols", len(cols))
for r in rows:
    print(" ", r["model"], "VRAM", r["peak_vram_mib"],
          "forward_lat", r["true_model_forward_latency_ms"][:52])
