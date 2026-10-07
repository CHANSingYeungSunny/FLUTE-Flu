# D5 repair audit

Generated 2026-09-16T16:10:53Z.

## Root cause

1. The Qwen snapshot has **no `refs/` entry**, so `from_pretrained` called with the repository id cannot resolve it under `local_files_only=True`.
2. The Gate had redirected `HF_HOME` to the new v3 cache, **hiding the v2 verified GPT-2 cache** that CALF and TimeCMA use by default — so all three LLM branches failed, not just Qwen.

## Repair

- new `scripts/innovation/assets.py` holding the authoritative descriptor (`model_repo_id`, `model_revision`, `local_snapshot_path`, `local_files_only`, `trust_remote_code`, `asset_manifest_sha256`);
- `_FrozenTextModel` now loads from the **verified snapshot directory** with `local_files_only=True`, `trust_remote_code=False`;
- `gpt2` passes through unchanged, so no unsupported argument can reach it (D3 guard is covered by a test).

## Verification

- Local model-free tests: **32 passed, 1 skipped**.
- Fresh Gate 565844: **7/8**. Qwen loaded **offline from the verified snapshot**; CALF (3.2 s) and TimeCMA (2.0 s) now build and backprop successfully.

## Remaining defects (in the Gate harness only)

- **G1** the gate omits `set_train_statistics(...)` before the Qwen forward pass.
- **G2** the gate forced `model_id=Qwen` on CALF and TimeCMA instead of their preregistered `gpt2` backbone.

Both live in `hpc_scripts/v3_prepilot_gate.py`, which is **outside** the 87-file frozen runtime source. They are harness defects, not scientific defects — but the Gate must still reach 8/8 before any Pilot may be submitted, and this prompt authorizes no further Gate retry.
