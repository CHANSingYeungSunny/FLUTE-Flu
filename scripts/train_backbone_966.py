"""
train_backbone_966.py — generic author-966 runner for the SIX remaining models
of the eight-model comparison (DLinear, PatchTST-inspired, iTransformer,
Qwen Time-LLM, CALF, TimeCMA).

WHY THIS RUNNER EXISTS
----------------------
The eight-model comparison on the author 966-row snapshot needs the SAME frozen
protocol as A2. MIFlu and NLinear already ran under it through
`train_miflu.py` / `train_nlinear_966.py`; their 24 fits are REUSED unchanged.
The other six backbones currently only exist inside the B-track 1,025-row
`innovation` machinery, which is bound to a different split, a different metric
code path and the legacy target-start window rule. Re-running them there would
not be comparable.

This runner therefore imports the A2 data-prep and window code
**verbatim** from `train_nlinear_966.py` (no re-implementation, so protocol
identity is by construction) and swaps only the model factory. Consequences:

  * identical data, identical full-SHA-256 profile check, identical train-only
    scaler, identical `--containment strict` window rule, identical
    `set_seed(seed + L)` convention, identical Adam lr=5e-4 / batch / epochs,
    identical validation-MSE checkpoint selection, identical DEFER_TEST gate;
  * the model classes are the SAME source files used by the B-track, so no
    architectural drift is introduced. They are loaded by file path so the
    heavy `backbones/__init__.py` registry is not executed.

ARCHITECTURE LABELS (do not upgrade these silently)
---------------------------------------------------
`dlinear` and `itransformer` are faithful re-implementations of the published
mechanisms. `patchtst` is a SUPERVISED, reduced-capacity re-implementation
with no RevIN and no self-supervised pretraining -> it stays labelled
"PatchTST-inspired"; claiming canonical PatchTST would require a separate
implementation and separate budget. `qwen_time_llm`, `calf_llm` and
`timecma_llm` are INSPIRED simplifications (frozen Qwen2.5-1.5B / GPT-2
backbone + named component contract), not the published systems.

MODEL-SPECIFIC LOSSES
---------------------
`calf_llm` exposes `auxiliary_loss()` (feature regularisation + output
consistency). It is ADDED to the z-space MSE, otherwise the alignment terms
would be dead code and the model would silently degenerate to
`forecast_head(series_repr)`. `qwen_time_llm` requires train-only Prompt-as-
Prefix statistics; they are computed from the TRAIN split only.

Usage:
  python scripts/train_backbone_966.py --backbone dlinear --horizon 24 --seed 42 \
      --profile author_966 --containment strict --ckpt-dir ... --export-dir ...
  python scripts/train_backbone_966.py --self-check      # CPU, no training
  python scripts/train_backbone_966.py --preflight --backbone calf_llm
"""
import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from configs import CONFIG, set_seed, VAR_COLS, resolve_profile
# A2 protocol code, imported verbatim — NOT re-implemented.
from train_nlinear_966 import (build_windows, eval_mse, load_and_normalize)
# Rolling-origin splitter (additive): `--fold 0` (default) = the fixed split.
import walk_forward

ILI_CHANNEL = 4

_BACKBONE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "innovation", "backbones")

# name -> (source file, class, kwargs builder, needs_text_backbone, fidelity label)
BACKBONES = {
    "dlinear":       ("dlinear.py",     "DLinear",         "plain",   False,
                      "re-implementation (Zeng et al., AAAI 2023)"),
    # NLinear is the linear representative for the EXPANDED benchmark: DLinear is
    # already a competitor in the essay's own Table V, so re-running it adds no
    # new baseline. Our DLinear numbers are kept as a replication reference only.
    "nlinear":       ("dlinear.py",     "NLinear",         "plain",   False,
                      "re-implementation (Zeng et al., AAAI 2023)"),
    "patchtst":      ("patchtst.py",    "PatchTST",        "plain",   False,
                      "PatchTST-INSPIRED (supervised, no RevIN, no pretraining, reduced capacity)"),
    "itransformer":  ("itransformer.py", "ITransformer",   "plain",   False,
                      "re-implementation (Liu et al., ICLR 2024)"),
    "qwen_time_llm": ("llm_inspired.py", "QwenTimeLLM",    "qwen",    True,
                      "Time-LLM-INSPIRED (frozen Qwen2.5-1.5B, patch prototype reprogramming, Prompt-as-Prefix)"),
    "calf_llm":      ("llm_inspired.py", "CALFInspired",   "gpt2",    True,
                      "CALF-INSPIRED (frozen GPT-2, parallel branches, 2 alignment losses)"),
    "timecma_llm":   ("llm_inspired.py", "TimeCMAInspired", "gpt2",   True,
                      "TimeCMA-INSPIRED (frozen GPT-2, retrieval alignment, last-token branch)"),
    # ── expanded non-LLM benchmark (2026-10-31) ──────────────────────────
    "dnn":           ("classic_nn.py",  "DNN",              "plain",   False,
                      "DNN baseline (per-channel MLP, INSPIRED_SIMPLIFICATION)"),
    "cnn":           ("classic_nn.py",  "CNN",              "plain",   False,
                      "CNN baseline (per-channel 1-D conv, INSPIRED_SIMPLIFICATION)"),
    "rnn":           ("classic_nn.py",  "RNN",              "plain",   False,
                      "RNN baseline (per-channel vanilla RNN, INSPIRED_SIMPLIFICATION)"),
    "lstm":          ("classic_nn.py",  "LSTM",             "plain",   False,
                      "LSTM baseline (per-channel LSTM, INSPIRED_SIMPLIFICATION)"),
    "gru":           ("classic_nn.py",  "GRU",              "plain",   False,
                      "GRU baseline (per-channel GRU, INSPIRED_SIMPLIFICATION)"),
    # ── the LLM-adapter arm (2026-11-01) ───────────────────────────────────
    # NOT one of the 16 benchmark arms: this is the adapter that lets the
    # `docs/LLM_ARMS.md` roster enter the benchmark at all (frozen encoder +
    # ONE shared Linear(D,L) head, channel-independent). `--mock-encoder` and
    # `--dry-run` exercise the whole path on CPU with no model download; such a
    # cell is probe-only and must never enter results (AGENTS.md rule 13(b)).
    "llm_encoder":   ("llm_encoder_backbone.py", "FrozenLLMEncoder", "llm", True,
                      "frozen-LLM encoder + shared linear head "
                      "(cross-scale probe, methodology item 3)"),
}

