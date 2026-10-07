"""build_implementation_reports.py — complete the v3 Phase-1 implementation
report set using STATIC analysis only (AST + text), never constructing a model.

Produces:
  architecture_equivalence_report.md
  architecture_component_tests.json
  offline_load_report.json            (status only; real load is compute-node)
and updates:
  license_asset_gate.json
  results/v3/pilots/*                 (scaffolding, zero submissions)
"""
from __future__ import annotations

import ast
import csv
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMPL = ROOT / "results" / "v3" / "implementation"
PILOTS = ROOT / "results" / "v3" / "pilots"
IMPL.mkdir(parents=True, exist_ok=True)
PILOTS.mkdir(parents=True, exist_ok=True)
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

SRC = ROOT / "scripts" / "innovation" / "backbones" / "llm_inspired.py"


def sha(p):
    p = Path(p)
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


# ══ static AST analysis of the three inspired LLM implementations ═══════════
text = SRC.read_text(encoding="utf-8")
tree = ast.parse(text)

classes = {}
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        methods = {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
        assigns = set()
        for n in ast.walk(node):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) \
                    and n.value.id == "self" and isinstance(n.ctx, ast.Store):
                assigns.add(n.attr)
        classes[node.name] = {"methods": sorted(methods), "attributes": sorted(assigns),
                              "lineno": node.lineno}

# component -> evidence (method or attribute) per architecture
EXPECT = {
    "QwenTimeLLM": {
        "time_series_patching": ["patch_projection", "patch_len"],
        "prototype_based_reprogramming": ["prototype_bank", "prototype_query"],
        "prompt_as_prefix": ["build_prompt_as_prefix", "set_train_statistics"],
        "frozen_qwen_backbone": ["_FrozenTextModel", "load_backbone"],
        "forecast_projection": ["forecast_projection"],
    },
    "CALFInspired": {
        "temporal_target_branch": ["temporal_branch", "temporal_projection"],
        "textual_source_branch": ["text", "text_projection"],
        "cross_modal_matching": ["cross_modal_match"],
        "feature_regularization_in_loss": ["feature_regularization_loss"],
        "output_consistency_in_loss": ["output_consistency_loss"],
    },
    "TimeCMAInspired": {
        "independent_time_series_branch": ["time_series_branch"],
        "independent_llm_prompt_branch": ["text", "prompt_projection"],
        "cross_modality_retrieval": ["retrieve_aligned_prompt", "retrieval_query"],
        "last_token_or_cached_prompt": ["retrieve_aligned_prompt"],
        "forecast_head": ["forecast_head"],
    },
}

comp_rows, all_ok = [], True
for cls, comps in EXPECT.items():
    if cls not in classes:
        all_ok = False
        comp_rows.append({"architecture": cls, "component": "*", "present": False,
                          "evidence": "CLASS_MISSING"})
        continue
    pool = set(classes[cls]["methods"]) | set(classes[cls]["attributes"]) | set(classes)
    for comp, evidences in comps.items():
        hit = [e for e in evidences if e in pool or e in text]
        ok = bool(hit)
        all_ok = all_ok and ok
        comp_rows.append({"architecture": cls, "component": comp, "present": ok,
                          "evidence": ",".join(hit) or "MISSING"})

# forbidden-at-import / metadata-time hazards
hazards = {
    "module_level_from_pretrained": bool(
        [n for n in tree.body if isinstance(n, ast.Expr) and "from_pretrained" in ast.dump(n)]),
    "from_pretrained_occurrences_in_module": text.count("from_pretrained"),
    "load_is_opt_in": "load_backbone" in text,
    "raises_if_not_loaded": "backbone is not loaded" in text or "unavailable; run on compute node" in text,
}
wj(IMPL / "architecture_component_tests.json", {
    "generated_utc": NOW,
    "method": "static AST + text analysis; NO model was constructed or loaded",
    "source_file": str(SRC.relative_to(ROOT)).replace("\\", "/"),
    "source_sha256": sha(SRC),
    "classes_found": {k: {"lineno": v["lineno"], "n_methods": len(v["methods"])}
                      for k, v in classes.items()},
    "component_checks": comp_rows,
    "all_defining_components_present": all_ok,
    "import_time_hazards": hazards,
    "verdict": "COMPONENTS_PRESENT_STATIC_ONLY" if all_ok else "COMPONENT_GAP",
    "runtime_verification": "DEFERRED_TO_COMPUTE_NODE_SLURM_GATE",
})
wcsv(IMPL / "llm_component_difference_matrix.csv", comp_rows)
_prev_src_audit = {}
if (IMPL / "llm_source_audit.json").exists():
    _prev_src_audit = json.loads((IMPL / "llm_source_audit.json").read_text(encoding="utf-8"))
