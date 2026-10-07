# TRACK C — CHAMPION REPORT (EN)

`AUTHOR_966_STRICT_CONTAINMENT_8MODEL_TEST_CHAMPIONSHIP`
Generated 2026-10-07 from the validated result files. No value below was typed
by hand.

---

## Verdict

**Champion: the official-repository-based corrected MIFlu.**
One-time Test, matched seeds 42/43/44, mean four-horizon `average_MSE_4L` =
**1.8652** (SD 0.0916), mean `average_MAE_4L` = **0.8842**.

It is first at **all four horizons** (L24 1.9686 · L36 1.9332 · L48 1.7547 ·
L60 1.8042), so the win does not depend on an average hiding a loss.

## Final Test ranking

| rank | model | side | mean MSE₄ₗ | SD | mean MAE₄ₗ |
|---:|---|---|---:|---:|---:|
| 1 | **miflu** (official-repo) | LLM | **1.8652** | 0.0916 | **0.8842** |
| 2 | nlinear | non-LLM | 2.0495 | 0.0299 | 0.9566 |
| 3 | dlinear | non-LLM | 2.3478 | 0.0040 | 1.0884 |
| 4 | timecma_llm | LLM | 2.6700 | 0.0177 | 1.0927 |
| 5 | patchtst | non-LLM | 3.9205 | 0.0543 | 1.3826 |
| 6 | itransformer | non-LLM | 3.9847 | 0.0317 | 1.3545 |
| 7 | qwen_time_llm | LLM | 5.2196 | 0.0701 | 1.5784 |
| 8 | calf_llm | LLM | 5.5153 | 0.0307 | 1.6080 |

MAE ranking is identical in order.

## Pairwise vs the champion (diff = miflu − other; A wins only if diff < 0)

| opponent | mean diff | miflu wins | opponent wins |
|---|---:|---:|---:|
| nlinear | −0.1844 | **11 / 12** | 1 |
| dlinear | −0.4827 | 12 / 12 | 0 |
| timecma_llm | −0.8049 | 12 / 12 | 0 |
| patchtst | −2.0553 | 12 / 12 | 0 |
| itransformer | −2.1195 | 12 / 12 | 0 |
| qwen_time_llm | −3.3544 | 12 / 12 | 0 |
| calf_llm | −3.6501 | 12 / 12 | 0 |

The nlinear row is the integrity check: the sign of the mean difference and the
win count agree, and one cell genuinely went to nlinear. A reversed win-count
bug would have reported 1/12 here.

## Two conclusions that must both be stated

1. **The corrected MIFlu is the best individual model.**
2. **The non-LLM group mean is better than the LLM group mean** —
   non-LLM **3.0756** vs LLM **3.8175**.

These are not in conflict. MIFlu is the only LLM-side model ahead of any
non-LLM model; `qwen_time_llm` (5.2196) and `calf_llm` (5.5153) drag the LLM
mean down.

## Contract and gates

- dataset sha `2a96dfed…ebfe5`, 966 rows, split **676 / 97 / 193**, T = 104
- strict containment; origins 549/74/170 · 537/62/158 · 525/50/146 · 513/38/134
- canonical key-set SHA `4ad79bb1…d1961`; 0 duplicate keys
- **seed-42 gate: 22 PASS / 0 FAIL**
- **scorer: 96 cells scored, 0 rejected**
- Test never read during fitting in any cell (`test_access_during_fit = False`)
- cells: 84 `RESCORE_ONLY`, 12 `GPU_RETRAIN`

### Rejected artefact

Stage-6 `pred_miflu_*` passed every structural check and was still rejected: it
is byte-identical to the A2 artefact (`sha256 76b81b5b0dfa5bde`), i.e. the
project's own reconstruction, not the official-repository implementation.
**Key compatibility does not establish implementation identity.** The 12 MIFlu
cells were therefore retrained.

## Cost and storage

- 12 GPU jobs, **1.5083 GPU-hours** total, all rc 0
- scoring and gate: CPU-only, zero GPU-hours
- quota (from `mmlsquota`, not filesystem free space): home **31 / 50 GB**
  (headroom 19 GB), scratch **285 / 300 GB** (headroom 15 GB), grace `none` on both
- checkpoints: locked format only, ~6.7–9.8 MB per cell; no per-epoch or
  optimizer state retained

## Limitations

- the claim holds only for this dataset, split, window rule, seed set and
  checkpoint policy
- three seeds support a standard deviation but not a strong significance claim;
  no p-values are asserted
- horizons are not independent replications
- `qwen_time_llm`, `calf_llm`, `timecma_llm` are *inspired* simplifications
  (frozen backbone + named component contract), **not** reproductions of the
  published systems — so "the LLM side is weaker" is scoped to these
  implementations
- MIFlu's paper-level verdict remains **`PARTIAL_REPRODUCTION`**; winning
  Track C does not make it a reproduction of the paper

## Track separation

| track | content | champion? |
|---|---|---|
| H | 1025-row historical replacement, old self-built MIFlu, split-boundary contamination | no — `PARTIAL_HISTORICAL_CONTROLLED_REPLACEMENT_EVIDENCE` |
| R | author-966 R1-B paper reproduction | no — `PARTIAL_REPRODUCTION` |
| **C** | **this report** | **YES** |

Absolute MSE values are never compared across tracks.

## Blocked paper items (unchanged)

- Table VI (US-Region) — `BLOCKED_BY_MISSING_DATA`
- Fig. 7 (few-shot) — `BLOCKED_BY_MISSING_CONFIGURATION`
- Table III — US-Region only, unreadable in the source PDF