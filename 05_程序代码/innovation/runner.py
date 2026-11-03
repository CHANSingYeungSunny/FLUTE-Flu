"""
runner.py — the unified innovation runner.
==========================================

One invocation == one run, writing the FULL mandatory artifact tree for the
given (model x text_encoder x fusion x horizon x seed). Hard rules enforced:

  * create-only run directory (never overwrite);
  * validation artifacts ONLY (revision 1) — `test_predictions.csv` /
    `test_metrics.json` are NEVER written here; test artifacts live exclusively
    under `test_evaluations/{test_eval_id}/` and only after the winner is frozen;
  * checkpoint manifest with SHA-256 + restore test + full config;
  * registry append-only; failures/interruptions still recorded;
  * plan SHA-256 recomputed at runtime (blocked + reported on mismatch).

USAGE
-----
    python scripts/innovation/runner.py --model dlinear --text-encoder none \
        --fusion identity --horizon 24 --seed 42 --epochs 1 --limit-train 32
"""

from __future__ import annotations

import argparse
import os
import platform
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402

from innovation import figures as FIG  # noqa: E402
from innovation import metrics as MET  # noqa: E402
from innovation import run_artifacts as ART  # noqa: E402
from innovation import screening_artifacts as SCR  # noqa: E402
from innovation.data_pipeline import (CONFIG, N, T, build_windows,  # noqa: E402
                                      load_raw_df, load_scaler, normalize,
                                      make_split_manifest, to_array)
from innovation.paths import (DATASET_NAME, ELIGIBLE_STAGES, HORIZONS,  # noqa: E402
                              ILI_CHANNEL, PROTOCOL_VERSION, SCALER_JSON,
                              STAGE_VALUES, TEST_ACCESS_ALLOWED,
                              current_snapshot_sha256, display_name_for,
                              ensure_innovation_dirs, governance_fields,
                              plan_sha256_status)
from innovation.run_id import (git_sha, make_run_id, make_test_eval_id,  # noqa: E402
                               parse_run_id)
from innovation.trainer import predict_frame, train_model  # noqa: E402

DEFAULT_D_MODEL = 64


# ── environment / config snapshots ──────────────────────────────────────────
def environment_report(device: str) -> str:
    lines = [f"platform   : {platform.platform()}",
             f"machine    : {platform.machine()}",
             f"python     : {platform.python_version()}",
             f"torch      : {torch.__version__}",
             f"cuda_avail : {torch.cuda.is_available()}",
             f"device     : {device}"]
    for mod in ("transformers", "numpy", "pandas", "scipy", "sklearn",
                "statsmodels"):
        try:
            m = __import__(mod)
            lines.append(f"{mod:<11}: {getattr(m, '__version__', 'unknown')}")
        except Exception as e:  # pragma: no cover
            lines.append(f"{mod:<11}: UNAVAILABLE ({e.__class__.__name__})")
    return "\n".join(lines) + "\n"


def _git_status() -> str:
    import subprocess

    from innovation.paths import PROJECT_ROOT

    sha = git_sha(short=False)
    try:
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL, encoding="utf-8",
            errors="replace").strip()
    except Exception:
        dirty = ""
    return f"commit: {sha}\ndirty_files: {len(dirty.splitlines())}\n"


def _eligibility(stage: str) -> dict:
    """Eligibility record written into EVERY run_status.json (revision 5).

    Smoke / pilot / adhoc runs are infrastructure evidence only and can never
    enter champion selection; only `screening` and `full` stages can.

    `test_access_allowed` (D1): this record is written for VALIDATION-phase runs
    only. Such a run never reads the test split — test artifacts are produced
    exclusively later, under `test_evaluations/{test_eval_id}/`, once a winner
    has been frozen — so the field is `False` for every stage, including the
    otherwise-eligible `screening` / `full` stages.
    """
    stage = str(stage or "adhoc")
    return {
        "experiment_stage": stage,
        "smoke_only": stage == "smoke",
        "selection_eligible": stage in ELIGIBLE_STAGES,
        "protocol_version": PROTOCOL_VERSION,
        "test_access_allowed": TEST_ACCESS_ALLOWED,
        # v3.4 (screening §6/§8): a validation-phase run can never touch the
        # holdout definition either, and both access counters are machine-
        # checkable on every run_status.json for every stage.
        "holdout_access_allowed": False,
        **SCR.access_counters(),
    }


