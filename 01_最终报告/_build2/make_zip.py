# -*- coding: utf-8 -*-
"""Build 01_最终报告/PROJECT_HANDOFF.zip and record what went in.

Exclusions (documented in deliverables/MANIFEST.md §6):
  required by the brief : .git/  __pycache__/  node_modules/  *.tmp  *.bak.*
                          deliverables/_build/
  added, with reasons   : checkpoints/            regenerable weights (5.0 GB)
                          .quarantine/            rejected artefacts (629 MB)
                          results/v3_clean/final, results/v3_clean/test_eval
                                                  >100 MB artefacts already git-ignored
                          _tmp_*/                 scratch staging
                          .pytest_cache/  old_wrong_reports/
                          deliverables/.dsh-office-*/   temporary page renders
                          deliverables/PROJECT_HANDOFF.zip (the archive itself)

Never excluded: hpc_results/, expanded_runs/, paper_tables/, docs/, scripts/,
deliverables/figures/.
"""
from __future__ import annotations

import json
import os
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dlv import data as D  # noqa: E402

ROOT = D.ROOT
OUT = os.path.join(ROOT, "01_最终报告", "PROJECT_HANDOFF.zip")
STATS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zip_stats.json")

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "checkpoints", ".quarantine",
                ".pytest_cache", "old_wrong_reports", "99_旧文件存档", ".codebuddy"}
EXCLUDE_PREFIXES = ("_tmp_", "_fix_", "_update_", "_chk", "_chkzip", "_gen_", "_add_", "_fin", "_make_", "_scan_", "_rename", "_verify_")
EXCLUDE_PATHS = {
    "01_最终报告/_build",
    "results/v3_clean/final",
    "results/v3_clean/test_eval",
}
EXCLUDE_GLOBS = (".tmp", ".bak")


def skip(rel: str) -> bool:
    parts = rel.replace("\\", "/").split("/")
    # any component, not just the top-level one: nested __pycache__/.pytest_cache
    # directories are created by test runs and must not enter the archive
    if any(p in EXCLUDE_DIRS for p in parts if p):
        return True
    if any(p.startswith(EXCLUDE_PREFIXES) for p in parts if p):
        return True
    if any(p.startswith(".dsh-office-") for p in parts):
        return True
    norm = "/".join(parts)
    if norm == "01_最终报告/PROJECT_HANDOFF.zip":
        return True
    if norm == "01_最终报告/CHATGPT_CONTEXT_PACK.zip":
        return True
    for p in EXCLUDE_PATHS:
        if norm == p or norm.startswith(p + "/"):
            return True
    name = parts[-1]
    if name.endswith(".tmp") or ".bak." in name or name.endswith(".bak"):
        return True
    return False


def main() -> int:
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = os.path.relpath(dirpath, ROOT)
        rel_dir = "" if rel_dir == "." else rel_dir.replace(os.sep, "/")
        dirnames[:] = sorted(d for d in dirnames
                             if not skip((rel_dir + "/" + d).strip("/")))
        for fn in sorted(filenames):
            rel = (rel_dir + "/" + fn).strip("/")
            if skip(rel):
                continue
            full = os.path.join(dirpath, fn)
            if os.path.getsize(full) > 0 or True:
                files.append((rel, full))

    t0 = time.time()
    if os.path.exists(OUT):
        os.remove(OUT)
    total_in = 0
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for rel, full in files:
            total_in += os.path.getsize(full)
            z.write(full, arcname=rel, compress_type=zipfile.ZIP_DEFLATED, compresslevel=1)
    dt = time.time() - t0
    size = os.path.getsize(OUT)

    with zipfile.ZipFile(OUT) as z:
        n = len(z.namelist())
        bad = z.testzip()

    tops = {}
    for rel, _ in files:
        tops[rel.split("/")[0]] = tops.get(rel.split("/")[0], 0) + 1

    stats = {
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "path": os.path.relpath(OUT, ROOT).replace(os.sep, "/"),
        "entries": n,
        "zip_bytes": size,
        "zip_mb": round(size / 1024 / 1024, 1),
        "input_bytes": total_in,
        "input_mb": round(total_in / 1024 / 1024, 1),
        "seconds": round(dt, 1),
        "crc_ok": bad is None,
        "excluded_dirs": sorted(EXCLUDE_DIRS) + ["_tmp_*", *sorted(EXCLUDE_PATHS)],
        "top_counts": tops,
    }
    with open(STATS, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=1)
    print(json.dumps(stats, indent=1))
    print("top-level entry counts:", dict(sorted(tops.items(), key=lambda kv: -kv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
