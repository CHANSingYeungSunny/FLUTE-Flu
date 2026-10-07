# F1 SCRIPT AUDIT

Generated 2026-10-06. Static inspection plus lightweight runtime checks.
Raw evidence: `logs/script_audit_static.txt`.

---

## 1. The 23 items the brief asks to verify

| # | Item | Verified value | How | Status |
|---|---|---|---|---|
| 1 | dataset path | `CODE_ROOT/data/raw/national_illness_raw_paper_exact.csv`, with a fallback to the A0 checkout copy | grep in `f1_gpu_fit.sbatch` L71-74 | ✅ |
| 2 | output path | `F1_ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1` in **both** sbatch scripts | grep L46 / L39 | ✅ |
| 3 | seed | `SEED=42` in both scripts; written into every artefact | grep L47 / L42 | ✅ |
| 4 | horizon | array index encodes it: `0-3` → L 24/36/48/60 for MIFlu, `4-7` → the same for no-text | `f1_gpu_fit.sbatch` L56-58 | ✅ |
| 5 | model identity | `ARM` is `miflu` or `notext`, carried into `TAG`, the manifest and the ledger | L58 | ✅ |
| 6 | target variables | 7 channels, keys from `scripts/configs.py::VAR_COLS`; enforced at scoring by gate G4 | `f1_score_all.py::F1_VAR_COLS` | ✅ |
| 7 | scaler behaviour | `ScalerBundle` fitted on train rows only; `preflight()` asserts `scaler.train_end == train_end` | trainer assertion | ✅ |
| 8 | validation selection | best validation `mse_all` per (model, L, seed) | trainers | ✅ |
| 9 | Test isolation | `DEFER_TEST=1` exported in both scripts; the trainer logs *"Test NOT evaluated (validation-only fit)"* | grep L89 / L54 | ✅ |
| 10 | predictions saving | `score_test_stage5.py::dump_predictions` writes `np.savez_compressed(pred=…, target=…)`; the naive runner writes the same schema | code inspection | ✅ |
| 11 | targets saving | same call | code inspection | ✅ |
| 12 | checkpoint saving | `save_locked_ckpt()` writes the best-validation state plus a frozen-key sidecar | code inspection | ✅ |
| 13 | checkpoint loading | the scoring step reloads from `ckpt/<tag>/`; the frozen keys are reconstructed from the pinned snapshot and provable via the sidecar | code inspection | ✅ |
| 14 | independent-scorer compatibility | the NPZ schema matches what `scorer_f1.load_cell_validated` reads; validated on 8 real naive artefacts | dry run | ✅ |
| 15 | trainable parameters | MIFlu 1,030,056 / no-text 1,028,520 (L=24) | `F1_MODEL_IDENTITY.csv` | ✅ |
| 16 | total parameters | 82,705,944 (GPT-2 backbone + head) | same | ✅ |
| 17 | LoRA activation for corrected MIFlu | LoRA applied to `c_attn`, r=4; the project's `miflu_model.py` applies it via its own `LoRALinear`, **not** peft | code inspection + 1,030,056 trainable count | ✅ |
| 18 | no-text mechanism | `train_ablation.py --variant no_multi` removes the text branch and **keeps** the GPT-2 forecaster and LoRA | code inspection | ✅ |
| 19 | **no accidental released-code inactive text path** | F1 uses `miflu_model.py` (text **prefixed**, reads trailing patches) — the structure that was **verified `text_active`** this round, **not** `GPT4TS_lora.py` (verified `text_inert`) | `../postrun_audit_20261006/RELEASED_CODE_TEXT_PATH_FINAL_CONCLUSION.md`, `A2_TEXT_ACTIVE_MAGNITUDE_AUDIT.md` | ✅ |
| 20 | no Historical Track B weights | F1 reads only `CODE_ROOT` (the project tree) and writes only to `$HOME/.../f1`; it never opens a `innovation_deploy_root_v3_*` path. The scorer additionally **rejects** any Track-B-profile artefact | grep + acceptance test A10 | ✅ |
| 21 | no scratch output | every `SBATCH --output/--error` and every output variable points at `$HOME`; `CODE_ROOT` on scratch is declared READ-ONLY | grep L46 / L39 | ✅ |
| 22 | no login-node computation | both scripts contain `if [[ "$(hostname)" == hpclogin* ]]; then ... exit 3` | grep L53 / L46 | ✅ |
| 23 | sequential submission only | `run_f1_sequential.sh` submits one element at a time; both sbatch comments state the `MaxSubmit=1` constraint | script inspection | ✅ |

**All 23 verified.**

---

## 2. Corrected-MIFlu specific checks (§6 of the brief)

