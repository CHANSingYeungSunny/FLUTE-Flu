#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cost_model.py (queue v2, Gap 3) -- measure ONE cell, project the night, degrade.

WHY THIS EXISTS
---------------
"~10 min/cell" is MIFlu's cost: 1.67 M trainable parameters, 20 epochs. An LLM arm
is a different animal -- a FROZEN 7B-27B model must forward ~104x7 prompts for
~776 windows before a single epoch of the small head runs, which can be an hour+
per cell. Planning the night on MIFlu's number would silently overcommit the GPU
allocation by 5-10x, and the failure mode is the worst one available: the chain
dies at 07:00 with the P0 MIFlu row still incomplete.

WHAT IT DOES
------------
1. Reads the MEASURED wall time of every completed `llm_cell` from
   `queue_state.tsv` (the controller writes wall_seconds for every task).
2. Assigns each arm a cost class by parameters:  S <= 3B, M 4-15B, L >= 27B.
3. Projects the remaining work per arm and per class. A class with no measured
   cell yet is scaled from the nearest measured class linearly in parameters
   (a frozen forward pass over a fixed token count is compute-bound, so time is
   approximately proportional to parameters); the formula is printed so the
   assumption is auditable.
4. Computes the REMAINING GPU ALLOCATION from the actual submitted jobs
   (`runner_s0.job` / `runner_s1.job` -> `scontrol show job`): a pending job that
   starts beyond the horizon contributes nothing, a running job contributes what
   is left of its wall clock. Nothing is assumed about partitions.
5. If the projection exceeds the allocation it DEGRADES IN A LOGGED ORDER:
       keep every P0 (MIFlu) cell, keep every P1 cell, then admit P2 arms
       smallest-first while they fit; every dropped arm's cells become
       `DEFERRED_COST` with the arithmetic in their note.
   It also RE-ADMITS (DEFERRED_COST -> TODO) if a later run finds the allocation
   grew, so a deferral is never a silent permanent drop.

USAGE
-----
    python cost_model.py                 # report only (no queue mutation)
    python cost_model.py --apply         # write queue_state rows + defer/readmit
    python cost_model.py --apply --horizon 12
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import time
from datetime import datetime

QUEUE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(QUEUE_DIR, "master_queue.tsv")
STATE_TSV = os.path.join(QUEUE_DIR, "queue_state.tsv")
REGISTRY = os.path.join(QUEUE_DIR, "arms_registry.json")
sys.path.insert(0, QUEUE_DIR)
import queue_store                                                    # noqa: E402

STATE_COLS = ["task_id", "state", "attempts", "wall_seconds", "gate",
              "last_job", "branch", "updated"]

#: class boundaries in billions of parameters
CLASS_S_MAX = 3.0
CLASS_M_MAX = 15.0

DEFAULT_MIFLU_SECONDS = float(os.environ.get("QUEUE_MIFLU_SECONDS", "900"))
UTILISATION = float(os.environ.get("QUEUE_UTILISATION", "0.85"))


def log(msg):
    print(msg, flush=True)


# ------------------------------------------------------------------ inputs ----
def read_queue():
    rows = []
    with open(QUEUE, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) == len(head):
                rows.append(dict(zip(head, f)))
    return rows


def read_state():
    rows = {}
    if not os.path.exists(STATE_TSV):
        return rows
    with open(STATE_TSV, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) == len(head) and f:
                rows[f[0]] = dict(zip(head, f))
    return rows


def write_state_rows(new_rows):
    """Merge rows keyed on task_id into queue_state.tsv, atomically."""
    rows = read_state()
    rows.update({r["task_id"]: r for r in new_rows})
    tmp = STATE_TSV + ".tmp.%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(STATE_COLS) + "\n")
        for r in rows.values():
            fh.write("\t".join(str(r.get(c, "")) for c in STATE_COLS) + "\n")
    os.replace(tmp, STATE_TSV)


def registry():
    import json
    return json.load(open(REGISTRY, encoding="utf-8"))["arms"]


def cost_class(params_b):
    if params_b <= CLASS_S_MAX:
        return "S"
    if params_b <= CLASS_M_MAX:
        return "M"
    return "L"


