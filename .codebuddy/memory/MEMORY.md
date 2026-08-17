# MLFlu Project — Long-Term Memory

## HPC Deployment (CityUHK Burgundy)
- **Login FQDN: `burgundy.hpc.cityu.edu.hk`** (this is the correct host; `hpclogin02` is WRONG/deprecated — do NOT use it). SSH alias `cityu` maps to this. Backup IP `144.214.138.99` if DNS fails.
- User: `sychan552`; scratch workspace: `$HOME/scratch/CHATTIME` (symlink to `/gpfs1/scratch/sychan552/CHATTIME`); project code at `/home/sychan552/scratch/CHATTIME/Chattime/`. (Verified 2026-08-16 — the earlier `MLFlu_Q1` path is WRONG/obsolete.)
- **⚠️ Remote dir map (verified 2026-08-16)**:
  - `/home/sychan552/scratch/CHATTIME/Chattime/` = **AUTHORITATIVE Phase-1 working dir** (MIFlu paper-protocol scripts uploaded, HPC_GUIDE §6 aligned). Train here.
  - `/home/sychan552/scratch/MLFLU/` = **LEGACY / DO-NOT-USE** (old L=52 workspace, `L_list=[52]`, incomplete checkpoints L24/L36/L52 only). Historical leftover; NOT deleted, but never submit training from here or read its ckpts as Phase-1 results.
  - `/home/sychan552/scratch/MLFlu_Q1/` = **DOES NOT EXIST** (obsolete path reference).
- **Mandatory after maintenance**: `module unload default && module load old_modules` before any other module.
- Module `anaconda3` NO LONGER EXISTS. Use `miniconda/python-3.9` (or `anaconda/3-2024.02`).
- **Reliable conda activation in SLURM**: do NOT rely on `module load miniconda` + `conda activate` (fails on GPU compute nodes intermittently, and `conda.sh` is not at standard path). Instead prepend absolute PATH:
  `export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH`
  Env lives at `/home/sychan552/.conda/envs/mlflu_hpc` (visible from compute nodes too).
- **SLURM pitfall**: `#SBATCH --output=$HOME/...` does NOT expand `$HOME` in directives → creates nested literal `$HOME` dir. Use absolute paths in `--output`/`--error`.
- Cache to scratch: `export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache; export TRANSFORMERS_CACHE=$HF_HOME` (protect 50GB home quota).
- Conda env: `mlflu_hpc` python3.9, PyTorch 2.5.1 CUDA11.8, transformers 4.57.6, peft, scipy, matplotlib, pandas, numpy.

## Training / Figure Scripts (current equivalents — verified 2026-08-16)
> **DELETED (2026-08-14) — do NOT reference these anymore**: `make_forecast_figure.py`,
> `figure_q1.sh`, `figure_q1_L36/L48/L60.sh`, `train_q1_L24/L36/L48/L60.sh`, `train_q1_L52.sh`,
> `infer_walkforward_L52.sh`. If a future session looks for them, they no longer exist.
- `scripts/train_miflu.py`: **authoritative MIFlu training entry point**. Single horizon via
  `--horizon L` (else full sweep `L_list=[24,36,48,60]`); 10 reps; static 70:10:20 split (no shuffle);
  scaler fit on TRAIN only; test target start strictly > val end. Saves `best_miflu_L{L}.pth`
  (best val_loss rep) + `data/results_miflu_paper_protocol_*.csv` + `data/predictions_miflu_L{L}_paper_protocol.csv`.
- `scripts/submit_miflu_paper_protocol.sh`: **authoritative SLURM submit** (replaces the deleted
  `train_q1_L*.sh`). `stingy` + `gpu:a100:1` + `--time=04:00:00` + PATH-prepend conda(`mlflu_hpc`)
  + HF cache(scratch). Submit four horizons independently:
  `for L in 24 36 48 60; do MIFLU_HORIZON=$L sbatch .../scripts/submit_miflu_paper_protocol.sh; done`
- `scripts/make_miflu_evaluation_figure.py`: **authoritative figure script** (replaces deleted
  `make_forecast_figure.py`). Reads the per-L split-CSV, plots **test only**, emits
  `fig_miflu_eval_continuous_L{L}.png` etc. Deprecated L=52 branch gated behind `--walkforward_csv`
  and emits `*_DEPRECATED` artifacts.
