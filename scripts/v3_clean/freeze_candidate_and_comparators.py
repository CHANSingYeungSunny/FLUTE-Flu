"""Freeze the final candidate (gpt2_miflu) and mandatory Test comparators
(nlinear, seasonal_naive).

Governance: this script RECOMPUTES the local preregistration file hashes and
FAILS if they drift from the frozen values already recorded in
`deferred_parent_binding.json`. It emits the four section-4 deliverables:

  final_candidate_freeze.json
  final_candidate_freeze.md
  final_comparator_freeze.json
  final_candidate_hash_manifest.json
"""
from __future__ import annotations

import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FINAL = os.path.join(ROOT, "results", "v3_clean", "final")
PREREG = os.path.join(ROOT, "results", "v3_clean", "preregistration")
ANALYSIS = os.path.join(ROOT, "results", "v3_clean", "analysis")

# Frozen hashes already recorded in deferred_parent_binding.json (authoritative).
FROZEN_EXPECTED = {
    "selection_rule": "afa7a780010aeed20fd7a2d361300ae2ce4411baeed1d458581538d3df359325",
    "selection_outcome": "f93e711288023703b7c6ed7818009e7598c70f6dc9ed4c9274691ea16f667dc4",
    "frozen_analysis_protocol": "cd229790fd0693334d79a1d63a38f06be8faf8cf30d83eb45c70603bc580fb6f",
}


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def verify_and_hash(rel: str, expected: str) -> str:
    p = os.path.join(ROOT, *rel.split("/"))
    actual = sha256_file(p)
    if actual.lower() != expected.lower():
        raise SystemExit(f"HASH DRIFT {rel}: expected {expected}, got {actual}")
    return actual