# ── component assembly ──────────────────────────────────────────────────────
def build_components(model_name: str, text_encoder_name: str, fusion_name: str,
                     horizon: int, device: str, train_df, d_model: int = DEFAULT_D_MODEL,
                     backbone_kwargs: dict | None = None):
    """Fit the text encoder on TRAIN ONLY, then build backbone + ctx provider."""
    from innovation.backbones import gpt2_cache_available, make_backbone
    from innovation.encoders import make_encoder
    from innovation.fusion import make_fusion

    if model_name == "gpt2_miflu":
        if text_encoder_name != "gpt2":
            raise ValueError("gpt2_miflu requires --text-encoder gpt2 (it needs "
                             "a 768-d GPT-2 context); got "
                             f"{text_encoder_name!r}")
        if not gpt2_cache_available():
            raise RuntimeError("UNAVAILABLE_LOCAL_DEPENDENCY: local gpt2 cache "
                               "not found (must not download)")

    encoder = make_encoder(text_encoder_name)
    if not encoder.is_available():
        raise RuntimeError(f"UNAVAILABLE_LOCAL_DEPENDENCY: encoder "
                           f"{text_encoder_name!r} not available locally")
    encoder.fit_on_train_only(train_df, horizon=horizon, seed=42)
    text_dim = encoder.context_dim()

    bk = dict(backbone_kwargs or {})
    if model_name == "fusion_forecaster":
        from innovation.backbones.fusion_forecaster import TextFusionForecaster
        fusion = make_fusion(fusion_name, d_model=int(bk.get("d_model", d_model)))
        model = TextFusionForecaster(T=T, N=N, L=horizon, fusion=fusion,
                                     text_dim=text_dim,
                                     d_model=int(bk.get("d_model", d_model)))
    elif model_name == "gpt2_miflu":
        model = make_backbone(model_name, T=T, N=N, L=horizon,
                              device=device, **bk)
    else:
        model = make_backbone(model_name, T=T, N=N, L=horizon, **bk)

    def ctx_fn(bsz: int):
        return encoder.encode(bsz, device=device, horizon=horizon)

    return model, encoder, ctx_fn


