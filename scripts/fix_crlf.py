#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_crlf.py — strip CRLF line terminators from text files.

Slurm rejects a batch script that contains DOS line breaks, and the shell
quoting needed for `sed -i "s/\r$//"` does not survive being passed through
the local PowerShell -> ssh hop. Doing it in Python avoids the quoting problem
entirely.

Usage: python fix_crlf.py <file> [<file> ...]
"""
from __future__ import annotations

import sys


def main():
    if len(sys.argv) < 2:
        print("usage: fix_crlf.py <file> [<file> ...]")
        return 2
    for path in sys.argv[1:]:
        with open(path, "rb") as fh:
            data = fh.read()
        fixed = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        if fixed == data:
            print(f"[fix] unchanged (already LF): {path}")
            continue
        with open(path, "wb") as fh:
            fh.write(fixed)
        n = data.count(b"\r\n") or data.count(b"\r")
        print(f"[fix] rewrote {n} line endings -> LF: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
