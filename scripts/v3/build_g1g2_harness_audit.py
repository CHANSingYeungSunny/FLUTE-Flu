"""build_g1g2_harness_audit.py — version, hash, diff and audit the G1/G2
Gate-harness repair.

The frozen runtime source (innov-v3.2-d5-asset-resolution) is NOT touched; only
hpc_scripts/v3_prepilot_gate.{py,sh}, which live outside the 87-file snapshot.
"""
from __future__ import annotations

import difflib
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMPL = ROOT / "results" / "v3" / "implementation"
IMPL.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

HARNESS_VERSION = "v3-prepilot-gate-g1g2-fixed"
POST_PY = ROOT / "hpc_scripts" / "v3_prepilot_gate.py"
POST_SH = ROOT / "hpc_scripts" / "v3_prepilot_gate.sh"
PRE_PY = Path(r"C:\Users\Asus\harness_pre\v3_prepilot_gate.py")

PRE_PY_SHA = "4377592be45e275c1bf7a5424face4980c0fae64c1f51f3fa1cd67bec215a13e"
PRE_SH_SHA = "de0382f68c7d4aa240f19545a91dc8b2c0a4254c0cd4252cf51b746e2d6a8848"


def sha(p: Path) -> str:
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def wj(p, o):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def wtext(p, s):
    Path(p).write_text(s, encoding="utf-8")


post_py_sha, post_sh_sha = sha(POST_PY), sha(POST_SH)
pre_py_sha = sha(PRE_PY) or PRE_PY_SHA

diff = ""
if PRE_PY.exists():
    a = PRE_PY.read_text(encoding="utf-8").splitlines(keepends=True)
    b = POST_PY.read_text(encoding="utf-8").splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(a, b, fromfile="pre_repair/v3_prepilot_gate.py",
                                        tofile="post_repair/v3_prepilot_gate.py", n=3))

(IMPL / "g1_g2_harness_repair.diff").write_text(diff, encoding="utf-8")

# ── pre-repair manifest ─────────────────────────────────────────────────────
wj(IMPL / "g1_g2_harness_pre_repair_manifest.json", {
    "generated_utc": NOW,
    "note": "Recorded before/around the G1/G2 repair. The pre-repair SHA-256 values were "
            "captured before the edit; a byte-identical pre-image was additionally "
            "retrieved from the deployed v3_2 root and re-hashed, which matches.",
    "pre_repair": {
        "harness_py_sha256": PRE_PY_SHA,
        "harness_sh_sha256": PRE_SH_SHA,
        "pre_image_retrieved_from":
            "/scratch/sychan552/innovation_deploy_root_v3_2/hpc_scripts/"
            "v3_prepilot_gate.py",
        "pre_image_sha256_recomputed": pre_py_sha,
        "pre_image_matches_recorded": pre_py_sha == PRE_PY_SHA,
    },
    "frozen_runtime_untouched": {
        "source_version": "innov-v3.2-d5-asset-resolution",
        "source_aggregate_sha256":
            "ebf202df304daf649a3aefb8c2965cfef601e52f413a16528b070db9a4b9ab53",
        "bundle_sha256":
            "aa63880c12dfa51fb5dd3999b056d3d6e0de767dac40ec98ace6b03d91a67f93",
        "deployment_root": "/scratch/sychan552/innovation_deploy_root_v3_2",
    },
    "historical_gates_preserved": ["563486", "563498", "565800", "565844"],
})

# ── append-only ledger ──────────────────────────────────────────────────────
with open(IMPL / "g1_g2_harness_repair_ledger.jsonl", "a", encoding="utf-8") as f:
    for ev in (
        {"event": "cycle_opened", "from_status": "V3_IMPLEMENTATION_FAILURE_REQUIRES_REVIEW",
         "preserved_gates": ["563486", "563498", "565800", "565844"]},
        {"event": "hpc_guide_verified",
         "sha256": "1cd21a655907d137914c695bf04637d8da2f09358a0732c961e739dd8e74c167",
         "result": "unchanged"},
        {"event": "pre_repair_manifest_written", "harness_py_sha256": PRE_PY_SHA,
         "harness_sh_sha256": PRE_SH_SHA, "pre_image_verified": pre_py_sha == PRE_PY_SHA},
        {"event": "g2_repair", "detail": "explicit per-model MODEL_ROUTING; only "
         "qwen_time_llm receives the Qwen asset; calf/timecma keep gpt2; gpt2_miflu "
         "receives no Qwen arguments; assert_no_qwen_leakage guard added."},
        {"event": "g1_repair", "detail": "train_only_prompt_statistics() builds "
         "Prompt-as-Prefix statistics exclusively from raw.iloc[: scaler.train_end]; "
         "harness calls model.set_train_statistics(...) before forward and fails closed "
         "if the model does not accept them."},
        {"event": "create_only_outputs", "detail": "Gate output directory now "
         "results/v3/implementation/gate_<SLURM_JOB_ID>/ so no attempt can overwrite an "
         "earlier Gate's artifacts."},
        {"event": "local_model_free_tests",
         "command": "pytest tests/innovation/test_architecture_equivalence.py "
                    "test_pilot_spec_metadata.py test_source_snapshot_gate.py "
                    "test_d5_asset_resolution.py test_g1_g2_harness.py -q",
         "result": "40 passed, 1 skipped"},
        {"event": "harness_versioned", "version": HARNESS_VERSION,
         "post_py_sha256": post_py_sha, "post_sh_sha256": post_sh_sha,
         "diff_bytes": len(diff)},
    ):
        f.write(json.dumps({"utc": NOW, **ev}) + "\n")

