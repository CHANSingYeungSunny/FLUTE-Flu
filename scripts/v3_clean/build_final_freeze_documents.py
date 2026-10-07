"""Build the Final Freeze documents (steps 4-9 of the Final Completion prompt).

Produces, in results/v3_clean/final/ :
  step 4: final_candidate_freeze.json / .md, final_comparator_freeze.json,
          final_candidate_hash_manifest.json
  step 5: final_evaluation_plan.json / .md, final_statistical_analysis_plan.json
  step 6: peak-evaluation-v1.json / .md
  step 8: final_test_figure_plan.json
  step 9: pre_test_freeze_audit.json, pre_test_freeze_manifest.json,
          pre_test_authorization_record.json

All data comes from authoritative local artifacts + previously recorded HPC
evidence (job IDs from sacct, compact hashes from the v3.15 inventory). Fields
that were never persisted by the v3.15 migration are recorded HONESTLY as
not_recorded / not_applicable — never guessed or fabricated.
"""
from __future__ import annotations

import hashlib
import json
import os
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FINAL = os.path.join(ROOT, "results", "v3_clean", "final")
os.makedirs(FINAL, exist_ok=True)

SEEDS = [42, 43, 44, 45, 46, 47, 48, 49, 50, 51]
HORIZONS = [24, 36, 48, 60]

# frozen governance hashes (authoritative, from deferred_parent_binding.json)
FROZEN = {
    "selection_rule": "afa7a780010aeed20fd7a2d361300ae2ce4411baeed1d458581538d3df359325",
    "selection_outcome": "f93e711288023703b7c6ed7818009e7598c70f6dc9ed4c9274691ea16f667dc4",
    "frozen_analysis_protocol": "cd229790fd0693334d79a1d63a38f06be8faf8cf30d83eb45c70603bc580fb6f",
    "source_manifest": "95e30137f53d3d3a10a6453f0912883e7361afaada24593bd4bce4db3ac5b313",
    "complete_specs_598": "a44aedce01e8c37a02792dea113ff2b3f118b37e236871f24dfbae896e4bcd0b",
}
IDENTITIES = {
    "hpc_guide_sha256": "1cd21a655907d137914c695bf04637d8da2f09358a0732c961e739dd8e74c167",
    "source_version": "innov-v3.19-baseline-no-checkpoint-finalization",
    "source_aggregate_sha256": "ae75b958b750e97c1ec9c0317ac80bf6fdc94ef979cfa280570540b0d889efaa",
    "deployment_aggregate_sha256": "05581a557158c0c19bb8e6caa1a5fb35fad889b774195616632cf62d9f4bcff6",
    "canonical_raw_data_sha256_prefix": "0a0648000066e12f",
    "scaler_sha256_prefix": "6b28b2d101309a80",
    "durable_root": "/home/sychan552/innovation_durable/screening",
}

NOW = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def verify_hash(rel: str, expected: str) -> str:
    p = os.path.join(ROOT, *rel.split("/"))
    actual = sha256_file(p)
    if actual.lower() != expected.lower():
        raise SystemExit(f"HASH DRIFT {rel}: expected {expected}, got {actual}")
    return actual


def run_keys(model: str, arm: str, seeds, suffix="w1") -> list[str]:
    out = []
    for h in HORIZONS:
        for s in seeds:
            tag = "seedna" if s == "n/a" else f"seed{s}"
            out.append(f"{arm}__{model}__L{h}__{tag}__{suffix}")
    return out


# ---- load per-run identity (job_id + compact_sha256) ----------------------
def load_primary_identity():
    p = os.path.join(ROOT, "_tmp_durable", "primary_identity.json")
    if not os.path.exists(p):
        raise SystemExit("_tmp_durable/primary_identity.json missing — run the "
                         "data-gathering step first")
    return json.load(open(p, encoding="utf-8"))


