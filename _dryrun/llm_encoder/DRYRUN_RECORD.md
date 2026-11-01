# `_dryrun/llm_encoder/DRYRUN_RECORD.md` — record of the CPU wiring proof (2026-11-01)

> **What this is:** the evidence file for the `--dry-run` proof of
> `scripts/llm_encoder_backbone.py` (the frozen-LLM adapter). It records what
> the probe wrote, what was verified, and that the mock cells were **deleted**
> afterwards. It is **not** a result and must never be quoted as one
> (`AGENTS.md` §2 rule 13(b)).
> **Chain:** `docs/LEDGER.md` (2026-11-01 rows) → this file → the two
> `manifest_*.json` files kept next to it (`probe_only=True` in both).

---

## 1. The commands

```bash
# A. default arm label (= backbone name)
python scripts/train_backbone_966.py --backbone llm_encoder --dry-run \
    --horizon 24 --seed 42 --containment strict --encoder-batch-size 8

# B. per-model arm label (the form the 14 real LLM arms will use)
python scripts/train_backbone_966.py --backbone llm_encoder --dry-run \
    --horizon 24 --seed 42 --containment strict --encoder-batch-size 8 \
    --arm-label llm_probe_demo --export-dir _dryrun/llm_encoder_label
```

`--dry-run` implies: CPU only (no GPU touched), `--mock-encoder` (no model
download), 1 epoch, `max_train=32` / `max_val=16`, an export dir under
`_dryrun/`, and `probe_only=True` in the manifest. The TEST split is never
capped, so the cell carries the **real** window count.

## 2. What was written (before deletion)

Run A — `_dryrun/llm_encoder/pred_llm_encoder_L24_s42.npz`,
sha256 `4a642f2fff5d94e35f13b1399834a89f1c1f8c0e2cdfae92ceca1b9521673f49`
(115,689 bytes):

| key | shape | dtype |
|---|---|---|
| `pred` | `(170, 7, 24)` | float32 |
| `target` | `(170, 7, 24)` | float32 |
| `target_start_row` | `(170,)` | int32 |
| `var_cols` | `(7,)` | `<U17` |
| `L` | `()` | int32 (= 24) |
| `seed` | `()` | int32 (= 42) |
| `model` | `()` | `<U11` (`llm_encoder`) |
| `profile` | `()` | `<U10` (`author_966`) |
| `containment` | `()` | `<U6` (`strict`) |
| `space` | `()` | `<U24` (`standardized_train_fit_z`) |

Run B — `_dryrun/llm_encoder_label/pred_llm_probe_demo_L24_s42.npz`,
sha256 `47d15e11aeabf33a1509e36bab38a73cc076c1fb9c51a3ea06c975473831cdc8`
(115,692 bytes): identical keys/shapes/dtypes, with `model = llm_probe_demo`.
It proves `--arm-label` turns one backbone into its own benchmark row, which is
mandatory because `analysis_expanded.py` keys models off the **filename**
(`pred_<model>_L<L>_s<seed>.npz`) — all 14 LLM arms share the `llm_encoder`
backbone, so each must pass its own label.

## 3. What was verified (both runs)

1. `scripts/eval_windows.py::check_cell_layout` **passes**: `W=170`,
   `n_eval=160 = eval_slice(170)`, `discarded=10` — the `(W//16)*16` evaluation
   rule holds for the emitted cell.
2. `target` and `target_start_row` are **bit-identical** to the existing
   benchmark cell `hpc_results/expanded_runs/calf_llm_L24_s42/pred_calf_llm_L24_s42.npz`
   (`max|diff| = 0.0`): the adapter produces the *shared* windows, not a
   different slice.
3. `pred` is finite everywhere; `L`/`seed`/`profile`/`containment`/`space` are
   the benchmark's values.
4. The manifest records `probe_only=True`, `mock_encoder=True`,
   `artefact_is_a_result=False`, the pinned revision
   `Qwen/Qwen2.5-1.5B@8faed761d45a263340a0528343f099c05c9a4323`, torch
   2.6.0+cu124 / transformers 4.25.0 / Python 3.9.0, the measured hardware block
   (`run_device=cpu`; the host's GTX 1650 is reported as inventory only),
   encoder params 262,336 (trainable 0) and head params 1,560 (`D=64 -> L=24`).

## 4. What was deleted, and why

* `pred_llm_encoder_L24_s42.npz` and `pred_llm_probe_demo_L24_s42.npz` —
  **deleted** after the checks above.
* both `metrics.csv` files — **deleted** as well: they held a mock-run MSE that
  must never be greppable by an analysis script.
* `_dryrun/ckpt/` — never created (`DEFER_TEST` unset, so no checkpoint saved).
* Verified afterwards: `pred_llm*` matches **0** files anywhere in the
  repository, and `hpc_results/expanded_runs/**/pred_*.npz` is still **204**.

Kept on purpose: the two `manifest_*.json` files. They carry
`probe_only=True` / `artefact_is_a_result=False`, so they cannot be mistaken for
benchmark-cell manifests, and they are the machine-readable evidence that the
cells were produced and then removed.

## 5. What this proves — and what it does not

**Proves:** the code path `(B,7,104) -> per-channel prompt -> frozen encoder ->
mean-pooled last hidden state -> shared Linear(D,L) -> (B,7,L)` runs end to end
through `train_backbone_966.py`, writes a cell with the benchmark's exact key
set and layout, and trains only the head (encoder trainable = 0).

**Does not prove:** any benchmark number. The encoder is a mock; per
`AGENTS.md` §2 rule 13(b) these runs are `probe_only` and must never enter
`paper_tables/*`, a figure, or any aggregation. The real arms still need the
per-model checkpoints, the per-model environment, a pinned revision and the
12 cells (L=24/36/48/60 x seeds 42/43/44) on A100/`stingy` — see the "Adapter
status" section of `docs/LLM_ARMS.md`.
