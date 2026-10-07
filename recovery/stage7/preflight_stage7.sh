#!/bin/bash
# Pre-execution site verification for the newly authorized 2.3 GPU-hour round.
# READ-ONLY. Run on the login node; touches only small files and sacct/squeue.
set -uo pipefail
cd /scratch/sychan552/a2_stage5 || exit 1
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python

echo "############ 1. queue / dispatchers / locks ############"
squeue -u "$USER"
echo "--- processes ---"
ps -u "$USER" -o pid,etime,cmd | grep -E "dispatch|train_backbone|score_test|main_ILI|a0_gpu" | grep -v grep || echo "  none running"
echo "--- tmux ---"; tmux ls 2>&1 | sed 's/^/  /'
echo "--- locks ---"
for L in results/stage6/logs/EXEC_LOCK results/stage5/logs/EXEC_LOCK; do
  if [ -e "$L" ]; then echo "  PRESENT $L:"; sed 's/^/    /' "$L"; else echo "  absent  $L"; fi
done
echo "--- any stage6 results already? ---"
find results/stage6 -type f 2>/dev/null | head -5 || true
[ -z "$(find results/stage6 -type f 2>/dev/null)" ] && echo "  (stage6 has no results: nothing submitted yet)"

echo
echo "############ 2. A2 durable archive: 36 checkpoints vs FIRST lock ############"
$PY - <<'PY'
import hashlib, json, os
D = "/home/sychan552/stage5_a2_durable"
lock = json.load(open(os.path.join(D, "scoring",
                                  "CHECKPOINT_LOCK_first_20260925T161329Z.json")))
def h(p, c=1 << 22):
    x = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(c)
            if not b: break
            x.update(b)
    return x.hexdigest()
ok = bad = miss = 0
for f in lock["fits"]:
    rel = f["ckpt_path"].split("ckpt/author_966/")[-1]
    p = os.path.join(D, "checkpoints", "author_966", rel)
    if not os.path.exists(p): print("  MISSING", rel); miss += 1; continue
    if os.path.getsize(p) != f["ckpt_bytes"]: print("  SIZE", rel); bad += 1; continue
    if h(p) != f["ckpt_sha256"]: print("  SHA FAIL", rel); bad += 1; continue
    ok += 1
print(f"  RESULT: ok={ok} sha_fail={bad} missing={miss} of {len(lock['fits'])}")
PY

echo
echo "############ 3. A2 result artefacts still intact ############"
$PY - <<'PY'
import glob, json
import numpy as np, pandas as pd
S = "/home/sychan552/stage5_a2_durable/scoring"
npz = sorted(glob.glob(S + "/predictions/pred_*.npz"))
print(f"  prediction NPZs      : {len(npz)} (expect 44)")
man = pd.read_csv(S + "/predictions/test_manifest.csv")
sc = json.load(open(S + "/predictions/scaler_train_only.json"))
sm = pd.read_csv(S + "/score_matrix.csv")
print(f"  test_manifest rows   : {len(man)} (expect 6688)")
print(f"  score_matrix rows    : {len(sm)} (expect 44)")
print(f"  scaler               : fitted on {sc['fit_on']}, {len(sc['var_cols'])} vars")
# spot-check one NPZ is readable and consistent
z = np.load(npz[0], allow_pickle=False)
m = float(np.mean((z["pred"] - z["target"]) ** 2))
print(f"  spot check {os.path.basename(npz[0])}: mse_all={m:.6f} "
      f"shape={z['pred'].shape} space={z['space']}")
PY

echo
echo "############ 4. NEW ledger for the 2.3 GPU-hour authorization ############"
L=results/stage7/GPU_LEDGER_stage7.tsv
mkdir -p results/stage7
echo "jobid	name	state	elapsed	gpu	gpu_hours	ours	submit" > "$L"
echo "  created $L (NEW round, counted from zero; A2's 1.1536/2.0 is untouched)"
echo "  authorized cap       : 2.3000 GPU-h"
echo "  A0 sub-budget        : 0.5000"
echo "  eight-model sub      : 1.8000"

echo
echo "############ 5. dispatcher: confirm --run is the real submit switch ############"
echo "--- without --run ---"
bash recovery/stage6/dispatch.sh 2>&1 | sed 's/^/  /'
echo "--- grep the switch and the stop rule in dispatch.sh ---"
grep -n -E '\-\-run|sbatch|BUDGET_GPU_H|spend|stop|STOP' recovery/stage6/dispatch.sh | sed 's/^/  /'

echo
echo "############ 6. A0 GPU script: confirm it is the author's default config ############"
grep -n -E 'MODE|train_epochs|learning_rate|multimodal|pred_len|itr|PREFT|PEFT|freeze|lora|main_ILI_lora' \
  recovery/a0/a0_gpu_minimal.sh | sed 's/^/  /'

echo
echo "############ 7. author tree unmodified + compat layer ############"
cd /scratch/sychan552/a0_replay && git status --porcelain | head -10 | sed 's/^/  /'
echo "  (empty above = author tree clean)"
git -C /scratch/sychan552/a0_replay log -1 --format='  commit=%H %cI' 2>/dev/null
sha256sum /scratch/sychan552/a2_stage5/recovery/a0/a0_compat.py | sed 's/^/  /'

echo
echo "############ 8. executed code hashes (freeze for this round) ############"
cd /scratch/sychan552/a2_stage5
sha256sum scripts/train_backbone_966.py scripts/score_test_stage5.py \
          scripts/build_lock_stage5.py scripts/train_nlinear_966.py scripts/configs.py \
          scripts/innovation/backbones/dlinear.py scripts/innovation/backbones/patchtst.py \
          scripts/innovation/backbones/itransformer.py \
          scripts/innovation/backbones/llm_inspired.py \
          scripts/innovation/assets.py recovery/stage6/recompute_eight.py \
  | tee results/stage7/code_sha256_stage7.txt | sed 's/^/  /'

echo
echo "############ 9. data + Qwen asset identity ############"
sha256sum data/raw/national_illness_raw_paper_exact.csv | sed 's/^/  /'
$PY -c "
import sys; sys.path.insert(0,'/scratch/sychan552/a2_stage5/scripts')
from innovation import assets as AS
src, kw = AS.resolve_pretrained_source('Qwen/Qwen2.5-1.5B')
print('  qwen source:', src); print('  qwen kwargs:', kw)
" | sed 's/^/  /'
