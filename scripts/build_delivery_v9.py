#!/usr/bin/env python3
"""Current revision-9 authoring entry point. PDF conversion is a separate command."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 for rel in ['scripts/build_current_documents.py','manuscript/build_manuscript.py','scripts/add_revision9_internal.py','scripts/split_internal_qa_zh.py','presentation/build_english_notes.py']:
  subprocess.run([sys.executable,str(ROOT/rel)],cwd=ROOT,check=True)
