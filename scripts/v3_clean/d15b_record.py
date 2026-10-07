"""d15b_record.py — record D15b pre/post SHA-256 and real unified diffs."""
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
    ("architecture_contract.py", r"C:\Users\Asus\ac_v315.py",
     "cd1ccae09fc3341f20be8ea64713a1aa624e1914027d012152721b2cee990789"),
    ("compact_checkpoint.py", r"C:\Users\Asus\cc_v315.py",
     "0d97c7d14ea81fb267a5f3e6266249672d0e2807de463e9a3328c49d9c73d158"),
    ("clean_gate.py", r"C:\Users\Asus\cg_v315.py",
     "0ff4fc105aed0cf5b67de35f0ec7d558ea6ca70f8c9616f63dd9615347c8ef29"),
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
    (OUT / f"d15b_repair_{name.replace('.py', '')}.diff").write_text(
        diff, encoding="utf-8")
    recs[name] = {"pre_sha256": hb, "post_sha256": ha,
                  "pre_matches_v3_15_deployed": hb == expected,
                  "diff_bytes": len(diff.encode("utf-8")),
                  "diff_sha256": hashlib.sha256(diff.encode()).hexdigest()}
    print(f"[d15b] {name}: pre={hb[:12]} match_v3_15={hb == expected} "
          f"post={ha[:12]} diff={len(diff.encode())}B")

(OUT / "d15b_repair_record.json").write_text(json.dumps({
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "defect": "D15b",
    "classification":
        "BEHAVIOR_NEUTRAL_ARCHITECTURE_STORAGE_CONTRACT_AND_CANONICAL_HASH_FIX",
    "files": recs,
    "scientific_behaviour_changed": False,
    "compact_tensor_selection_changed": False,
}, indent=2), encoding="utf-8")
print("[d15b] record written")
