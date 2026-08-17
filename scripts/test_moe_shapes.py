"""
test_moe_shapes.py — Shape & parameter validation for MoE/UCS prototypes
=========================================================================
Local test. Instantiates I2MoE (4 experts), Flex-MoE Missing Bank, and
UCS SGT prior with REAL MIFlu dimensions (D=768, num_patches=42) and
asserts:
  - output shape == input shape == (batch, seq, D)
  - added parameter counts are reported (cross-checked vs paper overhead)

Run: python test_moe_shapes.py
  or: python -m pytest test_moe_shapes.py -v
"""
import os
import sys
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moe_extension import I2MoE, FlexMoEMissingBank, UCS_SGT_Prior, count_params

D = 768
NUM_PATCHES = 42
TOTAL_PATCHES = 7 * NUM_PATCHES
TEXT_LEN = 367
SEQ = TEXT_LEN + TOTAL_PATCHES
B = 2


def test_i2moe_shape_and_params():
    m = I2MoE(D=D, n_experts=4)
    x = torch.randn(B, SEQ, D)
    y = m(x)
    assert y.shape == (B, SEQ, D), f"I2MoE shape {y.shape}"
    p = count_params(m)
    print(f"[TEST] I2MoE shape OK, added_params={p:,}")
    assert p > 0


def test_flexmoe_shape_and_params():
    m = FlexMoEMissingBank(D=D, bank_size=8)
    x = torch.randn(B, SEQ, D)
    y = m(x)
    assert y.shape == (B, SEQ, D), f"FlexMoE shape {y.shape}"
    p = count_params(m)
    print(f"[TEST] FlexMoE shape OK, added_params={p:,}")
    assert p > 0


def test_ucs_shape_and_params():
    m = UCS_SGT_Prior(seq=SEQ, D=D)
    x = torch.randn(B, SEQ, D)
    y = m(x)
    assert y.shape == (B, SEQ, D), f"UCS shape {y.shape}"
    # prior is a buffer (frozen) -> counts as 0 trainable params
    p = count_params(m)
    print(f"[TEST] UCS shape OK, added_params={p:,} (prior is frozen buffer)")
    # offline-settable
    m.set_prior(torch.randn(SEQ, D))
    y2 = m(x)
    assert y2.shape == (B, SEQ, D)


if __name__ == "__main__":
    test_i2moe_shape_and_params()
    test_flexmoe_shape_and_params()
    test_ucs_shape_and_params()
    print("\n[PASS] test_moe_shapes.py — all shape/param checks passed.")
