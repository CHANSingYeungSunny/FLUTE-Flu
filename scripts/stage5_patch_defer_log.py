# -*- coding: utf-8 -*-
"""train_miflu: make the final checkpoint log DEFER_TEST-safe."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "scripts", "train_miflu.py")
s = io.open(P, encoding="utf-8").read()

OLD = ('        log(f"    - L={L}: seed={info[\'seed\']}  '
       'best_val_mse={info[\'best_val\']:.6f}  test_mse_ili={info[\'test_mse_ili\']:.6f}")')
NEW = ('        if info.get("test_mse_ili") is None:\n'
       '            log(f"    - L={L}: seed={info[\'seed\']}  '
       'best_val_mse={info[\'best_val\']:.6f}  test=DEFERRED")\n'
       '        else:\n'
       '            log(f"    - L={L}: seed={info[\'seed\']}  '
       'best_val_mse={info[\'best_val\']:.6f}  '
       'test_mse_ili={info[\'test_mse_ili\']:.6f}")')
assert OLD in s, "log line not found"
s = s.replace(OLD, NEW, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("defer-safe checkpoint log installed")
