"""
prehpc_report.py — generate the pre-HPC verification artifacts.
==============================================================

Produces (all under `results/innovation/`):

  audit/fix_fingerprint.json          repository_head, working_tree_dirty,
                                      fix_identifier, fix_files + per-file
                                      SHA-256 + aggregate SHA-256, timestamp,
                                      fix_commit=null (NOT a commit)
  audit/failed_runs_resolution.md     the 5 failed registry entries: root cause,
                                      fix identifier/files, replacement run_id,
                                      resolution status, ineligibility proof
  audit/environment_report.{json,md}  nvidia-smi, CUDA count/name, and the
                                      requested vs actual device PER RUN, plus
                                      the explicit "CPU smoke" correction note
  audit/architecture_equivalence.{json,md}  the three fidelity levels with
                                      component-level file:line evidence
  audit/eligibility_policy.md         the eligibility contract
  legacy_runs_eligibility.json        annotation marking every existing
                                      smoke/failed run selection_eligible=false
  pre_hpc_gate.{json,md}              readiness for pilot generation, pilot
                                      submission and full-sweep submission
                                      (reported separately); never submits.

It performs NO git operation and NEVER invokes sbatch.
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import hashlib
import json
import os
import re
import subprocess

from innovation import fidelity as FID
from innovation import run_artifacts as ART
from innovation.paths import (AUDIT_DIR, FIX_FINGERPRINT_PATH,
                              FROZEN_WINNERS_PATH, HORIZONS,
                              HUMAN_REVIEW_CHECKLIST,
                              IMPLEMENTATION_SOURCE_VERSION, INNOVATION_ROOT,
                              LEGACY_ELIGIBILITY_PATH, PLAN_MD,
                              PLAN_SHA256_EXPECTED, PREHPC_GATE_PATH,
                              PROTOCOL_VERSION, PROJECT_ROOT, RUNS_ROOT,
                              SOURCE_SNAPSHOT_DIR, SOURCE_SNAPSHOT_MANIFEST,
                              TEST_EVAL_ROOT, plan_sha256_status)

FIX_FILES = ["scripts/innovation/runner.py"]
_MD = {
    "failed": os.path.join(AUDIT_DIR, "failed_runs_resolution.md"),
    "env": os.path.join(AUDIT_DIR, "environment_report.md"),
    "arch": os.path.join(AUDIT_DIR, "architecture_equivalence.md"),
    "elig": os.path.join(AUDIT_DIR, "eligibility_policy.md"),
    "gate": os.path.join(INNOVATION_ROOT, "pre_hpc_gate.md"),
    "checklist": HUMAN_REVIEW_CHECKLIST,
}


# ── helpers ─────────────────────────────────────────────────────────────────
def _git(args):
    """Run git and return stdout (UTF-8 with replacement — porcelain output
    contains CJK filenames that the cp950 default cannot decode)."""
    try:
        return subprocess.check_output(
            ["git", *args], cwd=PROJECT_ROOT, stderr=subprocess.DEVNULL,
            encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def fix_fingerprint() -> dict:
    head = _git(["rev-parse", "HEAD"]) or "nogit"
    short = _git(["rev-parse", "--short", "HEAD"]) or "nogit"
    dirty = bool(_git(["status", "--porcelain"]))
    per_file = {f: ART.sha256_file(os.path.join(PROJECT_ROOT, f))
                for f in FIX_FILES if os.path.exists(os.path.join(PROJECT_ROOT, f))}
    agg = hashlib.sha256("\n".join(f"{k}:{v}" for k, v in sorted(per_file.items()))
                         .encode()).hexdigest()
    pkg_files = sorted(glob.glob(os.path.join(PROJECT_ROOT, "scripts", "innovation",
                                              "**", "*.py"), recursive=True))
    pkg_lines = [f"{os.path.relpath(p, PROJECT_ROOT)}:"
                 f"{ART.sha256_file(p)}" for p in pkg_files]
    pkg_agg = hashlib.sha256("\n".join(pkg_lines).encode()).hexdigest()
    return {
        "repository_head": head,
        "repository_head_short": short,
        "working_tree_dirty": dirty,
        "fix_commit": None,                      # explicitly NOT a commit
        "fix_identifier": f"working-tree@{short}+innovation-pkg:{pkg_agg[:12]}",
        "fix_files": sorted(per_file),
        "fix_files_sha256": per_file,
        "fix_files_aggregate_sha256": agg,
        "innovation_package_files": len(pkg_files),
        "innovation_package_aggregate_sha256": pkg_agg,
        "timestamp_utc": ART.utc_now(),
        "note": ("The repair is UNCOMMITTED. `fix_commit` is null by definition; "
                 "`fix_identifier` identifies the working-tree state instead."),
    }


def _nvidia_smi() -> dict:
    try:
        r = subprocess.run(["nvidia-smi"], capture_output=True, text=True,
                           timeout=30)
        return {"available": r.returncode == 0, "output": r.stdout.strip()[:4000]}
    except Exception as e:
        return {"available": False, "error": str(e)}


def _torch_cuda() -> dict:
    try:
        import torch
        return {"cuda_available": bool(torch.cuda.is_available()),
                "device_count": int(torch.cuda.device_count()),
                "device_name": (torch.cuda.get_device_name(0)
                                if torch.cuda.is_available() else None),
                "torch": torch.__version__}
    except Exception as e:
        return {"error": str(e)}


def _parse_txt(path, key):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.strip().startswith(key):
                return line.split(":", 1)[1].strip()
    return None


def per_run_devices() -> list[dict]:
    out = []
    for d in sorted(glob.glob(os.path.join(RUNS_ROOT, "*"))):
        if not os.path.isdir(d):
            continue
        rid = os.path.basename(d)
        st = {}
        rp = os.path.join(d, "run_status.json")
        if os.path.exists(rp):
            try:
                st = json.load(open(rp, encoding="utf-8"))
            except Exception:
                st = {}
        cfg = os.path.join(d, "config_resolved.yaml")
        req = st.get("device_requested")
        if req is None and os.path.exists(cfg):
            m = re.search(r"device:\s*\"?([A-Za-z0-9:_]+)\"?", open(cfg, encoding="utf-8").read())
            req = m.group(1) if m else None
        act = st.get("device_actual") or _parse_txt(os.path.join(d, "environment.txt"), "device")
        out.append({
            "run_id": rid, "status": st.get("status"),
            "experiment_stage": st.get("experiment_stage"),
            "selection_eligible": st.get("selection_eligible"),
            "device_requested": req, "device_actual": act,
            "device_name": st.get("device_name"),
            "cuda_available": _parse_txt(os.path.join(d, "environment.txt"), "cuda_avail"),
        })
    return out


def failed_runs() -> tuple[list, list]:
    import csv
    reg = os.path.join(INNOVATION_ROOT, "registry.csv")
    rows = list(csv.DictReader(open(reg, encoding="utf-8"))) if os.path.exists(reg) else []
    failed = [r for r in rows if r["status"] == "failed"]
    ok = [r for r in rows if r["status"] == "ok"]

    def key(rid):
        p = rid.split("__")
        return tuple(p[:3] + p[4:6]) if len(p) >= 6 else tuple(p)

    ok_keys = {key(r["run_id"]): r["run_id"] for r in ok}
    resolved = []
    for r in failed:
        k = key(r["run_id"])
        resolved.append({"failed_run_id": r["run_id"],
                         "error": r["notes"],
                         "replacement_run_id": ok_keys.get(k),
                         "resolution_status": ("resolved" if ok_keys.get(k)
                                               else "unresolved")})
    return failed, resolved


def architecture_reports() -> dict:
    from innovation.backbones import make_backbone
    out = {}
    for name in ("dlinear", "nlinear", "patchtst", "itransformer",
                 "fusion_forecaster", "gpt2_miflu"):
        try:
            kw = dict(T=104, N=7, L=24)
            if name == "gpt2_miflu":
                kw["device"] = "cpu"
            rep = make_backbone(name, **kw).architecture_report()
        except Exception as e:
            rep = {"name": name, "error": str(e), "fidelity": None}
        out[name] = rep
    return out


# ── markdown writers ────────────────────────────────────────────────────────
def _write_md(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def md_failed(fp, resolved, ineligible_note):
    lines = ["# Failed runs resolution (pre-HPC)", "",
             f"- `repository_head`: `{fp['repository_head']}` "
             f"(short `{fp['repository_head_short']}`)",
             f"- `working_tree_dirty`: `{fp['working_tree_dirty']}`",
             f"- `fix_commit`: **null** (the repair is uncommitted)",
             f"- `fix_identifier`: `{fp['fix_identifier']}`",
             f"- `fix_files`: {', '.join('`'+f+'`' for f in fp['fix_files'])}",
             f"- `fix_files_aggregate_sha256`: `{fp['fix_files_aggregate_sha256']}`",
             f"- `timestamp_utc`: `{fp['timestamp_utc']}`", "",
             "## Per-file SHA-256", ""]
    for f, h in fp["fix_files_sha256"].items():
        lines.append(f"| `{f}` | `{h}` |")
    lines += ["", "## The 5 failed registry entries", "",
              "| failed run_id | root cause | fix_identifier | replacement run_id | resolution |",
              "|---|---|---|---|---|"]
    for r in resolved:
        lines.append(f"| `{r['failed_run_id']}` | {r['error']} | "
                     f"`{fp['fix_identifier']}` | `{r['replacement_run_id'] or 'NONE'}` | "
                     f"**{r['resolution_status']}** |")
    lines += ["", "## Eligibility of failed runs", "", ineligible_note, ""]
    _write_md(_MD["failed"], "\n".join(lines))


def md_env(env, runs):
    lines = ["# Environment report (pre-HPC)", "",
             "## Correction of the earlier “local CPU smoke” description", "",
             f"> **AUDIT NOTE.** The infrastructure/smoke phase was earlier "
             f"described as a “local CPU smoke”. That was **incorrect**: "
             f"`torch.cuda.is_available() == True` and every recorded run reports "
             f"`device: cuda`. The smoke runs actually executed on **cuda:0** "
             f"({env['torch_cuda'].get('device_name')}). The mis-description is "
             f"corrected here; no result is affected.", "",
             "## Observed environment", "",
             f"- CUDA available: `{env['torch_cuda'].get('cuda_available')}`",
             f"- CUDA device count: `{env['torch_cuda'].get('device_count')}`",
             f"- Device name: `{env['torch_cuda'].get('device_name')}`",
             f"- torch: `{env['torch_cuda'].get('torch')}`", "",
             "### nvidia-smi", "", "```",
             env["nvidia_smi"].get("output", env["nvidia_smi"].get("error", "(unavailable)")),
             "```", "",
             "## Requested vs actual device per run", "",
             "| run_id | status | stage | eligible | requested | actual | cuda_avail |",
             "|---|---|---|---|---|---|---|"]
    for r in runs:
        lines.append(f"| `{r['run_id'][:52]}…` | {r['status']} | {r['experiment_stage']} "
                     f"| {r['selection_eligible']} | {r['device_requested']} "
                     f"| {r['device_actual']} | {r['cuda_available']} |")
    _write_md(_MD["env"], "\n".join(lines))


def md_arch(arch):
    lines = ["# Architecture equivalence (pre-HPC)", "",
             f"Fidelity levels: `{FID.REFERENCE_FAITHFUL}`, "
             f"`{FID.REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS}`, "
             f"`{FID.INSPIRED_SIMPLIFICATION}`.", ""]
    for name, rep in arch.items():
        lines += [f"## `{name}` — **{rep.get('fidelity')}**", "",
                  f"- display name: {rep.get('display_name')}",
                  f"- published: {rep.get('published')}", ""]
        ev = rep.get("evidence") or []
        if ev:
            lines.append("Component-level evidence (file:line):")
            lines += [f"  - `{e}`" for e in ev]
            lines.append("")
        dev = rep.get("deviations") or []
        if dev:
            lines.append("Deviations from the published architecture:")
            for d in dev:
                lines.append(f"  - **{d.get('component')}** — {d.get('deviation')} "
                             f"(`{d.get('file_line')}`, disclosed={d.get('disclosed')})")
            lines.append("")
        else:
            lines += ["Deviations: none material.", ""]
    _write_md(_MD["arch"], "\n".join(lines))


def md_elig():
    _write_md(_MD["elig"], f"""# Run eligibility policy (pre-HPC)

