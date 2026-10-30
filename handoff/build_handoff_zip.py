# -*- coding: utf-8 -*-
"""Build the bilingual ChatGPT handoff package (text + code + data) and zip it.

Staging layout (handoff/staging/) mirrors the 00..07 structure documented in 00_HANDOFF.md.
Outputs handoff/MLFlu_ChatGPT_Handoff_<YYYYMMDD>.zip plus PACKAGE_MANIFEST.txt (per-file sha256).

Deliberately omitted (regenerable / redundant) — see generated OMITTED_REGENERABLE.md:
  *.tgz tarballs, s1es_runs/ (Track-S checkpoints incl. *.pth), non-GPT2 text-embedding dumps.

Usage:
    python handoff/build_handoff_zip.py               # build + verify
    python handoff/build_handoff_zip.py --keep-staging
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import os
import shutil
import sys
import zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(BASE, "handoff")
STAGING = os.path.join(HANDOFF, "staging")
GITHUB_SOFT_LIMIT_MB = 95      # warn above this
GITHUB_HARD_LIMIT_MB = 100     # GitHub per-file hard limit; split if exceeded
SPLIT_PART_MB = 90

PAPER_REF = os.path.join(BASE, "reference_papers",
                         "MIFlu_Large_Language_Model-Based_Multimodal_Influenza_Forecasting_Scheme.md")
REPORT_DOCX = "MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版_精简终版.docx"

EXCLUDE_EXTS = (".tgz", ".tar", ".gz", ".pth", ".npz", ".pyc", ".zip")
EXCLUDE_NAMES = ("__pycache__", ".git", "s1es_runs", ".pytest_cache")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_file(src: str, dst_rel: str) -> None:
    dst = os.path.join(STAGING, dst_rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src_dir: str, dst_rel: str,
              include_exts: tuple[str, ...] | None = None,
              extra_exclude_names: tuple[str, ...] = ()) -> int:
    """Copy a tree honouring EXCLUDE_EXTS/EXCLUDE_NAMES. Returns file count."""
    n = 0
    skip = EXCLUDE_NAMES + extra_exclude_names
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
        for fn in files:
            low = fn.lower()
            if low.endswith(EXCLUDE_EXTS) or fn.startswith("."):
                continue
            if include_exts is not None and not low.endswith(include_exts):
                continue
            copy_file(os.path.join(root, fn), os.path.join(dst_rel, os.path.relpath(root, src_dir), fn))
            n += 1
    return n


def copy_named(src_dir: str, dst_rel: str, names: list[str]) -> int:
    n = 0
    for nm in names:
        src = os.path.join(src_dir, nm)
        if os.path.exists(src):
            copy_file(src, os.path.join(dst_rel, nm))
            n += 1
        else:
            print(f"[handoff] WARN missing: {src}", file=sys.stderr)
    return n


def write_text(dst_rel: str, text: str) -> None:
    dst = os.path.join(STAGING, dst_rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)


def assemble() -> dict[str, int]:
    counts: dict[str, int] = {}
    if os.path.isdir(STAGING):
        shutil.rmtree(STAGING)
    os.makedirs(STAGING, exist_ok=True)

    # 00 — handoff brief
    copy_file(os.path.join(HANDOFF, "00_HANDOFF.md"), "00_HANDOFF.md")
    counts["00_HANDOFF.md"] = 1

    # 01 — paper + analyses
    counts["01_paper"] = copy_named(os.path.join(BASE, "docs", "01_paper"), "01_paper",
                                     ["PAPER_EXPLAINED.md", "AUTHOR_REPO_EXPLAINED.md"])
    if os.path.exists(PAPER_REF):
        copy_file(PAPER_REF, os.path.join("01_paper", "MIFlu_paper_fulltext_reference.md"))
        counts["01_paper"] += 1

    # 02 — author repo (code + its official data + the GPT-2 text embeddings actually used)
    counts["02_author_repo"] = copy_named(
        os.path.join(BASE, "docs", "01_paper"), "02_author_repo", ["AUTHOR_REPO_EXPLAINED.md"])
    counts["02_author_repo"] += copy_tree(
        os.path.join(BASE, "recovery", "author_repo"), os.path.join("02_author_repo", "code"),
        extra_exclude_names=("text_emb",))  # embedding dumps handled below
    emb_src = os.path.join(BASE, "recovery", "author_repo", "dataset", "illness", "text_emb")
    for src in sorted(glob.glob(os.path.join(emb_src, "text_emb_label_0507_*.txt"))):
        copy_file(src, os.path.join("02_author_repo", "code", "dataset", "illness",
                                    "text_emb", os.path.basename(src)))
        counts["02_author_repo"] += 1

    # 03 — our data (both vintages, with an explicit warning file)
    counts["03_data"] = copy_tree(os.path.join(BASE, "data"), "03_data", include_exts=(".csv", ".json"))
    write_text(os.path.join("03_data", "READ_ME_FIRST_DATA_VINTAGES.md"), """# ⚠ Data vintages — read before using

