# TRACK C — EXECUTION LOG

`AUTHOR_966_STRICT_CONTAINMENT_8MODEL_TEST_CHAMPIONSHIP`
Started 2026-10-07. Continued from the accepted project state.

---

## 0. Entry state (accepted, not re-audited)

| item | state |
|---|---|
| Track R (paper reproduction) | `PARTIAL_REPRODUCTION` — frozen |
| Track H (1025-row replacement) | `PARTIAL_HISTORICAL_CONTROLLED_REPLACEMENT_EVIDENCE` — frozen |
| F1 | frozen as `EXPLORATORY_A2F_CORRECTED_CONTRACT_PILOT` |
| F2 | cancelled |
| R1-C | unexecuted |
| storage | `STORAGE_READY_FOR_966_STRICT_8MODEL` |

---

## 1. Track H stopped safely

| step | action | result |
|---|---|---|
| 1 | killed the local submission controller | no further Track H submissions possible |
| 2 | in-flight job 608287_1 at 7:52 of a typical 8:51 | **allowed to finish** (near completion, no successor) → COMPLETED |
| 3 | stray job 608301_3 discovered, 3:41 of ~8:00 | **cancelled** (not near completion) |
| 4 | verified no controller process remained | `ps` clean |
| 5 | Track H outputs | **8 runs preserved**, nothing deleted |

**Frozen Track H evidence: 8 runs** — seed 42 × 4 horizons, seed 43 × 4 horizons.
Classified `PARTIAL_HISTORICAL_CONTROLLED_REPLACEMENT_EVIDENCE`. Not the champion.

---

## 2. Key contract finalised (§4)

The split-labelling defect was fixed and verified: **split membership is now
determined by the target range, never by the input-origin index.**

| check | result |
|---|---|
| builder assigns split from generation time | ✅ |
| regression assertion active in the builder | ✅ (asserts label ⇔ target range) |
| regression assertion active in the Track C dataset loader | ✅ (`Strict966Dataset`) |
| all 12 horizon×seed Test origin counts exact | ✅ 170/158/146/134 |
| duplicate Test keys | **0** |
| final key-set SHA-256 | **`4ad79bb1…d1961`** |

| manifest | rows |
|---|---:|
| `STRICT_966_TRAIN_KEYS.csv` | 1,858,248 |
| `STRICT_966_VALIDATION_KEYS.csv` | 182,448 |
| `STRICT_966_TEST_KEYS.csv` | 521,136 |

### Superseded key manifest — disclosure

The **first** canonical build (SHA `0742b4ab…042a7`) carried the split-label bug
and was **regenerated in place**; the invalid CSV set was removed before
regeneration rather than archived to a separate directory. The invalid
identifier is recorded in `SUPERSEDED_KEY_MANIFEST_NOTE.txt`, and no superseded
key artefact survives that could contaminate scoring — but the strict
"archive the invalid manifests" step was **not** performed as specified. Recorded
here rather than silently omitted.

---

## 3. Cell classification (§4/§5)

96 cells = 8 models × 4 horizons × 3 seeds (42/43/44).

| class | cells | models |
|---|---:|---|
| `RESCORE_ONLY` | **84** | nlinear, dlinear, patchtst, itransformer, qwen_time_llm, calf_llm, timecma_llm |
| `GPU_RETRAIN` | **12** | official-repository-based corrected MIFlu |

### Why the stage-6 MIFlu cells were rejected despite passing every key check

The stage-6 `pred_miflu_*` artefacts satisfy **every** structural test —
`containment=strict`, `profile=author_966`, z-space, canonical origins, correct
`var_cols`, correct shapes. They are still inadmissible:

> stage-6 `pred_miflu_L24_s42.npz` is **byte-identical** to the A2 artefact
> (`sha256 76b81b5b0dfa5bde`), so it is the **project's own from-scratch
> reconstruction**, which §6 explicitly forbids.

**Key compatibility does not establish implementation identity.** Had the 84-cell
"all reuse" result been accepted at face value, the championship would have
silently substituted exactly the model the brief rules out.

---

## 4. Incident — heavy job on the login node (self-inflicted)

**What happened.** The first run of the canonical scorer was issued as an `ssh`
one-liner against the login node. It was heavy (84 cells × 28k+ key rows, with an
O(n) tuple-keyed reindex). The connection was **reset by peer** and the node
briefly stopped accepting SSH.

**Root cause.** Violation of the standing rule that the login node is for
submit/poll/small-file work only — the same class of mistake as the 2026-09-16
incident recorded in the project memory.

