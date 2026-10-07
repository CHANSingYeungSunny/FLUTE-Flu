#!/bin/bash
# ==========================================================================
# d13_inventory.sh — LIGHTWEIGHT, READ-ONLY storage inventory for the D13
# quota remediation. Runs on the login node: only stat/du/find/awk, no
# model or data computation, nothing is modified.
#
# Outputs (all under /tmp/d13/):
#   big_files.tsv        size<TAB>path        for files > 50 MiB under durable
#   durable_entries.tsv  size<TAB>name        for every durable/screening entry
#   scratch_roots.tsv    size<TAB>name        for every scratch top-level entry
#   summary.txt          the aggregate figures
# ==========================================================================
set -uo pipefail
OUT=/tmp/d13
mkdir -p "$OUT"

DUR=/home/sychan552/innovation_durable
SCR=/gpfs1/scratch/sychan552

# ---- 1. every durable/screening entry with its size -----------------------
cd "$DUR/screening" || exit 1
for e in *; do
  [ -e "$e" ] || continue
  printf '%s\t%s\n' "$(du -sb "$e" 2>/dev/null | cut -f1)" "$e"
done > "$OUT/durable_entries.tsv"

# ---- 2. every file larger than 50 MiB under durable ----------------------
find "$DUR" -type f -size +50M -print0 2>/dev/null | while IFS= read -r -d '' f; do
  printf '%s\t%s\n' "$(stat -c %s "$f")" "$f"
done > "$OUT/big_files.tsv"

# ---- 3. scratch top-level roots ------------------------------------------
cd "$SCR" || exit 1
for e in *; do
  [ -e "$e" ] || continue
  printf '%s\t%s\n' "$(du -sb "$e" 2>/dev/null | cut -f1)" "$e"
done > "$OUT/scratch_roots.tsv"

# ---- 4. aggregates -------------------------------------------------------
W1_N=$(grep -c '__w1$' "$OUT/durable_entries.tsv" || true)
LG_N=$(grep -vc '__w1$' "$OUT/durable_entries.tsv" || true)
W1_B=$(awk -F'\t' '/__w1$/ {s+=$1} END {print s+0}' "$OUT/durable_entries.tsv")
LG_B=$(awk -F'\t' '$2 !~ /__w1$/ {s+=$1} END {print s+0}' "$OUT/durable_entries.tsv")
BF_W1_N=$(awk -F'\t' '$2 ~ /__w1/ {n++} END {print n+0}' "$OUT/big_files.tsv")
BF_LG_N=$(awk -F'\t' '$2 !~ /__w1/ {n++} END {print n+0}' "$OUT/big_files.tsv")
BF_W1_B=$(awk -F'\t' '$2 ~ /__w1/ {s+=$1} END {print s+0}' "$OUT/big_files.tsv")
BF_LG_B=$(awk -F'\t' '$2 !~ /__w1/ {s+=$1} END {print s+0}' "$OUT/big_files.tsv")

{
  echo "durable_wave1_entries=$W1_N"
  echo "durable_legacy_entries=$LG_N"
  echo "durable_wave1_bytes=$W1_B"
  echo "durable_legacy_bytes=$LG_B"
  echo "bigfiles_wave1_count=$BF_W1_N"
  echo "bigfiles_legacy_count=$BF_LG_N"
  echo "bigfiles_wave1_bytes=$BF_W1_B"
  echo "bigfiles_legacy_bytes=$BF_LG_B"
  echo "big_threshold_bytes=52428800"
  echo "---big file basenames (families)---"
  awk -F'\t' '{n=split($2,a,"/"); print a[n-2]}' "$OUT/big_files.tsv" | sort | uniq -c | sort -rn
  echo "---sizes by family (MiB, min/max/mean)---"
  awk -F'\t' '{n=split($2,a,"/"); fam=a[n-2]; s[fam]+=$1; c[fam]++; if($1>mx[fam]||mx[fam]==""){mx[fam]=$1} if($1<mn[fam]||mn[fam]==""){mn[fam]=$1} } END {for (f in s) printf "%s n=%d min=%.1f max=%.1f mean=%.1f\n", f, c[f], mn[f]/1048576, mx[f]/1048576, s[f]/c[f]/1048576}' "$OUT/big_files.tsv" | sort
} > "$OUT/summary.txt"

echo "INVENTORY_OK dir=$OUT"
ls -l "$OUT"