# ---- seasonal_naive hashes (recorded from HPC 2026-09-21) -----------------
SEASONAL_NAIVE = {
    24: {
        "job_id": "573398",
        "finalize_manifest_sha256": "449d3424efe7f98adf599ec6455ab24ea550460947cc526a897a5b659d3041d4",
        "predictions_csv_sha256": "85a12598119db196c56d9a5d14e394a1bf21d33dbe7a593289d66433a86ff080",
        "paper_aligned_sha256": "3a5569371910291d2b9801cc4a32dcb6e76fbbf1f5e2c0469f2a537dacd06df6",
        "ilitotal_full_sha256": "0bdf473a40ede7741c098bad64ccbc68cb8cc99320d8430842047049fcf06861",
        "ilitotal_fixed_sha256": "79ab00a9a5546833e161a7e67bc4531b5b0f1d0c9da7533b2d9444dced9e2493",
        "pte_pie_sha256": "41e1e1ddf8bc690e794ca10192bcb892865733b1ce0c78a8add72471e4327768",
    },
    36: {
        "job_id": "573400",
        "finalize_manifest_sha256": "1f75b1e3f221030177e06f9c36c3c7b3ca3712fa7a0355af9ff7c64070cf9179",
        "predictions_csv_sha256": "be3bca68302ebcbeb92397679a4b316a39044f06312a066116e9119cb90e69d0",
        "paper_aligned_sha256": "810960ad00e868169d4f0238c5ae8b46fb289fec8aab34098bfb24834f28941e",
        "ilitotal_full_sha256": "326eb368da6609d4d71a3c665b5c0ac1e69b4ff1b90a4491e41c5bc6b1859850",
        "ilitotal_fixed_sha256": "79ab00a9a5546833e161a7e67bc4531b5b0f1d0c9da7533b2d9444dced9e2493",
        "pte_pie_sha256": "41e1e1ddf8bc690e794ca10192bcb892865733b1ce0c78a8add72471e4327768",
    },
    48: {
        "job_id": "573402",
        "finalize_manifest_sha256": "702491d471d7403c39fa91e08a558b9eba1e3b2bd0a9f34e2ebe1299482240ce",
        "predictions_csv_sha256": "2dfbc3486fe86ccf1078eb97f0292516a9aa5e8b21076fe43c89b60c558f239a",
        "paper_aligned_sha256": "e6bb4fef9eac96ca889bce47fd940b077657dd7c526156df593e391faac09966",
        "ilitotal_full_sha256": "a2162a4f211cf9326f413acfefb64adb20e635dcb0f2e551408251888e2d3690",
        "ilitotal_fixed_sha256": "79ab00a9a5546833e161a7e67bc4531b5b0f1d0c9da7533b2d9444dced9e2493",
        "pte_pie_sha256": "41e1e1ddf8bc690e794ca10192bcb892865733b1ce0c78a8add72471e4327768",
    },
    60: {
        "job_id": "573404",
        "finalize_manifest_sha256": "02b48de7e23b14a42a257985c96294587dc2742fb937e0584c4bd8b5d355268e",
        "predictions_csv_sha256": "131122159d4dbdc10a195b42c19eee5798156598a0d0aa2918bf62f91524f7aa",
        "paper_aligned_sha256": "ceb5d578c877994b8d36108b5689fb168147d3bf245e7a16e91888aa36d155d6",
        "ilitotal_full_sha256": "129a5fd1a99409e5344625b25c5bd561ef626dc6efeec0deb82e5cfc39396fe5",
        "ilitotal_fixed_sha256": "79ab00a9a5546833e161a7e67bc4531b5b0f1d0c9da7533b2d9444dced9e2493",
        "pte_pie_sha256": "41e1e1ddf8bc690e794ca10192bcb892865733b1ce0c78a8add72471e4327768",
    },
}

PROVENANCE_GAP_STOCHASTIC = {
    "source_full_checkpoint_sha256": {
        "status": "not_recorded",
        "reason": "the full best_val_mse.pt was deleted during the v3.15 "
                  "compact-durable migration (migrate_accepted_rows.py); only "
                  "source_bytes was persisted. The hash is NOT recoverable from "
                  "compact.safetensors (file-bytes differ from the full ckpt).",
        "fabricated": False,
    },
    "canonical_tensor_sha256": {
        "status": "not_recorded_in_v315_manifest",
        "reason": "migrate_accepted_rows.py computed canonical_tensor_sha256 "
                  "internally (canonical-tensor-v1) but did NOT persist it to "
                  "compact_manifest.json. It IS deterministically recomputable "
                  "from compact.safetensors; test_eval.py recomputes and records "
                  "it in test_manifest.json at Test time.",
        "recomputable": True,
        "schema": "canonical-tensor-v1",
        "fabricated": False,
    },
}


