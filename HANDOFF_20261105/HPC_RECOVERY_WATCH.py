#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Burgundy login-node recovery watcher — read-only capture, NO auto-submit.

Implements 04_详细说明文档/OUTAGE_RECOVERY.md and BUG_POSTMORTEM_20261102 C5:
  * measure TCP/22 before diagnosing (never infer "cluster down" from an ssh error)
  * at most ONE ssh attempt per 75 s (MaxStartups / self-inflicted `Connection closed`)
  * every ssh attempt has a hard deadline; output streamed so partial logs survive
  * the instant a shell works: inspect/pkill stuck probes BEFORE doing science
  * then run the full rev9 fresh capture and write it locally
  * NEVER submits a job and NEVER cancels a job. The operator decides from the capture.

Usage:
    python HPC_RECOVERY_WATCH.py            # 20 attempts, ~25 min
    python HPC_RECOVERY_WATCH.py --once     # one attempt, then exit
"""
from __future__ import annotations
import argparse, datetime, json, os, socket, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "HPC_RECOVERY_WATCH.log")
CAPTURE = os.path.join(HERE, "REV9_CAPTURE_RECOVERED.md")
STATUS = os.path.join(HERE, "HPC_RECOVERY_STATUS.json")
HOST = "sychan552@burgundy.hpc.cityu.edu.hk"
IP = "144.214.138.99"
KEY = os.path.expanduser(r"~\.ssh\id_ed25519")
COOLDOWN = 75
ATTEMPT_DEADLINE = 30

SSH_BASE = ["ssh", "-n", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-i", KEY,
            "-o", "PreferredAuthentications=publickey", "-o", "ConnectTimeout=8",
            "-o", "ServerAliveInterval=8", "-o", "ServerAliveCountMax=2"]


def log(msg: str) -> None:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def tcp_ok() -> tuple[bool, str]:
    s = socket.socket(); s.settimeout(6); t = time.time()
    try:
        s.connect((IP, 22)); b = s.recv(80).decode(errors="replace").strip()
        return True, f"{time.time()-t:.2f}s banner={b}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        s.close()


def ssh_run(cmd: str, deadline: int = ATTEMPT_DEADLINE) -> tuple[int, list[str]]:
    p = subprocess.Popen(SSH_BASE + [HOST, cmd], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, bufsize=0)
    lines: list[str] = []
    def rd():
        for raw in iter(p.stdout.readline, b""):
            lines.append(raw.decode("utf-8", errors="replace").rstrip())
    threading.Thread(target=rd, daemon=True).start()
    end = time.time() + deadline
    while p.poll() is None and time.time() < end:
        time.sleep(0.4)
    if p.poll() is None:
        p.kill()
    try: p.wait(timeout=5)
    except Exception: pass
    return p.returncode, lines


# Executed only after a shell is proven to work. Kill the documented culprits first.
CLEANUP = r"""ps -u "$USER" -o pid,stat,etime,cmd | head -30;
pkill -f 'import transformers' 2>/dev/null; pkill -f 'du -sh' 2>/dev/null;
pkill -f export_miflu 2>/dev/null; echo CLEANUP_DONE"""

CAPTURE_CMD = r"""R=/gpfs1/scratch/sychan552/trackB_20261104
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
echo "=== UTC / HKT ==="; date -u; TZ=Asia/Hong_Kong date
echo "=== SQUEUE ==="; squeue -u sychan552 -o '%.10i %.26j %.10T %.12M %.22R' 2>/dev/null
echo "=== 7CH JOB? ==="; squeue -u sychan552 -n miflu_7ch_export -h 2>/dev/null || true
sacct -u sychan552 --starttime=2026-11-05T00:00 -X -o JobID,JobName,State,Elapsed 2>/dev/null | grep -iE '7ch|export' || echo NO_7CH_JOB
echo "=== CELLOK ==="
$PY "$R/cellok.py" count "$R/core/export" "$R/core/cells.tsv" 2>&1 | head -2
$PY "$R/cellok.py" count "$R/all/export" "$R/all/cells_all.tsv" 2>&1 | head -2
echo "=== 7CH OUTPUTS ==="; ls -la "$R/core/export7ch" 2>/dev/null | head -12 || echo NO_DIR
echo -n "npz_count "; find "$R/core/export7ch" -name '*.npz' 2>/dev/null | wc -l
echo "=== 7CH SCRIPTS ==="; ls -la "$R"/*7ch* "$R"/code/*7ch* 2>/dev/null || echo NO_SCRIPTS
echo "=== SENTINELS ==="; ls -la "$R/core/phase.done" "$R/all/phase.done" "$R/all/post_all.started" 2>/dev/null || echo NONE
echo "=== CONTROLLER ==="; tail -8 "$R/all/logs/controller_v2.log" 2>/dev/null
echo "=== LEGACY ==="; wc -l "$R/all/legacy_done.tsv" 2>/dev/null || true
echo "=== QUOTA ==="; mmlsquota -u sychan552 2>/dev/null | grep -e home -e scratch
echo "=== PS (post-cleanup) ==="; ps -u "$USER" -o pid,stat,etime,cmd | head -20
echo CAPTURE_DONE"""


def write_status(**kw) -> None:
    data = {"updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), **kw}
    with open(STATUS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--attempts", type=int, default=20)
    a = ap.parse_args()
    total = 1 if a.once else a.attempts

    log(f"WATCHER_START attempts={total} cooldown={COOLDOWN}s auto_submit=DISABLED")
    for i in range(total):
        ok, detail = tcp_ok()
        log(f"attempt {i+1}/{total} TCP22={ok} {detail}")
        if not ok:
            write_status(attempt=i+1, tcp22=False, ssh=False,
                         diagnosis="port 22 closed: node isolated/down; no remote remedy")
        else:
            rc, lines = ssh_run("echo SHELL_OK")
            good = rc == 0 and any("SHELL_OK" in x for x in lines)
            log(f"attempt {i+1}/{total} ssh_rc={rc} shell_ok={good} "
                f"last={'; '.join(lines[-2:])[:200]}")
            if good:
                log("SHELL RECOVERED — running documented cleanup FIRST")
                rc1, o1 = ssh_run(CLEANUP, deadline=40)
                log(f"cleanup_rc={rc1} tail={'; '.join(o1[-3:])[:300]}")
                log("running fresh rev9 capture")
                rc2, o2 = ssh_run(CAPTURE_CMD, deadline=90)
                text = "\n".join(o2)
                hdr = ("# REV9 live capture after login-node recovery\n\n"
                       f"- Capture UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n"
                       f"- SSH shell recovered: YES (attempt {i+1})\n"
                       f"- Cleanup exit: {rc1}; capture exit: {rc2}\n"
                       "- No job was submitted or cancelled by this watcher.\n\n```\n")
                with open(CAPTURE, "w", encoding="utf-8", newline="\n") as f:
                    f.write(hdr + text + "\n```\n")
                write_status(attempt=i+1, tcp22=True, ssh=True, shell_recovered=True,
                             cleanup_exit=rc1, capture_exit=rc2,
                             capture_file=CAPTURE, diagnosis="recovered")
                log(f"CAPTURE_WRITTEN {CAPTURE}")
                return 0
            write_status(attempt=i+1, tcp22=True, ssh=True, shell_recovered=False,
                         diagnosis="gotcha 11: auth OK, exec/sftp zero bytes; "
                                   "login shell cannot spawn; retry cannot fix; "
                                   "needs D-state process to clear or sysadmin")
        if i < total - 1:
            log(f"cooling down {COOLDOWN}s (MaxStartups / C5 rule)")
            time.sleep(COOLDOWN)
    log("WATCHER_END no shell recovered")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
