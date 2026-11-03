"""
hpc_specs.py — GENERATE (never submit) resumable, guard-protected Slurm scripts.
=============================================================================

Pre-HPC clarifications 6 & 8
----------------------------
  * EVERY submit script carries an explicit confirmation guard: it refuses to
    submit unless `CONFIRM_INNOVATION_SUBMIT=YES` is exported, and otherwise
    prints `submission_attempted=false` and exits 0. This makes accidental
    submission — including a full sweep during the verification phase —
    impossible.
  * The four PILOT jobs are generated as INDEPENDENT per-spec scripts and are
    NOT submitted. Pilot results are infrastructure evidence only.

Design: one run per job, `--skip-if-done` (resume) and `--max-seconds`
(timeout); the auto-submit chains respect stingy's 1-slot QOS cap.
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import json
import os

from innovation.paths import BANNED_RUNTIME_ROOT, INNOVATION_ROOT, PROJECT_ROOT

HPC_DIR = os.path.join(PROJECT_ROOT, "hpc_scripts")

# The eight pilot specs (infrastructure verification only; NOT a ranking).
PILOT_SPECS = [
  {"model": "nlinear", "text_encoder": "none", "fusion": "identity",
   "horizon": 24, "seed": 42},
    {"model": "gpt2_miflu", "text_encoder": "gpt2", "fusion": "concat_projection",
     "horizon": 24, "seed": 42},
    {"model": "dlinear", "text_encoder": "none", "fusion": "identity",
     "horizon": 24, "seed": 42},
    {"model": "patchtst", "text_encoder": "none", "fusion": "identity",
     "horizon": 24, "seed": 42},
    {"model": "itransformer", "text_encoder": "none", "fusion": "identity",
     "horizon": 24, "seed": 42},
    {"model": "qwen_time_llm", "text_encoder": "none", "fusion": "identity",
     "horizon": 24, "seed": 42,
     "backbone_kwargs": {"model_id": "Qwen/Qwen2.5-1.5B", "load_backbone": True}},
    {"model": "calf_llm", "text_encoder": "none", "fusion": "identity",
     "horizon": 24, "seed": 42,
     "backbone_kwargs": {"model_id": "gpt2", "load_backbone": True}},
    {"model": "timecma_llm", "text_encoder": "none", "fusion": "identity",
     "horizon": 24, "seed": 42,
     "backbone_kwargs": {"model_id": "gpt2", "load_backbone": True}},
]

_HEADER = """#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=hpc_results/innovation/logs/slurm_%j_%x.out
#SBATCH --error=hpc_results/innovation/logs/slurm_%j_%x.err
#SBATCH --signal=B:USR1@120

# NOTE: --mem must be explicit (the default is reset to ~1024MB and loading
# GPT-2 would OOM). Never request a generic single GPU on stingy (it may land
# on a V100 and OOM); always pin the a100 flavour exactly as below.
# --time is capped at 4h; jobs are intentionally small, one-run-per-job and
# resumable, so 4h is NOT assumed sufficient for a whole sweep.

set -euo pipefail
module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME

# ── DEPLOYMENT ROOT: EXPLICIT, never a silent fallback ──────────────────────
# The innovation experiment may only run from an ISOLATED deployment root. The
# original reproduction repository is forbidden as an execution path
# (incident 2026-09-15). A missing variable must FAIL CLOSED, never fall back to
# the submitter's current directory.
: "${{INNOVATION_DEPLOYMENT_ROOT:?INNOVATION_DEPLOYMENT_ROOT must be set to the isolated deployment root}}"
DEPLOYMENT_ROOT="$(cd "$INNOVATION_DEPLOYMENT_ROOT" && pwd -P)"

# The forbidden root is resolved WITHOUT cd-ing into it (readlink only), so this
# line can never execute anything inside the original repository.
FORBIDDEN_ROOT_RAW="{banned}"
FORBIDDEN_ROOT="$(readlink -f "$FORBIDDEN_ROOT_RAW" 2>/dev/null || true)"
if [ -n "$FORBIDDEN_ROOT" ]; then
  if [ "$DEPLOYMENT_ROOT" = "$FORBIDDEN_ROOT" ] || [ "${{DEPLOYMENT_ROOT#"$FORBIDDEN_ROOT/"}}" != "$DEPLOYMENT_ROOT" ]; then
    echo "FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT" >&2
    exit 2
  fi
