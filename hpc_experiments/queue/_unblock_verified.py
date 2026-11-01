#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_unblock_verified.py -- unblock an LLM arm ONLY if its weights are really local.

WHY A STRICT TEST AND NOT A MANIFEST CLAIM
------------------------------------------
A HuggingFace snapshot directory can exist, contain `config.json`, and contain
`safetensors` NAMES while every one of those names is a DANGLING SYMLINK into a
`blobs/` directory that was never populated (or was cleaned). `ls` shows a model;
`du` shows 83 K. Loading it fails at `from_pretrained`, i.e. AFTER a GPU has been
allocated. So the test here follows every weight symlink with `os.stat` and adds
up the bytes that actually exist. An arm passes only if

    config.json exists  AND  at least one weight file resolves  AND
    the resolved weight bytes total >= MIN_GB

Only then is its registry entry updated (`weights: downloaded`, pinned revision
from the snapshot directory name, which IS the sha) and its 12 `llm_cell` rows
flipped BLOCKED_MISSING_WEIGHTS -> TODO in place, atomically. Everything else is
left exactly as it was, with the measured reason recorded.

Usage:  _unblock_verified.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

QUEUE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(QUEUE_DIR, "master_queue.tsv")
REGISTRY = os.path.join(QUEUE_DIR, "arms_registry.json")
HF = "/home/sychan552/scratch/hf_cache"
MIN_GB = 0.5

#: what the download job reported, so the report can be compared with the disk
REPORTED_OK = [
    "tencent/Hunyuan-1.8B-Instruct", "tencent/WeMM-Embedding-2B",
    "tencent/Hunyuan-4B-Instruct", "tencent/WeMM-Embedding-4B",
    "tencent/ContextPilot-8B", "tencent/Hunyuan-7B-Instruct",
    "tencent/ContextPilot-14B", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
]
REPORTED_UNSUPPORTED = {
    "tencent/Penguin-Encoder": "trust_remote_code / no per-layer hidden states",
    "tencent/Youtu-HiChunk": "no per-layer hidden states",
}
REPORTED_FAILED = {
    "tencent/KaLM-Embedding-Gemma3-12B": "download/verify FAILED",
}

WF_EXT = (".safetensors", ".bin", ".pt", ".pth", ".gguf", ".npz")


def snapshots(model):
    """(layout, path) for both cache layouts huggingface_hub can leave behind."""
    slug = model.replace("/", "--")
    out = []
    for layout, base in (("flat", os.path.join(HF, "models--" + slug)),
                         ("hub", os.path.join(HF, "hub", "models--" + slug))):
        if not os.path.isdir(base):
            continue
        for snap in sorted(glob.glob(os.path.join(base, "snapshots", "*"))):
            out.append((layout, snap))
    return out


