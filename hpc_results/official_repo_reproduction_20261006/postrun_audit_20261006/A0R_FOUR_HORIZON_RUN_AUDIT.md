# A0-R — FOUR-HORIZON RELEASED-ENTRY-POINT RUN AUDIT

Generated 2026-10-06. Append-only; this file records state as measured and modifies nothing.

**Scope.** Four single-repetition training runs of the author's released entry point
`main_ILI_lora.py` (author commit `6ed2101`), one per horizon L = 24 / 36 / 48 / 60:
Slurm jobs **606365_0, 606378_1, 606385_2, 606412_3**. The runner recorded them under the
label `A1_reconstructed_paper_config`; the post-run lineage audit re-classifies the family
as **A0-R (released-code replay / reconstructed execution)**. They are **not** the
paper-faithful `A1-P` set and **not** a reproduction of Table V (see
`A0R_LIMITATIONS.md`). Both labels are carried below so nothing is ambiguous.

**Evidence read.** Each run's `provenance.txt`; the released per-epoch summary CSV each
run wrote (`./results/<setting>.csv`, archived as `a1_reconstructed_L*_..._itr0.csv`);
`a1_results_per_epoch.csv`, `a1_results_per_run.csv`, `a1_results_aggregate.csv`,
`a1_gpu_ledger.csv`; `slurm/miflu_a1_array.sbatch`; `recovery/author_repo/main_ILI_lora.py`;
`recovery/author_repo/utils/tools.py` (`test`, `vali`, `adjust_learning_rate`);
`recovery/author_repo/utils/metrics.py`; `recovery/author_repo/models/GPT4TS_lora.py`;
`recovery/author_repo/data_provider/data_loader.py` + `data_factory.py`;
`recovery/a1/a1_evidence_table_zh.md`; `HYPERPARAMETER_PROVENANCE.md`; `DEVIATION_LEDGER.md`;
`REPOSITORY_PROVENANCE.md`; the HPC `hpc_probe/*.json` parameter snapshots; live git on
`recovery/author_repo` and the project repo.

---

## 0. Field-by-field record

All four horizons share the same run recipe. Where a value is identical the cell repeats it
rather than pointing elsewhere. `UNRECOVERED` means no artifact records it.

