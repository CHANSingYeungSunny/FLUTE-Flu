"""Target-only scoring for ORIGINAL Track C. Never substitute new CPU variants."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from common import *

MODELS=['miflu','nlinear','dlinear','timecma_llm','patchtst','itransformer','qwen_time_llm','calf_llm']

def unpack_arrays(path,L,seed,z):
    expected=origins(L,'test');_,true,_=windows(z,L,'test')
    d=np.load(path,allow_pickle=False)
    pred=d['pred'] if 'pred' in d else d['prediction']
    target=d['target'] if 'target' in d else d['true']
    if pred.shape==(len(expected),7,L):pred=pred.transpose(0,2,1);target=target.transpose(0,2,1)
    if pred.shape!=(len(expected),L,7):raise ValueError('Invalid strict-966 prediction shape: '+str(path))
    if 'origins' in d:np.testing.assert_array_equal(d['origins'],expected)
    np.testing.assert_allclose(target,true,atol=4e-6,rtol=2e-6)
    return pred,target

def main(a):
    root=Path(a.handoff);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    _,z,mu,sd=load_data(root)
    old=pd.read_csv(root/'08_paper_tables/TRACK_C_TEST_MSE_RANKING.csv')
    perL=pd.read_csv(root/'08_paper_tables/TRACK_C_PER_HORIZON_CHAMPIONS.csv')
    rows=[];cells=[]
    search=[root]+[Path(x) for x in a.raw_root]
    inventory=[]
    for model in MODELS:
        got=[]
        for L in HORIZONS:
            for seed in SEEDS:
                if model=='miflu':
                    paths=list(root.glob(f'04_benchmark/miflu/*L{L}*seed{seed}/test_predictions_*.csv'))
                    if not paths:continue
                    p=paths[0];d=pd.read_csv(p).sort_values(['forecast_origin','forecast_lead','feature_index'])
                    assert not d.duplicated(['forecast_origin','forecast_lead','feature_index']).any()
                    assert d.dataset_hash.eq(DATA_SHA).all() and d.seed.eq(seed).all() and d.horizon.eq(L).all()
                    assert d.split.eq('test').all()
                    exp=pd.MultiIndex.from_product([origins(L,'test'),range(1,L+1),range(7)]).to_frame(index=False).to_numpy()
                    np.testing.assert_array_equal(d[['forecast_origin','forecast_lead','feature_index']],exp)
                    pred=d.y_pred_z.to_numpy().reshape(-1,L,7);target=d.y_true_z.to_numpy().reshape(-1,L,7)
                    _,true,_=windows(z,L,'test');np.testing.assert_allclose(target,true,atol=4e-6,rtol=2e-6)
                else:
                    # The original seven artifacts use this explicit naming convention.
                    # Unnamed CPU predictions.npz and CPU NLinear are not aliases.
                    paths=sorted({p for r in search for p in r.rglob(f'pred_{model}_L{L}_s{seed}.npz')})
                    if not paths:continue
                    if len({sha(p) for p in paths})>1:raise ValueError('Conflicting original predictions: '+str(paths))
                    p=paths[0];pred,target=unpack_arrays(p,L,seed,z)
                met=score(pred,target,sd)
                entry=dict(model=model,L=L,seed=seed,source_path=str(p),source_sha256=sha(p),**met)
                got.append(entry);cells.append(entry)
        original=old[old.model==model].iloc[0]
        all12=len(got)==12
        m=pd.DataFrame(got)
        rows.append(dict(model=model,track='TRACK_C',n_seeds=3,mean_Test_MSE_4L=original.mean_Test_MSE_4L,
            mean_Test_MAE_4L=original.mean_Test_MAE_4L,n_raw_cells_found=len(got),n_raw_cells_required=12,
            MSE_z_ILITOTAL=float(m.mse_z_ili.mean()) if all12 else np.nan,
            MSE_physical_ILITOTAL=float(m.mse_counts2_ili.mean()) if all12 else np.nan,
            MAE_z_ILITOTAL=float(m.mae_z_ili.mean()) if all12 else np.nan,
            MAE_physical_ILITOTAL=float(m.mae_counts_ili.mean()) if all12 else np.nan,
            physical_MSE_unit='patient-count^2',physical_MAE_unit='patient-count',
            status='DONE' if all12 else 'NA_RAW_PREDICTIONS_UNAVAILABLE',
            UNIFIED_PAIR_KEY=UNIFIED_PAIR_KEY))
    df=pd.DataFrame(rows);df.to_csv(out/'TRACK_C_ILITOTAL_MSE_MAE.csv',index=False)
    pd.DataFrame(cells).to_csv(out/'TRACK_C_ILITOTAL_PER_CELL.csv',index=False)
    lrows=[]
    cm=pd.DataFrame(cells)
    for row in perL.itertuples():
        g=cm[(cm.model==row.model)&(cm.L==row.L)]
        lrows.append(dict(model=row.model,L=row.L,mse=row.mse,mae=row.mae,
            MSE_z_ILITOTAL=g.mse_z_ili.mean() if len(g)==3 else np.nan,
            MSE_physical_ILITOTAL=g.mse_counts2_ili.mean() if len(g)==3 else np.nan,
            MAE_z_ILITOTAL=g.mae_z_ili.mean() if len(g)==3 else np.nan,
            MAE_physical_ILITOTAL=g.mae_counts_ili.mean() if len(g)==3 else np.nan,n_raw_seeds=len(g)))
    pd.DataFrame(lrows).to_csv(out/'TRACK_C_ILITOTAL_PER_L.csv',index=False)
    print(df[['model','mean_Test_MSE_4L','MSE_z_ILITOTAL','MSE_physical_ILITOTAL','status']].to_string(index=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--handoff',required=True);p.add_argument('--out',required=True)
    p.add_argument('--raw-root',action='append',default=[]);main(p.parse_args())
