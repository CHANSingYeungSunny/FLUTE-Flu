#!/bin/bash
#SBATCH --job-name=a0_embed_recover
#SBATCH --partition=stingy
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=/scratch/sychan552/a2_stage5/logs/a0_embed_%j.out
#SBATCH --error=/scratch/sychan552/a2_stage5/logs/a0_embed_%j.err
# CPU-only => ZERO GPU-hours.
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
$PY - <<'PY' 2>&1
import dis, marshal, sys
p = "/scratch/sychan552/a0_replay/__pycache__/embed.cpython-39.pyc"
code = marshal.loads(open(p, "rb").read()[16:])
TARGETS = ("PositionalEmbedding", "TokenEmbedding", "FixedEmbedding",
           "TemporalEmbedding", "TimeFeatureEmbedding", "DataEmbedding",
           "DataEmbedding_wo_pos", "DataEmbedding_wo_time")
for k in code.co_consts:
    if not hasattr(k, "co_name") or k.co_name not in TARGETS:
        continue
    print("=" * 78)
    print("CLASS", k.co_name)
    for m in k.co_consts:
        if not hasattr(m, "co_name"):
            continue
        print("-" * 70)
        print("  def", m.co_name, "args =", m.co_varnames[:m.co_argcount])
        if m.co_name == "__init__":
            print("  names:", sorted(set(m.co_names)))
            print("  consts:", [c for c in m.co_consts
                                if isinstance(c, (str, int, float, bool, type(None)))])
        dis.dis(m)
PY
