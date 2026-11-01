#!/usr/bin/env python3
"""Flip BLOCKED_MISSING_WEIGHTS llm_cell rows to TODO for arms whose weights are present.

Safe by construction:
  * a timestamped backup is written before any change;
  * ONLY rows whose kind is `llm_cell`, whose state is `BLOCKED_MISSING_WEIGHTS`,
    and whose model is in the OK set are touched;
  * every other byte of every other row is preserved verbatim;
  * the write is atomic (temp file in the same directory, then os.replace).

Usage:
    python flip_llm_blocked.py --queue /path/master_queue.tsv [--apply]
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from collections import Counter

# Arms whose weights are downloaded AND which were verified OK
# (per-layer hidden states confirmed) by weights_worker.py.
OK_ARMS = [
    "tencent/Hunyuan-1.8B-Instruct",
    "tencent/WeMM-Embedding-2B",
    "tencent/Hunyuan-4B-Instruct",
    "tencent/WeMM-Embedding-4B",
    "tencent/ContextPilot-8B",
    "tencent/Hunyuan-7B-Instruct",
    "tencent/ContextPilot-14B",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
]

# Already local before tonight; include them so their cells are unblocked too.
LOCAL_ARMS = [
    "Qwen/Qwen2.5-1.5B",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
]

BAD_STATE = "BLOCKED_MISSING_WEIGHTS"
GOOD_STATE = "TODO"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    path = args.queue
    with open(path, "r", encoding="utf-8", newline="") as fh:
        raw = fh.read()

    lines = raw.splitlines(keepends=True)
    if not lines:
        print("EMPTY QUEUE")
        return 1

    header = lines[0]
    cols = header.rstrip("\r\n").split("\t")
    try:
        i_kind = cols.index("kind")
        i_model = cols.index("model")
        i_state = cols.index("state")
    except ValueError:
        print(f"UNEXPECTED HEADER: {cols}")
        return 1
    print(f"columns={len(cols)} kind={i_kind} model={i_model} state={i_state}")

    wanted = set(OK_ARMS) | set(LOCAL_ARMS)

    before = Counter()
    after = Counter()
    flipped = 0
    touched_models = Counter()
    out = [header]

    for ln in lines[1:]:
        if not ln.strip():
            out.append(ln)
            continue
        f = ln.rstrip("\r\n").split("\t")
        if len(f) <= max(i_kind, i_model, i_state):
            out.append(ln)
            continue
        kind, model, state = f[i_kind], f[i_model], f[i_state]
        before[state] += 1
        if kind == "llm_cell" and state == BAD_STATE and model in wanted:
            f[i_state] = GOOD_STATE
            flipped += 1
            touched_models[model] += 1
            ln = "\t".join(f) + "\n"
        after[f[i_state]] += 1
        out.append(ln)

    print(f"\nBEFORE: {dict(before)}")
    print(f"AFTER : {dict(after)}")
    print(f"flipped {flipped} llm_cell rows")
    for m, c in sorted(touched_models.items()):
        print(f"  {c:3d}  {m}")
    llm_todo = sum(1 for ln in out[1:] if ln.strip()
                   for f in [ln.rstrip("\r\n").split("\t")]
                   if len(f) > max(i_kind, i_state)
                   and f[i_kind] == "llm_cell" and f[i_state] == GOOD_STATE)
    print(f"llm_cell now TODO: {llm_todo}")

    if not args.apply:
        print("\n(--check only; nothing written)")
        return 0

    backup = f"{path}.bak.{time.strftime('%Y%m%dT%H%M%S')}"
    shutil.copy2(path, backup)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(out))
    os.replace(tmp, path)
    print(f"\nWROTE {path}  (backup: {backup})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
