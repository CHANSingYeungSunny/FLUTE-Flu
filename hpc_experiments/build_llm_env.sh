#!/bin/bash
# ---------------------------------------------------------------------------
# Build a SEPARATE environment able to load Qwen/Qwen3.8-27B-FP8 (model_type
# 'qwen3_5'). HARD CONSTRAINT: mlflu_hpc (transformers 4.57.6, Python 3.9.25)
# must stay bit-identical - 16 benchmark arms depend on it.
#
# WHY NOT `conda create -n mlflu_llm --clone mlflu_hpc` (the preferred route):
#   1. MEASURED: conda is not available on this cluster any more.
#      - `module load Conda/1.10.0` -> "exists but cannot be loaded" (it is only
#        an extension of IJulia/1.24.2, per `module spider Conda`)
#      - no conda binary anywhere in $HOME; the only modules in MODULEPATH are
#        default / old_modules / ood-desktop / ood-jupyter
#      - the conda trees do exist (/home/sychan552/.conda/{pkgs,envs}), so the
#        cluster's conda tooling was removed after mlflu_hpc was created.
#   2. Even with conda, a clone cannot work: MEASURED from PyPI + GitHub on
#      2026-11-01 -
#         * every transformers 5.x has requires_python >= 3.10
#           (5.21.0+ requires >= 3.11)
#         * the first release shipping src/transformers/models/qwen3_5 is 5.3.0
#         * mlflu_hpc is Python 3.9.25 with cp39-only binary wheels
#      so `pip install -U transformers` inside a clone can only ever resolve to
#      a 4.x release - exactly the one that raised the original error. Raising
#      the interpreter in place would orphan torch's cp39 build.
#
# THEREFORE: a fresh venv from the system Python 3.11.13 (/usr/bin/python3.11),
# which satisfies the latest transformers' >=3.11 floor. torch is pinned to
# 2.5.1 = exactly the version mlflu_hpc uses, so later numerical comparisons
# between the envs are not confounded by torch differences.
# ---------------------------------------------------------------------------
set -x
date
PREFIX=/home/sychan552/.venvs
NEW=$PREFIX/mlflu_llm
mkdir -p "$PREFIX"

echo '### STEP 1: create py3.11 venv'
rm -rf "$NEW"
/usr/bin/python3.11 -m venv "$NEW" || { echo 'FATAL: venv creation failed'; exit 1; }
"$NEW/bin/python" -V || exit 1

echo '### STEP 2: upgrade pip'
"$NEW/bin/python" -m pip install --upgrade pip setuptools wheel 2>&1 | tail -4

echo '### STEP 3: torch 2.5.1 (same as mlflu_hpc), large download'
nice -n 19 "$NEW/bin/python" -m pip install "torch==2.5.1" 2>&1 | tail -12
RC=$?; echo "torch rc=$RC"
[ $RC -eq 0 ] || { echo 'FATAL: torch install failed'; exit $RC; }

echo '### STEP 4: latest transformers + huggingface_hub'
nice -n 19 "$NEW/bin/python" -m pip install -U transformers huggingface_hub 2>&1 | tail -12
RC=$?; echo "transformers rc=$RC"
[ $RC -eq 0 ] || { echo 'FATAL: transformers install failed'; exit $RC; }

# NOTE: no `import torch` / `import transformers` here - AGENTS.md §4 gotcha 12:
# heavy imports on the login node can block in state D and take the login shell
# down for every user. Versions are read from package metadata only.
echo '### STEP 5: installed versions (metadata only)'
"$NEW/bin/python" -m pip show torch transformers huggingface_hub tokenizers safetensors 2>&1 \
  | grep -E '^(Name|Version):'
echo '### ENV_BUILD_DONE'
date
