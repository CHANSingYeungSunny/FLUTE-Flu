"""build_d13_inventory.py — D13 storage inventory, classification and the
create-only deletion-candidate manifest.

Inputs (retrieved from the cluster, lightweight stat/du output only):
  C:\\Users\\Asus\\d13\\durable_entries.tsv   size<TAB>name   (durable/screening)
  C:\\Users\\Asus\\d13\\big_files.tsv         size<TAB>path   (>50 MiB, all of durable)
  C:\\Users\\Asus\\d13\\scratch_roots.tsv     size<TAB>name   (scratch top level)

NOTHING IS DELETED OR MOVED BY THIS SCRIPT. It only writes inventory and a
create-only candidate manifest under results/v3_clean/d13/.
"""
from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "v3_clean" / "d13"
OUT.mkdir(parents=True, exist_ok=True)
SRC = Path(r"C:\Users\Asus\d13")
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

GIB = 1024 ** 3


def rd_tsv(p: Path):
    rows = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        a, _, b = line.partition("\t")
        if not a.strip().isdigit():
            continue
        rows.append((int(a), b))
    return rows


durable = rd_tsv(SRC / "durable_entries.tsv")
big = rd_tsv(SRC / "big_files.tsv")
scratch = rd_tsv(SRC / "scratch_roots.tsv")

DUR = "/home/sychan552/innovation_durable"
SCR = "/gpfs1/scratch/sychan552"
SCREEN = f"{DUR}/screening"

# ── classify every durable/screening entry ────────────────────────────────
WAVE1_KEY = re.compile(r"^[a-z_]+__[a-z0-9_]+__L\d+__(seed\d+|seedna)__w1$")
PARTIAL_KEY = "primary__qwen_time_llm__L24__seed46__w1"

# governance files inside screening/ that carry the OLD (v3.3) line's audit
LEGACY_GOVERNANCE = {
    "all_model_observed_ranking.csv", "group_a_observed_ranking.csv",
    "group_b_observed_ranking.csv", "proposed_full_validation_candidates.json",
    "proposed_full_validation_candidates_v2.json",
    "restoration_verification.json", "durable_storage_copy_status.csv",
    "candidate_serialization_correction_audit.json", "evidence_pack.sha256",
    "_controller", "figures", "baselines",
}

entries = []
for size, name in sorted(durable, key=lambda r: -r[0]):
    p = f"{SCREEN}/{name}"
    if name == PARTIAL_KEY:
        cls, action = "H_PARTIAL_FAILED_COPY", "quarantine_then_delete"
        why = ("durable copy was interrupted at ~88% by the home quota; the "
               "run itself COMPLETED 0:0 and its scratch artifacts are intact")
    elif WAVE1_KEY.match(name):
        cls, action = ("B_CURRENT_WAVE1_ACCEPTED_DURABLE_EVIDENCE",
                       "preserve_then_convert_to_compact_in_v3_13")
        why = "accepted Wave-1 durable evidence (must not be lost)"
    elif name.startswith("screening_"):
        cls, action = "E_SUPERSEDED_MIFLU_BULK_REGENERABLE", \
            "quarantine_large_weights_keep_small_evidence"
        why = ("v3.3-era screening row (superseded by the clean-v3 line); its "
               "bulk is a per-row copy of the frozen backbone")
    elif name in LEGACY_GOVERNANCE:
        cls, action = "D_SUPERSEDED_MIFLU_EVIDENCE_REQUIRED_FOR_AUDIT", \
            "preserve"
        why = "v3.3-era governing record; tiny and audit-relevant"
    else:
        cls, action = "G_SYSTEM_SHARED_OR_UNKNOWN", "preserve_report_for_review"
        why = "not proven to be superseded or regenerable"
    entries.append({"path": p, "name": name, "bytes": size,
                    "gib": round(size / GIB, 3), "classification": cls,
                    "proposed_action": action, "rationale": why})

