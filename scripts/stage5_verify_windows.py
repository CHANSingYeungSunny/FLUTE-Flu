# -*- coding: utf-8 -*-
"""Stage 5 — verify strict-containment window counts for all three runners (CPU only)."""
import importlib.util
import io
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

EXPECTED = {24: (549, 74, 170), 36: (537, 62, 158), 48: (525, 50, 146), 60: (513, 38, 134)}
T, N, TOTAL = 104, 7, 966
TRAIN_END, VAL_END = 676, 773


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


rng = np.random.default_rng(0)
arr = rng.standard_normal((TOTAL, N)).astype(np.float32)

rows = []
for name in ("train_miflu", "train_ablation", "train_nlinear_966"):
    p = os.path.join(ROOT, "scripts", name + ".py")
    try:
        mod = load(name, p)
    except Exception as exc:  # import needs heavy deps
        rows.append((name, "IMPORT_FAILED", str(exc)[:80], "", "", ""))
        continue
    for L in (24, 36, 48, 60):
        out = mod.build_windows(arr, T, L, TRAIN_END, VAL_END, containment="strict")
        nt, nv, nte = len(out[0]), len(out[2]), len(out[4])
        exp = EXPECTED[L]
        rows.append((name, L, nt, nv, nte, "MATCH" if (nt, nv, nte) == exp else "MISMATCH exp=%s" % (exp,)))

lines = ["| runner | L | train | val | test | vs Stage5 table |", "|---|---:|---:|---:|---:|---|"]
for r in rows:
    lines.append("| %s | %s | %s | %s | %s | %s |" % r)
out = "\n".join(lines)
print(out)
io.open(os.path.join(ROOT, "recovery", "stage5", "window_counts_verify.md"), "w",
        encoding="utf-8").write("# Stage 5 — window count verification (CPU)\n\n" + out + "\n")
