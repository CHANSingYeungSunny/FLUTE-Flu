#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""miflu_controller_v2.py -- drive the MIFlu 7-channel export to 40/40 cells.

Called by `miflu_a100_controller_v2.sh` inside an A100/`stingy` allocation. It
does NOT train anything itself; it decides, per (L, seed), whether the cell is
already trustworthy, can be produced by a forward pass, or must be retrained,
then runs exactly that and verifies the result.

WHY A REWRITE (job 719030, 2026-11-01)
-------------------------------------
719030 was preempted (`PreemptMode=CANCEL`, `special_cs` landing on
gpu-a100-04) 13 min in, at epoch 2/20 of L=36 seed 2025. Nothing was wrong with
its `sbatch` self-requeue -- it never reached the wall-clock guard. Two further
defects made its partial output untrustworthy:

  1. `export_miflu_all7.find_ckpt` preferred `ckpt_L{L}_s{seed}/best_miflu_L{L}.pth`,
     which for seed 2021 holds the *best-val rep* of the earlier 10-rep run
     (seed 2024). L24 seed 2021 therefore failed its legacy cross-check
     (`dPRED=1.993`) and L36 seed 2021 was silently exported from seed-2024
     weights. Fixed in that file; this controller re-verifies every cell from
     its own npz.
  2. Its CELLS list omitted each horizon's best-val rep (36:2024, 48:2021,
     60:2025) and included 60:2021, which would have exported the L60 best rep
     (seed 2025) under the seed-2021 label. The enumeration here is 4x10 and
     the checkpoint trust order is explicit.

TRUST IS DERIVED, NEVER ASSUMED
-------------------------------
A cell is DONE only when all four rule-11 artefacts exist, the manifest's
`checkpoint.sha256` equals the sha256 of the checkpoint the trust order picks,
and the npz reproduces its own per-seed oracle to <= 1e-5 on the first
`(W // 16) * 16` test windows (the shared evaluation-window rule). Every DONE
cell gets a marker under `.miflu_verify/`, so later generations are O(1).

RETURN CODES
------------
  0  work loop finished (all planned cells processed; see the summary)
  2  wall-clock budget reached -- stop claiming new cells (successor pending)
  3  nothing to do: all 40 cells already verified
  4  a cell failed (train/export non-zero) but the rest were processed
  6  ORACLE/verification mismatch -> HALT marker written, do not accept output
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time

import numpy as np

CODE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CODE)

AUTHOR_RUNS = "/gpfs1/home/sychan552/stage5_a2_durable/author_runs"
HORIZONS = [24, 36, 48, 60]
SEEDS = list(range(2021, 2031))
# test windows available under containment="strict" (the npz must carry all of them)
W_AVAILABLE = {24: 170, 36: 158, 48: 146, 60: 134}
BATCH = 16

VERIFY_DIR = os.path.join(AUTHOR_RUNS, ".miflu_verify")
HALT_FILE = os.path.join(AUTHOR_RUNS, ".MIFLU_HALT")
TOL = 1e-5

_print_lock = threading.Lock()
_admin_fh = None


