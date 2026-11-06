#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproducible builder for the v8 final return package (TASK 8).

Assembles HANDOFF_20261105/v8/RETURN_V8/ from:
  * every v8 text file (.md .csv .json .tsv .py .sbatch .sh .txt .log),
    mirroring the v8/ subdirectory layout;
  * the updated HANDOFF_20261105/final/ scoring CSVs (COPY, never move/delete);
  * the v7 addendum/audit docs (labelled under audit/v7/);
  * the frozen v7 RETURN_V7 key files (COPY) kept SEPARATELY LABELLED under
    v7_snapshot/, plus the REQUIRED root skeleton, RAW_EVIDENCE/ NPZ and
    logs/EXECUTION_LOG.md needed by the official validator;
  * any v8 DOCX/PDF under 01_最终报告/v8/ IF they exist at build time (COPY only).

RETURN_MANIFEST.json is written ONLY by the official tool
(packaging/tools/make_return_manifest.py); this script NEVER hand-writes it.

It then rebuilds the two ZIPs in v8/ and reports byte sizes + SHA-256.

Re-run (single command) once T7 DOCX/PDF and/or the final WF CSV land:
    python "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/packaging/build_v8_return.py"

Windows paths contain spaces -> everything is absolute pathlib.Path.
shutil.rmtree is used ONLY on v8/RETURN_V8/ (our own staging dir).
"""
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu").resolve()
H = ROOT / "HANDOFF_20261105"
V8 = H / "v8"
FINAL = H / "final"
V7 = H / "v7"
V7RET = V7 / "RETURN_V7"
RET = V8 / "RETURN_V8"
PKG = V8 / "packaging"
TOOLS = PKG / "tools"                              # copies of the official tools
TOOLS_SRC = ROOT / "handoffs" / "20261105_return" / "tools"
REPORT_V8 = ROOT / "01_最终报告" / "v8"                 # may NOT exist yet (T7)
ZIP_RETURN = V8 / "RETURN_TO_CHATGPT.zip"
ZIP_RAW = V8 / "RAW_EVIDENCE.zip"
BUILD_LOG = PKG / "build_v8_return.stdout.txt"
REPORT_JSON = PKG / "v8_package_report.json"

TEXT_EXT = {".md", ".csv", ".json", ".tsv", ".py", ".sbatch", ".sh", ".txt", ".log"}
DOC_EXT = {".docx", ".pdf"}
# validate_return.py REQUIRED files at the return root (v7 frozen skeleton).
REQUIRED = [
    "RETURN_SUMMARY.md", "PROTOCOL_LOCK.json", "EXECUTION_PLAN.json",
    "RUN_LEDGER.csv", "RUN_METRICS.csv", "PEAK_EVENTS.csv",
    "MODEL_FIDELITY.csv", "CHECKS.json", "ENVIRONMENT.md", "PAPER_TO_CODE.md",
    "STATISTICAL_ANALYSIS_PLAN.md", "STATISTICAL_RESULTS.csv",
    "COST_AND_SCHEDULER.md", "OLD_NEW_RECONCILIATION.csv",
    "DOCUMENT_UPDATE_MAP.csv", "UNVERIFIED_ITEMS.md", "REPRODUCE.md",
    "CODE_CHANGES.patch",
]

_LINES = []


def log(msg=""):
    print(msg, flush=True)
    _LINES.append(msg)


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_under(p: Path, d: Path) -> bool:
    try:
        return p.resolve().is_relative_to(d.resolve())
    except Exception:
        return str(p.resolve()).startswith(str(d.resolve()))


def copy(src: Path, dst: Path):
    """Byte-identical COPY. The source is never moved, deleted or rewritten."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_rows(p: Path):
    """Yield data rows (excluding the header) of a UTF-8 CSV, or yield nothing."""
    if not p.is_file():
        return
    with p.open(encoding="utf-8", newline="") as fh:
        r = csv.reader(fh)
        next(r, None)
        yield from r


