"""
GPT-2 control-adapter reproduction (pre-HPC clarification 3)
===========================================================

Same checkpoint + same inputs: the existing MIFlu is checkpointed, loaded into
`GPT2MifluAdapter`, and both are run on identical inputs. Reports BOTH
`torch.equal` and `torch.allclose`, plus max/mean absolute difference, device,
dtype, eval mode, deterministic settings, input hash and checkpoint hash.

Real HPC-trained-checkpoint validation is deliberately marked PENDING until the
pilot stage (we do not pull checkpoints and do not touch the HPC here).
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402
import _repro  # noqa: E402

import torch  # noqa: E402

from innovation import run_artifacts as ART  # noqa: E402
from innovation.paths import AUDIT_DIR  # noqa: E402

REPORT = os.path.join(AUDIT_DIR, "gpt2_control_repro_report.json")
L, T, N, B = 24, 104, 7, 3


def run() -> dict:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    old, adapter, ckpt, ckpt_sha, sd_match = _repro.build_old_and_adapter(
        L, T, N, device)
    x, htext, ctx_meta = _repro.make_inputs(L, T, N, B, device)

    old.eval()
    adapter.eval()
    with torch.no_grad():
        y_old = _repro.old_forward_z(old, x, htext, device)
        y_adapter = adapter(x, htext)

    diff = (y_old - y_adapter).abs()
    rep = {
        "comparison": {
            "torch_equal": bool(torch.equal(y_old, y_adapter)),
            "torch_allclose_default": bool(torch.allclose(y_old, y_adapter)),
            "torch_allclose_atol_rtol": {
                "atol": 1e-6, "rtol": 1e-5,
                "result": bool(torch.allclose(y_old, y_adapter, atol=1e-6, rtol=1e-5)),
            },
            "max_abs_diff": float(diff.max().item()),
            "mean_abs_diff": float(diff.mean().item()),
        },
        "tensors": {
            "shape": list(y_old.shape), "dtype": str(y_old.dtype),
            "device": str(y_old.device),
        },
        "device": device,
        "eval_mode": {"old_is_training": bool(old.training),
                      "adapter_is_training": bool(adapter.training)},
        "deterministic_settings": _repro.deterministic_settings(),
        "inputs": {
            "x_sha256": _repro.tensor_sha256(x),
            "htext_sha256": _repro.tensor_sha256(htext),
            "context": ctx_meta,
        },
        "checkpoint": {
            "checkpoint_sha256": ckpt_sha,
            "state_dicts_match": bool(sd_match),
            "kind": "synthetic (existing MIFlu state_dict, fixed seed)",
        },
        "tolerance_declared": {"torch_equal_expected": True,
                               "max_abs_diff_atol": 1e-6},
        "hpc_checkpoint_validation": "pending_pilot_stage",
        "note": ("synthetic-checkpoint bit-exact reproduction only; validating "
                 "against a real HPC-trained MIFlu checkpoint is PENDING until "
                 "the pilot stage"),
    }
    ART.write_json(REPORT, rep)
    return rep


def test_gpt2_adapter_matches_existing_miflu():
    rep = run()
    print(json.dumps(rep["comparison"], indent=2))
    assert rep["checkpoint"]["state_dicts_match"], rep
    assert rep["comparison"]["torch_allclose_atol_rtol"]["result"], rep
    assert rep["comparison"]["max_abs_diff"] <= 1e-6, rep
    # A bit-exact adapter is the expectation; if this ever fails, the adapter
    # has diverged from the existing model and must be investigated.
    assert rep["comparison"]["torch_equal"], \
        f"adapter is not bit-exact vs existing MIFlu: {rep['comparison']}"
    assert rep["hpc_checkpoint_validation"] == "pending_pilot_stage"


if __name__ == "__main__":
    test_gpt2_adapter_matches_existing_miflu()
    print("[test_gpt2_control_repro] OK")
