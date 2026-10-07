"""stage_v319_controller.py — stage the v3.19 controller bundle for upload.

Unlike v3.18, `finalize_row.py` is NOT copied here: it is the FROZEN
v3.19 baseline-aware implementation inside v3_clean14, and the finalize
wrapper calls it in place. The order is regenerated from the immutable
registry (verified byte-identical to the remote _v318d order); the accepted
set is the remote 320-key list pulled verbatim.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess

R = r"c:\Users\Asus\Desktop\FYP code\MLFlu"
SRC_ACC = r"C:\Users\Asus\upload\v319\accepted_keys.txt"
U = r"C:\Users\Asus\upload\v319c"
os.makedirs(U, exist_ok=True)


def lf(src: str, dst: str, parse: bool = False) -> str:
    b = open(src, "rb").read().replace(b"\r\n", b"\n")
    if parse:
        ast.parse(b.decode("utf-8"))
    open(dst, "wb").write(b)
    return hashlib.sha256(b).hexdigest()


def bash_n(path: str) -> bool:
    # bash does not exist on the Windows staging host; this is verified on the
    # remote HPC node during the static audit (step 11).
    return None


reg = json.load(open(os.path.join(R, "results", "v3_clean", "runs",
                                   "complete_specs_598.json"), encoding="utf-8"))
order = [s for s in reg["specs"]
         if s.get("wave") == 1 and s.get("submittable")
         and s.get("executable_binding")]
order.sort(key=lambda s: s["order"])

acc = [ln.rstrip("\n").rstrip("\r")
       for ln in open(SRC_ACC, encoding="utf-8") if ln.strip()]
acc_set = set(acc)
remaining = [s["run_key"] for s in order if s["run_key"] not in acc_set]
first = remaining[0]

open(os.path.join(U, "formal_execution_order_wave1.txt"), "w",
     encoding="utf-8", newline="").write(
         "".join(s["run_key"] + "\n" for s in order))
open(os.path.join(U, "accepted_keys.txt"), "w", encoding="utf-8",
     newline="").write("".join(k + "\n" for k in acc))

print(f"order={len(order)} accepted={len(acc)} remaining={len(remaining)}")
print(f"first_unaccepted={first}")

manifests = {}
for src, dst, parse in (
    (os.path.join(U, "formal_execution_order_wave1.txt"),
     os.path.join(U, "formal_execution_order_wave1.txt"), False),
    (os.path.join(U, "accepted_keys.txt"),
     os.path.join(U, "accepted_keys.txt"), False),
    (os.path.join(R, "scripts", "v3_clean", "v319_row_finalize.sh"),
     os.path.join(U, "v319_row_finalize.sh"), False),
    (os.path.join(R, "scripts", "v3_clean", "wave1_controller_v319.sh"),
     os.path.join(U, "wave1_controller_v319.sh"), False),
    (os.path.join(R, "scripts", "v3_clean", "wave1_launch_v319.sh"),
     os.path.join(U, "wave1_launch_v319.sh"), False),
    (os.path.join(R, "scripts", "v3_clean", "quota_preflight.py"),
     os.path.join(U, "quota_preflight.py"), True),
):
    h = lf(src, dst, parse)
    manifests[os.path.basename(dst)] = h
    print(f"  {os.path.basename(dst):34s} sha={h[:16]}…")

json.dump({"version": "innov-v3.19-baseline-no-checkpoint-finalization",
           "first_unaccepted": first, "files": manifests,
           "bash_n": "verify on remote HPC node"},
          open(os.path.join(U, "controller_manifest.json"), "w"),
          indent=2, sort_keys=True)
print("staged 6 files; bash -n deferred to remote static audit")
