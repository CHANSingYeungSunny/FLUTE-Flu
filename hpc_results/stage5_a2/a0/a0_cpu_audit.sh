#!/bin/bash
#SBATCH --job-name=a0_cpu_audit
#SBATCH --partition=stingy
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=/scratch/sychan552/a2_stage5/a0_cpu_audit_%j.out
#SBATCH --error=/scratch/sychan552/a2_stage5/a0_cpu_audit_%j.err
#
# A0 (released-code diagnostic replay) — CPU-only precheck. NO GPU request, so
# this costs ZERO GPU-hours. It establishes exactly what blocks a minimal A0
# run BEFORE any GPU time is spent, per the recovery plan §3.
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
A0=/scratch/sychan552/a0_replay
echo "[a0] host=$(hostname) $(date -u +%FT%TZ)"

echo "=== 1. author repo tree (pinned commit 6ed2101) ==="
ls -1 "$A0" 2>/dev/null || { echo "MISSING $A0"; exit 2; }
cd "$A0" || exit 2
git log -1 --format='commit=%H%ndate=%cI' 2>/dev/null || echo "(no .git — vendored copy)"

echo
echo "=== 2. data + embedding assets required by the released defaults ==="
$PY - <<'PY'
import os
A0 = "/scratch/sychan552/a0_replay"
need = ["dataset/illness/national_illness.csv",
        "dataset/illness/national_illness_orig.csv"]
for L in (24, 36, 48, 60):
    need.append(f"dataset/illness/text_emb/text_emb_label_0507_{L}.txt")
for f in need:
    p = os.path.join(A0, f)
    print(f"  {'OK ' if os.path.exists(p) else 'MISSING'} {f}"
          + (f"  ({os.path.getsize(p)} bytes)" if os.path.exists(p) else ""))
# the released code imports a top-level `embed` module
print(f"  {'OK ' if os.path.exists(os.path.join(A0,'embed.py')) else 'MISSING'} embed.py"
      "   (imported by models/GPT4TS_lora.py line 10)")
PY

echo
echo "=== 3. python dependency availability in mlflu_hpc ==="
$PY - <<'PY'
import importlib
for m in ("torch", "transformers", "peft", "einops", "numpy", "pandas", "sklearn"):
    try:
        mod = importlib.import_module(m)
        print(f"  OK      {m:<12} {getattr(mod,'__version__','?')}")
    except Exception as e:
        print(f"  MISSING {m:<12} {type(e).__name__}: {e}")
PY

echo
echo "=== 4. can the released entry point even be imported? ==="
$PY - <<'PY'
import os, sys, traceback
A0 = "/scratch/sychan552/a0_replay"
sys.path.insert(0, A0)
os.chdir(A0)                      # the released code uses RELATIVE paths
for mod in ("utils.tools", "utils.metrics", "utils.timefeatures",
            "data_provider.data_factory", "models.GPT4TS_lora"):
    try:
        __import__(mod)
        print(f"  OK      import {mod}")
    except Exception as e:
        print(f"  FAIL    import {mod}: {type(e).__name__}: {e}")
PY

echo
echo "=== 5. released-code split arithmetic on the 966-row file (no training) ==="
$PY - <<'PY'
import numpy as np, pandas as pd
A0 = "/scratch/sychan552/a0_replay"
df = pd.read_csv(A0 + "/dataset/illness/national_illness.csv")
n = len(df); seq_len, pred_len = 104, 24
num_train = int(n * 0.7); num_test = int(n * 0.2); num_vali = n - num_train - num_test
b1 = [0, num_train - seq_len, n - num_test - seq_len]
b2 = [num_train, num_train + num_vali, n]
print(f"  rows={n}  num_train={num_train} num_vali={num_vali} num_test={num_test}")
print(f"  borders1={b1}  borders2={b2}")
cols = list(df.columns); cols.remove("OT")
print(f"  header={list(df.columns)}  enc_in(data cols)={len(cols)}")
for i, nm in enumerate(("train", "val", "test")):
    ln = (b2[i] - b1[i]) - seq_len - pred_len + 1
    mult = 1 if nm == "test" else len(cols)   # released __len__ multiplies ONLY for train/val
    print(f"  {nm:<5} slice_len={b2[i]-b1[i]:>4}  released __len__ = {ln} * {mult} = {ln*mult}"
          f"   (A2 strict train/val/test for L=24 = 549/74/170)")
print("  => released Test covers feat_id = index // tot_len = 0 for every index")
PY

echo
echo "=== 6. released default hyperparameters actually in argparse ==="
grep -n -E "add_argument\('--(multimodal|train_epochs|learning_rate|batch_size|itr|gpt_layers|seq_len|pred_len|lora_r|PEFT|freeze|embed|textmodel|backbone|patch_size|stride|target|features)'" \
     "$A0/main_ILI_lora.py" | sed 's/^/  /'

echo
echo "=== 7. does the released code read Test during training? (static) ==="
grep -n -E "test\(|vali\(|early_stopping|best.*mse|min_mse|torch.save" "$A0/main_ILI_lora.py" | sed 's/^/  /' | head -40

echo
echo "[a0] cpu audit done $(date -u +%FT%TZ)"
