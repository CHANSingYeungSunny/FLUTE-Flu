#!/usr/bin/env python3
"""Measure warm-up + repeated inference latency for one model inside sbatch."""
import argparse
import importlib
import json
import os
import time

import numpy as np
import pandas as pd
import torch

ROOT = "/gpfs1/scratch/sychan552/stage5_a2_durable"
BASE = f"{ROOT}/code/queue/t2_fm"
ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True,
                choices=["chronos", "timesfm", "frozen_encoder"])
a = ap.parse_args()

dev = "cuda" if torch.cuda.is_available() else "cpu"
out = {"model": a.model, "device": dev,
       "gpu": torch.cuda.get_device_name(0) if dev == "cuda" else "NONE",
       "torch": torch.__version__, "python": __import__("sys").version.split()[0]}


def sync():
    if dev == "cuda":
        torch.cuda.synchronize()


df = pd.read_csv(f"{ROOT}/data/raw/national_illness_author_repo_966.csv")
cols = [c for c in df.columns if c != "date"]
sc = json.load(open(f"{ROOT}/data/scaler_miflu_author966.json"))
Z = (df[cols].to_numpy(dtype=np.float64) - np.asarray(sc["mean"])) / np.asarray(sc["std"])
ctx = Z[773 - 104:773]                       # (104,7)
ctx_t = torch.tensor(ctx.T, dtype=torch.float32)

if a.model == "chronos":
    from chronos import ChronosBoltPipeline
    p = f"{BASE}/extracted/chronos_bolt_tiny/chronos_bolt_tiny"
    t0 = time.perf_counter()
    pipe = ChronosBoltPipeline.from_pretrained(p, local_files_only=True, device_map=dev)
    out["load_s"] = round(time.perf_counter() - t0, 4)
    pipe.predict(ctx_t[:1], prediction_length=24); sync()
    lat = []
    for _ in range(20):
        t = time.perf_counter()
        pipe.predict(ctx_t, prediction_length=24); sync()
        lat.append((time.perf_counter() - t) * 1000.0)
    out.update({"warmup_runs": 1, "repeat_runs": 20,
                "batch": "7 independent series", "precision": "float32",
                "latency_mean_ms": round(float(np.mean(lat)), 3),
                "latency_std_ms": round(float(np.std(lat)), 3),
                "status": "MEASURED"})

elif a.model == "timesfm":
    import timesfm
    ck = f"{BASE}/extracted/timesfm_2_0_500m_pytorch/timesfm_2_0_500m_pytorch/torch_model.ckpt"
    t0 = time.perf_counter()
    hp = timesfm.TimesFmHparams(backend="gpu" if dev == "cuda" else "cpu",
                                per_core_batch_size=32, horizon_len=128,
                                context_len=512, input_patch_len=32,
                                output_patch_len=128, num_layers=50,
                                model_dims=1280, use_positional_embedding=False)
    tfm = timesfm.TimesFm(hparams=hp, checkpoint=timesfm.TimesFmCheckpoint(
        version="torch", path=ck))
    out["load_s"] = round(time.perf_counter() - t0, 4)
    inputs = [ctx[:, c] for c in range(7)]
    tfm.forecast(inputs, freq=[1] * 7); sync()
    lat = []
    for _ in range(10):
        t = time.perf_counter()
        tfm.forecast(inputs, freq=[1] * 7); sync()
        lat.append((time.perf_counter() - t) * 1000.0)
    out.update({"warmup_runs": 1, "repeat_runs": 10,
                "batch": "7 independent series", "precision": "float32",
                "freq_indicator": 1,
                "latency_mean_ms": round(float(np.mean(lat)), 3),
                "latency_std_ms": round(float(np.std(lat)), 3),
                "status": "MEASURED"})

else:  # frozen_encoder
    import glob
    candidates = [
        f"{ROOT}/hf_cache/hub", f"{ROOT}/hf_cache",
        "/gpfs1/scratch/sychan552/stage5_a2_durable/hf_cache/hub",
        "/gpfs1/scratch/sychan552/stage5_a2_durable/hf_cache",
        "/gpfs1/home/sychan552/.cache/huggingface/hub",
    ]
    found = []
    for c in candidates:
        found.extend(sorted(glob.glob(os.path.join(c, "models--*")))[:5])
    out["cache_paths_checked"] = candidates
    out["cache_hits"] = found[:20]
    if not found:
        out["status"] = "NOT_MEASURED"
        out["reason"] = "no HF model cache directory found at any checked path"
    else:
        try:
            from transformers import AutoModel, AutoTokenizer
            target = found[0]
            snap = sorted(glob.glob(os.path.join(target, "snapshots", "*")))
            local = snap[-1] if snap else target
            t0 = time.perf_counter()
            m = AutoModel.from_pretrained(local, local_files_only=True).to(dev).eval()
            out["load_s"] = round(time.perf_counter() - t0, 4)
            out["model_path"] = local
            ids = torch.ones((1, 104), dtype=torch.long, device=dev)
            with torch.no_grad():
                m(input_ids=ids); sync()
                lat = []
                for _ in range(10):
                    t = time.perf_counter()
                    m(input_ids=ids); sync()
                    lat.append((time.perf_counter() - t) * 1000.0)
            out.update({"warmup_runs": 1, "repeat_runs": 10,
                        "batch": "1 sequence x 104 tokens", "precision": "float32",
                        "latency_mean_ms": round(float(np.mean(lat)), 3),
                        "latency_std_ms": round(float(np.std(lat)), 3),
                        "status": "MEASURED"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            out["status"] = "NOT_MEASURED"
            out["reason"] = type(e).__name__ + ": " + str(e)[:250]

print("T6_MODEL_PROBE", json.dumps(out, indent=2), flush=True)