- `scripts/compute_miflu_indicators.py`: per-horizon peak/trend indicators (Timing/Peak-Hit/
  Peak-Intensity, Fix-Brief #3 semantics) on the paper-protocol CSVs.
- `scripts/feature_verification.py`: 3-tier feature check (Granger/RF/SHAP) for N=7.

## Bugs Fixed (2026-08-06 run)
1. **L=36 first training (job 491036) → all NaN**: caused by concurrent training jobs sharing one GPU node (`gpu-v100s-06`); re-submitting L=36 alone (491106) trained fine (loss normal from ep1). Lesson: avoid submitting multiple training jobs concurrently on same node; submit sequentially or ensure separate GPUs.
2. **`make_forecast_figure.py` crash `IndexError: index 202008`** at false-peak annotation (line ~306): `falsep` list stores **epiweek values** (e.g. 202008) but drawing code used them as array indices. Fixed by resolving epiweek→index via `np.where(fc_epiweeks==pp)`. Only triggers when a horizon has a "false peak" (L=48 did; L=24/60 had empty falsep so escaped). Applies to all L; fixed globally.

## Cross-Reference Convention (2026-08-14, UPDATED 2026-08-17)
- **唯一交叉参考 = `MIFlu_paper.md`**（论文 PDF 的**直接 markdown 转换**，IEEE JBHI 2025，Moon et al.）。这是当前唯一权威的论文口径来源。
- ⚠️ **旧 `MIFlu_Complete_Extraction.md` 已删除（2026-08-17）**。它含**至少一处编造内容**（如声称 OT 为"黑箱 best guess"、prompt 用 `{min1}`..`{max7}` 占位符等，与 PDF Table X 实际 `<min(X1_train)>` 等不符），**不得再引用**。任何源自该旧文件的结论都必须用 `MIFlu_paper.md` 重新核对后才能采用。
- 已删除：`miflu_ground_truth.json`、3 个提取 .txt、旧 `REPRODUCTION_PROOF_V2_ZH.md`、`MLFlu_forecast_figure.md`、`MIFlu_Complete_Extraction.md`。核对论文口径只用 `MIFlu_paper.md`，不引用任何提取 .txt/json/旧 md。

## Evaluation Protocol (current — AUTHORITATIVE)
- **唯一权威协议 = MIFlu 论文协议**: `L ∈ {24, 36, 48, 60}` 四档**独立**训练/评估，每档 10 reps，
  **静态 70:10:20 切分**（shuffle=False，不重叠窗口），scaler 仅 fit 于 TRAIN，test target 起点
  严格 > val 终点。N=7 (OT=num_patients（CDC 总就诊人次/分母，全量未缩放），是**我们自己的实现选择**，论文 Table X 仅称其为
  "'OT' feature for long-term forecasting task"，未给公式、未称黑箱)。T=104。
- 4 指标阈值: Peak Hit≥0.75 / Timing≤2.0 / Peak Intensity≤20.0 / Direction≥0.60（per-horizon 计算）。
- **L=52 walk-forward 已废弃**: 曾在 2026-08-14~08-16 短暂作为主协议，现**已废弃并隔离到
  `scripts/chattime_variant/generate_walkforward.py`**，**仅作 Phase 2 ChatTime 对照参考**，
  **不得再作为 MIFlu 复现的主结论来源**。其产物（`results/ili/miflu_fulltest_walkforward.csv`、
  连续图、peak metrics）一律标记 DEPRECATED，与论文协议表/图**禁止混用**。

## Protocol History / Flip-Flop Warning
- **时间线（一句话）**: 2026-08 初定 L=24/36/48/60 四档独立协议 → 2026-08-14 一度删除四档、
  改成 L=52 连续 walk-forward 作主协议 → 2026-08-16 经审计确认后**重建四档独立协议为唯一权威**，
  L=52 降级为废弃隔离项。
- **🔴 硬性规则（不可绕过）**: 未来任何要把主协议**改回 L=52** 或**任何非论文原版协议**
  （如改切分比例、改 N、改独立档为滚动窗口等）的改动，**必须先获得用户显式确认**，且**必须同步更新
  本文件（MEMORY.md）、两端 `HPC_GUIDE.md`（本地+远端）、`PROJECT_STATE.md` 三处，缺一不可**。
  缺任一处的协议变更视为未完成、无效，禁止据此提交训练或下结论。

## Results (2026-08-06)
- All 4 horizons (L=24/36/48/60) trained + figured successfully.
- Local copy: `hpc_results/data/` (16 PNGs + 4 CSVs + 4 .pth checkpoints).
- Notable result: L=24 COVID Wave 1 peak (epiweek 202006 = 111,361) flagged as **GT (missed)** by model (pred ~47,962, -56.9%) → this is the Missed peak the Peak Ledger (Fig B2) is designed to surface for retrospective revision.
