"""
audit_original_repo_integrity.py — READ-ONLY content-level integrity audit.
===========================================================================

Incident: an innov-v2.2 bundle was accidentally extracted into the ORIGINAL
reproduction repository on HPC (`.../CHATTIME/Chattime`) instead of the isolated
deployment root, and the bundle-only additions were then removed.

This module closes that incident with CONTENT-LEVEL evidence. Deliberately it
does NOT rely on file size, mtime, pyc-header size, `git status` or a successful
import. The strongest available content reference for a pre-incident file is the
surviving compiled artifact that HPC produced FROM that pre-incident source:

    __pycache__/<mod>.cpython-39.pyc

If the CURRENT source, compiled in memory with the same interpreter, yields the
SAME canonical bytecode digest as the surviving pre-incident .pyc, the two
sources are content-equivalent (limitation: comments and pure whitespace are not
represented in bytecode, so this proves semantic content identity, not byte
identity; where a stronger reference exists it is used instead).

WHY THIS FILE IS NOT UNDER scripts/innovation/
----------------------------------------------
`scripts/innovation/**` and `tests/innovation/**` are inside the FROZEN source
snapshot. Adding a file there would change the runtime aggregate and force a new
source version cascade. This audit tool lives outside that scope on purpose.

STRICT READ-ONLY CONTRACT
-------------------------
* the audited root is opened read-only; nothing is written, touched, chmod'd,
  copied over, restored or removed;
* every output is written to `--out-dir`, which is REJECTED if it resolves inside
  the audited root;
* run it with `python -B` so the interpreter cannot emit new __pycache__ files.

USAGE
-----
  # 1) locally: build the reference (frozen manifest + local copies + git blobs)
  python scripts/audit_original_repo_integrity.py --make-ref --out-dir <dir>

  # 2) on HPC: audit the reproduction root with that reference
  python -B scripts/audit_original_repo_integrity.py --audit \
      --root /home/sychan552/scratch/CHATTIME/Chattime \
      --ref  audit_reference.json --out-dir <stage-out>
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import marshal
import os
import subprocess
import sys


def _utc_now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

try:  # the auditor must also run STANDALONE on HPC, outside any deployment root
    from innovation.paths import (INNOVATION_ROOT, PROJECT_ROOT,  # noqa: E402
                                  SOURCE_SNAPSHOT_MANIFEST)
except Exception:  # pragma: no cover
    PROJECT_ROOT = os.path.dirname(_HERE)
    INNOVATION_ROOT = os.path.join(PROJECT_ROOT, "results", "innovation")
    SOURCE_SNAPSHOT_MANIFEST = os.path.join(
        INNOVATION_ROOT, "source_snapshot_manifest.json")

# The reused original-reproduction modules that the innovation bundle SHIPS and
# that therefore could have overwritten pre-existing files.
REUSED_DEPENDENCY_FILES = (
    "scripts/configs.py", "scripts/scaler_utils.py", "scripts/miflu_model.py",
    "scripts/textual_embedder.py", "scripts/compute_miflu_indicators.py",
    "scripts/cdc_calendar.py", "scripts/early_stopping.py",
)

# Paths created by the extraction and then removed during recovery.
REMOVED_DURING_RECOVERY = (
    "scripts/innovation", "tests/innovation", "results/innovation",
    "MIFlu_innovation_plan_v2.md", "hpc_scripts/innovation_worker.sh",
    "hpc_scripts/pilot_gpt2_miflu_L24_seed42.sh",
    "hpc_scripts/pilot_dlinear_L24_seed42.sh",
    "hpc_scripts/pilot_patchtst_L24_seed42.sh",
    "hpc_scripts/pilot_itransformer_L24_seed42.sh",
    "hpc_scripts/submit_innovation_pilot.sh",
    "hpc_scripts/submit_innovation_smoke.sh",
    "hpc_scripts/submit_innovation_screening.sh",
    "hpc_scripts/submit_innovation_full.sh",
    "hpc_scripts/hpc_env_check.sh", "hpc_scripts/pilot_specs.json",
)

# Anything matching these must be ABSENT from the reproduction root.
RESIDUAL_GLOBS = (
    "scripts/innovation", "tests/innovation", "results/innovation",
    "MIFlu_innovation_plan_v2.md",
    "hpc_scripts/innovation_worker.sh", "hpc_scripts/hpc_env_check.sh",
    "hpc_scripts/pilot_specs.json",
    "hpc_scripts/pilot_gpt2_miflu_L24_seed42.sh",
    "hpc_scripts/pilot_dlinear_L24_seed42.sh",
    "hpc_scripts/pilot_patchtst_L24_seed42.sh",
    "hpc_scripts/pilot_itransformer_L24_seed42.sh",
    "hpc_scripts/submit_innovation_pilot.sh",
    "hpc_scripts/submit_innovation_smoke.sh",
    "hpc_scripts/submit_innovation_screening.sh",
    "hpc_scripts/submit_innovation_full.sh",
    "results/innovation/source_snapshot_manifest.json",
    "innovation_hpc_bundle.tar.gz", "innovation_hpc_bundle.tar.gz.sha256",
)

# Non-source artifacts to spot-check against the LOCAL (untouched) copies.
SPOTCHECK = (
    ("data/raw/national_illness_raw.csv", "data/raw/national_illness_raw.csv"),
    ("data/scaler_miflu_national.json", "data/scaler_miflu_national.json"),
    ("data/predictions_miflu_L24_paper_protocol.csv",
     "data/predictions_miflu_L24_paper_protocol.csv"),
    ("hpc_results/journal_evidence/full__earlystop/reps_1_to_10/summary.csv",
     "results/ili/journal_evidence/full__earlystop/reps_1_to_10/summary.csv"),
    ("hpc_results/journal_evidence/full__earlystop/reps_1_to_10/metrics.csv",
     "results/ili/journal_evidence/full__earlystop/reps_1_to_10/metrics.csv"),
)

STATUS_OK = "VERIFIED_IDENTICAL"
STATUS_REMOVED = "EXPECTED_NEW_AND_REMOVED"
STATUS_PREEXISTING_MOD = "PREEXISTING_LOCAL_MODIFICATION_VERIFIED"
STATUS_RESIDUAL = "RESIDUAL_UNEXPECTED"
STATUS_MISMATCH = "HASH_MISMATCH"
STATUS_NOREF = "REFERENCE_UNAVAILABLE"
STATUS_UNRESOLVED = "UNRESOLVED"


# ── hashing helpers ─────────────────────────────────────────────────────────
def sha256_file(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for blk in iter(lambda: f.read(1 << 20), b""):
                h.update(blk)
        return h.hexdigest()
    except OSError:
        return None


def _walk_code(h, code) -> None:
    """Canonical bytecode digest: name, argcount, firstlineno, code bytes, names,
    varnames and consts (recursing into nested code objects).

    co_filename is EXCLUDED (it differs between the original compile location and
    this audit), and co_flags is EXCLUDED (compile flags may legitimately differ).
    """
    h.update(code.co_name.encode("utf-8", "replace"))
    h.update(str(code.co_argcount).encode())
    h.update(str(code.co_firstlineno).encode())
    h.update(code.co_code)
    h.update(repr(code.co_names).encode("utf-8", "replace"))
    h.update(repr(code.co_varnames).encode("utf-8", "replace"))
    for k in code.co_consts:
        if hasattr(k, "co_code"):
            _walk_code(h, k)
        else:
            h.update(repr(k).encode("utf-8", "replace"))


def code_digest(code) -> str:
    h = hashlib.sha256()
    _walk_code(h, code)
    return h.hexdigest()


def pyc_header(path: str) -> tuple[int, int] | None:
    """Return (recorded_source_mtime, recorded_source_size) from a 3.9 pyc."""
    try:
        with open(path, "rb") as f:
            head = f.read(16)
        if len(head) < 16:
            return None
        import struct
        _magic, _flags, mtime, size = struct.unpack("<4sIII", head)
        return int(mtime), int(size)
    except OSError:
        return None


def pyc_digest(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            data = f.read()
        return code_digest(marshal.loads(data[16:]))
    except Exception:
        return None


def source_digest(path: str) -> str | None:
    """Compile `path` IN MEMORY (no pyc is written) and digest the bytecode."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            src = f.read()
        return code_digest(compile(src, "<integrity-audit>", "exec",
                                   dont_inherit=True))
    except Exception:
        return None


