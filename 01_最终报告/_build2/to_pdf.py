#!/usr/bin/env python3
"""Portable conversion of the eight current DOCX files using installed/bundled LibreOffice."""
from pathlib import Path
import os,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'01_最终报告'
NAMES=[f'{kind}_{lang}' for kind in ['report_internal','progress_report','ieee_manuscript','record_for_journal'] for lang in ['en','zh']]+['report_internal_qa_zh']
def main():
 runtime=os.environ.get('CODEX_PRIMARY_RUNTIME_ROOT');candidate=Path(runtime)/'dependencies/bin/override/soffice' if runtime else None
 executable=str(candidate) if candidate and candidate.exists() else shutil.which('soffice') or shutil.which('libreoffice')
 if not executable:raise SystemExit('LibreOffice missing. Install LibreOffice and put soffice on PATH.')
 for name in NAMES:
  if name=='ieee_manuscript_en':
   subprocess.run([os.environ.get('CODEX_PRIMARY_RUNTIME_PYTHON') or __import__('sys').executable,str(ROOT/'manuscript/build_pdf.py')],check=True)
   continue
  src=OUT/(name+'.docx')
  with tempfile.TemporaryDirectory(prefix='miflu_pdf_') as tmp:
   path=Path(tmp);profile=(path/'profile').as_uri()
   cp=subprocess.run([executable,'--headless','-env:UserInstallation='+profile,'--convert-to','pdf','--outdir',str(path),str(src)],capture_output=True,text=True,timeout=120)
   result=path/(name+'.pdf')
   if cp.returncode or not result.exists():raise RuntimeError(name+': '+cp.stderr+cp.stdout)
   shutil.copy2(result,OUT/result.name)
  print(name+'.pdf')
if __name__=='__main__':main()
