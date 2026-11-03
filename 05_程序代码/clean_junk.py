# -*- coding: utf-8 -*-
"""Remove scratch output older than a cutoff, with the project's never-delete list enforced.

This is the executable form of the rule in `docs/REPO_HYGIENE.md`:

    remove  _*.out  _*.err  *.tmp  *.bak.*   older than 24 h,
    from the repo root and any non-source location,

and never touch `hpc_results/**`, `expanded_runs/**`, `paper_tables/*.csv`, `docs/**`,
`scripts/**`, or any `pred_*.npz`.

Default is REPORT ONLY. Pass `--apply` to delete, `--hours N` to change the cutoff.

    python scripts/clean_junk.py                 # report
    python scripts/clean_junk.py --apply         # delete
    python scripts/clean_junk.py --hours 0 --apply   # everything matching, regardless of age
"""
from __future__ import annotations

import argparse
import os
import time
from fnmatch import fnmatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATTERNS = ("_*.out", "_*.err", "*.tmp", "*.bak.*")
PROTECTED_DIRS = ("03_预测数据_证据", "expanded_runs", "02_数字表格", "04_详细说明文档", "05_程序代码",
                  ".git", ".quarantine", "reference_papers")
NEVER_DELETE = ("pred_",)


def is_protected(rel: str) -> bool:
    parts = rel.replace("\\", "/").split("/")
    if parts[0] in PROTECTED_DIRS:
        return True
    return any(p in ("checkpoints", "node_modules", "__pycache__") for p in parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--hours", type=float, default=24.0)
    a = ap.parse_args()
    cutoff = time.time() - a.hours * 3600

    hits, kept_young, protected = [], 0, 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
        for fn in filenames:
            if not any(fnmatch(fn, p) for p in PATTERNS):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT)
            if is_protected(rel) or any(fn.startswith(p) for p in NEVER_DELETE):
                protected += 1
                continue
            if os.path.getmtime(full) >= cutoff:
                kept_young += 1
                continue
            hits.append((rel, os.path.getsize(full)))

    total = sum(s for _, s in hits)
    print(f"root            : {ROOT}")
    print(f"cutoff          : {a.hours:g} h  ({time.strftime('%Y-%m-%d %H:%M', time.localtime(cutoff))})")
    print(f"matched patterns: {len(hits) + kept_young + protected}")
    print(f"  too young     : {kept_young}  (kept: a running job may still be writing them)")
    print(f"  protected     : {protected}")
    print(f"  deletable     : {len(hits)}  ({total / 1024:.1f} KiB)")
    for rel, size in sorted(hits)[:40]:
        print(f"    {size:>9,}  {rel}")
    if len(hits) > 40:
        print(f"    ... and {len(hits) - 40} more")

    if not a.apply:
        print("\nREPORT ONLY. Re-run with --apply to delete.")
        return 0
    removed = 0
    for rel, _ in hits:
        try:
            os.remove(os.path.join(ROOT, rel))
            removed += 1
        except OSError as exc:                     # pragma: no cover
            print(f"  FAILED {rel}: {exc}")
    print(f"\nremoved {removed} file(s), {total / 1024:.1f} KiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