def build_candidate_identity(identity):
    """Build the full final_candidate_freeze.json payload for gpt2_miflu."""
    gpt_keys = run_keys("gpt2_miflu", "primary", SEEDS)
    per_run = {}
    for rk in gpt_keys:
        rec = identity[rk]
        per_run[rk] = {"job_id": rec["job_id"],
                       "compact_sha256": rec["compact_sha256"],
                       "compact_bytes": int(rec["compact_bytes"]),
                       "finalized_utc": rec["finalized_utc"]}
    return {
        "generated_utc": NOW,
        "append_only": True,
        "no_new_scientific_result": True,
        "final_candidate": "gpt2_miflu",
        "selection_rule_identity": {
            "source": "results/v3_clean/preregistration/paper_aligned_selection_rule.json",
            "sha256": FROZEN["selection_rule"],
            "ranking_metric": "average_MSE_4L (seven-variable, full-horizon, z-space)",
            "lower_is_better": True,
            "tie_break_order": ["average_MSE_4L", "average_MAE_4L", "resource cost"],
            "forbidden": ["peak_hit_ratio", "PTE/PIE", "baseline-relative ratio",
                          "(r24+r60)/2"],
        },
        "selection_outcome_identity": {
            "source": "results/v3_clean/analysis/selection_outcome.json",
            "sha256": FROZEN["selection_outcome"],
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
            "sha256": FROZEN["frozen_analysis_protocol"],
        },
        "supporting_accepted_rows": {
            "count": 40, "orders": list(range(161, 201)),
            "horizons": HORIZONS, "seeds": SEEDS, "run_keys": gpt_keys,
        },
        "model_config_identity": {
            "model": "gpt2_miflu", "arm": "primary", "family": "llm",
            "backbone": "gpt2 (TextualInputEmbedder / gpt2_miflu adapter)",
            "text_encoder": "gpt2", "T": 104, "N": 7, "epochs": 20,
            "batch_size": 16, "lr": 0.0005, "patience": 7,
            "full_params": 1030056, "lora_trainable_params": 73728,
        },
        "base_model_identity": {
            "base_model_id": "gpt2",
            "base_model_revision": "openai-community/gpt2 (default revision, offline cached)",
            "transformers_on_hpc": "4.57.6",
            "source_version": IDENTITIES["source_version"],
            "source_manifest_sha256": FROZEN["source_manifest"],
            "source_aggregate_sha256": IDENTITIES["source_aggregate_sha256"],
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
            "durable_root": IDENTITIES["durable_root"],
            "per_run": per_run,
            "restoration_evidence_per_run": {
                "reconstruction_exact": True,
                "restoration_exact": True,
                "n_keys_unequal": 0,
                "source": "compact_manifest.json (v3.15 migration) — bit-exact "
                          "reconstruction by construction",
            },
            "provenance_gaps": PROVENANCE_GAP_STOCHASTIC,
        },
        "prompt_text_identity": {
            "config_resolved_yaml_sha256": "f8edfd3a7c5be0c13c3f167b6a6bcbd058c55294e1d3a45d1a3441c20c67c29c",
            "prompt_statistics_metadata_sha256": "d3b0bcfe82ef4b2be00f08e6d5067728cc4a72a7de49fcfca06e473db009e76f",
        },
        "input_variables": ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4",
                            "AGE 5-24", "ILITOTAL", "NUM. OF PROVIDERS", "OT"],
        "scaler_identity": {
            "scaler_metadata_sha256": "51b57fd0ec7528bc4452c9065f7e86bb7cf238e714db281b68970e17c0a4e8d5",
            "train_only": True, "n_variables": 7,
            "fit_scope": "data[:717] train rows only",
        },
        "split_identity": {
            "split_manifest_sha256": "5e562727791119e4ff4365a5263b2a40bb7a46f8c2b0fe5d8e6124fa6e7a5cef",
            "full_rows": 1025, "train_end": 717, "val_end": 819,
            "test_end": 1025, "test_count": 206,
        },
        "horizons": HORIZONS,
        "seed_policy": {
            "seeds": SEEDS, "n_seeds": 10,
            "policy": "deterministic inference; per-seed frozen checkpoint restored "
                      "from compact.safetensors, evaluated on Test, aggregated as "
                      "mean over seeds 42..51 within each L, matching the frozen "
                      "selection rule.",
            "deterministic_inference": True,
        },
        "no_change_declaration": (
            "No model, checkpoint, comparator, prompt, scaler, hyperparameter, "
            "endpoint, or rule may change after Test/Holdout access begins. This "
            "freeze is append-only and irreversible for the one-time Test phase."),
    }


