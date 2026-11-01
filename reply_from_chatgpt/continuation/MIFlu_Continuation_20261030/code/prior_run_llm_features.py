"""Ready-to-run local-snapshot LLM paired experiment; no download or API call.

Encoding-only and generation-augmented arms use the SAME pinned instruct
checkpoint and downstream random forest. Requires an absolute local snapshot
path and explicit immutable revision metadata. Uses only observed windows.
This code is supplied for HPC continuation; results are NOT claimed until run.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from common import *

def prompt_for_window(x,L):
    """All values are z-space observed inputs; no future outcomes or calendar dates."""
    stats=[]
    for i,f in enumerate(FEATURES):
        a=x[:,i]
        stats.append(dict(variable=f,last=round(float(a[-1]),4),mean=round(float(a.mean()),4),
            sd=round(float(a.std()),4),change4=round(float(a[-1]-a[-5]),4),
            change13=round(float(a[-1]-a[-14]),4),min=round(float(a.min()),4),max=round(float(a.max()),4),
            last13=[round(float(v),3) for v in a[-13:]]))
    return ('US CDC National-Illness, seven weekly variables. Values are standardized using training rows only. '
            f'Only the previous 104 observations are available. Forecasting window length: {L} weeks. '
            'Do not infer dates, consult memorized historical outcomes, or use future observations. '
            'Observed summaries: '+json.dumps(stats,separators=(',',':')))

def main(a):
    import re
    if not re.fullmatch(r'[0-9a-fA-F]{40}',a.revision):
        raise SystemExit('Supply the immutable 40-character model commit, not a moving revision label')
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.decomposition import PCA
    snap=Path(a.snapshot).resolve()
    if not snap.is_dir():raise SystemExit('Local checkpoint absent; no network download attempted')
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    raw,z,mu,sd=load_data(a.handoff);torch.manual_seed(42)
    tok=AutoTokenizer.from_pretrained(snap,local_files_only=True)
    if tok.pad_token_id is None:tok.pad_token=tok.eos_token
    model=AutoModelForCausalLM.from_pretrained(snap,local_files_only=True,
        torch_dtype=torch.bfloat16 if a.device.startswith('cuda') else torch.float32).to(a.device).eval()
    for p in model.parameters():p.requires_grad=False
    asset=[dict(path=str(p.relative_to(snap)),sha256=sha(p)) for p in sorted(snap.rglob('*')) if p.is_file()]
    (out/'asset_manifest.json').write_text(json.dumps(dict(model_id=a.model_id,revision=a.revision,files=asset),indent=2))
    metrics=[];costs=[];peaks=[]
    for L in HORIZONS:
        data={s:windows(z,L,s) for s in SPLITS}
        for mode in ['encoding_only','generation_augmented']:
            encoded={};generation_cost=0;cache=[]
            start=time.perf_counter()
            for split,(x,y,o) in data.items():
                features=[]
                for xx,oo in zip(x,o):
                    prompt=prompt_for_window(xx,L)
                    generated=''
                    if mode=='generation_augmented':
                        instruction=prompt+'\nReturn a concise structured analysis (at most 96 tokens) of observed trend, seasonal clues, and uncertainty. No unobserved facts or future numbers.'
                        inp=tok.apply_chat_template([dict(role='user',content=instruction)],tokenize=True,return_tensors='pt',add_generation_prompt=True).to(a.device)
                        with torch.no_grad():ids=model.generate(inp,max_new_tokens=96,do_sample=False,pad_token_id=tok.pad_token_id)
                        generated=tok.decode(ids[0,inp.shape[1]:],skip_special_tokens=True)
                        generation_cost+=ids.shape[1]-inp.shape[1]
                    text=prompt+('\nStructured analysis: '+generated if generated else '')
                    batch=tok(text,return_tensors='pt',truncation=True,max_length=2048).to(a.device)
                    with torch.no_grad():
                        hs=model.base_model(**batch).last_hidden_state
                    features.append(hs.mean(1).float().cpu().numpy()[0])
                    cache.append(dict(split=split,origin=int(oo),L=L,mode=mode,prompt=prompt,generated=generated,
                        input_sha256=hashlib.sha256(text.encode()).hexdigest()))
                encoded[split]=np.stack(features)
            encoding_seconds=time.perf_counter()-start
            # Train-only PCA aligns dimensions for all language models.
            pca=PCA(n_components=16,svd_solver='full').fit(encoded['train'])
            f={s:np.concatenate([data[s][0].reshape(len(data[s][0]),-1),pca.transform(encoded[s])],1) for s in data}
            np.savez_compressed(out/f'features_{mode}_L{L}.npz',**encoded)
            (out/f'text_cache_{mode}_L{L}.json').write_text(json.dumps(cache,indent=2))
            for seed in SEEDS:
                t0=time.perf_counter();y=data['train'][1]
                reg=RandomForestRegressor(n_estimators=64,max_depth=8,min_samples_leaf=3,max_features=.5,random_state=seed,n_jobs=2)
                reg.fit(f['train'],y.reshape(len(y),-1))
                vy=data['validation'][1];vp=reg.predict(f['validation']).reshape(vy.shape)
                # No configuration search here; validation is reported, test once.
                ty=data['test'][1];t1=time.perf_counter();pred=reg.predict(f['test']).reshape(ty.shape)
                infer=time.perf_counter()-t1
                name=a.model_id.replace('/','__')+'_'+mode
                metrics.append(dict(track='LLM_FEATURE_EXPLORATORY_966',model=name,L=L,seed=seed,
                    model_revision=a.revision,mode=mode,uses_text=True,val_mse=float(((vp-vy)**2).mean()),**score(pred,ty,sd)))
                np.savez_compressed(out/f'{mode}_L{L}_s{seed}.npz',pred=pred,target=ty,origins=data['test'][2])
                costs.append(dict(model=name,L=L,seed=seed,feature_seconds_shared=encoding_seconds,
                    generated_tokens_shared=int(generation_cost),downstream_seconds=time.perf_counter()-t0,
                    inference_seconds=infer,llm_parameters=sum(p.numel() for p in model.parameters()),
                    device=a.device,flops=None,note='feature cost shared across seeds; do not count three times'))
                peaks+=peak_events(data['test'][2]+1,ty[:,0,ILI]*sd[ILI]+mu[ILI],pred[:,0,ILI]*sd[ILI]+mu[ILI],name,L,seed)
                pd.DataFrame(metrics).to_csv(out/'llm_metrics.csv',index=False)
                pd.DataFrame(costs).to_csv(out/'llm_cost.csv',index=False)
                pd.DataFrame(peaks).to_csv(out/'llm_peak_events.csv',index=False)
    peak_summary(pd.DataFrame(peaks)).to_csv(out/'llm_peak_by_L.csv',index=False)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for x in ['handoff','out','snapshot','model-id','revision']:p.add_argument('--'+x,required=True)
    p.add_argument('--device',default='cuda');main(p.parse_args())
