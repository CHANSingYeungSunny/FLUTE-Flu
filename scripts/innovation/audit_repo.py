"""
audit_repo.py — machine-checkable repository audit (runtime facts).
==================================================================

Writes into `results/innovation/audit/`:
  * plan_sha256.json            authoritative plan hash RECOMPUTED at runtime
  * environment.txt             interpreter + library versions
  * dependency_probe.json       local availability of every plugin dependency
  * prompt_variation_report.json unique-prompt count + embedding variance
                                (revision 6: if all prompts are identical, the
                                TF-IDF+SVD context is a fixed contextual
                                embedding baseline)

The narrative audit (`audit.md`), the compliance matrix
(`plan_compliance_matrix.md`), the early-stopping audit
(`early_stopping_audit.md`) and the frozen peak-criteria spec
(`peak_criteria_spec.md`) are static documents written alongside these.
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from innovation import run_artifacts as ART  # noqa: E402
from innovation.paths import AUDIT_DIR, HORIZONS, ensure_innovation_dirs, plan_sha256_status  # noqa: E402


def dependency_probe() -> dict:
    probe = {"libraries": {}, "models": {}, "unavailable": []}

    for mod in ("torch", "transformers", "numpy", "pandas", "scipy", "sklearn",
                "statsmodels", "matplotlib"):
        try:
            m = __import__(mod)
            probe["libraries"][mod] = {"available": True,
                                       "version": getattr(m, "__version__", "?")}
        except Exception as e:
            probe["libraries"][mod] = {"available": False, "error": str(e)}
            probe["unavailable"].append(f"lib:{mod}")

    from innovation.backbones.gpt2_miflu_adapter import gpt2_cache_available
    probe["models"]["gpt2"] = {"available": bool(gpt2_cache_available()),
                               "kind": "local HF cache"}
    for m in ("fasttext", "bert", "minilm", "chronos", "timesfm", "moirai"):
        probe["models"][m] = {"available": False,
                              "status": "UNAVAILABLE_LOCAL_DEPENDENCY",
                              "note": "deferred to batch 2; never downloaded"}

    try:
        from innovation.backbones import available_backbones
        from innovation.encoders import available_encoders
        from innovation.fusion import available_fusions
        probe["backbones"] = available_backbones()
        probe["encoders"] = available_encoders()
        probe["fusions"] = available_fusions()
    except Exception as e:  # pragma: no cover
        probe["registry_error"] = str(e)
    return probe


def prompt_variation_report() -> dict:
    """Count unique prompts (train-only) and measure embedding variance."""
    from innovation.data_pipeline import load_raw_df, load_scaler
    from textual_embedder import build_prompt

    scaler = load_scaler()
    train_df = load_raw_df().iloc[:scaler.train_end]
    prompts = {L: build_prompt(train_df, T=104, L=L) for L in HORIZONS}
    unique_prompts = sorted(set(prompts.values()))
    rep = {
        "n_horizons": len(HORIZONS),
        "n_unique_prompts": len(unique_prompts),
        "identical_across_horizons": len(unique_prompts) == 1,
        "per_horizon_prompt_length": {int(L): len(p) for L, p in prompts.items()},
        "within_horizon_variation": 0,
        "note": ("The prompt depends only on train-set min/max statistics and "
                 "the horizon L, so it is CONSTANT across weeks within a "
                 "horizon. With <2 unique prompts the TF-IDF+SVD encoder "
                 "yields a FIXED CONTEXTUAL EMBEDDING baseline."),
    }

    try:
        from innovation.backbones.gpt2_miflu_adapter import gpt2_cache_available
        if gpt2_cache_available():
            from textual_embedder import TextualInputEmbedder
            import torch
            emb = TextualInputEmbedder(device="cpu")
            vecs = []
            with torch.no_grad():
                for L in HORIZONS:
                    h = emb(prompts[L])                 # (1, K, 768)
                    vecs.append(h.mean(dim=1).squeeze(0).numpy())
            V = np.vstack(vecs)
            var = np.var(V, axis=0)
            rep["embedding_variance"] = {
                "per_dim_mean_var": float(np.mean(var)),
                "per_dim_max_var": float(np.max(var)),
                "pairwise_cosine_min": float(_cos_min(V)),
            }
        else:
            rep["embedding_variance"] = {"status": "UNAVAILABLE_LOCAL_DEPENDENCY"}
    except Exception as e:  # pragma: no cover
        rep["embedding_variance"] = {"error": str(e)}
    return rep


def _cos_min(V: np.ndarray) -> float:
    Vn = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-12)
    C = Vn @ Vn.T
    iu = np.triu_indices(len(V), k=1)
    return float(C[iu].min()) if len(iu[0]) else 1.0


def main(argv=None) -> int:
    ensure_innovation_dirs()
    os.makedirs(AUDIT_DIR, exist_ok=True)

    plan = plan_sha256_status()
    ART.write_json(os.path.join(AUDIT_DIR, "plan_sha256.json"), plan)

    with open(os.path.join(AUDIT_DIR, "environment.txt"), "w", encoding="utf-8") as f:
        import platform
        f.write(f"platform: {platform.platform()}\npython: {platform.python_version()}\n")
        for mod in ("torch", "transformers", "numpy", "pandas", "scipy",
                    "sklearn", "statsmodels", "matplotlib"):
            try:
                m = __import__(mod)
                f.write(f"{mod}: {getattr(m, '__version__', '?')}\n")
            except Exception:
                f.write(f"{mod}: UNAVAILABLE\n")

    dep = dependency_probe()
    ART.write_json(os.path.join(AUDIT_DIR, "dependency_probe.json"), dep)

    pv = prompt_variation_report()
    ART.write_json(os.path.join(AUDIT_DIR, "prompt_variation_report.json"), pv)

    print("[audit_repo] plan sha256 matches:", plan["matches"])
    if not plan["matches"]:
        print("[audit_repo][BLOCK] plan hash changed:",
              plan["sha256_expected"], "->", plan["sha256_runtime"])
    print("[audit_repo] unavailable deps:", dep["unavailable"])
    print("[audit_repo] unique prompts:", pv["n_unique_prompts"])
    return 0 if plan["matches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
