#!/bin/bash
# Read-only inspection of Stage-5 A2 remote state.
cd /scratch/sychan552/a2_stage5 || exit 1

echo "=== date ==="
date -u +%FT%TZ

echo "=== dir sizes ==="
for d in results/stage5/author_966/miflu results/stage5/author_966/notext \
         results/stage5/author_966/nlinear results/stage5/author_966/naive \
         results/stage5/ckpt/author_966/miflu results/stage5/ckpt/author_966/notext \
         results/stage5/ckpt/author_966/nlinear ; do
  n=$(ls -1 "$d" 2>/dev/null | wc -l)
  echo "$d  files=$n"
done

echo "=== miflu exports ==="
ls -1 results/stage5/author_966/miflu
echo "=== miflu ckpts ==="
ls -1 results/stage5/ckpt/author_966/miflu
echo "=== notext exports (top) ==="
ls -1 results/stage5/author_966/notext
for L in 24 36 48 60; do
  echo "-- notext horizon_L$L"
  ls -1 "results/stage5/author_966/notext/horizon_L$L" 2>/dev/null
done
echo "=== notext ckpts ==="
find results/stage5/ckpt/author_966/notext -maxdepth 2 | sort
echo "=== nlinear exports ==="
ls -1 results/stage5/author_966/nlinear
echo "=== nlinear ckpts ==="
ls -1 results/stage5/ckpt/author_966/nlinear
echo "=== naive exports ==="
ls -1 results/stage5/author_966/naive

echo "=== logs ==="
ls -1 results/stage5/logs

echo "=== tail notext L24 job 585843 ==="
tail -60 results/stage5/logs/task_585843.out 2>/dev/null
echo "--- err ---"
tail -30 results/stage5/logs/task_585843.err 2>/dev/null

echo "=== tail notext FAILED job 585821 ==="
tail -40 results/stage5/logs/task_585821.out 2>/dev/null
echo "--- err ---"
tail -40 results/stage5/logs/task_585821.err 2>/dev/null
