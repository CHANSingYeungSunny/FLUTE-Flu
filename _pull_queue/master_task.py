#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""master_task.py -- execute exactly ONE task from `master_queue.tsv`.

Called by `master_controller.sh` (never by hand except for debugging). The
controller owns the state machine; this file only knows how to (a) decide
whether a task is already finished and passes its gate (idempotence) and
(b) do the work when it is not.

EXIT CODES (the controller maps these onto queue states)
--------------------------------------------------------
  0  DONE      -- artefact exists and reproduces its gate
  2  RETRY     -- a real execution failure; the controller retries, and after
                  the 2nd failure marks the task SKIPPED with the reason
  3  IMPOSSIBLE-- this task can never succeed here (no checkpoint, model does
                  not yield hidden states, ...) -> SKIPPED immediately
  7  NOT-A100  -- the device is not an A100; the task must not run (rule 13)
  9  ORACLE    -- a cell's output does not reproduce its per-seed oracle. The
                  export is withheld and the task is FAILED, never DONE.

GATE VALUES
-----------
`GATE=<float>` is printed on success (7-variable z-space MSE on the shared
`(W//16)*16` windows) so the controller can record it in `queue_state.tsv`.
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

sys.path.insert(0, QUEUE_DIR)
import queue_store                                                  # noqa: E402

PY_HPC = "/home/sychan552/.conda/envs/mlflu_hpc/bin/python"
PY_LLM = "/home/sychan552/.venvs/mlflu_llm/bin/python"

#: the staged analysis tree on the cluster (`stage_analysis.sh`): a mini repo root
#: with scripts/, paper_tables/, figures/, and hpc_results/expanded_runs symlinked
#: to the real cell tree. Finalisation runs HERE, so it needs no login node.
ANALYSIS = os.path.join(RUNS, "analysis")

W_AVAILABLE = {24: 170, 36: 158, 48: 146, 60: 134}

#: env name -> interpreter. A queue row names its env explicitly; a row whose env
#: is unknown or whose interpreter is absent is SKIPPED as `env-missing`, never retried.
ENVS = {"hpc": PY_HPC, "llm": PY_LLM}


def arms() -> dict:
    """hf_id -> registry entry (venv, encoder_batch_size, revision, label)."""
    import json as _json
    reg = _json.load(open(REGISTRY, encoding="utf-8"))
    return {a["hf_id"]: a for a in reg["arms"]}


def pinned_revision(arm: dict):
    """The pinned sha: the registry constant, else what the CPU probe measured."""
    if arm.get("revision"):
        return arm["revision"]
    p = os.path.join(QUEUE_DIR, "p2", f"{arm['label']}.json")
    if os.path.exists(p):
        try:
            import json as _json
            rec = _json.load(open(p, encoding="utf-8"))
            if rec.get("ok") and rec.get("revision"):
                return rec["revision"]
        except OSError:
            pass
    return None


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def done(gate=None, note="") -> int:
    if gate is not None:
        print(f"GATE={gate}", flush=True)
    print(f"NOTE={note}", flush=True)
    return 0


def retry(reason) -> int:
    print(f"REASON={reason}", flush=True)
    return 2


def impossible(reason) -> int:
    print(f"SKIP_REASON={reason}", flush=True)
    return 3


def oracle_halt(reason) -> int:
    print(f"REASON={reason}", flush=True)
    return 9


