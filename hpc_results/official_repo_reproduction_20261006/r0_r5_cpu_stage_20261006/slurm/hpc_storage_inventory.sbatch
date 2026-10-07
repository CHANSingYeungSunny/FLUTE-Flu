#!/bin/bash
#SBATCH --job-name=hpc_inventory
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r0_r5_cpu_stage_20261006/logs/inv_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r0_r5_cpu_stage_20261006/logs/inv_%j.err
#
# READ-ONLY HPC storage inventory. CPU-only, ZERO GPU-hours.
#
# The user authorised an EVIDENCE-BASED cleanup, explicitly NOT blanket deletion.
# This job only MEASURES. It deletes nothing.
set -uo pipefail
OUT=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r0_r5_cpu_stage_20261006/inventory
mkdir -p "$OUT"
H=/gpfs1/home/sychan552
S=/gpfs1/scratch/sychan552
[[ "$(hostname)" == hpclogin* ]] && { echo REFUSING; exit 3; }
echo "[inv] host=$(hostname) job=${SLURM_JOB_ID} start=$(date -u +%FT%TZ)"

echo "=== 1. quotas ==="
mmlsquota -u sychan552 > "$OUT/quota.txt" 2>&1; cat "$OUT/quota.txt"

echo "=== 2. top-level inventory (home + scratch) ==="
{
  printf 'fs\ttop_level\tbytes\tfiles\tlatest_mtime\n'
  for base in "$H" "$S"; do
    fs=$([ "$base" = "$H" ] && echo home || echo scratch)
    for d in "$base"/*; do
      [ -e "$d" ] || continue
      b=$(du -sb "$d" 2>/dev/null | awk '{print $1}')
      n=$(find "$d" -type f 2>/dev/null | wc -l)
      m=$(find "$d" -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1)
      m=$( [ -n "$m" ] && date -u -d "@${m%%.*}" +%FT%TZ 2>/dev/null || echo unknown )
      printf '%s\t%s\t%s\t%s\t%s\n' "$fs" "$d" "${b:-0}" "$n" "$m"
    done
  done
} > "$OUT/top_level.tsv" 2>/dev/null
sort -t$'\t' -k3,3rn "$OUT/top_level.tsv" | head -30

echo "=== 3. cache directories (REGENERABLE_CACHE candidates) ==="
{
  for p in "$H/.cache/huggingface" "$H/.cache/torch" "$H/.cache/pip" "$H/.cache" \
           "$H/.conda/pkgs" "$S/.cache"; do
    [ -e "$p" ] && printf '%s\t%s\n' "$p" "$(du -sh "$p" 2>/dev/null | cut -f1)"
  done
} | tee "$OUT/caches.tsv"

echo "=== 4. scratch big consumers ==="
du -sh "$S"/* 2>/dev/null | sort -rh > "$OUT/scratch_top.tsv"
head -20 "$OUT/scratch_top.tsv"

echo "=== 5. *.part / partial / stale temp (FAILED_RUN_TEMPORARY candidates) ==="
find "$H" "$S" -name '*.part' -o -name '*.partial' -o -name '*.tmp' 2>/dev/null \
  | head -50 > "$OUT/partial_files.txt"
wc -l < "$OUT/partial_files.txt"

echo "=== 6. empty directories ==="
find "$H" "$S" -type d -empty 2>/dev/null | head -50 > "$OUT/empty_dirs.txt"
wc -l < "$OUT/empty_dirs.txt"

echo "=== 7. symlink / hard-link census (link targets are UNSAFE_TO_DELETE) ==="
find "$H" "$S" -type l 2>/dev/null | wc -l > "$OUT/n_symlinks.txt"
find "$H" "$S" -type f -links +1 2>/dev/null | wc -l > "$OUT/n_hardlinks.txt"
echo "symlinks=$(cat "$OUT/n_symlinks.txt") hardlinked=$(cat "$OUT/n_hardlinks.txt")"

echo "=== 8. protected asset census ==="
{
  echo "# author repository"
  git -C /scratch/sychan552/a0_replay rev-parse HEAD 2>/dev/null
  du -sb /scratch/sychan552/a0_replay 2>/dev/null | awk '{print "a0_replay_bytes="$1}'
  echo "# innovation_deploy_root_v3_* (UNSAFE_TO_DELETE)"
  ls -d "$S"/innovation_deploy_root_v3_* 2>/dev/null | wc -l
  du -sb "$S"/innovation_deploy_root_v3_* 2>/dev/null | awk '{s+=$1} END{print "v3_family_bytes="s}'
  echo "# project result trees"
  for d in "$H/official_repo_reproduction_20261006" "$S/a2_stage5" "$S/CHATTIME"; do
    [ -e "$d" ] && printf '%s\t%s\n' "$d" "$(du -sb "$d" 2>/dev/null | awk '{print $1}')"
  done
} | tee "$OUT/protected_census.txt"

echo "=== 9. fresh quota AFTER the scan (did anything change?) ==="
mmlsquota -u sychan552 2>&1 | tail -3

echo "[inv] end=$(date -u +%FT%TZ)  wrote $OUT"
ls -la "$OUT" | tail -15