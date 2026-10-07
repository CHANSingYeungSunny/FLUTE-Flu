#!/bin/bash
#SBATCH --job-name=audit_hash
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=04:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/postrun_audit_20261006/logs/hash_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/postrun_audit_20261006/logs/hash_%j.err
#
# CPU-ONLY, ZERO GPU-HOURS, STRICTLY READ-ONLY.
#
# Purpose: decide whether the large checkpoint-like files in the HISTORICAL
# Track-B deployment family (innovation_deploy_root_v3_*) are genuinely
# byte-identical, or merely same-size/same-name. The brief forbids classifying
# duplicates by filename or directory name alone, and forbids copying a large
# checkpoint merely to compare it - so we hash in place, read-only.
#
# Nothing is deleted, moved, renamed or written outside the out/ directory.
set -uo pipefail

BASE=/gpfs1/scratch/sychan552
OUT=/gpfs1/home/sychan552/official_repo_reproduction_20261006/postrun_audit_20261006/out
mkdir -p "$OUT"

echo "[hash] host=$(hostname) job=${SLURM_JOB_ID} start=$(date -u +%FT%TZ)"
if [[ "$(hostname)" == hpclogin* ]]; then echo "[hash] REFUSING login node"; exit 3; fi

# Full SHA-256 of every checkpoint-like file, plus inode and link count.
# 594 files / ~202 GiB - a sequential read on GPFS.
find ${BASE}/innovation_deploy_root_v3_* -type f \
     \( -name '*.safetensors' -o -name '*.pt' -o -name '*.bin' -o -name '*.pth' \) \
     -print0 2>/dev/null | \
while IFS= read -r -d '' f; do
  sz=$(stat -c '%s' "$f" 2>/dev/null)
  ino=$(stat -c '%i' "$f" 2>/dev/null)
  nl=$(stat -c '%h' "$f" 2>/dev/null)
  h=$(sha256sum "$f" 2>/dev/null | cut -d' ' -f1)
  printf '%s\t%s\t%s\t%s\t%s\n' "$sz" "$ino" "$nl" "${h:-HASH_FAILED}" "$f"
done > "$OUT/checkpoint_sha256.tsv"

echo "[hash] hashed $(wc -l < $OUT/checkpoint_sha256.tsv) files"

# Group by hash to get the TRUE duplicate structure.
sort -t$'\t' -k4,4 "$OUT/checkpoint_sha256.tsv" | \
awk -F'\t' '{ if ($4==prev) { n++; bytes=$1 } else { if (n>1) printf "%s\t%d\t%d\t%s\n", prev, n, n*bytes, size; prev=$4; n=1; bytes=$1; size=$1 } }
     END { if (n>1) printf "%s\t%d\t%d\t%s\n", prev, n, n*bytes, size }' \
  > "$OUT/checkpoint_hash_duplicate_groups.tsv"
echo "[hash] identical-content groups: $(wc -l < $OUT/checkpoint_hash_duplicate_groups.tsv)"

# Reclaimable bytes if every duplicate group were collapsed to one copy.
awk -F'\t' '{ tot += ($2-1)*$4 } END { printf "reclaimable_bytes_if_collapsed=%d\n", tot }' \
  "$OUT/checkpoint_hash_duplicate_groups.tsv" > "$OUT/checkpoint_dedup_summary.txt"
awk -F'\t' '{ u += $1 } END { printf "unique_bytes=%d\n", u }' \
  "$OUT/checkpoint_hash_duplicate_groups.tsv" >> "$OUT/checkpoint_dedup_summary.txt"
cat "$OUT/checkpoint_dedup_summary.txt"

# Same treatment restricted to the Qwen artifacts (the storage driver).
grep -i qwen "$OUT/checkpoint_sha256.tsv" > "$OUT/qwen_checkpoint_sha256.tsv" 2>/dev/null
echo "[hash] qwen checkpoint files: $(wc -l < $OUT/qwen_checkpoint_sha256.tsv)"
sort -t$'\t' -k4,4 "$OUT/qwen_checkpoint_sha256.tsv" | \
awk -F'\t' '{ c[$4]++; s[$4]=$1 } END { for (h in c) if (c[h]>1) printf "%s\t%d\t%d\n", h, c[h], c[h]*s[h] }' \
  | sort -k3,3rn > "$OUT/qwen_duplicate_groups.tsv"
awk -F'\t' '{ t += ($2-1)*($3/$2) } END { printf "qwen_reclaimable_bytes_if_collapsed=%d\n", t }' \
  "$OUT/qwen_duplicate_groups.tsv" >> "$OUT/checkpoint_dedup_summary.txt"
tail -1 "$OUT/checkpoint_dedup_summary.txt"

# Small non-checkpoint files: hash them too so "duplicate" claims about code,
# configs, CSVs and reports can also be evidence-based.
find ${BASE}/innovation_deploy_root_v3_* -type f -size -4M \
     \( -name '*.py' -o -name '*.json' -o -name '*.sh' -o -name '*.csv' -o -name '*.md' \) \
     -print0 2>/dev/null | \
while IFS= read -r -d '' f; do
  sz=$(stat -c '%s' "$f" 2>/dev/null)
  h=$(sha256sum "$f" 2>/dev/null | cut -d' ' -f1)
  printf '%s\t%s\t%s\n' "$sz" "${h:-HASH_FAILED}" "$f"
done > "$OUT/small_file_sha256.tsv"
echo "[hash] hashed $(wc -l < $OUT/small_file_sha256.tsv) small files"

awk -F'\t' '{ c[$2]++; s[$2]=$1 } END { for (h in c) if (c[h]>1) n++ ; printf "duplicate_small_file_groups=%d\n", n }' \
  "$OUT/small_file_sha256.tsv" > "$OUT/small_file_duplicate_summary.txt"
cat "$OUT/small_file_duplicate_summary.txt"

echo "[hash] done end=$(date -u +%FT%TZ)"
ls -la "$OUT" | tail -12