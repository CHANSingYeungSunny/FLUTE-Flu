# MIFlu 作者仓库解读 / Author Repository Explained

> **What this is / 这是什么**：对论文官方代码仓库 `https://github.com/Jmoon3108/MIFlu`
> （已验证为作者原始仓库，非 fork；本地检出于 `recovery/author_repo/`，gitignore 不入库）
> 的结构解读，以及"论文章节 ↔ 代码文件"对照表。

---

## 1. Big picture / 一句话看懂

该仓库就是论文的官方实现，入口 `main_ILI_lora.py`：解析参数 → `data_provider/` 读
`dataset/illness/national_illness.csv` → 在 `models/` 里选模型（MIFlu 本体 =
`models/GPT4TS_lora.py`，即"前 K 层 GPT-2 + LoRA"的预测 LLM）→ 用 `utils/tools.py`
的 `vali/test` 循环训练与评估 → 输出 MSE/MAE。

> 中文要点：这是论文官方代码。核心模型叫 `GPT4TS_lora.py`（GPT4TS + LoRA = MIFlu 的预测 LLM），
> 入口 `main_ILI_lora.py`，数据在 `dataset/illness/national_illness.csv`。

## 2. Directory map / 目录结构

```
recovery/author_repo/                      # = github.com/Jmoon3108/MIFlu (local clone)
├── main_ILI_lora.py                       # ★ ENTRY POINT: argparse + train()/vali/test loop
├── text_emb.ipynb                         # notebook that generates precomputed text embeddings
├── models/
│   ├── GPT4TS_lora.py                     # ★ MIFlu core: GPT-2(K layers) + LoRA(r=4 on c_attn)
│   ├── GPT4TS.py / GPT4TS_new.py / GPT4TS_orig.py   # GPT4TS baseline variants (no/other adaptation)
│   ├── DLinear.py                         # linear decomposition baseline
│   └── PatchTST.py                        # patch-based transformer baseline
├── data_provider/
│   ├── data_factory.py                    # data_provider() dispatcher
│   └── data_loader.py                     # Dataset/DataLoader for the custom CSV
├── utils/
│   ├── metrics.py                         # MSE/MAE/etc.
│   ├── timefeatures.py                    # time feature encodings (timeF)
│   └── tools.py                           # EarlyStopping, adjust_learning_rate, vali, test, visual
└── dataset/illness/
    ├── national_illness.csv               # ★ AUTHOR DATA, 966 rows, sha256 2a96dfed…ebfe5
    ├── national_illness_orig.csv          # same values, human-readable headers (8594cecb…)
    └── text_emb/… (28 .txt)               # precomputed textual embeddings (from text_emb.ipynb)
```

## 3. Paper ↔ code mapping / 论文章节 ↔ 代码对照

