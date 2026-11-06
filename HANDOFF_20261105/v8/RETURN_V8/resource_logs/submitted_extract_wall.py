#!/usr/bin/env python
# TASK 6 / t6_res - extract REAL training wall times from queue logs.
# Runs INSIDE an sbatch compute-node job ONLY (no NPZ/model work on login node).
# Sources:
#   master_queue.tsv  : per-cell "wall=NNNs" note fields (measured by the queue workers)
#   wf_fix218 shard0.log : UTC START/END per cell (job 743850, read-only, NOT written to)
import os
import re
import json
import datetime
import statistics

BASE = "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res"
LOGS = os.path.join(BASE, "logs")
MASTER_QUEUE = "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/master_queue.tsv"
SHARD0 = "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/shard0.log"

# Representative subset models for TASK 6.
TARGET_MODELS = {
    "MIFlu": "MIFlu",
    "NLinear": "nlinear",
    "PatchTST": "patchtst",
    "DeepSeek-R1-Distill-Qwen-1.5B (frozen encoder)": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
}

os.makedirs(LOGS, exist_ok=True)

# ---------------------------------------------------------------- master_queue
raw_lines = []
with open(MASTER_QUEUE, "r", encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f, start=1):
        raw_lines.append((i, line.rstrip("\n")))

wall_re = re.compile(r"wall=(\d+)s")
gate_re = re.compile(r"gate=([0-9.eE+-]+)")

all_rows = []
for i, line in raw_lines:
    m = wall_re.search(line)
    if not m:
        continue
    cols = line.split("\t")
    if len(cols) < 11:
        continue
    g = gate_re.search(line)
    all_rows.append({
        "line_no": i,
        "task_id": cols[0],
        "kind": cols[1],
        "model": cols[2],
        "L": cols[3],
        "seed": cols[4],
        "priority": cols[5],
        "env": cols[6],
        "state": cols[7],
        "attempts": cols[8],
        "last_job": cols[9],
        "note": cols[10],
        "wall_s": int(m.group(1)),
        "gate": g.group(1) if g else "",
        "source_file": MASTER_QUEUE,
    })

with open(os.path.join(LOGS, "training_wall_extraction.tsv"), "w", encoding="utf-8") as f:
    f.write("\t".join(["source_file", "line_no", "task_id", "kind", "model", "L", "seed",
                       "state", "last_job", "wall_s", "gate", "raw_note"]) + "\n")
    for r in all_rows:
        f.write("\t".join([r["source_file"], str(r["line_no"]), r["task_id"], r["kind"],
                           r["model"], r["L"], r["seed"], r["state"], r["last_job"],
                           str(r["wall_s"]), r["gate"], r["note"]]) + "\n")

# Per-model summary across the WHOLE file (all models), for transparency.
by_model = {}
for r in all_rows:
    by_model.setdefault(r["model"], []).append(r["wall_s"])
with open(os.path.join(LOGS, "training_wall_summary_all_models.tsv"), "w", encoding="utf-8") as f:
    f.write("\t".join(["model", "n_cells", "mean_s", "median_s", "min_s", "max_s", "sum_s"]) + "\n")
    for model in sorted(by_model):
        v = sorted(by_model[model])
        f.write("\t".join([model, str(len(v)), f"{statistics.mean(v):.4f}",
                           f"{statistics.median(v):.1f}", str(v[0]), str(v[-1]),
                           str(sum(v))]) + "\n")

# Focused extraction for the 4 representative models with exact line numbers.
target_evidence = {}
for label, model_name in TARGET_MODELS.items():
    rows = [r for r in all_rows if r["model"] == model_name]
    v = sorted(r["wall_s"] for r in rows)
    rep = rows[0] if rows else None       # first measured cell for this model
    target_evidence[label] = {
        "model_in_queue": model_name,
        "n_cells_with_wall": len(rows),
        "mean_s": statistics.mean(v) if v else None,
        "median_s": statistics.median(v) if v else None,
        "min_s": v[0] if v else None,
        "max_s": v[-1] if v else None,
        "representative_cell": {
            "source_file": rep["source_file"] if rep else None,
            "line_no": rep["line_no"] if rep else None,
            "task_id": rep["task_id"] if rep else None,
            "wall_s": rep["wall_s"] if rep else None,
            "last_job": rep["last_job"] if rep else None,
            "raw_note": rep["note"] if rep else None,
        } if rep else None,
        "all_wall_s": v,
    }

