"""build_cleanup_inventory.py — read-only inventory of figures + reports before the
final figure audit / minimal-deliverables cleanup.

Produces (into results/v3_clean/analysis/final_cleanup_audit/):
  figure_inventory_before.csv / .json
  report_inventory_before.csv  / .json

Every record: absolute path, relative path, type, bytes, mtime, SHA-256,
scientific role, split classification, referenced-by, decision, reason.
This is READ-ONLY: it never modifies or deletes anything.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ANALYSIS = os.path.join(ROOT, "results", "v3_clean", "analysis")
FIGURES = os.path.join(ANALYSIS, "figures")
REPORTS = os.path.join(ANALYSIS, "reports")
OUT = os.path.join(ANALYSIS, "final_cleanup_audit")
os.makedirs(OUT, exist_ok=True)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".gif"}


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def mtime_utc(path: str) -> str:
    return datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc).isoformat()


def classify_split(name: str, parent: str) -> str:
    """Best-effort split classification from path/name (never a scientific claim)."""
    if "final_test" in name or "final_report_figures" in parent or "final_test_prediction" in name:
        return "Test"
    if "fig_test_" in name:
        return "Test"
    # gallery under analysis/figures is Wave-1 validation prediction gallery
    return "Validation"


def figure_records():
    recs = []
    for dirpath, dirnames, filenames in os.walk(FIGURES):
        for fn in sorted(filenames):
            if os.path.splitext(fn)[1].lower() not in IMAGE_EXTS:
                continue
            p = os.path.join(dirpath, fn)
            recs.append({
                "absolute_path": p,
                "relative_path": rel(p),
                "file_type": os.path.splitext(fn)[1].lower().lstrip("."),
                "byte_size": os.path.getsize(p),
                "modification_time": mtime_utc(p),
                "sha256": sha256(p),
                "scientific_role": "",
                "split": classify_split(fn, dirpath),
                "referenced_by": "",
                "decision": "",
                "reason": "",
            })
    return recs


def report_records():
    recs = []
    for fn in sorted(os.listdir(REPORTS)):
        p = os.path.join(REPORTS, fn)
        if not os.path.isfile(p):
            continue
        recs.append({
            "absolute_path": p,
            "relative_path": rel(p),
            "file_type": os.path.splitext(fn)[1].lower().lstrip("."),
            "byte_size": os.path.getsize(p),
            "modification_time": mtime_utc(p),
            "sha256": sha256(p),
            "scientific_role": "",
            "split": "",
            "referenced_by": "",
            "decision": "",
            "reason": "",
        })
    return recs


def write(records, csv_path, json_path):
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        w.writeheader()
        w.writerows(records)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def main():
    fig = figure_records()
    rep = report_records()
    write(fig, os.path.join(OUT, "figure_inventory_before.csv"),
          os.path.join(OUT, "figure_inventory_before.json"))
    write(rep, os.path.join(OUT, "report_inventory_before.csv"),
          os.path.join(OUT, "report_inventory_before.json"))
    print("figures:", len(fig))
    print("reports:", len(rep))
    print("wrote inventory to", OUT)


if __name__ == "__main__":
    main()
