# MIFlu continuation package

Project: **CHAN Sing Yeung Sunny — Final Year Project**. Reference paper: Moon, Shim, Kim & Hwang, *MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme*, IEEE JBHI 29(10):7790–7801 (2025). Moon et al. authored the reference method and released upstream files, not Sunny's entire reproduction/extension codebase. Upstream source notices are preserved.

**PARTIAL_REPRODUCTION. Text pathway mechanism contradiction: UNRESOLVED.** This package adds evidence and prepared jobs; it does not replace the single authoritative historical DOCX/MD or claim new GPU results. No A/B historical data are merged. The data are US CDC National-Illness, SHA256 `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5`. Reference anchor: `966|L24|seed42`; other cells retain their actual L/seed.

Start with **TASK_STATUS.md** for the five task statuses, exact file paths and key numbers. Paths below are relative to this package root.

## Reproduce the local tasks

The bundle contains the required original MIFlu prediction CSVs, immutable author/R1B sources, four text matrices, scaler and frozen aggregate tables. The seven original non-MIFlu raw arrays are still absent. Selected prior CPU result CSVs are included for integration; the full prior prediction/checkpoint bundle remains the separately supplied previous artifact.

```bash
python code/reconstruct_peak_criteria.py --handoff inputs/handoff --out 04_benchmark/peak_criteria.json
python code/score_ilitotal.py --handoff inputs/handoff --out paper_tables
python code/integrate_paper_tables.py --handoff inputs/handoff --prior inputs/prior --target-scores paper_tables --out paper_tables
```

Local table work needs NumPy/Pandas; no GPU or model weights are needed. These calculations were performed with NumPy 2.3.5 and Pandas 2.2.3. CSVs retain computation precision; Markdown displays four decimals for MSE/MAE and two for percentages.

To recover missing original target errors later, extract the original prediction tarball into a separate directory and pass `--raw-root /path/to/extracted/original_arrays` to `score_ilitotal.py`. It accepts the original `pred_<model>_L<L>_s<seed>.npz` convention, validates strict-966 shapes/targets/origins, and will not substitute the new CPU NLinear for original Track C NLinear. Then rerun table integration.

## Stage the bundle on Burgundy

The supplied `inputs/handoff/00b_HPC_GUIDE.md` is preserved as evidence. Operational settings used here: one A100 on `stingy`, at most one submitted job at a time, wall time no more than four hours, and no model compute on login nodes. Its old ChatTime/deprecated-pipeline sections do not override the new C2/LLM protocols. These are guide-derived settings, not a fresh verification of live scheduler policy; inspect `showqos` and `squeue` on the cluster before submission.

Default remote root:

`/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030`

From the parent of the extracted package, in Windows PowerShell or Git Bash:

```bash
ssh sychan552@burgundy.hpc.cityu.edu.hk "mkdir -p /home/sychan552/scratch/MLFLU"
scp -r MIFlu_Continuation_20261030 sychan552@burgundy.hpc.cityu.edu.hk:/home/sychan552/scratch/MLFLU/
```

Use a fresh destination if an existing copy has already produced results. Scripts refuse conflicting/nonempty result overwrites. A different installation root can be supplied using the `MIFLU_PROJECT_ROOT` environment variable and `sbatch --export=ALL,MIFLU_PROJECT_ROOT=/absolute/new/root`. Slurm copies scripts into its spool, so jobs deliberately do **not** derive the project root from the copied script's directory.

The local Windows passwordless key described by the guide is not inherited by this cloud environment. Both FQDN and backup-IP connections failed here; see `results/HPC_CONNECTIVITY_CHECK.json`. No private keys are included or requested.

## C2 scheduler job — all 12 cells

Prepared script: `hpc/submit_c2.sh`. One GPU allocation sequentially runs L=24/36/48/60 × seeds 42/43/44, using 20 epochs, batch16, Adam, MSE, lr0.0005, LoRA r4, six GPT-2 layers and validation-only checkpoint selection. The model source is the newly supplied R1B subclass; its text prefix/readout is a declared algorithm change to the author release. The source and original author class are copied byte-for-byte.

C2 matches the original end-of-epoch update at the start of the next epoch: epoch4 still uses 0.0005; epoch5 uses 0.00045. Packaged R1C had started decay one epoch earlier. The previous candidate is retained as `code/candidate_c2_original.py`; the active trainer adds import-path/unused-import compatibility and provenance guards without changing its model/training equations beyond the requested scheduler alignment.

Submit after staging:

```bash
ssh sychan552@burgundy.hpc.cityu.edu.hk "sbatch --chdir=/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030 /home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030/hpc/submit_c2.sh"
```

The default Python is `/home/sychan552/.conda/envs/mlflu_hpc/bin/python`, as in the supplied guide. GPT-2 uses the cache from the original R1C job record: `HF_HOME=/home/sychan552/.cache/huggingface`, offline mode. This differs from the guide's old ChatTime cache. Override `C2_PYTHON` / `C2_HF_HOME` only when deliberately matching another verified environment. Preflight checks the allocated A100, dataset/scaler and cached GPT-2 configuration; missing weights cause an explicit failure at model load, not a silent download or random-weight substitution. Import-only shims cover the unused missing `embed.py` symbols and a removed PEFT int8 helper; calling a shim fails. They were exercised by the local corrected-model shape check.

