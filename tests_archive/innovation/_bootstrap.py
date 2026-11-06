"""Shared bootstrap for innovation tests (adds `scripts/` to sys.path)."""
from __future__ import annotations

import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
for _p in (SCRIPTS_DIR, PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
