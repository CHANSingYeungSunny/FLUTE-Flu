#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""measure_llm_forward.py — MEASURED per-window cost of the frozen-LLM encoder.

WHY THIS FILE EXISTS
--------------------
`hpc_experiments/queue/cost_model.py` prices an LLM cell with a **900 s default
that nobody ever measured**. The LLM half of the programme is therefore planned
on a guess: 168 cells x 900 s = 42 h, a number with no anchor. This script
replaces the guess with a measurement anyone can re-run:

    python hpc_experiments/measure_llm_forward.py \
        --model-id Qwen/Qwen2.5-1.5B \
        --revision 8faed761d45a263340a0528343f099c05c9a4323 \
        --batch 8 --repeats 3

It times the **real adapter** (`scripts/llm_encoder_backbone.py::FrozenLLMEncoder`,
the same object `train_backbone_966.py --backbone llm_encoder` uses) on prompts
rendered by the adapter's own `render_channel_prompt`, so the number includes
tokenisation, the frozen forward, `extract_last_hidden_state` and the masked mean
pool — i.e. everything a benchmark cell pays per (window, channel).

WHAT IT PRINTS
--------------
* `tokens_per_prompt`, `s_per_prompt` (batch-1 equivalent), `prompts_per_s`
* `prompts_per_cell = 7 channels x (n_train + n_val + n_test) windows`
  (793 at L=24 on the author-966 strict split: 549 + 74 + 170)
* `cell_seconds` for THIS model, and the same number divided by `--gpu-factor`
  as an explicit **projection** for an A100 (the factor is an assumption until
  one GPU cell is measured; it is printed with the result so it cannot be
  mistaken for a measurement).
* a class table S (<=3 B) / M (4-15 B) / L (>=27 B) obtained by scaling the
  measured cost with `params_b / measured_params_b` — a linear-in-parameters
  rule, which is the right order of magnitude for a batch-1 decode-free forward
  and is labelled as a projection.

Exit codes: 0 measured, 3 the model could not be loaded (reason printed).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(PROJECT_ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

#: Strict-containment test windows at L=24 on the author-966 split (metrics.csv
#: of any benchmark cell): used to size a cell's prompt count.
WINDOWS_L24 = {"train": 549, "val": 74, "test": 170}
N_CHANNELS = 7

#: Parameter classes the queue prices separately (docs/LLM_ARMS.md roster).
CLASSES = (("S", 0.4, 3.0), ("M", 4.0, 15.0), ("L", 27.0, 40.0))


def prompts_per_cell(windows=None) -> int:
    """Encoder prompts one cell costs: every window x every channel.

    The adapter is channel-independent and its prompt carries no channel
    identity, so one cell runs `n_windows x 7` encoder forwards **once** (the
    vectors are cached and reused across epochs); the trainable head is then
    trained on those cached vectors. That is why the encoder forward dominates
    and the training loop does not.
    """
    w = windows or WINDOWS_L24
    return int(sum(w.values()) * N_CHANNELS)


def measure(model_id: str, revision: str = None, batch: int = 8,
            repeats: int = 3, prompt_tokens: int = 0, log=print) -> dict:
    """Time the real adapter and return a cost record (no training)."""
    import torch
    import llm_encoder_backbone as llm

    log(f"[measure] building FrozenLLMEncoder({model_id}@{revision or 'main'}), "
        f"encoder_batch_size={batch}")
    t0 = time.time()
    enc = llm.FrozenLLMEncoder(T=104, N=N_CHANNELS, L=24, model_id=model_id,
                               revision=revision, encoder_batch_size=batch,
                               local_files_only=False)
    build_s = time.time() - t0
    prov = enc.provenance()
    log(f"[measure] loaded in {build_s:.1f}s: "
        f"{prov['encoder']['parameters']:,} encoder params, "
        f"head {prov['head']['parameters']:,}, device={prov['device']}")

    # Prompts exactly as the adapter renders them (z-space values, 4 dp, CSV).
    import numpy as np
    rng = np.random.default_rng(0)
    n = int(batch) * int(repeats)
    prompts = [llm.render_channel_prompt(rng.normal(0, 1, 104).round(4).tolist())
               for _ in range(n)]
    tok = enc._tokenize(prompts)                      # the adapter's own tokeniser
    n_tok = float(tok["input_ids"].shape[1])

    t0 = time.time()
    with torch.no_grad():
        vec = enc.encode_prompts(prompts)
    elapsed = time.time() - t0
    s_per_prompt = elapsed / n
    record = {
        "model_id": model_id, "revision": prov["revision"],
        "device": prov["device"], "encoder_batch_size": int(batch),
        "encoder_parameters": prov["encoder"]["parameters"],
        "head_parameters": prov["head"]["parameters"],
        "tokens_per_prompt": n_tok,
        "n_prompts_timed": n, "elapsed_s": round(elapsed, 4),
        "s_per_prompt": round(s_per_prompt, 6),
        "prompts_per_s": round(1.0 / s_per_prompt, 4) if s_per_prompt else None,
        "pooled_shape": list(vec.shape),
        "prompts_per_cell": prompts_per_cell(),
        "cell_seconds": round(s_per_prompt * prompts_per_cell(), 1),
        "build_seconds": round(build_s, 2),
        "library_versions": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "transformers": prov.get("library_versions", {}).get("transformers"),
        },
    }
    log(f"[measure] {n_tok:.0f} tokens/prompt, {s_per_prompt*1000:.1f} ms/prompt "
        f"({1.0/s_per_prompt:.2f} prompts/s) on {prov['device']}")
    log(f"[measure] one cell = {record['prompts_per_cell']} encoder prompts "
        f"-> {record['cell_seconds']/60:.1f} min on this device")
    return record


