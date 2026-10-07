#!/usr/bin/env python3
"""Stage 5 A2 independent Test-scoring entry.

Scores 36 learned fits (miflu/no_multi/nlinear x 4 L x 3 seeds) from locked
per-(model,L,seed) checkpoints + 8 naive baselines, on author_966 Test
(containment=strict), with ONE metric code path.
Primary: 7-variable standardized MSE. average_MSE_4L = mean over seeds, then
equal-weight mean over L. Supplementary: per-var MSE/MAE, per-var original-unit
MAE/RMSE, ILITOTAL (ch 4) MSE/MAE/PCC.
"""
import argparse, importlib.util, json, os, sys
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(__file__))
from configs import CONFIG, VAR_COLS, ILI_CHANNEL, resolve_profile, split_for_profile, verify_profile_hash
from scaler_utils import ScalerBundle
from miflu_model import MIFlu
from textual_embedder import TextualInputEmbedder, build_prompt

_DLINEAR = os.path.join(os.path.dirname(__file__), "innovation", "backbones", "dlinear.py")
SEEDS = [42, 43, 44]
SEASONAL_LAG = 52
BENIGN = ("attn.bias", "attn.masked_bias")
EXPECTED = {24: 170, 36: 158, 48: 146, 60: 134}


def log(m=""): print(m, flush=True)


def load_nlinear_class():
    spec = importlib.util.spec_from_file_location("_nl", _DLINEAR)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.NLinear


def load_and_normalize(profile):
    p = resolve_profile(profile); verify_profile_hash(profile)
    df = pd.read_csv(p["data_path"]); data = df[VAR_COLS].values.astype(np.float32)
    n = len(data); t_end, v_end = split_for_profile(profile, n)
    bundle = ScalerBundle.fit_from_train(df, VAR_COLS, train_end=t_end, val_end=v_end)
    mean = bundle.mean_.reshape(1, -1).astype(np.float32)
    std = bundle.scale_.reshape(1, -1).astype(np.float32)
    return {"data_norm": (data - mean) / std, "train_end": t_end, "val_end": v_end,
            "n": n, "train_df": df.iloc[:t_end], "scaler": bundle, "df": df,
            "train_mean": mean, "train_std": std, "profile": p}


def build_windows(data_norm, T, L, train_end, val_end, containment="strict"):
    total = data_norm.shape[0]; N = data_norm.shape[1]; nw = total - T - L + 1
    X = np.zeros((nw, N, T), np.float32); Y = np.zeros((nw, N, L), np.float32)
    splits = np.zeros(nw, np.int8); ts_all = np.arange(nw) + T
    for i in range(nw):
        X[i] = data_norm[i:i+T].T; Y[i] = data_norm[i+T:i+T+L].T; ts = i + T
        if containment == "strict":
            splits[i] = 0 if ts+L <= train_end else (1 if ts >= train_end and ts+L <= val_end else (2 if ts >= val_end and ts+L <= total else -1))
        else:
            splits[i] = 0 if ts < train_end else (1 if ts <= val_end else 2)
    keep = np.where(splits >= 0)[0]
    X, Y, splits, ts_all = X[keep], Y[keep], splits[keep], ts_all[keep]
    return (X[splits == 0], Y[splits == 0], X[splits == 1], Y[splits == 1],
            X[splits == 2], Y[splits == 2], {"target_starts": ts_all, "splits": splits})


def compute_metrics(pred, target, train_mean, train_std):
    N = pred.shape[1]
    mse_all = float(np.mean((pred-target)**2)); mae_all = float(np.mean(np.abs(pred-target)))
    per_mse = [float(np.mean((pred[:, v]-target[:, v])**2)) for v in range(N)]
    per_mae = [float(np.mean(np.abs(pred[:, v]-target[:, v]))) for v in range(N)]
    gt = target[:, ILI_CHANNEL].ravel(); pr = pred[:, ILI_CHANNEL].ravel()
    mse_ili = float(np.mean((pred[:, ILI_CHANNEL]-target[:, ILI_CHANNEL])**2))
    mae_ili = float(np.mean(np.abs(pred[:, ILI_CHANNEL]-target[:, ILI_CHANNEL])))
    pcc = float(np.corrcoef(gt, pr)[0, 1]) if (np.std(gt) > 0 and np.std(pr) > 0) else float("nan")
    tm = train_mean.reshape(1, N, 1); ts = train_std.reshape(1, N, 1)
    pp = pred * ts + tm; tt = target * ts + tm
    rmse_phys = [float(np.sqrt(np.mean((pp[:, v]-tt[:, v])**2))) for v in range(N)]
    mae_phys = [float(np.mean(np.abs(pp[:, v]-tt[:, v]))) for v in range(N)]
    return {"mse_all": mse_all, "mae_all": mae_all, "mse_ili": mse_ili, "mae_ili": mae_ili,
            "pcc_ili": pcc, "per_mse": per_mse, "per_mae": per_mae,
            "rmse_phys": rmse_phys, "mae_phys": mae_phys}


