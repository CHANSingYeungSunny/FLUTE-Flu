#!/bin/bash
# Hierarchical Lmod: Miniconda3/24.7 needs the `default` parent module loaded first.
echo '===== module load default; module load Miniconda3/24.7 ====='
module load default 2>&1 | head -5
module load Miniconda3/24.7 2>&1 | head -5
echo "  python: $(command -v python) $(python -V 2>&1)"
echo "  conda : $(command -v conda)"
echo "  CONDA_PREFIX=$CONDA_PREFIX"
conda --version 2>&1
echo '  --- envs ---'
conda env list 2>&1 | head -10
echo '===== alternative: module load old_modules; module load miniconda/python-3.12.9 ====='
( module load old_modules 2>&1 | head -3
  module load miniconda/python-3.12.9 2>&1 | head -3
  echo "  python: $(command -v python) $(python -V 2>&1)"
  echo "  conda : $(command -v conda)"
)
echo END