# ------------------------------------------------------- measured wall time ---
def measured_per_cell(qrows, srows):
    """arm label -> [measured seconds] for every DONE llm_cell."""
    kind_of = {r["task_id"]: r["kind"] for r in qrows}
    out = {}
    for tid, st in srows.items():
        if st.get("state") != "DONE" or kind_of.get(tid) != "llm_cell":
            continue
        try:
            secs = float(st.get("wall_seconds") or 0)
        except ValueError:
            continue
        if secs <= 0:
            continue
        label = tid.rsplit("_L", 1)[0]
        out.setdefault(label, []).append(secs)
    return out


def class_rates(meas, arms_by_label):
    """class -> (rate seconds/cell, source string)."""
    per = {}
    for label, secs in meas.items():
        arm = arms_by_label.get(label)
        if not arm:
            continue
        per.setdefault(cost_class(float(arm["params_b"])), []).extend(secs)
    rates = {}
    for c, secs in per.items():
        rates[c] = (sum(secs) / len(secs), "measured n=%d" % len(secs))
    if "S" not in rates:
        # nothing measured at all: fall back to the documented MIFlu-order number
        rates["S"] = (DEFAULT_MIFLU_SECONDS, "no measurement yet; default")
    # scale the unmeasured classes from the smallest measured reference
    ref_c = min(rates, key=lambda c: {"S": 0, "M": 1, "L": 2}[c])
    ref_rate = rates[ref_c][0]
    ref_params = min(float(a["params_b"]) for a in arms_by_label.values()
                     if cost_class(float(a["params_b"])) == ref_c) or 1.0
    ref_params = max(ref_params, 0.1)
    for c in ("S", "M", "L"):
        if c not in rates:
            med = [float(a["params_b"]) for a in arms_by_label.values()
                   if cost_class(float(a["params_b"])) == c]
            p = sorted(med)[len(med) // 2] if med else ref_params
            rates[c] = (ref_rate * (p / ref_params),
                        "scaled from class %s (%.2f s/cell at %.2fB) x %.2fB/%.2fB"
                        % (ref_c, ref_rate, ref_params, p, ref_params))
    return rates


# ------------------------------------------------------------- allocation -----
def parse_timelimit(s):
    """Slurm TimeLimit ('5-00:00:00', '12:00:00', 'UNLIMITED') -> seconds."""
    if not s or s in ("UNLIMITED", "INVALID"):
        return 24 * 3600
    days = 0
    if "-" in s:
        d, s = s.split("-", 1)
        days = int(d)
    parts = [int(x) for x in s.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    return days * 86400 + parts[0] * 3600 + parts[1] * 60 + parts[2]


def job_info(jid):
    r = subprocess.run(["scontrol", "show", "job", str(jid)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    kv = {}
    for tok in r.stdout.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            kv[k] = v
    return kv


def lane_jobs():
    ids = []
    for lane in ("s0", "s1"):
        p = os.path.join(QUEUE_DIR, "runner_%s.job" % lane)
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line.isdigit():
                ids.append((lane, line))
    return ids


def allocation(horizon_s):
    """Usable GPU-seconds in the next `horizon_s`, measured from the real jobs."""
    now = time.time()
    total = 0.0
    detail = []
    for lane, jid in lane_jobs():
        info = job_info(jid)
        if not info:
            detail.append("lane %s job %s: gone (0 s)" % (lane, jid))
            continue
        st = info.get("JobState", "?")
        limit = parse_timelimit(info.get("TimeLimit", ""))
        try:
            start = datetime.strptime(info.get("StartTime", ""), "%Y-%m-%dT%H:%M:%S").timestamp()
        except ValueError:
            start = now
        if st == "RUNNING":
            try:
                el = parse_timelimit(info.get("Elapsed", "0:00:00"))
            except ValueError:
                el = 0
            start = now
            limit = max(0, limit - el)
        begin = max(now, start)
        end = min(now + horizon_s, start + limit)
        usable = max(0.0, end - begin) * UTILISATION
        total += usable
        detail.append("lane %s job %s: %s time=%s start=%s usable=%.0fs (x%.2f)"
                      % (lane, jid, st, info.get("TimeLimit", "?"),
                         info.get("StartTime", "?"), usable, UTILISATION))
    override = os.environ.get("QUEUE_ALLOCATION_SECONDS", "")
    if override:
        total = float(override)
        detail.append("QUEUE_ALLOCATION_SECONDS override = %.0fs" % total)
    if not detail:
        total = float(os.environ.get("QUEUE_DEFAULT_ALLOCATION", "14400"))
        detail.append("no runner job registered: default allocation %.0fs" % total)
    return total, detail


# ------------------------------------------------------------------- main -----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="mutate the queue (defer/readmit)")
    ap.add_argument("--horizon", type=float,
                    default=float(os.environ.get("QUEUE_COST_HORIZON_H", "12")),
                    help="hours of night still available (default 12)")
    ap.add_argument("--min-measured", type=int, default=1,
                    help="do not degrade until this many llm cells are measured")
    a = ap.parse_args()

    qrows = read_queue()
    srows = read_state()
    reg = registry()
    arms_by_label = {x["label"]: x for x in reg}
    arms_by_hf = {x["hf_id"]: x for x in reg}

    meas = measured_per_cell(qrows, srows)
    n_meas = sum(len(v) for v in meas.values())
    rates = class_rates(meas, arms_by_label)

    # ---- remaining work per arm ------------------------------------------
    remaining = {}
    for r in qrows:
        if r["kind"] != "llm_cell":
            continue
        if r["state"] not in ("TODO", "BLOCKED_MISSING_WEIGHTS", "RUNNING"):
            continue
        label = r["task_id"].rsplit("_L", 1)[0]
        remaining[label] = remaining.get(label, 0) + 1

    p0_left = sum(1 for r in qrows if r["priority"] == "P0"
                  and r["state"] in ("TODO", "RUNNING", "BLOCKED_MISSING_WEIGHTS"))
    p1_left = sum(1 for r in qrows if r["priority"] == "P1"
                  and r["state"] in ("TODO", "RUNNING", "BLOCKED_MISSING_WEIGHTS"))

    alloc, alloc_detail = allocation(a.horizon * 3600)

    log("=" * 78)
    log("cost_model: measured llm cells = %d  (%s)"
        % (n_meas, ", ".join("%s:%d" % (k, len(v)) for k, v in sorted(meas.items())) or "none"))
    for c in ("S", "M", "L"):
        log("  class %s rate = %8.1f s/cell   [%s]" % (c, rates[c][0], rates[c][1]))
    log("  P0 MIFlu cells left = %d  at %.0f s/cell (measured-order constant) = %.0f s"
        % (p0_left, DEFAULT_MIFLU_SECONDS, p0_left * DEFAULT_MIFLU_SECONDS))
    log("  allocation over the next %.1f h:" % a.horizon)
    for d in alloc_detail:
        log("    " + d)
    log("    => usable allocation = %.0f s (%.2f GPU-hours)" % (alloc, alloc / 3600))

    # ---- projection -------------------------------------------------------
    proj = {}
    for label, n in sorted(remaining.items()):
        arm = arms_by_label.get(label)
        if not arm:
            continue
        c = cost_class(float(arm["params_b"]))
        proj[label] = {"cells": n, "class": c, "rate": rates[c][0],
                       "seconds": n * rates[c][0], "params_b": float(arm["params_b"]),
                       "priority": min(r["priority"] for r in qrows
                                       if r["task_id"].rsplit("_L", 1)[0] == label),
                       "state": ("DEFERRED_COST"
                                 if any(r["task_id"].rsplit("_L", 1)[0] == label
                                        and r["state"] == "DEFERRED_COST" for r in qrows)
                                 else "live")}
    p0_cost = p0_left * DEFAULT_MIFLU_SECONDS
    p1_cost = sum(v["seconds"] for v in proj.values() if v["priority"] == "P1")
    log("  projected P0 = %.0f s, P1 = %.0f s (both ALWAYS kept by policy)" % (p0_cost, p1_cost))

    budget = alloc - p0_cost - p1_cost
    kept, deferred = [], []
    for label, v in sorted(proj.items(), key=lambda kv: (kv[1]["params_b"], kv[0])):
        if v["priority"] in ("P0", "P1"):
            kept.append((label, v, "P0/P1 policy"))
            continue
        if v["seconds"] <= budget:
            budget -= v["seconds"]
            kept.append((label, v, "fits"))
        else:
            deferred.append((label, v))

    log("-" * 78)
    for label, v, why in kept:
        log("  KEEP     %-28s class %s  %2d cells x %7.1f s = %8.0f s   (%s)"
            % (label, v["class"], v["cells"], v["rate"], v["seconds"], why))
    for label, v in deferred:
        log("  DEFER    %-28s class %s  %2d cells x %7.1f s = %8.0f s   (budget left %.0f s)"
            % (label, v["class"], v["cells"], v["rate"], v["seconds"], budget))
    if not deferred:
        log("  nothing deferred: the projection fits the allocation")
    log("=" * 78)

    # ---- queue_state rows (the audit trail of the measurement itself) -----
    stamp = time.strftime("%F %T")
    rows = []
    for label, secs in sorted(meas.items()):
        rows.append({"task_id": "_cost_measured_%s" % label, "state": "MEASURED",
                     "attempts": len(secs), "wall_seconds": "%.0f" % (sum(secs) / len(secs)),
                     "gate": "%.1f s/cell" % (sum(secs) / len(secs)),
                     "last_job": "-", "branch": "cost.measured", "updated": stamp})
    for c in ("S", "M", "L"):
        rows.append({"task_id": "_cost_rate_%s" % c, "state": "RATE", "attempts": "-",
                     "wall_seconds": "%.1f" % rates[c][0], "gate": "%.1f s/cell" % rates[c][0],
                     "last_job": "-", "branch": "cost.rate", "updated": stamp})
    rows.append({"task_id": "_cost_allocation", "state": "ALLOC", "attempts": "-",
                 "wall_seconds": "%.0f" % alloc, "gate": "%.0f s" % alloc, "last_job": "-",
                 "branch": "cost.allocation", "updated": stamp})
    rows.append({"task_id": "_cost_projection", "state": "PROJECTION",
                 "attempts": "-",
                 "wall_seconds": "%.0f" % (p0_cost + p1_cost + sum(v["seconds"]
                                                                   for _l, v, _w in kept)),
                 "gate": "kept=%d;deferred=%d" % (len(kept), len(deferred)),
                 "last_job": "-", "branch": "cost.projection", "updated": stamp})

    if a.apply:
        write_state_rows(rows)
        if n_meas < a.min_measured:
            log("cost_model: only %d measured cell(s) < %d -- projection is advisory, "
                "no arm deferred yet" % (n_meas, a.min_measured))
        else:
            for label, v in deferred:
                note = ("DEFERRED_COST: %d cells x %.1f s/cell = %.0f s > budget left "
                        "%.0f s. allocation=%.0f s (%.1f h horizon; %s) - P0 %.0f s and "
                        "P1 %.0f s are kept by policy, P2 arms admitted smallest-first "
                        "by params_b; this arm (%.2fB) did not fit. Rates: S=%.0f M=%.0f "
                        "L=%.0f s/cell (class %s: %s)."
                        % (v["cells"], v["rate"], v["seconds"], budget, alloc, a.horizon,
                           "; ".join(alloc_detail), p0_cost, p1_cost, v["params_b"],
                           rates["S"][0], rates["M"][0], rates["L"][0], v["class"],
                           rates[v["class"]][1]))
                n = queue_store.defer_arm(arms_by_label[label]["hf_id"], note)
                log("  applied: %s -> %d cell(s) DEFERRED_COST" % (label, n))
            # re-admission: a deferral must never be a silent permanent drop
            alive = {label for label, _v, _w in kept}
            back = [[arms_by_label[l]["hf_id"] for l in alive if l in arms_by_label]]
            for group in back:
                for hf in group:
                    n = queue_store.readmit_deferred(hf, "cost_model: fits the allocation "
                                                         "on re-measurement")
                    if n:
                        log("  re-admitted: %s -> %d cell(s) TODO" % (hf, n))
    else:
        log("(report only; pass --apply to write queue_state.tsv and defer)")

    with open(os.path.join(QUEUE_DIR, "cost_projection.txt"), "w", encoding="utf-8") as fh:
        fh.write("allocation=%.0f s over %.1f h\n" % (alloc, a.horizon))
        for d in alloc_detail:
            fh.write("  %s\n" % d)
        for c in ("S", "M", "L"):
            fh.write("rate_%s=%.1f s/cell (%s)\n" % (c, rates[c][0], rates[c][1]))
        for label, v, why in kept:
            fh.write("KEEP %s %s %d cells %.0f s (%s)\n"
                     % (label, v["class"], v["cells"], v["seconds"], why))
        for label, v in deferred:
            fh.write("DEFER %s %s %d cells %.0f s\n"
                     % (label, v["class"], v["cells"], v["seconds"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