def load_weights(model, ckpt, allow_missing=frozenset()):
    state = torch.load(ckpt, map_location="cpu")
    missing, unexpected = model.load_state_dict(state, strict=False)
    bad = [k for k in missing if k not in allow_missing
           and not any(k.endswith(b) for b in BENIGN)]
    if bad or unexpected:
        raise RuntimeError(f"weight mismatch {ckpt}: "
                           f"unexplained_missing={bad} unexpected={unexpected}")
    return model


# --------------------------------------------------------------------------
# Stage 6 (eight-model comparison): the six additional backbones.
# They are the SAME source files used by the training runner
# (`train_backbone_966.py`), loaded by path so the heavy registry is not
# executed. The frozen text backbone is rebuilt from the pinned local snapshot;
# its tensors are intentionally absent from the checkpoint and are declared in
# the sidecar written next to it, so reconstruction is verified rather than
# assumed.
# --------------------------------------------------------------------------
_BB_DIR = os.path.join(os.path.dirname(__file__), "innovation", "backbones")
QWEN_ID = "Qwen/Qwen2.5-1.5B"
BB_SPEC = {
    "dlinear":       ("dlinear.py",     "DLinear",         "plain", "gpt2"),
    "patchtst":      ("patchtst.py",    "PatchTST",        "plain", "gpt2"),
    "itransformer":  ("itransformer.py", "ITransformer",   "plain", "gpt2"),
    "qwen_time_llm": ("llm_inspired.py", "QwenTimeLLM",    "qwen",  "gpt2"),
    "calf_llm":      ("llm_inspired.py", "CALFInspired",   "gpt2",  "gpt2"),
    "timecma_llm":   ("llm_inspired.py", "TimeCMAInspired", "gpt2",  "gpt2"),
}


