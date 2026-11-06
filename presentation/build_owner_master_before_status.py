#!/usr/bin/env python3
"""Restore the exact user-corrected PowerPoint master without reflow or style changes.
Usage: python presentation/build_deck.py [--out repeat.pptx]
Scientific/notes consistency is checked by verify_presentation.py. For a fresh
programmatic alternative, run build_generated_deck.py; it cannot reproduce manual
PowerPoint theme/formatting changes and deliberately uses a different output name.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
HERE=Path(__file__).resolve().parent

def build(out):
    manifest=json.loads((HERE/'source/USER_CORRECTIONS.json').read_text())
    source=HERE/'source'/manifest['filename']
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != manifest['sha256']:raise ValueError('User-corrected source hash changed; review and update its manifest first.')
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    if out.resolve()!=source.resolve():shutil.copyfile(source,out)
    print(out.name,digest);return out
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=HERE/'Week12_Progress_Presentation.pptx');build(p.parse_args().out)