def measure(snap):
    """(config_ok, n_weight_files, resolved_bytes, dangling) for one snapshot."""
    cfg = os.path.exists(os.path.join(snap, "config.json"))
    n = 0
    total = 0
    dangling = 0
    for p in glob.glob(os.path.join(snap, "*")):
        if not p.endswith(WF_EXT):
            continue
        n += 1
        try:
            st = os.stat(p)                      # follows the symlink
            total += st.st_size
        except OSError:
            dangling += 1
    return cfg, n, total, dangling


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    reg = json.load(open(REGISTRY, encoding="utf-8"))
    by_hf = {x["hf_id"]: x for x in reg["arms"]}

    verdicts = {}
    print("%-44s %-5s %-8s %-6s %-4s %-6s %-12s %s"
          % ("arm", "layout", "config", "wfiles", "dang", "GB", "VERDICT", "revision"))
    for arm in reg["arms"]:
        m = arm["hf_id"]
        snaps = snapshots(m)
        best = None
        for layout, snap in snaps:
            cfg, n, total, dang = measure(snap)
            gb = total / 2 ** 30
            rev = os.path.basename(snap)
            ok = cfg and n > 0 and dang == 0 and gb >= MIN_GB
            cand = {"layout": layout, "snap": snap, "rev": rev, "gb": gb,
                    "cfg": cfg, "n": n, "dang": dang, "ok": ok}
            print("%-44s %-5s %-8s %-6d %-4d %-6.2f %-12s %s"
                  % (m, layout, "yes" if cfg else "NO", n, dang, gb,
                     "OK" if ok else "not-usable", rev[:12]))
            if ok and (best is None or gb > best["gb"]):
                best = cand
        verdicts[m] = best

    print()
    usable = [m for m, v in verdicts.items() if v]
    print("USABLE (real weights on disk): %d" % len(usable))
    for m in usable:
        print("  %-44s %5.2f GB  revision=%s  layout=%s"
              % (m, verdicts[m]["gb"], verdicts[m]["rev"], verdicts[m]["layout"]))
    claimed = [m for m in REPORTED_OK if not verdicts.get(m)]
    if claimed:
        print("CLAIMED-OK BUT NOT USABLE ON DISK: %d" % len(claimed))
        for m in claimed:
            v = None
            for layout, snap in snapshots(m):
                cfg, n, total, dang = measure(snap)
                v = "%s: %.2f GB, %d weight file(s), %d dangling" % (layout, total / 2 ** 30, n, dang)
            print("  %-44s %s" % (m, v or "no snapshot directory at all"))

    if not a.apply:
        print("\n(report only; --apply would pin revisions and flip the rows)")
        return 0

    # ---- registry: pin revision + weights for the usable arms ---------------
    changed = []
    for arm in reg["arms"]:
        m = arm["hf_id"]
        v = verdicts.get(m)
        if v:
            if arm.get("revision") != v["rev"] or arm.get("weights") != "downloaded":
                arm["revision"] = v["rev"]
                arm["weights"] = "downloaded"
                changed.append(m)
        elif m in REPORTED_UNSUPPORTED:
            arm["weights"] = "unsupported"
            arm["note"] = ("UNSUPPORTED: %s -- never retried"
                           % REPORTED_UNSUPPORTED[m])
        elif m in REPORTED_FAILED:
            arm["weights"] = "failed"
            arm["note"] = ("FAILED: %s -- never retried" % REPORTED_FAILED[m])
    tmp = REGISTRY + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, REGISTRY)
    print("\nregistry: %d arm(s) updated (weights=downloaded + pinned revision)" % len(changed))
    for m in changed:
        print("  %-44s -> %s" % (m, verdicts[m]["rev"]))

    # ---- queue: flip only the usable arms' rows ----------------------------
    with open(QUEUE, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    head = lines[0].split("\t")
    idx = {c: i for i, c in enumerate(head)}
    flipped, annotated = 0, 0
    out = [lines[0]]
    for line in lines[1:]:
        f = line.split("\t")
        if len(f) != len(head):
            out.append(line)
            continue
        m = f[idx["model"]]
        st = f[idx["state"]]
        if f[idx["kind"]] == "llm_cell" and st == "BLOCKED_MISSING_WEIGHTS":
            # Weights on disk are NECESSARY but not SUFFICIENT: an arm whose
            # adapter cannot produce per-layer hidden states is unusable however
            # complete its checkpoint is, so it must never be flipped to TODO.
            if verdicts.get(m) and m not in REPORTED_UNSUPPORTED:
                f[idx["state"]] = "TODO"
                f[idx["note"]] = ("unblocked: weights verified local (%.2f GB, revision %s); "
                                  "was BLOCKED_MISSING_WEIGHTS" % (verdicts[m]["gb"],
                                                                   verdicts[m]["rev"][:12]))
                flipped += 1
            elif m in REPORTED_UNSUPPORTED:
                f[idx["note"]] = ("stays BLOCKED: UNSUPPORTED - %s (never retried)"
                                  % REPORTED_UNSUPPORTED[m])
                annotated += 1
            elif m in REPORTED_FAILED:
                f[idx["note"]] = ("stays BLOCKED: download FAILED - %s (never retried)"
                                  % REPORTED_FAILED[m])
                annotated += 1
            else:
                f[idx["note"]] = ("stays BLOCKED: no usable weights on disk "
                                  "(snapshot is metadata/dangling symlinks only)")
                annotated += 1
        out.append("\t".join(f))
    qtmp = QUEUE + ".tmp.%d" % os.getpid()
    with open(qtmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    os.replace(qtmp, QUEUE)
    print("\nqueue: %d row(s) BLOCKED -> TODO, %d row(s) annotated in place" % (flipped, annotated))
    with open(os.path.join(QUEUE_DIR, "queue_events.log"), "a", encoding="utf-8") as fh:
        fh.write("[%s] UNBLOCK verified %d llm_cell row(s) -> TODO (arms: %s); "
                 "%d left blocked with a measured reason\n"
                 % (time.strftime("%F %T"), flipped, ",".join(sorted(usable)), annotated))
    return 0


if __name__ == "__main__":
    sys.exit(main())