fi

cd "$DEPLOYMENT_ROOT"
echo "[deployment_root] $DEPLOYMENT_ROOT"
mkdir -p hpc_results/innovation/logs

# Preemption notice: record it; the python process still writes run_status.json.
trap 'echo "[preempt] SIGUSR1 at $(date)"; export INNOVATION_PREEMPTED=1' USR1
""".format(banned=BANNED_RUNTIME_ROOT)

# Explicit confirmation guard placed in EVERY submit script.
_GUARD = """
# ── CONFIRMATION GUARD (pre-HPC clarification 6) ────────────────────────────
# Nothing is submitted unless the operator explicitly opts in. During the
# verification phase this ALWAYS reports submission_attempted=false.
: "${CONFIRM_INNOVATION_SUBMIT:=NO}"
if [ "$CONFIRM_INNOVATION_SUBMIT" != "YES" ]; then
  echo "[guard] REFUSED to submit: export CONFIRM_INNOVATION_SUBMIT=YES to proceed."
  echo "[guard] submission_attempted=false"
  exit 0
fi
echo "[guard] submission_attempted=true"
"""

# Startup governance assertion shared by the pilot scripts and the worker:
# compares the DEPLOYED manifest aggregate with the hash recorded in
# pilot_specs.json and asserts stage / purpose / eligibility / test access.
_STARTUP_PY = """
python - <<'PY'
import json, os, sys
want = __MODEL_EXPR__
stage = __STAGE_EXPR__
man = json.load(open("results/innovation/source_snapshot_manifest.json", encoding="utf-8"))
agg = man["aggregate_sha256"]
bad = []
if stage == "pilot":
    specs = json.load(open("hpc_scripts/pilot_specs.json", encoding="utf-8"))
    rec = next((s for s in specs.get("specs", []) if s.get("model") == want), None)
    if rec is None:
        print("[abort] no pilot spec for " + want); sys.exit(1)
    if rec.get("source_snapshot_sha256") != agg:
        bad.append("source_snapshot_sha256 mismatch spec=%s manifest=%s" % (rec.get("source_snapshot_sha256"), agg))
    for k in ("test_access_allowed", "selection_eligible", "paper_result_eligible"):
        if rec.get(k) is not False:
            bad.append("%s is not false" % k)
    if rec.get("experiment_stage") != "pilot" or rec.get("purpose") != "infrastructure_verification_only":
        bad.append("experiment_stage/purpose mismatch")
print("[startup] stage=" + str(stage))
print("[startup] expected_aggregate_sha256=" + agg)
if bad:
    for b in bad:
        print("[abort] " + b)
    sys.exit(1)
print("[startup] governance check OK")
PY
RC=$?
if [ "$RC" -ne 0 ]; then
  echo "[abort] startup governance check FAILED"
  exit 1
fi
"""

_WORKER = _HEADER + _GUARD + """
# Usage: innovation_worker.sh MODEL ENCODER FUSION HORIZON SEED [EPOCHS] [STAGE]
# One invocation == exactly one (model x horizon x seed). The worker itself never
# queues a job, never selects a model, never touches test, and never relaxes the
# pilot's selection_eligible / paper_result_eligible flags.
MODEL=${1:?model}; ENC=${2:?text_encoder}; FUSION=${3:?fusion}
L=${4:?horizon}; SEED=${5:?seed}; EPOCHS=${6:-20}; STAGE=${7:-screening}
export PILOT_MODEL="$MODEL"
export WORKER_STAGE="$STAGE"

echo "[worker] start $(date) | $MODEL / $ENC / $FUSION | L=$L seed=$SEED stage=$STAGE"

# 1. runtime path guard (explicit deployment root)
python scripts/innovation/runtime_guard.py \\
    --deployment-root "$DEPLOYMENT_ROOT" || {
  echo "[abort] FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT"
  exit 1
}

# 2. explicit-root source verification
python scripts/innovation/verify_source_snapshot.py \\
    --deployment-root "$DEPLOYMENT_ROOT" \\
    --manifest results/innovation/source_snapshot_manifest.json || {
  echo "[abort] source snapshot verification FAILED — refusing to run"
  exit 1
}