QWEN_MODEL_ID = "Qwen/Qwen2.5-1.5B"

#: Options for the frozen-LLM encoder arm, filled from the CLI in `main()`.
#: Kept module-level (like QWEN_MODEL_ID) so `build_model`'s signature — which
#: every existing call site uses — does not change.
LLM_ENCODER_OPTS = {"mock_encoder": False}

#: Optional train/val window caps for a CPU dry run (`None` = every window).
#: The TEST split is never capped: the dry run must still emit the real W.
TRAIN_LIMITS = {"max_train": None, "max_val": None}


def load_backbone_class(name):
    """Load a backbone class from its source file by path.

    Resolution order: `scripts/innovation/backbones/<file>` (where the 16
    existing arms live), then `scripts/<file>` (the standalone LLM adapter,
    `llm_encoder_backbone.py`, lives next to this runner). Executing the file
    directly is what keeps `backbones/__init__.py` — and its heavy registry —
    out of the process.
    """
    fn, cls, _mode, _needs, _lbl = BACKBONES[name]
    candidates = [os.path.join(_BACKBONE_DIR, fn),
                  os.path.join(os.path.dirname(os.path.abspath(__file__)), fn)]
    path = next((p for p in candidates if os.path.exists(p)), candidates[0])
    spec = importlib.util.spec_from_file_location(f"_bb_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, cls)


def build_model(name, T, N, L, device):
    cls = load_backbone_class(name)
    _fn, _cls, mode, needs_text, _lbl = BACKBONES[name]
    if mode == "qwen":
        m = cls(T=T, N=N, L=L, model_id=QWEN_MODEL_ID, load_backbone=True)
    elif mode == "gpt2":
        m = cls(T=T, N=N, L=L, model_id="gpt2", load_backbone=True)
    elif mode == "llm":
        # frozen-LLM encoder: model id / revision / encoder batch size / mock
        # switch all arrive through LLM_ENCODER_OPTS (set by main()).
        m = cls(T=T, N=N, L=L, **LLM_ENCODER_OPTS)
    else:
        m = cls(T=T, N=N, L=L)
    return m.to(device)


def train_only_prompt_statistics(dd, L, N):
    """Prompt-as-Prefix statistics from the TRAIN rows only (no val/Test)."""
    tr = dd["train_df"][VAR_COLS]
    return {"horizon": int(L), "channel_count": int(N),
            "target_name": "ILITOTAL",
            "train_rows": int(len(tr)),
            "mean": {c: float(tr[c].mean()) for c in VAR_COLS},
            "std": {c: float(tr[c].std(ddof=0)) for c in VAR_COLS},
            "min": {c: float(tr[c].min()) for c in VAR_COLS},
            "max": {c: float(tr[c].max()) for c in VAR_COLS}}


def param_report(model):
    tot = sum(p.numel() for p in model.parameters())
    tr = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"total_parameters": int(tot), "trainable_parameters": int(tr)}


