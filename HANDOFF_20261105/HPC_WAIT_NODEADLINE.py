#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ONE persistent SSH connection with NO client-side deadline.

Difference from earlier attempts:
  * ServerAliveInterval=0 / ServerAliveCountMax=0  -> the client never aborts with
    "Timeout, server not responding". That message was OUR timeout, not the server's.
  * Exactly ONE connection, no retry loop -> no MaxStartups self-lockout
    (BUG_POSTMORTEM_20261102 C5).
  * The command IS the full rev9 capture, so recovery produces data immediately.
  * Read-only. Never submits, never cancels, never pkills.

Run detached:
  python HPC_WAIT_NODEADLINE.py
Stop:
  taskkill /PID <pid> /T /F
Logs: HPC_WAIT_NODEADLINE.log ; result: REV9_CAPTURE_RECOVERED.md
"""
from __future__ import annotations
import datetime, json, os, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "HPC_WAIT_NODEADLINE.log")
OUTTXT = os.path.join(HERE, "HPC_WAIT_NODEADLINE_OUTPUT.txt")
CAPTURE = os.path.join(HERE, "REV9_CAPTURE_RECOVERED.md")
STATUS = os.path.join(HERE, "HPC_WAIT_STATUS.json")
KEY = os.path.expanduser(r"~\.ssh\id_ed25519")
HOST = "sychan552@burgundy.hpc.cityu.edu.hk"


def log(msg):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


CAPTURE_CMD = r"""echo SHELL_OK
R=/gpfs1/scratch/sychan552/trackB_20261104
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
echo "=== UTC / HKT ==="; date -u; TZ=Asia/Hong_Kong date
echo "=== WHO / LOAD (D-state check) ==="; uptime; who | wc -l
echo "=== PS (look for D/D+ STAT) ==="; ps -u "$USER" -o pid,stat,etime,cmd | head -40
echo "=== SQUEUE ==="; squeue -u sychan552 -o '%.10i %.26j %.10T %.12M %.22R' 2>/dev/null
echo "=== 7CH JOB ==="; squeue -u sychan552 -n miflu_7ch_export -h 2>/dev/null; sacct -u sychan552 --starttime=2026-11-05T00:00 -X -o JobID,JobName,State,Elapsed 2>/dev/null | grep -iE '7ch|export' || echo NO_7CH_JOB
echo "=== CELLOK ==="
$PY "$R/cellok.py" count "$R/core/export" "$R/core/cells.tsv" 2>&1 | head -2
$PY "$R/cellok.py" count "$R/all/export" "$R/all/cells_all.tsv" 2>&1 | head -2
echo "=== 7CH OUTPUTS ==="; ls -la "$R/core/export7ch" 2>/dev/null | head -12 || echo NO_DIR
echo -n "npz_count "; find "$R/core/export7ch" -name '*.npz' 2>/dev/null | wc -l
echo "=== SENTINELS ==="; ls -la "$R/core/phase.done" "$R/all/phase.done" "$R/all/post_all.started" 2>/dev/null || echo NONE
echo "=== CONTROLLER ==="; tail -8 "$R/all/logs/controller_v2.log" 2>/dev/null
echo "=== LEGACY ==="; wc -l "$R/all/legacy_done.tsv" 2>/dev/null || true
echo "=== QUOTA ==="; mmlsquota -u sychan552 2>/dev/null | grep -e home -e scratch
echo CAPTURE_DONE"""

SSH = ["ssh", "-n", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-i", KEY,
       "-o", "PreferredAuthentications=publickey", "-o", "ConnectTimeout=10",
       # critical: disable client-side liveness timeout entirely
       "-o", "ServerAliveInterval=0", "-o", "ServerAliveCountMax=0",
       "-o", "TCPKeepAlive=yes", HOST, CAPTURE_CMD]


def main():
    log("NO_DEADLINE_WAIT_START single_connection=True client_timeout=DISABLED")
    p = subprocess.Popen(SSH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, bufsize=0)
    lines = []
    started = time.time()

    def rd():
        for raw in iter(p.stdout.readline, b""):
            x = raw.decode("utf-8", errors="replace").rstrip()
            lines.append(x)
            with open(OUTTXT, "a", encoding="utf-8") as f:
                f.write(x + "\n")
            # log only milestones, not every line
            if any(k in x for k in ("SHELL_OK", "=== ", "CAPTURE_DONE", "D-state",
                                    "COMPLETE", "NO_7CH_JOB", "npz_count")):
                log("OUT " + x[:200])
    threading.Thread(target=rd, daemon=True).start()

    # NO deadline: wait indefinitely, heartbeat every 30 s
    hb = 0
    while p.poll() is None:
        time.sleep(1)
        if int(time.time() - started) // 30 > hb:
            hb = int(time.time() - started) // 30
            log(f"still waiting elapsed={int(time.time()-started)}s lines={len(lines)}")
    p.wait()
    rc = p.returncode
    log(f"SSH_EXIT {rc} elapsed={int(time.time()-started)}s lines={len(lines)}")

    ok = rc == 0 and any("SHELL_OK" in x for x in lines)
    if ok:
        hdr = ("# REV9 live capture — recovered after no-deadline wait\n\n"
               f"- Captured UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n"
               f"- SSH exit: {rc}; elapsed: {int(time.time()-started)} s\n"
               "- Read-only. No job submitted, no job cancelled, no pkill.\n\n```\n")
        with open(CAPTURE, "w", encoding="utf-8", newline="\n") as f:
            f.write(hdr + "\n".join(lines) + "\n```\n")
        log(f"CAPTURE_WRITTEN {CAPTURE}")
    with open(STATUS, "w", encoding="utf-8") as f:
        json.dump({"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "ssh_exit": rc, "shell_ok": ok, "lines": len(lines),
                   "elapsed_s": int(time.time()-started),
                   "capture": CAPTURE if ok else None}, f, indent=2)
    log("WAIT_END")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