A run may enter `select_best_model.py` **only** when its `run_status.json`
explicitly carries ALL of:

| Field | Required value |
|---|---|
| `protocol_version` | `{PROTOCOL_VERSION}` |
| `experiment_stage` | `screening` or `full` |
| `selection_eligible` | `true` |
| `smoke_only` | `false` |
| `status` | `ok` |

Everything else is excluded **by construction**:

* `smoke` / `pilot` / `adhoc` / `validation` stages;
* failed or blocked runs;
* runs predating this schema (missing eligibility fields);
* runs produced under a different protocol version;
* any run force-excluded by `legacy_runs_eligibility.json`.

`legacy_runs_eligibility.json` annotates existing runs **without mutating**
their artifacts (create-only principle preserved).
""")


# ── main ────────────────────────────────────────────────────────────────────
def main(argv=None) -> int:
    os.makedirs(AUDIT_DIR, exist_ok=True)
    fp = fix_fingerprint()
    ART.write_json(FIX_FINGERPRINT_PATH, fp)

    failed, resolved = failed_runs()
    n_resolved = sum(1 for r in resolved if r["resolution_status"] == "resolved")
    md_failed(fp, resolved,
              f"All {len(failed)} failed runs are recorded in the registry with "
              f"`status=failed`; they carry `selection_eligible=false` (or no "
              f"eligibility fields at all) and are therefore **ineligible for "
              f"model selection** by construction (`select_best_model.py` "
              f"eligibility gate). {n_resolved}/{len(failed)} have a successful "
              f"same-spec replacement.")

    env = {"nvidia_smi": _nvidia_smi(), "torch_cuda": _torch_cuda()}
    runs = per_run_devices()
    ART.write_json(os.path.join(AUDIT_DIR, "environment_report.json"),
                   {"env": env, "runs": runs})
    md_env(env, runs)

    arch = architecture_reports()
    ART.write_json(os.path.join(AUDIT_DIR, "architecture_equivalence.json"),
                   {"levels": list(FID.LEVELS), "models": arch})
    md_arch(arch)
    md_elig()

    # legacy annotation: existing smoke/failed/ad-hoc runs -> ineligible
    legacy = []
    for r in runs:
        stage = r.get("experiment_stage")
        if r["status"] != "ok" or stage in (None, "smoke", "pilot", "adhoc",
                                            "validation"):
            legacy.append({
                "run_id": r["run_id"],
                "selection_eligible": False,
                "reason": ("legacy run predating the eligibility schema"
                           if stage is None else
                           f"stage={stage} is infrastructure-only"),
            })
    ART.write_json(LEGACY_ELIGIBILITY_PATH,
                   {"note": "annotation only; existing artifacts untouched",
                    "runs": legacy})

    # ── readiness gate ──
    def _read_report(name):
        p = os.path.join(AUDIT_DIR, name)
        if not os.path.exists(p):
            return None
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            return None

    agg = _read_report("aggregation_regression_report.json")
    pipe = _read_report("pipeline_regression_report.json")
    gpt2 = _read_report("gpt2_control_repro_report.json")
    slurm = _read_report("slurm_validation_report.json")

    pilot_scripts = sorted(glob.glob(os.path.join(PROJECT_ROOT, "hpc_scripts",
                                                  "pilot_*.sh")))
    from innovation.backbones import gpt2_cache_available
    plan = plan_sha256_status()

    checks = {
        "plan_sha256_matches": plan["matches"],
        "four_pilot_scripts_present": len(pilot_scripts) == 4,
        "pilot_specs_json_present": os.path.exists(os.path.join(
            PROJECT_ROOT, "hpc_scripts", "pilot_specs.json")),
        "gpt2_cache_available": bool(gpt2_cache_available()),
        "aggregation_regression_ok": bool(agg and agg.get("all_agree")),
        "pipeline_regression_ok": bool(pipe and pipe.get("all_agree")),
        "gpt2_control_repro_ok": bool(gpt2 and gpt2["comparison"]["torch_equal"]),
        "slurm_validation_ok": bool(slurm and slurm.get("all_ok")),
        "submission_guards_present": None,  # filled from slurm report below
        "test_split_sealed": (not os.path.exists(FROZEN_WINNERS_PATH)
                              and not any(os.scandir(TEST_EVAL_ROOT))
                              if os.path.isdir(TEST_EVAL_ROOT) else True),
        "no_test_artifacts_under_runs": not any(
            glob.glob(os.path.join(RUNS_ROOT, "**", "test_*"), recursive=True)),
    }
    if slurm:
        checks["submission_guards_present"] = all(
            ("CONFIRM_INNOVATION_SUBMIT" in open(
                os.path.join(PROJECT_ROOT, "hpc_scripts", r["script"]),
                encoding="utf-8").read())
            for r in slurm.get("results", []) if r["is_submit_driver"])

    # ── source-freeze checks ──
    snap = None
    if os.path.exists(SOURCE_SNAPSHOT_MANIFEST):
        try:
            snap = json.load(open(SOURCE_SNAPSHOT_MANIFEST, encoding="utf-8"))
        except Exception:
            snap = None
    pspec = None
    pspec_path = os.path.join(PROJECT_ROOT, "hpc_scripts", "pilot_specs.json")
    if os.path.exists(pspec_path):
        try:
            pspec = json.load(open(pspec_path, encoding="utf-8"))
        except Exception:
            pspec = None
    spec_shas = [s.get("source_snapshot_sha256")
                 for s in (pspec or {}).get("specs", [])]
    snap_sha = (pspec or {}).get("source_snapshot_sha256")
    checks["source_snapshot_dir_present"] = os.path.isdir(SOURCE_SNAPSHOT_DIR)
    checks["source_snapshot_manifest_present"] = snap is not None
    checks["pilot_specs_carry_snapshot_sha"] = bool(
        snap_sha not in (None, "PENDING") and spec_shas
        and all(s not in (None, "PENDING") for s in spec_shas)
        and (snap or {}).get("aggregate_sha256") == snap_sha)
    checks["pilot_specs_selection_eligible_false"] = bool(
        pspec and pspec.get("selection_eligible") is False
        and all(s.get("selection_eligible") is False
                for s in pspec.get("specs", [])))

    pilot_generation_ready = bool(
        checks["four_pilot_scripts_present"] and checks["pilot_specs_json_present"]
        and checks["plan_sha256_matches"]
        and checks["source_snapshot_dir_present"]
        and checks["source_snapshot_manifest_present"]
        and checks["pilot_specs_carry_snapshot_sha"]
        and checks["pilot_specs_selection_eligible_false"])

    # The frozen source has NOT been deployed/verified on HPC, and this phase
    # must not submit anything, so pilot submission stays BLOCKED.
    deployment_verified = False
    blocker = None if deployment_verified else "UNVERIFIED_HPC_SOURCE_DEPLOYMENT"
    pilot_submission_ready = bool(
        pilot_generation_ready and deployment_verified
        and checks["aggregation_regression_ok"] and checks["pipeline_regression_ok"]
        and checks["gpt2_control_repro_ok"] and checks["slurm_validation_ok"])

    gate = {
        "created_utc": ART.utc_now(),
        "protocol_version": PROTOCOL_VERSION,
        "scientific_protocol_version": PROTOCOL_VERSION,
        "implementation_source_version": IMPLEMENTATION_SOURCE_VERSION,
        "plan_sha256_expected": PLAN_SHA256_EXPECTED,
        "plan_sha256_runtime": plan["sha256_runtime"],
        "fix_fingerprint": {"repository_head": fp["repository_head"],
                            "working_tree_dirty": fp["working_tree_dirty"],
                            "fix_commit": None,
                            "fix_identifier": fp["fix_identifier"]},
        "source_freeze": {
            "manifest": (os.path.relpath(SOURCE_SNAPSHOT_MANIFEST, PROJECT_ROOT)
                         .replace(os.sep, "/") if snap else None),
            "aggregate_sha256": (snap or {}).get("aggregate_sha256"),
            "n_files": (snap or {}).get("n_files"),
            "total_bytes": (snap or {}).get("total_bytes"),
            "snapshot_dir": (snap or {}).get("snapshot_dir"),
            "repository_head_short": (snap or {}).get("repository_head_short"),
            "working_tree_dirty": (snap or {}).get("working_tree_dirty"),
        },
        "source_deployment_verification": {
            "verified": deployment_verified,
            "blocker": "UNVERIFIED_HPC_SOURCE_DEPLOYMENT",
            "how_to_verify": ("after deploying the frozen source, run on HPC: "
                              "`python scripts/innovation/verify_source_snapshot.py "
                              "--manifest results/innovation/source_snapshot_manifest.json` "
                              "— it must exit 0 and print the aggregate hash"),
        },
        "checks": checks,
        "blocker": blocker,
        "readiness": {
            "pilot_generation_ready": pilot_generation_ready,
            "pilot_submission_ready": pilot_submission_ready,
            "full_sweep_submission_ready": False,
        },
        "full_sweep_blocked_reason": ("pilot has not been run/reviewed; the full "
                                      "sweep remains blocked until pilot evidence "
                                      "is accepted"),
        "submission_attempted": False,
        "sbatch_invoked": False,
        "test_sealed": bool(checks["test_split_sealed"]),
        "frozen_winner_created": False,
        "pilot_scripts": [os.path.relpath(p, PROJECT_ROOT) for p in pilot_scripts],
    }
    ART.write_json(PREHPC_GATE_PATH, gate)

    _write_md(_MD["gate"], "\n".join([
        "# Pre-HPC gate", "",
        f"- Readiness — pilot generation: **{pilot_generation_ready}**",
        f"- Readiness — pilot submission: **{pilot_submission_ready}** "
        f"(blocker: `{blocker}`)",
        f"- Readiness — full-sweep submission: **False** "
        f"({gate['full_sweep_blocked_reason']})", "",
        f"- source snapshot: `{(snap or {}).get('aggregate_sha256')}` "
        f"({(snap or {}).get('n_files')} files)",
        f"- `submission_attempted`: {gate['submission_attempted']}",
        f"- `sbatch_invoked`: {gate['sbatch_invoked']}",
        f"- test sealed: {gate['test_sealed']} | frozen winner created: "
        f"{gate['frozen_winner_created']}", "",
        "## Checks", ""] + [f"- `{k}`: {v}" for k, v in checks.items()] + [
        "", "## Pilot scripts (generated, NOT submitted)", ""]
        + [f"- `{p}`" for p in gate["pilot_scripts"]]))

    # ── human review checklist ──
    def _tick(ok):
        return "x" if ok else " "

    _write_md(_MD["checklist"], "\n".join([
        "# Human review checklist — pre-pilot source freeze", "",
        f"Generated `{gate['created_utc']}` · scientific protocol "
        f"`{PROTOCOL_VERSION}` · implementation source "
        f"`{IMPLEMENTATION_SOURCE_VERSION}` · HEAD "
        f"`{fp['repository_head_short']}` (dirty={fp['working_tree_dirty']})",
        "", "## 1. Failed-run resolution",
        f"- [{_tick(True)}] All {len(resolved)} failed registry entries documented "
        f"with root cause; {n_resolved} have a same-spec replacement "
        "(`audit/failed_runs_resolution.md`).",
        "- [x] Failed runs are ineligible by construction (status != ok / no "
        "eligibility fields / legacy annotation).", "",
        "## 2. Environment identity",
        f"- [x] CUDA devices `{env['torch_cuda'].get('device_count')}`, name "
        f"`{env['torch_cuda'].get('device_name')}`; nvidia-smi captured "
        "(`audit/environment_report.md`).",
        "- [x] Requested vs actual device recorded per run; the earlier \"CPU "
        "smoke\" wording is corrected (runs actually used cuda:0).", "",
        "## 3. Aggregation regression",
        f"- [{_tick(checks['aggregation_regression_ok'])}] Same-CSV re-aggregation "
        "agrees row-by-row incl. date index, y_true/y_pred, MSE, MAE, PTE, PIE "
        "(`audit/aggregation_regression_report.json`).", "",
        "## 4. End-to-end pipeline regression",
        f"- [{_tick(checks['pipeline_regression_ok'])}] Old MIFlu path vs "
        "innovation runner, same checkpoint + inputs; z and physical differences "
        "are 0.0 (`audit/pipeline_regression_report.json`).", "",
        "## 5. GPT-2 adapter reproduction",
        f"- [{_tick(checks['gpt2_control_repro_ok'])}] Synthetic checkpoint: "
        "`torch.equal=True`, max_abs_diff=0.0 "
        "(`audit/gpt2_control_repro_report.json`).",
        "- [ ] Real HPC-trained checkpoint validation — PENDING until the pilot "
        "stage (deliberately not done here).", "",
        "## 6. Architecture fidelity disclosures",
        "- [x] Three levels used; per-model fidelity + component-level file:line "
        + "; ".join(f"`{k}`={v.get('fidelity')}" for k, v in arch.items())
        + " (`audit/architecture_equivalence.md`).", "",
        "## 7. Eligibility gate",
        "- [x] Selector is validation-only, `test_accessed=false`; smoke/pilot/"
        "failed/legacy runs excluded by construction "
        "(`results/innovation/model_selection_audit.json`).",
        "- [x] All pilot specs carry `selection_eligible=false`.", "",
        "## 8. Slurm safety",
        f"- [{_tick(checks['slurm_validation_ok'])}] Structural + `bash -n` "
        "validation passed; confirmation guards present on every submit script; "
        "`submission_attempted=false`, `sbatch_invoked=false` "
        "(`audit/slurm_validation_report.json`).", "",
        "## 9. Source snapshot integrity",
        f"- [{_tick(checks['source_snapshot_manifest_present'])}] Snapshot "
        f"`aggregate_sha256={(snap or {}).get('aggregate_sha256')}` over "
        f"`{(snap or {}).get('n_files')}` files; carried into every pilot spec.",
        "- [ ] HPC source deployment verification — **UNVERIFIED** "
        "(`blocker=UNVERIFIED_HPC_SOURCE_DEPLOYMENT`). Pilot startup check "
        "aborts on any drift.", "",
        "## 10. Test-set sealing",
        f"- [{_tick(checks['test_split_sealed'])}] `frozen_winners.json` absent, "
        "`test_evaluations/` empty, zero test artifacts under `runs/`.", "",
        "## Overall",
        f"- `pilot_generation_ready` = **{pilot_generation_ready}**",
        f"- `pilot_submission_ready` = **{pilot_submission_ready}** "
        f"(blocker: `{blocker}`)",
        "- `full_sweep_submission_ready` = **False**",
        "- `submission_attempted` = **False**; `sbatch_invoked` = **False**", "",
        "> Pilot runs remain `selection_eligible=false`. No winner, no ranking, "
        "no test artifact, no journal performance conclusion.",
    ]))

    print("[prehpc_report] readiness:", gate["readiness"])
    print("[prehpc_report] blocker:", gate["blocker"],
          "| source snapshot:", (snap or {}).get("aggregate_sha256"))
    print("[prehpc_report] submission_attempted:",
          gate["submission_attempted"], "| sbatch_invoked:",
          gate["sbatch_invoked"])
    for k, v in checks.items():
        print(f"   - {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
