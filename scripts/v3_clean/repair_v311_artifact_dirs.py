"""repair_v311_artifact_dirs.py — D11: artifact-directory initialization missing.

EVIDENCE (Gate 569016, authoritative, from each path's own run_status.json):
  * 16/18 paths: `clean_runner.py` line 330, in main
        history.to_csv(os.path.join(run_dir, "logs", "train_history.csv"))
    OSError: Cannot save file into a non-existent directory: .../<run>/logs
  * 2/18 paths (baselines): `clean_runner.py` line 263, in main
        pred_df.to_csv(os.path.join(run_dir, "predictions", ...))
    OSError: Cannot save file into a non-existent directory: .../<run>/predictions

WHY ONLY SOME DIRECTORIES EXISTED: `_atomic_write_json` / `_write_text` create
the parent of the FILE they write (so `metrics/` and `checkpoints/` appeared),
but pandas `.to_csv` does NOT create directories.

Single root cause, two call sites. Classification:
  BEHAVIOR_NEUTRAL_ARTIFACT_DIRECTORY_INITIALIZATION_FIX

Nothing scientific is touched: no model, loss, optimizer, early stopping,
checkpoint choice, T, N, horizon, seed, split, scaler, prompt statistics,
metric, threshold, matrix row, ablation/control semantics or endpoint.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SC = ROOT / "results" / "v3_clean" / "preregistration"
RUNNER = ROOT / "scripts" / "innovation" / "clean_runner.py"
SC.mkdir(parents=True, exist_ok=True)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

VERSION_BEFORE = "innov-v3.10-backbone-kwarg-fix"
VERSION_AFTER = "innov-v3.11-artifact-directory-initialization"
CLASSIFICATION = "BEHAVIOR_NEUTRAL_ARTIFACT_DIRECTORY_INITIALIZATION_FIX"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha_b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


before_text = RUNNER.read_text(encoding="utf-8")

# ── patch 1: the single shared initializer ─────────────────────────────────
ANCHOR_1 = '''def load_registry(deployment_root: str) -> dict:'''
INSERT_1 = '''# v3.11 (D11): the COMPLETE per-run artifact tree. `_atomic_write_json` and
# `_write_text` create the parent of the file they write (which is why
# metrics/ and checkpoints/ existed in Gate 569016), but pandas `.to_csv` does
# NOT — so logs/train_history.csv and predictions/validation_predictions.csv
# died with "Cannot save file into a non-existent directory".
RUN_SUBDIRS = ("logs", "predictions", "metrics", "checkpoints")


def ensure_run_dirs(run_dir: str, out_root: str) -> str:
    """Idempotently create the full run artifact tree (called ONCE per run).

    Safety, all mandatory:
      * `run_dir` must be a DIRECT child of the authorised output root;
      * the RESOLVED real paths must stay directly under the real output root,
        so a symlinked run directory or an escaping `..` can never cause a
        write outside the authorised output root;
      * only the four declared sub-directories are created — never any other
        path, and never a parent outside the authorised output root.

    Behaviour-neutral: no scientific input, metric or checkpoint choice is
    touched. Returns the resolved run directory.
    """
    real_out = os.path.realpath(out_root)
    real_run = os.path.realpath(run_dir)
    if os.path.dirname(real_run) != real_out:
        raise SystemExit(
            "run directory escapes the authorised output root: "
            f"{run_dir} (resolved {real_run})")
    os.makedirs(real_run, exist_ok=True)
    for name in RUN_SUBDIRS:
        d = os.path.join(real_run, name)
        if os.path.islink(d):
            raise SystemExit(f"refusing symlinked artifact directory: {d}")
        os.makedirs(d, exist_ok=True)
    return real_run


def load_registry(deployment_root: str) -> dict:'''

# ── patch 2: call it exactly once, after create-only resolution ────────────
ANCHOR_2 = '''    if os.path.exists(run_dir) and os.listdir(run_dir):
        raise SystemExit(f"run directory already exists and is non-empty: {run_dir}")
    os.makedirs(run_dir, exist_ok=True)'''
INSERT_2 = '''    if os.path.exists(run_dir) and os.listdir(run_dir):
        raise SystemExit(f"run directory already exists and is non-empty: {run_dir}")
    # D11: create the COMPLETE artifact tree ONCE, after the create-only and
    # path-containment checks, and before ANY artifact write.
    run_dir = ensure_run_dirs(run_dir, out_root)'''

patches = [("scripts/innovation/clean_runner.py", ANCHOR_1, INSERT_1),
           ("scripts/innovation/clean_runner.py", ANCHOR_2, INSERT_2)]

# ── pre-repair evidence (recorded BEFORE any edit) ─────────────────────────
pre_path = SC / "d11_pre_repair_manifest.json"
if not pre_path.exists():
    pre_path.write_text(json.dumps({
        "generated_utc": NOW, "defect": "D11",
        "classification": CLASSIFICATION,
        "runtime_version_before": VERSION_BEFORE,
        "runtime_version_after": VERSION_AFTER,
        "failing_gate": {"job_id": "569016", "state": "FAILED",
                         "exit_code": "1:0", "elapsed": "00:24:33",
                         "node": "gpu-a100-06", "passed": "1/19",
                         "n_failing_paths": 18},
        "failure_signature": {
            "exception": "OSError",
            "message": "Cannot save file into a non-existent directory",
            "single_root_cause": True,
            "call_sites": [
                {"line": 330, "fn": "main", "file": "logs/train_history.csv",
                 "paths": 16, "arms": ["primary", "ablation",
                                       "negative_control"]},
                {"line": 263, "fn": "main",
                 "file": "predictions/validation_predictions.csv",
                 "paths": 2, "arms": ["baseline"]}],
            "missing_directories": ["logs", "predictions"],
            "directories_that_existed": ["metrics", "checkpoints"],
            "why": "_atomic_write_json/_write_text create the parent of the "
                   "file they write; pandas .to_csv does not.",
            "stage": "after training completed and checkpoint saved (stochastic) "
                     "/ after metrics written (baseline)",
            "scientific_inputs_affected": False},
        "pre_repair_sha256": {
            "scripts/innovation/clean_runner.py": sha(RUNNER)},
        "scientific_protocol_changed": False,
        "formal_rows_submitted": "0/598", "test_access": 0, "holdout_access": 0,
        "note": "Recorded BEFORE any edit, per prompt section 3.",
    }, indent=2), encoding="utf-8")

after_text = before_text
results = []
for rel, anchor, insert in patches:
    if anchor in after_text:
        after_text = after_text.replace(anchor, insert, 1)
        results.append(f"{rel}: applied")
    elif insert in after_text:
        results.append(f"{rel}: already applied")
    else:
        raise SystemExit(f"D11 anchor not found in {rel}")

applied = any("applied" == r.split(": ")[1] for r in results)
if applied:
    with open(RUNNER, "w", encoding="utf-8", newline="") as f:
        f.write(after_text)

diff = "".join(difflib.unified_diff(
    before_text.splitlines(keepends=True), after_text.splitlines(keepends=True),
    fromfile="a/scripts/innovation/clean_runner.py",
    tofile="b/scripts/innovation/clean_runner.py"))
dp = SC / "d11_repair.diff"
if diff.strip():
    dp.write_text(diff, encoding="utf-8")
elif dp.exists():
    diff = dp.read_text(encoding="utf-8")

# ── classify EVERY changed line; any scientific line means immediate stop ──
added = [l[1:] for l in diff.splitlines()
         if l.startswith("+") and not l.startswith("+++")]
removed = [l[1:] for l in diff.splitlines()
           if l.startswith("-") and not l.startswith("---")]
SCI_PATTERNS = ("loss", "optimizer", "lr=", "learning_rate", "patience",
                "horizon", "seed", "T_WINDOW", "N_VARIABLES", "scaler",
                "prompt_stat", "threshold", "peak", "early_stop", "scheduler")
sci_hits = [l for l in added + removed
            if any(p in l.lower() for p in SCI_PATTERNS)]
if sci_hits:
    raise SystemExit(f"SCIENTIFIC LINE CHANGED — STOP: {sci_hits}")

pre = json.loads(pre_path.read_text(encoding="utf-8"))
rec = {
    "generated_utc": NOW, "defect": "D11", "applied_now": applied,
    "classification": CLASSIFICATION,
    "file": "scripts/innovation/clean_runner.py",
    "pre_repair_sha256": pre["pre_repair_sha256"][
        "scripts/innovation/clean_runner.py"],
    "post_repair_sha256": sha(RUNNER),
    "diff_bytes": len(diff.encode("utf-8")),
    "diff_sha256": sha_b(diff.encode("utf-8")),
    "lines_added": len(added), "lines_removed": len(removed),
    "changed_line_classification": "ALL lines are artifact-directory "
                                   "initialization or its safety guards; "
                                   "0 scientific lines",
    "scientific_lines_changed": 0,
    "patch_results": results,
    "shared_initializer": "ensure_run_dirs(run_dir, out_root)",
    "called_once_per_run": True,
    "idempotent": True,
    "run_subdirs": ["logs", "predictions", "metrics", "checkpoints"],
    "safety": {"direct_child_only": True, "symlink_escape_rejected": True,
               "path_traversal_rejected": True,
               "no_path_outside_out_root": True},
    "formal_rows_submitted": "0/598",
}
(SC / "d11_repair_record.json").write_text(json.dumps(rec, indent=2),
                                           encoding="utf-8")
with open(SC / "d11_repair_ledger.jsonl", "a", encoding="utf-8",
          newline="") as f:
    f.write(json.dumps({"utc": NOW, "event": "d11_repair_applied",
                        "applied": applied,
                        "pre": rec["pre_repair_sha256"],
                        "post": rec["post_repair_sha256"],
                        "diff_bytes": rec["diff_bytes"]}) + "\n")

print(f"[d11] applied={applied} pre={rec['pre_repair_sha256'][:16]} "
      f"post={rec['post_repair_sha256'][:16]} diff_bytes={rec['diff_bytes']} "
      f"added={len(added)} removed={len(removed)} sci_lines=0")
