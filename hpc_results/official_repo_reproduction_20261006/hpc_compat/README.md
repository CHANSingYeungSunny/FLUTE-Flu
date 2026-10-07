# hpc_compat — compatibility layer for replaying the author's released code

Placed FIRST on `PYTHONPATH` so nothing is written into the author's tree.
`sitecustomize.py` is imported automatically by CPython at startup when this
directory is on `PYTHONPATH`; it restores the NumPy 2.0-removed aliases and the
peft `prepare_model_for_int8_training` symbol (referenced only in a comment).

`einops.py` and `embed.py` are used ONLY when the real modules are absent.
Set by the sbatch scripts; every run records `compat_dir` and
`dead_import_shims` in its JSON so a reader can see exactly what was stood in for.
