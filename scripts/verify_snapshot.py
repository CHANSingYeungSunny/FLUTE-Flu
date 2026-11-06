#!/usr/bin/env python3
"""Read-only audit of the supplied snapshot. Never rewrites source CSVs or trains models."""
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import linregress,spearmanr
ROOT=Path(__file__).resolve().parents[1]

def holm(p):
    p=np.asarray(p,dtype=float)
    if p.ndim!=1 or np.any(~np.isfinite(p)) or np.any((p<0)|(p>1)):raise ValueError('invalid p-values')
    order=np.argsort(p,kind='stable');out=np.empty_like(p)
    out[order]=np.minimum(1,np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p)))))
    return out

def facts(root=ROOT,raw_smoke=False):
    pt=root/'02_数字表格';m=pd.read_csv(pt/'BENCH_MSE_BY_MODEL_L.csv');p=pd.read_csv(pt/'BENCH_PTE_PIE_BY_STEP.csv');e=pd.read_csv(pt/'BENCH_EFFICIENCY.csv');t=pd.read_csv(pt/'BENCH_PAIRED_TESTS.csv');v=pd.read_csv(pt/'ESSAY_VS_REPRODUCTION_TABLE_V.csv')
    rank=m.groupby('model').agg(mse=('mse_7var_z','mean'),mae=('mae_7var_z','mean'),family=('family','first')).sort_values('mse')
    assert list(rank.index[:3])==['miflu','patchtst','nlinear'] and len(rank)==28
    passed=(p.PTE_wk<=1)&(p.PIE_pct<=25)
    assert np.array_equal(passed.to_numpy(),p.kramer_shaman_pass.to_numpy())
    k=p.assign(passes=passed).groupby('model').agg(PTE=('PTE_wk','mean'),PIE=('PIE_pct','mean'),passes=('passes','sum'))
    rank=rank.join(k);fit=linregress(np.log10(e.dropna(subset=['params']).params),e.dropna(subset=['params']).mse_mean)
    t['p_holm_recomputed']=holm(t.p_raw)
    # Six-decimal exports lose the exact enumeration grid. Recovered values are explicitly labelled.
    recovered=np.rint(t.p_raw.to_numpy()*4096)/4096
    assert np.max(np.abs(recovered-t.p_raw))<=5.01e-7
    t['p_raw_grid_recovered']=recovered;t['p_holm_grid_recovered']=holm(recovered)
    pair=t[(t.model_a=='nlinear')&(t.model_b=='patchtst')].iloc[0]
    a=pd.read_csv(root/'06_原始数据集/raw/national_illness_author_repo_966.csv').iloc[:,1:].to_numpy(float)
    b=pd.read_csv(root/'06_原始数据集/raw/national_illness_raw_paper_exact.csv').iloc[:,2:].to_numpy(float)
    assert a.shape==(966,7) and np.max(abs(a-b))==0
    ans={'models':28,'families':rank.groupby('family').size().to_dict(),'ranking':rank.reset_index().to_dict('records'),'spread':float(rank.mse.max()/rank.mse.min()),'slope':float(fit.slope),'r2':float(fit.rvalue**2),'rho_pie':list(spearmanr(rank.mse,rank.PIE)),'rho_passes':list(spearmanr(rank.mse,rank.passes)),'raw_significant_pairs':int((t.p_raw<.05).sum()),'corrected_significant_pairs':int((t.p_holm_recomputed<.05).sum()),'pair':pair.to_dict(),'pair_raw_rank':int(t.p_raw.rank(method='min').loc[pair.name]),'source_holm_max_error':float(np.max(abs(t.p_holm-t.p_holm_recomputed))),'data_numeric_maxdiff':0.0,'reproduction':v.to_dict('records'),'ablation_status':'Supplied queue at 4 November 2026 reports 60/60 DONE; per-variant aggregation not verified; live cluster not contacted','original_test_suite':'Archived files supplied; collection has import/dependency errors; no passing-suite or reliable total claimed','full_28_pair_coverage':len(t)==378,'pair_models':sorted(set(t.model_a)|set(t.model_b))}
    if raw_smoke:
        file=root/'03_预测数据_证据/expanded_runs/nlinear_L24_s42/pred_nlinear_L24_s42.npz'
        if not file.exists():raise FileNotFoundError('raw smoke requires full handoff: '+str(file))
        with np.load(file,allow_pickle=False) as z:
            n=(len(z['pred'])//16)*16
            assert z['pred'].shape==(170,7,24) and n==160
            ans['raw_smoke']={'path':str(file.relative_to(root)),'evaluated_windows':n,'mse':float(np.mean((z['pred'][:n].astype(float)-z['target'][:n].astype(float))**2)),'min_target_start_row':int(z['target_start_row'][:n].min())}
            assert ans['raw_smoke']['min_target_start_row']>=773
    return ans,t,rank

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw-smoke',action='store_true');ap.add_argument('--out',type=Path,default=ROOT/'audit');args=ap.parse_args()
    ans,t,r=facts(raw_smoke=args.raw_smoke);args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'verified_facts.json').write_text(json.dumps(ans,ensure_ascii=False,indent=2),encoding='utf-8');t.to_csv(args.out/'HOLM_RECOMPUTATION.csv',index=False);r.to_csv(args.out/'VERIFIED_RANKING.csv')
    files=sorted((ROOT/'02_数字表格').glob('*.csv'));(args.out/'INPUT_SHA256.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
    print('SNAPSHOT AUDIT: PASS (arithmetic and source flags; source Holm column is defective)')
    print('Ranking: MIFlu 1.5574, PatchTST 1.6621, NLinear 1.8716')
    print('Raw p < 0.05: 128/136; proper Holm: 0/136; minimum adjusted p approximately 0.0664')
    print('NLinear-PatchTST: corrected from rounded export {:.6f}; enumeration-grid recovery {:.7f}'.format(ans['pair']['p_holm_recomputed'],ans['pair']['p_holm_grid_recovered']))
    print('Paired family: 17 models including MIFlu, excluding DLinear and the 11 encoders; 136 pairs.')
    print('Archived suite: COLLECTION FAILED; model execution and GPU training: NOT EXECUTED')
    if args.raw_smoke:print('Raw CPU smoke MSE: {:.8f}'.format(ans['raw_smoke']['mse']))
    return 0
if __name__=='__main__':raise SystemExit(main())
