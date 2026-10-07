"""audit_publication.py — plan-completion audit, AUC-Best-so-far, resource audit,
publication-ready manuscript wording and final artifact integrity manifest.

OUTSIDE the frozen innovation source hash. No model execution, no Test access,
no reselection. Purely reads artifacts that already exist.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from scipy import stats as sps

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
INN = ROOT / "results" / "innovation"
TEV_ID = "final_nlinear_20260915T145710Z"
TEV = INN / "test_evaluations" / TEV_ID
AUD = INN / "final_audit"
FINAL = INN / "final"
for d in (AUD, FINAL):
    d.mkdir(parents=True, exist_ok=True)


def _j(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _wj(p, o):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def _sha(p):
    p = Path(p)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _rows(p):
    p = Path(p)
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _csv(p, rows, cols=None):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    cols = cols or list(rows[0].keys())
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _holm(pvals):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * pvals[i])
        adj[i] = min(1.0, run)
    return adj


man = _j(TEV / "test_evaluation_manifest.json")
cells = _rows(AUD / "test_cell_manifest.csv")
recomp = _rows(AUD / "metric_recomputation.csv")
integ = _j(AUD / "one_time_test_integrity.json")
recon = _j(AUD / "execution_reconciliation.json")
stats_audit = _j(AUD / "statistical_audit.json")
champ = man.get("champion", "nlinear")
base = sorted({c["model_key"] for c in cells if c["role"] == "baseline"})
BL = base[0] if base else "gpt2_miflu"
horizons = sorted({int(c["horizon"]) for c in cells})

# ══ A. z-space (PRIMARY) paired tests ═══════════════════════════════════════
def vals(m, L, key):
    return [float(r[f"recomp_{key}"]) for r in recomp
            if r.get("model_key") == m and int(r.get("horizon")) == L
            and r.get(f"recomp_{key}") not in (None, "")]


zrows = []
for L in horizons:
    for metric in ("mse_all_z", "mae_all_z"):
        cs = {int(r["seed"]): float(r[f"recomp_{metric}"]) for r in recomp
              if r.get("model_key") == champ and int(r.get("horizon")) == L}
        bs = {int(r["seed"]): float(r[f"recomp_{metric}"]) for r in recomp
              if r.get("model_key") == BL and int(r.get("horizon")) == L}
        common = sorted(set(cs) & set(bs))
        if len(common) < 2:
            continue
        a = [cs[s] for s in common]
        b = [bs[s] for s in common]
        t, p = sps.ttest_rel(a, b)
        d = np.asarray(a) - np.asarray(b)
        zrows.append({"horizon": L, "metric": metric, "n_paired": len(common),
                      "champion_mean": float(np.mean(a)), "baseline_mean": float(np.mean(b)),
                      "mean_diff": float(np.mean(a) - np.mean(b)),
                      "pct_diff": float((np.mean(a) - np.mean(b)) / np.mean(b) * 100.0),
                      "p_raw": float(p),
                      "cohens_dz": float(d.mean() / d.std(ddof=1)) if d.std(ddof=1) > 0 else None})
adj = _holm([r["p_raw"] for r in zrows])
for r, a in zip(zrows, adj):
    r["p_holm"] = float(a)
    r["significant_holm_0.05"] = bool(a < 0.05)
_csv(AUD / "primary_zspace_paired_tests.csv", zrows)

# ══ B. plan requirement audit ═══════════════════════════════════════════════
ITEMS = [
    ("DLinear/NLinear", "COMPLETED", "both evaluated in Screening and Stage F"),
    ("TimesNet", "NOT_COMPLETED", "not implemented; not present in any run"),
    ("PatchTST", "COMPLETED", "evaluated in Screening and Stage F"),
    ("iTransformer", "COMPLETED", "evaluated in Screening and Stage F"),
    ("TimeMixer or ModernTCN", "NOT_COMPLETED", "neither implemented"),
    ("text encoder: none", "COMPLETED", "used by all non-LLM runs"),
    ("text encoder: TF-IDF+SVD", "NOT_COMPLETED", "not implemented"),
    ("text encoder: fastText", "NOT_COMPLETED", "not implemented"),
    ("text encoder: BERT/MiniLM", "NOT_COMPLETED", "not implemented"),
    ("text encoder: GPT-2", "COMPLETED", "frozen gpt2_miflu / MIFlu arm"),
    ("fusion: concat projection", "COMPLETED", "Stage G fusion ablation"),
    ("fusion: FiLM/gating", "COMPLETED", "Stage G fusion ablation"),
    ("fusion: cross-attention", "COMPLETED", "Stage G fusion ablation"),
    ("negative control: zero-text", "NOT_COMPLETED", "not run"),
    ("negative control: shuffled-text", "NOT_COMPLETED", "not run"),
    ("LLM/TSFM: Time-LLM-style", "NOT_COMPLETED", "not implemented"),
    ("LLM/TSFM: CALF/TimeCMA-style", "NOT_COMPLETED", "not implemented"),
    ("TSFM: Chronos", "NOT_COMPLETED", "unavailable locally"),
    ("TSFM: TimesFM", "NOT_COMPLETED", "unavailable locally"),
    ("TSFM: Moirai", "NOT_COMPLETED", "unavailable locally"),
    ("robustness analysis", "COMPLETED", "Stage I seed-repeat sweep (4 models x L24/60 x 3 seeds)"),
    ("common-date analysis", "COMPLETED", "final_common_date_comparison.csv"),
    ("COVID-period analysis", "NOT_COMPLETED", "not separately pre-registered or reported"),
    ("pre-COVID analysis", "NOT_COMPLETED",
     "not pre-registered; must not be retroactively presented as confirmatory"),
    ("resource analysis", "COMPLETED", "this audit (parameters, train time, GPU-hours)"),
    ("AUC-Best-so-far", "COMPLETED", "computed in this audit from Stage-F validation runs"),
    ("validation-only freeze", "COMPLETED", "freeze_audit.json passed=true"),
    ("one-time Test", "COMPLETED", "52/52 cells, single receipt"),
    ("EvoForecast", "NOT_COMPLETED", "optional extension; deferred, not attempted"),
    ("implementation completed", "COMPLETED", "frozen innovation source v2.10"),
    ("Smoke completed", "COMPLETED", "smoke runs present and annotated"),
    ("formal evaluation completed", "COMPLETED", "Stage F: 160 unique cells"),
    ("final Test completed", "COMPLETED", "52/52, integrity passed"),
    ("optional extension deferred", "NOT_COMPLETED", "EvoForecast"),
]
items = [{"requirement": a, "status": b, "evidence": c} for a, b, c in ITEMS]
counts = {}
for it in items:
    counts[it["status"]] = counts.get(it["status"], 0) + 1
plan_audit = {"generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
              "items": items, "counts": counts,
              "mandatory_main_study_complete": True,
              "whole_plan_complete": False,
              "reason": "Unavailable/deferred candidate families (TimesNet, TimeMixer/ModernTCN, "
                        "TF-IDF+SVD, fastText, BERT/MiniLM, zero-text/shuffled-text, "
                        "Time-LLM-style, CALF/TimeCMA-style, Chronos, TimesFM, Moirai), "
                        "unreported COVID/pre-COVID splits, and the optional EvoForecast arm "
                        "are not completed."}
_wj(FINAL / "plan_completion_audit.json", plan_audit)

ml = ["# Plan completion matrix", "",
      f"Generated {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')} UTC.", "",
      "Status vocabulary: `COMPLETED`, `VALID_REUSE`, `UNAVAILABLE_DEPENDENCY`,",
      "`DEFERRED_COMPUTE_BUDGET`, `EXCLUDED_WITH_JUSTIFICATION`, `NOT_COMPLETED`.", "",
      "| Requirement | Status | Evidence |", "|---|---|---|"]
for it in items:
    ml.append(f"| {it['requirement']} | **{it['status']}** | {it['evidence']} |")
ml += ["", f"Counts: {counts}", "",
       "**The whole broad plan is NOT declared complete.** Mandatory main-study items",
       "(formal evaluation, validation-only freeze, one-time Test) are complete; several",
       "candidate families are unavailable/deferred and EvoForecast was not attempted.", ""]
(FINAL / "plan_completion_matrix.md").write_text("\n".join(ml), encoding="utf-8")

# ══ C. AUC-Best-so-far ══════════════════════════════════════════════════════
facts = _j(INN / "screening_runs_facts.json")
coh = _j(INN / "governance" / "stage_provenance" / "stage_f_cohort_manifest.json")
cohort_ids = {c["run_id"] for c in coh.get("cohort", [])}
elig = [f for f in facts
        if f.get("run_id") in cohort_ids
        and f.get("status") == "ok"
        and f.get("experiment_stage") == "full"
        and f.get("best_val_mse") is not None
        and f.get("test_access_allowed") is False
        and not f.get("test_artifacts_written")]
elig.sort(key=lambda f: (f.get("run_id") or ""))
if elig:
    ys = [float(f["best_val_mse"]) for f in elig]
    worst, best = max(ys), min(ys)
    rng = (worst - best) or 1.0
    secs = [float(f.get("train_seconds") or 0.0) for f in elig]
    cum = np.cumsum(secs) / 3600.0
    x = (cum / cum[-1]) if cum[-1] > 0 else np.linspace(0, 1, len(elig))
    bsf, y = worst, []
    for v in ys:
        bsf = min(bsf, v)
        y.append((worst - bsf) / rng)
    auc = float(np.trapz(y, x))
    gpu_h = float(cum[-1])
else:
    auc, gpu_h, x, y = None, None, [], []

auc_rec = {
    "definition": "one evaluator call = one candidate model trained and scored on validation",
    "eligible_runs": len(elig),
    "excluded": {"smoke": True, "pilot": True, "failed_diagnostics": True,
                 "test": True, "post_freeze": True},
    "objective": "best validation MSE so far (lower is better)",
    "normalisation": "min-max over the eligible validation-MSE range; budget normalised "
                     "to cumulative GPU-hours / total",
    "integration": "trapezoid over normalised budget",
    "auc_best_so_far": auc,
    "total_gpu_hours": gpu_h,
    "caveat": "This measures MODEL-DISCOVERY EFFICIENCY under a fixed validation budget, "
              "not final disease-prediction accuracy. It does not replace MSE/MAE/PTE/PIE.",
}
_wj(AUD / "auc_best_so_far.json", auc_rec)

# ══ D. resource audit ═══════════════════════════════════════════════════════
by_model = {}
for f in facts:
    if f.get("model_key"):
        d = by_model.setdefault(f["model_key"], {"n": 0, "train_seconds": [],
                                                 "total_parameters": set(),
                                                 "trainable_parameters": set()})
        d["n"] += 1
        if f.get("train_seconds") is not None:
            d["train_seconds"].append(float(f["train_seconds"]))
        for k in ("total_parameters", "trainable_parameters"):
            if f.get(k) is not None:
                d[k].add(int(f[k]))
res = {"per_model": {}, "observed_on": "compute nodes (Slurm stingy jobs)",
       "login_node_compute": "PROHIBITED and recorded as an incident (see below)"}
for m, d in sorted(by_model.items()):
    res["per_model"][m] = {
        "n_runs": d["n"],
        "total_parameters": sorted(d["total_parameters"]),
        "trainable_parameters": sorted(d["trainable_parameters"]),
        "train_seconds_mean": float(np.mean(d["train_seconds"])) if d["train_seconds"] else None,
        "train_seconds_total": float(np.sum(d["train_seconds"])) if d["train_seconds"] else None,
    }
res["final_test"] = {"job_id": "560659", "partition": "stingy", "gres": "gpu:a100:1",
                     "time_limit": "02:00:00", "elapsed": "00:01:00", "exit_code": "0:0",
                     "node": "gpu-a100-03"}
res["checkpoint_verification_job"] = {"job_id": "560692", "partition": "stingy",
                                      "cpus": 2, "mem": "8G", "time_limit": "00:20:00"}
res["login_node_incident"] = {
    "date": "2026-09-16",
    "symptom": "SSH authentication succeeded but new shell creation hung",
    "root_cause": "one-time Test inference running via nohup on the login node entered "
                  "D state (uninterruptible I/O wait) and contributed to process/resource "
                  "blockage",
    "evidence": {"pid": 3032070, "stat": "D", "elapsed": "01:14:20",
                 "stalled_cell_count": 41},
    "recovery": "exact-process termination from an already-open shell "
                "(kill -9 3032070), then narrow pkill -9 -f run_one_time_test / controller.sh",
    "lawful_continuation": "same receipt, same manifest, same test_eval_id; missing cells "
                           "only; submitted through sbatch job 560659",
    "preventive_rule": "all future model computation through Slurm compute allocation only",
    "not_the_fault_of": "the cluster or the network",
}
res["job_failures_and_retries"] = {
    "slurm_jobs": recon.get("slurm_jobs_in_sacct"),
    "completed": recon.get("slurm_jobs_completed"),
    "failed": recon.get("slurm_jobs_failed"),
    "test_resume_retries": 1,
    "note": "one mechanical resume after the login-node process was terminated",
}
_wj(AUD / "resource_audit.json", res)

res_rows = []
for m, d in res["per_model"].items():
    res_rows.append({"scope": "validation/training", "model_key": m, "n_runs": d["n_runs"],
                     "total_parameters": "|".join(str(v) for v in d["total_parameters"]),
                     "trainable_parameters": "|".join(str(v) for v in d["trainable_parameters"]),
                     "train_seconds_mean": d["train_seconds_mean"],
                     "train_seconds_total": d["train_seconds_total"]})
res_rows.append({"scope": "final_test", "model_key": "nlinear+gpt2_miflu", "n_runs": 52,
                 "total_parameters": "", "trainable_parameters": "",
                 "train_seconds_mean": "", "train_seconds_total": 60.0})
_csv(FINAL / "final_resource_summary.csv", res_rows)

# ══ E. manuscript wording (zh / en) ═════════════════════════════════════════
def zs(m, L, k):
    v = vals(m, L, k)
    return float(np.mean(v)) if v else float("nan")


def red(m, L):
    a, b = zs(champ, L, "mse_all_z"), zs(m, L, "mse_all_z")
    return (b - a) / b * 100.0 if b else float("nan")


peak_by = {}
for r in recomp:
    if r.get("model_key") and r.get("horizon"):
        d = peak_by.setdefault((r["model_key"], int(r["horizon"])), {})
        d.setdefault("pte", []).append(float(r["recomp_mean_pte_weeks"]))
        d.setdefault("pie", []).append(float(r["recomp_mean_pie_pct"]))

reductions = [red(BL, L) for L in horizons]
en = ["# Results (manuscript-ready, English)", "",
      "## Primary metric", "",
      "Following MIFlu (IEEE JBHI 2025, §V-B), MSE and MAE in the normalised (z) space are the",
      "primary accuracy metrics; physical-unit values are reported as supplementary.", "",
      "## Test-set accuracy", "",
      "| Horizon | NLinear MSE (z) | MIFlu (GPT-2) MSE (z) | Reduction | NLinear MAE (z) | MIFlu MAE (z) |",
      "|---|---|---|---|---|---|"]
for L in horizons:
    en.append(f"| L={L} | {zs(champ, L, 'mse_all_z'):.4f} | {zs(BL, L, 'mse_all_z'):.4f} | "
              f"{red(BL, L):.2f}% | {zs(champ, L, 'mae_all_z'):.4f} | "
              f"{zs(BL, L, 'mae_all_z'):.4f} |")
en += ["",
       f"The frozen champion **{champ}** shows a *lower* Test MSE than the frozen MIFlu baseline "
       f"**{BL}** at all four horizons, with observed reductions of "
       f"{min(reductions):.2f}%--{max(reductions):.2f}% in z-space MSE. "
       "On MAE the two arms are effectively tied at L=48, where the baseline is marginally lower.",
       "",
       "## Statistical caveat (mandatory wording)", "",
       f"The baseline provides three seeds, so the effective paired sample size is "
       f"**{stats_audit['effective_paired_sample_size']}** per horizon, not ten. After Holm "
       "correction across all paired comparisons, only one comparison reaches significance. "
       "Accordingly we report **observed best** and make **no broad claim of statistical "
       "superiority**.", "",
       "## Peak criterion", "",
       "The only acceptance criterion implemented and reported is the literature criterion",
       "**PTE <= 1 week AND PIE <= 25%** (seasonal peak timing error and peak intensity error).",
       "", "| Model | L | mean PTE (weeks) | mean PIE (%) | criterion |", "|---|---|---|---|---|"]
for m in (champ, BL):
    for L in horizons:
        d = peak_by.get((m, L))
        if not d:
            continue
        pte, pie = float(np.mean(d["pte"])), float(np.mean(d["pie"]))
        ok = pte <= 1.0 and pie <= 25.0
        en.append(f"| {m} | {L} | {pte:.2f} | {pie:.2f} | {'MET' if ok else 'not met'} |")
en += ["", "NLinear meets the literature criterion at L=48 and L=60 and does not meet it at",
       "L=24 or L=36. The frozen MIFlu baseline does not meet it at any evaluated horizon.", "",
       "## Naming fidelity", "",
       "PatchTST- and iTransformer-based backbones are re-implementations **inspired by** the",
       "published architectures; they are described as `PatchTST-inspired` and",
       "`iTransformer-aligned`, not as official reference implementations.", "",
       "## Unavailable or deferred families", "",
       "TimesNet, TimeMixer/ModernTCN, TF-IDF+SVD, fastText, BERT/MiniLM, zero-text and",
       "shuffled-text negative controls, Time-LLM-style reprogramming, CALF/TimeCMA-style",
       "alignment, and Chronos/TimesFM/Moirai were **not** available or **not** completed and",
       "are therefore not reported as results.", ""]
(FINAL / "manuscript_results_en.md").write_text("\n".join(en), encoding="utf-8")

zh = ["# 结果（稿件可用，中文）", "",
      "## 主指标口径", "",
      "依照 MIFlu（IEEE JBHI 2025，§V-B），以归一化（z 空间）MSE 与 MAE 为**主**指标，",
      "物理量纲数值作为补充。", "",
      "## Test 集精度", "",
      "| Horizon | NLinear MSE(z) | MIFlu(GPT-2) MSE(z) | 降幅 | NLinear MAE(z) | MIFlu MAE(z) |",
      "|---|---|---|---|---|---|"]
for L in horizons:
    zh.append(f"| L={L} | {zs(champ, L, 'mse_all_z'):.4f} | {zs(BL, L, 'mse_all_z'):.4f} | "
              f"{red(BL, L):.2f}% | {zs(champ, L, 'mae_all_z'):.4f} | "
              f"{zs(BL, L, 'mae_all_z'):.4f} |")
zh += ["",
       f"冻结冠军 **{champ}** 在四个 horizon 上的 Test MSE 均**低于**冻结 MIFlu 基线 **{BL}**，",
       f"z 空间 MSE 的观测降幅为 {min(reductions):.2f}%–{max(reductions):.2f}%。",
       "MAE 上两臂在 L=48 基本持平，基线略低。", "",
       "## 统计表述限制（必须保留）", "",
       f"基线仅有 3 个 seed，因此每 horizon 的有效配对样本量为 "
       f"**{stats_audit['effective_paired_sample_size']}**，而非十个。",
       "对所有配对比较做 Holm 校正后，仅一项达到显著。因此我们只报 **observed best**，",
       "**不声称广泛的统计优越性**。", "",
       "## 峰值判据", "",
       "唯一实现并报告的验收标准为文献判据：**PTE ≤ 1 周 且 PIE ≤ 25%**。", "",
       "| 模型 | L | 平均 PTE（周） | 平均 PIE（%） | 判定 |", "|---|---|---|---|---|"]
for m in (champ, BL):
    for L in horizons:
        d = peak_by.get((m, L))
        if not d:
            continue
        pte, pie = float(np.mean(d["pte"])), float(np.mean(d["pie"]))
        ok = pte <= 1.0 and pie <= 25.0
        zh.append(f"| {m} | {L} | {pte:.2f} | {pie:.2f} | {'达标' if ok else '未达标'} |")
zh += ["", "NLinear 在 L=48 与 L=60 达标，在 L=24 与 L=36 未达标；冻结 MIFlu 基线在所有",
       "被评估 horizon 上均未达标。", "",
       "## 命名忠实性", "",
       "PatchTST 与 iTransformer 骨干为受已发表架构**启发**的重新实现，表述为",
       "「PatchTST-inspired」与「iTransformer-aligned」，不声称官方参考实现。", "",
       "## 不可用或延迟的候选族", "",
       "TimesNet、TimeMixer/ModernTCN、TF-IDF+SVD、fastText、BERT/MiniLM、zero-text 与",
       "shuffled-text 负对照、Time-LLM 风格 reprogramming、CALF/TimeCMA 风格对齐，以及",
       "Chronos/TimesFM/Moirai 均**不可用或未完成**，故不作为结果报告。", ""]
(FINAL / "manuscript_results_zh.md").write_text("\n".join(zh), encoding="utf-8")

meth_en = """# Methods (manuscript-ready, English)

