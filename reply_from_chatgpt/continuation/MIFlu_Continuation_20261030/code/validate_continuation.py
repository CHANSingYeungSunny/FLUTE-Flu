"""Validate scientific contracts, provenance and ready-to-submit file syntax."""
import argparse,ast,json,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from common import *

def main(a):
    root=Path(a.root);load_data(root/'inputs/handoff');checks={}
    p=json.loads((root/'04_benchmark/peak_criteria.json').read_text())
    primary=p['CONSENSUS']['models']
    assert p['CONSENSUS']['forecast_lead_k_weeks']==1
    for m,n in [('miflu',15),('dlinear',31),('nlinear',36)]:assert primary[m]['overall']['n_hit']==n
    for m,g in primary.items():
        assert sum(v['n_hit'] for v in g['per_L'].values())==g['overall']['n_hit']
        assert sum(v['n_true_peaks'] for v in g['per_L'].values())==36
    checks['peak_consensus_and_per_L_totals']='PASS'
    rank=pd.read_csv(root/'paper_tables/EXPANDED_COMBINED_TEST_MSE_RANKING.csv')
    perL=pd.read_csv(root/'paper_tables/EXPANDED_COMBINED_PER_HORIZON.csv')
    pk=pd.read_csv(root/'paper_tables/EXPANDED_COMBINED_PTE_PIE_PER_MODEL_L.csv')
    assert len(rank)==19 and rank.model_instance_id.nunique()==19
    assert len(perL)==76 and perL.groupby('model_instance_id').size().eq(4).all()
    assert len(pk)==76 and pk.forecast_lead_k.eq(1).all()
    assert set(rank.cohort)=={'TRACK_C','CPU_EXPLORATORY_20261030'}
    for i,g in perL.groupby('model_instance_id'):
        r=rank[rank.model_instance_id==i].iloc[0]
        np.testing.assert_allclose(g.mse.mean(),r.mean_Test_MSE_4L,rtol=1e-12)
    checks['combined_tables_19_instances_76_model_L_rows']='PASS'
    il=pd.read_csv(root/'paper_tables/TRACK_C_ILITOTAL_MSE_MAE.csv')
    assert il.MSE_z_ILITOTAL.notna().sum()==1 and il.iloc[0].model=='miflu'
    np.testing.assert_allclose(il.iloc[0].MSE_physical_ILITOTAL,il.iloc[0].MSE_z_ILITOTAL*9003.15234375**2)
    checks['target_conversion_and_no_missing_raw_imputation']='PASS'
    registry=json.loads((root/'protocol/llm_registry.json').read_text())
    assert len(registry['models']['deepseek']['revision'])==40
    for m in registry['models'].values():
        for f,h in m['custom_source_sha256'].items():
            src=root/'protocol/model_source'/(m['repo_id'].replace('/','__')+'__'+f)
            assert sha(src)==h
    checks['pinned_custom_model_source_hashes']='PASS'
    for sh in (root/'hpc').glob('*.sh'):
        subprocess.run(['bash','-n',str(sh)],check=True)
        s=sh.read_text()
        if '#SBATCH' in s:
            assert '--gres=gpu:a100:1' in s and '--partition=stingy' in s
            assert '--array' not in s.split('set -')[0]
        assert 'rm -rf' not in s and 'rsync --delete' not in s
    checks['shell_syntax_explicit_single_A100_no_arrays']='PASS'
    for py in (root/'code').rglob('*.py'):ast.parse(py.read_text())
    checks['python_source_parse']='PASS'
    # Model source import and tiny-model runtime checks are a separate genuine
    # local runtime result, not a substitute for complete GPU/checkpoint runs.
    sp=root/'results/prepared_model_smoke_tests.json'
    if sp.exists():
        smoke=json.loads(sp.read_text());assert all(v.startswith('PASS') for k,v in smoke.items() if k!='environment')
        checks['tiny_random_model_runtime_tests']='PASS; full pretrained GPU jobs NOT RUN'
    else:raise AssertionError('Prepared model runtime smoke-test evidence missing')
    checks['cluster_submission']='NOT_ATTEMPTED: user requested preparation; network unavailable'
    checks['full_C2_or_LLM_MSE']='UNAVAILABLE: no full experiment executed'
    (root/'results/CONTINUATION_VERIFICATION.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);main(p.parse_args())
