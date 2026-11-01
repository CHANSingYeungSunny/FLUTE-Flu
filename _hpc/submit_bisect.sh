#!/bin/bash -l
#SBATCH --job-name=miflu_bisect
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=slurm-bisect-%j.out
#
# Blocker B bisection: are the two L24 seed-2021 checkpoints the same weights?
#   A = ckpt_L24_s2021/_rep_miflu_L24_seed2021.pth        (rep 1 of the 10-rep run)
#   B = ckpt_L24_s2021_pred/best_miflu_L24.pth            (the standalone 1-rep run)
# Both log test_mse_all = 1.240157 yet the exported predictions differ by 1.99 sd.
set -uo pipefail
module unload default
module load old_modules
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
cd /gpfs1/home/sychan552/stage5_a2_durable/code

echo "=== file hashes ==="
md5sum "${AR}/ckpt_L24_s2021/_rep_miflu_L24_seed2021.pth" "${AR}/ckpt_L24_s2021_pred/best_miflu_L24.pth"

"${PY}" - <<'PYEOF'
import hashlib, torch
AR = "/gpfs1/home/sychan552/stage5_a2_durable/author_runs"
A = f"{AR}/ckpt_L24_s2021/_rep_miflu_L24_seed2021.pth"
B = f"{AR}/ckpt_L24_s2021_pred/best_miflu_L24.pth"
a = torch.load(A, map_location="cpu")
b = torch.load(B, map_location="cpu")
print(f"[bisect] A tensors={len(a)}  B tensors={len(b)}  same keys={set(a)==set(b)}")

def h(t):
    return hashlib.sha256(t.detach().cpu().numpy().tobytes()).hexdigest()[:16]

diffs = []
for k in sorted(set(a) & set(b)):
    ta, tb = a[k], b[k]
    if tuple(ta.shape) != tuple(tb.shape):
        print(f"  [SHAPE] {k}: {tuple(ta.shape)} vs {tuple(tb.shape)}")
        continue
    d = float((ta.float() - tb.float()).abs().max())
    diffs.append((d, k, h(ta), h(tb)))
diffs.sort(reverse=True)
identical = sum(1 for d, *_ in diffs if d == 0.0)
print(f"[bisect] tensors compared={len(diffs)}  bit-identical={identical}")
print("[bisect] top-10 largest per-tensor max|delta|:")
for d, k, ha, hb in diffs[:10]:
    print(f"   {d:.6e}  {k}   shaA={ha} shaB={hb}")
print(f"[bisect] VERDICT: {'SAME WEIGHTS' if identical == len(diffs) else 'DIFFERENT WEIGHTS'}")
PYEOF