## Data and splitting
National ILI series. One fixed chronological split (train/validation/test) shared by all
arms. The scaler and prompt statistics are fitted on the training split only. Test never
participates in early stopping, hyper-parameter choice, model selection or thresholding.

## Protocol
Four horizons L in {24, 36, 48, 60} are trained and scored independently; predictions are
never merged across lead times. Ten seeds (42-51) for the champion arm; the frozen MIFlu
baseline provides three seeds (42-44).

## Two-level criteria
Level 1 (when to stop training): validation MSE only, patience=7, best-validation-MSE
checkpoint restored. Level 2 (post-hoc accuracy): PTE and PIE against the literature
criterion PTE <= 1 week AND PIE <= 25%. No project-defined acceptance threshold is
implemented or reported.

## Champion selection and Test isolation
Selection uses validation only, on the pre-registered Stage-F cohort of 160 unique cells.
The champion is frozen before any Test access. A single-use receipt authorises exactly one
Test evaluation, whose 52-cell manifest is immutable and created before access. Test results
never influenced selection, retraining or thresholding.

## Statistics
Per-horizon means, standard deviations and percentile bootstrap 95% CIs
(10,000 resamples, fixed RNG seed). Paired comparisons use identical (horizon, seed) pairs;
effect size is Cohen's dz; multiplicity is controlled with Holm across the whole family of
paired comparisons. Where a corrected p-value does not support a claim, the wording is
"observed best".
"""
(FINAL / "manuscript_methods_en.md").write_text(meth_en, encoding="utf-8")

meth_zh = """# 方法（稿件可用，中文）

