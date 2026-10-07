# G1/G2 Gate-harness tests (model-free)

Generated 2026-09-16T16:20:39Z.

- harness version `v3-prepilot-gate-g1g2-fixed`
- monkey-patched to fail: `from_pretrained`, `socket.connect`, `socket.create_connection`, `torch.cuda`

- full suite: **40 passed, 1 skipped**

| ID | check | test | result |
|---|---|---|---|
| T1 | only qwen_time_llm receives the Qwen asset descriptor | `test_only_qwen_time_llm_receives_the_qwen_asset` | passed |
| T2 | calf_llm, timecma_llm and gpt2_miflu retain GPT-2 routing | `test_calf_timecma_and_miflu_retain_gpt2` | passed |
| T3 | broad **kwargs cannot override a preregistered backbone | `test_broad_kwargs_cannot_override_a_preregistered_backbone` | passed |
| T4 | Qwen statistics come from the training split only | `test_train_statistics_come_from_the_training_split_only` | passed |
| T5 | missing Qwen statistics fail closed | `test_missing_train_statistics_fail_closed` | passed |
| T6 | validation/Test statistics cannot be selected | `test_validation_or_test_statistics_cannot_be_selected` | passed |
| T7 | Gate writes to a create-only per-job directory | `test_harness_writes_to_a_create_only_job_directory` | passed |
| T8 | no metadata generation and no Test/holdout paths in the harness | `test_no_metadata_generation_and_no_test_paths` | passed |

No real model was loaded locally.
