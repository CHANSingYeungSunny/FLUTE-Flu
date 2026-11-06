#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recover a CityU Burgundy login node wedged by D-state processes.

VALIDATED 2026-11-05 (see 04_详细说明文档/HPC_LOGIN_NODE_DSTATE_RECOVERY.md and
HANDOFF_20261105/INCIDENT_20261105_LOGIN_NODE_DSTATE.md).

Problem
-------
`ssh` authenticates but returns zero bytes because the login shell cannot be
spawned (HPC_RUNBOOK gotcha 11). A D-state task does NOT discard SIGKILL: the
signal is pending and delivered when the task returns from I/O. Therefore, in
the short window where a shell does spawn, the FIRST command must be `pkill`,
not `ps` and not a status capture.

Key details that made it work
-----------------------------
* ONE persistent SSH connection, no retry loop (rapid retries -> MaxStartups
  `Connection closed`, BUG_POSTMORTEM_20261102 C5).
* `ServerAliveInterval=0` / `ServerAliveCountMax=0`: otherwise OUR client
  aborts with a misleading `Timeout, server not responding`.
* `pkill -9 -u "$USER" -f 'impo[r]t transformers'`: bracket self-exclusion so
  pkill does not match its own `bash -c` command line and kill the session.
* `timeout 4` around every kill and `timeout N` around every capture line:
  a /proc scan over D-state entries can hang and consume the whole window.
* NO `ps`, NO `du -sh`, NO heavy imports on the login node.
* Read-only with respect to jobs: never `sbatch`, never `scancel`, never
  delete files. Verify afterwards with `sacct` that no job changed state.

Usage
-----
    python hpc_login_node_recover.py --out-dir ./recovery --no-deadline
    python hpc_login_node_recover.py --out-dir ./recovery --deadline 600

Outputs: <out-dir>/recovery.log, recovery_output.txt, recovery_status.json,
         and REV9_CAPTURE_RECOVERED.md when a full capture completes.
"""
from __future__ import annotations
import argparse
import datetime
import json
import os
import socket
import subprocess
import sys
import threading
import time

DEFAULT_HOST = "sychan552@burgundy.hpc.cityu.edu.hk"
DEFAULT_IP = "144.214.138.99"
DEFAULT_ROOT = "/gpfs1/scratch/sychan552/trackB_20261104"

# Patterns use the bracket self-exclusion trick. Add site-specific stuck probes
# here, never broad patterns like 'python -c' (would kill unrelated work).
KILL_PATTERNS = [
    "impo[r]t transformers",
    "d[u] -sh",
    "dl_ds3[2].py",
    "export_miflu_7[c]h",
    "export_miflu_all[7]",
]


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_remote(root: str) -> str:
    kills = "\n".join(
        f"timeout 4 pkill -9 -u \"$USER\" -f '{p}' 2>/dev/null; echo PKILL_{i}=$?"
        for i, p in enumerate(KILL_PATTERNS)
    )
    return f"""{kills}
