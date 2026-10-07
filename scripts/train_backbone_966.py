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
import importlib.util
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from configs import CONFIG, set_seed, VAR_COLS
# A2 protocol code, imported verbatim — NOT re-implemented.
from train_nlinear_966 import (build_windows, eval_mse, load_and_normalize)

ILI_CHANNEL = 4

_BACKBONE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "innovation", "backbones")

# name -> (source file, class, kwargs builder, needs_text_backbone, fidelity label)
BACKBONES = {
    "dlinear":       ("dlinear.py",     "DLinear",         "plain",   False,
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
}

QWEN_MODEL_ID = "Qwen/Qwen2.5-1.5B"


def load_backbone_class(name):
    fn, cls, _mode, _needs, _lbl = BACKBONES[name]
    path = os.path.join(_BACKBONE_DIR, fn)
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
              containment="strict", log=print):
    set_seed(seed + L)                      # A2 convention (same as NLinear/MIFlu)
    T, N = CONFIG["T"], CONFIG["N"]
    Xt, Yt, Xv, Yv, Xte, Yte, _s = build_windows(
        data_dict["data_norm"], T, L, data_dict["train_end"],
        data_dict["val_end"], containment=containment)

    tl = DataLoader(TensorDataset(torch.from_numpy(Xt), torch.from_numpy(Yt)),
                    batch_size=batch, shuffle=True)
    vl = DataLoader(TensorDataset(torch.from_numpy(Xv), torch.from_numpy(Yv)),
                    batch_size=batch, shuffle=False)
    el = DataLoader(TensorDataset(torch.from_numpy(Xte), torch.from_numpy(Yte)),
                    batch_size=batch, shuffle=False)

    model = build_model(name, T, N, L, device)
    pr = param_report(model)
    log(f"  [{name}] L={L} seed={seed} params total={pr['total_parameters']:,} "
        f"trainable={pr['trainable_parameters']:,}")
    if hasattr(model, "set_train_statistics"):
        st = train_only_prompt_statistics(data_dict, L, N)
        model.set_train_statistics(st)
        log(f"  [{name}] Prompt-as-Prefix statistics set from TRAIN rows only "
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

    out = {"L": L, "seed": seed, "best_val": best_val, "best_epoch": best_epoch,
           "n_train": int(len(Xt)), "n_val": int(len(Xv)), "n_test": int(len(Xte)),
           "params": pr, "epoch_rows": ep_rows}

    if os.environ.get("DEFER_TEST") == "1":
        log(f"  [{name}] DEFER_TEST=1 - Test NOT evaluated (validation-only fit)")
        p, side = save_locked_ckpt(model, ckpt_dir, name, L, seed)
        n_frozen = sum(1 for n, q in model.named_parameters() if not q.requires_grad)
        log(f"  [{name}] locked best-val ckpt -> {p}"
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
        except Exception as e:
            print(f"[self-check] {name:<14} UNAVAILABLE: {type(e).__name__}: {e}")
            ok = False
    print(f"[self-check] {'PASS' if ok else 'FAIL'}")
    return ok


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


def main():
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
    a = ap.parse_args()

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
    ckpt_dir = a.ckpt_dir or os.path.join("checkpoints", a.backbone)
    export_dir = a.export_dir or os.path.join("results", "author_966", a.backbone)
    os.makedirs(export_dir, exist_ok=True)
    metrics_path = os.path.join(export_dir, "metrics.csv")

    print(f"[A2] run_config backbone={a.backbone} containment={a.containment} "
          f"profile={a.profile} horizon={a.horizon} seed={a.seed} device={device}")
    print(f"[A2] fidelity_label: {BACKBONES[a.backbone][4]}")

    dd = load_and_normalize(a.profile)
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
        if os.path.exists(os.path.join(ckpt_dir, f"best_{a.backbone}_L{key[0]}_seed{key[1]}.pth")):
            done.add(key)
    if done:
        print(f"[A2] RESUME: {len(done)} (L, seed) fits already complete: {sorted(done)}")

    for L in L_list:
        if (L, a.seed) in done:
            print(f"  [L={L}] seed={a.seed} already complete, skipping")
            continue
        t0 = time.time()
        r = train_one(dd, a.backbone, L, a.seed, a.epochs, a.batch, device,
                      ckpt_dir, a.containment)
        if a.epoch_log_dir:
            os.makedirs(a.epoch_log_dir, exist_ok=True)
            pd.DataFrame(r["epoch_rows"]).to_csv(
                os.path.join(a.epoch_log_dir,
                             f"epochs_{a.backbone}_L{L}_seed{a.seed}.csv"), index=False)
        row = {"backbone": a.backbone, "L": L, "seed": a.seed,
               "fidelity_label": BACKBONES[a.backbone][4],
               "mse_all": r["mse_all"], "mae_all": r["mae_all"],
               "mse_ili": r["mse_ili"], "mae_ili": r["mae_ili"],
               "best_val": r["best_val"], "best_epoch": r["best_epoch"],
               "n_train": r["n_train"], "n_val": r["n_val"], "n_test": r["n_test"],
               "total_parameters": r["params"]["total_parameters"],
               "trainable_parameters": r["params"]["trainable_parameters"],
               "ckpt": r["ckpt"] or "",
               "ckpt_sidecar": r.get("ckpt_sidecar") or ""}
        rows = [x for x in rows if (int(x["L"]), int(x["seed"])) != (L, a.seed)]
        rows.append(row)
        pd.DataFrame(rows).to_csv(metrics_path, index=False)
        verdict = ("TEST DEFERRED" if r["mse_all"] is None
                   else f"mse_all={r['mse_all']:.6f}")
        print(f"[{a.backbone}] L={L} seed={a.seed} {verdict} "
              f"best_val={r['best_val']:.6f} best_epoch={r['best_epoch']} "
              f"({time.time()-t0:.1f}s)")
    print(f"[{a.backbone}] DONE -> {metrics_path}")


if __name__ == "__main__":
    main()
