"""
slurm_check.py — structural + optional shell-syntax validation of Slurm scripts.
===============================================================================

Pre-HPC clarification 6 & 7
---------------------------
Validates EVERY generated `hpc_scripts/innovation_*.sh` / `hpc_scripts/pilot_*.sh`:

  * shell syntax: `bash -n` when a bash binary is found (Git Bash / WSL / PATH),
    otherwise a structured Python check only (reported honestly);
  * structural contract:
      - one small resumable unit per job (`--skip-if-done`, `--max-seconds`);
      - exactly ONE `runner.py` invocation per worker/pilot script;
      - workers/pilots contain NO `sbatch` (only submit drivers may submit);
      - submit drivers ALL carry the `CONFIRM_INNOVATION_SUBMIT` guard;
      - no bare `--gres=gpu:1`; `--mem` and `--time<=04:00:00` present.

It NEVER invokes `sbatch`; the report records `submission_attempted=false` and
`sbatch_invoked=false`.
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import os
import re
import shutil
import subprocess

from innovation import run_artifacts as ART
from innovation.paths import AUDIT_DIR, PROJECT_ROOT

HPC_DIR = os.path.join(PROJECT_ROOT, "hpc_scripts")
GLOB_PATTERNS = ("innovation_*.sh", "pilot_*.sh", "submit_innovation_*.sh")
SUBMIT_NAMES = ("submit_innovation_smoke.sh", "submit_innovation_pilot.sh",
                "submit_innovation_screening.sh", "submit_innovation_full.sh")
WORKER_NAMES = ("innovation_worker.sh",)
GUARD_TOKEN = "CONFIRM_INNOVATION_SUBMIT"


def find_bash():
    """Return a usable bash path, or None (never installs anything)."""
    p = shutil.which("bash")
    if p:
        return p
    for cand in (r"C:\Program Files\Git\bin\bash.exe",
                 r"C:\Program Files\Git\usr\bin\bash.exe",
                 r"C:\Program Files (x86)\Git\bin\bash.exe",
                 "/bin/bash", "/usr/bin/bash"):
        if os.path.exists(cand):
            return cand
    return None


def _bash_syntax(bash: str, path: str) -> dict:
    try:
        r = subprocess.run([bash, "-n", path], capture_output=True, text=True,
                           timeout=30)
        return {"checked": True, "returncode": r.returncode,
                "ok": r.returncode == 0, "stderr": r.stderr.strip()[:400]}
    except Exception as e:
        return {"checked": True, "ok": False, "error": str(e)}


def check_script(path: str, bash: str | None) -> dict:
    name = os.path.basename(path)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    is_submit = name in SUBMIT_NAMES
    is_worker = name in WORKER_NAMES or name.startswith("pilot_")

    issues = []

    def need(cond, msg):
        if not cond:
            issues.append(msg)

    need(text.startswith("#!/bin/bash"), "missing '#!/bin/bash' shebang")
    need("#SBATCH --partition=stingy" in text, "missing --partition=stingy")
    need("--gres=gpu:a100:1" in text, "missing --gres=gpu:a100:1")
    need(re.search(r"#SBATCH --mem=\d+G", text) is not None,
         "missing/invalid explicit #SBATCH --mem=NN G")
    need(re.search(r"(?m)^\s*#SBATCH\s+--gres=gpu:1\s*$", text) is None,
         "[BUG] bare '#SBATCH --gres=gpu:1' present "
         "(may land on a V100 -> OOM)")
    m_time = re.search(r"#SBATCH --time=(\d{2}):(\d{2}):(\d{2})", text)
    if not m_time:
        issues.append("missing #SBATCH --time=HH:MM:SS")
    else:
        hh = int(m_time.group(1))
        if hh > 4 or (hh == 4 and (int(m_time.group(2)) or int(m_time.group(3)))):
            issues.append(f"#SBATCH --time exceeds the 4h stingy cap: {m_time.group(0)}")
    # `set -euo pipefail` (and any other short-option bundle containing `u`)
    # satisfies the "no unset variable" requirement; match it semantically.
    need(re.search(r"^\s*set\s+-[euxo]*u[euxo]*(\s+pipefail)?\s*$", text,
                   re.M) is not None, "missing 'set -u' (or an equivalent "
                                      "`set -euo pipefail`)")

    starts = len(re.findall(r"python\s+scripts/innovation/runner\.py", text))
    if is_worker:
        need(starts == 1, f"worker/pilot must invoke runner.py exactly once "
                          f"(found {starts})")
        need("--skip-if-done" in text, "worker/pilot missing --skip-if-done (resume)")
        need("--max-seconds" in text, "worker/pilot missing --max-seconds (timeout)")
    if re.search(r"(?m)^\s*sbatch\s", text) and not is_submit:
        issues.append("non-submit script contains an sbatch INVOCATION "
                      "(must not submit)")
    if is_submit:
        need(GUARD_TOKEN in text, "submit script missing the confirmation guard")
        need("submission_attempted=false" in text,
             "submit script must report submission_attempted=false when refused")

    if is_worker:
        need("--experiment-stage" in text, "worker/pilot missing --experiment-stage")

    syntax = _bash_syntax(bash, path) if bash else \
        {"checked": False, "ok": True, "reason": "no bash binary available"}
    return {"script": name, "is_submit_driver": is_submit, "is_worker": is_worker,
            "runner_invocations": starts, "structural_ok": not issues,
            "issues": issues, "bash_syntax": syntax,
            "ok": (not issues) and syntax.get("ok", True)}


def main(argv=None) -> int:
    files = []
    for pat in GLOB_PATTERNS:
        files += glob.glob(os.path.join(HPC_DIR, pat))
    files = sorted(set(files))
    bash = find_bash()
    results = [check_script(f, bash) for f in files]
    all_ok = all(r["ok"] for r in results)
    report = {
        "created_utc": ART.utc_now(),
        "bash_found": bash,
        "shell_syntax_checked": bool(bash),
        "n_scripts": len(results),
        "all_ok": bool(all_ok),
        "submission_attempted": False,
        "sbatch_invoked": False,
        "results": results,
    }
    ART.write_json(os.path.join(AUDIT_DIR, "slurm_validation_report.json"), report)
    print(f"[slurm_check] {len(results)} scripts | bash={bash} | "
          f"all_ok={all_ok} | submission_attempted=False")
    for r in results:
        flag = "OK " if r["ok"] else "FAIL"
        print(f"   [{flag}] {r['script']} (runner_calls={r['runner_invocations']})")
        for i in r["issues"]:
            print(f"          - {i}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
