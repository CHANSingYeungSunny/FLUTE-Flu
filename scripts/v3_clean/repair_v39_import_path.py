"""repair_v39_import_path.py — v3.9 repair of the Gate-568972 root cause.

EVIDENCE (not a guess): every one of the 18 failing paths in Gate 568972 shows
the SAME traceback, at IMPORT time, before any data or model work:

    File ".../scripts/innovation/clean_runner.py", line 41, in <module>
        from innovation import clean_metrics as CM
    ModuleNotFoundError: No module named 'innovation'

CAUSE: `clean_runner.py` derives `_ROOT` as the DEPLOYMENT ROOT and inserts it
on `sys.path`, but the `innovation` package lives in `<root>/scripts/innovation`.
The package parent `<root>/scripts` was never added, so the import fails.

This is squarely inside the authorised repair scope "runtime path resolution".
Nothing about the model, loss, optimizer, early stopping, horizons, seeds,
metrics, the 598-row matrix, ablation/control semantics or the endpoint
hierarchy is touched.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SC = ROOT / "results" / "v3_clean" / "preregistration"
RUNNER = ROOT / "scripts" / "innovation" / "clean_runner.py"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
SC.mkdir(parents=True, exist_ok=True)

VERSION_BEFORE = "innov-v3.8-complete-deployment-closure"
VERSION_AFTER = "innov-v3.9-runner-import-path-fix"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ── 1. record the pre-repair state BEFORE any edit ──────────────────────────
before_text = RUNNER.read_text(encoding="utf-8")
pre = {"generated_utc": NOW, "defect": "D8",
       "classification": "BEHAVIOR_NEUTRAL_RUNTIME_PATH_RESOLUTION_FIX",
       "runtime_version_before": VERSION_BEFORE,
       "runtime_version_after": VERSION_AFTER,
       "failing_gate": {"job_id": "568972", "state": "FAILED",
                        "exit_code": "1:0", "passed": "1/19",
                        "only_passing_check": "deferred_guard",
                        "n_failing_paths": 18},
       "failure_signature": {
           "exception": "ModuleNotFoundError",
           "message": "No module named 'innovation'",
           "failing_file": "scripts/innovation/clean_runner.py",
           "failing_line": 41,
           "stage": "import (before any data or model work)",
           "shared_by_all_18_paths": True},
       "pre_repair_sha256": {str(RUNNER.relative_to(ROOT)): sha(RUNNER)},
       "pre_repair_bytes": len(before_text.encode("utf-8")),
       "note": "Recorded BEFORE any edit, per prompt section 10."}
pre_path = SC / "d8_pre_repair_manifest.json"
if pre_path.exists():
    # NEVER overwrite recorded pre-repair evidence: on a re-run the file on disk
    # still holds the FIRST-read hash, which is the authoritative pre state.
    pre = json.loads(pre_path.read_text(encoding="utf-8"))
else:
    pre["pre_repair_sha256"] = {
        str(RUNNER.relative_to(ROOT)).replace("\\", "/"): sha(RUNNER)}
    pre_path.write_text(json.dumps(pre, indent=2), encoding="utf-8")

# ── 2. minimal fix: put the package parent (<root>/scripts) on sys.path ────
OLD = """_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)"""
NEW = """_HERE = os.path.dirname(os.path.abspath(__file__))     # <root>/scripts/innovation
# The importable package parent is <root>/scripts, NOT the deployment root.
# Inserting the root alone made every run die with
# "ModuleNotFoundError: No module named 'innovation'" (Gate 568972).
_SCRIPTS_ROOT = os.path.dirname(_HERE)                    # <root>/scripts
_ROOT = os.path.dirname(_SCRIPTS_ROOT)                    # <root>
for _p in (_SCRIPTS_ROOT, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)"""

after_text = before_text
if OLD in after_text:
    after_text = after_text.replace(OLD, NEW)
    applied = True
elif NEW in after_text:
    applied = False                      # idempotent re-run
else:
    raise SystemExit("clean_runner.py anchor not found; refusing to patch")

if applied:
    with open(RUNNER, "w", encoding="utf-8", newline="") as f:
        f.write(after_text)

diff = "".join(difflib.unified_diff(
    before_text.splitlines(keepends=True), after_text.splitlines(keepends=True),
    fromfile="a/scripts/innovation/clean_runner.py",
    tofile="b/scripts/innovation/clean_runner.py"))
diff_path = SC / "d8_repair.diff"
if diff.strip():
    diff_path.write_text(diff, encoding="utf-8")
elif diff_path.exists():
    # Re-run after the patch is already in place produces an EMPTY diff; keep
    # the originally recorded evidence instead of clobbering it.
    diff = diff_path.read_text(encoding="utf-8")

record = {
    "generated_utc": NOW, "defect": "D8",
    "applied_now": applied,
    "classification": "BEHAVIOR_NEUTRAL_RUNTIME_PATH_RESOLUTION_FIX",
    "file": str(RUNNER.relative_to(ROOT)).replace("\\", "/"),
    # tolerant of either separator in the recorded manifest
    "pre_repair_sha256": pre["pre_repair_sha256"][
        next(k for k in pre["pre_repair_sha256"]
             if k.endswith("clean_runner.py"))],
    "post_repair_sha256": sha(RUNNER),
    "diff_bytes": len(diff.encode("utf-8")),
    "diff_sha256": sha_bytes(diff.encode("utf-8")),
    "repair_scope": "runtime path resolution (authorised, item 8)",
    "untouched": ["model architecture", "loss", "optimizer",
                  "early stopping", "horizons", "seeds", "metrics",
                  "598-row matrix", "ablation/control semantics",
                  "endpoint hierarchy"],
    "scientific_parameters_changed": 0,
}
(SC / "d8_repair_record.json").write_text(
    json.dumps(record, indent=2), encoding="utf-8")

with open(SC / "d8_repair_ledger.jsonl", "a", encoding="utf-8",
          newline="") as f:
    f.write(json.dumps({"utc": NOW, "event": "repair_applied",
                        "applied": applied,
                        "pre": record["pre_repair_sha256"],
                        "post": record["post_repair_sha256"]}) + "\n")

print(f"[d8] applied={applied}")
print(f"[d8] pre  sha={record['pre_repair_sha256'][:16]}")
print(f"[d8] post sha={record['post_repair_sha256'][:16]}")
print(f"[d8] diff bytes={record['diff_bytes']} sha={record['diff_sha256'][:16]}")