def save_locked_ckpt(model, ckpt_dir, name, L, seed):
    """Persist the best-validation weights.

    Frozen text-backbone tensors (Qwen2.5-1.5B / GPT-2) are NOT stored: they are
    bit-identically reconstructible from the pinned local snapshot recorded in
    `innovation/assets.py`, and storing them would cost ~3 GB per Qwen fit
    (36 GB for 12 fits) for zero information. Their key set is written to a
    sidecar so the scoring step can prove the reconstruction is exact instead of
    trusting it. A100 memory: the Qwen backbone is loaded in fp32 (3.1 GB) and
    never receives gradients, so peak VRAM is dominated by activations.
    """
    os.makedirs(ckpt_dir, exist_ok=True)
    frozen = {n for n, p in model.named_parameters() if not p.requires_grad}
    sd = model.state_dict()
    keep = {k: v.detach().cpu().clone() for k, v in sd.items() if k not in frozen}
    p = os.path.join(ckpt_dir, f"best_{name}_L{L}_seed{seed}.pth")
    torch.save(keep, p)
    side = os.path.join(ckpt_dir, f"best_{name}_L{L}_seed{seed}.frozen_keys.json")
    json.dump({"frozen_keys": sorted(frozen),
               "n_stored_tensors": len(keep),
               "n_frozen_tensors": len(frozen),
               "asset": ("Qwen/Qwen2.5-1.5B@8faed761d45a263340a0528343f099c05c9a4323"
                         if name == "qwen_time_llm" else
                         ("gpt2@607a30d783dfa663caf39e06633721c8d4cfcd7e"
                          if name in ("calf_llm", "timecma_llm") else None)),
               "note": "frozen backbone tensors are reconstructed from the pinned "
                       "local snapshot and intentionally not stored"},
              open(side, "w"), indent=2)
    return p, side


def train_one(data_dict, name, L, seed, epochs, batch, device, ckpt_dir,
              containment="strict", log=print, max_train=None, max_val=None,
              arm_label=None):
    set_seed(seed + L)                      # A2 convention (same as NLinear/MIFlu)
    t_start = time.time()
    # `name` selects the backbone class; `label` is the benchmark arm identity
    # (default: identical). They differ only for the frozen-LLM adapter, where
    # one backbone serves 14 models: the label makes each one its own row
    # (`pred_<label>_L<L>_s<seed>.npz`, which is what analysis_expanded.py globs).
    label = arm_label or name
    T, N = CONFIG["T"], CONFIG["N"]
    Xt, Yt, Xv, Yv, Xte, Yte, _s = build_windows(
        data_dict["data_norm"], T, L, data_dict["train_end"],
        data_dict["val_end"], containment=containment)
    # Optional caps for a CPU wiring proof (`--dry-run`). They shorten ONLY the
    # fit — the test split is untouched, so the exported cell still carries the
    # real window count (170/158/146/134) and the real evaluation slice.
    if max_train is not None:
        Xt, Yt = Xt[:int(max_train)], Yt[:int(max_train)]
    if max_val is not None:
        Xv, Yv = Xv[:int(max_val)], Yv[:int(max_val)]

    tl = DataLoader(TensorDataset(torch.from_numpy(Xt), torch.from_numpy(Yt)),
                    batch_size=batch, shuffle=True)
    vl = DataLoader(TensorDataset(torch.from_numpy(Xv), torch.from_numpy(Yv)),
                    batch_size=batch, shuffle=False)
    el = DataLoader(TensorDataset(torch.from_numpy(Xte), torch.from_numpy(Yte)),
                    batch_size=batch, shuffle=False)

    model = build_model(name, T, N, L, device)
    pr = param_report(model)
    log(f"  [{label}] L={L} seed={seed} params total={pr['total_parameters']:,} "
        f"trainable={pr['trainable_parameters']:,}")
    # Frozen-encoder arms (llm_encoder) expose provenance for the manifest.
    prov = model.provenance() if hasattr(model, "provenance") else None
    if prov:
        log(f"  [{label}] frozen encoder {prov['model_id']}@{prov['revision']} "
            f"({prov['encoder']['parameters']:,} params, trainable="
            f"{prov['encoder']['trainable_parameters']}) | head "
            f"{prov['head']['parameters']:,} params | device={prov['device']} | "
            f"encoder_batch_size={prov['encoder_batch_size']} | "
            f"mock_encoder={prov['mock_encoder']}")
    if hasattr(model, "set_train_statistics"):
        st = train_only_prompt_statistics(data_dict, L, N)
        model.set_train_statistics(st)
        log(f"  [{label}] Prompt-as-Prefix statistics set from TRAIN rows only "
            f"(n={st['train_rows']})")

    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=5e-4)
    crit = nn.MSELoss()
    has_aux = hasattr(model, "auxiliary_loss")

    best_val, best_state, best_epoch = float("inf"), None, -1
    ep_rows = []
    for ep in range(epochs):
        model.train()
        tot_loss = nb = 0.0
        for bx, by in tl:
            bx, by = bx.to(device), by.to(device)
            opt.zero_grad()
            out = model(bx)
            loss = crit(out, by)
            if has_aux:                     # CALF: alignment terms must be live
                loss = loss + model.auxiliary_loss()
            loss.backward()
            opt.step()
            tot_loss += float(loss.detach()); nb += 1
        v_mse_all, v_mae_all, _, _ = eval_mse(model, vl, device)
        if v_mse_all < best_val:
            best_val, best_epoch = v_mse_all, ep
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        row = {"epoch": ep + 1, "train_loss": tot_loss / max(nb, 1),
               "val_mse_all": v_mse_all, "val_mae_all": v_mae_all}
        ep_rows.append(row)
        log(f"    ep {ep+1:>2}/{epochs} | train_loss={row['train_loss']:.6f} "
            f"| val_mse={v_mse_all:.6f}(All) | val_mae={v_mae_all:.6f}")
    if best_state is not None:
        model.load_state_dict(best_state)

    # ── Collect TEST predictions ───────────────────────────────────────────
    # Needed downstream for the per-step MSE / PTE-PIE / denormalised plots.
    # metrics.csv alone is not enough: those analyses need every test window's
    # predicted and true values on the z-scale.
    _preds, _trues = [], []
    model.eval()
    with torch.no_grad():
        for _bx, _by in el:
            _preds.append(model(_bx.to(device)).detach().cpu().numpy())
            _trues.append(_by.numpy())
    if _preds:
        test_pred = np.concatenate(_preds)
        test_true = np.concatenate(_trues)
    else:
        test_pred = np.zeros((0, N, L), dtype=np.float32)
        test_true = np.zeros((0, N, L), dtype=np.float32)
    _splits = np.asarray(_s["splits"])
    test_start = np.asarray(_s["target_starts"])[_splits == 2][:len(test_pred)]

    # Persist the frozen-encoder vector cache (llm_encoder only) so a re-run is
    # cheap and bit-identical; a no-op for the 16 trained arms.
    encoder_cache = model.save_cache() if hasattr(model, "save_cache") else None
    if encoder_cache:
        log(f"  [{label}] frozen-encoder cache -> {encoder_cache}")

    out = {"L": L, "seed": seed, "best_val": best_val, "best_epoch": best_epoch,
           "n_train": int(len(Xt)), "n_val": int(len(Xv)), "n_test": int(len(Xte)),
           "params": pr, "epoch_rows": ep_rows,
           "test_pred": test_pred, "test_true": test_true,
           "test_start": test_start, "provenance": prov,
           "encoder_cache": encoder_cache,
           "wall_seconds": time.time() - t_start}

    if os.environ.get("DEFER_TEST") == "1":
        log(f"  [{label}] DEFER_TEST=1 - Test NOT evaluated (validation-only fit)")
        p, side = save_locked_ckpt(model, ckpt_dir, label, L, seed)
        n_frozen = sum(1 for n, q in model.named_parameters() if not q.requires_grad)
        log(f"  [{label}] locked best-val ckpt -> {p}"
            + (f"  ({n_frozen} frozen backbone tensors not stored, see sidecar)"
               if n_frozen else ""))
        out.update({"mse_all": None, "mae_all": None, "mse_ili": None,
                    "mae_ili": None, "ckpt": p, "ckpt_sidecar": side,
                    "test_deferred": True})
        return out
    t_mse_all, t_mae_all, t_mse_ili, t_mae_ili = eval_mse(model, el, device)
    out.update({"mse_all": t_mse_all, "mae_all": t_mae_all,
                "mse_ili": t_mse_ili, "mae_ili": t_mae_ili, "ckpt": None})
    return out


