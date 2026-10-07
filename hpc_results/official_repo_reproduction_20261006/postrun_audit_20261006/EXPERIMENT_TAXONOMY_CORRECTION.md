# EXPERIMENT TAXONOMY CORRECTION

Generated 2026-10-06. Append-only - no original file was modified.

## Purpose

The earlier deliverables used looser naming ("A2", "A1", "stage6", "the A1 runs").
This document fixes the canonical taxonomy and re-labels every existing artifact
against it, so that a reader cannot mistake one track for another.

## Canonical names

| Name | Meaning | Repository basis |
|---|---|---|
| **A0-R** | author released-code replay — records what the shipped code actually does, defects preserved | author repo, verbatim |
| **A1-P** | paper-configuration reconstruction — the paper's intended experiment rebuilt on the author repo | author repo + declared reconstruction |
| **A2-F** | corrected fair benchmark — the new LLM vs non-LLM comparison under one shared contract | author repo basis, corrected implementation |
| **Historical Track B** | the earlier self-built implementation, benchmark and deployment, all predating the official repo pull | project's own code |
| **July-2026 track** | results computed on the 1025-row July snapshot | either codebase, distinct dataset |

## Re-labelling of existing artifacts

| Artifact | Old label used | **Correct label** | Why |
|---|---|---|---|
| `hpc_results/stage5_a2/**`, jobs 5858xx | "A2" | **A2 basis (corrected reconstruction)**, *not yet* A2-F | corrected implementation, but its model set and contract predate the A2-F contract in `A2F_FAIR_COMPARISON_CONTRACT.md` |
| `hpc_results/stage6/**`, jobs 5870xx–5873xx | "stage6 eight-model" | **A2 basis + A0-R diagnostics** | mixes a corrected-implementation benchmark with released-code diagnostics |
| jobs 606365/606378/606385/606412 | "A1 runs", `A1_reconstructed_paper_config` | **A0-R** released-code feature-0 replay, single run per horizon | they ran the author's entry point with its defects intact (Test-selected checkpoint, feature-0 Test, no-op freeze) |
| jobs 606357/606358/606360 | "text-path probe" | **A0-R evidence** | deterministic released-code intervention |
| `results/v3_clean/**`, `results/innovation/**` | "v3_clean", "innovation" | **Historical Track B** | predate the 2026-09-24 clone; self-built code |
| `innovation_deploy_root_v3_*` (19 dirs) | "the deploy roots" | **HISTORICAL_TRACK_B_PRE_OFFICIAL_REPOSITORY_DEPLOYMENT** | all latest mtimes <= 2026-09-21, before the clone |
| July-2026 1025-row numbers | sometimes "the B track" | **July-2026 track**, a *dataset*, not a codebase lineage | avoids collision with "Track B" |

## Status of each track

| Track | Status | Label |
|---|---|---|
| A0-R released-code behaviour audit | substantially complete | `PARTIAL` (full released-code replay across 10 repetitions never run) |
| Released-code text-path resolution | complete, CPU + A100 agree | `COMPLETE` |
| A1-P paper reconstruction | contract audited; **no A1-P run exists yet** | `BLOCKED_BY_MISSING_INFORMATION` |
| A1-P at 10 repetitions | not run | `BLOCKED_BY_GPU_QUOTA` |
| A2-F fair benchmark | contract written; **no A2-F run exists yet** | `NOT_STARTED` |
| Historical Track B preservation | inventoried read-only | `COMPLETE` for inventory, not for recovery execution |
| Paper Table V–IX / Figures 3–7 | not reproduced | `NOT_STARTED` |

## The naming rule going forward

1. A run is A0-R only if it executes the author's code **unmodified in behaviour**.
2. A run is A1-P only if it targets the **recovered paper contract** with a disclosed
   reconstruction ledger — and it does not exist yet.
3. A run is A2-F only if it satisfies **every** clause of
   `A2F_FAIR_COMPARISON_CONTRACT.md`.
4. Anything from the self-built codebase is **Historical Track B**, permanently.
5. No result may be moved between these categories by renaming. A change of category
   requires a new run.
