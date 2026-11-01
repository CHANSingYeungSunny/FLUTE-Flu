"""Generate a concise, factual task handover from measured output tables."""
import argparse,json
from pathlib import Path
import pandas as pd
from common import table

def main(a):
    root=Path(a.root)
    criteria=json.loads((root/'04_benchmark/peak_criteria.json').read_text())
    lit=criteria['CONSENSUS']['criteria_versions']['LITERATURE_PTE1_PIE25']['models']
    custom=criteria['CONSENSUS']['criteria_versions']['PROJECT_CUSTOM_PTE2_PIE20']['models']
    peaks=[]
    for m in lit:
        s=lit[m]['overall'];c=custom[m]['overall']
        peaks.append(dict(model=m,literature_hits=f"{s['n_hit']}/{s['n_true_peaks']}",literature_hit_pct=s['hit_rate_pct'],
            custom_hits=f"{c['n_hit']}/{c['n_true_peaks']}",custom_hit_pct=c['hit_rate_pct']))
    il=pd.read_csv(root/'paper_tables/TRACK_C_ILITOTAL_MSE_MAE.csv')
    ilshow=il[['model','mean_Test_MSE_4L','MSE_z_ILITOTAL','MSE_physical_ILITOTAL']]
    perL=[]
    for L,v in lit['miflu']['per_L'].items():
        perL.append(dict(model='miflu',L=int(L),actual_lead_k=1,n_hit=v['n_hit'],n_true=v['n_true_peaks'],
            hit_rate_pct=v['hit_rate_pct'],mean_PTE_wk=v['mean_PTE_wk'],mean_PIE_pct=v['mean_PIE_pct']))
    rank=pd.read_csv(root/'paper_tables/EXPANDED_COMBINED_TEST_MSE_RANKING.csv')
    top=rank[['rank_MSE','model_instance_id','mean_Test_MSE_4L','mean_Test_MAE_4L']].head(8)
    models=json.loads((root/'protocol/llm_registry.json').read_text())['models']
    status='''# MIFlu continuation task status

Project: **CHAN Sing Yeung Sunny — Final Year Project**. Moon, Shim, Kim & Hwang authored the reference paper and upstream reference implementation, not this entire project. Correct reference title: *MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme*, IEEE JBHI 29(10):7790–7801 (2025). Dataset: **US CDC National-Illness**, not Hong Kong.

Status: **PARTIAL_REPRODUCTION**. Text mechanism: **UNRESOLVED**. No reproduction-success claim. MSE is an error metric, not accuracy. Reference anchor: `966|L24|seed42`. Official data SHA256: `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5`.

Paths below are exact paths relative to the extracted `MIFlu_Continuation_20261030/` package. The historical authoritative DOCX/MD is preserved; this is an execution/status handover, not a competing final research report.

| Task | Status | Main produced file | Blocker / boundary |
| --- | --- | --- | --- |
| 1 Peak consensus | DONE | `04_benchmark/peak_criteria.json` | New documented reconstruction schema; original JSON bytes/schema were not recovered |
| 2 Original eight-model target scores | PARTIAL | `paper_tables/TRACK_C_ILITOTAL_MSE_MAE.csv` | Seven original raw prediction sets and tarball still absent; their target scores remain NA |
| 3 C2 job preparation | DONE | `hpc/submit_c2.sh` | Prepared and locally checked; not submitted or trained on HPC |
| 4 Qwen/DeepSeek job preparation | DONE | `hpc/submit_qwen.sh`, `hpc/submit_deepseek.sh` | Full weights/environment/GPU pilots and experiment execution remain pending |
| 5 Expanded paper tables | DONE | `paper_tables/EXPANDED_COMBINED_TEST_MSE_RANKING.csv` | Combined order descriptive; protocol-specific ranks and cost groups retained |

## Task 1 — reconstructed peak_criteria.json

Produced:

- `04_benchmark/peak_criteria.json`
- `04_benchmark/PEAK_CRITERIA_CONSENSUS_SUMMARY.csv`
- `04_benchmark/PEAK_CRITERIA_PER_MODEL_L.csv`
- `code/reconstruct_peak_criteria.py`

The JSON has `CONSENSUS.models` for the selected literature criterion and `CONSENSUS.criteria_versions` for both literature and project-custom versions. It includes per-model, per-L and per-seed counts, hit rates, matched PTE/PIE means, missed/false peaks, source hashes, units, actual forecast lead k=1 and L window lengths. Literature hits were checked against both the pass matrix and by-model summary; per-L totals were checked against per-cell records.

The literature composite is **PTE≤1 week AND PIE≤25%**, applied per true peak. The custom project version is **PTE≤2 weeks AND PIE≤20%**. The latter is not labelled a literature or MIFlu-paper standard. Means are not used to decide individual hits; misses remain in the denominator.

{PEAKS}

MIFlu's per-L literature results, **all at k=1**:

{MIFLU_L}

Pooled matched-event MIFlu means are PTE **0.3000 weeks** and PIE **25.17%**. The original summary's mean-of-cell values **0.29 weeks / 25.00%** are retained separately. The aggregation methods weight cells differently; this is not a change to the authoritative 15/36 count. The provided PIE values are rounded to two decimals; no event lies close enough to the 20% or 25% boundary to make the reclassified custom count ambiguous.

## Task 2 — ILITOTAL-only original Track C errors

Produced:

- `paper_tables/TRACK_C_ILITOTAL_MSE_MAE.csv`
- `paper_tables/TRACK_C_ILITOTAL_PER_L.csv`
- `paper_tables/TRACK_C_ILITOTAL_PER_CELL.csv`
- `results/raw_prediction_inventory.csv`
- `code/score_ilitotal.py`

All 12 original MIFlu cells were rescored from raw CSVs with strict keys and targets verified. The two attachments contain **no original seven-model prediction tarball or 84 original non-MIFlu raw arrays**. Their newer CPU files belong to different experimental instances and were not substituted.

{ILI}

MIFlu's target-only MSE is **3.7020 z²**, or **300071219.8818 patient-count²**, using the packaged ILITOTAL scale **9003.15234375**. Its seven-variable aggregate remains **1.8652**; these are different target scopes. Physical MAE and all four per-L values are also supplied. No scalar conversion is applied to the seven-variable aggregate. NA means raw evidence unavailable, not zero.

Needed to finish Task 2: the actual `test_eval_download.tar.gz` or original `pred_<model>_L<L>_s<seed>.npz` files. The scoring command accepts `--raw-root` and validates dataset/target compatibility before using them. Files found only on inaccessible HPC cannot be claimed available locally.

## Task 3 — complete C2 scheduler launch package

Produced:

- `hpc/submit_c2.sh`
- `code/candidate_c2_train.py`
- `code/candidate_c2_original.py` — unchanged previous candidate, for provenance
- `code/aggregate_c2.py`
- `code/hpc_preflight.py`
- `code/hpc_compat/embed.py`
- `paper_tables/C2_PLANNED_CELL_COMPARISON.csv`
- `paper_tables/C2_SCHEDULER_TIMELINE.csv`
- `paper_tables/c2_pending/C2_STATUS.json`

The job uses one A100 allocation on `stingy`, 4 CPU cores, 16GiB host RAM, a 2h wall budget and a serial four-L × three-seed sweep. This respects the supplied guide's one-job limit and avoids a 12-task array. It loads the supplied `05b_r1b_model/r1b_model.py` and unchanged author class. The prefix/readout and freeze repairs remain declared method changes.

The aligned schedule keeps epoch4 at **0.0005** and applies **0.00045** at epoch5. The earlier C1 candidate applies 0.00045 at epoch4. Training is 20 epochs, batch16, Adam/MSE, six GPT-2 layers, LoRA r4, and validation-only checkpoint selection. Dataset, text asset, trainer, source, environment and actual cell keys are recorded. Text matrices cannot silently fall back to None.

After staging the package at the documented default remote root:

```bash
ssh sychan552@burgundy.hpc.cityu.edu.hk "sbatch --chdir=/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030 /home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030/hpc/submit_c2.sh"
```

Results and comparison files will appear under `runs/c2_<JOBID>/paper_tables/`. The scorer compares each new cell with its same-L/same-seed archived Track C counterpart. A grand four-L mean is emitted only after all 12 cells complete; partial output cannot masquerade as a full mean. Software/runtime differences must still be considered when interpreting deltas.

**New C2 MSE, improvement and GPU cost: unavailable — no full training executed.** Local corrected-model checks passed for output shape, six-layer truncation and **1,673,496 trainable parameters at L24**, using random initialization rather than pretrained weights. These checks do not resolve the text-mechanism contradiction.

## Task 4 — Qwen and DeepSeek encoding/generation arms

Produced:

- `hpc/submit_qwen.sh`
- `hpc/submit_deepseek.sh`
- `hpc/run_llm_job.sh`
- `hpc/submit_llm_sweep.sh`
- `hpc/setup_llm_env.sh`
- `hpc/download_llm_weights.sh`
- `code/run_llm_features.py` — resumable adaptation of the prior runner
- `code/prior_run_llm_features.py` — previous runner retained as prompt/source provenance
- `code/download_model_weights.py`
- `code/aggregate_llm.py`
- `protocol/llm_registry.json`
- `protocol/model_source/` — pinned configuration/custom source and notices
- `paper_tables/llm_pending/LLM_EXPECTED_RUN_MATRIX.csv`

{MODEL_SPEC}

The registry pins immutable model commits. Staging downloads create `assets/<alias>.json` with snapshot paths and full file hashes. GPU jobs use local-only BF16 loading. DeepSeek's custom model/config code is pinned and its configuration/source hashes verified. No external inference API or API key is needed for either model. Optional Hugging Face download authentication remains outside source files.

Expected weight paths are under `/gpfs1/scratch/sychan552/CHATTIME/.cache/hub/models--<org>--<model>/snapshots/<revision>`. The README gives exact paths and setup/download/submit commands. Memory estimates assume batch1, frozen BF16 weights, eager attention and at most2048 input tokens; they are **not measured allocations**. The DeepSeek official model card specifies a single40GB GPU for BF16 inference. Full GPU pilots are required before interpreting runtime/memory claims.

Each model has encoding-only and deterministic generation-augmented arms at all four L values. Each arm uses 16 train-fitted PCA feature dimensions plus numerical lags and the same RF forecaster. Generation is capped at96 tokens of structured analysis of observed history. This is not a claim about hidden reasoning or known improvement. Features are cached, seed-shared and resumable; input/prompt hashes and generated text are retained. There are **16 planned feature jobs / 48 downstream seed cells**, currently all NOT_RUN.

Tiny random Qwen and pinned DeepSeek MoE models passed local encoding/cached-generation API checks under Transformers4.46.3. Full checkpoints, the proposed cluster environment, GPU performance and forecast quality remain untested. The serial submission controller observes `stingy` capacity and does no model compute on login nodes. Output aggregators emit familiar MSE ranking, per-L, target-unit, peak and cost tables only for actually measured cells.

## Task 5 — integrated paper tables

Produced:

- `paper_tables/EXPANDED_COMBINED_TEST_MSE_RANKING.csv`
- `paper_tables/EXPANDED_COMBINED_TEST_MAE_RANKING.csv`
- `paper_tables/EXPANDED_COMBINED_PER_HORIZON.csv`
- `paper_tables/EXPANDED_COMBINED_MSE_PROFILES.csv`
- `paper_tables/EXPANDED_COMBINED_NORMALIZED_PROFILES.csv`
- `paper_tables/EXPANDED_COMBINED_PTE_PIE_PER_MODEL_L.csv`
- `paper_tables/EXPANDED_COMBINED_PTE_PIE_ALL_CRITERIA.csv`
- `paper_tables/EXPANDED_COST_ACCURACY_PARETO.csv`
- `paper_tables/INTEGRATION_MANIFEST.json`
- `code/integrate_paper_tables.py`

The combined display contains **19 experimental instances**: eight original Track C instances plus11 previous CPU instances. There are **76 per-L rows** and **76 literature peak model/L rows**. Both NLinear runs are retained with distinct instance identifiers, not averaged. The original Track C CSVs remain separate and unchanged. The previous12-cell PeakBlend hybrid is outside the requested132-cell integration.

Top combined entries, **descriptive ordering only**:

{TOP}

Ranks within protocol groups, fidelity labels and data hash are retained. No A/B scores enter this table. The old and new strict-966 groups share evaluation data but have different training histories/configurations; combined ordering is not confirmatory cross-protocol evidence or a replacement champion declaration.

The cost frontier uses only the **same measured CPU cost group**. KNN and the new CPU NLinear are nondominated in fit/validation CPU wall time versus MSE. Archived A100 MIFlu cost is reported separately; the other seven original training costs remain NA. No line is drawn across CPU/A100 or incompatible timing scopes. Parameters/FLOPs are never fabricated.

## Verification and remaining execution boundary

`results/CONTINUATION_VERIFICATION.json` records passing consensus, per-L totals, target conversion, no-imputation rules, 19/76 table dimensions, pinned source hashes, Python parsing and Bash syntax checks. `results/prepared_model_smoke_tests.json` records the actual tiny-model API checks and local versions. `results/INPUT_ARCHIVE_PROVENANCE.json` links the two supplied archives by hash.

The newly supplied model and HPC guide resolve their previous **file-availability** blockers. They do not create remote network access: the FQDN fails DNS here and the documented backup IP fails with network unreachable. **Zero HPC jobs were submitted; no new C2 or LLM forecast score is claimed.** Run the prepared jobs from the user's environment where passwordless SSH already works, then pull results/checkpoints/tables/logs with `hpc/pull_results.sh`.
'''
    specs=[]
    for alias,m in models.items():specs.append(dict(alias=alias,repo_id=m['repo_id'],revision=m['revision'],
        expected_VRAM_GiB=f"{m['expected_gpu_memory_GiB'][0]}–{m['expected_gpu_memory_GiB'][1]} (estimate)",API='none; local weights'))
    replacements={'{PEAKS}':table(pd.DataFrame(peaks),{'literature_hit_pct':'.2f','custom_hit_pct':'.2f'}),
        '{MIFLU_L}':table(pd.DataFrame(perL),{'hit_rate_pct':'.2f','mean_PIE_pct':'.2f'}),
        '{ILI}':table(ilshow),'{TOP}':table(top),'{MODEL_SPEC}':table(pd.DataFrame(specs))}
    for old,new in replacements.items():status=status.replace(old,new)
    (root/'TASK_STATUS.md').write_text(status)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);main(p.parse_args())