def build_stage6_backbone(name, T, N, L, device, dd):
    fn, cls, mode, _ = BB_SPEC[name]
    path = os.path.join(_BB_DIR, fn)
    spec = importlib.util.spec_from_file_location(f"_s6_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    K = getattr(mod, cls)
    if mode == "qwen":
        m = K(T=T, N=N, L=L, model_id=QWEN_ID, load_backbone=True)
        tr = dd["train_df"][VAR_COLS]
        m.set_train_statistics({"horizon": int(L), "channel_count": int(N),
                                "target_name": "ILITOTAL",
                                "train_rows": int(len(tr)),
                                "mean": {c: float(tr[c].mean()) for c in VAR_COLS},
                                "std": {c: float(tr[c].std(ddof=0)) for c in VAR_COLS},
                                "min": {c: float(tr[c].min()) for c in VAR_COLS},
                                "max": {c: float(tr[c].max()) for c in VAR_COLS}})
    elif mode == "gpt2":
        m = K(T=T, N=N, L=L, model_id="gpt2", load_backbone=True)
    else:
        m = K(T=T, N=N, L=L)
    return m.to(device)


@torch.no_grad()
def predict_backbone(model, X, batch, device):
    model.eval()
    dl = DataLoader(TensorDataset(torch.from_numpy(X)), batch_size=batch, shuffle=False)
    return np.concatenate([model(bx.to(device)).cpu().numpy() for (bx,) in dl])


@torch.no_grad()
def predict_miflu(model, X, batch, prompt_cache, tm, ts):
    model.eval()
    dl = DataLoader(TensorDataset(torch.from_numpy(X)), batch_size=batch, shuffle=False)
    outs = []
    for (bx,) in dl:
        bx = bx.to(model.device); bsz = bx.size(0)
        ht = None if prompt_cache is None else (prompt_cache.expand(bsz, -1, -1) if prompt_cache.shape[0] == 1 else prompt_cache[:bsz])
        outs.append(model(bx, htext=ht, train_mean=tm, train_std=ts)[0].cpu().numpy())
    return np.concatenate(outs)


@torch.no_grad()
def predict_nlinear(model, X, batch, device):
    # NLinear is a bare nn.Linear subclass and carries no `.device` attribute
    # (MIFlu does), so the target device is passed in explicitly.
    model.eval()
    dl = DataLoader(TensorDataset(torch.from_numpy(X)), batch_size=batch, shuffle=False)
    return np.concatenate([model(bx.to(device)).cpu().numpy() for (bx,) in dl])


def naive_pred(data_norm, target_starts, test_mask, L, name):
    N = data_norm.shape[1]; idx = np.where(test_mask)[0]; ts_all = target_starts[idx]
    pred = np.zeros((len(idx), N, L), np.float32); target = np.zeros((len(idx), N, L), np.float32)
    clamped = 0
    for j, ts in enumerate(ts_all):
        target[j] = data_norm[ts:ts+L].T
        if name == "last_value_naive":
            pred[j] = np.repeat(data_norm[ts-1][:, None], L, axis=1)
        else:
            for s in range(L):
                ref = ts + s - SEASONAL_LAG
                if ref < 0: ref = 0; clamped += 1
                pred[j, :, s] = data_norm[ref]
    return pred, target, clamped


def row(model, L, seed, m):
    r = {"model": model, "L": L, "seed": seed, "mse_all": m["mse_all"], "mae_all": m["mae_all"],
         "mse_ili": m["mse_ili"], "mae_ili": m["mae_ili"], "pcc_ili": m["pcc_ili"]}
    for v, name in enumerate(VAR_COLS):
        short = name.replace(" ", "_").replace("%", "pct").replace(".", "")
        r[f"mse_{short}"] = m["per_mse"][v]; r[f"mae_{short}"] = m["per_mae"][v]
        r[f"rmse_phys_{short}"] = m["rmse_phys"][v]; r[f"mae_phys_{short}"] = m["mae_phys"][v]
    return r


# --------------------------------------------------------------------------
# Artifact dump (Stage 5 A2 takeover, 2026-09-26).
# The metric code path above is UNCHANGED. This layer only persists, for every
# scored (model, L, seed): the standardized-space truth and prediction tensors,
# the exact Test origins (row indices + epiweek / release_date labels), the
# variable order, the train-only scaler, and the Test mask, so that
# average_MSE_4L can be recomputed independently from the artefacts alone.
# --------------------------------------------------------------------------
DUMP = {"n": 0}


def dump_predictions(dump_dir, df, model, L, seed, pred, target, ts_test,
                     train_mean, train_std, profile, containment):
    os.makedirs(dump_dir, exist_ok=True)
    np.savez_compressed(
        os.path.join(dump_dir, f"pred_{model}_L{L}_s{seed}.npz"),
        pred=pred.astype(np.float32), target=target.astype(np.float32),
        target_start_row=ts_test.astype(np.int32), L=np.int32(L), seed=np.int32(seed),
        var_cols=np.array(VAR_COLS), train_mean=train_mean.astype(np.float32),
        train_std=train_std.astype(np.float32), model=np.array(model),
        profile=np.array(profile), containment=np.array(containment),
        space=np.array("standardized_train_fit_z"))
    ew = "epiweek" if "epiweek" in df.columns else None
    rd = "release_date" if "release_date" in df.columns else None
    return [{"model": model, "L": L, "seed": seed, "origin_i": int(j),
             "origin_row_last_observed": int(ts - 1), "target_start_row": int(ts),
             "target_end_row": int(ts + L - 1), "n_leads": int(L),
             "origin_epiweek": (df[ew].iloc[ts - 1] if ew else None),
             "first_target_epiweek": (df[ew].iloc[ts] if ew else None),
             "last_target_epiweek": (df[ew].iloc[ts + L - 1] if ew else None),
             "first_target_release_date": (df[rd].iloc[ts] if rd else None),
             "last_target_release_date": (df[rd].iloc[ts + L - 1] if rd else None)}
            for j, ts in enumerate(ts_test)]


def write_scaler(dump_dir, dd):
    b = dd["scaler"]
    json.dump({"profile": dd["profile"].get("profile_id", "author_966"),
               "fit_on": "train rows [0, %d) ONLY" % dd["train_end"],
               "train_end": dd["train_end"], "val_end": dd["val_end"],
               "var_cols": VAR_COLS,
               "mean": np.asarray(b.mean_).ravel().tolist(),
               "scale": np.asarray(b.scale_).ravel().tolist()},
              open(os.path.join(dump_dir, "scaler_train_only.json"), "w"), indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="author_966", choices=("project_1025", "author_966"))
    ap.add_argument("--containment", default="strict", choices=("start", "strict"))
    ap.add_argument("--ckpt-root", default="results/stage5/ckpt/author_966")
    ap.add_argument("--export-dir", default="results/stage5/scoring")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--horizons", default=None,
                    help="Comma-separated subset of L to score (default: all).")
    ap.add_argument("--dump-dir", default=None,
                    help="Where per-(model,L,seed) prediction NPZs + test manifest + "
                         "train-only scaler are written (default: <export-dir>/predictions).")
    ap.add_argument("--stage6", action="store_true",
                    help="Also score the six Stage-6 eight-model backbones "
                         "(dlinear, patchtst, itransformer, qwen_time_llm, "
                         "calf_llm, timecma_llm) from their locked checkpoints.")
    a = ap.parse_args()
    if not a.dump_dir:
        a.dump_dir = os.path.join(a.export_dir, "predictions")
    device = ("cuda" if torch.cuda.is_available() else "cpu") if a.device == "auto" else a.device
    horizons = ([int(x) for x in a.horizons.split(",")] if a.horizons else CONFIG["L_list"])

    os.makedirs(a.export_dir, exist_ok=True)
    dd = load_and_normalize(a.profile)
    tm_t = torch.from_numpy(dd["train_mean"].astype(np.float32))
    ts_t = torch.from_numpy(dd["train_std"].astype(np.float32))

    try:
        te = TextualInputEmbedder(device="cpu"); log("text embedder OK")
    except Exception as e:
        te = None; log(f"[WARN] text embedder unavailable: {e}")

    NLinear = load_nlinear_class()
    rows = []
    manifest = []
    for L in horizons:
        T, N = CONFIG["T"], CONFIG["N"]
        Xt, Yt, Xv, Yv, Xte, Yte, sinfo = build_windows(dd["data_norm"], T, L, dd["train_end"], dd["val_end"], a.containment)
        assert len(Xte) == EXPECTED[L], f"L={L}: {len(Xte)} != {EXPECTED[L]}"
        log(f"\n=== L={L}: test={len(Xte)} train={len(Xt)} val={len(Xv)} ===")

        pc = te(build_prompt(dd["train_df"], T=T, L=L, date_range_string=dd["profile"]["date_range_string"])) if te is not None else None

        specs = [("miflu", "miflu", "best_miflu_L{L}_seed{s}.pth", True),
                 ("notext", "notext", "best_ablation_no_multi_L{L}_seed{s}.pth", False),
                 ("nlinear", "nlinear", "best_nlinear_L{L}_seed{s}.pth", None)]
        # Stage 6: the six remaining eight-model backbones, when their
        # checkpoints exist. Enabled with --stage6; absent checkpoints are
        # reported as SKIP, never silently averaged in.
        if a.stage6:
            specs += [(n, n, "best_%s_L{L}_seed{s}.pth" % n, None)
                      for n in BB_SPEC]
        for name, sub, tmpl, use_text in specs:
            for s in SEEDS:
                ckpt = os.path.join(a.ckpt_root, sub, tmpl.format(L=L, s=s))
                if not os.path.exists(ckpt):
                    log(f"  [SKIP] {name} L={L} s={s}: missing"); continue
                if name in ("miflu", "notext"):
                    if te is None: log(f"  [SKIP] {name}: no embedder"); continue
                    m = MIFlu(N=N, T=T, L=L, Lp=CONFIG["Lp"], S=CONFIG["S"], K=CONFIG["K"],
                              lora_r=CONFIG["lora_r"], device=device, use_text_ln=True,
                              use_lora=True, gated_inject=False, unfreeze_first_k=0).to(device)
                    load_weights(m, ckpt)
                    pred = predict_miflu(m, Xte, CONFIG["batch_size"], (pc.to(device) if use_text else None), tm_t, ts_t)
                elif name == "nlinear":
                    m = NLinear(T=T, N=N, L=L).to(device)
                    load_weights(m, ckpt)
                    pred = predict_nlinear(m, Xte, CONFIG["batch_size"], device)
                else:
                    side = ckpt.replace(".pth", ".frozen_keys.json")
                    allow = set()
                    if os.path.exists(side):
                        allow = set(json.load(open(side))["frozen_keys"])
                    elif BB_SPEC[name][2] != "plain":
                        log(f"  [SKIP] {name} L={L} s={s}: no frozen_keys sidecar")
                        continue
                    m = build_stage6_backbone(name, T, N, L, device, dd)
                    load_weights(m, ckpt, allow_missing=allow)
                    pred = predict_backbone(m, Xte, CONFIG["batch_size"], device)
                    del m
                    if device == "cuda":
                        torch.cuda.empty_cache()
                mm = compute_metrics(pred, Yte, dd["train_mean"], dd["train_std"])
                rows.append(row(name, L, s, mm))
                manifest.extend(dump_predictions(
                    a.dump_dir, dd["df"], name, L, s, pred, Yte,
                    sinfo["target_starts"][sinfo["splits"] == 2],
                    dd["train_mean"], dd["train_std"], a.profile, a.containment))
                log(f"  {name:8s} L={L:2d} s={s}: mse_all={mm['mse_all']:.6f} mse_ili={mm['mse_ili']:.6f} pcc={mm['pcc_ili']:.4f}")

        # Naive baselines (deterministic, once per L)
        test_mask = sinfo["splits"] == 2
        for nm in ("last_value_naive", "seasonal_naive"):
            p, tgt, cl = naive_pred(dd["data_norm"], sinfo["target_starts"], test_mask, L, nm)
            mm = compute_metrics(p, tgt, dd["train_mean"], dd["train_std"])
            rows.append(row(nm, L, 42, mm))
            manifest.extend(dump_predictions(
                a.dump_dir, dd["df"], nm, L, 42, p, tgt,
                sinfo["target_starts"][test_mask],
                dd["train_mean"], dd["train_std"], a.profile, a.containment))
            log(f"  {nm:18s} L={L:2d}: mse_all={mm['mse_all']:.6f} mse_ili={mm['mse_ili']:.6f} (clamped={cl})")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(a.export_dir, "score_matrix.csv"), index=False)

    write_scaler(a.dump_dir, dd)
    pd.DataFrame(manifest).to_csv(os.path.join(a.dump_dir, "test_manifest.csv"), index=False)
    log(f"\nartefacts: {len(manifest)} origin rows -> {a.dump_dir}/test_manifest.csv")

    # Seed-averaged summary per (model, L), then average_MSE_4L per model.
    g = df.groupby(["model", "L"]).agg(mse_all_mean=("mse_all", "mean"), mse_all_std=("mse_all", "std"),
                                        mae_all_mean=("mae_all", "mean"), mse_ili_mean=("mse_ili", "mean"),
                                        mae_ili_mean=("mae_ili", "mean"), pcc_ili_mean=("pcc_ili", "mean")).reset_index()
    g.to_csv(os.path.join(a.export_dir, "score_summary.csv"), index=False)

    avg4 = (g.groupby("model")["mse_all_mean"].mean()
             .rename("average_MSE_4L").reset_index())
    avg4.to_csv(os.path.join(a.export_dir, "average_mse_4L.csv"), index=False)

    log("\n=== average_MSE_4L (7-var standardized MSE, mean seeds then mean L) ===")
    for _, r in avg4.sort_values("average_MSE_4L").iterrows():
        log(f"  {r['model']:18s} {r['average_MSE_4L']:.6f}")
    log(f"\nDONE -> {a.export_dir}/score_matrix.csv, score_summary.csv, average_mse_4L.csv")


if __name__ == "__main__":
    main()
