#!/bin/bash
# Track-B v2 lane. Static stripe partition -> NO shared cursor, NO flock, NO duplicate claims.
# Usage: run_lane_v2.sh <LANE> <NLANES> <core|all>
set -u
LANE="$1"; NLANES="$2"; PHASE="$3"
R=/gpfs1/scratch/sychan552/trackB_20261104
if [ "$PHASE" = "core" ]; then
  BASE="$R/core"; CELLS="$BASE/cells.tsv"; TOTAL=160
else
  BASE="$R/all"; CELLS="$BASE/cells_all.tsv"; TOTAL=1120
fi
PY=/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python
CODE=/gpfs1/scratch/sychan552/stage5_a2_durable/code
HELPER="$R/cellok.py"
CLAIMS="$BASE/claims"; FAILED="$BASE/failed"; PARTIAL="$BASE/partial"
mkdir -p "$CLAIMS" "$FAILED" "$PARTIAL" "$BASE/logs"
cd "$CODE" || exit 2
# Keep the exact environment under which the old lanes already produced valid
# miflu cells: no global HF overrides. Encoder runs set them inline below.
export PYTHONUNBUFFERED=1

log() { echo "$(date -u +%FT%TZ) lane$LANE $*" >> "$BASE/logs/lane${LANE}_v2.log"; }
DID_WORK=0

# Quarantine a partial cell so a failed run can never masquerade as a complete one.
quarantine() {
  local d="$1" key="$2"
  [ -d "$d" ] || return 0
  local q="$PARTIAL/${key}_$(date -u +%Y%m%dT%H%M%SZ)"
  mkdir -p "$q"
  find "$d" -mindepth 1 -maxdepth 1 -exec mv -t "$q" {} + 2>/dev/null || true
  log "QUARANTINED $key -> $q"
}

