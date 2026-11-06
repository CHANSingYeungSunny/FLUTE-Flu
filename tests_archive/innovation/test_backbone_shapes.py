"""Component SHAPE tests (revision 4): backbones / encoders / fusions."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

import torch  # noqa: E402

from innovation.backbones import make_backbone  # noqa: E402
from innovation.fusion import make_fusion  # noqa: E402

T, N, L, B = 104, 7, 24, 2


def test_nontext_backbones_shape():
    x = torch.randn(B, N, T)
    for name in ("dlinear", "nlinear", "patchtst", "itransformer"):
        m = make_backbone(name, T=T, N=N, L=L)
        y = m(x)
        assert tuple(y.shape) == (B, N, L), (name, y.shape)
        assert m.trainable_parameters() > 0, name
        rep = m.architecture_report()
        assert "published" in rep and "fidelity" in rep, rep


def test_fusions_shape_and_identity_when_no_text():
    ht = torch.randn(B, 5, 32)
    hx = torch.randn(B, 3, 32)
    for name in ("concat_projection", "film_gate", "cross_attention"):
        f = make_fusion(name, d_model=32)
        assert tuple(f(ht, hx).shape) == (B, 5, 32), name
        # no text -> identity passthrough
        assert torch.allclose(f(ht, None), ht), name
    ident = make_fusion("identity")
    assert torch.allclose(ident(ht, hx), ht)


def test_fusion_forecaster_with_text():
    from innovation.backbones.fusion_forecaster import TextFusionForecaster
    m = TextFusionForecaster(T=T, N=N, L=L,
                             fusion=make_fusion("film_gate", d_model=16),
                             text_dim=8, d_model=16)
    y = m(torch.randn(B, N, T), torch.randn(B, 4, 8))
    assert tuple(y.shape) == (B, N, L), y.shape


def test_arch_reports_flag_deviation():
    from innovation import fidelity as FID
    pt = make_backbone("patchtst", T=T, N=N, L=L).architecture_report()
    assert pt["fidelity"] == FID.INSPIRED_SIMPLIFICATION, pt
    for name in ("dlinear", "nlinear"):
        r = make_backbone(name, T=T, N=N, L=L).architecture_report()
        assert r["fidelity"] == FID.REFERENCE_FAITHFUL, (name, r)
    it = make_backbone("itransformer", T=T, N=N, L=L).architecture_report()
    assert it["fidelity"] == FID.REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS, it


if __name__ == "__main__":
    test_nontext_backbones_shape()
    test_fusions_shape_and_identity_when_no_text()
    test_fusion_forecaster_with_text()
    test_arch_reports_flag_deviation()
    print("[test_backbone_shapes] OK")
