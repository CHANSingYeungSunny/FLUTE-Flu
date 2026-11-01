#!/bin/bash
# Figure out which module actually puts `conda` on PATH.
probe() {
    local mod="$1"
    echo "===== module load $mod ====="
    ( module load "$mod" 2>&1 | head -5
      echo "  python: $(command -v python) $(python -V 2>&1)"
      echo "  conda : $(command -v conda)"
      echo "  CONDA_PREFIX=$CONDA_PREFIX"
      echo "  conda version: $(conda --version 2>&1)"
    ) 2>&1
}
probe miniconda/python-3.12.9
probe Miniconda3/24.7
probe miniconda/python-3.9
echo '--- module list after each attempt is per-subshell, so this is clean ---'
echo END
