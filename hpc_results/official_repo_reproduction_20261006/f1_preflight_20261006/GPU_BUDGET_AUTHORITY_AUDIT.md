# GPU BUDGET AUTHORITY AUDIT

Generated 2026-10-06. **Read-only audit. No GPU job was submitted, nothing was deleted
or modified.**

# VERDICT: `FOUR_HOURS_IS_JOB_WALLTIME_ONLY`

with a second, independent finding: **the 2.3 GPU-hour figure is a user instruction, not
an HPC limit, and it is a round-scoped incremental grant that is now essentially spent.**

---

## 1. Exact origin of the 2.3 GPU-hour figure

**Source: a user instruction.** Verbatim from
`CodeBuddy_Authorization_and_Final_Execution_ZH.md`, line 11:

> 用户已查看以下具体申请并指示继续直至完成。本指令批准**新增累计最多 2.3 GPU-hours**，分别计划
> A0 最小发布代码诊断 **0.5 GPU-hours**、作者数据八模型比较剩余 72 次拟合及评分 **1.8 GPU-hours**。
> 两个子额度用于排程控制；如一支实际少用，可在总额 2.3 内用于另一支的同一已批准任务，但不得增加
> 模型、种子、预测长度或新实验。**2.3 是所有新增分配的硬上限，不能与旧 A2 的 0.8464 余额相加成为
> 3.1464。**

Translated precisely:

| Element | Content |
|---|---|
| Who granted it | **the user** ("用户已查看…并指示继续直至完成") |
| What it is | a **new incremental** cap ("**新增**累计最多 2.3 GPU-hours") |
| Composition | A0 minimal released-code diagnostic **0.5** + author-data eight-model remaining 72 fits and scoring **1.8** |
| Scope of the sub-budgets | "排程控制" — scheduling control; unused headroom in one may be used for the other's **already-approved** task |
| Explicit prohibition | may **not** add models, seeds, prediction lengths or new experiments |
| Explicit non-additivity | "**不能与旧 A2 的 0.8464 余额相加成为 3.1464**" |

### Classification of the origin

| Candidate origin | Is it the source? |
|---|---|
| **user instruction** | ✅ **YES** |
| recovery plan | ❌ no — the plan proposes a *matrix*, not this number; it says only "set a supervisor-approved GPU-hour cap" (`EE4080_MIFlu_Research_Recovery_Plan.md` L360) |
| previous report | ❌ no — reports *quote* 2.3, they do not create it |
| **supervisor-approved cap** | ❌ **no — and this matters**: no supervisor-approved cap exists in any artifact. `recovery/STATE.md` L177 records D-compute as "**GRANTED by user**", not by the supervisor |
| HPC guide | ❌ no — the guide contains no GPU-hour budget at all (`HPC_GUIDE_4_HOUR_INTERPRETATION.md`) |
| Slurm/QOS constraint | ❌ **no** — see §3; the account has no GPU-minute allocation |
| conservative self-imposed stopping rule | ❌ no — it was user-granted, not self-imposed |

**Answer: the 2.3 is a user-granted, round-scoped, incremental authorization.**

---

## 2. Exact meaning of "4 hours"

**`HPC_GUIDE.md` §3**: the `stingy` **QOS wall-clock cap per job** (`04:00:00`), enforced
by `QOSMaxWallDurationPerJobLimit`.

Full analysis: `HPC_GUIDE_4_HOUR_INTERPRETATION.md`.

**Live correction**: the stingy QOS `MaxWall` is now **06:00:00**, not 04:00:00 — the
guide is out of date. Either way it is a **per-job wall-clock** limit, and neither value
is a GPU-hour budget.

---

## 3. Live Slurm / QOS / account limits

Queried 2026-10-06 with lightweight commands.

| Level | Field | Value | Is it a GPU-hour budget? |
|---|---|---|---|
| QoS `partition-stingy` | `MaxWall` | **06:00:00** | ❌ per-job wall |
| QoS `partition-stingy` | `MaxTRESMins` | `cpu=46080, gres/gpu=**2880**` | ❌ per-**job** GPU-minutes = 48 GPU-h/job |
| QoS `partition-stingy` | `GrpTRESMins` | **empty** | — |
| QoS `partition-stingy` | `MaxSubmitJobs` / `MaxJobsPU` | 1 / 1 | ❌ concurrency |
| partition `stingy` | `MaxTime` | `UNLIMITED` (QoS is the binding limit) | — |
| account `ga_bms_kkhchan` | `GrpTRES`, `GrpTRESMins` | **empty** | — |
| user assoc `sychan552` | `GrpTRESMins`, `GrpTRESRunMins`, `MaxTRES`, `MaxTRESMins`, `MaxJobs`, `MaxSubmit` | **all empty** | — |
| QOS the account holds | — | **`normal` only** (no `MaxTRESMins`, no `GrpTRESMins`) | — |
| other QOS (`fyp`, `vip`, `partition-*`) | `gres/gpu=2880` etc. | exist, but **the account does not hold them** | — |
| live job accounting | QOS actually used by jobs 606365/606378/606385/606412 | **`normal`** | — |

**No field anywhere equals 4 GPU-hours. No cumulative GPU-hour allocation exists for this
account at any level.**

