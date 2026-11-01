"""Create portable continuation archive with source/input/output SHA256 records."""
import argparse,json,zipfile
from pathlib import Path
from common import sha

def main(a):
    root=Path(a.root).resolve();dest=Path(a.zip).resolve()
    if dest.is_relative_to(root):raise ValueError('Archive must be outside its source directory')
    files=[p for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
           and p.name!='FILE_SHA256_MANIFEST.json']
    manifest=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
    mp=root/'FILE_SHA256_MANIFEST.json';mp.write_text(json.dumps(manifest,indent=2));files.append(mp)
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,'MIFlu_Continuation_20261030/'+str(p.relative_to(root)))
    with zipfile.ZipFile(dest) as z:assert z.testzip() is None
    print(json.dumps(dict(path=str(dest),bytes=dest.stat().st_size,sha256=sha(dest),entries=len(files))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--zip',required=True);main(p.parse_args())
