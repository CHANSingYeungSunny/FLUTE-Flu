"""
metadata_chain.py — five-layer runtime metadata chain report (innov-v2.3).
=========================================================================

For ONE run, read the same governance field from all five evidence layers and
prove they agree:

    1. pilot_specs.json            (the spec that requested the run)
    2. config_resolved.yaml        (resolved run configuration)
    3. run_status.json             (runtime status)
    4. checkpoint_manifest.json    (the checkpoint that was selected)
    5. registry_v2.csv             (the versioned registry row)

`runtime_metadata_chain_complete = true` is set ONLY when every required field
is PRESENT and EQUAL in all five layers. It is never concluded from
run_status.json alone.

USAGE
-----
    python scripts/innovation/metadata_chain.py --run-id <run_id>
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from innovation.paths import (AUDIT_DIR, INNOVATION_ROOT,  # noqa: E402
                              PROJECT_ROOT, REQUIRED_METADATA_FIELDS)

import csv  # noqa: E402
import datetime  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402

LAYERS = ("pilot_specs.json", "config_resolved.yaml", "run_status.json",
          "checkpoint_manifest.json", "registry_v2.csv")


def _utc() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def yaml_top_level_scalars(path: str) -> dict:
    """Minimal reader for the flat `key: value` pairs written by
    `run_artifacts.write_min_yaml` (no third-party YAML dependency)."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line or line[0] in (" ", "\t", "#", "-"):
                continue
            if ":" not in line:
                continue
            k, _, v = line.partition(":")
            v = v.strip()
            if not v or v.startswith("|") or v.startswith(">"):
                continue
            if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
                v = v[1:-1]
            out[k.strip()] = v
    return out


STAGE_SPECIFIC_FIELDS = ("experiment_stage", "purpose")