# 3. v2.4 hash + governance assertion (runs after PILOT_MODEL is exported)
""" + _STARTUP_PY.replace(
    "__MODEL_EXPR__", 'os.environ.get("PILOT_MODEL") or ""').replace(
    "__STAGE_EXPR__", 'os.environ.get("WORKER_STAGE", "pilot")') + """
python scripts/innovation/runner.py \\
    --model "$MODEL" --text-encoder "$ENC" --fusion "$FUSION" \\
    --horizon "$L" --seed "$SEED" --epochs "$EPOCHS" \\
    --experiment-stage "$STAGE" \\
    --max-seconds 12600 --skip-if-done || {
  RC=$?
  echo "[worker] FAILED rc=$RC at $(date)"
  exit $RC
}
echo "[worker] python rc=0 at $(date)"
"""


def _pilot_script(name: str, spec: dict) -> str:
    """One INDEPENDENT sbatch script for a single pilot spec (guarded)."""
    startup = _STARTUP_PY.replace(
        "__MODEL_EXPR__", '"%s"' % spec["model"]).replace(
        "__STAGE_EXPR__", '"pilot"')
    backbone_args = ""
    if spec.get("backbone_kwargs"):
      backbone_args = (f" --model-id '{spec['backbone_kwargs']['model_id']}'"
               " --load-backbone")
    return _HEADER + _GUARD + f"""
# Pilot job (INFRASTRUCTURE VERIFICATION ONLY — never a ranking).
echo "[pilot] start $(date) | {name}"

# ── 1. RUNTIME PATH GUARD (original reproduction repo is OUT of exec path) ──
python scripts/innovation/runtime_guard.py \\
    --deployment-root "$DEPLOYMENT_ROOT" || {{
  echo "[abort] FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT"
  exit 1
}}

# ── 2. SOURCE FREEZE STARTUP CHECK (explicit root; abort on drift) ──────────
python scripts/innovation/verify_source_snapshot.py \\
    --deployment-root "$DEPLOYMENT_ROOT" \\
    --manifest results/innovation/source_snapshot_manifest.json || {{
  echo "[abort] source snapshot verification FAILED — refusing to run"
  exit 1
}}

# ── 3. v2.4 hash + test-access / eligibility assertion ─────────────────────
{startup}
python scripts/innovation/runner.py \\
    --model "{spec['model']}" --text-encoder "{spec['text_encoder']}" \\
    --fusion "{spec['fusion']}" --horizon {spec['horizon']} \\
    --seed {spec['seed']} --epochs 20 --experiment-stage pilot{backbone_args} \\
    --max-seconds 12600 --skip-if-done || {{
  RC=$?
  echo "[pilot] FAILED rc=$RC at $(date)"
  exit $RC
}}
echo "[pilot] python rc=0 at $(date)"
"""


def _chain(name: str, note: str, specs: list[tuple]) -> str:
    lines = [_HEADER, _GUARD, f"\n# {note}\n", "set -u\n", "SPECS=("]
    for s in specs:
        lines.append('  "%s"' % " ".join(str(x) for x in s))
    lines.append(")\n")
    lines.append(
        "# Chain: submit one at a time, waiting for the single stingy slot.\n"
        "for spec in \"${SPECS[@]}\"; do\n"
        "  set -- $spec\n"
        "  while [ \"$(squeue -u $USER -h -p stingy | wc -l)\" -ge 1 ]; do sleep 60; done\n"
        "  echo \"[chain] submitting $spec at $(date)\"\n"
        "  sbatch hpc_scripts/innovation_worker.sh \"$@\"\n"
        "done\n"
        "echo \"[chain] all submitted at $(date)\"\n")
    return "".join(lines)


def _pilot_script_name(spec: dict) -> str:
    return f"pilot_{spec['model']}_L{spec['horizon']}_seed{spec['seed']}.sh"


def _submit_pilot_driver() -> str:
    """Serial, fail-stop submitter for EXACTLY the eight authorized pilots.

    * references the four independent pilot scripts by name (never the generic
      worker, so each pilot keeps its own entry point and startup checks);
    * submits ONE job at a time: the next is submitted only after the previous
      reaches a terminal state, which respects the stingy cap of 1 running +
      1 pending;
    * additionally chains with `--dependency=afterok:` (never `afterany`), so a
      failed predecessor also cancels anything already queued;
    * explicit FAIL-STOP: a predecessor that is not COMPLETED with ExitCode 0:0
      stops the driver; no retry and no recursion.
    """
    names = [_pilot_script_name(s) for s in PILOT_SPECS]
    lst = "\n".join('  "hpc_scripts/%s"' % n for n in names)
    return _HEADER + _GUARD + f"""