# ── scratch roots ─────────────────────────────────────────────────────────
SCRATCH_CLASS = {
    "CHATTIME": ("F_OTHER_PROJECT_CONFIRMED_USER_OWNED", "preserve",
                 "the original reproduction project; never touched"),
    "MLFLU": ("F_OTHER_PROJECT_CONFIRMED_USER_OWNED", "preserve",
              "earlier MIFlu working tree"),
    "innovation_deploy_root_v3_clean6": (
        "A_ACTIVE_CURRENT_WAVE1_REQUIRED", "preserve",
        "the ACTIVE v3.12 deployment root of the running Wave-1"),
    "innovation_deploy_root_v3_clean5": (
        "D_SUPERSEDED_MIFLU_EVIDENCE_REQUIRED_FOR_AUDIT", "preserve",
        "v3.12 deployment whose Gate 570846 passed 19/19 (historical Gate "
        "evidence)"),
    "innovation_deploy_root_v3_clean4": (
        "D_SUPERSEDED_MIFLU_EVIDENCE_REQUIRED_FOR_AUDIT", "preserve",
        "v3.10/v3.11 deployment + Gate 569016/570452 evidence"),
    "innovation_deploy_root_v3_clean3": (
        "D_SUPERSEDED_MIFLU_EVIDENCE_REQUIRED_FOR_AUDIT", "preserve",
        "v3.9 deployment + Gate 568988 evidence"),
}
scratch_rows = []
for size, name in sorted(scratch, key=lambda r: -r[0]):
    cls, action, why = SCRATCH_CLASS.get(
        name, ("E_SUPERSEDED_MIFLU_BULK_REGENERABLE",
               "review_before_quarantine",
               "superseded deployment root; bulk = run artifacts/weights"))
    scratch_rows.append({"path": f"{SCR}/{name}", "name": name, "bytes": size,
                         "gib": round(size / GIB, 3), "classification": cls,
                         "proposed_action": action, "rationale": why})

# ── big-file candidates (weights only; manifests/logs are never candidates) ─
WEIGHT_SUFFIXES = (".pt", ".pth", ".safetensors", ".bin")
cand = []
for size, path in sorted(big, key=lambda r: -r[0]):
    is_w = path.endswith(WEIGHT_SUFFIXES)
    in_wave1 = "/screening/" in path and WAVE1_KEY.match(
        path.split("/screening/")[1].split("/")[0])
    if not is_w:
        continue
    if in_wave1:
        if PARTIAL_KEY in path:
            cand.append({
                "path": path, "bytes": size, "gib": round(size / GIB, 3),
                "classification": "H_PARTIAL_FAILED_COPY",
                "action": "quarantine_then_delete",
                "proof": "interrupted durable copy of a COMPLETED run; "
                         "scratch source is intact and restorable"})
        # accepted Wave-1 weights are converted, not deleted, in v3.13
    else:
        cand.append({
            "path": path, "bytes": size, "gib": round(size / GIB, 3),
            "classification": "E_SUPERSEDED_MIFLU_BULK_REGENERABLE",
            "action": "quarantine_large_weights_keep_small_evidence",
            "proof": "v3.3-era per-row copy of a frozen backbone that also "
                     "exists in the shared HF cache; manifests/metrics/"
                     "predictions/logs are preserved"})

# ── capacity model ────────────────────────────────────────────────────────
# observed per-row durable checkpoint footprint (full policy) by family
FAMILY_FULL_GIB = {"nlinear": 0.002, "dlinear": 0.002, "patchtst": 0.005,
                   "itransformer": 0.006, "gpt2_miflu": 0.31, "qwen_time_llm": 5.75,
                   "calf_llm": 0.47, "timecma_llm": 0.47, "baseline": 0.001}
# remaining rows in the frozen Wave-1 order (after the 205 already submitted)
REMAIN = {"qwen_time_llm": 35, "calf_llm": 40, "timecma_llm": 40,
          "gpt2_miflu": 252, "baseline": 8}
full_policy = {k: round(v * FAMILY_FULL_GIB[k], 1) for k, v in REMAIN.items()}

home_now = 101.0
legacy_free = round(sum(e["bytes"] for e in entries
                        if e["classification"] == "E_SUPERSEDED_MIFLU_BULK_REGENERABLE")
                    / GIB, 1)
partial_free = round(sum(e["bytes"] for e in entries
                         if e["classification"] == "H_PARTIAL_FAILED_COPY")
                     / GIB, 1)
wave1_big = round(sum(s for s, p in big
                      if "/screening/" in p and WAVE1_KEY.match(
                          p.split("/screening/")[1].split("/")[0])) / GIB, 1)

