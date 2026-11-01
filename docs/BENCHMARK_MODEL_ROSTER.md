# Benchmark model roster — measured vs planned vs excluded

> **Read this before quoting any model count.** Three different lists are easy to
> confuse, and only ONE of them contains results.
>
> Last updated: 2026-11-01. Source of truth for measured numbers is
> `paper_tables/BENCH_*.csv`; this file only records *membership and status*.

---

## 1. MEASURED — in the benchmark results (13 non-LLM + 3 LLM = 16)

Every row below has 4 horizons × 3 seeds = 12 cells in
`hpc_results/expanded_runs/<model>_L<L>_s<seed>/pred_*.npz`, and appears in
`BENCH_MSE_BY_MODEL_L.csv`, `BENCH_PTE_PIE_BY_STEP.csv`, `BENCH_EFFICIENCY.csv`,
`BENCH_CRPS_WIS.csv`, `BENCH_PAIRED_TESTS.csv` and the 64 figures.

| # | model | family | params | status |
|---:|---|---|---:|---|
| 1 | PatchTST | transformer | 531,878 | ✅ measured |
| 2 | iTransformer | transformer | 75,672 | ✅ measured |
| 3 | **NLinear** | linear | 2,520 | ✅ measured |
| 4 | DNN | neural | 33,048 | ✅ measured |
| 5 | CNN | neural | 22,488 | ✅ measured |
| 6 | RNN | neural | 5,848 | ✅ measured |
| 7 | LSTM | neural | 18,712 | ✅ measured |
| 8 | GRU | neural | 14,424 | ✅ measured |
| 9 | Decision Tree | classical_ml | n/a | ✅ measured |
| 10 | Random Forest | classical_ml | n/a | ✅ measured |
| 11 | Gradient Boosting | classical_ml | n/a | ✅ measured |
| 12 | SVR | classical_ml | n/a | ✅ measured |
| 13 | KNN | classical_ml | n/a | ✅ measured |
| 14 | TimeCMA-LLM | llm | 125,830,824 | ✅ measured |
| 15 | Qwen-Time-LLM | llm | 1,544,084,680 | ✅ measured |
| 16 | CALF-LLM | llm | 126,421,416 | ✅ measured |

**DLinear is EXCLUDED by design** (it is already in the essay's Table V, so it is not a
new baseline). It must never appear in a table, figure or ranking.

**MIFlu** is not a benchmark competitor: it is the *reproduction target*, reported
separately against Table V (4-horizon mean 1.4995 vs 1.4355, +4.5 %).

---

## 2. PLANNED — NOT measured, NOT in any result table

These were selected as feasible additions. **None has been downloaded into a runnable
form, trained, or measured.** They appear only in `AGENTS.md` §6 and nowhere in
`paper_tables/`.

| class | model | params | approx size | note | status |
|---|---|---:|---:|---|---|
| S | `tencent/Penguin-Encoder` | 0.4 B | 0.8 GB | native Feature Extraction task | ❌ not run |
| S | `tencent/Hunyuan-1.8B-Instruct` | 2 B | 4 GB | | ❌ not run |
| S | `tencent/WeMM-Embedding-2B` | 3 B | 6 GB | embedding model | ❌ not run |
| S | `Qwen/Qwen2.5-1.5B` | 1.5 B | 3 GB | weights downloaded & offline-load verified | ❌ not trained |
| S | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | 1.5 B | 3 GB | weights downloaded & offline-load verified | ❌ not trained |
| M | `tencent/WeMM-Embedding-4B` | 5 B | 10 GB | best candidate (official embedding model) | ❌ not run |
| M | `tencent/Youtu-HiChunk` | 4 B | 8 GB | Feature Extraction | ❌ not run |
| M | `tencent/Hunyuan-4B-Instruct` | 4 B | 8 GB | | ❌ not run |
| M | `tencent/ContextPilot-8B` | 8 B | 16 GB | | ❌ not run |
| M | `tencent/Hunyuan-7B-Instruct` | 8 B | 16 GB | | ❌ not run |
| M | `tencent/KaLM-Embedding-Gemma3-12B` | 12 B | 24 GB | Sentence Similarity | ❌ not run |
| M | `tencent/ContextPilot-14B` | 15 B | 30 GB | | ❌ not run |
| L | `Qwen/Qwen3.8-27B-FP8` | 28 B | 28.7 GB | weights downloaded; **`qwen3_5` unsupported by transformers 4.57.6** | 🟡 separate env in progress |
| L | `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` | 33 B | 66 GB | `qwen2` architecture → loads with the current stack | 🟡 download in progress |

Adding any of these to the results requires **three** things that are not yet in place:
(1) a frozen-encoder adapter producing `(B, 7, L)` from text features, (2) the
reproducibility protocol (pinned revision + manifest + frozen feature table), and
(3) a GPU slot. That is queue item §13.B → §13.LLM-arms in `AGENTS.md`.

---

## 3. EXCLUDED — with measured sizes (this table is a paper contribution)

Excluded for **size**, not for availability. Sizes below are from the HuggingFace model
pages, not estimates.

| model | params / repo size | reason |
|---|---|---|
| `tencent/Hy4-preview` / `-FP8` | 780 B / 804 B | far beyond any node here |
| `tencent/Hy3` / `-FP8` | 299 B | beyond memory |
| `tencent/Hunyuan-A13B-Instruct` | 80 B | beyond A100-40G |
| `tencent/DeepSeek-V3.1-Terminus-W4AFP8` | 349 B | beyond memory |
| `stepfun-ai/Step-5-Preview` | **650 GB** (23 shards) | beyond memory |
| `zai-org/GLM-5.3` | **756 GB** (141 shards) | beyond memory |
| `MiniMaxAI/MiniMax-M3.1-Flash` | **252 GB** | beyond A100-40G |
| `XiaomiMiMo/MiMo-V2.6-Pro-RL` | **573 GB** | beyond memory |
| `deepseek-ai/DeepSeek-V4-Flash` / `V4.1-Flash-1017` | 291 B / **763 B** | beyond memory |
| `audnai/penclaw-Kimi-K3.1-pro` | gated | weights not accessible |
| `stealth-model/space-bunny-alpha` | 141 GB GGUF | needs llama.cpp, breaks the uniform transformers pipeline |
| all Translation / Image-to-3D / Video models | — | task mismatch (not time-series representation learning) |

Paper sentence: *"The newest open models at the time of writing are 291 B–1.6 T; the
smallest DeepSeek release is 291 B. They are excluded by memory, not by availability.
Qwen3.8-27B was additionally excluded because its `qwen3_5` architecture is not
supported by the fixed `transformers` version used for all other arms, which we hold
constant for reproducibility."*

---

## 4. Summary counts

| category | count |
|---|---:|
| **Measured in the benchmark** | **16** |
| Planned, not run | 14 (10 Tencent + 4 Qwen/DeepSeek) |
| Excluded with a documented reason | 12 groups |
| Reproduction target (separate) | 1 (MIFlu) |

**Do not describe this as a "19-model" or "30-model" benchmark until the planned rows
actually have `pred_*.npz` and appear in `BENCH_*.csv`.**
