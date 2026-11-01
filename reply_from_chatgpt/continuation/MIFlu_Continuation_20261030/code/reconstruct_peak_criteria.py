"""Reconstruct a versioned consensus artifact from frozen event/summary evidence.

This is a new documented schema, NOT a claim to recover the missing original
JSON bytes/schema. Means condition on matched events; hits include misses in
the denominator. L is the trained output length; actual measured lead is k=1.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def clean(v):
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,list):return [clean(x) for x in v]
    if isinstance(v,(np.integer,)):return int(v)
    if isinstance(v,(np.floating,float)):return float(v) if np.isfinite(v) else None
    if isinstance(v,np.bool_):return bool(v)
    return v

def summarize(g,pte,pie,frozen=False):
    truth=g[g.true_row.notna()];matched=truth[truth.PTE_wk.notna() & truth.PIE_pct.notna()]
    passing=(truth.PTE_wk<=pte)&(truth.PIE_pct<=pie)
    if frozen:
        assert np.array_equal(passing.to_numpy(),truth.status.eq('Hit').to_numpy())
        hits=int(truth.status.eq('Hit').sum())
    else:hits=int(passing.sum())
    # PIE is rounded to 0.01 percentage points in CSV. Identify threshold
    # uncertainty instead of claiming raw precision for newly derived criteria.
    uncertain=int(((matched.PIE_pct-pie).abs()<=.005+1e-12).sum())
    return dict(n_true_peaks=len(truth),n_matched=len(matched),n_missed=len(truth)-len(matched),
        n_false_peaks=int(g.status.eq('FalsePeak').sum()),n_hit=hits,
        hit_rate_pct=100*hits/len(truth) if len(truth) else None,
        mean_PTE_wk=matched.PTE_wk.mean(),mean_PIE_pct=matched.PIE_pct.mean(),
        means_scope='matched true peaks only; pooled event means, not mean of rounded cell means',
        rounded_PIE_threshold_ambiguous_events=uncertain,
        hit_precision='frozen literature statuses verified against rounded errors' if frozen else 'recomputed from 2-decimal event PIE; ambiguity count disclosed')

def main(a):
    root=Path(a.handoff)/'04_benchmark';out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    names=['TRACK_C_PTE_PIE_PER_EVENT.csv','TRACK_C_PTE_PIE_PASS_MATRIX.csv','PTE_PIE_by_model.csv','PTE_PIE_per_cell.csv','PTE_PIE_METHOD.json']
    ev=pd.read_csv(root/names[0]);matrix=pd.read_csv(root/names[1]);overall=pd.read_csv(root/names[2]);cells=pd.read_csv(root/names[3])
    criteria={};tab=[]
    for version,pte,pie in [('LITERATURE_PTE1_PIE25',1,25),('PROJECT_CUSTOM_PTE2_PIE20',2,20)]:
        models={}
        for model,g in ev.groupby('model',sort=False):
            s=summarize(g,pte,pie,version.startswith('LITERATURE'))
            ms=matrix[matrix.model==model].iloc[0];os=overall[overall.model==model].iloc[0]
            if version.startswith('LITERATURE'):
                assert s['n_hit']==ms.literature_hits_PTE1_PIE25==os.n_hit
                assert s['n_true_peaks']==ms.n_true_peaks==os.n_true_peaks==36
                assert abs(s['hit_rate_pct']-float(ms.literature_hit_rate_pct))<=.051
            byL={}
            for L,gl in g.groupby('L'):
                sl=summarize(gl,pte,pie,version.startswith('LITERATURE'))
                cg=cells[(cells.model==model)&(cells.L==L)]
                if version.startswith('LITERATURE'):assert sl['n_hit']==int(cg.n_hit.sum())
                sl['per_seed']={str(int(seed)):summarize(gs,pte,pie,version.startswith('LITERATURE')) for seed,gs in gl.groupby('seed')}
                byL[str(int(L))]=sl
                tab.append(dict(model=model,L=int(L),forecast_lead_k=1,criteria_version=version,**{k:v for k,v in sl.items() if k!='per_seed'}))
            s['reported_mean_of_cell_PTE_wk']=float(os.mean_of_cell_PTE_wk)
            s['reported_mean_of_cell_PIE_pct']=float(os.mean_of_cell_PIE_pct)
            models[model]=dict(overall=s,per_L=byL)
        criteria[version]=dict(PTE_max_weeks=pte,PIE_max_pct=pie,operator='AND',judgment_unit='per true peak',models=models)
    payload=dict(schema_version='reconstructed-consensus/1.0',
        artifact_status='RECONSTRUCTED_FROM_FROZEN_CSV_NOT_ORIGINAL_JSON_RECOVERY',
        project_author='CHAN Sing Yeung Sunny',project_type='Final Year Project',
        reference_paper_authors='Moon, Shim, Kim & Hwang',
        reproduction_status='PARTIAL_REPRODUCTION',text_pathway_status='UNRESOLVED',
        UNIFIED_PAIR_KEY='966|L24|seed42',
        dataset_sha256='2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5',
        CONSENSUS=dict(selected_criteria_version='LITERATURE_PTE1_PIE25',
            models=criteria['LITERATURE_PTE1_PIE25']['models'],
            forecast_lead_k_weeks=1,output_window_lengths_L=[24,36,48,60],seeds=[42,43,44],
            variable='ILITOTAL',feature_index=4,units='physical surveillance ILI visit counts',
            provenance='Event hits corroborated against pass matrix and by-model summary; per-L hits checked against per-cell table',
            criteria_versions=criteria),
        notes=[
            'NLinear 36/36; DLinear 31/36; MIFlu 15/36 under literature joint criterion.',
            'This measures actual one-week lead k=1, not 24–60-week lead peak skill.',
            'The joint AND composite is the project application of two Kramer & Shaman 2019 tolerances.',
            'Custom PTE<=2/PIE<=20 is a project convention, not the literature criterion.',
            'Means exclude unmatched peaks; mean PASS does not replace event-level hit judgment.',
            'Three true seasonal peaks recur across seeds/windows; 36 records are not independent epidemics.',
            'Frozen matcher +/-2 weeks and greedy above-mean picker preserved; min_sep40 masks +/-20, not true 40-week separation.',
            'Reported mean-of-cell errors retained separately; they differ from pooled matched-event means.'
        ],source_files=[dict(path='04_benchmark/'+n,sha256=sha(root/n)) for n in names])
    out.write_text(json.dumps(clean(payload),indent=2,ensure_ascii=False,allow_nan=False))
    pd.DataFrame(tab).to_csv(out.with_name('PEAK_CRITERIA_PER_MODEL_L.csv'),index=False)
    summary=pd.DataFrame([dict(model=m,**v['overall']) for m,v in criteria['LITERATURE_PTE1_PIE25']['models'].items()])
    summary.to_csv(out.with_name('PEAK_CRITERIA_CONSENSUS_SUMMARY.csv'),index=False)
    print(summary[['model','n_hit','n_true_peaks','hit_rate_pct']].to_string(index=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--handoff',required=True);p.add_argument('--out',required=True);main(p.parse_args())
