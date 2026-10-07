# v3 Pilot validation report

Generated 2026-09-16T17:01:14Z.

**5/8 pilots completed.** Gate `565869` COMPLETED 0:0 (8/8).

| # | model | horizon | seed | job | state | exit | elapsed |
|---|---|---|---|---|---|---|---|
| 1 | `nlinear` | 24 | 42 | 565871 | COMPLETED | 0:0 | 00:00:09 |
| 2 | `dlinear` | 24 | 42 | 565875 | COMPLETED | 0:0 | 00:00:08 |
| 3 | `patchtst` | 24 | 42 | 565879 | COMPLETED | 0:0 | 00:00:11 |
| 4 | `itransformer` | 24 | 42 | 565880 | COMPLETED | 0:0 | 00:00:09 |
| 5 | `gpt2_miflu` | 24 | 42 | 565882 | COMPLETED | 0:0 | 00:02:09 |
| 6 | `qwen_time_llm` | 24 | 42 | - | NOT_SUBMITTED | - | - |
| 7 | `calf_llm` | 24 | 42 | - | NOT_SUBMITTED | - | - |
| 8 | `timecma_llm` | 24 | 42 | - | NOT_SUBMITTED | - | - |

## Marks (permanent)

`experiment_stage=pilot`, `purpose=infrastructure_verification_only`, `selection_eligible=false`, `paper_result_eligible=false`, `test_access_allowed=false`.

Pilot results are **not rankable** and are **not** paper results. Test/holdout access counts remain 0.

## Not done

Pilots 6-8 (`qwen_time_llm`, `calf_llm`, `timecma_llm`) were never submitted; the serial sequence stopped at 5/8 and resumption needs explicit authorisation.