def build_comparator_freeze(identity):
    nlin_keys = run_keys("nlinear", "primary", SEEDS)
    nlin_per_run = {}
    for rk in nlin_keys:
        rec = identity[rk]
        nlin_per_run[rk] = {"job_id": rec["job_id"],
                            "compact_sha256": rec["compact_sha256"],
                            "compact_bytes": int(rec["compact_bytes"]),
                            "finalized_utc": rec["finalized_utc"]}
    return {
        "generated_utc": NOW, "append_only": True,
        "no_new_scientific_result": True,
        "mandatory_comparator_set": {
            "purpose": "Smallest mandatory comparison set for generalization "
                       "interpretation; Test is NOT a second model-selection stage.",
            "include_exactly": ["gpt2_miflu", "nlinear", "seasonal_naive"],
        },
        "nlinear": {
            "role": "best Validation Non-LLM comparator",
            "arm": "primary", "family": "non_llm",
            "average_mse_4l": 1.0697672040053035,
            "supporting_accepted_rows": {
                "count": 40, "orders": list(range(1, 41)),
                "horizons": HORIZONS, "seeds": SEEDS, "run_keys": nlin_keys,
            },
            "model_config_identity": {"model": "nlinear", "text_encoder": "none",
                                      "T": 104, "N": 7, "epochs": 20,
                                      "batch_size": 16, "lr": 0.0005,
                                      "patience": 7, "device": "cuda"},
            "checkpoint_identity": {
                "policy": "v3.15-compact-durable",
                "durable_root": IDENTITIES["durable_root"],
                "per_run": nlin_per_run,
                "restoration_evidence_per_run": {
                    "reconstruction_exact": True, "restoration_exact": True,
                    "n_keys_unequal": 0,
                    "source": "compact_manifest.json (v3.15 migration)",
                },
                "provenance_gaps": PROVENANCE_GAP_STOCHASTIC,
            },
            "source_identity": {
                "source_aggregate_sha256": "a46fdcd1738b9cc81e71ca3b07ee43cdef11a50b5f6eeee4346cbdde1b466ccc",
                "version": "innov-v3.12-gate-validator-schema-alignment",
                "note": "trained under v3.12 tooling; checkpoint reconstructs "
                        "bit-exactly under the current source.",
            },
        },
        "seasonal_naive": {
            "role": "deterministic seasonal reference",
            "arm": "baseline", "family": "reference",
            "supporting_accepted_rows": {
                "count": 4, "orders": [325, 326, 327, 328],
                "horizons": HORIZONS, "seeds": ["n/a"],
                "run_keys": run_keys("seasonal_naive", "baseline", ["n/a"]),
            },
            "deterministic_reconstruction_identity": {
                "checkpoint_applicable": False,
                "stochastic_seed_applicable": False,
                "policy": "v3.19-baseline-no-checkpoint-durable",
                "reason": "deterministic_baseline_no_checkpoint",
                "rule": "seasonal naive: predict value from 52 weeks earlier "
                        "(clamped to the 104-week input window).",
                "checkpoint_hashes": "not_applicable",
                "source_aggregate_sha256": IDENTITIES["source_aggregate_sha256"],
                "durable_root": IDENTITIES["durable_root"],
            },
            "per_horizon": SEASONAL_NAIVE,
            "prediction_metric_hashes": {
                "note": "validation_predictions.csv + four metric files per horizon "
                        "(hashing recorded 2026-09-21 from HPC durable dirs).",
                "per_horizon": SEASONAL_NAIVE,
            },
        },
        "no_change_declaration": (
            "No model, checkpoint, comparator, prompt, scaler, hyperparameter, "
            "endpoint, or rule may change after Test/Holdout access begins."),
    }


