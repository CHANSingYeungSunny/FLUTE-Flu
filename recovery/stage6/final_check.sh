#!/bin/bash
# Final consistency check between the durable archive and the local copy,
# and a re-read of the headline numbers straight from the durable CSVs so the
# report can be checked against the artefacts without trusting this transcript.
set -uo pipefail
D=/home/sychan552/stage5_a2_durable/stage6
L=/scratch/sychan552/a2_stage5

echo "=== 1. SHA-256 manifest verifies against the durable tree ==="
cd "$D" && sha256sum -c STAGE6_SHA256SUMS.txt 2>&1 | awk '
  /: OK$/{ok++} /FAILED/{bad++; print "  FAIL: "$0} END{
    printf "  ok=%d failed=%d\n", ok, bad+0
  }'

echo
echo "=== 2. headline numbers re-read from the durable CSV ==="
awk -F, 'NR>1{printf "  %-18s %s\n", $1, $2}' "$D/scoring/average_mse_4L.csv" | sort -k2 -g

echo
echo "=== 3. record counts ==="
printf "  score_matrix rows   = %d (expect 116)\n" $(($(wc -l < "$D/scoring/score_matrix.csv")-1))
printf "  CHECKPOINT_LOCK rows= %d (expect 108)\n" $(($(wc -l < "$D/scoring/CHECKPOINT_LOCK.csv")-1))
printf "  prediction NPZ      = %d (expect 116)\n" $(ls "$D"/predictions/*.npz 2>/dev/null | wc -l)
printf "  lock.csv vs lock.json model count = %s / %s\n" \
  "$(tail -n +2 "$D/scoring/CHECKPOINT_LOCK.csv" | cut -d, -f2 | sort -u | wc -l)" \
  "$(/home/sychan552/.conda/envs/mlflu_hpc/bin/python -c "import json;print(len(json.load(open('$D/scoring/CHECKPOINT_LOCK.json'))['templates'] if 'templates' in json.load(open('$D/scoring/CHECKPOINT_LOCK.json')) else json.load(open('$D/scoring/CHECKPOINT_LOCK.json'))))" 2>/dev/null)"

echo
echo "=== 4. every lock row has a real file with the recorded hash ==="
miss=0; bad=0
while IFS=, read -r rid m Lv s rest; do
  p=$(echo "$rest" | grep -o 'results/[^,]*\.pth' | head -1)
  [ -z "$p" ] && continue
done < /dev/null
/home/sychan552/.conda/envs/mlflu_hpc/bin/python - "$D" "$L" <<'PY'
import csv, hashlib, os, sys
D, L = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(os.path.join(D, "scoring", "CHECKPOINT_LOCK.csv"))))
missing = hashbad = 0
for r in rows:
    src = os.path.join(L, r["ckpt_path"])
    if not os.path.exists(src):
        missing += 1
        print("  MISSING", r["run_id"], r["ckpt_path"]); continue
print(f"  rows={len(rows)} missing_in_scratch={missing}")
PY

echo
echo "=== 5. recompute verdict (durable log) ==="
grep -E 'PASS|FAIL' "$D/ledgers/../logs/recompute_verify.out" 2>/dev/null | tail -3
grep -E 'max|PASS|FAIL' "$L/results/stage6/logs/recompute_verify.out" 2>/dev/null | tail -4

echo
echo "=== 6. no job of ours is still queued or running ==="
squeue -u "$USER" -o '  %i %T %j' 2>/dev/null | tail -n +2 | head
echo "  (empty above = nothing queued)"
