# F1 BUDGET RECALCULATION

Generated 2026-10-06. Companion to `GPU_BUDGET_AUTHORITY_AUDIT.md`.

---

## 1. The premise of the requested recalculation does not hold

The brief asks: *"**If** the guide and authorization establish a total 4.0 GPU-hour budget,
recalculate …"*

**They do not establish one.** Verified in `GPU_BUDGET_AUTHORITY_AUDIT.md`:

| Source | What it actually establishes |
|---|---|
| `HPC_GUIDE.md` §3 | a **per-job wall-clock** cap (04:00:00 per the guide; **06:00:00** live) — **no** GPU-hour budget |
| the authorization document | a **2.3 GPU-hour incremental** grant — **not 4.0** |
| Slurm / QOS / account / user | **no GPU-minute allocation at any level** |
| supervisor | **no cap exists** — one was recommended (`EE4020…Recovery_Plan.md` L360), never set |

So the requested figures are presented below **explicitly as a hypothetical scenario**.
Presenting them as an authorized budget would be false, and could lead to spending that
no one approved.

---

## 2. The hypothetical 4.0 GPU-hour scenario (NOT AUTHORIZED)

Reproducing the arithmetic exactly as the brief specifies, **labelled hypothetical**:

| Item | Value (GPU-h) |
|---|---:|
| total authorized budget *(hypothetical)* | 4.00000 |
| consumed (verified) | 2.24361 |
| actual remaining *(hypothetical)* | **1.75639** |
| F1 base estimate | 0.42664 |
| F1 10 % estimate | 0.46930 |
| F1 20 % estimate | 0.51197 |
| proposed F1 hard cap | 0.60000 |
| remaining after reserving 0.60 | **1.15639** |

**Under this scenario F1 would fit comfortably**, with 1.16 GPU-h left for F2 or a second
pilot. **But the scenario is not authorized**, so these numbers must not be used as a
spending basis.

---

## 3. The actual position

| Item | Value (GPU-h) |
|---|---:|
| **authorized and unspent** | **0.05639** |
| F1 base estimate | 0.42664 |
| F1 10 % estimate | 0.46930 |
| F1 20 % estimate | 0.51197 |
| proposed F1 hard cap | 0.60000 |
| **shortfall against the base estimate** | **0.37025** |
| **shortfall against the proposed cap** | **0.54361** |

**F1 cannot be submitted from the current position.**

What 0.05639 GPU-h would buy: roughly **one** MIFlu fit (0.0533 GPU-h) — i.e. one arm at
one horizon out of the eight GPU fits F1 needs. Even a single model across all four
horizons (4 × 0.0533 = 0.2133) does not fit.

---

## 4. Where the 4.0 figure could have come from — and why it is wrong

| Plausible source of "4" | Reality |
|---|---|
| the guide's 4-hour wall cap | a **per-job wall-clock** limit, not GPU-hours |
| 2.0 (A2) + 2.0 (a supposed second round) | the second round was granted as **2.3**, not 2.0 |
| 2.0 (A2 cap) + 2.3 (Stage-6 cap) = 4.3 | arithmetically true, but the 2.3 grant **explicitly forbids** combining with the earlier remainder |
| the A2 remainder 0.8464 added to 2.3 = 3.1464 | **explicitly prohibited** by the grant: "不能与旧 A2 的 0.8464 余额相加成为 3.1464" |
| a misreading of `MaxTRESMins gres/gpu=2880` | that is **2880 GPU-minutes = 48 GPU-hours, per job** |

**No path yields a 4.0 GPU-hour budget.** The nearest real numbers are 2.0 and 2.3, and
the grant itself forbids adding them.

---

## 5. If the user wants the 4.0 scenario to become real

That requires a **new user decision**, not a reinterpretation. Options:

| Option | What it means | F1 covered? |
|---|---|---|
| **Grant 0.60 GPU-h for F1** | the amount F1 actually needs | ✅ yes, with a 20 % buffer |
| Grant 1.16 GPU-h | F1 + room for F2 (three seeds) | ✅ yes, plus the next step |
| Declare the budget to be 4.0 GPU-h total | makes the historical 2.0 + 2.3 non-additivity rule moot, and releases 1.75639 | ✅ yes, generously |
| Keep the present position | 0.05639 remains | ❌ no |

**Recommendation: grant 0.60 GPU-h for F1** — the smallest decision that unblocks the
pilot, with a stated 20 % buffer. If the three-seed stage is likely to follow soon,
1.16 GPU-h is the more efficient single decision because it avoids a second approval.

---

## 6. What this document does NOT do

- It does **not** reinterpret "4 hours" as quota. `HPC_GUIDE_4_HOUR_INTERPRETATION.md`
  shows the 4h is a per-job wall-clock cap.
- It does **not** claim the 2.3 is an HPC limit; it is a user grant.
- It does **not** submit, queue, or reserve anything.
- It does **not** modify any previous budget statement. The earlier reports continue to
  say "2.3 GPU-h cap"; this document corrects the **provenance** of that number (user
  grant, not HPC rule) without editing them.

---

## 7. One-line answer

> **The 4.0 GPU-hour budget does not exist. The real authorized position is 0.05639 GPU-h
> unspent against a user-granted 2.3 GPU-h round cap. F1 needs 0.43–0.60 GPU-h, so it
> requires a new user grant of ~0.60 GPU-h before it can be submitted.**