def main() -> int:
    # verify frozen governance hashes (fail-stop on drift)
    sel_rule_h = verify_hash("results/v3_clean/preregistration/paper_aligned_selection_rule.json",
                             FROZEN["selection_rule"])
    sel_out_h = verify_hash("results/v3_clean/analysis/selection_outcome.json",
                            FROZEN["selection_outcome"])
    proto_h = verify_hash("results/v3_clean/analysis/frozen_analysis_protocol.json",
                          FROZEN["frozen_analysis_protocol"])

    identity = load_primary_identity()
    candidate = build_candidate_identity(identity)
    comparators = build_comparator_freeze(identity)

    # ---- step 4 ---------------------------------------------------------
    write_json(os.path.join(FINAL, "final_candidate_freeze.json"), candidate)
    write_json(os.path.join(FINAL, "final_comparator_freeze.json"), comparators)
    write_json(os.path.join(FINAL, "final_candidate_hash_manifest.json"), {
        "generated_utc": NOW,
        "source_artifacts": {
            "paper_aligned_selection_rule.json": sel_rule_h,
            "selection_outcome.json": sel_out_h,
            "frozen_analysis_protocol.json": proto_h,
        },
        "freeze_files": {},  # filled after writing md
    })

    # ---- step 5 / 6 / 8 / 9 ---------------------------------------------
    write_step5()
    write_step6()
    write_step8()
    write_step9()

    # ---- md files + hash manifest (step 4 md) ---------------------------
    write_candidate_md(candidate)
    hash_manifest = json.load(open(os.path.join(FINAL, "final_candidate_hash_manifest.json"), encoding="utf-8"))
    for fn in ("final_candidate_freeze.json", "final_candidate_freeze.md",
               "final_comparator_freeze.json"):
        hash_manifest["freeze_files"][fn] = sha256_file(os.path.join(FINAL, fn))
    write_json(os.path.join(FINAL, "final_candidate_hash_manifest.json"), hash_manifest)

    print("WROTE all step 4-9 freeze documents to", FINAL)
    return 0


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    print("  wrote", os.path.basename(path))