## 数据与切分
国家级 ILI 序列。所有方法共享同一固定时序切分（train/validation/test）。scaler 与 prompt
统计仅在训练段拟合。Test 从不参与 early stopping、超参选择、模型选择或阈值制定。

## 协议
L ∈ {24, 36, 48, 60} 四个 horizon 独立训练与评分，预测绝不跨 lead time 合并。冠军臂使用
10 个 seed（42–51）；冻结 MIFlu 基线提供 3 个 seed（42–44）。

## 两层标准
第一层（何时停止训练）：仅看 validation MSE，patience=7，恢复最低 validation MSE 的
checkpoint。第二层（训练后精度验收）：PTE 与 PIE，唯一判据为文献标准 PTE ≤ 1 周且
PIE ≤ 25%。未实现也未报告任何项目自定的验收阈值。

## 冠军选择与 Test 隔离
选择仅基于 validation，在预注册的 Stage-F 队列（160 个唯一单元）上进行。冠军在任何
Test 访问之前冻结。单次授权收据只允许一次 Test 评估，其 52 单元清单不可变且在访问前创建。
Test 结果从未影响选择、重训或阈值。

## 统计
每个 horizon 报均值、标准差与百分位 bootstrap 95% CI（10,000 次重抽样，固定随机种子）。
配对比较使用相同的 (horizon, seed) 配对；效应量为 Cohen's dz；对全部配对比较族做 Holm
校正。若校正后 p 值不支持，则表述为「observed best」。
"""
(FINAL / "manuscript_methods_zh.md").write_text(meth_zh, encoding="utf-8")

lim_en = """# Limitations (manuscript-ready, English)

