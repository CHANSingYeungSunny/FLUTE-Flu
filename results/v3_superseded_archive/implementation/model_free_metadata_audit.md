# Model-free metadata audit

The metadata defect was repaired in `scripts/innovation/hpc_specs.py`: `_arch_report` is now a static dictionary lookup and never calls `make_backbone()`. The architecture-equivalence test helper also uses static reports for GPT-2, Qwen, CALF, and TimeCMA.

The focused static suite passed **22 tests**. No real model was loaded, no Transformers cache was used by the repaired metadata path, no network was used, and no National-Illness dataset was read during metadata generation. Real model construction, `from_pretrained`, forward/gradient checks, checkpoint restore, and offline-load checks remain compute-node-only.