| # | Field | L=24 (606365_0) | L=36 (606378_1) | L=48 (606385_2) | L=60 (606412_3) |
|---|---|---|---|---|---|
| 1 | Slurm job ID | `606365_0` | `606378_1` | `606385_2` | `606412_3` |
| 2 | Horizon (`--pred_len` / output length) | 24 | 36 | 48 | 60 |
| 3 | Author git remote (code that ran) | `https://github.com/Jmoon3108/MIFlu.git` | same | same | same |
| 4 | Author git commit | `6ed210150b8819313947cf607eb1821c87b1bee3` (2025-03-21, "Initial commit") | same | same | same |
| 5 | Author git diff state | Source tree unmodified. `git diff` on tracked files = **0 insertions, 0 deletions**; only `models/__pycache__/GPT4TS_lora.cpython-39.pyc` (a regenerated binary) differs. `provenance.txt` records `author_source_modified=1 non-pyc entries` = the run's own untracked `results/` output dir (`?? results/`), not source. | same | same | same |
| 6 | Project (FLUTE-Flu) repo remote / commit | `https://github.com/CHANSingYeungSunny/FLUTE-Flu.git` @ `1f6563f7ea52620354a4fa0666b813b6a9f9cc51` (branch `recovery-stage4`) | same | same | same |
| 7 | Dataset path | `/scratch/sychan552/a0_replay/dataset/illness/national_illness.csv` (via `--root_path './dataset/illness/'` + `--data_path 'national_illness.csv'`; CWD=`a1_work`, `dataset` symlinked read-only to the author checkout). Local mirror: `recovery/author_repo/dataset/illness/national_illness.csv` | same | same | same |
| 8 | Dataset SHA-256 | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` | same | same | same |
| 9 | Row count | 966 data rows (967 lines incl. header) | same | same | same |
| 10 | Variable count | **7** numeric columns (`1,2,3,4,5,6,OT`); `date` is the timestamp column. Dataset resolves `enc_in = data_x.shape[-1] = 7`; the CLI `--enc_in 862` is unused by `GPT4TS` | same | same | same |
| 11 | Split boundaries (computed from the loader's integer rule) | `num_train=int(966*0.7)=676`, `num_test=int(966*0.2)=193`, `num_vali=966-676-193=97`. `border1s=[0,676-104,966-193-104]=[0,572,669]`; `border2s=[676,676+97,966]=[676,773,966]`. Train=[0,676), Val=[572,773), Test=[669,966). `percent=100` → train `border2` rescale is a no-op | same | same | same |
| 12 | Seed | 2021 (`fix_seed`; `random.seed`/`torch.manual_seed`/`np.random.seed` once at import; not re-seeded per run or per `itr`) | 2021 | 2021 | 2021 |
| 13 | Epochs | 20 — `RECONSTRUCTED` (paper discloses no value; author default `--train_epochs 1`) | 20 | 20 | 20 |
| 14 | Initial learning rate | 5e-4 — `RECONSTRUCTED` (paper discloses no value; author default `1e-4`) | 5e-4 | 5e-4 | 5e-4 |
| 15 | Learning-rate schedule | `adjust_learning_rate(optim, epoch+1, args)` called every epoch (`--cos 0` branch). `--lradj type1` → `lr = 5e-4` for e<3, else `5e-4 * 0.9**(e-3)` (e=1..20). The `CosineAnnealingLR(T_max=10, eta_min=1e-8)` object is constructed at L172 but **never stepped** (`cos=0`) | same | same | same |
| 16 | Decay factor (effective) | **0.9**, hard-coded in the `type1` branch (`utils/tools.py` L27). Final-epoch lr = 5e-4·0.9¹⁷ ≈ **8.34e-5**; measured on HPC: `Updating learning rate to 0.00019371024450000004` = 5e-4·0.9⁹ at e=12 (job 606378). **`--decay_fac 0.75` is passed but INERT under `type1`** (it is read only by the `type2`/`type4` branches). The project's own `lr_schedule` strings ("decay_fac=0.75") are therefore wrong; see §2 | same | same | same |
| 17 | Optimizer | `torch.optim.Adam(params, lr=5e-4)` — betas (0.9, 0.999), eps 1e-8, **weight_decay 0** (never set) | same | same | same |
| 18 | Batch size | 16 (`DataLoader` batch size for train/val/test) | 16 | 16 | 16 |
| 19 | Input length (`--seq_len`) | 104 | 104 | 104 | 104 |
| 20 | Output length (`--pred_len`) | 24 | 36 | 48 | 60 |
| 21 | Label length (`--label_len`) | 18 | 18 | 18 | 18 |
| 22 | Patch length (`--patch_size`) | 24 | 24 | 24 | 24 |
| 23 | Stride (`--stride`) | 2 | 2 | 2 | 2 |
| 24 | Patch count (`patch_num`) | 42 = `(104-24)//2+1` then `+1` for the `ReplicationPad1d((0,stride))` | 42 | 42 | 42 |
| 25 | GPT-2 layer count (`--gpt_layers`) | 6 (`llmmodel.h = llmmodel.h[:6]`) | 6 | 6 | 6 |
| 26 | PEFT setting | **1** (LoRA branch executes) | 1 | 1 | 1 |
| 27 | LoRA rank | r=4 (`lora_alpha=4`, `lora_dropout=0.05`, `bias="none"`, `task_type="FEATURE_EXTRACTION"`) | 4 | 4 | 4 |
| 28 | Effective `target_modules` | `["c_attn"]` — the author's **list** default, because `--target_modules` is deliberately NOT passed on the CLI (see §1) | same | same | same |
| 29 | Total parameter count | **82,705,944** (measured: `hpc_probe/text_path_probe_cpu.json` and `..._gpu.json`, `parameters.total`; = 6-layer GPT-2 81,912,576 + `in_layer` 19,200 + `out_layer` 774,168) | **83,093,028** (computed same decomposition; `out_layer` 1,161,252) | **83,480,112** (`out_layer` 1,548,336) | **83,867,196** (measured: `text_path_probe_cpu_local_L60.json` `parameters.total`; `out_layer` 1,935,420) |
| 30 | Trainable parameter count | Measured for the **released-default** config (PEFT=0): **82,705,944 / 82,705,944 = 100%** (`a1_evidence_table_zh.md` §3; `hpc_probe/*.json`). For **these four A0-R runs** (PEFT=1), no artifact records the count → **UNRECOVERED** (see §2 note A) | UNRECOVERED | UNRECOVERED | UNRECOVERED |
| 31 | Evaluated feature IDs | **`{0}` only** — the `Dataset_Custom.__len__` test branch omits `×enc_in` (L312-316), so `index < tot_len` ⇒ `feat_id = index//tot_len = 0` for every test sample; feature 0 = first numeric column `"1"` (weighted ILI) | `{0}` | `{0}` | `{0}` |
| 32 | Test sample count | Dataset `__len__` = `297-104-24+1 = 170` windows; `DataLoader(drop_last=True)` → `⌊170/16⌋ = 10` batches → **160 origins scored** (10 discarded) | 158 windows → 9 batches → **144 scored** (14 discarded) | 146 → 9 → **144 scored** (2 discarded) | 134 → 8 → **128 scored** (6 discarded) |
| 33 | Checkpoint-selection rule | Minimum over epochs of the **per-epoch Test MSE**: `mse_temp,mae_temp = test(...)` each epoch (L211); `if mse_temp < min_mse: best_epoch_result = {..., 'model_state': model.state_dict()}` (L225-227); strict improvement only; `torch.save(state)` to `checkpoints/<setting>/checkpoint.pth` (L263-264) | same | same | same |
| 34 | Did Test data affect selection? | **YES** — the Test set is scored every epoch and its MSE chooses the saved checkpoint (leakage) | YES | YES | YES |
| 35 | Final checkpoint | Weights after the last training update (epoch index 19). Used for the post-loop `test()` (L245) | same | same | same |
| 36 | Selected checkpoint | `best_epoch_result['model_state']` — epoch with the lowest epoch-level Test MSE; loaded at L260, saved to `checkpoints/<setting>/checkpoint.pth` | same | same | same |
| 37 | Predictions path | **None.** `test()` accumulates `preds`/`trues` in memory only and returns two scalars; the `np.save(...)` calls are commented out (L299-302); the only writer (`test_vis`) is called after the metrics CSV and **crashes** (see §3). No `.npy`/prediction file exists anywhere in the archive → **ABSENT** | ABSENT | ABSENT | ABSENT |
| 38 | Targets path | **None** — same reason; ground-truth arrays are never persisted → **ABSENT** | ABSENT | ABSENT | ABSENT |
| 39 | Metrics path | `./results/<setting>.csv` = `a1_reconstructed_L{L}_itr1_multimodal1_gpt2_gpt2_sl104_ll18_pl{L}_dm768_nh4_el3_gl6_df768_ebtimeF_itr0.csv` (per-epoch `iteration,epoch,mse,mae`). Local copies: L24 `hpc_a1/…pl24….csv`; L36 `hpc_a1_runs/L36/…pl36….csv`; L48 `hpc_a1_runs/L48/…pl48….csv`; L60 `hpc_a1_runs/L60/…pl60….csv` | ✓ | ✓ | ✓ |
| 40 | Final-epoch MSE / MAE | 0.579273 / 0.474049 | 0.592006 / 0.443037 | 0.608798 / 0.468771 | 0.636060 / 0.525178 |
| 41 | Selected (best) MSE / MAE | 0.534386 / 0.450279 | 0.538689 / 0.419530 | 0.606936 / 0.468384 | 0.593349 / 0.509288 |
| 42 | Selected epoch | 8 | 10 | 16 | 5 |
| 43 | Script's own printed `mse_mean` (= `np.mean(mses)`, itr=1 ⇒ final-epoch value) | **0.5793** | **0.5920** | **0.6088** | **0.6361** |
| 44 | `mse_mean_over_epochs` (build-script quantity = mean of the 20 per-epoch values) | 0.604363 | 0.602817 | 0.657133 | 0.654465 |
| 45 | Independent re-scoring possible from the archived artifacts? | **NO** — no per-sample predictions/targets, no checkpoint in the local archive; only 20 scalar (MSE, MAE) pairs per run (see §3) | NO | NO | NO |
| 46 | Missing artifact(s) | `checkpoint.pth` (not in local archive), `train.log` (not in local archive), prediction/target arrays (never produced), `test_vis` CSV/PNG (crash) | same | same | same |
| 47 | Wall seconds (recorded) | 1054 | 1014 | 977 | 942 |
| 48 | Slurm elapsed (sacct) | 00:17:34 | 00:16:54 | 00:16:18 | 00:15:42 |
| 49 | Author exit code | **1** (non-zero — see §3) | 1 | 1 | 1 |
| 50 | Text-embedding asset SHA-256 (`text_emb_label_0507_{L}.txt`) | `837502311354c9ddf71e42fbdf5689b6bbbbd2f00c71055d0d226c3c1f44c0c8` | `f70d1a141928f1fd65ba78bad30a9a167fa9315a4c22effc291aac2bd593b464` | `25bf529f66842df18b09b7dd3f0418347c098d07222e0017fc75e80f3205edd5` | `fe98826fef910fd3e0316b67b823274b7991084db67524125ac0c4eda29f4ac0` |

