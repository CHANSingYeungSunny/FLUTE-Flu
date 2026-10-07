# AUTONOMOUS EXECUTION LOG

Project: MIFlu reproduction / historical replacement (R0–R10).
Session date: 2026-10-07 (HKT). Host reachable: CityUHK Burgundy.

---

## 0. State found at session start

| Item | State |
|---|---|
| Slurm queue | empty at first poll |
| **in fact** | a corrected-pilot controller `/tmp/r1b_v2.sh` was **already running** (PID 665478) |
| namespace | `official_repo_reproduction_20261006/r1_v2_20261007/` |
| home | 30 GB / 50 GB quota |
| scratch | **414 GB / 300 GB quota — grace EXPIRED** |
| highest failed pilot | jobs 607969_0 (FAILED), 607984_1 (CANCELLED) under the old `r1/` namespace |
| F1 | frozen; not touched |

**Discovery.** The previous pilot's engineering failure (short final Test target)
had already been diagnosed and fixed, and a *corrected* chain was mid-flight when
this session began. The correct action was therefore **not** to resubmit — it was
to verify the fix, let the chain finish, and work the other fronts in parallel.
Submitting anything would have collided with `MaxSubmit=1`.

---

## 1. Corrected-window verification (authorisation §4, items 1–9)

Ran `verify_corrected_window.py` against the **deployed** trainer, imported
verbatim rather than re-typed.

**Result: 49 PASS / 0 FAIL.**

| Required check | Result |
|---|---|
| corrected code deployed (SHA-256 vs HPC copy) | `b0789459…86f3` — identical |
| regression assertion rejects short targets | PASS — old formula reproduced, 103 short windows at L=24, e.g. `o=839 → 23 rows`; corrected class asserts fail-closed |
| CPU sweep over every split × every horizon | PASS — 4 horizons × 3 splits |
| every input is `(104, 7)` | PASS |
| every target is `(L, 7)` | PASS |
| all seven channels present | PASS — `1,2,3,4,5,6,OT` |
| no target crosses a split boundary | PASS |
| window equals `data[o−T+1:o+1]` / `data[o+1:o+1+L]` | PASS |
| forecast-key counts match contract | PASS — all four horizons exact |

Counts reproduced exactly: **549/74/170 · 537/62/158 · 525/50/146 · 513/38/134**.
Evidence: `R1B_CORRECTED_WINDOW_VERIFICATION.json`.

Data identity: `2a96dfed…bfe5`, identical locally and on the HPC.

---

## 2. Corrected R1-B pilot (authorisation §4)

Namespace **`r1_v2_20261007`** — deliberately distinct from the invalid `r1/`
written by jobs 607969/607984, so failed output cannot be mistaken for corrected
output. The old logs are preserved untouched.

Progress observed during this session (chain driven by `/tmp/r1b_v2.sh`):

| L | job | state | elapsed | GPU-h | Test MSE | Test MAE | paper MSE/MAE |
|---|---|---|---:|---:|---:|---:|---|
| 24 | 608045_0 | COMPLETED | 00:08:01 | 0.1336 | **2.1335** | **0.9298** | 1.542 / 0.726 |
| 36 | 608061_1 | COMPLETED | 00:07:45 | 0.1292 | **2.0227** | **0.9977** | 1.422 / 0.779 |
| 48 | 608087_2 | COMPLETED | 00:07:31 | 0.1253 | **1.8413** | **0.8957** | 1.414 / 0.757 |
| 60 | 608105_3 | COMPLETED | 00:07:17 | 0.1214 | **1.7933** | **0.9116** | 1.364 / 0.719 |
| | | | **00:30:34** | **0.5094** | | | |

Every fit passed its own gates: validation-selected checkpoint, Test read once,
locked checkpoint written and atomic, `checkpoint_reload_max_abs_diff = 0.0`,
prediction NPZ persisted, origins matching the verified contract.

**The chain completed within this session.** Independent scoring (gate C12) and the
per-checkpoint text-path probe (gate C6, job 608153, CPU-only/zero GPU-hours) both
followed, so **all 15 contract gates are closed**.

**Tier-1 verdict: `PARTIAL_REPRODUCTION`** — 0/4 horizons inside the predeclared
±0.10 MSE band. Full detail in `R1B_CORRECTED_PILOT_REPORT.md`.

---

## 3. Storage cleanup (authorisation §5–8)

Executed with a nine-guard classifier; **no blanket deletion**.
Detail: `HPC_CLEANUP_RECLAIMED_SPACE.md`, `HPC_CLEANUP_EXECUTED.csv`.

* removed **359 superseded full checkpoints = 128.82 GiB**
* retained **294 (67.32 GiB)** that failed a guard — `PROTECTED_UNCERTAIN`
* **scratch 414 GB → 285 GB; grace `expired` → `none`**

---

## 4. What this session did NOT do

Stated plainly so nothing is overclaimed:

* did **not** submit any Slurm job — the corrected chain was already running;
* did **not** issue a Tier-1 reproduction verdict — the pilot is incomplete;
* did **not** run R1-C, Tier-2, Tier-3, the historical 1025-row replacement,
  the 4-vs-4 re-score, or generate the replacement DOCX;
* did **not** touch F1, the original Chinese DOCX, the author repository, or any
  `PROTECTED_REQUIRED` asset;
* did **not** delete anything in `CHATTIME`, `a0_replay`, `clean14`, or the
  294 unproven checkpoints.