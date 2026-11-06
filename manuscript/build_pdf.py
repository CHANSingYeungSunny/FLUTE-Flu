#!/usr/bin/env python3
"""Compile the canonical journal PDF from the included publisher class."""
from pathlib import Path
import subprocess,sys,shutil,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;L=HERE/'overleaf'
def build():
 logs=[]
 for i in range(2):
  r=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=L,capture_output=True,text=True);logs.append(r.stdout+'\n'+r.stderr)
  if r.returncode:raise RuntimeError(logs[-1][-2500:])
 last=logs[-1]
 for token in ['Overfull \\hbox','Overfull \\vbox','undefined references','undefined on input line']:
  if token in last:raise RuntimeError('Unresolved LaTeX issue: '+token)
 out=ROOT/'01_最终报告/ieee_manuscript_en.pdf';shutil.copyfile(L/'main.pdf',out)
 A=ROOT/'audit/revision9';A.mkdir(exist_ok=True,parents=True);(A/'LATEX_BUILD.log').write_text(last)
 receipt={'command':'pdflatex -interaction=nonstopmode -halt-on-error main.tex','passes':2,'executed_locally':True,'overleaf_cloud_executed':False,'unresolved_references':False,'overfull_boxes':False,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'expected_publisher_class_name_warning':'ieeecolor provides IEEEtran'}
 (A/'LATEX_BUILD.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':build()
