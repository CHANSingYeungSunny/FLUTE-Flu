#!/bin/bash
#SBATCH --job-name=audit_readonly
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/postrun_audit_20261006/logs/audit_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/postrun_audit_20261006/logs/audit_%j.err
#
# CPU-ONLY, ZERO GPU-HOURS. This job exists because the login-node rules forbid
# substantial filesystem scanning and hashing there. It is STRICTLY READ-ONLY:
#   * no delete, move, rename, compress, truncate, write, relink
#   * no model loading, no inference, no training
#   * the only writes are its own outputs under postrun_audit_20261006/out/
#
# It inventories the HISTORICAL Track-B deployment family
# (innovation_deploy_root_v3_*), which is UNSAFE_TO_DELETE and must not be
# touched. Everything here is metadata collection.
set -uo pipefail

BASE=/gpfs1/scratch/sychan552
OUT=/gpfs1/home/sychan552/official_repo_reproduction_20261006/postrun_audit_20261006/out
mkdir -p "$OUT"

echo "[audit] host=$(hostname) job=${SLURM_JOB_ID} start=$(date -u +%FT%TZ)"
if [[ "$(hostname)" == hpclogin* ]]; then echo "[audit] REFUSING login node"; exit 3; fi

# ── 1. locate the family -----------------------------------------------------
ls -d ${BASE}/innovation_deploy_root_v3_* 2>/dev/null | sort > "$OUT/v3_dirlist.txt"
echo "[audit] v3 directories found: $(wc -l < $OUT/v3_dirlist.txt)"

# ── 2. per-directory metadata ------------------------------------------------
{
  printf 'path\towner\tgroup\tsize_apparent_h\tdu_actual_h\tfiles\tdirs\tsymlinks\tbroken_symlinks\tlatest_mtime_utc\n'
  while read -r d; do
    [ -d "$d" ] || continue
    own=$(stat -c '%U' "$d" 2>/dev/null)
    grp=$(stat -c '%G' "$d" 2>/dev/null)
    app=$(du -sh --apparent-size "$d" 2>/dev/null | cut -f1)
    act=$(du -sh "$d" 2>/dev/null | cut -f1)
    nf=$(find "$d" -type f 2>/dev/null | wc -l)
    nd=$(find "$d" -type d 2>/dev/null | wc -l)
    nl=$(find "$d" -type l 2>/dev/null | wc -l)
    bl=$(find "$d" -xtype l 2>/dev/null | wc -l)
    mt=$(find "$d" -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1)
    mt=$( [ -n "$mt" ] && date -u -d "@${mt%%.*}" +%FT%TZ 2>/dev/null || echo unknown )
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$d" "$own" "$grp" "$app" "$act" "$nf" "$nd" "$nl" "$bl" "$mt"
  done < "$OUT/v3_dirlist.txt"
} > "$OUT/v3_perdir.tsv" 2>/dev/null
echo "[audit] per-directory table written"

# ── 3. top-level content shape of every v3 directory --------------------------
{
  printf 'path\ttop_entries\n'
  while read -r d; do
    [ -d "$d" ] || continue
    ents=$(ls -1 "$d" 2>/dev/null | tr '\n' '|')
    printf '%s\t%s\n' "$d" "$ents"
  done < "$OUT/v3_dirlist.txt"
} > "$OUT/v3_toplevel.tsv"

# ── 4. largest files and largest subdirectories -------------------------------
: > "$OUT/v3_largest_files.tsv"
while read -r d; do
  [ -d "$d" ] || continue
  find "$d" -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -8 | \
    awk -v D="$d" 'BEGIN{OFS="\t"}{print D,$1,$2}' >> "$OUT/v3_largest_files.tsv"
done < "$OUT/v3_dirlist.txt"

