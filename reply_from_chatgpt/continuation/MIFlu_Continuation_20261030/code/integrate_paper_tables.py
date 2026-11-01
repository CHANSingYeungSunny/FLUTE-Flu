"""Combine inventories while retaining protocol and model-instance identities.

Combined rank is descriptive ordering, NOT a new frozen Track C championship.
No A/B data enter this table. CPU NLinear is a separate configuration instance.
"""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from common import *
from reconstruct_peak_criteria import summarize

def nondominated(df,x,y):
    out=[]
    for i,row in df.iterrows():
        if pd.isna(row[x]) or pd.isna(row[y]):out.append(None);continue
        others=df.drop(i)
        dominated=((others[x]<=row[x])&(others[y]<=row[y])&((others[x]<row[x])|(others[y]<row[y]))).any()
        out.append(not dominated)
    return out

def main(a):
    root,prior,out=Path(a.handoff),Path(a.prior),Path(a.out);out.mkdir(parents=True,exist_ok=True)
    old=pd.read_csv(root/'08_paper_tables/TRACK_C_TEST_MSE_RANKING.csv')
    oldili=pd.read_csv(Path(a.target_scores)/'TRACK_C_ILITOTAL_MSE_MAE.csv').set_index('model')
    cells=pd.read_csv(prior/'results/expanded_all_cells.csv')
    cpu=cells[cells.model!='PeakBlend'].copy();assert len(cpu)==132
    rows=[]
    for d in old.itertuples():
        v=oldili.loc[d.model]
        rows.append(dict(model=d.model,model_instance_id='TRACK_C::'+d.model,cohort='TRACK_C',
            mean_Test_MSE_4L=d.mean_Test_MSE_4L,sd_Test_MSE_4L=d.sd_Test_MSE_4L,
            mean_Test_MAE_4L=d.mean_Test_MAE_4L,side=d.side,n_seeds=3,
            MSE_z_ILITOTAL=v.MSE_z_ILITOTAL,MSE_physical_ILITOTAL=v.MSE_physical_ILITOTAL,
            MAE_z_ILITOTAL=v.MAE_z_ILITOTAL,MAE_physical_ILITOTAL=v.MAE_physical_ILITOTAL,
            implementation_fidelity='official-repository-based corrected' if d.model=='miflu' else
                'inspired simplification' if d.model in ['qwen_time_llm','calf_llm','timecma_llm'] else 'archived project implementation'))
    for name,g in cpu.groupby('model'):
        byseed=g.groupby('seed').mse_z_all7.mean()
        rows.append(dict(model=name,model_instance_id='CPU_20261030::'+name,cohort='CPU_EXPLORATORY_20261030',
            mean_Test_MSE_4L=byseed.mean(),sd_Test_MSE_4L=byseed.std(ddof=1),
            mean_Test_MAE_4L=g.mae_z_all7.mean(),side='non-LLM',n_seeds=3,
            MSE_z_ILITOTAL=g.mse_z_ili.mean(),MSE_physical_ILITOTAL=g.mse_counts2_ili.mean(),
            MAE_z_ILITOTAL=g.mae_z_ili.mean(),MAE_physical_ILITOTAL=g.mae_counts_ili.mean(),
            implementation_fidelity='pinned upstream compact' if name in ['TimesNet','Autoformer'] else 'new compact project implementation'))
    ranking=pd.DataFrame(rows).sort_values('mean_Test_MSE_4L').reset_index(drop=True)
    ranking.insert(0,'rank_MSE',np.arange(1,len(ranking)+1))
    ranking['rank_MSE_within_cohort']=ranking.groupby('cohort').mean_Test_MSE_4L.rank(method='min').astype(int)
    ranking['rank_scope']='descriptive combined display; inferential comparison must respect cohort/protocol'
    ranking['dataset_sha256']=DATA_SHA;ranking['reference_pair_anchor']=UNIFIED_PAIR_KEY
    ranking['actual_model_count_note']='19 experimental instances; NLinear appears in two distinct protocol instances'
    ranking.to_csv(out/'EXPANDED_COMBINED_TEST_MSE_RANKING.csv',index=False)
    mae=ranking.sort_values('mean_Test_MAE_4L').copy();mae.insert(0,'rank_MAE',range(1,len(mae)+1));mae.to_csv(out/'EXPANDED_COMBINED_TEST_MAE_RANKING.csv',index=False)
    hor=pd.read_csv(root/'08_paper_tables/TRACK_C_PER_HORIZON_CHAMPIONS.csv')
    il=pd.read_csv(Path(a.target_scores)/'TRACK_C_ILITOTAL_PER_L.csv')
    oh=hor.merge(il.drop(columns=['mse','mae']),on=['model','L']);oh['cohort']='TRACK_C';oh['model_instance_id']='TRACK_C::'+oh.model
    nh=cpu.groupby(['model','L'])[['mse_z_all7','mae_z_all7','mse_z_ili','mse_counts2_ili','mae_z_ili','mae_counts_ili']].mean().reset_index()
    nh=nh.rename(columns=dict(mse_z_all7='mse',mae_z_all7='mae',mse_z_ili='MSE_z_ILITOTAL',mse_counts2_ili='MSE_physical_ILITOTAL',mae_z_ili='MAE_z_ILITOTAL',mae_counts_ili='MAE_physical_ILITOTAL'))
    nh['cohort']='CPU_EXPLORATORY_20261030';nh['model_instance_id']='CPU_20261030::'+nh.model;nh['n_raw_seeds']=3
    perL=pd.concat([oh,nh],ignore_index=True).drop(columns=['rank'],errors='ignore')
    perL['rank_MSE_within_L_cohort']=perL.groupby(['cohort','L']).mse.rank(method='min').astype(int)
    perL.to_csv(out/'EXPANDED_COMBINED_PER_HORIZON.csv',index=False)
    profile=perL.pivot(index=['model_instance_id','model','cohort'],columns='L',values='mse')
    profile['mean_MSE_4L']=profile[list(HORIZONS)].mean(1)
    profile['best_L']=profile[list(HORIZONS)].idxmin(1);profile['worst_L']=profile[list(HORIZONS)].idxmax(1)
    profile.to_csv(out/'EXPANDED_COMBINED_MSE_PROFILES.csv')
    norm=profile[list(HORIZONS)].div(profile.mean_MSE_4L,axis=0);norm.to_csv(out/'EXPANDED_COMBINED_NORMALIZED_PROFILES.csv')
    oldev=pd.read_csv(root/'04_benchmark/TRACK_C_PTE_PIE_PER_EVENT.csv');oldev['cohort']='TRACK_C';oldev['model_instance_id']='TRACK_C::'+oldev.model
    newev=pd.read_csv(prior/'results/expanded_all_peak_events.csv');newev=newev[newev.model!='PeakBlend'].copy()
    newev['cohort']='CPU_EXPLORATORY_20261030';newev['model_instance_id']='CPU_20261030::'+newev.model
    events=pd.concat([oldev,newev],ignore_index=True);pks=[]
    for (iid,model,cohort,L),g in events.groupby(['model_instance_id','model','cohort','L']):
        for version,pte,pie in [('LITERATURE_PTE1_PIE25',1,25),('PROJECT_CUSTOM_PTE2_PIE20',2,20)]:
            s=summarize(g,pte,pie,frozen=(version.startswith('LITERATURE')))
            # Only custom errors derived from archive CSV have two-decimal precision.
            pks.append(dict(model_instance_id=iid,model=model,cohort=cohort,L=L,forecast_lead_k=1,
                criteria_version=version,mean_PTE_pass=(s['mean_PTE_wk']<=pte) if pd.notna(s['mean_PTE_wk']) else None,
                mean_PIE_pass=(s['mean_PIE_pct']<=pie) if pd.notna(s['mean_PIE_pct']) else None,
                criteria_judgment='event-level AND; mean pass fields diagnostic only',**s))
    pk=pd.DataFrame(pks);pk.to_csv(out/'EXPANDED_COMBINED_PTE_PIE_ALL_CRITERIA.csv',index=False)
    pk[pk.criteria_version=='LITERATURE_PTE1_PIE25'].to_csv(out/'EXPANDED_COMBINED_PTE_PIE_PER_MODEL_L.csv',index=False)
    c=pd.read_csv(prior/'results/expanded_cost_summary.csv')
    c['model_instance_id']='CPU_20261030::'+c.model;c['cost_cohort']='CPU_SHARED_HOST_20261030'
    c['time_unit']='CPU wall seconds per model/L/seed cell';c['pareto_cost']=c.fit_val_seconds_mean
    c=c.merge(ranking[['model_instance_id','mean_Test_MSE_4L']],on='model_instance_id')
    c['pareto_nondominated_within_cost_cohort']=nondominated(c,'pareto_cost','mean_Test_MSE_4L')
    c['measured_vs_estimated']='measured, concurrent host load; approximate timings'
    costs=[c]
    mm=pd.read_csv(root/'08_paper_tables/TRACK_C_MIFLU_RUN_MATRIX.csv')
    costs.append(pd.DataFrame([dict(model='miflu',model_instance_id='TRACK_C::miflu',cost_cohort='ARCHIVED_A100_TRACK_C',
        mean_Test_MSE_4L=float(old[old.model=='miflu'].mean_Test_MSE_4L.iloc[0]),
        fit_val_seconds_mean=mm.wall_seconds.mean(),fit_val_seconds_total=mm.wall_seconds.sum(),
        gpu_hours_total=mm.wall_seconds.sum()/3600,parameters_min=mm.total_parameters.min(),parameters_max=mm.total_parameters.max(),
        pareto_cost=np.nan,pareto_nondominated_within_cost_cohort=None,
        measured_vs_estimated='archived wall seconds; scope may include scoring/writing, not comparable to CPU fit-only cost',
        time_unit='A100 wall seconds; not used in CPU frontier',uses_text=True,FLOPs='unmeasured')]))
    for name in old.model:
        if name!='miflu':costs.append(pd.DataFrame([dict(model=name,model_instance_id='TRACK_C::'+name,cost_cohort='ARCHIVED_COST_UNAVAILABLE',
            mean_Test_MSE_4L=float(old[old.model==name].mean_Test_MSE_4L.iloc[0]),measured_vs_estimated='NA: original training cost not packaged')]))
    pd.concat(costs,ignore_index=True).to_csv(out/'EXPANDED_COST_ACCURACY_PARETO.csv',index=False)
    # Frozen Track C filenames remain their original scope and content.
    for p in (root/'08_paper_tables').glob('TRACK_C_*.csv'):
        import shutil;shutil.copyfile(p,out/p.name)
    result=dict(combined_model_instances=len(ranking),original_track_c_instances=len(old),new_cpu_instances=cpu.model.nunique(),
        combined_per_L_rows=len(perL),literature_peak_rows=len(pk[pk.criteria_version=='LITERATURE_PTE1_PIE25']),
        caveat='Combined ordering descriptive only; retain protocol-specific ranks and separate cost cohorts',
        reproduction_status='PARTIAL_REPRODUCTION',project_author='CHAN Sing Yeung Sunny')
    (out/'INTEGRATION_MANIFEST.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['handoff','prior','target-scores','out']:p.add_argument('--'+n,required=True)
    main(p.parse_args())