The job requests one A100, four CPU cores, 16 GiB host memory and two hours. The archived 12-cell Track C run used approximately 1.51 A100 hours, making two hours reasonable headroom; the new runtime remains unmeasured. No job arrays, multiple-GPU requests or queue bypasses are used.

Outputs go to `runs/c2_<SLURM_JOB_ID>/`. On exit, including a partial failure, `aggregate_c2.py` independently scores saved predictions and writes:

- `paper_tables/C2_STATUS.json`
- `paper_tables/C2_RESULTS_PER_CELL.csv` when any cell is complete
- `paper_tables/C2_PER_HORIZON.csv` when any cell is complete
- `paper_tables/C2_TEST_MSE_RANKING_COMPARISON.csv` **only after all 12 cells complete**

The comparison contains each archived Track C counterpart, absolute MSE delta and relative delta. It is not automatically a one-factor causal experiment: the recovered source/runtime fingerprint must also match the archived implementation. Test is read once after each checkpoint is frozen. The current package has only `paper_tables/c2_pending/C2_STATUS.json`; there is no C2 MSE yet.

## LLM jobs — pinned encoding and generation arms

Source registry: `protocol/llm_registry.json`. Each model has four L values and two modes; each job computes features once and fits the same downstream random forest for three seeds. Total planned scope is **16 feature jobs / 48 downstream cells**. The numerical windows, train-only scaler, 16 train-fitted PCA dimensions and downstream RF configuration are shared across the two arms. The generation arm adds a deterministic, bounded 96-token structured analysis of observed inputs; it is an operational generation feature, not proof of hidden reasoning. No future data or calendar labels enter the prompt.

| Alias | Exact model and immutable revision | Planning VRAM, BF16/batch1 | API configuration |
| --- | --- | --- | --- |
| qwen | Qwen/Qwen2.5-1.5B-Instruct @ `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` | 6–10 GiB estimated; not measured | No inference API/key; local weights |
| deepseek | deepseek-ai/DeepSeek-V2-Lite-Chat @ `85864749cd611b4353ce1decdb286193298f64c7` | 34–39 GiB estimated; not measured; single 40GB A100 pilot required | No inference API/key; pinned local custom code |

