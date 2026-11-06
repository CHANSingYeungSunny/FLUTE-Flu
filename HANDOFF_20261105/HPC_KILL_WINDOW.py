#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Opportunistic stuck-probe killer: issue pkill in the FIRST second of any shell window.

Design notes (learned from the 14:43:55 UTC 16-second window):
  * The remote command's FIRST line is pkill, NOT ps and NOT capture. Previously
    `ps ... | head` stalled and killed the only usable window.
  * Patterns use the bracket self-exclusion trick ('impo[r]t transformers') so
    pkill does not match its own `bash -c` command line and kill our session.
  * pkill is scoped with -u "$USER"; NO scancel, NO Slurm job is touched
    (Slurm jobs run on compute nodes, not this login shell).
  * Light capture only afterwards: no `ps`, no `du -sh`, no heavy imports
    (HPC_RUNBOOK gotcha 10/12).
  * One persistent SSH connection, ServerAlive disabled, NO retry loop
    (avoids BUG_POSTMORTEM_20261102 C5 MaxStartups self-lockout).
  * Read-only with respect to jobs: does not submit, does not cancel, does not
    delete files. ONLY sends signals to the user's own stuck probe processes.

Run detached:  python HPC_KILL_WINDOW.py
Stop:          taskkill /PID <pid> /T /F
Logs:          HPC_KILL_WINDOW.log / HPC_KILL_WINDOW_OUTPUT.txt / HPC_KILL_WINDOW_STATUS.json
"""
from __future__ import annotations
import datetime, json, os, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "HPC_KILL_WINDOW.log")
OUTTXT = os.path.join(HERE, "HPC_KILL_WINDOW_OUTPUT.txt")
STATUS = os.path.join(HERE, "HPC_KILL_WINDOW_STATUS.json")
CAPTURE = os.path.join(HERE, "REV9_CAPTURE_RECOVERED.md")
KEY = os.path.expanduser(r"~\.ssh\id_ed25519")
HOST = "sychan552@burgundy.hpc.cityu.edu.hk"


def log(msg):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# IMPORTANT: first command must be the kill, before ANY observation.
# Bracket trick prevents matching our own bash -c command line.
REMOTE = r"""timeout 4 pkill -9 -u "$USER" -f 'impo[r]t transformers' 2>/dev/null; echo PKILL_A=$?
timeout 4 pkill -9 -u "$USER" -f 'd[u] -sh' 2>/dev/null; echo PKILL_B=$?
timeout 4 pkill -9 -u "$USER" -f 'dl_ds3[2].py' 2>/dev/null; echo PKILL_C=$?
timeout 4 pkill -9 -u "$USER" -f 'export_miflu_7[c]h' 2>/dev/null; echo PKILL_D=$?
timeout 4 pkill -9 -u "$USER" -f 'export_miflu_all[7]' 2>/dev/null; echo PKILL_E=$?
echo KILL_COMMANDS_ISSUED
echo SHELL_OK; date -u
R=/gpfs1/scratch/sychan552/trackB_20261104
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
echo SQUEUE; timeout 8 squeue -u sychan552 -h -o "%i|%j|%T|%M" 2>/dev/null
echo CELLOK_CORE; timeout 20 $PY "$R/cellok.py" count "$R/core/export" "$R/core/cells.tsv" 2>&1 | head -1
echo CELLOK_ALL; timeout 20 $PY "$R/cellok.py" count "$R/all/export" "$R/all/cells_all.tsv" 2>&1 | head -1
echo NPZ7CH; timeout 8 find "$R/core/export7ch" -name '*.npz' 2>/dev/null | wc -l
echo JOB7CH; timeout 8 squeue -u sychan552 -n miflu_7ch_export -h 2>/dev/null; echo JOB7CH_END
echo QUOTA; timeout 8 mmlsquota -u sychan552 2>/dev/null | grep -e home -e scratch
echo CAPTURE_DONE
timeout 4 pkill -9 -u "$USER" -f 'impo[r]t transformers' 2>/dev/null; echo PKILL_ROUND2=$?"""

SSH = ["ssh", "-n", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-i", KEY,
       "-o", "PreferredAuthentications=publickey", "-o", "ConnectTimeout=10",
       "-o", "ServerAliveInterval=0", "-o", "ServerAliveCountMax=0",
       "-o", "TCPKeepAlive=yes", HOST, REMOTE]


def main():
    log("KILL_WINDOW_START single_connection=True deadline=NONE kill_first=True")
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
            log("OUT " + x[:220])
    threading.Thread(target=rd, daemon=True).start()

    hb = 0
    while p.poll() is None:
        time.sleep(1)
        if int(time.time() - started) // 30 > hb:
            hb = int(time.time() - started) // 30
            log(f"waiting elapsed={int(time.time()-started)}s lines={len(lines)}")
    p.wait()
    rc = p.returncode
    log(f"SSH_EXIT {rc} elapsed={int(time.time()-started)}s lines={len(lines)}")

    txt = "\n".join(lines)
    killed = "KILL_COMMANDS_ISSUED" in txt
    shell = any("SHELL_OK" in x for x in lines)
    with open(STATUS, "w", encoding="utf-8") as f:
        json.dump({"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "ssh_exit": rc, "shell_appeared": shell,
                   "kill_commands_issued": killed,
                   "pkill_rcs": [x for x in lines if x.startswith("PKILL_")],
                   "capture_done": "CAPTURE_DONE" in txt,
                   "lines": len(lines)}, f, indent=2)
    if shell and "CAPTURE_DONE" in txt:
        hdr = ("# REV9 live capture (after opportunistic stuck-probe kill)\n\n"
               f"- UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n"
               f"- SSH exit {rc}; kill commands issued: {killed}\n"
               "- No job submitted, no job cancelled, no file deleted.\n\n```\n")
        with open(CAPTURE, "w", encoding="utf-8", newline="\n") as f:
            f.write(hdr + txt + "\n```\n")
        log(f"CAPTURE_WRITTEN {CAPTURE}")
    log("KILL_WINDOW_END")
    return 0 if shell and killed else 1


if __name__ == "__main__":
    raise SystemExit(main())
