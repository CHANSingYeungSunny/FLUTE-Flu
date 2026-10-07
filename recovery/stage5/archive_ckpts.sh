#!/bin/bash
#SBATCH --job-name=a2_ckpt_archive
#SBATCH --partition=stingy
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:40:00
#SBATCH --output=/home/sychan552/stage5_a2_durable/archive_log_%j.out
#SBATCH --error=/home/sychan552/stage5_a2_durable/archive_log_%j.err
#
# Stage 5 A2 — archive the 36 locked checkpoints out of scratch into the
# persistent home location, then verify every file byte-for-byte against the
# SHA-256 recorded in the ORIGINAL first lock
# (CHECKPOINT_LOCK_first_20260925T161329Z.json, written 16:13:29Z, before any
# Test inference). The originals in scratch are kept until this passes.
#
# CPU-only: NO --gres request, so this consumes ZERO GPU-hours. `coursework` is not
# available to this account and `batch` demands a larger CPU/mem floor, so the
# CPU-only `stingy` submission path is used (verified to be accepted).
set -euo pipefail

SRC=/scratch/sychan552/a2_stage5/results/stage5
DST=/home/sychan552/stage5_a2_durable/checkpoints/author_966
LOCK=/home/sychan552/stage5_a2_durable/scoring/CHECKPOINT_LOCK_first_20260925T161329Z.json

echo "[archive] start $(date -u +%FT%TZ) host=$(hostname)"
mkdir -p "$DST"
[ -f "$LOCK" ] || { echo "[archive] FATAL: first-lock file missing" >&2; exit 2; }

echo "[archive] step 1 — copy 36 checkpoints (5.0 GB)"
for m in miflu notext nlinear; do
  mkdir -p "$DST/$m"
  cp -p "$SRC/ckpt/author_966/$m"/*.pth "$DST/$m/"
  echo "  copied $m: $(ls -1 "$DST/$m" | wc -l) files"
done

echo "[archive] step 2 — copy the non-weight A2 artefacts that live only in scratch"
mkdir -p /home/sychan552/stage5_a2_durable/per_run
cp -p "$SRC/author_966/miflu/metrics.csv"                 /home/sychan552/stage5_a2_durable/per_run/ 2>/dev/null || true
cp -p "$SRC/author_966/miflu"/training_miflu_log_*.txt     /home/sychan552/stage5_a2_durable/per_run/ 2>/dev/null || true
cp -p "$SRC/author_966/notext/training_ablation.log"       /home/sychan552/stage5_a2_durable/per_run/ 2>/dev/null || true
cp -rp "$SRC/author_966/notext/horizon_L24"                /home/sychan552/stage5_a2_durable/per_run/notext_horizon_L24 2>/dev/null || true
cp -rp "$SRC/author_966/notext/horizon_L36"                /home/sychan552/stage5_a2_durable/per_run/notext_horizon_L36 2>/dev/null || true
cp -rp "$SRC/author_966/notext/horizon_L48"                /home/sychan552/stage5_a2_durable/per_run/notext_horizon_L48 2>/dev/null || true
cp -rp "$SRC/author_966/notext/horizon_L60"                /home/sychan552/stage5_a2_durable/per_run/notext_horizon_L60 2>/dev/null || true

echo "[archive] step 3 — verify every archived file against the FIRST lock"
/home/sychan552/.conda/envs/mlflu_hpc/bin/python - <<'PY'
import hashlib, json, os, sys
LOCK = "/home/sychan552/stage5_a2_durable/scoring/CHECKPOINT_LOCK_first_20260925T161329Z.json"
DST  = "/home/sychan552/stage5_a2_durable/checkpoints/author_966"
lock = json.load(open(LOCK))
def sha256(p, chunk=1 << 22):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()
ok = bad = miss = 0
for fit in lock["fits"]:
    rel = fit["ckpt_path"].split("ckpt/author_966/")[-1]      # e.g. miflu/best_miflu_L24_seed42.pth
    dst = os.path.join(DST, rel)
    if not os.path.exists(dst):
        print(f"  MISSING  {fit['run_id']}  {rel}"); miss += 1; continue
    if os.path.getsize(dst) != fit["ckpt_bytes"]:
        print(f"  SIZE     {fit['run_id']}"); bad += 1; continue
    d = sha256(dst)
    if d != fit["ckpt_sha256"]:
        print(f"  SHA FAIL {fit['run_id']}  {d} != {fit['ckpt_sha256']}"); bad += 1; continue
    ok += 1
print(f"[archive] verify: ok={ok} sha_fail={bad} missing={miss} of {len(lock['fits'])}")
if bad or miss or ok != 36:
    sys.exit(3)
PY

echo "[archive] step 4 — re-verify the result NPZs / scaler / manifest are readable"
/home/sychan552/.conda/envs/mlflu_hpc/bin/python - <<'PY'
import glob, json, sys
import numpy as np, pandas as pd
D = "/home/sychan552/stage5_a2_durable/scoring/predictions"
f = sorted(glob.glob(D + "/pred_*.npz"))
assert len(f) == 44, f"expected 44 artefacts, found {len(f)}"
tot = 0.0
for p in f:
    z = np.load(p, allow_pickle=False)
    tot += float(np.mean((z["pred"] - z["target"]) ** 2))
    assert z["pred"].shape == z["target"].shape
s = json.load(open(D + "/scaler_train_only.json"))
m = pd.read_csv(D + "/test_manifest.csv")
print(f"[archive] artefacts OK: {len(f)} NPZ readable, mean mse_all over all = {tot/len(f):.6f}")
print(f"[archive] scaler OK: {len(s['var_cols'])} vars, fitted on {s['fit_on']}")
print(f"[archive] manifest OK: {len(m)} origin rows")
PY

echo "[archive] step 5 — write the archive manifest"
cd /home/sychan552/stage5_a2_durable
find checkpoints -type f -exec sha256sum {} + | sort -k2 > CHECKPOINT_ARCHIVE_SHA256SUMS.txt
du -sh checkpoints
wc -l CHECKPOINT_ARCHIVE_SHA256SUMS.txt
echo "[archive] PASS  $(date -u +%FT%TZ)"