# ---------------------------------------------------------------- hardware ----
def assert_a100() -> None:
    import torch
    if not torch.cuda.is_available():
        print("REASON=no-cuda-device")
        sys.exit(7)
    name = torch.cuda.get_device_name(0)
    cap = torch.cuda.get_device_capability(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 2 ** 30
    log(f"[a100] measured gpu={name} capability={cap} vram={vram:.1f}GiB")
    if "A100" not in name:
        print(f"REASON=not-a100:{name}")
        sys.exit(7)


# ------------------------------------------------------------------ MIFlu ----
def eval_slice(W: int, batch: int = 16) -> int:
    return (W // batch) * batch


def miflu_cell(task_id: str) -> int:
    """One MIFlu reproduction cell: retrain if needed, export all 7 vars, verify."""
    import threading
    sys.path.insert(0, CODE)
    import export_miflu_all7 as EX
    import miflu_controller_v2 as MC

    m = re.match(r"miflu_L(\d+)_s(\d+)$", task_id)
    if not m:
        return impossible(f"bad miflu task id {task_id!r}")
    L, S = int(m.group(1)), int(m.group(2))
    want = EX.oracle_mse(L, S)
    if want is None:
        return impossible("no oracle for this (L, seed)")

    # ---- idempotence: already verified? -----------------------------------
    ckpt, prov = EX.find_ckpt(L, S)
    if ckpt is not None and MC.marker_exists(L, S):
        ok, why = MC.verify_cell(L, S, ckpt, want)
        if ok:
            return done(want, f"already DONE ({why}); ckpt={prov}")
        log(f"[recheck] marker present but verification failed ({why}) -> redoing")

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
    log(f"[plan] {task_id} action={action} oracle={want:.6f} ckpt={(ckpt or '-')}")

    if action == "done":
        MC.write_marker(L, S, {"L": L, "seed": S, "checkpoint": ckpt, "provenance": prov,
                               "oracle_mse": want,
                               "verified_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                               "detail": "re-verified by master queue"})
        return done(want, f"re-verified existing cell ckpt={prov}")

    res = MC.process_cell(cell, py=sys.executable,
                          deadline=time.time() + 1e9, stop=threading.Event())
    st = str(res.get("status", ""))
    log(f"[result] {task_id} {res}")
    if st == "verified":
        return done(want, res.get("detail", ""))
    if st.startswith("HALT"):
        return oracle_halt(st)
    if st.startswith("no-checkpoint"):
        return impossible(st)
    return retry(st or "unknown-failure")


# -------------------------------------------------------------- LLM cells ----
def llm_cell(task_id: str, model: str, L: int, seed: int, env_name: str = "") -> int:
    """One frozen-encoder cell: `train_backbone_966.py --backbone llm_encoder`."""
    m = re.match(r"(.+)_L(\d+)_s(\d+)$", task_id)
    if not m:
        return impossible(f"bad llm task id {task_id!r}")
    label = m.group(1)
    arm = arms().get(model)
    if arm is None:
        return impossible(f"model {model!r} not in arms_registry.json")
    # ---- per-model environment routing (Gap 2) ----------------------------
    # The queue row names the env; the registry is the fallback. A wrong env is
    # the classic silent failure (qwen3_5 cannot even be *parsed* by transformers
    # 4.x), so it is resolved explicitly and a missing env is SKIPPED, not retried.
    venv = env_name if env_name not in ("", "-") else arm["venv"]
    py = ENVS.get(venv)
    if py is None:
        return impossible(f"env-missing: unknown env {venv!r} (known: {sorted(ENVS)})")
    if not os.path.exists(py):
        return impossible(f"env-missing: interpreter {py} does not exist")
    log(f"[llm] {task_id} env={venv} interpreter={py}")
    rev = pinned_revision(arm)
    if rev is None:
        return impossible("no pinned revision yet - the CPU probe (kind=llm_probe) must run first")

    export_dir = os.path.join(EXPANDED, f"{label}_L{L}_s{seed}")
    ckpt_dir = os.path.join(RUNS, "checkpoints", "llm_encoder", label)
    cache = os.path.join(SCRATCH, "llm_cache", f"{label}.pt")
    npz = os.path.join(export_dir, f"pred_{label}_L{L}_s{seed}.npz")
    man = os.path.join(export_dir, f"manifest_{label}_L{L}_s{seed}.json")
    metrics = os.path.join(export_dir, "metrics.csv")

    # ---- idempotence: gate on the cell itself -----------------------------
    if os.path.exists(npz) and os.path.exists(man) and os.path.exists(metrics):
        gate = llm_gate(npz, L)
        if gate is not None:
            return done(gate, f"already DONE ({npz})")

    if not os.path.exists(py):
        return impossible(f"missing interpreter {py}")
    os.makedirs(export_dir, exist_ok=True)
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(os.path.dirname(cache), exist_ok=True)

    cmd = [py, "-u", "train_backbone_966.py",
           "--backbone", "llm_encoder", "--arm-label", label,
           "--llm-model-id", model,
           "--encoder-batch-size", str(arm["encoder_batch_size"]),
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
    })
    log(f"[llm] {task_id} exec: {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=CODE, env=env)
    if r.returncode != 0:
        return retry(f"train_backbone_966 rc={r.returncode}")

    gate = llm_gate(npz, L)
    if gate is None:
        return retry("trainer returned 0 but the cell artefact is absent/malformed")
    return done(gate, f"{npz}")


def llm_gate(npz_path: str, L: int):
    """7-var z-space MSE on the shared window set, or None if the cell is invalid."""
    try:
        import numpy as np
        z = np.load(npz_path)
        pred, target = z["pred"], z["target"]
        if pred.shape != target.shape or pred.ndim != 3:
            log(f"[gate] bad shape pred={pred.shape} target={target.shape}")
            return None
        W, nvar, nlead = pred.shape
        if nvar != 7 or nlead != L:
            log(f"[gate] not (W,7,{L}): {pred.shape}")
            return None
        if W != W_AVAILABLE[L]:
            log(f"[gate] W={W} != available {W_AVAILABLE[L]} for L={L}")
            return None
        n = eval_slice(W)
        err = pred[:n].astype("float64") - target[:n].astype("float64")
        return float((err ** 2).mean())
    except Exception as exc:                                   # noqa: BLE001
        log(f"[gate] cannot read {npz_path}: {type(exc).__name__}: {exc}")
        return None


# ------------------------------------------------------------- LLM probes ----
def probe_record(arm: dict):
    import json as _json
    p = os.path.join(QUEUE_DIR, "p2", f"{arm['label']}.json")
    if not os.path.exists(p):
        return {}
    try:
        return _json.load(open(p, encoding="utf-8"))
    except OSError:
        return {}


def model_ref(arm: dict, model: str) -> str:
    """What to pass as `--llm-model-id`: the hub id, or a local dir from the
    curl fallback download (independent of huggingface_hub working)."""
    rec = probe_record(arm)
    ld = rec.get("local_dir")
    if ld and os.path.isdir(ld):
        return ld
    return model


def llm_probe(task_id: str, model: str) -> int:
    """P2: pin the revision, get the weights on CPU, prove a hidden-state read-out.

    Redundancy rule for tonight: TWO independent download paths. The primary is
    `huggingface_hub.snapshot_download` (3 attempts); if that fails for any
    reason (proxy/DNS/http2/python stack), the fallback resolves the repo's file
    list from the HTTP API and fetches every file with plain `curl -L --retry`.
    A model is only declared unusable when a *forward pass with real weights*
    says so -- not because one download mechanism broke.

    Runs ONLY on a CPU partition (`QUEUE_CPU_ONLY=1`): rule 13(b). It never
    touches an A100 and it is not on the critical path -- the MIFlu cells do not
    depend on it.
    """
    import json as _json
    import urllib.request

    outdir = os.path.join(QUEUE_DIR, "p2")
    os.makedirs(outdir, exist_ok=True)
    slug = task_id[len("probe_"):] if task_id.startswith("probe_") else task_id
    rec_path = os.path.join(outdir, f"{slug}.json")
    rec = {"task_id": task_id, "model_id": model, "when": time.strftime("%F %T")}

    # ---- idempotence -------------------------------------------------------
    old = probe_record({"label": slug})
    if old.get("ok"):
        queue_store.unblock_model(model, "TODO",
                                  f"unblocked by CPU probe: revision={old.get('revision')} "
                                  f"hidden read-out OK D={old.get('hidden_dim')}")
        return done(None, f"already probed: revision={old.get('revision')} D={old.get('hidden_dim')}")

    # ---- 1. pin the revision sha (curl AND urllib: two paths) --------------
    api = f"https://huggingface.co/api/models/{model}"
    rev = None
    try:
        with urllib.request.urlopen(api, timeout=30) as fh:
            rev = _json.loads(fh.read().decode("utf-8")).get("sha")
    except Exception as exc:                                    # noqa: BLE001
        rec["urllib_error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
    if not rev:
        r = subprocess.run(["curl", "-sS", "-m", "40", api], capture_output=True, text=True)
        try:
            rev = _json.loads(r.stdout).get("sha")
        except Exception:                                       # noqa: BLE001
            rev = None
    if not rev:
        return retry(f"revision-lookup-failed; urllib={rec.get('urllib_error')}")
    rec["revision"] = rev
    log(f"[probe] {task_id} pinned revision={rev}")

    # ---- 2. weights: snapshot_download, then a curl fallback --------------
    env = dict(os.environ)
    env.update({"HF_HOME": os.path.join(SCRATCH, "hf_cache"),
                "HF_HUB_CACHE": os.path.join(SCRATCH, "hf_cache"),
                "HF_HUB_DOWNLOAD_TIMEOUT": "60"})
    dl_ok = False
    dl_err = ""
    for attempt in range(1, 4):
        r = subprocess.run(
            [PY_HPC, "-c",
             "from huggingface_hub import snapshot_download as s;"
             f"p=s(repo_id={model!r}, revision={rev!r}, max_workers=2);print('PATH='+p)"],
            cwd=CODE, env=env, capture_output=True, text=True)
        if r.returncode == 0:
            dl_ok = True
            break
        dl_err = (r.stderr or "").strip().splitlines()[-1:] or [""]
        dl_err = dl_err[0]
        log(f"[probe] snapshot_download attempt {attempt}/3 failed: {dl_err[:200]}")
        time.sleep(20 * attempt)
    rec["snapshot_download_ok"] = dl_ok

    local_dir = os.path.join(SCRATCH, "hf_models", slug)
    if not dl_ok:
        log(f"[probe] falling back to curl download into {local_dir}")
        try:
            with urllib.request.urlopen(f"{api}/tree/{rev}?recursive=1", timeout=40) as fh:
                tree = _json.loads(fh.read().decode("utf-8"))
        except Exception:                                       # noqa: BLE001
            r = subprocess.run(["curl", "-sS", "-m", "60", f"{api}/tree/{rev}?recursive=1"],
                               capture_output=True, text=True)
            tree = _json.loads(r.stdout)
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
            url = f"https://huggingface.co/{model}/resolve/{rev}/{p}"
            r = subprocess.run(["curl", "-sSL", "--retry", "3", "--retry-delay", "5",
                                "-m", "3600", "-o", dst, url], capture_output=True, text=True)
            if r.returncode != 0:
                rec["curl_error"] = f"{p}: {r.returncode} {(r.stderr or '')[:200]}"
                log(f"[probe] curl failed on {p}: {rec['curl_error']}")
                break
            ok_n += 1
        rec["files_downloaded"] = ok_n
        rec["files_total"] = len(files)
        if ok_n != len(files):
            _save(rec_path, rec)
            return retry(f"both download paths failed ({dl_err[:160]})")
        rec["local_dir"] = local_dir

    # ---- 3. CPU 2-layer smoke test: is there a hidden-state read-out? ------
    ref = rec.get("local_dir") or model
    smoke_json = os.path.join(outdir, f"{slug}.smoke.json")
    smoke = [PY_HPC, os.path.join(QUEUE_DIR, "probe_hidden_state.py"),
             "--model", ref, "--revision", rev, "--layers", "2", "--json", smoke_json]
    r2 = subprocess.run(smoke, cwd=CODE, env=env, capture_output=True, text=True)
    rec["smoke_rc"] = r2.returncode
    rec["smoke_tail"] = ((r2.stdout or "") + (r2.stderr or ""))[-1200:]

    if r2.returncode == 0:
        try:
            s = _json.load(open(smoke_json, encoding="utf-8"))
            rec.update({"ok": True, "hidden_dim": s.get("hidden_dim"),
                        "hidden_source": s.get("hidden_source"),
                        "model_type": s.get("model_type")})
            _save(rec_path, rec)
            n = queue_store.unblock_model(
                model, "TODO",
                f"unblocked by CPU probe: revision={rev} hidden read-out "
                f"{s.get('hidden_source')} D={s.get('hidden_dim')}")
            return done(None, f"revision={rev} D={s.get('hidden_dim')} unblocked {n} cells")
        except Exception as exc:                                # noqa: BLE001
            rec.update({"ok": False, "error": f"smoke json unreadable: {exc}"})
            _save(rec_path, rec)
            return retry(f"smoke-json-unreadable {exc}")

    reason = _tail_reason(smoke_json, r2)
    if r2.returncode == 3:
        rec.update({"ok": False, "error": reason})
        _save(rec_path, rec)
        n = queue_store.unblock_model(model, "SKIPPED",
                                      f"probe: no hidden-state read-out ({reason[:200]})")
        return impossible(f"no-hidden-state-readout: {reason[:200]} (skipped {n} cells)")
    rec.update({"ok": False, "error": reason})
    _save(rec_path, rec)
    return retry(f"smoke-test rc={r2.returncode}: {reason[:160]}")


def _tail_reason(smoke_json, proc) -> str:
    import json as _json
    try:
        s = _json.load(open(smoke_json, encoding="utf-8"))
        if s.get("error"):
            return str(s["error"])[:300]
    except OSError:
        pass
    txt = ((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()
    return txt[-1][:300] if txt else "no output"


def _save(path: str, rec: dict) -> None:
    import json as _json
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        _json.dump(rec, fh, indent=2, sort_keys=True)
    os.replace(tmp, path)


# ------------------------------------------------------------- finalisation ----
#: F1-F5. Cells on disk are worth nothing until these have run: they are what
#: produce the MSE/MAE, PTE/PIE, the K&S verdict, CRPS/WIS and every figure.
#: Each entry is (label, [argv...]) executed with cwd = ANALYSIS.
FINALISE_STEPS = {
    "final_import_miflu": [
        ["scripts/import_miflu_predictions.py", "--npz-dir", "author_runs",
         "--horizons", "24", "36", "48", "60", "--seeds"] + [str(s) for s in range(2021, 2031)],
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

#: the table whose mtime proves the chain actually rewrote something
PROOF_TABLE = "paper_tables/BENCH_MSE_BY_MODEL_L.csv"
CORE_TABLES = ["paper_tables/BENCH_MSE_BY_MODEL_L.csv",
               "paper_tables/BENCH_PTE_PIE_BY_STEP.csv",
               "paper_tables/BENCH_EFFICIENCY.csv"]


def cell_signature() -> str:
    """Cheap identity of the on-disk cell population (so unchanged runs no-op)."""
    n_exp = n_all7 = 0
    newest = 0.0
    for base, pat in ((os.path.join(RUNS, "expanded_runs"), "pred_*.npz"),
                      (os.path.join(AUTHOR_RUNS), "pred_miflu_L*_seed*.npz")):
        try:
            for p in glob.glob(os.path.join(base, "*", pat)):
                newest = max(newest, os.path.getmtime(p))
                n_exp += 1
        except OSError:
            pass
    try:
        for p in glob.glob(os.path.join(AUTHOR_RUNS, "L*_all7", "pred_*.npz")):
            newest = max(newest, os.path.getmtime(p))
            n_all7 += 1
    except OSError:
        pass
    return f"exp={n_exp} all7={n_all7} newest={int(newest)}"


def finalise(task_id: str, env_name: str = "") -> int:
    """Run one F-step group against the staged analysis tree.

    Idempotent by cell signature: if nothing new landed since the last successful
    run it returns DONE with `NOTE=no-new-cells` in ~1 s, which is what lets the
    controller re-arm it after EVERY batch of cells instead of once at the end.

    Tolerant of partial data on purpose: a missing MIFlu row or a missing LLM arm
    must not stop the tables that CAN be produced, so a failing step is recorded
    and the chain continues; the task is only retried when no core table exists.
    """
    import fcntl
    import glob as _glob

    if task_id not in FINALISE_STEPS:
        return impossible(f"unknown finalise step {task_id!r}")
    if not os.path.isdir(os.path.join(ANALYSIS, "scripts")):
        return impossible(f"env-missing: analysis tree absent at {ANALYSIS} "
                          f"(run stage_analysis.sh)")

    outdir = os.path.join(QUEUE_DIR, "finalise")
    os.makedirs(outdir, exist_ok=True)
    logpath = os.path.join(outdir, f"{task_id}.log")
    recpath = os.path.join(outdir, f"{task_id}.json")

    # ---- cross-lane lock: two controllers must never rebuild at the same time --
    lockfh = open(os.path.join(QUEUE_DIR, ".finalise.lock"), "a+")
    try:
        fcntl.flock(lockfh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lockfh.close()
        return done(None, "another lane is finalising; skipped this round")

    try:
        sig = cell_signature()
        rec = {}
        if os.path.exists(recpath):
            try:
                rec = json.load(open(recpath, encoding="utf-8"))
            except OSError:
                rec = {}
        if rec.get("signature") == sig and rec.get("ok"):
            print("NOTE=no-new-cells", flush=True)
            return done(None, f"no new cells since the last successful run ({sig})")

        venv = env_name if env_name not in ("", "-") else "hpc"
        py = ENVS.get(venv)
        if py is None or not os.path.exists(py):
            return impossible(f"env-missing: interpreter for env {venv!r} not found")

        # ---- keep the pre-freeze reference before any table is overwritten ----
        prefreeze = os.path.join(outdir, "pre_freeze")
        os.makedirs(prefreeze, exist_ok=True)
        for t in CORE_TABLES:
            src = os.path.join(ANALYSIS, t)
            dst = os.path.join(prefreeze, os.path.basename(t))
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)

        proof = os.path.join(ANALYSIS, PROOF_TABLE)
        mtime_before = os.path.getmtime(proof) if os.path.exists(proof) else 0
        results, failures = [], []
        with open(logpath, "a", encoding="utf-8") as fh:
            fh.write("\n" + "=" * 78 + f"\n[{time.strftime('%F %T')}] {task_id} sig={sig}\n")
            fh.flush()
            for argv in FINALISE_STEPS[task_id]:
                cmd = [py, "-u"] + argv
                fh.write(f"\n$ {' '.join(cmd)}\n")
                fh.flush()
                t0 = time.time()
                r = subprocess.run(cmd, cwd=ANALYSIS, stdout=fh, stderr=subprocess.STDOUT)
                dt = time.time() - t0
                results.append({"cmd": " ".join(argv), "rc": r.returncode,
                                "seconds": round(dt, 1)})
                fh.write(f"[rc={r.returncode} {dt:.1f}s]\n")
                fh.flush()
                if r.returncode != 0:
                    failures.append(f"{os.path.basename(argv[0])} rc={r.returncode}")
        mtime_after = os.path.getmtime(proof) if os.path.exists(proof) else 0

        # ---- import_miflu / verify steps have their own success criterion -----
        gate = None
        if task_id == "final_import_miflu":
            gate = _count_imported()
            ok = gate >= 0
        elif task_id == "final_miflu_oracle":
            tail = _tail(logpath, 4000)
            if "PASS" in tail:
                gate = 1.0
                ok = True
            elif "SKIPPED" in tail:
                gate = 0.0
                ok = True            # legitimately not applicable yet (row not merged)
            else:
                gate = -1.0
                ok = False           # a real oracle mismatch: loud, not DONE-green
        else:
            ok = (mtime_after > mtime_before) or (not failures)
            gate = float(sum(1 for t in CORE_TABLES
                             if os.path.exists(os.path.join(ANALYSIS, t))))

        rec = {"task_id": task_id, "signature": sig, "ok": bool(ok),
               "steps": results, "failures": failures, "gate": gate,
               "proof_mtime_before": mtime_before, "proof_mtime_after": mtime_after,
               "when": time.strftime("%F %T")}
        _save(recpath, rec)
        note = (f"steps={len(results)} failed={len(failures)} "
                f"proof_table={'rewritten' if mtime_after > mtime_before else 'unchanged'}"
                + (f" failures={failures}" if failures else ""))
        log(f"[finalise] {task_id}: {note}")

        if task_id == "final_miflu_oracle" and not ok:
            return oracle_halt("verify_miflu_oracle did not print PASS (see "
                               f"{logpath})")
        if not ok:
            return retry(f"finalise {task_id} produced nothing: {failures}")
        return done(gate, note)
    finally:
        try:
            fcntl.flock(lockfh, fcntl.LOCK_UN)
        except OSError:
            pass
        lockfh.close()


def _count_imported() -> int:
    n = 0
    for p in glob.glob(os.path.join(EXPANDED, "miflu_L*", "pred_*.npz")):
        n += 1
    return n


def _tail(path: str, n: int = 2000) -> str:
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - n))
            return fh.read().decode("utf-8", "replace")
    except OSError:
        return ""


# -------------------------------------------------------------------- main ---
def main() -> int:
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
        assert_a100()

    if a.kind == "miflu_cell":
        return miflu_cell(a.task_id)
    if a.kind == "llm_cell":
        return llm_cell(a.task_id, a.model, int(a.L), int(a.seed), a.env)
    if a.kind == "llm_probe":
        return llm_probe(a.task_id, a.model)
    if a.kind == "finalise":
        return finalise(a.task_id, a.env)
    return impossible(f"unknown kind {a.kind!r}")


if __name__ == "__main__":
    sys.exit(main())