### The one place "2880" appears

`gres/gpu=2880` is **GPU-minutes**, i.e. **48 GPU-hours — but per JOB**, not per project.
It is a ceiling on a single job, and with `MaxWall=06:00:00` and 1 GPU per job the binding
constraint is the wall clock (6 GPU-h per job at most), never the TRES-minutes. **This is
a per-job ceiling, not a spending allowance.**

---

## 4. Preserved, independently verified usage

| Item | Value | Source |
|---|---:|---|
| consumed GPU-hours | **2.24361** | `postrun_audit_20261006/GPU_LEDGER_VERIFICATION.csv`, recalculated from live `sacct` |
| previous assumed cap | **2.3** | user instruction (above) |
| previously reported remaining | **0.05639** | 2.3 − 2.24361 |

### Decomposition of the 2.24361 (important, and worth stating plainly)

| Round | Cap | Used | Authority |
|---|---:|---:|---|
| Round 1 — A2 / stage 5 | **2.0** GPU-h | 1.1536 | user (D-compute, `recovery/STATE.md` L177) |
| Round 2 — Stage 6 (A0 + eight models) | **2.3** GPU-h **incremental** | 1.12555 | user instruction (this audit's source) |
| 2026-10-06 continuation (A100 text probe + four horizon runs) | charged against the Round-2 remainder | 1.11806 | see below |
| **Round 2 total charged** | 2.3 | **2.24361** | |
| **Round 2 remaining** | | **0.05639** | |

⚠️ **A scope observation that should be confirmed by the user.** The Round-2 grant named
A0 + the eight-model comparison. The 2026-10-06 continuation spent **1.11806 GPU-h** on a
text-path A100 probe and four horizon runs, which are *not* the named eight-model fits.
That spend was made under the user's later instruction to "把能够执行的复现、训练、评估…完成"
and to "自动提交在允许预算内的最大不重复 run", and the two rounds' ledgers were kept
separate as the grant required. **But the named scope and the actual spend differ, so the
user should confirm whether the continuation counts against Round 2.**

Either way the arithmetic is unchanged: **0.05639 GPU-h remains.**

---

## 5. Actual authorized total, and actual remaining

| Question | Answer |
|---|---|
| Is there an HPC-authorized total GPU-hour budget? | **No.** None exists at partition, QoS, account or user level. |
| What governs new GPU spending? | The **user's** round-scoped grants (2.0 for A2, then 2.3 incremental for Stage 6) |
| Total authorized across both rounds | 2.0 + 2.3 = 4.3 GPU-h, **but explicitly non-additive in accounting**: the 2.3 grant forbids combining with the A2 remainder (0.8464) |
| Consumed | **2.24361** against the Round-2 2.3 grant (Round 1's 1.1536 is closed against its own 2.0) |
| **Actual remaining** | **0.05639 GPU-h** |
| Supervisor-approved cap | **none exists** — `EE4080_MIFlu_Research_Recovery_Plan.md` L360 recommends setting one; it was never set |

---

## 6. The brief's conditional recalculation

The brief asks: *"If the guide and authorization establish a total 4.0 GPU-hour budget,
recalculate …"*

**They do not.** The guide establishes a 4h (now 6h) **per-job wall-clock** cap and no
GPU-hour budget; the authorization establishes a **2.3 incremental** grant. Neither is a
4.0 GPU-hour budget, and no combination of them yields one.

The requested arithmetic is therefore presented in `F1_BUDGET_RECALCULATION.md` **as an
explicitly labelled hypothetical**, not as an authorized figure — because writing it as
authorized would be false.

---

## 7. Can F1 be submitted without requesting additional quota?

**No.**

| | Value |
|---|---:|
| F1 base estimate | 0.42664 GPU-h |
| F1 with 10 % buffer | 0.46930 GPU-h |
| F1 with 20 % buffer | 0.51197 GPU-h |
| proposed F1 hard cap | 0.60 GPU-h |
| **actual remaining** | **0.05639 GPU-h** |
| **shortfall** | **0.37 – 0.54 GPU-h** |

The remaining 0.05639 GPU-h would cover roughly **one** MIFlu fit (0.0533 GPU-h) and
nothing else — not the eight GPU fits F1 requires, and not even one full model × four
horizons.

### What authorization is still required

> **A new user grant of GPU quota for the A2-F pilot.** Concretely: authorisation to
> spend up to **0.60 GPU-h** on Option F1, on `stingy`, ≤1 concurrent job, all output on
> `$HOME`.

No HPC-side approval is needed — the account has no allocation to exceed, and the per-job
limits (6h wall, 48 GPU-h TRES-minutes, 1 concurrent) are not binding for a 34-minute,
8-fit pilot. **The gate is purely the user's own budget decision**, because the only
budget that exists is the one the user granted.

---

## 8. Confirmations

| Confirmation | Evidence |
|---|---|
| **No GPU job was submitted** | no `sbatch` was invoked; `squeue -u $USER` empty |
| **No file was deleted or modified** | read-only inspection only; the 66-file hash snapshot remains 66/66 identical |
| **No login-node computation** | only `sacctmgr`, `scontrol`, `sinfo`, `sacct`, `grep`, `sed` — all explicitly permitted lightweight commands |