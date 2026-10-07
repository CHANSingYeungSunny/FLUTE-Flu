"""d15_record.py — record D15 pre/post SHA-256 and a real unified diff."""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import time
from pathlib import Path

R = Path(r"c:\Users\Asus\Desktop\FYP code\MLFlu")
OUT = R / "results" / "v3_clean" / "d13"
OUT.mkdir(parents=True, exist_ok=True)

# (repo-relative name, local copy of the v3.14-deployed file, expected pre hash)
PAIRS = [
    ("compact_checkpoint.py",
     r"C:\Users\Asus\compact_checkpoint.py",
     "ca5c64ccd587d8fcca914ac8df0b24d9003f0672148c1ebee6ce33d609a9426c"),
    ("clean_gate.py",
     r"C:\Users\Asus\clean_gate.py",
     "1d3847b95edbfe36be09f0c6ce5904ece047d0cefc976033aa69cc218a572d3c"),
]

recs = {}
for name, before, expected in PAIRS:
    b = open(before, "rb").read()
    a = open(R / "scripts" / "innovation" / name, "rb").read()
    hb = hashlib.sha256(b).hexdigest()
    ha = hashlib.sha256(a).hexdigest()
    bl = b.decode("utf-8").replace("\r\n", "\n").splitlines(True)
    al = a.decode("utf-8").replace("\r\n", "\n").splitlines(True)
    diff = "".join(difflib.unified_diff(
        bl, al,
        fromfile="a/scripts/innovation/" + name,
        tofile="b/scripts/innovation/" + name))
    (OUT / f"d15_repair_{name.replace('.py', '')}.diff").write_text(
        diff, encoding="utf-8")
    recs[name] = {"pre_sha256": hb, "post_sha256": ha,
                  "pre_matches_v3_14_deployed": hb == expected,
                  "diff_bytes": len(diff.encode("utf-8")),
                  "diff_sha256": hashlib.sha256(diff.encode()).hexdigest()}
    print(f"[d15] {name}: pre={hb[:12]} match_v3_14={hb == expected} "
          f"post={ha[:12]} diff={len(diff.encode())}B")

(OUT / "d15_repair_record.json").write_text(json.dumps({
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "defect": "D15",
    "classification":
        "BEHAVIOR_NEUTRAL_GATE_STORAGE_PREDICATE_APPLICABILITY_FIX",
    "files": recs,
    "new_files": ["scripts/innovation/architecture_contract.py"],
    "scientific_behaviour_changed": False,
}, indent=2), encoding="utf-8")
print("[d15] record written")
