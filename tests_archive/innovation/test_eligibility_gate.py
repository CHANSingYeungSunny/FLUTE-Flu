"""
Eligibility gate (pre-HPC clarification 5)
==========================================

Smoke runs, pilot runs, failed debug runs, ad-hoc runs, runs missing the
eligibility fields and protocol mismatches must ALL be excluded from
`select_best_model`. Only `screening` / `full` runs with explicit
`selection_eligible=true` and a matching `protocol_version` may be selected.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

from innovation import run_artifacts as ART  # noqa: E402
from innovation import select_best_model as SBM  # noqa: E402
from innovation.paths import PROTOCOL_VERSION  # noqa: E402
from innovation.run_id import make_run_id  # noqa: E402


def _mk(root, model, stage, *, status="ok", protocol=PROTOCOL_VERSION,
        eligible=None, smoke_only=None, seed=42, horizon=24, mse=1.0, tag=""):
    rid = make_run_id("national_ili", model, "none", "identity", horizon, seed,
                      timestamp=f"T{model}{stage}{seed}{tag}", gitsha="g")
    d = os.path.join(root, rid)
    os.makedirs(d, exist_ok=True)
    payload = {"status": status, "best_val_mse": mse}
    if stage is not None:
        payload["experiment_stage"] = stage
    if protocol is not None:
        payload["protocol_version"] = protocol
    if eligible is None:
        eligible = stage in ("screening", "full")
    if stage is not None:
        payload["selection_eligible"] = bool(eligible)
        payload["smoke_only"] = bool(smoke_only if smoke_only is not None
                                     else stage == "smoke")
    ART.write_run_status(d, **payload)
    return rid, d


def test_gate_excludes_ineligible():
    tmp = tempfile.mkdtemp(prefix="innov_elig_")
    legacy_path = os.path.join(tmp, "legacy.json")
    old_runs, old_legacy = SBM.RUNS_ROOT, SBM.LEGACY_ELIGIBILITY_PATH
    SBM.RUNS_ROOT, SBM.LEGACY_ELIGIBILITY_PATH = tmp, legacy_path
    try:
        _mk(tmp, "dlinear", "screening")                 # eligible
        _mk(tmp, "patchtst", "full")                     # eligible
        _mk(tmp, "itransformer", "smoke")                # excluded (smoke)
        _mk(tmp, "nlinear", "pilot")                     # excluded (pilot)
        _mk(tmp, "gpt2_miflu", "full", status="failed")  # excluded (failed)
        rid_legacy, _ = _mk(tmp, "dlinear", "adhoc")     # excluded (adhoc)
        rid_noauth, _ = _mk(tmp, "dlinear", None)        # excluded (no fields)
        _mk(tmp, "patchtst", "full", protocol="innov-v0", tag="B")  # protocol mismatch

        # a legacy annotation force-excludes an otherwise-eligible run
        rid_ok, _ = _mk(tmp, "nlinear", "screening")
        with open(legacy_path, "w", encoding="utf-8") as f:
            json.dump({"runs": [{"run_id": rid_ok, "selection_eligible": False,
                                 "reason": "produced before eligibility schema"}]}, f)

        rows = SBM.scan_runs()
        audit = SBM.build_audit(rows)

        eligible_ids = {r["run_id"] for r in rows if r["eligible"]}
        assert len(eligible_ids) == 2, eligible_ids          # screening+full only
        assert rid_ok not in eligible_ids, "legacy force-exclude failed"
        assert rid_noauth not in eligible_ids, "missing-fields run must be excluded"

        reasons = {e["run_id"]: " ".join(e["reasons"])
                   for e in audit["excluded_runs"]}
        assert "smoke" in reasons[[k for k in reasons if "smoke" in k][0]]
        joined = " ".join(reasons.values())
        for token in ("smoke_only", "stage_not_eligible", "not ok",
                      "missing_eligibility_fields", "protocol_version_mismatch",
                      "legacy_annotation"):
            assert token in joined, (token, joined)
        assert audit["test_accessed"] is False
        assert audit["protocol_version"] == PROTOCOL_VERSION
    finally:
        SBM.RUNS_ROOT, SBM.LEGACY_ELIGIBILITY_PATH = old_runs, old_legacy


if __name__ == "__main__":
    test_gate_excludes_ineligible()
    print("[test_eligibility_gate] OK")