def eval_slice(W: int, batch: int = BATCH) -> int:
    """Mirror of `scripts/eval_windows.py::eval_slice` -- the one shared rule.

    Never hard-code 160/144/144/128: they are `(W // 16) * 16` for the four
    horizons and are recomputed here from the npz's own window count.
    """
    return (W // batch) * batch


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    with _print_lock:
        print(line, flush=True)
        if _admin_fh is not None:
            _admin_fh.write(line + "\n")
            _admin_fh.flush()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def cell_paths(L: int, S: int) -> dict:
    d = os.path.join(AUTHOR_RUNS, f"L{L}_all7")
    return {
        "dir": d,
        "npz": os.path.join(d, f"pred_miflu_L{L}_seed{S}.npz"),
        "csv": os.path.join(d, f"predictions_miflu_L{L}_seed{S}.csv"),
        "results": os.path.join(d, f"results_miflu_L{L}_seed{S}.csv"),
        "manifest": os.path.join(d, f"manifest_miflu_L{L}_seed{S}.json"),
    }


def npz_mse(path: str, L: int) -> tuple:
    """7-variable MSE on the shared window set, straight from the npz.

    Returns (mse, W, n_eval). Asserts the (W, 7, L) layout before slicing.
    """
    z = np.load(path)
    pred, target = z["pred"], z["target"]
    if pred.shape != target.shape or pred.ndim != 3:
        raise AssertionError(f"bad npz shape pred={pred.shape} target={target.shape}")
    W, nvar, nlead = pred.shape
    if nvar != 7 or nlead != L:
        raise AssertionError(f"npz is not (W,7,L): {pred.shape} vs L={L}")
    if W != W_AVAILABLE[L]:
        raise AssertionError(f"npz has W={W} test windows, expected {W_AVAILABLE[L]} for L={L}")
    n = eval_slice(W)
    err = pred[:n].astype(np.float64) - target[:n].astype(np.float64)
    return float(np.mean(err ** 2)), W, n


def verify_cell(L: int, S: int, ckpt: str, want_oracle: float) -> tuple:
    """Full DONE check: artefacts present, checkpoint identity, oracle agreement."""
    p = cell_paths(L, S)
    missing = [k for k in ("npz", "csv", "results", "manifest") if not os.path.exists(p[k])]
    if missing:
        return False, f"missing {missing}"
    man = json.load(open(p["manifest"], encoding="utf-8"))
    man_sha = (man.get("checkpoint") or {}).get("sha256")
    got_sha = sha256_file(ckpt)
    if man_sha != got_sha:
        return False, f"manifest checkpoint sha {str(man_sha)[:12]} != {got_sha[:12]} ({os.path.basename(ckpt)})"
    mse, W, n = npz_mse(p["npz"], L)
    if want_oracle is None:
        return False, "no oracle for this (L, seed)"
    d = abs(mse - want_oracle)
    if d > TOL:
        return False, f"oracle mismatch: npz MSE {mse:.6f} vs {want_oracle:.6f} (|d|={d:.2e})"
    return True, f"verified mse={mse:.6f} (|d|={d:.2e}) W={W} n_eval={n}"


def write_marker(L: int, S: int, info: dict) -> None:
    os.makedirs(VERIFY_DIR, exist_ok=True)
    p = os.path.join(VERIFY_DIR, f"L{L}_s{S}.json")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=2, sort_keys=True)
    os.replace(tmp, p)


def marker_exists(L: int, S: int) -> bool:
    return os.path.exists(os.path.join(VERIFY_DIR, f"L{L}_s{S}.json"))


def ensure_best_copies() -> list:
    """Copy the four original-run best checkpoints to a safe directory (idempotent).

    They are the ONLY weights for L24/L36 seed 2024, L48 seed 2021, L60 seed 2025
    and must survive any retrain that happens to write into `ckpt_L{L}_s{S}/`.
    """
    os.makedirs(os.path.join(AUTHOR_RUNS, "ckpt_best_repro"), exist_ok=True)
    out = []
    for L in HORIZONS:
        src = os.path.join(AUTHOR_RUNS, f"ckpt_L{L}_s2021", f"best_miflu_L{L}.pth")
        dst = os.path.join(AUTHOR_RUNS, "ckpt_best_repro", f"best_miflu_L{L}.pth")
        if not os.path.exists(src):
            out.append((L, "no source"))
            continue
        if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src):
            out.append((L, "already copied"))
            continue
        tmp = dst + ".part"
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)
        out.append((L, "copied"))
    return out


def run_cmd(cmd: list, logpath: str, timeout: float = None) -> int:
    os.makedirs(os.path.dirname(logpath), exist_ok=True)
    with open(logpath, "a", encoding="utf-8") as fh:
        fh.write("\n" + "=" * 78 + "\n")
        fh.write(f"[{time.strftime('%F %T')}] $ {' '.join(cmd)}\n")
        fh.flush()
        try:
            r = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT,
                               cwd=CODE, timeout=timeout)
            return r.returncode
        except subprocess.TimeoutExpired:
            fh.write("[timeout]\n")
            return 124