with open(os.path.join(LOGS, "training_wall_targets.tsv"), "w", encoding="utf-8") as f:
    f.write("\t".join(["subset_label", "model_in_queue", "n_cells", "mean_s", "median_s",
                       "min_s", "max_s", "rep_line_no", "rep_task_id", "rep_wall_s",
                       "rep_last_job", "rep_raw_note", "source_file"]) + "\n")
    for label, e in target_evidence.items():
        rc = e["representative_cell"] or {}
        f.write("\t".join([label, e["model_in_queue"], str(e["n_cells_with_wall"]),
                           f"{e['mean_s']:.4f}" if e["mean_s"] is not None else "NA",
                           f"{e['median_s']:.1f}" if e["median_s"] is not None else "NA",
                           str(e["min_s"]), str(e["max_s"]),
                           str(rc.get("line_no", "NA")), str(rc.get("task_id", "NA")),
                           str(rc.get("wall_s", "NA")), str(rc.get("last_job", "NA")),
                           str(rc.get("raw_note", "NA")), MASTER_QUEUE]) + "\n")

# ------------------------------------------------------------------ shard0.log
# Independent corroboration: UTC START/END per cell from job 743850's own log.
shard_rows = []
start_re = re.compile(r"^(\S+) START (\S+)$")
end_re = re.compile(r"^(\S+) END (\S+) rc=(\d+)$")
starts = {}
ends = {}
if os.path.exists(SHARD0):
    with open(SHARD0, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            m = start_re.match(line)
            if m:
                starts[m.group(2)] = (m.group(1), i)
                continue
            m = end_re.match(line)
            if m:
                ends[m.group(2)] = (m.group(1), m.group(3), i)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    for cell in sorted(starts):
        if cell not in ends:
            continue
        t0, l0 = starts[cell]
        t1, rc, l1 = ends[cell]
        try:
            d0 = datetime.datetime.strptime(t0, fmt)
            d1 = datetime.datetime.strptime(t1, fmt)
            dur = int((d1 - d0).total_seconds())
        except Exception:
            dur = "PARSE_ERROR"
        shard_rows.append({
            "cell": cell, "start_utc": t0, "end_utc": t1, "rc": rc,
            "duration_s": dur, "start_line": l0, "end_line": l1,
            "source_file": SHARD0,
        })
with open(os.path.join(LOGS, "shard0_wall_extraction.tsv"), "w", encoding="utf-8") as f:
    f.write("\t".join(["cell", "start_utc", "end_utc", "rc", "duration_s",
                       "start_line", "end_line", "source_file"]) + "\n")
    for r in shard_rows:
        f.write("\t".join([r["cell"], r["start_utc"], r["end_utc"], r["rc"],
                           str(r["duration_s"]), str(r["start_line"]), str(r["end_line"]),
                           r["source_file"]]) + "\n")

with open(os.path.join(LOGS, "training_wall_evidence.json"), "w", encoding="utf-8") as f:
    json.dump({
        "label": "REAL measured per-cell training wall times from queue logs",
        "master_queue": MASTER_QUEUE,
        "master_queue_total_lines": len(raw_lines),
        "master_queue_rows_with_wall": len(all_rows),
        "shard0_log": SHARD0,
        "shard0_complete_start_end_pairs": len(shard_rows),
        "targets": target_evidence,
    }, f, indent=2, sort_keys=True)

print("EXTRACT_WALL_OK")
print("master_queue_rows_with_wall =", len(all_rows))
print("shard0_complete_start_end_pairs =", len(shard_rows))
for label, e in target_evidence.items():
    rc = e["representative_cell"] or {}
    print(f"TARGET {label}: n={e['n_cells_with_wall']} mean={e['mean_s']:.2f}s "
          f"rep=line{rc.get('line_no')} {rc.get('task_id')} wall={rc.get('wall_s')}s")
