"""
_diag_baseline_check.py — Trivial-baseline diagnostic for MIFlu National L=24.

Two scaler conventions compared, both on the SAME test windows:
  (A) TRAIN-ONLY fit  : StandardScaler fit on data[:train_end]  (current code)
  (B) POOLED fit      : StandardScaler fit on the WHOLE series
                        (train+val+test), per paper Section V-B "StandardScaler-
                        normalized data" reference point — checks if the gap vs
                        paper (MSE 1.542) is just a train-only vs whole-series
                        fit convention difference.

For each convention we report:
  - test-target variance of channel 4 (ILITOTAL) in that normalized space
  - const-mean (predict 0, since train/whole mean -> 0 after scaling) baseline MSE
  - hist-mean baseline MSE (per-window input history mean)
"""
import sys, os
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from train_miflu import load_and_normalize, build_windows, CONFIG

L = 24
T = CONFIG["T"]
N = CONFIG["N"]
CH = 4  # ILITOTAL

dd = load_and_normalize()
t_end, v_end = dd["train_end"], dd["val_end"]

# Raw data (unnormalized) and the channel used.
df = __import__("pandas").read_csv(dd["DATA_PATH"] if "DATA_PATH" in dd else
                                    os.path.join(os.path.dirname(__file__), "..",
                                                 "data", "raw", "national_illness_raw.csv"))
VAR_COLS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
            "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
raw = df[VAR_COLS].values.astype(np.float32)
n = len(raw)

MODEL_MSE = 5.055854  # from HPC L=24 run (train-only convention, channel 4)

def convention(name, mean, std):
    std = std + 1e-8
    data_norm = (raw - mean) / std
    Xtr, Ytr, Xv, Yv, Xte, Yte, sinfo = build_windows(
        data_norm, T, L, t_end, v_end)
    Y = Yte[:, CH, :]
    var = float(Y.var())
    const0 = np.zeros_like(Y)
    mse_const0 = float(np.mean((const0 - Y) ** 2))
    hist = Xte[:, CH, :].mean(axis=1, keepdims=True)
    mse_hist = float(np.mean((np.repeat(hist, L, axis=1) - Y) ** 2))
    print(f"\n=== Convention: {name} ===")
    print(f"  test-target channel4: mean={Y.mean():.4f} std={Y.std():.4f} var={var:.4f}")
    print(f"  const-mean(0) baseline MSE_ili = {mse_const0:.4f}")
    print(f"  hist-mean    baseline MSE_ili = {mse_hist:.4f}")
    return var, mse_const0, mse_hist

print(f"[DIAG] L={L}  n={n}  train_end={t_end} val_end={v_end}  test windows=182")

# (A) train-only
tr_mean = raw[:t_end].mean(axis=0, keepdims=True)
tr_std = raw[:t_end].std(axis=0, keepdims=True)
va, ca, ha = convention("TRAIN-ONLY fit (current code)", tr_mean, tr_std)

# (B) pooled whole-series fit
po_mean = raw.mean(axis=0, keepdims=True)
po_std = raw.std(axis=0, keepdims=True)
vb, cb, hb = convention("POOLED (train+val+test) fit", po_mean, po_std)

print("\n=== SUMMARY ===")
print(f"  Model (trained, train-only space) MSE_ili = {MODEL_MSE:.4f}")
print(f"  Paper National L=24 MSE (reference)       = 1.5420")
print(f"  TRAIN-ONLY : test var={va:.4f}  const0 MSE={ca:.4f}  hist MSE={ha:.4f}")
print(f"  POOLED     : test var={vb:.4f}  const0 MSE={cb:.4f}  hist MSE={hb:.4f}")
if abs(cb - ca) < 0.05:
    print("  >> Pooled vs train-only baseline MSE nearly identical -> "
          "fit-convention difference does NOT explain the gap. Gap is from a "
          "different normalization space / channel scaling, not train-vs-whole fit.")
else:
    print(f"  >> Pooled baseline ({cb:.4f}) differs from train-only ({ca:.4f}); "
          "fit convention contributes to the gap.")
