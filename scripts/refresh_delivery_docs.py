#!/usr/bin/env python3
"""Refresh inventory without reintroducing pre-return prose."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parents[1]/'01_最终报告/_build2/make_manifest.py'),run_name='__main__')
