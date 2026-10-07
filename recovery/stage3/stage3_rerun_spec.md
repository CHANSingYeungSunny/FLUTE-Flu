# Stage 3 — rerun specification

Date: 2026-09-24. Status: **PREPARED** (no GPU jobs, training, or Test
evaluation launched). This document converts the Stage 1/2 audits into the
smallest scientifically justified rerun package.

Companion artifacts: `run_matrix.csv` (45 rows), `configs/` (profiles +
protocols), `commands.md` (exact commands), `author_data_adapter.patch`
(unapplied), `resource_estimate.md`, `supervisor_brief.md`.

---

## 1. Corrected evidence and claim labels

**Released source behavior** (A0, verbatim) is not the paper, and not the
project. Under its own defaults it runs `multimodal=0` (text dead), `PEFT=0`
(full fine-tune), `freeze=1` (no-op), `train_epochs=1`, evaluates only feature
0 (weighted ILI) on Test, and selects "best" by Test MSE in-loop. (Details:
`implementation_audit.md` §1–§7.)

**Project configuration** (B + corrected model) is a "project reconstruction
with documented deviations", *not* "paper-faithful": text-first ordering,
7-channel joint head, LoRA r=4 with proper freeze, validation selection, 20
epochs, 10 reps. It is hard-wired to the 1,025-row snapshot and — corrected
from an earlier claim — has already run the 966-row author data (job 514859)
and the 1,025-row paper-window run.

**Paper behavior** (A1) is reconstructed only to the extent the paper discloses
(K=6, Lp=24, S=2, r=4, batch=16, lr=5e-4, 20 ep, seed=42, scaler-train-fit,
70/10/20). Undisclosed: optimizer family, scheduler, seed *set*, scaler
convention, text content. See the discrepancy ledger in §4.

**Synthetic mechanism test vs end-to-end**: `smoke_text_visibility.py`
reconstructs a tiny causal-attention mechanism, not the author model. Its
bit-identical prefix confirms the *mechanism* (suffix text cannot reach retained
prefix under causal attention when no other path exists); it is **not** an
end-to-end reproduction.

**72 revised weeks**: report as "72 overlapping weeks with value differences"
(first revised 2002w40-based; verified alignment rule in `data_identity_report.md`),
not "revision", unless provenance supports it.

## 2. Calendar-gap consequences (corrected)

Run `recovery/stage3/gap_consequence_check.py` (already executed). Authoritative
result via `cdc_calendar.canonicalize_epiweeks`:

- **1,025-row snapshot**: exactly **one** real gap (2002 w21–39 absent, 19
  weeks, between rows 19/20). Three week-53 label-offset years exist but are
  calendar-dense (dates unchanged). Consequence, all horizons:
  - input crosses gap: **20 train origins** (rows 0–19);
  - target crosses gap: **0**;
  - nominal-lead ≠ elapsed weeks: **0**;
  - seasonal-naive lag-52 invalid origins: **0** (all target rows ≥ 104 are in
    the dense region; the gap only inflates 20 train lookbacks to ~123 weeks).
- **966-row author data**: **no real gap** (dense; starts 2002w40). Zero
  consequences.

Policy: **no gap-driven retraining or re-selection is required.** Preserve the
existing dense-row results; disclose the 20-origin lookback inflation as a
limitation. Do not impute the missing weeks; do not replace the snapshot with
refreshed API values. The split lengths 676/97/193 are per-split observation
counts, not window counts (window counts: `configs/author_966_profile.json`).

## 3. Recommended minimum matrix (45 rows, ~1.2 GPU-h)

| Leg | Question | Fits | Entry point | Status |
| --- | --- | ---: | --- | --- |
| A0 | What does the released code compute? | 1 | author `main_ILI_lora.py` | BLOCKED (D-a0-env) |
| A2-MIFlu | Corrected model vs paper on author data | 12 | `train_miflu.py --profile author_966` | BLOCKED_PENDING_PATCH (D-adapter) |
| A2-NOTEXT | Whole-text-pathway contrast | 12 | `train_ablation.py --variant no_multi --profile author_966` | BLOCKED_PENDING_PATCH |
| A2-NLIN | Linear floor on same task | 12 | `train_nlinear_966.py` (NEW) | BLOCKED_PENDING_PATCH (D-nlinear) |
| A2 naive | Persistence + seasonal floors | 8 | `train_naive_966.py` (NEW) | BLOCKED_PENDING_PATCH |

