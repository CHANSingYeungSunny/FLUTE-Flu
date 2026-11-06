#!/usr/bin/env python3
"""Convert the deck and bilingual notes to PDFs with installed/bundled LibreOffice."""
from pathlib import Path
import os,shutil,tempfile,subprocess,argparse
HERE=Path(__file__).resolve().parent

def convert(only='all'):
 runtime=os.environ.get('CODEX_PRIMARY_RUNTIME_ROOT');candidate=Path(runtime)/'dependencies/bin/override/soffice' if runtime else None
 executable=str(candidate) if candidate and candidate.exists() else shutil.which('soffice') or shutil.which('libreoffice')
 if not executable:raise SystemExit('Install LibreOffice and put soffice on PATH. Install a CJK font for bilingual notes.')
 names={'deck':'Week12_Progress_Presentation.pptx','notes':'Presentation_Notes_EN_ZH.docx'}
 for key,filename in names.items():
  if only not in ('all',key):continue
  with tempfile.TemporaryDirectory(prefix='miflu_present_') as tmp:
   temp=Path(tmp);src=HERE/filename
   cp=subprocess.run([executable,'--headless','-env:UserInstallation='+(temp/'profile').as_uri(),'--convert-to','pdf','--outdir',str(temp),str(src)],capture_output=True,text=True,timeout=120)
   result=temp/(src.stem+'.pdf')
   if cp.returncode or not result.is_file():raise RuntimeError(cp.stderr+cp.stdout)
   shutil.copy2(result,HERE/result.name)
   print(result.name,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--only',choices=['all','deck','notes'],default='all');convert(p.parse_args().only)
