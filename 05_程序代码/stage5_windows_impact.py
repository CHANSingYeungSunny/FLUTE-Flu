# -*- coding: utf-8 -*-
"""Stage 5 — quantify the D-windows defect's impact on OLD experiments.

For each historical profile, count validation windows whose target block crosses
into the Test segment under the legacy 'start' rule, and the share of target steps
that are Test rows. Also confirm Test windows themselves are fully contained.
"""
import io
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = 104

PROFILES = {
    "project_1025 (v3_clean Wave-1 / Test phase)": dict(n=1025, train_end=717, val_end=819),
    "author_966 676/97/193 (A2 target)": dict(n=966, train_end=676, val_end=773),
    "author_966 676/96/194 (job 514859 historical)": dict(n=966, train_end=676, val_end=772),
}

rows = []
for pname, p in PROFILES.items():
    n, te, ve = p["n"], p["train_end"], p["val_end"]
    for L in (24, 36, 48, 60):
        nw = n - T - L + 1
        ts = np.arange(nw) + T
        val_mask = (ts >= te) & (ts <= ve)
        test_mask = ts > ve
        n_val = int(val_mask.sum())
        n_test = int(test_mask.sum())
        # legacy rule: a "val" window's target may run past val_end into Test
        ts_val = ts[val_mask]
        crossing = ts_val + L - 1 > ve
        n_cross = int(crossing.sum())
        steps_total = n_val * L
        steps_in_test = int(np.sum(np.clip(ts_val + L - 1 - ve, 0, L)))
        # Test windows under the legacy rule: are their targets fully inside Test?
        ts_test = ts[test_mask]
        test_fully_in = bool(np.all(ts_test >= ve + 1) and np.all(ts_test + L - 1 <= n - 1))
        rows.append(dict(profile=pname, L=L, n_val=n_val, n_val_crossing=n_cross,
                         pct_val_crossing=round(100.0 * n_cross / n_val, 1),
                         pct_val_target_steps_in_test=round(100.0 * steps_in_test / steps_total, 1),
                         n_test=n_test, test_targets_fully_in_test=test_fully_in))

out = {
    "rule_examined": "legacy: split by target START only (target may straddle the next split)",
    "measured_on": "2026-09-25",
    "profiles": PROFILES,
    "results": rows,
}
p = os.path.join(ROOT, "recovery", "stage5", "windows_impact_on_old_runs.json")
with io.open(p, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print(json.dumps(rows, indent=2))