# ── CPU checks: no training, no Test scoring ───────────────────────────────
def self_check(only=None):
    """Architecture self-check. For the text-backed models the real frozen
    backbone IS loaded (gpt2 / Qwen2.5-1.5B from the local cache) so that a
    forward pass is actually verified; a failure to load is reported as
    UNAVAILABLE rather than silently passing."""
    ok = True
    names = [only] if only else list(BACKBONES)
    for name in names:
        try:
            cls = load_backbone_class(name)
        except Exception as e:
            print(f"[self-check] {name:<14} IMPORT FAIL: {type(e).__name__}: {e}")
            ok = False
            continue
        _fn, _cls, mode, _needs, lbl = BACKBONES[name]
        try:
            if mode == "qwen":
                m = cls(T=104, N=7, L=24, model_id=QWEN_MODEL_ID, load_backbone=True)
                m.set_train_statistics({"horizon": 24, "channel_count": 7,
                                       "target_name": "ILITOTAL"})
            elif mode == "gpt2":
                m = cls(T=104, N=7, L=24, model_id="gpt2", load_backbone=True)
            elif mode == "llm":
                # self-check must never download: exercise the arm with the mock
                # encoder. `--preflight --llm-model-id ...` loads the real one.
                m = cls(T=104, N=7, L=24, mock_encoder=True)
            else:
                m = cls(T=104, N=7, L=24)
            m.eval()
            with torch.no_grad():
                y = m(torch.randn(2, 7, 104))
            tot = sum(p.numel() for p in m.parameters())
            tr = sum(p.numel() for p in m.parameters() if p.requires_grad)
            shape_ok = tuple(y.shape) == (2, 7, 24)
            if not shape_ok:
                ok = False
            print(f"[self-check] {name:<14} {cls.__name__:<16} forward={tuple(y.shape)} "
                  f"total={tot:,} trainable={tr:,} backbone_loaded={mode in ('gpt2','qwen')} "
                  f"{'OK' if shape_ok else 'SHAPE-FAIL'}")
            print(f"[self-check] {'':<14} label: {lbl}")
            if mode == "llm":
                print(f"[self-check] {'':<14} mock_encoder=True "
                      f"(self-check never downloads a checkpoint)")
        except Exception as e:
            print(f"[self-check] {name:<14} UNAVAILABLE: {type(e).__name__}: {e}")
            ok = False
    print(f"[self-check] {'PASS' if ok else 'FAIL'}")
    return ok


