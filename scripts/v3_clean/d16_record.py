"""d16_record.py — record D16 pre/post SHA-256 and real unified diffs."""
from __future__ import annotations

import difflib
import hashlib
import json
import time
from pathlib import Path

R = Path(r"c:\Users\Asus\Desktop\FYP code\MLFlu")
OUT = R / "results" / "v3_clean" / "d13"
OUT.mkdir(parents=True, exist_ok=True)

PAIRS = [
    ("clean_gate.py", r"C:\Users\Asus\cg_v317.py",
     "ed993ad7868fe8239aeb3158e3d78f41e30b20e9eb29e0a6807f3e08c5e874e9"),
]

recs = {}
for name, before, expected in PAIRS:
    b = open(before, "rb").read()
    a = open(R / "scripts" / "innovation" / name, "rb").read()
    hb, ha = hashlib.sha256(b).hexdigest(), hashlib.sha256(a).hexdigest()
    diff = "".join(difflib.unified_diff(
        b.decode("utf-8").replace("\r\n", "\n").splitlines(True),
        a.decode("utf-8").replace("\r\n", "\n").splitlines(True),
        fromfile="a/scripts/innovation/" + name,
        tofile="b/scripts/innovation/" + name))
    (OUT / f"d16_repair_{name.replace('.py', '')}.diff").write_text(
        diff, encoding="utf-8")
    recs[name] = {"pre_sha256": hb, "post_sha256": ha,
                  "pre_matches_v3_16_deployed": hb == expected,
                  "diff_bytes": len(diff.encode("utf-8")),
                  "diff_sha256": hashlib.sha256(diff.encode()).hexdigest()}
    print(f"[d16] {name}: pre={hb[:12]} match_v3_16={hb == expected} "
          f"post={ha[:12]} diff={len(diff.encode())}B")

new_files = ["storage_verification.py", "same_source_invariant.py"]
(OUT / "d16_repair_record.json").write_text(json.dumps({
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "defect": "D16",
    "classification":
        "BEHAVIOR_NEUTRAL_GATE_VERIFICATION_WIRING_AND_SAME_SOURCE_INVARIANT_FIX",
    "files": recs,
    "new_files": new_files,
    "scientific_behaviour_changed": False,
    "compact_tensor_selection_changed": False,
    "note": ("the verdict now reads ONLY the typed StorageVerification; a "
             "missing required check fails closed with "
             "MISSING_REQUIRED_STORAGE_CHECK"),
}, indent=2), encoding="utf-8")
print("[d16] record written")
