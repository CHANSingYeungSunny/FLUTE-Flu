"""
_repro.py — shared helpers for the pre-HPC regression tests.

Two independent regressions are supported (pre-HPC clarification 2):

  (a) AGGREGATION regression  — re-aggregate the SAME exported prediction CSV
      with the existing pipeline and with the innovation metrics layer and
      compare row-by-row (see test_aggregation_regression.py).

  (b) END-TO-END pipeline regression — run the SAME model state (a checkpoint
      produced by the existing MIFlu) and the SAME inputs through
      (i) the old MIFlu forward path and (ii) the innovation runner's
      prediction path, then compare the produced predictions and metrics
      (see test_pipeline_regression_endtoend.py).

It also backs the GPT-2 control-adapter reproduction test
(test_gpt2_control_repro.py).

Nothing here downloads anything; the GPT-2 context uses the local cache when
available and falls back to a deterministic synthetic context otherwise.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))  # repo root
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402


def tensor_sha256(t: torch.Tensor) -> str:
    a = t.detach().to("cpu").contiguous().numpy()
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(str(tuple(a.shape)).encode())
    h.update(a.tobytes())
    return h.hexdigest()


def deterministic_settings() -> dict:
    return {
        "torch_deterministic_algorithms": bool(
            torch.are_deterministic_algorithms_enabled()),
        "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
        "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
        "torch_seed_drawn": True,
    }


def make_inputs(L: int, T: int, N: int, batch: int, device: str,
                seed: int = 0):
    """Deterministic (x, htext). htext uses the LOCAL gpt2 cache if present."""
    torch.manual_seed(seed)
    x = torch.randn(batch, N, T, device=device)
    ctx_meta = {"source": "synthetic", "shape": None}
    htext = torch.randn(batch, 8, 768, device=device)
    try:
        from innovation.backbones.gpt2_miflu_adapter import gpt2_cache_available
        if gpt2_cache_available():
            from textual_embedder import TextualInputEmbedder, build_prompt
            from innovation.data_pipeline import load_raw_df, load_scaler
            scaler = load_scaler()
            train_df = load_raw_df().iloc[:scaler.train_end]
            emb = TextualInputEmbedder(device=device)
            prompt = build_prompt(train_df, T=T, L=L)
            with torch.no_grad():
                h = emb(prompt).detach().to(device)          # (1, K, 768)
            htext = h.expand(batch, -1, -1).contiguous()
            ctx_meta = {"source": "gpt2_local_cache", "shape": list(h.shape)}
    except Exception as e:  # pragma: no cover
        ctx_meta = {"source": "synthetic_fallback", "error": str(e),
                    "shape": [batch, 8, 768]}
    return x, htext, ctx_meta


def build_old_and_adapter(L: int, T: int, N: int, device: str, seed: int = 0):
    """Build the existing MIFlu, checkpoint it, and load it into the adapter.

    Returns (old_model, adapter, ckpt_path, ckpt_sha, state_dict_match).
    """
    from miflu_model import MIFlu
    from innovation.backbones.gpt2_miflu_adapter import GPT2MifluAdapter
    from innovation import run_artifacts as ART

    torch.manual_seed(seed)
    old = MIFlu(N=N, T=T, L=L, Lp=24, S=2, K=6, lora_r=4, device=device)
    tmp = tempfile.mkdtemp(prefix="innov_repro_")
    ckpt = os.path.join(tmp, "existing_miflu.pt")
    torch.save(old.state_dict(), ckpt)

    adapter = GPT2MifluAdapter(T=T, N=N, L=L, device=device)
    sd = torch.load(ckpt, map_location=device, weights_only=True)
    adapter.inner.load_state_dict(sd, strict=True)
    match = (ART.state_dict_sha256(adapter.inner.state_dict())
             == ART.state_dict_sha256(old.state_dict()))
    return old, adapter, ckpt, ART.sha256_file(ckpt), bool(match)


def old_forward_z(old_model, x, htext, device):
    # MIFlu does train_mean.view(1, -1, 1): pass 1-D (N,) so the reshape is (1, N, 1).
    n = x.shape[1]
    tm = torch.zeros(n, device=device)
    ts = torch.ones(n, device=device)
    with torch.no_grad():
        yh_rev, _phys, _m, _s = old_model(x, htext=htext,
                                          train_mean=tm, train_std=ts)
    return yh_rev


def old_path_frame(old_model, X, Y, idx, T, L, scaler, htext, device,
                   batch_size: int = 16) -> pd.DataFrame:
    """Old-pipeline prediction frame (same schema as the innovation runner)."""
    from cdc_calendar import attach_calendar

    N = X.shape[1]
    # Feed the scaler's real mean/std so MIFlu's y_phys is the SAME physical
    # quantity the innovation runner computes (z * scale + mean).
    tm = torch.as_tensor(np.asarray(scaler.mean_, dtype=np.float32), device=device)
    ts = torch.as_tensor(np.asarray(scaler.scale_, dtype=np.float32), device=device)
    rows = []
    with torch.no_grad():
        for s in range(0, len(X), batch_size):
            bx = torch.from_numpy(X[s:s + batch_size]).to(device)
            bsz = bx.size(0)
            ht = htext[:bsz] if htext.shape[0] >= bsz else htext.expand(bsz, -1, -1)
            yh_rev, yh_phys, _m, _s = old_model(bx, htext=ht, train_mean=tm,
                                                train_std=ts)
            by = Y[s:s + batch_size]
            gt_z, pr_z = by[:, 4, :], yh_rev.cpu().numpy()[:, 4, :]
            gt_p = gt_z * float(scaler.scale_[4]) + float(scaler.mean_[4])
            pr_p = yh_phys.cpu().numpy()[:, 4, :]
            for r in range(bsz):
                base = int(idx[s + r]) + int(T)
                for step in range(L):
                    rows.append(("val", base + step, step, float(gt_z[r, step]),
                                 float(pr_z[r, step]), float(gt_p[r, step]),
                                 float(pr_p[r, step])))
    df = pd.DataFrame(rows, columns=[
        "split", "abs_week", "step", "ground_truth_ili", "prediction_ili",
        "ground_truth_ili_phys", "prediction_ili_phys"])
    df = attach_calendar(df, abs_week_col="abs_week")
    return df[["split", "abs_week", "step", "epiweek", "week_start_date",
               "ground_truth_ili", "prediction_ili",
               "ground_truth_ili_phys", "prediction_ili_phys"]]


def diff_stats(a, b) -> dict:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    d = np.abs(a - b)
    return {"max_abs_diff": float(d.max()) if d.size else 0.0,
            "mean_abs_diff": float(d.mean()) if d.size else 0.0,
            "n": int(d.size)}
