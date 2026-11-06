#!/bin/bash
#SBATCH --job-name=t2_env_probe_v8
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:12:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/envprobe_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/envprobe_%j.err
set -u
mkdir -p /gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs
echo "=== T2_ENV_PROBE START $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID ==="
echo "--- python candidates ---"
for p in /usr/bin/python3 /usr/local/bin/python3 /gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python /home/sychan552/.venvs/mlflu_llm/bin/python; do
  if [ -x "$p" ]; then echo -n "$p -> "; timeout 10s "$p" -V 2>&1; else echo "$p MISSING"; fi
done
echo "--- which python3 / pip ---"
which python3 pip pip3 2>&1 || true
echo "--- proxy ---"
env | grep -i proxy | head -8 || echo NO_PROXY
echo "--- internet + PyPI reachability (short) ---"
timeout 20s curl -s -o /dev/null -w "pypi_json_http=%{http_code}\n" https://pypi.org/pypi/chronos-forecasting/json || echo "curl_pypi_rc=$?"
timeout 20s curl -s -o /dev/null -w "hf_http=%{http_code}\n" https://huggingface.co  || echo "curl_hf_rc=$?"
echo "--- pip index test from mlflu_hpc python ---"
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
timeout 60s "$PY" -m pip index versions chronos-forecasting 2>&1 | head -8 || echo "pip_index_rc=$?"
echo "--- system python3 version detail ---"
/usr/bin/python3 -c "import sys; print(sys.version); print(sys.executable)" 2>&1 || true
echo "--- conda envs ---"
timeout 8s ls -la /gpfs1/home/sychan552/.conda/envs/ 2>/dev/null | head -15
echo "=== T2_ENV_PROBE END $(date -u +%FT%TZ) ==="
