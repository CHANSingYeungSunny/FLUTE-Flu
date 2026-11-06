"""
The TEST GATE: select_best_model must NEVER read the test split.
================================================================

If the selector ever touched a test path, these tests FAIL — which is the
required behaviour (plan §6: "选择程序若读取 test，单元测试必须失败").
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

from innovation import run_artifacts as ART  # noqa: E402
from innovation import select_best_model as SBM  # noqa: E402
from innovation.run_id import make_run_id  # noqa: E402


def _write_run(root, spec, val_mse, peak=1.0, status="ok"):
    rid = make_run_id("national_ili", spec["model"], spec["text_encoder"],
                      spec["fusion"], spec["horizon"], spec["seed"],
                      timestamp=f"T{spec['horizon']}{spec['seed']}",
                      gitsha="g")
    d = os.path.join(root, rid)
    os.makedirs(os.path.join(d, "metrics"), exist_ok=True)
    ART.write_run_status(d, status=status, best_val_mse=val_mse,
                         val_mae_all_z=val_mse, peak_hit_ratio=peak,
                         trainable_parameters=1000, train_seconds=1.0)
    return d


def test_guard_rejects_test_paths():
    for p in ("runs/x/metrics/test_metrics.json",
              "runs/x/predictions/test_predictions.csv",
              os.path.join("test_evaluations", "abc", "metrics",
                           "test_metrics.json")):
        try:
            SBM.assert_no_test_path(p)
            raise AssertionError(f"guard must reject {p!r}")
        except RuntimeError:
            pass


def test_scan_runs_never_opens_test():
    tmp = tempfile.mkdtemp(prefix="innov_gate_")
    old_art, old_sbm = ART.RUNS_ROOT, SBM.RUNS_ROOT
    ART.RUNS_ROOT = tmp
    SBM.RUNS_ROOT = tmp          # the selector reads its OWN module binding
    try:
        _write_run(tmp, {"model": "dlinear", "text_encoder": "none",
                         "fusion": "identity", "horizon": 24, "seed": 42}, 3.0)
        # a decoy test artifact with absurd values must never be read
        decoy = os.path.join(tmp, "test_evaluations", "abc", "metrics")
        os.makedirs(decoy, exist_ok=True)
        with open(os.path.join(decoy, "test_metrics.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"mse_all_z": -999.0}, f)

        opened = []

        def guard_open(path, *a, **k):
            SBM.assert_no_test_path(path)
            opened.append(str(path))
            return open(path, *a, **k)

        rows = SBM.scan_runs(open_fn=guard_open)
        assert len(rows) == 1, rows
        assert all("test" not in p.lower() for p in opened), opened
        audit = SBM.build_audit(rows)
        assert audit["test_accessed"] is False
    finally:
        ART.RUNS_ROOT = old_art
        SBM.RUNS_ROOT = old_sbm


if __name__ == "__main__":
    test_guard_rejects_test_paths()
    test_scan_runs_never_opens_test()
    print("[test_test_gate] OK")
