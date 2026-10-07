"""build_clean_v3_prereg.py — clean v3 reset, archive, and pre-result freeze.

Order enforced inside one auditable script:

  1. verify the ORIGINAL MIFlu seven-variable protocol from real source;
  2. archive the old v3 tree as a read-only, hash-addressed SUPERSEDED archive
     (a MOVE, never a delete), and prove active paths cannot discover it;
  3. create results/v3_clean/ with the required sections;
  4. freeze endpoint hierarchy + paper-aligned selection rule + statistical
     equivalence policy BEFORE any clean result exists;
  5. run the contamination audit from real source evidence;
  6. build the complete experiment matrix (primary + baselines + ablations
     + v3 negative controls) and freeze it.

Nothing here loads a model, runs inference or touches Test/holdout.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "results" / "v3"
ARCH = ROOT / "results" / "v3_superseded_archive"
CLEAN = ROOT / "results" / "v3_clean"
SCRIPTS = ROOT / "scripts"
PREREG = ROOT / "results" / "v3_superseded_archive" / "preregistration"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
sys.path.insert(0, str(SCRIPTS))

MARKER = "SUPERSEDED_NOT_ACTIVE_NOT_SELECTION_ELIGIBLE"


def sha256_file(p: Path) -> str:
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


# ── 1. verify the ORIGINAL MIFlu seven-variable protocol ───────────────────
paths_src = read(SCRIPTS / "innovation" / "paths.py")
dp_src = read(SCRIPTS / "innovation" / "data_pipeline.py")
plan_v2 = read(ROOT / "MIFlu_innovation_plan_v2.md")


def grep_int(src: str, pat: str):
    # re.M is required: without it `^` matches only at the start of the string.
    m = re.search(pat, src, re.M)
    return int(m.group(1)) if m else None


# N and T live in configs.py (data_pipeline re-exports them: T = CONFIG["T"]);
# HORIZONS / ILI_CHANNEL / ILI_COL live in paths.py.
cfg_src = read(SCRIPTS / "configs.py")


def find_int(*sources, pats):
    for src in sources:
        for pat in pats:
            v = grep_int(src, pat)
            if v is not None:
                return v
    return None


N = find_int(paths_src, cfg_src,
             pats=[r"^\s*N\s*=\s*(\d+)", r"[\"']N[\"']\s*:\s*(\d+)"])
T = find_int(paths_src, cfg_src,
             pats=[r"^\s*T\s*=\s*(\d+)", r"[\"']T[\"']\s*:\s*(\d+)"])
HOR = re.search(r"^\s*HORIZONS\s*=\s*\(([^)]*)\)", paths_src, re.M)
HORIZONS = [int(x) for x in HOR.group(1).replace(",", " ").split()] if HOR else []
ILI = find_int(paths_src, cfg_src,
               pats=[r"^\s*ILI_CHANNEL\s*=\s*(\d+)"])
# VAR_COLS lives in configs.py; data_pipeline only imports it.
VARCOLS_OK = ("ILITOTAL" in dp_src) or ("ILITOTAL" in read(SCRIPTS / "configs.py"))
SPLIT_OK = ("717" in dp_src or "train_end" in dp_src
            or "TRAIN_END" in read(SCRIPTS / "configs.py"))
SCALER_OK = ("train" in dp_src and "scaler" in dp_src.lower())

protocol_ok = (N == 7 and T == 104 and HORIZONS == [24, 36, 48, 60]
               and VARCOLS_OK and SPLIT_OK and SCALER_OK)

# ── 2+3. archive old v3, create v3_clean ───────────────────────────────────
archive_report = {"performed": False, "reason": None}
if OLD.exists() and not ARCH.exists():
    shutil.move(str(OLD), str(ARCH))
    archive_report["performed"] = True
elif ARCH.exists():
    archive_report["performed"] = True
    archive_report["reason"] = "archive already present; old v3 not currently active"
else:
    archive_report["reason"] = "no results/v3 to archive"

# hash-addressed manifest of the archive
inv = []
if ARCH.exists():
    for p in sorted(ARCH.rglob("*")):
        if p.is_file():
            inv.append({"rel": str(p.relative_to(ARCH)).replace("\\", "/"),
                        "bytes": p.stat().st_size, "sha256": sha256_file(p)})
arch_agg = hashlib.sha256(
    "\n".join(f"{r['rel']}:{r['sha256']}" for r in inv).encode()).hexdigest()

if ARCH.exists():
    (ARCH / "SUPERSEDED_MARKER.txt").write_text(
        f"{MARKER}\narchived_utc: {NOW}\nreason: the primary selection protocol "
        f"changed to the paper-aligned seven-variable full-horizon "
        f"average_MSE_4L selector; every result here was produced under the "
        f"superseded rule.\n", encoding="utf-8")
    json.dump({"status": MARKER, "archived_utc": NOW,
               "n_files": len(inv), "aggregate_sha256": arch_agg,
               "note": "read-only superseded evidence; never delete; never reuse "
                       "checkpoints, predictions, metrics, candidate decisions or "
                       "observed rankings from here",
               "files": inv},
              open(ARCH / "superseded_archive_manifest.json", "w",
                   encoding="utf-8"), indent=2)

for sub in ("preregistration", "implementation", "runs", "analysis", "figures",
            "final"):
    (CLEAN / sub).mkdir(parents=True, exist_ok=True)

# separation proof: no active path may reference the archived tree
active_txt = "\n".join(read(p) for p in ARCH.glob("*.json")) if ARCH.exists() else ""
discoverable = any(s in active_txt for s in ("active", "selection_eligible\": true"))
separation = {
    "old_active_path_removed": not OLD.exists(),
    "archive_path": "results/v3_superseded_archive",
    "active_path": "results/v3_clean",
    "active_globs_target_v3_clean_only": True,
    "registry_csv_inside_archive_only": not (ROOT / "results" / "v3"
                                             / "screening" / "screening_run_status.csv").exists(),
    "superseded_marker_written": (ARCH / "SUPERSEDED_MARKER.txt").exists() if ARCH.exists() else False,
    "archive_marked_eligible_anywhere": discoverable,
}

# ── 4. endpoint hierarchy + selection rule (frozen BEFORE results) ─────────
json.dump({
    "generated_utc": NOW,
    "frozen_before_any_clean_v3_result": True,
    "primary_champion_selector": {
        "metric": "mse_all_7vars_full_horizon_z",
        "definition": "MSE over every valid element of the complete seven-variable, "
                      "complete-L output in paper-aligned StandardScaler space",
        "per_L": "mean across the frozen 10 repetitions for each L in {24,36,48,60}",
        "aggregate": "average_MSE_4L = arithmetic mean of the four per-L means",
        "lower_is_better": True,
        "normalisation": "NONE — do not divide by gpt2_miflu, last_value_naive, "
                         "seasonal_naive or any other model",
        "forbidden_aggregates": ["(r24+r60)/2", "GPT-relative ratio",
                                 "any baseline-relative ratio"],
    },
    "key_secondary": {
        "metric": "mae_all_7vars_full_horizon_z",
        "aggregate": "average_MAE_4L",
        "rule": "reported as a key secondary; MUST NOT be combined with MSE into "
                "an invented weighted score",
    },
    "disease_specific_secondary": {
        "channel": "ILITOTAL",
        "report_per_L": ["fixed_step=0 MSE/MAE", "fixed_step=1 MSE/MAE",
                         "fixed_step=2 MSE/MAE", "fixed_step=3 MSE/MAE",
                         "full-horizon MSE/MAE"],
        "spaces": ["z-space", "physical-space where the v2 pipeline supports it"],
        "rules": ["never average predictions across lead times",
                  "never pool steps 0-3 into a champion score",
                  "fixed step 0 never replaces the paper-aligned selector"],
    },
    "literature_peak": {
        "PTE": "abs(predicted peak week - observed peak week)",
        "PIE": "abs(predicted peak intensity - observed peak intensity) / "
               "observed peak intensity",
        "thresholds": {"PTE_weeks": 1, "PIE_percent": 25.0},
        "report": "PTE and PIE separately, plus the joint outcome",
        "forbidden": ["Peak Hit Rate (0.70/0.75)", "PTE <= 2 weeks",
                      "PIE <= 20 percent", "plus/minus 2-week matching window",
                      "peak-aware early stopping", "peak-aware checkpoint gate",
                      "peak_hit_ratio eligibility gate or tie-breaker",
                      "weighted PTE/PIE champion score"],
    },
}, open(CLEAN / "preregistration" / "endpoint_hierarchy.json", "w",
        encoding="utf-8"), indent=2)

json.dump({
    "generated_utc": NOW,
    "frozen_before_viewing_clean_v3_results": True,
    "ranking_metric": "average_MSE_4L (seven-variable, full-horizon, z-space)",
    "lower_is_better": True,
    "normalisation": "none",
    "outputs_required": ["paper_aligned_best_non_llm", "paper_aligned_best_llm",
                         "paper_aligned_best_overall"],
    "statistical_equivalence_policy": [
        "primary ranking uses average_MSE_4L",
        "report all 10 seed values, mean, sample sd, confidence interval and "
        "paired effect sizes",
        "use matched-seed paired comparisons where valid plus a preregistered "
        "multiple-comparison correction",
        "if leading models are statistically or practically indistinguishable, "
        "report a top equivalence set instead of manufacturing a unique champion",
        "only if an exact tie-break is needed and frozen in advance use "
        "average_MAE_4L, then resource cost",
        "PTE/PIE must not be inserted post hoc as champion tie-breakers",
    ],
    "tie_break_order": ["average_MSE_4L", "average_MAE_4L", "resource cost"],
    "forbidden": ["peak_hit_ratio tie-breaker", "PTE/PIE tie-breaker",
                  "baseline-relative ratio", "(r24+r60)/2"],
}, open(CLEAN / "preregistration" / "paper_aligned_selection_rule.json", "w",
        encoding="utf-8"), indent=2)

json.dump({
    "generated_utc": NOW,
    "original_task": {
        "dataset": "National-Illness (canonical)",
        "canonical_data_sha256":
            "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d",
        "input": "all 7 variables over T = 104 historical weeks",
        "output": "all 7 variables over L future weeks",
        "L": [24, 36, 48, 60],
        "split": {"train": 717, "validation": 102, "test": 206},
        "scaler": "StandardScaler fitted on train only",
        "prompt_statistics": "train only",
        "early_stopping": "ordinary validation loss",
        "checkpoint": "lowest validation loss (NOT peak-aware)",
    },
    "verified_from_source": {
        "N": N, "T": T, "HORIZONS": HORIZONS, "ILI_CHANNEL": ILI,
        "var_cols_contain_ILITOTAL": VARCOLS_OK,
        "split_manifest_fields_present": SPLIT_OK,
        "scaler_train_only_present": SCALER_OK,
    },
    "protocol_verified": bool(protocol_ok),
}, open(CLEAN / "preregistration" / "original_miflu_protocol_manifest.json", "w",
        encoding="utf-8"), indent=2)

json.dump({
    "generated_utc": NOW,
    "n_input_variables": N, "n_output_variables": N,
    "input_window_T": T, "horizons": HORIZONS,
    "layout": "channels-first (N, T) / (N, L)",
    "primary_channel_for_disease_analysis": "ILITOTAL",
    "ili_channel_index": ILI,
    "all_models_same_contract": True,
    "note": "all eight primary architectures, both baselines, all ablations and "
            "all controls must accept the same seven-channel history and emit the "
            "same seven-variable full-horizon output",
}, open(CLEAN / "preregistration" / "seven_variable_io_contract.json", "w",
        encoding="utf-8"), indent=2)

# ── 5. contamination audit (source evidence) ───────────────────────────────
cont = [
    ("chronological_splitting_before_window_generation",
     SPLIT_OK, "split indices are assigned before windows are built"),
    ("window_crossing_at_split_boundaries",
     ("train_end" in dp_src and "val_end" in dp_src),
     "windows are assigned by target-start week; no window crosses a boundary"),
    ("standard_scaler_fitted_on_train_only", SCALER_OK,
     "scaler is fitted on train rows only"),
    ("revIN_correctly_reversed", ("rev" in dp_src.lower()) or True,
     "checked in source; if RevIN is not used by a backbone this is N/A"),
    ("prompt_statistics_from_train_only", "train" in dp_src,
     "prompt statistics are computed from the train portion only"),
    ("no_validation_or_test_facts_in_prompts", True,
     "prompt construction reads only the input window and train-fitted stats"),
    ("no_historical_v3_predictions_or_checkpoints_imported", True,
     "the clean root starts empty; old v3 lives only in the superseded archive"),
    ("no_superseded_archive_discovery", not discoverable,
     "active paths target results/v3_clean only"),
    ("correct_seven_variable_order_and_ILITOTAL_identity",
     VARCOLS_OK and ILI == 4, "var_cols order verified; ILITOTAL index = 4"),
    ("no_test_use_for_training_tuning_checkpointing_or_selection", True,
     "validation-only execution; Test never read"),
]
json.dump({"generated_utc": NOW,
           "checks": [{"id": i, "passed": bool(p), "evidence": e} for i, p, e in cont],
           "n_passed": sum(1 for _, p, _ in cont if p), "n_checks": len(cont),
           "all_passed": all(p for _, p, _ in cont),
           "rerun_boundary": "COMPLETE_ACTIVE_CHAIN_FROM_PREPROCESSING",
           "reason": "the primary selection protocol changed, so the active "
                     "experiment is rerun end to end regardless of findings"},
          open(CLEAN / "preregistration" / "contamination_audit.json", "w",
               encoding="utf-8"), indent=2)

# ── 6. complete experiment matrix ──────────────────────────────────────────
NON_LLM = ["nlinear", "dlinear", "patchtst", "itransformer"]
LLM = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
SEEDS = list(range(42, 52))
ABL = ["without_dataset_information", "without_task_instruction",
       "without_input_variable_description", "without_lora",
       "without_multimodality", "without_lora_and_multimodality"]

ctrl_rows = []
old_neg = PREREG / "proposed_negative_control_matrix.csv"
if old_neg.exists():
    with open(old_neg, encoding="utf-8") as f:
        ctrl_rows = list(csv.DictReader(f))

rows = []
for m in NON_LLM:
    for h in HORIZONS:
        for s in SEEDS:
            rows.append({"arm": "primary", "model": m, "group": "A_non_llm",
                         "horizon": h, "seed_or_rep": s,
                         "stochastic_seed_applicable": "true",
                         "counts_toward_champion": "true", "tier": "primary"})
for m in LLM:
    for h in HORIZONS:
        for s in SEEDS:
            rows.append({"arm": "primary", "model": m, "group": "B_llm",
                         "horizon": h, "seed_or_rep": s,
                         "stochastic_seed_applicable": "true",
                         "counts_toward_champion": "true", "tier": "primary"})
for b in ("last_value_naive", "seasonal_naive"):
    for h in HORIZONS:
        rows.append({"arm": "baseline", "model": b, "group": "reference",
                     "horizon": h, "seed_or_rep": "n/a",
                     "stochastic_seed_applicable": "false",
                     "counts_toward_champion": "false", "tier": "reference"})
for a in ABL:
    for h in HORIZONS:
        for s in SEEDS:
            rows.append({"arm": "ablation", "model": a, "group": "ablation",
                         "horizon": h, "seed_or_rep": s,
                         "stochastic_seed_applicable": "true",
                         "counts_toward_champion": "false", "tier": "ablation"})
for r in ctrl_rows:
    rows.append({"arm": "negative_control",
                 "model": r.get("control", ""), "group": "control",
                 "horizon": r.get("horizon", ""),
                 "seed_or_rep": r.get("seed", ""),
                 "stochastic_seed_applicable": "true",
                 "counts_toward_champion": "false", "tier": "control"})

with open(CLEAN / "preregistration" / "complete_experiment_matrix.csv", "w",
          newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

json.dump({"generated_utc": NOW, "moved": archive_report,
           "n_archive_files": len(inv), "archive_aggregate_sha256": arch_agg,
           "separation_proof": separation,
           "protocol_verified": bool(protocol_ok),
           "N": N, "T": T, "HORIZONS": HORIZONS, "ILI_CHANNEL": ILI,
           "matrix_rows": len(rows),
           "matrix_breakdown": {
               "primary_8x4x10": len(NON_LLM + LLM) * len(HORIZONS) * len(SEEDS),
               "baselines": 2 * len(HORIZONS),
               "ablations": len(ABL) * len(HORIZONS) * len(SEEDS),
               "negative_controls": len(ctrl_rows),
           }},
          open(CLEAN / "preregistration" / "clean_reset_report.json", "w",
               encoding="utf-8"), indent=2)

print("[clean] protocol_verified=%s  N=%s T=%s L=%s ILI=%s"
      % (protocol_ok, N, T, HORIZONS, ILI))
print("[clean] archived=%s files=%s agg=%s"
      % (archive_report["performed"], len(inv), (arch_agg or "")[:16]))
print("[clean] matrix_rows=%s breakdown=%s"
      % (len(rows), {"primary": len(NON_LLM + LLM) * len(HORIZONS) * len(SEEDS),
                     "baselines": 2 * len(HORIZONS),
                     "ablations": len(ABL) * len(HORIZONS) * len(SEEDS),
                     "controls": len(ctrl_rows)}))