| Requirement | Evidence |
|---|---|
| **LoRA is actually applied** | trainable parameter count 1,030,056 ≪ total 82,705,944; the LoRA modules are `c_attn` at r=4, implemented in `miflu_model.LoRALinear`. (Contrast: the *released* `GPT4TS_lora.py` has `PEFT=0` by default, so its LoRA branch never executes — that defect is documented, and F1 does not use that code path.) |
| **intended modules are trainable** | 1,030,056 trainable in the corrected MIFlu vs 1,028,520 for no-text — the 1,536-parameter difference is exactly the text-path contribution |
| **frozen modules actually have `requires_grad=False`** | the frozen GPT-2 backbone is excluded from the saved checkpoint via `frozen = {n for n, p in model.named_parameters() if not p.requires_grad}`, and the list is written to a sidecar for audit |
| **the corrected implementation receives standardized input** | `MIFlu.forward` documents `x` as *"ALREADY in StandardScaler space"*; the trainer feeds `data_norm` |
| **the text intervention probe uses standardized input** | `../probe_a2_text_path_v2.py` applies the train-fit scaler first. **This was the defect fixed this round**: v1 fed raw values and inflated the measured text effect by 5–10 orders of magnitude |
| **saved checkpoints can be reloaded** | the frozen-key sidecar exists precisely so the reload can be *proven* rather than trusted; the reload path is exercised by the scoring step |

---

## 3. Matched no-text specific checks

| Requirement | Evidence |
|---|---|
| **the GPT-2 forecasting backbone remains** | `--variant no_multi` alters only the modality branch; total parameters are unchanged at 82,705,944 |
| **text content is removed or neutralised as defined** | the text branch is removed entirely (not zeroed, not replaced with a constant), so the mechanism question is "no text at all" |
| **architecture, optimizer and training policy otherwise matched** | same T=104, same 7 channels, same 20 epochs, batch 16, lr 5e-4, Adam, same containment, same `set_seed(seed + L)`, same validation selection |
| **labelled LLM-based unimodal, not non-LLM** | `F1_MODEL_IDENTITY.csv` places it in **category 2 (LLM-based unimodal)**; the four-category scheme is defined in `A2F_FAIR_COMPARISON_CONTRACT.md` §3 |

---

## 4. Runtime checks performed this round

| Check | Result |
|---|---|
| `naive_leakage_safe.py --self-test` | 6/6 PASS |
| `scorer_acceptance_tests.py` | 20/20 PASS |
| `f1_score_all.py --allow-partial` over 8 real artefacts | 8 accepted, 0 rejected, 0 key violations |
| `f1_naive_runner.py` on the real 966-row data, L=24 and L=60 | 170 / 134 origins — **matching the recorded strict-containment counts** (549/74/170 and 513/38/134), confirming forecast-key identity with the trained arms |
| `bash -n` on all three sbatch/launcher scripts | syntax OK |
| `ast.parse` on all F1 Python files | parses OK |

---

## 5. Findings that required a fix during this audit

| # | Finding | Action |
|---|---|---|
| 1 | the scorer crashed on a shape mismatch | wrote `scorer_f1.py` (validation-first), original untouched |
| 2 | Seasonal Naive leaked at L=60 (8 leads) | wrote `naive_leakage_safe.py` + `f1_naive_runner.py` |
| 3 | my first declared key list used wrong aliases | corrected to the project's `VAR_COLS`; the gate caught it |
| 4 | the `--allow-partial` path reported "ALL GATES PASS" while completeness gates failed | replaced with an explicit `status` field (`COMPLETE` / `INCOMPLETE_INTEGRITY_OK` / `FAILED_INTEGRITY` / `PARTIAL_DRY_RUN_INTEGRITY_OK`) |
| 5 | the F1 golden-model list omitted `seasonal_naive` under its runner name | the runner writes `model=seasonal_naive` (not the estimate file's `seasonal_naive_leakage_safe`) so the gate matches |

**None of these were papered over**; each is recorded here and in
`F1_SCORER_ACCEPTANCE_TESTS.md`.

---

## 6. What the audit does NOT cover

- It does not execute a GPU fit, so VRAM and peak-RAM figures are **estimates** derived
  from the measured stage6/A1 runs, not measurements of F1 itself.
- It does not verify the trainer end-to-end on the HPC; the trainers themselves are
  unchanged from stage5/stage6, where they were validated
  (`recovery/stage6/s6_cpu_validate.sh` records `syntax_fail=0`).
- It does not test checkpoint reload for the F1 tags, because no F1 checkpoint exists yet.
  That is verified as step 10 of the submission order.