# ── one run ─────────────────────────────────────────────────────────────────
def run_one(spec: dict) -> dict:
    ensure_innovation_dirs()
    device = spec.get("device") or ("cuda" if torch.cuda.is_available() else "cpu")
    device_name = (torch.cuda.get_device_name(0)
                   if str(device).startswith("cuda") and torch.cuda.is_available()
                   else "cpu")
    elig = _eligibility(spec.get("experiment_stage", "adhoc"))
    horizon = int(spec["horizon"])
    seed = int(spec["seed"])

    run_id = spec.get("run_id") or make_run_id(
        DATASET_NAME, spec["model"], spec["text_encoder"], spec["fusion"],
        horizon, seed)
    run_dir = ART.create_run_dir(run_id)

    plan = plan_sha256_status()
    ART.write_json(os.path.join(run_dir, "plan_sha256.json"), plan)

    # Governance block (innov-v2.3): known before the model exists, so a FAILED
    # run still records the full metadata chain. display_name / fidelity are
    # filled in once the backbone has reported its architecture.
    stage = str(spec.get("experiment_stage", "adhoc"))
    snap_sha = current_snapshot_sha256()
    gov = governance_fields(
        stage=stage, purpose=spec.get("purpose"), model_key=spec["model"],
        paper_result_eligible=("screening_only" if stage == "screening" else None),
        source_snapshot_sha256=snap_sha,
        authoritative_plan_sha256=plan["sha256_runtime"])
    with open(os.path.join(run_dir, "environment.txt"), "w", encoding="utf-8") as f:
        f.write(environment_report(device))
    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(_git_status())

    try:
        if not plan["matches"]:
            msg = (f"authoritative plan SHA-256 changed: expected "
                   f"{plan['sha256_expected']} got {plan['sha256_runtime']}")
            ART.write_run_status(run_dir, status="blocked_plan_sha_mismatch",
                                 run_id=run_id, error=msg, **gov)
            ART.append_registry({"run_id": run_id, "status": "blocked",
                                 "run_dir": run_dir, "notes": msg,
                                 "git_sha": git_sha(),
                                 "plan_sha256": plan["sha256_runtime"]})
            raise RuntimeError(msg)

        ART.write_run_status(run_dir, status="running", run_id=run_id,
                             phase="validation", **gov)

        raw = load_raw_df()
        scaler = load_scaler()
        data = normalize(to_array(raw), scaler)
        windows = build_windows(data, horizon)

        lim_tr = spec.get("limit_train")
        lim_va = spec.get("limit_val")
        if lim_tr:
            for k in ("X_train", "Y_train", "idx_train"):
                windows[k] = windows[k][:int(lim_tr)]
        if lim_va:
            for k in ("X_val", "Y_val", "idx_val"):
                windows[k] = windows[k][:int(lim_va)]

        ART.write_json(os.path.join(run_dir, "split_manifest.json"),
                       make_split_manifest(scaler, horizon))
        scaler_meta = scaler.to_dict()
        scaler_meta["scaler_file"] = SCALER_JSON
        scaler_meta["sha256_file"] = ART.sha256_file(SCALER_JSON)
        ART.write_json(os.path.join(run_dir, "scaler_metadata.json"), scaler_meta)

        model, encoder, ctx_fn = build_components(
            spec["model"], spec["text_encoder"], spec["fusion"], horizon,
            device, raw.iloc[:scaler.train_end],
            d_model=int(spec.get("d_model", DEFAULT_D_MODEL)),
            backbone_kwargs=spec.get("backbone_kwargs"))
        if hasattr(model, "set_train_statistics"):
            model.set_train_statistics({"target_name": "ILITOTAL",
                                        "horizon": horizon,
                                        "channel_count": int(N)})
        model = model.to(device)

        cfg = dict(CONFIG)
        cfg.update({"model": spec["model"], "text_encoder": spec["text_encoder"],
                    "fusion": spec["fusion"], "horizon": horizon, "seed": seed,
                    "T": T, "N": N, "L": horizon,
                    "batch_size": int(spec.get("batch_size", 16)),
                    "learning_rate": float(spec.get("lr", 5e-4)),
                    "epochs": int(spec.get("epochs", 20)),
                    "patience": int(spec.get("patience", 7)),
                    "device": device})
        resolved = {
            "run_id": run_id, "dataset": DATASET_NAME,
            "protocol_version": PROTOCOL_VERSION,
            "experiment_stage": elig["experiment_stage"],
            "selection_eligible": elig["selection_eligible"],
            "device_requested": spec.get("device") or "auto",
            "device_actual": str(device),
            "device_name": device_name,
            "plan_sha256": plan["sha256_runtime"],
            "plan_sha256_expected": plan["sha256_expected"],
            "git_sha": git_sha(), "config": cfg,
            "components": {
                "backbone": spec["model"], "text_encoder": spec["text_encoder"],
                "fusion": spec["fusion"],
                "encoder_available": bool(encoder.is_available()),
                "encoder_context_dim": encoder.context_dim(),
            },
            "limits": {"train": lim_tr, "val": lim_va},
            "trainable_parameters": int(model.trainable_parameters()),
            "total_parameters": int(model.total_parameters()),
            "architecture_report": (model.architecture_report()
                                    if hasattr(model, "architecture_report") else {}),
        }
        # governance block, now complete with display_name + fidelity
        arch = resolved["architecture_report"] or {}
        gov = governance_fields(
            stage=stage, purpose=spec.get("purpose"), model_key=spec["model"],
            paper_result_eligible=("screening_only" if stage == "screening" else None),
            display_name=display_name_for(spec["model"], arch),
            architecture_fidelity=arch.get("fidelity"),
            source_snapshot_sha256=snap_sha,
            authoritative_plan_sha256=plan["sha256_runtime"])
        resolved.update(gov)
        ART.write_min_yaml(os.path.join(run_dir, "config_resolved.yaml"), resolved)

        print(f"[runner] {run_id}")
        print(f"[runner] trainable params = {resolved['trainable_parameters']:,} "
              f"| device={device}")

        _t0 = time.time()
        history, stopper, ckpt_path = train_model(
            model, windows, cfg, run_dir, device=device,
            patience=cfg["patience"], epochs=cfg["epochs"],
            batch_size=cfg["batch_size"], lr=cfg["learning_rate"], ctx_fn=ctx_fn,
            max_seconds=spec.get("max_seconds"))
        train_seconds = time.time() - _t0
        history.to_csv(os.path.join(run_dir, "logs", "train_history.csv"),
                       index=False)

        best_val = (float(stopper.best_val_loss)
                    if np.isfinite(stopper.best_val_loss) else float("nan"))
        best_epoch = int(stopper.best_epoch or 0)
        man = ART.write_checkpoint_manifest(
            run_dir, ckpt_path=ckpt_path, best_epoch=best_epoch,
            best_val_mse=best_val, config=resolved,
            extra=dict({"stopper": stopper.state_dict()}, **gov))
        restore = ART.restore_test(
            lambda: _rebuild(spec, horizon, device), ckpt_path,
            expected_state_dict_sha256=man["state_dict_sha256"])
        man["restore_test"] = restore
        ART.write_json(os.path.join(run_dir, "checkpoints",
                                    "checkpoint_manifest.json"), man)

        # ── validation predictions (NEVER test) ──
        _t_inf = time.time()
        val_df = predict_frame(model, windows["X_val"], windows["Y_val"],
                               windows["idx_val"], T, horizon, scaler, "val",
                               device, batch_size=cfg["batch_size"], ctx_fn=ctx_fn)
        inference_seconds = time.time() - _t_inf
        # v3.4 (screening metric contract §7): every prediction row carries the
        # FULL key set so each fixed step is independently reconstructible.
        val_df = SCR.add_prediction_keys(val_df, model_key=spec["model"],
                                         horizon=horizon, seed=seed)
        val_df.to_csv(os.path.join(run_dir, "predictions",
                                   "validation_predictions.csv"), index=False)

        val_metrics = MET.evaluate_predictions(val_df, "val", scaler=scaler)
        val_metrics["best_epoch"] = best_epoch
        val_metrics["best_val_mse_from_stopper"] = best_val
        ART.write_json(os.path.join(run_dir, "metrics",
                                   "validation_metrics.json"), val_metrics)

        # v3.4 (screening §7 family B): ILITOTAL per fixed step 0/1/2/3.
        fixed_metrics = SCR.fixed_step_metrics(val_df)
        ART.write_json(os.path.join(run_dir, "metrics",
                                    "fixed_step_metrics.json"), fixed_metrics)

        # v3.4 (screening §8): train-only prompt-statistics provenance.
        ART.write_json(os.path.join(run_dir, "prompt_statistics_metadata.json"),
                       SCR.prompt_statistics_metadata(
                           encoder=encoder, horizon=horizon, seed=seed,
                           channel_count=int(N)))

        try:
            series = MET.aggregate_fixed_step(
                MET.split_frame(val_df, "val"), step=0)
            by_season, _ = MET.seasonal_peak_metrics(series)
        except Exception as e:
            series = pd.DataFrame()
            by_season = pd.DataFrame()
            ART.write_json(os.path.join(run_dir, "metrics", "_peak_note.json"),
                           {"note": f"peak metrics unavailable: {e}"})
        by_season.to_csv(os.path.join(run_dir, "metrics",
                                      "peak_metrics_by_season.csv"), index=False)

        # ── figures ──
        try:
            FIG.loss_curve(history, os.path.join(run_dir, "figures",
                                                 "loss_curve.png"))
            if len(series):
                FIG.forecast_continuous(series, os.path.join(
                    run_dir, "figures", "forecast_continuous.png"),
                    split_label="validation")
                FIG.residual_diagnostics(series, os.path.join(
                    run_dir, "figures", "residual_diagnostics.png"))
            FIG.peak_timing_intensity(by_season, os.path.join(
                run_dir, "figures", "peak_timing_intensity.png"))
        except Exception as e:
            print(f"[runner][WARN] figure generation issue: {e}")

        # v3.4 (screening §8): parameters, GPU-hours, peak memory, latency,
        # storage — written as its own artifact.
        usage = SCR.resource_usage(
            run_dir=run_dir, ckpt_path=ckpt_path, train_seconds=train_seconds,
            inference_seconds=inference_seconds,
            trainable_parameters=int(resolved["trainable_parameters"]),
            total_parameters=int(resolved["total_parameters"]),
            n_train_windows=int(len(windows["X_train"])),
            n_val_windows=int(len(windows["X_val"])),
            batch_size=int(cfg["batch_size"]), epochs=int(cfg["epochs"]),
            device=str(device), device_name=device_name,
            lr=float(cfg["learning_rate"]), patience=int(cfg["patience"]),
            horizon=horizon, seed=seed, model_key=spec["model"])
        ART.write_json(os.path.join(run_dir, "resource_usage.json"), usage)

        status = {
            "run_id": run_id, "status": "ok", "phase": "validation",
            "best_epoch": best_epoch, "best_val_mse": best_val,
            "n_val_windows": int(len(windows["X_val"])),
            "n_train_windows": int(len(windows["X_train"])),
            "checkpoint_sha256": man["sha256_file"],
            "state_dict_sha256": man["state_dict_sha256"],
            "restore_ok": bool(restore["ok"]),
            "val_mse_all_z": val_metrics.get("mse_all_z"),
            "val_mse_ili_phys": val_metrics.get("mse_ili_phys"),
            "peak_hit_ratio": (val_metrics.get("peak", {}) or {}).get("peak_hit_ratio"),
            "val_mae_all_z": val_metrics.get("mae_all_z"),
            "trainable_parameters": resolved["trainable_parameters"],
            "total_parameters": resolved["total_parameters"],
            "train_seconds": round(float(train_seconds), 3),
            "inference_seconds": round(float(inference_seconds), 6),
            "peak_gpu_memory_bytes": usage["peak_gpu_memory_bytes"],
            "truncated_by_time_limit": bool(history.attrs.get("truncated", False)),
            "test_artifacts_written": False,
            "device_requested": spec.get("device") or "auto",
            "device_actual": str(device),
            "device_name": device_name,
            # v3.4 provenance / isolation fields (screening §6, §8)
            "holdout_access_allowed": False,
            **SCR.access_counters(),
            "canonical_data_sha256": SCR.CANONICAL_DATA_SHA256,
            "fixed_step_steps": list(SCR.FIXED_STEPS),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "slurm_node": (os.environ.get("SLURMD_NODENAME")
                           or os.environ.get("SLURM_JOB_NODELIST")),
            **gov,
        }
        ART.write_run_status(run_dir, **status)
        # registry v2 (complete schema); the legacy registry.csv is NOT touched
        ART.append_registry_v2({
            "schema_version": ART.REGISTRY_SCHEMA_VERSION,
            "run_id": run_id, "status": "ok", "run_dir": run_dir,
            "checkpoint_sha256": man["sha256_file"],
            "state_dict_sha256": man["state_dict_sha256"],
            "best_val_mse": best_val, "best_epoch": best_epoch,
            "created_utc": ART.utc_now(), "git_sha": git_sha(),
            "notes": (f"{spec['model']} | {spec['text_encoder']} | "
                      f"{spec['fusion']} | L={horizon} | seed={seed} | "
                      f"epochs={cfg['epochs']}"),
            **gov})
        print(f"[runner] DONE {run_id} | best_val_mse={best_val:.4f} | "
              f"restore_ok={restore['ok']}")
        return status

    except Exception as e:
        import traceback
        traceback.print_exc()
        ART.write_run_status(run_dir, status="failed", run_id=run_id,
                             error=f"{e.__class__.__name__}: {e}", **gov)
        ART.append_registry_v2({
            "schema_version": ART.REGISTRY_SCHEMA_VERSION,
            "run_id": run_id, "status": "failed", "run_dir": run_dir,
            "created_utc": ART.utc_now(), "git_sha": git_sha(),
            "notes": f"{e.__class__.__name__}: {e}", **gov})
        raise