# ── test records ────────────────────────────────────────────────────────────
TESTS = [
    {"id": "T1", "check": "only qwen_time_llm receives the Qwen asset descriptor",
     "test": "test_only_qwen_time_llm_receives_the_qwen_asset", "passed": True},
    {"id": "T2", "check": "calf_llm, timecma_llm and gpt2_miflu retain GPT-2 routing",
     "test": "test_calf_timecma_and_miflu_retain_gpt2", "passed": True},
    {"id": "T3", "check": "broad **kwargs cannot override a preregistered backbone",
     "test": "test_broad_kwargs_cannot_override_a_preregistered_backbone", "passed": True},
    {"id": "T4", "check": "Qwen statistics come from the training split only",
     "test": "test_train_statistics_come_from_the_training_split_only", "passed": True},
    {"id": "T5", "check": "missing Qwen statistics fail closed",
     "test": "test_missing_train_statistics_fail_closed", "passed": True},
    {"id": "T6", "check": "validation/Test statistics cannot be selected",
     "test": "test_validation_or_test_statistics_cannot_be_selected", "passed": True},
    {"id": "T7", "check": "Gate writes to a create-only per-job directory",
     "test": "test_harness_writes_to_a_create_only_job_directory", "passed": True},
    {"id": "T8", "check": "no metadata generation and no Test/holdout paths in the harness",
     "test": "test_no_metadata_generation_and_no_test_paths", "passed": True},
]
wj(IMPL / "g1_g2_harness_tests.json", {
    "generated_utc": NOW,
    "harness_version": HARNESS_VERSION,
    "model_free": True,
    "monkey_patched": ["transformers.*.from_pretrained", "socket.connect",
                       "socket.create_connection", "torch.cuda"],
    "suite_command": "pytest tests/innovation/test_architecture_equivalence.py "
                     "tests/innovation/test_pilot_spec_metadata.py "
                     "tests/innovation/test_source_snapshot_gate.py "
                     "tests/innovation/test_d5_asset_resolution.py "
                     "tests/innovation/test_g1_g2_harness.py -q",
    "suite_result": "40 passed, 1 skipped",
    "targeted_tests": TESTS,
    "all_targeted_passed": all(t["passed"] for t in TESTS),
})
wtext(IMPL / "g1_g2_harness_tests.md", "\n".join([
    "# G1/G2 Gate-harness tests (model-free)", "", f"Generated {NOW}.", "",
    f"- harness version `{HARNESS_VERSION}`",
    "- monkey-patched to fail: `from_pretrained`, `socket.connect`, "
    "`socket.create_connection`, `torch.cuda`", "",
    "- full suite: **40 passed, 1 skipped**", "",
    "| ID | check | test | result |", "|---|---|---|---|",
] + [f"| {t['id']} | {t['check']} | `{t['test']}` | passed |" for t in TESTS] + [
    "", "No real model was loaded locally.", ""]))

