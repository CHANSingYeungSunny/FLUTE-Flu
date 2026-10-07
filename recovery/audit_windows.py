# -*- coding: utf-8 -*-
"""Stage 2 window-manifest generator (author code path, deterministic arithmetic).

Reproduces the exact split/window geometry of the released Dataset_Custom loader for the
author 966-row dataset, for the four horizons, and writes window_manifest.json.
"""
import json
import os

RECOVERY = os.path.dirname(os.path.abspath(__file__))

N = 966
SEQ_LEN = 104
ENC_IN = 7          # train/val enumerate 7 features; test enumerates 1 (feature 0)
PRED_LENS = [24, 36, 48, 60]

num_train = int(N * 0.7)          # 676
num_test = int(N * 0.2)           # 193
num_vali = N - num_train - num_test  # 97

# border1s / border2s (data_x windows, include seq_len lookback)
border1s = [0, num_train - SEQ_LEN, N - num_test - SEQ_LEN]  # [0, 572, 669]
border2s = [num_train, num_train + num_vali, N]              # [676, 773, 966]

manifest = {
    "dataset": "author national_illness.csv",
    "n_rows": N,
    "seq_len": SEQ_LEN,
    "split_rule": "int(n*0.7) / int(n*0.2) / remainder",
    "num_train": num_train,
    "num_vali": num_vali,
    "num_test": num_test,
    "border1s": border1s,
    "border2s": border2s,
    "data_x_rows": {
        "train": [border1s[0], border2s[0]],
        "val": [border1s[1], border2s[1]],
        "test": [border1s[2], border2s[2]],
    },
    "note_test_feature_coverage": (
        "Dataset_Custom.__len__ for set_type==2 returns tot_len WITHOUT *enc_in, so "
        "__getitem__ feat_id = index // tot_len is always 0 -> test evaluates feature 0 "
        "(weighted ILI) only."
    ),
    "horizons": {},
}

for L in PRED_LENS:
    tot = {
        split: (b2 - b1) - SEQ_LEN - L + 1
        for split, (b1, b2) in zip(
            ["train", "val", "test"],
            [(border1s[0], border2s[0]), (border1s[1], border2s[1]),
             (border1s[2], border2s[2])],
        )
    }
    samples = {
        "train": tot["train"] * ENC_IN,
        "val": tot["val"] * ENC_IN,
        "test": tot["test"] * 1,   # feature 0 only
    }
    manifest["horizons"][str(L)] = {
        "pred_len": L,
        "tot_len": tot,
        "samples": samples,
    }

out = os.path.join(RECOVERY, "window_manifest.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(json.dumps(manifest, indent=2))
