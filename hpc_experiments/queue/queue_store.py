#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""queue_store.py -- the one atomic, lock-protected accessor for `master_queue.tsv`.

Two controllers (one per partition) plus a CPU probe job can all write the queue
at the same time, so every mutation goes through a single `flock`-protected
read-modify-write with the result `os.replace`d into place. The lock file is
shared with the bash controller (`flock 200`), so the two write paths exclude
each other.

COLUMNS (11, queue v2)
----------------------
task_id  kind  model  L  seed  priority  env  state  attempts  last_job  note

`env` is explicit and is the AUTHORITATIVE interpreter choice for the row
(Gap 2): `hpc` -> /home/sychan552/.conda/envs/mlflu_hpc/bin/python,
`llm` -> /home/sychan552/.venvs/mlflu_llm/bin/python. A row whose env binary is
absent becomes SKIPPED `env-missing` and is never retried.

States
------
TODO                     runnable now
RUNNING                  a controller has claimed it (reset to TODO on restart)
DONE                     artefact exists and passes its gate
FAILED                   terminal failure (not-a100, NaN, ...)
SKIPPED                  will never be attempted again; reason in `note`
BLOCKED_MISSING_WEIGHTS  cannot run until the CPU probe downloaded + pinned it
DEFERRED_COST            dropped by the Gap-3 cost projection, arithmetic in `note`
"""
from __future__ import annotations

import fcntl
import os
import time

QUEUE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(QUEUE_DIR, "master_queue.tsv")
LOCK = os.path.join(QUEUE_DIR, ".queue.lock")
EVENTS = os.path.join(QUEUE_DIR, "queue_events.log")
COLUMNS = ["task_id", "kind", "model", "L", "seed", "priority", "env",
           "state", "attempts", "last_job", "note"]
IDX = {c: i for i, c in enumerate(COLUMNS)}

#: states that still count as "work to do" for the watchdog / termination tests
PENDING_STATES = ("TODO", "RUNNING", "BLOCKED_MISSING_WEIGHTS")
#: states that mean "this task will never run again"
TERMINAL_STATES = ("DONE", "FAILED", "SKIPPED", "DEFERRED_COST")


class locked:
    """Exclusive advisory lock shared with the bash controller."""

    def __enter__(self):
        self.fh = open(LOCK, "a+")
        fcntl.flock(self.fh, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.fh, fcntl.LOCK_UN)
        self.fh.close()
        return False


def read_rows() -> list:
    with open(QUEUE, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    rows = []
    for i, line in enumerate(lines):
        if i == 0:
            continue
        f = line.split("\t")
        if len(f) == len(COLUMNS):
            rows.append(f)
    return rows


def write_rows(rows: list) -> None:
    tmp = QUEUE + ".tmp.%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(COLUMNS) + "\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    os.replace(tmp, QUEUE)


def update(rows_by_id: dict) -> None:
    """Apply {task_id: {column: value}} under the lock."""
    with locked():
        rows = read_rows()
        for r in rows:
            chg = rows_by_id.get(r[0])
            if not chg:
                continue
            for k, v in chg.items():
                r[IDX[k]] = str(v)
        write_rows(rows)


def set_state(task_id: str, state: str, note: str = None, last_job: str = None) -> None:
    chg = {"state": state}
    if note is not None:
        chg["note"] = note
    if last_job is not None:
        chg["last_job"] = last_job
    update({task_id: chg})
    event("%s -> %s%s" % (task_id, state, " (%s)" % note if note else ""))


def set_env(task_id: str, env: str, note: str = None) -> None:
    """Record the env that actually worked (arch fallback), keeping the queue honest."""
    chg = {"env": env}
    if note is not None:
        chg["note"] = note
    update({task_id: chg})
    event("%s env -> %s%s" % (task_id, env, " (%s)" % note if note else ""))


def event(msg: str) -> None:
    line = "[%s] %s\n" % (time.strftime("%F %T"), msg)
    with open(EVENTS, "a", encoding="utf-8") as fh:
        fh.write(line)


def unblock_model(model_id: str, new_state: str, reason: str) -> int:
    """Flip a model's 12 BLOCKED_MISSING_WEIGHTS cells after the CPU probe.

    new_state="TODO"    -> weights local, revision pinned, hidden-state read-out
                           proven: the cells become runnable.
    new_state="SKIPPED" -> the model cannot be an arm (measured): the cells are
                           SKIPPED with the reason, never left as TODO.
    """
    assert new_state in ("TODO", "SKIPPED"), new_state
    with locked():
        rows = read_rows()
        n = 0
        for r in rows:
            if r[1] != "llm_cell" or r[2] != model_id:
                continue
            if r[IDX["state"]] != "BLOCKED_MISSING_WEIGHTS":
                continue
            r[IDX["state"]] = new_state
            r[IDX["note"]] = reason
            n += 1
        write_rows(rows)
    event("unblock_model %s: %d cells -> %s (%s)" % (model_id, n, new_state, reason))
    return n


def rearm_finalise(why: str) -> int:
    """Put the P4 finalisation tasks back to TODO after new cells landed.

    They are idempotent: each compares the on-disk cell signature with the last
    run and does nothing when it has not changed, so re-arming costs ~1 s when
    there is no new data and rebuilds every table when there is.
    """
    with locked():
        rows = read_rows()
        n = 0
        for r in rows:
            if r[1] in FINALISE_KINDS and r[IDX["state"]] == "DONE":
                r[IDX["state"]] = "TODO"
                r[IDX["note"]] = "re-armed after %s" % why
                n += 1
        write_rows(rows)
    if n:
        event("re-armed %d finalise rows after %s" % (n, why))
    return n


#: every finalisation kind the controller knows (F1-F5 plus the v1 alias)
FINALISE_KINDS = ("f1_import_miflu", "f2_miflu_oracle", "f3_analysis_chain",
                  "f4_verify", "f5_llm_import", "finalise")


def defer_arm(model_id: str, reason: str) -> int:
    """Mark an arm's not-yet-run cells DEFERRED_COST (never touches DONE/RUNNING)."""
    with locked():
        rows = read_rows()
        n = 0
        for r in rows:
            if r[1] != "llm_cell" or r[2] != model_id:
                continue
            if r[IDX["state"]] not in ("TODO", "BLOCKED_MISSING_WEIGHTS"):
                continue
            r[IDX["state"]] = "DEFERRED_COST"
            r[IDX["note"]] = reason
            n += 1
        write_rows(rows)
    event("defer_arm %s: %d cells -> DEFERRED_COST (%s)" % (model_id, n, reason))
    return n