: > "$OUT/v3_largest_subdirs.tsv"
while read -r d; do
  [ -d "$d" ] || continue
  du -sh "$d"/*/ 2>/dev/null | sort -rh | head -8 | \
    awk -v D="$d" 'BEGIN{OFS="\t"}{print D,$1,$2}' >> "$OUT/v3_largest_subdirs.tsv"
done < "$OUT/v3_dirlist.txt"

# ── 5. file-extension census (model formats, tokenizers, configs) -------------
find ${BASE}/innovation_deploy_root_v3_* -type f -printf '%f\n' 2>/dev/null | \
  sed 's/.*\.//' | sort | uniq -c | sort -rn | head -40 > "$OUT/v3_extension_census.txt"

# ── 6. checkpoint / artifact census by pattern ---------------------------------
{
  for pat in '*.safetensors' '*.bin' '*.pt' '*.pth' '*.ckpt' 'adapter_model*' \
             'adapter_config*' 'tokenizer*' 'config.json' 'generation_config*' \
             '*.csv' '*.json' '*.md' '*.py' '*.txt'; do
    n=$(find ${BASE}/innovation_deploy_root_v3_* -name "$pat" 2>/dev/null | wc -l)
    printf '%s\t%s\n' "$pat" "$n"
  done
} > "$OUT/v3_artifact_census.tsv"

# ── 7. sizes of every checkpoint-like file (for dedup analysis) ---------------
find ${BASE}/innovation_deploy_root_v3_* -type f \
     \( -name '*.safetensors' -o -name '*.bin' -o -name '*.pt' -o -name '*.pth' \
        -o -name 'adapter_model*' \) -printf '%s\t%i\t%n\t%p\n' 2>/dev/null \
  | sort -k1,1rn > "$OUT/v3_checkpoint_files.tsv"
echo "[audit] checkpoint-like files: $(wc -l < $OUT/v3_checkpoint_files.tsv)"

# ── 8. hard-link / symlink evidence -------------------------------------------
# inode counts > 1 mean real hard links
awk -F'\t' '$3 > 1 {print}' "$OUT/v3_checkpoint_files.tsv" > "$OUT/v3_hardlinked_files.tsv"
echo "[audit] hard-linked checkpoint files: $(wc -l < $OUT/v3_hardlinked_files.tsv)"

find ${BASE}/innovation_deploy_root_v3_* -type l -printf '%p\t%l\n' 2>/dev/null \
  > "$OUT/v3_symlinks.tsv"
echo "[audit] symlinks: $(wc -l < $OUT/v3_symlinks.tsv)"
awk -F'\t' '{print $2}' "$OUT/v3_symlinks.tsv" 2>/dev/null | sort | uniq -c | sort -rn \
  > "$OUT/v3_symlink_targets.txt" 2>/dev/null

# ── 9. git metadata inside the v3 family --------------------------------------
{
  while read -r d; do
    [ -d "$d/.git" ] || continue
    echo "=== $d"
    git -C "$d" remote -v 2>/dev/null | head -2
    git -C "$d" rev-parse HEAD 2>/dev/null
    git -C "$d" log -1 --format='%H %cI %s' 2>/dev/null
  done < "$OUT/v3_dirlist.txt"
} > "$OUT/v3_git_metadata.txt" 2>/dev/null

# ── 10. timestamps: does the family predate the official repo pull? ------------
{
  echo "# earliest and latest file mtime per v3 directory"
  while read -r d; do
    [ -d "$d" ] || continue
    e=$(find "$d" -type f -printf '%T@\n' 2>/dev/null | sort -n | head -1)
    l=$(find "$d" -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1)
    ed=$( [ -n "$e" ] && date -u -d "@${e%%.*}" +%FT%TZ 2>/dev/null || echo unknown )
    ld=$( [ -n "$l" ] && date -u -d "@${l%%.*}" +%FT%TZ 2>/dev/null || echo unknown )
    printf '%s\t%s\t%s\n' "$d" "$ed" "$ld"
  done < "$OUT/v3_dirlist.txt"
} > "$OUT/v3_timestamps.tsv"

# ── 11. official-repo marker dates for the comparison ------------------------
{
  echo "# author repo checkout"
  ls -ld --time-style=full-iso /scratch/sychan552/a0_replay 2>/dev/null
  git -C /scratch/sychan552/a0_replay log -1 --format='%H %cI' 2>/dev/null
  echo "# earliest appearance of the official repo checkout (mtime of .git/HEAD)"
  stat -c '%n %y' /scratch/sychan552/a0_replay/.git/HEAD 2>/dev/null
  echo "# a0_replay file count"
  find /scratch/sychan552/a0_replay -maxdepth 1 2>/dev/null | wc -l
} > "$OUT/official_repo_markers.txt" 2>/dev/null

# ── 12. total apparent vs actual for the whole family -------------------------
{
  echo "family_apparent_bytes=$(du -sb --apparent-size ${BASE}/innovation_deploy_root_v3_* 2>/dev/null | awk '{s+=$1} END{print s}')"
  echo "family_actual_bytes=$(du -sb ${BASE}/innovation_deploy_root_v3_* 2>/dev/null | awk '{s+=$1} END{print s}')"
  echo "family_file_count=$(find ${BASE}/innovation_deploy_root_v3_* -type f 2>/dev/null | wc -l)"
  echo "scratch_user_total_bytes=$(du -sb ${BASE} 2>/dev/null | awk '{print $1}')"
} > "$OUT/v3_family_totals.txt"

# ── 13. quota snapshot ---------------------------------------------------------
mmlsquota -u sychan552 > "$OUT/quota_snapshot.txt" 2>&1

# ── 14. sacct GPU ledger since 2026-09-26 (verification of the prior total) ---
sacct -S 2026-09-26 -X -P -o JobID,JobName,Partition,State,Elapsed,AllocTRES \
  > "$OUT/sacct_since_0926.psv" 2>/dev/null
sacct -S 2026-09-26 -X -P -o JobID,JobName,Partition,State,Elapsed,AllocTRES \
  | grep -E 'gres/gpu' > "$OUT/sacct_gpu_jobs.psv" 2>/dev/null
echo "[audit] gpu jobs since 0926: $(wc -l < $OUT/sacct_gpu_jobs.psv)"

echo "[audit] done end=$(date -u +%FT%TZ)"
ls -la "$OUT" | tail -30