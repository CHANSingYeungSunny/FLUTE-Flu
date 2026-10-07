# MEMORY — MIFlu / ChatTime journal reproducibility project

## Recovery track (A/B/C) — author-966 reproduction
- Tracks: A = author 966-row reproduction (676/97/193; `author_966` profile), B = refreshed 1025-row
  benchmark (717/819; v3_clean results, already frozen), C = holdout generalization.
- **A2 is COMPLETE and REPORTED (2026-09-26).** 36/36 fits, 8/8 baselines, 36 checkpoints locked
  (SHA-256) *before* any Test inference, 44/44 unified Test evaluations, primary metric independently
  recomputed from prediction NPZs (max Δ 4.44e-16, PASS). Reports: `recovery/stage5/results_report_zh.md`,
  `supervisor_brief_zh.md`, `results_tables_zh.md`, `execution_ledger.md`. Artefacts: `hpc_results/stage5_a2/`
  (local) + `/home/sychan552/stage5_a2_durable` (remote durable). **A0 still BLOCKED/未执行.**
- **Result:** `average_MSE_4L` (7-var z MSE) notext **1.922** < miflu **2.042** ≈ nlinear **2.050** <
  seasonal_naive 2.269 ≪ last_value 7.166. Text pathway shows **no confirmed benefit**; paired-by-seed
  signs flip across L (miflu−notext +0.119±0.275). MIFlu≈NLinear is *not resolvable* at 3 seeds —
  do NOT write it up as "equivalent". Corrected reconstruction, NOT a paper reproduction.
- **Budget:** 2.0 GPU-h cumulative cap for the whole round; **used 1.1536** (4153 GPU-s, `sacct -X`),
  **remaining 0.8464**. Rebuild with `recovery/stage5/build_ledger.sh`, never estimate.
- **Window rule defect (fixed, and it was real):** runners assigned windows by TARGET START only, so at
  L=60 train targets spilled into validation and validation targets into Test (contaminating checkpoint
  selection). `--containment strict` (whole target inside its split) gives 549/74/170, 537/62/158,
  525/50/146, 513/38/134. Default stays `start` for legacy comparability.
- **DEFER_TEST=1 pattern:** learned fits run with `DEFER_TEST=1` so `evaluate`/`export_prediction_csv`
  are skipped; per-(L,seed) best-val checkpoints are written to `--ckpt-dir`; a single later
  `score_test_stage5.py` pass does all Test scoring. Beware: any summary that does
  `np.mean([r['mse_all'] ...])` crashes with `TypeError: NoneType` under DEFER_TEST — that crashed
  4 no-text jobs after their training had already succeeded.
- **Resume-guard trap:** a "done" test that reads a metric column which is *absent under DEFER_TEST*
  marks every existing row complete. Key resume on `(L, rep, seed)` + per-seed checkpoint existence,
  never on a deferred metric. Symptom here: jobs COMPLETED in ~16 s having trained nothing.
- `run_task.sh` pipes each seed's output through `tail -40`, which destroyed per-epoch traces (20 epochs
  → 3 lines). MIFlu's runner writes a full per-run log; the ablation/nlinear runners do not, so
  `best_epoch` is unrecoverable for them. Don't `grep` those logs to "recover" epochs — it mis-attributes
  seeds. `best_val` is the selection quantity and IS recorded for all 36.
- Actual executed code hashes: `recovery/stage5/hashes_stage5_executed.json` (supersedes
  `hashes_stage5.json`, which predates the DEFER_TEST wiring — keep the old file as history).

## Stage 6 — A0 / A1 / eight-model (2026-09-26). New GPU used: 0.0000
- **Every Stage-6/A0 job was CPU-only**: submitted to `stingy` with **no `--gres`**, so it costs
  **zero** GPU-hours. `sacct` shows `billing=5,cpu=N,mem=NG,node=1` with no `gres/gpu`.
  This is how to do audits/archives/preflight at no budget cost. `coursework` is NOT available to
  this account; `batch` demands a bigger CPU/mem floor; `stingy` accepts CPU-only jobs.
