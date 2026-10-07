# -*- coding: utf-8 -*-
"""Stage 5 pre-launch: verify ACTUAL input/target indices, boundaries and the last legal window.

Not just counts -- checks off-by-one explicitly for every split and horizon.
"""
import importlib.util
import io
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

spec = importlib.util.spec_from_file_location(
    "t966", os.path.join(ROOT, "scripts", "train_nlinear_966.py"))
t966 = importlib.util.module_from_spec(spec)
sys.modules["t966"] = t966
spec.loader.exec_module(t966)

T = 104
PROFILE = "author_966"

dd = t966.load_and_normalize(PROFILE)
n = int(dd["n"])
te, ve = int(dd["train_end"]), int(dd["val_end"])
rng = np.random.default_rng(7)
arr = rng.standard_normal((n, dd["data_norm"].shape[1])).astype(np.float32)

lines = []
lines.append("# Stage 5 — 窗口索引 / 边界 / 末窗核对（strict 目标完整包含）\n")
lines.append("profile=%s  n=%d  train_end=%d  val_end=%d  T=%d\n" % (PROFILE, n, te, ve, T))
lines.append("| L | split | 窗口数 | 首窗 input | 首窗 target | 末窗 input | 末窗 target | 校验 |")
lines.append("|---|---|---:|---|---|---|---|---|")

ok_all = True
for L in (24, 36, 48, 60):
    Xt, Yt, Xv, Yv, Xte, Yte, sinfo = t966.build_windows(
        arr, T, L, te, ve, containment="strict")
    ts = sinfo["target_starts"]
    sp = sinfo["splits"]
    for name, Xs, code, lo, hi in (("train", Xt, 0, 0, te),
                                   ("val", Xv, 1, te, ve),
                                   ("test", Xte, 2, ve, n)):
        idx = np.where(sp == code)[0]
        if len(idx) == 0:
            lines.append("| %d | %s | 0 | - | - | - | - | EMPTY |" % (L, name))
            ok_all = False
            continue
        ts_sel = ts[idx]
        first_in = (int(ts_sel[0]) - T, int(ts_sel[0]) - 1)
        first_tg = (int(ts_sel[0]), int(ts_sel[0]) + L - 1)
        last_in = (int(ts_sel[-1]) - T, int(ts_sel[-1]) - 1)
        last_tg = (int(ts_sel[-1]), int(ts_sel[-1]) + L - 1)
        checks = []
        checks.append(first_in[0] >= 0)
        checks.append(last_tg[1] < n)          # 目标末位在文件内
        checks.append(first_tg[0] >= lo and last_tg[1] < hi)   # 目标完整在划分内
        checks.append(np.all(np.diff(ts_sel) == 1))            # stride=1 连续
        checks.append(np.all((ts_sel >= (lo if code else T))))
        ok = all(checks)
        ok_all &= ok
        lines.append("| %d | %s | %d | [%d,%d] | [%d,%d] | [%d,%d] | [%d,%d] | %s |" % (
            L, name, len(idx), first_in[0], first_in[1], first_tg[0], first_tg[1],
            last_in[0], last_in[1], last_tg[0], last_tg[1], "OK" if ok else "FAIL"))

lines.append("")
lines.append("结论：%s" % ("全部通过（含 off-by-one 与末窗检查）" if ok_all else "存在失败项"))
out = "\n".join(lines)
print(out)
io.open(os.path.join(ROOT, "recovery", "stage5", "window_indices_verify.md"), "w",
        encoding="utf-8").write(out + "\n")
