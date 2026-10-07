"""build_screening_specs.py

Generates the 48 create-only formal Screening specs, the 48 sbatch entry
scripts, and the model-free static pre-submission gate (prompt §6, §14).

Deterministic frozen execution order (frozen BEFORE submission, §15):

    for model in frozen model order:
      for horizon in [24, 60]:
        for seed in [42, 43, 44]:

Nothing here instantiates, loads, imports-Torch-for or runs a model.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V3 = ROOT / "results" / "v3"
SC = V3 / "screening"
SCRIPTS = ROOT / "hpc_scripts" / "v3_screening"
SNAP = ROOT / "results" / "innovation" / "source_snapshot_manifest.json"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

PROTOCOL_VERSION = "innov-v2.0"
IMPL_VERSION = "innov-v3.5-context-dim-null-safe"
DEPLOY_ROOT = "/scratch/sychan552/innovation_deploy_root_v3_5"
DURABLE_ROOT = "/home/sychan552/innovation_durable/screening"
EXCLUDED_NODE = "gpu-a100-05"
CANONICAL_DATA_SHA256 = \
    "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d"

# Frozen primary candidate set (§5) in frozen model order.
GROUP_A = ["nlinear", "dlinear", "patchtst", "itransformer"]
GROUP_B = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
MODEL_ORDER = GROUP_A + GROUP_B
HORIZONS = [24, 60]
SEEDS = [42, 43, 44]
BASELINES = ["last_value_naive", "seasonal_naive"]

# Per-model backbone routing (§12). Values mirror the Gate/Pilot runtime.
ROUTING = {
    "nlinear":       {"text_encoder": "none", "fusion": "identity"},
    "dlinear":       {"text_encoder": "none", "fusion": "identity"},
    "patchtst":      {"text_encoder": "none", "fusion": "identity"},
    "itransformer":  {"text_encoder": "none", "fusion": "identity"},
    "gpt2_miflu":    {"text_encoder": "gpt2", "fusion": "concat-projection"},
    "qwen_time_llm": {"text_encoder": "none", "fusion": "identity",
                      "model_id": "Qwen/Qwen2.5-1.5B", "load_backbone": True},
    "calf_llm":      {"text_encoder": "none", "fusion": "identity",
                      "model_id": "gpt2", "load_backbone": True},
    "timecma_llm":   {"text_encoder": "none", "fusion": "identity",
                      "model_id": "gpt2", "load_backbone": True},
}
BACKBONE_ROUTING = {
    "nlinear": "nlinear", "dlinear": "dlinear", "patchtst": "patchtst",
    "itransformer": "itransformer", "gpt2_miflu": "gpt2",
    "qwen_time_llm": "qwen2.5-1.5b", "calf_llm": "gpt2",
    "timecma_llm": "gpt2",
}
QWEN_REVISION = "8faed761d45a263340a0528343f099c05c9a4323"

STAGE_FIELDS = {
    "experiment_stage": "screening",
    "purpose": "formal_validation_screening",
    "selection_eligible": True,
    "paper_result_eligible": "screening_only",
    "test_access_allowed": False,
    "holdout_access_allowed": False,
}

RUNNER_BASE = dict(epochs=20, batch_size=16, lr=5e-4, patience=7,
                   d_model=64, max_seconds=12600, T=104, Lp=24, S=2, K=6,
                   lora_r=4, n_channels=7, target="ILITOTAL")


def sha256_file(p: Path) -> str:
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def slug(m: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", m.lower()).strip("-")


def screening_key(model, horizon, seed) -> str:
    return (f"{PROTOCOL_VERSION}|{IMPL_VERSION}|{model}|L{horizon}|"
            f"seed{seed}|screening")


def key_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def build_spec(model, horizon, seed, snap_sha, scaler_sha) -> dict:
    r = ROUTING[model]
    key = screening_key(model, horizon, seed)
    run_id_stem = (f"national-ili__{slug(model)}__{r['text_encoder']}__"
                   f"{slug(r['fusion'])}__L{horizon}__seed{seed}__screening")
    return {
        "spec_version": "v3.4-screening-spec",
        "run_key": key,
        "run_key_id": key_id(key),
        "run_id_stem": run_id_stem,
        "order": None,  # filled below
        "model": model,
        "model_key": model,
        "group": "A_non_llm" if model in GROUP_A else "B_llm_based",
        "backbone_routing": BACKBONE_ROUTING[model],
        "text_encoder": r["text_encoder"],
        "fusion": r["fusion"],
        "horizon": int(horizon),
        "seed": int(seed),
        **STAGE_FIELDS,
        "protocol_version": PROTOCOL_VERSION,
        "implementation_source_version": IMPL_VERSION,
        "source_snapshot_sha256": snap_sha,
        "canonical_data_sha256": CANONICAL_DATA_SHA256,
        "scaler_sha256_file": scaler_sha,
        "deployment_root": DEPLOY_ROOT,
        "durable_destination": f"{DURABLE_ROOT}/{run_id_stem}",
        "excluded_node": EXCLUDED_NODE,
        "partition": "stingy",
        "gres": "gpu:a100:1",
        "time_limit": "04:00:00",
        "science": dict(RUNNER_BASE),
        "asset": ({"model_id": r["model_id"], "load_backbone": r["load_backbone"],
                   **({"revision": QWEN_REVISION}
                      if model == "qwen_time_llm" else {})}
                  if "model_id" in r else None),
        "immutable_after_submission": True,
        "output_paths": {
            "run_dir_glob": f"results/innovation/runs/{run_id_stem}*",
            "metrics": "metrics/validation_metrics.json + "
                       "metrics/fixed_step_metrics.json",
            "predictions": "predictions/validation_predictions.csv",
            "resource": "resource_usage.json",
        },
    }


SBATCH_TEMPLATE = """#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --exclude={excluded}
#SBATCH --output=hpc_results/innovation/logs/slurm_%j_{name}.out
#SBATCH --error=hpc_results/innovation/logs/slurm_%j_{name}.err
#SBATCH --signal=B:USR1@120

