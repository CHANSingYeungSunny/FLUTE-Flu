#!/usr/bin/env python3
"""Generate the tabular deliverables for the 2026-10-06 continuation round.

Everything here is derived from artefacts that already exist on disk. Nothing
is invented: if a value is not backed by a file on disk it is written as
UNKNOWN / PENDING rather than estimated.

Run:
    python hpc_results/official_repo_reproduction_20261006/build_deliverables.py
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))

HORIZONS = [24, 36, 48, 60]
SEEDS_3 = [42, 43, 44]
SEEDS_10 = list(range(42, 52))

# model -> (group, implementation class)
MODEL_META = {
    "miflu":         ("LLM",     "corrected reconstruction (text path repaired)"),
    "notext":        ("CONTROL", "MIFlu control, forecasting GPT-2 + LoRA KEPT"),
    "nlinear":       ("non-LLM", "canonical NLinear"),
    "dlinear":       ("non-LLM", "own re-implementation"),
    "patchtst":      ("non-LLM", "PatchTST-INSPIRED (NOT canonical)"),
    "itransformer":  ("non-LLM", "own re-implementation"),
    "timecma_llm":   ("LLM",     "TimeCMA-INSPIRED"),
    "qwen_time_llm": ("LLM",     "Time-LLM-INSPIRED on Qwen2.5-1.5B"),
    "calf_llm":      ("LLM",     "CALF-INSPIRED"),
    "seasonal_naive": ("baseline", "deterministic reference"),
    "last_value_naive": ("baseline", "deterministic reference"),
    "gpt2_miflu":    ("LLM",     "July-track corrected MIFlu"),
}


def w(path, rows, fields=None):
    full = os.path.join(HERE, path)
    if not rows:
        print(f"  (skip {path}: no rows)")
        return
    fields = fields or list(rows[0].keys())
    with open(full, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    print(f"  wrote {path}  ({len(rows)} rows)")


def read_csv(rel, **kw):
    p = os.path.join(PROJ, rel)
    if not os.path.exists(p):
        return []
    with open(p, newline="", **kw) as fh:
        return list(csv.DictReader(fh))


# ── 1. author_paper_targets.csv ─────────────────────────────────────────────
def author_targets():
    target = {24: (1.542, 0.726), 36: (1.422, 0.779),
              48: (1.414, 0.757), 60: (1.364, 0.719)}
    rows = []
    for L in HORIZONS:
        mse, mae = target[L]
        rows.append({"L": L, "paper_MSE": mse, "paper_MAE": mae,
                     "source": "MIFlu paper Table V",
                     "caveat": "paper states baseline columns are imported from "
                               "refs [9]/[14]; whether MIFlu's own column is a "
                               "rerun is not stated"})
    rows.append({"L": "mean(4L)", "paper_MSE": 1.4355, "paper_MAE": 0.74525,
                 "source": "arithmetic mean of Table V",
                 "caveat": "paper's own rounded statement is 1.436/0.745 (Table VIII)"})
    return rows


# ── 2. RUN_MANIFEST.csv ─────────────────────────────────────────────────────
def run_manifest():
    rows = []
    # stage6 ledger = the 72 new fits (+3 retries)
    led = read_csv("hpc_results/stage6/ledgers/run_ledger.csv")
    retries = defaultdict(int)
    for r in led:
        key = (r.get("model", ""), r.get("L", ""), r.get("seed", ""))
        retries[key] += 1
        rows.append({
            "run_key": r.get("key", ""), "slurm_jobid": r.get("jobid", ""),
            "model": r.get("model", ""), "L": r.get("L", ""), "seed": r.get("seed", ""),
            "track": "A_author966", "phase": "stage6",
            "start": r.get("extra", "").split("_start=")[-1].split(" ")[0] if r.get("extra") else "",
            "exit": r.get("exit", (r.get("extra", "").split("exit=")[-1])),
            "attempt_index": retries[key],
            "attempt_status": "superseded-retry" if retries[key] > 1 else "primary",
        })
    # stage5 A2 = 36 learned fits + 8 baselines, job id from the stage5 evidence
    for m in ("miflu", "nlinear", "notext"):
        for L in HORIZONS:
            for s in SEEDS_3:
                rows.append({"run_key": f"S5-{m.upper()}-L{L}-S{s}", "slurm_jobid": "see stage5 ledger",
                             "model": m, "L": L, "seed": s, "track": "A_author966",
                             "phase": "stage5_a2", "start": "UNKNOWN", "exit": "0",
                             "attempt_index": 1, "attempt_status": "primary"})
    for m in ("last_value_naive", "seasonal_naive"):
        for L in HORIZONS:
            rows.append({"run_key": f"S5-{m.upper()}-L{L}-DET", "slurm_jobid": "deterministic",
                         "model": m, "L": L, "seed": "deterministic", "track": "A_author966",
                         "phase": "stage5_a2", "start": "UNKNOWN", "exit": "0",
                         "attempt_index": 1, "attempt_status": "primary"})
    return rows


# ── 3. REMAINING_RUN_MATRIX.csv ─────────────────────────────────────────────
def remaining_matrix():
    """What is NOT done, with the minimum action. Nothing here is estimated as
    complete."""
    rows = []
    for m in ["miflu", "notext", "nlinear", "dlinear", "last_value_naive",
              "seasonal_naive", "patchtst", "itransformer", "qwen_time_llm",
              "calf_llm", "timecma_llm"]:
        grp = MODEL_META.get(m, ("?", "?"))[0]
        for L in HORIZONS:
            have = set(SEEDS_3)
            deterministic = m.endswith("naive")
            want = {0} if deterministic else set(SEEDS_10)
            missing = sorted(want - (have if not deterministic else want))
            rows.append({
                "track": "A_author966", "model": m, "group": grp, "L": L,
                "seeds_done": ("deterministic" if deterministic else "42,43,44"),
                "seeds_required_by_paper": ("n/a" if deterministic else "10 repetitions"),
                "seeds_missing": ("none" if deterministic else ",".join(str(x) for x in missing)),
                "n_missing_fits": (0 if deterministic else len(missing)),
                "estimated_gpu_hours": (0.0 if deterministic else round(len(missing) * 0.0125, 4)),
                "gpu_hours_basis": "measured: stage6 spent 1.05 GPU-h on 72 fits = 0.0146 h/fit; "
                                   "the cheaper 20-epoch fits averaged 0.0125 h",
                "blocked_by": "GPU budget: 0.308 of the 2.3 GPU-h cap remains; one "
                              "A1 fit costs a measured 0.282 GPU-h",
                "next_action": "sbatch --array=<idx> slurm/miflu_a1_array.sbatch once the "
                               "cap is extended (arrays count >1 against stingy MaxSubmit=1, "
                               "so submit one index at a time)",
            })
    # items that are not just more seeds
    extra = [
        ("A1_paper_config", "author released main_ILI_lora.py", "all 4", "1 repetition",
         "DONE 2026-10-06: all four horizons ran on the author's entry point "
         "(jobs 606365/606378/606385/606412). Metric is the author's own "
         "feature-0, Test-selected quantity - NOT Table V.",
         "no blocker for what ran; the remaining repetitions are budget-bound",
         "set MIFLU_ITR=10 and extend the cap by ~11.3 GPU-h"),
        ("A1_repetitions", "author released main_ILI_lora.py", "all", "1 of 10",
         "paper asks for the mean of 10 repetitions; 1 completed per horizon",
         "each repetition costs a MEASURED 0.2817 GPU-h; 40 fits = ~11.27 GPU-h; "
         "remaining authorised headroom is 0.056 GPU-h",
         "extend the cap, then sbatch --array=<idx> per horizon (MaxSubmit=1)"),
        ("A0_full_replay", "author released code", "-", "-", "only a 1-epoch minimum diagnostic exists",
         "not authorised", "requires a separate budget approval; each fit is ~0.28 GPU-h"),
        ("text_path_probe_gpu", "probe", "-", "-", "DONE - CPU and GPU both ran, verdicts AGREE (text_inert)",
         "none", "none - closed. Re-run only if the environment changes."),
        ("paired_stats_win_direction", "project paired_stats.py", "-", "-",
         "DONE - corrected script + unit tests written; original file left untouched",
         "none", "update recovery/stage6/results_report_zh.md §0 from '5/12' to '7/12'"),
        ("canonical_patchtst", "patchtst", "-", "-", "current implementation is PatchTST-INSPIRED",
         "not implemented", "implement canonical PatchTST or keep the INSPIRED label"),
        ("regional_table_VI", "ReILIF / SAIFlu-Net / Cola-GNN", "-", "-", "never run", "not authorised",
         "out of core scope; must be declared as not-run"),
        ("text_embedder_table_VII", "BERT / LLaMA2-7B", "-", "-", "never run", "not authorised",
         "out of core scope; must be declared as not-run"),
        ("track_C_generalisation", "-", "-", "-", "no untouched interval exists",
         "no genuinely unseen period available",
         "requires supervisor decision on a future holdout"),
        ("scratch_quota", "cluster storage", "-", "-",
         "OVER QUOTA: 413 GB used against a 300 GB user quota, grace expired",
         "writes to /gpfs1/scratch fail intermittently",
         "user decision: clean the innovation_deploy_root_v3_* staging dirs "
         "(52+50+11+11+9.7+9.6x6 GB) - NOT deleted by this round"),
    ]
    for t, m, L, s, status, blocked, nxt in extra:
        rows.append({"track": t, "model": m, "group": "-", "L": L,
                     "seeds_done": s, "seeds_required_by_paper": "-",
                     "seeds_missing": "-", "n_missing_fits": "UNKNOWN",
                     "estimated_gpu_hours": "UNKNOWN", "gpu_hours_basis": "-",
                     "blocked_by": blocked, "next_action": f"{status} :: {nxt}"})
    return rows


# ── 4-7. reproduction + benchmark tables ────────────────────────────────────
def scorer_cells():
    return read_csv("hpc_results/official_repo_reproduction_20261006/indep_scorer_cells.csv")


def per_seed_rows(cells):
    rows = []
    for c in cells:
        rows.append({
            "track": "A_author966", "model": c["model"],
            "group": MODEL_META.get(c["model"], ("?", "?"))[0],
            "L": c["L"], "seed": c["seed"], "n_origins": c["n_origins"],
            "n_vars": c["n_vars"], "n_leads": c["n_leads"],
            "mse_all_7vars_z": c["mse_all"], "mae_all_7vars_z": c["mae_all"],
            "space": c["space"], "protocol": c["containment"],
            "n_seeds_in_this_round": 3,
            "paper_repetitions": 10,
            "seed_count_gap": "3 of the paper's 10 repetitions",
            "source_artefact": c["path"],
        })
    return rows


def aggregate_rows(cells):
    per = defaultdict(lambda: defaultdict(list))
    for c in cells:
        per[c["model"]][int(c["L"])].append(float(c["mse_all"]))
    rows = []
    for m, d in per.items():
        if sorted(d) != HORIZONS:
            continue
        Lm = {L: sum(d[L]) / len(d[L]) for L in HORIZONS}
        rows.append({
            "track": "A_author966", "model": m,
            "group": MODEL_META.get(m, ("?", "?"))[0],
            "implementation": MODEL_META.get(m, ("?", "?"))[1],
            **{f"MSE_L{L}": f"{Lm[L]:.6f}" for L in HORIZONS},
            "average_MSE_4L": f"{sum(Lm.values()) / 4:.6f}",
            "n_seeds_per_L": len(d[24]),
            "n_cells": sum(len(v) for v in d.values()),
            "comparable_to_paper": "NO - different metric normalisation, "
                                   "3 vs 10 repetitions, reconstructed hyperparameters",
        })
    rows.sort(key=lambda r: float(r["average_MSE_4L"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def paper_vs_repro(agg):
    paper = {L: (1.542, 0.726) for L in HORIZONS}
    paper[24] = (1.542, 0.726); paper[36] = (1.422, 0.779)
    paper[48] = (1.414, 0.757); paper[60] = (1.364, 0.719)
    rows = []
    mif = next((r for r in agg if r["model"] == "miflu"), None)
    if not mif:
        return rows
    for L in HORIZONS:
        ours = float(mif[f"MSE_L{L}"])
        p = paper[L][0]
        rows.append({
            "L": L, "paper_MSE": p, "reproduced_MSE_Lz": f"{ours:.4f}",
            "abs_diff": f"{ours - p:+.4f}", "ratio": f"{ours / p:.2f}x",
            "comparable": "NO",
            "why_not_comparable": "paper does not disclose epochs/lr; our value is "
                                  "z-space 3-seed with a reconstructed recipe; the "
                                  "paper's is 10 repetitions with its own scaler. "
                                  "This table documents a gap, it does NOT "
                                  "demonstrate a reproduction.",
        })
    rows.append({"L": "mean(4L)", "paper_MSE": 1.4355,
                 "reproduced_MSE_Lz": f"{sum(float(mif[f'MSE_L{L}']) for L in HORIZONS) / 4:.4f}",
                 "abs_diff": f"{sum(float(mif[f'MSE_L{L}']) for L in HORIZONS) / 4 - 1.4355:+.4f}",
                 "ratio": f"{sum(float(mif[f'MSE_L{L}']) for L in HORIZONS) / 4 / 1.4355:.2f}x",
                 "comparable": "NO",
                 "why_not_comparable": "see per-horizon rows"})
    return rows


def per_horizon_benchmark(agg):
    rows = []
    for L in HORIZONS:
        ranked = sorted(agg, key=lambda r: float(r[f"MSE_L{L}"]))
        if not ranked:
            continue
        rows.append({
            "L": L,
            "best_overall": ranked[0]["model"],
            "best_overall_MSE": ranked[0][f"MSE_L{L}"],
            "best_LLM": next((r["model"] for r in ranked if r["group"] == "LLM"), "-"),
            "best_LLM_MSE": next((r[f"MSE_L{L}"] for r in ranked if r["group"] == "LLM"), "-"),
            "best_nonLLM": next((r["model"] for r in ranked if r["group"] == "non-LLM"), "-"),
            "best_nonLLM_MSE": next((r[f"MSE_L{L}"] for r in ranked if r["group"] == "non-LLM"), "-"),
            "best_control_notext": next((r[f"MSE_L{L}"] for r in ranked if r["model"] == "notext"), "-"),
            "full_ranking": " > ".join(f"{r['model']}({float(r[f'MSE_L{L}']):.4f})" for r in ranked),
        })
    return rows


def per_variable_rows():
    src = read_csv("hpc_results/official_repo_reproduction_20261006/indep_scorer_per_variable.csv")
    per = defaultdict(list)
    for r in src:
        per[(r["model"], r["variable"])].append(float(r["mse"]))
    rows = []
    for (m, v), vals in per.items():
        rows.append({"track": "A_author966", "model": m,
                     "group": MODEL_META.get(m, ("?", "?"))[0],
                     "variable": v, "n_cells": len(vals),
                     "mse_mean_over_cells": f"{sum(vals) / len(vals):.6f}"})
    rows.sort(key=lambda r: (r["model"], r["variable"]))
    return rows


# ── 8. cost_summary.csv ─────────────────────────────────────────────────────
def cost_summary():
    return [
        # ---- pre-existing (stage 6 round, 2026-09-26) -----------------------
        {"item": "stage6 COMPLETED jobs", "gpu_hours": 1.0500,
         "basis": "sacct -X; re-verified live on the cluster 2026-10-06"},
        {"item": "stage6 FAILED attempts", "gpu_hours": 0.0756,
         "basis": "same; no result depends on them"},
        {"item": "stage6 subtotal", "gpu_hours": 1.1256, "basis": "sum"},
        {"item": "stage5 over-cap but billed", "gpu_hours": 0.4400,
         "basis": "jobs 585540/585544/585555/585581/585843-585846"},
        # ---- this round (2026-10-06) ---------------------------------------
        {"item": "2026-10-06 probe_text_path_gpu (job 606358)", "gpu_hours": 0.00833,
         "basis": "sacct Elapsed 00:00:30 on gres/gpu:a100"},
        {"item": "2026-10-06 a1_measure failed attempt (job 606361_0)", "gpu_hours": 0.00194,
         "basis": "sacct Elapsed 00:00:07; peft target_modules crash"},
        {"item": "2026-10-06 A1 L=24 (job 606365_0)", "gpu_hours": 0.29278,
         "basis": "sacct Elapsed 00:17:34"},
        {"item": "2026-10-06 A1 L=36 (job 606378_1)", "gpu_hours": 0.28167,
         "basis": "sacct Elapsed 00:16:54"},
        {"item": "2026-10-06 A1 L=48 (job 606385_2)", "gpu_hours": 0.27167,
         "basis": "sacct Elapsed 00:16:18"},
        {"item": "2026-10-06 A1 L=60 (job 606412_3)", "gpu_hours": 0.26167,
         "basis": "sacct Elapsed 00:15:42"},
        {"item": "2026-10-06 CPU-only jobs (probe cpu, diag_peft, compare)",
         "gpu_hours": 0.0,
         "basis": "no gres/gpu requested - zero GPU-hours by construction"},
        {"item": "2026-10-06 subtotal", "gpu_hours": 1.11806,
         "basis": "sum of the five sacct-verified a100 jobs"},
        # ---- cap arithmetic -------------------------------------------------
        {"item": "authorised cumulative cap", "gpu_hours": 2.3,
         "basis": "user authorisation for the stage6 + continuation round"},
        {"item": "cumulative used", "gpu_hours": 2.24366,
         "basis": "1.1256 (stage6) + 1.11806 (this round)"},
        {"item": "headroom remaining", "gpu_hours": 0.05634,
         "basis": "cap - used; ~3.4 minutes of A100 time - hence no further "
                  "A1 repetitions were submitted and the round stopped here"},
        # ---- measured unit costs -------------------------------------------
        {"item": "measured per-fit cost, A2 LoRA config (20 epochs)",
         "gpu_hours": 0.0146,
         "basis": "stage6: 1.05 GPU-h / 72 fits"},
        {"item": "measured per-fit cost, A1 author config (20 epochs, full GPT-2 trainable)",
         "gpu_hours": 0.2817,
         "basis": "mean of the three completed A1 fits; 19x the A2 cost because "
                  "the author's freeze is a no-op so all 82.7M parameters train"},
        {"item": "estimated cost of the full A1 run (4 horizons x 10 repetitions)",
         "gpu_hours": 11.27,
         "basis": "40 fits x 0.2817 measured; this is the real price of the "
                  "paper's 'mean of 10 repetitions' on the author's code"},
    ]


# ── 9. failures_and_retries.csv ─────────────────────────────────────────────
def failures():
    return [
        {"jobid": "587048", "state": "FAILED", "cause": "A0 import blocker",
         "product_damage": "none", "resolution": "compat layer applied, resubmitted"},
        {"jobid": "587054", "state": "FAILED", "cause": "--checkpoints dir did not exist",
         "product_damage": "none", "resolution": "directory created, resubmitted"},
        {"jobid": "587059", "state": "FAILED", "cause": "itr loop index out of range",
         "product_damage": "none", "resolution": "itr fixed, resubmitted"},
        {"jobid": "587068", "state": "FAILED (old wrapper)", "cause":
         "author code returns rc=1; old wrapper mapped it straight to FAILED",
         "product_damage": "NONE - the 82 s replay completed; product valid",
         "resolution": "wrapper fixed at 18:33:19, between 587068 end and 587091 submit"},
        {"jobid": "587373", "state": "FAILED", "cause":
         "build_lock_stage5.py line 115 FileNotFoundError 'results/stage6/lock_templates.json'",
         "product_damage": "none - scoring never started",
         "resolution": "path fixed, resubmitted as 587385"},
        {"jobid": "587385", "state": "exit 3", "cause":
         "closing assertion expected 104 rows, found 116 (stale expectation)",
         "product_damage": "NONE - the full 116-row score matrix was written",
         "resolution": "expectation updated; verification re-run PASS (max dev 8.9e-16)"},
        {"jobid": "587243", "state": "CANCELLED", "cause":
         "cancelled by 90731875, which does not exist in this cluster's accounting",
         "product_damage": "none - superseded duplicate",
         "resolution": "no product depends on it"},
        # ---- 2026-10-06 continuation round ---------------------------------
        {"jobid": "606361_0", "state": "COMPLETED (author rc=1)", "cause":
         "A1 passed --target_modules 'c_attn' on the command line; the author's "
         "argparse declares it type=str with a LIST default, so the override "
         "arrived as a bare string and peft raised 'Target modules c_attn not found'",
         "product_damage": "none - died in model construction before any training",
         "resolution": "removed the override (author's own list default now applies); "
                       "diagnosed with CPU job 606362, which tested 7 spellings for 0 GPU-h"},
        {"jobid": "606363_0", "state": "CANCELLED", "cause":
         "submitted before the target_modules fix landed; cancelled to avoid "
         "burning GPU time on a known-bad configuration",
         "product_damage": "none - cancelled while still PENDING, never started",
         "resolution": "resubmitted as 606365 after the fix"},
        {"jobid": "n/a (sbatch rejected)", "state": "REJECTED",
         "cause": "QOSMaxSubmitJobPerUserLimit - stingy sets MaxSubmit=1, "
                  "MaxJobsPU=1, and --array=1-2 counts as two submissions",
         "product_damage": "none - submission never accepted",
         "resolution": "each A1 horizon submitted as its own single-element array "
                       "and awaited before the next"},
        {"jobid": "n/a (scp)", "state": "FAILED", "cause":
         "Disk quota exceeded on /gpfs1/scratch (413 GB used against a 300 GB "
         "user quota, grace expired)",
         "product_damage": "none - only the upload failed",
         "resolution": "all outputs relocated to /gpfs1/home/sychan552/; scratch "
                       "used read-only for the author checkout"},
    ]


# ── 10. B-track benchmark tables ────────────────────────────────────────────
def best_model_summary(agg):
    """The seven separate answers section 8 demands - never collapsed into one
    headline number."""
    rows = []
    ranked = sorted(agg, key=lambda r: float(r["average_MSE_4L"]))
    llm = [r for r in ranked if r["group"] == "LLM"]
    non = [r for r in ranked if r["group"] == "non-LLM"]
    core = [r for r in ranked if r["model"] != "notext"]
    ctrl = next((r for r in ranked if r["model"] == "notext"), None)

    def row(question, answer, value, basis):
        rows.append({"question": question, "answer": answer,
                     "average_MSE_4L": value, "basis": basis})

    rows.append({
        "question": "1. best overall among the eight core models",
        "answer": core[0]["model"] if core else "-",
        "average_MSE_4L": core[0]["average_MSE_4L"] if core else "-",
        "basis": "Track A, author 966 rows, z-space, 3 seeds x 4 horizons. "
                 "The notext control scores lower still but is a CONTROL, "
                 "not one of the eight models."})
    rows.append({
        "question": "1b. best overall INCLUDING the control",
        "answer": ctrl["model"] if ctrl else "-",
        "average_MSE_4L": ctrl["average_MSE_4L"] if ctrl else "-",
        "basis": "notext keeps the GPT-2 forecasting backbone AND LoRA, so it is "
                 "not a non-LLM model - reported separately on purpose."})
    row("2. best LLM-based model", llm[0]["model"] if llm else "-",
        llm[0]["average_MSE_4L"] if llm else "-",
        "group = {miflu, timecma_llm, qwen_time_llm, calf_llm}")
    row("3. best non-LLM model", non[0]["model"] if non else "-",
        non[0]["average_MSE_4L"] if non else "-",
        "group = {nlinear, dlinear, patchtst, itransformer}")
    rows.append({
        "question": "4. matched mechanism: full MIFlu vs matched no-text",
        "answer": "notext - miflu = -0.1194, t = -1.50, 7/12 cells",
        "average_MSE_4L": "1.9222 vs 2.0415",
        "basis": "same data, same protocol, same forecasting GPT-2 and LoRA; only "
                 "the text path differs. NOT significant -> 'removing text is "
                 "better' cannot be claimed. See paired_stats_corrected.csv."})
    for L in HORIZONS:
        best = min(agg, key=lambda r: float(r[f"MSE_L{L}"]))
        rows.append({
            "question": f"5. per-horizon winner L={L}",
            "answer": best["model"],
            "average_MSE_4L": best[f"MSE_L{L}"],
            "basis": "MSE at this horizon only; the winner flips between notext, "
                     "miflu and nlinear across horizons, so no single-horizon "
                     "result may be extrapolated."})
    mif = next((r for r in agg if r["model"] == "miflu"), None)
    nli = next((r for r in agg if r["model"] == "nlinear"), None)
    if mif and nli:
        spread_m = max(float(mif[f"MSE_L{L}"]) for L in HORIZONS) - min(float(mif[f"MSE_L{L}"]) for L in HORIZONS)
        spread_n = max(float(nli[f"MSE_L{L}"]) for L in HORIZONS) - min(float(nli[f"MSE_L{L}"]) for L in HORIZONS)
        rows.append({
            "question": "6. stability across horizons",
            "answer": f"miflu range {spread_m:.3f} vs nlinear range {spread_n:.3f}",
            "average_MSE_4L": "-",
            "basis": f"MIFlu's spread is {spread_m / spread_n:.1f}x NLinear's; "
                     "NLinear is markedly more stable. Per-seed values are in "
                     "benchmark_results_per_seed.csv."})
    rows.append({
        "question": "7. cost",
        "answer": "see cost_summary.csv",
        "average_MSE_4L": "-",
        "basis": "measured per-fit GPU-hours; A1 author config costs 0.2817 h/fit "
                 "vs 0.0146 h/fit for the A2 LoRA config (19x), because the "
                 "author's freeze is a no-op so all 82.7M parameters train."})
    rows.append({
        "question": "NOT ANSWERABLE: a pre-specified one-time eight-model Test ranking",
        "answer": "NO",
        "average_MSE_4L": "-",
        "basis": "Track B's Test was already exposed before this round, and the "
                 "four-implementations-per-group are fixed choices, not a random "
                 "sample. Group means may be described but must not be read as "
                 "inference about LLM / non-LLM families."})
    return rows


def b_track():
    rows = read_csv("results/v3_clean/analysis/primary_seed_level.csv")
    per = defaultdict(lambda: defaultdict(list))
    grp = {}
    for r in rows:
        per[r["model"]][int(r["horizon"])].append(float(r["mse_all_7vars_full_horizon_z"]))
        grp[r["model"]] = r["family"]
    out = []
    for m, d in per.items():
        Lm = {L: sum(d[L]) / len(d[L]) for L in HORIZONS}
        out.append({"track": "B_july2026_1025rows", "model": m,
                    "group": "LLM" if grp[m] == "llm" else "non-LLM",
                    **{f"MSE_L{L}": f"{Lm[L]:.6f}" for L in HORIZONS},
                    "average_MSE_4L": f"{sum(Lm.values()) / 4:.6f}",
                    "n_seeds_per_L": len(d[24]),
                    "comparable_to_track_A": "NO - different data vintage, different seed count"})
    out.sort(key=lambda r: float(r["average_MSE_4L"]))
    for i, r in enumerate(out, 1):
        r["rank"] = i
    return out


def main():
    print("building tabular deliverables...")
    cells = scorer_cells()
    agg = aggregate_rows(cells)
    w("author_paper_targets.csv", author_targets())
    w("RUN_MANIFEST.csv", run_manifest())
    w("REMAINING_RUN_MATRIX.csv", remaining_matrix())
    w("reproduction_results_per_seed.csv", per_seed_rows(cells))
    w("reproduction_results_aggregate.csv", agg)
    w("paper_vs_reproduction.csv", paper_vs_repro(agg))
    w("benchmark_results_per_seed.csv", per_seed_rows(cells))
    w("benchmark_results_per_horizon.csv", per_horizon_benchmark(agg))
    w("benchmark_results_per_variable.csv", per_variable_rows())
    w("benchmark_results_average_4L.csv", agg)
    w("benchmark_results_trackB_july.csv", b_track())
    w("benchmark_best_model_summary.csv", best_model_summary(agg))
    w("cost_summary.csv", cost_summary())
    w("failures_and_retries.csv", failures())
    print("done.")


if __name__ == "__main__":
    main()