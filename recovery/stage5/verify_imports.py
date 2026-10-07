# -*- coding: utf-8 -*-
"""Stage 5 — verify every runner imports in the MLFLU execution dir, and hash key files."""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

KEY = ["scripts/configs.py", "scripts/train_miflu.py", "scripts/train_ablation.py",
       "scripts/train_nlinear_966.py", "scripts/train_naive_966.py",
       "scripts/recipes.py", "scripts/early_stopping.py", "scripts/miflu_model.py",
       "scripts/textual_embedder.py", "scripts/scaler_utils.py", "scripts/cdc_calendar.py",
       "data/raw/national_illness_raw_paper_exact.csv"]

out = {"cwd": os.getcwd(), "python": sys.version.split()[0], "hashes": {}, "imports": {}}
for k in KEY:
    p = os.path.join(ROOT, k)
    out["hashes"][k] = (hashlib.sha256(open(p, "rb").read()).hexdigest()
                        if os.path.exists(p) else "MISSING")

import torch
out["torch"] = torch.__version__
out["cuda"] = torch.cuda.is_available()

for name in ("configs", "miflu_model", "textual_embedder", "scaler_utils", "cdc_calendar",
             "recipes", "early_stopping", "train_miflu", "train_ablation",
             "train_nlinear_966", "train_naive_966"):
    try:
        __import__(name)
        out["imports"][name] = "OK"
    except Exception as exc:
        out["imports"][name] = "FAIL: %s" % exc

import train_miflu as tm
import train_ablation as ta
import train_nlinear_966 as tn
import train_naive_966 as tv
out["containment_support"] = {
    "train_miflu": "containment" in tm.build_windows.__code__.co_varnames,
    "train_ablation": "containment" in ta.build_windows.__code__.co_varnames,
    "train_nlinear": "containment" in tn.build_windows.__code__.co_varnames,
    "train_naive": "containment" in tv.window_index.__code__.co_varnames,
}
out["defer_test_support"] = {
    "train_miflu": "DEFER_TEST" in open(os.path.join(ROOT, "scripts", "train_miflu.py")).read(),
    "train_ablation": "DEFER_TEST" in open(os.path.join(ROOT, "scripts", "train_ablation.py")).read(),
    "train_nlinear": "DEFER_TEST" in open(os.path.join(ROOT, "scripts", "train_nlinear_966.py")).read(),
}
print(json.dumps(out, indent=2))
