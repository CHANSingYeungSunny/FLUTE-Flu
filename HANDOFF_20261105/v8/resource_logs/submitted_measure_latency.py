#!/usr/bin/env python
# TASK 6 / t6_res - NPZ SCORING-PATH LATENCY MEASUREMENT.
#
# IMPORTANT LABEL: this is "NPZ scoring-path latency", NOT a model forward pass.
# We load an existing prediction NPZ (pred/target arrays of shape (W,7,L)) and
# time a deterministic repeated scoring operation:
#       np.mean((pred - target) ** 2)
# after an explicit warm-up. No checkpoint, no torch, no model weights are used.
# AGENTS.md RULE 1: this Python/NPZ work runs INSIDE an sbatch compute-node job.
import os
import json
import time
import hashlib
import datetime
import numpy as np

BASE = "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res"
LOGS = os.path.join(BASE, "logs")
NPZ_ROOT = "/gpfs1/home/sychan552/stage5_a2_durable/expanded_runs"

WARMUP = 5
REPEAT = 50

MODELS = [
    {"subset_label": "MIFlu",
     "npz": os.path.join(NPZ_ROOT, "miflu_L24_s42", "pred_miflu_L24_s42.npz")},
    {"subset_label": "NLinear",
     "npz": os.path.join(NPZ_ROOT, "nlinear_L24_s42", "pred_nlinear_L24_s42.npz")},
    {"subset_label": "PatchTST",
     "npz": os.path.join(NPZ_ROOT, "patchtst_L24_s42", "pred_patchtst_L24_s42.npz")},
    {"subset_label": "DeepSeek-R1-Distill-Qwen-1.5B (frozen encoder)",
     "npz": os.path.join(NPZ_ROOT, "ds_r1_distill_qwen1_5b_L24_s42",
                         "pred_ds_r1_distill_qwen1_5b_L24_s42.npz")},
]

os.makedirs(LOGS, exist_ok=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def mean_std(xs):
    n = len(xs)
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    return mean, var ** 0.5


results = []
for m in MODELS:
    path = m["npz"]
    label = m["subset_label"]
    rec = {"subset_label": label, "npz_path": path,
           "label": "NPZ scoring-path latency (NOT a model forward pass)",
           "warmup_runs": WARMUP, "repeat_runs": REPEAT}
    if not os.path.exists(path):
        rec["status"] = "NOT_MEASURED"
        rec["reason"] = "prediction NPZ file does not exist"
        results.append(rec)
        print(f"[{label}] NOT_MEASURED: npz missing")
        continue
    t_load0 = time.perf_counter()
    z = np.load(path, allow_pickle=False)
    pred = np.asarray(z["pred"])
    target = np.asarray(z["target"])
    z.close()
    t_load1 = time.perf_counter()
    load_ms = (t_load1 - t_load0) * 1000.0
    if pred.shape != target.shape or pred.ndim != 3:
        rec["status"] = "NOT_MEASURED"
        rec["reason"] = f"unexpected array shape pred={pred.shape} target={target.shape}"
        results.append(rec)
        continue

    # The deterministic scoring-path operation (mirrors MSE scoring forward).
    def scoring_op():
        return float(np.mean((pred - target) ** 2))

    for _ in range(WARMUP):          # explicit warm-up, NOT timed
        _ = scoring_op()

    per_iter_ms = []
    for _ in range(REPEAT):          # timed repeats
        t0 = time.perf_counter()
        mse = scoring_op()
        t1 = time.perf_counter()
        per_iter_ms.append((t1 - t0) * 1000.0)

    mean_ms, std_ms = mean_std(per_iter_ms)
    rec.update({
        "status": "MEASURED",
        "measurement_kind": "NPZ_scoring_path_only_NOT_model_forward",
        "npz_load_ms_once": round(load_ms, 4),
        "npz_bytes": os.path.getsize(path),
        "npz_sha256": sha256(path),
        "pred_shape": list(pred.shape),
        "target_shape": list(target.shape),
        "dtype": str(pred.dtype),
        "batch_W_windows": int(pred.shape[0]),
        "channels": int(pred.shape[1]),
        "horizon_L": int(pred.shape[2]),
        "mse_value": mse,
        "mean_ms": mean_ms,
        "std_ms": std_ms,
        "min_ms": min(per_iter_ms),
        "max_ms": max(per_iter_ms),
        "per_iteration_ms": per_iter_ms,
    })
    results.append(rec)
    print(f"[{label}] MEASURED NPZ-scoring-path: mean={mean_ms:.4f}ms std={std_ms:.4f}ms "
          f"warmup={WARMUP} repeat={REPEAT} shape={pred.shape} dtype={pred.dtype}")

out = {
    "utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "label": "NPZ scoring-path latency (NOT a model forward pass)",
    "warning": "These numbers are NPZ load + vectorized MSE scoring latency on CPU; "
               "they are NOT neural-network inference latency and MUST NOT be "
               "reported as a model forward pass.",
    "warmup_runs": WARMUP,
    "repeat_runs": REPEAT,
    "results": results,
}
with open(os.path.join(LOGS, "npz_scoring_latency.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, sort_keys=True)

# Flat TSV for the CSV build.
with open(os.path.join(LOGS, "npz_scoring_latency.tsv"), "w", encoding="utf-8") as f:
    f.write("\t".join(["subset_label", "status", "mean_ms", "std_ms", "min_ms", "max_ms",
                       "warmup_runs", "repeat_runs", "batch_W_windows", "channels",
                       "horizon_L", "dtype", "npz_bytes", "npz_load_ms_once",
                       "npz_sha256", "npz_path"]) + "\n")
    for r in results:
        if r["status"] != "MEASURED":
            f.write("\t".join([r["subset_label"], r["status"], "NA", "NA", "NA", "NA",
                               str(r["warmup_runs"]), str(r["repeat_runs"]), "NA", "NA",
                               "NA", "NA", "NA", "NA", "NA", r["npz_path"]]) + "\n")
        else:
            f.write("\t".join([r["subset_label"], r["status"], f"{r['mean_ms']:.6f}",
                               f"{r['std_ms']:.6f}", f"{r['min_ms']:.6f}", f"{r['max_ms']:.6f}",
                               str(r["warmup_runs"]), str(r["repeat_runs"]),
                               str(r["batch_W_windows"]), str(r["channels"]),
                               str(r["horizon_L"]), r["dtype"], str(r["npz_bytes"]),
                               f"{r['npz_load_ms_once']:.4f}", r["npz_sha256"],
                               r["npz_path"]]) + "\n")

print("MEASURE_LATENCY_OK measured=", sum(1 for r in results if r["status"] == "MEASURED"))
