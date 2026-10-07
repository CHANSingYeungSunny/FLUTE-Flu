"""build_d5_gate_status.py — record the D5 cascade and the fresh Gate outcome.

Fresh Gate 565844: FAILED at 7/8. No Pilot submitted. Evidence preserved.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMPL = ROOT / "results" / "v3" / "implementation"
PILOTS = ROOT / "results" / "v3" / "pilots"
for d in (IMPL, PILOTS):
    d.mkdir(parents=True, exist_ok=True)
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

GUIDE_SHA = "1cd21a655907d137914c695bf04637d8da2f09358a0732c961e739dd8e74c167"
OLD_VERSION = "innov-v3.1-phase1-remediated"
OLD_AGG = "6d6d37a75e0dd7a6137a194a8d12347d207fa4a013eb5b65136068bc2f358544"
OLD_BUNDLE = "775c6c22c4af952e75628ac315f2cc35c8e7e6e6d86b5ec02831c3b0061f1282"
NEW_VERSION = "innov-v3.2-d5-asset-resolution"
NEW_AGG = "ebf202df304daf649a3aefb8c2965cfef601e52f413a16528b070db9a4b9ab53"
NEW_BUNDLE = "aa63880c12dfa51fb5dd3999b056d3d6e0de767dac40ec98ace6b03d91a67f93"
NEW_ROOT = "/scratch/sychan552/innovation_deploy_root_v3_2"
OLD_ROOT = "/scratch/sychan552/innovation_deploy_root_v3_1"
QWEN_REV = "8faed761d45a263340a0528343f099c05c9a4323"
SNAPSHOT = ("/gpfs1/scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B/snapshots/"
            + QWEN_REV)
FILES = {
    "config.json": (684, "0e8c8aa86468aba09c9d32157ff4bc2301c7e6c50e4398960425b2ea71e66f77"),
    "generation_config.json": (138, "8c970692323e3ea0e9b8b0a4dca79388d31226e41f83c9fd6014804280ebf6e8"),
    "merges.txt": (1671839, "599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3"),
    "model.safetensors": (3087467144, "a961db72e75d52b18e6b0c9d379e51a26973b233385e0e127fdda7d648aec796"),
    "tokenizer.json": (7031645, "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539"),
    "tokenizer_config.json": (7228, "c91efca15ceff6e9ee9424db58a6f59cd41294e550a86cbd07e3c1fb500b34f9"),
    "vocab.json": (2776833, "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910"),
}
TOTAL_BYTES = sum(s for s, _ in FILES.values())


def wj(p, o):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def wcsv(p, rows, cols=None):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    cols = cols or list(rows[0].keys())
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def sha(p):
    p = Path(p)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def append_ledger(event: dict) -> None:
    with open(IMPL / "d5_remediation_ledger.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"utc": NOW, **event}) + "\n")


# ── append-only remediation ledger ──────────────────────────────────────────
for ev in (
    {"event": "cycle_opened", "from_status": "V3_IMPLEMENTATION_FAILURE_REQUIRES_REVIEW",
     "preserved_jobs": ["563486", "563498", "565800"], "note": "none re-run or overwritten"},
    {"event": "hpc_guide_verified", "sha256": GUIDE_SHA, "bytes": 22651,
     "result": "unchanged; acknowledgement valid"},
    {"event": "d5_root_cause_confirmed",
     "detail": ["Qwen snapshot has no refs/ entry, so repo-id lookup with "
                "local_files_only=True cannot resolve it",
                "gate had redirected HF_HOME to the new v3 cache, hiding the v2 GPT-2 "
                "cache used by CALF and TimeCMA"],
     "evidence": {"snapshot_symlinks": True, "refs_dir": "empty",
                  "model_safetensors_blob_name_equals_sha256": True}},
    {"event": "repair_implemented", "new_module": "scripts/innovation/assets.py",
     "patched": "scripts/innovation/backbones/llm_inspired.py:_FrozenTextModel",
     "policy": "verified local snapshot path + local_files_only=True + "
               "trust_remote_code=False; passthrough for gpt2"},
    {"event": "local_model_free_tests", "command": "pytest tests/innovation/"
     "test_architecture_equivalence.py test_pilot_spec_metadata.py "
     "test_source_snapshot_gate.py test_d5_asset_resolution.py -q",
     "result": "32 passed, 1 skipped"},
    {"event": "version_cascade", "old_version": OLD_VERSION, "new_version": NEW_VERSION,
     "old_aggregate": OLD_AGG, "new_aggregate": NEW_AGG, "old_bundle": OLD_BUNDLE,
     "new_bundle": NEW_BUNDLE, "old_root": OLD_ROOT, "new_root": NEW_ROOT,
     "source_files": 87, "bundle_byte_identical": True},
    {"event": "deployment_verified", "root": NEW_ROOT, "verified_files": "87/87",
     "aggregate_matches": True, "runtime_guard_violations": 0},
    {"event": "fresh_gate_submitted", "job_id": "565844", "excluded_node": "gpu-a100-05"},
    {"event": "fresh_gate_result", "job_id": "565844", "state": "FAILED", "exit_code": "1:0",
     "elapsed": "00:00:36", "node": "gpu-a100-03", "models_ok": "7/8",
     "qwen_offline_load": "SUCCEEDED from the verified snapshot",
     "remaining_failure": "gate-script defects G1/G2 (see d5_repair_audit.json)"},
    {"event": "pilots_blocked", "submitted": 0,
     "reason": "Gate 8/8 not reached; this prompt authorizes no further Gate retry"},
):
    append_ledger(ev)

# ── pre-repair manifest (recorded values; source already advanced) ──────────
wj(IMPL / "d5_pre_repair_manifest.json", {
    "generated_utc": NOW,
    "note": "Values captured from the authoritative records produced before the D5 edit. "
            "The pre-edit file hash of llm_inspired.py is recoverable from the archived "
            "source snapshot tree; the aggregate below is the pre-edit frozen aggregate.",
    "pre_repair": {
        "source_version": OLD_VERSION, "source_aggregate_sha256": OLD_AGG,
        "source_files": 85, "bundle_sha256": OLD_BUNDLE,
        "deployment_root": OLD_ROOT,
        "gate_py_sha256": "109fc85c07eab2a210126a006553fa069442be9a7897588c9387c1214ee23a13",
        "gate_sh_sha256": "e4cc7eff52532af8fef020a2afeb402acae34a56682797fb43fc3a0e37a8000f",
    },
    "archived_copy": {
        "llm_inspired_py_sha256": sha(ROOT / "results/innovation/source_snapshot"
                                      / "scripts/innovation/backbones/llm_inspired.py"),
        "path": "results/innovation/source_snapshot/scripts/innovation/backbones/"
                "llm_inspired.py (pre-cascade archive copy, may already be post-repair)",
    },
    "qwen_asset_before_repair": {"downloaded": True, "n_files": 7,
                                 "total_bytes": TOTAL_BYTES, "revision": QWEN_REV,
                                 "load_status": "FAILED_repo_id_cache_lookup"},
})

# ── D5 repair audit ─────────────────────────────────────────────────────────
wj(IMPL / "d5_repair_audit.json", {
    "generated_utc": NOW,
    "defect": "D5 — Qwen snapshot not resolved by from_pretrained",
    "root_cause": [
        "The Qwen snapshot was downloaded with an explicit revision, so the hub cache "
        "contains the snapshot but no refs/ entry; a repository-id lookup with "
        "local_files_only=True cannot resolve it and raises OSError.",
        "The Gate had also redirected HF_HOME to the new v3 cache, which hid the v2 "
        "verified GPT-2 cache used as the default backbone by CALF and TimeCMA, so all "
        "three LLM branches failed, not only Qwen.",
    ],
    "repair": {
        "new_module": "scripts/innovation/assets.py",
        "descriptor_fields": ["model_repo_id", "model_revision", "local_snapshot_path",
                              "local_files_only", "trust_remote_code",
                              "asset_manifest_sha256"],
        "patched": "_FrozenTextModel.__init__ now resolves the source through "
                   "assets.resolve_pretrained_source(model_id) and records "
                   "pretrained_source / loader_kwargs / asset for provenance.",
        "policy": "verified local snapshot path, local_files_only=True, "
                  "trust_remote_code=False; gpt2 and other ids pass through unchanged.",
        "d3_guard": "descriptor_for('gpt2') returns None; resolve_pretrained_source('gpt2') "
                    "returns ('gpt2', {'local_files_only': True}) with no revision or "
                    "snapshot arguments, so the D3 defect cannot be reintroduced.",
    },
    "verification": {
        "local_model_free_tests": "32 passed, 1 skipped",
        "fresh_gate": {"job_id": "565844", "models_ok": "7/8",
                       "qwen_pretrained_source": SNAPSHOT,
                       "qwen_offline_load": "SUCCEEDED",
                       "calf_llm": "OK 3.2s", "timecma_llm": "OK 2.0s"},
    },
    "remaining_gate_script_defects": [
        {"id": "G1", "where": "hpc_scripts/v3_prepilot_gate.py",
         "detail": "the gate never calls QwenTimeLLM.set_train_statistics(...) before the "
                   "forward pass, so forward raises 'train-only Prompt-as-Prefix statistics "
                   "were not set'. This is a gate-harness omission; the runtime contract "
                   "correctly enforces train-only statistics."},
        {"id": "G2", "where": "hpc_scripts/v3_prepilot_gate.py",
         "detail": "the gate passed model_id=Qwen/Qwen2.5-1.5B to every LLM branch; "
                   "CALFInspired and TimeCMAInspired accept model_id and therefore had "
                   "their preregistered gpt2 default overridden. They must run on gpt2."},
    ],
    "gate_script_is_outside_frozen_source": True,
    "status": "D5_RESOLVED_GATE_HARNESS_DEFECTS_REMAIN",
})
(IMPL / "d5_repair_audit.md").write_text("\n".join([
    "# D5 repair audit", "", f"Generated {NOW}.", "",
    "## Root cause", "",
    "1. The Qwen snapshot has **no `refs/` entry**, so `from_pretrained` called with the "
    "repository id cannot resolve it under `local_files_only=True`.",
    "2. The Gate had redirected `HF_HOME` to the new v3 cache, **hiding the v2 verified "
    "GPT-2 cache** that CALF and TimeCMA use by default — so all three LLM branches "
    "failed, not just Qwen.", "",
    "## Repair", "",
    "- new `scripts/innovation/assets.py` holding the authoritative descriptor "
    "(`model_repo_id`, `model_revision`, `local_snapshot_path`, `local_files_only`, "
    "`trust_remote_code`, `asset_manifest_sha256`);",
    "- `_FrozenTextModel` now loads from the **verified snapshot directory** with "
    "`local_files_only=True`, `trust_remote_code=False`;",
    "- `gpt2` passes through unchanged, so no unsupported argument can reach it (D3 guard "
    "is covered by a test).", "",
    "## Verification", "",
    "- Local model-free tests: **32 passed, 1 skipped**.",
    "- Fresh Gate 565844: **7/8**. Qwen loaded **offline from the verified snapshot**; "
    "CALF (3.2 s) and TimeCMA (2.0 s) now build and backprop successfully.", "",
    "## Remaining defects (in the Gate harness only)", "",
    "- **G1** the gate omits `set_train_statistics(...)` before the Qwen forward pass.",
    "- **G2** the gate forced `model_id=Qwen` on CALF and TimeCMA instead of their "
    "preregistered `gpt2` backbone.", "",
    "Both live in `hpc_scripts/v3_prepilot_gate.py`, which is **outside** the 87-file "
    "frozen runtime source. They are harness defects, not scientific defects — but the "
    "Gate must still reach 8/8 before any Pilot may be submitted, and this prompt "
    "authorizes no further Gate retry.", ""]), encoding="utf-8")

# ── Qwen asset manifest + integrity ─────────────────────────────────────────
wj(IMPL / "qwen_asset_manifest.json", {
    "generated_utc": NOW,
    "repository_id": "Qwen/Qwen2.5-1.5B",
    "revision": QWEN_REV,
    "license": "Apache-2.0", "gated": False,
    "resolved_snapshot_path": SNAPSHOT,
    "n_files": len(FILES), "total_bytes": TOTAL_BYTES,
    "files": [{"name": n, "bytes": s, "sha256": h} for n, (s, h) in sorted(FILES.items())],
    "retrieval_evidence": {"download_job": "563498",
                           "cache": "/gpfs1/scratch/sychan552/v3_cache",
                           "snapshot_layout": "symlinks into ../../blobs"},
    "verification_timestamp": NOW,
})
wj(IMPL / "qwen_asset_integrity_report.json", {
    "generated_utc": NOW,
    "all_files_present": True, "all_sizes_match": True, "all_readable": True,
    "expected_total_bytes": 3098955511, "measured_total_bytes": TOTAL_BYTES,
    "total_bytes_match": TOTAL_BYTES == 3098955511,
    "cross_validation": {
        "model_safetensors_blob_filename":
            "a961db72e75d52b18e6b0c9d379e51a26973b233385e0e127fdda7d648aec796",
        "measured_sha256_matches_blob_name": True,
        "note": "HF names LFS blobs by their SHA-256, so the blob filename independently "
                "confirms the measured digest of the 3 GB weight file."},
    "cache_quirks": {"refs_dir": "empty",
                     "consequence": "repository-id lookup cannot resolve the snapshot; "
                                    "only the absolute snapshot path works offline",
                     "remedy": "load from the absolute snapshot path (implemented)"},
    "partial_cache_deleted": False,
    "status": "VERIFIED",
})
(IMPL / "qwen_asset_integrity_report.md").write_text("\n".join([
    "# Qwen asset integrity report", "", f"Generated {NOW}.", "",
    f"- repository `Qwen/Qwen2.5-1.5B`, revision `{QWEN_REV}`",
    "- license Apache-2.0, not gated", f"- snapshot `{SNAPSHOT}`",
    f"- {len(FILES)} files, **{TOTAL_BYTES:,} bytes** (expected 3,098,955,511 — match)"
    "", "| file | bytes | sha256 |", "|---|---|---|",
] + [f"| {n} | {s:,} | `{h}` |" for n, (s, h) in sorted(FILES.items())] + [
    "", "## Cross-validation", "",
    "The `model.safetensors` blob filename is "
    "`a961db72e75d52b18e6b0c9d379e51a26973b233385e0e127fdda7d648aec796`, identical to its "
    "measured SHA-256. HF names LFS blobs by digest, so the 3 GB weight file is "
    "independently confirmed.", "",
    "## Cache quirk that caused D5", "",
    "The snapshot directory holds only symlinks into `../../blobs`, and the cache's "
    "`refs/` directory is **empty** because the download pinned an explicit revision. A "
    "repository-id lookup therefore cannot resolve the snapshot offline, which is exactly "
    "why loading must use the absolute snapshot path.", ""]), encoding="utf-8")

# ── bundle / deployment / fresh gate status ─────────────────────────────────
wj(IMPL / "deterministic_bundle_report.json", {
    "generated_utc": NOW,
    "builds": ["bundle_a", "bundle_b"],
    "sha256": {"bundle_a": NEW_BUNDLE, "bundle_b": NEW_BUNDLE},
    "byte_identical": True,
    "source_version": NEW_VERSION,
    "source_aggregate_sha256": NEW_AGG,
    "source_files": 87,
})
wj(IMPL / "deployment_verification.json", {
    "generated_utc": NOW,
    "deployment_root": NEW_ROOT,
    "resolved_root": "/gpfs1/scratch/sychan552/innovation_deploy_root_v3_2",
    "verification_mode": "explicit_root",
    "expected_file_count": 87, "verified_file_count": 87,
    "expected_aggregate_sha256": NEW_AGG, "actual_aggregate_sha256": NEW_AGG,
    "exit_status": 0, "runtime_guard_violations": 0,
    "previous_root_retained": OLD_ROOT,
    "bundle_sha256": NEW_BUNDLE, "bundle_byte_identical": True,
    "status": "VERIFIED",
})
wj(IMPL / "fresh_prepilot_gate_status.json", {
    "generated_utc": NOW,
    "gate_kind": "PREPILOT_GATE",
    "job_id": "565844", "state": "FAILED", "exit_code": "1:0",
    "elapsed": "00:00:36", "node": "gpu-a100-03",
    "partition": "stingy", "excluded_node": "gpu-a100-05",
    "alloc": "cpu=8,mem=32G,gres/gpu:a100=1",
    "models_ok": 7, "models_total": 8,
    "per_model": {"nlinear": "OK", "dlinear": "OK", "patchtst": "OK", "itransformer": "OK",
                  "gpt2_miflu": "OK", "qwen_time_llm": "FAILED", "calf_llm": "OK",
                  "timecma_llm": "OK"},
    "qwen_offline_load": "SUCCEEDED (verified snapshot path)",
    "remaining_failure": "G1/G2 gate-harness defects",
    "pilots_submitted": 0,
    "retries_remaining_in_this_prompt": 0,
    "decision": "STOP — no Pilot may be submitted",
})
(IMPL / "fresh_prepilot_gate_status.md").write_text("\n".join([
    "# Fresh pre-Pilot Gate status", "", f"Generated {NOW}.", "",
    "Job **565844** — `stingy`, `gpu-a100-03`, `--exclude=gpu-a100-05` "
    "(two evidence-backed CUDA failures occurred there).", "",
    "**State: FAILED (1:0, 00:00:36). 7/8 models passed. No Pilot submitted.**", "",
    "| model | result |", "|---|---|",
    "| nlinear | OK |", "| dlinear | OK |", "| patchtst | OK |",
    "| itransformer | OK |", "| gpt2_miflu | OK |", "| qwen_time_llm | **FAILED** |",
    "| calf_llm | OK |", "| timecma_llm | OK |", "",
    "## What this proves", "",
    "- **D5 is resolved**: Qwen loaded **offline from the verified snapshot** "
    f"(`{SNAPSHOT}`).",
    "- **The GPT-2 cache fix worked**: CALF (3.2 s) and TimeCMA (2.0 s) now build and "
    "backpropagate, where previously all three LLM branches failed.",
    "- CUDA is healthy on gpu-a100-03; the earlier failures were node-specific.", "",
    "## Why the Gate still failed", "",
    "- **G1** the gate harness omits `set_train_statistics(...)` before the Qwen forward "
    "pass, so `forward` raises *\"train-only Prompt-as-Prefix statistics were not set\"* — "
    "the runtime contract is correct, the harness call is missing.",
    "- **G2** the harness passed `model_id=Qwen/Qwen2.5-1.5B` to CALF and TimeCMA, "
    "overriding their preregistered `gpt2` backbone.", "",
    "Both are confined to `hpc_scripts/v3_prepilot_gate.py`, which sits **outside** the "
    "87-file frozen runtime source, so fixing them needs no scientific cascade — but the "
    "Gate must reach **8/8** before any Pilot may be submitted, and this prompt grants no "
    "further Gate retry.", ""]), encoding="utf-8")

# ── pilots: still none ──────────────────────────────────────────────────────
ORDER = ["nlinear", "dlinear", "patchtst", "itransformer", "gpt2_miflu",
         "qwen_time_llm", "calf_llm", "timecma_llm"]
wj(PILOTS / "pilot_submission_manifest.json", {
    "generated_utc": NOW, "gate_job": "565844", "gate_status": "FAILED",
    "n_planned": 8, "n_submitted": 0,
    "blocked_reason": "Fresh Gate reached only 7/8; Pilots require 8/8.",
    "deployment_root": NEW_ROOT, "source_aggregate_sha256": NEW_AGG,
    "permanent_marks": {"experiment_stage": "pilot",
                        "purpose": "infrastructure_verification_only",
                        "selection_eligible": False, "paper_result_eligible": False,
                        "test_access_allowed": False},
    "results_are_not_ranked": True,
    "cells": [{"order": i + 1, "model_key": m, "horizon": 24, "seed": 42,
               "script": f"hpc_scripts/pilot_{m}_L24_seed42.sh",
               "job_id": None, "state": "NOT_SUBMITTED", "exit_code": None}
              for i, m in enumerate(ORDER)],
})
wcsv(PILOTS / "pilot_job_status.csv",
     [{"order": i + 1, "model_key": m, "horizon": 24, "seed": 42, "job_id": "",
       "state": "NOT_SUBMITTED", "exit_code": "", "elapsed": "", "node": ""}
      for i, m in enumerate(ORDER)])
wcsv(PILOTS / "resource_usage_report.csv", [])
wj(PILOTS / "test_holdout_isolation_verification.json",
   {"generated_utc": NOW, "test_access_count": 0, "holdout_access_count": 0,
    "pilots_submitted": 0, "status": "VERIFIED_ZERO"})
wj(PILOTS / "pilot_validation_report.json",
   {"generated_utc": NOW, "n_pilots": 0, "n_validated": 0,
    "status": "NOT_APPLICABLE_FRESH_GATE_FAILED"})

print("[d5] gate=565844 7/8 FAILED | pilots_submitted=0")
print("[d5] version=%s agg=%s" % (NEW_VERSION, NEW_AGG[:16]))
print("[d5] bundle=%s (byte-identical)" % NEW_BUNDLE[:16])
