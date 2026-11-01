#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""master_task.py (queue v2) -- execute exactly ONE task from `master_queue.tsv`.

Called by `master_controller.sh` (never by hand except for debugging). The
controller owns the queue state machine; this file knows how to (a) decide
whether a task is already finished and passes its gate (idempotence) and (b) do
the work when it is not.

EVERY BRANCH IS NAMED AND PRINTED
---------------------------------
Each exit path prints `BRANCH=<dotted.name>` before it returns. The controller
copies that string into `queue_state.tsv` and `queue_events.log`, so after an
unattended night every task says *which* decision fired, not merely that it
failed. The branch names are the ones in the hardening brief:

  hw.not-a100 hw.no-cuda hw.cuda-busy hw.oom-halved
  train.nan train.oracle-mismatch train.oracle-mismatch-retry train.timeout
  skip.env-missing skip.download-* skip.no-hidden-state skip.arch-unsupported
  skip.no-revision skip.oom skip.impossible
  w.blocked-missing-weights d.partial-mode d.refreeze d.rows-lost
  d.arms-changed d.miflu-row-missing d.disk-pressure
  ok.done ok.already-done ok.finalise

EXIT CODES (the controller maps these onto queue states)
-------------------------------------------------------
  0  DONE         -- artefact exists and reproduces its gate
  2  RETRY        -- a real execution failure; the controller retries, and after
                     the 2nd failure marks the task SKIPPED with the reason
  3  SKIPPED      -- can never succeed here (env missing, no revision, model
                     yields no hidden states, OOM at batch size 1, ...)
  4  FAILED       -- terminal, do NOT retry: NaN/inf loss or non-finite MSE (a
                     retry reproduces it by construction)
  7  NOT-A100     -- the device is not an A100; the task must not run (rule 13)
  9  ORACLE       -- the cell does not reproduce its per-seed oracle. The export
                     is withheld (never accepted into tables) and retried once;
                     a second mismatch is SKIPPED, so the queue always advances.

GATE VALUES
-----------
`GATE=<value>` on success. For a cell it is the 7-variable z-space MSE on the
shared `(W//16)*16` windows. For a finalisation task it is `n_cells=<N>;n_arms=<M>`
(or the string gate named in FINALISE_META), which is what makes the report able
to say "every table this much data supports was emitted".
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

QUEUE_DIR = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(QUEUE_DIR)
RUNS = "/gpfs1/home/sychan552/stage5_a2_durable"
EXPANDED = os.path.join(RUNS, "expanded_runs")
AUTHOR_RUNS = os.path.join(RUNS, "author_runs")
SCRATCH = "/home/sychan552/scratch"
REGISTRY = os.path.join(QUEUE_DIR, "arms_registry.json")
OVERRIDES = os.path.join(QUEUE_DIR, "overrides.json")

sys.path.insert(0, QUEUE_DIR)
import queue_store                                                  # noqa: E402

PY_HPC = "/home/sychan552/.conda/envs/mlflu_hpc/bin/python"
PY_LLM = "/home/sychan552/.venvs/mlflu_llm/bin/python"

#: the staged analysis tree on the cluster (`stage_analysis.sh`): a mini repo
#: root with scripts/, paper_tables/, hpc_results/expanded_runs symlinked to the
#: real cell tree. Finalisation runs HERE, so it needs no login node and no
#: network. Without it F1-F5 cannot run at all on the cluster.
ANALYSIS = os.path.join(RUNS, "analysis")
LOGDIR = os.path.join(QUEUE_DIR, "logs")

W_AVAILABLE = {24: 170, 36: 158, 48: 146, 60: 134}

#: env name -> interpreter (Gap 2). A queue row names its env explicitly; an
#: unknown env, or one whose interpreter is absent, is SKIPPED as `env-missing`
#: and is never retried -- a missing binary cannot appear on a retry.
ENVS = {"hpc": PY_HPC, "llm": PY_LLM}
ENV_ALT = {"hpc": "llm", "llm": "hpc"}


# ------------------------------------------------------------------ logging ----
def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def br(name):
    """Record the decision that fired. The controller greps this line."""
    print("BRANCH=%s" % name, flush=True)


def done(gate=None, note="", branch="ok.done"):
    br(branch)
    if gate is not None:
        print("GATE=%s" % gate, flush=True)
    print("NOTE=%s" % note, flush=True)
    return 0


def retry(reason, branch="retry.generic"):
    br(branch)
    print("REASON=%s" % reason, flush=True)
    return 2


def skip(reason, branch="skip.impossible"):
    br(branch)
    print("SKIP_REASON=%s" % reason, flush=True)
    return 3


def failed(reason, branch="train.failed"):
    br(branch)
    print("REASON=%s" % reason, flush=True)
    return 4


def not_a100(reason):
    br("hw.not-a100")
    print("REASON=%s" % reason, flush=True)
    return 7


def oracle_halt(reason, branch="train.oracle-mismatch"):
    br(branch)
    print("REASON=%s" % reason, flush=True)
    return 9


# --------------------------------------------------------------- registry -----
def arms():
    """hf_id -> registry entry (venv, encoder_batch_size, revision, label)."""
    reg = json.load(open(REGISTRY, encoding="utf-8"))
    return {a["hf_id"]: a for a in reg["arms"]}


