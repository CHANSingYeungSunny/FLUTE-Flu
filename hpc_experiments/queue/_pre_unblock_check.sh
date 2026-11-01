#!/bin/bash
# _pre_unblock_check.sh -- read-only facts BEFORE touching the registry or queue.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1
st() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n "s/^$2=//p"; }

echo "=== jobs ==="
squeue -u sychan552 -o '%.8i %.10P %.20j %.2t %.21S'
echo
for j in 720105 720106 720052 720107; do
  printf '  %-8s %-14s %-9s start=%-20s %s\n' "$j" "$(st "$j" JobName)" "$(st "$j" JobState)" \
    "$(st "$j" StartTime)" "$(st "$j" TimeLimit)"
done

echo
echo "=== queue histogram BEFORE ==="
awk -F'\t' 'NR>1{c[$6" "$8]++} END{for(k in c) printf "  %-34s %d\n", k, c[k]}' master_queue.tsv | sort
echo
echo "  llm_cell rows by state:"
awk -F'\t' 'NR>1 && $2=="llm_cell"{c[$8]++} END{for(k in c) printf "    %-26s %d\n", k, c[k]}' master_queue.tsv | sort

echo
echo "=== weights manifest (job 720519 output) ==="
for f in $(ls -1t weights_manifest_solo.json 2>/dev/null; ls -1t ../weights_manifest_solo.json 2>/dev/null); do
  echo "  found: $f"; "$PY" - "$f" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
print("  keys:", sorted(d)[:12])
for k in ("required","ok","unsupported","failed","missing"):
    if k in d: print("  %-12s %s" % (k, d[k]))
arms = d.get("arms") or d.get("results") or []
if isinstance(arms, list):
    for a in arms:
        if isinstance(a, dict):
            print("   ", a.get("hf_id") or a.get("model") or a.get("name"),
                  "->", a.get("status") or a.get("verdict"), a.get("reason","")[:60])
PY
done
echo "  (if nothing above, the manifest is not in the queue dir)"

echo
echo "=== p2 probe records (revision pinning) ==="
if [ -d p2 ]; then
  for f in p2/*.json; do
    [ -f "$f" ] || continue
    "$PY" - "$f" <<'PY'
import json,sys,os
d=json.load(open(sys.argv[1]))
print("  %-34s ok=%s rev=%s" % (os.path.basename(sys.argv[1])[:-5], d.get("ok"),
                                (d.get("revision") or "-")[:12]))
PY
  done
else
  echo "  no p2/ directory"
fi

echo
echo "=== registry: weights + revision per arm ==="
"$PY" - <<'PY'
import json
reg = json.load(open("arms_registry.json", encoding="utf-8"))
for a in reg["arms"]:
    print("  %-34s pri=%s venv=%-4s weights=%-13s revision=%s params_b=%s bs=%s"
          % (a["label"], a["priority"], a["venv"], a["weights"],
             (a["revision"] or "-")[:12], a["params_b"], a["encoder_batch_size"]))
PY