All four text-embedding hashes were re-verified locally against
`recovery/author_repo/dataset/illness/text_emb/` — exact match.

---

## 1. The `--target_modules` argparse type trap

`main_ILI_lora.py` L47 declares:

```python
parser.add_argument('--target_modules', type=str, default=["c_attn"], help='lora target modules')
```

The default is a **list**, but `type=str` means any value supplied on the command line is
coerced to a **string**. Passing `--target_modules c_attn` therefore delivers the bare
string `"c_attn"`, which peft interprets as a *regex* and cannot resolve, so
`get_peft_model` raises `ValueError: Target modules c_attn not found in the base model`.

* This was hit for real: the first attempt (`job 606361_0`, sbatch-array index 0 with the
  override) died in **7 s** during model construction, before any training
  (`failures_and_retries.csv`; `a1_gpu_ledger.csv`).
* A zero-GPU CPU diagnostic (`slurm/diag_peft_lora.sbatch`, job 606362) tested 7 spellings:
  `["c_attn"]` (list) OK; `"c_attn"` (string) FAIL; `["attn.c_attn"]` OK; `r"^.*c_attn$"` OK.
* `miflu_a1_array.sbatch` therefore **deliberately does not pass `--target_modules`**, so the
  author's own list default `["c_attn"]` is what actually reaches `LoraConfig`.