# ── run manifest (provenance + probe flag) ─────────────────────────────────
def _code_identity(path=None):
    """SHA-256 identity of a source file (this runner by default)."""
    p = os.path.abspath(path or __file__)
    with open(p, "rb") as fh:
        return {"file": p, "sha256": hashlib.sha256(fh.read()).hexdigest()}


def _measured_hardware(run_device):
    """Measured hardware block (AGENTS.md rule 12: measured, never assumed).

    `run_device` is the device this run actually used; the GPU inventory is
    reported separately and flagged as availability, so a CPU probe on a
    GPU-equipped host can never be misread as a GPU run.
    """
    info = {"run_device": str(run_device),
            "cuda_available": bool(torch.cuda.is_available()),
            "gpu_name": None, "gpu_count": 0, "gpu_capability": None,
            "cuda_version": getattr(torch.version, "cuda", None)}
    if torch.cuda.is_available():
        info.update({"gpu_name": torch.cuda.get_device_name(0),
                     "gpu_count": int(torch.cuda.device_count()),
                     "gpu_capability": list(torch.cuda.get_device_capability(0))})
    return info


def write_run_manifest(path, *, backbone, L, seed, provenance, wall_seconds,
                       profile, containment, probe_only, mock_encoder,
                       run_device, config=None, fold=None):
    """Write the per-cell manifest for a frozen-encoder run.

    Carries the rule-12 provenance block (hardware measured at run time, Slurm
    identity, library versions, code sha256) and the rule-13(b) probe flag, so a
    mock/CPU cell is self-labelling and cannot be mistaken for a result.

    `fold` (a `walk_forward.Fold` or `None`) records the rolling-origin geometry
    of the cell, so a fold cell can never be mistaken for a fixed-split cell.
    """
    payload = {
        "model": backbone, "L": int(L), "seed": int(seed),
        "profile": profile, "containment": containment,
        "eval_space": "standardized_train_fit_z",
        "n_eval_windows_rule": "eval_slice(W, batch=16) = (W // 16) * 16",
        "probe_only": bool(probe_only),
        "mock_encoder": bool(mock_encoder),
        "artefact_is_a_result": not (bool(probe_only) or bool(mock_encoder)),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "wall_seconds": None if wall_seconds is None else round(float(wall_seconds), 3),
        "hardware": _measured_hardware(run_device),
        "slurm": {k: os.environ[k] for k in
                  ("SLURM_JOB_ID", "SLURM_JOB_PARTITION", "SLURM_NODELIST")
                  if k in os.environ},
        "library_versions": {"python": platform.python_version(),
                             "torch": torch.__version__,
                             "numpy": np.__version__},
        "code": {"runner": _code_identity()},
        "encoder": provenance,
        "fold": None if fold is None else fold.as_dict(),
        "config": dict(config or {}),
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return path


def preflight(profile, name, L, containment="strict"):
    dd = load_and_normalize(profile)          # verifies the data SHA-256
    T, N = CONFIG["T"], CONFIG["N"]
    Xt, Yt, Xv, Yv, Xte, Yte, sinfo = build_windows(
        dd["data_norm"], T, L, dd["train_end"], dd["val_end"], containment=containment)
    ts, sp = sinfo["target_starts"], sinfo["splits"]
    if containment == "strict":
        assert ((sp == 0) == (ts + L <= dd["train_end"])).all()
        assert ((sp == 1) == ((ts >= dd["train_end"]) & (ts + L <= dd["val_end"]))).all()
        assert ((sp == 2) == ((ts >= dd["val_end"]) & (ts + L <= dd["n"]))).all()
    assert dd["scaler"].train_end == dd["train_end"]
    assert dd["data_norm"].dtype == np.float32
    m = build_model(name, T, N, L, "cpu")
    with torch.no_grad():
        y = m(torch.from_numpy(Xte[:2]).float())
    assert tuple(y.shape) == (2, N, L)
    print(f"[preflight] {name} OK  profile={profile} n={dd['n']} "
          f"train={len(Xt)} val={len(Xv)} test={len(Xte)} "
          f"containment={containment} scaler_train_only=OK")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", required=False, default=None, choices=sorted(BACKBONES))
    ap.add_argument("--horizon", type=int, default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--profile", default="author_966",
                    choices=("project_1025", "author_966"))
    ap.add_argument("--epochs", type=int, default=CONFIG["epochs"])
    ap.add_argument("--batch", type=int, default=CONFIG["batch_size"])
    ap.add_argument("--containment", choices=["start", "strict"], default="start")
    ap.add_argument("--export-dir", default=None)
    ap.add_argument("--ckpt-dir", default=None)
    ap.add_argument("--epoch-log-dir", default=None,
                    help="Directory for the FULL per-epoch trace (no truncation).")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    # ── frozen-LLM encoder arm (llm_encoder) ───────────────────────────────
    ap.add_argument("--encoder-batch-size", type=int, default=8,
                    help="Prompts per frozen-encoder forward. The memory knob: a "
                         "27B/33B encoder is run in chunks, never over the whole "
                         "dataset at once (docs/LLM_ARMS.md: 54.73 GB on an A100).")
    ap.add_argument("--llm-model-id", default=None,
                    help="HuggingFace checkpoint for the frozen encoder arm "
                         "(default: llm_encoder_backbone.DEFAULT_MODEL_ID).")
    ap.add_argument("--llm-revision", default=None,
                    help="Pinned revision sha (required for a real run).")
    ap.add_argument("--llm-allow-unpinned", action="store_true",
                    help="Allow an unpinned revision (probe only).")
    ap.add_argument("--llm-allow-download", action="store_true",
                    help="Allow the encoder to download (default: local files only).")
    ap.add_argument("--encoder-device", default=None, choices=("cpu", "cuda"),
                    help="Device for the frozen encoder (default: the training device).")
    ap.add_argument("--encoder-cache", default=None,
                    help="Persistent encoder-vector cache path (torch save; loaded if "
                         "present, written after the run).")
    ap.add_argument("--mock-encoder", action="store_true",
                    help="Use the CPU mock encoder: no GPU, no model download.")
    ap.add_argument("--mock-hidden-dim", type=int, default=64)
    ap.add_argument("--mock-mode", choices=("embedding", "fixed"), default="embedding")
    ap.add_argument("--max-train-windows", type=int, default=None,
                    help="Cap the TRAIN windows of the fit (dry run only; test split "
                         "is never capped).")
    ap.add_argument("--max-val-windows", type=int, default=None,
                    help="Cap the VALIDATION windows of the fit (dry run only).")
    ap.add_argument("--arm-label", default=None,
                    help="Benchmark arm identity (default: the --backbone name). "
                         "One backbone can serve several arms — the frozen-LLM "
                         "adapter feeds 14 models — and analysis_expanded.py keys "
                         "models off `pred_<label>_L<L>_s<seed>.npz`, so each LLM "
                         "arm MUST pass its own label (e.g. llm_qwen2p5_1p5b).")
    ap.add_argument("--dry-run", action="store_true",
                    help="CPU end-to-end wiring proof: implies --mock-encoder, 1 epoch, "
                         "a tiny train/val subset and a probe-only export dir. The "
                         "cell it writes is NOT a result (AGENTS.md rule 13(b)).")
    ap.add_argument("--probe-only", action="store_true",
                    help="Mark this cell probe_only=True and forbid writing it under "
                         "expanded_runs (AGENTS.md rule 13(b)). Needed for a REAL "
                         "checkpoint probed on a CPU/IO partition: it proves the "
                         "adapter works without producing a number that could enter "
                         "a table.")
    # ── rolling origin (additive; 0 = the existing fixed split) ────────────
    walk_forward.add_fold_argument(ap)
    a = ap.parse_args(argv)

    if os.environ.get("A2_REQUIRE_STRICT") == "1" and a.containment != "strict":
        raise SystemExit("[A2] A2_REQUIRE_STRICT=1 requires --containment strict, "
                         f"got {a.containment!r}")
    if a.self_check:
        sys.exit(0 if self_check(a.backbone) else 1)
    if not a.backbone:
        raise SystemExit("--backbone is required")
    if a.preflight:
        sys.exit(0 if preflight(a.profile, a.backbone, a.horizon or 24, a.containment) else 1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Benchmark arm identity: identical to the backbone for the 16 existing arms.
    arm_label = a.arm_label or a.backbone
    if os.path.sep in arm_label or "/" in arm_label or " " in arm_label:
        raise SystemExit(f"--arm-label must be a single path-free token, got {arm_label!r}")

    # ── --dry-run defaults: CPU, mock encoder, tiny fit, probe-only output ──
    if a.dry_run:
        if a.backbone != "llm_encoder":
            raise SystemExit("--dry-run is implemented for --backbone llm_encoder only")
        if not a.mock_encoder:
            print("[dry-run] forcing --mock-encoder (no GPU, no model download)")
        a.mock_encoder = True
        if a.epochs == CONFIG["epochs"]:
            a.epochs = 1
        if a.max_train_windows is None:
            a.max_train_windows = 32
        if a.max_val_windows is None:
            a.max_val_windows = 16
        if a.export_dir is None:
            a.export_dir = os.path.join("_dryrun", a.backbone)
        if a.ckpt_dir is None:
            a.ckpt_dir = os.path.join("_dryrun", "ckpt")
        if a.encoder_device is None:
            a.encoder_device = "cpu"
        # The wiring proof is a CPU proof: no GPU is touched at all.
        device = "cpu"
        a.encoder_device = "cpu"
    if a.mock_encoder and a.backbone != "llm_encoder":
        raise SystemExit("--mock-encoder is implemented for --backbone llm_encoder only")

    # ── rolling origin: resolve the fold BEFORE reading any data (additive) ──
    # `--fold 0` (default) leaves every line below exactly as it was.
    fold = None
    fold_split = None
    if a.fold:
        _n_rows = int(resolve_profile(a.profile)["n_rows"])
        _te, _ve, fold = walk_forward.fold_from_args(
            a, _n_rows, a.profile, horizon=a.horizon)
        fold_split = (fold.train_end, fold.val_end)
        print(f"[A2] rolling-origin fold {fold.label}: "
              f"train_end={fold.train_end} val_end={fold.val_end} "
              f"test_end={fold.test_end} — the fit may read rows "
              f"[0:{fold.test_end}) only")

    ckpt_dir = a.ckpt_dir or os.path.join("checkpoints", a.backbone)
    if a.export_dir:
        export_dir = a.export_dir
    elif a.fold:
        # A fold cell must never land beside the 204 fixed-split benchmark cells.
        export_dir = os.path.join("hpc_results", "walk_forward", fold.label,
                                  a.backbone)
    else:
        export_dir = os.path.join("results", "author_966", a.backbone)
    # Hard guard for rule 13(b): a mock-encoder cell is a probe and must never
    # land where the benchmark cells live.
    if (a.mock_encoder or a.probe_only or a.dry_run) and "expanded_runs" in os.path.normpath(export_dir):
        raise SystemExit(
            "[rule 13b] refusing to write a mock-encoder cell under expanded_runs: "
            "probe-only artefacts must never enter results")
    # A rolling-origin cell is a different protocol with a different scaler fit;
    # mixing it into the fixed-split tree would silently invalidate both.
    if fold is not None and "expanded_runs" in os.path.normpath(export_dir):
        raise SystemExit(
            "[walk-forward] refusing to write a fold cell under expanded_runs: "
            "rolling-origin cells are not comparable with the fixed-split "
            "benchmark cells (AGENTS.md rule 10)")
    os.makedirs(export_dir, exist_ok=True)
    metrics_path = os.path.join(export_dir, "metrics.csv")

    if a.backbone == "llm_encoder":
        from llm_encoder_backbone import DEFAULT_MODEL_ID as _LLM_MODEL_ID
        from llm_encoder_backbone import DEFAULT_REVISION as _LLM_REVISION
        LLM_ENCODER_OPTS.update({
            "model_id": a.llm_model_id or _LLM_MODEL_ID,
            "revision": a.llm_revision if a.llm_revision is not None else _LLM_REVISION,
            "encoder_batch_size": a.encoder_batch_size,
            "device": a.encoder_device or device,
            "mock_encoder": bool(a.mock_encoder),
            "mock_hidden_dim": a.mock_hidden_dim,
            "mock_mode": a.mock_mode,
            "local_files_only": not a.llm_allow_download,
            "allow_unpinned_revision": bool(a.llm_allow_unpinned),
            "cache_path": a.encoder_cache,
        })
        TRAIN_LIMITS.update({"max_train": a.max_train_windows,
                             "max_val": a.max_val_windows})

    print(f"[A2] run_config backbone={a.backbone} containment={a.containment} "
          f"profile={a.profile} horizon={a.horizon} seed={a.seed} device={device}")
    if a.backbone == "llm_encoder":
        print(f"[A2] llm_encoder: model_id={LLM_ENCODER_OPTS['model_id']} "
              f"revision={LLM_ENCODER_OPTS['revision']} "
              f"encoder_batch_size={LLM_ENCODER_OPTS['encoder_batch_size']} "
              f"mock_encoder={LLM_ENCODER_OPTS['mock_encoder']} "
              f"epochs={a.epochs} max_train={TRAIN_LIMITS['max_train']} "
              f"max_val={TRAIN_LIMITS['max_val']} dry_run={bool(a.dry_run)}")
        if a.mock_encoder:
            print("[A2] PROBE ONLY: mock encoder -> this cell is NOT a result and "
                  "must never enter paper_tables/ or any aggregation (rule 13b)")
    print(f"[A2] fidelity_label: {BACKBONES[a.backbone][4]}")

    dd = load_and_normalize(a.profile, split=fold_split)
    if fold is not None:
        # The fold may read rows[0:test_end] ONLY. Truncating here is what stops
        # build_windows from labelling the whole tail of the series as "test".
        dd = walk_forward.restrict_data(dd, fold)
        print(f"[A2] fold {fold.label}: profile={a.profile} n={dd['n']} "
              f"train_end={dd['train_end']} val_end={dd['val_end']} "
              f"test_end={fold.test_end} split_source={dd['split_source']} "
              f"(scaler re-fitted on this fold's train prefix only)")
    L_list = [a.horizon] if a.horizon is not None else CONFIG["L_list"]

    rows = []
    if os.path.exists(metrics_path):
        try:
            rows = pd.read_csv(metrics_path).to_dict("records")
        except Exception:
            rows = []
    # Resume is keyed on (L, seed) AND the locked per-seed checkpoint, never on a
    # Test metric (which is deliberately absent while DEFER_TEST=1).
    done = set()
    for r in rows:
        try:
            key = (int(r["L"]), int(r["seed"]))
        except (KeyError, TypeError, ValueError):
            continue
        if os.path.exists(os.path.join(ckpt_dir, f"best_{arm_label}_L{key[0]}_seed{key[1]}.pth")):
            done.add(key)
    if done:
        print(f"[A2] RESUME: {len(done)} (L, seed) fits already complete: {sorted(done)}")

    for L in L_list:
        if (L, a.seed) in done:
            print(f"  [L={L}] seed={a.seed} already complete, skipping")
            continue
        t0 = time.time()
        r = train_one(dd, a.backbone, L, a.seed, a.epochs, a.batch, device,
                      ckpt_dir, a.containment,
                      max_train=TRAIN_LIMITS["max_train"],
                      max_val=TRAIN_LIMITS["max_val"],
                      arm_label=arm_label)
        if a.epoch_log_dir:
            os.makedirs(a.epoch_log_dir, exist_ok=True)
            pd.DataFrame(r["epoch_rows"]).to_csv(
                os.path.join(a.epoch_log_dir,
                             f"epochs_{arm_label}_L{L}_seed{a.seed}.csv"), index=False)
        row = {"backbone": arm_label, "L": L, "seed": a.seed,
               "fidelity_label": BACKBONES[a.backbone][4],
               "mse_all": r["mse_all"], "mae_all": r["mae_all"],
               "mse_ili": r["mse_ili"], "mae_ili": r["mae_ili"],
               "best_val": r["best_val"], "best_epoch": r["best_epoch"],
               "n_train": r["n_train"], "n_val": r["n_val"], "n_test": r["n_test"],
               "total_parameters": r["params"]["total_parameters"],
               "trainable_parameters": r["params"]["trainable_parameters"],
               "ckpt": r["ckpt"] or "",
               "ckpt_sidecar": r.get("ckpt_sidecar") or ""}
        if r.get("provenance"):
            row["model_id"] = r["provenance"]["model_id"]
            row["revision"] = r["provenance"]["revision"]
            row["probe_only"] = bool(a.mock_encoder or a.dry_run or a.probe_only)
        rows = [x for x in rows if (int(x["L"]), int(x["seed"])) != (L, a.seed)]
        rows.append(row)
        pd.DataFrame(rows).to_csv(metrics_path, index=False)
        # ── per-window TEST predictions (for per-step MSE / PTE-PIE / plots) ──
        if r.get("test_pred") is not None and len(r["test_pred"]):
            npz_path = os.path.join(
                export_dir, f"pred_{arm_label}_L{L}_s{a.seed}.npz")
            _cell = dict(
                pred=r["test_pred"].astype(np.float32),
                target=r["test_true"].astype(np.float32),
                target_start_row=r["test_start"].astype(np.int32),
                L=np.int32(L), seed=np.int32(a.seed),
                var_cols=np.array(VAR_COLS), model=np.array(arm_label),
                profile=np.array(a.profile), containment=np.array(a.containment),
                space=np.array("standardized_train_fit_z"))
            if fold is not None:
                # Fold metadata exists ONLY on fold cells, so a fixed-split cell
                # keeps exactly the key set it has always had.
                _cell.update(fold=np.int32(fold.index),
                             fold_test_end=np.int32(fold.test_end),
                             n_train_rows=np.int32(r["n_train"]),
                             n_val_rows=np.int32(r["n_val"]))
            np.savez_compressed(npz_path, **_cell)
            print(f"[{arm_label}] predictions -> {npz_path}")
        # ── run manifest (frozen-encoder arms, and EVERY fold cell) ──────────
        # A fold cell always gets a manifest: its geometry (borders, scaler fit,
        # test block) is what makes it reproducible, and a fold run has no
        # fixed-split counterpart to compare against.
        if r.get("provenance") or fold is not None:
            mpath = write_run_manifest(
                os.path.join(export_dir,
                             f"manifest_{arm_label}_L{L}_s{a.seed}.json"),
                backbone=arm_label, L=L, seed=a.seed,
                provenance=r["provenance"], wall_seconds=r.get("wall_seconds"),
                profile=a.profile, containment=a.containment,
                probe_only=bool(a.dry_run or a.mock_encoder or a.probe_only),
                mock_encoder=bool(a.mock_encoder),
                run_device=device,
                fold=fold,
                config={"epochs": a.epochs, "batch": a.batch,
                        "encoder_batch_size": LLM_ENCODER_OPTS.get("encoder_batch_size"),
                        "max_train_windows": TRAIN_LIMITS["max_train"],
                        "max_val_windows": TRAIN_LIMITS["max_val"],
                        "encoder_device": a.encoder_device,
                        "dry_run": bool(a.dry_run),
                        "epoch_rows": r["epoch_rows"],
                        "n_train": r["n_train"], "n_val": r["n_val"],
                        "n_test": r["n_test"],
                        "split_source": dd.get("split_source", "profile"),
                        "train_end": dd["train_end"],
                        "val_end": dd["val_end"]})
            print(f"[{arm_label}] manifest -> {mpath}")
        verdict = ("TEST DEFERRED" if r["mse_all"] is None
                   else f"mse_all={r['mse_all']:.6f}")
        print(f"[{arm_label}] L={L} seed={a.seed} {verdict} "
              f"best_val={r['best_val']:.6f} best_epoch={r['best_epoch']} "
              f"({time.time()-t0:.1f}s)")
    print(f"[{arm_label}] DONE -> {metrics_path}")


if __name__ == "__main__":
    main()
