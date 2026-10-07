#!/bin/bash
# Syntax-check every stage script and confirm the Stage-6 dispatcher is ARMED
# but idle. Read-only. CPU-only (runs on the login node; trivial).
cd /scratch/sychan552/a2_stage5 || exit 1
echo "=== bash -n over all stage scripts ==="
fail=0
for f in recovery/stage5/*.sh recovery/stage6/*.sh recovery/a0/*.sh; do
  [ -f "$f" ] || continue
  if bash -n "$f" 2>/dev/null; then echo "  SYNTAX OK   $f"; else echo "  SYNTAX FAIL $f"; bash -n "$f"; fail=1; fi
done
echo "=== python AST over the stage scripts ==="
for f in scripts/train_backbone_966.py scripts/score_test_stage5.py \
         scripts/build_lock_stage5.py recovery/stage6/recompute_eight.py \
         recovery/a0/a0_compat.py; do
  /home/sychan552/.conda/envs/mlflu_hpc/bin/python -c "
import ast,sys
ast.parse(open('$f',encoding='utf-8').read()); print('  AST OK   $f')" || fail=1
done
echo
echo "=== Stage-6 dispatcher state (must be idle / not running) ==="
bash recovery/stage6/dispatch.sh
echo
echo "=== queue / lock / stray dispatchers ==="
squeue -u "$USER"
ls -la results/stage6/logs/EXEC_LOCK 2>&1 | sed 's/^/  /'
ps -u "$USER" -o pid,etime,cmd | grep -E "dispatch|train_backbone|score_test" | grep -v grep || echo "  no dispatcher running"
tmux ls 2>&1 | sed 's/^/  /'
echo
echo "=== stage6 results so far ==="
find results/stage6 -type f 2>/dev/null | head -20 || echo "  (none - nothing submitted)"
echo "syntax_fail=$fail"
