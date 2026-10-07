# HISTORICAL TRACK B — RECOVERABILITY VERDICT

Generated 2026-10-06.

## Verdict

# NOT RECOVERABLE AS A RUNNABLE DEPLOYMENT — PRESERVED AS AN ARTIFACT ARCHIVE

| Aspect | Verdict |
|---|---|
| is the code present? | **YES** - the self-built `scripts/` is inside every directory |
| are checkpoints present? | **YES** - 594 files, 201.7 GiB, all retained |
| is any of it byte-identical to anything else? | almost none - only 66.7 MiB of 201.7 GiB |
| can a run be re-executed *from the family alone*? | **NO** - base weights, tokenizer, config and the launch command are all outside or absent |
| can metrics be independently verified? | **NO** - no predictions or targets were saved |
| is there a documented entry point? | **NO** - no launch script, README or CI config in any of the 19 |
| is the dataset version recoverable per run? | **NO** - `UNRECOVERED` for most runs |
| is it safe to delete to relieve the scratch quota? | **NO** - `UNSAFE_TO_DELETE`; and deduplication recovers only ~313 MiB anyway |

## Strongest candidates for future attention

| Rank | Directory | Why |
|---|---|---|
| 1 | `innovation_deploy_root_v3_clean6` | largest (52 GiB), most files (5,023), most checkpoints (221), latest of the "clean" family except clean14 |
| 2 | `innovation_deploy_root_v3_clean14` | **latest mtime in the whole family (2026-09-21T04:56:42Z)** - by construction the closest to the end of Track-B work |
| 3 | `innovation_deploy_root_v3_5` | 50 GiB; the last of the non-clean builds (2026-09-17) |

## Strongest Qwen deployment candidate

The `durable_sim/**/primary__qwen_time_llm__L*__seed*__w1/compact.safetensors` exports
(1.41 MiB each, 4,167x reduced). They are the only **deployment-ready** Qwen artifacts in
existence, and they are **the only known reduced form** for that model - hence
`HISTORICAL_FINAL_DEPLOYMENT_POSSIBLE_DUPLICATE` at high priority, and preserved.

## What remains preserved no matter what

Everything. See `FILE_INTEGRITY_AND_NONDELETION_CONFIRMATION.md`.

## Minimum future recovery test (no GPU, CPU-only Slurm job)

1. Load **one** `compact.safetensors` and print its key names and dtypes (does not require
   a base model).
2. Determine from the keys whether the export is adapter-only or adapter+head.
3. Confirm whether an external Qwen2.5-1.5B base is required.
4. Attempt a single forward pass.

Steps 1-2 are cheap and settle most of the `UNKNOWN` rows in
`HISTORICAL_CHECKPOINT_REDUCTION_TECHNIQUES.csv`. **Not run in this round** - it exceeds
what the brief authorised (preserve and understand, not recovery execution).

## Why it cannot substitute for a new official-repository run

1. Different codebase (self-built, not the author's).
2. Different lineage (predates the 2026-09-24 clone).
3. Checkpoints were **reduced after training**, so the artifact differs from the trained model.
4. No predictions were saved, so nothing can be re-scored under a new contract.
5. Dataset version is not recoverable per run.

Using any of it inside A0-R, A1-P or A2-F would create an invalid mixture.
