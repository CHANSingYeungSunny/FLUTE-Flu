#!/bin/bash
P=/usr/bin/python3.11
echo "=== $P -V ==="
$P -V 2>&1
echo '=== venv module ==='
$P -m venv --help 2>&1 | head -5
echo '=== ensurepip ==='
$P -m ensurepip --version 2>&1 | head -5
echo '=== sysconfig ==='
$P -c "import sysconfig,sys;print(sys.version);print('EXT_SUFFIX',sysconfig.get_config_var('EXT_SUFFIX'));print('prefix',sys.prefix)" 2>&1
echo '=== pip present? ==='
$P -m pip --version 2>&1 | head -3
echo '=== can we write a test venv? ==='
TD=/home/sychan552/scratch/_venvtest
rm -rf "$TD"
$P -m venv "$TD" 2>&1 | tail -5
if [ -x "$TD/bin/python" ]; then
  echo "venv OK: $("$TD/bin/python" -V 2>&1)"
  "$TD/bin/python" -m pip --version 2>&1 | head -2
else
  echo "venv FAILED"
fi
rm -rf "$TD"
echo '=== module load default then avail ==='
( module load default 2>&1|head -3; echo "MODULEPATH=$MODULEPATH" | tr ':' '\n' | head; module avail 2>&1 | head -25 )
echo END
