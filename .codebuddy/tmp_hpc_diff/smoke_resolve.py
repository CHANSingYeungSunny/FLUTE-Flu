import os, sys, json

R = "/scratch/sychan552/innovation_deploy_root_v3_clean14"
os.environ["INNOVATION_DEPLOYMENT_ROOT"] = R
os.environ["INNOVATION_REGISTRY_REL"] = "results/v3_clean/runs/complete_specs_amended.json"
sys.path.insert(0, R + "/scripts")

from innovation import compact_checkpoint as CC

keys = [
    "negative_control__llm_removed_or_alignment_only__L24__seed42__w2",
    "negative_control__llm_removed_or_alignment_only__L24__seed43__w2",
    "negative_control__llm_removed_or_alignment_only__L24__seed44__w2",
    "negative_control__llm_removed_or_alignment_only__L60__seed42__w2",
    "negative_control__llm_removed_or_alignment_only__L60__seed43__w2",
    "negative_control__llm_removed_or_alignment_only__L60__seed44__w2",
]

ok = True
for k in keys:
    try:
        info = CC.resolve_run_key(k)
        print(json.dumps(info))
        # assertions on required provenance
        assert info["model"] == "llm_removed_or_alignment_only", info["model"]
        assert info["arm"] == "negative_control", info["arm"]
        assert info["parent_model"] == "timecma_llm", info.get("parent_model")
        assert info["control"] == "llm_removed_or_alignment_only", info.get("control")
        assert info["wave"] == 2, info["wave"]
    except Exception as e:
        ok = False
        print("FAIL", k, type(e).__name__, str(e))

print("ALL_OK" if ok else "HAS_FAILURES")
sys.exit(0 if ok else 1)