def process_cell(cell: dict, py: str, deadline: float, stop: threading.Event) -> dict:
    L, S, action = cell["L"], cell["S"], cell["action"]
    tag = f"L{L}_s{S}"
    if time.time() > deadline and action == "train":
        return {"cell": tag, "status": "deferred"}
    if stop.is_set():
        return {"cell": tag, "status": "skipped-halt"}

    run_dir = os.path.join(AUTHOR_RUNS, "_seedruns", tag)
    ckpt_dir = os.path.join(AUTHOR_RUNS, "ckpt_retrain", tag)
    os.makedirs(run_dir, exist_ok=True)

    if action == "train":
        log(f"[train] {tag} start")
        cmd = [py, "-u", "train_miflu.py",
               "--profile", "author_repo_966", "--horizon", str(L),
               "--text-source", "author_file", "--reps", "1", "--seed", str(S),
               "--epochs", "20", "--batch", "16", "--learning-rate", "0.0001",
               "--containment", "strict",
               "--export-dir", run_dir, "--ckpt-dir", ckpt_dir]
        rc = run_cmd(cmd, os.path.join(run_dir, "controller_train.log"))
        if rc != 0:
            log(f"[train] {tag} FAILED rc={rc} (see {run_dir}/controller_train.log)")
            return {"cell": tag, "status": f"train-failed rc={rc}"}
        log(f"[train] {tag} done")

    # export (always --force: an existing file with the wrong checkpoint must be replaced)
    log(f"[export] {tag} start (action={action})")
    rc = run_cmd([py, "-u", "export_miflu_all7.py", "--cells", f"{L}:{S}",
                  "--device", "cuda", "--force"],
                 os.path.join(run_dir, "controller_export.log"))
    if rc != 0:
        log(f"[export] {tag} FAILED rc={rc}")
        return {"cell": tag, "status": f"export-failed rc={rc}"}

    ckpt, prov = cell["pick"]
    if ckpt is None:
        # The plan's pick is STALE for a retrain cell: at plan time no checkpoint
        # existed, so `find_ckpt` returned None. Re-resolve it now, through the
        # same trust order, or the verification below would compare against a
        # non-existent path (the 20:04 TypeError on L36 s2021/s2025/s2026).
        import export_miflu_all7 as EX
        ckpt, prov = EX.find_ckpt(L, S)
    if ckpt is None:
        log(f"[FAIL] {tag}: no checkpoint after {action} (trust order found none)")
        return {"cell": tag, "status": f"no-checkpoint-after-{action}"}
    ok, why = verify_cell(L, S, ckpt, cell["oracle"])
    if not ok:
        stop.set()
        try:
            with open(HALT_FILE, "w", encoding="utf-8") as fh:
                fh.write(f"{time.strftime('%F %T')} HALT on {tag}: {why}\n")
        except OSError:
            pass
        log(f"[HALT] {tag}: {why}")
        return {"cell": tag, "status": f"HALT: {why}"}

    write_marker(L, S, {"L": L, "seed": S, "checkpoint": ckpt, "provenance": prov,
                        "checkpoint_sha256": sha256_file(ckpt),
                        "oracle_mse": cell["oracle"],
                        "verified_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        "detail": why})
    log(f"[ok] {tag} {why}")
    return {"cell": tag, "status": "verified", "detail": why}


def build_plan(limit=None) -> list:
    import export_miflu_all7 as EX

    cells = []
    for L in HORIZONS:
        for S in SEEDS:
            ckpt, prov = EX.find_ckpt(L, S)
            want = EX.oracle_mse(L, S)
            action = None
            if marker_exists(L, S):
                action = "done"
            elif ckpt is None:
                action = "train"
            else:
                p = cell_paths(L, S)
                have = all(os.path.exists(p[k]) for k in ("npz", "csv", "results", "manifest"))
                if have:
                    ok, _why = verify_cell(L, S, ckpt, want)
                    action = "done" if ok else "export"   # wrong ckpt/stale -> re-export
                else:
                    action = "export"
            if action == "done" and ckpt is not None:
                write_marker(L, S, {"L": L, "seed": S, "checkpoint": ckpt,
                                    "provenance": prov, "oracle_mse": want,
                                    "verified_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                    "detail": "pre-existing cell re-verified"})
            cells.append({"L": L, "S": S, "action": action, "pick": (ckpt, prov), "oracle": want})
            if limit and len(cells) >= limit:
                return cells
    return cells


def main() -> int:
    global _admin_fh
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="print the plan and exit")
    ap.add_argument("--count", action="store_true", help="print the number of verified cells and exit")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--budget-seconds", type=float, default=11100.0)
    ap.add_argument("--admin-log", default="")
    ap.add_argument("--gen", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--no-copy", action="store_true")
    a = ap.parse_args()

    if a.count:
        n = sum(1 for L in HORIZONS for S in SEEDS if marker_exists(L, S))
        print(n)
        return 0

    if a.admin_log:
        _admin_fh = open(a.admin_log, "a", encoding="utf-8")

    t0 = time.time()
    py = sys.executable

    if a.plan:
        plan = build_plan(limit=a.limit)
        from collections import Counter
        cnt = Counter(c["action"] for c in plan)
        print(f"[plan] gen={a.gen} cells={len(plan)} {dict(cnt)}")
        for c in plan:
            ck = c["pick"][0] or "-"
            print(f"  L={c['L']:>2} seed={c['S']} {c['action']:<6} oracle={c['oracle']} ckpt={os.path.basename(ck)}")
        return 0

    if not a.no_copy:
        for L, what in ensure_best_copies():
            log(f"[backup] ckpt_L{L}_s2021/best_miflu_L{L}.pth -> ckpt_best_repro/ ({what})")

    if os.path.exists(HALT_FILE):
        log(f"[halt] {HALT_FILE} exists -> refusing to work")
        return 6

    plan = build_plan(limit=a.limit)
    todo = [c for c in plan if c["action"] != "done"]
    done = len(plan) - len(todo)
    log(f"[gen {a.gen}] plan: {len(plan)} cells, {done} already verified, {len(todo)} to do "
        f"({sum(1 for c in todo if c['action'] == 'train')} train + "
        f"{sum(1 for c in todo if c['action'] == 'export')} export)")

    if not todo:
        log(f"[gen {a.gen}] NOTHING TO DO: all {len(plan)} cells verified")
        return 3

    deadline = t0 + a.budget_seconds
    stop = threading.Event()
    q = queue.Queue()
    # exports first: they are ~20 s each and immediately raise the verified count
    for c in sorted(todo, key=lambda c: 0 if c["action"] == "export" else 1):
        q.put(c)

    results = []

    def worker():
        while not stop.is_set():
            try:
                c = q.get_nowait()
            except queue.Empty:
                return
            if time.time() > deadline:
                results.append({"cell": f"L{c['L']}_s{c['S']}", "status": "deferred"})
                continue
            try:
                results.append(process_cell(c, py, deadline, stop))
            except Exception as e:                        # noqa: BLE001
                log(f"[error] L{c['L']}_s{c['S']}: {type(e).__name__}: {e}")
                results.append({"cell": f"L{c['L']}_s{c['S']}", "status": f"error {type(e).__name__}"})

    n_workers = max(1, min(a.workers, len(todo)))
    log(f"[gen {a.gen}] starting {n_workers} workers, budget {a.budget_seconds:.0f}s")
    threads = [threading.Thread(target=worker, daemon=True) for _ in range(n_workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    n_ok = sum(1 for r in results if r.get("status") == "verified")
    n_halt = any(str(r.get("status", "")).startswith("HALT") for r in results)
    n_fail = [r for r in results if "failed" in str(r.get("status", "")) or "error" in str(r.get("status", ""))]
    n_def = sum(1 for r in results if r.get("status") == "deferred")
    total_verified = sum(1 for L in HORIZONS for S in SEEDS if marker_exists(L, S))

    log(f"[gen {a.gen}] summary: verified_now={n_ok} failed={len(n_fail)} deferred={n_def} "
        f"total_verified={total_verified}/40 elapsed={time.time() - t0:.0f}s")
    for r in results:
        if "failed" in str(r.get("status", "")) or "error" in str(r.get("status", "")):
            log(f"  [FAIL] {r['cell']}: {r['status']}")

    if n_halt:
        return 6
    if n_fail:
        return 4
    if total_verified < 40 and n_def:
        return 2
    if total_verified < 40:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
