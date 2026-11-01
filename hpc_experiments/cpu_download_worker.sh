#!/bin/bash
# =============================================================================
# hpc_experiments/cpu_download_worker.sh
#
# WHAT THIS IS
# ------------
# The **weights fetcher** for the 14 frozen-encoder LLM arms. It turns
# `docs/LLM_ARMS.md` §7.1's "weights: missing" into pinned local snapshots, with
# a manifest that proves it and a CPU probe that records which architectures can
# emit per-layer hidden states (`OK`) and which cannot (`UNSUPPORTED` + reason).
#
# It does NO GPU work, trains nothing, scores nothing, and never touches
# `code/queue/*` (it only READS `code/queue/arms_registry.json`).
#
# ABSOLUTE PATHS ONLY — `dirname "$0"` IS FORBIDDEN HERE
# -----------------------------------------------------
# `sbatch` spools this script to `/var/spool/slurmd/job<N>/slurm_script`, so `$0`
# resolves into the spool directory and every path derived from it is wrong. That
# bug has already cost this project one failed submission tonight, so every path
# below is absolute and nothing is derived from `$0`. If the tree moves, edit
# `R` and nothing else.
#
# WHY THESE #SBATCH LINES
# -----------------------
#  * **no GRES line at all** — a GRES header becomes part of the job specification and cannot be overridden
#    from the command line, which is exactly how an earlier CPU lane became
#    unplaceable on `tiny`/`batch` (LEDGER 2026-11-01 22:37);
#  * `--mem` must satisfy `mem <= cpus-per-task * 1024` MB because `tiny` sets
#    `DefMemPerCPU=1024` (measured); 8 x 1024 = 8192, so 8000M is safe;
#  * `--time=2-23:00:00` is just under `batch`'s `MaxTime` of 3 days (measured
#    with `scontrol show partition batch`). On `tiny` override with
#    `--time=5-00:00:00` at submit time (tiny's MaxTime is 5 days);
#  * the job **self-requeues** at the wall budget with
#    `scontrol requeue "$SLURM_JOB_ID"`, which keeps the same job id and resets
#    `Elapsed` (measured, LEDGER 22:40), so one job id is an indefinite chain.
#    `sbatch` from inside a job would NOT work (QOS allows one submission per
#    user; the `stingy` case already failed with `QOSMaxSubmitJobPerUserLimit`).
#
# INTERNET
# --------
# `tiny` and `batch` both have outbound HTTPS through the CityU proxy, and
# `HfApi().model_info("tencent/Penguin-Encoder")` returned a sha in 6.4 s on
# `tiny` (measured). The proxy is exported below.
#
# STORAGE (home is ~59 GiB, scratch ~670 GiB — never fill home)
# ------------------------------------------------------------
# `HF_HOME` **and** `HF_HUB_CACHE` both point into scratch: the 33 B arm alone is
# ~66 GB. `huggingface_hub` reads `HF_HUB_CACHE`; `transformers` and the legacy
# cache path read `HF_HOME`. Setting only one of them silently writes to the
# other, so both are set and both are asserted below.
#
# ORDER — SMALLEST FIRST, DeepSeek-32B LAST
# -----------------------------------------
# The arm list is sorted by parameter count so usable arms are banked early and
# the 66 GB transfer (most likely to exhaust disk) runs last. The sort happens in
# this script, from the registry's own `params_b`, so it cannot drift from
# `arms_registry.json`.
#
# USAGE (queue owner submits; this session submits exactly this one job)
# ---------------------------------------------------------------------
#   mkdir -p /gpfs1/home/sychan552/stage5_a2_durable/code/logs
#   sbatch --partition=batch /gpfs1/home/sychan552/stage5_a2_durable/code/cpu_download_worker.sh
#   # fallback if batch refuses / has no free node:
#   sbatch --partition=tiny --time=5-00:00:00 \
#          /gpfs1/home/sychan552/stage5_a2_durable/code/cpu_download_worker.sh
#
# Env knobs (all optional; defaults are absolute):
#   R                 repo root on the cluster
#   REGISTRY          arms registry (READ ONLY — never written by this script)
#   HF_CACHE_ROOT     scratch cache root
#   MANIFEST          weights manifest path
#   VENV              python env dir
#   HF_MAX_WORKERS    parallel downloads            (default 4)
#   PROBE_CHECKPOINT  1 = also probe the real checkpoint for arms <= MAX_PARAMS_B
#   TIME_BUDGET_SEC   wall reserve for the requeue   (default 600)
#   DRY_RUN           1 = print the plan, download nothing
# =============================================================================
#SBATCH --job-name=mlflu_dl_weights
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8000M
#SBATCH --time=2-23:00:00
#SBATCH --output=/gpfs1/home/sychan552/stage5_a2_durable/code/logs/dl_weights-%j.out
#SBATCH --error=/gpfs1/home/sychan552/stage5_a2_durable/code/logs/dl_weights-%j.err
# NOTE: deliberately no GRES line. See the header.