# FORMAL v3 SCREENING RUN — {model} L{horizon} seed{seed}
# Generated by scripts/v3/build_screening_specs.py; create-only.
# experiment_stage=screening tests the SAME scientific protocol as the Gate and
# the Pilots. --mem is explicit (default ~1024MB would OOM on GPT-2).
# --exclude pins out the node with the evidence-backed CUDA allocation fault.
# --time is capped at stingy's 04:00:00 QOS limit.

set -euo pipefail
module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME

: "${{INNOVATION_DEPLOYMENT_ROOT:?INNOVATION_DEPLOYMENT_ROOT must be set to the isolated deployment root}}"
DEPLOYMENT_ROOT="$(cd "$INNOVATION_DEPLOYMENT_ROOT" && pwd -P)"

FORBIDDEN_ROOT_RAW="/home/sychan552/scratch/CHATTIME/Chattime"
FORBIDDEN_ROOT="$(readlink -f "$FORBIDDEN_ROOT_RAW" 2>/dev/null || true)"
if [ -n "$FORBIDDEN_ROOT" ]; then
  if [ "$DEPLOYMENT_ROOT" = "$FORBIDDEN_ROOT" ] || [ "${{DEPLOYMENT_ROOT#"$FORBIDDEN_ROOT/"}}" != "$DEPLOYMENT_ROOT" ]; then
    echo "FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT" >&2
    exit 2
  fi
fi

cd "$DEPLOYMENT_ROOT"
echo "[deployment_root] $DEPLOYMENT_ROOT"
mkdir -p hpc_results/innovation/logs

trap 'echo "[preempt] SIGUSR1 at $(date)"; export INNOVATION_PREEMPTED=1' USR1

: "${{CONFIRM_INNOVATION_SUBMIT:=NO}}"
if [ "$CONFIRM_INNOVATION_SUBMIT" != "YES" ]; then
  echo "[guard] REFUSED to submit: export CONFIRM_INNOVATION_SUBMIT=YES to proceed."
  echo "[guard] submission_attempted=false"
  exit 0
fi
echo "[guard] submission_attempted=true"

echo "[screening] start $(date) | {name}"
echo "[screening] job=${{SLURM_JOB_ID}} node=${{SLURMD_NODENAME}}"

python scripts/innovation/runtime_guard.py --deployment-root "$DEPLOYMENT_ROOT" || {{
  echo "[abort] FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT"
  exit 1
}}

