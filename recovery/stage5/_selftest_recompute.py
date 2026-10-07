"""Local synthetic self-test for recompute_from_artifacts.py (no GPU, no data)."""
import os, sys, json, shutil
import numpy as np, pandas as pd

ROOT = r"C:\Users\Asus\AppData\Local\Temp\opencode\rtest"
SC = os.path.join(ROOT, "scoring"); D = os.path.join(SC, "predictions")
shutil.rmtree(ROOT, ignore_errors=True); os.makedirs(D)

VAR = ["a", "b", "c", "d", "e", "f", "g"]
L = {24: 170, 36: 158, 48: 146, 60: 134}
rng = np.random.default_rng(0)
tm = np.zeros((1, 7), np.float32); tsd = np.ones((1, 7), np.float32)
man, rec = [], []
for Lx, n in L.items():
    tsr = np.arange(773, 773 + n)          # inside [773, 966) incl. whole target
    for model, seeds in (("miflu", [42, 43, 44]), ("notext", [42, 43, 44]),
                         ("nlinear", [42, 43, 44]), ("last_value_naive", [42]),
                         ("seasonal_naive", [42])):
        for s in seeds:
            tgt = rng.normal(size=(n, 7, Lx)).astype(np.float32)
            pred = tgt + rng.normal(scale=0.3, size=tgt.shape).astype(np.float32)
            np.savez_compressed(os.path.join(D, f"pred_{model}_L{Lx}_s{s}.npz"),
                                pred=pred, target=tgt, target_start_row=tsr.astype(np.int32),
                                L=np.int32(Lx), seed=np.int32(s), var_cols=np.array(VAR),
                                train_mean=tm, train_std=tsd, model=np.array(model),
                                profile=np.array("author_966"),
                                containment=np.array("strict"),
                                space=np.array("standardized_train_fit_z"))
            mse = float(np.mean((pred - tgt) ** 2)); mae = float(np.mean(np.abs(pred - tgt)))
            rec.append({"model": model, "L": Lx, "seed": s, "mse_all": mse, "mae_all": mae,
                        "mse_ili": mse, "mae_ili": mae, "pcc_ili": 0.5})
            for j, t in enumerate(tsr):
                man.append({"model": model, "L": Lx, "seed": s, "origin_i": j,
                            "origin_row_last_observed": int(t - 1),
                            "target_start_row": int(t), "target_end_row": int(t + Lx - 1),
                            "n_leads": Lx, "origin_epiweek": 200000 + int(t),
                            "first_target_epiweek": 200000 + int(t),
                            "last_target_epiweek": 200000 + int(t + Lx - 1)})
pd.DataFrame(rec).to_csv(os.path.join(SC, "score_matrix.csv"), index=False)
pd.DataFrame(man).to_csv(os.path.join(D, "test_manifest.csv"), index=False)
json.dump({"profile": "author_966", "fit_on": "train rows [0, 676) ONLY",
           "train_end": 676, "val_end": 773, "var_cols": VAR,
           "mean": [0] * 7, "scale": [1] * 7},
          open(os.path.join(D, "scaler_train_only.json"), "w"))
g = pd.DataFrame(rec).groupby(["model", "L"])["mse_all"].mean().reset_index()
g.groupby("model")["mse_all"].mean().rename("average_MSE_4L").reset_index() \
 .to_csv(os.path.join(SC, "average_mse_4L.csv"), index=False)

rc = os.system(f'python "{os.path.abspath("recovery/stage5/recompute_from_artifacts.py")}" --scoring "{SC}"')
print("exit code:", rc >> 8)
# negative test: corrupt one prediction so mse disagrees
z = np.load(os.path.join(D, "pred_miflu_L24_s42.npz"))
d = dict(z); d["pred"] = z["pred"] + 1.0
np.savez_compressed(os.path.join(D, "pred_miflu_L24_s42.npz"), **d)
rc2 = os.system(f'python "{os.path.abspath("recovery/stage5/recompute_from_artifacts.py")}" --scoring "{SC}"')
print("negative-test exit code (expect 3):", rc2 >> 8)
