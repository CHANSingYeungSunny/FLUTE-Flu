"""New audit tests. These do not replace the original suite omitted from the handoff."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest
path=Path(__file__).resolve().parents[1]/'scripts/verify_snapshot.py'
spec=importlib.util.spec_from_file_location('verify_snapshot',path);a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def test_holm_known_step_down_values():
    np.testing.assert_allclose(a.holm([.04,.01,.02]),[.04,.03,.04])
def test_holm_ties_use_maximum_not_minimum():
    np.testing.assert_allclose(a.holm([.01,.01,.03]),[.03,.03,.03])
def test_exact_twelve_cell_floor_cannot_pass_136_holm():
    p=np.repeat(2/4096,136)
    assert min(a.holm(p))>.05
@pytest.mark.parametrize('p',[[float('nan')],[-.01],[1.1]])
def test_invalid_p_rejected(p):
    with pytest.raises(ValueError):a.holm(p)
def test_csv_facts_and_family_coverage():
    f,_,r=a.facts();assert f['corrected_significant_pairs']==0;assert f['pair_raw_rank']==117
    assert r.loc['nlinear','passes']==4 and r.loc['miflu','passes']==4 and r.loc['patchtst','passes']==0
    assert len(f['pair_models'])==17 and len(r)==28
