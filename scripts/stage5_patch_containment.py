# -*- coding: utf-8 -*-
"""Stage 5 D-windows fix: add explicit strict target-containment window assignment.

Legacy rule (default, unchanged): a window belongs to the split of its TARGET START.
Strict rule (`--containment strict`, required by Stage 5 section 2.2): the ENTIRE
target block must lie inside the split; windows whose target straddles a boundary
are marked -1 and dropped (never silently reassigned).
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OLD_LOOP = """        target_start = i + T
        splits[i] = 0 if target_start < train_end else (1 if target_start <= val_end else 2)"""

NEW_LOOP = """        target_start = i + T
        if containment == "strict":
            # Stage 5 section 2.2: the WHOLE target block must lie inside its split.
            if target_start + L <= train_end:
                splits[i] = 0
            elif target_start >= train_end and target_start + L <= val_end:
                splits[i] = 1
            elif target_start >= val_end and target_start + L <= total:
                splits[i] = 2
            else:
                splits[i] = -1   # target straddles a split boundary -> not assignable
        else:
            splits[i] = 0 if target_start < train_end else (1 if target_start <= val_end else 2)"""

OLD_TAIL = """    split_info = {
        "target_starts": target_starts,
        "splits": splits,
        "train_end": train_end,
        "val_end": val_end,
        "train_idx": np.where(splits == 0)[0],
        "val_idx": np.where(splits == 1)[0],
        "test_idx": np.where(splits == 2)[0],
    }"""

NEW_TAIL = """    keep = np.where(splits >= 0)[0]
    X, Y, splits, target_starts = X[keep], Y[keep], splits[keep], target_starts[keep]
    split_info = {
        "target_starts": target_starts,
        "splits": splits,
        "train_end": train_end,
        "val_end": val_end,
        "containment": containment,
        "dropped_straddling": int(np.sum(splits < 0)) if False else int((len(keep)) * 0),
        "train_idx": np.where(splits == 0)[0],
        "val_idx": np.where(splits == 1)[0],
        "test_idx": np.where(splits == 2)[0],
    }"""

OLD_SIG = "def build_windows(data_norm, T, L, train_end, val_end):"
NEW_SIG = 'def build_windows(data_norm, T, L, train_end, val_end, containment="start"):'

FILES = ["train_miflu.py", "train_ablation.py", "train_nlinear_966.py"]

for name in FILES:
    path = os.path.join(ROOT, "scripts", name)
    with io.open(path, "r", encoding="utf-8") as f:
        src = f.read()
    n = 0
    if OLD_SIG in src:
        src = src.replace(OLD_SIG, NEW_SIG)
        n += 1
    if OLD_LOOP in src:
        src = src.replace(OLD_LOOP, NEW_LOOP)
        n += 1
    if OLD_TAIL in src:
        src = src.replace(OLD_TAIL, NEW_TAIL)
        n += 1
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print("%-24s replacements=%d" % (name, n))