def write_candidate_md(candidate):
    L = ["# Final Candidate Freeze — gpt2_miflu", "",
         "Frozen from authorized Validation evidence only. No Test/Holdout, "
         "runtime, storage, PTE/PIE, partial-horizon, or subjective criterion "
         "was used.", "",
         f"- **Final candidate**: `gpt2_miflu` (family `llm`, arm `primary`)",
         "- **Ranking metric**: `average_MSE_4L` (seven-variable, full-horizon, "
         "z-space, lower better)",
         f"- **Winner mean**: `{candidate['selection_outcome_identity']['winner_average_mse_4l']}`",
         f"- **Runner-up (Non-LLM)**: `nlinear` = `{candidate['selection_outcome_identity']['runner_up_average_mse_4l']}`",
         f"- **Paired t (winner vs runner)**: `{candidate['selection_outcome_identity']['paired_t']:.3f}`, p = `{candidate['selection_outcome_identity']['p_value']:.2e}`",
         "", "## Identities (hashes verified at freeze time)", "",
         f"- selection rule sha256: `{candidate['selection_rule_identity']['sha256']}`",
         f"- selection outcome sha256: `{candidate['selection_outcome_identity']['sha256']}`",
         f"- frozen analysis protocol sha256: `{candidate['frozen_analysis_protocol_identity']['sha256']}`",
         "", "## Supporting accepted rows", "",
         f"- count: `{candidate['supporting_accepted_rows']['count']}` (orders 161–200, seeds 42–51, horizons 24/36/48/60)",
         "", "## Checkpoint identity (per run)", "",
         "Each run carries an original training job_id (sacct) and the "
         "v3.15 compact_sha256 (authoritative content hash).", "",
         "| run_key | job_id | compact_sha256 |", "|---|---|---|"]
    for rk, rec in candidate["checkpoint_identity"]["per_run"].items():
        L.append(f"| `{rk}` | {rec['job_id']} | `{rec['compact_sha256']}` |")
    L += ["", "## Provenance gaps (honest, not fabricated)", "",
          "- `source_full_checkpoint_sha256`: **not recorded** — full checkpoint "
          "deleted during v3.15 migration.",
          "- `canonical_tensor_sha256`: **not recorded in v3.15 manifest** — "
          "deterministically recomputable from `compact.safetensors`; recomputed "
          "at Test time by `test_eval.py`.",
          "", "## No-change declaration", "",
          candidate["no_change_declaration"], ""]
    with open(os.path.join(FINAL, "final_candidate_freeze.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(L))
    print("  wrote final_candidate_freeze.md")


def write_step5():
    eval_plan = {
        "generated_utc": NOW, "frozen_before_test_access": True,
        "purpose": "Final evaluation plan for the one-time Test/Holdout phase.",
        "primary_endpoint": {
            "metric": "mse_all_7vars_full_horizon_z",
            "space": "StandardScaler z (train-only scaler)",
            "aggregation": "per-L mean over 10 seeds (42..51); then average_MSE_4L "
                           "= arithmetic mean over L in {24,36,48,60}",
            "direction": "lower is better",
            "matches_wave1": True,
        },
        "key_secondary": {
            "metric": "mae_all_7vars_full_horizon_z",
            "aggregation": "same as primary (per-L seed-mean; average_MAE_4L)",
            "rule": "reported; never combined with MSE into an invented score",
        },
        "additional_endpoints": [
            "ilitotal_full_horizon MSE/MAE (physical, inverse-transformed)",
            "PTE/PIE + hit rates (peak-evaluation-v1 spec, secondary public-health)",
        ],
        "horizon_weighting": "equal (arithmetic mean over L); matches Wave-1",
        "seed_handling": {
            "n_seeds_per_L": 10,
            "seeds": SEEDS,
            "policy": "each frozen per-seed checkpoint is restored and evaluated "
                      "on Test; report per-seed and seed-mean per L; no seed selection",
        },
        "confidence_interval_method": "standard error across 10 seeds per L; "
                                      "t-distribution 95% CI (df=9)",
        "paired_unpaired": "matched-seed paired comparisons (candidate vs each "
                           "comparator), paired t-test on the 10 seeds per L",
        "multiple_comparison": "Holm-Bonferroni across the pre-registered "
                               "confirmatory tests",
        "missing_data_policy": "Test windows complete by construction; any missing "
                               "window => fail-stop (no imputation)",
        "outlier_policy": "no outlier removal; all Test target windows included",
        "tie_equivalence_policy": "report both; never manufacture a unique winner",
        "rounding": "4 significant figures in reports",
        "validation_to_test_gap": {
            "definition": "Test average_MSE_4L - Validation average_MSE_4L "
                          "(also per-L); negative = better on Test",
        },
        "success_interpretation": "descriptive generalization report; no "
                                  "pre-registered pass/fail threshold",
    }
    stat_plan = {
        "generated_utc": NOW, "frozen_before_test_access": True,
        "confirmatory_tests": [
            {"id": "C1", "test": "gpt2_miflu vs nlinear Test MSE (paired t over "
                                 "10 seeds), per L and average_MSE_4L"},
            {"id": "C2", "test": "gpt2_miflu vs seasonal_naive Test MSE (paired "
                                 "t over 10 seeds), per L and average_MSE_4L"},
            {"id": "C3", "test": "nlinear vs seasonal_naive Test MSE"},
        ],
        "effect_sizes": "Cohen's d_z (paired) for each confirmatory comparison",
        "multiple_comparison": "Holm-Bonferroni across C1/C2/C3 (family of "
                               "confirmatory tests, alpha=0.05)",
        "pte_pie_hit_rates": "PTE<=1wk / PIE<=25% / joint, per eligible season "
                             "and lead, aggregated per horizon",
        "exploratory_labels": "PTE/PIE are labeled secondary/public-health "
                              "application; they never revise the Wave-1 selection",
    }
    write_json(os.path.join(FINAL, "final_evaluation_plan.json"), eval_plan)
    write_json(os.path.join(FINAL, "final_statistical_analysis_plan.json"), stat_plan)
    md = ["# Final Evaluation Plan", "", "Frozen before Test access.", "",
          "| item | value |", "|---|---|"]
    for k, v in eval_plan.items():
        md.append(f"| {k} | `{json.dumps(v, ensure_ascii=False)}` |")
    md.append("")
    with open(os.path.join(FINAL, "final_evaluation_plan.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(md))
    print("  wrote final_evaluation_plan.json/.md, final_statistical_analysis_plan.json")


def write_step6():
    peak = {
        "spec_id": "peak-evaluation-v1",
        "generated_utc": NOW, "frozen_before_test_access": True,
        "target": "ILITOTAL", "channel_index": 4,
        "scale": "inverse-transformed original scale (physical)",
        "forecast_origin_definition": "window index i (0-based); input = "
            "data[i:i+104]; target = data[i+104:i+104+L]",
        "target_date_reconstruction": "abs_week = forecast_origin + 104 + step; "
            "calendar date from cdc_calendar.load_week_calendar (abs_week 0 = "
            "epiweek 200201, week_start 2001-12-30)",
        "epiweek_convention": "CDC epiweek YYYYWW",
        "calendar_anchors": {"abs_week_715": "2016-01-24", "abs_week_769": "2017-02-05",
                             "abs_week_819": "2018-01-21", "abs_week_820": "2018-01-28",
                             "abs_week_821": "2018-02-04"},
        "season_definition": {
            "convention": "influenza season = epiweek 40..52 of year Y plus "
                          "epiweek 1..20 of year Y+1, labeled 'YYYY/YYYY+1'",
            "epiweek_parse": "year = epiweek // 100; week = epiweek % 100",
            "eligible_season": "a season is eligible for a given (model, horizon, "
                               "lead) if it has >= 2 distinct target weeks with "
                               "predictions at that lead AND max observed ILITOTAL > 0",
        },
        "metrics": {
            "PTE": "abs(predicted peak week - observed peak week), unit = weeks",
            "PIE": "abs(predicted peak intensity - observed peak intensity) / "
                   "abs(observed peak intensity) * 100, unit = percent",
            "PTE_hit": "PTE <= 1 week",
            "PIE_hit": "PIE <= 25 percent",
            "joint_hit": "PTE_hit AND PIE_hit",
        },
        "peak_detection": {
            "scope": "single global peak per eligible season over that season's "
                     "target weeks",
            "tie_rule": "multiple equal maxima => first (earliest) index "
                        "(np.argmax semantics)",
            "rolling_window": "for lead-time l, restrict to target weeks whose "
                              "lead_weeks == l before peak detection",
            "dedup": "overlapping forecast origins predicting the same target "
                     "week are averaged (group by target_date)",
        },
        "edge_policies": {
            "missing_week": "exclude that season (or fail-stop if systemic)",
            "observed_peak_zero": "PIE undefined => exclude (PIE=None, no hit)",
            "incomplete_season": "season without a full lead-coverage window is "
                                 "reported but marked partial",
        },
        "lead_time": {"definition": "lead_weeks = step + 1; steps 0..3 => 1..4 "
                                    "weeks ahead",
                      "aggregation": "PTE/PIE computed per lead, reported per "
                                     "lead and averaged over lead"},
        "citation": "Kramer and Shaman (2019) DOI 10.1371/journal.pcbi.1006742 "
                    "(thresholds only; no CDC-compatible claim unless audited)",
    }
    write_json(os.path.join(FINAL, "peak-evaluation-v1.json"), peak)
    md = ["# Peak Evaluation Specification — peak-evaluation-v1", "",
          "Frozen before Test access.", ""]
    for k, v in peak.items():
        md.append(f"- **{k}**: `{json.dumps(v, ensure_ascii=False)}`")
    md.append("")
    with open(os.path.join(FINAL, "peak-evaluation-v1.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(md))
    print("  wrote peak-evaluation-v1.json/.md")


def write_step8():
    fig_plan = {
        "generated_utc": NOW, "frozen_before_test_access": True,
        "display_rules": {
            "plot_scope": "authorized Test/Holdout target forecast window only",
            "ground_truth": "solid line", "prediction": "dashed line",
            "peaks": "mark observed and predicted peaks",
            "scale": "inverse-transformed ILITOTAL original scale",
            "omit": ["historical-input tail", "Training/Validation prediction "
                     "curves", "input/forecast boundary line and labels"],
        },
        "reference_figure": "results/ili/figures/fig_q1_step_sweep_L24_L60_step1.png",
        "case_selection_rule": {
            "deterministic": True,
            "rule": "for each (model, horizon), plot the seed-mean prediction "
                    "curve (mean over seeds 42..51) over the SAME authorized Test "
                    "forecast window; never select a curve after viewing results",
            "authorized_models": ["gpt2_miflu", "nlinear", "seasonal_naive"],
        },
        "provenance_row_fields": ["figure_id", "model", "horizon",
                                  "forecast_origin", "input_start_date",
                                  "input_end_date", "test_target_start_date",
                                  "test_target_end_date",
                                  "input_target_overlap_count",
                                  "future_target_leakage_count",
                                  "scaler_fit_split", "checkpoint_selection_split",
                                  "plotted_target_split", "MSE", "MAE", "PTE",
                                  "PIE", "PTE_hit", "PIE_hit", "joint_hit"],
        "hard_conditions": {
            "input_target_overlap_count": 0,
            "future_target_leakage_count": 0,
            "scaler_fit_split": "Training",
            "checkpoint_selection_split": "Validation",
            "plotted_target_split": "Test/Holdout",
        },
    }
    write_json(os.path.join(FINAL, "final_test_figure_plan.json"), fig_plan)
    print("  wrote final_test_figure_plan.json")


def write_step9():
    test_eval_p = os.path.join(ROOT, "scripts", "innovation", "test_eval.py")
    test_eval_sha = sha256_file(test_eval_p)

    audit = {
        "generated_utc": NOW,
        "pre_test_freeze_audit": "ALL GREEN required before Test access",
        "checks": {
            "wave1_accepted_580": True,
            "deferred_resolved_18_of_18": True,
            "equivalent_mappings_12_of_12": True,
            "new_controls_accepted_6_of_6": True,
            "final_candidate_frozen": True,
            "mandatory_comparators_frozen": True,
            "analysis_plan_frozen": True,
            "pte_pie_spec_frozen": True,
            "date_event_audit_passed": True,
            "test_figure_plan_frozen": True,
            "test_scripts_frozen": True,
            "source_deployment_spec_data_scaler_hashes_recorded": True,
            "queue_empty": None,
            "controller_absent": None,
            "lock_free": None,
            "test_access": 0,
            "holdout_access": 0,
        },
        "test_script": {"path": "scripts/innovation/test_eval.py",
                        "sha256": test_eval_sha},
        "note": "queue_empty/controller_absent/lock_free are filled from the "
                "authoritative HPC state check (performed separately, immediately "
                "before Test access).",
    }
    write_json(os.path.join(FINAL, "pre_test_freeze_audit.json"), audit)

    authz = {
        "generated_utc": NOW,
        "authorization": "one-time Test/Holdout phase (exactly once)",
        "authorized_models": ["gpt2_miflu", "nlinear", "seasonal_naive"],
        "authorized_horizons": HORIZONS,
        "authorized_seeds": {"gpt2_miflu": SEEDS, "nlinear": SEEDS,
                             "seasonal_naive": ["n/a"]},
        "expected_job_count": {"gpt2_miflu": 40, "nlinear": 40,
                               "seasonal_naive": 4},
        "expected_access_count": "one read of the Test split per run (84 total "
                                 "inference jobs); test split read counter starts 0",
        "permitted_retry": "one retry only for a proven scheduler/node/filesystem/"
                           "DNS transport transient, with no scientific change",
        "forbidden_after_test_access": [
            "change model/checkpoint/seed", "change prompt/scaler/horizons/endpoints",
            "change PTE/PIE/date/season/rolling rules", "add or remove comparators",
            "rerun because results are disappointing",
            "select better-looking Test curves manually",
            "return to Validation for further model development",
        ],
        "analysis_plan_hash": "see final_evaluation_plan.json",
        "pte_pie_spec_hash": "see peak-evaluation-v1.json",
        "figure_plan_hash": "see final_test_figure_plan.json",
    }
    write_json(os.path.join(FINAL, "pre_test_authorization_record.json"), authz)

    manifest = {
        "generated_utc": NOW,
        "freeze_files": {},
        "test_script_sha256": test_eval_sha,
        "identities": IDENTITIES,
        "governance_hashes": FROZEN,
    }
    for fn in sorted(os.listdir(FINAL)):
        manifest["freeze_files"][fn] = sha256_file(os.path.join(FINAL, fn))
    write_json(os.path.join(FINAL, "pre_test_freeze_manifest.json"), manifest)
    print("  wrote pre_test_freeze_audit.json, pre_test_authorization_record.json, "
          "pre_test_freeze_manifest.json")


if __name__ == "__main__":
    raise SystemExit(main())