1. **Baseline seed count.** The frozen MIFlu baseline provides three seeds, so paired
   inference has an effective sample size of three per horizon. No broad statistical
   superiority is claimed; only one comparison survives Holm correction.
2. **Unavailable candidate families.** TimesNet, TimeMixer/ModernTCN, TF-IDF+SVD, fastText,
   BERT/MiniLM, zero-text and shuffled-text negative controls, Time-LLM-style reprogramming,
   CALF/TimeCMA-style alignment, and Chronos/TimesFM/Moirai were unavailable or not
   completed. Conclusions do not extend to them.
3. **Historical repository integrity.** The pre-incident byte identity of one indicator
   script could not be established; the current canonical script was adopted prospectively
   with a regression check against a trusted pre-incident prediction file. This is a
   reproducibility limitation, not a scientific result.
4. **Source-version repair history.** Ten implementation-source revisions (v2.1-v2.10) were
   required. None changed the scientific protocol, splits, scaler, prompt statistics,
   metrics, thresholds or early stopping.
5. **Login-node incident (2026-09-16).** The one-time Test was initially executed as a
   `nohup` process on a login node, which is prohibited; it entered D state and blocked new
   SSH sessions. It was terminated, and the remaining immutable Test cells were completed
   through a compliant `sbatch` job reusing the same receipt, manifest and evaluation ID.
   This is disclosed as a **process** incident in reproducibility materials; it did not alter
   any scientific input, checkpoint or metric.
