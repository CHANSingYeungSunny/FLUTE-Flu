import json, glob, os, subprocess

R = "/scratch/sychan552/innovation_deploy_root_v3_clean14"
RUNS = R + "/results/v3_clean/runs"

def sh(c):
    try:
        return subprocess.check_output(c, shell=True, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        return "ERR:" + (e.output or b"").decode()

print("=== sacct full JobName ===")
print(sh("sacct -S 2026-09-21 -X -n -o JobID,JobName%90,State,ExitCode,Elapsed | grep -iE 'llm_removed|v319|finaliz' | head -40"))

print("\n=== amended registry order (6) ===")
reg = json.load(open(RUNS + "/complete_specs_amended.json", encoding="utf-8"))
rows = [s for s in reg["specs"] if "llm_removed" in s.get("control", "")]
rows.sort(key=lambda s: s["order"])
for s in rows:
    print(s["order"], s["run_key"], "horizon=", s["horizon"], "seed=", s["seed"],
          "parent=", s.get("parent_model"), "control=", s.get("control"))

print("\n=== run dir: job id evidence ===")
for rk in sorted(glob.glob(RUNS + "/negative_control__llm_removed_or_alignment_only__*")):
    base = os.path.basename(rk)
    found = {}
    for fn in ("run_status.json", "resource_usage.json",
               "logs/slurm_job_id.txt", "slurm_job_id.txt", "job_id.txt"):
        p = rk + "/" + fn
        if os.path.isfile(p):
            try:
                t = open(p, encoding="utf-8").read()
                found[fn] = t[:200]
            except Exception as e:
                found[fn] = "ERR " + str(e)
    # grep for SLURM_JOB_ID / job_id in run_status & resource
    for fn in ("run_status.json", "resource_usage.json"):
        p = rk + "/" + fn
        if os.path.isfile(p):
            t = open(p, encoding="utf-8").read()
            for k in ("job_id", "slurm", "SLURM", "576"):
                if k in t:
                    import re
                    m = re.findall(r'"?(?:slurm_?)?job_?id"?\s*[:=]\s*"?(\d+)', t, re.I)
                    if m:
                        found.setdefault("jobid_" + fn, m)
    print("\n--", base)
    for k, v in found.items():
        print("   ", k, "=", v)
