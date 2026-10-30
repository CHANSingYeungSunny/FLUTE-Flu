"""
source_snapshot.py — freeze the exact innovation source for HPC transfer.
=======================================================================

WHY (pre-pilot source freeze)
-----------------------------
The working tree is DIRTY (no commit). `pilot_submission_ready` therefore cannot
be trusted unless the exact source that will run on HPC is reproducibly
identified. This module:

  1. copies every file the pilot needs into an immutable snapshot directory
     (`results/innovation/source_snapshot/<repo-relative path>`);
  2. writes `source_snapshot_manifest.json` with each file's repo-relative
     path, size and SHA-256, plus the aggregate SHA-256;
  3. records repository HEAD, dirty-tree status, the authoritative plan hash,
     the SCIENTIFIC protocol version and the IMPLEMENTATION source version;
  4. stamps `source_snapshot_sha256` into every pilot spec
     (`hpc_scripts/pilot_specs.json`).

`collect_paths(root)` takes an EXPLICIT root: the same function is used to
enumerate the frozen source AND to enumerate a DEPLOYED root during
deployment verification. Nothing falls back to a module-level root once a root
has been supplied.

The snapshot is content-addressed: `aggregate_sha256` pins it, the pilot specs
carry it, and the pilot startup check (`verify_source_snapshot.py`) recomputes
the deployed file-set hash and ABORTS on any difference.

`hpc_scripts/pilot_specs.json` is deliberately EXCLUDED from the hashed file set
— it carries the aggregate hash, so including it would be circular.
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import hashlib
import json
import os
import shutil
import subprocess

from innovation import run_artifacts as ART
from innovation.paths import (IMPLEMENTATION_SOURCE_VERSION, PLAN_MD,
                              PROTOCOL_VERSION, PROJECT_ROOT,
                              SOURCE_SNAPSHOT_DIR, SOURCE_SNAPSHOT_MANIFEST,
                              pilot_spec_metadata)

# ── what the pilot needs ────────────────────────────────────────────────────
SNAPSHOT_INCLUDE_DIRS = ("scripts/innovation", "tests/innovation")
SNAPSHOT_HPC_PREFIXES = ("innovation_", "pilot_", "submit_innovation_")
SNAPSHOT_INCLUDE_FILES = ("docs/protocol_freeze/MIFlu_innovation_plan_v2.md",)
# existing modules the innovation code RE-USES (required to run the pilot)
SNAPSHOT_DEPENDENCY_FILES = (
    "scripts/configs.py", "scripts/scaler_utils.py", "scripts/miflu_model.py",
    "scripts/textual_embedder.py", "scripts/compute_miflu_indicators.py",
    "scripts/cdc_calendar.py", "scripts/early_stopping.py",
)
# generated, hash-bearing files that must NOT be inside the hashed set
SNAPSHOT_EXCLUDE = ("hpc_scripts/pilot_specs.json",)
EXCLUDE_PARTS = ("__pycache__",)


def _git(args):
    """Run git and return stdout.

    NOTE: decode as UTF-8 with replacement — the porcelain output contains CJK
    filenames, and the default locale (cp950) raises UnicodeDecodeError, which
    would be silently swallowed and make a DIRTY tree look clean.
    """
    try:
        return subprocess.check_output(
            ["git", *args], cwd=PROJECT_ROOT, stderr=subprocess.DEVNULL,
            encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def collect_paths(root: str = PROJECT_ROOT) -> list[str]:
    """Enumerate the CONTROLLED source scope UNDER `root` (repo-relative, sorted).

    `root` is EXPLICIT: pass a deployment root to enumerate a deployed tree.
    All present / missing / extra decisions in `verify_source_snapshot` come
    from THIS function, so supplying a root fully determines the comparison —
    there is no silent fall-back to a module-level root.
    """
    root = os.path.abspath(root)
    out: set[str] = set()

    def _rel(p: str) -> str:
        return os.path.relpath(p, root).replace(os.sep, "/")

    for d in SNAPSHOT_INCLUDE_DIRS:
        for p in glob.glob(os.path.join(root, d, "**", "*"), recursive=True):
            if os.path.isfile(p) and any(x in p for x in EXCLUDE_PARTS):
                continue
            if os.path.isfile(p):
                out.add(_rel(p))

    for p in glob.glob(os.path.join(root, "hpc_scripts", "*.sh")):
        if os.path.basename(p).startswith(SNAPSHOT_HPC_PREFIXES):
            out.add(_rel(p))

    for f in SNAPSHOT_INCLUDE_FILES + SNAPSHOT_DEPENDENCY_FILES:
        if os.path.exists(os.path.join(root, f)):
            out.add(f)

    for ex in SNAPSHOT_EXCLUDE:
        out.discard(ex)
    return sorted(out)


def _aggregate(files: list[dict]) -> str:
    lines = [f"{f['path']}:{f['sha256']}" for f in sorted(files, key=lambda x: x["path"])]
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def build(rebuild: bool = True) -> dict:
    root = PROJECT_ROOT
    paths = collect_paths(root)

    # copy into the immutable snapshot tree
    if os.path.isdir(SOURCE_SNAPSHOT_DIR) and not rebuild:
        raise FileExistsError(f"snapshot already exists: {SOURCE_SNAPSHOT_DIR} "
                              "(pass rebuild=True)")
    if os.path.isdir(SOURCE_SNAPSHOT_DIR):
        shutil.rmtree(SOURCE_SNAPSHOT_DIR)
    files = []
    for rel in paths:
        src = os.path.join(root, rel)
        dst = os.path.join(SOURCE_SNAPSHOT_DIR, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        files.append({"path": rel, "size": os.path.getsize(src),
                      "sha256": ART.sha256_file(src)})

    head = _git(["rev-parse", "HEAD"]) or "nogit"
    short = _git(["rev-parse", "--short", "HEAD"]) or "nogit"
    dirty = bool(_git(["status", "--porcelain"]))
    manifest = {
        "created_utc": ART.utc_now(),
        "scientific_protocol_version": PROTOCOL_VERSION,
        "implementation_source_version": IMPLEMENTATION_SOURCE_VERSION,
        "protocol_version": PROTOCOL_VERSION,          # backwards-compatible key
        "repository_head": head,
        "repository_head_short": short,
        "working_tree_dirty": dirty,
        "authoritative_plan": {"path": os.path.relpath(PLAN_MD, root).replace(os.sep, "/"),
                               "sha256": ART.sha256_file(PLAN_MD)},
        "n_files": len(files),
        "total_bytes": int(sum(f["size"] for f in files)),
        "files": files,
        "excluded_from_hash": list(SNAPSHOT_EXCLUDE),
        "controlled_scope": {
            "include_dirs": list(SNAPSHOT_INCLUDE_DIRS),
            "hpc_script_prefixes": list(SNAPSHOT_HPC_PREFIXES),
            "include_files": list(SNAPSHOT_INCLUDE_FILES),
            "dependency_files": list(SNAPSHOT_DEPENDENCY_FILES),
            "exclude": list(SNAPSHOT_EXCLUDE),
        },
        "aggregate_scheme": ("sha256 of sorted '<path>:<sha256>' lines joined by '\\n'"),
        "aggregate_sha256": _aggregate(files),
        "snapshot_dir": os.path.relpath(SOURCE_SNAPSHOT_DIR, root).replace(os.sep, "/"),
        "note": ("content-addressed immutable snapshot of the UNCOMMITTED source; "
                 "pilot specs carry aggregate_sha256 and the pilot startup check "
                 "aborts on any deployed-file difference"),
    }
    ART.write_json(SOURCE_SNAPSHOT_MANIFEST, manifest)
    stamp_pilot_specs(manifest["aggregate_sha256"])
    return manifest


def stamp_pilot_specs(sha: str) -> str | None:
    """Write source_snapshot_sha256 into every pilot spec (excluded from hash).

    D1 repair (innov-v2.2): the mandated metadata contract
    (`experiment_stage` / `test_access_allowed` / `protocol_version`) is re-stamped
    here as well, so running the snapshot cascade alone can never leave the pilot
    specs without those fields.
    """
    p = os.path.join(PROJECT_ROOT, "hpc_scripts", "pilot_specs.json")
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    meta = pilot_spec_metadata()
    data.update(meta)
    data["source_snapshot_sha256"] = sha
    data["implementation_source_version"] = IMPLEMENTATION_SOURCE_VERSION
    for spec in data.get("specs", []):
        spec.update(meta)
        spec["source_snapshot_sha256"] = sha
        spec["implementation_source_version"] = IMPLEMENTATION_SOURCE_VERSION
    ART.write_json(p, data)
    return p


def main(argv=None) -> int:
    m = build(rebuild=True)
    print(f"[source_snapshot] scientific_protocol={m['scientific_protocol_version']} "
          f"implementation_source={m['implementation_source_version']}")
    print(f"[source_snapshot] files={m['n_files']} bytes={m['total_bytes']}")
    print(f"[source_snapshot] aggregate_sha256={m['aggregate_sha256']}")
    print(f"[source_snapshot] head={m['repository_head_short']} "
          f"dirty={m['working_tree_dirty']}")
    print(f"[source_snapshot] manifest -> {SOURCE_SNAPSHOT_MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