6. **EvoForecast.** The optional AlphaEvolve-inspired arm was not attempted and must not be
   described as completed.
7. **COVID/pre-COVID splits.** Not pre-registered; not presented as confirmatory analysis.
"""
(FINAL / "manuscript_limitations_en.md").write_text(lim_en, encoding="utf-8")

lim_zh = """# 局限性（稿件可用，中文）

1. **基线 seed 数量。** 冻结 MIFlu 基线仅提供 3 个 seed，因此每 horizon 的配对推断有效
   样本量为 3。不声称广泛的统计优越性；Holm 校正后仅一项比较显著。
2. **不可用候选族。** TimesNet、TimeMixer/ModernTCN、TF-IDF+SVD、fastText、BERT/MiniLM、
   zero-text 与 shuffled-text 负对照、Time-LLM 风格 reprogramming、CALF/TimeCMA 风格对齐，
   以及 Chronos/TimesFM/Moirai 均不可用或未完成，结论不推广至这些族。
3. **历史仓库完整性。** 某一个指标脚本在事故前的字节同一性无法确立；现行规范脚本系前瞻性
   采纳，并以事故前可信预测文件做回归校验。这是可复现性限制，不是科学结果。
4. **源码版本修复史。** 经历 v2.1–v2.10 共十次实现版本修订，均未改变科学协议、切分、
   scaler、prompt 统计、指标、阈值或早停策略。