| File | Rows | sha256 (first 16) | What it is |
|------|-----:|-------------------|------------|
| `raw/national_illness_raw_paper_exact.csv` | 966 | 31ffc1693de205ca… | project-schema copy of the AUTHOR data (value-identical) |
| `raw/national_illness_raw.csv` | 1025 | c2b983af2bf38614… | 2026-07 FluView snapshot — DIFFERENT vintage, values revised from MMWR 2016w40 |

**Never mix scores computed on these two files.** The official data is the author's 966-row
`national_illness.csv` (see `02_author_repo/code/dataset/illness/`, sha256 2a96dfed…ebfe5).
The author CSV's `date` column is a synthetic 7-day index, not real CDC weeks.
""")

    # 04 — current benchmark + authoritative report
    counts["04_benchmark"] = copy_tree(
        os.path.join(BASE, "results", "v3_clean", "analysis", "peak_criteria"), "04_benchmark")
    counts["04_benchmark"] += copy_named(
        os.path.join(BASE, "reports", "concise_final"), "04_benchmark",
        [REPORT_DOCX, "REPORT_精简终版.md", "CONCISE_FINAL_REPORT_CHANGELOG.md",
         "CONCISE_FINAL_REPORT_RENDER_AUDIT.md", "CONCISE_FINAL_REPORT_SHA256.txt",
         "CONCISE_FINAL_REPORT_SOURCE_MANIFEST.csv"])
    copy_file(os.path.join(BASE, "CURRENT_OFFICIAL_REPORT.txt"),
              os.path.join("04_benchmark", "CURRENT_OFFICIAL_REPORT.txt"))
    counts["04_benchmark"] += 1

    # 05 — reproduction + independent audit + data identity
    r1 = os.path.join(BASE, "hpc_results", "official_repo_reproduction_20261006")
    counts["05_reproduction_audit"] = 0
    r1dir = os.path.join(r1, "r1_v2_verification_20261007")
    for pattern in ("R1C_*", "PAPER_GAP_COMPARABILITY_AUDIT.csv", "TRACK_C_MASTER_CONTRACT.md"):
        for src in sorted(glob.glob(os.path.join(r1dir, pattern))):
            if os.path.isfile(src) and not src.lower().endswith(EXCLUDE_EXTS):
                copy_file(src, os.path.join("05_reproduction_audit", os.path.basename(src)))
                counts["05_reproduction_audit"] += 1
    counts["05_reproduction_audit"] += copy_named(
        os.path.join(r1, "r0_r5_cpu_stage_20261006"), "05_reproduction_audit",
        ["PAPER_LEVEL_REPRODUCTION_VERDICT.md"])
    counts["05_reproduction_audit"] += copy_named(r1, "05_reproduction_audit",
                                                  ["REPOSITORY_PROVENANCE.md", "REPORT_ZH.md"])
    counts["05_reproduction_audit"] += copy_named(
        os.path.join(BASE, "audit_20260930"), "05_reproduction_audit",
        ["audit_report_zh.md", "data_files_probe.json"])
    for src in sorted(glob.glob(os.path.join(BASE, "audit_20260930", "**", "*.csv"), recursive=True)):
        copy_file(src, os.path.join("05_reproduction_audit", os.path.basename(src)))
        counts["05_reproduction_audit"] += 1
    counts["05_reproduction_audit"] += copy_named(
        os.path.join(BASE, "recovery"), "05_reproduction_audit",
        ["data_identity_report.md", "dataset_manifest.json", "manifest.json"])

    # 06 — scripts + tests
    counts["06_scripts"] = copy_tree(os.path.join(BASE, "scripts"), "06_scripts",
                                     include_exts=(".py", ".sh"))
    counts["06_scripts"] += copy_tree(os.path.join(BASE, "tests"),
                                      os.path.join("06_scripts", "tests"), include_exts=(".py",))
    copy_file(os.path.join(HANDOFF, "build_handoff_zip.py"),
              os.path.join("06_scripts", "build_handoff_zip.py"))
    counts["06_scripts"] += 1

    # 07 — docs layer
    counts["07_docs"] = 0
    if os.path.exists(os.path.join(BASE, "START_HERE.md")):
        copy_file(os.path.join(BASE, "START_HERE.md"), "START_HERE.md")
        counts["07_docs"] += 1
    counts["07_docs"] += copy_named(os.path.join(BASE, "docs"), "07_docs",
                                    ["GLOSSARY.md", "DIRECTORY_MAP.md", "EVIDENCE_INDEX.md"])

    # 08 — paper tables (flat authoritative tables)
    counts["08_paper_tables"] = copy_tree(os.path.join(BASE, "paper_tables"), "08_paper_tables",
                                          include_exts=(".csv", ".txt", ".md"))
    return counts


def write_omitted_note() -> None:
    write_text("OMITTED_REGENERABLE.md", """# Omitted from this package (regenerable / redundant)

