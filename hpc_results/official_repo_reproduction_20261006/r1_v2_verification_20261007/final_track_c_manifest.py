#!/usr/bin/env python3
"""
final_track_c_manifest.py — verify every required Track C deliverable exists,
then emit the master manifest with size + checksum + validation status.
CPU-only; run via sbatch.
"""
from __future__ import annotations

import hashlib
import os
import subprocess

B = "/gpfs1/home/sychan552/official_repo_reproduction_20261006/strict966_championship_20261007"

REQUIRED = [
    "TRACK_C_MASTER_CONTRACT.md", "TRACK_C_MODEL_IDENTITY.csv",
    "TRACK_C_CELL_CLASSIFICATION.csv", "STRICT_966_TRAIN_KEYS.csv",
    "STRICT_966_VALIDATION_KEYS.csv", "STRICT_966_TEST_KEYS.csv",
    "STRICT_966_KEY_MANIFEST.json", "STRICT_966_KEY_VALIDATION.md",
    "SEED42_EIGHT_MODEL_GATE_REPORT.md", "SEED42_EIGHT_MODEL_GATE_RESULTS.csv",
    "TRACK_C_MIFLU_RUN_MATRIX.csv",
    "TRACK_C_RESCORED_84_CELL_MANIFEST.csv", "TRACK_C_RESULTS_PER_CELL.csv",
    "TRACK_C_RESULTS_PER_SEED.csv", "TRACK_C_RESULTS_PER_HORIZON.csv",
    "TRACK_C_RESULTS_PER_MODEL.csv", "TRACK_C_TEST_MSE_RANKING.csv",
    "TRACK_C_TEST_MAE_RANKING.csv", "TRACK_C_PER_HORIZON_CHAMPIONS.csv",
    "TRACK_C_PER_SEED_RANKINGS.csv", "TRACK_C_LLM_NONLLM_GROUP_SUMMARY.csv",
    "TRACK_C_PAIRWISE_STATS_CORRECTED.csv", "TRACK_C_COST_SUMMARY.csv",
    "TRACK_C_CHECKPOINT_MANIFEST.csv", "TRACK_C_PREDICTION_MANIFEST.csv",
    "TRACK_C_CHAMPION_REPORT_ZH.md", "TRACK_C_CHAMPION_REPORT_EN.md",
    "TRACK_C_EXECUTION_LOG.md", "TRACK_C_RETRY_LOG.csv",
    "TRACK_C_SHA256_MANIFEST.txt", "TRACK_C_FILE_INTEGRITY_REPORT.md",
    "FINAL_DOCX_RENDER_AUDIT.md", "FINAL_DOCX_SOURCE_DATA_MANIFEST.csv",
    "FINAL_DOCX_SHA256.txt",
    "MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版.docx",
]
LEDGER = "manifests/TRACK_C_MIFLU_RESOURCE_LEDGER.csv"
REQUIRED.append(LEDGER)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def quota():
    try:
        r = subprocess.run(["mmlsquota", "--block-size=G"], capture_output=True,
                           text=True, timeout=60)
        return r.stdout
    except Exception as e:  # noqa: BLE001
        return f"error: {e}"


rows, missing = [], []
for rel in REQUIRED:
    p = os.path.join(B, rel)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        rows.append({"deliverable": rel, "bytes": os.path.getsize(p),
                     "sha256": sha(p), "validation_status": "PRESENT_NONEMPTY",
                     "path": p})
    else:
        missing.append(rel)
        rows.append({"deliverable": rel, "bytes": 0, "sha256": "",
                     "validation_status": "MISSING", "path": p})

with open(f"{B}/TRACK_C_DELIVERABLE_MANIFEST.csv", "w") as fh:
    fh.write("deliverable,bytes,sha256,validation_status,path\n")
    for r in rows:
        fh.write(f"{r['deliverable']},{r['bytes']},{r['sha256']},"
                 f"{r['validation_status']},{r['path']}\n")

# refresh the master checksum file over everything in the root
allf = sorted(f for f in os.listdir(B)
              if os.path.isfile(os.path.join(B, f))
              and f != "TRACK_C_SHA256_MANIFEST.txt")
with open(f"{B}/TRACK_C_SHA256_MANIFEST.txt", "w") as fh:
    for f in allf:
        fh.write(f"{sha(os.path.join(B, f))}  {f}\n")

q = quota()
print("=" * 78)
print("FINAL TRACK C DELIVERABLE VERIFICATION")
print("=" * 78)
print(f"required deliverables : {len(REQUIRED)}")
print(f"present and non-empty : {len(REQUIRED) - len(missing)}")
print(f"missing               : {len(missing)} -> {missing}")
print(f"root files hashed     : {len(allf)}")
print()
print("mmlsquota (authoritative):")
for line in q.splitlines():
    if line.split()[:1] and line.split()[0] in ("home", "scratch", "Filesystem"):
        print("  " + line)
print()
print("RESULT:", "ALL_DELIVERABLES_PRESENT" if not missing
      else "INCOMPLETE")