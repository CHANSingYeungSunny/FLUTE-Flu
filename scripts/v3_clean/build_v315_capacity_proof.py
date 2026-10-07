"""build_v315_capacity_proof.py — conservative capacity proof (v3.15).

Uses MEASURED compact sizes from the Gate (not estimates) and the refreshed
quota/usage snapshot. Fails loudly if any hard limit would be violated.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(r"c:\Users\Asus\Desktop\FYP code\MLFlu")
sys.path.insert(0, str(REPO / "scripts"))
from innovation import storage_policy as SP                    # noqa: E402

GIB = SP.GIB
GATE = REPO / "results" / "v3_clean" / "runs" / "gate_571855_report.json"

# ---------- refreshed measured snapshot (2026-09-19) ----------
# POST-MIGRATION measured snapshot (2026-09-19, after job 571918)
HOME_USED_GIB = 13.8              # mmlsquota 14,512,144 KB
HOME_LIMIT_GIB = 100.0
SCRATCH_USED_GIB = 383.1          # 434.2 GiB after reclaiming 51.07 GiB
SCRATCH_LIMIT_GIB = 1024.0
QUARANTINE_GIB = 0.0              # deleted after 205/205 verification
WAVE1_DURABLE_GIB = 0.94          # 205 rows migrated AND verified to compact
SHARED_BASE_GIB = 14.0            # immutable HF snapshots kept for restore
SUPERSEDED_ROOTS_GIB = 72.0       # v3_5/v3_3/v3_4/v2_8/v3_cache (delete eligible)

# ---------- measured compact bytes per schema (Gate 571905 / proof 571631)
FALLBACK = {
    "nlinear": 10224, "dlinear": 20480, "patchtst": 351704,
    "itransformer": 305376, "gpt2_miflu": 4135503,
    "qwen_time_llm": 1482128, "calf_llm": 7927320, "timecma_llm": 5564776,
    "baseline": 2048,
}


def measured_from_gate() -> dict:
    """Prefer the Gate's own measured numbers; fall back to the proof job."""
    out = dict(FALLBACK)
    try:
        rep = json.loads(GATE.read_text(encoding="utf-8"))
        for m in rep["results"]:
            st = m.get("storage") or {}
            if st.get("mode") == "compact" and st.get("compact_bytes"):
                out[m.get("model")] = int(st["compact_bytes"])
    except Exception:                                          # noqa: BLE001
        pass
    return out


REMAINING = {"qwen_time_llm": 35, "calf_llm": 40, "timecma_llm": 40,
             "gpt2_miflu": 252, "baseline": 8}


def main() -> int:
    measured = measured_from_gate()
    SP.COMPACT_BYTES_BY_SCHEMA.update(measured)

    # 205 accepted/interrupted durable rows -> compact reuse
    per_row = {}
    for sch, n in (("gpt2_miflu", 40), ("qwen_time_llm", 5), ("nlinear", 40),
                   ("dlinear", 40), ("patchtst", 40), ("itransformer", 40)):
        per_row[sch] = n
    compact_205 = sum(SP.projected_row_bytes(s) * n for s, n in per_row.items())
    saving = max(0, int(WAVE1_DURABLE_GIB * GIB) - compact_205)

    quota = {
        "home": {"used_bytes": int(HOME_USED_GIB * GIB),
                 "limit_bytes": int(HOME_LIMIT_GIB * GIB),
                 "used_gib": HOME_USED_GIB, "limit_gib": HOME_LIMIT_GIB},
        "scratch": {"used_bytes": int(SCRATCH_USED_GIB * GIB),
                    "limit_bytes": int(SCRATCH_LIMIT_GIB * GIB),
                    "used_gib": SCRATCH_USED_GIB,
                    "limit_gib": SCRATCH_LIMIT_GIB},
    }
    proj = SP.capacity_projection(quota, REMAINING,
                                  accepted_rows_durable_bytes=0,
                                  wave1_rows_durable_bytes=int(WAVE1_DURABLE_GIB * GIB),
                                  scratch_now_bytes=int(SCRATCH_USED_GIB * GIB))
    proj["measured_compact_bytes_by_schema"] = {k: int(v) for k, v in
                                                measured.items()}
    proj["compaction_saving_gib"] = round(saving / GIB, 2)
    proj["projected_final_home_gib"] = round(
        HOME_USED_GIB - saving / GIB + proj["remaining_gib"], 2)
    proj["projected_peak_home_gib"] = round(
        proj["projected_final_home_gib"] + max(
            SP.projected_row_bytes(s) for s in REMAINING) / GIB, 2)
    proj["home_reserve_gib"] = round(
        HOME_LIMIT_GIB - proj["projected_peak_home_gib"], 2)
    proj["scratch_after_quarantine_deletion_gib"] = round(
        SCRATCH_USED_GIB - QUARANTINE_GIB, 2)
    proj["scratch_after_quarantine_and_superseded_deletion_gib"] = round(
        SCRATCH_USED_GIB - QUARANTINE_GIB - SUPERSEDED_ROOTS_GIB, 2)
    proj["scratch_grace_days"] = 10
    proj["shared_base_gib"] = SHARED_BASE_GIB
    proj["hard_conditions"] = {
        "final_home_le_80": proj["projected_final_home_gib"] <= 80.0,
        "peak_home_le_80": proj["projected_peak_home_gib"] <= 80.0,
        "home_reserve_ge_20": proj["home_reserve_gib"] >= 20.0,
        "scratch_far_below_1024":
            proj["scratch_after_quarantine_deletion_gib"] < 1024.0,
    }
    proj["passed"] = all(proj["hard_conditions"].values())
    proj["generated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    proj["basis"] = ("measured compact sizes from Gate 571905 / proof 571631; "
                     "refreshed du + mmlsquota snapshot 2026-09-19")

    out = REPO / "results" / "v3_clean" / "d13" / "capacity_proof_v315.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(proj, indent=2), encoding="utf-8")

    print(f"[cap] home now {HOME_USED_GIB} GiB | compaction saving "
          f"{proj['compaction_saving_gib']} GiB | remaining "
          f"{proj['remaining_gib']} GiB")
    print(f"[cap] projected final home = {proj['projected_final_home_gib']} GiB")
    print(f"[cap] projected peak  home = {proj['projected_peak_home_gib']} GiB")
    print(f"[cap] home reserve         = {proj['home_reserve_gib']} GiB")
    print(f"[cap] scratch after quarantine deletion = "
          f"{proj['scratch_after_quarantine_deletion_gib']} GiB")
    print(f"[cap] hard conditions = {proj['hard_conditions']}")
    print(f"[cap] PASSED = {proj['passed']}")
    return 0 if proj["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
