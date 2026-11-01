"""Fail before fitting on wrong hardware/data or unavailable required assets."""
import argparse,importlib.metadata,json,os,platform,socket
from pathlib import Path
from common import load_data,sha,DATA_SHA

def main(a):
    import torch
    if not os.getenv('SLURM_JOB_ID'):raise SystemExit('Run model preflight inside an allocated Slurm compute job')
    if socket.gethostname().lower().startswith('hpclogin'):raise SystemExit('No model compute on login node')
    if not torch.cuda.is_available():raise SystemExit('CUDA is required; no silent CPU fallback')
    gpu=torch.cuda.get_device_name(0)
    if 'A100' not in gpu:raise SystemExit('Guide requires A100 allocation, got '+gpu)
    root=Path(a.root);load_data(root/'inputs/handoff')
    packages={}
    for p in ['torch','transformers','peft','einops','numpy','pandas','scikit-learn','accelerate']:
        try:packages[p]=importlib.metadata.version(p)
        except importlib.metadata.PackageNotFoundError:packages[p]=None
    cache_commit=None
    if a.kind=='c2':
        from transformers import GPT2Config
        cfg=GPT2Config.from_pretrained('gpt2',local_files_only=True)
        cache_commit=getattr(cfg,'_commit_hash',None)
        if cfg.n_embd!=768:raise SystemExit('Wrong GPT2 hidden size')
        for p in ['torch','transformers','peft','einops','numpy','pandas']:
            if packages[p] is None:raise SystemExit('Missing C2 dependency '+p)
    record=dict(host=socket.gethostname(),gpu=gpu,gpu_total_memory_bytes=torch.cuda.get_device_properties(0).total_memory,
        python=platform.python_version(),packages=packages,HF_HOME=os.getenv('HF_HOME'),GPT2_cached_config_commit=cache_commit,
        dataset_sha256=DATA_SHA,slurm_job_id=os.getenv('SLURM_JOB_ID'),
        project_author='CHAN Sing Yeung Sunny',text_pathway_status='UNRESOLVED',reproduction_status='PARTIAL_REPRODUCTION')
    Path(a.out).write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--kind',choices=['c2','llm'],required=True);p.add_argument('--out',required=True);main(p.parse_args())