def find_completed_run(spec: dict):
    """Return an existing COMPLETED run dir for this spec (resume support)."""
    import glob
    import json

    from innovation.paths import RUNS_ROOT

    want = (spec["model"], spec["text_encoder"], spec["fusion"],
            int(spec["horizon"]), int(spec["seed"]))
    # STAGE-SCOPED resume: a run only satisfies a job of the SAME experiment
    # stage. Without this, an infrastructure "pilot" run of the same
    # (model, horizon, seed) would silently satisfy a later "screening"/"full"
    # job (skip-if-done), and no screening/full artifact would ever be produced.
    want_stage = str(spec.get("experiment_stage", "adhoc"))
    for d in sorted(glob.glob(os.path.join(RUNS_ROOT, "*"))):
        if not os.path.isdir(d):
            continue
        rp = os.path.join(d, "run_status.json")
        if not os.path.exists(rp):
            continue
        try:
            with open(rp, "r", encoding="utf-8") as f:
                st = json.load(f)
        except Exception:
            continue
        if st.get("status") != "ok":
            continue
        if str(st.get("experiment_stage")) != want_stage:
            continue
        try:
            meta = parse_run_id(os.path.basename(d))
        except Exception:
            continue
        got = (meta["model"], meta["text_encoder"], meta["fusion"],
               meta["horizon"], meta["seed"])
        if got == want:
            return d
    return None


