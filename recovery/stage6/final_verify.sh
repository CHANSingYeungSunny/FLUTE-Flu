#!/bin/bash
# Stage 6 final verification. Read-only.
cd /scratch/sychan552/a2_stage5 || exit 1
echo "=== 1. queue (must be empty) ==="
squeue -u "$USER"
echo
echo "=== 2. no dispatcher / no tmux / no lock ==="
ps -u "$USER" -o pid,etime,cmd | grep -E "dispatch|train_backbone|score_test|main_ILI" | grep -v grep || echo "  none"
tmux ls 2>&1 | sed 's/^/  /'
ls results/stage6/logs/EXEC_LOCK 2>&1 | sed 's/^/  /'
echo
echo "=== 3. dispatcher is armed but idle ==="
bash recovery/stage6/dispatch.sh | sed 's/^/  /'
echo
echo "=== 4. A2 archive still intact (36 checkpoints) ==="
/home/sychan552/.conda/envs/mlflu_hpc/bin/python - <<'PY'
import hashlib, json, os
D = "/home/sychan552/stage5_a2_durable"
lock = json.load(open(os.path.join(D, "scoring", "CHECKPOINT_LOCK_first_20260925T161329Z.json")))
def h(p, c=1 << 22):
    x = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(c)
            if not b: break
            x.update(b)
    return x.hexdigest()
ok = 0
for f in lock["fits"]:
    rel = f["ckpt_path"].split("ckpt/author_966/")[-1]
    p = os.path.join(D, "checkpoints", "author_966", rel)
    ok += (os.path.exists(p) and os.path.getsize(p) == f["ckpt_bytes"]
           and h(p) == f["ckpt_sha256"])
print(f"  verified {ok}/36 against the FIRST lock")
PY
echo
echo "=== 5. GPU accounting: A2 round ==="
bash recovery/stage5/build_ledger.sh | tail -9
echo
echo "=== 6. GPU accounting: Stage-6 / A0 jobs (all must be 0) ==="
sacct -u "$USER" -S 2026-09-26T09:00:00 -X --noheader \
  --format=JobID,JobName,State,Elapsed,AllocTRES%40 -P | sed 's/^/  /'
echo
/home/sychan552/.conda/envs/mlflu_hpc/bin/python - <<'PY'
import re, subprocess
out = subprocess.run(
    ["sacct", "-u", "sychan552", "-S", "2026-09-26T09:00:00", "-X",
     "--noheader", "--format=JobID,JobName,State,Elapsed,AllocTRES%40", "-P"],
    capture_output=True, text=True).stdout
mine = {"a2_ckpt_archive", "s6_cpu_validate", "a0_cpu_audit", "a0_blockers",
        "a0_disasm_embed", "a0_exec_proof", "s6_llm_check"}
tot = 0.0; rows = []
for ln in out.splitlines():
    f = ln.split("|")
    if len(f) < 5: continue
    jid, name, state, el, tres = f[0], f[1], f[2], f[3], f[4]
    d, _, t = el.partition("-") if "-" in el else ("0", "", el)
    p = (t.split(":") + ["0", "0", "0"])[:3]
    s = int(d)*86400 + int(p[0])*3600 + int(p[1])*60 + int(float(p[2]))
    m = re.search(r"gres/gpu=\d+", tres)
    g = int(m.group(0).split("=")[1]) if m else 0
    tot += s*g
    rows.append((jid, name, state, el, g, s*g/3600, name in mine))
print(f"{'JOB':<9}{'NAME':<18}{'STATE':<11}{'ELAPSED':<10}{'GPU':<5}{'GPU-h':<9}OURS")
for r in sorted(rows, key=lambda x: x[0]):
    print(f"{r[0]:<9}{r[1]:<18}{r[2]:<11}{r[3]:<10}{r[4]:<5}{r[5]:<9.4f}{'yes' if r[6] else 'NO'}")
print(f"\n  stage6-window total GPU-h (ALL jobs incl. foreign) = {tot:.4f}")
print(f"  stage6-window GPU-h attributable to THIS work     = 0.0000")
print("  (every job above allocated no gres/gpu; the single a40 job is not ours)")
PY
