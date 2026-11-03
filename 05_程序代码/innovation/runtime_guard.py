"""
runtime_guard.py — the original reproduction repository is OUT of the execution path.
===============================================================================

The 2026-09-15 incident extracted an innovation bundle into the original
reproduction repository. That repository is now permanently excluded from the
innovation execution path:

    /home/sychan552/scratch/CHATTIME/Chattime

Any innovation job whose Python source resolves under it must fail with

    FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT

The comparison is made on RESOLVED paths (symlinks and `..` collapsed with
`os.path.realpath`, separators normalised to `/`), never on a raw unnormalised
string prefix test. Directory containment is checked as `<banned>/…`.

USAGE
-----
    python scripts/innovation/runtime_guard.py [--deployment-root ROOT]
    # exit 0 = clean; exit 2 = FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from innovation.paths import (BANNED_RUNTIME_MARKERS,  # noqa: E402
                              BANNED_RUNTIME_ROOT)

import os  # noqa: E402
import posixpath  # noqa: E402
import sys  # noqa: E402

FAILURE_CODE = "FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT"

# modules that make up the innovation runtime; their __file__ must be clean
WATCHED_MODULES = ("innovation", "configs", "scaler_utils", "miflu_model",
                   "textual_embedder", "compute_miflu_indicators",
                   "cdc_calendar", "early_stopping")


def _norm(p: str) -> str:
    return posixpath.normpath(str(p).replace("\\", "/"))


def resolved(p: str) -> str:
    """Fully resolved path (symlinks + '..' collapsed), always '/' separated."""
    try:
        return os.path.realpath(os.path.abspath(str(p))).replace("\\", "/")
    except Exception:
        return _norm(p)


def banned_resolved() -> str:
    return _norm(BANNED_RUNTIME_ROOT)


def is_banned(path: str) -> bool:
    r = resolved(path)
    b = banned_resolved()
    if r == b or r.startswith(b + "/"):
        return True
    return any(m in r for m in BANNED_RUNTIME_MARKERS)


def _candidate_paths(deployment_root: str | None = None) -> list[tuple[str, str]]:
    """(label, path) pairs that must not resolve into the banned repository."""
    out: list[tuple[str, str]] = []
    for i, p in enumerate(sys.path):
        if p:
            out.append((f"sys.path[{i}]", p))
    for name, mod in sorted(sys.modules.items()):
        root = name.split(".")[0]
        if root in WATCHED_MODULES:
            f = getattr(mod, "__file__", None)
            if f:
                out.append((f"module:{name}", f))
    env = os.environ.get("INNOVATION_DEPLOYMENT_ROOT")
    if env:
        out.append(("env:INNOVATION_DEPLOYMENT_ROOT", env))
    if deployment_root:
        out.append(("arg:--deployment-root", deployment_root))
    if not out:
        out.append(("cwd", os.getcwd()))
    return out


def check(deployment_root: str | None = None) -> dict:
    banned = banned_resolved()
    violations = []
    checked = 0
    for label, p in _candidate_paths(deployment_root):
        checked += 1
        r = resolved(p)
        if is_banned(p):
            violations.append({"label": label, "path": str(p), "resolved": r})
    return {
        "ok": not violations,
        "failure_code": (None if not violations else FAILURE_CODE),
        "banned_root": BANNED_RUNTIME_ROOT,
        "banned_root_resolved": banned,
        "deployment_root": deployment_root,
        "paths_checked": checked,
        "violations": violations,
    }


def assert_clean(deployment_root: str | None = None) -> dict:
    res = check(deployment_root)
    if not res["ok"]:
        raise RuntimeError(f"{FAILURE_CODE}: {res['violations']}")
    return res


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--deployment-root", default=None)
    a = ap.parse_args(argv)
    res = check(a.deployment_root)
    print(f"[runtime_guard] banned_root={res['banned_root']}")
    print(f"[runtime_guard] paths_checked={res['paths_checked']} "
          f"violations={len(res['violations'])}")
    for v in res["violations"]:
        print(f"[runtime_guard] {FAILURE_CODE} {v['label']} -> {v['resolved']}")
    if not res["ok"]:
        print(f"[runtime_guard] FAILED: {FAILURE_CODE}")
        return 2
    print("[runtime_guard] OK: no runtime source resolves into the original "
          "reproduction repository")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
