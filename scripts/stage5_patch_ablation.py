# -*- coding: utf-8 -*-
"""Thread --containment through train_ablation.py's train / export call sites."""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "scripts", "train_ablation.py")
s = io.open(P, encoding="utf-8").read()

reps = 0

# 1) call sites -> pass containment
s, n = re.subn(
    r'Xt, Yt, Xv, Yv, Xte, Yte = build_windows\(\s*\n?\s*data_dict\["data_norm"\], config\["T"\], L,\s*\n?\s*data_dict\["train_end"\], data_dict\["val_end"\]\)\s*\n',
    'Xt, Yt, Xv, Yv, Xte, Yte = build_windows(\n'
    '        data_dict["data_norm"], config["T"], L,\n'
    '        data_dict["train_end"], data_dict["val_end"], containment=containment)\n',
    s)
reps += n
print("call sites patched:", n)

# 2) make 'containment' available inside those functions: add a module-level
#    ACTIVE_CONTAINMENT that main() sets, used as the default.
if "ACTIVE_CONTAINMENT" not in s:
    s = s.replace('def build_windows(data_norm, T, L, train_end, val_end, containment="start"):',
                  'ACTIVE_CONTAINMENT = "start"   # Stage 5: set from --containment in main()\n\n\n'
                  'def build_windows(data_norm, T, L, train_end, val_end, containment="start"):', 1)
    reps += 1

# 3) give each patched function a containment argument defaulting to the active one
s, n = re.subn(r'def (train_rep|export_prediction_csv|train_one)\(([^)]*?)\):',
               lambda m: 'def %s(%s%s):' % (
                   m.group(1),
                   m.group(2).rstrip(),
                   (", containment=None" if "containment" not in m.group(2) else "")),
               s)
print("signatures touched:", n)

# 4) ensure containment resolves to the active value inside those functions
s = s.replace("containment=containment)", "containment=(containment or ACTIVE_CONTAINMENT))")
print("resolutions patched:", s.count("containment=(containment or ACTIVE_CONTAINMENT))"))

# 5) main() sets ACTIVE_CONTAINMENT from args
if "ACTIVE_CONTAINMENT = args.containment" not in s:
    s = s.replace("    # ---- Stage 5 A2 guard",
                  "    global ACTIVE_CONTAINMENT\n"
                  "    ACTIVE_CONTAINMENT = args.containment\n"
                  "    # ---- Stage 5 A2 guard", 1)
    print("main wiring added")

io.open(P, "w", encoding="utf-8").write(s)
print("written")
