#!/bin/bash
echo '=== module list ==='
module list 2>&1 | head -20
echo '=== module avail (first 40) ==='
module avail 2>&1 | head -40
echo '=== system pythons ==='
ls -l /usr/bin/python3* /usr/local/bin/python3* 2>/dev/null
echo '=== ML module dir ==='
ls /usr/local/Modules/modulefiles 2>/dev/null | head -20
ls /etc/modulefiles 2>/dev/null | head -20
echo '=== conda anywhere in /opt ==='
ls -d /opt/*conda* /opt/*/conda 2>/dev/null | head
echo '=== modulepath ==='
echo "$MODULEPATH" | tr ':' '\n' | head -20
echo END
