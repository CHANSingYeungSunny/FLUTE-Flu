#!/usr/bin/env python3
"""
probe_text_path_deterministic.py — resolve the P0 text-path contradiction.

THE CONTRADICTION BEING RESOLVED
--------------------------------
  * A0 GPU replay (jobs 587091 / 587068): `--multimodal 0` -> MSE 0.9685,
    `--multimodal 1` -> MSE 0.8581.  Text appears to matter.
  * Stage-2 CPU probe (job 587002): replacing the text embedding changed the
    output by exactly 0.000e+00 and the text gradient was exactly 0.  Text
    appears inert.

  These cannot both be true.  Note that comparing multimodal=0 vs multimodal=1
  does NOT settle it: the flag changes the sequence length, hence dropout RNG
  consumption and every downstream activation.  A training-loss difference
  between those two runs is therefore NOT evidence that text content matters.

WHAT THIS PROBE DOES INSTEAD
----------------------------
  Fixes weights, dtype, device, batch, input window and seed, calls
  `model.eval()` (so every Dropout is in eval mode), and then runs the SAME
  forward pass three times with THREE TEXT EMBEDDINGS OF IDENTICAL SHAPE:
      (1) original file content
      (2) different file content  (the same-shape embedding of another horizon)
      (3) row-permuted original   (same multiset of rows, different order)
  Identical shape => identical sequence length => identical dropout RNG
  consumption => any output difference is attributable to text CONTENT alone.

  It additionally measures, via a forward-pre-hook that splits the concatenated
  `inputs_embeds` into two leaf tensors, the gradient norm of the forecasting
  loss with respect to (a) the text embeddings and (b) the time-series patch
  embeddings.

  Finally it records, empirically, which positions the forecasting head reads.

VERDICT RULE (predeclared)
--------------------------
  * text_inert  : max |Δprediction| <= tol AND text grad norm == 0
                  -> the released implementation's text CONTENT has no effect
                     on the forecast, under these fixed conditions.
  * text_active : max |Δprediction| > tol OR text grad norm > 0
                  -> text content does reach the forecast under these
                     conditions; then compare with the other device's JSON to
                     localise where the CPU/GPU disagreement came from.
  tol is a dtype-scaled tolerance, declared below, never tuned to the result.

This script is DEVICE-AGNOSTIC ON PURPOSE.  The CPU and GPU runs must be the
same file with a different --device, never two different probes.

RUN (never on the Burgundy login node):
    sbatch slurm/probe_text_path_cpu.sbatch
    sbatch slurm/probe_text_path_gpu.sbatch
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys

import numpy as np
import torch
import torch.nn as nn


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tensor(t):
    return hashlib.sha256(np.ascontiguousarray(t.detach().cpu().numpy()).tobytes()).hexdigest()


def build_configs(args):
    """Released-code defaults from main_ILI_lora.py (commit 6ed2101), with only
    the flags the probe needs overridden."""
    cfg = argparse.Namespace(
        model_id="probe", checkpoints="./checkpoints/",
        multimodal=1,                       # text branch MUST be present to test it
        root_path="./dataset/illness/",
        data_path="national_illness.csv", data="custom", features="M", freq=0,
        target="OT", embed="timeF", percent=100,
        lora_r=4, target_modules=["c_attn"], PEFT=0,
        seq_len=104, pred_len=args.L, label_len=18,
        decay_fac=0.75, learning_rate=1e-4, batch_size=args.batch,
        num_workers=0, train_epochs=1, lradj="type1", patience=3,
        gpt_layers=6, backbone="gpt2", textmodel="gpt2", e_layers=3,
        d_model=768, n_heads=4, d_ff=768, dropout=0.2,
        enc_in=7, c_out=7, patch_size=24, kernel_size=25,
        loss_func="mse", pretrain=1, freeze=1, model="model", stride=2,
        max_len=-1, hid_dim=16, tmax=10, itr=1, cos=0,
    )
    return cfg


def dropout_report(model):
    """Every Dropout module and its training flag. torch.nn.Module.eval() flips
    this for nested modules too, but we print it rather than assume it."""
    out = []
    for name, mod in model.named_modules():
        if isinstance(mod, nn.Dropout):
            out.append({"name": name or "<root>", "p": float(mod.p),
                        "training": bool(mod.training)})
    return out


def load_text_variants(text_dir, L, alt_L):
    """Three SAME-SHAPE text embeddings. Returns (variants, meta)."""
    orig_path = os.path.join(text_dir, f"text_emb_label_0507_{L}.txt")
    alt_path = os.path.join(text_dir, f"text_emb_label_0507_{alt_L}.txt")
    if not os.path.exists(orig_path):
        raise SystemExit(f"[probe] ABORT: missing text asset {orig_path}")
    if not os.path.exists(alt_path):
        raise SystemExit(f"[probe] ABORT: missing control asset {alt_path}")
    orig = np.loadtxt(orig_path).astype(np.float32)
    alt = np.loadtxt(alt_path).astype(np.float32)
    if orig.shape != alt.shape:
        raise SystemExit(
            f"[probe] ABORT: control text has shape {alt.shape} != original "
            f"{orig.shape}; an equal-length replacement is impossible, so this "
            f"control cannot separate content from length.")
    rng = np.random.RandomState(0)
    perm = rng.permutation(orig.shape[0])
    permuted = orig[perm]
    variants = {
        "original": orig,
        "different_content_same_shape": alt,
        "row_permuted_same_multiset": permuted,
    }
    meta = {
        "original_path": orig_path,
        "control_path": alt_path,
        "original_sha256": sha256_file(orig_path),
        "control_sha256": sha256_file(alt_path),
        "shape": list(orig.shape),
        "n_tokens": int(orig.shape[0]),
        "d_model": int(orig.shape[1]),
        "control_is_equal_length": True,
    }
    return variants, meta


def _install_dead_import_shims():
    """Install ONLY the import shims that are provably unreachable at run time.

    The released `models/GPT4TS_lora.py` imports, unconditionally at module
    level, names that some environments lack:

        `transformers.models.llama.modeling_llama.LlamaModel`
            absent from transformers < 4.28.  The released code uses it only
            under `configs.backbone == 'llama2'`; this probe sets
            backbone='gpt2', so the name is never instantiated.  The shim raises
            if it ever is, so it cannot silently stand in for real work.

    Anything else (einops / embed / peft) is handled by the recorded
    compatibility directory passed via --compat.  Every shim installed here is
    listed in the JSON report under `dead_import_shims`, so a reader can see
    exactly what was stood in for and confirm none of it is on the executed path.
    """
    installed = []
    try:
        from transformers.models.llama.modeling_llama import LlamaModel  # noqa: F401
    except Exception:
        import types
        import transformers.models as _tm

        class LlamaModel:                       # pragma: no cover - dead path
            def __init__(self, *a, **k):
                raise RuntimeError(
                    "LlamaModel shim was instantiated; this probe only supports "
                    "backbone='gpt2'. Re-run with a transformers build that "
                    "provides the real LlamaModel.")

        pkg = types.ModuleType("transformers.models.llama")
        mod = types.ModuleType("transformers.models.llama.modeling_llama")
        mod.LlamaModel = LlamaModel
        pkg.modeling_llama = mod
        sys.modules["transformers.models.llama"] = pkg
        sys.modules["transformers.models.llama.modeling_llama"] = mod
        setattr(_tm, "llama", pkg)
        installed.append("transformers.models.llama.modeling_llama.LlamaModel")
    return installed


def build_input(repo, seq_len, batch, n_vars):
    """Real data: the last `seq_len` rows of the training block (rows [0,676) of
    the 966-row author file), stacked over the first `n_vars` numeric channels."""
    csv = os.path.join(repo, "dataset", "illness", "national_illness.csv")
    raw = np.genfromtxt(csv, delimiter=",", names=True, dtype=None, encoding="utf-8")
    names = list(raw.dtype.names)
    cols = [n for n in names if n.lower() != "date"][:n_vars]
    X = np.column_stack([raw[c].astype(np.float64) for c in cols])
    X = X[:676][-seq_len:]
    x = np.tile(X[None, :, :], (batch, 1, 1))
    return torch.tensor(x, dtype=torch.float32), cols


# ─────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="author repo checkout (commit 6ed2101)")
    ap.add_argument("--compat", default="", help="dir holding a0_compat.py (einops/embed shim)")
    ap.add_argument("--ckpt", default="", help="checkpoint .pth/.pt; omit for deterministic random init")
    ap.add_argument("--init-seed", type=int, default=42)
    ap.add_argument("--L", type=int, default=24, choices=[24, 36, 48, 60])
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--dtype", default="float32", choices=["float32", "float64"])
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--positive-control", action="store_true",
                    help="ALSO run the declared prefix-text repair to prove the "
                         "probe can detect text influence when text is actually "
                         "reachable. Reported separately; it is an algorithm "
                         "change and is never mixed into the released verdict.")
    args = ap.parse_args()

    device = torch.device(args.device)
    dtype = {"float32": torch.float32, "float64": torch.float64}[args.dtype]

    # Decision tolerance, declared BEFORE any number is looked at, keyed to the
    # running dtype. Never tuned to the outcome.
    tol = 1e-6 if dtype == torch.float32 else 1e-12

    if args.compat:
        sys.path.insert(0, os.path.abspath(args.compat))
    sys.path.insert(0, os.path.abspath(args.repo))

    dead_shims = _install_dead_import_shims()

    # ---- determinism -------------------------------------------------------
    torch.manual_seed(args.init_seed)
    np.random.seed(args.init_seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.init_seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
    except Exception:
        pass

    report = {
        "probe": "text_path_deterministic",
        "schema_version": 1,
        "host": platform.node(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "numpy": np.__version__,
        "device": str(device),
        "device_name": (torch.cuda.get_device_name(device) if device.type == "cuda" else "cpu"),
        "dtype": args.dtype,
        "L": args.L,
        "batch": args.batch,
        "init_seed": args.init_seed,
        "dead_import_shims": dead_shims,
        "compat_dir": os.path.abspath(args.compat) if args.compat else None,
    }

    # ---- author repo identity ---------------------------------------------
    try:
        report["author_repo"] = os.path.abspath(args.repo)
        report["author_commit"] = subprocess.check_output(
            ["git", "-C", args.repo, "rev-parse", "HEAD"], text=True).strip()
        dirty = [l[3:].strip() for l in subprocess.check_output(
            ["git", "-C", args.repo, "status", "--porcelain"], text=True).splitlines() if l.strip()]
        # __pycache__ is regenerated by merely importing the module; it is not a
        # source modification. Report both so the distinction is auditable.
        source_dirty = [d for d in dirty if "__pycache__" not in d]
        report["author_commit_dirty_files"] = dirty
        report["author_source_dirty_files"] = source_dirty
        report["author_commit_dirty"] = bool(source_dirty)
        report["author_model_sha256"] = sha256_file(
            os.path.join(args.repo, "models", "GPT4TS_lora.py"))
    except Exception as e:                                  # pragma: no cover
        report["author_commit"] = f"UNKNOWN ({e})"

    # ---- build model -------------------------------------------------------
    from models.GPT4TS_lora import GPT4TS                    # noqa: E402
    cfg = build_configs(args)
    report["config"] = {k: v for k, v in vars(cfg).items()}
    model = GPT4TS(cfg, device)
    model.to(device=device, dtype=dtype)

    if args.ckpt:
        state = torch.load(args.ckpt, map_location=device)
        state = state.get("state_dict", state.get("model", state))
        missing, unexpected = model.load_state_dict(state, strict=False)
        report["checkpoint"] = {
            "path": os.path.abspath(args.ckpt),
            "sha256": sha256_file(args.ckpt),
            "missing_keys": list(missing),
            "unexpected_keys": list(unexpected),
        }
    else:
        report["checkpoint"] = {
            "path": None,
            "note": "no --ckpt supplied; deterministic seeded random init "
                    f"(seed={args.init_seed}). A0 released-code replay has no "
                    "released checkpoint either, so this matches A0's situation.",
        }

    model.eval()
    report["model_eval_mode"] = not model.training
    report["dropout_modules"] = dropout_report(model)
    report["any_dropout_training"] = any(d["training"] for d in report["dropout_modules"])

    # trainable-parameter inventory (released code has NO LoRA: PEFT=0)
    trainable = [n for n, p in model.named_parameters() if p.requires_grad]
    total = sum(p.numel() for p in model.parameters())
    report["parameters"] = {
        "total": int(total),
        "trainable": int(sum(p.numel() for p in model.parameters() if p.requires_grad)),
        "trainable_names": trainable[:50],
        "n_trainable_tensors": len(trainable),
    }
    report["all_parameters_sha256"] = sha256_tensor(
        torch.cat([p.detach().reshape(-1).cpu() for p in model.parameters()]))

    # ---- input -------------------------------------------------------------
    x, cols = build_input(args.repo, cfg.seq_len, args.batch, n_vars=1)
    x = x.to(device=device, dtype=dtype)
    report["input"] = {"shape": list(x.shape), "columns": cols,
                       "sha256": sha256_tensor(x), "seq_len": cfg.seq_len}

    text_dir = os.path.join(args.repo, "dataset", "illness", "text_emb")
    alt_L = 60 if args.L != 60 else 24
    variants, text_meta = load_text_variants(text_dir, args.L, alt_L)
    report["text_assets"] = text_meta

    patch_num = model.patch_num
    n_tokens = text_meta["n_tokens"]
    report["sequence_layout"] = {
        "patch_num": int(patch_num),
        "text_len": int(n_tokens),
        "total_seq_len": int(patch_num + n_tokens),
        "time_series_position_range": [0, int(patch_num) - 1],
        "text_position_range": [int(patch_num), int(patch_num) + int(n_tokens) - 1],
        "text_comes_first_or_last": "LAST (text appended after the patch tokens; "
                                    "released GPT4TS_lora.py line 139)",
    }

    # ---- instrument: capture what the head reads, and split the LLM input ---
    captured = {}

    def head_pre_hook(module, inputs):
        t = inputs[0]
        captured["head_input_shape"] = list(t.shape)
        # out_layer is Linear(d_model * patch_num, pred_len); the flattened
        # feature count divided by the model width is the number of sequence
        # positions the forecasting head actually consumes.
        captured["head_positions_read"] = int(t.shape[-1] // cfg.d_model)

    h_head = model.out_layer.register_forward_pre_hook(head_pre_hook)

    def llm_pre_hook(module, hook_args, hook_kwargs):
        emb = hook_kwargs.get("inputs_embeds", None)
        if emb is None:
            return None
        captured["llm_input_shape"] = list(emb.shape)
        ts = emb[:, :patch_num, :].detach().clone()
        txt = emb[:, patch_num:, :].detach().clone()
        if torch.is_grad_enabled():          # only build leaves when a backward will follow
            ts.requires_grad_(True)
            txt.requires_grad_(True)
            captured["ts_leaf"] = ts
            captured["text_leaf"] = txt
        captured["ts_embedding_sha256"] = sha256_tensor(ts)
        hook_kwargs["inputs_embeds"] = torch.cat([ts, txt], dim=1)
        return (hook_args, hook_kwargs)

    h_llm = model.llmmodel.register_forward_pre_hook(llm_pre_hook, with_kwargs=True)

    # ---- (A) prediction difference across equal-length text contents -------
    from contextlib import contextmanager

    @contextmanager
    def text_substituted(arr):
        """The released forward reads its text embedding from a hard-coded
        RELATIVE path, so the author's tree cannot be fed alternative content
        without either writing into it (forbidden) or substituting the reader
        for the duration of the call only. This does the latter: identical
        shape, identical dtype, identical downstream code path."""
        real_loadtxt = np.loadtxt

        def fake_loadtxt(path, *a, **k):
            return arr.astype(np.float64)

        np.loadtxt = fake_loadtxt
        try:
            yield
        finally:
            np.loadtxt = real_loadtxt

    preds = {}
    for name, arr in variants.items():
        with text_substituted(arr):
            with torch.no_grad():
                out = model(x, 0)
        preds[name] = out.detach()
        report[f"prediction_sha256_{name}"] = sha256_tensor(out)

    base = preds["original"]
    diffs = {}
    for name in ("different_content_same_shape", "row_permuted_same_multiset"):
        d = (preds[name] - base).abs()
        diffs[name] = {
            "max_abs_prediction_difference": float(d.max()),
            "mean_abs_prediction_difference": float(d.mean()),
            "n_elements": int(d.numel()),
            "n_differing_elements": int((d > 0).sum()),
        }
    report["prediction_differences"] = diffs

    # ---- (A2) FLAG CONTROL: multimodal=0 vs multimodal=1 --------------------
    # The A0 GPU evidence compared these two runs and read the difference as
    # "text matters". But the flag changes the SEQUENCE LENGTH (patch_num vs
    # patch_num + n_tokens), which changes dropout RNG consumption and every
    # downstream activation. This block measures that difference at fixed
    # weights so it can be compared against the equal-length content swap.
    model.multimodal = 0
    try:
        with torch.no_grad():
            out_flag0 = model(x, 0).detach()
    finally:
        model.multimodal = 1
    dflag = (out_flag0 - preds["original"]).abs()
    report["flag_control"] = {
        "description": "multimodal=0 vs multimodal=1 at identical weights/input. "
                       "This is the comparison the A0 GPU evidence relied on. It "
                       "changes the sequence length and therefore the dropout RNG "
                       "stream, so it does NOT isolate text CONTENT.",
        "sequence_len_multimodal_0": int(patch_num),
        "sequence_len_multimodal_1": int(patch_num + n_tokens),
        "max_abs_prediction_difference": float(dflag.max()),
        "mean_abs_prediction_difference": float(dflag.mean()),
        "isolates_text_content": False,
    }
    print(f"[probe] flag control (multimodal 0 vs 1, length "
          f"{patch_num} vs {patch_num + n_tokens}): max|Δpred| = "
          f"{float(dflag.max()):.6e}  [NOT a text-content test]")

    # ---- (B) gradient of the forecasting loss wrt text vs time-series ------
    model.zero_grad(set_to_none=True)
    with text_substituted(variants["original"]):
        out = model(x, 0)
        loss = (out ** 2).mean()
    loss.backward()

    ts_leaf = captured.get("ts_leaf")
    text_leaf = captured.get("text_leaf")

    def gnorm(t):
        if t is None or t.grad is None:
            return None
        return float(t.grad.detach().norm().item())

    def gmax(t):
        if t is None or t.grad is None:
            return None
        return float(t.grad.detach().abs().max().item())

    report["gradients"] = {
        "loss": float(loss.item()),
        "text_embedding_grad_norm": gnorm(text_leaf),
        "text_embedding_grad_max_abs": gmax(text_leaf),
        "time_series_embedding_grad_norm": gnorm(ts_leaf),
        "time_series_embedding_grad_max_abs": gmax(ts_leaf),
        "note": "gradients are of the same forecasting loss wrt the two halves of "
                "the concatenated inputs_embeds actually fed to the LLM",
    }

    # ---- (C) what the head actually reads ---------------------------------
    report["head"] = {
        "head_input_shape": captured.get("head_input_shape"),
        "d_model": int(cfg.d_model),
        "head_positions_read": captured.get("head_positions_read"),
        "head_in_features": int(model.out_layer.in_features),
        "head_out_features": int(model.out_layer.out_features),
        "llm_input_shape": captured.get("llm_input_shape"),
        "time_series_embedding_sha256": captured.get("ts_embedding_sha256"),
    }

    h_head.remove()
    h_llm.remove()

    # ---- (D) POSITIVE CONTROL: the declared prefix-text repair --------------
    # Purpose: distinguish "text is inert" from "the probe is blind". The
    # released order is (patch, text); under causal attention the patch outputs
    # can never see the text. The repair prefixes the text and then reads the
    # patch positions that FOLLOW it. This is a DECLARED ALGORITHM CHANGE, not
    # the released implementation, and its result is reported in its own block.
    if args.positive_control:
        import inspect

        src = inspect.getsource(type(model).forward)
        sub_a = ("outputs = torch.cat((outputs, text_emb_tensor), axis = 1)",
                 "outputs = torch.cat((text_emb_tensor, outputs), axis = 1)")
        sub_b = ("outputs = outputs[:, :self.patch_num,:]",
                 "outputs = outputs[:, text_emb_tensor.shape[1]:"
                 "text_emb_tensor.shape[1]+self.patch_num,:]")
        applied = []
        for old, new in (sub_a, sub_b):
            if old not in src:
                raise SystemExit(
                    "[probe] ABORT: positive-control rewrite failed to apply\n"
                    f"        expected to find: {old!r}\n"
                    "        The released forward has changed; refusing to run a "
                    "control that is not exactly the released code plus two edits.")
            src = src.replace(old, new)
            applied.append({"from": old, "to": new})

        ns = {"torch": torch, "np": np, "rearrange": None}
        # reuse the real rearrange from the model's own module namespace
        ns["rearrange"] = sys.modules[type(model).__module__].rearrange
        src = "\n".join(l[4:] if l.startswith("    ") else l
                        for l in src.split("\n"))
        exec(compile(src, "<prefix-text-repair>", "exec"), ns)
        repaired_forward = ns["forward"]

        pc_preds = {}
        for name in ("original", "different_content_same_shape"):
            with text_substituted(variants[name]):
                with torch.no_grad():
                    pc_preds[name] = repaired_forward(model, x, 0).detach()
        d = (pc_preds["different_content_same_shape"] - pc_preds["original"]).abs()
        pc_max = float(d.max())
        report["positive_control"] = {
            "description": "prefix-text repair (declared algorithm change): text "
                           "concatenated BEFORE the patch tokens and the patch "
                           "positions that follow the text are read by the head",
            "edits_applied": applied,
            "max_abs_prediction_difference": pc_max,
            "mean_abs_prediction_difference": float(d.mean()),
            "detects_text_influence": bool(pc_max > tol),
            "interpretation": ("the probe CAN detect text influence when text is "
                               "reachable; therefore a zero difference in the "
                               "released path is a real zero, not a blind probe"
                               if pc_max > tol else
                               "the positive control ALSO shows no effect; the "
                               "probe may be unable to detect text influence, so "
                               "the released-path zero is inconclusive"),
            "is_released_implementation": False,
        }
        print(f"[probe] positive control (prefix-text repair, DECLARED CHANGE): "
              f"max|Δpred| = {pc_max:.6e} -> "
              f"{'DETECTS' if pc_max > tol else 'DOES NOT DETECT'} text influence")

    # ---- verdict -----------------------------------------------------------
    report["tolerance"] = tol
    report["tolerance_basis"] = ("float32 accumulate over a 6-layer GPT-2; "
                                 "declared in advance, not tuned to the result")

    max_diff = max(d["max_abs_prediction_difference"] for d in diffs.values())
    text_grad = report["gradients"]["text_embedding_grad_norm"]
    ts_grad = report["gradients"]["time_series_embedding_grad_norm"]

    pred_changed = max_diff > tol
    grad_nonzero = (text_grad is not None and text_grad > 0.0)
    head_reads_text = (report["head"]["head_positions_read"] is not None and
                       report["head"]["head_positions_read"] > patch_num)

    if not pred_changed and not grad_nonzero:
        verdict = "text_inert"
        why = ("equal-length different-content text changed the prediction by "
               f"at most {max_diff:.3e} (<= tol {tol:.1e}) and the text embedding "
               "gradient is exactly zero")
    else:
        verdict = "text_active"
        why = ("text content DOES reach the forecast under these fixed "
               f"conditions: max|Δpred|={max_diff:.3e}, "
               f"|grad_text|={text_grad}")

    report["verdict"] = verdict
    report["verdict_reason"] = why
    report["verdict_scope"] = (
        "This verdict applies to the released commit replayed under a recorded "
        "compatibility layer, with PEFT=0 and the released argparse defaults. It "
        "is not a verdict on the paper's method and not a reproduction claim.")
    report["diagnostics"] = {
        "prediction_changed": bool(pred_changed),
        "text_gradient_nonzero": bool(grad_nonzero),
        "time_series_gradient_nonzero": bool(ts_grad is not None and ts_grad > 0),
        "head_reads_any_text_position": bool(head_reads_text),
        "dropout_inactive": not report["any_dropout_training"],
        "model_in_eval_mode": report["model_eval_mode"],
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(report, fh, indent=2)

    print(f"[probe] device={report['device_name']} dtype={args.dtype} L={args.L}")
    print(f"[probe] sequence layout: patches [0,{patch_num-1}] "
          f"text [{patch_num},{patch_num+n_tokens-1}]")
    print(f"[probe] head reads {report['head']['head_positions_read']} positions")
    print(f"[probe] max|Δpred| over equal-length text swaps = {max_diff:.6e} "
          f"(tol {tol:.1e})")
    print(f"[probe] |grad_text| = {text_grad}   |grad_ts| = {ts_grad}")
    print(f"[probe] VERDICT = {verdict} :: {why}")
    print(f"[probe] wrote {args.out}")


if __name__ == "__main__":
    main()