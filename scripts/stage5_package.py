# -*- coding: utf-8 -*-
"""Stage 5 — dependency-complete, NON-destructive deployment package.

Includes the full scripts tree (packages with __init__.py preserved), data/raw
and the stage5 control files. Extraction on HPC overwrites files only; it never
deletes results or checkpoints.
"""
import hashlib
import io
import json
import os
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = r"C:\Users\Asus\stage5_deploy.tar.gz"   # no spaces -> scp-safe

TARGETS = [
    ("scripts", True),                 # whole tree: packages + __init__.py kept
    ("data/raw", True),
    ("recovery/stage5", True),
]

SKIP_DIRS = {"__pycache__", ".ipynb_checkpoints"}
SKIP_EXT = {".pyc", ".pyo", ".pyd"}

manifest = {}
with tarfile.open(OUT, "w:gz") as tf:
    for rel, _ in TARGETS:
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p):
            tf.add(p, arcname=rel)
            manifest[rel] = hashlib.sha256(open(p, "rb").read()).hexdigest()
            continue
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if os.path.splitext(fn)[1] in SKIP_EXT:
                    continue
                fp = os.path.join(dirpath, fn)
                arc = os.path.relpath(fp, ROOT).replace("\\", "/")
                tf.add(fp, arcname=arc)
                try:
                    manifest[arc] = hashlib.sha256(open(fp, "rb").read()).hexdigest()
                except OSError:
                    pass

with io.open(r"C:\Users\Asus\stage5_deploy_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)
print("packaged %s (%d bytes, %d files)" % (OUT, os.path.getsize(OUT), len(manifest)))
for k in ("scripts/train_miflu.py", "scripts/train_ablation.py",
          "scripts/train_nlinear_966.py", "scripts/train_naive_966.py",
          "scripts/recipes.py", "scripts/early_stopping.py",
          "scripts/configs.py", "scripts/innovation/__init__.py"):
    print("  %-40s %s" % (k, manifest.get(k, "MISSING")))
