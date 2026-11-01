#!/bin/bash
# _v2check.sh -- static checks for the v2 queue code, then the two offline proofs.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1

echo "=== 0. strip CRLF / BOM (scp from Windows) ==="
for f in master_controller.sh master_task.py queue_store.py make_queue.py cost_model.py \
         submit_night.sh watchdog.sh cpu_worker.sh stage_analysis.sh arms_registry.json; do
  sed -i 's/\r$//' "$f"
  sed -i '1s/^\xEF\xBB\xBF//' "$f"
done
for f in master_controller.sh watchdog.sh submit_night.sh cpu_worker.sh; do
  printf '  %-22s first2=' "$f"; head -c 2 "$f" | od -An -c | tr -d '\n'; echo
done

echo
echo "=== 1. bash syntax ==="
for f in master_controller.sh watchdog.sh submit_night.sh cpu_worker.sh; do
  if bash -n "$f"; then echo "  OK   $f"; else echo "  FAIL $f"; fi
done

echo
echo "=== 2. python syntax + json ==="
for f in master_task.py queue_store.py make_queue.py cost_model.py; do
  if "$PY" -m py_compile "$f"; then echo "  OK   $f"; else echo "  FAIL $f"; fi
done
"$PY" -c 'import json;d=json.load(open("arms_registry.json"));print("  OK arms_registry.json:",len(d["arms"]),"arms; envs:",sorted({a["venv"] for a in d["arms"]}))'

echo
echo "=== 3. migrate / merge the queue (state preserved) ==="
cp -p master_queue.tsv "master_queue.tsv.bak_$(date +%H%M%S)"
"$PY" make_queue.py --migrate
"$PY" make_queue.py
echo "--- header ---"; head -1 master_queue.tsv | tr '\t' '\n' | nl
echo "--- counts ---"
awk -F'\t' 'NR>1{c[$6" "$8]++} END{for(k in c) printf "  %-26s %d\n", k, c[k]}' master_queue.tsv | sort
echo "--- F1-F5 rows ---"
awk -F'\t' 'NR>1 && $6=="P4"{printf "  %-24s kind=%-20s env=%-4s state=%-8s att=%s\n",$1,$2,$7,$8,$9}' master_queue.tsv
echo "--- env column coverage ---"
awk -F'\t' 'NR>1{e[$7]++} END{for(k in e) printf "  env=%-5s %d\n", k, e[k]}' master_queue.tsv | sort
echo "--- rows with empty env (must be 0) ---"
awk -F'\t' 'NR>1 && ($7==""||$7=="-") {n++} END{print "  empty_env_rows="n+0}' master_queue.tsv

echo
echo "=== 4. DRY RUN (stripe partition assertions) ==="
bash master_controller.sh --dry-run; echo "dry-run rc=$?"

echo
echo "=== 5. SELFTEST (crash / oracle / claim / env-missing) ==="
bash master_controller.sh --selftest; echo "selftest rc=$?"
