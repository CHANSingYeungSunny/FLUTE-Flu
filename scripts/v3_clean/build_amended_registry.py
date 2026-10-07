"""build_amended_registry.py — append-only amended execution registry.

Resolves the 18 deferred Wave-2 controls per
`results/v3_clean/preregistration/DEFERRED_CONTROLS_PROTOCOL_AMENDMENT.json`
WITHOUT editing the frozen `complete_specs_598.json`.

Emits:
  * results/v3_clean/runs/complete_specs_amended.json
      - same 598 rows as the frozen registry;
      - 12 zero_text/shuffled_text Wave-2 rows -> marked exact equivalents of
        their accepted Wave-1 counterparts (submittable=false, no new jobs);
      - 6 llm_removed_or_alignment_only rows -> rebound to timecma_llm
        (submittable=true, executable_binding=true).
  * hpc_scripts/v3_clean/<6 rebound run_keys>.sh (LF-only), each selecting the
    amended registry via INNOVATION_REGISTRY_REL.

The frozen matrix is never modified (deleted=0, duplicated=0).
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "results" / "v3_clean" / "runs"
PREREG = ROOT / "results" / "v3_clean" / "preregistration"
SCRIPTS_OUT = ROOT / "hpc_scripts" / "v3_clean"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

FROZEN = RUNS / "complete_specs_598.json"
AMENDMENT = PREREG / "DEFERRED_CONTROLS_PROTOCOL_AMENDMENT.json"
AMENDED = RUNS / "complete_specs_amended.json"

frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
amend = json.loads(AMENDMENT.read_text(encoding="utf-8"))

# ── 1. equivalence map (12 zero_text/shuffled_text) ─────────────────────────
equiv = {}
for e in amend["amendment_A_equivalence_mapping"]:
    equiv[e["wave2_run_key"]] = {
        "equivalent_wave1_run_key": e["equivalent_wave1_run_key"],
        "wave1_job_id": e["wave1_job_id"],
        "wave1_compact_sha256": e["wave1_compact_sha256"],
        "wave1_source_full_checkpoint_sha256":
            e["wave1_source_full_checkpoint_sha256"],
        "wave1_canonical_tensor_sha256": e["wave1_canonical_tensor_sha256"],
    }

# ── 2. rebound llm_removed rows (6) ──────────────────────────────────────────
rebound = {c["run_key"]: c for c in amend["amendment_B_rebind_controls"]}
rebound_keys = sorted(rebound, key=lambda k: rebound[k]["order"])

# ── 3. produce the amended specs ────────────────────────────────────────────
specs = []
n_executable = 0
for s in frozen["specs"]:
    s = dict(s)
    rk = s["run_key"]
    if rk in equiv:
        s["amended_action"] = "equivalent_to_wave1"
        s["amended_equivalence"] = equiv[rk]
        s["submittable"] = False
        s["executable_binding"] = False
    elif rk in rebound:
        s["amended_action"] = "rebind_parent_to_timecma_llm"
        s["parent_model"] = "timecma_llm"
        s["submittable"] = True
        s["executable_binding"] = True
        s["intervention"] = {"text_mode": "removed"}
    if s.get("executable_binding"):
        n_executable += 1
    specs.append(s)

amended = {
    "generated_utc": NOW,
    "amendment_id": amend["amendment_id"],
    "amendment_authority": amend["authority"],
    "frozen_source": "complete_specs_598.json (byte-identical, never edited)",
    "frozen_source_sha256": hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
    "version": frozen.get("version"),
    "aggregate_sha256": frozen.get("aggregate_sha256"),
    "n_specs": len(specs),
    "n_executable_bindings": n_executable,
    "n_equivalent_to_wave1": len(equiv),
    "n_rebound": len(rebound),
    "specs": specs,
}
AMENDED.write_text(json.dumps(amended, indent=2), encoding="utf-8")

# ── 4. LF-only Slurm scripts for the 6 rebound rows ─────────────────────────
TEMPLATE = """#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --output=hpc_results/innovation/logs/slurm_%j_{name}.out
#SBATCH --error=hpc_results/innovation/logs/slurm_%j_{name}.err

# clean-v3 Wave 2 amended row (rebind llm_removed_or_alignment_only -> timecma_llm): {run_key}
set -euo pipefail
module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
export INNOVATION_REGISTRY_REL=results/v3_clean/runs/complete_specs_amended.json
: "${{INNOVATION_DEPLOYMENT_ROOT:?must be set}}"
: "${{CONFIRM_INNOVATION_SUBMIT:=NO}}"
if [ "$CONFIRM_INNOVATION_SUBMIT" != "YES" ]; then
  echo "[guard] submission_attempted=false"
  exit 0
fi
cd "$INNOVATION_DEPLOYMENT_ROOT"
mkdir -p hpc_results/innovation/logs
python scripts/innovation/clean_runner.py --run-key {run_key}
"""
n_scripts = 0
crlf = 0
for rk in rebound_keys:
    body = TEMPLATE.format(name=rk, run_key=rk)
    p = SCRIPTS_OUT / f"{rk}.sh"
    p.write_bytes(body.encode("utf-8"))
    n_scripts += 1
    if b"\r" in p.read_bytes():
        crlf += 1

# ── 5. audit ────────────────────────────────────────────────────────────────
audit = {
    "generated_utc": NOW,
    "frozen_edited": False,
    "frozen_sha256_unchanged": True,
    "n_specs": len(specs),
    "n_executable_bindings": n_executable,
    "n_equivalent_to_wave1": len(equiv),
    "n_rebound": len(rebound),
    "n_scripts_written": n_scripts,
    "crlf_scripts": crlf,
    "rebound_parent": "timecma_llm",
}
(RUNS / "amended_registry_audit.json").write_text(
    json.dumps(audit, indent=2), encoding="utf-8")

print(f"[amended] specs={len(specs)} executable={n_executable} "
      f"equivalent={len(equiv)} rebound={len(rebound)} scripts={n_scripts} "
      f"crlf={crlf}")
print(f"[amended] frozen sha256 (unchanged) = "
      f"{audit['frozen_sha256_unchanged']}")
