# HPC Round 3 — Results & Live Job Status

> Executed 2026-10-30 by connecting directly to `burgundy.hpc.cityu.edu.hk`
> (ChatGPT could not reach the cluster; these results were produced locally on HPC).

## Major finding — ILITOTAL-only ranking REVERSES the 7-variable ranking

This is the most important result of this round. When the clinically meaningful
**ILITOTAL** target is scored alone (instead of the 7-variable aggregate), the model
ranking changes dramatically:

| Rank | Model | MSE_z (ILITOTAL-only) | MSE_physical (patient-count²) | 7-var aggregate rank |
|---|---|---:|---:|---|
| 1 | **NLinear** | **1.2952** | 104,983,983 | 2 |
| 2 | DLinear | 1.5043 | 121,935,084 | 3 |
| 3 | TimeCMA-LLM | 2.3180 | 187,892,024 | 4 |
| 4 | **MIFlu** | 3.7020 | 300,071,212 | **1** |
| 5 | PatchTST | 3.5466 | 287,478,248 | 5 |
| 6 | iTransformer | 3.6949 | 299,498,248 | 6 |
| 7 | Qwen-Time-LLM | 4.2402 | 343,699,610 | 7 |
| 8 | CALF-LLM | 5.2650 | 426,766,157 | 8 |

**Interpretation**: MIFlu is best on the 7-variable *aggregate* (1.8652) but only
**4th** on ILITOTAL alone (3.7020). NLinear — a trivially cheap linear model — is
**2.9× better** than MIFlu at forecasting the actual ILI patient count.

This is a **publication-relevant** finding: the paper's headline claim rests on the
aggregate metric, which is dominated by 6 non-clinical variables. On the variable that
matters for public health (ILITOTAL), a one-line linear baseline wins.

### Verification (both sources cross-checked against authoritative Track C)

| Source | Used for | All-7 cross-check |
|--------|----------|-------------------|
| `miflu_strict966__*` CSVs | MIFlu | 1.8652 ✓ MATCH |
| `stage6/pred_<model>_L<L>_s<seed>.npz` | 7 baselines | all 7 ✓ MATCH |

- MIFlu ILITOTAL independently reproduced: **3.7020 z²** / **300,071,219.88 patient-count²**
  (matches ChatGPT's figure exactly).
- Stage6 MIFlu is a **different instance** (all-7 = 2.0415 ≠ 1.8652) → correctly excluded.
- Stage6 baselines all-7 == Track C exactly → correctly included.

## Live HPC jobs

| JOBID | Partition | Job | State | Scheduled |
|---|---|---|---|---|
| **711388** | `stingy` | `miflu_c2` — C2 corrected-scheduler 12-cell sweep | PENDING (Priority) | **2026-10-31 00:03:50** on `gpu-a100-05`, ends 02:03:50 |
| **711416** | `tiny` | `miflu_llm_dl` — Qwen/DeepSeek weight staging | PENDING (Priority) | TBD |

### C2 experiment (711388)
- 12 cells: L ∈ {24,36,48,60} × seed ∈ {42,43,44}
- Corrected **end-of-epoch** scheduler alignment (the one-epoch discrepancy ChatGPT found)
- Expected: if Track R evidence holds, ~1.8% MSE reduction (1.8652 → ~1.83)
- Results auto-aggregate via `aggregate_c2.py` on job exit

### LLM download (711416)
- Reuses existing `mlflu_hpc` env — **no new env needed** (torch 2.5.1 + transformers 4.57.6 already present)
- Registry created at `protocol/llm_registry.json` (Qwen2.5-1.5B-Instruct, DeepSeek-V2-Lite-Chat)
- After download completes, the LLM arms (48 cells) can be submitted

## Environment notes (discovered this round)

- `conda` is a **module** (`Conda/1.10.0`), NOT on PATH by default → `conda create` fails in plain scripts.
- **`mlflu_hpc` already has all LLM deps** (torch 2.5.1, transformers 4.57.6, accelerate, safetensors,
  sentencepiece, tokenizers) → do NOT build a separate `mlflu_llm_20261030` env.
- `batch` partition rejects small jobs (8 CPU/32 GB too small) → use `tiny` for CPU staging work.

## Data recovered from HPC (previously "missing")

| Asset | HPC path | Status |
|-------|----------|--------|
| Complete 8-model predictions | `/home/sychan552/stage5_a2_durable/stage6/predictions/` (116 npz) | ✅ 7 baselines verified == Track C |
| MIFlu strict966 CSVs | `/home/sychan552/miflu_test_csv.tgz` (12 cells) | ✅ verified 1.8652 |
| `r1b_model.py` | in continuation package | ✅ |
| `test_eval_download.tar.gz` | `/gpfs1/scratch/sychan552/_test_phase/` | ⚠ MIFlu + seasonal_naive only |

## Status

**PARTIAL_REPRODUCTION** — unchanged. Text-pathway contradiction **UNRESOLVED**.
No reproduction-success claim. Awaiting C2 and LLM results.
