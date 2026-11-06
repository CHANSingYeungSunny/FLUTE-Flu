# PAPER_TO_CODE

Status: **verification_level = unverified** for the paper text and the official repository commit.

| Paper claim | Official code | Local code | Discrepancy | Evidence depth |
|---|---|---|---|---|
| 10 repetitions, seeds unspecified | not pinned | 10 seeds 2021-2030 in `train_miflu.py` | seed labels are the project's, not proven the paper's | static only |
| checkpoint selected on test | `main_ILI_lora.py` lines 211/225 (reported) | validation selection in `train_miflu.py` | disclosed deviation | reported, not re-read here |
| 7-variable aggregate metric | not pinned | `eval_windows.py --n_vars 7` | original loader reportedly 1 variable | static |
| T/L semantics | not pinned | T=104, L=24/36/48/60 | none observed | static |

The MIFlu PDF was not opened in this session; the official repository commit was not pinned.
Do not upgrade this table to verified without the PDF and a commit hash.


## RE-CHECK NOTE (2026-11-04)

This table remains `unverified`: the paper PDF and a pinned official commit were still not opened. The row claiming test-set checkpoint selection is a reported reading, not a re-verified one. Do not state as fact that the original authors leaked test data, and do not assert the paper covers only two evaluation dimensions, until the full text and a commit hash are read.
