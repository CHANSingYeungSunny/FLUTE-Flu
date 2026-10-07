#!/bin/bash
# ==========================================================================
# d15_quarantine_staging.sh — quarantine the D15 stale staging leftover.
#
# The failed finalize for baseline__last_value_naive__L24__seedna__w1 left an
# UNPUBLISHED staging directory (<key>.staging) inside the durable root.
# It must be preserved as evidence but never promoted to a final package.
#
# Same audited contract as d13_quarantine.sh (owner + realpath containment +
# symlink refusal, two phases). Separate quarantine root per defect.
# ==========================================================================
set -uo pipefail

MODE="${1:---dry-run}"
CAND="${2:-}"
[ -n "$CAND" ] || { echo "usage: $0 --dry-run|--execute <candidates.tsv>"; exit 2; }
[ -f "$CAND" ] || { echo "candidate list not found: $CAND"; exit 2; }

Q=/gpfs1/scratch/sychan552/_d15_quarantine
ALLOWED="$(realpath -m /home/sychan552/innovation_durable)"
OWNER=sychan552
SUFFIX="${MODE#--}"
MAN="$Q/quarantine_manifest_${SUFFIX}.tsv"

mkdir -p "$Q"
[ -f "$MAN" ] || printf 'utc\tkind\tsrc\trel\tbytes\towner\tcontained\taction\n' > "$MAN"

n_ok=0; n_ref=0; total=0
while IFS=$'\t' read -r kind path; do
  [ -z "${kind:-}" ] && continue
  [ -z "${path:-}" ] && continue
  case "$kind" in
    file|dir) ;;
    *) echo "REFUSE bad kind=$kind" >&2; n_ref=$((n_ref+1)); continue ;;
  esac
  if [ ! -e "$path" ]; then
    echo "REFUSE missing: $path" >&2; n_ref=$((n_ref+1)); continue
  fi
  if [ -L "$path" ]; then
    echo "REFUSE symlink: $path" >&2; n_ref=$((n_ref+1)); continue
  fi
  own="$(stat -c %U "$path" 2>/dev/null || echo UNKNOWN)"
  if [ "$own" != "$OWNER" ]; then
    echo "REFUSE owner=$own: $path" >&2; n_ref=$((n_ref+1)); continue
  fi
  rp="$(realpath -m "$path")"
  case "$rp" in
    "$ALLOWED"/*) ;;
    *) echo "REFUSE outside allowed root: $rp" >&2; n_ref=$((n_ref+1)); continue ;;
  esac
  sz="$(du -sb "$rp" 2>/dev/null | cut -f1)"
  rel="${rp#$ALLOWED/}"
  total=$((total + sz))
  if [ "$MODE" = "--execute" ]; then
    dest="$Q/$rel"
    mkdir -p "$(dirname "$dest")"
    mv "$rp" "$dest"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$kind" "$rp" "$rel" "$sz" "$own" yes moved >> "$MAN"
  else
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$kind" "$rp" "$rel" "$sz" "$own" yes dry_run >> "$MAN"
  fi
  n_ok=$((n_ok + 1))
done < "$CAND"

echo "QUARANTINE mode=$MODE accepted=$n_ok refused=$n_ref bytes=$total"
echo "QUARANTINE manifest=$MAN"
du -sh "$Q" 2>/dev/null | tail -1
