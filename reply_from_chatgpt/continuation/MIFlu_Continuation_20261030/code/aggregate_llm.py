"""Export measured LLM arms to the Track-C-shaped table schema, without mixing tracks."""
import argparse,json
from pathlib import Path
import pandas as pd
import numpy as np
from common import *

def main(a):
    root,out=Path(a.runs),Path(a.out);out.mkdir(parents=True,exist_ok=True)
    cells=[];peaks=[];shared=[]
    for p in sorted(root.glob('*/*/*/LLM_RESULTS_PER_CELL.csv')):
        g=pd.read_csv(p);cells.append(g)
        pk=p.with_name('LLM_PTE_PIE_PER_MODEL_L.csv')
        if pk.exists():peaks.append(pd.read_csv(pk))
        cost=p.with_name('shared_cost.json')
        if cost.exists():
            c=json.loads(cost.read_text());c.update(model=g.model.iloc[0],L=int(g.L.iloc[0]),source=str(cost));shared.append(c)
    expected=[]
    for model in ['qwen','deepseek']:
        for arm in ['encoding_only','generation_augmented']:
            for L in HORIZONS:
                for seed in SEEDS:expected.append(dict(model=model+'_'+arm,L=L,seed=seed))
    plan=pd.DataFrame(expected)
    if not cells:
        plan['status']='NOT_RUN';plan['test_mse_z']=np.nan;plan['test_mae_z']=np.nan
        plan.to_csv(out/'LLM_EXPECTED_RUN_MATRIX.csv',index=False)
        (out/'LLM_STATUS.json').write_text(json.dumps(dict(expected_cells=48,measured_cells=0,status='NOT_RUN'),indent=2))
        print('No LLM results; exported 48 explicit NOT_RUN cells.');return
    d=pd.concat(cells,ignore_index=True)
    if d.duplicated(['model','L','seed']).any():raise ValueError('Duplicate LLM cell outputs')
    d.to_csv(out/'LLM_RESULTS_PER_CELL.csv',index=False)
    plan=plan.merge(d[['model','L','seed','mse_z_all7','mae_z_all7']],on=['model','L','seed'],how='left')
    plan['status']=np.where(plan.mse_z_all7.notna(),'MEASURED','NOT_RUN')
    plan.to_csv(out/'LLM_EXPECTED_RUN_MATRIX.csv',index=False)
    summary=[];horizons=[]
    for name,g in d.groupby('model'):
        done=len(g)==12 and set(g.L)==set(HORIZONS) and set(g.seed)==set(SEEDS)
        bs=g.groupby('seed').mse_z_all7.mean()
        summary.append(dict(model=name,mean_Test_MSE_4L=bs.mean() if done else np.nan,
            sd_Test_MSE_4L=bs.std(ddof=1) if done else np.nan,mean_Test_MAE_4L=g.mae_z_all7.mean() if done else np.nan,
            side='LLM',n_seeds=3,n_completed_cells=len(g),status='COMPLETE' if done else 'PARTIAL_NO_4L_MEAN',track='LLM_FEATURE_EXPLORATORY_966'))
        for L,h in g.groupby('L'):
            if len(h)==3:horizons.append(dict(model=name,L=int(L),mse=h.mse_z_all7.mean(),mae=h.mae_z_all7.mean(),
                MSE_z_ILITOTAL=h.mse_z_ili.mean(),MSE_physical_ILITOTAL=h.mse_counts2_ili.mean(),
                MAE_z_ILITOTAL=h.mae_z_ili.mean(),MAE_physical_ILITOTAL=h.mae_counts_ili.mean(),n_seeds=3))
    rank=pd.DataFrame(summary).sort_values('mean_Test_MSE_4L');rank.insert(0,'rank_MSE',rank.mean_Test_MSE_4L.rank(method='min'))
    rank.to_csv(out/'LLM_TEST_MSE_RANKING.csv',index=False)
    pd.DataFrame(horizons).to_csv(out/'LLM_PER_HORIZON.csv',index=False)
    if peaks:pd.concat(peaks,ignore_index=True).to_csv(out/'LLM_PTE_PIE_PER_MODEL_L.csv',index=False)
    # One row per L/arm, so each feature computation is counted once across seeds.
    pd.DataFrame(shared).to_csv(out/'LLM_SHARED_FEATURE_COST.csv',index=False)
    (out/'LLM_STATUS.json').write_text(json.dumps(dict(expected_cells=48,measured_cells=len(d),
        complete_conditions=sum(x['status']=='COMPLETE' for x in summary),reproduction_status='PARTIAL_REPRODUCTION'),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runs',required=True);p.add_argument('--out',required=True);main(p.parse_args())
