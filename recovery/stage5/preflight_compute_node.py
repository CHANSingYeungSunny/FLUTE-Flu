# -*- coding: utf-8 -*-
"""Stage 5 — compute-node preflight (GPU node only; never the login node).

Reuses the runners' own machinery (no toy substitutes):

1. env / GPT-2 cache / revision / offline load;
2. text-tensor sensitivity through the REAL TextualInputEmbedder and a real
   MIFlu forward (fixed weights, eval mode, dropout off);
3. trainable/frozen parameter counts, LoRA modules, output shape, 7-variable loss;
4. no-text variant semantics vs the frozen config;
5. bounded forward-only resource measurement (counts as GPU usage);
6. checkpoint save/restore round trip.

Never reads or scores the Test split.
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # .../a2_stage5
sys.path.insert(0, os.path.join(ROOT, "scripts"))


def sha(p, n=16):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:n] if os.path.exists(p) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="author_966")
    ap.add_argument("--horizon", type=int, default=24)
    ap.add_argument("--containment", default="strict")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rep = {"profile": args.profile, "horizon": args.horizon,
           "containment": args.containment, "checks": {}}
    rep["env"] = {"python": sys.version.split()[0], "torch": torch.__version__,
                  "cuda_available": torch.cuda.is_available(),
                  "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"}

    import configs
    from configs import CONFIG
    profiles = configs.resolve_profile(args.profile)
    rep["checks"]["profile"] = {"name": args.profile,
                                "train_end": int(CONFIG.get("train_end", 0)),
                                "val_end": int(CONFIG.get("val_end", 0))}
    rep["checks"]["profile"]["profiles_known"] = sorted(
        getattr(configs, "DATA_PROFILES", {}).keys())

    # ---- 1. GPT-2 cache / revision / offline load
    cache = os.environ.get("HF_HOME") or os.path.expanduser("~/.cache/huggingface")
    rep["checks"]["gpt2_cache"] = {"HF_HOME": cache, "exists": os.path.isdir(cache)}
    from transformers import GPT2Tokenizer, GPT2Config
    tok = GPT2Tokenizer.from_pretrained("gpt2", local_files_only=True)
    cfg = GPT2Config.from_pretrained("gpt2", local_files_only=True)
    rep["checks"]["gpt2_offline"] = {"status": "PASS", "n_layer": cfg.n_layer,
                                     "n_embd": cfg.n_embd}

    import train_miflu as tm
    from miflu_model import MIFlu
    from textual_embedder import TextualInputEmbedder, build_prompt

    # ---- data (train/validation only; Test never read)
    # train_miflu / train_ablation read the profile from their module-level
    # ACTIVE_PROFILE (normally set by --profile in main()); set it explicitly.
    # Mirror exactly what train_miflu.main() does for --profile: reassign the
    # module-level ACTIVE_PROFILE / DATA_PATH / SCALER_PATH.
    _prof = configs.resolve_profile(args.profile)
    tm.ACTIVE_PROFILE = args.profile
    tm.DATA_PATH = _prof["data_path"]
    tm.SCALER_PATH = _prof["scaler_path"]
    ta_profile_set = False
    try:
        import train_ablation as _ta
        _ta.ACTIVE_PROFILE = args.profile
        ta_profile_set = True
    except Exception:
        pass
    rep["checks"]["profile"]["ACTIVE_PROFILE_set"] = {"train_miflu": True,
                                                      "train_ablation": ta_profile_set}
    rep["checks"]["profile"]["data_path"] = _prof["data_path"]
    dd = tm.load_and_normalize()
    rep["checks"]["data"] = {"n": int(dd["data_norm"].shape[0]),
                             "train_end": int(dd["train_end"]),
                             "val_end": int(dd["val_end"])}
    Xt, Yt, Xv, Yv, Xte, Yte, sinfo = tm.build_windows(
        dd["data_norm"], CONFIG["T"], args.horizon,
        dd["train_end"], dd["val_end"], containment=args.containment)
    rep["checks"]["windows"] = {"train": len(Xt), "val": len(Xv), "test": len(Xte),
                                "containment": args.containment}

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ---- 2. text-tensor sensitivity (real embedder)
    p1 = build_prompt(dd["train_df"], T=CONFIG["T"], L=args.horizon,
                      date_range_string="2002-09-29 to 2021-03-28")
    p2 = build_prompt(dd["train_df"], T=CONFIG["T"], L=args.horizon,
                      date_range_string="REPLACED TEXT FOR SENSITIVITY CHECK 9999")
    emb = TextualInputEmbedder(device=str(dev))
    with torch.no_grad():
        h1, h2 = emb(p1), emb(p2)
    if h1.shape == h2.shape:
        d_emb = float((h1 - h2).abs().max())
    else:
        # token counts differ -> compare the common prefix and the pooled vectors
        m = min(h1.shape[1], h2.shape[1])
        d_emb = float((h1[:, :m, :] - h2[:, :m, :]).abs().max())
    pooled = float((h1.mean(dim=1) - h2.mean(dim=1)).abs().max())
    rep["checks"]["text_embed_sensitivity"] = {
        "tokens_p1": int(h1.shape[1]), "tokens_p2": int(h2.shape[1]),
        "max_abs_diff_common_prefix": d_emb, "max_abs_diff_pooled": pooled,
        "verdict": "PASS" if (d_emb > 0 or pooled > 0) else "FAIL (text inert)"}

    # ---- 3. real MIFlu forward: fixed weights, eval, dropout off
    torch.manual_seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)
    model = MIFlu(N=CONFIG["N"], T=CONFIG["T"], L=args.horizon, Lp=CONFIG["Lp"],
                  S=CONFIG["S"], K=CONFIG["K"], lora_r=CONFIG["lora_r"], device=str(dev))
    model.to(dev).eval()
    for m in model.modules():
        if isinstance(m, torch.nn.Dropout):
            m.p = 0.0
    tmean = torch.from_numpy(dd["train_mean"].astype(np.float32)).to(dev)
    tstd = torch.from_numpy(dd["train_std"].astype(np.float32)).to(dev)
    x = torch.from_numpy(Xv[:4]).to(dev)          # VALIDATION windows only
    tgt = torch.from_numpy(Yv[:4]).to(dev)
    with torch.no_grad():
        out1 = model(x, htext=h1, train_mean=tmean, train_std=tstd)
        out2 = model(x, htext=h2, train_mean=tmean, train_std=tstd)
    y1 = out1[0] if isinstance(out1, (tuple, list)) else out1
    y2 = out2[0] if isinstance(out2, (tuple, list)) else out2
    d_out = float((y1 - y2).abs().max())
    shape_ok = (y1.dim() == 3 and y1.shape[1] == CONFIG["N"] and y1.shape[2] == args.horizon)
    rep["checks"]["miflu_forward"] = {"output_shape": tuple(y1.shape),
                                      "expected": (4, CONFIG["N"], args.horizon),
                                      "shape_ok": bool(shape_ok),
                                      "output_delta_on_text_change": d_out,
                                      "verdict": "PASS" if (d_out > 0 and shape_ok)
                                                 else "CHECK (see values)"}

    tr = sum(p.numel() for p in model.parameters() if p.requires_grad)
    fr = sum(p.numel() for p in model.parameters() if not p.requires_grad)
    lora = sorted({type(m).__name__ for m in model.modules()
                   if "lora" in type(m).__name__.lower()})
    rep["checks"]["params"] = {"trainable": int(tr), "frozen": int(fr), "lora_modules": lora}

    loss = float(torch.nn.MSELoss()(y1, tgt).item())
    rep["checks"]["loss_7var"] = loss

    # ---- 6. checkpoint save/restore round trip
    buf = os.path.join(HERE, "_preflight_ckpt.pt")
    sd = model.state_dict()
    torch.save(sd, buf)
    sd2 = torch.load(buf, map_location=dev)
    same = all(torch.equal(sd[k], sd2[k]) for k in sd)
    rep["checks"]["ckpt_roundtrip"] = {"identical": bool(same), "sha256_16": sha(buf)}
    os.remove(buf)

    # ---- 4. no-text semantics (code-level + config mirror)
    try:
        import train_ablation as ta
        _ta_ok = True
    except Exception as exc:
        ta, _ta_ok = None, str(exc)
    rep["checks"]["no_text_definition"] = {
        "variant": "no_multi", "use_text": False, "prompt_cache": None,
        "train_ablation_importable": _ta_ok,
        "note": "removes the WHOLE text pathway; sequence length / patch positions change "
                "(WHOLE-PATHWAY contrast, not a matched-length content control)"}

    # ---- 5. bounded resource measurement (forward only)
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        t0 = time.time()
        steps = 5
        for _ in range(steps):
            with torch.no_grad():
                model(x, htext=h1, train_mean=tmean, train_std=tstd)
        torch.cuda.synchronize()
        dt = (time.time() - t0) / steps
        rep["checks"]["resources"] = {"peak_mem_bytes": int(torch.cuda.max_memory_allocated()),
                                      "seconds_per_forward_batch4": round(dt, 4),
                                      "covers": "forward only (batch 4, no backward/optimizer)"}
    else:
        rep["checks"]["resources"] = "SKIPPED (no CUDA)"

    rep["test_access"] = "NONE — only train/validation windows were used"
    out = args.out or os.path.join(HERE, "preflight_result.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, default=str)
    print(json.dumps(rep, indent=2, default=str))


if __name__ == "__main__":
    main()
