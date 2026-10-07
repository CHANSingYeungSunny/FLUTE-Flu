"""
smoke.py — minimal end-to-end smoke for the innovation pipeline.
===============================================================

REVISION 4: smoke is split into
  (a) component SHAPE tests  -> `tests/innovation/test_backbone_shapes.py`;
  (b) a SMALL, REPRESENTATIVE set of end-to-end combinations (below) — NOT the
      full Cartesian product.

Smoke results are for PIPELINE VALIDATION ONLY. They are not a performance
measurement, must never rank models, and must never enter a paper conclusion.
"""

from __future__ import annotations

import os
import sys
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

from innovation.runner import run_one  # noqa: E402

SMOKE_SETTINGS = {"horizon": 24, "seed": 42, "epochs": 1, "batch_size": 8,
                  "patience": 7, "limit_train": 32, "limit_val": 16}

# Representative combinations (NOT the Cartesian product).
COMBOS = [
    ("dlinear", "none", "identity"),
    ("nlinear", "none", "identity"),
    ("patchtst", "none", "identity"),
    ("itransformer", "none", "identity"),
    ("fusion_forecaster", "tfidf_svd", "concat_projection"),
    ("fusion_forecaster", "gpt2", "film_gate"),
    ("fusion_forecaster", "gpt2", "cross_attention"),
    ("gpt2_miflu", "gpt2", "concat_projection"),
]


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    skip_gpt2 = "--skip-gpt2" in argv
    device = "cuda" if _cuda() else "cpu"
    print("=" * 78)
    print("INNOVATION SMOKE — pipeline validation only. NOT for ranking.")
    print(f"device={device}  settings={SMOKE_SETTINGS}")
    print("=" * 78)

    ok, failed = [], []
    for model, enc, fusion in COMBOS:
        if skip_gpt2 and (model == "gpt2_miflu" or enc == "gpt2"):
            print(f"[skip] {model}/{enc}/{fusion} (--skip-gpt2)")
            continue
        spec = dict(SMOKE_SETTINGS)
        spec.update({"model": model, "text_encoder": enc, "fusion": fusion,
                     "device": device, "experiment_stage": "smoke"})
        try:
            st = run_one(spec)
            ok.append((model, enc, fusion, st.get("best_val_mse")))
            print(f"[OK] {model}/{enc}/{fusion} -> best_val_mse="
                  f"{st.get('best_val_mse')}")
        except Exception as e:
            failed.append((model, enc, fusion, f"{e.__class__.__name__}: {e}"))
            print(f"[FAIL] {model}/{enc}/{fusion}: {e}")
            traceback.print_exc()

    print("-" * 78)
    print(f"smoke: {len(ok)} ok, {len(failed)} failed")
    for f in failed:
        print("  FAILED:", f)
    print("NOTE: smoke numbers are pipeline checks only — NOT a ranking.")
    return 0 if not failed else 1


def _cuda() -> bool:
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
