"""Independent C2 prediction scorer plus matched archived Track C comparison."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from common import *

def main(a):
    runs,out,root=Path(a.runs),Path(a.out),Path(a.handoff);out.mkdir(parents=True,exist_ok=True)
    _,z,mu,sd=load_data(root)
    reference=pd.read_csv(root/'08_paper_tables/TRACK_C_MIFLU_RUN_MATRIX.csv')
    cells=[]
    for p in sorted(runs.glob('*/manifest_r1c_c2_endmatch__L*__seed*.json')):
        m=json.loads(p.read_text());L,seed=int(m['horizon']),int(m['seed'])
        if m['dataset_sha256']!=DATA_SHA:raise ValueError('Wrong dataset in C2 manifest')
        if m['lr_schedule']!='r1c_type1':raise ValueError('C2 must use aligned type1 schedule')
        f=p.parent/f'test_predictions_r1c_c2_endmatch__L{L}__seed{seed}.csv'
        d=pd.read_csv(f).sort_values(['forecast_origin','forecast_lead','feature_index'])
        expected=pd.MultiIndex.from_product([origins(L,'test'),range(1,L+1),range(7)]).to_frame(index=False).to_numpy()
        np.testing.assert_array_equal(d[['forecast_origin','forecast_lead','feature_index']],expected)
        if d.duplicated(['forecast_origin','forecast_lead','feature_index']).any():raise ValueError('Duplicate prediction key')
        assert d.dataset_hash.eq(DATA_SHA).all() and d.seed.eq(seed).all() and d.horizon.eq(L).all()
        assert d.split.eq('test').all()
        pred=d.y_pred_z.to_numpy().reshape(-1,L,7);target=d.y_true_z.to_numpy().reshape(-1,L,7)
        _,truth,_=windows(z,L,'test');np.testing.assert_allclose(target,truth,atol=4e-6,rtol=2e-6)
        result=score(pred,target,sd);np.testing.assert_allclose(result['mse_z_all7'],m['test_mse_z'],rtol=1e-10)
        ref=reference[(reference.horizon==L)&(reference.seed==seed)].iloc[0]
        cells.append(dict(model='MIFlu_C2',track='R_C2_EXPLORATORY',L=L,seed=seed,
            **result,Track_C_MSE=ref.test_mse_z,Track_C_MAE=ref.test_mae_z,
            delta_MSE_vs_Track_C=result['mse_z_all7']-ref.test_mse_z,
            relative_delta_pct=100*(result['mse_z_all7']/ref.test_mse_z-1),
            source_prediction_sha256=sha(f),best_epoch=m['best_epoch'],wall_seconds=m['wall_seconds'],
            status='MEASURED_AFTER_FROZEN_CHECKPOINT',text_pathway_status='UNRESOLVED'))
    d=pd.DataFrame(cells)
    expected={(L,s) for L in HORIZONS for s in SEEDS}
    available={(r['L'],r['seed']) for r in cells}
    assert len(available)==len(cells),'Duplicate complete C2 cells'
    if not available.issubset(expected):raise ValueError('Unexpected cell configuration')
    status=dict(expected_cells=12,completed_cells=len(cells),missing_cells=sorted(expected-available),
        state='COMPLETE' if available==expected else 'PENDING_OR_PARTIAL',
        reproduction_status='PARTIAL_REPRODUCTION',UNIFIED_PAIR_KEY=UNIFIED_PAIR_KEY,
        caution='Archived Track C comparator may differ in software/runtime; not a guaranteed one-factor causal contrast')
    (out/'C2_STATUS.json').write_text(json.dumps(status,indent=2))
    if len(d):
        d.to_csv(out/'C2_RESULTS_PER_CELL.csv',index=False)
        hl=d.groupby('L')[['mse_z_all7','mae_z_all7','mse_z_ili','mse_counts2_ili','Track_C_MSE','delta_MSE_vs_Track_C']].mean().reset_index()
        hl=hl.merge(d.groupby('L').seed.nunique().rename('n_seeds_completed'),on='L')
        hl['expected_n_seeds']=3
        hl['status']=np.where(hl.n_seeds_completed.eq(3),'COMPLETE_HORIZON','PARTIAL_HORIZON')
        hl.to_csv(out/'C2_PER_HORIZON.csv',index=False)
        # A four-horizon grand mean is released ONLY when all 12 cells exist.
        if available==expected:
            byseed=d.groupby('seed').mse_z_all7.mean()
            pd.DataFrame([dict(model='MIFlu_C2',mean_Test_MSE_4L=byseed.mean(),sd_Test_MSE_4L=byseed.std(ddof=1),
                mean_Test_MAE_4L=d.mae_z_all7.mean(),Track_C_MSE_4L=d.Track_C_MSE.mean(),
                delta_vs_Track_C=d.delta_MSE_vs_Track_C.mean(),n_seeds=3,status='PARTIAL_REPRODUCTION')]).to_csv(out/'C2_TEST_MSE_RANKING_COMPARISON.csv',index=False)
    print(json.dumps(status,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['runs','out','handoff']:p.add_argument('--'+n,required=True)
    main(p.parse_args())