echo KILL_COMMANDS_ISSUED
echo SHELL_OK; date -u
R={root}
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
echo SQUEUE; timeout 8 squeue -u sychan552 -h -o "%i|%j|%T|%M" 2>/dev/null
echo CELLOK_CORE; timeout 20 $PY "$R/cellok.py" count "$R/core/export" "$R/core/cells.tsv" 2>&1 | head -1
echo CELLOK_ALL; timeout 20 $PY "$R/cellok.py" count "$R/all/export" "$R/all/cells_all.tsv" 2>&1 | head -1
echo NPZ7CH; timeout 8 find "$R/core/export7ch" -name '*.npz' 2>/dev/null | wc -l
echo JOB7CH; timeout 8 squeue -u sychan552 -n miflu_7ch_export -h 2>/dev/null; echo JOB7CH_END
echo QUOTA; timeout 8 mmlsquota -u sychan552 2>/dev/null | grep -e home -e scratch
echo CAPTURE_DONE
timeout 4 pkill -9 -u "$USER" -f '{KILL_PATTERNS[0]}' 2>/dev/null; echo PKILL_ROUND2=$?"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--ip", default=DEFAULT_IP)
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--key", default=os.path.expanduser(r"~\.ssh\id_ed25519"))
    ap.add_argument("--deadline", type=int, default=0,
                    help="0 = no deadline (wait indefinitely for a window)")
    ap.add_argument("--measure-only", action="store_true",
                    help="only measure TCP/22, do not connect or kill")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    log_p = os.path.join(args.out_dir, "recovery.log")
    out_p = os.path.join(args.out_dir, "recovery_output.txt")
    st_p = os.path.join(args.out_dir, "recovery_status.json")
    cap_p = os.path.join(args.out_dir, "REV9_CAPTURE_RECOVERED.md")

    def log(msg: str) -> None:
        line = f"[{now_utc()}] {msg}"
        print(line, flush=True)
        with open(log_p, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    # ---- measure first (no shell needed) ----
    s = socket.socket(); s.settimeout(6); t0 = time.time()
    try:
        s.connect((args.ip, 22))
        banner = s.recv(80).decode(errors="replace").strip()
        ok, detail = True, f"{time.time()-t0:.2f}s banner={banner}"
    except Exception as e:
        ok, detail = False, f"{type(e).__name__}: {e}"
    finally:
        s.close()
    log(f"MEASURE TCP22={ok} {detail}")
    if args.measure_only:
        return 0 if ok else 1
    if not ok:
        log("port 22 closed -> node isolated/down; NO remote remedy, wait or escalate")
        return 1

    ssh = ["ssh", "-n", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
           "-i", args.key, "-o", "PreferredAuthentications=publickey",
           "-o", "ConnectTimeout=10",
           "-o", "ServerAliveInterval=0", "-o", "ServerAliveCountMax=0",
           "-o", "TCPKeepAlive=yes", args.host, build_remote(args.root)]
    log("WAIT_START single_connection=True kill_first=True auto_submit=DISABLED")
    p = subprocess.Popen(ssh, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, bufsize=0)
    lines: list[str] = []
    started = time.time()

    def reader() -> None:
        for raw in iter(p.stdout.readline, b""):
            x = raw.decode("utf-8", errors="replace").rstrip()
            lines.append(x)
            with open(out_p, "a", encoding="utf-8") as f:
                f.write(x + "\n")
            log("OUT " + x[:220])
    threading.Thread(target=reader, daemon=True).start()

    hb = 0
    while p.poll() is None:
        time.sleep(1)
        elapsed = int(time.time() - started)
        if args.deadline and elapsed >= args.deadline:
            log(f"DEADLINE {args.deadline}s reached; terminating")
            p.kill(); break
        if elapsed // 30 > hb:
            hb = elapsed // 30
            log(f"waiting elapsed={elapsed}s lines={len(lines)}")
    p.wait()
    rc = p.returncode
    log(f"SSH_EXIT {rc} elapsed={int(time.time()-started)}s lines={len(lines)}")

    txt = "\n".join(lines)
    killed = "KILL_COMMANDS_ISSUED" in txt
    shell = "SHELL_OK" in txt
    status = {
        "utc": now_utc(), "ssh_exit": rc, "shell_appeared": shell,
        "kill_commands_issued": killed,
        "pkill_rcs": [x for x in lines if x.startswith("PKILL_")],
        "capture_done": "CAPTURE_DONE" in txt, "lines": len(lines),
        "note": "Read-only w.r.t. Slurm jobs. Verify with sacct after use.",
    }
    with open(st_p, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)
    if shell and "CAPTURE_DONE" in txt:
        with open(cap_p, "w", encoding="utf-8", newline="\n") as f:
            f.write("# Live capture after login-node recovery\n\n"
                    f"- UTC: {now_utc()}\n- SSH exit {rc}; kill issued {killed}\n"
                    "- No job submitted, cancelled or deleted.\n\n```\n"
                    + txt + "\n```\n")
        log(f"CAPTURE_WRITTEN {cap_p}")
    log("WAIT_END")
    return 0 if (shell and killed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