Seeds = first three of the frozen list `[42,43,44,45,46,47,48,49,50,51]`
(42/43/44), never chosen by result inspection. Selection = `average_MSE_4L`
(7-var, full-horizon, z-space), best **validation** MSE per fit, Test once.

**A1** shares its candidate config with A2-MIFlu (the corrected model was built
to the paper's disclosed protocol). No duplicate training is scheduled; A1 is
the ledger in §4 plus the A2-MIFlu numbers.

**"no text" definition**: `no_multi` = `use_text=False`, `prompt_cache=None`
(single zero token). Text tokens are removed, so sequence length and patch
positions change — this is a *whole-pathway* contrast, not a matched-length
content control. A same-length scrambled-text control is optional and separate
from the 36-fit minimum.

## 4. Paper-to-code discrepancy ledger (A1)

| Paper claim | Released code | Project reconstruction | Consequence for reproduction |
| --- | --- | --- | --- |
| multimodal text conditions forecast | text inert (`[htime‖htext]`, prefix retained) | text-first (`[htext‖htime]`) | released code cannot have produced a text-conditioned result |
| 7-variable national MSE/MAE | Test = feature 0 only | joint 7-channel head | paper number ≠ released-code output |
| held-out Test | Test in-loop, best-by-Test | val-selected, Test once | released code's Test is not unseen |
| LoRA/frozen backbone | freeze no-op, PEFT off (full FT) | LoRA r=4 + freeze | compute and equivalence differ |
| epochs/seeds | 1 epoch / itr 1 default | 20 ep / 10 reps | paper's epoch/seed set is external |
| prompt = influenza narrative | placeholder "Text from users" | real CDC stats prompt | text content is unverified in paper |

Blocked-for-A1 claim: a paper-reproduction *number* is blocked only where a
critical method is ambiguous (epoch count, seed set, scaler convention, text
content). The A2-MIFlu leg still answers "does the corrected model, on author
data, land near the paper number" — which is the actionable claim.

## 5. Full-compute expansion (separate, NOT in the minimum)

Only if the supervisor orders it, add incrementally (never by default):
- 10-rep paper protocol on A2-MIFlu (+108 fits ≈ +1.5 GPU-h);
- regional / few-shot / 8-model table (new data + new runners, larger budget);
- same-length scrambled-text control (matched content control, +12 fits);
- DeepSeek / newer Qwen backbones — explicitly deferred; out of core scope.

## 6. Evidence limits

- `smoke_text_visibility.py` proves a mechanism, not an end-to-end reproduction.
- The corrected model's 966-row run (job 514859) used the project's 676/96/194
  split, not the author's 676/97/193 — so it is a data-leg landmark, not the
  final A2 number.
- No untouched holdout exists; the old Test is `EXPOSED` and cannot be restored.
- Epoch time is measured (8 s); per-fit/total times are extrapolated; NLinear,
  naive, and A0 times are `UNMEASURED`.

## 7. Dependency-based decision tree

```
D-adapter (apply patch) ──┬─ yes ─▶ A2-MIFlu / A2-NOTEXT ready
                          └─ no  ─▶ A2 fully blocked (data-leg only)
D-nlinear (authorize runners) ─▶ A2-NLIN / A2 naive
D-a0-env (GPU + gpt2 cache) ─▶ A0-01
D-split (676/97/193 vs 676/96/194) ─▶ boundary for all A2 rows
D-target (keep average_MSE_4L) ─▶ metric for all A2 rows
D-scope / D-compute / D-naming / D-holdout ─▶ expansion + labeling + C
```

Every proposed run is `PREPARED`; none is `CHECKED` (that requires running,
which is GPU-gated). `BLOCKED` vs `BLOCKED_PENDING_PATCH` is recorded per row in
`run_matrix.csv`.

## 8. Stop line

No GPU jobs, training, or new Test evaluation were launched. The next step is
supervisor approval of the D-decisions, then applying the patch and running the
A2 matrix on a compute node (Stage 4, not started here).
