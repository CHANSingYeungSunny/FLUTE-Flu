# -*- coding: utf-8 -*-
"""train_miflu: skip Test averaging while DEFER_TEST=1 (no Test numbers exist)."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "scripts", "train_miflu.py")
s = io.open(P, encoding="utf-8").read()

OLD = ('        avg_mse_all = np.mean([r["test_mse_all"] for r in L_reps])\n'
       '        avg_mse_ili = np.mean([r["test_mse_ili"] for r in L_reps])\n'
       '        log(f"  [L={L}] FINAL: MSE_AllVars={avg_mse_all:.6f} '
       'MSE_ILITotal={avg_mse_ili:.6f}"); log()')
NEW = ('        if any(r.get("test_deferred") for r in L_reps):\n'
       '            log(f"  [L={L}] FINAL: TEST DEFERRED - no Test numbers produced '
       '(locked-batch step); "\n'
       '                f"best val={best_val:.6f}")\n'
       '        else:\n'
       '            avg_mse_all = np.mean([r["test_mse_all"] for r in L_reps])\n'
       '            avg_mse_ili = np.mean([r["test_mse_ili"] for r in L_reps])\n'
       '            log(f"  [L={L}] FINAL: MSE_AllVars={avg_mse_all:.6f} '
       'MSE_ILITotal={avg_mse_ili:.6f}")\n'
       '        log()')
assert OLD in s, "avg block not found"
s = s.replace(OLD, NEW, 1)

# all_rows must not carry None into the CSV summary either
OLD2 = ('            all_rows.append({"L": L, "rep": rep+1,\n'
        '                "mse_ili": r["test_mse_ili"], "mae_ili": r["test_mae_ili"],')
NEW2 = ('            all_rows.append({"L": L, "rep": rep+1,\n'
        '                "mse_ili": r["test_mse_ili"] if r.get("test_mse_ili") is not None '
        'else np.nan, "mae_ili": r["test_mae_ili"] if r.get("test_mae_ili") is not None '
        'else np.nan,')
if OLD2 in s:
    s = s.replace(OLD2, NEW2, 1)
    print("csv rows made defer-safe")

io.open(P, "w", encoding="utf-8").write(s)
print("defer-safe averaging installed")
