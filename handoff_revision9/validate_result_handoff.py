#!/usr/bin/env python3
"""Integrity validator for a NEW MIFlu return; never certifies scientific correctness.
Usage: python validate_result_handoff.py manifest RETURN_ROOT
       python validate_result_handoff.py check RETURN_ROOT --out RETURN_ROOT/VALIDATION_RESULT.json
"""
from pathlib import Path,PurePosixPath
import argparse,json,hashlib,csv,re
CONTRACT=Path(__file__).with_name('RETURN_CONTRACT.json')
EXCLUDE={'RETURN_MANIFEST.json','VALIDATION_RESULT.json'}
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def entries(root):
 return sorted(p for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix() not in EXCLUDE)
def manifest(root):
 rows=[]
 for p in entries(root):
  if p.is_symlink():raise ValueError('Symlink not allowed: '+str(p))
  rows.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)})
 result={'schema_version':1,'files':rows};(root/'RETURN_MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n');return result
def check(root,contract=CONTRACT):
 errors=[];warnings=[];c=json.loads(Path(contract).read_text());listed={};m={};status={}
 try:m=json.loads((root/'RETURN_MANIFEST.json').read_text())
 except Exception as e:errors.append('Manifest unreadable: '+str(e))
 for r in m.get('files',[]):
  rel=r.get('path','');q=PurePosixPath(rel)
  if not rel or q.is_absolute() or '..' in q.parts or '\\' in rel or rel in EXCLUDE:errors.append('Unsafe/excluded manifest path: '+rel);continue
  if rel in listed:errors.append('Duplicate manifest path: '+rel)
  listed[rel]=r;p=root/rel
  if not p.is_file() or p.is_symlink():errors.append('Missing/nonregular file: '+rel);continue
  if p.stat().st_size!=r.get('bytes') or digest(p)!=r.get('sha256'):errors.append('Size/hash mismatch: '+rel)
 actual={p.relative_to(root).as_posix() for p in entries(root)}
 for rel in sorted(actual-set(listed)):errors.append('Unlisted file: '+rel)
 for rel in c['required_readable_files']:
  if rel=='VALIDATION_RESULT.json':continue
  if not (root/rel).is_file():errors.append('Required readable file missing: '+rel)
 try:status=json.loads((root/'RETURN_STATUS.json').read_text())
 except Exception as e:errors.append('Status unreadable: '+str(e))
 for key in c['status_required_keys']:
  if key not in status:errors.append('Required status key missing: '+key)
 blocked=status.get('blocked_outputs',{})
 if not isinstance(blocked,dict):errors.append('blocked_outputs must map paths to reasons');blocked={}
 for rel in c['required_aggregation_or_explicit_block']:
  if not (root/rel).is_file() and not (isinstance(blocked.get(rel),str) and blocked[rel].strip()):errors.append('Aggregation neither supplied nor explicitly blocked: '+rel)
 for key in ['core','national','ablation']:
  obj=status.get(key,{})
  if not isinstance(obj,dict):errors.append(key+' must be an object');continue
  if 'planned' in obj and 'completed' in obj:
   if not all(isinstance(obj.get(k),int) and obj[k]>=0 for k in ['planned','completed']) or obj['completed']>obj['planned']:errors.append(key+' declared counts invalid')
   if obj.get('status')=='complete' and obj['completed']!=obj['planned']:errors.append(key+' incorrectly declares complete')
 try:
  rows=list(csv.DictReader((root/'COMMANDS_EXECUTED.csv').open(newline='')))
  for i,row in enumerate(rows,2):
   if not row.get('command','').strip() or row.get('status') not in ['EXECUTED','NOT_EXECUTED']:errors.append('Command row '+str(i)+' missing exact command/status')
   if row.get('status')=='EXECUTED' and not row.get('exit_code','').strip():errors.append('Executed command lacks exit code at row '+str(i))
 except Exception as e:errors.append('Commands CSV unreadable: '+str(e))
 warnings.append('Declared counts and file presence are not scientific completeness checks. Raw scores, array/channel/window alignment, test validity and claims require independent review.')
 return {'integrity_status':'PASS' if not errors else 'FAIL','errors':errors,'warnings':warnings,'listed_files':len(listed),'scientific_readiness':'NOT_ASSESSED','scope':c['integrity_pass_claim']}
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['manifest','check']);ap.add_argument('root',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args();root=a.root.resolve()
 if a.action=='manifest':r=manifest(root);print('Manifest files:',len(r['files']))
 else:
  r=check(root);out=a.out or root/'VALIDATION_RESULT.json';out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(bool(r['errors']))