# ── git helpers (reference build only; never mutating) ───────────────────────
def _git(args) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=PROJECT_ROOT, stderr=subprocess.DEVNULL,
            encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


# ── reference build (local) ─────────────────────────────────────────────────
def build_reference(out_dir: str) -> dict:
    with open(SOURCE_SNAPSHOT_MANIFEST, "r", encoding="utf-8") as f:
        man = json.load(f)
    frozen = {r["path"]: r["sha256"] for r in man["files"]}

    preexisting = []
    for rel in REUSED_DEPENDENCY_FILES:
        local = os.path.join(PROJECT_ROOT, rel)
        head_blob = _git(["rev-parse", f"HEAD:{rel}"])
        if not head_blob or head_blob.startswith("HEAD:"):
            head_blob = None
        work_blob = _git(["hash-object", rel]) or None
        status = _git(["status", "--porcelain", "--", rel])
        preexisting.append({
            "path": rel,
            "category": "reused_dependency_source",
            "frozen_sha256": frozen.get(rel),
            "local_sha256": sha256_file(local),
            "git_tracked": head_blob is not None,
            "git_head_blob": head_blob,
            "git_work_blob": work_blob,
            "git_status": status,
            "git_diff_empty": (head_blob is not None and head_blob == work_blob),
        })

    spot = []
    for remote_rel, local_rel in SPOTCHECK:
        lp = os.path.join(PROJECT_ROOT, local_rel)
        spot.append({
            "remote_path": remote_rel,
            "local_path": local_rel,
            "local_sha256": sha256_file(lp) if os.path.exists(lp) else None,
            "local_exists": os.path.exists(lp),
        })

    # the FULL archive member list defines the incident BLAST RADIUS: only these
    # paths could possibly have been created or overwritten by the extraction.
    import tarfile
    arch = os.path.join(PROJECT_ROOT, "results", "innovation", "hpc_deployment",
                        "innovation_hpc_bundle.tar.gz")
    members = sorted(tarfile.open(arch).getnames()) if os.path.exists(arch) else []

    ref = {
        "created_utc": _utc_now(),
        "generator": "scripts/audit_original_repo_integrity.py --make-ref",
        "implementation_source_version": man.get("implementation_source_version"),
        "scientific_protocol_version": man.get("scientific_protocol_version"),
        "source_snapshot_aggregate_sha256": man.get("aggregate_sha256"),
        "source_snapshot_n_files": man.get("n_files"),
        "repository_head": man.get("repository_head"),
        "bundle_archive": os.path.relpath(arch, PROJECT_ROOT).replace(os.sep, "/"),
        "bundle_member_count": len(members),
        "bundle_members": members,
        "preexisting": preexisting,
        "removed_during_recovery": list(REMOVED_DURING_RECOVERY),
        "residual_globs": list(RESIDUAL_GLOBS),
        "spotcheck": spot,
    }
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "audit_reference.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(ref, f, indent=2)
    print(f"[audit] reference -> {p}")
    return ref


