#!/bin/bash
# ==========================================================================
# d13_quarantine.sh — manifest-driven, containment-checked quarantine.
#
# Usage:  bash d13_quarantine.sh --dry-run|--execute <candidates.tsv>
#
# candidates.tsv is TAB separated:  kind<TAB>path
#   kind = file | dir
#
# Every candidate must pass ALL of:
#   * exists
#   * owned by the user
#   * realpath is strictly INSIDE the allowed root
#   * is not a symlink
# Anything that fails is REFUSED and reported (never deleted).
#
# Phase 1 (--dry-run) writes a manifest and touches nothing.
# Phase 2 (--execute) moves the candidate into the quarantine root, preserving
# the relative path, and appends to the SAME manifest.
#
# Permanent deletion is a separate, explicit later step.
# ==========================================================================
set -uo pipefail

MODE="${1:---dry-run}"
CAND="${2:-}"
[ -n "$CAND" ] || { echo "usage: $0 --dry-run|--execute <candidates.tsv>"; exit 2; }
[ -f "$CAND" ] || { echo "candidate list not found: $CAND"; exit 2; }

Q=/gpfs1/scratch/sychan552/_d13_quarantine
# `/home/sychan552` is a symlink/bind onto `/gpfs1/home/sychan552`, so BOTH the
# allowed root and every candidate must be canonicalised before comparing.
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