To keep the zip under GitHub's 100 MB per-file limit, the following were intentionally left out.
Nothing here affects any conclusion; all are regenerable or redundant copies.

| Omitted | Size | How to get it / why it is safe |
|---------|-----:|--------------------------------|
| `results/.../peak_criteria/s1es_runs/` (Track-S early-stop checkpoints, `*.pth`) | ~217 MB | Regenerable by re-running the Track-S script; conclusion already summarised in `04_benchmark/TRACK_S_FINAL_REPORT_DECISION.md` + `S1ES_RESULTS_PER_FIT.csv` |
| `s1es_runs.tgz`, `miflu_test_csv.tgz` | ~124 MB | Tarballs of the above / of CSVs that are already included unpacked |
| Non-GPT2 text-embedding dumps (`LLAMA*`, `BERT*`, other date-stamped variants in author `text_emb/`) | ~277 MB | Regenerable via author `text_emb.ipynb`; the embeddings actually loaded by the released training code (`text_emb_label_0507_{24,36,48,60}.txt`) ARE included |
| `*.npz`, `*.pyc`, `__pycache__/` | — | caches / intermediate arrays |
| Historical experiment trees (`results/v2_legacy_archive/`, `v3_superseded_archive/`, `hpc_results/stage5_a2|stage6|hpc_a1*`) | large | superseded evidence, kept in the main repo only |
""")


def build_manifest() -> str:
    lines = ["# PACKAGE MANIFEST (path, bytes, sha256)"]
    total = 0
    for root, dirs, files in os.walk(STAGING):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in sorted(files):
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, STAGING).replace("\\", "/")
            size = os.path.getsize(p)
            total += size
            lines.append(f"{rel}\t{size}\t{sha256_file(p)}")
    lines.append(f"TOTAL\t{total}")
    return "\n".join(lines) + "\n"


def make_zip(date_tag: str) -> str:
    zip_path = os.path.join(HANDOFF, f"MLFlu_ChatGPT_Handoff_{date_tag}.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, dirs, files in os.walk(STAGING):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fn in sorted(files):
                p = os.path.join(root, fn)
                arc = os.path.relpath(p, STAGING).replace("\\", "/")
                z.write(p, arc)
    return zip_path


def verify_zip(zip_path: str) -> bool:
    ok = True
    with zipfile.ZipFile(zip_path) as z:
        bad = z.testzip()
        if bad:
            print(f"[handoff] FAIL corrupt entry: {bad}")
            ok = False
        names = set(z.namelist())
        for required in ["00_HANDOFF.md", f"04_benchmark/{REPORT_DOCX}",
                         "02_author_repo/code/dataset/illness/national_illness.csv",
                         "01_paper/PAPER_EXPLAINED.md", "07_docs/DIRECTORY_MAP.md",
                         "PACKAGE_MANIFEST.txt", "OMITTED_REGENERABLE.md"]:
            if required not in names:
                print(f"[handoff] FAIL missing in zip: {required}")
                ok = False
        print(f"[handoff] entries: {len(names)}")
    return ok


def split_if_needed(zip_path: str) -> list[str]:
    """Split AFTER verification. Parts must be concatenated back before use."""
    size_mb = os.path.getsize(zip_path) / 1e6
    if size_mb <= GITHUB_HARD_LIMIT_MB:
        return [zip_path]
    print(f"[handoff] zip {size_mb:.1f}MB exceeds {GITHUB_HARD_LIMIT_MB}MB — splitting into parts")
    part = SPLIT_PART_MB * 1_000_000
    out: list[str] = []
    with open(zip_path, "rb") as f:
        idx = 1
        while True:
            chunk = f.read(part)
            if not chunk:
                break
            out_path = f"{zip_path}.{idx:03d}"
            with open(out_path, "wb") as o:
                o.write(chunk)
            out.append(out_path)
            idx += 1
    os.remove(zip_path)
    print("[handoff] NOTE: reassemble with `copy /b part.001+part.002 … out.zip` before unzipping")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-staging", action="store_true")
    ap.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"))
    args = ap.parse_args()

    print("[handoff] assembling staging …")
    counts = assemble()
    write_omitted_note()
    for k, v in counts.items():
        print(f"[handoff]   {k}: {v} files")
    write_text("PACKAGE_MANIFEST.txt", build_manifest())

    print("[handoff] zipping …")
    zip_path = make_zip(args.date)
    ok = verify_zip(zip_path)                      # verify the whole zip FIRST
    outputs = split_if_needed(zip_path)            # split only if above the hard limit
    for p in outputs:
        mb = os.path.getsize(p) / 1e6
        print(f"[handoff] {p}  ({mb:.1f} MB)"
              + ("  ⚠ above soft limit" if mb > GITHUB_SOFT_LIMIT_MB else ""))
    if not args.keep_staging and os.path.isdir(STAGING):
        shutil.rmtree(STAGING)
    print("[handoff] OK" if ok else "[handoff] FAILED verification")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
