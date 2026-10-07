"""build_v38_closure.py — items 1-16: v3.7 supersede marker, complete runtime
dependency closure, v3.8 freeze, 598 specs, and a complete bundle A/B.

Root cause being fixed: the v3.7 bundle contained ONLY `scripts/*.py`, so the
frozen 598-spec registry, the 580 Slurm scripts and the canonical data were never
deployed and `clean_runner.py` could not start (Gate 568959).

This script therefore builds a COMPLETE runtime dependency closure:

    frozen scientific source  (scripts/**, incl. clean_runner.py, clean_gate.py)
    complete_specs_598.json / .csv        (the registry clean_runner reads)
    580 executable Slurm scripts + Gate wrapper
    canonical data / scaler artifacts
    asset descriptors (ids + revisions, NEVER weights)
    governance / isolation / metric-schema files
    environment / bootstrap metadata

and emits a deployment manifest with role, bytes and SHA-256 for every member.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "results" / "v3_clean" / "preregistration"
IMPL = ROOT / "results" / "v3_clean" / "implementation"
RUNS = ROOT / "results" / "v3_clean" / "runs"
SCRIPTS_SRC = ROOT / "hpc_scripts" / "v3_clean"
for d in (PREREG, IMPL, RUNS, SCRIPTS_SRC):
    d.mkdir(parents=True, exist_ok=True)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# Version identity is overridable so the SAME audited closure builder can cut a
# later version (e.g. v3.9) without forking the logic.
VERSION = os.environ.get("INNOV_VERSION",
                         "innov-v3.8-complete-deployment-closure")
PREV_VERSION = os.environ.get("INNOV_PREV_VERSION",
                              "innov-v3.7-clean-runner-complete")
# Version-derived marker filename so cutting a later version NEVER overwrites an
# earlier version's supersede record (historical evidence must be immutable).
SUPERSEDED_NAME = PREV_VERSION.replace("innov-", "").replace(".", "") \
                             .split("-")[0] + "_SUPERSEDED.json"
DEFERRED_PARENT = "BEST_VALIDATION_LLM_AFTER_SCREENING"
RUNNER_REL = "scripts/innovation/clean_runner.py"
GATE_REL = "scripts/innovation/clean_gate.py"
SPECS_JSON_REL = "results/v3_clean/runs/complete_specs_598.json"
SPECS_CSV_REL = "results/v3_clean/runs/complete_specs_598.csv"


TEXT_SUFFIXES = (".py", ".sh", ".json", ".csv", ".txt", ".md", ".yaml", ".yml")


def deploy_bytes(p: Path) -> bytes:
    """Bytes as they will EXIST in the deployment.

    Text members are normalised to POSIX LF: on Windows, `write_text()` and most
    repo files carry CRLF, and a CRLF `.sh` breaks bash (heredocs and #SBATCH
    parsing). The manifest hash MUST be taken over these normalised bytes so the
    recorded hash equals what is actually deployed.
    """
    data = p.read_bytes()
    if p.suffix.lower() in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return data


def sha256_file(p: Path) -> str:
    return hashlib.sha256(deploy_bytes(p)).hexdigest()


def apply(txt, old, new, label):
    n = txt.count(old)
    if n == 0 and new in txt:
        return txt, False
    if n != 1:
        raise SystemExit(f"anchor {label!r} not unique: found {n}")
    return txt.replace(old, new), True


# ── 1/4. preserve v3.7 and mark it superseded ───────────────────────────────
json.dump({
    "generated_utc": NOW,
    "status": "SUPERSEDED_FOR_EXECUTION_DEPLOYMENT_INCOMPLETENESS",
    "version": PREV_VERSION,
    "bundle_sha256":
        "ada959427ce7c949086cd3bfd63887ecf01fd7d2c86aac4aebb921e093b07bb1",
    "failed_deployment": "/scratch/sychan552/innovation_deploy_root_v3_clean1",
    "gate_job": "568959",
    "gate_result": "FAILED ExitCode 1:0",
    "failure_stage": "before clean_runner.py could execute",
    "reason": "the v3.7 bundle contained only scripts/*.py; the frozen 598-spec "
              "registry, hpc_scripts and canonical data were never deployed",
    "classification": "deployment-completeness defect (NOT a model/data/training/"
                      "metric or clean_runner scientific defect)",
    "preserved": True,
    "must_not": ["rerun 568959",
                 "patch v3_clean1 in place and retry"],
    "successor": VERSION,
}, open(IMPL / SUPERSEDED_NAME, "w", encoding="utf-8"), indent=2)

# ── 11. bump to v3.8 ────────────────────────────────────────────────────────
VP = ROOT / "scripts" / "innovation" / "paths.py"
vp = VP.read_text(encoding="utf-8")
vp2, bumped = apply(vp, f'IMPLEMENTATION_SOURCE_VERSION = "{PREV_VERSION}"',
                    f'IMPLEMENTATION_SOURCE_VERSION = "{VERSION}"', "version_bump")
if not bumped and VERSION not in vp:
    raise SystemExit("could not bump the source version")
VP.write_text(vp2, encoding="utf-8")

# ── source manifest + aggregate (frozen scientific source) ───────────────────
src_files = []
for p in sorted((ROOT / "scripts").rglob("*.py")):
    rel = str(p.relative_to(ROOT)).replace("\\", "/")
    if "/v3_clean/" in rel or "/__pycache__" in rel:
        continue
    src_files.append((rel, p))
src_files.sort()
source_manifest = [{"path": r, "sha256": sha256_file(p), "bytes": p.stat().st_size}
                   for r, p in src_files]
source_aggregate = hashlib.sha256(
    "\n".join(f"{m['path']}:{m['sha256']}" for m in source_manifest).encode()
).hexdigest()
json.dump({"generated_utc": NOW, "version": VERSION,
           "n_files": len(source_manifest),
           "aggregate_sha256": source_aggregate, "files": source_manifest},
          open(IMPL / "source_manifest.json", "w", encoding="utf-8"), indent=2)

# ── 13/14. regenerate the 598 specs bound to the v3.8 identity ───────────────
NON_LLM = ["nlinear", "dlinear", "patchtst", "itransformer"]
LLM = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
HOR = [24, 36, 48, 60]
SEEDS = list(range(42, 52))
ABL = ["without_dataset_information", "without_task_instruction",
       "without_input_variable_description", "without_lora",
       "without_multimodality", "without_lora_and_multimodality"]

rows = []


def add(**kw):
    kw.setdefault("submittable", True)
    kw.setdefault("executable_binding", True)
    rows.append(kw)


for m in NON_LLM:
    for h in HOR:
        for s in SEEDS:
            add(wave=1, arm="primary", model=m, group="A_non_llm", horizon=h,
                seed=s, control="", parent_model=m)
for m in LLM:
    for h in HOR:
        for s in SEEDS:
            add(wave=1, arm="primary", model=m, group="B_llm", horizon=h,
                seed=s, control="", parent_model=m)
for b in ("last_value_naive", "seasonal_naive"):
    for h in HOR:
        add(wave=1, arm="baseline", model=b, group="reference", horizon=h,
            seed="n/a", control="", parent_model=b)
for a in ABL:
    for h in HOR:
        for s in SEEDS:
            add(wave=1, arm="ablation", model=a, group="ablation", horizon=h,
                seed=s, control="", parent_model="gpt2_miflu")
for c in ("zero_text", "shuffled_text"):
    for h in (24, 60):
        for s in (42, 43, 44):
            add(wave=1, arm="negative_control", model=c, group="control",
                horizon=h, seed=s, control=c, parent_model="gpt2_miflu")
for c in ("zero_text", "shuffled_text", "llm_removed_or_alignment_only"):
    for h in (24, 60):
        for s in (42, 43, 44):
            add(wave=2, arm="negative_control", model=c, group="control",
                horizon=h, seed=s, control=c, parent_model=DEFERRED_PARENT,
                submittable=False, executable_binding=False)

for i, r in enumerate(rows, 1):
    r["order"] = i
    seed_tok = str(r["seed"]).replace("/", "")
    r["run_key"] = (f"{r['arm']}__{r['control'] or r['model']}__"
                    f"L{r['horizon']}__seed{seed_tok}__w{r['wave']}")
keys = [f"{r['model']}|{r['control']}|{r['parent_model']}|{r['horizon']}|"
        f"{r['seed']}|{r['wave']}" for r in rows]
duplicated = len(keys) - len(set(keys))
n_w1 = sum(1 for r in rows if r["wave"] == 1)
n_w2 = sum(1 for r in rows if r["wave"] == 2)

specs_payload = {"generated_utc": NOW, "version": VERSION,
                 "source_aggregate_sha256": source_aggregate,
                 "n_specs": len(rows),
                 "n_executable_bindings": sum(1 for r in rows
                                              if r["executable_binding"]),
                 "wave1": n_w1, "wave2": n_w2,
                 "runner": RUNNER_REL, "gate": GATE_REL,
                 "specs": rows}
json.dump(specs_payload, open(RUNS / "complete_specs_598.json", "w",
                              encoding="utf-8"), indent=2)
with open(RUNS / "complete_specs_598.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# ── 5/6/7. complete runtime dependency closure ──────────────────────────────
# (deploy_relative_path, local_source_path, role)
closure = []


def add_closure(deploy_rel: str, local: Path, role: str):
    if not local.exists():
        raise SystemExit(f"closure member missing: {local}")
    closure.append((deploy_rel, local, role))


for m in source_manifest:                      # frozen scientific source
    add_closure(m["path"], ROOT / m["path"], "frozen_scientific_source")
add_closure(SPECS_JSON_REL, RUNS / "complete_specs_598.json",
            "frozen_spec_registry_json")
add_closure(SPECS_CSV_REL, RUNS / "complete_specs_598.csv",
            "frozen_spec_registry_csv")
for p in sorted(SCRIPTS_SRC.glob("*.sh")):      # 580 row scripts + gate wrapper
    rel = f"hpc_scripts/v3_clean/{p.name}"
    role = ("gate_wrapper" if p.name == "clean_gate.sh"
            else "executable_slurm_script")
    add_closure(rel, p, role)
# RECURSIVE: load_raw_df() reads RAW_CSV = data/raw/national_illness_raw.csv,
# so a top-level-only glob would silently omit the canonical raw data (the exact
# class of defect that broke Gate 568959).
for p in sorted((ROOT / "data").rglob("*")):
    if p.is_file():
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        add_closure(rel, p, "canonical_data_or_scaler")
for p in sorted(PREREG.glob("*.json")):          # governance / isolation / schemas
    add_closure(f"results/v3_clean/preregistration/{p.name}", p,
                "governance_isolation_or_schema")
add_closure("results/v3_clean/implementation/source_manifest.json",
            IMPL / "source_manifest.json", "source_manifest")
add_closure(f"results/v3_clean/implementation/{SUPERSEDED_NAME}",
            IMPL / SUPERSEDED_NAME, "superseded_version_marker")

# asset descriptors: ids and revisions ONLY, never weights
assets = {
    "generated_utc": NOW,
    "policy": "immutable pretrained backbones are referenced by repository id "
              "and revision; weights are resolved from the offline cache and are "
              "NOT bundled",
    "assets": [
        {"role": "frozen_text_backbone", "repo_id": "gpt2",
         "framework": "transformers", "cache_path":
             "~/.cache/huggingface/hub/models--gpt2"},
        {"role": "frozen_llm_backbone", "repo_id": "Qwen/Qwen2.5-1.5B",
         "revision": "8faed761d45a263340a0528343f099c05c9a4323",
         "framework": "transformers", "cache_path":
             "~/.cache/huggingface/hub/models--Qwen--Qwen2.5-1.5B"},
    ],
}
assets_p = IMPL / "asset_descriptors.json"
assets_p.write_text(json.dumps(assets, indent=2), encoding="utf-8")
add_closure("results/v3_clean/implementation/asset_descriptors.json", assets_p,
            "asset_descriptor")

env_meta = {
    "generated_utc": NOW, "version": VERSION,
    "python": sys.version.split()[0],
    "conda_env": "mlflu_hpc",
    "path_prepend": "/home/sychan552/.conda/envs/mlflu_hpc/bin",
    "modules": "module unload default; module load old_modules",
    "hf_home": "/gpfs1/scratch/sychan552/CHATTIME/.cache",
    "matplotlib_backend": "Agg",
    "slurm": {"partition": "stingy", "gres": "gpu:a100:1",
              "exclude": "gpu-a100-05", "max_time": "04:00:00"},
}
env_p = IMPL / "environment_bootstrap.json"
env_p.write_text(json.dumps(env_meta, indent=2), encoding="utf-8")
add_closure("results/v3_clean/implementation/environment_bootstrap.json", env_p,
            "environment_bootstrap_metadata")

# ── 12. deployment manifest + deployment aggregate ───────────────────────────
deployment_manifest = []
for rel, local, role in sorted(closure):
    deployment_manifest.append({"path": rel, "role": role,
                                "bytes": local.stat().st_size,
                                "sha256": sha256_file(local)})
deployment_aggregate = hashlib.sha256(
    "\n".join(f"{m['path']}:{m['sha256']}" for m in deployment_manifest).encode()
).hexdigest()
json.dump({"generated_utc": NOW, "version": VERSION,
           "source_aggregate_sha256": source_aggregate,
           "deployment_aggregate_sha256": deployment_aggregate,
           "n_members": len(deployment_manifest),
           "roles": sorted({m["role"] for m in deployment_manifest}),
           "members": deployment_manifest},
          open(IMPL / "deployment_manifest.json", "w", encoding="utf-8"),
          indent=2)

# ── 15/16. complete bundle A and B, independently ───────────────────────────
FORBIDDEN_SUBSTRINGS = ("v3_superseded_archive", "test_evaluations",
                        "test_predictions", "test_metrics", "holdout")


def build_bundle(path: Path) -> tuple[str, list]:
    if path.exists():
        path.unlink()
    names = []
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        for rel, local, _role in sorted(closure):
            low = rel.lower()
            if any(f in low for f in FORBIDDEN_SUBSTRINGS):
                raise SystemExit(f"forbidden member in bundle: {rel}")
            names.append(rel)
            info = zipfile.ZipInfo(rel, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, deploy_bytes(local))
    return sha256_file(path), names


ba, names_a = build_bundle(IMPL / "bundle_a.zip")
bb, names_b = build_bundle(IMPL / "bundle_b.zip")
byte_identical = (IMPL / "bundle_a.zip").read_bytes() == \
                 (IMPL / "bundle_b.zip").read_bytes()
json.dump({"generated_utc": NOW, "version": VERSION,
           "bundle_a_sha256": ba, "bundle_b_sha256": bb,
           "sha256_identical": ba == bb,
           "byte_identical": byte_identical,
           "member_list_identical": names_a == names_b,
           "n_members": len(names_a),
           "source_aggregate_sha256": source_aggregate,
           "deployment_aggregate_sha256": deployment_aggregate,
           "excluded": list(FORBIDDEN_SUBSTRINGS)},
          open(IMPL / "deterministic_bundle_report.json", "w",
               encoding="utf-8"), indent=2)

print("[v38] version=%s" % VERSION)
print("[v38] source_files=%d source_agg=%s"
      % (len(source_manifest), source_aggregate[:16]))
print("[v38] specs=%d wave1=%d wave2=%d deleted=0 duplicated=%d"
      % (len(rows), n_w1, n_w2, duplicated))
print("[v38] closure_members=%d deployment_agg=%s"
      % (len(deployment_manifest), deployment_aggregate[:16]))
print("[v38] bundle A=%s B=%s byte_identical=%s members_equal=%s"
      % (ba[:16], bb[:16], byte_identical, names_a == names_b))
if not (ba == bb and byte_identical and names_a == names_b):
    raise SystemExit("bundle A/B mismatch")
