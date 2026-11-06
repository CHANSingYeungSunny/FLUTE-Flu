#!/usr/bin/env python
# Build v8/RESOURCE_MEASUREMENTS.csv from the REAL raw logs saved by job 744239.
# No value is invented: every numeric entry is read from a log file under
# v8/resource_logs/. Everything else is NOT_MEASURED with an exact reason.
import csv
import json
import os

ROOT = "C:/Users/Asus/Desktop/FYP code/MLFlu"
V8 = os.path.join(ROOT, "HANDOFF_20261105", "v8")
LOG = os.path.join(V8, "resource_logs")
OUT = os.path.join(V8, "RESOURCE_MEASUREMENTS.csv")

SCOPE = "subset_only_not_full_1120"
SUBSET = "representative_subset_6_models"


def read_tsv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


wall = {r["subset_label"]: r for r in read_tsv(os.path.join(LOG, "training_wall_targets.tsv"))}
lat = {r["subset_label"]: r for r in read_tsv(os.path.join(LOG, "npz_scoring_latency.tsv"))}

with open(os.path.join(LOG, "versions.json"), "r", encoding="utf-8") as f:
    ver = json.load(f)
SW = ("Python {py}; numpy {np}; pandas {pd}; torch {th} "
      "(torch.cuda.is_available={tc} on job 744239); GNU time 1.9").format(
    py=ver["python_version"].split(" (")[0],
    np=ver["numpy"], pd=ver["pandas"], th=ver["torch"],
    tc=str(ver["torch_cuda_available"]).lower())

VRAM_BLOCKER = (
    "NOT_MEASURED (no GPU allocated in this job: job 744239 used "
    "--partition=tiny with no --gres=gpu, nvidia-smi absent; GPU attempts failed: "
    "job 744253 t6_res_gpu PENDING Reason=Priority StartTime=2026-11-08T02:25:47Z "
    "-> time-boxed and cancelled 2026-11-06T13:56:49Z; t6_res_gpu_stingy sbatch "
    "rejected twice with 'QOSMaxSubmitJobPerUserLimit' rc=1. See "
    "resource_logs/peak_vram_mib.txt, resource_logs/gpu_attempts_state.txt, "
    "resource_logs/t6_gpu_attempts_transcript.txt)"
)

TRUE_FWD_BLOCKER = (
    "NOT_MEASURED (no GPU job ever started; real model-forward latency was not "
    "measured. The only latency measured is NPZ scoring-path latency, explicitly "
    "NOT a model forward pass. See resource_logs/t6_gpu_attempts_transcript.txt)"
)

BLOCK_REASON = (
    "TASK 2 is BLOCKED (v8/foundation/T2_VERDICT.md sec.6/8): no full pinned "
    "weights downloaded, no isolated HPC env (/home/sychan552/.venvs/mlflu_fm), "
    "no 1-cell pilot. No prediction NPZ, no wall time, no VRAM, no latency exist."
)

FIELDS = [
    "model", "subset", "scope",
    "training_wall_s", "training_wall_source",
    "peak_vram_mib", "vram_source",
    "inference_latency_ms_mean", "inference_latency_ms_std",
    "warmup_runs", "repeat_runs", "batch", "precision",
    "gpu_model", "software_versions", "status", "evidence_path",
    "training_wall_n_cells", "training_wall_mean_s_over_n_cells",
    "inference_latency_kind", "true_model_forward_latency_ms",
    "npz_source_path", "npz_sha256", "blocker_reason_or_notes",
]

rows = []

MEASURED = [
    ("MIFlu", "MIFlu"),
    ("NLinear", "NLinear"),
    ("PatchTST", "PatchTST"),
    ("DeepSeek-R1-Distill-Qwen-1.5B (frozen language encoder)",
     "DeepSeek-R1-Distill-Qwen-1.5B (frozen encoder)"),
]

