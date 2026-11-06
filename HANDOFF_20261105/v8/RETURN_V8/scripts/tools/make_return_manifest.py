#!/usr/bin/env python3
"""Hash a consolidated return folder. Does not execute or validate experiments."""
import argparse,hashlib,json
from pathlib import Path

def build(root,exclude=None):
 root=Path(root).resolve();exclude=set(exclude or [])
 if exclude-{'VALIDATION_RESULT.json'}:raise ValueError('Only the validator output may be excluded')
 files=[]
 for p in sorted(root.rglob('*')):
  if p.is_symlink():raise ValueError(f'Symlink not allowed: {p}')
  if not p.is_file():continue
  rel=p.relative_to(root).as_posix()
  if rel=='RETURN_MANIFEST.json' or rel in exclude:continue
  h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
  files.append({'path':rel,'bytes':p.stat().st_size,'sha256':h.hexdigest()})
 obj={'schema_version':1,'scope':'file integrity only; no scientific validation','excluded_outputs':sorted(exclude),'files':files}
 (root/'RETURN_MANIFEST.json').write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8');return obj
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('root',type=Path);a.add_argument('--exclude',action='append',default=[]);args=a.parse_args();print('files hashed:',len(build(args.root,args.exclude)['files']))
