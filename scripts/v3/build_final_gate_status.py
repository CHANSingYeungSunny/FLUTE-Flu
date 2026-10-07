"""build_final_gate_status.py — record the FINAL pre-Pilot Gate outcome (job 565860).

Gate FAILED at 6/8. G1 and G2 are both proven repaired; a NEW frozen-runtime defect
(D6: GPT-2 tokenizer has no padding token) blocks CALF and TimeCMA. Fixing D6 needs
a frozen runtime-source change, so the workflow stops; no Pilot was submitted.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMPL = ROOT / "results" / "v3" / "implementation"
PILOTS = ROOT / "results" / "v3" / "pilots"
for d in (IMPL, PILOTS):
    d.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


MODELS = {
    "nlinear": "OK", "dlinear": "OK", "patchtst": "OK", "itransformer": "OK",
    "gpt2_miflu": "OK", "qwen_time_llm": "OK", "calf_llm": "FAILED",
    "timecma_llm": "FAILED",
}

wj(IMPL / "final_prepilot_gate_status.json", {
    "generated_utc": NOW,
    "gate_kind": "PREPILOT_GATE",
    "job_id": "565860",
    "state": "FAILED", "exit_code": "1:0", "elapsed": "00:00:20",
    "node": "gpu-a100-03", "partition": "stingy", "excluded_node": "gpu-a100-05",
    "alloc": "cpu=8,mem=32G,gres/gpu:a100=1",
    "harness_version": "v3-prepilot-gate-g1g2-fixed",
    "output_dir": "results/v3/implementation/gate_565860",
    "models_ok": 6, "models_total": 8, "per_model": MODELS,
    "preflight": {
        "source_files_verified": "87/87",
        "source_aggregate_sha256":
            "ebf202df304daf649a3aefb8c2965cfef601e52f413a16528b070db9a4b9ab53",
        "runtime_guard_violations": 0,
        "canonical_data_sha256":
            "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d",
        "test_access_count": 0, "holdout_access_count": 0,
        "formal_pilots_submitted_before_gate": 0,
    },
    "g1_status": "REPAIRED_AND_PROVEN",
    "g1_evidence": {"qwen_time_llm": "OK 1.7s",
                    "train_statistics_set_before_forward": True,
                    "statistics_source": "raw.iloc[: scaler.train_end]"},
    "g2_status": "REPAIRED_AND_PROVEN",
    "g2_evidence": {
        "qwen_time_llm_kwargs": {"model_id": "Qwen/Qwen2.5-1.5B",
                                 "load_backbone": True},
        "calf_llm_kwargs": {"load_backbone": True},
        "timecma_llm_kwargs": {"load_backbone": True},
        "gpt2_miflu_kwargs": None,
        "leakage_guard": "passed (no non-Qwen model received Qwen arguments)"},
    "new_defect": {
        "id": "D6",
        "where": "scripts/innovation/backbones/llm_inspired.py :: "
                 "_FrozenTextModel.encode_prompt",
        "frozen_runtime": True,
        "error": "ValueError: Asking to pad but the tokenizer does not have a padding "
                 "token. Please select a token to use as `pad_token` "
                 "(tokenizer.pad_token = tokenizer.eos_token e.g.) or add a new pad token "
                 "via tokenizer.add_special_tokens({'pad_token': '[PAD]'})",
        "why_now": "With G2 fixed, CALF and TimeCMA correctly use GPT-2. Qwen's tokenizer "
                   "has a pad token, GPT-2's does not, so the padding=True call that "
                   "worked for Qwen fails for GPT-2.",
        "not_a_harness_defect": "the harness cannot fix this without mutating the frozen "
                                "runtime model/tokenizer behaviour",
    },
    "decision": "STOP — Gate 6/8; this prompt authorizes no further Gate retry and no "
                "Pilot submission",
    "pilots_submitted": 0,
    "retries_remaining": 0,
})

(IMPL / "final_prepilot_gate_status.md").write_text("\n".join([
    "# Final pre-Pilot Gate status", "", f"Generated {NOW}.", "",
    "Job **565860** — `stingy`, `gpu-a100-03`, `--exclude=gpu-a100-05`, harness "
    "`v3-prepilot-gate-g1g2-fixed`, create-only output `gate_565860/`.", "",
    "**State: FAILED (1:0, 00:00:20). 6/8 models passed. No Pilot submitted.**", "",
    "| model | result |", "|---|---|",
] + [f"| {m} | {r} |" for m, r in MODELS.items()] + [
    "", "## G1 — repaired and proven",
    "", "`qwen_time_llm` now passes (**1.7 s**): the harness calls "
    "`set_train_statistics(...)` before `forward`, with statistics derived exclusively "
    "from the frozen training split (`raw.iloc[: scaler.train_end]`).", "",
    "## G2 — repaired and proven", "",
    "| model | backbone kwargs |", "|---|---|",
    "| qwen_time_llm | `model_id=Qwen/Qwen2.5-1.5B, load_backbone=True` |",
    "| calf_llm | `load_backbone=True` (keeps preregistered **gpt2**) |",
    "| timecma_llm | `load_backbone=True` (keeps preregistered **gpt2**) |",
    "| gpt2_miflu | none |",
    "", "The leakage guard passed: no non-Qwen model received any Qwen argument.", "",
    "## New defect D6 (frozen runtime, not the harness)", "",
    "With G2 fixed, CALF and TimeCMA correctly load GPT-2 — and then fail:",
    "",
    "```",
    "ValueError: Asking to pad but the tokenizer does not have a padding token.",
    "Please select a token to use as `pad_token` (tokenizer.pad_token =",
    "tokenizer.eos_token e.g.) or add a new pad token via",
    "tokenizer.add_special_tokens({'pad_token': '[PAD]'})",
    "```",
    "",
    "`_FrozenTextModel.encode_prompt` calls the tokenizer with `padding=True`. Qwen's "
    "tokenizer has a pad token; **GPT-2's does not**. This is a genuine defect in the "
    "frozen runtime source, so per the repair scope it cannot be patched by the harness.",
    "",
    "## Decision", "",
    "Gate reached only 6/8. This prompt authorizes **no further Gate retry** and no "
    "Pilot submission. Evidence for all five Gate jobs is preserved.", ""]),
    encoding="utf-8")

ORDER = ["nlinear", "dlinear", "patchtst", "itransformer", "gpt2_miflu",
         "qwen_time_llm", "calf_llm", "timecma_llm"]
wj(PILOTS / "pilot_submission_manifest.json", {
    "generated_utc": NOW, "gate_job": "565860", "gate_status": "FAILED",
    "gate_models_ok": "6/8", "n_planned": 8, "n_submitted": 0,
    "blocked_reason": "Final Gate reached only 6/8 (frozen-runtime defect D6).",
    "deployment_root": "/scratch/sychan552/innovation_deploy_root_v3_2",
    "source_aggregate_sha256":
        "ebf202df304daf649a3aefb8c2965cfef601e52f413a16528b070db9a4b9ab53",
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
    "status": "NOT_APPLICABLE_FINAL_GATE_FAILED"})

with open(IMPL / "g1_g2_harness_repair_ledger.jsonl", "a", encoding="utf-8") as f:
    for ev in (
        {"event": "harness_uploaded", "root":
            "/scratch/sychan552/innovation_deploy_root_v3_2",
         "remote_py_sha256":
            "942804cc2b415a1c8ca02dd981d216ff658b991fadbd318eb36f3046fc025758",
         "remote_sh_sha256":
            "de0382f68c7d4aa240f19545a91dc8b2c0a4254c0cd4252cf51b746e2d6a8848",
         "matches_local": True},
        {"event": "gate_565844_outputs_archived",
         "path": "results/v3/implementation/gate_565844/",
         "files": ["architecture_component_tests.json", "offline_load_report.json",
                   "weight_and_asset_manifest.json"]},
        {"event": "final_gate_submitted", "job_id": "565860",
         "excluded_node": "gpu-a100-05"},
        {"event": "final_gate_result", "job_id": "565860", "state": "FAILED",
         "exit_code": "1:0", "elapsed": "00:00:20", "node": "gpu-a100-03",
         "models_ok": "6/8", "g1": "REPAIRED_AND_PROVEN", "g2": "REPAIRED_AND_PROVEN",
         "new_defect": "D6 GPT-2 tokenizer has no padding token (frozen runtime)"},
        {"event": "pilots_blocked", "submitted": 0,
         "reason": "Gate 6/8; no further Gate retry authorized"},
    ):
        f.write(json.dumps({"utc": NOW, **ev}) + "\n")

print("[final] gate=565860 6/8 FAILED | pilots_submitted=0 | D6 in frozen runtime")