| Paper (Section) | Concept | Where in repo |
|-----------------|---------|---------------|
| IV-A Textual input embedder | prompt → tokenizer → frozen GPT-2 → `h_text` | `text_emb.ipynb` (embeddings generated offline) + `dataset/illness/text_emb/*.txt` (loaded at runtime) |
| IV-B Time-series input embedder | instance norm → patching → linear embedder | `models/GPT4TS_lora.py` (PatchEmbedding-style layer; `--patch_size 24`, `--stride 2`) |
| IV-C Forecasting LLM | GPT-2 first K layers + LoRA r=4 on attention, PE+LN trainable, output projection | `models/GPT4TS_lora.py` (class `GPT4TS`, `CustomConfig`) |
| V-C Experimental details | Table IV hyperparameters | `main_ILI_lora.py` argparse (⚠ defaults ≠ paper, see §5) |
| V-A Dataset | 966-row National-Illness | `dataset/illness/national_illness.csv` |
| V-B Metrics | MSE/MAE (normalized space) | `utils/metrics.py` + `vali/test` in `utils/tools.py` |
| Table V baselines | GPT4TS / DLinear / PatchTST / … | `models/GPT4TS*.py`, `DLinear.py`, `PatchTST.py` (others imported from cited papers' code, not shipped here) |

## 4. Entry-point defaults worth knowing / 入口默认值（源码实测）

From `main_ILI_lora.py` argparse (line numbers ≈ 32–85):

| Arg | Repo default | Paper Table IV |
|-----|--------------|----------------|
| `--root_path` | `./dataset/illness/` | — |
| `--data_path` | `national_illness.csv` | — |
| `--seq_len` (T) | `104` | 104 ✅ |
| `--pred_len` (L) | `24` | 24/36/48/60 (pass per run) |
| `--batch_size` | `16` | 16 ✅ |
| `--learning_rate` | `0.0001` | **0.0005** ⚠ |
| `--train_epochs` | `1` | **20** ⚠ |
| `--lradj` | `type1` | not disclosed ⚠ |
| `--gpt_layers` (K) | `6` | 6 ✅ (national) |
| `--patch_size` (Lp) | `24` | 24 ✅ |
| `--stride` (S) | `2` | 2 ✅ |
| `--lora_r` / `--target_modules` | `4` / `["c_attn"]` | r=4 on attention ✅ |
| `--backbone` / `--textmodel` | `gpt2` / `gpt2` | full GPT-2 text embedder, GPT-2 forecasting ✅ |
| `--multimodal` / `--PEFT` / `--freeze` / `--pretrain` | `0/0/1/1` | switches for ablation |
| `fix_seed` | `2021` (module-level) | 10 repetitions, seeds not disclosed ⚠ |
| `--target` | `OT` | OT = total patient visits (denominator variable) |

⚠ = **repo default ≠ paper setting** — reproducing Table V requires explicitly passing paper values.
This mismatch is one documented source of our PARTIAL_REPRODUCTION gap.

## 5. How to run (author intent) / 作者原意运行方式

```bash
cd recovery/author_repo
python main_ILI_lora.py --model_id MIFlu_national_L24 --multimodal 1 --PEFT 1 \
  --root_path ./dataset/illness/ --data_path national_illness.csv \
  --seq_len 104 --pred_len 24 --batch_size 16 --learning_rate 0.0005 \
  --train_epochs 20 --gpt_layers 6 --patch_size 24 --stride 2 --lora_r 4
```

- `--multimodal 1` activates the text path (text embeddings from `text_emb/`);
  `--multimodal 0` = GPT4TS-style ablation (time-series only).
- `--PEFT 1` + `--lora_r 4` enables the LoRA adapters; `--freeze 1` keeps GPT-2 weights frozen.
- Output MSE/MAE are in the normalized (z) space, matching the national-task metric.

## 6. Data file identity / 数据文件身份（重要）

| File | Rows | sha256 | Note |
|------|-----:|--------|------|
| `dataset/illness/national_illness.csv` | 966 | `2a96dfed…ebfe5` | ★ **author's processed file — THE official data** |
| `dataset/illness/national_illness_orig.csv` | 966 | `8594cecb…` | identical parsed values, readable headers |
| `data/raw/national_illness_raw_paper_exact.csv` (our project) | 966 | `31ffc169…` | reformatted copy, value-identical |
| `data/raw/national_illness_raw.csv` (our project) | 1025 | `c2b983af…` | ⚠ DIFFERENT vintage (2026-07 FluView snapshot; CDC-revised values from MMWR 2016w40). NOT the author data — never mix scores. |

Author CSV `date` column is **synthetic** (2002-01-01 → 2020-06-30 at exact 7-day cadence), not real
CDC week labels. Full provenance: `recovery/data_identity_report.md`.

> 中文要点：正式数据 = 作者 966 行 `national_illness.csv`（SHA 2a96dfed…）；我们项目里那个 1025 行的
> CSV 是另一个 vintage 的 FluView 快照，数值不同，**绝不能混用来比较分数**。

## 7. Known caveats / 已知注意点

1. **Repo defaults drift from paper** (§4) — always pass Table IV values explicitly.
2. **Text embeddings are precomputed** (`text_emb/*.txt` from `text_emb.ipynb`), so the "frozen
   full GPT-2 textual embedder" runs offline; runtime loads embeddings.
3. **Text-path effectiveness is an OPEN CONTRADICTION in our audits** — GPU replay shows non-zero
   text-embedder gradients while CPU replay measured exactly zero effect; ablation evidence points
   both ways. Must be reported as unresolved (never claim it helps or is useless).
4. `--enc_in/--c_out = 862` defaults look like another dataset's width; national runs use the CSV's
   actual column count via the data loader.
5. Repo has no code for the other 10 Table V baselines (paper says they are taken from prior work).