# ---------------------------------------------------------------------------
# 1. ASSEMBLE RETURN_V8
# ---------------------------------------------------------------------------
def assemble():
    if RET.exists():
        # Allowed: rmtree ONLY on our own v8/RETURN_V8/ staging dir (copies only).
        shutil.rmtree(RET)
    RET.mkdir(parents=True)

    # (a) generic recursive scan of v8 text files, preserving relative layout.
    #     Skip RETURN_V8 (self output) and packaging/ (builder + tools + notes).
    skip = [RET, PKG]
    n = 0
    for p in sorted(V8.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXT:
            continue
        if any(is_under(p, d) for d in skip):
            continue
        copy(p, RET / p.relative_to(V8))
        n += 1
    log(f"[assemble] v8 text files mirrored: {n}")

    # (b) updated final/ scoring CSVs + docs (COPY, never move/delete).
    m = 0
    for p in sorted(FINAL.iterdir()):
        if p.is_file():
            copy(p, RET / "final" / p.name)
            m += 1
    log(f"[assemble] final/ files copied: {m}")

    # (c) v7 addendum / audit documents (clearly labelled).
    k = 0
    for name in ["V7_SCIENTIFIC_ADDENDUM.md", "BLOCKED_AND_UNVERIFIED.md",
                 "MESSAGE_TO_CHATGPT.md", "DOCUMENT_UPDATE_MAP.csv"]:
        s = V7 / name
        if s.is_file():
            copy(s, RET / "audit" / "v7" / name)
            k += 1
    log(f"[assemble] v7 addendum/audit docs copied into audit/v7/: {k}")

    # (d) frozen v7 RETURN_V7 key files (COPY), kept SEPARATELY LABELLED.
    for p in sorted(V7RET.iterdir()):
        if p.is_file():
            copy(p, RET / "v7_snapshot" / p.name)
    v7docs = V7RET / "DOCUMENTS" / "v7"
    nd = 0
    if v7docs.is_dir():
        for p in sorted(v7docs.rglob("*")):
            if p.is_file():
                copy(p, RET / "v7_snapshot" / "DOCUMENTS" / "v7" / p.relative_to(v7docs))
                nd += 1
    log(f"[assemble] v7_snapshot/ root files + DOCUMENTS/v7 copied: {nd} docs")

    # (e) REQUIRED root skeleton (validator needs these at RETURN_V8 root).
    for name in REQUIRED:
        s = V7RET / name
        if s.is_file():
            copy(s, RET / name)
        else:
            log(f"[assemble][WARN] missing v7 required root file: {s}")
    log(f"[assemble] REQUIRED root skeleton copied: {len(REQUIRED)}")

    # (f) RAW_EVIDENCE/ NPZ (root RUN_LEDGER prediction_path target).
    raw = V7RET / "RAW_EVIDENCE"
    nr = 0
    if raw.is_dir():
        for p in sorted(raw.rglob("*")):
            if p.is_file():
                copy(p, RET / "RAW_EVIDENCE" / p.relative_to(raw))
                nr += 1
    log(f"[assemble] RAW_EVIDENCE/ NPZ copied (1120-panel): {nr}")

    # (g) logs/EXECUTION_LOG.md (CHECKS.json log_path target).
    elog = V7RET / "logs" / "EXECUTION_LOG.md"
    if elog.is_file():
        copy(elog, RET / "logs" / "EXECUTION_LOG.md")
        log("[assemble] logs/EXECUTION_LOG.md copied")

    # (h) official tool copies + this builder, for reproducibility.
    for name in ("make_return_manifest.py", "validate_return.py"):
        s = TOOLS / name
        if s.is_file():
            copy(s, RET / "scripts" / "tools" / name)
    self_src = PKG / "build_v8_return.py"
    if self_src.is_file():
        copy(self_src, RET / "scripts" / "build_v8_return.py")
    log("[assemble] official tool copies + builder mirrored into scripts/")

    # (i) v8 DOCX/PDF under 01_最终报告/v8/ IF they exist (COPY only).
    if REPORT_V8.is_dir():
        found = 0
        for p in sorted(REPORT_V8.rglob("*")):
            if p.is_file() and p.suffix.lower() in DOC_EXT:
                copy(p, RET / "DOCUMENTS" / "v8" / p.relative_to(REPORT_V8))
                found += 1
        log(f"[assemble] 01_最终报告/v8/ DOCX/PDF copied: {found}")
    else:
        log("[assemble] 01_最终报告/v8/ NOT present at build time -> skipped "
            "(T7 DOCX/PDF may land AFTER this packaging pass)")

    # (j) structural layout / old-new separation note (NOT a scientific result).
    # Dynamic status lines: never hard-code a stale claim about T2/T7/T1 files.
    t1_note = ("`final/WF_RECOMPUTED.csv` in THIS build: "
               + str(sum(1 for _ in csv_rows(RET / "final" / "WF_RECOMPUTED.csv")))
               + " data rows; see `evidence/WF_RECOMPUTE_REPORT.json` for the "
                 "validated status counts.")
    t7_note = ("`DOCUMENTS/v8/` IS present in this build."
               if (RET / "DOCUMENTS" / "v8").is_dir()
               else "`DOCUMENTS/v8/` is absent in this build.")
    t2_note = ("Foundation models (Chronos / TimesFM) are on a SEPARATE ROSTER "
               "(`foundation/FOUNDATION_ROSTER.csv`), never merged into the 28-arm "
               "family. Their current execution status is recorded in "
               "`foundation/T2_VERDICT.md` and any `T2_*` update files; read those "
               "instead of relying on a status string in this structural note.")
    (RET / "RETURN_LAYOUT.md").write_text(
        "# RETURN_V8 layout and old/new separation (structural note)\n\n"
        "This file describes the package layout. It is NOT a scientific result.\n\n"
        "- `final/` — the NEW 1120-panel scored CSVs + audit docs, copied from\n"
        "  `HANDOFF_20261105/final/` (COPY; sources untouched).\n"
        "- `foundation/`, `cdc_vintage/`, `resource_logs/`, `evidence/`, `scripts/` —\n"
        "  v8 task evidence (T1–T7 text files), mirroring `v8/` subdirectories.\n"
        "- `audit/v7/` — the v7 addendum/audit documents, kept separate.\n"
        "- `v7_snapshot/` — the FROZEN v7 RETURN_V7 key files (root files +\n"
        "  `DOCUMENTS/v7/`), COPIED verbatim and SEPARATELY LABELLED. The NPZ raw\n"
        "  predictions that its ledger points to live at `RAW_EVIDENCE/`.\n"
        "- `RAW_EVIDENCE/` — the 1120 validated raw prediction NPZ (old 28-arm\n"
        "  snapshot / previous return era), carried over unchanged for the ledger.\n"
        "- `logs/EXECUTION_LOG.md` — referenced by the root `CHECKS.json`.\n"
        "- Root `RUN_LEDGER.csv`, `CHECKS.json`, `RETURN_SUMMARY.md`, protocol/plan\n"
        "  JSON etc. are the carried-over v7 structural skeleton needed by the\n"
        "  official validator; they are NOT new v8 measurements.\n"
        "- `DOCUMENTS/v8/` — v8 DOCX/PDF from `01_最终报告/v8/` (COPY only).\n\n"
        "## Build-time status (generated dynamically, never hard-coded)\n\n"
        + "- T1: " + t1_note + "\n"
        + "- T7: " + t7_note + "\n"
        + "- T2: " + t2_note + "\n\n"
        "## Old / new separation (AGENTS.md RULE 4)\n\n"
        "The frozen 28-arm historical snapshot (`02_数字表格/*.csv`, Holm 0/136,\n"
        "NLinear–PatchTST 0.1172, 4/16 aggregate cells) is a SEPARATE old-snapshot\n"
        "fact and is NOT part of this return. The NEW 1120-panel tables are under\n"
        "`final/` and are never merged into that old snapshot. The numerical\n"
        "foundation models (Chronos / TimesFM) live on a SEPARATE ROSTER and are\n"
        "NOT merged into the 28-arm family. The legacy 5-fold N=3 walk-forward panel\n"
        "(seeds 42/43/44) is ALSO a separate scoring population and must not be\n"
        "merged with the national 1120-cell panel.\n\n"
        "A validator `integrity_status: PASS` is STRUCTURAL ONLY and MUST be read\n"
        "with `scientific_readiness: NOT_ASSESSED`.\n",
        encoding="utf-8")

    files = sorted(p.relative_to(RET).as_posix() for p in RET.rglob("*") if p.is_file())
    log(f"[assemble] TOTAL files in RETURN_V8: {len(files)}")
    log("[assemble] exact list of included relative paths:")
    for r in files:
        log("  " + r)
    return files


# ---------------------------------------------------------------------------
# 2. OFFICIAL TOOLS (RETURN_MANIFEST.json written ONLY here)
# ---------------------------------------------------------------------------
def run_cmd(name, cmd):
    log("[cmd] " + name)
    log("[cmd] argv: " + " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd))
    r = subprocess.run([str(c) for c in cmd], cwd=str(ROOT), text=True,
                       capture_output=True)
    (PKG / f"{name}.command.txt").write_text(
        " ".join(str(c) for c in cmd) + "\n", encoding="utf-8")
    (PKG / f"{name}.stdout.txt").write_text(r.stdout or "", encoding="utf-8")
    (PKG / f"{name}.stderr.txt").write_text(r.stderr or "", encoding="utf-8")
    (PKG / f"{name}.exit_code.txt").write_text(str(r.returncode) + "\n", encoding="utf-8")
    log(f"[cmd] {name} exit_code={r.returncode}")
    if r.stdout:
        log("[cmd] stdout:\n" + r.stdout.rstrip())
    if r.stderr:
        log("[cmd] stderr:\n" + r.stderr.rstrip())
    return r


def official_tools():
    cmd1 = [sys.executable, str(TOOLS / "make_return_manifest.py"),
            str(RET), "--exclude", "VALIDATION_RESULT.json"]
    cmd2 = [sys.executable, str(TOOLS / "validate_return.py"),
            str(RET), "--out", str(RET / "VALIDATION_RESULT.json")]
    r1 = run_cmd("make_return_manifest", cmd1)
    if r1.returncode != 0:
        log("[FATAL] make_return_manifest.py failed; aborting.")
        raise SystemExit(r1.returncode)
    r2 = run_cmd("validate_return", cmd2)
    vr = {}
    vp = RET / "VALIDATION_RESULT.json"
    if vp.is_file():
        try:
            vr = json.loads(vp.read_text(encoding="utf-8"))
        except Exception as ex:
            log(f"[validator] could not parse VALIDATION_RESULT.json: {ex}")
    log(f"[validator] integrity_status={vr.get('integrity_status', 'MISSING')} "
        f"scientific_readiness={vr.get('scientific_readiness', 'MISSING')} "
        f"errors={vr.get('errors', 'MISSING')}")
    # NEVER force a PASS: report the real verdict and propagate a failing rc.
    return r2.returncode, vr


# ---------------------------------------------------------------------------
# 3. ZIPs
# ---------------------------------------------------------------------------
def zip_return():
    if ZIP_RETURN.exists():
        ZIP_RETURN.unlink()
    with zipfile.ZipFile(ZIP_RETURN, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(RET.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(RET).as_posix())
    return ZIP_RETURN


def zip_raw():
    if ZIP_RAW.exists():
        ZIP_RAW.unlink()
    seen = set()
    with zipfile.ZipFile(ZIP_RAW, "w", zipfile.ZIP_DEFLATED) as zf:
        # whole raw-evidence directories (all extensions, incl. .body/.err/.sha256)
        for base, prefix in [(V8 / "evidence", "evidence"),
                             (V8 / "resource_logs", "resource_logs"),
                             (V8 / "cdc_vintage", "cdc_vintage"),
                             (V8 / "foundation", "foundation"),
                             (V8 / "scripts", "scripts"),
                             (FINAL, "final")]:
            if base.is_dir():
                for p in sorted(base.rglob("*")):
                    if p.is_file():
                        arc = prefix + "/" + p.relative_to(base).as_posix()
                        if arc not in seen:
                            zf.write(p, arc)
                            seen.add(arc)
        # every raw prediction NPZ already present in the project (COPY only,
        # nothing downloaded). NPZ copies inside RETURN_V8 are skipped to avoid
        # duplication; legacy archives stay in their own labelled subtrees.
        npz_count = 0
        for p in sorted(ROOT.rglob("*.npz")):
            if is_under(p, RET):
                continue
            arc = "raw_npz/" + p.relative_to(ROOT).as_posix()
            if arc not in seen:
                zf.write(p, arc)
                seen.add(arc)
                npz_count += 1
        zf.writestr(
            "RAW_EVIDENCE_README.md",
            "# RAW_EVIDENCE.zip — v8 (packaging pass)\n\n"
            "- `evidence/`, `resource_logs/`, `cdc_vintage/`, `foundation/`,\n"
            "  `scripts/` — full v8 raw-evidence directories (all extensions).\n"
            "- `final/` — HANDOFF_20261105/final/ (all files: scoring CSVs + audit MDs).\n"
            "- `raw_npz/<full project-relative path>` — every raw prediction NPZ\n"
            "  already present in the project at build time; COPY only, nothing\n"
            "  downloaded, moved, deleted or modified.\n\n"
            "NPZ under `HANDOFF_20261105/v7/RETURN_V7/RAW_EVIDENCE/` are the\n"
            "validated 1120-panel predictions referenced by RETURN_V8/RUN_LEDGER.csv.\n"
            "NPZ under `99_旧文件存档/`, `03_预测数据_证据/`, `handoffs/` are\n"
            "historical/legacy archived prediction sets (28-arm / earlier snapshot\n"
            "era), kept in their OWN labelled subtrees and NOT merged into the\n"
            "1120-panel tables (AGENTS.md RULE 4).\n"
            f"NPZ files bundled: {npz_count}.\n",
        )
    return ZIP_RAW


def zip_report(p: Path):
    return {"path": str(p), "bytes": p.stat().st_size, "sha256": sha256_file(p)}


# ---------------------------------------------------------------------------
def main():
    PKG.mkdir(parents=True, exist_ok=True)
    start = utcnow()
    log(f"### build_v8_return.py start_utc={start}")
    log(f"ROOT={ROOT}")
    log(f"RETURN_V8={RET}")

    files = assemble()
    rc, verdict = official_tools()
    z1 = zip_report(zip_return())
    z2 = zip_report(zip_raw())
    log(f"[zip] {z1['path']} bytes={z1['bytes']} sha256={z1['sha256']}")
    log(f"[zip] {z2['path']} bytes={z2['bytes']} sha256={z2['sha256']}")

    end = utcnow()
    log(f"### build_v8_return.py end_utc={end}")
    log(f"### validator exit_code={rc} "
        f"integrity_status={verdict.get('integrity_status', 'MISSING')} "
        f"scientific_readiness={verdict.get('scientific_readiness', 'MISSING')}")

    report = {
        "start_utc": start,
        "end_utc": end,
        "return_dir": str(RET),
        "file_count": len(files),
        "validator_exit_code": rc,
        "validator": verdict,
        "zips": {"RETURN_TO_CHATGPT.zip": z1, "RAW_EVIDENCE.zip": z2},
        "included_relative_paths": files,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    BUILD_LOG.write_text("\n".join(_LINES) + "\n", encoding="utf-8")
    # Propagate a failing validator rc; NEVER fabricate a PASS.
    return rc if rc != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
