"""stage_v318_controller.py — stage the v3.18 controller bundle for upload."""
from __future__ import annotations

import ast
import json
import os

R = r"c:\Users\Asus\Desktop\FYP code\MLFlu"
U = r"C:\Users\Asus\upload\v318b"
os.makedirs(U, exist_ok=True)


def lf(src: str, dst: str, parse: bool = False) -> int:
    b = open(src, "rb").read().replace(b"\r\n", b"\n")
    if parse:
        ast.parse(b.decode("utf-8"))
    open(dst, "wb").write(b)
    has_cr = (b"\r" in b)
    print("  %-38s %7d bytes  CR=%s" % (os.path.basename(dst), len(b), has_cr))
    return len(b)


reg = json.loads(open(os.path.join(R, "results", "v3_clean", "runs",
                                   "complete_specs_598.json"),
                      encoding="utf-8").read())
order = [s for s in reg["specs"]
         if s.get("wave") == 1 and s.get("submittable")
         and s.get("executable_binding")]
order.sort(key=lambda s: s["order"])
inv = json.loads(open(r"C:\Users\Asus\inventory_205_final.json",
                      encoding="utf-8").read())
acc = [r["run_key"] for r in inv["rows"]]

open(os.path.join(U, "formal_execution_order_wave1.txt"), "w",
     encoding="utf-8", newline="").write(
         "".join(s["run_key"] + "\n" for s in order))
open(os.path.join(U, "accepted_keys.txt"), "w", encoding="utf-8",
     newline="").write("".join(k + "\n" for k in acc))
print(f"order={len(order)} accepted={len(acc)} "
      f"remaining={len(order) - len(set(acc))}")

lf(os.path.join(U, "formal_execution_order_wave1.txt"),
   os.path.join(U, "formal_execution_order_wave1.txt"))
lf(os.path.join(U, "accepted_keys.txt"), os.path.join(U, "accepted_keys.txt"))
lf(os.path.join(R, "scripts", "innovation", "finalize_row.py"),
   os.path.join(U, "finalize_row.py"), parse=True)
for f in ("v318_row_finalize.sh", "wave1_controller_v318.sh"):
    lf(os.path.join(R, "scripts", "v3_clean", f), os.path.join(U, f))

# the quota preflight parses `mmlsquota` (statvfs is useless on GPFS)
lf(os.path.join(R, "scripts", "v3_clean", "quota_preflight.py"),
   os.path.join(U, "quota_preflight.py"), parse=True)