model = {
    "home_used_gib_now": home_now,
    "home_hard_limit_gib": 100.0,
    "home_soft_quota_gib": 50.0,
    "durable_total_gib": 88.0,
    "freed_if_legacy_weights_quarantined_gib": legacy_free,
    "freed_if_partial_copy_quarantined_gib": partial_free,
    "wave1_big_weights_gib": wave1_big,
    "remaining_rows_full_policy_gib": full_policy,
    "remaining_rows_full_policy_total_gib": round(sum(full_policy.values()), 1),
    "verdict": ("INFEASIBLE under the current full-copy policy: the remaining "
                "375 rows would need ~317 GiB against a 100 GiB home hard "
                "limit. The compact-checkpoint policy is MANDATORY, and even "
                "then the Wave-1 durable footprint must first be reduced."),
    "safety_margin_required_gib": max(20.0, 0.2 * 100.0),
}

# ── write the artifacts ───────────────────────────────────────────────────
(OUT / "storage_inventory.json").write_text(json.dumps({
    "generated_utc": NOW, "host": "burgundy",
    "durable_root": DUR, "scratch_root": SCR,
    "n_durable_entries": len(entries), "n_scratch_roots": len(scratch_rows),
    "n_big_files": len(big),
    "durable_entries": entries, "scratch_roots": scratch_rows,
    "capacity_model": model,
}, indent=2), encoding="utf-8")

with open(OUT / "storage_inventory.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["path", "bytes", "gib", "classification", "proposed_action",
                "rationale"])
    for r in entries + scratch_rows:
        w.writerow([r["path"], r["bytes"], r["gib"], r["classification"],
                    r["proposed_action"], r["rationale"]])

(OUT / "deletion_candidate_manifest.json").write_text(json.dumps({
    "generated_utc": NOW,
    "policy": "create-only; dry-run first; quarantine before delete; never "
              "delete unknown/shared/active/audit-required material",
    "quarantine_root_proposed": f"{SCR}/_d13_quarantine",
    "n_candidates": len(cand),
    "candidate_bytes": sum(c["bytes"] for c in cand),
    "candidate_gib": round(sum(c["bytes"] for c in cand) / GIB, 2),
    "candidates": cand,
    "explicitly_preserved": {
        "wave1_accepted_rows": 205,
        "job_571472_scratch": "preserved and used for recovery, not retrained",
        "canonical_data_and_bundles": "preserved",
        "gate_and_controller_evidence": "preserved",
        "chattime_and_other_project": "preserved",
        "unknown_paths": "preserved and reported for review",
    },
}, indent=2), encoding="utf-8")

md = [f"# D13 storage inventory ({NOW})", "",
      f"- durable root: `{DUR}` — **{len(entries)}** entries",
      f"- scratch root: `{SCR}` — **{len(scratch_rows)}** top-level entries",
      f"- files > 50 MiB: **{len(big)}**", "",
      "## Capacity model", ""]
for k, v in model.items():
    md.append(f"- `{k}` = {v}")
md += ["", "## Deletion candidates (quarantine first, delete after)", "",
       f"- **{len(cand)}** candidates, "
       f"**{round(sum(c['bytes'] for c in cand) / GIB, 2)} GiB**", "",
       "| size GiB | class | path |", "|---|---|---|"]
for c in cand[:60]:
    md.append(f"| {c['gib']} | {c['classification']} | `{c['path']}` |")
md += ["", "> No file has been deleted or moved. This manifest is create-only.",
       ""]
(OUT / "storage_inventory.md").write_text("\n".join(md), encoding="utf-8")

print(f"[d13] durable entries={len(entries)} scratch roots={len(scratch_rows)} "
      f"big files={len(big)}")
print(f"[d13] candidates={len(cand)} "
      f"{round(sum(c['bytes'] for c in cand)/GIB,2)} GiB")
print(f"[d13] legacy quarantine would free "
      f"{model['freed_if_legacy_weights_quarantined_gib']} GiB; "
      f"partial copy {model['freed_if_partial_copy_quarantined_gib']} GiB")
print(f"[d13] remaining 375 rows under FULL policy = "
      f"{model['remaining_rows_full_policy_total_gib']} GiB -> INFEASIBLE")