run_one() {
  local model="$1" L="$2" seed="$3" kind="$4" mid="$5" rev="$6" route="$7"
  local key="${model}_L${L}_s${seed}"
  local out="$BASE/export/$model/L${L}_s${seed}"
  local ck="$BASE/ckpt/$model/L${L}_s${seed}"
  local claim="$CLAIMS/$key"
  # atomic per-cell claim via mkdir (GPFS-safe); stale claims expire after 6h
  if ! mkdir "$claim" 2>/dev/null; then
    local opid=""; local ohost=""; local reclaim=0
    if [ -f "$claim/owner" ]; then
      read -r opid ohost _ < "$claim/owner" 2>/dev/null || true
      if [ -n "$opid" ] && [ "$ohost" = "$(hostname)" ] && [ ! -d "/proc/$opid" ]; then
        reclaim=1
      fi
    fi
    local age=$(( $(date +%s) - $(stat -c %Y "$claim" 2>/dev/null || echo 0) ))
    if [ "$reclaim" -eq 0 ] && [ "$age" -lt 21600 ]; then
      log "CLAIMED_ELSEWHERE $key owner=$opid@$ohost age=$age"; return 0
    fi
    log "RECLAIM_CLAIM $key dead_owner=$reclaim age=$age"
    rm -rf "$claim"; mkdir "$claim" 2>/dev/null || { log "CLAIM_RACE $key"; return 0; }
  fi
  echo "$$ $(hostname) $(date -u +%FT%TZ)" > "$claim/owner"
  if "$PY" "$HELPER" check "$out" "$route" >/dev/null 2>&1; then
    log "SKIP_COMPLETE $key"; rm -f "$claim/owner"; rmdir "$claim" 2>/dev/null; return 0
  fi
  local why; why=$("$PY" "$HELPER" check "$out" "$route" 2>/dev/null | head -1)
  quarantine "$out" "$key"
  mkdir -p "$out" "$ck"
  local attempts=0
  if [ -f "$FAILED/$key" ]; then attempts=$(cat "$FAILED/$key"); fi
  if [ "$attempts" -ge 2 ]; then
    log "BLOCKED_MAX_ATTEMPTS $key attempts=$attempts"; rm -f "$claim/owner"; rmdir "$claim" 2>/dev/null; return 0
  fi
  local rc=0
  DID_WORK=$((DID_WORK+1))
  log "START $key route=$route attempt=$((attempts+1)) slurm=${SLURM_JOB_ID:-none}"
  case "$route" in
    miflu)
      "$PY" train_miflu.py --profile author_repo_966 --horizon "$L" --seed "$seed" \
        --reps 1 --epochs 20 --containment strict --export-dir "$out" --ckpt-dir "$ck" \
        >> "$BASE/logs/lane${LANE}_v2.log" 2>&1 || rc=$? ;;
    classical)
      "$PY" train_classical_966.py --model "$model" --profile author_966 \
        --horizon "$L" --seed "$seed" --containment strict --export-dir "$out" \
        >> "$BASE/logs/lane${LANE}_v2.log" 2>&1 || rc=$? ;;
    encoder)
      if [ -z "$mid" ] || [ -z "$rev" ]; then
        log "BLOCKED_NO_PINNED_REVISION $key"; echo "$key missing pinned revision" >> "$BASE/blocked.tsv"
        rc=99
      else
        # Cheap preflight: never burn a GPU on a pinned revision whose weights are absent.
        # HF_HOME is set INLINE for this one command only, so later miflu cells keep
        # their normal GPT-2 cache location.
        HFC=/gpfs1/scratch/sychan552/hf_cache
        org=${mid%%/*}; nm=${mid#*/}
        snap="$HFC/hub/models--${org}--${nm}/snapshots/${rev}"
        snap2="$HFC/models--${org}--${nm}/snapshots/${rev}"
        if [ ! -d "$snap" ] && [ ! -d "$snap2" ]; then
          log "BLOCKED_MISSING_PINNED_WEIGHTS $key $mid@$rev"
          echo -e "$key\t$mid@$rev\tmissing_pinned_weights" >> "$BASE/blocked.tsv"
          rc=98
        else
          HF_HOME="$HFC" HF_HUB_CACHE="$HFC/hub" \
          HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
          "$PY" train_backbone_966.py --backbone llm_encoder --profile author_966 \
            --horizon "$L" --seed "$seed" --containment strict --llm-model-id "$mid" \
            --llm-revision "$rev" --encoder-device cuda --export-dir "$out" --ckpt-dir "$ck" \
            >> "$BASE/logs/lane${LANE}_v2.log" 2>&1 || rc=$?
        fi
      fi ;;
    backbone)
      "$PY" train_backbone_966.py --backbone "$model" --profile author_966 \
        --horizon "$L" --seed "$seed" --containment strict --export-dir "$out" --ckpt-dir "$ck" \
        >> "$BASE/logs/lane${LANE}_v2.log" 2>&1 || rc=$? ;;
  esac
  if [ "$rc" -eq 0 ] && "$PY" "$HELPER" check "$out" "$route" >/dev/null 2>&1; then
    log "END_OK $key rc=0"; rm -f "$FAILED/$key"
  else
    echo $((attempts+1)) > "$FAILED/$key"
    echo -e "$key\trc=$rc\t$why" >> "$BASE/retry.tsv"
    log "END_FAIL $key rc=$rc why=$why attempts=$((attempts+1))"
  fi
  rm -f "$claim/owner"; rmdir "$claim" 2>/dev/null || true
}

# Three passes: retries are REAL re-executions, capped at 2 attempts per cell.
for pass in 1 2 3; do
  n=0
  DID_WORK=0
  idx=0
  while IFS=$'\t' read -r model L seed kind mid rev; do
    [ -z "${model:-}" ] && continue
    if [ $(( idx % NLANES )) -ne "$LANE" ]; then idx=$((idx+1)); continue; fi
    idx=$((idx+1))
    kind=${kind:-backbone}; mid=${mid:-}; rev=${rev:-}
    case "$model" in
      miflu) route=miflu ;;
      decision_tree|gradient_boosting|knn|random_forest|svr) route=classical ;;
      *) if [ "$kind" = "encoder" ]; then route=encoder; else route=backbone; fi ;;
    esac
    run_one "$model" "$L" "$seed" "$kind" "$mid" "$rev" "$route"
    n=$((n+1))
  done < <(sed 's/\r$//' "$CELLS" | awk 'NF')
  done_now=$("$PY" "$HELPER" count "$BASE/export" "$CELLS" 2>/dev/null | head -1 | awk '{print $2}')
  log "PASS $pass processed=$n did_work=$DID_WORK complete=$done_now/$TOTAL"
  if [ "${done_now:-0}" -ge "$TOTAL" ]; then break; fi
  if [ "$DID_WORK" -eq 0 ]; then
    touch "$BASE/lane${LANE}_v2.done"
    log "LANE_STRIPE_COMPLETE (no incomplete cells in this stripe)"
    break
  fi
done
final_done=$("$PY" "$HELPER" count "$BASE/export" "$CELLS" 2>/dev/null | head -1 | awk '{print $2}')
log "LANE_EXIT complete=${final_done:-0}/$TOTAL"
