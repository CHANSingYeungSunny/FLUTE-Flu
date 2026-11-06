#!/usr/bin/env python3
"""Validate return structure/hashes, not experiments, statistics or publishability."""
import argparse,csv,hashlib,json
from pathlib import Path
REQUIRED=['RETURN_SUMMARY.md','PROTOCOL_LOCK.json','EXECUTION_PLAN.json','RUN_LEDGER.csv','RUN_METRICS.csv','PEAK_EVENTS.csv','MODEL_FIDELITY.csv','CHECKS.json','ENVIRONMENT.md','PAPER_TO_CODE.md','STATISTICAL_ANALYSIS_PLAN.md','STATISTICAL_RESULTS.csv','COST_AND_SCHEDULER.md','OLD_NEW_RECONCILIATION.csv','DOCUMENT_UPDATE_MAP.csv','UNVERIFIED_ITEMS.md','REPRODUCE.md','CODE_CHANGES.patch','RETURN_MANIFEST.json']
STATUSES={'planned','queued','running','completed','reused','failed','skipped','blocked','not_executed'}
CHECK_STATUSES={'passed','failed','skipped','blocked','not_executed'}
COLUMNS=['run_id','track','profile','model','variant','region','origin','L','seed','status','effective_replication','data_sha256','code_sha256','config_sha256','checkpoint_sha256','prediction_path','config_path','metrics_path','log_path','job_id','started_utc','ended_utc','hardware','total_params','trainable_params','train_wall_seconds','inference_wall_seconds','peak_memory_bytes','reuse_source_run_id','reason']
def validate(root):
 root=Path(root).resolve();errors=[];counts={};listed=set()
 def safe(rel):
  if not isinstance(rel,str) or not rel or Path(rel).is_absolute() or '..' in Path(rel).parts:raise ValueError(f'unsafe path: {rel!r}')
  p=(root/rel).resolve()
  if not p.is_relative_to(root):raise ValueError(f'path escapes root: {rel}')
  return p
 for f in REQUIRED:
  if not (root/f).is_file():errors.append('missing '+f)
 for name in ['PROTOCOL_LOCK.json','EXECUTION_PLAN.json','CHECKS.json','RETURN_MANIFEST.json']:
  try:json.loads((root/name).read_text(encoding='utf-8'))
  except Exception as ex:errors.append(name+': '+str(ex))
 excluded=set()
 try:
  m=json.loads((root/'RETURN_MANIFEST.json').read_text(encoding='utf-8'));excluded=set(m.get('excluded_outputs',[]))
  if excluded-{'VALIDATION_RESULT.json'}:errors.append('unsupported manifest exclusion')
  for item in m['files']:
   rel=item['path'];p=safe(rel)
   if rel in listed:errors.append('duplicate manifest path '+rel)
   listed.add(rel)
   if p.is_symlink() or not p.is_file():errors.append('missing/invalid manifest member '+rel);continue
   h=hashlib.sha256()
   with p.open('rb') as f:
    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
   if p.stat().st_size!=item['bytes'] or h.hexdigest()!=item['sha256']:errors.append('hash/size mismatch '+rel)
  actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}-{'RETURN_MANIFEST.json'}-excluded
  if actual!=listed:errors.append('manifest coverage differs: '+str(sorted(actual^listed)))
 except Exception as ex:errors.append('manifest: '+str(ex))
 try:
  with (root/'RUN_LEDGER.csv').open(newline='',encoding='utf-8-sig') as f:
   reader=csv.DictReader(f)
   if not set(COLUMNS)<=set(reader.fieldnames or []):errors.append('RUN_LEDGER missing columns')
   ids=set()
   for row in reader:
    rid=row.get('run_id','');status=row.get('status','');counts[status]=counts.get(status,0)+1
    if not rid or rid in ids:errors.append('blank/duplicate run ID '+rid)
    ids.add(rid)
    if status not in STATUSES:errors.append('invalid run status '+rid)
    if status in {'completed','reused'}:
     for key in ['prediction_path','config_path','metrics_path','log_path']:
      rel=row.get(key,'')
      try:
       if not safe(rel).is_file() or rel not in listed:errors.append('run evidence absent/unhashed '+rid+' '+key)
      except Exception as ex:errors.append(rid+' '+str(ex))
    if status in {'failed','skipped','blocked','not_executed'} and not row.get('reason'):errors.append('missing run reason '+rid)
 except Exception as ex:errors.append('ledger: '+str(ex))
 check_counts={}
 try:
  checks=json.loads((root/'CHECKS.json').read_text(encoding='utf-8'))['checks']
  if not isinstance(checks,list) or not checks:errors.append('CHECKS must contain at least one actual status record')
  names=set()
  for c in checks:
   name=c.get('name','');status=c.get('status');check_counts[status]=check_counts.get(status,0)+1
   if not name or name in names:errors.append('blank/duplicate check name')
   names.add(name)
   if status not in CHECK_STATUSES:errors.append('invalid check status '+name)
   if status in {'passed','failed'}:
    if not c.get('command') or type(c.get('exit_code')) is not int:errors.append('check missing command/exit '+name)
    elif (status=='passed')!=(c['exit_code']==0):errors.append('check status/exit mismatch '+name)
    try:
     if not safe(c.get('log_path')).is_file() or c['log_path'] not in listed:errors.append('check log absent/unhashed '+name)
    except Exception as ex:errors.append(name+' '+str(ex))
   elif status in {'blocked','not_executed'} and c.get('exit_code') is not None:errors.append('unexecuted check has exit code '+name)
 except Exception as ex:errors.append('checks: '+str(ex))
 return {'integrity_status':'PASS' if not errors else 'FAIL','scope':'structure, file hashes and limited status consistency only; NOT scientific validation','run_status_counts':counts,'check_status_counts':check_counts,'scientific_readiness':'NOT_ASSESSED','errors':errors}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();r=validate(a.root);print(json.dumps(r,indent=2))
 if a.out:a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(bool(r['errors']))
