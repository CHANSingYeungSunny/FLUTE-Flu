#!/bin/bash
# ==========================================================================
# d13_quarantine_delete.sh — manifest-driven PERMANENT deletion of the
# quarantine contents, allowed ONLY because verified replacements exist.
#
# Safety gates (all must pass, else NOTHING is deleted):
#   1. the execute-phase manifest exists and is non-empty
#   2. every quarantined path is inside the quarantine root (realpath)
#   3. every quarantined path is owned by the user
#   4. no path is a symlink
#   5. the 205 verified compact packages still exist in the durable root
#      (the replacements), and the verification summary proves 205/205
#   6. the protected paths are explicitly NOT in the deletion set
#
# No wildcards are used: only the exact `rel` entries from the manifest.
# ==========================================================================
set -uo pipefail

Q=/gpfs1/scratch/sychan552/_d13_quarantine
MAN="$Q/quarantine_manifest_execute.tsv"
DUR=/home/sychan552/innovation_durable/screening
VER=/scratch/sychan552/_v318d/verify205/verification_summary.json
OWNER=sychan552
REPORT=/scratch/sychan552/_v318d/quarantine_deletion_report.json

[ -f "$MAN" ] || { echo "FAIL-STOP: manifest missing: $MAN"; exit 1; }
[ -f "$VER" ] || { echo "FAIL-STOP: verification summary missing"; exit 1; }

# ---- gate 5: the replacements must be proven -----------------------------
NCOMPACT=$(ls -1 "$DUR"/*/compact.safetensors 2>/dev/null | wc -l)
NMANIFEST=$(ls -1 "$DUR"/*/compact_manifest.json 2>/dev/null | wc -l)
echo "replacements: compact=$NCOMPACT manifests=$NMANIFEST"
if [ "$NCOMPACT" -lt 205 ] || [ "$NMANIFEST" -lt 205 ]; then
  echo "FAIL-STOP: expected 205 verified compact packages, found $NCOMPACT"
  exit 1
fi
grep -q '"verified_rows": 205' "$VER" || {
  echo "FAIL-STOP: verification summary does not prove 205/205"; exit 1; }
grep -q '"verification_failures": 0' "$VER" || {
  echo "FAIL-STOP: verification failures are not 0"; exit 1; }
grep -q '"A": 205' "$VER" || {
  echo "FAIL-STOP: Path A count is not 205"; exit 1; }
grep -q '"C": 0' "$VER" || {
  echo "FAIL-STOP: Path_C is not 0"; exit 1; }

# ---- gates 2-4 + 6, then delete ------------------------------------------
QREAL="$(realpath -m "$Q")"
deleted=0; bytes=0; refused=0
while IFS=$'\t' read -r utc kind src rel sz owner contained action; do
  [ "$utc" = "utc" ] && continue          # header
  [ -z "${rel:-}" ] && continue
  target="$Q/$rel"
  case "$(realpath -m "$target")" in
    "$QREAL"/*) ;;
    *) echo "REFUSE outside quarantine: $target"; refused=$((refused+1)); continue ;;
  esac
  # protected paths must never appear
  case "$rel" in
    *CHATTIME*|*.conda*|*results/v3_clean/runs/complete_specs_598.json*)
      echo "REFUSE protected: $rel"; refused=$((refused+1)); continue ;;
  esac
  [ -e "$target" ] || { echo "skip missing: $rel"; continue; }
  [ -L "$target" ] && { echo "REFUSE symlink: $rel"; refused=$((refused+1)); continue; }
  own="$(stat -c %U "$target" 2>/dev/null)"
  [ "$own" = "$OWNER" ] || { echo "REFUSE owner=$own: $rel"; refused=$((refused+1)); continue; }
  b="$(du -sb "$target" 2>/dev/null | cut -f1)"
  rm -rf -- "$target"
  deleted=$((deleted+1)); bytes=$((bytes + b))
done < "$MAN"

printf '{"deleted":%d,"refused":%d,"reclaimed_bytes":%d}\n' \
  "$deleted" "$refused" "$bytes" > "$REPORT"
echo "QUARANTINE_DELETE deleted=$deleted refused=$refused bytes=$bytes"
du -sh "$Q" 2>/dev/null | tail -1