def _norm(v) -> str:
    """Canonical form for comparison: booleans are case-insensitive because the
    YAML layer writes `false` while JSON writes False and CSV writes 'False'."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v).strip()
    if s.lower() in ("true", "false"):
        return s.lower()
    return s


def read_layers(run_id: str, run_dir: str, model_key: str) -> dict:
    layers: dict[str, dict] = {}

    # 1 ── pilot_specs.json
    ps_path = os.path.join(PROJECT_ROOT, "hpc_scripts", "pilot_specs.json")
    spec = {}
    if os.path.exists(ps_path):
        with open(ps_path, "r", encoding="utf-8") as f:
            ps = json.load(f)
        top = {k: v for k, v in ps.items() if k != "specs"}
        for s in ps.get("specs", []):
            if s.get("model") == model_key:
                spec = dict(top, **s)      # top-level metadata + the spec itself
                break
        if not spec:
            spec = dict(top)
        layers["pilot_specs.json"] = spec
    else:
        layers["pilot_specs.json"] = {}

    # 2 ── config_resolved.yaml
    layers["config_resolved.yaml"] = yaml_top_level_scalars(
        os.path.join(run_dir, "config_resolved.yaml"))

    # 3 ── run_status.json
    rs_path = os.path.join(run_dir, "run_status.json")
    layers["run_status.json"] = (json.load(open(rs_path, encoding="utf-8"))
                                 if os.path.exists(rs_path) else {})

    # 4 ── checkpoint_manifest.json
    cm_path = os.path.join(run_dir, "checkpoints", "checkpoint_manifest.json")
    layers["checkpoint_manifest.json"] = (
        json.load(open(cm_path, encoding="utf-8")) if os.path.exists(cm_path) else {})

    # 5 ── registry_v2.csv
    reg_path = os.path.join(INNOVATION_ROOT, "registry_v2.csv")
    row = {}
    if os.path.exists(reg_path):
        with open(reg_path, "r", newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("run_id") == run_id:
                    row = r
                    break
    layers["registry_v2.csv"] = row
    return layers


def build(run_id: str, run_dir: str, model_key: str) -> dict:
    """Compare the five layers.

    `pilot_specs.json` describes a PILOT run. When this report is produced from a
    smoke (metadata-contract) run, `experiment_stage` and `purpose` differ BY
    DEFINITION between that layer and the run's own layers. Those two fields are
    therefore compared on the four RUN-produced layers, and the pilot layer is
    additionally required to carry exactly the values a pilot run would carry
    (`governance_fields(stage='pilot')`). Every other field must agree across all
    five layers.
    """
    layers = read_layers(run_id, run_dir, model_key)
    run_layers = [L for L in LAYERS if L != "pilot_specs.json"]
    run_stage = _norm(layers.get("run_status.json", {}).get("experiment_stage"))

    fields = []
    all_ok = True
    for f in REQUIRED_METADATA_FIELDS:
        vals = {L: _norm(layers.get(L, {}).get(f)) for L in LAYERS}
        present = [L for L in LAYERS
                   if (f in layers.get(L, {})) and vals[L] != ""]
        if f in STAGE_SPECIFIC_FIELDS and run_stage != "pilot":
            compared = run_layers
        else:
            compared = list(LAYERS)
        cvals = [vals[L] for L in compared if L in present]
        missing = [L for L in compared if L not in present]
        distinct = sorted(set(cvals))
        ok = (not missing) and len(distinct) == 1
        all_ok = all_ok and ok
        fields.append({
            "field": f, "values": vals, "layers_compared": compared,
            "layers_present": present, "layers_missing": missing,
            "distinct_values": distinct, "agree": ok,
            "note": ("stage-specific: compared on the run layers because the "
                     "pilot-spec layer describes a pilot run"
                     if f in STAGE_SPECIFIC_FIELDS and run_stage != "pilot"
                     else ""),
        })

    # the pilot-spec layer must equal what a pilot run would actually emit
    from innovation.paths import governance_fields
    pilot_expected = governance_fields(stage="pilot", model_key=model_key)
    pilot_layer = layers.get("pilot_specs.json", {})
    pilot_ok = True
    pilot_check = []
    for f in REQUIRED_METADATA_FIELDS:
        exp = _norm(pilot_expected.get(f))
        got = _norm(pilot_layer.get(f))
        if f in ("source_snapshot_sha256", "authoritative_plan_sha256",
                 "model_key", "display_name", "architecture_fidelity",
                 "protocol_version", "implementation_source_version",
                 "selection_eligible", "paper_result_eligible",
                 "test_access_allowed", "experiment_stage", "purpose"):
            same = (exp == got) if exp != "" else got != ""
            pilot_ok = pilot_ok and same
            pilot_check.append({"field": f, "expected_pilot_value": exp,
                                "pilot_spec_value": got, "match": bool(same)})
    all_ok = all_ok and pilot_ok

    rep = {
        "generated_utc": _utc(),
        "run_id": run_id, "run_dir": os.path.relpath(
            run_dir, PROJECT_ROOT).replace(os.sep, "/"), "model_key": model_key,
        "run_stage": run_stage,
        "layers": LAYERS,
        "required_fields": list(REQUIRED_METADATA_FIELDS),
        "fields": fields,
        "pilot_spec_layer_ok": bool(pilot_ok),
        "pilot_spec_layer_check": pilot_check,
        "runtime_metadata_chain_complete": bool(all_ok),
        "note": ("complete only if every required field is present and equal "
                 "across the layers that can legitimately be equal, the pilot-spec "
                 "layer carries exactly the values a pilot run would emit, and no "
                 "conclusion is drawn from run_status.json alone"),
    }
    os.makedirs(AUDIT_DIR, exist_ok=True)
    with open(os.path.join(AUDIT_DIR, "runtime_metadata_chain_report.json"),
              "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)

    head = ["field"] + [L for L in LAYERS] + ["agree"]
    lines = ["# Runtime metadata chain report", "",
             f"- run_id: `{run_id}`", f"- model_key: `{model_key}`",
             f"- complete: **{rep['runtime_metadata_chain_complete']}**", "",
             "| " + " | ".join(head) + " |",
             "|" + "---|" * len(head)]
    for e in fields:
        cells = [f"`{e['field']}`"] + [e["values"][L] or "—" for L in LAYERS] \
            + [("OK" if e["agree"] else "MISMATCH")]
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "> " + rep["note"], ""]
    with open(os.path.join(AUDIT_DIR, "runtime_metadata_chain_report.md"),
              "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return rep


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--model-key", default=None)
    a = ap.parse_args(argv)
    from innovation.paths import RUNS_ROOT
    run_dir = a.run_dir or os.path.join(RUNS_ROOT, a.run_id)
    model_key = a.model_key
    if not model_key:
        parts = a.run_id.split("__")
        model_key = parts[1] if len(parts) > 1 else None
    rep = build(a.run_id, run_dir, model_key)
    print(f"[metadata_chain] complete={rep['runtime_metadata_chain_complete']}")
    for e in rep["fields"]:
        if not e["agree"]:
            print(f"   MISMATCH {e['field']}: missing={e['layers_missing']} "
                  f"distinct={e['distinct_values']}")
    return 0 if rep["runtime_metadata_chain_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