5. **登录节点事故（2026-09-16）。** 一次性 Test 最初以 `nohup` 在登录节点执行（违规），
   进入 D 状态并阻塞新建 SSH 会话。该进程被终止后，剩余不可变单元通过合规的 `sbatch`
   作业完成，复用同一收据、同一清单与同一评估 ID。此事作为**流程**事故在可复现性材料中
   披露，未改变任何科学输入、checkpoint 或指标。
6. **EvoForecast。** 可选的 AlphaEvolve 启发分支未尝试，不得描述为已完成。
7. **COVID / pre-COVID 分段。** 未预注册，不作为验证性分析呈现。
"""
(FINAL / "manuscript_limitations_zh.md").write_text(lim_zh, encoding="utf-8")

# ══ F. final artifact integrity manifest ════════════════════════════════════
CANON = []
for p in sorted(FINAL.rglob("*")):
    if p.is_file():
        CANON.append({"canonical_path": str(p.relative_to(ROOT)).replace("\\", "/"),
                      "role": "final_report" if p.suffix in (".md", ".csv", ".json") else "other",
                      "bytes": p.stat().st_size, "sha256": _sha(p),
                      "source_test_eval_id": TEV_ID,
                      "source_checkpoint_hash": "",
                      "generated_utc": datetime.datetime.utcfromtimestamp(
                          p.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "classification": "derived"})
for p in sorted((TEV / "figures").rglob("*")):
    if p.is_file():
        CANON.append({"canonical_path": str(p.relative_to(ROOT)).replace("\\", "/"),
                      "role": "figure", "bytes": p.stat().st_size, "sha256": _sha(p),
                      "source_test_eval_id": TEV_ID, "source_checkpoint_hash": "",
                      "generated_utc": datetime.datetime.utcfromtimestamp(
                          p.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "classification": "derived"})
for p in sorted(AUD.rglob("*")):
    if p.is_file():
        CANON.append({"canonical_path": str(p.relative_to(ROOT)).replace("\\", "/"),
                      "role": "final_audit", "bytes": p.stat().st_size, "sha256": _sha(p),
                      "source_test_eval_id": TEV_ID, "source_checkpoint_hash": "",
                      "generated_utc": datetime.datetime.utcfromtimestamp(
                          p.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "classification": "derived"})

seen, dup = {}, []
for r in CANON:
    k = r["canonical_path"]
    if k in seen and seen[k] != r["sha256"]:
        dup.append(k)
    seen[k] = r["sha256"]
manifest = {"generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "test_eval_id": TEV_ID, "n_artifacts": len(CANON),
            "duplicate_canonical_paths_with_conflicting_content": dup,
            "artifacts": CANON}
_wj(FINAL / "final_artifact_manifest.json", manifest)
_csv(FINAL / "final_artifact_manifest.csv", CANON)

print("[pub] plan_items=%d counts=%s" % (len(items), counts))
print("[pub] auc_best_so_far=%s over %d eligible runs (%.4f GPU-h)"
      % (round(auc, 6) if auc is not None else None, len(elig), gpu_h or 0))
print("[pub] artifacts=%d conflicts=%d" % (len(CANON), len(dup)))
print("[pub] z_space_holm_significant=%s"
      % ([f"L{r['horizon']} {r['metric']}" for r in zrows if r["significant_holm_0.05"]] or "none"))
