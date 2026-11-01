"""Strict author-966 contract. All arrays use (origin, lead, variable).

L is an output-window length; k (1..L) is a forecast lead. Do not conflate them.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

DATA_SHA = '2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5'
UNIFIED_PAIR_KEY = '966|L24|seed42'  # reference anchor; each cell keeps its real L/seed
SPLITS = {'train': (0, 676), 'validation': (676, 773), 'test': (773, 966)}
HORIZONS = (24, 36, 48, 60)
SEEDS = (42, 43, 44)
T = 104
N = 7
ILI = 4
FEATURES = ['% WEIGHTED ILI', '% UNWEIGHTED ILI', 'AGE 0-4', 'AGE 5-24',
            'ILITOTAL', 'NUM. OF PROVIDERS', 'OT']

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(2**20), b''): h.update(b)
    return h.hexdigest()

def load_data(root):
    root = Path(root)
    p = root/'02_author_repo/code/dataset/illness/national_illness.csv'
    if sha(p) != DATA_SHA: raise ValueError('Official dataset SHA256 mismatch')
    df = pd.read_csv(p)
    x = df.iloc[:, 1:].to_numpy(dtype=np.float64)
    if x.shape != (966, 7) or not np.isfinite(x).all():
        raise ValueError('Strict 966 x 7 finite-data contract failed')
    # Use the packaged Track C scaler rather than silently substituting a refit.
    sc = json.loads((root/'03_data/scaler_miflu_author966.json').read_text())
    mu, sd = np.array(sc['mean']), np.array(sc['std'])
    np.testing.assert_allclose(mu, x[:676].mean(0), rtol=2e-7)
    np.testing.assert_allclose(sd, x[:676].std(0), rtol=2e-7)
    return x, ((x-mu)/sd).astype(np.float32), mu, sd

def origins(L, split):
    lo, hi = SPLITS[split]
    o = np.arange(max(lo-1, T-1), hi-L, dtype=np.int64)
    assert ((o+1 >= lo) & (o+L < hi)).all()
    return o

def windows(z, L, split):
    o = origins(L, split)
    return (np.stack([z[v-T+1:v+1] for v in o]),
            np.stack([z[v+1:v+L+1] for v in o]), o)

def score(pred, true, sd):
    if pred.shape != true.shape or pred.ndim != 3 or pred.shape[-1] != 7:
        raise ValueError('Expected matching (origin,lead,7) arrays')
    if not np.isfinite(pred).all() or not np.isfinite(true).all():
        raise ValueError('Non-finite predictions/targets')
    e = pred.astype(np.float64)-true.astype(np.float64)
    ie = e[:, :, ILI]
    return dict(mse_z_all7=float((e**2).mean()), mae_z_all7=float(abs(e).mean()),
                mse_z_ili=float((ie**2).mean()), mae_z_ili=float(abs(ie).mean()),
                mse_counts2_ili=float((ie**2).mean()*sd[ILI]**2),
                mae_counts_ili=float(abs(ie).mean()*sd[ILI]),
                n_origins=len(e), n_elements=e.size)

def pick_peaks(v, min_sep=40, floor=None):
    """Frozen legacy picker, reproduced exactly, including its half-distance mask.

    IMPORTANT: min_sep=40 masks +/-20, hence the actual enforced spacing is
    21 positions, NOT 40. This is a documented legacy defect, not a new claim.
    """
    v = np.asarray(v, float)
    if not len(v): return []
    work = v.copy(); floor = v.mean() if floor is None else floor
    out = []; half = min_sep//2
    while np.isfinite(work).any():
        i = int(np.argmax(work))
        if work[i] < floor or not np.isfinite(work[i]): break
        out.append(i)
        work[max(0,i-half):min(len(v),i+half+1)] = -np.inf
    return sorted(out)

def peak_events(rows, truth, pred, model, L, seed, metric='legacy_k1'):
    tp, pp = pick_peaks(truth), pick_peaks(pred)
    used = set(); events = []
    for ti in tp:
        candidates = [pi for pi in pp if pi not in used and abs(rows[pi]-rows[ti]) <= 2]
        pi = min(candidates, key=lambda i: abs(rows[i]-rows[ti])) if candidates else None
        r = dict(model=model,L=L,seed=seed,metric=metric,true_row=int(rows[ti]),
                 true_val=float(truth[ti]), pred_row=np.nan,pred_val=np.nan,
                 PTE_wk=np.nan,PIE_pct=np.nan,status='Missed')
        if pi is not None:
            used.add(pi); pte = abs(int(rows[pi]-rows[ti]))
            pie = abs(float(pred[pi]-truth[ti]))/abs(float(truth[ti]))*100
            r.update(pred_row=int(rows[pi]),pred_val=float(pred[pi]),PTE_wk=pte,
                     PIE_pct=pie,status='Hit' if pte <= 1 and pie <= 25 else 'MatchedNotHit')
        events.append(r)
    for pi in pp:
        if pi not in used:
            events.append(dict(model=model,L=L,seed=seed,metric=metric,true_row=np.nan,
                true_val=np.nan,pred_row=int(rows[pi]),pred_val=float(pred[pi]),
                PTE_wk=np.nan,PIE_pct=np.nan,status='FalsePeak'))
    return events

def peak_summary(events):
    """Pool event values, NOT rounded cell means; misses remain in hit denominator.

    Mean-pass columns are diagnostics, never substitutes for event-level hits.
    PTE/PIE means are conditional on a match within +/-2 weeks.
    """
    rows = []
    for (m,L), g in events.groupby(['model','L'],sort=False):
        truth = g[g.true_row.notna()]; matched = truth[truth.PTE_wk.notna()]
        pte, pie = matched.PTE_wk.mean(), matched.PIE_pct.mean()
        flag = lambda v,t: 'NA' if pd.isna(v) else ('PASS' if v <= t else 'FAIL')
        rows.append(dict(model=m,L=int(L),mean_PTE_wk=pte,mean_PIE_pct=pie,
            mean_PTE_le1=flag(pte,1),mean_PIE_le25=flag(pie,25),
            mean_combined=('NA' if not len(matched) else
                           'PASS' if pte <= 1 and pie <= 25 else 'FAIL'),
            n_true=len(truth),n_matched=len(matched),n_missed=len(truth)-len(matched),
            n_false=int((g.status=='FalsePeak').sum()),n_hit=int((truth.status=='Hit').sum()),
            hit_rate_pct=100*(truth.status=='Hit').mean()))
    return pd.DataFrame(rows)

def table(df, formats=None):
    """Stable Markdown formatting with four decimals; percentages use two."""
    formats = formats or {}
    def fmt(c,v):
        if pd.isna(v): return 'NA'
        if isinstance(v,(float,np.floating)): return format(v,formats.get(c,'.4f'))
        return str(v).replace('|','\\|')
    lines = ['| '+' | '.join(map(str,df.columns))+' |',
             '| '+' | '.join(['---']*len(df.columns))+' |']
    lines += ['| '+' | '.join(fmt(c,v) for c,v in zip(df.columns,r))+' |'
              for r in df.itertuples(index=False,name=None)]
    return '\n'.join(lines)