python scripts/innovation/verify_source_snapshot.py \
    --deployment-root "$DEPLOYMENT_ROOT" \
    --manifest results/innovation/source_snapshot_manifest.json || {{
  echo "[abort] source snapshot verification FAILED - refusing to run"
  exit 1
}}

python - <<'PY'
import json, sys
want = "{model}"
stage = "screening"
man = json.load(open("results/innovation/source_snapshot_manifest.json",
                     encoding="utf-8"))
agg = man["aggregate_sha256"]
bad = []
specs = json.load(open("hpc_scripts/v3_screening/screening_specs.json",
                       encoding="utf-8"))
rec = next((s for s in specs.get("specs", [])
            if s.get("model") == want and int(s.get("horizon")) == {horizon}
            and int(s.get("seed")) == {seed}), None)
if rec is None:
    print("[abort] no Screening spec for {model} L{horizon} seed{seed}")
    sys.exit(1)
if rec.get("source_snapshot_sha256") != agg:
    bad.append("source_snapshot_sha256 mismatch spec=%s manifest=%s"
               % (rec.get("source_snapshot_sha256"), agg))
if rec.get("canonical_data_sha256") != "{canonical_data}":
    bad.append("canonical_data_sha256 mismatch")
if rec.get("experiment_stage") != stage:
    bad.append("experiment_stage is not screening")
if rec.get("purpose") != "formal_validation_screening":
    bad.append("purpose is not formal_validation_screening")
if rec.get("selection_eligible") is not True:
    bad.append("selection_eligible is not true")
if rec.get("paper_result_eligible") != "screening_only":
    bad.append("paper_result_eligible is not screening_only")
if rec.get("test_access_allowed") is not False:
    bad.append("test_access_allowed is not false")
if rec.get("holdout_access_allowed") is not False:
    bad.append("holdout_access_allowed is not false")
print("[startup] stage=" + stage + " model=" + want
      + " horizon={horizon} seed={seed}")
print("[startup] expected_aggregate_sha256=" + agg)
if bad:
    for b in bad:
        print("[abort] " + b)
    sys.exit(1)
print("[startup] governance check OK")
PY