**Effective `target_modules` for all four runs = `["c_attn"]` (a Python list).** The sbatch
carries this reasoning inline (lines 98-103) and it is recorded as DEV-10 in
`DEVIATION_LEDGER.md`. This is a *runner workaround for an author bug*, not an algorithm
change; but because the sbatch also does not pass several other flags, "the exact script
that ran" should be read together with the sacct record (see §4).

---

## 2. Trap notes

**A. Trainable parameter count.** The `freeze` loop (`GPT4TS_lora.py` L58-61, L87-90) **only
ever sets `requires_grad = True`** for names containing `ln`/`wpe`; it never sets anything to
`False`. It is therefore a no-op and cannot freeze anything. Measured on the released-default
configuration (PEFT=0) the model is **82,705,944 / 82,705,944 = 100 % trainable**
(`a1_evidence_table_zh.md` §3; `hpc_probe/*.json` `parameters.trainable`). **Caveat for these
four runs:** they set `PEFT=1`, which routes through `get_peft_model(...)`; in peft that
call freezes the base model and marks only the LoRA weights (plus the re-enabled `ln`/`wpe`
params) trainable. No A0-R artifact records the resulting count, so the A0-R trainable figure
is **UNRECOVERED**. The project's own cost narrative ("the author's freeze is a no-op so all
82.7M parameters train", `cost_summary.csv`; `REPORT_EN.md` §D) carries the released-default
measurement into the PEFT=1 runs and is **not verified for these four runs** — flagged as an
open discrepancy rather than silently reconciled.

**B. Learning-rate schedule description is wrong in the derived tables.**
`a1_results_per_run.csv`, `a1_results_aggregate.csv` and `REPORT_EN.md` label the schedule
"type1 exponential decay, **decay_fac=0.75**". The code's `type1` branch hard-codes a factor
of **0.9** and never reads `decay_fac`; the measured on-HPC step
(0.00019371024450000004 ≈ 5e-4·0.9⁹) confirms 0.9. `decay_fac=0.75` is passed but inert. The
correct effective decay factor is **0.9 per epoch after epoch 3**.

