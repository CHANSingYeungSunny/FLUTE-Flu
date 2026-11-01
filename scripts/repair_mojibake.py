"""Repair files corrupted by a PowerShell Set-Content/Add-Content round-trip.

Symptom seen 2026-11-01: correct UTF-8 text was read with the wrong code page and
re-written, so non-ASCII characters became mojibake:
    U+00A7 SECTION SIGN  ->  U+79AE (禮)
    U+00B7 MIDDLE DOT    ->  U+7E5A (繚)
    U+2014 EM DASH       ->  '?' or '??'
    U+2013 EN DASH       ->  '?' or '??'
    U+2192 RIGHT ARROW   ->  '?'
The double-encoding is reversible when the bytes were merely mis-decoded as
cp936/gbk: text.encode('gbk').decode('utf-8') restores them. Where the bytes were
replaced by literal '?', the information is gone and we fall back to a heuristic
substitution, reporting exactly how many characters each strategy repaired.

Usage:
    python scripts/repair_mojibake.py --check           # report only
    python scripts/repair_mojibake.py --apply           # rewrite in place, with .bak
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

TARGETS = [
    "AGENTS.md",
    "docs/LEDGER.md",
    "docs/STATE.md",
    "docs/HPC_RUNBOOK.md",
    "docs/WORK_BREAKDOWN.md",
    "docs/PROGRESS_GATE.md",
]

SUSPECT = ("\u79ae", "\u7e5a", "??", "\ufffd")

# heuristic fallbacks for lossy '?' runs, only where they replaced a dash
FALLBACKS = [
    (" \ufffd\ufffd ", " \u2014 "),
    (" \ufffd ", " \u2014 "),
    (" \ufffd\ufffd", " \u2014"),
    ("\ufffd\ufffd ", "\u2014 "),
    ("\ufffd", "\u2014"),
    (" ?? ", " \u2014 "),
    (" ??", " \u2014"),
    ("?? ", "\u2014 "),
    ("\u79ae", "\u00a7"),
    ("\u7e5a", "\u00b7"),
]


def try_gbk_roundtrip(text: str) -> tuple[str, int]:
    """Undo a cp936 mis-decode. Returns (text, number_of_chars_changed)."""
    try:
        repaired = text.encode("gbk").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text, 0
    if repaired == text:
        return text, 0
    changed = sum(1 for a, b in zip(text, repaired) if a != b)
    return repaired, changed


def heuristic(text: str) -> tuple[str, int]:
    out = text
    fixed = 0
    for bad, good in FALLBACKS:
        n = out.count(bad)
        if n:
            out = out.replace(bad, good)
            fixed += n * len(bad)
    return out, fixed


def count_suspect(text: str) -> int:
    return sum(text.count(s) for s in SUSPECT)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, do not write")
    ap.add_argument("--apply", action="store_true", help="rewrite files in place")
    ap.add_argument("--root", default=".", help="project root")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    total_before = total_after = 0

    for rel in TARGETS:
        path = root / rel
        if not path.exists():
            print(f"{rel:32s} MISSING")
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            print(f"{rel:32s} NOT-UTF8 ({exc}); skipping")
            continue

        before = count_suspect(text)
        if before == 0:
            print(f"{rel:32s} clean ({len(raw)} B)")
            continue

        # strategy 1: reverse the cp936 mis-decode
        repaired, n1 = try_gbk_roundtrip(text)
        mid = count_suspect(repaired)
        # strategy 2: what the round-trip could not fix
        repaired2, n2 = heuristic(repaired)
        after = count_suspect(repaired2)

        total_before += before
        total_after += after
        print(
            f"{rel:32s} suspect {before:5d} -> {after:5d}"
            f"  (gbk-roundtrip fixed {n1}, heuristic fixed {n2})"
        )

        if args.apply:
            if after >= before:
                print(f"{rel:32s}  no improvement; leaving untouched")
                continue
            shutil.copy2(path, path.with_suffix(path.suffix + ".mojibake.bak"))
            path.write_bytes(repaired2.encode("utf-8"))
            print(f"{rel:32s}  rewritten ({len(repaired2.encode('utf-8'))} B), .bak kept")

    print(f"\nTOTAL suspect characters: {total_before} -> {total_after}")
    if args.apply:
        print("Backups written as <file>.mojibake.bak")
    return 0 if total_after == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
