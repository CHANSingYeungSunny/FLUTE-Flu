# -*- coding: utf-8 -*-
"""Single source of every number used in the 01_最终报告.

Rule: a number may only enter the documents by being read here, and this module
reads `paper_tables/*.csv` (or a documented, citable constant).  The asserts at
the bottom pin the headline values that AGENTS.md / docs/STATE.md fix, so a
silent drift in the CSVs cannot silently change a document.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PT = os.path.join(ROOT, "02_数字表格")
FIG = os.path.join(ROOT, "01_最终报告", "figures")

# ----------------------------------------------------------------- data facts
N_ROWS = 966
N_CHANNELS = 7
TRAIN_END, VAL_END = 676, 773          # data/scaler_miflu_author966.json
TEST_ROWS = N_ROWS - VAL_END           # 193
MIN_TEST_TARGET_ROW = 773              # leakage guard, containment=strict
WINDOWS_AVAIL = {24: 170, 36: 158, 48: 146, 60: 134}
WINDOWS_EVAL = {24: 160, 36: 144, 48: 144, 60: 128}
HORIZONS = [24, 36, 48, 60]

SCALER = json.load(open(os.path.join(ROOT, "06_原始数据集", "scaler_miflu_author966.json"), encoding="utf-8"))
VAR_COLS = SCALER["var_cols"]            # 7 channels, canonical order
SCALER_MEAN = SCALER["mean"]
SCALER_STD = SCALER["std"]
ILITOTAL_IDX = VAR_COLS.index("ILITOTAL")
OT_IDX = VAR_COLS.index("OT")

# ------------------------------------------------------- reproduction (Table V)
# Paper values transcribed from reference_papers/MIFlu_..._Scheme.md, TABLE V
# (lines 249-261).  Cross-checked against paper_tables/ESSAY_VS_REPRODUCTION_TABLE_V.csv,
# which carries the same four numbers and the same 4-horizon mean 1.4355.
PAPER_MSE = {24: 1.542, 36: 1.422, 48: 1.414, 60: 1.364}
PAPER_MAE = {24: 0.726, 36: 0.779, 48: 0.757, 60: 0.719}
PAPER_MSE_4L = 1.4355
PAPER_MAE_4L = 0.7452

OURS_MSE = {24: 1.3045, 36: 1.3561, 48: 1.6543, 60: 1.6829}   # 10-rep means
OURS_MAE = {24: 0.7482, 36: 0.7712, 48: 0.8381, 60: 0.8596}   # 10-rep means, all four
# The authoritative reproduction table (paper value, ours, delta, MAE side).
TABLE_V = pd.read_csv(os.path.join(PT, "ESSAY_VS_REPRODUCTION_TABLE_V.csv"))
ORACLE = {   # per-seed 7-var aggregate MSE, seeds 2021..2030
    24: [1.240157, 1.201078, 1.284212, 1.259462, 1.464643,
         1.368497, 1.392309, 1.230425, 1.231536, 1.373057],
    36: [1.314358, 1.306645, 1.269466, 1.154099, 1.767328,
         1.312511, 1.400796, 1.302717, 1.404061, 1.328807],
    48: [1.482299, 1.711215, 1.663857, 1.879495, 1.723161,
         1.620327, 1.628296, 1.588157, 1.570881, 1.675020],
    60: [1.599641, 1.664878, 1.821282, 1.915250, 1.410785,
         1.984315, 1.614602, 1.401814, 1.520661, 1.895393],
}

# --------------------------------------------------------------- benchmark (16)
MSE_L = pd.read_csv(os.path.join(PT, "BENCH_MSE_BY_MODEL_L.csv"))
EFF = pd.read_csv(os.path.join(PT, "BENCH_EFFICIENCY.csv"))
NAIVE = pd.read_csv(os.path.join(PT, "BENCH_SEASONAL_NAIVE.csv"))
PTE = pd.read_csv(os.path.join(PT, "BENCH_PTE_PIE_BY_STEP.csv"))
PAIRED = pd.read_csv(os.path.join(PT, "BENCH_PAIRED_TESTS.csv"))
FAMILY_CSV = pd.read_csv(os.path.join(PT, "BENCH_MSE_BY_FAMILY.csv"))
PROV = pd.read_csv(os.path.join(PT, "BENCH_GPU_PROVENANCE.csv"))

EN_NAME = {
    "patchtst": "PatchTST", "nlinear": "NLinear", "dnn": "DNN",
    "timecma_llm": "TimeCMA", "gradient_boosting": "Gradient Boosting",
    "knn": "KNN", "random_forest": "Random Forest", "itransformer": "iTransformer",
    "decision_tree": "Decision Tree", "gru": "GRU", "lstm": "LSTM", "rnn": "RNN",
    "qwen_time_llm": "Qwen-Time", "svr": "SVR", "calf_llm": "CALF", "cnn": "CNN",
    "seasonal_naive": "Seasonal naive",
    # ── MIFlu + 11 frozen LLM encoder arms (GAP-A/GAP-B) ──
    "miflu": "MIFlu",
    "qwen25_1_5b": "Qwen2.5-1.5B",
    "ds_r1_distill_qwen1_5b": "DeepSeek-R1-Qwen-1.5B",
    "ds_r1_distill_qwen7b": "DeepSeek-R1-Qwen-7B",
    "ds_r1_distill_llama8b": "DeepSeek-R1-Llama-8B",
    "ds_r1_distill_qwen14b": "DeepSeek-R1-Qwen-14B",
    "ds_r1_distill_32b": "DeepSeek-R1-32B",
    "tencent_contextpilot_8b": "ContextPilot-8B",
    "tencent_contextpilot_14b": "ContextPilot-14B",
    "tencent_hunyuan_1p8b_instruct": "Hunyuan-1.8B",
    "tencent_hunyuan_4b_instruct": "Hunyuan-4B",
    "tencent_hunyuan_7b_instruct": "Hunyuan-7B",
}
FAMILY_EN = {
    "transformer": "Transformer", "linear": "Linear", "neural": "Neural",
    "llm": "LLM-based", "classical_ml": "Classical ML", "classical": "Classical ML",
    "llm_encoder": "Frozen LLM Encoder",
}
FAMILY_ZH = {
    "transformer": "Transformer", "linear": "线性", "neural": "神经网络",
    "llm": "基于 LLM", "classical_ml": "经典机器学习", "classical": "经典机器学习",
    "llm_encoder": "冻结 LLM 编码器",
}


def r4(x, nd=4):
    """Format a float with fixed decimals; '—' for NaN."""
    if x is None:
        return "—"
    try:
        if isinstance(x, float) and (np.isnan(x)):
            return "—"
    except (TypeError, ValueError):
        pass
    return f"{float(x):.{nd}f}"


def model_rank_table():
    """16 benchmark arms, ranked by 4-horizon mean 7-var z-space MSE."""
    d = MSE_L.copy()
    piv = d.pivot_table(index="model", columns="L", values="mse_7var_z", aggfunc="mean")
    mae = d.pivot_table(index="model", columns="L", values="mae_7var_z", aggfunc="mean")
    rows = []
    for m in piv.index:
        vals = [piv.loc[m, L] for L in HORIZONS]
        rows.append({
            "model": m,
            "family": d[d.model == m]["family"].iloc[0],
            "L": vals,
            "mean": float(np.mean(vals)),
            "mae_mean": float(np.mean([mae.loc[m, L] for L in HORIZONS])),
            "mae_L": [float(mae.loc[m, L]) for L in HORIZONS],
        })
    rows.sort(key=lambda r: r["mean"])
    params = {r.model: r.params for r in EFF.itertuples()}
    for r in rows:
        r["params"] = params.get(r["model"], float("nan"))
    return rows


RANK = model_rank_table()
BENCH_MEAN = {r["model"]: r["mean"] for r in RANK}


def pte_by_step():
    """Per model: mean over the 4 horizons of PTE/PIE at each fixed step + pass count."""
    out = {}
    for m, g in PTE.groupby("model"):
        steps = []
        for s in (0, 1, 2, 3):
            q = g[g.step == s]
            steps.append({
                "pte": float(q.PTE_wk.mean()),
                "pie": float(q.PIE_pct.mean()),
                "pass": bool((q.kramer_shaman_pass.astype(bool)).all() and len(q) > 0),
            })
        out[m] = {"steps": steps,
                  "passes": int(g.kramer_shaman_pass.astype(bool).sum()),
                  "n": int(len(g))}
    return out


PTE_STEP = pte_by_step()


def ks_order():
    """Models ordered by K&S peak-skill performance.
    Priority: (1) passes desc, (2) step-0 PTE asc, (3) step-0 PIE asc.
    This puts the peak-skill champion (NLinear) first, not the MSE champion."""
    def ks_key(m):
        v = PTE_STEP.get(m, {"passes": 0, "n": 16, "steps": []})
        passes = v.get("passes", 0)
        steps = v.get("steps", [])
        # Step 0 performance (1 week ahead) — most important
        s0_pte = steps[0].get("pte", 999) if steps else 999
        s0_pie = steps[0].get("pie", 999) if steps else 999
        return (-passes, s0_pte, s0_pie)
    all_models = [r["model"] for r in RANK]
    return sorted(all_models, key=ks_key)


def seasonal_mean():
    return float(NAIVE.mse_7var_z.mean())


def pareto_facts():
    e = EFF.dropna(subset=["params"]).sort_values("params")
    pt = e[e.model == "patchtst"].iloc[0]
    nl = e[e.model == "nlinear"].iloc[0]
    return {
        "slope": float(pt.mse_vs_log10params_slope),
        "r2": float(pt.mse_vs_log10params_r2),
        "n_params_models": int(len(e)),
        "patch_params": int(pt.params),
        "nlinear_params": int(nl.params),
        "ratio": float(pt.params / nl.params),
        "mse_gain_pct": float((nl.mse_mean - pt.mse_mean) / nl.mse_mean * 100),
        "pareto": [r.model for r in EFF.itertuples() if r.on_pareto is True],
        "patch_rel_improve": float(pt.rel_improve_vs_seasonal_pct),
    }


PARETO = pareto_facts()


# ------------------------------------------------- peak skill vs accuracy (28)
def _ks_summary():
    """Per-model K&S facts, read from BENCH_PTE_PIE_BY_STEP.csv (3 seeds per cell)."""
    out = {}
    for m, g in PTE.groupby("model"):
        s0 = g[g.step == 0]
        out[m] = {
            "passes": int(g.kramer_shaman_pass.astype(bool).sum()),
            "n": int(len(g)),
            "mean_pte": float(g.PTE_wk.mean()),
            "mean_pie": float(g.PIE_pct.mean()),
            "step0_pie": float(s0.PIE_pct.mean()),
            "step0_pte": float(s0.PTE_wk.mean()),
            "step0_passes": int(s0.kramer_shaman_pass.astype(bool).sum()),
        }
    return out


KS = _ks_summary()


def _spearman(x, y):
    """Spearman rho and its two-sided p, without requiring scipy at build time."""
    try:
        from scipy.stats import spearmanr
        r = spearmanr(x, y)
        return float(r.statistic), float(r.pvalue)
    except Exception:                                    # pragma: no cover
        rx, ry = pd.Series(x).rank(), pd.Series(y).rank()
        rho = float(np.corrcoef(rx, ry)[0, 1])
        n = len(rx)
        t = rho * np.sqrt((n - 2) / max(1e-12, 1 - rho ** 2))
        from math import erf, sqrt
        p = 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))
        return rho, float(p)


def _decoupling_facts():
    """Rank associations between accuracy (MSE) and peak skill across the 28 arms.

    Reported because the honest version of the 'MSE vs peak skill' claim is not
    'they are unrelated': across the whole roster they are positively correlated.
    The finding is that the *frontier* is ordered the other way round, and that
    the acceptance verdict does not follow the MSE rank.
    """
    d = pd.DataFrame({"mse": {r["model"]: r["mean"] for r in RANK}})
    d["pie"] = [KS[m]["mean_pie"] for m in d.index]
    d["pte"] = [KS[m]["mean_pte"] for m in d.index]
    d["passes"] = [KS[m]["passes"] for m in d.index]
    rho_pie, p_pie = _spearman(d.mse, d.pie)
    rho_pte, p_pte = _spearman(d.mse, d.pte)
    rho_pass, p_pass = _spearman(d.mse, d.passes)
    top3 = ["miflu", "patchtst", "nlinear"]
    return {
        "n": int(len(d)),
        "rho_pie": rho_pie, "p_pie": p_pie,
        "rho_pte": rho_pte, "p_pte": p_pte,
        "rho_pass": rho_pass, "p_pass": p_pass,
        "top3": top3,
        "top3_mse": [float(d.loc[m, "mse"]) for m in top3],
        "top3_pie": [float(d.loc[m, "pie"]) for m in top3],
        "top3_passes": [int(d.loc[m, "passes"]) for m in top3],
    }


DECOUPLE = _decoupling_facts()


def _encoder_facts():
    """The 11 frozen-encoder arms, read from the same ranking table."""
    enc = [r for r in RANK if r["family"] == "llm_encoder"]
    enc.sort(key=lambda r: r["mean"])
    return {
        "n": len(enc),
        "best": enc[0]["model"], "best_mse": float(enc[0]["mean"]),
        "worst": enc[-1]["model"], "worst_mse": float(enc[-1]["mean"]),
        "ratio_best": float(enc[0]["mean"] / BENCH_MEAN["miflu"]),
        "ratio_worst": float(enc[-1]["mean"] / BENCH_MEAN["miflu"]),
        "passes": sum(KS[r["model"]]["passes"] for r in enc),
        "all": [(r["model"], float(r["mean"])) for r in enc],
    }


ENC = _encoder_facts()

# ---------------------------------------------------------------- paired tests
# The exported CSV's `p_holm` column was produced with a reverse cumulative
# minimum, which is not a valid Holm adjustment.  The step-down adjustment is
# recomputed here from `p_raw`, so every document uses the correct value.  With
# m = 136 pairs and n = 12 cells the smallest attainable raw p is 2/2^12, hence
# the smallest attainable adjusted p is 136 * 0.000488 = 0.066: no pair can
# survive at 0.05, which is a statement about power, not about the models.
def _holm_adjust(p):
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for rank, idx in enumerate(order):
        run = max(run, (m - rank) * p[idx])
        adj[idx] = min(1.0, run)
    return adj


PAIRED = PAIRED.assign(p_holm=_holm_adjust(PAIRED.p_raw.values))
N_PAIRS = int(len(PAIRED))
N_PAIRS_SIG = int((PAIRED.p_holm < 0.05).sum())
N_RAW_SIG = int((PAIRED.p_raw < 0.05).sum())
HOLM_MIN = float(PAIRED.p_holm.min())
PAIR = PAIRED[((PAIRED.model_a == "nlinear") & (PAIRED.model_b == "patchtst"))].iloc[0]
PAIR_RANK = int((PAIRED.p_holm < PAIR.p_holm).sum()) + 1

# family counts, read from the CSV rather than typed into prose
FAMILY_COUNTS = {k: int(v) for k, v in
                 pd.read_csv(os.path.join(PT, "BENCH_MSE_BY_MODEL_L.csv"))
                 .groupby("family")["model"].nunique().items()}
N_CONVENTIONAL = int(sum(FAMILY_COUNTS.get(k, 0) for k in
                         ("classical_ml", "neural", "transformer", "linear")))
N_LLM_BASED = int(FAMILY_COUNTS.get("llm", 0))
N_ENCODERS = int(FAMILY_COUNTS.get("llm_encoder", 0))

# ------------------------------------------------------------- LLM encoder arms
LLM_ARMS = [
    ("Qwen2.5-1.5B", "Qwen2.5 (dense)", 1.5),
    ("DeepSeek-R1-Distill-Qwen-1.5B", "DeepSeek-R1 distill (Qwen2)", 1.5),
    ("DeepSeek-R1-Distill-Qwen-7B", "DeepSeek-R1 distill (Qwen2)", 7.0),
    ("DeepSeek-R1-Distill-Llama-8B", "DeepSeek-R1 distill (Llama)", 8.0),
    ("DeepSeek-R1-Distill-Qwen-14B", "DeepSeek-R1 distill (Qwen2)", 14.0),
    ("DeepSeek-R1-Distill-Qwen-32B", "DeepSeek-R1 distill (Qwen2)", 32.0),
    ("Tencent ContextPilot-8B", "Tencent ContextPilot", 8.0),
    ("Tencent ContextPilot-14B", "Tencent ContextPilot", 14.0),
    ("Tencent Hunyuan-1.8B", "Tencent Hunyuan", 1.8),
    ("Tencent Hunyuan-4B", "Tencent Hunyuan", 4.0),
    ("Tencent Hunyuan-7B", "Tencent Hunyuan", 7.0),
]
LLM_SKIPPED = [
    ("Tencent WeMM-Embedding-2B", "embedding-only: cannot emit per-layer hidden states"),
    ("Tencent WeMM-Embedding-4B", "embedding-only: cannot emit per-layer hidden states"),
]
LLM_EXCLUDED = [
    ("Tencent Penguin-Encoder", "requires trust_remote_code; not loadable in the pinned stack"),
    ("Tencent Youtu-HiChunk", "no per-layer hidden states exposed"),
    ("Tencent KaLM-Embedding-Gemma3-12B", "weight download failed"),
    ("Qwen3.8-27B-FP8", "FP8 dequantises to ~54.7 GB bf16; not downloaded"),
    ("Llama-70B", "does not fit an 80 GB A100"),
]
LLM_CELLS_DONE, LLM_CELLS_TOTAL = 132, 156

# ------------------------------------------------------------------- in flight
# Table VIII: 5 variants x 4 horizons x 3 seeds = 60 cells.  The snapshot that
# these documents are built from (MANIFEST.md, 3 Nov 2026 05:27) reports 27 of 60
# complete and no per-variant export pulled; one older note claims 60/60, which no
# artefact on disk supports.  The documents therefore report the design and the
# completion count, and claim no depth trend.
TABLE8_DONE, TABLE8_TOTAL = 27, 60
DRIVER_JOB = "722968"
ABLATION = [
    # variant, flag, cells (0 = reference row, not part of the 60), question
    ("full (K=6)", "default", 0, "Reference arm: the MIFlu benchmark instance itself (already in the benchmark table)."),
    ("no_lora", "--no-lora", 12, "Is the accuracy carried by the LoRA adaptation, or by the frozen backbone?"),
    ("K=2", "--num-layers 2", 12, "Depth ladder: does a 2-layer stack lose accuracy?"),
    ("K=4", "--num-layers 4", 12, "Depth ladder: the paper's regional depth."),
    ("K=8", "--num-layers 8", 12, "Depth ladder: does extra depth help?"),
    ("K=12", "--num-layers 12", 12, "Depth ladder: is there a capacity ceiling?"),
]

# --------------------------------------------------------------- defect ledger
DEFECTS = [
    ("A1", "Seed never reached the LLM training path; the adapter reset the RNG",
     "36 LLM cells bit-identical across seeds; every ±sd exactly 0", "Fixed 2026-11-02 03:57:47"),
    ("A2", "Best-val snapshot cloned the frozen encoder instead of the trainable head",
     "7B arm OOM; the 32B arm could never complete on any 80 GB A100", "Fixed"),
    ("A3", "revision: null in the arm registry (no queue/p2/ directory)",
     "every unblocked LLM cell terminated as skip.no-revision", "Fixed"),
    ("A4", "Two different HuggingFace cache layouts",
     "10 of 13 arms invisible to from_pretrained, after the GPU was allocated", "Fixed"),
    ("A5", "flock is not a cross-node mutex on GPFS",
     "two lanes lost each other's DONE markers; replaced by a mkdir lock", "Patched, unverified"),
    ("A6", "Attempt cap not enforced in the controller",
     "rows reached attempts=26 against a stated maximum of 2", "Open"),
    ("A7", "Two pipelines could not have executed at all (dispatch branch missing)",
     "Table VI / walk-forward rows would never have started", "Fixed"),
    ("A8", "persistent_driver.sh died exactly when it had work (set -u expansion)",
     "the queue stopped advancing with runnable rows left", "Fixed"),
]

# ------------------------------------------------------------------- artefacts
ABLATION_NOTE_EN = ("The `--no-text` ablation is bit-identical to the full model, because the text "
                    "embeddings sit behind the causal mask. It is reported as a structural "
                    "verification, never as an ablation effect.")
ABLATION_NOTE_ZH = ("`--no-text` 消融与完整模型逐位相同（bit-identical），因为文本嵌入位于因果掩码之后。"
                    "它只能作为结构验证报告，绝不能当作消融效应。")

WINDOW_WHY_EN = ("MIFlu's own loader uses DataLoader(batch_size=16, drop_last=True), which discards the "
                 "final partial batch: 170→160, 158→144, 146→144, 134→128. The discarded windows are "
                 "measurably harder (1.3929–1.4423 MSE, i.e. ~1.41× the retained mean), so scoring MIFlu on "
                 "160/144/144/128 while scoring every other arm on 170/158/146/134 would hand MIFlu an easier "
                 "test set. All 17 arms are therefore scored on the same cropped windows.")
WINDOW_WHY_ZH = ("MIFlu 自己的数据加载器使用 DataLoader(batch_size=16, drop_last=True)，会丢弃最后一个不满的"
                 "批次：170→160、158→144、146→144、134→128。被丢弃的窗口实测更难（MSE 1.3929–1.4423，约为保留"
                 "窗口均值的 1.41 倍）。若 MIFlu 按 160/144/144/128 计分而其他模型按 170/158/146/134 计分，"
                 "就等于给 MIFlu 一个更容易的测试集。因此全部 17 个模型统一在裁剪后的同一批窗口上计分。")

# ------------------------------------------------------------------- assertions
assert len(VAR_COLS) == 7
assert VAR_COLS[ILITOTAL_IDX] == "ILITOTAL"
assert abs(np.mean([PAPER_MSE[L] for L in HORIZONS]) - PAPER_MSE_4L) < 5e-4
assert abs(np.mean([OURS_MSE[L] for L in HORIZONS]) - 1.4995) < 5e-4, np.mean([OURS_MSE[L] for L in HORIZONS])
for L in HORIZONS:
    assert abs(np.mean(ORACLE[L]) - OURS_MSE[L]) < 5e-4, (L, np.mean(ORACLE[L]), OURS_MSE[L])
    row = TABLE_V[TABLE_V.L.astype(str) == str(L)].iloc[0]
    assert abs(float(row.our_MSE) - OURS_MSE[L]) < 5e-5, (L, row.our_MSE, OURS_MSE[L])
    assert abs(float(row.our_MAE) - OURS_MAE[L]) < 5e-5, (L, row.our_MAE, OURS_MAE[L])
assert abs(float(TABLE_V[TABLE_V.L.astype(str) == "4L-mean"].iloc[0].our_MAE) - 0.8043) < 5e-5
assert abs(BENCH_MEAN["patchtst"] - 1.6621) < 5e-4
assert abs(BENCH_MEAN["nlinear"] - 1.8716) < 5e-4
assert abs(BENCH_MEAN["dnn"] - 2.1415) < 5e-4
# 28 models: 16 non-LLM (excl DLinear) + MIFlu + 3 LLM + 11 LLM encoders (GAP-A/GAP-B complete)
# MIFlu benchmark row (3-seed mean 1.5574) is now the MSE champion, ahead of PatchTST (1.6621)
assert RANK[0]["model"] == "miflu" and len(RANK) == 28
assert "dlinear" not in BENCH_MEAN, "DLinear must stay excluded"
assert PTE_STEP["nlinear"]["passes"] == 4 and PTE_STEP["patchtst"]["passes"] == 0
# MIFlu also has 4 passes (GAP-A row now present); other models have 0
for m, v in PTE_STEP.items():
    if m not in ("nlinear", "miflu"):
        assert v["passes"] == 0, (m, v["passes"])
assert abs(PARETO["slope"] - 0.1171) < 5e-5 and abs(PARETO["r2"] - 0.0223) < 5e-5
assert set(PARETO["pareto"]) == {"nlinear", "patchtst"}
assert int(round(PARETO["ratio"])) == 211
assert abs(PARETO["mse_gain_pct"] - 11.2) < 0.06
assert len(PROV) == 204 and (PROV.gpu_type == "A100-SXM4-80GB").all()
assert (PROV.partition == "stingy").all()
# --- peak skill vs accuracy -------------------------------------------------
assert KS["miflu"]["passes"] == 4 and KS["nlinear"]["passes"] == 4
assert KS["patchtst"]["passes"] == 0
assert KS["nlinear"]["step0_passes"] == 4 and KS["miflu"]["step0_passes"] == 3
assert KS["miflu"]["mean_pte"] < KS["patchtst"]["mean_pte"] < KS["nlinear"]["mean_pte"]
assert KS["nlinear"]["mean_pie"] < KS["miflu"]["mean_pie"] < KS["patchtst"]["mean_pie"]
# The frontier is ordered the other way round from MSE: NLinear (3rd) has the
# best PIE, PatchTST (2nd) the worst of the three.
assert DECOUPLE["top3"] == ["miflu", "patchtst", "nlinear"]
assert DECOUPLE["top3_pie"][2] < DECOUPLE["top3_pie"][0] < DECOUPLE["top3_pie"][1]
assert DECOUPLE["top3_passes"] == [4, 0, 4]
assert abs(DECOUPLE["rho_pie"] - 0.7356) < 5e-3 and DECOUPLE["p_pie"] < 1e-4
assert abs(DECOUPLE["rho_pass"] + 0.4292) < 5e-3 and DECOUPLE["p_pass"] < 0.05
assert ENC["n"] == 11 and ENC["passes"] == 0
assert abs(ENC["best_mse"] - 4.7374) < 5e-4 and abs(ENC["worst_mse"] - 5.2049) < 5e-4
assert ENC["best_mse"] > BENCH_MEAN["decision_tree"]      # every encoder loses to a decision tree
assert abs(ENC["ratio_best"] - 3.04) < 0.01
# --- significance -----------------------------------------------------------
assert N_PAIRS == 136 and N_PAIRS_SIG == 0 and N_RAW_SIG == 128
assert abs(HOLM_MIN - 0.0664) < 5e-4
assert abs(float(PAIR.p_holm) - 0.1172) < 5e-4
# family decomposition: 13 conventional + 4 LLM-based + 11 frozen encoders = 28
assert (N_CONVENTIONAL, N_LLM_BASED, N_ENCODERS) == (13, 4, 11)
assert float(PAIR.mean_diff) > 0 and int(PAIR.wins_a) == 2
assert PAIR_RANK > 100, PAIR_RANK        # it is nowhere near the top six by p
assert TABLE8_DONE < TABLE8_TOTAL
