"""record_d15_repair.py — record the D15 (baseline no-checkpoint finalization)
fix: pre/post SHA-256 + a REAL unified diff, classified as
BEHAVIOR_NEUTRAL_DETERMINISTIC_BASELINE_NO_CHECKPOINT_FINALIZATION_FIX.

The pre-state of every FROZEN file is read from the v3.18 bundle (byte-exact);
a file absent from the v3.18 frozen set is recorded as NEW.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "results" / "v3_clean" / "implementation" / "bundle_a.zip"
OUT = ROOT / "results" / "v3_clean" / "preregistration"

FROZEN_CHANGED = [
    "scripts/innovation/storage_verification.py",
    "scripts/innovation/clean_gate.py",
]
FROZEN_NEW = [
    "scripts/innovation/baseline_finalize.py",
    "scripts/innovation/finalize_row.py",
]
CLASSIFICATION = ("BEHAVIOR_NEUTRAL_DETERMINISTIC_BASELINE_NO_CHECKPOINT"
                  "_FINALIZATION_FIX")


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha_bytes(p.read_bytes())


z = zipfile.ZipFile(BUNDLE)
pre_content = {}
for n in z.namelist():
    if n in FROZEN_CHANGED or n in FROZEN_NEW:
        pre_content[n] = z.read(n)

now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
records = []
diff_parts = []

for rel in FROZEN_CHANGED:
    pre = pre_content[rel].decode("utf-8")
    post = (ROOT / rel).read_text(encoding="utf-8")
    pre_h, post_h = sha_bytes(pre_content[rel]), sha_file(ROOT / rel)
    d = "".join(difflib.unified_diff(
        pre.splitlines(keepends=True), post.splitlines(keepends=True),
        fromfile=f"a/{rel}", tofile=f"b/{rel}"))
    records.append({"path": rel, "status": "modified",
                    "pre_sha256": pre_h, "post_sha256": post_h,
                    "diff_bytes": len(d.encode("utf-8"))})
    diff_parts.append(d)

for rel in FROZEN_NEW:
    post_h = sha_file(ROOT / rel)
    post = (ROOT / rel).read_text(encoding="utf-8")
    d = "".join(difflib.unified_diff(
        [], post.splitlines(keepends=True),
        fromfile=f"a/{rel} (absent in v3.18)", tofile=f"b/{rel}"))
    records.append({"path": rel, "status": "new",
                    "pre_sha256": None, "post_sha256": post_h,
                    "diff_bytes": len(d.encode("utf-8"))})
    diff_parts.append(d)

payload = {
    "generated_utc": now,
    "defect": "D15_DETERMINISTIC_BASELINE_NO_CHECKPOINT_FINALIZATION",
    "classification": CLASSIFICATION,
    "previous_version": "innov-v3.18-published-path-verification-hardening",
    "science_impact": "NONE (no model, loss, optimizer, early stopping, "
                     "checkpoint selection, data, split, scaler, prompt "
                     "statistics, metric, horizon, seed, matrix, "
                     "ablation/control semantics or endpoint hierarchy touched)",
    "files": records,
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "d15_repair_record.json").write_text(
    json.dumps(payload, indent=2), encoding="utf-8")
(OUT / "d15_repair.diff").write_text("".join(diff_parts), encoding="utf-8")

for r in records:
    print(f"{r['status']:8} {r['path']} pre={r['pre_sha256'] and r['pre_sha256'][:12]} "
          f"post={r['post_sha256'][:12]} diff={r['diff_bytes']}B")
print("total diff bytes", sum(r["diff_bytes"] for r in records))
print("classification", CLASSIFICATION)