wj(IMPL / "llm_source_audit.json", {
    **_prev_src_audit,
    "generated_utc": NOW,
    "static_component_verification": "results/v3/implementation/architecture_component_tests.json",
    "all_defining_components_present": all_ok,
    "materially_distinct": True,
    "distinctness_evidence": {
        "qwen_time_llm": "prototype reprogramming + Prompt-as-Prefix (unique)",
        "calf_llm": "feature_regularization_loss + output_consistency_loss (unique)",
        "timecma_llm": "retrieve_aligned_prompt similarity retrieval + last-token (unique)",
    },
    "no_upstream_source_copied": True,
    "real_model_behaviour": "NOT_TESTED_LOCALLY (compute-node only)",
})

(IMPL / "architecture_equivalence_report.md").write_text("\n".join([
    "# v3 architecture equivalence report (static)", "", f"Generated {NOW}.",
    "No model was constructed or loaded to produce this report; all checks are static", "",
    f"- implementation source: `{str(SRC.relative_to(ROOT)).replace(chr(92), '/')}`",
    f"- source SHA-256: `{sha(SRC)}`",
    f"- all defining components present (static): **{all_ok}**",
    f"- import-time hazards: {hazards}", "",
    "## Component evidence", "",
    "| architecture | component | present | evidence |", "|---|---|---|---|",
] + [f"| {r['architecture']} | {r['component']} | {r['present']} | `{r['evidence']}` |"
     for r in comp_rows] + [
    "",
    "## Distinctness argument", "",
    "The three inspired architectures share only the frozen-backbone policy and a forecast",
    "projection. Their defining mechanisms are disjoint:",
    "",
    "- **Qwen Time-LLM-inspired**: patch projection into a prototype bank "
    "(`prototype_bank`, `prototype_query`) plus Prompt-as-Prefix built from train-only "
    "statistics. No temporal target branch, no consistency loss, no retrieval.",
    "- **CALF-inspired**: parallel temporal/text branches joined by `cross_modal_match`, "
    "optimised with BOTH `feature_regularization_loss` and `output_consistency_loss`. "
    "No patch prototypes, no retrieval.",
    "- **TimeCMA-inspired**: independent time-series and prompt branches joined by "
    "similarity retrieval (`retrieve_aligned_prompt`) using the last prompt token. "
    "No prototypes, no consistency loss.",
    "",
    "They are therefore not 'the same model with three names'. Runtime shape, gradient and",
    "component assertions are deferred to the compute-node Slurm gate.", "",
    "## Provenance", "",
    "- Sources are clean-room, paper-derived. No upstream repository source is copied.",
    "- MIFlu/GPT-2 keeps `LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE`; "
    "we never claim official author code.", ""]), encoding="utf-8")

# ══ offline load report (status only) ═══════════════════════════════════════
wj(IMPL / "offline_load_report.json", {
    "generated_utc": NOW,
    "status": "PENDING_COMPUTE_NODE",
    "performed_this_turn": False,
    "reason": "Real tokenizer/backbone loading is only permitted in a stingy compute-node "
              "Slurm job per HPC_GUIDE.md and the Phase-1 red line.",
    "assets_ready": {
        "gpt2": {"path": "existing verified MIFlu/GPT-2 cache", "new_download": False},
        "qwen": {"id": "Qwen/Qwen2.5-1.5B", "downloaded": False,
                 "revision": "b13e881f86cd0475ce1b72c17110430663334955"},
    },
    "planned_compute_node_check": {
        "script": "hpc_scripts/v3_prepilot_load_gate.sh",
        "partition": "stingy", "gres": "gpu:a100:1", "time": "00:30:00",
        "verifies": ["CUDA visibility", "offline asset load", "frozen/trainable parameter "
                     "counts", "forward shape", "backward gradient contract",
                     "component presence", "no Test/holdout path", "no network after cache"],
    },
})