**Impact.** None to data or to the running GPU job: `608308_0` completed
normally (00:07:52, rc 0). No login-node process survived. No artefact was
damaged.

**Fix (two parts).**

1. `score_track_c.py` — replaced the tuple-keyed `set_index().loc[]` reindex with
   a `merge(..., validate="one_to_one")`, removing the superlinear step.
2. All scoring moved to `track_c_score.sbatch` — **CPU-only, zero GPU-hours, on a
   compute node**. The scorer is never run through `ssh` again.

**Regression guard.** Every subsequent call is a `sbatch` submission; the login
node is used only for `squeue`, `sacct`, `sbatch` and small file reads.

---

## 5. Track C MIFlu execution

Frozen configuration for all 12 cells (not tuned after any result):
`T=104, epochs=20, batch=16, lr=5e-4, LoRA r=4 on c_attn, PEFT=1, effective
freeze, validation-only selection, Test read once, locked checkpoint, atomic write.`

| cell | job | state | elapsed | note |
|---|---|---|---:|---|
| L24 seed42 | 608308_0 | **COMPLETED** | 00:07:52 | rc 0 |
| L36/48/60 seed42, all × seeds 43/44 | — | queued chain | — | 11 remaining |

**L24 seed42 contract verification** (the first cell, checked in full):

| check | value |
|---|---|
| window counts | **549 / 74 / 170** ✅ |
| n_val | 12,432 = 74·24·7 ✅ |
| n_test | **28,560 = 170·24·7** ✅ |
| trainable / total | 1,673,496 (2.02 %) ✅ |
| LoRA tensors | 12 ✅ |
| Test access during fit | **False** ✅ |
| Test MSE (z) | 1.885572 |
| Test MAE (z) | 0.871653 |

---

## 6. Retry log

| # | failure mode | classification | action | outcome |
|---|---|---|---|---|
| 1 | scorer O(n) reindex + login-node execution | environment / rule violation | merge instead of reindex; move to sbatch | fixed |
| 2 | stray Track H job 608301_3 | superseded-workflow | cancelled, evidence preserved | fixed |

Two distinct failure modes, one attempt each. Within the two-retry budget.

---

## 7. Completion record

| stage | job | state | result |
|---|---|---|---|
| 12 MIFlu cells | 608308 … 609378 | all COMPLETED rc 0 | 12/12, zero contract failures |
| canonical scorer | 609385 | COMPLETED | **96 cells scored, 0 rejected** |
| seed-42 gate | 609386 | COMPLETED | **22 PASS / 0 FAIL** |
| finalizer | 609408, 609439 | COMPLETED | 12 deliverables generated |
| final manifest | 609446 | COMPLETED | all required deliverables present |

**Champion: official-repository-based corrected MIFlu** — mean one-time Test
`average_MSE_4L` **1.8652** (SD 0.0916), first at all four horizons.

GPU cost **1.5083 GPU-hours** across 12 jobs, all rc 0. Scoring, gate, finalizer
and manifest were CPU-only — zero GPU-hours.

### Additional defects found during finalisation

| # | defect | class | fix |
|---|---|---|---|
| 4 | `all_jobs_rc_zero` reported False on a fully successful matrix | code (report parsing) | ledger stores `rc` as the string `"rc=0"`; strip the prefix before comparing |
| 5 | DOCX: table header not repeated across a page break | document layout | set `w:tblHeader` on every table header row |
| 6 | DOCX: model column too narrow, name wrapped | document layout | explicit column widths |
| 7 | DOCX: model name duplicated in one sentence | document text | corrected |
| 8 | console `UnicodeEncodeError` (cp950) printing Chinese paths | environment | force `PYTHONIOENCODING=utf-8` |

All five verified fixed by re-running and re-inspecting the rendered pages.

### Final deliverable set

All 36 required Track C deliverables present and non-empty, plus the DOCX and
its render audit (`FINAL_DOCX_RENDER_AUDIT.md`, `FINAL_DOCX_SOURCE_DATA_MANIFEST.csv`,
`FINAL_DOCX_SHA256.txt`), plus `TRACK_C_DELIVERABLE_MANIFEST.csv` with size and
SHA-256 per file.

**DOCX render audit: PASS** — 8 pages, no clipping, no blank pages, no
overlapping text, tables complete, pagination continuous. The original report
`MIFlu_非LLM与LLM流感预测最终报告_中文版.docx` is **unchanged**
(sha256 `9c573f48…`).

### Tier-2

**Not started.** Explicitly gated behind the championship report, which is now
complete — so Tier-2 (Table VIII, Table VII if assets exist, Fig. 3, runtime,
sensitivities) is the next eligible work.