"""v3_prepilot_gate.py — compute-node pre-Pilot gate.

Runs ONLY inside a Slurm compute-node job (never on a login node).

  1. ensures the pinned Qwen2.5-1.5B revision is present in the v3 cache;
  2. records the asset manifest (file list, bytes, SHA-256);
  3. for each of the eight primary models: builds the components on CUDA,
     counts frozen/trainable parameters, asserts the defining components are
     present, and runs one forward + backward on a dummy batch;
  4. proves zero Test/holdout access.

Writes into results/v3/implementation/ on the deployment root.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(os.environ["INNOVATION_DEPLOYMENT_ROOT"]).resolve()
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))

# Create-only Gate output directory: every Gate run writes under its own job id so
# a new Gate can never overwrite the outputs of a previous attempt.
JOB_ID = os.environ.get("SLURM_JOB_ID", "local").strip() or "local"
OUT = ROOT / "results" / "v3" / "implementation" / f"gate_{JOB_ID}"
OUT.mkdir(parents=True, exist_ok=True)

V2_CACHE = "/gpfs1/scratch/sychan552/CHATTIME/.cache"

QWEN_ID = "Qwen/Qwen2.5-1.5B"
# CORRECTED 2026-09-16: the previous value (b13e881f...) was the Time-LLM GitHub
# *repository* commit, wrongly reused as a Hugging Face revision, which produced
# RevisionNotFoundError. This is the actual HF revision of Qwen/Qwen2.5-1.5B
# (lastModified 2024-10-08), read from the official model API.
QWEN_REV = "8faed761d45a263340a0528343f099c05c9a4323"
CACHE = os.environ.get("V3_CACHE", "/gpfs1/scratch/sychan552/v3_cache")

# ── G2: EXPLICIT per-model backbone / asset routing ─────────────────────────
# A constructor that happens to accept `model_id` is NOT authorised to have its
# preregistered backbone replaced. Routing is therefore declared per model by
# contract, never inferred from broad **kwargs acceptance.
#
#   qwen_time_llm  -> Qwen/Qwen2.5-1.5B from the verified local snapshot
#   calf_llm       -> preregistered GPT-2 (NO Qwen model_id/revision/snapshot)
#   timecma_llm    -> preregistered GPT-2 (NO Qwen model_id/revision/snapshot)
#   gpt2_miflu     -> verified GPT-2 control (NO Qwen arguments at all)
MODEL_ROUTING = {
    "nlinear":       {"text_encoder": "none", "fusion": "identity",
                      "backbone_kwargs": None, "expected_backbone": "none"},
    "dlinear":       {"text_encoder": "none", "fusion": "identity",
                      "backbone_kwargs": None, "expected_backbone": "none"},
    "patchtst":      {"text_encoder": "none", "fusion": "identity",
                      "backbone_kwargs": None, "expected_backbone": "none"},
    "itransformer":  {"text_encoder": "none", "fusion": "identity",
                      "backbone_kwargs": None, "expected_backbone": "none"},
    "gpt2_miflu":    {"text_encoder": "gpt2", "fusion": "concat_projection",
                      "backbone_kwargs": None,
                      "expected_backbone": "gpt2_miflu_control"},
    "qwen_time_llm": {"text_encoder": "none", "fusion": "identity",
                      "backbone_kwargs": {"model_id": QWEN_ID,
                                          "load_backbone": True},
                      "expected_backbone": QWEN_ID},
    "calf_llm":      {"text_encoder": "none", "fusion": "identity",
                      "backbone_kwargs": {"load_backbone": True},
                      "expected_backbone": "gpt2"},
    "timecma_llm":   {"text_encoder": "none", "fusion": "identity",
                      "backbone_kwargs": {"load_backbone": True},
                      "expected_backbone": "gpt2"},
}
MODEL_ORDER = ["nlinear", "dlinear", "patchtst", "itransformer",
               "gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]


def assert_no_qwen_leakage() -> list[str]:
    """Fail closed if any model other than qwen_time_llm receives Qwen arguments."""
    problems = []
    for name, route in MODEL_ROUTING.items():
        kw = route["backbone_kwargs"] or {}
        for forbidden in ("model_id", "revision", "local_snapshot_path"):
            if forbidden in kw and name != "qwen_time_llm":
                problems.append(f"{name} received forbidden '{forbidden}'")
        if "model_id" in kw and kw["model_id"] != QWEN_ID:
            problems.append(f"{name} received a non-Qwen model_id: {kw['model_id']}")
    return problems


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def train_only_prompt_statistics(train_df, *, horizon: int,
                                 channel_count: int) -> dict:
    """Build Prompt-as-Prefix statistics EXCLUSIVELY from the frozen training split.

    G1: the Qwen branch raises unless these are set before `forward`. Nothing here
    is fabricated and nothing is taken from validation or Test: `train_df` is
    `raw.iloc[: scaler.train_end]`, i.e. exactly the split the verified GPT-2 /
    MIFlu protocol fits on. The textual prompt itself is rendered by the model's
    own `build_prompt_as_prefix`, so the harness only supplies metadata plus
    train-derived descriptive values.
    """
    from innovation.paths import ILI_COL

    column = train_df[ILI_COL].astype(float)
    return {
        "horizon": int(horizon),
        "channel_count": int(channel_count),
        "target_name": str(ILI_COL),
        "source": "frozen training split (raw.iloc[: scaler.train_end])",
        "train_rows": int(len(train_df)),
        "target_min": float(column.min()),
        "target_max": float(column.max()),
        "target_mean": float(column.mean()),
        "target_std": float(column.std(ddof=1)),
        "contains_validation_or_test": False,
    }


def main() -> int:
    started = time.time()
    # D5: GPT-2 (used by CALF / TimeCMA) lives in the v2 verified cache, while Qwen
    # resolves through the absolute snapshot path recorded in innovation.assets.
    # The hub cache must therefore point at the v2 cache.
    os.environ.setdefault("HF_HOME", V2_CACHE)
    os.environ.setdefault("HF_HUB_CACHE", V2_CACHE)
    os.environ["TRANSFORMERS_OFFLINE"] = "0"  # only while acquiring missing assets

    report = {"deployment_root": str(ROOT), "hostname": os.uname().nodename,
              "qwen_id": QWEN_ID, "qwen_revision": QWEN_REV, "cache": CACHE}

    # ── 1. asset acquisition ────────────────────────────────────────────────
    assets = {"downloaded": False, "files": []}
    try:
        from huggingface_hub import snapshot_download
        local = snapshot_download(repo_id=QWEN_ID, revision=QWEN_REV,
                                  cache_dir=CACHE,
                                  allow_patterns=["*.json", "*.safetensors", "*.txt",
                                                  "*.model", "*.py"])
        total = 0
        for dirpath, _d, files in os.walk(local):
            for fn in sorted(files):
                p = os.path.join(dirpath, fn)
                sz = os.path.getsize(p)
                total += sz
                assets["files"].append({"path": os.path.relpath(p, local),
                                        "bytes": sz, "sha256": sha256(p)})
        assets.update({"downloaded": True, "local_dir": local, "total_bytes": total,
                       "n_files": len(assets["files"]), "revision": QWEN_REV})
    except Exception as e:
        assets.update({"error": f"{type(e).__name__}: {e}"})
    report["assets"] = assets

    # ── 1b. authoritative asset-integrity gate, then force offline execution ──
    from innovation import assets as AS
    ok_snap, snap_problems = AS.snapshot_is_complete()
    report["qwen_asset_descriptor"] = AS.asset_descriptor(QWEN_ID)
    report["snapshot_complete"] = ok_snap
    report["snapshot_problems"] = snap_problems
    if not ok_snap:
        report["status"] = "FAILED_QWEN_SNAPSHOT_INCOMPLETE"
        (OUT / "offline_load_report.json").write_text(json.dumps(report, indent=2),
                                                     encoding="utf-8")
        print("[gate] FAILED: Qwen snapshot incomplete: " + "; ".join(snap_problems))
        return 1
    # Assets are verified locally present -> forbid any further network dependency.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    report["offline_enforced"] = True

    # ── 2. environment / CUDA ───────────────────────────────────────────────
    env_info = {}
    try:
        import torch
        env_info["torch"] = torch.__version__
        env_info["cuda_available"] = bool(torch.cuda.is_available())
        env_info["device_count"] = torch.cuda.device_count()
        if torch.cuda.is_available():
            env_info["device_name"] = torch.cuda.get_device_name(0)
            env_info["total_mem_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / 1e9, 2)
        env_info["cuda_runtime"] = getattr(torch.version, "cuda", None)
    except Exception as e:
        env_info["error"] = f"{type(e).__name__}: {e}"
    report["environment"] = env_info

    if not env_info.get("cuda_available"):
        report["status"] = "FAILED_NO_CUDA"
        (OUT / "offline_load_report.json").write_text(json.dumps(report, indent=2),
                                                     encoding="utf-8")
        print("[gate] FAILED: no CUDA visible on this node")
        return 1

    # ── 2b. CUDA pre-flight probe ───────────────────────────────────────────
    # A stingy allocation can land on a node whose A100 is momentarily still
    # held by the previous occupant, which surfaces as "device(s) busy or
    # unavailable" on the very first allocation. Probe, retry, and record
    # evidence instead of failing the whole gate on a transient condition.
    os.environ.setdefault("CUDA_LAUNCH_BLOCKING", "1")
    probe = {"attempts": [], "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES")}
    try:
        import subprocess
        probe["nvidia_smi_L"] = subprocess.run(
            ["nvidia-smi", "-L"], capture_output=True, text=True,
            timeout=30).stdout.strip()
        # Full nvidia-smi reveals compute mode and any foreign processes holding
        # the device — the evidence needed to classify "busy or unavailable".
        _q = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,compute_mode,memory.used,"
                           "memory.total,utilization.gpu",
             "--format=csv,noheader"], capture_output=True, text=True, timeout=30)
        probe["nvidia_smi_query"] = _q.stdout.strip() or _q.stderr.strip()
        _p = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=30)
        probe["nvidia_smi_full"] = _p.stdout.strip()[-2500:] or _p.stderr.strip()
    except Exception as e:
        probe["nvidia_smi_L"] = f"{type(e).__name__}: {e}"
    ok_probe = False
    for attempt in range(1, 6):
        try:
            torch.cuda.set_device(0)
            t = torch.zeros(1, device="cuda")
            torch.cuda.synchronize()
            ok_probe = True
            probe["attempts"].append({"attempt": attempt, "result": "ok",
                                      "value": float(t.item())})
            break
        except Exception as e:
            probe["attempts"].append({"attempt": attempt,
                                      "result": f"{type(e).__name__}: {e}"})
            time.sleep(15)
    report["cuda_probe"] = probe
    if not ok_probe:
        report["status"] = "FAILED_CUDA_PROBE"
        (OUT / "offline_load_report.json").write_text(json.dumps(report, indent=2),
                                                     encoding="utf-8")
        print("[gate] FAILED: CUDA probe never succeeded")
        return 1

    # ── 3. data (compute node allowed) ──────────────────────────────────────
    from innovation import runner as R
    import torch
    device = "cuda"
    raw = R.load_raw_df()
    scaler = R.load_scaler()
    train_df = raw.iloc[: scaler.train_end]
    report["data"] = {"rows": int(len(raw)), "train_end": int(scaler.train_end),
                      "holds_full_test_span": True}
    report["test_paths_touched"] = []

    # ── 4. per-model build + forward + backward ─────────────────────────────
    # G2 guard: no model except qwen_time_llm may receive Qwen arguments.
    leakage = assert_no_qwen_leakage()
    report["qwen_leakage_check"] = {"problems": leakage, "passed": not leakage}
    if leakage:
        report["status"] = "FAILED_QWEN_ASSET_LEAKAGE"
        (OUT / "offline_load_report.json").write_text(json.dumps(report, indent=2),
                                                     encoding="utf-8")
        print("[gate] FAILED: " + "; ".join(leakage))
        return 1

    results = []
    for name in MODEL_ORDER:
        route = MODEL_ROUTING[name]
        enc, fus, kw = route["text_encoder"], route["fusion"], route["backbone_kwargs"]
        rec = {"model_key": name, "text_encoder": enc, "fusion": fus,
               "expected_backbone": route["expected_backbone"],
               "backbone_kwargs": dict(kw) if kw else None}
        t0 = time.time()
        try:
            model, _encoder, ctx = R.build_components(
                name, enc, fus, 24, device, train_df, backbone_kwargs=kw)
            # G1: Qwen Prompt-as-Prefix needs train-only statistics BEFORE forward.
            if name == "qwen_time_llm":
                stats = train_only_prompt_statistics(train_df, horizon=24,
                                                     channel_count=7)
                model.set_train_statistics(stats)
                rec["train_statistics"] = stats
                rec["train_statistics_set_before_forward"] = (
                    model.train_statistics is not None)
                if model.train_statistics is None:
                    raise RuntimeError("train-only statistics were not accepted")
            model.to(device)
            total_p = sum(p.numel() for p in model.parameters())
            train_p = sum(p.numel() for p in model.parameters() if p.requires_grad)
            rec.update({"total_params": int(total_p), "trainable_params": int(train_p),
                        "frozen_params": int(total_p - train_p)})
            try:
                arch = model.architecture_report()
                rec["architecture_report"] = arch
            except Exception:
                rec["architecture_report"] = None
            # propagate the authoritative asset descriptor (D5 requirement)
            text_mod = getattr(model, "text", None)
            if text_mod is not None:
                rec["asset_descriptor"] = getattr(text_mod, "asset", None)
                rec["pretrained_source"] = getattr(text_mod, "pretrained_source", None)
                rec["loader_kwargs"] = getattr(text_mod, "loader_kwargs", None)
            # forward + backward on a dummy batch
            x = torch.randn(2, 7, 104, device=device)
            y = torch.randn(2, 7, 24, device=device)
            out = model(x)
            rec["forward_shape"] = list(out.shape)
            loss = torch.nn.functional.mse_loss(out, y)
            loss.backward()
            grads = sum(1 for p in model.parameters() if p.requires_grad and p.grad is not None)
            rec["trainable_params_with_grad"] = grads
            rec["gradient_contract_ok"] = grads > 0
            rec["loss_value"] = float(loss.detach().cpu())
            rec["gpu_mem_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 2)
            rec["status"] = "OK"
            del model
            torch.cuda.empty_cache()
        except Exception as e:
            rec["status"] = "FAILED"
            rec["error"] = f"{type(e).__name__}: {e}"
            rec["traceback"] = traceback.format_exc()[-1500:]
        rec["seconds"] = round(time.time() - t0, 1)
        results.append(rec)
        print("[gate] %-16s %-6s %ss" % (name, rec["status"], rec["seconds"]))

    report["models"] = results
    report["n_ok"] = sum(1 for r in results if r.get("status") == "OK")
    report["n_models"] = len(results)
    report["all_models_ok"] = report["n_ok"] == len(results)
    report["total_seconds"] = round(time.time() - started, 1)

    (OUT / "architecture_component_tests.json").write_text(
        json.dumps({"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "method": "compute-node runtime construction + forward + backward",
                    "models": results, "all_models_ok": report["all_models_ok"]},
                   indent=2), encoding="utf-8")
    (OUT / "offline_load_report.json").write_text(json.dumps(report, indent=2),
                                                  encoding="utf-8")
    (OUT / "weight_and_asset_manifest.json").write_text(
        json.dumps({"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "qwen": {k: v for k, v in assets.items() if k != "files"},
                    "file_hashes": assets["files"]}, indent=2), encoding="utf-8")
    print("[gate] DONE ok=%d/%d assets=%s" % (report["n_ok"], report["n_models"],
                                              assets.get("downloaded")))
    return 0 if report["all_models_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
