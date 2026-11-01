# PROGRESS GATE — the context-loss prevention contract

**What this is.** A mandatory, per-turn checklist that forces every agent to write its
progress into the project's memory **before the turn ends**. It exists because long agent
runs lose state at context-window boundaries: when the window is exhausted, whatever was
only in the conversation is gone. `AGENTS.md` `R2` already *asks* for this; this file makes
it **checkable**.

**When to read it.** Every session, immediately after `AGENTS.md` `R1`. And again before
ending any turn that produced a number, a file, a decision, a failure or an exclusion.

**What it points to.** `AGENTS.md` (protocol), `docs/STATE.md` (current truth),
`docs/LEDGER.md` (append-only history), `docs/WORK_BREAKDOWN.md` (§11 done / §13 status),
`docs/HPC_RUNBOOK.md` (cluster operations), `scripts/check_progress_gate.py` (the checker).

**Depends on.** Nothing. It is pure process.

**Chain.** `AGENTS.md` → this file → `docs/STATE.md` → `docs/LEDGER.md` → the evidence file
named in the row.

---

## 1. THE FIVE WRITES — a turn is INCOMPLETE without them

Every turn that changes anything must land **all five**, in this order of importance:

| # | File | What must change | Failure mode it prevents |
|---|---|---|---|
| 1 | **`docs/LEDGER.md`** | append **one dated row**: what changed, the measured evidence, the file/path | "we did something and nobody knows" |
| 2 | **`docs/STATE.md` §1** | the headline numbers, if any changed | stale numbers quoted as current |
| 3 | **`docs/WORK_BREAKDOWN.md` §13** | the status of every item the turn touched (`✅ / 🟡 / ❌` + why) | "is X done?" answered from memory |
| 4 | **`docs/HPC_RUNBOOK.md`** | only if an **operational** fact changed (partition, QOS, a new gotcha, a wrong claim corrected) | repeating a mistake that cost hours |
| 5 | **`AGENTS.md`** | only if the **10-line headline state** changed; keep the file **< 20 KB** | exceeding the harness's 65536-byte injection budget |

**Never** rewrite history (`R3`): superseded numbers go to the ledger with a date and a
reason; do not silently replace them in `STATE.md`.

## 2. TURN-CLOSE CHECKLIST — copy this into your reasoning before you answer

```
[ ] Did this turn produce a NEW number, file, decision, failure, or exclusion?
    NO  -> the turn is read-only; say so and stop. No writes required.
    YES -> continue.
[ ] LEDGER.md has a new dated row, and it names the evidence (command output or path)?
[ ] STATE.md §1 headline numbers updated, if they moved?
[ ] WORK_BREAKDOWN.md §13 rows updated for every item touched?
[ ] HPC_RUNBOOK.md updated, if an operational fact changed or a wrong one was corrected?
[ ] AGENTS.md headline updated only if the 10-line state moved — and still < 20 KB?
[ ] Any claim marked ✅ has an artefact on disk AND a command that reproduces it (R4)?
[ ] Could a fresh agent, reading only these files, continue without asking a question?
```

## 3. THE CHECKER — make freshness machine-verifiable

`python scripts/check_progress_gate.py` must exit non-zero if any of these fail:

1. `docs/LEDGER.md`'s **last dated row is today** (or the last turn had no state change,
   declared explicitly).
2. `docs/STATE.md` mtime is **not older than** `docs/LEDGER.md` mtime (state trails history).
3. `docs/WORK_BREAKDOWN.md` mentions every job id / file that the latest ledger row names.
4. `AGENTS.md` is **< 20 000 bytes**.
5. No `TODO`/`FIXME`/`PLACEHOLDER` survives in a file the ledger row claims is `✅`.

Run it as the last command of a turn that changed state. It is the mechanical backstop for
the checklist above.

## 4. RECOVERY — what to do when you inherit an unfinished state

The recovery order is deliberately the *reverse* of the write order, because you need the
newest facts first:

1. `docs/LEDGER.md` — **tail it**. The last few rows are the truth about "what was happening
   when the previous agent ran out of context", including what it intended to do next.
2. `docs/STATE.md` §1 — the headline numbers as of the last successful write.
3. `docs/WORK_BREAKDOWN.md` §13 — what is `✅` vs `🟡` vs `❌`, and the note explaining each.
4. `docs/HPC_RUNBOOK.md` — the operational facts you must not re-learn the hard way.
5. Only then, the cluster itself: `sacct` / `scontrol` (never `squeue` — see the runbook).

**A ledger row must always answer three questions**, or it is not a usable row:
*what changed*, *how it was verified*, and *what the next agent should do next*.

## 5. WHY THIS EXISTS — two concrete failures from 2026-11-01

Both cost real time and both were caused by state living only in a conversation:

- A `find_ckpt` trust-order bug exported one cell from another seed's weights. The wrong
  conclusion ("the old CSV is the outlier") was reached, recorded nowhere, and later had to
  be discovered again and reversed. A ledger row with the manifest sha would have caught it.
- Three agents wrote the same queue files concurrently (`master_task.py` 19 260 → 28 722
  bytes while a second agent edited it). Nothing recorded **who owned which file**, so the
  collision repeated. `docs/LEDGER.md` now carries an explicit ownership row per handover.

The lesson: **on-disk memory is the only memory that survives a context boundary.** Write
it before you answer, not after you are asked.
