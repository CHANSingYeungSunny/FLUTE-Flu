from pathlib import Path
import numpy as np,pandas as pd,json,csv,collections,hashlib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();r=args.root;OUT=args.out;OUT.mkdir(parents=True,exist_ok=True);rows=[];issues=[]
for phase in ['core','all']:
 for p in sorted((r/'RAW_EVIDENCE/cells'/phase/'export').glob('*/*')):
  if not p.is_dir():continue
  model=p.parent.name;npzs=list(p.glob('pred_*.npz'));L=int(p.name.split('_')[0][1:]);seed=int(p.name.split('_s')[1]);row={'phase':phase,'model':model,'L':L,'seed':seed}
  if npzs:
   with np.load(npzs[0],allow_pickle=False) as z:
    pred=z['pred'];gt=z['target'];start=z['target_start_row']
    assert pred.shape==gt.shape and pred.shape[1:]==(7,L),p
    assert np.isfinite(pred).all() and np.isfinite(gt).all(),p
    assert pred.shape[0]=={24:170,36:158,48:146,60:134}[L],p
    assert np.all(start>=773) and np.all(start+L<=966),p
    mse=float(np.mean((pred.astype(np.float64)-gt.astype(np.float64))**2));mae=float(np.mean(np.abs(pred.astype(np.float64)-gt.astype(np.float64))))
    row.update(raw_seven_channel_rescored=True,n_windows=len(start),mse_recomputed=mse,mae_recomputed=mae)
   if (p/'metrics.csv').exists():
    m=pd.read_csv(p/'metrics.csv').iloc[0];recorded=float(m['mse_all']);recordedmae=float(m['mae_all'])
   else:
    m=json.loads((p/'metrics.json').read_text());recorded=m['test_mse_7var_z'];recordedmae=m['test_mae_7var_z']
   row.update(mse_stored=recorded,mae_stored=recordedmae,mse_abs_delta=abs(mse-recorded),mae_abs_delta=abs(mae-recordedmae))
   if not np.isclose(mse,recorded,rtol=2e-6,atol=1e-7) or not np.isclose(mae,recordedmae,rtol=2e-6,atol=1e-7):issues.append({'cell':str(p),'issue':'metric mismatch',**row})
  else:
   f=next(p.glob('predictions_*.csv'));d=pd.read_csv(f);t=d[d['split']=='test'].copy();m=json.loads(next(p.glob('manifest_*.json')).read_text());best=m['best_rep']
   assert len(t)>0 and np.isfinite(t[['ground_truth_ili','prediction_ili']].to_numpy()).all(),p
   t['target_start_row']=t.abs_week-t.step; starts=sorted(t.target_start_row.unique()); assert len(starts)=={24:170,36:158,48:146,60:134}[L]; assert min(starts)>=773 and max(starts)+L<=966; cropped=t[t.target_start_row.isin(starts[:{24:160,36:144,48:144,60:128}[L]])]; mse=float(np.mean((cropped.prediction_ili.to_numpy()-cropped.ground_truth_ili.to_numpy())**2));mae=float(np.mean(np.abs(cropped.prediction_ili.to_numpy()-cropped.ground_truth_ili.to_numpy())))
   row.update(raw_seven_channel_rescored=False,scope='ILITOTAL only; seven-channel raw tensor not attached',n_test_rows=len(t),n_windows=len(starts),scored_panel='historical_crop matching MIFlu stored metrics; other NPZ stored metrics use all windows',n_leads=t.step.nunique(),ili_mse_recomputed=mse,ili_mse_manifest=float(best['test_mse_ili']),ili_mae_recomputed=mae)
   if not np.isclose(mse,float(best['test_mse_ili']),rtol=2e-6,atol=1e-7):issues.append({'cell':str(p),'issue':'MIFlu ILITOTAL metric mismatch',**row})
  rows.append(row)
summary={'scope':'Independent arithmetic and array-contract verification on supplied predictions only; no model training rerun','cells':len(rows),'npz_seven_channel_cells':sum(x['raw_seven_channel_rescored'] for x in rows),'miflu_ili_csv_cells':sum(not x['raw_seven_channel_rescored'] for x in rows),'issues':issues,'max_npz_mse_abs_delta':max(x.get('mse_abs_delta',0) for x in rows)}
(OUT/'RAW_RESCORE_CELLS.json').write_text(json.dumps(rows,indent=2)+'\n');(OUT/'RAW_RESCORE_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='issues'},indent=2));print('issues',len(issues))