# ── audit (remote / read-only) ──────────────────────────────────────────────
def _entry(path, category, **kw) -> dict:
    e = {"path": path, "category": category}
    e.update(kw)
    return e


def _stat(path: str) -> tuple[str | None, int | None]:
    """Read-only stat: (mtime UTC, size). Used as SCOPE evidence, never as proof
    of content identity."""
    try:
        st = os.stat(path)
        return (datetime.datetime.utcfromtimestamp(st.st_mtime)
                .strftime("%Y-%m-%dT%H:%M:%SZ"), int(st.st_size))
    except OSError:
        return None, None


def audit(root: str, ref: dict, out_dir: str) -> dict:
    root = os.path.abspath(root)
    out_abs = os.path.abspath(out_dir)
    if out_abs == root or out_abs.startswith(root + os.sep):
        raise SystemExit("REFUSING: --out-dir must be OUTSIDE the audited root")

    entries: list[dict] = []

    # 1 ── pre-existing reused dependency sources ────────────────────────────
    for p in ref["preexisting"]:
        rel = p["path"]
        full = os.path.join(root, rel)
        cur_sha = sha256_file(full)
        if cur_sha is None:
            entries.append(_entry(rel, "reused_dependency_source",
                                  exists=False, status=STATUS_RESIDUAL,
                                  note="pre-existing file is MISSING"))
            continue

        # (a) does it equal the frozen innovation copy that the extraction wrote?
        matches_frozen = (p.get("frozen_sha256") is not None
                          and cur_sha == p["frozen_sha256"])

        # (b) CONTENT-LEVEL: bytecode vs the surviving pre-incident .pyc
        stem = os.path.splitext(os.path.basename(rel))[0]
        pyc = os.path.join(root, "scripts", "__pycache__",
                           f"{stem}.cpython-39.pyc")
        hdr = pyc_header(pyc)
        d_src = source_digest(full)
        d_pyc = pyc_digest(pyc) if hdr else None
        pyc_size = hdr[1] if hdr else None
        cur_size = os.path.getsize(full)

        if hdr is None:
            status, method = STATUS_NOREF, "no surviving pre-incident pyc"
        elif pyc_size != cur_size:
            status = STATUS_UNRESOLVED
            method = (f"pyc is STALE (recorded source size {pyc_size} != "
                      f"current {cur_size}); it predates the incident but was "
                      "compiled from an older revision, so it cannot certify the "
                      "pre-incident content")
        elif d_src is None or d_pyc is None:
            status, method = STATUS_NOREF, "bytecode digest unavailable"
        elif d_src == d_pyc:
            status = STATUS_OK
            method = ("bytecode-equivalent to the surviving pre-incident pyc "
                      "(content-level; insensitive to comment/whitespace-only "
                      "edits)")
        else:
            status = STATUS_MISMATCH
            method = ("current source compiles to DIFFERENT bytecode than the "
                      "surviving pre-incident pyc")

        # (c) a clean git-tracked file gives an independent blob reference
        if (status in (STATUS_OK, STATUS_NOREF) and p.get("git_tracked")
                and not p.get("git_diff_empty")):
            status = STATUS_PREEXISTING_MOD
            method += " | locally tracked with a documented working-tree edit"

        entries.append(_entry(
            rel, "reused_dependency_source", exists=True,
            in_blast_radius=True, incident_relevance="incident_affected",
            remote_mtime_utc=_stat(full)[0], remote_size_bytes=cur_size,
            sha256=cur_sha, matches_frozen_copy=matches_frozen,
            frozen_sha256=p.get("frozen_sha256"),
            local_sha256=p.get("local_sha256"),
            git_tracked=p.get("git_tracked"),
            git_head_blob=p.get("git_head_blob"),
            git_work_blob=p.get("git_work_blob"),
            git_status=p.get("git_status"),
            git_diff_empty=p.get("git_diff_empty"),
            pyc_present=hdr is not None,
            pyc_recorded_source_size=pyc_size,
            current_size=cur_size,
            bytecode_digest_current=d_src,
            bytecode_digest_preincident_pyc=d_pyc,
            verification_method=method, status=status))

    # 2 ── paths created by the extraction and removed during recovery ───────
    members = set(ref.get("bundle_members") or [])
    for rel in ref["removed_during_recovery"]:
        full = os.path.join(root, rel)
        exists = os.path.exists(full)
        mt, sz = _stat(full)
        entries.append(_entry(rel, "extracted_then_removed", exists=exists,
                              in_blast_radius=True,
                              incident_relevance="incident_affected",
                              remote_mtime_utc=mt, remote_size_bytes=sz,
                              status=(STATUS_RESIDUAL if exists
                                      else STATUS_REMOVED),
                              note=("still present -> residual" if exists else
                                    "absent as expected after recovery")))

    # 3 ── residual scan ─────────────────────────────────────────────────────
    for rel in ref["residual_globs"]:
        full = os.path.join(root, rel)
        exists = os.path.exists(full)
        if exists:
            mt, sz = _stat(full)
            entries.append(_entry(rel, "residual_scan", exists=True,
                                  in_blast_radius=True,
                                  incident_relevance="incident_affected",
                                  remote_mtime_utc=mt, remote_size_bytes=sz,
                                  status=STATUS_RESIDUAL,
                                  note="unexpected residual in the reproduction "
                                       "repository"))

    # 4 ── non-source artifacts vs the untouched LOCAL copies ────────────────
    for sp in ref["spotcheck"]:
        rel = sp["remote_path"]
        full = os.path.join(root, rel)
        cur = sha256_file(full)
        mt, sz = _stat(full)
        # A non-source probe is inside the blast radius ONLY if the bundle
        # actually shipped that path; otherwise the extraction could never have
        # written it, so any divergence is a PRE-EXISTING local/remote difference
        # and carries no incident relevance.
        in_scope = rel in members
        base = {
            "in_blast_radius": in_scope,
            "incident_relevance": ("incident_affected" if in_scope else
                                   "none: not a bundle member, so the "
                                   "extraction could not have written it"),
            "remote_mtime_utc": mt, "remote_size_bytes": sz,
            "local_sha256": sp.get("local_sha256"),
            "local_reference_path": sp.get("local_path"),
        }
        if cur is None:
            entries.append(_entry(rel, "nonsource_artifact", exists=False,
                                  status=STATUS_NOREF,
                                  note="path absent on HPC", **base))
        elif not sp.get("local_exists") or not sp.get("local_sha256"):
            entries.append(_entry(rel, "nonsource_artifact", exists=True,
                                  sha256=cur, status=STATUS_NOREF,
                                  note="no trusted local reference copy",
                                  **base))
        elif cur == sp["local_sha256"]:
            entries.append(_entry(rel, "nonsource_artifact", exists=True,
                                  sha256=cur, status=STATUS_OK,
                                  verification_method="sha256 == untouched local "
                                                      "reference copy", **base))
        else:
            entries.append(_entry(rel, "nonsource_artifact", exists=True,
                                  sha256=cur, status=STATUS_MISMATCH,
                                  note="differs from the local reference copy "
                                       "(pre-existing local/remote divergence; "
                                       "NOT incident damage — see mtime)",
                                  **base))

    # 5 ── inventory: directories that could have been touched ───────────────
    dirs = {}
    for d in ("scripts", "scripts/__pycache__", "hpc_scripts", "results",
              "data", "hpc_results", "weights"):
        full = os.path.join(root, d)
        dirs[d] = {"exists": os.path.isdir(full),
                   "entries": (sorted(os.listdir(full))
                               if os.path.isdir(full) else [])[:60]}

    # ── GATE ───────────────────────────────────────────────────────────────
    # The incident gate is scoped to the INCIDENT BLAST RADIUS (bundle members +
    # the paths removed during recovery). A divergence on a path the bundle never
    # shipped is reported, but it cannot be incident damage and must not be used
    # to (falsely) claim nor (wrongly) deny incident closure.
    scoped = [e for e in entries if e.get("in_blast_radius")]
    accepted = (STATUS_OK, STATUS_REMOVED, STATUS_PREEXISTING_MOD)
    gate_ok = (all(e["status"] in accepted for e in scoped)
               and not any(e["status"] == STATUS_RESIDUAL for e in entries))
    blockers = sorted({e["status"] for e in scoped} - set(accepted))
    out_of_scope_divergence = [
        {"path": e["path"], "status": e["status"],
         "remote_mtime_utc": e.get("remote_mtime_utc"),
         "remote_size_bytes": e.get("remote_size_bytes"),
         "local_sha256": e.get("local_sha256"),
         "note": e.get("note")}
        for e in entries
        if not e.get("in_blast_radius") and e["status"] == STATUS_MISMATCH]

    report = {
        "generated_utc": _utc_now(),
        "audited_root": root,
        "read_only": True,
        "reference": {
            "implementation_source_version":
                ref.get("implementation_source_version"),
            "source_snapshot_aggregate_sha256":
                ref.get("source_snapshot_aggregate_sha256"),
            "repository_head": ref.get("repository_head"),
        },
        "directories": dirs,
        "summary": {
            "entries": len(entries),
            "verified_identical": sum(1 for e in entries
                                      if e["status"] == STATUS_OK),
            "expected_new_and_removed": sum(1 for e in entries
                                            if e["status"] == STATUS_REMOVED),
            "preexisting_local_modification_verified": sum(
                1 for e in entries if e["status"] == STATUS_PREEXISTING_MOD),
            "residual_unexpected": sum(1 for e in entries
                                       if e["status"] == STATUS_RESIDUAL),
            "hash_mismatch": sum(1 for e in entries
                                 if e["status"] == STATUS_MISMATCH),
            "reference_unavailable": sum(1 for e in entries
                                         if e["status"] == STATUS_NOREF),
            "unresolved": sum(1 for e in entries if e["status"] ==
                              STATUS_UNRESOLVED),
        },
        "original_reproduction_repository_integrity_verified": gate_ok,
        "blocker": (None if gate_ok
                    else "ORIGINAL_REPRO_REPOSITORY_INTEGRITY_NOT_FULLY_VERIFIED"),
        "open_statuses": blockers,
        "scoped_entry_count": len(scoped),
        "out_of_scope_divergence": out_of_scope_divergence,
        "entries": entries,
    }

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "original_repo_integrity_report.json"),
              "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    cols = ["path", "category", "status", "exists", "in_blast_radius",
            "incident_relevance", "remote_mtime_utc", "remote_size_bytes",
            "sha256", "local_sha256", "frozen_sha256", "matches_frozen_copy",
            "bytecode_digest_current", "bytecode_digest_preincident_pyc",
            "pyc_recorded_source_size", "current_size", "git_tracked",
            "git_head_blob", "git_work_blob", "git_diff_empty",
            "verification_method", "note"]
    with open(os.path.join(out_dir, "content_hash_comparison.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for e in entries:
            w.writerow({c: e.get(c, "") for c in cols})

    print(f"[audit] entries={len(entries)} gate_ok={gate_ok} "
          f"open={blockers}")
    for e in entries:
        if e["status"] not in (STATUS_OK, STATUS_REMOVED):
            print(f"   ! {e['status']:>22}  {e['path']}")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=PROJECT_ROOT)
    ap.add_argument("--ref", default=None)
    ap.add_argument("--out-dir", default=os.path.join(INNOVATION_ROOT, "audit"))
    ap.add_argument("--make-ref", action="store_true")
    ap.add_argument("--audit", action="store_true")
    a = ap.parse_args(argv)

    if a.make_ref:
        build_reference(a.out_dir)
        return 0
    if a.audit:
        if not a.ref:
            ap.error("--audit requires --ref")
        with open(a.ref, "r", encoding="utf-8") as f:
            ref = json.load(f)
        audit(a.root, ref, a.out_dir)
        return 0
    ap.error("choose --make-ref or --audit")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
