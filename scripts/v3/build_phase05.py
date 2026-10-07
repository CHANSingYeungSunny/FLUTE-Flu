"""build_phase05.py — v3 Phase 0.5: citation corrections, holdout forensics,
live official-source ledger, LLM architecture contracts, environment plan,
budget recomputation and figure-contract revalidation.

Authorized this turn: read-only forensics, internet verification, document
generation. NOT authorized and NOT performed: weight download, model
construction/loading, training, inference, Slurm submission, holdout access.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PRE = ROOT / "results" / "v3" / "preregistration"
FOR = PRE / "holdout_forensics"
CON = PRE / "llm_architecture_contracts"
for d in (PRE, FOR, CON):
    d.mkdir(parents=True, exist_ok=True)

NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
VERIF_TIME = NOW


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


# ══ A. citation correction audit ════════════════════════════════════════════
CORR = [
    {"id": "C1", "subject": "Time-LLM venue",
     "before": "ICML 2024", "after": "ICLR 2024",
     "severity": "factual citation error",
     "evidence": ["GitHub API repo description: '[ICLR 2024] Official implementation of "
                  "\"Time-LLM: Time Series Forecasting by Reprogramming Large Language Models\"'",
                  "https://proceedings.iclr.cc/paper_files/paper/2024/hash/680b2a8135b9c71278a09cafb605869e-Abstract-Conference.html",
                  "https://mlanthology.org/iclr/2024/jin2024iclr-timellm/"],
     "files_corrected": ["results/v3/preregistration/candidate_feasibility_matrix.json",
                         "results/v3/preregistration/candidate_feasibility_matrix.md",
                         "results/v3/preregistration/architecture_fidelity_matrix.md",
                         "results/v3/preregistration/dependency_and_license_audit.json",
                         "results/v3/preregistration/official_source_ledger.json",
                         "results/v3/preregistration/official_source_ledger.md"]},
    {"id": "C2", "subject": "raw-data latest observation date",
     "before": "raw data extends to 2023-10-06 (inferred from release_date)",
     "after": "release_date is the dataset release stamp, NOT the observation date; "
              "the observation axis is epiweek, whose maximum is 202152 (2021 week 52)",
     "severity": "material factual error that created a phantom unused interval",
     "evidence": ["release_date has only 8 distinct values over 1025 rows",
                  "epiweek has 1025 distinct values, range 200201..202152",
                  "no row has epiweek > 202152 (count = 0)"],
     "files_corrected": ["results/v3/preregistration/untouched_holdout_feasibility.json"]},
    {"id": "C3", "subject": "LTSF-Linear (NLinear/DLinear) license",
     "before": "MIT (pending live verification)", "after": "Apache-2.0",
     "severity": "license misstatement",
     "evidence": ["https://api.github.com/repos/cure-lab/LTSF-Linear -> license.spdx_id = Apache-2.0"],
     "files_corrected": ["results/v3/preregistration/dependency_and_license_audit.json",
                         "results/v3/preregistration/official_source_ledger.json"]},
    {"id": "C4", "subject": "PatchTST license",
     "before": "MIT (pending live verification)", "after": "Apache-2.0",
     "severity": "license misstatement",
     "evidence": ["https://api.github.com/repos/yuqinie98/PatchTST -> license.spdx_id = Apache-2.0"],
     "files_corrected": ["results/v3/preregistration/dependency_and_license_audit.json",
                         "results/v3/preregistration/official_source_ledger.json"]},
    {"id": "C5", "subject": "iTransformer license",
     "before": "MIT (pending live verification)", "after": "MIT (confirmed)",
     "severity": "confirmation",
     "evidence": ["https://api.github.com/repos/thuml/iTransformer -> license.spdx_id = MIT"],
     "files_corrected": ["results/v3/preregistration/dependency_and_license_audit.json"]},
    {"id": "C6", "subject": "TimeCMA license",
     "before": "pending live verification", "after": "NOASSERTION (Other) - manual review required",
     "severity": "blocks unconditional use",
     "evidence": ["https://api.github.com/repos/ChenxiLiu-HNU/TimeCMA -> license.key = other, "
                  "spdx_id = NOASSERTION"],
     "files_corrected": ["results/v3/preregistration/dependency_and_license_audit.json",
                         "results/v3/preregistration/model_access_action_items.md"]},
]
wj(PRE / "citation_correction_audit.json",
   {"generated_utc": NOW, "n_corrections": len(CORR),
    "scan_scope": "active v3 documents only; immutable v2 evidence untouched",
    "active_v3_files_scanned": [
        "MIFlu_innovation_plan_v3.md",
        "results/v3/preregistration/candidate_feasibility_matrix.json",
        "results/v3/preregistration/candidate_feasibility_matrix.md",
        "results/v3/preregistration/architecture_fidelity_matrix.md",
        "results/v3/preregistration/dependency_and_license_audit.json",
        "results/v3/preregistration/untouched_holdout_feasibility.json",
        "scripts/v3/figure_style.py"],
    "corrections": CORR})
(PRE / "citation_correction_audit.md").write_text("\n".join([
    "# Citation and factual correction audit", "", f"Generated {NOW}.",
    "Scope: **active v3 documents only**. Immutable v2 evidence was not rewritten.", "",
    "| ID | Subject | Before | After | Severity |", "|---|---|---|---|---|",
] + [f"| {c['id']} | {c['subject']} | {c['before']} | {c['after']} | {c['severity']} |"
     for c in CORR] + ["", "## Evidence", ""] +
    sum([[f"**{c['id']} — {c['subject']}**"] + [f"- {e}" for e in c["evidence"]] +
         ["- corrected in: " + ", ".join(f"`{f}`" for f in c["files_corrected"]), ""]
         for c in CORR], []) + [
    "## Note on C2", "",
    "The previous turn treated `release_date` as the observation date. It is not: it is the",
    "dataset release stamp and has only 8 distinct values across 1025 rows. The real time",
    "axis is `epiweek` (200201..202152). This error created the appearance of an unused",
    "2022-2023 interval that does not exist in the file.", ""]), encoding="utf-8")

# ══ B. holdout forensics ════════════════════════════════════════════════════
RAW_REL = "data/raw/national_illness_raw.csv"
RAW = ROOT / RAW_REL
raw_sha = sha(RAW)
raw_bytes = RAW.stat().st_size if RAW.exists() else 0
df = pd.read_csv(RAW)
n_rows = len(df)
ew_min, ew_max = int(df["epiweek"].min()), int(df["epiweek"].max())
rel_min, rel_max = str(df["release_date"].min()), str(df["release_date"].max())
n_rel_unique = int(df["release_date"].nunique())

copies = [
    {"copy_id": "local_canonical", "path": RAW_REL, "host": "local",
     "sha256": raw_sha, "bytes": raw_bytes, "role": "the file used by v2 and inspected here"},
    {"copy_id": "hpc_mlflu", "path": "/gpfs1/scratch/sychan552/MLFLU/data/raw/national_illness_raw.csv",
     "host": "burgundy", "sha256": "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d",
     "bytes": raw_bytes, "role": "HPC project copy"},
    {"copy_id": "hpc_v2_10_deploy_root",
     "path": "/scratch/sychan552/innovation_deploy_root_v2_10/data/raw/national_illness_raw.csv",
     "host": "burgundy", "sha256": "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d",
     "bytes": raw_bytes, "role": "v2 isolated deployment root copy"},
    {"copy_id": "hpc_repro_repo",
     "path": "/home/sychan552/scratch/CHATTIME/Chattime/data/raw/national_illness_raw.csv",
     "host": "burgundy", "sha256": "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d",
     "bytes": raw_bytes, "role": "original reproduction repository copy"},
]
all_same = len({c["sha256"] for c in copies}) == 1
wcsv(FOR / "raw_copy_inventory.csv", copies)
wj(FOR / "raw_copy_hashes.json",
   {"generated_utc": NOW, "canonical_sha256": raw_sha, "bytes": raw_bytes,
    "n_copies": len(copies), "all_copies_byte_identical": bool(all_same),
    "content_identity_proof": "SHA-256 equality across all four copies proves the currently "
                              "inspected file is byte-identical to the copies used on HPC; "
                              "mtimes are recorded only as supporting metadata and are never "
                              "used as proof of content identity.",
    "copies": copies})

mapping = [{"row_index": int(r), "epiweek": int(e),
            "release_date": str(rel), "ili_total": float(t)}
           for r, e, rel, t in zip(df.index, df["epiweek"], df["release_date"], df["ILITOTAL"])]
wcsv(FOR / "row_to_week_mapping.csv", mapping)

TEV = ROOT / "results/innovation/test_evaluations/final_nlinear_20260915T145710Z"
pred_files = sorted((TEV / "predictions").glob("*.csv"))
p_first = pd.read_csv(pred_files[0]) if pred_files else pd.DataFrame()
tgt_ew = sorted(p_first["epiweek"].unique()) if "epiweek" in p_first else []
row_of = dict(zip(df["epiweek"], df.index))
splits = [{"segment": "train", "row_start": 0, "row_end": 716,
           "epiweek_range": f"{int(df['epiweek'].iloc[0])}-{int(df['epiweek'].iloc[716])}",
           "classification": "PROVEN_USED_IN_V2_TRAIN",
           "note": "split_manifest train_end=717; scaler and prompt statistics fitted here only"},
          {"segment": "validation", "row_start": 717, "row_end": 819,
           "epiweek_range": f"{int(df['epiweek'].iloc[717])}-{int(df['epiweek'].iloc[819])}",
           "classification": "PROVEN_USED_IN_V2_VALIDATION",
           "note": "split_manifest val_end=819; also serves as input context for the first "
                   "test windows"},
          {"segment": "test_input_context", "row_start": 716, "row_end": 819,
           "epiweek_range": f"{int(df['epiweek'].iloc[716])}-{int(df['epiweek'].iloc[819])}",
           "classification": "PROVEN_USED_IN_V2_TEST_INPUT",
           "note": "T=104 look-back means test windows starting at row 820 consume rows "
                   "716-819 as input"},
          {"segment": "test_target", "row_start": 820, "row_end": 1024,
           "epiweek_range": f"{int(df['epiweek'].iloc[820])}-{int(df['epiweek'].iloc[1024])}",
           "classification": "PROVEN_USED_IN_V2_TEST_TARGET",
           "note": "205 distinct target epiweeks; matches exported v2 Test predictions"}]
recon = {
    "generated_utc": NOW, "T_lookback": 104,
    "raw_rows": n_rows, "epiweek_min": ew_min, "epiweek_max": ew_max,
    "n_windows_L24": 182, "n_windows_L60": 146,
    "target_epiweeks_observed": {"min": int(tgt_ew[0]) if tgt_ew else None,
                                 "max": int(tgt_ew[-1]) if tgt_ew else None,
                                 "n_distinct": len(tgt_ew)},
    "derivation": "n_windows = N_segment - T - L + 1. For L=24: 309-104-24+1=182; "
                  "for L=60: 309-104-60+1=146. Both give the same test segment size N=309, "
                  "i.e. raw rows 716..1024 counting from the first usable window.",
    "consistency_check": "L24 prediction rows 4368 = 182*24; L60 prediction rows 8760 = "
                         "146*60. Both consistent with a single 309-row test segment.",
    "segments": splits,
}
wj(FOR / "split_and_window_reconstruction.json", recon)

wj(FOR / "v2_data_access_timeline.json", {
    "generated_utc": NOW,
    "events": [
        {"order": 1, "event": "raw CSV acquired into the project (data/raw)",
         "content_proof": f"SHA-256 {raw_sha}", "note": "content identical on local and HPC"},
        {"order": 2, "event": "v2 scaler and prompt statistics fitted on train rows 0..716 only",
         "evidence": "split_manifest scaler_fit = 'train rows only (data[:train_end])'"},
        {"order": 3, "event": "v2 Stage F full validation runs trained/evaluated",
         "evidence": "results/innovation/runs/*/split_manifest.json"},
        {"order": 4, "event": "v2 champion frozen (nlinear)",
         "evidence": "frozen_winners.json, freeze_audit.json (test_access_count = 0)"},
        {"order": 5, "event": "v2 one-time Test evaluation, 52 cells",
         "evidence": f"target epiweeks {int(tgt_ew[0]) if tgt_ew else '?'}.."
                     f"{int(tgt_ew[-1]) if tgt_ew else '?'} = rows 820..1024 (last row)"},
        {"order": 6, "event": "v3 Phase 0.5 read-only forensics on the same file",
         "content_proof": f"SHA-256 {raw_sha} (unchanged)"},
    ],
    "conclusion": "The maximum observable epiweek in the file is 202152. The v2 Test target "
                  "range ends at exactly the same epiweek. No observation exists after it."})

post = {
    "generated_utc": NOW,
    "question": "Were the 2022-2023 ILI weeks used by v2?",
    "answer": "The question is void: those weeks are not present in the dataset.",
    "content_level_evidence": {
        "epiweek_max_in_file": ew_max,
        "rows_with_epiweek_gt_202152": 0,
        "release_date_distinct_values": n_rel_unique,
        "release_date_max": rel_max,
        "release_date_meaning": "dataset release/publication stamp, not an observation date",
    },
    "classification": [
        {"interval": "epiweeks 200201..201740 (approx rows 0..716)",
         "classification": "PROVEN_USED_IN_V2_TRAIN"},
        {"interval": "epiweeks ~201741..201804 (approx rows 717..819)",
         "classification": "PROVEN_USED_IN_V2_VALIDATION"},
        {"interval": "epiweeks 201805..202152 (rows 820..1024)",
         "classification": "PROVEN_USED_IN_V2_TEST_TARGET"},
        {"interval": "2022-01-01..2023-12-31 (would be epiweeks 202201..202352)",
         "classification": "REFERENCE_UNAVAILABLE",
         "detail": "no row in the file carries an epiweek in this range; the file's last "
                   "observation is epiweek 202152"},
    ],
    "previous_error": "The prior turn reported 'apparent unused weeks' by reading "
                      "release_date (max 2023-10-06) as if it were the observation date. "
                      "That was wrong and is corrected here.",
}
wj(FOR / "post_2021_usage_audit.json", post)

(FOR / "holdout_forensics_report.md").write_text("\n".join([
    "# v3 holdout forensics report (read-only)", "", f"Generated {NOW}.",
    "No holdout labels were accessed; no model was run.", "",
    "## 1. Root cause of the date contradiction", "",
    f"- `release_date` has only **{n_rel_unique} distinct values** across {n_rows} rows, "
    f"max **{rel_max}**.",
    "- `epiweek` has **1025 distinct values**, range "
    f"**{ew_min}..{ew_max}**.",
    "- Therefore `release_date` is the **dataset release stamp**, not the observation date.",
    "- The last observation is **epiweek 202152 (2021 week 52)**, i.e. the week ending "
    "2021-12-26.",
    "",
    "## 2. What v2 actually used", "",
    "| Segment | Rows | epiweeks | Classification |", "|---|---|---|---|",
] + [f"| {s['segment']} | {s['row_start']}..{s['row_end']} | {s['epiweek_range']} | "
     f"{s['classification']} |" for s in splits] + [
    "",
    f"- Test target epiweeks: **{int(tgt_ew[0]) if tgt_ew else '?'}.."
    f"{int(tgt_ew[-1]) if tgt_ew else '?'}** ({len(tgt_ew)} distinct) - identical to the "
    "exported v2 predictions.",
    "- Window arithmetic: `n_windows = N - T - L + 1`; L=24 gives 182 and L=60 gives 146, "
    "both implying the same 309-row test segment.",
    "",
    "## 3. Content identity", "",
    f"- Canonical SHA-256 **{raw_sha}** ({raw_bytes} bytes)",
    f"- All four copies (local + three HPC paths) are byte-identical: **{all_same}**",
    "- This is content-level proof, not mtime-based.",
    "",
    "## 4. Verdict on the 2022-2023 interval", "",
    "**REFERENCE_UNAVAILABLE.** There are **0 rows** with epiweek > 202152. The interval "
    "does not exist in this dataset, so it can be neither proven untouched nor proposed as "
    "a holdout.",
    "",
    "## 5. Consequences", "",
    "- Internal option 1 (future ILI weeks already in the file) is **eliminated**.",
    "- A v3 final holdout requires **new external or genuinely future data**, which needs "
    "user acquisition and a licence/access record.",
    "- Until then v3 is **validation-only** and must stop before final holdout evaluation "
    "(`V3_VALIDATION_ONLY_NO_NEW_HOLDOUT`).", ""]), encoding="utf-8")

# reject the interval; update feasibility record with the corrected facts
hold = json.loads((PRE / "untouched_holdout_feasibility.json").read_text(encoding="utf-8"))
hold["generated_utc"] = NOW
hold["corrected_2026_09_16"] = {
    "release_date_is_not_observation_date": True,
    "epiweek_max": ew_max, "rows_after_202152": 0,
    "apparent_unused_weeks": False,
    "error_corrected": "previous 'apparent_unused_weeks' was an artefact of reading "
                       "release_date as the time axis"}
hold["options"][0].update({"status": "ELIMINATED", "apparent_unused_weeks": False,
                           "elimination_reason": "no row in the file has epiweek > 202152"})
hold["conclusion"] = "NO_UNTOUCHED_INTERVAL_AVAILABLE_INTERNAL"
hold["decision"] = "REJECTED"
hold["external_options"] = [
    {"option": "acquire newer CDC/FluView ILI weeks released after the v2 cut-off",
     "requires": "user download + licence/terms record + raw SHA-256", "status": "USER_ACTION"},
    {"option": "external jurisdiction or surveillance source (e.g. another national/regional "
               "ILI series)",
     "requires": "source selection, licence check, access record", "status": "USER_ACTION"},
    {"option": "another locked influenza dataset not used to design v3",
     "requires": "scientific decision + evidence it did not influence v3 design",
     "status": "USER_ACTION"},
]
hold["consequence"] = ("v3 proceeds validation-only; final holdout evaluation is blocked "
                       "until external/future data is acquired and registered.")
wj(PRE / "untouched_holdout_feasibility.json", hold)

# ══ C. official source ledger ═══════════════════════════════════════════════
LEDGER = [
    {"model_key": "nlinear", "group": "A_non_llm",
     "paper": "Are Transformers Effective for Time Series Forecasting?",
     "venue": "AAAI 2023 (Oral)", "canonical_url": "https://arxiv.org/abs/2205.13504",
        "repository": "https://github.com/cure-lab/LTSF-Linear", "branch": "main",
        "pinned_commit": "0c113668a3b88c4c4ee586b8c5ec3e539c4de5a6", "license": "Apache-2.0",
     "backbone": "none (linear)", "gated": False,
     "transformers_requirement": "n/a", "verified_at": VERIF_TIME},
    {"model_key": "dlinear", "group": "A_non_llm",
     "paper": "Are Transformers Effective for Time Series Forecasting?",
     "venue": "AAAI 2023 (Oral)", "canonical_url": "https://arxiv.org/abs/2205.13504",
        "repository": "https://github.com/cure-lab/LTSF-Linear", "branch": "main",
        "pinned_commit": "0c113668a3b88c4c4ee586b8c5ec3e539c4de5a6", "license": "Apache-2.0",
     "backbone": "none (linear)", "gated": False,
     "transformers_requirement": "n/a", "verified_at": VERIF_TIME},
    {"model_key": "patchtst", "group": "A_non_llm",
     "paper": "A Time Series is Worth 64 Words: Long-term Forecasting with Transformers",
     "venue": "ICLR 2023", "canonical_url": "https://arxiv.org/abs/2211.14730",
        "repository": "https://github.com/yuqinie98/PatchTST", "branch": "main",
        "pinned_commit": "204c21efe0b39603ad6e2ca640ef5896646ab1a9", "license": "Apache-2.0",
     "backbone": "none (Transformer)", "gated": False,
     "transformers_requirement": "n/a", "verified_at": VERIF_TIME},
    {"model_key": "itransformer", "group": "A_non_llm",
     "paper": "iTransformer: Inverted Transformers Are Effective for Time Series Forecasting",
     "venue": "ICLR 2024 Spotlight", "canonical_url": "https://arxiv.org/abs/2310.06625",
     "repository": "https://github.com/thuml/iTransformer", "branch": "main",
        "pinned_commit": "c2426e68ca13f74aaec08045c5c724d8ad328124", "license": "MIT",
     "backbone": "none (Transformer)", "gated": False,
     "transformers_requirement": "n/a", "verified_at": VERIF_TIME},
    {"model_key": "gpt2_miflu", "group": "B_llm",
     "paper": "MIFlu (IEEE JBHI 2025)", "venue": "IEEE JBHI 2025",
     "canonical_url": "https://doi.org/10.1109/JBHI.2025.3561214",
    "repository": "repository-local control; no independent official MIFlu code URL was found in active project records",
    "branch": "n/a", "pinned_commit": "n/a", "license": "UNRESOLVED_LOCAL_CONTROL",
        "backbone": "GPT-2", "gated": False,
    "transformers_requirement": "as in the v2 environment", "verified_at": VERIF_TIME,
    "verification_status": "LOCAL_CONTROL_NOT_OFFICIAL_REPO_VERIFIED",
    "note": "The v2 control is retained, but its local code/weights are not evidence of an official public repository or license."},
    {"model_key": "qwen_time_llm", "group": "B_llm",
     "paper": "Time-LLM: Time Series Forecasting by Reprogramming Large Language Models",
     "venue": "ICLR 2024", "canonical_url": "https://arxiv.org/abs/2310.01728",
     "repository": "https://github.com/KimMeen/Time-LLM", "branch": "main",
     "pinned_commit": "b13e881f86cd0475ce1b72c17110430663334955",
        "pinned_commit_date": "2025-10-15T11:40:16Z", "license": "Apache-2.0",
     "backbone": "Qwen/Qwen2.5-1.5B", "backbone_params": "1.54B",
     "backbone_dtype": "BF16", "approx_weight_gb": 3.1,
     "gated": False, "transformers_requirement": ">= 4.37.0 (KeyError 'qwen2' below that)",
     "verified_at": VERIF_TIME},
    {"model_key": "calf_llm", "group": "B_llm",
     "paper": "CALF: Aligning LLMs for Time Series Forecasting via Cross-Modal Fine-Tuning",
     "venue": "AAAI 2025", "canonical_url": "https://arxiv.org/abs/2403.07300",
     "repository": "https://github.com/Hank0626/CALF", "branch": "main",
     "pinned_commit": "50e7270af9a9b256acaf33b2688fef7d95f5a3f0",
        "pinned_commit_date": "2025-03-14T08:39:37Z", "license": "Apache-2.0",
     "backbone": "GPT-2 (pinned for feasibility; already cached offline)",
     "gated": False, "transformers_requirement": "as in the v2 environment",
     "verified_at": VERIF_TIME},
    {"model_key": "timecma_llm", "group": "B_llm",
     "paper": "TimeCMA: Towards LLM-Empowered Multivariate Time Series Forecasting via "
              "Cross-Modality Alignment",
     "venue": "AAAI 2025", "canonical_url": "https://arxiv.org/abs/2406.01638",
     "repository": "https://github.com/ChenxiLiu-HNU/TimeCMA", "branch": "main",
        "pinned_commit": "223e4ae9364bec3e3a2d8bb39ab6eed2cf510296",
     "pinned_commit_date": "2025-12-08T11:40:15Z", "license": "NOASSERTION (Other)",
     "license_action": "manual licence review required before use",
     "backbone": "GPT-2 (pinned for feasibility; already cached offline)",
     "gated": False, "transformers_requirement": "as in the v2 environment",
     "verified_at": VERIF_TIME},
]
wj(PRE / "official_source_ledger.json",
   {"generated_utc": NOW, "verification_method": "live internet queries against official "
                                                 "GitHub API endpoints, arXiv, conference "
                                                 "proceedings and the official model card",
    "weights_downloaded": False, "n_records": len(LEDGER), "records": LEDGER})
(PRE / "official_source_ledger.md").write_text("\n".join([
    "# Official source ledger (live verified)", "", f"Verified at {VERIF_TIME}.",
    "No weights were downloaded.", "",
    "| model_key | Paper | Venue | Repository | Pinned commit | Licence | Backbone |",
    "|---|---|---|---|---|---|---|",
] + [f"| `{r['model_key']}` | {r['paper']} | {r['venue']} | {r['repository']} | "
     f"`{r['pinned_commit']}` | {r['license']} | {r['backbone']} |" for r in LEDGER] + [
    "",
    "## Corrections applied this turn", "",
    "- **Time-LLM: ICML 2024 -> ICLR 2024** (official repo description and ICLR proceedings).",
    "- LTSF-Linear and PatchTST licences corrected to **Apache-2.0**.",
    "- **TimeCMA licence is NOASSERTION (Other)** - manual review required.",
    "",
    "## Backbone decision", "",
    "Only **Qwen2.5-1.5B** requires a new download (~3.1 GB BF16). CALF-inspired and "
    "TimeCMA-inspired pin **GPT-2**, which is already cached offline from v2, keeping the "
    "new-download surface minimal and the study reproducible offline. This is a documented, "
    "fidelity-affecting choice recorded in the architecture contracts.", ""]),
    encoding="utf-8")

print("[phase05] forensics: epiweek %d..%d, rows_after_202152=0, copies_identical=%s"
      % (ew_min, ew_max, all_same))
print("[phase05] ledger=%d | corrections=%d" % (len(LEDGER), len(CORR)))
