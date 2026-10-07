"""run_one_time_test.py — the ONE-TIME final Test evaluation driver.

Lives OUTSIDE the frozen innovation source hash. It never selects, tunes or
retrains: it evaluates ONLY the checkpoints bound to `frozen_model_manifest.json`
(champion) plus the frozen MIFlu baseline, using the SAME frozen evaluation
functions as `innovation.runner` (load_raw_df/load_scaler/normalize/build_windows/
build_components/predict_frame + innovation.metrics.evaluate_predictions).

Pre-access gate -> immutable Test-evaluation manifest -> single-use receipt
(exclusive create) -> evaluation -> artifacts under test_evaluations/<tev_id>/.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import socket
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

TEST_RE = re.compile(r"(^|[/\\])test(_evaluations)?([/\\]|$)|test_predictions|test_metrics",
                     re.IGNORECASE)


def _sha(p):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    except OSError:
        return ""


def _j(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _wj(p, o, exclusive=False):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    mode = "x" if exclusive else "w"
    with open(p, mode, encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deployment-root", required=True)
    ap.add_argument("--expect-manifest-sha", required=True)
    ap.add_argument("--expect-cohort-sha", required=True)
    ap.add_argument("--device", default=None)
    a = ap.parse_args()
    os.chdir(a.deployment_root)

    INN = "results/innovation"
    GP = os.path.join(INN, "governance", "stage_provenance")
    FMM = os.path.join(INN, "frozen_model_manifest.json")
    COH = os.path.join(GP, "stage_f_cohort_manifest.json")
    FA = os.path.join(INN, "freeze_audit.json")
    MS = os.path.join(INN, "model_selection_audit.json")
    TR = os.path.join(INN, "test_readiness", "test_readiness_audit.json")
    RECEIPT = os.path.join(INN, "test_evaluations", "ONE_TIME_TEST_ACCESS_RECEIPT.json")

    # ── pre-access gate ─────────────────────────────────────────────────────
    fails = []
    fa = _j(FA); ms = _j(MS); man = _j(FMM); coh = _j(COH); tr = _j(TR)
    man_sha, coh_sha = _sha(FMM), _sha(COH)
    if not fa.get("passed"):
        fails.append("freeze_audit.passed!=true")
    if not ms.get("cohort_complete"):
        fails.append("cohort_complete!=true")
    if ms.get("cohort_resolved_cells") != 160:
        fails.append("resolved_cells!=160")
    if len(ms.get("duplicate_cells", [])) != 0:
        fails.append("duplicate_cells!=0")
    if ms.get("test_access_count", 0) != 0 or ms.get("test_artifact_count", 0) != 0:
        fails.append("selection_test_access!=0")
    if man_sha != a.expect_manifest_sha:
        fails.append("manifest_sha_mismatch")
    if coh_sha != a.expect_cohort_sha:
        fails.append("cohort_sha_mismatch")
    if man.get("champion_model_key") != "nlinear":
        fails.append("champion!=nlinear")
    if sorted(man.get("baseline_val_mse_by_L", {}).keys()) != ["24", "36", "48", "60"]:
        fails.append("horizons!=24/36/48/60")
    # A receipt means the single authorization was ALREADY consumed; in that case
    # we may only RESUME the SAME immutable evaluation, never start a second one.
    resume = os.path.exists(RECEIPT)
    if fails:
        print("ONE_TIME_TEST_PRECHECK_FAILED: " + "; ".join(fails))
        return 2

    from innovation import runner as R
    import torch
    device = a.device or ("cuda" if torch.cuda.is_available() else "cpu")

    champion = man["champion_model_key"]
    champion_runs = [(c["model_key"], c["horizon"], c["seed"], c["run_id"],
                      c.get("checkpoint_sha256", "")) for c in coh["cohort"]
                     if c["model_key"] == champion]
    baseline_runs = [(b["model_key"], b["horizon"], b["seed"], b["run_id"], "")
                     for b in coh.get("baseline_cohort", [])]

    # ── verify every frozen checkpoint exists + matches its recorded SHA-256 ──
    ck_fail = []
    for (m, L, s, rid, csha) in champion_runs:
        ck = os.path.join(INN, "runs", rid, "checkpoints", "best_val_mse.pt")
        if not os.path.exists(ck):
            ck_fail.append(rid)
        elif csha and _sha(ck) != csha:
            ck_fail.append(rid)
    if ck_fail:
        print("ONE_TIME_TEST_PRECHECK_FAILED: checkpoint mismatch " + str(ck_fail[:3]))
        return 2

    tev_id = None
    if resume:
        prev = _j(RECEIPT)
        tev_id = prev.get("test_eval_id")
        if (prev.get("frozen_model_manifest_sha256") != man_sha
                or prev.get("cohort_manifest_sha256") != coh_sha):
            print("ONE_TIME_TEST_COMPROMISED_REQUIRES_DISCLOSURE: receipt hashes differ")
            return 4
        print("[test] resuming existing evaluation " + str(tev_id))
    if not tev_id:
        tev_id = "final_nlinear_" + datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    tev = os.path.join(INN, "test_evaluations", tev_id)
    for sub in ("predictions", "metrics", "figures", "logs"):
        os.makedirs(os.path.join(tev, sub), exist_ok=True)

    # ── immutable Test-evaluation manifest (BEFORE any Test access) ──────────
    cells = [{"role": "champion", "model_key": m, "horizon": L, "seed": s, "run_id": rid}
             for (m, L, s, rid, _c) in champion_runs] + \
            [{"role": "baseline", "model_key": m, "horizon": L, "seed": s, "run_id": rid}
             for (m, L, s, rid, _c) in baseline_runs]
    _manifest_path = os.path.join(tev, "test_evaluation_manifest.json")
    if not os.path.exists(_manifest_path):   # create-only: never rewrite after access
        _wj(_manifest_path, {
        "test_eval_id": tev_id, "created_utc": datetime.datetime.utcnow()
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "champion": champion, "cells": cells, "n_cells": len(cells),
        "frozen_model_manifest_sha256": man_sha, "cohort_manifest_sha256": coh_sha,
        "scientific_protocol_version": man.get("scientific_protocol_version"),
        "implementation_source_version": man.get("implementation_source_version"),
        "source_aggregate_sha256": man.get("source_aggregate_sha256"),
    })

    # ── single-use receipt (exclusive create) — consumes the authorization ────
    if resume:
        print("[test] receipt already present; continuing the SAME evaluation")
    else:
        token = os.environ.get("ONE_TIME_TEST_AUTHORIZATION", "")
        if not token:
            print("ONE_TIME_TEST_PRECHECK_FAILED: missing ONE_TIME_TEST_AUTHORIZATION")
            return 2
        _wj(RECEIPT, {
            "authorization_token_sha256": hashlib.sha256(token.encode()).hexdigest(),
            "frozen_model_manifest_sha256": man_sha,
            "cohort_manifest_sha256": coh_sha,
            "scientific_protocol_version": man.get("scientific_protocol_version"),
            "implementation_source_version": man.get("implementation_source_version"),
            "source_aggregate_sha256": man.get("source_aggregate_sha256"),
            "deployment_root": os.getcwd(),
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "hostname": socket.gethostname(), "pid": os.getpid(),
            "declared_access_count": 1, "champion_model_key": champion,
            "checkpoint_sha256": man.get("checkpoint_sha256", {}),
            "test_eval_id": tev_id,
        }, exclusive=True)
        print("[test] receipt created (authorization consumed); Test access begins")

    # ── the one-time evaluation (champion + frozen baseline) ─────────────────
    raw = R.load_raw_df()
    scaler = R.load_scaler()
    data = R.normalize(R.to_array(raw), scaler)
    train_df = raw.iloc[:scaler.train_end]
    from innovation import metrics as MET

    results = []
    for role, runs in (("champion", champion_runs), ("baseline", baseline_runs)):
        for (m, L, s, rid, _c) in runs:
            _met = os.path.join(tev, "metrics", f"{role}__{m}__L{L}__s{s}.json")
            if os.path.exists(_met):       # resume: already evaluated, never redo
                results.append(_j(_met))
                continue
            windows = R.build_windows(data, int(L))
            model, _enc, ctx = R.build_components(
                m, "gpt2" if m == "gpt2_miflu" else "none",
                "concat_projection" if m == "gpt2_miflu" else "identity",
                int(L), device, train_df)
            ck = os.path.join(INN, "runs", rid, "checkpoints", "best_val_mse.pt")
            state = torch.load(ck, map_location=device, weights_only=True)
            model.load_state_dict(state, strict=True)
            model.eval()
            df = R.predict_frame(model, windows["X_test"], windows["Y_test"],
                                 windows["idx_test"], R.T, int(L), scaler, "test",
                                 device, batch_size=16, ctx_fn=ctx)
            df.to_csv(os.path.join(tev, "predictions",
                                   f"{role}__{m}__L{L}__s{s}.csv"), index=False)
            tm = MET.evaluate_predictions(df, "test", scaler=scaler)
            tm["role"] = role; tm["model_key"] = m; tm["horizon"] = L
            tm["seed"] = s; tm["run_id"] = rid
            _wj(os.path.join(tev, "metrics", f"{role}__{m}__L{L}__s{s}.json"), tm)
            results.append(tm)
            print("[test] %s %s L%s s%s -> mse=%s n=%s"
                  % (role, m, L, s, tm.get("mse"), tm.get("n", tm.get("row_count"))))

    _wj(os.path.join(tev, "metrics", "aggregate.json"),
        {"n_cells": len(results), "results": results})
    _wj(os.path.join(tev, "job_status.json"),
        {"status": "ok", "cells": len(results), "test_access_count": 1,
         "test_eval_id": tev_id})
    _wj(os.path.join(tev, "source_and_plan_hashes.json"),
        {"source_aggregate_sha256": man.get("source_aggregate_sha256"),
         "authoritative_plan_sha256": man.get("authoritative_plan_sha256")})
    _wj(os.path.join(tev, "frozen_model_manifest.copy.json"), man)
    with open(os.path.join(tev, "environment.txt"), "w", encoding="utf-8") as f:
        f.write("device=%s\nhost=%s\nutc=%s\n" % (device, socket.gethostname(),
                                                  datetime.datetime.utcnow().isoformat()))
    print("[test] DONE cells=%d -> %s" % (len(results), tev))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