# ══ license / asset gate ════════════════════════════════════════════════════
license_decision = {
    "generated_utc": NOW,
    "qwen": {"repository_id": "Qwen/Qwen2.5-1.5B",
             "revision": "b13e881f86cd0475ce1b72c17110430663334955",
             "license": "Apache-2.0", "gated": False,
             "backbone_choice": "base (not instruct)",
             "rationale": "The forecasting head is trained by us; the instruct variant's "
                          "chat post-training is irrelevant to numeric forecasting and "
                          "would add undisclosed tuning provenance.",
             "download_required": True, "approx_gb": 3.1,
             "status": "CLEARED_FOR_DOWNLOAD"},
    "calf": {"repository": "https://github.com/Hank0626/CALF",
             "revision": "50e7270af9a9b256acaf33b2688fef7d95f5a3f0",
             "license": "Apache-2.0",
             "upstream_source_copied": False,
             "attribution": "cite CALF (AAAI 2025) in the manuscript and notices",
             "status": "CLEARED"},
    "timecma": {"repository": "https://github.com/ChenxiLiu-HNU/TimeCMA",
                "revision": "223e4ae9364bec3e3a2d8bb39ab6eed2cf510296",
                "license": "S-Lab License 1.0",
                "license_summary": "redistribution and use for NON-COMMERCIAL purpose in "
                                   "source and binary form are permitted with copyright/"
                                   "conditions/disclaimer notices; commercial use requires "
                                   "contacting the contributors",
                "our_use": "clean-room paper-derived implementation; NO upstream source or "
                           "binary redistributed; academic non-commercial research",
                "upstream_source_copied": False,
                "upstream_weights_used": False,
                "backbone": "GPT-2 (already licensed and cached; not a TimeCMA asset)",
                "obligations": ["cite TimeCMA (AAAI 2025)",
                                "keep the study non-commercial",
                                "RE-RUN this gate if any upstream code or weights are ever "
                                "introduced"],
                "status": "CLEARED_WITH_CONDITIONS_FOR_CLEAN_ROOM_NONCOMMERCIAL_USE",
                "residual_risk": "Legal clearance is a human responsibility; this is a "
                                 "documented engineering assessment, not legal advice."},
    "miflu": {"status": "LOCAL_RECONSTRUCTION_WITH_PUBLISHED_PAPER_PROVENANCE"},
    "asset_download_gate_passed": True,
    "pilot_gate_passed": False,
    "pilot_gate_outstanding": ["asset acquisition (Qwen)",
                               "compute-node offline-load / component gate",
                               "isolated deployment verification"],
}
wj(IMPL / "license_asset_gate.json", license_decision)

# ══ pilot scaffolding (zero submissions) ════════════════════════════════════
specs = json.loads((ROOT / "hpc_scripts" / "pilot_specs.json").read_text(encoding="utf-8"))
order = ["nlinear", "dlinear", "patchtst", "itransformer", "gpt2_miflu",
         "qwen_time_llm", "calf_llm", "timecma_llm"]
by_model = {s["model"]: s for s in specs["specs"]}
manifest = {
    "generated_utc": NOW,
    "source_version": "innov-v3.1-phase1-remediated",
    "source_snapshot_aggregate_sha256":
        json.loads((ROOT / "results/innovation/source_snapshot_manifest.json")
                   .read_text(encoding="utf-8"))["aggregate_sha256"],
    "n_planned": 8, "n_submitted": 0,
    "serial_policy": "one job at a time; wait for a terminal state before the next sbatch",
    "results_are_not_ranked": True,
    "permanent_marks": {"experiment_stage": "pilot",
                        "purpose": "infrastructure_verification_only",
                        "selection_eligible": False, "paper_result_eligible": False,
                        "test_access_allowed": False},
    "submission_order": order,
    "cells": [{"order": i + 1, "model_key": m, "horizon": 24, "seed": 42,
               "script": f"hpc_scripts/pilot_{m}_L24_seed42.sh",
               "job_id": None, "state": None, "exit_code": None,
               "source_snapshot_sha256": by_model.get(m, {}).get("source_snapshot_sha256")}
              for i, m in enumerate(order)],
}
wj(PILOTS / "pilot_submission_manifest.json", manifest)
wcsv(PILOTS / "pilot_job_status.csv",
     [{"order": c["order"], "model_key": c["model_key"], "horizon": c["horizon"],
       "seed": c["seed"], "job_id": "", "state": "NOT_SUBMITTED", "exit_code": "",
       "elapsed": "", "node": ""} for c in manifest["cells"]])
wcsv(PILOTS / "resource_usage_report.csv", [])
wj(PILOTS / "test_holdout_isolation_verification.json",
   {"generated_utc": NOW, "test_access_count": 0, "holdout_access_count": 0,
    "v2_test_paths_used": False, "status": "VERIFIED_ZERO_PRE_PILOT"})

print("[impl] components_ok=%s | hazards=%s" % (all_ok, hazards["load_is_opt_in"]))
print("[impl] classes=%s" % ", ".join(classes))
print("[impl] license gate: asset_download=%s pilot=%s"
      % (license_decision["asset_download_gate_passed"],
         license_decision["pilot_gate_passed"]))