set -uo pipefail          # NOT -e: one unsupported model must not kill the sweep

# ── absolute paths only (never $0, never dirname) ──────────────────────────
R="${R:-/gpfs1/home/sychan552/stage5_a2_durable}"
WORKER="${WORKER:-$R/code/weights_worker.py}"
REGISTRY="${REGISTRY:-$R/code/queue/arms_registry.json}"     # READ ONLY
HF_CACHE_ROOT="${HF_CACHE_ROOT:-/home/sychan552/scratch/hf_cache}"
OUT_DIR="${OUT_DIR:-/home/sychan552/scratch/mlflu_weights}"
#: Disjoint model list for this job (space- or comma-separated hf ids). Empty =
#: every required arm. Two parallel jobs must pass disjoint lists so no repo is
#: fetched twice, and they must use DIFFERENT manifests (see MANIFEST below).
MODELS="${MODELS:-}"
JOB_TAG="${JOB_TAG:-solo}"
MANIFEST="${MANIFEST:-$OUT_DIR/weights_manifest${JOB_TAG:+_$JOB_TAG}.json}"
LOG="${LOG:-$OUT_DIR/cpu_download_worker${JOB_TAG:+_$JOB_TAG}.log}"
VENV="${VENV:-/home/sychan552/.venvs/mlflu_llm}"
MAX_PARAMS_B="${MAX_PARAMS_B:-8}"
PROBE_CHECKPOINT="${PROBE_CHECKPOINT:-0}"
HF_MAX_WORKERS="${HF_MAX_WORKERS:-4}"
TIME_BUDGET_SEC="${TIME_BUDGET_SEC:-600}"
DRY_RUN="${DRY_RUN:-0}"

# ── 0. refuse to run on the login node ──────────────────────────────────────
if [ -z "${SLURM_JOB_ID:-}" ] && [ "$DRY_RUN" != "1" ]; then
  echo "REFUSING to run outside Slurm: this worker downloads tens of GB and must" >&2
  echo "never run on the login node. Submit it:" >&2
  echo "  sbatch --partition=batch $R/code/cpu_download_worker.sh" >&2
  echo "(DRY_RUN=1 is allowed for a local dry run.)" >&2
  exit 64
fi

mkdir -p "$OUT_DIR" "$HF_CACHE_ROOT/hub" 2>/dev/null || true
exec > >(tee -a "$LOG") 2>&1

say() { printf '[%s] %s\n' "$(date '+%F %T')" "$*"; }

say "=== cpu_download_worker start ==="
say "job=${SLURM_JOB_ID:-LOCAL} partition=${SLURM_JOB_PARTITION:-none} node=${SLURM_NODELIST:-$(hostname)} tag=$JOB_TAG"
say "R=$R worker=$WORKER registry=$REGISTRY"
say "manifest=$MANIFEST log=$LOG venv=$VENV dry_run=$DRY_RUN"
say "models filter: ${MODELS:-<all required arms>}"

# ── 1. internet + caches (both names, both on scratch) ─────────────────────
export HTTPS_PROXY="${HTTPS_PROXY:-http://proxy.cityu.edu.hk:8080}"
export HTTP_PROXY="${HTTP_PROXY:-http://proxy.cityu.edu.hk:8080}"
export https_proxy="$HTTPS_PROXY"
export http_proxy="$HTTP_PROXY"
export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1}"
export HF_HOME="${HF_HOME:-$HF_CACHE_ROOT}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-$HF_CACHE_ROOT/hub}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$HF_HUB_CACHE}"
export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-0}"
export PYTHONUNBUFFERED=1
export HF_MAX_WORKERS
mkdir -p "$HF_CACHE_ROOT" "$HF_HUB_CACHE" 2>/dev/null || true
say "HF_HOME=$HF_HOME"
say "HF_HUB_CACHE=$HF_HUB_CACHE"
say "HTTPS_PROXY=$HTTPS_PROXY"
# The cache must live on a DIFFERENT filesystem from $HOME. A substring test is
# wrong here: `/home/<user>/scratch` is a SYMLINK to the scratch filesystem, so
# `case "$HF_HOME" in *"$HOME"*)` rejects the correct path — it did exactly that
# on the first submission (23:40) and cost one failed job. Compare device ids.
HF_HOME_REAL=$(readlink -f "$HF_HOME" 2>/dev/null || echo "$HF_HOME")
HOME_REAL=$(readlink -f "$HOME" 2>/dev/null || echo "$HOME")
DEV_HF=$(stat -c %d "$HF_HOME_REAL" 2>/dev/null || echo hf)
DEV_HOME=$(stat -c %d "$HOME_REAL" 2>/dev/null || echo home)
say "resolved: HF_HOME -> $HF_HOME_REAL (dev $DEV_HF), HOME -> $HOME_REAL (dev $DEV_HOME)"
if [ "$DEV_HF" = "$DEV_HOME" ]; then
  say "FATAL: HF_HOME resolves onto the HOME filesystem ($HF_HOME_REAL); refusing to fill the home quota"
  exit 65
