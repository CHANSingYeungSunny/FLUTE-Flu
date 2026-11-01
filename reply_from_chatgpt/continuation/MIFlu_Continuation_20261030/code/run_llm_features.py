"""Resumable per-model/L/arm adaptation of the previously supplied LLM runner.

DeepSeek uses its pinned local custom code; no API or online load in GPU jobs.
Features are deterministic, observed-input-only and cached before test scoring.
"""
from __future__ import annotations
import argparse,hashlib,importlib.metadata,json,os,sqlite3,time
from pathlib import Path
import numpy as np
import pandas as pd
from common import *
from prior_run_llm_features import prompt_for_window

def main(a):
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from sklearn.decomposition import PCA
    from sklearn.ensemble import RandomForestRegressor
    cfg=json.loads(Path(a.registry).read_text());m=cfg['models'][a.model]
    snap=Path(a.snapshot).resolve();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    if snap.name!=m['revision']:
        raise SystemExit('Use the pinned Hugging Face snapshots/<revision> directory recorded by the downloader')
    if sha(snap/'config.json')!=m['config_sha256']:
        raise SystemExit('Pinned model configuration mismatch')
    for f,h in m['custom_source_sha256'].items():
        if sha(snap/f)!=h:raise SystemExit('Pinned DeepSeek source mismatch: '+f)
    identity=dict(model=a.model,repo_id=m['repo_id'],revision=m['revision'],L=a.horizon,mode=a.mode,
        registry_sha256=sha(a.registry),runner_sha256=sha(__file__),prior_prompt_source_sha256=sha(Path(__file__).with_name('prior_run_llm_features.py')),
        dataset_sha256=DATA_SHA,UNIFIED_PAIR_KEY=UNIFIED_PAIR_KEY,track='LLM_FEATURE_EXPLORATORY_966',
        cell_protocol='3 matched downstream seeds; feature cache shared; test once per frozen estimator')
    ip=out/'identity.json'
    if ip.exists() and json.loads(ip.read_text())!=identity:raise SystemExit('Output belongs to another configuration; use a fresh directory')
    ip.write_text(json.dumps(identity,indent=2))
    if (out/'COMPLETE.json').exists():print('Complete arm retained; no test reevaluation');return
    raw,z,mu,sd=load_data(a.handoff);L=a.horizon
    data={s:windows(z,L,s) for s in SPLITS}
    db=sqlite3.connect(out/'features.sqlite3')
    db.execute('CREATE TABLE IF NOT EXISTS features (split TEXT, origin INTEGER, vector BLOB, prompt TEXT, generated TEXT, input_hash TEXT, encoding_seconds REAL, generation_seconds REAL, input_tokens INTEGER, generated_tokens INTEGER, PRIMARY KEY(split,origin))')
    torch.manual_seed(42)
    model=None;tok=None;device=torch.device(a.device)
    if device.type=='cuda' and not torch.cuda.is_available():raise SystemExit('Requested GPU unavailable; no silent CPU fallback')
    def ensure_model():
        nonlocal model,tok
        if model is not None:return
        if device.type=='cuda':torch.cuda.reset_peak_memory_stats()
        tok=AutoTokenizer.from_pretrained(snap,local_files_only=True,trust_remote_code=m['trust_remote_code'])
        if tok.pad_token_id is None:tok.pad_token=tok.eos_token
        model=AutoModelForCausalLM.from_pretrained(snap,local_files_only=True,
            trust_remote_code=m['trust_remote_code'],torch_dtype=torch.bfloat16,
            attn_implementation=cfg['attention'],low_cpu_mem_usage=True,device_map={'':str(device)})
        model.eval()
        for p in model.parameters():p.requires_grad=False
        record=dict(identity=identity,parameters=sum(p.numel() for p in model.parameters()),
            torch=torch.__version__,transformers=importlib.metadata.version('transformers'),
            gpu=torch.cuda.get_device_name() if device.type=='cuda' else None,
            source_files={f:sha(snap/f) for f in m['custom_source_sha256']})
        (out/'runtime.json').write_text(json.dumps(record,indent=2))
    def sync():
        if device.type=='cuda':torch.cuda.synchronize()
    generated_new=0
    for split,(x,y,o) in data.items():
        for xx,oo in zip(x,o):
            if db.execute('SELECT 1 FROM features WHERE split=? AND origin=?',(split,int(oo))).fetchone():continue
            ensure_model();prompt=prompt_for_window(xx,L);generated='';gen_s=0.;nt=0
            if a.mode=='generation_augmented':
                instruction=prompt+'\nReturn a concise structured analysis (at most 96 tokens) of observed trend, seasonal clues, and uncertainty. No unobserved facts or future numbers.'
                text=tok.apply_chat_template([dict(role='user',content=instruction)],tokenize=False,add_generation_prompt=True)
                inp=tok(text,return_tensors='pt',add_special_tokens=False).to(device)
                if inp.input_ids.shape[1]>cfg['max_input_tokens']:raise RuntimeError('Generation prompt exceeds frozen token budget')
                sync();t0=time.perf_counter()
                with torch.inference_mode():
                    ids=model.generate(**inp,max_new_tokens=cfg['max_new_tokens'],do_sample=False,use_cache=True,pad_token_id=tok.pad_token_id)
                sync();gen_s=time.perf_counter()-t0
                nt=ids.shape[1]-inp.input_ids.shape[1]
                generated=tok.decode(ids[0,inp.input_ids.shape[1]:],skip_special_tokens=True)
            text=prompt+('\nStructured analysis: '+generated if generated else '')
            batch=tok(text,return_tensors='pt').to(device)
            if batch.input_ids.shape[1]>cfg['max_input_tokens']:raise RuntimeError('Embedding prompt exceeds frozen budget; no silent truncation of generated features')
            sync();t0=time.perf_counter()
            with torch.inference_mode():
                hidden=model.base_model(**batch,use_cache=False,return_dict=True).last_hidden_state
                feature=hidden.float().mean(1).cpu().numpy()[0]
            sync();encode_s=time.perf_counter()-t0
            db.execute('INSERT INTO features VALUES(?,?,?,?,?,?,?,?,?,?)',(split,int(oo),feature.astype('<f4').tobytes(),prompt,generated,
                hashlib.sha256(text.encode()).hexdigest(),encode_s,gen_s,int(batch.input_ids.shape[1]),int(nt)))
            db.commit();generated_new+=1
            if generated_new%25==0:print(f'{a.model} L{L} {a.mode}: new cached windows {generated_new}',flush=True)
            if a.pilot_windows and generated_new>=a.pilot_windows:
                pilot=dict(status='PILOT_ONLY_NOT_FORECAST_RESULTS',new_windows=generated_new,
                    gpu_peak_allocated_bytes=torch.cuda.max_memory_allocated() if device.type=='cuda' else None,
                    gpu_peak_reserved_bytes=torch.cuda.max_memory_reserved() if device.type=='cuda' else None)
                (out/'PILOT.json').write_text(json.dumps(pilot,indent=2));db.close();print(json.dumps(pilot));return
    encoded={}
    for s,(_,_,o) in data.items():
        rows=[db.execute('SELECT vector FROM features WHERE split=? AND origin=?',(s,int(v))).fetchone() for v in o]
        if any(v is None for v in rows):raise RuntimeError('Incomplete feature cache')
        encoded[s]=np.stack([np.frombuffer(v[0],dtype='<f4') for v in rows])
    q=db.execute('SELECT SUM(encoding_seconds),SUM(generation_seconds),SUM(input_tokens),SUM(generated_tokens),COUNT(*) FROM features').fetchone()
    # Features are shared across seeds. They are counted once in shared_cost.json.
    shared=dict(encoding_seconds=q[0],generation_seconds=q[1],embedding_input_tokens=q[2],generated_tokens=q[3],
        n_windows=q[4],feature_GPU_hours=(q[0]+q[1])/3600 if device.type=='cuda' else 0,
        cost_scope='synchronized feature compute, shared over 3 seeds; excludes model loading/download/queue/PCA/RF',
        gpu_peak_allocated_bytes=torch.cuda.max_memory_allocated() if model is not None and device.type=='cuda' else None,
        gpu_peak_reserved_bytes=torch.cuda.max_memory_reserved() if model is not None and device.type=='cuda' else None,
        peak_memory_note='current invocation only; resumed caches may have been created by earlier invocations')
    (out/'shared_cost.json').write_text(json.dumps(shared,indent=2));db.close()
    # Train-only dimensional alignment; no fitting on validation or test embeddings.
    pca=PCA(n_components=cfg['pca_components'],svd_solver='full').fit(encoded['train'])
    f={s:np.concatenate([data[s][0].reshape(len(data[s][0]),-1),pca.transform(encoded[s])],1) for s in data}
    np.savez_compressed(out/'pca_train_fit.npz',components=pca.components_,mean=pca.mean_)
    metrics=[];events=[]
    for seed in cfg['seeds']:
        mp=out/f'seed{seed}_metrics.json';pp=out/f'seed{seed}_peaks.json'
        if mp.exists():metrics.append(json.loads(mp.read_text()));events+=json.loads(pp.read_text());continue
        y=data['train'][1];t0=time.perf_counter()
        reg=RandomForestRegressor(**cfg['downstream'],random_state=seed,n_jobs=4)
        reg.fit(f['train'],y.reshape(len(y),-1));fit_s=time.perf_counter()-t0
        vy=data['validation'][1];vp=reg.predict(f['validation']).reshape(vy.shape)
        val=float(((vp-vy)**2).mean())
        # Fixed RF configuration; test evaluated once after its fit is frozen.
        ty=data['test'][1];t0=time.perf_counter();pred=reg.predict(f['test']).reshape(ty.shape);infer_s=time.perf_counter()-t0
        name=a.model+'_'+a.mode
        row=dict(model=name,L=L,seed=seed,track='LLM_FEATURE_EXPLORATORY_966',revision=m['revision'],mode=a.mode,
            **score(pred,ty,sd),val_mse=val,rf_fit_seconds=fit_s,rf_test_inference_seconds=infer_s,
            uses_text=True,cell_pair_key=f'966|L{L}|seed{seed}',UNIFIED_PAIR_KEY=UNIFIED_PAIR_KEY,
            project_author='CHAN Sing Yeung Sunny',reproduction_status='PARTIAL_REPRODUCTION',text_pathway_status='UNRESOLVED')
        np.savez_compressed(out/f'seed{seed}_predictions.npz',pred=pred,target=ty,origins=data['test'][2])
        pe=peak_events(data['test'][2]+1,ty[:,0,ILI]*sd[ILI]+mu[ILI],pred[:,0,ILI]*sd[ILI]+mu[ILI],name,L,seed)
        pp.write_text(json.dumps(pe,indent=2));mp.write_text(json.dumps(row,indent=2));metrics.append(row);events+=pe
    pd.DataFrame(metrics).to_csv(out/'LLM_RESULTS_PER_CELL.csv',index=False)
    pd.DataFrame(events).to_csv(out/'LLM_PEAK_EVENTS.csv',index=False)
    peak_summary(pd.DataFrame(events)).to_csv(out/'LLM_PTE_PIE_PER_MODEL_L.csv',index=False)
    (out/'COMPLETE.json').write_text(json.dumps(dict(completed_cells=3,identity=identity),indent=2))
    print('Completed 3 downstream seed cells; features shared and cached.')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['registry','handoff','snapshot','out']:p.add_argument('--'+n,required=True)
    p.add_argument('--model',choices=['qwen','deepseek'],required=True);p.add_argument('--horizon',type=int,choices=HORIZONS,required=True)
    p.add_argument('--mode',choices=['encoding_only','generation_augmented'],required=True)
    p.add_argument('--device',default='cuda');p.add_argument('--pilot-windows',type=int,default=0);main(p.parse_args())
