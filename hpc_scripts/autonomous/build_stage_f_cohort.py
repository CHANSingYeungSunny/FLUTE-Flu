"""build_stage_f_cohort.py — reconstruct the pre-registered Stage F cohort from
immutable orchestration provenance (NOT performance). Read-only.

Evidence chain: stage_plan.json (F expansion) -> job_ledger.csv (stage=F rows,
job_id, spec, submitted_utc) -> Slurm worker log line `[runner] <run_id>`
(job -> run artifact link) -> registry_v2.csv (checkpoint/source hashes).

Writes results/innovation/governance/stage_provenance/*.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AC = os.path.join(ROOT, "results", "innovation", "autonomous_completion")
INN = os.path.join(ROOT, "results", "innovation")
OUT = os.path.join(INN, "governance", "stage_provenance")

PLAN = json.load(open(os.path.join(AC, "stage_plan.json"), encoding="utf-8"))
LEDGER = list(csv.DictReader(open(os.path.join(AC, "job_ledger.csv"), encoding="utf-8")))
REG = {r["run_id"]: r for r in csv.DictReader(open(os.path.join(INN, "registry_v2.csv"),
                                                   encoding="utf-8"))}
RUNNER = os.path.join(INN, "_runner_lines.txt")
FHASH = os.path.join(INN, "_stage_f_file_hashes.json")
STAGES = {s["key"]: s for s in PLAN.get("stages", [])}

SEV = "8941335bbf58a213d2269f20a72bdb75761d290a017cd937ddc09361175759be"  # v2.9 at reconstruction


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8", newline="\n").write(text)


def _wjson(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w", encoding="utf-8"), indent=2)


def _sha(path):
    h = hashlib.sha256()
    h.update(open(path, "rb").read())
    return h.hexdigest()


# job_id -> run_id from worker logs
job2run = {}
for line in open(RUNNER, encoding="utf-8", errors="replace"):
    m = re.search(r"slurm_(\d+)_innovation_worker\.sh\.out:\[runner\] (national-\S+)", line)
    if m:
        job2run.setdefault(m.group(1), m.group(2))

# Stage F expected cells (model, enc, fusion, horizon, seed)
e = STAGES["F"]["expand"]
F_cells = [(m, enc, fu, L, s) for m in e["models"] for enc in e["text_encoders"]
           for fu in e["fusions"] for L in e["horizons"] for s in e["seeds"]]

led_F = [r for r in LEDGER if r.get("stage") == "F"]
led_by_notes = {r.get("notes", ""): r for r in led_F}
fh = json.load(open(FHASH, encoding="utf-8")) if os.path.exists(FHASH) else {}

cohort, unresolved = [], []
for (m, enc, fu, L, s) in F_cells:
    key = "KEY=F|%s|%s|%s|L%d|s%d" % (m, enc, fu, L, s)
    row = led_by_notes.get(key)
    if not row or row.get("state") != "COMPLETED":
        unresolved.append({"cell": [m, L, s], "reason": "no completed F ledger row"})
        continue
    jid = row.get("job_id", "")
    rid = job2run.get(jid)
    if not rid:
        unresolved.append({"cell": [m, L, s], "job_id": jid,
                           "reason": "no job->run mapping in worker log"})
        continue
    reg = REG.get(rid, {})
    cohort.append({
        "model_key": m, "horizon": L, "seed": s, "run_id": rid, "job_id": jid,
        "source_version": reg.get("implementation_source_version", ""),
        "source_hash": reg.get("source_snapshot_sha256", ""),
        "checkpoint_sha256": reg.get("checkpoint_sha256", ""),
        "validation_prediction_sha256": fh.get(rid, {}).get("val_pred_sha", ""),
        "resolved_config_sha256": fh.get(rid, {}).get("config_sha", ""),
        "ledger_row_or_evidence_reference":
            "job_ledger.csv stage=F job_id=%s; worker log slurm_%s_innovation_worker.sh.out"
            % (jid, jid),
        "provenance_decision": "STAGE_F_FULL_EVALUATION",
    })

# annotation: classify every `full`-labelled run by its ledger stage
stage_of_job = {r["job_id"]: r["stage"] for r in LEDGER if r.get("stage")}
MAP = {"F": "STAGE_F_FULL_EVALUATION", "G": "STAGE_G_TEXT_OR_FUSION_ABLATION",
       "H": "STAGE_H_LLM_OR_TSFM", "I": "STAGE_I_ROBUSTNESS_OR_RESOURCE",
       "J": "STAGE_J_AUC_SEARCH_EFFICIENCY"}
annotation = []
for rid, reg in REG.items():
    jid = ""
    for j, rr in job2run.items():
        if rr == rid:
            jid = j
            break
    sem = MAP.get(stage_of_job.get(jid, ""), "UNRESOLVED_STAGE_PROVENANCE")
    annotation.append({"run_id": rid, "job_id": jid, "historical_label": "full",
                       "corrected_semantic_stage": sem})

# baseline cohort (MIFlu control): NOT part of the Stage-F matrix, but the
# champion rule needs it for per-horizon normalisation. Provenance: stage H rows.
baseline_cohort = []
for r in LEDGER:
    if r.get("stage") != "H" or r.get("model_key") != "gpt2_miflu":
        continue
    jid = r.get("job_id", "")
    rid = job2run.get(jid)
    if not rid:
        continue
    baseline_cohort.append({
        "model_key": "gpt2_miflu",
        "horizon": int(r["horizon"]) if str(r.get("horizon", "")).isdigit() else None,
        "seed": int(r["seed"]) if str(r.get("seed", "")).isdigit() else None,
        "run_id": rid, "job_id": jid,
        "provenance_decision": "STAGE_H_LLM_OR_TSFM_BASELINE"})

# Gate
cells = {(c["model_key"], c["horizon"], c["seed"]) for c in cohort}
dups = len(cohort) - len(cells)
per_model = {}
for c in cohort:
    per_model.setdefault(c["model_key"], set()).add((c["horizon"], c["seed"]))

gate = {
    "expected_cells": 160, "resolved_stage_f_cells": len(cohort),
    "missing_cells": 160 - len(cohort), "duplicate_cells": dups,
    "unresolved_cells": len(unresolved),
    "test_access_count": 0, "test_artifact_count": 0,
    "per_model_cells": {m: len(v) for m, v in per_model.items()},
    "jobs_without_run_mapping": sum(1 for r in led_F if r.get("job_id") not in job2run),
    "baseline_cohort_size": len(baseline_cohort),
    "baseline_horizons": sorted({b["horizon"] for b in baseline_cohort}),
    "cohort_lawful": bool(len(cohort) == 160 and dups == 0 and not unresolved),
}
_wjson(os.path.join(OUT, "provenance_reconstruction_audit.json"), gate)

_wjson(os.path.join(OUT, "stage_f_cohort_manifest.json"), {
    "annotation_version": "v1", "selection_scope": "stage_f_only",
    "scientific_protocol_version": "innov-v2.0",
    "implementation_source_version": "innov-v2.9",
    "source_evidence_hashes": {"source_snapshot_aggregate_sha256": SEV},
    "models": e["models"], "horizons": e["horizons"], "seeds": e["seeds"],
    "expected_cells": 160, "cohort_size": len(cohort),
    "cohort": cohort,
    "baseline_cohort": baseline_cohort,
    "baseline_cohort_size": len(baseline_cohort),
})
_wcsv = lambda p, cols, rows: (os.makedirs(os.path.dirname(p), exist_ok=True),
                               open(p, "w", encoding="utf-8", newline="").write(
                                   "\n".join([",".join(cols)]
                                             + [",".join(str(r.get(c, "")) for c in cols)
                                                for r in rows]) + "\n"))
_wcsv(os.path.join(OUT, "stage_f_cohort_manifest.csv"),
      ["model_key", "horizon", "seed", "run_id", "job_id", "source_hash",
       "checkpoint_sha256", "provenance_decision"],
      [{k: c.get(k) for k in ("model_key", "horizon", "seed", "run_id", "job_id",
                              "source_hash", "checkpoint_sha256", "provenance_decision")}
       for c in cohort])
_wjson(os.path.join(OUT, "stage_provenance_annotation.json"), {
    "annotation_version": "v1", "scientific_protocol_version": "innov-v2.0",
    "implementation_source_version": "innov-v2.9",
    "selection_scope": "stage_f_only", "historical_label": "full",
    "n_runs": len(annotation), "annotation": annotation})
_wcsv(os.path.join(OUT, "stage_provenance_annotation.csv"),
      ["run_id", "job_id", "historical_label", "corrected_semantic_stage"], annotation)

_w(os.path.join(OUT, "provenance_evidence_map.md"), "\n".join([
    "# Stage F provenance evidence map", "",
    "1. `stage_plan.json` — pre-execution Stage F expansion (4 models x 4 horizons x 10 seeds).",
    "2. `job_ledger.csv` — append-only rows with `stage=F` (job_id, spec, submitted_utc).",
    "3. Slurm worker logs `hpc_results/innovation/logs/slurm_<job_id>_innovation_worker.sh.out`",
    "   — the `[runner] <run_id>` line is the EXACT job->run artifact link.",
    "4. `registry_v2.csv` — checkpoint / source hashes per run.",
    "",
    "No MSE/MAE/PTE/PIE/epoch or any performance value is used for membership.", "",
    "- jobs with a resolved job->run mapping: %d" % len(job2run),
    "- Stage F ledger rows: %d; resolved to runs: %d; unresolved: %d"
    % (len(led_F), len(cohort), len(unresolved)),
]))
_w(os.path.join(OUT, "provenance_reconstruction_audit.md"), "\n".join([
    "# Stage F provenance reconstruction audit", "",
    "| metric | value |", "|---|---|",
] + ["| %s | %s |" % (k, v) for k, v in gate.items() if k != "per_model_cells"]
  + ["", "per-model cells: %s" % gate["per_model_cells"]]))

print("[cohort] lawful=%s resolved=%d/160 dups=%d unresolved=%d"
      % (gate["cohort_lawful"], len(cohort), dups, len(unresolved)))
print("[cohort] per-model cells:", gate["per_model_cells"])
if unresolved[:3]:
    print("[cohort] unresolved examples:", unresolved[:3])
