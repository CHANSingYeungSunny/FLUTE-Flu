"""build_prepilot_gate_status.py — record the REAL pre-Pilot Gate outcome.

Gate FAILED. Five of eight models passed on gpu-a100-03; the three new LLM
branches failed deterministically on asset-cache resolution. No Pilot was
submitted. All evidence is recorded, nothing is deleted.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMPL = ROOT / "results" / "v3" / "implementation"
PILOTS = ROOT / "results" / "v3" / "pilots"
for d in (IMPL, PILOTS):
    d.mkdir(parents=True, exist_ok=True)
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

DEPLOY_ROOT = "/scratch/sychan552/innovation_deploy_root_v3_1"
SOURCE_AGG = "6d6d37a75e0dd7a6137a194a8d12347d207fa4a013eb5b65136068bc2f358544"
BUNDLE = "775c6c22c4af952e75628ac315f2cc35c8e7e6e6d86b5ec02831c3b0061f1282"
GUIDE_SHA = "1cd21a655907d137914c695bf04637d8da2f09358a0732c961e739dd8e74c167"
DATA_SHA = "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d"
QWEN_REV = "8faed761d45a263340a0528343f099c05c9a4323"


def wj(p, o):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def wcsv(p, rows, cols=None):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    cols = cols or list(rows[0].keys())
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ── the three Gate attempts, in order ───────────────────────────────────────
ATTEMPTS = [
    {"job_id": "563486", "attempt": 1, "state": "FAILED", "exit_code": "1:0",
     "elapsed": "00:01:04", "node": "gpu-a100-05", "partition": "stingy",
     "alloc": "cpu=8,mem=32G,gres/gpu:a100=1", "models_ok": "0/8",
     "assets_downloaded": False,
     "failures": ["D1 RevisionNotFoundError (Time-LLM commit used as Qwen revision)",
                  "D2 CUDA busy/unavailable on first allocation",
                  "D3 gpt2_miflu TypeError unexpected keyword 'model_id'",
                  "D4 Qwen not cached -> transformers reports no connection"]},
    {"job_id": "563498", "attempt": 2, "state": "FAILED", "exit_code": "1:0",
     "elapsed": "00:02:33", "node": "gpu-a100-05", "partition": "stingy",
     "alloc": "cpu=8,mem=32G,gres/gpu:a100=1", "models_ok": "0/8",
     "assets_downloaded": True,
     "failures": ["D2 persisted: CUDA probe 5/5 attempts failed with "
                  "'CUDA-capable device(s) is/are busy or unavailable'"],
     "assets": {"n_files": 7, "total_bytes": 3098955511, "revision": QWEN_REV,
                "cache": "/gpfs1/scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B/"
                         "snapshots/" + QWEN_REV}},
    {"job_id": "565800", "attempt": 3, "state": "FAILED", "exit_code": "1:0",
     "elapsed": "00:01:12", "node": "gpu-a100-03", "partition": "stingy",
     "alloc": "cpu=8,mem=32G,gres/gpu:a100=1", "models_ok": "5/8",
     "assets_downloaded": True,
     "node_excluded": "gpu-a100-05",
     "models_ok_list": ["nlinear", "dlinear", "patchtst", "itransformer", "gpt2_miflu"],
     "models_failed_list": ["qwen_time_llm", "calf_llm", "timecma_llm"],
     "failures": ["D2 RESOLVED by avoiding the faulty node (CUDA works on gpu-a100-03)",
                  "D3 RESOLVED (gpt2_miflu now builds and backprops)",
                  "NEW D5: all three new LLM branches raise OSError "
                  "\"We couldn't connect to 'https://huggingface.co' ... and couldn't find "
                  "them in the cached files\" even though the pinned revision IS present in "
                  "HF_HUB_CACHE"]},
]

GATE = {
    "generated_utc": NOW,
    "gate_kind": "PREPILOT_GATE",
    "outcome": "FAILED",
    "attempts": ATTEMPTS,
    "retries_used": 3,
    "retries_permitted_by_prompt": 2,
    "acceptance_criteria": {
        "slurm_state_COMPLETED": False,
        "exit_code_0_0": False,
        "partition_stingy": True,
        "allocated_gpu_a100_1": True,
        "source_files_verified_85_of_85": True,
        "source_aggregate_matches": True,
        "runtime_guard_violations": 0,
        "canonical_data_sha256_matches": True,
        "test_access_count": 0,
        "holdout_access_count": 0,
        "formal_pilot_jobs_submitted_before_gate": 0,
        "cuda_visible_and_usable": True,
        "all_eight_models_built_with_gradients": False,
    },
    "notes": [
        "Job 565800 is the single evidence-backed retry permitted from this prompt; it was "
        "spent avoiding the faulty node gpu-a100-05.",
        "Five of eight models, including gpt2_miflu, now build on CUDA with a verified "
        "backward pass on gpu-a100-03.",
        "The three new LLM branches fail deterministically on asset-cache resolution, which "
        "is a code/plumbing defect, not a transient scheduler condition.",
        "No Pilot may be submitted while the Gate is FAILED.",
    ],
}
wj(IMPL / "prepilot_gate_status.json", GATE)
wj(IMPL / "prepilot_gate_job_563498_audit.json", {
    "generated_utc": NOW, "job_id": "563498", "gate_kind": "PREPILOT_GATE",
    "state": "FAILED", "exit_code": "1:0", "elapsed": "00:02:33",
    "node": "gpu-a100-05", "partition": "stingy",
    "alloc_tres": "cpu=8,mem=32G,node=1,billing=15,gres/gpu=1,gres/gpu:a100=1",
    "preflight": {"runtime_guard_violations": 0,
                  "source_files_verified": "85/85",
                  "source_aggregate_sha256": SOURCE_AGG},
    "failed_check": "CUDA pre-flight probe",
    "cuda_visible_devices": "0",
    "nvidia_smi_L": "GPU 0: NVIDIA A100-SXM4-80GB (UUID: GPU-2f50742c-cd0b-dd43-630a-54069b9eeae5)",
    "torch": "2.5.1", "cuda_runtime": "11.8",
    "probe_attempts": 5,
    "probe_errors": ["CUDA error: CUDA-capable device(s) is/are busy or unavailable"] * 5,
    "assets_downloaded": True, "asset_total_bytes": 3098955511, "asset_n_files": 7,
    "asset_revision": QWEN_REV,
    "classification": "TRANSIENT_OR_NODE_SPECIFIC_CUDA_INIT_FAILURE",
    "resolution": "Retry 565800 excluded gpu-a100-05; CUDA then initialised normally on "
                  "gpu-a100-03, confirming the device was held by a foreign context on "
                  "gpu-a100-05 and that no project code change was required.",
})

# ── CUDA preflight report (from the retry, which is the informative run) ────
wj(IMPL / "cuda_preflight_report.json", {
    "generated_utc": NOW,
    "job_563498": {"node": "gpu-a100-05", "cuda_visible_devices": "0",
                   "nvidia_smi_L": "GPU 0: NVIDIA A100-SXM4-80GB",
                   "torch": "2.5.1", "cuda_runtime": "11.8",
                   "cuda_available": True, "device_count": 1,
                   "total_mem_gb": 85.09,
                   "allocations_succeeded": 0, "allocation_attempts": 5,
                   "error": "CUDA-capable device(s) is/are busy or unavailable",
                   "verdict": "UNUSABLE_ON_THIS_NODE"},
    "job_565800": {"node": "gpu-a100-03", "cuda_visible_devices": "0",
                   "torch": "2.5.1", "cuda_runtime": "11.8",
                   "allocations_succeeded": 5,
                   "models_built_on_cuda":
                       ["nlinear", "dlinear", "patchtst", "itransformer", "gpt2_miflu"],
                   "peak_gpu_mem_gb_observed": 0.68,
                   "verdict": "USABLE"},
    "conclusion": "CUDA is usable on the cluster; gpu-a100-05 was temporarily unusable. "
                  "The remediation was node exclusion, not a code change.",
})

# ── asset integrity ─────────────────────────────────────────────────────────
wj(IMPL / "asset_integrity_report.json", {
    "generated_utc": NOW,
    "qwen": {"id": "Qwen/Qwen2.5-1.5B", "revision": QWEN_REV,
             "license": "Apache-2.0", "gated": False,
             "downloaded": True, "n_files": 7, "total_bytes": 3098955511,
             "approx_gib": 2.89,
             "cache": "/gpfs1/scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B/"
                      "snapshots/" + QWEN_REV,
             "download_job": "563498",
             "load_status": "FAILED_TO_RESOLVE_AT_FROM_PRETRAINED",
             "root_cause": "The pinned revision is present in the hub cache, but "
                           "from_pretrained resolves the model without the explicit "
                           "revision / local snapshot path and therefore falls back to a "
                           "network lookup that the compute node cannot complete.",
             "remedy": "Pass revision=QWEN_REV (or the local snapshot directory) to the "
                       "text-backbone loader, or set local_files_only=True after cache "
                       "preparation. Requires a source change and a fresh Gate run."},
    "gpt2": {"source": "existing verified MIFlu/GPT-2 asset path", "new_download": False,
             "load_status": "OK on compute node (job 565800)"},
    "file_hashes": [],
    "note": "File-level SHA-256 values were computed by the Gate into "
            "weight_and_asset_manifest.json on the deployment root.",
})

# ── deployment verification ─────────────────────────────────────────────────
wj(IMPL / "deployment_verification.json", {
    "generated_utc": NOW,
    "deployment_root": DEPLOY_ROOT,
    "resolved_root": "/gpfs1/scratch/sychan552/innovation_deploy_root_v3_1",
    "verification_mode": "explicit_root",
    "expected_file_count": 85, "verified_file_count": 85,
    "expected_aggregate_sha256": SOURCE_AGG, "actual_aggregate_sha256": SOURCE_AGG,
    "exit_status": 0,
    "runtime_guard_violations": 0,
    "forbidden_root": "/home/sychan552/scratch/CHATTIME/Chattime",
    "bundle_sha256": BUNDLE, "bundle_byte_identical": True,
    "canonical_data_sha256": DATA_SHA,
    "login_node_model_loading": False,
    "status": "VERIFIED",
})

# ── pilots: none submitted ──────────────────────────────────────────────────
ORDER = ["nlinear", "dlinear", "patchtst", "itransformer", "gpt2_miflu",
         "qwen_time_llm", "calf_llm", "timecma_llm"]
try:
    specs = json.loads((ROOT / "hpc_scripts" / "pilot_specs.json").read_text(encoding="utf-8"))
    by_model = {s["model"]: s for s in specs["specs"]}
except Exception:
    by_model = {}

wj(PILOTS / "pilot_submission_manifest.json", {
    "generated_utc": NOW,
    "gate_status": "FAILED",
    "n_planned": 8, "n_submitted": 0,
    "blocked_reason": "Pre-Pilot Gate did not pass; no Pilot may be submitted.",
    "deployment_root": DEPLOY_ROOT,
    "source_aggregate_sha256": SOURCE_AGG,
    "serial_policy": "one job at a time; wait for terminal state before the next sbatch",
    "permanent_marks": {"experiment_stage": "pilot",
                        "purpose": "infrastructure_verification_only",
                        "selection_eligible": False, "paper_result_eligible": False,
                        "test_access_allowed": False},
    "results_are_not_ranked": True,
    "cells": [{"order": i + 1, "model_key": m, "horizon": 24, "seed": 42,
               "script": f"hpc_scripts/pilot_{m}_L24_seed42.sh",
               "job_id": None, "state": "NOT_SUBMITTED", "exit_code": None}
              for i, m in enumerate(ORDER)],
})
wcsv(PILOTS / "pilot_job_status.csv",
     [{"order": i + 1, "model_key": m, "horizon": 24, "seed": 42,
       "job_id": "", "state": "NOT_SUBMITTED", "exit_code": "", "elapsed": "", "node": ""}
      for i, m in enumerate(ORDER)])
wcsv(PILOTS / "resource_usage_report.csv", [])
wj(PILOTS / "test_holdout_isolation_verification.json",
   {"generated_utc": NOW, "test_access_count": 0, "holdout_access_count": 0,
    "pilots_submitted": 0, "v2_test_paths_used": False,
    "status": "VERIFIED_ZERO"})
wj(PILOTS / "pilot_validation_report.json",
   {"generated_utc": NOW, "n_pilots": 0, "n_validated": 0,
    "status": "NOT_APPLICABLE_GATE_FAILED"})

(IMPL / "prepilot_gate_status.md").write_text("\n".join([
    "# Pre-Pilot Gate status", "", f"Generated {NOW}.", "",
    "**Outcome: FAILED.** No Pilot was submitted.", "",
    "| # | Job | Node | State | Exit | Elapsed | Models OK | Assets |",
    "|---|---|---|---|---|---|---|---|",
] + [f"| {a['attempt']} | {a['job_id']} | {a['node']} | {a['state']} | {a['exit_code']} | "
     f"{a['elapsed']} | {a['models_ok']} | {a['assets_downloaded']} |" for a in ATTEMPTS] + [
    "", "## Acceptance criteria", "",
    "| Criterion | Result |", "|---|---|",
] + [f"| {k} | {v} |" for k, v in GATE["acceptance_criteria"].items()] + [
    "", "## What passed", "",
    "- `HPC_GUIDE.md` hash unchanged; full text read before any HPC action.",
    f"- Isolated deployment root verified: 85/85 files, aggregate `{SOURCE_AGG}`, exit 0.",
    "- `runtime_guard`: 0 violations; no runtime import from the original repository.",
    "- Canonical data SHA-256 matches; Test and holdout access counts are 0.",
    "- Qwen pinned revision downloaded: 7 files, 3,098,955,511 bytes, revision "
    f"`{QWEN_REV}`.",
    "- On gpu-a100-03, CUDA works and five models build with a verified backward pass, "
    "including gpt2_miflu (82,136,232 total / 1,030,056 trainable params, 45 grads, "
    "forward shape [2, 7, 24]).",
    "", "## What failed", "",
    "- **D1 (fixed)**: Time-LLM repository commit had been used as the Qwen revision; "
    f"corrected to `{QWEN_REV}`.",
    "- **D2 (resolved operationally)**: gpu-a100-05 rejected every CUDA allocation; "
    "excluding that node fixed it, so no project code change was needed.",
    "- **D3 (fixed)**: unsupported `model_id` is no longer passed to the GPT-2 adapter.",
    "- **D4 (partially open)**: the assets are downloaded and correct, but "
    "`from_pretrained` does not resolve them from the hub cache on the compute node and "
    "falls back to a network lookup.",
    "", "## Retries", "",
    "Three Gate runs were used (563486, 563498, 565800). This prompt permitted one further "
    "retry beyond 563498; it was spent on 565800. No further Gate retry is permitted here.",
    "", "## Next step", "",
    "Repair the asset-resolution plumbing in the text-backbone loader (pass the pinned "
    "revision or the local snapshot path, or set `local_files_only=True`), then perform a "
    "fresh Gate run. Pilots may only be submitted after that Gate passes.", ""]),
    encoding="utf-8")

(PILOTS / "pilot_validation_report.md").write_text("\n".join([
    "# Pilot validation report", "", f"Generated {NOW}.", "",
    "**No Pilot was submitted.** The pre-Pilot Gate (jobs 563486, 563498, 565800) did not "
    "pass, so Pilot submission is blocked by the workflow.", "",
    "| # | Model | Horizon | Seed | Job ID | State |",
    "|---|---|---|---|---|---|",
] + [f"| {i+1} | {m} | 24 | 42 | - | NOT_SUBMITTED |"
     for i, m in enumerate(ORDER)] + [
    "", "Test and holdout access counts remain 0. Pilot metrics were not produced, so "
    "nothing was ranked.", ""]), encoding="utf-8")

print("[gate_status] outcome=FAILED attempts=3 pilots_submitted=0")
print("[gate_status] models_ok_565800=5/8")
