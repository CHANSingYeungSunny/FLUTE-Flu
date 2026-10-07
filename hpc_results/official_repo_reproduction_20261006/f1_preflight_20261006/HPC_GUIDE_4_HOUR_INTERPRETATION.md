# HPC GUIDE — "4 HOURS" INTERPRETATION

Generated 2026-10-06. Source: `HPC_GUIDE.md` (working-tree copy, 22,651 bytes, mtime 2026-09-01 18:32).
Note: `git status` shows `D HPC_GUIDE.md` (the tracked copy deleted) **and** `?? HPC_GUIDE.md`
(a new untracked file with the same name). Both were read; the working-tree copy is quoted below.

---

## 1. Relevant section, quoted verbatim

`HPC_GUIDE.md`, **§3 Partition Policy**, table and hard rule:

```
| Partition  | GPU                | Wall limit                | Notes |
| `gpu_a100` | A100-40G           | up to 12h                 | Usually fully allocated ... |
| `stingy`   | mixed (incl. gpu-a100-03~06) | QOS-capped at 04:00:00 | Often has idle A100s → faster start. Use this by default. |
```

> **HARD RULE — `stingy` QOS wall-clock cap = `04:00:00` (4h).** Submitting with
> `--time=12:00:00` (or any value > 4h) FAILS immediately with
> `QOSMaxWallDurationPerJobLimit` (`sbatch` rejects before the job even queues). Always
> set `--time=04:00:00` (or lower: `02:00:00`, `01:00:00`). The full ILI walk-forward job
> runs in <30 min, so 4h is ample headroom. **Never write a `--time` larger than 04:00:00
> on `stingy`.** (If you genuinely need >4h, use `#SBATCH --partition=gpu_a100` instead —
> but expect a long `PD` wait since it is usually fully allocated.)

*(`HPC_GUIDE.md` §3, immediately after the partition table.)*

---

## 2. What "4 hours" means

| Candidate meaning | Is it this? | Evidence |
|---|---|---|
| 4 total project GPU-hours | ❌ **no** | the text says "wall-clock cap" and names `--time`, a wall-clock flag |
| 4 GPU-hours per student | ❌ no | no per-student allocation is mentioned anywhere in the guide |
| 4 GPU-hours per week | ❌ no | no periodicity is mentioned |
| **maximum wall time per Slurm job** | ✅ **YES** | "*`stingy` QOS wall-clock cap = `04:00:00`*"; the failure mode quoted is `QOSMaxWallDurationPerJobLimit`, which is a **per-job** limit |
| recommended request size | ❌ no | the guide advises *smaller* values (`02:00:00`, `01:00:00`) |
| supervisor-approved experiment budget | ❌ no | the guide never mentions a supervisor or a project budget |

**Answer: it is the maximum wall-clock time of a single Slurm job on `stingy`.**

Three independent confirmations inside the same paragraph:

1. it is described as a **wall-clock** cap;
2. the enforcing error is `QOSMaxWallDurationPerJobLimit` — a *per-job* limit;
3. the remedy offered for needing more is to **change partition** (`gpu_a100`, 12h), which
   only makes sense for a per-job limit — a GPU-hour budget could not be escaped by
   changing partition.

---

## 3. Live verification — and a discrepancy with the guide

Queried on 2026-10-06 with lightweight `sacctmgr`/`scontrol` commands:

```
sacctmgr show qos partition-stingy format=Name,MaxWall,MaxTRES,MaxTRESMins,GrpTRESMins,MaxSubmitJobs,MaxJobsPU
-> partition-stingy | MaxWall=06:00:00 | MaxTRESMins=cpu=46080,gres/gpu=2880 | GrpTRESMins=(empty) | MaxSubmit=1 | MaxJobsPU=1

scontrol show partition stingy
-> MaxTime=UNLIMITED ; QoS=partition-stingy
```

| Field | Guide says | Live says | Note |
|---|---|---|---|
| `MaxWall` (stingy QOS) | 04:00:00 | **06:00:00** | **the guide is out of date**; the cap has been raised to 6h |
| `MaxTRESMins` | not mentioned | `cpu=46080, gres/gpu=2880` | **2880 GPU-minutes = 48 GPU-hours — per JOB** |
| `GrpTRESMins` | not mentioned | **empty** | no group-level GPU-minute budget |
| `MaxSubmitJobs` / `MaxJobsPU` | 1 / 1 | 1 / 1 | agrees with the guide (§3b) |

**Two consequences:**

1. **"4 hours" is even less of a GPU-hour budget than it looks** — the live per-job wall
   cap is 6h, and the per-job GPU-minute ceiling is 48 GPU-h. Both are **per-job**
   ceilings. Neither is a spending allowance.
2. **Neither figure is 4 GPU-hours.** No HPC field anywhere equals 4 GPU-hours.

---

## 4. Is there any HPC-level GPU budget at all?

No. Checked exhaustively with lightweight commands:

| Level | Field | Value |
|---|---|---|
| partition `stingy` QoS | `GrpTRESMins` | **empty** |
| partition `stingy` QoS | `MaxTRESMins` | per-job only (2880 GPU-min) |
| account `ga_bms_kkhchan` | `GrpTRES`, `GrpTRESMins` | **empty** |
| user association `sychan552` | `GrpTRESMins`, `GrpTRESRunMins`, `MaxTRES`, `MaxTRESMins`, `MaxJobs`, `MaxSubmit` | **all empty** |
| QOS held by the account | `normal` | **no MaxTRESMins, no GrpTRESMins** |
| other QOS (`fyp`, `vip`, `partition-*`) | exist, but the account **does not hold them** | `sacctmgr show assoc user=sychan552` returns only `ga_bms_kkhchan | normal` |
| live job accounting | QOS actually used | `normal` |

**The account has no GPU-minute allocation of any kind.** GPU consumption is limited only
by per-job wall time, per-job TRES-minutes, and concurrency — never by a cumulative
project budget.

---

## 5. The explicit non-equivalence the brief warns about

> Do not assume that a four-hour job time limit equals a four-GPU-hour research budget.

Confirmed: they are **not** equivalent, and here the distinction is larger than the brief
supposes, because:

- the live per-job wall cap is **6h**, not 4h;
- the per-job GPU-minute cap is **48 GPU-h**, not 4;
- **no** cumulative GPU-hour budget exists at the HPC level at all.

The 4h figure in the guide is a **submission parameter** (`--time=04:00:00`), not a
resource budget.

---

## 6. Conclusion

```
4 HOURS  ==  MAXIMUM WALL-CLOCK TIME OF ONE SLURM JOB ON THE stingy PARTITION
             (guide: 04:00:00; live QoS: 06:00:00)
```

It confers **no** GPU-hour allowance. It cannot be reinterpreted as available quota.