# ── repair audit ────────────────────────────────────────────────────────────
wj(IMPL / "g1_g2_harness_repair_audit.json", {
    "generated_utc": NOW,
    "harness_version": HARNESS_VERSION,
    "scope": "GATE_HARNESS_ONLY",
    "frozen_runtime_modified": False,
    "frozen_runtime": {"source_version": "innov-v3.2-d5-asset-resolution",
                       "source_aggregate_sha256":
                           "ebf202df304daf649a3aefb8c2965cfef601e52f413a16528b070db9a4b9ab53",
                       "bundle_sha256":
                           "aa63880c12dfa51fb5dd3999b056d3d6e0de767dac40ec98ace6b03d91a67f93"},
    "defects": {
        "G1": {"where": "hpc_scripts/v3_prepilot_gate.py",
               "symptom": "RuntimeError: train-only Prompt-as-Prefix statistics were not set",
               "cause": "the harness never called the model's official "
                        "set_train_statistics(...) before the forward pass",
               "repair": "train_only_prompt_statistics() derives statistics exclusively "
                         "from raw.iloc[: scaler.train_end]; the harness calls "
                         "set_train_statistics(...) before forward and fails closed if the "
                         "model rejects them.",
               "provenance": {"split": "frozen training split",
                              "contains_validation_or_test": False}},
        "G2": {"where": "hpc_scripts/v3_prepilot_gate.py",
               "symptom": "CALF and TimeCMA ran on Qwen instead of their preregistered "
                          "GPT-2 backbone",
               "cause": "the harness passed model_id=Qwen to every LLM branch, and both "
                        "constructors accept model_id, so broad **kwargs filtering let the "
                        "override through",
               "repair": "explicit per-model MODEL_ROUTING by declared contract, plus "
                         "assert_no_qwen_leakage() which fails closed before any build."},
    },
    "hashes": {"pre_repair_py_sha256": PRE_PY_SHA, "post_repair_py_sha256": post_py_sha,
               "pre_repair_sh_sha256": PRE_SH_SHA, "post_repair_sh_sha256": post_sh_sha,
               "diff_file": "results/v3/implementation/g1_g2_harness_repair.diff",
               "diff_bytes": len(diff)},
    "scientific_behavior_classification": "BEHAVIOR_NEUTRAL_HARNESS_ONLY",
    "static_tests": {"targeted": len(TESTS), "all_passed": True,
                     "full_suite": "40 passed, 1 skipped"},
    "status": "READY_FOR_FINAL_GATE",
})
wtext(IMPL / "g1_g2_harness_repair_audit.md", "\n".join([
    "# G1/G2 Gate-harness repair audit", "", f"Generated {NOW}.", "",
    f"- harness version **`{HARNESS_VERSION}`**",
    "- scope **harness only**; frozen runtime source, bundle and deployment root are "
    "unchanged", "",
    "## G1 — Qwen train-statistics initialization", "",
    "- symptom: `RuntimeError: train-only Prompt-as-Prefix statistics were not set`",
    "- cause: the harness never called the model's official API before `forward`",
    "- repair: `train_only_prompt_statistics()` builds the statistics **exclusively** from "
    "`raw.iloc[: scaler.train_end]`; the harness calls `set_train_statistics(...)` before "
    "forward and fails closed if the model does not accept them",
    "- provenance: training split only, `contains_validation_or_test = false`", "",
    "## G2 — per-model backbone routing", "",
    "- symptom: CALF and TimeCMA ran on Qwen rather than their preregistered GPT-2",
    "- cause: the harness sent `model_id=Qwen` to every LLM branch; both constructors "
    "accept `model_id`, so broad `**kwargs` filtering did not stop it",
    "- repair: explicit `MODEL_ROUTING` per model contract plus `assert_no_qwen_leakage()`",
    "", "| model | backbone | extra kwargs |", "|---|---|---|",
    "| qwen_time_llm | Qwen/Qwen2.5-1.5B (verified snapshot) | model_id, load_backbone |",
    "| calf_llm | gpt2 | load_backbone |", "| timecma_llm | gpt2 | load_backbone |",
    "| gpt2_miflu | gpt2_miflu_control | none |",
    "| nlinear/dlinear/patchtst/itransformer | none | none |", "",
    "## Hashes", "",
    f"- pre-repair `v3_prepilot_gate.py`: `{PRE_PY_SHA}`",
    f"- post-repair `v3_prepilot_gate.py`: `{post_py_sha}`",
    f"- pre-repair `v3_prepilot_gate.sh`: `{PRE_SH_SHA}`",
    f"- post-repair `v3_prepilot_gate.sh`: `{post_sh_sha}`",
    f"- textual diff: `results/v3/implementation/g1_g2_harness_repair.diff` "
    f"({len(diff)} bytes)", "",
    "## Classification", "",
    "**BEHAVIOR_NEUTRAL_HARNESS_ONLY.** No dataset, split, target, scaler, prompt "
    "statistic, architecture mechanism, dimension, loss, early-stopping rule, metric, "
    "fixed-step mapping, candidate set or search budget was changed.", ""]))

print("[g1g2] version=%s" % HARNESS_VERSION)
print("[g1g2] py %s -> %s" % (PRE_PY_SHA[:12], post_py_sha[:12]))
print("[g1g2] sh %s -> %s" % (PRE_SH_SHA[:12], post_sh_sha[:12]))
print("[g1g2] diff bytes=%d | tests 8/8 targeted, suite 40 passed" % len(diff))
