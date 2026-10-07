#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:15:00
#SBATCH --output=hpc_results/innovation/logs/gpu_alloc_check_%j.out
#SBATCH --error=hpc_results/innovation/logs/gpu_alloc_check_%j.err

# ============================================================================
# gpu_allocation_env_check.sh — ONE no-training A100 allocation facts job.
# Implementation source innov-v2.2 (scientific protocol innov-v2.0).
#
# It is the ONLY way to clear UNVERIFIED_HPC_A100_ALLOCATION, because a login
# node has no GPU. It deliberately:
#   * trains nothing;
#   * loads no train / validation / test data;
#   * does NOT invoke scripts/innovation/runner.py, so no run directory,
#     no checkpoint, no prediction, no metric and no registry.csv row is created;
#   * writes ONLY the environment-allocation report below (plus the Slurm log);
#   * does NOT unlock pilot submission — that needs its own authorization.
#
# NOT part of the frozen runtime source hash: its name avoids the
# innovation_ / pilot_ / submit_innovation_ prefixes used by the source snapshot,
# so editing it does not require a source-version cascade.
#
# Run from the ISOLATED deployment root (never the reproduction repo):
#   cd /home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.2_06b83e18
#   CONFIRM_INNOVATION_SUBMIT=YES sbatch hpc_scripts/gpu_allocation_env_check.sh
# ============================================================================
set -u

# ── CONFIRMATION GUARD (nothing is submitted without an explicit opt-in) ─────
: "${CONFIRM_INNOVATION_SUBMIT:=NO}"
if [ "$CONFIRM_INNOVATION_SUBMIT" != "YES" ]; then
  echo "[guard] REFUSED to submit: export CONFIRM_INNOVATION_SUBMIT=YES to proceed."
  echo "[guard] submission_attempted=false"
  exit 0
fi
echo "[guard] submission_attempted=true"

# ── ISOLATED deployment root (explicit; NOT the reproduction repository) ────
export INNOVATION_DEPLOYMENT_ROOT=/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.2_06b83e18
cd "$INNOVATION_DEPLOYMENT_ROOT" || { echo "deployment root not found"; exit 1; }
AGGREGATE=06b83e18e4bb66d69ae457087fa5024bb4a50884bca3c080ca51af35de575e86

module unload default 2>/dev/null; module load old_modules 2>/dev/null
export PATH="/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH"
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export TRANSFORMERS_CACHE=$HF_HOME
export HF_DATASETS_CACHE=$HF_HOME
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
mkdir -p hpc_results/innovation/logs results/innovation/hpc_deployment_verification/innov-v2.2

echo "== deployed source aggregate verification =="
python scripts/innovation/verify_source_snapshot.py \
  --deployment-root "$INNOVATION_DEPLOYMENT_ROOT" \
  --manifest results/innovation/source_snapshot_manifest.json \
  --expect "$AGGREGATE" || { echo "SOURCE_VERIFY=FAILED"; exit 1; }

echo "== allocation =="
echo "hostname=$(hostname)"
echo "utc=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-none}"
echo "SLURM_JOB_PARTITION=${SLURM_JOB_PARTITION:-none}"
echo "SLURM_JOB_GPUS=${SLURM_JOB_GPUS:-none}"
echo "SLURM_GPUS_ON_NODE=${SLURM_GPUS_ON_NODE:-none}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-none}"

echo "== nvidia-smi =="
nvidia-smi 2>&1 || echo "nvidia-smi: unavailable"

echo "== facts (no training, no data, no run) =="
python - <<PY
import json, os, sys, datetime, subprocess
sys.path.insert(0, "scripts")
from innovation.paths import (IMPLEMENTATION_SOURCE_VERSION, PLAN_SHA256_EXPECTED,
                              PROTOCOL_VERSION, plan_sha256)
