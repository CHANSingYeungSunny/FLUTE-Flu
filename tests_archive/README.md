# tests_archive — the archived pytest suite (for inspection)

This folder is a **copy** of the project's test suite as it stood on 2026-11-02, taken from
`99_旧文件存档/tests/` so that the handoff archive contains it. It is here for audit, not as a
working CI target.

## What is in it

43 files. The ones that matter for the claims in the documents:

- `test_miflu_ablations.py` — locks the Table VIII flag contract on `scripts/train_miflu.py`:
  defaults unchanged; `--no-lora` toggles only `use_lora`; `--num-layers K` sets depth only;
  `--no-text` removes the text branch; and, at the model level, `use_text=False` makes the forward
  pass ignore the text tensor, so two different text tensors give **bit-identical** predictions.
  That is the invariant the reports call "a structural verification, not an ablation effect".
- `test_timing_metric.py`, `test_revin_math.py`, `test_leakage_audit.py`,
  `test_walk_forward.py`, `test_train_regional.py`, `test_llm_seed_*.py` — the other protocol
  invariants (PTE, RevIN, leakage guard, fold geometry, regional harness, seed provenance).

## Honest state

- The suite was written against the `scripts/` layout of the time. The shipped tree uses
  `05_程序代码/`; several tests therefore **fail at collection** (missing module paths), which is
  why `pytest --collect-only` reports errors as well as collected tests.
- The documents do **not** claim a passing suite or a test count. They cite the specific invariant
  in `test_miflu_ablations.py` and point here so a reader can inspect it.
- To actually run it you need the training tree and its dependencies (torch, transformers), which
  are not part of the handoff. A static read of `test_miflu_ablations.py` is enough to check what
  the invariant asserts; running it is optional.

## Commands (on the owner's machine, not required for review)

```
python -m pytest -q tests_archive/test_miflu_ablations.py     # needs scripts/ + torch
python -m pytest -q tests_archive --collect-only             # shows the collection errors
```
