import json, os, subprocess, glob

R = "/scratch/sychan552/innovation_deploy_root_v3_clean14"
RUNS = R + "/results/v3_clean/runs"
DUR = "/home/sychan552/innovation_durable/screening"

def sh(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        return "ERR:" + (e.output or b"").decode()

print("=== sacct recent (llm_removed / finalize) ===")
print(sh("sacct -S 2026-09-21 -X -n -o JobID,JobName%60,State,ExitCode | grep -iE 'llm_removed|finaliz|v319' | head -50"))

print("\n=== squeue ===")
print(sh("squeue -u sychan552 -h -o '%i %j %T' 2>&1 | head -20"))

print("\n=== AMENDED registry: 6 rebound rows ===")
try:
    d = json.load(open(RUNS + "/complete_specs_amended.json", encoding="utf-8"))
    rs = [s for s in d["specs"] if "llm_removed" in s.get("control", "")]
    for s in sorted(rs, key=lambda x: x["order"]):
        print(json.dumps({k: s.get(k) for k in
            ("run_key","order","arm","model","control","parent_model",
             "horizon","seed","wave","submittable","executable_binding",
             "amended_action","intervention")}))
    print("n_rebound_total=", len(rs))
except Exception as e:
    print("AMENDED ERR", e)

print("\n=== FROZEN registry: 6 llm_removed rows ===")
try:
    d = json.load(open(RUNS + "/complete_specs_598.json", encoding="utf-8"))
    rs = [s for s in d["specs"] if "llm_removed" in s.get("control", "")]
    for s in sorted(rs, key=lambda x: x["order"]):
        print(json.dumps({k: s.get(k) for k in
            ("run_key","order","arm","model","control","parent_model",
             "horizon","seed","wave","submittable","executable_binding")}))
except Exception as e:
    print("FROZEN ERR", e)

print("\n=== ledger files ===")
for p in glob.glob("/scratch/sychan552/_v319d/*.jsonl") + \
         glob.glob("/scratch/sychan552/_v319*/wave*ledger*.jsonl") + \
         glob.glob("/scratch/sychan552/_v319*/*.jsonl"):
    try:
        lines = open(p).read().strip().splitlines()
        print(p, "lines=", len(lines))
        for ln in lines[-8:]:
            print("   ", ln[:160])
    except Exception as e:
        print(p, "ERR", e)

print("\n=== durable _controller ===")
print(sh("ls -la " + DUR + "/_controller 2>&1 | head -30"))

print("\n=== 6 run dirs: run_status spec + checkpoint_manifest ===")
for rk in sorted(glob.glob(RUNS + "/negative_control__llm_removed_or_alignment_only__*")):
    base = os.path.basename(rk)
    try:
        rs = json.load(open(rk + "/run_status.json", encoding="utf-8"))
        print("\n---", base)
        print("  state=", rs.get("state"), "spec=", json.dumps(rs.get("spec", {})))
        print("  checkpoint_applicable=", rs.get("checkpoint_applicable"),
              "stochastic_seed_applicable=", rs.get("stochastic_seed_applicable"))
    except Exception as e:
        print("  run_status ERR", e)
    cm = rk + "/checkpoints/checkpoint_manifest.json"
    try:
        cmj = json.load(open(cm, encoding="utf-8"))
        print("  ckpt_manifest restore_ok=", cmj.get("restore_ok"),
              "best_epoch=", cmj.get("best_epoch"),
              "n_trainable=", cmj.get("trainable_parameters"))
    except Exception as e:
        print("  ckpt_manifest ERR", e)
    ru = rk + "/resource_usage.json"
    try:
        ruj = json.load(open(ru, encoding="utf-8"))
        print("  resource train_s=", ruj.get("train_seconds"),
              "gpu_h=", ruj.get("gpu_hours"))
    except Exception as e:
        print("  resource ERR", e)