**C. Feature coverage.** 7 variables exist, but only `feat_id = 0` (column `"1"`, weighted
ILI) is ever evaluated, because `Dataset_Custom.__len__` returns the window count
*without* `×enc_in` for the test split. Train and validation *do* iterate all 7 features
(each sample is single-variate, `(B, L, 1)`); the test split does not.

**D. Split rule.** `num_train = int(966×0.7) = 676`, `num_test = int(966×0.2) = 193`,
`num_vali = 966 − 676 − 193 = 97`. With `seq_len=104` the loader's borders are
train `[0, 676)`, val `[572, 773)`, test `[669, 966)`. The test slice has 297 rows, so the
per-horizon test window counts are 170 / 158 / 146 / 134 before `drop_last`, and
160 / 144 / 144 / 128 scored after it.

---

## 3. Run completion / independent re-scoring

* **`author_exit_code = 1` on all four runs.** Training, the per-epoch scoring, the summary
  CSV write (L251), the "Best performance" print (L259) and the best-checkpoint `torch.save`
  (L264) all precede the only call that can fail at the end: `test_vis(model, test_data,
  test_loader, args, device, 1)` (L267). `test_vis`'s signature is
  `(model, test_data, test_loader, args, setting, device)`; the caller passes a
  `torch.device` as `setting` and the int `1` as `device`, so `setting + 'results.csv'`
  (L368) raises `TypeError` (unsupported operand `torch.device + str`) and the process exits
  non-zero. The defining `train.log` was **not** preserved locally, so this is stated as the
  code-consistency explanation, not as a directly-logged trace.
* **No prediction/target arrays were saved — verified.** `test()` (L290-331) keeps `preds`/
  `trues` only as locals and returns `(mse, mae)`; the only `np.save` calls are commented out
  (L299-302); `test_vis` is the only writer and (a) crashes and (b) even if it ran would
  persist only the *last lead* of feature 0 (`pred[:,-1,0]`). A repo-wide search finds no
  `.npy`/prediction/target file for any A0-R horizon.
* **Consequence: independent re-scoring is impossible** from the archived artifacts. The only
  surviving numeric outputs are 20 scalar `(MSE, MAE)` pairs per horizon, already reduced
  over batches × origins × leads × 1 feature and already in standardized space. There is no
  per-sample prediction to re-score and no checkpoint in the local archive to re-run
  inference from.
* **Checkpoint status.** `torch.save` (L264) runs before the `test_vis` crash, and the sbatch
  copies `checkpoints/*${TAG}*/checkpoint.pth` to the run dir (lines 114-117), so a
  `checkpoint.pth` should exist on HPC — but it is **absent from the local archive**. Whether
  it is still present on `/gpfs1/home/.../a1_work/checkpoints/` is not established by the
  evidence read here → recorded as **missing from the archive**.

---

## 4. Runner vs. record

`slurm/miflu_a1_array.sbatch` declares `--job-name=miflu_a1` and `--array=0-3`, and defaults
`MIFLU_ITR=3`. The sacct record shows per-horizon job names (`a1_measure`, `a1_L36`,
`a1_L48`, `a1_L60`) and single-element array indices `_0.._3`, and every `provenance.txt`
records `itr=1` — i.e. the script was submitted one horizon at a time (stingy QOS
`MaxSubmit=1`, DEV-12) with `MIFLU_ITR=1` and a per-horizon `--job-name` override. So the
sbatch file is the right *program*, but the actual sbatch invocation differed in job name,
array shape and `itr`. This matches `REMAINING_RUN_MATRIX.csv`, which lists the paper's 7
missing repetitions per horizon as still to be run.

---

## 5. What this run is / is not

* **Is:** a faithful, provenance-locked execution of the author's released entry point at
  commit `6ed2101`, with paper-disclosed settings injected (PEFT=1, r=4, multimodal=1,
  Lp=24, S=2, T=104, K=6, 70:10:20) plus reconstructed epochs/lr and minimal execution
  fixes (no `--target_modules` override).
* **Is not:** a reproduction of Table V, and not the paper-faithful `A1-P` set. Full
  reasoning and the itemised reasons are in `A0R_LIMITATIONS.md`.