rep = {
    "check": "a100_allocation_environment_check",
    "implementation_source_version": IMPLEMENTATION_SOURCE_VERSION,
    "scientific_protocol_version": PROTOCOL_VERSION,
    "utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "hostname": os.uname().nodename,
    "deployment_root": os.environ.get("INNOVATION_DEPLOYMENT_ROOT"),
    "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    "slurm_partition": os.environ.get("SLURM_JOB_PARTITION"),
    "slurm_job_gpus": os.environ.get("SLURM_JOB_GPUS"),
    "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    "training_performed": False,
    "data_loaded": False,
}
# authoritative plan hash + protocol/implementation versions, read from the
# DEPLOYED code (never hardcoded), and the runtime source aggregate
plan = plan_sha256()
rep["plan_sha256_runtime"] = plan
rep["plan_sha256_expected"] = PLAN_SHA256_EXPECTED
rep["plan_sha256_matches"] = plan.lower() == PLAN_SHA256_EXPECTED.lower()
man = json.load(open("results/innovation/source_snapshot_manifest.json"))
rep["source_aggregate_expected"] = man["aggregate_sha256"]
rep["source_snapshot_n_files"] = man["n_files"]
v = subprocess.run([sys.executable, "scripts/innovation/verify_source_snapshot.py",
                    "--deployment-root", os.environ.get("INNOVATION_DEPLOYMENT_ROOT"),
                    "--manifest", "results/innovation/source_snapshot_manifest.json",
                    "--expect", man["aggregate_sha256"]],
                   capture_output=True, text=True)
rep["source_verification_exit"] = v.returncode
rep["source_aggregate_actual"] = None
for line in (v.stdout or "").splitlines():
    if "actual_aggregate_sha256" in line:
        rep["source_aggregate_actual"] = line.split("=")[-1].strip()
rep["source_verification_ok"] = bool(
    v.returncode == 0
    and rep["source_aggregate_actual"] == rep["source_aggregate_expected"])
try:
    p = subprocess.run(["nvidia-smi", "--query-gpu=index,name,memory.total,driver_version",
                        "--format=csv,noheader"], capture_output=True, text=True, timeout=60)
    rep["nvidia_smi_query"] = p.stdout.strip()
except Exception as e:
    rep["nvidia_smi_query"] = f"unavailable: {type(e).__name__}"
try:
    import torch
    rep["torch"] = torch.__version__
    rep["cuda_runtime_version"] = torch.version.cuda
    rep["cuda_available"] = bool(torch.cuda.is_available())
    rep["cuda_device_count"] = int(torch.cuda.device_count())
    rep["cudnn_version"] = torch.backends.cudnn.version() if torch.cuda.is_available() else None
    gpus = []
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            pr = torch.cuda.get_device_properties(i)
            gpus.append({"index": i, "name": pr.name, "total_memory_bytes": pr.total_memory,
                         "compute_capability": f"{pr.major}.{pr.minor}"})
            # tiny allocation only: proves the device is usable, trains nothing
            a = torch.zeros(1024, device=f"cuda:{i}")
            gpus[-1]["allocation_ok"] = bool(a.sum().item() == 0)
        rep["gpu_name_0"] = torch.cuda.get_device_name(0)
    rep["gpus"] = gpus
    rep["exactly_one_gpu"] = (rep["cuda_device_count"] == 1)
    rep["gpu_name_is_a100"] = all("A100" in g["name"] for g in gpus) and len(gpus) == 1
except Exception as e:
    rep["torch_probe_failed"] = f"{type(e).__name__}: {e}"
try:
    from transformers import GPT2Model, GPT2Tokenizer
    GPT2Tokenizer.from_pretrained("gpt2"); GPT2Model.from_pretrained("gpt2")
    rep["gpt2_offline_load"] = "OK"
except Exception as e:
    rep["gpt2_offline_load"] = f"FAILED {type(e).__name__}: {e}"

rep["allocation_check_ok"] = bool(
    rep.get("cuda_available") and rep.get("exactly_one_gpu")
    and rep.get("gpu_name_is_a100") and rep.get("gpt2_offline_load") == "OK"
    and rep.get("source_verification_ok") and rep.get("plan_sha256_matches"))
out = (f"results/innovation/hpc_deployment_verification/innov-v2.2/"
       f"a100_allocation_check_{os.environ.get('SLURM_JOB_ID','local')}.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(rep, f, indent=2)
print(json.dumps(rep, indent=2))
print("REPORT", out)
PY
RC=$?
echo "== done (no training, no data, no run created) =="
exit $RC
