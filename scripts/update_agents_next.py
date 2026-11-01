"""Replace the stale item 6 of AGENTS.md section 1 with the current state + tomorrow's plan.

Uses Python's own UTF-8 handling end to end (no PowerShell text round-trip), because a
PowerShell `Set-Content -Encoding UTF8` round-trip mangled this file earlier tonight
(section signs and middle dots became mojibake). Writes atomically and keeps a backup.
"""
from __future__ import annotations

import io
import os
import shutil
import time

PATH = r"C:\Users\Asus\Desktop\FYP code\MLFlu\AGENTS.md"

OLD_MARKER = "6. **The MIFlu benchmark row is NOT merged yet**"

NEW = (
    "6. **MIFlu row 31/40 verified (02:23); the LLM lane is wired end-to-end but 0 LLM cell is "
    "measured.** Overnight: `720105` P0 MIFlu (stingy), `720106` Qwen P1 (gpu_a100), `720052` "
    "single writer (tiny), `720107` successor watcher (tiny - submits a `P1 P2` lane when P0 "
    "ends, cutoff 07:00). Weights are local for **10 arms** (8 OK + two 1.5B); `llm_cell` TODO "
    "**132** / BLOCKED 36; revisions pinned; `local_snapshot()` handles the two HF cache "
    "layouts. **NEXT SESSION, in this order: (1) `ls author_runs/.miflu_verify | wc -l` -> if "
    "40, re-run `verify_miflu_oracle.py` then the analysis chain so the MIFlu row becomes "
    "quotable; (2) `tail code/queue/successor.log` + `grep DONE code/queue/queue_state.tsv` to "
    "prove whether any LLM cell actually ran, and if not, why; (3) run **Table VI regional, "
    "MIFlu only (21 cells, ~1 A100-h)** - the best value per GPU hour available; (4) "
    "`make_llm_lanes.py` then the 10 OK arms' 12-cell lanes; (5) rolling origin LAST "
    "(120-270 A100-h).** `docs/WORK_BREAKDOWN.md` 7 + `docs/PROGRESS_GATE.md`."
)


def main() -> int:
    raw = io.open(PATH, encoding="utf-8").read()
    lines = raw.splitlines(keepends=True)
    hit = None
    for i, ln in enumerate(lines):
        if ln.startswith(OLD_MARKER):
            hit = i
            break
    if hit is None:
        print("MARKER NOT FOUND - item 6 already updated or reworded; nothing written")
        return 0
    print(f"replacing line {hit + 1} ({len(lines[hit])} chars) with {len(NEW)} chars")
    old = lines[hit]
    # preserve the trailing newline style of the original line
    nl = "\n" if old.endswith("\n") else ""
    lines[hit] = NEW + nl
    shutil.copy2(PATH, PATH + ".bak." + time.strftime("%Y%m%dT%H%M%S"))
    tmp = PATH + ".tmp"
    io.open(tmp, "w", encoding="utf-8", newline="").write("".join(lines))
    os.replace(tmp, PATH)
    out = io.open(PATH, encoding="utf-8").read()
    print("bytes:", len(out.encode("utf-8")))
    print("section signs:", out.count("\u00a7"), "mojibake:", out.count("\u79ae"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