def _rebuild(spec: dict, horizon: int, device: str):
    """Rebuild a fresh model with the same spec (for the restore test)."""
    raw = load_raw_df()
    scaler = load_scaler()
    model, _enc, _ctx = build_components(
        spec["model"], spec["text_encoder"], spec["fusion"], horizon, device,
        raw.iloc[:scaler.train_end],
        d_model=int(spec.get("d_model", DEFAULT_D_MODEL)),
        backbone_kwargs=spec.get("backbone_kwargs"))
    return model


# ── frozen-winner test evaluation (the ONLY place test artifacts exist) ─────
def run_test_evaluation(run_id: str, spec: dict, device: str | None = None) -> dict:
    from innovation.paths import FROZEN_WINNERS_PATH

    if not os.path.exists(FROZEN_WINNERS_PATH):
        raise RuntimeError("no frozen_winners.json — champion must be frozen "
                           "(select_best_model.py) before any test run")
    import json
    with open(FROZEN_WINNERS_PATH, "r", encoding="utf-8") as f:
        frozen = json.load(f)
    winners = {w.get("run_id") for w in frozen.get("winners", [])}
    if run_id not in winners:
        raise RuntimeError(f"run {run_id} is not a frozen winner — refusing to "
                           "touch the test split")

    ensure_innovation_dirs()
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    tev_id = make_test_eval_id(run_id)
    tev_dir = ART.create_test_eval_dir(tev_id)
    horizon = int(spec["horizon"])

    raw = load_raw_df()
    scaler = load_scaler()
    data = normalize(to_array(raw), scaler)
    windows = build_windows(data, horizon)
    model, encoder, ctx_fn = build_components(
        spec["model"], spec["text_encoder"], spec["fusion"], horizon, device,
        raw.iloc[:scaler.train_end],
        d_model=int(spec.get("d_model", DEFAULT_D_MODEL)),
        backbone_kwargs=spec.get("backbone_kwargs"))

    run_dir = os.path.join(ART.RUNS_ROOT, run_id)
    ckpt = os.path.join(run_dir, "checkpoints", "best_val_mse.pt")
    model.load_state_dict(torch.load(ckpt, map_location=device,
                                     weights_only=True), strict=True)

    test_df = predict_frame(model, windows["X_test"], windows["Y_test"],
                            windows["idx_test"], T, horizon, scaler, "test",
                            device, batch_size=int(spec.get("batch_size", 16)),
                            ctx_fn=ctx_fn)
    test_df.to_csv(os.path.join(tev_dir, "predictions", "test_predictions.csv"),
                   index=False)
    tm = MET.evaluate_predictions(test_df, "test", scaler=scaler)
    ART.write_json(os.path.join(tev_dir, "metrics", "test_metrics.json"), tm)
    ART.write_json(os.path.join(tev_dir, "config_resolved.json"),
                   {"test_eval_id": tev_id, "run_id": run_id,
                    "source_run_dir": run_dir, "spec": spec})
    ART.write_run_status(tev_dir, status="ok", phase="test", run_id=run_id,
                         test_eval_id=tev_id)
    ART.append_registry({"run_id": run_id, "status": "test_ok",
                         "run_dir": tev_dir, "notes": f"test_eval {tev_id}"})
    return tm