- **A0 verdict (executed, CPU, job 587002):** text→output max diff = **exactly 0**; text gradient norm
  = **exactly 0**; 6/12 GPT-2 blocks; **LoRA never applied** (`PEFT=0`); **`freeze` is a no-op** →
  82,705,944 / 82,705,944 = **100% trainable**; forward is per-feature `(B,104,1)→(B,24,1)`;
  **Test covers feat_id=[0] only** (170→160 after drop_last); split **676/97/193 identical to A2**;
  Test read every epoch and used to pick + save the checkpoint; early stopping commented out.
  A0's three import blockers (`einops`, `embed.py`, peft symbol) are all **dead imports** — resolved by
  `recovery/a0/a0_compat.py` in a separate sys.path dir, author's tree byte-for-byte untouched.
- **A1 headline:** the paper **never states epochs or lr** ("set empirically", L298). Three incompatible
  configs: paper *unspecified* / released default 1 @ 1e-4 / project A2 20 @ 5e-4. And the paper's
  **token order is self-contradictory** (L205 `len(token)+num(patches)` vs L219 `num(patches)+len(token)`
  vs L225's index) — so "the code is wrong" is NOT the right claim; the code matches L222's prose
  ("the token portion is discarded"). The formula is what cannot be resolved.
- **Eight models:** runner `scripts/train_backbone_966.py` imports A2's `build_windows` /
  `load_and_normalize` / `eval_mse` **directly**, so protocol identity is by construction
  (verified: "reuses the SAME objects: True True True"). Six backbones self-check OK with **real**
  frozen backbones; trainable counts match the B track exactly (qwen 370,376 / calf 1,981,608 /
  timecma 1,391,016) → B-track timings are a valid cost basis. 96 final fits = **24 reused**
  (MIFlu+NLinear) + 72 new; measured **1.3221 GPU-h** pure training → **~1.8** with overheads.
- **PENDING-QUOTA (the only blocker):** A0 GPU ~0.5 + eight-model ~1.8 = **~2.3 GPU-h**, 26 jobs.
  A2's remaining 0.8464 was deliberately **not** spent. Cheap-first ordering means 5 models = 0.193
  GPU-h fits almost any grant; Qwen alone is 1.13.
- Frozen text-backbone tensors are **not** stored in the `.pth` (key set → `.frozen_keys.json`
  sidecar, values rebuilt from the pinned snapshot) — keeps 72 checkpoints under ~2 GB instead of ~40 GB.
- A2 checkpoints **archived + re-verified 36/36** against the FIRST lock at
  `/home/sychan552/stage5_a2_durable/checkpoints/` (7.4 G); scratch originals kept.
- `dispatch.sh` pattern worth reusing: with no `--run` it only prints the plan and exits, it owns an
  `EXEC_LOCK` it refuses to steal, and it checks consumed GPU-hours **before every submission**
  (`BUDGET_GPU_H`) so a stop leaves the remaining matrix recorded.

## 🔴 PERMANENT RULES
- **NEVER run compute jobs on the HPC login node** (2026-09-16 incident: `nohup python &` D-stated and blocked sshd
  forking; needed `kill -9`). All train/infer/eval/finalize via `sbatch`. Login node = submit/poll/small-file only.
- **GOLDEN RULE OF ARTIFACT ISOLATION:** every run saves to an immutable hierarchy; never share a checkpoint dir
  across horizons/variants.
- **Test/holdout isolation:** test & holdout access must remain 0/0 until champion lawfully frozen. Never mutate the
  frozen selection rule or raw `data/` beyond read.

## HPC environment (CityUHK Burgundy)
- Login: `ssh sychan552@burgundy.hpc.cityu.edu.hk` (ed25519 key). From Windows PowerShell the working
  incantation is `ssh -n -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 -o PreferredAuthentications=publickey cityu <cmd>`;
  without `PreferredAuthentications=publickey` the key is offered but the server falls through to
  keyboard-interactive and BatchMode fails. `scratch -> /scratch/sychan552`; `/home/sychan552` -> `/gpfs1/home/sychan552`.
- PowerShell → `ssh` strips `"` `'` `(` `)` **and expands `$var` locally** → never pass a bash `for` loop or
  `$d` inline (dies as a PowerShell parse error, e.g. `wc : term not recognized`). Write the remote script to a
  local file, `scp` it, `sed -i 's/\r$//'`, then `bash` it.
- **QOS RULE (non-negotiable):** `stingy` caps `Jobs=1` + `Submit-Job=1` → max 1 running + 1 pending.
  Default: `#SBATCH --partition=stingy --gres=gpu:a100:1 --time=04:00:00` (never bare `--gres=gpu:1` → V100 OOM;
  never `--time>04:00:00`). Avoid congested `gpu_a100`. Chain jobs via auto-submit polling `squeue -u $USER -h -p stingy`.
- Stack: py3.9, torch 2.5.1, transformers 4.57.6. Conda env `mlflu_hpc`
  (`/home/sychan552/.conda/envs/mlflu_hpc/bin/python`); login default python lacks torch.
- Storage quota: home 50/100 GiB; scratch 300/1024 GiB, 10-day grace.

## Paper ground truth: output shape & metric scope (verified 2026-09-22 from PDF)
- MIFlu predicts **all N=7 variables** (N×L), not ILITOTAL only. Eq.(1) X∈R^{N×T}→Ŷ; head = `nn.Linear(D, N*L)`
  (same as GPT4TS; ablation "w/o LoRA+multimodality ≡ GPT4TS").
- Table V MSE/MAE are **7-channel averages** in StandardScaler z-space. ILITOTAL alone is used only for the
  qualitative Fig. 7. Primary metric = `mse_all_7vars_full_horizon_z`; ILITOTAL metrics secondary-only.
- **Trap:** never compare ILITOTAL-only MSE against Table V (it is ≈1.9–2.0× the 7-var average on our test eval).

## Key model internals
- `MIFlu.forward(x, htext)`; `x`=(B,N,T) train-only z-space; `htext` from `TextualInputEmbedder`(gpt2) over a prompt.
- `gated_inject`: `use_text_ln=True, use_lora=True, gated_inject=True, unfreeze_first_k=2`.
- `ModalityAligner` at `model.forecasting_llm.modality_aligner`; its `cross_attn` discards weights → recover via
  forward hook (`need_weights=True`).
- Test window: input `data[k:k+T]`, target `data[k+T:k+T+L]`; T=104, val_end=819.
- gpt2_miflu full params=1,030,056; LoRA=73,728.

## "clean v3" execution + acceptance contract
- Version chain (tooling only; protocol frozen): …→ v3.19 `compact-durable` finalize. Active root
  `/scratch/sychan552/innovation_deploy_root_v3_clean14` (amendment B). Superseded roots + Gate jobs are IMMUTABLE.
- **Acceptance contract:** row job (train/infer/metrics) THEN finalize (compact→restore→predictions+4 metric artefacts
  reconcile→atomic durable publish→delete full ckpt). `COMPLETED 0:0` ≠ accepted; needs fail-closed
  `storage-verification-v1` + ACCEPTED ledger event. Finalize skips `export_compact` for deterministic baselines.
- **Compact checkpoint (bit-exact):** keep keys where `k not in base_sd or not torch.equal(v, base_sd[k])`.
  Read with `safetensors.torch.load_file` (NOT `torch.load` → UnpicklingError).
- **Ledger gotchas:** JSONL has NO spaces; never `sort` the frozen order file (reorders matrix); `scp` from
  space-containing paths silently splits → stage to a no-space dir.
- `clean_runner.py` (~345) forces `model_id="gpt2", load_backbone=True` for timecma_llm, so "removed" mode still
  stores frozen gpt2 → 503MB/checkpoint (compact removes).

## Wave-1 (frozen) — shape, selection rule, results
- **Shape:** 598 = 580 (Wave 1) + 18 deferred (Wave 2). Order = 320 primary + 8 baseline + 240 ablation + 12
  negative_control. deleted=0, duplicated=0. Durable: `/home/sychan552/innovation_durable/screening/`.
- **Per-run metrics (4 families):** `paper_aligned_full_output_metrics.json`, `ilitotal_fixed_step_metrics.json`,
  `ilitotal_full_horizon_metrics.json`, `pte_pie_metrics.json`.
- **Frozen selection rule:** rank `average_MSE_4L` (mean of per-L means over seeds 42..51, L∈{24,36,48,60},
  7-var full-horizon z, lower better). Secondary `average_MAE_4L`. Forbidden tie-breaks: peak-hit, PTE/PIE,
  baseline-relative ratio, `(r24+r60)/2`. Report top equivalence set (no manufactured unique champion).
- **Results (avg_MSE_4L):** gpt2_miflu 0.771 (winner) < nlinear 1.070 < patchtst 1.076 < dlinear 1.171 < timecma_llm
  1.181 < itransformer 1.253 ≈ qwen_time_llm 1.253 < calf_llm 1.765. Non-LLM (1.142) beats LLM (1.243); win driven by
  gpt2_miflu alone (SD 0.071 vs nlinear 0.003). seasonal_naive beats gpt2_miflu on L24/36/48. Ablation: only
  `without_dataset_information` significant (+12.8%, p=0.004); zero_text −0.063, shuffled_text +0.081.
- **PTE/PIE (secondary only):** `validation_predictions.csv` has `target_date=None` → target week =
  `forecast_origin+104+step`. patchtst PTE=1.61 wk best; gpt2_miflu mid-table (PTE 2.12 wk, PIE 41.5%).

## Deferred controls amendment (DONE — 2026-09-21)
- Append-only amendment `DEFERRED_CONTROLS_PROTOCOL_AMENDMENT_2026-09-21` resolves 18 deferred:
  defect-A (12) zero_text/shuffled_text = exact duplicates of accepted Wave-1 rows → equivalent, no rerun;
  defect-B (6) `llm_removed_or_alignment_only` rebound to timecma_llm.
- Registry `results/v3_clean/runs/complete_specs_amended.json`. Rebound jobs 576502/576507/576509 (L24),
  576510/576512/576513 (L60) all COMPLETED 0:0.
- Source edits: `compact_checkpoint.py` honours `INNOVATION_REGISTRY_REL`, drops `wave==2` disqualifier, carries
  `control`/`parent_model`/`amended_action`; `finalize_row.py` manifest gains provenance + `--amendment-id`.
  HPC originals backed up as `*.pre_amendmentB`.
- **FINALIZED (`_v319b` controller): 6/6 ACCEPTED**, `_w2` durable dirs published (compact ~5.3MB each,
  n_keys_unequal=0), full ckpt deleted. **Global reconcile CLOSED: 598 = 580 + 12 + 6**; Test/holdout=0/0.
- **Paired analysis (seeds 42-44, primary metric):** L24 removed 1.0955 vs timecma 1.0720 (+2.2%, p=0.490 ns);
  L60 removed 1.3301 vs timecma 1.2363 (+7.6%, p=0.002 significant) → LLM/text branch matters at long horizon.

## Local ↔ HPC gotchas
- PowerShell → `ssh` strips `"` `'` `(` `)` → remote one-liners use NO quotes/parens; use `grep -i word`,
  `cut -d_ -f1`, bare words; here-docs also lose quotes → use no-quote Python or pure bash.
- `scp` to a Windows path must NOT end with backslash. Safe-delete guard blocks `del`/`rmdir` → quarantine by `move`.
- Checkpoint `state_dict` cross-version: load `strict=False`, guard rejecting any other missing key (legacy
  `attn.bias`/`masked_bias` safe to ignore).
- Windows `write_to_file` writes CRLF → breaks remote token match → `sed -i 's/\r$//'`.
- `sacct -X` elapsed is `HH:MM:SS` with **no** day field unless >24 h; a naive `partition("-")` on it
  puts the whole string in the day part and throws. Handle both forms. `AllocTRES` shows
  `gres/gpu:a100=1` (not `gpu:a100:1`) — match on `gres/gpu=`.
- Finalize controller per-row `du -sh` D-stated the login node → strip it.
- Local env: py3.9, torch 2.6.0+cu124 (CPU), transformers 4.25.0; gpt2 in local HF cache → offline rebuild/inference.
  **python-docx + reportlab installed locally**; `scripts/v3_clean/md2docs.py` renders Markdown→DOCX/PDF.
- `git status --porcelain` with CJK filenames → UnicodeDecodeError under cp950 → use `encoding="utf-8", errors="replace"`.