The estimates assume frozen BF16 weights, eager attention, at most 2048 input tokens and batch1. Qwen has about 1.54B parameters according to its [model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct); the theoretical BF16 weight footprint is approximately 2.87 GiB before runtime overhead. DeepSeek-V2-Lite has about 15.7B total parameters, even though only about 2.4B are active per token. Its [official model card](https://huggingface.co/deepseek-ai/DeepSeek-V2-Lite-Chat) specifies a 40GB GPU for BF16 inference. The proposed workload's VRAM ranges are engineering estimates, not measured model-card claims. No quantization is silently substituted if memory is insufficient.

Weights will stage under:

- `/gpfs1/scratch/sychan552/CHATTIME/.cache/hub/models--Qwen--Qwen2.5-1.5B-Instruct/snapshots/989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
- `/gpfs1/scratch/sychan552/CHATTIME/.cache/hub/models--deepseek-ai--DeepSeek-V2-Lite-Chat/snapshots/85864749cd611b4353ce1decdb286193298f64c7`

The downloader writes resolved paths and full staged-file hashes into `assets/qwen.json` and `assets/deepseek.json`. GPU jobs use local-only loading and offline flags. Public downloads need no inference API credential; optional Hugging Face authentication can remain in the user's existing environment. No credentials belong in these files.

One-time setup and download on an appropriate network-enabled staging node:

```bash
bash hpc/setup_llm_env.sh
bash hpc/download_llm_weights.sh qwen
bash hpc/download_llm_weights.sh deepseek
```

`setup_llm_env.sh` creates a separate Python3.10 environment at `/home/sychan552/.conda/envs/mlflu_llm_20261030` and pins Torch2.3.1 CUDA12.1, Transformers4.46.3 and other dependencies. It leaves the existing `mlflu_hpc` environment unchanged. The GPU environment is proposed and not installed/validated here. Local API checks passed with Torch2.15.0, Transformers4.46.3 and PEFT0.13.2. The exact local versions are recorded in `results/prepared_model_smoke_tests.json`. Pinning Transformers below4.50 also avoids a known custom-generation API change in this DeepSeek source. Full GPU pilot checks remain required.

Single-arm pilot, after staging/setup:

```bash
sbatch --export=ALL,LLM_PILOT_WINDOWS=3 hpc/submit_qwen.sh 24 encoding_only
sbatch --export=ALL,LLM_PILOT_WINDOWS=3 hpc/submit_deepseek.sh 24 generation_augmented
```

Submit these **one at a time**, respecting the guide's single-job `stingy` limit. Inspect `PILOT.json` for measured memory and estimate full runtime before selecting a wall-time override; do not inflate resources to bypass scheduling limits. Pilot features are cached and reused by the full run with the same configuration. Never leave `LLM_PILOT_WINDOWS` set during a full sweep.

Individual full jobs:

```bash
sbatch hpc/submit_qwen.sh 24 encoding_only
sbatch hpc/submit_qwen.sh 24 generation_augmented
sbatch hpc/submit_deepseek.sh 24 encoding_only
sbatch hpc/submit_deepseek.sh 24 generation_augmented
```

Repeat L=36/48/60, or use the serial submission controller:

```bash
bash hpc/submit_llm_sweep.sh qwen
bash hpc/submit_llm_sweep.sh deepseek
```

The controller runs only Slurm submission/monitoring commands on the login node, waits for the current `stingy` allocation to clear, stops on an incomplete arm, and records job IDs/accounting. It does not create an array or submit 16 pending jobs. Qwen jobs request one hour / one A100 / 16GiB host RAM; DeepSeek jobs request two hours / one A100 / 32GiB host RAM. Times are initial planning budgets, not measured completion guarantees. Each arm's SQLite feature cache permits explicit resubmission after a timeout without regenerating completed windows. Failed/incomplete runs are not ranked.

LLM results live in `runs/llm/<alias>/L<L>/<mode>/`: prediction NPZs, cell metric JSONs, shared feature cost, tokenized-prompt hashes, cached generated analyses, runtime/version evidence, peak records and completion markers. Feature GPU compute cost is shared across seeds and counted once; Slurm allocation cost is separately available from `logs/llm_resource_ledger.psv`. Additional no-text/sham-text/token-budget controls are required before attributing a future gain to text semantics or reasoning.

Collect tables in the familiar Track-C-shaped column convention:

```bash
python code/aggregate_llm.py --runs runs/llm --out paper_tables/llm_measured
```

Outputs include `LLM_TEST_MSE_RANKING.csv` (`mean_Test_MSE_4L`, SD, MAE, seeds), `LLM_PER_HORIZON.csv`, `LLM_PTE_PIE_PER_MODEL_L.csv`, `LLM_RESULTS_PER_CELL.csv`, and `LLM_SHARED_FEATURE_COST.csv`. LLM results remain in their own explicitly labelled exploratory protocol group. The current `paper_tables/llm_pending/LLM_EXPECTED_RUN_MATRIX.csv` contains 48 **NOT_RUN** rows with unavailable scores.

## Table interpretation

`paper_tables/EXPANDED_COMBINED_TEST_MSE_RANKING.csv` contains all eight original Track C instances and the 11 prior CPU instances. NLinear appears twice because the archived and CPU configurations are separate experimental runs; they are not collapsed or counted as two distinct model families. Combined `rank_MSE` is only descriptive ordering. `rank_MSE_within_cohort`, `cohort`, `model_instance_id` and fidelity labels preserve the valid scope. Do not cite it as a new frozen championship or infer general LLM superiority.

`EXPANDED_COMBINED_PER_HORIZON.csv` contains 76 model/L rows with multivariate and valid target-only physical metrics. `EXPANDED_COMBINED_PTE_PIE_PER_MODEL_L.csv` contains 76 literature-criterion rows for **actual k=1**. The all-criteria file also includes the project custom thresholds. Mean PASS fields are diagnostic, not substitutes for event-level hit rates. Misses stay in the hit-rate denominator; mean timing/intensity errors exclude unmatched peaks. Rounded original PIE values are labelled.

`EXPANDED_COST_ACCURACY_PARETO.csv` identifies KNN and the new NLinear as nondominated within the measured CPU-cost group. Historical A100 MIFlu cost is separate; the other seven original model costs are NA. No frontier connects different devices/cost definitions. PeakBlend is excluded from the requested 132-cell table integration and remains in the prior bundle as a separately reported hybrid feasibility test.

## Checks and result preservation

```bash
python code/validate_continuation.py --root .
```

The local runtime test needs Torch/Transformers/PEFT/einops and uses only randomly initialized tiny models:

```bash
python code/test_prepared_experiments.py --root . --out results/prepared_model_smoke_tests.json
```

It checks the corrected R1B shape, six layers, LoRA trainable count, C2 timing, Qwen APIs and the exact pinned DeepSeek custom MoE encoding/cached-generation APIs. It is not a reproduction score, pretrained-model test or a resolution of the mechanism contradiction. Shell syntax, target conversion, table dimensions, source hashes and peak consensus totals are checked separately.

After every completed GPU job, pull the output, checkpoints, logs and tables to the local project before scratch retention can remove them:

```bash
bash hpc/pull_results.sh ./HPC_results_20261030
```

The bundle has no new GPU MSE, no measured full-LLM memory/latency, and no reproduction-success claim. Those remain empirical outcomes to collect after submission in the user's working HPC environment.
