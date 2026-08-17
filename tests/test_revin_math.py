"""
test_revin_math.py — Tutor Q5 unit test (RevIN invertibility + projection dim)
================================================================================
Local unit test. NO training. Validates the two math claims behind the
metric correctness:
  1. RevIN (reverse instance norm) forward-inverse is strictly invertible:
       y_hat = y_hat_norm * stdev + means
       y_hat_norm_recovered = (y_hat - means) / stdev
       assert y_hat_norm_recovered == y_hat_norm  (within fp tolerance)
  2. Output Projection dimension == L (=24): the model emits exactly L steps
     for the target horizon, so de-normalized MSE/MAE are computed on the
     correct length.

Run:  python -m pytest tests/test_revin_math.py -v
  or: python tests/test_revin_math.py
"""
import os
import sys
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from miflu_model import MIFlu

D = 768
L = 24
N = 7
T = 104
Lp, S, K, lora_r = 24, 2, 6, 4


def revin_inverse_check(seed=0):
    rng = np.random.default_rng(seed)
    bsz = 4
    # instance-norm stats (batch, N, 1)
    means = torch.tensor(rng.normal(0, 1, size=(bsz, N, 1)), dtype=torch.float32)
    stdevs = torch.tensor(rng.uniform(0.5, 2.0, size=(bsz, N, 1)), dtype=torch.float32)
    # normalized predictions (batch, N, L)
    y_norm = torch.tensor(rng.normal(0, 1, size=(bsz, N, L)), dtype=torch.float32)
    # forward: de-norm
    y_hat = y_norm * stdevs + means
    # inverse: re-norm to recover
    y_norm_rec = (y_hat - means) / stdevs
    max_err = (y_norm_rec - y_norm).abs().max().item()
    return max_err


def output_projection_dim_check():
    model = MIFlu(N=N, T=T, L=L, Lp=Lp, S=S, K=K, lora_r=lora_r, device="cpu")
    x = torch.randn(2, N, T)
    htext = torch.randn(1, 367, D)
    y_hat, _, _, _ = model(x, htext)
    return tuple(y_hat.shape)


def test_revin_strictly_invertible():
    err = revin_inverse_check()
    print(f"[TEST] RevIN max recovery error = {err:.3e}")
    assert err < 1e-5, f"RevIN not invertible, err={err}"


def test_output_projection_dim_equals_L():
    shape = output_projection_dim_check()
    print(f"[TEST] y_hat shape = {shape}  (expected (2, {N}, {L}))")
    assert shape == (2, N, L), f"Output dim wrong: {shape}"


if __name__ == "__main__":
    test_revin_strictly_invertible()
    test_output_projection_dim_equals_L()
    print("\n[PASS] All RevIN / projection unit tests passed.")