# ── SERIAL SUBMISSION OF EXACTLY THE EIGHT AUTHORIZED PILOTS ────────────────
# pilot_gpt2_miflu_L24_seed42.sh / pilot_dlinear_L24_seed42.sh
# pilot_patchtst_L24_seed42.sh  / pilot_itransformer_L24_seed42.sh
# plus Qwen, CALF, and TimeCMA. Nothing else is ever queued: no generic worker,
# no other stage, no self-call,
# no re-submission of a failed job.
PILOTS=(
{lst}
)
PREV=""
for pilot in "${{PILOTS[@]}}"; do
  if [ -n "$PREV" ]; then
    echo "[chain] waiting for job $PREV to reach a terminal state"
    ST=""
    N=0
    while [ $N -lt 240 ]; do
      ST=$(sacct -j "$PREV" -X -n -o State 2>/dev/null | head -n 1 | tr -d ' ' || true)
      case "$ST" in
        COMPLETED|FAILED|CANCELLED*|TIMEOUT|NODE_FAIL|OUT_OF_MEMORY) break ;;
      esac
      sleep 30
      N=$((N + 1))
    done
    EC=$(sacct -j "$PREV" -X -n -o ExitCode 2>/dev/null | head -n 1 | tr -d ' ' || true)
    if [ "$ST" != "COMPLETED" ] || [ "${{EC%%:*}}" != "0" ]; then
      echo "[chain] FAIL-STOP: predecessor $PREV state=$ST exit=$EC - not submitting further pilots"
      exit 1
    fi
  fi
  if [ -z "$PREV" ]; then
    OUT=$(sbatch --parsable "$pilot")
  else
    OUT=$(sbatch --parsable --dependency=afterok:$PREV "$pilot")
  fi
  echo "[chain] submitted $pilot jobid=$OUT dependency=${{PREV:-none}}"
  PREV="$OUT"