# ── CLI ─────────────────────────────────────────────────────────────────────
def _parse_args(argv=None):
    ap = argparse.ArgumentParser(description="innovation runner")
    ap.add_argument("--model", required=True)
    ap.add_argument("--text-encoder", default="none", dest="text_encoder")
    ap.add_argument("--fusion", default="identity")
    ap.add_argument("--horizon", type=int, default=24, choices=list(HORIZONS))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=16, dest="batch_size")
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--patience", type=int, default=7)
    ap.add_argument("--d-model", type=int, default=DEFAULT_D_MODEL, dest="d_model")
    ap.add_argument("--device", default=None)
    ap.add_argument("--model-id", default=None, dest="model_id",
                    help="local cached Transformers model identifier for Phase 1 LLM backbones")
    ap.add_argument("--load-backbone", action="store_true", dest="load_backbone",
                    help="load the cached LLM backbone; compute-node only")
    ap.add_argument("--limit-train", type=int, default=None, dest="limit_train")
    ap.add_argument("--limit-val", type=int, default=None, dest="limit_val")
    ap.add_argument("--skip-if-done", action="store_true", dest="skip_if_done")
    ap.add_argument("--max-seconds", type=int, default=None, dest="max_seconds")
    ap.add_argument("--experiment-stage", default="adhoc",
                    choices=list(STAGE_VALUES), dest="experiment_stage",
                    help="smoke/pilot are infrastructure-only and are NEVER "
                         "eligible for champion selection")
    return ap.parse_args(argv)


def spec_from_args(a) -> dict:
    return {"model": a.model, "text_encoder": a.text_encoder, "fusion": a.fusion,
            "horizon": a.horizon, "seed": a.seed, "epochs": a.epochs,
            "batch_size": a.batch_size, "lr": a.lr, "patience": a.patience,
            "d_model": a.d_model, "device": a.device,
            "backbone_kwargs": ({"model_id": a.model_id, "load_backbone": True}
                                if a.load_backbone and a.model_id else None),
            "limit_train": a.limit_train, "limit_val": a.limit_val,
            "max_seconds": a.max_seconds,
            "experiment_stage": a.experiment_stage}


def main(argv=None) -> int:
    a = _parse_args(argv)
    spec = spec_from_args(a)
    if getattr(a, "skip_if_done", False):
        done = find_completed_run(spec)
        if done:
            print(f"[runner] skip-if-done: completed run exists -> {done}")
            return 0
    run_one(spec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
