"""Explicit pinned snapshot download for an online staging node; no API inference."""
import argparse,json
from pathlib import Path

def main(a):
    from huggingface_hub import snapshot_download
    cfg=json.loads(Path(a.registry).read_text());m=cfg['models'][a.model]
    path=snapshot_download(repo_id=m['repo_id'],revision=m['revision'],cache_dir=a.cache_dir,
        allow_patterns=['*.json','*.safetensors','*.model','*.txt','*.py','LICENSE*','README.md'],
        ignore_patterns=['*.bin','*.h5','*.msgpack'])
    from common import sha
    for f,h in m['custom_source_sha256'].items():
        if sha(Path(path)/f)!=h:raise SystemExit('Custom source hash mismatch: '+f)
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    manifest=[dict(path=str(p.relative_to(path)),bytes=p.stat().st_size,sha256=sha(p))
              for p in sorted(Path(path).rglob('*')) if p.is_file()]
    Path(a.out).write_text(json.dumps(dict(alias=a.model,repo_id=m['repo_id'],revision=m['revision'],snapshot_path=path,
        snapshot_files=manifest,manifest_scope='Full staged snapshot SHA256, generated once after download'),indent=2))
    print(path)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--registry',required=True);p.add_argument('--model',choices=['qwen','deepseek'],required=True)
    p.add_argument('--cache-dir',required=True);p.add_argument('--out',required=True);main(p.parse_args())
