#!/bin/bash
# Stage 6 — publish the A0 / A1 / eight-model preparation artefacts to the
# persistent home location, then re-verify the A2 checkpoint archive.
# CPU-only (invoked from the login node; file copy of small text artefacts only,
# the 5 GB checkpoint archive is NOT touched here).
set -euo pipefail
SRC=/scratch/sychan552/a2_stage5
DST=/home/sychan552/stage5_a2_durable
mkdir -p "$DST"/{logs,code,stage6,a0,a1}

echo "[pub6] copying stage-6 / a0 / a1 artefacts"
cp -p "$SRC"/recovery/stage6/*.md              "$DST/stage6/" 2>/dev/null || true
cp -p "$SRC"/recovery/stage6/*.sh              "$DST/stage6/" 2>/dev/null || true
cp -p "$SRC"/recovery/stage6/*.py              "$DST/stage6/" 2>/dev/null || true
cp -p "$SRC"/recovery/stage6/*.json            "$DST/stage6/" 2>/dev/null || true
cp -p "$SRC"/recovery/a0/*.sh                  "$DST/a0/"     2>/dev/null || true
cp -p "$SRC"/recovery/a0/*.py                  "$DST/a0/"     2>/dev/null || true
cp -p "$SRC"/recovery/a0/*.md                  "$DST/a0/"     2>/dev/null || true
cp -p "$SRC"/recovery/a1/*.md                  "$DST/a1/"     2>/dev/null || true

echo "[pub6] copying the stage-6 code + the executed a0 logs"
for f in train_backbone_966.py score_test_stage5.py build_lock_stage5.py; do
  cp -p "$SRC/scripts/$f" "$DST/code/" 2>/dev/null || true
done
for j in 586934 586942 586945 586947 586950 586962 586982 586990 586995 587002 587011; do
  for p in "$SRC/logs/${j}_archive_log" "$SRC/logs/a0_${j}" "$SRC/logs/s6_${j}" \
           "$SRC/a0_cpu_audit_${j}" "$SRC/a0_blockers_${j}"; do
    [ -f "${p}.out" ] && cp -p "${p}.out" "$DST/logs/" 2>/dev/null || true
    [ -f "${p}.err" ] && cp -p "${p}.err" "$DST/logs/" 2>/dev/null || true
  done
done
# the CPU-only job log actually lives in the home dir already
cp -p "$DST/archive_log_586934.out" "$DST/logs/" 2>/dev/null || true
cp -p "$DST/archive_log_586934.err" "$DST/logs/" 2>/dev/null || true

echo "[pub6] re-verifying the A2 checkpoint archive (36 files) against the FIRST lock"
/home/sychan552/.conda/envs/mlflu_hpc/bin/python - <<'PY'
import hashlib, json, os, sys
DST = "/home/sychan552/stage5_a2_durable"
lock = json.load(open(os.path.join(DST, "scoring",
                                  "CHECKPOINT_LOCK_first_20260925T161329Z.json")))
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
    rel = fit["ckpt_path"].split("ckpt/author_966/")[-1]
    p = os.path.join(DST, "checkpoints", "author_966", rel)
    if not os.path.exists(p):
        print("  MISSING", rel); miss += 1; continue
    if os.path.getsize(p) != fit["ckpt_bytes"]:
        print("  SIZE", rel); bad += 1; continue
    if sha256(p) != fit["ckpt_sha256"]:
        print("  SHA FAIL", rel); bad += 1; continue
    ok += 1
print(f"[pub6] archive verify: ok={ok} sha_fail={bad} missing={miss} of {len(lock['fits'])}")
sys.exit(0 if (bad == 0 and miss == 0 and ok == 36) else 3)
PY

echo "[pub6] rewriting the durable checksum manifest"
cd "$DST"
rm -f STAGE5_A2_DURABLE_SHA256SUMS.txt
find . -type f ! -name 'STAGE5_A2_DURABLE_SHA256SUMS.txt' -exec sha256sum {} + \
  | sort -k2 > STAGE5_A2_DURABLE_SHA256SUMS.txt
echo "[pub6] files=$(wc -l < STAGE5_A2_DURABLE_SHA256SUMS.txt)  size=$(du -sh . | cut -f1)"
find "$DST" -maxdepth 1 -type d | sort | sed 's/^/  /'
echo "[pub6] ok"