def main() -> int:
    os.makedirs(FINAL, exist_ok=True)

    # ---- recompute + cross-check the frozen governance hashes -------------
    sel_rule_h = verify_and_hash(
        "results/v3_clean/preregistration/paper_aligned_selection_rule.json",
        FROZEN_EXPECTED["selection_rule"])
    sel_out_h = verify_and_hash(
        "results/v3_clean/analysis/selection_outcome.json",
        FROZEN_EXPECTED["selection_outcome"])
    proto_h = verify_and_hash(
        "results/v3_clean/analysis/frozen_analysis_protocol.json",
        FROZEN_EXPECTED["frozen_analysis_protocol"])

    def run_keys(model: str, arm: str, seeds, suffix) -> list[str]:
        out = []
        for h in (24, 36, 48, 60):
            for s in seeds:
                tag = "seedna" if s == "n/a" else f"seed{s}"
                out.append(f"{arm}__{model}__L{h}__{tag}__{suffix}")
        return out

    seeds_full = [42, 43, 44, 45, 46, 47, 48, 49, 50, 51]

    candidate = {
        "generated_utc": "2026-09-21T00:00:00Z",
        "append_only": True,
        "no_new_scientific_result": True,
        "final_candidate": "gpt2_miflu",
        "selection_rule_identity": {
            "source": "results/v3_clean/preregistration/paper_aligned_selection_rule.json",
            "sha256": sel_rule_h,
            "ranking_metric": "average_MSE_4L (seven-variable, full-horizon, z-space)",
            "lower_is_better": True,
            "tie_break_order": ["average_MSE_4L", "average_MAE_4L", "resource cost"],
            "forbidden": ["peak_hit_ratio", "PTE/PIE", "baseline-relative ratio",
                          "(r24+r60)/2"],
        },
        "selection_outcome_identity": {
            "source": "results/v3_clean/analysis/selection_outcome.json",
            "sha256": sel_out_h,
            "winner": "gpt2_miflu",
            "winner_average_mse_4l": 0.7708721562796242,
            "runner_up": "nlinear",
            "runner_up_average_mse_4l": 1.0697672040053035,
            "paired_t": -13.3288594825976,
            "p_value": 3.1326018425874847e-07,
            "n_pairs": 10,
            "top_equivalence_set": [],
            "equivalence_triggered": False,
        },
        "frozen_analysis_protocol_identity": {
            "source": "results/v3_clean/analysis/frozen_analysis_protocol.json",
            "sha256": proto_h,
        },
        "supporting_accepted_rows": {
            "count": 40,
            "orders": list(range(161, 201)),
            "horizons": [24, 36, 48, 60],
            "seeds": seeds_full,
            "run_keys": run_keys("gpt2_miflu", "primary", seeds_full, "w1"),
        },
        "model_config_identity": {
            "model": "gpt2_miflu",
            "arm": "primary",
            "family": "llm",
            "backbone": "gpt2 (TextualInputEmbedder / gpt2_miflu adapter)",
            "text_encoder": "gpt2",
            "T": 104,
            "N": 7,
            "epochs": 20,
            "batch_size": 16,
            "lr": 0.0005,
            "patience": 7,
            "full_params": 1030056,
            "lora_trainable_params": 73728,
        },
        "base_model_identity": {
            "base_model_id": "gpt2",
            "base_model_revision": "openai-community/gpt2 (default revision, offline cached)",
            "transformers_on_hpc": "4.57.6",
            "source_version": "innov-v3.19-baseline-no-checkpoint-finalization",
            "source_manifest_sha256": "95e30137f53d3d3a10a6453f0912883e7361afaada24593bd4bce4db3ac5b313",
            "source_aggregate_sha256": "ae75b958b750e97c1ec9c0317ac80bf6fdc94ef979cfa280570540b0d889efaa",
            "gpt2_related_source_files": {
                "scripts/innovation/backbones/gpt2_miflu_adapter.py": "6dc97049c36f90d3de8f25ad641b57077a25950374b5b3f735bb72f40120a2d0",
                "scripts/innovation/backbones/llm_inspired.py": "ffbd5f5321f5f4462bc896b1b99aad9eb5e9768c5e5d8c20e31e35e3b6d50140",
                "scripts/innovation/encoders/gpt2_encoder.py": "a72b60e87a6514e07f358c1a6bc878ed50cf832be18610af6d337d31c52fe6b3",
                "scripts/miflu_model.py": "0e6bdb61213bfdcc72e6a5b2733fc891a613baeb3dc52b514997c1507bfc15ef",
                "scripts/textual_embedder.py": "fc52226fca7fa3165d13221a9d744b0bdb8fc29d56d8cfe848a42f018fc002a0",
            },
        },
        "checkpoint_identity": {
            "policy": "v3.15-compact-durable",
            "example_run": "primary__gpt2_miflu__L24__seed42__w1",
            "compact_sha256": "acace30755848ea741da4102e3556c35aea31497568f17a9168ac80a634483ef",
            "compact_bytes": 4135503,
            "source_bytes": 328585702,
            "compression_ratio": 79.45,
            "has_pretrained_backbone": False,
            "no_frozen_backbone_duplication": True,
            "reconstruction_exact": True,
            "restoration_exact": True,
            "n_keys_unequal": 0,
            "durable_root": "/home/sychan552/innovation_durable/screening",
        },
        "prompt_text_identity": {
            "config_resolved_yaml_sha256": "f8edfd3a7c5be0c13c3f167b6a6bcbd058c55294e1d3a45d1a3441c20c67c29c",
            "prompt_statistics_metadata_sha256": "d3b0bcfe82ef4b2be00f08e6d5067728cc4a72a7de49fcfca06e473db009e76f",
        },
        "input_variables": [
            "% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
            "ILITOTAL", "NUM. OF PROVIDERS", "OT",
        ],
        "scaler_identity": {
            "scaler_metadata_sha256": "51b57fd0ec7528bc4452c9065f7e86bb7cf238e714db281b68970e17c0a4e8d5",
            "train_only": True,
            "n_variables": 7,
            "fit_scope": "data[:717] train rows only",
        },
        "split_identity": {
            "split_manifest_sha256": "5e562727791119e4ff4365a5263b2a40bb7a46f8c2b0fe5d8e6124fa6e7a5cef",
            "full_rows": 1025,
            "train_end": 717,
            "val_end": 819,
            "test_end": 1025,
            "test_count": 206,
        },
        "horizons": [24, 36, 48, 60],
        "seed_policy": {
            "seeds": seeds_full,
            "n_seeds": 10,
            "policy": "deterministic inference; per-seed frozen checkpoint restored "
                      "from compact.safetensors, evaluated on Test, aggregated as "
                      "mean over seeds 42..51 within each L, matching the frozen "
                      "selection rule.",
            "deterministic_inference": True,
        },
        "software_deployment": {
            "python": "3.9.25",
            "platform": "Linux glibc2.34",
            "torch": "2.5.1",
            "transformers": "4.57.6",
            "example_job_id": 571231,
            "git_commit": "not tracked on HPC deployment (empty git_commit.txt)",
        },
        "no_change_declaration": (
            "No model, checkpoint, comparator, prompt, scaler, hyperparameter, "
            "endpoint, or rule may change after Test/Holdout access begins. This "
            "freeze is append-only and irreversible for the one-time Test phase."
        ),
    }

    comparators = {
        "generated_utc": "2026-09-21T00:00:00Z",
        "append_only": True,
        "no_new_scientific_result": True,
        "mandatory_comparator_set": {
            "purpose": "Smallest mandatory comparison set for generalization "
                       "interpretation; Test is NOT a second model-selection stage.",
            "include_exactly": ["gpt2_miflu", "nlinear", "seasonal_naive"],
        },
        "nlinear": {
            "role": "best Validation Non-LLM comparator",
            "arm": "primary",
            "family": "non_llm",
            "average_mse_4l": 1.0697672040053035,
            "supporting_accepted_rows": {
                "count": 40,
                "orders": list(range(1, 41)),
                "horizons": [24, 36, 48, 60],
                "seeds": seeds_full,
                "run_keys": run_keys("nlinear", "primary", seeds_full, "w1"),
            },
            "model_config_identity": {
                "model": "nlinear",
                "text_encoder": "none",
                "T": 104,
                "N": 7,
                "epochs": 20,
                "batch_size": 16,
                "lr": 0.0005,
                "patience": 7,
                "device": "cuda",
            },
            "checkpoint_identity": {
                "policy": "v3.15-compact-durable",
                "example_run": "primary__nlinear__L24__seed42__w1",
                "compact_sha256": "cc11cb834517d64dec02517e200b81f13e3a65ade4d9e33334ff396bc3bfaf26",
                "compact_bytes": 10224,
                "source_bytes": 11638,
                "compression_ratio": 1.14,
                "has_pretrained_backbone": False,
                "reconstruction_exact": True,
                "restoration_exact": True,
                "n_keys_unequal": 0,
                "durable_root": "/home/sychan552/innovation_durable/screening",
            },
            "source_identity": {
                "source_aggregate_sha256": "a46fdcd1738b9cc81e71ca3b07ee43cdef11a50b5f6eeee4346cbdde1b466ccc",
                "version": "innov-v3.12-gate-validator-schema-alignment",
                "note": "trained under v3.12 tooling; checkpoint reconstructs "
                        "bit-exactly under the current source (compact_manifest "
                        "reconstruction_exact=true, n_keys_unequal=0).",
            },
            "example_job_id": 570957,
        },
        "seasonal_naive": {
            "role": "deterministic seasonal reference",
            "arm": "baseline",
            "family": "reference",
            "supporting_accepted_rows": {
                "count": 4,
                "orders": [325, 326, 327, 328],
                "horizons": [24, 36, 48, 60],
                "seeds": ["n/a"],
                "run_keys": run_keys("seasonal_naive", "baseline", ["n/a"], "w1"),
            },
            "deterministic_reconstruction_identity": {
                "checkpoint_applicable": False,
                "stochastic_seed_applicable": False,
                "policy": "v3.19-baseline-no-checkpoint-durable",
                "reason": "deterministic_baseline_no_checkpoint",
                "rule": "seasonal naive: predict value from 52 weeks earlier "
                        "(clamped to the 104-week input window).",
                "source_aggregate_sha256": "ae75b958b750e97c1ec9c0317ac80bf6fdc94ef979cfa280570540b0d889efaa",
                "durable_root": "/home/sychan552/innovation_durable/screening",
            },
            "example_job_id": 573398,
        },
        "no_change_declaration": candidate["no_change_declaration"],
    }

    # ---- write JSON files -------------------------------------------------
    with open(os.path.join(FINAL, "final_candidate_freeze.json"), "w",
              encoding="utf-8") as f:
        json.dump(candidate, f, indent=2)
    with open(os.path.join(FINAL, "final_comparator_freeze.json"), "w",
              encoding="utf-8") as f:
        json.dump(comparators, f, indent=2)

    # ---- write Markdown ----------------------------------------------------
    md = []
    md.append("# Final Candidate Freeze — gpt2_miflu")
    md.append("")
    md.append("Frozen from authorized Validation evidence only. No Test/Holdout, "
              "runtime, storage, PTE/PIE, partial-horizon, or subjective criterion "
              "was used.")
    md.append("")
    md.append(f"- **Final candidate**: `gpt2_miflu` (family `llm`, arm `primary`)")
    md.append(f"- **Ranking metric**: `average_MSE_4L` (seven-variable, full-horizon, z-space, lower better)")
    md.append(f"- **Winner mean**: `{candidate['selection_outcome_identity']['winner_average_mse_4l']}`")
    md.append(f"- **Runner-up (Non-LLM)**: `nlinear` = `{candidate['selection_outcome_identity']['runner_up_average_mse_4l']}`")
    md.append(f"- **Paired t (winner vs runner)**: `{candidate['selection_outcome_identity']['paired_t']:.3f}`, p = `{candidate['selection_outcome_identity']['p_value']:.2e}`")
    md.append("")
    md.append("## Selection-rule identity")
    md.append("")
    md.append(f"- source: `{candidate['selection_rule_identity']['source']}`")
    md.append(f"- sha256: `{candidate['selection_rule_identity']['sha256']}`")
    md.append(f"- selection outcome sha256: `{candidate['selection_outcome_identity']['sha256']}`")
    md.append(f"- frozen analysis protocol sha256: `{candidate['frozen_analysis_protocol_identity']['sha256']}`")
    md.append("")
    md.append("## Supporting accepted rows")
    md.append("")
    md.append(f"- count: `{candidate['supporting_accepted_rows']['count']}` (orders 161–200, seeds 42–51, horizons 24/36/48/60)")
    md.append("")
    md.append("## Model / config identity")
    md.append("")
    for k, v in candidate["model_config_identity"].items():
        md.append(f"- `{k}`: `{v}`")
    md.append("")
    md.append("## Base model identity")
    md.append("")
    for k, v in candidate["base_model_identity"].items():
        if k == "gpt2_related_source_files":
            md.append(f"- `{k}`:")
            for fk, fv in v.items():
                md.append(f"  - `{fk}` -> `{fv}`")
        else:
            md.append(f"- `{k}`: `{v}`")
    md.append("")
    md.append("## Checkpoint identity")
    md.append("")
    for k, v in candidate["checkpoint_identity"].items():
        md.append(f"- `{k}`: `{v}`")
    md.append("")
    md.append("## Prompt / text / scaler / split / seed")
    md.append("")
    for k, v in candidate["prompt_text_identity"].items():
        md.append(f"- `{k}`: `{v}`")
    for k, v in candidate["scaler_identity"].items():
        md.append(f"- scaler `{k}`: `{v}`")
    for k, v in candidate["split_identity"].items():
        md.append(f"- split `{k}`: `{v}`")
    md.append(f"- horizons: `{candidate['horizons']}`")
    md.append(f"- seeds: `{candidate['seed_policy']['seeds']}` (n={candidate['seed_policy']['n_seeds']}, deterministic inference)")
    md.append("")
    md.append("## No-change declaration")
    md.append("")
    md.append(candidate["no_change_declaration"])
    md.append("")
    with open(os.path.join(FINAL, "final_candidate_freeze.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(md))

    # ---- hash manifest (self hashes + source hashes) ----------------------
    manifest = {
        "generated_utc": "2026-09-21T00:00:00Z",
        "purpose": "SHA-256 manifest for the final candidate and comparator freeze",
        "source_artifacts": {
            "paper_aligned_selection_rule.json": sel_rule_h,
            "selection_outcome.json": sel_out_h,
            "frozen_analysis_protocol.json": proto_h,
        },
        "freeze_files": {},
    }
    for fn in ("final_candidate_freeze.json", "final_candidate_freeze.md",
               "final_comparator_freeze.json"):
        manifest["freeze_files"][fn] = sha256_file(os.path.join(FINAL, fn))
    with open(os.path.join(FINAL, "final_candidate_hash_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("WROTE final_candidate_freeze.json")
    print("WROTE final_candidate_freeze.md")
    print("WROTE final_comparator_freeze.json")
    print("WROTE final_candidate_hash_manifest.json")
    print("selection_rule sha256 OK:", sel_rule_h)
    print("selection_outcome sha256 OK:", sel_out_h)
    print("frozen_analysis_protocol sha256 OK:", proto_h)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