def class_table(measured: dict, measured_params_b: float, gpu_factor: float) -> list:
    """Extrapolate S/M/L cell costs from one measurement (linear in parameters)."""
    rows = []
    for name, lo, hi in CLASSES:
        ref = 1.5 if name == "S" else (8.0 if name == "M" else 27.0)
        scale = ref / float(measured_params_b)
        rows.append({
            "class": name, "params_b_range": f"{lo}-{hi}>=", "reference_params_b": ref,
            "scale_vs_measured": round(scale, 3),
            "cell_minutes_measured_device": round(measured["cell_seconds"] * scale / 60, 1),
            "cell_minutes_a100_projection": round(
                measured["cell_seconds"] * scale / max(gpu_factor, 1e-9) / 60, 1),
        })
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Measure the frozen-LLM encoder's per-window forward cost "
                    "(no training, no GPU needed).")
    ap.add_argument("--model-id", required=True)
    ap.add_argument("--revision", default=None,
                    help="Pinned sha; omit for a probe (revision is recorded).")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--measured-params-b", type=float, default=None,
                    help="Parameter count of the measured model, for the class "
                         "table (default: 1.5 for Qwen2.5-1.5B).")
    ap.add_argument("--gpu-factor", type=float, default=25.0,
                    help="ASSUMPTION: how much faster an A100 is than this device "
                         "on a batch-1-ish forward. Printed with the projection.")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args(argv)

    try:
        rec = measure(a.model_id, a.revision, a.batch, a.repeats)
    except BaseException as exc:                       # noqa: BLE001
        print(f"[measure] UNAVAILABLE: {type(exc).__name__}: {exc}")
        return 3

    params_b = a.measured_params_b or (
        1.5 if "1.5B" in a.model_id or "1p5b" in a.model_id.lower() else 8.0)
    rec["measured_params_b"] = params_b
    rec["gpu_factor_assumed"] = a.gpu_factor
    rec["class_table"] = class_table(rec, params_b, a.gpu_factor)
    print("\nclass | params | scale | cell min (this device) | cell min (A100 proj.)")
    for r in rec["class_table"]:
        print("%5s | %6.1fB | x%-5.2f | %10.1f | %12.1f"
              % (r["class"], r["reference_params_b"], r["scale_vs_measured"],
                 r["cell_minutes_measured_device"], r["cell_minutes_a100_projection"]))
    print("\nNOTE: the A100 column divides by --gpu-factor=%.1f, an ASSUMPTION "
          "until one GPU cell is measured. The measured column is real."
          % a.gpu_factor)
    if a.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(a.json_out)), exist_ok=True)
        with open(a.json_out, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        print(f"[measure] wrote {a.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
