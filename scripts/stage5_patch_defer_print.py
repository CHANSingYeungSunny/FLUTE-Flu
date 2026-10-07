# -*- coding: utf-8 -*-
"""Make the NLinear runner's summary print DEFER_TEST-safe (None metrics)."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "scripts", "train_nlinear_966.py")
s = io.open(P, encoding="utf-8").read()

OLD = ('        print(f"[nlinear] L={L} seed={args.seed} mse_all={r[\'mse_all\']:.6f} "\n'
       '              f"mse_ili={r[\'mse_ili\']:.6f} best_val={r[\'best_val\']:.6f} "\n'
       '              f"({time.time()-t0:.1f}s)")')
NEW = ('        if r.get("mse_all") is None:\n'
       '            print(f"[nlinear] L={L} seed={args.seed} TEST DEFERRED "\n'
       '                  f"best_val={r[\'best_val\']:.6f} best_epoch={r.get(\'best_epoch\')} "\n'
       '                  f"({time.time()-t0:.1f}s)")\n'
       '        else:\n'
       '            print(f"[nlinear] L={L} seed={args.seed} mse_all={r[\'mse_all\']:.6f} "\n'
       '                  f"mse_ili={r[\'mse_ili\']:.6f} best_val={r[\'best_val\']:.6f} "\n'
       '                  f"({time.time()-t0:.1f}s)")')
assert OLD in s, "print block not found"
s = s.replace(OLD, NEW, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("defer-safe print installed")
