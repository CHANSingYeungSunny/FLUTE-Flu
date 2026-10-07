# Stage 4 — applied code changes & configuration hashes

Date: 2026-09-24. Status: **READY_FOR_AUTHORIZED_LAUNCH** (implementation +
CPU preflight done; no GPU job, training, or Test evaluation launched).

The Stage-3 `author_data_adapter.patch` was **illustrative and did not apply**
(`git apply --check` fails with "patch with only garbage"). Per Stage 4 §2 I did
**not** force-apply it; I implemented the same behaviour directly with `Edit`,
in isolation, on branch `recovery-stage4`. The 1025-row guard is **not** deleted —
it is retained for the default profile and bypassed only via an explicit,
hash-pinned `--profile author_966`.

---

## 1. What changed and why

| File | Change | Why |
| --- | --- | --- |
| `scripts/configs.py` | Added immutable `DATA_PROFILES` (project_1025 / author_966), `resolve_profile()`, `split_for_profile()`, `verify_profile_hash()`; extended `_self_check()`. | Give each data vintage its own pinned data-hash, split rule, scaler path and prompt date-range, so track A (author 966) can never be silently conflated with track B (project 1025). |
| `scripts/textual_embedder.py` | `build_prompt()` / `_format_prompt()` accept `date_range_string`. | The author 966 profile says "between 2002 and 2020"; the prompt label must follow the profile (descriptive only — min/max stats are already train-only). |
| `scripts/train_miflu.py` | Added `--profile`; `load_and_normalize()` uses `split_for_profile()`; scaler path from profile; `attach_calendar(..., raw_csv=DATA_PATH)`; prompt built with `date_range_string`. | Let the corrected MIFlu run on author 966 (676/97/193) without touching the 1025-row default. |
| `scripts/train_ablation.py` | Added `--profile`; same threading through `load_and_normalize()`, prompt builders, and the run header. | Let the `no_multi` (no-text) ablation run on author 966. |
| `scripts/train_nlinear_966.py` | **NEW** thin NLinear runner (reuses `innovation/backbones/dlinear.py::NLinear` via `importlib`, avoids the heavy `backbones/__init__.py`). | NLinear was only reachable through the 1025-row 598-spec innovation harness; this runs it under the A2 protocol on author 966. |
| `scripts/train_naive_966.py` | **NEW** deterministic Last-Value / Seasonal-Naive runner. | The two forecast floors were never computed on author 966. |

The full unified diff is in `recovery/stage4/adapter.diff` (reproducible with
`diff -u recovery/stage4/before/<f> scripts/<f>`).

## 2. Configuration hashes (SHA-256, first 16 hex)

| Artifact | before (Stage 3) | after (Stage 4) |
| --- | --- | --- |
| `scripts/configs.py` | `5b64ad545a621b6b` | `06eb39cd55df0bb8` |
| `scripts/textual_embedder.py` | `55022ebba7e9d437` | `13b51b34f6253d0b` |
| `scripts/train_miflu.py` | `a36aa336b1306f83` | `7839514a3e1d8ac0` |
| `scripts/train_ablation.py` | `22ef8ac74d3e57f5` | `a0578d2608c8ad2a` |
| `scripts/train_nlinear_966.py` | — (new) | `46c855c63af1a41e` |
| `scripts/train_naive_966.py` | — (new) | `434857f812deceff` |

## 3. Frozen dataset profiles

| profile | data_path | sha256 | n_rows | split | scaler_path | prompt span |
| --- | --- | --- | --- | --- | --- | --- |
| `project_1025` | `data/raw/national_illness_raw.csv` | `c2b983af…` | 1025 | 717/819 | `data/scaler_miflu_national.json` | 2002–2021 |
| `author_966` | `data/raw/national_illness_raw_paper_exact.csv` | `31ffc169…` | 966 | 676/773 | `data/scaler_miflu_author966.json` | 2002–2020 |

Both hashes verified at runtime (`verify_profile_hash`); both scaler paths are
distinct so no cache is ever shared across vintages.

## 4. Behaviour preservation

- `project_1025` remains the default profile in every entry point; its data
  path, hash, split (717/819) and scaler path are byte-for-byte unchanged.
- `train_ablation.load_and_normalize()` still calls `assert_full_window()` +
  `derive_split()` **for the default profile only** — the 966-row truncation
  guard is preserved, not deleted.
- `configs._self_check()` still passes (new assertions added, none removed).