fi
if [ "$HF_HOME" != "$HF_CACHE_ROOT" ] || [ "$HF_HUB_CACHE" != "$HF_CACHE_ROOT/hub" ]; then
  say "WARN: cache paths differ from the scratch defaults; check the env"
fi
say "disk free: $(df -h "$HF_CACHE_ROOT" 2>/dev/null | tail -1 | awk '{print $4}') on $HF_CACHE_ROOT; $(df -h "$HOME" 2>/dev/null | tail -1 | awk '{print $4}') on HOME"

# ── 2. python env ──────────────────────────────────────────────────────────
if [ -f "$VENV/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  say "activated venv: $VENV"
else
  say "WARN: venv $VENV not found; using $(command -v python)"
fi
PY="$(command -v python)"
say "python=$PY ($($PY -V 2>&1))"
$PY -c 'import huggingface_hub, transformers, torch; print("hf_hub", huggingface_hub.__version__, "transformers", transformers.__version__, "torch", torch.__version__)' \
  || { say "FATAL: huggingface_hub/transformers/torch missing in $VENV"; exit 66; }

# ── 3. the arm list, SMALLEST FIRST (from the registry's params_b) ─────────
say "--- required arms (10 Tencent + DeepSeek-R1-Distill-Qwen-32B), smallest first ---"
if [ -n "$MODELS" ]; then
  # disjoint slice for this job: "a,b,c" or "a b c"
  # shellcheck disable=SC2086
  if ! $PY "$WORKER" arms --registry "$REGISTRY" \
        --models $(printf '%s' "$MODELS" | tr ',' ' '); then
    say "FATAL: cannot read $REGISTRY or bad MODELS=$MODELS"; exit 67
  fi
else
  if ! $PY "$WORKER" arms --registry "$REGISTRY"; then
    say "FATAL: cannot read $REGISTRY"; exit 67
  fi
fi > "$OUT_DIR/arms_raw_$JOB_TAG.tsv"
# columns: hf_id, label, revision, venv, params_b ; empty/None params_b sorts last
awk -F'\t' '{ p=$5; if (p=="" || p=="None") p=99999; printf "%s\t%s\n", p, $0 }' \
  "$OUT_DIR/arms_raw_$JOB_TAG.tsv" | sort -t$'\t' -k1,1g | cut -f2- > "$OUT_DIR/arms_$JOB_TAG.tsv"
cat "$OUT_DIR/arms_$JOB_TAG.tsv"
N_ARMS=$(grep -c . "$OUT_DIR/arms_$JOB_TAG.tsv" || true)
say "arms: $N_ARMS (order above is the download order)"
if [ -n "$MODELS" ] && [ "$N_ARMS" -lt 1 ]; then
  say "FATAL: MODELS=$MODELS matched no required arm"; exit 67
fi
if [ -z "$MODELS" ] && [ "$N_ARMS" -lt 11 ]; then
  say "FATAL: expected >= 11 arms from $REGISTRY, got $N_ARMS"; exit 67
fi

# ── 4. manifest must start valid (or not exist) ────────────────────────────
if [ -f "$MANIFEST" ]; then
  $PY "$WORKER" check --manifest "$MANIFEST" || { say "FATAL: existing manifest is invalid"; exit 68; }
  say "resuming from an existing manifest ($MANIFEST)"
else
  say "no manifest yet: starting fresh ($MANIFEST)"
fi

# ── 5. self-requeue helper (wall measured, never assumed) ──────────────────
remaining_seconds() {
  if [ -z "${SLURM_JOB_ID:-}" ]; then echo 99999999; return; fi
  local end now end_s
  end=$(scontrol show job "$SLURM_JOB_ID" | tr ' ' '\n' | awk -F= '/^EndTime=/{print $2}' | head -1)
  if [ -z "$end" ] || [ "$end" = "Unknown" ]; then echo 99999999; return; fi
  now=$(date +%s)
  end_s=$(date -d "$end" +%s 2>/dev/null || echo "$now")
  echo $(( end_s - now ))
}

maybe_requeue() {
  local left
  left=$(remaining_seconds)
  say "wall remaining ~${left}s (reserve ${TIME_BUDGET_SEC}s)"
  if [ "$left" -le "$TIME_BUDGET_SEC" ]; then
    if [ "$DRY_RUN" = "1" ] || [ -z "${SLURM_JOB_ID:-}" ]; then
      say "would requeue here (dry run / no Slurm)"; return 1
    fi
    say "near the wall limit -> scontrol requeue $SLURM_JOB_ID (same job id, Elapsed resets)"
    scontrol requeue "$SLURM_JOB_ID"
    return 1
  fi
  return 0
}

# ── 6. the loop: smallest arm first, manifest written after EVERY model ────
DONE=0; SKIPPED=0; UNSUP=0; FAILED=0
while IFS=$'\t' read -r HF_ID LABEL REVISION VENV_TAG PARAMS_B; do
  [ -z "${HF_ID:-}" ] && continue
  if ! maybe_requeue; then
    say "stopping to requeue; finished=$DONE skipped=$SKIPPED unsupported=$UNSUP failed=$FAILED"
    exit 0
  fi

  # Already terminal (OK or UNSUPPORTED)? Skip — a resumed run must be cheap.
  if [ -f "$MANIFEST" ]; then
    STATE=$($PY -c 'import json,sys
m = json.load(open(sys.argv[1]))
for e in m.get("entries", []):
    if e.get("model") == sys.argv[2]:
        print(e.get("status", "PENDING")); break
else:
    print("MISSING")' "$MANIFEST" "$HF_ID" 2>/dev/null || echo MISSING)
    case "$STATE" in
      OK|UNSUPPORTED) say "SKIP $HF_ID (already $STATE in the manifest)"; SKIPPED=$((SKIPPED+1)); continue ;;
    esac
  fi

  ARGS=(--model "$HF_ID" --label "$LABEL" --manifest "$MANIFEST" --max-params-b "$MAX_PARAMS_B")
  [ -n "${REVISION:-}" ] && [ "$REVISION" != "None" ] && ARGS+=(--revision "$REVISION")
  [ -n "${PARAMS_B:-}" ] && [ "$PARAMS_B" != "None" ] && ARGS+=(--params-b "$PARAMS_B")
  [ "$PROBE_CHECKPOINT" = "1" ] && ARGS+=(--probe-checkpoint)

  say "DOWNLOAD $HF_ID (label=$LABEL size=${PARAMS_B:-?}B revision=${REVISION:-auto})"
  if [ "$DRY_RUN" = "1" ]; then
    say "  dry run: would call $PY $WORKER download ${ARGS[*]}"; continue
  fi
  OUT=$($PY "$WORKER" download "${ARGS[@]}" 2>&1); RC=$?
  printf '%s\n' "$OUT" | sed 's/^/    /'
  if [ $RC -eq 0 ]; then
    case "$OUT" in
      *STATUS=UNSUPPORTED*) UNSUP=$((UNSUP+1)) ;;
      *) DONE=$((DONE+1)) ;;
    esac
  else
    FAILED=$((FAILED+1)); say "  FAILED $HF_ID (rc=$RC) — recorded in the manifest"
  fi
  say "  progress: finished=$DONE skipped=$SKIPPED unsupported=$UNSUP failed=$FAILED"
  maybe_requeue || { say "requeued after $HF_ID"; exit 0; }
done < "$OUT_DIR/arms_$JOB_TAG.tsv"

# ── 7. final validation + coverage ────────────────────────────────────────
say "--- manifest validation ---"
$PY "$WORKER" check --manifest "$MANIFEST" || { say "FATAL: manifest invalid"; exit 69; }
$PY "$WORKER" coverage --manifest "$MANIFEST" --registry "$REGISTRY" || true
say "finished=$DONE skipped=$SKIPPED unsupported=$UNSUP failed=$FAILED"
say "manifest: $MANIFEST"
say "=== cpu_download_worker done (job ${SLURM_JOB_ID:-LOCAL}) ==="
# A non-zero exit would burn the queue's attempt counter for a job that did its
# job; missing/failed arms are visible in the coverage report instead.
exit 0