for model, key in MEASURED:
    w = wall[key]
    l = lat[key]
    tw_src = ("{sf}:L{ln} task_id={tid} last_job={job} note='{note}'; "
              "raw=resource_logs/training_wall_extraction.tsv + "
              "resource_logs/training_wall_targets.tsv (job 744239)").format(
        sf=w["source_file"], ln=w["rep_line_no"], tid=w["rep_task_id"],
        job=w["rep_last_job"], note=w["rep_raw_note"].strip())
    rows.append({
        "model": model,
        "subset": SUBSET,
        "scope": SCOPE,
        "training_wall_s": w["rep_wall_s"],
        "training_wall_source": tw_src,
        "peak_vram_mib": "NOT_MEASURED",
        "vram_source": VRAM_BLOCKER,
        "inference_latency_ms_mean": l["mean_ms"],
        "inference_latency_ms_std": l["std_ms"],
        "warmup_runs": l["warmup_runs"],
        "repeat_runs": l["repeat_runs"],
        "batch": l["batch_W_windows"] + " (W windows in one vectorized op)",
        "precision": l["dtype"] + " (source NPZ array dtype)",
        "gpu_model": "NONE (job 744239: --partition=tiny, no --gres=gpu; nvidia-smi not present)",
        "software_versions": SW,
        "status": "MEASURED (subset only; NOT full-1120)",
        "evidence_path": ("HANDOFF_20261105/v8/resource_logs/training_wall_targets.tsv; "
                          "HANDOFF_20261105/v8/resource_logs/training_wall_extraction.tsv; "
                          "HANDOFF_20261105/v8/resource_logs/npz_scoring_latency.tsv; "
                          "HANDOFF_20261105/v8/resource_logs/time_v_latency.txt; "
                          "HANDOFF_20261105/v8/resource_logs/versions.json"),
        "training_wall_n_cells": w["n_cells"],
        "training_wall_mean_s_over_n_cells": w["mean_s"],
        "inference_latency_kind": ("NPZ scoring-path latency ONLY "
                                   "(repeated np.mean((pred-target)**2) over (W,7,L)); "
                                   "NOT a model forward pass"),
        "true_model_forward_latency_ms": TRUE_FWD_BLOCKER,
        "npz_source_path": l["npz_path"],
        "npz_sha256": l["npz_sha256"],
        "blocker_reason_or_notes": (
            "training_wall_s is ONE real historical per-cell queue measurement "
            "(master_queue.tsv note 'wall=NNNs'), NOT re-timed by T6; "
            "n_cells and mean_s are derived from the saved extraction log. "
            "Historical A100 provenance: 02_数字表格/BENCH_GPU_PROVENANCE.csv "
            "(not re-measured). peak_vram_mib and true model-forward latency are "
            "NOT_MEASURED: no GPU job ran."),
    })

for model in ("Chronos", "TimesFM"):
    rows.append({
        "model": model,
        "subset": SUBSET,
        "scope": SCOPE,
        "training_wall_s": "NOT_MEASURED",
        "training_wall_source": "NOT_MEASURED (" + BLOCK_REASON + ")",
        "peak_vram_mib": "NOT_MEASURED",
        "vram_source": "NOT_MEASURED (" + BLOCK_REASON + ")",
        "inference_latency_ms_mean": "NOT_MEASURED",
        "inference_latency_ms_std": "NOT_MEASURED",
        "warmup_runs": "NOT_MEASURED",
        "repeat_runs": "NOT_MEASURED",
        "batch": "NOT_MEASURED",
        "precision": "NOT_MEASURED",
        "gpu_model": "NOT_MEASURED",
        "software_versions": "NOT_MEASURED (no isolated FM env created)",
        "status": "BLOCKED / NOT_EXECUTED",
        "evidence_path": ("HANDOFF_20261105/v8/foundation/T2_VERDICT.md; "
                          "HANDOFF_20261105/v8/foundation/FOUNDATION_MODEL_PROVENANCE.md; "
                          "HANDOFF_20261105/v8/foundation/FOUNDATION_ROSTER.csv"),
        "training_wall_n_cells": "NOT_MEASURED",
        "training_wall_mean_s_over_n_cells": "NOT_MEASURED",
        "inference_latency_kind": "NOT_MEASURED (no prediction NPZ exists)",
        "true_model_forward_latency_ms": "NOT_MEASURED (" + BLOCK_REASON + ")",
        "npz_source_path": "NOT_MEASURED",
        "npz_sha256": "NOT_MEASURED",
        "blocker_reason_or_notes": BLOCK_REASON,
    })

with open(OUT, "w", encoding="utf-8", newline="") as f:
    wtr = csv.DictWriter(f, fieldnames=FIELDS)
    wtr.writeheader()
    for r in rows:
        wtr.writerow(r)

print("WROTE", OUT)
print("rows =", len(rows), " columns =", len(FIELDS))
