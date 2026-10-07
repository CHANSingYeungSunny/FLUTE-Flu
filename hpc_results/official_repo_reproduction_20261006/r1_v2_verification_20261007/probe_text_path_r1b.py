#!/usr/bin/env python3
"""
probe_text_path_r1b.py — close gate C6 for the corrected R1-B pilot.

For each horizon: rebuild the corrected model, load the LOCKED checkpoint
(trainable tensors + frozen-key sidecar), then

  * re-verify the checkpoint -> prediction path against the persisted NPZ
    (re-verifies C11 / T29 on the real artefacts), and
  * run the equal-length text intervention on a real Test batch, so the
    text-path verdict is established per CHECKPOINT rather than per
    configuration.

CPU only. Zero GPU-hours.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import torch
import torch.nn as nn

T, N_VARS = 104, 7
DATA_SHA_EXPECT = "2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code-root", required=True)
    ap.add_argument("--r1b", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, a.r1b)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "r1b_train_mod", os.path.join(a.r1b, "r1b_train.py"))
    tr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tr)
    from r1b_model import R1BCorrectedMIFlu, run_text_influence_check

    data_path = os.path.join(a.code_root, "dataset", "illness",
                             "national_illness.csv")
    got = tr.sha256_file(data_path)
    assert got == DATA_SHA_EXPECT, f"dataset sha mismatch {got}"
    data, tr_end, va_end, cols = tr.load_data(a.code_root, data_path)

    report = {}
    for L in (24, 36, 48, 60):
        tag = f"r1b__L{L}__rep0"
        d = os.path.join(a.run_dir, "preds", tag)
        ckpt = os.path.join(d, f"ckpt_{tag}.pth")
        side = os.path.join(d, f"ckpt_{tag}.frozen_keys.json")
        npz = os.path.join(d, f"pred_{tag}.npz")
        if not (os.path.exists(ckpt) and os.path.exists(npz)):
            report[L] = {"error": "artefact missing"}
            continue

        text, text_path = tr.build_prompt_embeddings(a.code_root, L, data_path)
        import argparse as _ap
        configs = _ap.Namespace(
            model_id="r1b", checkpoints=d, multimodal=1,
            root_path=os.path.dirname(data_path),
            data_path=os.path.basename(data_path), data="custom", features="M",
            freq=0, target="OT", embed="timeF", percent=100, lora_r=4,
            target_modules=["c_attn"], PEFT=1, seq_len=T, pred_len=L,
            label_len=18, decay_fac=0.75, learning_rate=5e-4, batch_size=16,
            num_workers=0, train_epochs=20, lradj="type1", patience=3,
            gpt_layers=6, backbone="gpt2", textmodel="gpt2", e_layers=3,
            d_model=768, n_heads=4, d_ff=768, dropout=0.2, enc_in=N_VARS,
            c_out=N_VARS, patch_size=24, kernel_size=25, loss_func="mse",
            pretrain=1, freeze=1, model="model", stride=2, max_len=-1,
            hid_dim=16, tmax=10, itr=1, cos=0)

        dev = torch.device("cpu")
        model = R1BCorrectedMIFlu(configs, dev, text_embeddings=text).to(dev)
        keep = torch.load(ckpt, map_location="cpu")
        sidecar = json.load(open(side))
        missing = model.load_state_dict(keep, strict=False)
        model.eval()

        # real Test batch
        ds_te = tr.R1BDataset(data, T, L, va_end, len(data))
        xb, yb, ob = ds_te[0]
        xb = xb.unsqueeze(0)

        with torch.no_grad():
            pred = model(xb).numpy()
        te = torch.as_tensor(np.asarray(text), dtype=torch.float32)
        probe = te
        ctrl = torch.zeros_like(te)
        infl = run_text_influence_check(model, xb, probe, ctrl)

        # cross-check the first-origin prediction against the persisted NPZ
        z = np.load(npz, allow_pickle=False)
        pred_npz, targ_npz, orig_npz = z["pred"], z["target"], z["target_start_row"]
        match = None
        for i, o in enumerate(orig_npz):
            if int(o) == int(ob):
                match = float(np.abs(pred[0] - pred_npz[i]).max())
                break

        report[L] = {
            "text_asset": text_path,
            "n_stored_tensors_loaded": len(keep),
            "n_frozen_tensors_sidecar": sidecar["n_frozen_tensors"],
            "load_missing_keys": list(getattr(missing, "missing_keys", [])),
            "load_unexpected_keys": list(getattr(missing, "unexpected_keys", [])),
            "text_path_verdict": infl["verdict"],
            "max_abs_prediction_difference": infl["max_abs_prediction_difference"],
            "text_embedding_grad_norm": infl["text_embedding_grad_norm"],
            "total_grad_norm": infl["total_grad_norm"],
            "checkpoint_vs_persisted_npz_max_abs_diff": match,
            "frozen_keys_restored": not any(
                "missing" in k for k in getattr(missing, "missing_keys", [])),
        }
        print(f"[probe] L={L} text={infl['verdict']} "
              f"max|d|={infl['max_abs_prediction_difference']:.4e} "
              f"grad={infl['text_embedding_grad_norm']:.4e} "
              f"ckpt-vs-npz={match}")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(report, open(a.out, "w"), indent=2, default=str)
    print(f"[probe] wrote {a.out}")
    allactive = all(v.get("text_path_verdict") == "text_active"
                    for v in report.values() if "error" not in v)
    print(f"[probe] ALL_TEXT_ACTIVE = {allactive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())