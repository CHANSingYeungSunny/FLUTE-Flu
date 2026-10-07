# -*- coding: utf-8 -*-
"""Add best_epoch tracking to the NLinear runner (needed for the selection record)."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "scripts", "train_nlinear_966.py")
s = io.open(P, encoding="utf-8").read()

old_init = '    best_val = float("inf")\n    best_state = None\n'
new_init = '    best_val = float("inf")\n    best_state = None\n    best_epoch = -1\n'
assert old_init in s, "init block not found"
s = s.replace(old_init, new_init, 1)

old_loop = '    for _ in range(epochs):\n        model.train()\n'
new_loop = '    for ep in range(epochs):\n        model.train()\n'
assert old_loop in s, "loop header not found"
s = s.replace(old_loop, new_loop, 1)

old_upd = '        if v_mse_all < best_val:\n            best_val = v_mse_all\n'
new_upd = '        if v_mse_all < best_val:\n            best_val = v_mse_all\n            best_epoch = ep\n'
assert old_upd in s, "update block not found"
s = s.replace(old_upd, new_upd, 1)

io.open(P, "w", encoding="utf-8").write(s)
print("best_epoch tracking added")
