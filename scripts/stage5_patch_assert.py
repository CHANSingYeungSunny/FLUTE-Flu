# -*- coding: utf-8 -*-
"""Stage 5 — assert containment=strict at run time when A2_REQUIRE_STRICT=1,
and record the effective run configuration for every runner."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BLOCK = '''
    # ---- Stage 5 A2 guard: containment must be explicit and strict ----
    import os as _os
    _req = _os.environ.get("A2_REQUIRE_STRICT") == "1"
    if _req and getattr(args, "containment", "start") != "strict":
        raise SystemExit("[A2] A2_REQUIRE_STRICT=1 requires --containment strict, got %r"
                         % getattr(args, "containment", None))
    print("[A2] run_config containment=%s profile=%s horizon=%s seed=%s"
          % (getattr(args, "containment", "start"), getattr(args, "profile", None),
             getattr(args, "horizon", None), getattr(args, "seed", None)))
'''

TARGETS = {
    "train_miflu.py": '    set_seed(args.seed)\n',
    "train_ablation.py": None,
    "train_nlinear_966.py": None,
    "train_naive_966.py": None,
}

for name in TARGETS:
    p = os.path.join(ROOT, "scripts", name)
    with io.open(p, "r", encoding="utf-8") as f:
        src = f.read()
    if "A2_REQUIRE_STRICT" in src:
        print("%-22s already patched" % name)
        continue
    # insert right after args = ...parse_args() line
    marker = None
    for line in src.split("\n"):
        s = line.strip()
        if s.startswith("args = ap.parse_args()") or s.startswith("args = parser.parse_args()"):
            marker = line
            break
    if marker is None:
        print("%-22s MARKER NOT FOUND" % name)
        continue
    src = src.replace(marker, marker + BLOCK, 1)
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(src)
    print("%-22s patched" % name)
