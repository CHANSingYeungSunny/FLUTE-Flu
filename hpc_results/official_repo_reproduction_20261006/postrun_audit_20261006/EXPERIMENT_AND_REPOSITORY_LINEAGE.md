# EXPERIMENT AND REPOSITORY LINEAGE

Generated 2026-10-06. Append-only.

**Purpose**: separate the two research lineages rigorously, so that no result from one
is ever presented as, averaged with, or ranked against the other.

---

## 0. The single hard boundary

```
author repo clone:  2026-09-24 09:54:29 +0800
                    recovery/author_repo/.git/logs/HEAD line 1:
                    "clone: from https://github.com/Jmoon3108/MIFlu.git"
```

This timestamp is **filesystem-proven**, not merely recalled. Everything **before** it
belongs to Historical Track B; everything **after** belongs to the official-repository
lineage.

| Lineage | Window | Basis |
|---|---|---|
| **Historical Track B** | ≤ 2026-09-22 | filesystem timestamps (see §2) |
| **Official-repository work** | 2026-09-24 → 2026-10-06 | clone log + job records |

---

## 1. Historical Track B — pre-official-repository work

### B1 — self-built MIFlu implementation

| Item | Value |
|---|---|
| Approx. date | 2026-08-05 → 2026-08-17 |
| Repository | the project's own repo (FLUTE-Flu), **not** the author's |
| Remote | `https://github.com/CHANSingYeungSunny/FLUTE-Flu.git` |
| Git commit | `1f6563f…` (single commit; history unusable for ordering) |
| Evidence | `analysis/*.py` (2026-08-05), `scripts/miflu_model.py`, `MIFlu_innovation_plan_v2.md` (2026-09-14), `v3` (2026-09-16) |
| Confidence | **filesystem** for dates; the *content* claim that this is a self-built implementation is **USER_CONFIRMED + filesystem-supported** (`scripts/miflu_model.py` is a from-scratch re-implementation, not the author's `models/GPT4TS_lora.py`) |

### B2 — the original LLM vs non-LLM comparison

| Item | Value |
|---|---|
| Approx. date | 2026-09-19 → 2026-09-21 |
| Evidence | `results/innovation/` (2026-09-19), `results/v3_clean/` (2026-09-21), `.codebuddy/memory/2026-09-1*.md` |
| Dataset | July-2026 1025-row snapshot |
| Confidence | **filesystem** for dates and outputs |

### B3 / B4 — old final deployment and checkpoint reduction

| Item | Value |
|---|---|
| Artifact family | `innovation_deploy_root_v3_*` (19 directories, **UNSAFE_TO_DELETE**) |
| Host | `/gpfs1/scratch/sychan552/` |
| Date | determined by the read-only audit job (see `HISTORICAL_TRACK_B_DEPLOYMENT_INVENTORY.csv`) |
| Reduction work | optimizer/scheduler stripping, best-checkpoint-only retention, LoRA handling, checkpoint consolidation, inference-only export — see `HISTORICAL_CHECKPOINT_REDUCTION_TECHNIQUES.csv` |
| Confidence | **filesystem** where measured; **USER_CONFIRMED** for the *motivation* (the stated reason was to fit within storage limits) |

### B5 — the author's official repository is pulled

```
2026-09-24 09:54:29 +0800   clone: from https://github.com/Jmoon3108/MIFlu.git
                            HEAD = 6ed210150b8819313947cf607eb1821c87b1bee3
```

**Confidence: filesystem-proven.**

> ⚠️ **USER_CONFIRMED status.** The brief states that Track B work was completed
> *before* the official repo was pulled. That ordering is **independently corroborated
> by the filesystem**: the Track-B output trees (`results/innovation`, `results/v3_clean`)
> are dated 2026-09-19/21, and the clone log is 2026-09-24. Where a Track-B fact rests
> on the user's recollection alone, it is labelled `USER_CONFIRMED` in
> `HISTORICAL_AND_OFFICIAL_TIMELINE.csv` and is **not** presented as filesystem-proven.

---

## 2. Official-repository lineage — 2026-09-24 onward

| Phase | Window | Evidence |
|---|---|---|
| Repository identity verification, data-identity audit | 2026-09-24 → 09-26 | `recovery/` (2026-09-24), `recovery/stage5/` (09-26) |
| A0-R released-code CPU diagnostics | 2026-09-26 | jobs 587002 etc.; `recovery/a0/` |
| A2 corrected reconstruction, stage-5 fitted runs | 2026-09-26 | `hpc_results/stage5_a2/` |
| A0-R GPU minimum diagnostic + stage-6 eight-model comparison | 2026-09-26 | jobs 587048–587385; `hpc_results/stage6/` |
| Independent audit | 2026-09-30 | `audit_20260930/` |
| Text-path probe (CPU + A100), PEFT diagnostic, A1 four horizons | **2026-10-05/06** | jobs 606357–606412 |
| This post-run audit | 2026-10-06 | job 606430 |

---

## 3. What may NOT be claimed about each lineage

### About Historical Track B

Track B **is not** and **must not be described as**:

- author-repository output
- official-code reproduction
- `A0-R`, `A1-P` or `A2-F`
- proof that the paper was reproduced
- a substitute for the official-repository benchmark
- a source of checkpoints that may be reused as official-repository results

### About the official-repository lineage

- Using the official MIFlu repository as the basis **does not** make NLinear, DLinear,
  PatchTST, iTransformer, Qwen Time-LLM, CALF or TimeCMA "official implementations".
  Those models have their own provenance; see `../IMPLEMENTATION_IDENTITY.md`.
- The author's released code being reproducible does **not** mean the paper was
  reproduced. See `../HYPERPARAMETER_PROVENANCE.md` and `TABLE_V_REPRODUCIBILITY_VERDICT.md`.

---

## 4. Cross-lineage reuse: prohibited by default

| Question | Default answer |
|---|---|
| May a Track-B checkpoint be scored as an A0-R / A1-P / A2-F result? | **No** |
| May Track-B and official-repository MSE values share a ranking table? | **No** |
| May they be averaged? | **No** |
| May a Track-B model be relabelled because the new basis "should" give similar numbers? | **No** |

The default compatibility verdict across lineages is
`INCOMPATIBLE_ACROSS_TRACKS_UNLESS_PROVEN_OTHERWISE`. Any exception requires an explicit,
evidence-backed justification recorded in `CROSS_TRACK_COMPATIBILITY_MATRIX.csv`.

---

## 5. Why the boundary matters scientifically

The Track-B deployment embedded checkpoint-reduction techniques (notably for Qwen) that
alter the artifact itself. Reusing such a checkpoint in a new comparison would silently
change the model under test while claiming the new protocol. That is a protocol mixture,
not a comparison. See `HISTORICAL_QWEN_REDUCTION_PROVENANCE.md`.