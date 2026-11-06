#!/usr/bin/env python3
"""Current document entry point; historical builder retained separately for provenance."""
from pathlib import Path
import sys
from build_historical_reports import final_styles, SOURCES, refline
ROOT=Path(__file__).resolve().parents[2]
def build(*args,**kwargs):
 import subprocess
 return subprocess.run([sys.executable,str(ROOT/'scripts/build_delivery_v9.py')],cwd=ROOT,check=True)
if __name__=='__main__':build()