done
echo "[chain] all eight authorized pilots submitted; last jobid=$PREV"
"""


def generate() -> list[str]:
    os.makedirs(HPC_DIR, exist_ok=True)
    written = []

    def _w(fname, content):
        p = os.path.join(HPC_DIR, fname)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        written.append(p)

    _w("innovation_worker.sh", _WORKER)

    # ── eight INDEPENDENT pilot scripts (unsubmitted) ──
    for spec in PILOT_SPECS:
        fname = f"pilot_{spec['model']}_L{spec['horizon']}_seed{spec['seed']}.sh"
        _w(fname, _pilot_script(fname, spec))
    # carry the frozen-source hash into every pilot spec (pilot_specs.json is
    # EXCLUDED from the source-snapshot hash set, so this is not circular)
    snap_sha = None
    snap_manifest = os.path.join(INNOVATION_ROOT, "source_snapshot_manifest.json")
    if os.path.exists(snap_manifest):
        try:
            with open(snap_manifest, "r", encoding="utf-8") as f:
                snap_sha = json.load(f).get("aggregate_sha256")
        except Exception:
            snap_sha = None
    from innovation.paths import (IMPLEMENTATION_SOURCE_VERSION,
                                  PROTOCOL_VERSION, current_snapshot_sha256,
                                  display_name_for, governance_fields,
                                  plan_sha256)
    # innov-v2.3: the top-level object AND every individual spec carry the FULL
    # 12-field governance block, all produced by the single contract
    # `paths.governance_fields()` so a refactor cannot silently drop any of them.
    plan_sha = plan_sha256()
    snap_sha = current_snapshot_sha256()

    def _arch_report(model_key: str) -> dict:
      # Metadata generation must never instantiate a backbone. In particular,
      # GPT-2/Qwen construction can reach Transformers caches; real loading
      # is reserved for the compute-node Pilot job.
      reports = {
        "nlinear": {"display_name": "NLinear", "fidelity": "REFERENCE_FAITHFUL"},
        "dlinear": {"display_name": "DLinear", "fidelity": "REFERENCE_FAITHFUL"},
        "patchtst": {"display_name": "PatchTST-inspired", "fidelity": "INSPIRED_SIMPLIFICATION"},
        "itransformer": {"display_name": "iTransformer-aligned", "fidelity": "REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS"},
        "gpt2_miflu": {"display_name": "MIFlu GPT-2", "fidelity": "LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE"},
        "qwen_time_llm": {"display_name": "Qwen2.5-1.5B Time-LLM-inspired", "fidelity": "INSPIRED_WITH_COMPONENT_CONTRACT"},
        "calf_llm": {"display_name": "CALF-inspired Cross-Modal LLM", "fidelity": "INSPIRED_WITH_COMPONENT_CONTRACT"},
        "timecma_llm": {"display_name": "TimeCMA-inspired LLM", "fidelity": "CLEAN_ROOM_PAPER_DERIVED_INSPIRED_IMPLEMENTATION"},
      }
      return reports[model_key]

    def _gov(model_key: str) -> dict:
        rep = _arch_report(model_key)
        return governance_fields(
            stage="pilot", model_key=model_key,
            display_name=display_name_for(model_key, rep),
            architecture_fidelity=rep.get("fidelity"),
            source_snapshot_sha256=snap_sha,
            authoritative_plan_sha256=plan_sha)

    gov_top = governance_fields(stage="pilot",
                                source_snapshot_sha256=snap_sha,
                                authoritative_plan_sha256=plan_sha)
    specs = [dict(s, **_gov(s["model"])) for s in PILOT_SPECS]
    _w("pilot_specs.json",
       json.dumps({"note": "infrastructure verification only; not a ranking",
                   **gov_top,
                   "scientific_protocol_version": PROTOCOL_VERSION,
                   "implementation_source_version": IMPLEMENTATION_SOURCE_VERSION,
                   "source_snapshot_sha256": snap_sha or "PENDING",
                   "selection_eligible": False,
                   "model_keys": [s["model"] for s in PILOT_SPECS],
                   "specs": specs}, indent=2) + "\n")

    # guarded, serial, fail-stop driver for EXACTLY the eight authorized pilots
    _w("submit_innovation_pilot.sh", _submit_pilot_driver())

    _w("submit_innovation_smoke.sh", _chain(
        "smoke", "Smoke: 1 epoch, representative combos (pipeline only).",
        [("dlinear", "none", "identity", 24, 42, 1, "smoke"),
         ("patchtst", "none", "identity", 24, 42, 1, "smoke"),
         ("itransformer", "none", "identity", 24, 42, 1, "smoke"),
         ("fusion_forecaster", "tfidf_svd", "concat_projection", 24, 42, 1, "smoke"),
         ("gpt2_miflu", "gpt2", "concat_projection", 24, 42, 1, "smoke")]))

    screening = []
    for m in ("dlinear", "nlinear", "patchtst", "itransformer"):
        for L in (24, 60):
            for seed in (42, 43, 44):
                screening.append((m, "none", "identity", L, seed, 20, "screening"))
    _w("submit_innovation_screening.sh", _chain(
        "screening", "Non-LLM, no-text screening: L=24/60, seeds 42-44.",
        screening))

    full = []
    for m in ("dlinear", "patchtst", "itransformer", "gpt2_miflu"):
        for L in (24, 36, 48, 60):
            for seed in range(42, 52):
                enc = "gpt2" if m == "gpt2_miflu" else "none"
                fus = "concat_projection" if m == "gpt2_miflu" else "identity"
                full.append((m, enc, fus, L, seed, 20, "full"))
    _w("submit_innovation_full.sh", _chain(
        "full", "FULL SWEEP: all L x seeds 42..51 (guarded; auto chain).", full))
    return written


def main(argv=None) -> int:
    written = generate()
    print("[hpc_specs] generated (NOT submitted):")
    for p in written:
        print("  ", p)
    print("[hpc_specs] every submit script REFUSES unless "
          "CONFIRM_INNOVATION_SUBMIT=YES (submission_attempted=false otherwise).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