def overrides():
    try:
        return json.load(open(OVERRIDES, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def batch_size_for(arm):
    """Registry batch size, unless a previous OOM halved it (persisted)."""
    ov = overrides().get(arm["label"], {})
    if "encoder_batch_size" in ov:
        return int(ov["encoder_batch_size"]), int(ov.get("halved_from", 0))
    return int(arm["encoder_batch_size"]), 0


def halve_batch(arm, current):
    """Persist a halved batch size so the retry (any lane, any generation) uses it."""
    nxt = max(1, current // 2)
    ov = overrides()
    ov.setdefault(arm["label"], {})
    ov[arm["label"]]["encoder_batch_size"] = nxt
    ov[arm["label"]].setdefault("halved_from", int(arm["encoder_batch_size"]))
    tmp = OVERRIDES + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(ov, fh, indent=2, sort_keys=True)
    os.replace(tmp, OVERRIDES)
    return nxt


def pinned_revision(arm):
    """The pinned sha: the registry constant, else what the CPU probe measured."""
    if arm.get("revision"):
        return arm["revision"]
    p = os.path.join(QUEUE_DIR, "p2", "%s.json" % arm["label"])
    if os.path.exists(p):
        try:
            rec = json.load(open(p, encoding="utf-8"))
            if rec.get("ok") and rec.get("revision"):
                return rec["revision"]
        except (OSError, ValueError):
            pass
    return None


#: The cluster carries TWO huggingface cache layouts side by side (runbook
#: gotcha 1, in reverse): `hf_cache/models--X` (populated with cache_dir=$HF_HOME)
#: and `hf_cache/hub/models--X` (populated with HF_HOME). `HF_HUB_CACHE` can point
#: at only ONE of them, so a model living in the other is invisible to
#: `from_pretrained(..., local_files_only=True)` even though its weights ARE on
#: disk -- and that failure happens after a GPU has already been allocated.
#: Resolving the snapshot directory here makes the load independent of the var.
HF_CACHE = os.path.join(SCRATCH, "hf_cache")
WF_EXT = (".safetensors", ".bin", ".pt", ".pth")


def local_snapshot(model, want_rev=None):
    """A verified on-disk snapshot directory for `model`, or None.

    "Verified" means `config.json` exists AND the weight files -- following their
    symlinks, so a dangling blob counts as zero bytes -- add up to >= 0.5 GiB.
    A metadata-only snapshot therefore never passes (it would fail at load time).
    """
    slug = model.replace("/", "--")
    for base in (os.path.join(HF_CACHE, "models--" + slug),
                 os.path.join(HF_CACHE, "hub", "models--" + slug)):
        cands = sorted(glob.glob(os.path.join(base, "snapshots", "*")))
        if not cands:
            continue
        if want_rev:
            exact = [c for c in cands if os.path.basename(c).startswith(want_rev[:12])]
            cands = exact or cands
        best, best_bytes = None, 0
        for snap in cands:
            if not os.path.exists(os.path.join(snap, "config.json")):
                continue
            tot = 0
            for p in glob.glob(os.path.join(snap, "*")):
                if p.endswith(WF_EXT):
                    try:
                        tot += os.stat(p).st_size
                    except OSError:
                        pass
            if tot > best_bytes:
                best, best_bytes = snap, tot
        if best and best_bytes >= 0.5 * 2 ** 30:
            return best
    return None


# ---------------------------------------------------------------- hardware ----
def assert_a100():
    import torch
    if not torch.cuda.is_available():
        return 7
    name = torch.cuda.get_device_name(0)
    cap = torch.cuda.get_device_capability(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 2 ** 30
    log("[a100] measured gpu=%s capability=%s vram=%.1fGiB" % (name, cap, vram))
    if "A100" not in name:
        return name
    return 0


# ------------------------------------------------------------------ MIFlu -----
def eval_slice(W, batch=16):
    return (W // batch) * batch


def miflu_cell(task_id):
    """One MIFlu reproduction cell: retrain if needed, export all 7 vars, verify."""
    import threading
    sys.path.insert(0, CODE)
    try:
        import export_miflu_all7 as EX
        import miflu_controller_v2 as MC
    except Exception as exc:                                   # noqa: BLE001
        return failed("import-failed: %s: %s" % (type(exc).__name__, exc),
                      "train.import-failed")

    m = re.match(r"miflu_L(\d+)_s(\d+)$", task_id)
    if not m:
        return skip("bad miflu task id %r" % task_id)
    L, S = int(m.group(1)), int(m.group(2))
    want = EX.oracle_mse(L, S)
    if want is None:
        return skip("no oracle for this (L, seed) - see make_queue.py --check-oracle",
                    "skip.no-oracle")
    if want != want or want in (float("inf"), float("-inf")):
        return failed("oracle itself is non-finite (%r): the (L,seed) cannot be used"
                      % (want,), "train.nan")

    # ---- idempotence: already verified? -----------------------------------
    ckpt, prov = EX.find_ckpt(L, S)
    if ckpt is not None and MC.marker_exists(L, S):
        ok, why = MC.verify_cell(L, S, ckpt, want)
        if ok:
            return done(want, "already DONE (%s); ckpt=%s" % (why, prov),
                        "ok.already-done")
        log("[recheck] marker present but verification failed (%s) -> redoing" % why)

    # ---- single-cell plan, mirroring MC.build_plan ------------------------
    if ckpt is None:
        action = "train"
    else:
        p = MC.cell_paths(L, S)
        have = all(os.path.exists(p[k]) for k in ("npz", "csv", "results", "manifest"))
        if have:
            ok, _why = MC.verify_cell(L, S, ckpt, want)
            action = "done" if ok else "export"
        else:
            action = "export"
    cell = {"L": L, "S": S, "action": action, "pick": (ckpt, prov), "oracle": want}
    log("[plan] %s action=%s oracle=%.6f ckpt=%s" % (task_id, action, want, ckpt or "-"))

    if action == "done":
        MC.write_marker(L, S, {"L": L, "seed": S, "checkpoint": ckpt, "provenance": prov,
                               "oracle_mse": want,
                               "verified_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                               "detail": "re-verified by master queue"})
        return done(want, "re-verified existing cell ckpt=%s" % prov, "ok.already-done")

    res = MC.process_cell(cell, py=sys.executable,
                          deadline=time.time() + 1e9, stop=threading.Event())
    st = str(res.get("status", ""))
    log("[result] %s %s" % (task_id, res))
    if st == "verified":
        return done(want, res.get("detail", ""))
    if st.startswith("HALT") or "oracle" in st.lower() and "mismatch" in st.lower():
        return oracle_halt(st)
    if st.startswith("no-checkpoint"):
        return skip(st, "w.blocked-missing-weights")
    if "nan" in st.lower() or "nonfinite" in st.lower() or "non-finite" in st.lower():
        return failed(st, "train.nan")
    if "out of memory" in st.lower() or "cuda oom" in st.lower():
        return retry(st, "hw.oom-halved")
    if "busy or unavailable" in st.lower() or "cuda-capable device" in st.lower():
        return retry(st, "hw.cuda-busy")
    return retry(st or "unknown-failure")


# -------------------------------------------------------------- disk guard ----
CKPT_ROOT = os.path.join(RUNS, "checkpoints", "llm_encoder")
MIN_FREE_GB = float(os.environ.get("QUEUE_MIN_FREE_GB", "40"))


def disk_guard(keep_label):
    """Under quota pressure delete the OLDEST ckpt_* trees we do not need now.

    Logs every deletion to `queue/deletions.log` (append-only). Returns the branch
    that fired so the controller can record it; never raises, never blocks.
    """
    try:
        st = os.statvfs(SCRATCH)
        free_gb = st.f_bavail * st.f_frsize / 2 ** 30
    except OSError:
        return "d.disk-pressure-unknown"
    log("[disk] scratch free=%.1fGB (floor %.1fGB)" % (free_gb, MIN_FREE_GB))
    if free_gb >= MIN_FREE_GB:
        return ""
    victims = []
    for d in glob.glob(os.path.join(CKPT_ROOT, "*", "ckpt_*")):
        if os.path.basename(os.path.dirname(d)) == keep_label:
            continue
        try:
            victims.append((os.path.getmtime(d), d))
        except OSError:
            pass
    victims.sort()
    with open(os.path.join(QUEUE_DIR, "deletions.log"), "a", encoding="utf-8") as fh:
        fh.write("[%s] free=%.1fGB < %.1fGB floor; deleting %d candidate(s)\n"
                 % (time.strftime("%F %T"), free_gb, MIN_FREE_GB, len(victims)))
        for _mt, d in victims:
            try:
                sz = sum(os.path.getsize(os.path.join(r, f))
                         for r, _dd, ff in os.walk(d) for f in ff) / 2 ** 30
            except OSError:
                sz = -1
            shutil.rmtree(d, ignore_errors=True)
            fh.write("  deleted %s (%.2f GB)\n" % (d, sz))
            fh.flush()
            try:
                free_gb = os.statvfs(SCRATCH).f_bavail * os.statvfs(SCRATCH).f_frsize / 2 ** 30
            except OSError:
                free_gb = -1
            if 0 <= free_gb >= MIN_FREE_GB:
                break
    return "d.disk-pressure"


# -------------------------------------------------------------- LLM cells -----
ARCH_PATTERNS = (
    "not recognized", "not recognised", "model type", "does not support",
    "unrecognized", "unsupported", "no module named", "cannot import",
)
OOM_PATTERNS = ("out of memory", "cuda error: out of memory", "cublas_status_alloc_failed")
BUSY_PATTERNS = ("busy or unavailable", "cuda-capable device", "cuda initialization error",
                 "no cuda-capable", "device-side assert")
NAN_PATTERNS = ("loss is nan", "nan loss", "loss=nan", "non-finite", "nonfinite",
                "inf loss", "loss=inf")


def _last_run(text, tid):
    """Only the CURRENT run's output.

    The finalise log is append-only across the whole night, so a naive "is
    'RESULT: PASS' in the tail?" check matches a PASS from three cycles ago and
    reports the current failing run as a success. Every run starts with a header
    line `[YYYY-MM-DD HH:MM:SS] <task_id> kind=...`, so slice from the last one.
    """
    marker = "] %s kind=" % tid
    i = text.rfind(marker)
    return text[i:] if i >= 0 else text


def _tail(path, n=6000):
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - n))
            return fh.read().decode("utf-8", "replace")
    except OSError:
        return ""


def _classify_trainer_failure(text):
    low = text.lower()
    for p in OOM_PATTERNS:
        if p in low:
            return "oom"
    for p in BUSY_PATTERNS:
        if p in low:
            return "cuda-busy"
    for p in NAN_PATTERNS:
        if p in low:
            return "nan"
    for p in ARCH_PATTERNS:
        if p in low:
            return "arch"
    return ""


def llm_gate(npz_path, L):
    """7-var z-space MSE on the shared window set, or None if the cell is invalid."""
    try:
        import numpy as np
        z = np.load(npz_path)
        pred, target = z["pred"], z["target"]
        if pred.shape != target.shape or pred.ndim != 3:
            log("[gate] bad shape pred=%s target=%s" % (pred.shape, target.shape))
            return None
        W, nvar, nlead = pred.shape
        if nvar != 7 or nlead != L:
            log("[gate] not (W,7,%d): %s" % (L, pred.shape))
            return None
        if W != W_AVAILABLE[L]:
            log("[gate] W=%d != available %d for L=%d" % (W, W_AVAILABLE[L], L))
            return None
        n = eval_slice(W)
        err = pred[:n].astype("float64") - target[:n].astype("float64")
        v = float((err ** 2).mean())
        if v != v or v in (float("inf"), float("-inf")):
            log("[gate] NON-FINITE MSE %r -> cell rejected" % (v,))
            return None
        return v
    except Exception as exc:                                   # noqa: BLE001
        log("[gate] cannot read %s: %s: %s" % (npz_path, type(exc).__name__, exc))
        return None


def _run(cmd, cwd, env, logfh):
    logfh.write("\n$ %s\n" % " ".join(cmd))
    logfh.flush()
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, env=env, stdout=logfh, stderr=subprocess.STDOUT)
    logfh.write("[rc=%d %.1fs]\n" % (r.returncode, time.time() - t0))
    logfh.flush()
    return r.returncode


def llm_cell(task_id, model, L, seed, env_name=""):
    """One frozen-encoder cell: `train_backbone_966.py --backbone llm_encoder`."""
    m = re.match(r"(.+)_L(\d+)_s(\d+)$", task_id)
    if not m:
        return skip("bad llm task id %r" % task_id)
    label = m.group(1)
    arm = arms().get(model)
    if arm is None:
        return skip("model %r not in arms_registry.json" % model)

    # ---- Gap 2: per-model environment routing -----------------------------
    # The queue row names the env; the registry is the fallback. A wrong env is
    # the classic silent failure (qwen3_5 cannot be parsed by transformers 4.x),
    # so it is resolved explicitly and a missing interpreter is SKIPPED, never
    # retried: a binary that does not exist cannot appear on the next attempt.
    venv = env_name if env_name not in ("", "-") else arm["venv"]
    py = ENVS.get(venv)
    if py is None:
        return skip("env-missing: unknown env %r (known: %s)"
                    % (venv, sorted(ENVS)), "skip.env-missing")
    if not os.path.exists(py):
        return skip("env-missing: interpreter %s does not exist" % py, "skip.env-missing")
    log("[llm] %s env=%s interpreter=%s" % (task_id, venv, py))
    if arm["venv"] != venv:
        log("[llm] NOTE queue env %r overrides registry venv %r (queue is authoritative)"
            % (venv, arm["venv"]))

    rev = pinned_revision(arm)
    if rev is None:
        return skip("no-revision: the CPU probe (kind=llm_probe) must pin the sha first",
                    "skip.no-revision")

    bs, halved_from = batch_size_for(arm)
    export_dir = os.path.join(EXPANDED, "%s_L%d_s%d" % (label, L, seed))
    ckpt_dir = os.path.join(RUNS, "checkpoints", "llm_encoder", label)
    cache = os.path.join(SCRATCH, "llm_cache", "%s.pt" % label)
    npz = os.path.join(export_dir, "pred_%s_L%d_s%d.npz" % (label, L, seed))
    man = os.path.join(export_dir, "manifest_%s_L%d_s%d.json" % (label, L, seed))
    metrics = os.path.join(export_dir, "metrics.csv")

    # ---- idempotence: gate on the cell itself -----------------------------
    if not os.path.exists(npz):
        # the trainer picks its own file stem from --arm-label; accept any
        # pred_*.npz in the export dir rather than failing on a name mismatch.
        hits = sorted(glob.glob(os.path.join(export_dir, "pred_*.npz")))
        if hits:
            npz = hits[0]
    if os.path.exists(npz) and os.path.exists(man) and os.path.exists(metrics):
        gate = llm_gate(npz, L)
        if gate is not None:
            return done(gate, "already DONE (%s)" % npz, "ok.already-done")

    os.makedirs(export_dir, exist_ok=True)
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    os.makedirs(LOGDIR, exist_ok=True)
    dbr = disk_guard(label)
    if dbr:
        br(dbr)

    # ---- resolve the weights on disk, in EITHER cache layout (see above) ----
    snap = local_snapshot(model, rev)
    model_ref = snap if snap else model
    if snap:
        log("[llm] %s local snapshot %s (%.1f GiB) - bypasses HF_HUB_CACHE"
            % (task_id, snap, sum(os.stat(p).st_size
                                  for p in glob.glob(os.path.join(snap, "*"))
                                  if p.endswith(WF_EXT)) / 2 ** 30))
        br("w.local-snapshot")
    else:
        log("[llm] %s no verified local snapshot; letting transformers resolve %s@%s"
            % (task_id, model, rev[:12]))

    cmd = [py, "-u", "train_backbone_966.py",
           "--backbone", "llm_encoder", "--arm-label", label,
           "--llm-model-id", model_ref,
           "--encoder-batch-size", str(bs),
           "--encoder-device", "cuda",
           "--profile", "author_966", "--containment", "strict",
           "--horizon", str(L), "--seed", str(seed),
           "--export-dir", export_dir, "--ckpt-dir", ckpt_dir,
           "--encoder-cache", cache, "--llm-revision", rev]

    env = dict(os.environ)
    env.update({
        "HF_HOME": os.path.join(SCRATCH, "hf_cache"),
        "HF_HUB_CACHE": os.path.join(SCRATCH, "hf_cache"),
        "TRANSFORMERS_OFFLINE": "1", "HF_HUB_OFFLINE": "1",
        "PYTHONUNBUFFERED": "1",
    })
    log("[llm] %s exec: %s" % (task_id, " ".join(cmd)))
    logpath = os.path.join(LOGDIR, "trainer_%s.log" % task_id)
    with open(logpath, "a", encoding="utf-8") as fh:
        fh.write("\n==== %s bs=%s env=%s\n" % (time.strftime("%F %T"), bs, venv))
        fh.flush()
        rc = _run(cmd, CODE, env, fh)
    tail = _tail(logpath)

    if rc != 0:
        cause = _classify_trainer_failure(tail)
        # ---- arch fallback: one attempt in the other env, then give up -----
        alt = ENV_ALT.get(venv)
        if cause == "arch" and alt in ENVS and os.path.exists(ENVS[alt]):
            apy = ENVS[alt]
            log("[llm] arch failure in env=%s -> ONE retry in env=%s (%s)" % (venv, alt, apy))
            br("w.arch-fallback-%s-to-%s" % (venv, alt))
            cmd2 = list(cmd)
            cmd2[0] = apy
            with open(logpath, "a", encoding="utf-8") as fh:
                fh.write("\n==== %s ARCH FALLBACK env=%s\n" % (time.strftime("%F %T"), alt))
                fh.flush()
                rc2 = _run(cmd2, CODE, env, fh)
            if rc2 != 0:
                return skip("arch-unsupported: trainer rc=%d in env=%s and rc=%d in env=%s"
                            % (rc, venv, rc2, alt), "skip.arch-unsupported")
            os.environ["QUEUE_ENV_USED"] = alt
            print("ENV_USED=%s" % alt, flush=True)
        elif cause == "oom":
            if bs <= 1:
                return skip("oom at --encoder-batch-size 1: %s" % tail[-300:], "skip.oom")
            nxt = halve_batch(arm, bs)
            return retry("oom at bs=%d -> halved to %d for the retry: %s"
                         % (bs, nxt, tail[-300:]), "hw.oom-halved")
        elif cause == "cuda-busy":
            return retry("CUDA busy/unavailable on this node: %s" % tail[-300:],
                         "hw.cuda-busy")
        elif cause == "nan":
            return failed("non-finite loss/MSE: %s" % tail[-300:], "train.nan")
        else:
            return retry("train_backbone_966 rc=%d: %s" % (rc, tail[-300:]))

    gate = llm_gate(npz, L)
    if gate is None:
        hits = sorted(glob.glob(os.path.join(export_dir, "pred_*.npz")))
        for h in hits:
            gate = llm_gate(h, L)
            if gate is not None:
                npz = h
                break
    if gate is None:
        if os.path.exists(npz):
            return failed("trainer rc=0 but the export is invalid/non-finite: %s" % npz,
                          "train.nan")
        return retry("trainer returned 0 but the cell artefact is absent: %s" % npz)
    note = npz
    if halved_from:
        note += "; encoder-batch-size halved %d -> %d after an OOM" % (halved_from, bs)
    return done(gate, note)


# ------------------------------------------------------------- LLM probes -----
def probe_record(arm):
    p = os.path.join(QUEUE_DIR, "p2", "%s.json" % arm["label"])
    if not os.path.exists(p):
        return {}
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def model_ref(arm, model):
    """What to pass as `--llm-model-id`: the hub id, or a local dir from the
    curl fallback download (independent of huggingface_hub working)."""
    rec = probe_record(arm)
    ld = rec.get("local_dir")
    if ld and os.path.isdir(ld):
        return ld
    return model


def llm_probe(task_id, model):
    """P2: pin the revision, get the weights on CPU, prove a hidden-state read-out.

    Two independent download paths (huggingface_hub, then curl). A model is only
    declared unusable when a *forward pass with real weights* says so.
    Runs ONLY on a CPU partition (QUEUE_CPU_ONLY=1): rule 13(b).
    """
    import urllib.request

    outdir = os.path.join(QUEUE_DIR, "p2")
    os.makedirs(outdir, exist_ok=True)
    slug = task_id[len("probe_"):] if task_id.startswith("probe_") else task_id
    rec_path = os.path.join(outdir, "%s.json" % slug)
    rec = {"task_id": task_id, "model_id": model, "when": time.strftime("%F %T")}

    old = probe_record({"label": slug})
    if old.get("ok"):
        n = queue_store.unblock_model(model, "TODO",
                                      "unblocked by CPU probe: revision=%s hidden read-out D=%s"
                                      % (old.get("revision"), old.get("hidden_dim")))
        return done(None, "already probed: revision=%s D=%s (%d cells TODO)"
                    % (old.get("revision"), old.get("hidden_dim"), n), "ok.already-done")

    # ---- 1. pin the revision sha (urllib AND curl: two paths) --------------
    api = "https://huggingface.co/api/models/%s" % model
    rev = None
    try:
        with urllib.request.urlopen(api, timeout=30) as fh:
            rev = json.loads(fh.read().decode("utf-8")).get("sha")
    except Exception as exc:                                    # noqa: BLE001
        rec["urllib_error"] = "%s: %s" % (type(exc).__name__, str(exc)[:120])
    if not rev:
        r = subprocess.run(["curl", "-sS", "-m", "40", api], capture_output=True, text=True)
        try:
            rev = json.loads(r.stdout).get("sha")
        except ValueError:
            rev = None
    if not rev:
        return skip("download-revision-lookup-failed (no network?): urllib=%s"
                    % rec.get("urllib_error"), "skip.download-no-network")
    rec["revision"] = rev
    log("[probe] %s pinned revision=%s" % (task_id, rev))

    # ---- 2. weights: snapshot_download, then a curl fallback --------------
    env = dict(os.environ)
    env.update({"HF_HOME": os.path.join(SCRATCH, "hf_cache"),
                "HF_HUB_CACHE": os.path.join(SCRATCH, "hf_cache"),
                "HF_HUB_DOWNLOAD_TIMEOUT": "60"})
    dl_ok, dl_err = False, ""
    for attempt in range(1, 4):
        r = subprocess.run(
            [PY_HPC, "-c",
             "from huggingface_hub import snapshot_download as s;"
             "p=s(repo_id=%r, revision=%r, max_workers=2);print('PATH='+p)"
             % (model, rev)],
            cwd=CODE, env=env, capture_output=True, text=True)
        if r.returncode == 0:
            dl_ok = True
            break
        dl_err = (r.stderr or "").strip().splitlines()[-1:] or [""]
        dl_err = dl_err[0]
        log("[probe] snapshot_download attempt %d/3 failed: %s" % (attempt, dl_err[:200]))
        time.sleep(20 * attempt)
    rec["snapshot_download_ok"] = dl_ok

    local_dir = os.path.join(SCRATCH, "hf_models", slug)
    if not dl_ok:
        log("[probe] falling back to curl download into %s" % local_dir)
        try:
            with urllib.request.urlopen("%s/tree/%s?recursive=1" % (api, rev),
                                        timeout=40) as fh:
                tree = json.loads(fh.read().decode("utf-8"))
        except Exception:                                       # noqa: BLE001
            r = subprocess.run(["curl", "-sS", "-m", "60",
                                "%s/tree/%s?recursive=1" % (api, rev)],
                               capture_output=True, text=True)
            try:
                tree = json.loads(r.stdout)
            except ValueError:
                return skip("download-no-file-list (both paths failed: %s)" % dl_err[:160],
                            "skip.download-gated")
        files = [e for e in tree if e.get("type") == "file"]
        os.makedirs(local_dir, exist_ok=True)
        ok_n = 0
        for e in files:
            p = e["path"]
            dst = os.path.join(local_dir, p)
            os.makedirs(os.path.dirname(dst) or local_dir, exist_ok=True)
            if os.path.exists(dst) and os.path.getsize(dst) == e.get("size", -1):
                ok_n += 1
                continue
            url = "https://huggingface.co/%s/resolve/%s/%s" % (model, rev, p)
            r = subprocess.run(["curl", "-sSL", "--retry", "3", "--retry-delay", "5",
                                "-m", "3600", "-o", dst, url], capture_output=True, text=True)
            if r.returncode != 0:
                rec["curl_error"] = "%s: %d %s" % (p, r.returncode, (r.stderr or "")[:200])
                log("[probe] curl failed on %s: %s" % (p, rec["curl_error"]))
                break
            ok_n += 1
        rec["files_downloaded"] = ok_n
        rec["files_total"] = len(files)
        if ok_n != len(files):
            _save(rec_path, rec)
            if ok_n == 0:
                return skip("download-no-network (both paths failed: %s)" % dl_err[:160],
                            "skip.download-no-network")
            return skip("download-partial: %d/%d files (disk full or 404: %s)"
                        % (ok_n, len(files), rec.get("curl_error", "")[:160]),
                        "skip.download-partial")
        rec["local_dir"] = local_dir

    # ---- 3. CPU 2-layer smoke test: is there a hidden-state read-out? ------
    ref = rec.get("local_dir") or model
    smoke_json = os.path.join(outdir, "%s.smoke.json" % slug)
    smoke = [PY_HPC, os.path.join(QUEUE_DIR, "probe_hidden_state.py"),
             "--model", ref, "--revision", rev, "--layers", "2", "--json", smoke_json]
    r2 = subprocess.run(smoke, cwd=CODE, env=env, capture_output=True, text=True)
    rec["smoke_rc"] = r2.returncode
    rec["smoke_tail"] = ((r2.stdout or "") + (r2.stderr or ""))[-1200:]

    if r2.returncode == 0:
        try:
            s = json.load(open(smoke_json, encoding="utf-8"))
            rec.update({"ok": True, "hidden_dim": s.get("hidden_dim"),
                        "hidden_source": s.get("hidden_source"),
                        "model_type": s.get("model_type")})
            _save(rec_path, rec)
            n = queue_store.unblock_model(
                model, "TODO",
                "unblocked by CPU probe: revision=%s hidden read-out %s D=%s"
                % (rev, s.get("hidden_source"), s.get("hidden_dim")))
            return done(None, "revision=%s D=%s unblocked %d cells"
                        % (rev, s.get("hidden_dim"), n))
        except (OSError, ValueError) as exc:
            rec.update({"ok": False, "error": "smoke json unreadable: %s" % exc})
            _save(rec_path, rec)
            return retry("smoke-json-unreadable %s" % exc)

    reason = _tail_reason(smoke_json, r2)
    rec.update({"ok": False, "error": reason})
    _save(rec_path, rec)
    if r2.returncode == 3:
        n = queue_store.unblock_model(model, "SKIPPED",
                                      "probe: no hidden-state read-out (%s)" % reason[:200])
        return skip("no-hidden-state-readout: %s (skipped %d cells)" % (reason[:200], n),
                    "skip.no-hidden-state")
    low = reason.lower()
    if "not recognized" in low or "model type" in low or "unsupported" in low:
        n = queue_store.unblock_model(model, "SKIPPED",
                                      "arch-unsupported in tr4.57.6 (env=hpc): %s" % reason[:200])
        return skip("arch-unsupported in env=hpc: %s (skipped %d cells)"
                    % (reason[:200], n), "skip.arch-unsupported")
    return retry("smoke-test rc=%d: %s" % (r2.returncode, reason[:160]))


def _tail_reason(smoke_json, proc):
    try:
        s = json.load(open(smoke_json, encoding="utf-8"))
        if s.get("error"):
            return str(s["error"])[:300]
    except (OSError, ValueError):
        pass
    txt = ((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()
    return txt[-1][:300] if txt else "no output"


def _save(path, rec):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2, sort_keys=True)
    os.replace(tmp, path)


# ------------------------------------------------------------ finalisation ----
#: F1-F5. Cells on disk are worth nothing until these have run: they are what
#: produce MSE/MAE, PTE/PIE, the K&S verdict, CRPS/WIS and every figure.
#: Each entry is (label, [argv...]) executed with cwd = ANALYSIS.
FINALISE_STEPS = {
    "final_import_miflu": [
        ["scripts/import_miflu_predictions.py", "--npz-dir", "author_runs",
         "--horizons", "24", "36", "48", "60",
         "--seeds"] + [str(s) for s in range(2021, 2031)],
    ],
    "final_miflu_oracle": [
        ["scripts/verify_miflu_oracle.py"],
    ],
    "final_analysis_chain": [
        ["scripts/analysis_expanded.py"],
        ["scripts/analysis_postprocess.py"],
        ["scripts/seasonal_naive_baseline.py"],
        ["scripts/plot_bench.py"],
        ["scripts/plot_pareto.py"],
    ],
    "final_verify_bench": [
        ["scripts/verify_bench_unchanged.py"],
    ],
    "final_llm_import": [
        ["scripts/analysis_expanded.py"],
        ["scripts/plot_bench.py"],
        ["scripts/plot_pareto.py"],
    ],
}

#: kind == the v2 name; the task_id keeps the historical spelling so an existing
#: queue row is still recognised. Either resolves to the same step group.
KIND_TO_ID = {
    "f1_import_miflu": "final_import_miflu",
    "f2_miflu_oracle": "final_miflu_oracle",
    "f3_analysis_chain": "final_analysis_chain",
    "f4_verify": "final_verify_bench",
    "f5_llm_import": "final_llm_import",
    "finalise": "",
}

#: the table whose mtime proves the chain actually rewrote something
PROOF_TABLE = "paper_tables/BENCH_MSE_BY_MODEL_L.csv"
CORE_TABLES = ["paper_tables/BENCH_MSE_BY_MODEL_L.csv",
               "paper_tables/BENCH_PTE_PIE_BY_STEP.csv",
               "paper_tables/BENCH_EFFICIENCY.csv",
               "paper_tables/BENCH_CRPS_WIS.csv",
               "paper_tables/BENCH_SEASONAL_NAIVE.csv"]


def n_cells_on_disk():
    """Every benchmark cell (16 arms + all LLM arms + MIFlu) the analysis can see."""
    n = 0
    for pat in (os.path.join(EXPANDED, "*", "pred_*.npz"),):
        n += len(glob.glob(pat))
    return n


def n_arms_in_table():
    """Distinct `model` values actually written into the merged table."""
    p = os.path.join(ANALYSIS, "paper_tables", "BENCH_MSE_BY_MODEL_L.csv")
    try:
        with open(p, encoding="utf-8") as fh:
            head = fh.readline().rstrip("\n").split(",")
            if "model" not in head:
                return 0
            i = head.index("model")
            return len({ln.split(",")[i] for ln in fh if ln.strip()})
    except (OSError, IndexError):
        return 0


def cell_signature():
    """Cheap identity of the on-disk cell population (unchanged -> no-op)."""
    n_exp = n_all7 = 0
    newest = 0.0
    for base, pat in ((EXPANDED, "pred_*.npz"),
                      (AUTHOR_RUNS, "pred_miflu_L*_seed*.npz")):
        for p in glob.glob(os.path.join(base, "*", pat)):
            try:
                newest = max(newest, os.path.getmtime(p))
                n_exp += 1
            except OSError:
                pass
    for p in glob.glob(os.path.join(AUTHOR_RUNS, "L*_all7", "pred_*.npz")):
        try:
            newest = max(newest, os.path.getmtime(p))
            n_all7 += 1
        except OSError:
            pass
    return "exp=%d all7=%d newest=%d" % (n_exp, n_all7, int(newest))


def _read_csv_models(name):
    """{model: row} from a paper_tables CSV, keyed on the `model` column."""
    import csv
    p = os.path.join(ANALYSIS, "paper_tables", name)
    if not os.path.exists(p):
        return {}
    with open(p, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = {}
    for r in rows:
        k = r.get("model")
        if k:
            out.setdefault(k, []).append(r)
    return out


def f4_verify(outdir, py, logfh):
    """verify_bench_unchanged.py with an explicit freeze policy.

    * always copy the pre-freeze `BENCH_*.post_evalwindow16.csv` aside first;
    * an unchanged result is DONE;
    * a table that legitimately GREW (every baseline model still present, more
      models than before) is re-frozen with the backup kept, branch data.refreeze;
    * rows LOST, or a pre-existing arm's value changed, is a real regression:
      FAILED, and the evidence is preserved rather than re-frozen over.
    """
    ts = time.strftime("%Y%m%dT%H%M%S")
    backup = os.path.join(outdir, "freeze_backup_%s" % ts)
    os.makedirs(backup, exist_ok=True)
    n_copy = 0
    for src in glob.glob(os.path.join(ANALYSIS, "paper_tables",
                                      "BENCH_*.post_evalwindow16.csv")):
        dst = os.path.join(backup, os.path.basename(src))
        shutil.copy2(src, dst)
        n_copy += 1
    logfh.write("[f4] pre-freeze backup: %d file(s) -> %s\n" % (n_copy, backup))
    logfh.flush()

    new = _read_csv_models("BENCH_MSE_BY_MODEL_L.csv")
    old = _read_csv_models("BENCH_MSE_BY_MODEL_L.post_evalwindow16.csv")
    before = len(open(os.path.join(ANALYSIS, PROOF_TABLE), encoding="utf-8").readlines()) \
        if os.path.exists(os.path.join(ANALYSIS, PROOF_TABLE)) else 0

    rc = 0
    for argv in FINALISE_STEPS["final_verify_bench"]:
        rc = _run([py, "-u"] + argv, ANALYSIS, dict(os.environ), logfh)
    logfh.flush()
    if rc == 0:
        return done("n_cells=%d;n_arms=%d" % (n_cells_on_disk(), len(new)),
                    "verify_bench_unchanged PASS; pre-freeze copy at %s" % backup,
                    "ok.finalise")

    # ---- decide: legitimate growth, lost rows, or a changed arm ------------
    if not old:
        return retry("verify failed and there is no baseline freeze to compare "
                     "against (rc=%s); backup at %s" % (rc, backup), "d.verify-failed")
    missing = [k for k in old if k not in new]
    if missing:
        return failed("verify FAILED and %d baseline model row(s) are LOST "
                      "(%s); not re-freezing over the evidence (backup %s)"
                      % (len(missing), ",".join(sorted(missing)[:6]), backup),
                      "d.rows-lost")
    grew = len(new) > len(old)
    changed = []
    for k, orows in old.items():
        nrows = new.get(k, [])
        for o in orows:
            for n in nrows:
                if o.get("L") == n.get("L") and o.get("n_seeds") == n.get("n_seeds"):
                    try:
                        if abs(float(o["mse_7var_z"]) - float(n["mse_7var_z"])) > 1e-6:
                            changed.append("%s/L%s" % (k, o.get("L")))
                    except (KeyError, TypeError, ValueError):
                        pass
    if changed:
        return failed("verify FAILED and %d pre-existing arm cell(s) changed value "
                      "(%s); refusing to re-freeze (backup %s)"
                      % (len(changed), ",".join(sorted(set(changed))[:6]), backup),
                      "d.arms-changed")
    if not grew:
        return retry("verify FAILED (rc=%s) with no lost rows and no growth; "
                     "backup %s" % (rc, backup), "d.verify-failed")

    # ---- legitimate growth: re-freeze, keeping the pre-freeze copy --------
    logfh.write("[f4] table grew %d -> %d models: re-freezing\n"
                % (len(old), len(new)))
    for src in glob.glob(os.path.join(ANALYSIS, "paper_tables", "BENCH_*.csv")):
        base = os.path.basename(src)
        if ".post_evalwindow16" in base or ".pre_" in base:
            continue
        dst = os.path.join(ANALYSIS, "paper_tables",
                           base[:-4] + ".post_evalwindow16.csv")
        shutil.copy2(src, dst)
    rc2 = 0
    for argv in FINALISE_STEPS["final_verify_bench"]:
        rc2 = _run([py, "-u"] + argv, ANALYSIS, dict(os.environ), logfh)
    logfh.flush()
    if rc2 == 0:
        return done("n_cells=%d;n_arms=%d" % (n_cells_on_disk(), len(new)),
                    "re-frozen after legitimate growth %d -> %d models "
                    "(pre-freeze copy kept at %s)"
                    % (len(old), len(new), backup), "d.refreeze")
    return retry("re-freeze did not satisfy verify_bench_unchanged (rc=%s); "
                 "backup %s" % (rc2, backup), "d.refreeze")


def finalise(task_id, kind="", env_name=""):
    """Run one F-step group against the staged analysis tree.

    Idempotent by cell signature: if nothing new landed since the last successful
    run it returns DONE with `NOTE=no-new-cells` in ~1 s, which is what lets the
    controller re-arm it after every batch of cells instead of once at the end.

    Tolerant of partial data on purpose: a missing MIFlu row or a missing LLM arm
    must not stop the tables that CAN be produced, so a failing step is recorded
    and the chain continues; the task is only retried when no core table exists.
    """
    import fcntl

    tid = KIND_TO_ID.get(kind, "") or task_id
    if tid not in FINALISE_STEPS:
        return skip("unknown finalise step %r (kind=%r)" % (task_id, kind))
    if not os.path.isdir(os.path.join(ANALYSIS, "scripts")):
        return skip("env-missing: analysis tree absent at %s (run stage_analysis.sh)"
                    % ANALYSIS, "skip.env-missing")

    venv = env_name if env_name not in ("", "-") else "hpc"
    py = ENVS.get(venv)
    if py is None or not os.path.exists(py):
        return skip("env-missing: interpreter for env %r not found (%s)" % (venv, py),
                    "skip.env-missing")

    outdir = os.path.join(QUEUE_DIR, "finalise")
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(LOGDIR, exist_ok=True)
    logpath = os.path.join(outdir, "%s.log" % tid)
    recpath = os.path.join(outdir, "%s.json" % tid)

    # ---- cross-lane lock IN THE ANALYSIS TREE ------------------------------
    # This is the lock that actually protects paper_tables/: it lives next to the
    # artefacts it guards, so a reader of analysis/ can see that a single writer
    # owns the tree. It is held for the whole rebuild, not per file.
    lockfh = open(os.path.join(ANALYSIS, ".finalise.lock"), "a+")
    try:
        fcntl.flock(lockfh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lockfh.close()
        return done(None, "another writer holds analysis/.finalise.lock; skipped this cycle",
                    "ok.finalise-locked")

    try:
        sig = cell_signature()
        rec = {}
        if os.path.exists(recpath):
            try:
                rec = json.load(open(recpath, encoding="utf-8"))
            except (OSError, ValueError):
                rec = {}
        force = os.environ.get("QUEUE_FORCE_FINALISE", "0") == "1"
        if rec.get("signature") == sig and rec.get("ok") and not force:
            print("NOTE=no-new-cells", flush=True)
            return done(None, "no new cells since the last successful run (%s)" % sig,
                        "ok.no-new-cells")
        if force:
            log("[finalise] QUEUE_FORCE_FINALISE=1: idempotence short-circuit disabled")

        # ---- F1 pre-flight: contamination gate + import completeness --------
        if tid == "final_import_miflu":
            n_before = len(glob.glob(os.path.join(EXPANDED, "miflu_L*_s*")))
            ra = subprocess.run([py, "-u", os.path.join(QUEUE_DIR, "audit_miflu_cells.py"),
                                 "--apply"],
                                cwd=QUEUE_DIR, capture_output=True, text=True)
            with open(logpath, "a", encoding="utf-8") as fh:
                fh.write("\n$ audit_miflu_cells.py --apply  [rc=%d]\n%s%s\n"
                         % (ra.returncode, ra.stdout or "", ra.stderr or ""))
            log("[finalise] contamination audit rc=%d: %s"
                % (ra.returncode, (ra.stdout or "").strip().splitlines()[-1:] or [""]))
            n_markers = len(glob.glob(os.path.join(AUTHOR_RUNS, ".miflu_verify", "*")))
            n_importable = len(glob.glob(os.path.join(AUTHOR_RUNS, "L*_all7",
                                                      "pred_miflu_L*_seed*.npz")))
            n_importable += len(glob.glob(os.path.join(EXPANDED, "miflu_L*_s*",
                                                       "pred_*.npz")))
            if n_markers and n_importable < n_markers:
                return skip("import-partial: the importer would see %d cell(s) but %d "
                            "verify marker(s) exist; refusing to import a partial view "
                            "(a rebuild from a partial set would drop table rows)"
                            % (n_importable, n_markers), "d.import-partial")
            log("[finalise] import pre-flight: markers=%d importable=%d miflu_dirs_before=%d"
                % (n_markers, n_importable, n_before))

        proof = os.path.join(ANALYSIS, PROOF_TABLE)
        mtime_before = os.path.getmtime(proof) if os.path.exists(proof) else 0
        results, failures = [], []
        with open(logpath, "a", encoding="utf-8") as fh:
            fh.write("\n" + "=" * 78 + "\n[%s] %s kind=%s env=%s sig=%s\n"
                     % (time.strftime("%F %T"), tid, kind or "-", venv, sig))
            fh.flush()

            if tid == "final_verify_bench":
                rc = f4_verify(outdir, py, fh)          # returns an exit code path
                # f4_verify already chose done()/retry()/failed(); re-raise it
                raise _F4(rc)

            for argv in FINALISE_STEPS[tid]:
                t0 = time.time()
                rc = _run([py, "-u"] + argv, ANALYSIS, dict(os.environ), fh)
                results.append({"cmd": " ".join(argv), "rc": rc,
                                "seconds": round(time.time() - t0, 1)})
                if rc != 0:
                    failures.append("%s rc=%d" % (os.path.basename(argv[0]), rc))
                    log("[finalise] step %s failed rc=%d - continuing in partial mode"
                        % (argv[0], rc))
        mtime_after = os.path.getmtime(proof) if os.path.exists(proof) else 0

        # ---- per-kind success criterion --------------------------------------
        n_cells = n_cells_on_disk()
        n_arms = n_arms_in_table()
        gate = "n_cells=%d;n_arms=%d" % (n_cells, n_arms)
        branch = "ok.finalise"

        if tid == "final_miflu_oracle":
            tail = _last_run(_tail(logpath, 20000), tid)
            n_miflu = len(glob.glob(os.path.join(EXPANDED, "miflu_L*", "pred_*.npz")))
            dump = os.path.join(LOGDIR, "f2_miflu_oracle_%s.out"
                                % time.strftime("%Y%m%dT%H%M%S"))
            shutil.copy2(logpath, dump)
            gate = "n_cells=%d" % n_miflu
            cell_fail = [ln for ln in tail.splitlines()
                         if ln.startswith("[FAIL]") and "mse_7var_z" not in ln]
            row_fail = [ln for ln in tail.splitlines()
                        if ln.startswith("[FAIL]") and "mse_7var_z" in ln]
            if "RESULT: PASS" in tail:
                ok, branch = True, "ok.finalise"
            elif cell_fail:
                # a CELL does not reproduce its oracle: never accept the artefact
                ok, branch = False, "train.oracle-mismatch"
            elif row_fail and n_miflu:
                # every cell on disk reproduces its oracle, but the merged row is a
                # partial mean (e.g. 18 of the 40 reproduction cells). That row must
                # never be quoted as the MIFlu benchmark number, so it is reported
                # loudly and the branch says exactly that -- it is a completeness
                # condition, not a bad measurement, so the writer keeps working.
                ok, branch = True, "d.miflu-row-partial"
                log("[finalise] MIFlu TABLE ROW IS A PARTIAL MEAN over the cells on "
                    "disk (%d npz); %d horizon(s) do not match the 10-seed oracle yet "
                    "and the row must not be quoted until all 40 cells exist"
                    % (n_miflu, len(row_fail)))
            elif "SKIPPED" in tail and n_miflu == 0:
                ok, branch = True, "d.miflu-row-missing"
            else:
                ok, branch = False, "train.oracle-mismatch"
            log("[finalise] %s: oracle %s branch=%s (stdout at %s)"
                % (tid, "PASS" if ok else "NOT PASS", branch, dump))
        elif tid == "final_import_miflu":
            gate = "n_cells=%d" % len(glob.glob(os.path.join(EXPANDED, "miflu_L*",
                                                             "pred_*.npz")))
            ok = True
        else:
            ok = (mtime_after > mtime_before) or (not failures)
            if failures and ok:
                branch = "d.partial-mode"
            if not ok:
                branch = "d.no-table"

        rec = {"task_id": tid, "signature": sig, "ok": bool(ok),
               "steps": results, "failures": failures, "gate": gate,
               "proof_mtime_before": mtime_before, "proof_mtime_after": mtime_after,
               "when": time.strftime("%F %T")}
        _save(recpath, rec)
        note = ("steps=%d failed=%d n_cells=%d n_arms=%d proof_table=%s"
                % (len(results), len(failures), n_cells, n_arms,
                   "rewritten" if mtime_after > mtime_before else "unchanged")
                + (" failures=%s" % failures if failures else ""))
        log("[finalise] %s: %s" % (tid, note))
        _write_status(tid, sig, ok, gate, failures, logpath, mtime_after)

        if tid == "final_miflu_oracle" and not ok:
            return oracle_halt("verify_miflu_oracle did not print RESULT: PASS "
                               "(see %s)" % logpath)
        if not ok:
            return retry("finalise %s wrote no table: %s" % (tid, failures),
                         "d.no-table")
        return done(gate, note, branch)
    except _F4 as exc:
        return exc.code
    finally:
        try:
            fcntl.flock(lockfh, fcntl.LOCK_UN)
        except OSError:
            pass
        lockfh.close()


class _F4(Exception):
    """carries the already-decided exit code out of f4_verify."""

    def __init__(self, code):
        Exception.__init__(self, str(code))
        self.code = code


def _write_status(tid, sig, ok, gate, failures, logpath, table_mtime):
    """`queue/finalise_status.json`: what the writer did, every cycle.

    The morning question is "did the tables get rebuilt, and from what?" -- this
    file answers it without reading a 4000-line log: the cycle number, how many
    cells the writer could see, the table mtime it produced, and the last error.
    """
    p = os.path.join(QUEUE_DIR, "finalise_status.json")
    cyc_p = os.path.join(QUEUE_DIR, ".writer_cycle")
    try:
        cyc = int(open(cyc_p).read().strip() or 0) + 1
    except (OSError, ValueError):
        cyc = 1
    try:
        with open(cyc_p, "w") as fh:
            fh.write(str(cyc))
    except OSError:
        pass
    proof = os.path.join(ANALYSIS, PROOF_TABLE)
    payload = {
        "cycle": cyc,
        "when": time.strftime("%F %T"),
        "pid": os.getpid(),
        "slurm_job": os.environ.get("SLURM_JOB_ID", "local"),
        "task": tid,
        "signature": sig,
        "ok": bool(ok),
        "gate": gate,
        "n_markers": len(glob.glob(os.path.join(AUTHOR_RUNS, ".miflu_verify", "*"))),
        "n_cells": n_cells_on_disk(),
        "n_arms": n_arms_in_table(),
        "last_table_mtime": (time.strftime("%F %T", time.localtime(table_mtime))
                             if table_mtime else None),
        "table_path": proof,
        "failures": failures,
        "last_error": failures[-1] if failures else None,
        "log": logpath,
    }
    tmp = p + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
        os.replace(tmp, p)
    except OSError as exc:
        log("[finalise] could not write %s: %s" % (p, exc))


# -------------------------------------------------------------------- main ---
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?", default="run")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--kind", required=True)
    ap.add_argument("--model", default="")
    ap.add_argument("--L", default="-")
    ap.add_argument("--seed", default="-")
    ap.add_argument("--env", default="", help="hpc | llm | -  (per-model interpreter routing)")
    ap.add_argument("--require-a100", default="1")
    a = ap.parse_args()

    os.chdir(CODE)
    if a.kind in ("miflu_cell", "llm_cell") and a.require_a100 == "1":
        bad = assert_a100()
        if bad == 7:
            br("hw.no-cuda")
            print("REASON=no-cuda-device", flush=True)
            return 7
        if bad:
            return not_a100("not-a100:%s" % bad)

    if a.kind == "miflu_cell":
        return miflu_cell(a.task_id)
    if a.kind == "llm_cell":
        return llm_cell(a.task_id, a.model, int(a.L), int(a.seed), a.env)
    if a.kind == "llm_probe":
        return llm_probe(a.task_id, a.model)
    if a.kind in KIND_TO_ID:
        return finalise(a.task_id, a.kind, a.env)
    return skip("unknown kind %r" % a.kind)


if __name__ == "__main__":
    sys.exit(main())