def readmit_deferred(model_id: str, reason: str) -> int:
    """Reverse a deferral when the allocation turns out to be big enough.

    A def tumour must never be a silent permanent drop: this is the documented
    way back, and it is logged like the deferral itself.
    """
    with locked():
        rows = read_rows()
        n = 0
        for r in rows:
            if r[1] != "llm_cell" or r[2] != model_id:
                continue
            if r[IDX["state"]] != "DEFERRED_COST":
                continue
            r[IDX["state"]] = "TODO"
            r[IDX["note"]] = "re-admitted: %s" % reason
            n += 1
        write_rows(rows)
    if n:
        event("readmit_deferred %s: %d cells -> TODO (%s)" % (model_id, n, reason))
    return n


def state_of(task_id: str, default=None):
    for r in read_rows():
        if r[0] == task_id:
            return r[IDX["state"]]
    return default


def get(task_id: str):
    for r in read_rows():
        if r[0] == task_id:
            return dict(zip(COLUMNS, r))
    return None


def counts() -> dict:
    out = {}
    for r in read_rows():
        st = r[IDX["state"]]
        out[st] = out.get(st, 0) + 1
    return out


def pending_count() -> int:
    """Rows that are not in a terminal state (what the watchdog watches)."""
    return sum(n for st, n in counts().items() if st not in TERMINAL_STATES)