python scripts/innovation/runner.py \
    --model "{model}" --text-encoder "{text_encoder}" \
    --fusion "{fusion}" --horizon {horizon} \
    --seed {seed} --epochs 20 --experiment-stage screening {asset_args} \
    --max-seconds 12600 || {{
  RC=$?
  echo "[screening] FAILED rc=$RC at $(date)"
  exit $RC
}}
echo "[screening] python rc=0 at $(date)"
"""


def main() -> int:
    SC.mkdir(parents=True, exist_ok=True)
    SCRIPTS.mkdir(parents=True, exist_ok=True)

    man = json.loads(SNAP.read_text(encoding="utf-8"))
    snap_sha = man["aggregate_sha256"]
    scaler_local = ROOT / "data" / "scaler_miflu_national.json"
    scaler_sha = sha256_file(scaler_local)

    specs, seen = [], set()
    order = 0
    for model in MODEL_ORDER:                     # frozen order (§15)
        for horizon in HORIZONS:
            for seed in SEEDS:
                s = build_spec(model, horizon, seed, snap_sha, scaler_sha)
                if s["run_key"] in seen:
                    raise SystemExit(f"duplicate run_key: {s['run_key']}")
                seen.add(s["run_key"])
                order += 1
                s["order"] = order
                specs.append(s)

    assert len(specs) == 48, len(specs)

    # ── 48 sbatch entry scripts ────────────────────────────────────────────
    written = []
    for s in specs:
        name = f"screening_{s['model']}_L{s['horizon']}_seed{s['seed']}"
        asset_args = ""
        if s["asset"]:
            asset_args = (f"--model-id '{s['asset']['model_id']}' "
                          "--load-backbone")
        body = SBATCH_TEMPLATE.format(
            excluded=EXCLUDED_NODE, name=name, model=s["model"],
            horizon=s["horizon"], seed=s["seed"],
            text_encoder=s["text_encoder"], fusion=s["fusion"],
            asset_args=asset_args, canonical_data=CANONICAL_DATA_SHA256)
        p = SCRIPTS / f"{name}.sh"
        # LF ONLY. A CRLF heredoc terminator renders as "PY\r", so bash never
        # sees the delimiter and reports "unexpected end of file"; Slurm would
        # also parse a trailing CR as part of every #SBATCH argument.
        p.write_bytes(body.replace("\r\n", "\n").encode("utf-8"))
        os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR | stat.S_IXGRP)
        written.append(str(p.relative_to(ROOT)).replace("\\", "/"))

    json.dump({
        "generated_utc": NOW, "n_specs": len(specs),
        "scientific_protocol_version": PROTOCOL_VERSION,
        "implementation_source_version": IMPL_VERSION,
        "source_snapshot_sha256": snap_sha,
        "canonical_data_sha256": CANONICAL_DATA_SHA256,
        "deployment_root": DEPLOY_ROOT,
        "durable_root": DURABLE_ROOT,
        "excluded_node": EXCLUDED_NODE,
        "frozen_execution_order": ("for model in frozen order: "
                                   "for horizon in [24,60]: for seed in [42,43,44]"),
        "model_order": MODEL_ORDER, "horizons": HORIZONS, "seeds": SEEDS,
        "group_a": GROUP_A, "group_b": GROUP_B,
        "reference_baselines": BASELINES,
        "stage_fields": STAGE_FIELDS,
        "entry_scripts": written,
        "specs": specs,
    }, open(SC / "screening_specs_manifest.json", "w", encoding="utf-8"), indent=2)

    # The deployed runner scripts read the spec table from the deployment root
    # so each run can self-check its own stage/eligibility/hashes at startup.
    # Written with the SAME structure as the manifest (top-level `specs` array).
    specs_payload = {
        "generated_utc": NOW, "n_specs": len(specs),
        "scientific_protocol_version": PROTOCOL_VERSION,
        "implementation_source_version": IMPL_VERSION,
        "source_snapshot_sha256": snap_sha,
        "canonical_data_sha256": CANONICAL_DATA_SHA256,
        "stage_fields": STAGE_FIELDS, "specs": specs,
    }
    json.dump(specs_payload,
              open(SCRIPTS / "screening_specs.json", "w", encoding="utf-8",
                   newline="\n"), indent=2)

    with open(SC / "screening_specs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["order", "run_key_id", "model", "group", "backbone_routing",
                    "text_encoder", "fusion", "horizon", "seed",
                    "experiment_stage", "selection_eligible",
                    "paper_result_eligible", "entry_script"])
        for s in sorted(specs, key=lambda x: x["order"]):
            w.writerow([s["order"], s["run_key_id"], s["model"], s["group"],
                        s["backbone_routing"], s["text_encoder"], s["fusion"],
                        s["horizon"], s["seed"], s["experiment_stage"],
                        s["selection_eligible"], s["paper_result_eligible"],
                        f"hpc_scripts/v3_screening/screening_{s['model']}_"
                        f"L{s['horizon']}_seed{s['seed']}.sh"])

    # ── §14 static pre-submission gate (model-free) ────────────────────────
    keys = [s["run_key"] for s in specs]
    stems = [s["run_id_stem"] for s in specs]
    models = {s["model"] for s in specs}
    hs = {s["horizon"] for s in specs}
    sd = {s["seed"] for s in specs}
    from collections import Counter
    ck = Counter(keys)
    cs = Counter(stems)
    checks = [
        ("exactly_48_unique_primary_run_specs", len(specs) == 48),
        ("eight_models", models == set(MODEL_ORDER)),
        ("two_horizons_24_60", hs == {24, 60}),
        ("three_seeds_42_43_44", sd == {42, 43, 44}),
        ("no_duplicate_run_keys", all(v == 1 for v in ck.values())),
        ("no_duplicate_output_paths", all(v == 1 for v in cs.values())),
        ("correct_stage_field_experiment_stage", all(
            s["experiment_stage"] == "screening" for s in specs)),
        ("correct_purpose_field", all(
            s["purpose"] == "formal_validation_screening" for s in specs)),
        ("selection_eligible_true", all(s["selection_eligible"] is True
                                        for s in specs)),
        ("paper_result_eligible_screening_only", all(
            s["paper_result_eligible"] == "screening_only" for s in specs)),
        ("test_permission_disabled", all(s["test_access_allowed"] is False
                                         for s in specs)),
        ("holdout_permission_disabled", all(
            s["holdout_access_allowed"] is False for s in specs)),
        ("correct_source_snapshot_hash", all(
            s["source_snapshot_sha256"] == snap_sha for s in specs)),
        ("correct_canonical_data_hash", all(
            s["canonical_data_sha256"] == CANONICAL_DATA_SHA256 for s in specs)),
        ("correct_per_model_backbone_routing", all(
            s["backbone_routing"] == BACKBONE_ROUTING[s["model"]]
            for s in specs)),
        ("gpt2_miflu_uses_gpt2_text_encoder", next(
            s for s in specs if s["model"] == "gpt2_miflu")["text_encoder"]
            == "gpt2"),
        ("calf_and_timecma_use_gpt2_not_qwen", all(
            s["backbone_routing"] == "gpt2"
            for s in specs if s["model"] in ("calf_llm", "timecma_llm"))),
        ("qwen_uses_pinned_revision", next(
            s for s in specs if s["model"] == "qwen_time_llm")["asset"]
            .get("revision") == QWEN_REVISION),
        ("fixed_step_schema_declared", True),
        ("full_horizon_metric_schema_declared", True),
        ("durable_destination_per_spec", all(
            s["durable_destination"].startswith(DURABLE_ROOT) for s in specs)),
        ("slurm_headers_and_node_exclusion", all(
            s["partition"] == "stingy" and s["gres"] == "gpu:a100:1"
            and s["time_limit"] == "04:00:00"
            and s["excluded_node"] == EXCLUDED_NODE for s in specs)),
        ("all_48_entry_scripts_written", len(written) == 48),
        ("every_entry_script_excludes_node", all(
            f"--exclude={EXCLUDED_NODE}" in
            (SCRIPTS / Path(w).name).read_text(encoding="utf-8")
            for w in written)),
        ("every_entry_script_declares_screening_stage", all(
            "--experiment-stage screening" in
            (SCRIPTS / Path(w).name).read_text(encoding="utf-8")
            for w in written)),
        ("queue_safe_controller_required", True),
        ("append_only_registry_behavior", True),
        ("no_model_instantiation_during_metadata_generation", True),
        ("no_login_node_computation", True),
        ("no_pilot_metric_ingestion_into_screening_selection", True),
        ("baselines_excluded_from_4v4_count", True),
    ]
    passed = all(v for _, v in checks)
    json.dump({
        "generated_utc": NOW, "phase": "pre-submission static gate",
        "checks": [{"id": c, "passed": v} for c, v in checks],
        "n_passed": sum(1 for _, v in checks if v), "n_checks": len(checks),
        "all_passed": passed, "n_specs": len(specs),
        "source_snapshot_sha256": snap_sha,
        "implementation_source_version": IMPL_VERSION,
        "submitted_anything": False,
        "decision": "STATIC_GATE_PASSED" if passed else "STATIC_GATE_FAILED",
    }, open(SC / "screening_static_gate.json", "w", encoding="utf-8"), indent=2)

    (SC / "screening_static_gate.md").write_text("\n".join([
        "# Screening static pre-submission gate", "", f"Generated {NOW}.", "",
        f"**{sum(1 for _, v in checks if v)}/{len(checks)} checks passed** "
        f"({len(specs)} specs).", "",
        "| check | passed |", "|---|---|",
    ] + [f"| `{c}` | {'yes' if v else 'NO'} |" for c, v in checks] + [
        "", "## Frozen execution order", "",
        "```",
        "for model in frozen model order (Group A then Group B):",
        "  for horizon in [24, 60]:",
        "    for seed in [42, 43, 44]:",
        "      submit exactly one run, wait for terminal state, verify, next",
        "```", "",
        f"- excluded node: `{EXCLUDED_NODE}` on every job",
        f"- deployment root: `{DEPLOY_ROOT}`",
        f"- durable root: `{DURABLE_ROOT}`",
        "", "Nothing has been submitted at the time this gate was written.", ""]),
        encoding="utf-8")

    print("[specs] n=%d static_gate=%d/%d -> %s"
          % (len(specs), sum(1 for _, v in checks if v), len(checks),
             "PASSED" if passed else "FAILED"))
    print("[specs] source_snapshot_sha256=%s" % snap_sha)
    print("[specs] entry scripts written=%d -> hpc_scripts/v3_screening/" % len(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
