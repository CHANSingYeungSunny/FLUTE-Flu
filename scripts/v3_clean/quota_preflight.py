"""quota_preflight.py — per-row quota preflight (fail-closed).

NOTE: `os.statvfs('/home/...')` is USELESS on this GPFS mount — it reports the
whole filesystem (observed 40145 GiB "used"), not the user quota. The authority
is `mmlsquota`, so that is what this script parses.

Exit codes:
  0  the next row may be submitted
  3  quota would be violated -> the controller must NOT submit
  4  quota could not be measured (fail closed)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(
    os.environ.get("INNOVATION_DEPLOYMENT_ROOT", "."), "scripts"))

from innovation import storage_policy as SP                      # noqa: E402


def measure() -> dict:
    try:
        out = subprocess.run(["mmlsquota"], capture_output=True, text=True,
                             timeout=30)
        text = (out.stdout or "") + (out.stderr or "")
    except Exception as e:                                       # noqa: BLE001
        raise RuntimeError(f"mmlsquota failed: {type(e).__name__}: {e}")
    q = SP.parse_quota(text)
    if "home" not in q:
        raise RuntimeError(f"could not parse home quota from: {text[:200]!r}")
    return q


def main() -> int:
    run_key = sys.argv[1] if len(sys.argv) > 1 else ""
    schema = sys.argv[2] if len(sys.argv) > 2 else run_key
    # a synthetic override lets the audit prove the over-limit path fails closed
    forced = os.environ.get("PREFLIGHT_FORCE_NEED_BYTES")

    q = measure()
    home = q["home"]
    used = home["used_bytes"]
    limit = home["limit_bytes"]
    need = int(forced) if forced else SP.projected_row_bytes(schema)

    reserve_after = (limit - used - need) / SP.GIB
    ok = reserve_after >= SP.HOME_RESERVE_GIB

    scratch = q.get("scratch", {})
    scratch_ok = (scratch.get("used_bytes", 0)
                  < SP.SCRATCH_HARD_QUOTA_GIB * SP.GIB)

    payload = {
        "run_key": run_key, "schema": schema,
        "home_used_gib": round(used / SP.GIB, 3),
        "home_limit_gib": round(limit / SP.GIB, 3),
        "row_need_bytes": need,
        "reserve_after_row_gib": round(reserve_after, 3),
        "required_reserve_gib": SP.HOME_RESERVE_GIB,
        "scratch_used_gib": round(scratch.get("used_bytes", 0) / SP.GIB, 3),
        "scratch_ok": scratch_ok,
        "ok": bool(ok and scratch_ok),
    }
    print(json.dumps(payload))
    return 0 if payload["ok"] else 3


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                                       # noqa: BLE001
        print(json.dumps({"error": f"{type(e).__name__}: {e}", "ok": False}))
        sys.exit(4)
