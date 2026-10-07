from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "results" / "innovation" / "source_snapshot_manifest.json"
OUT = ROOT / "results" / "v3" / "implementation"


def build(path: Path) -> str:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = ["results/innovation/source_snapshot_manifest.json"]
    files.extend(item["path"] for item in manifest["files"])
    files.extend(str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT / "hpc_scripts").glob("pilot_*.sh")))
    files.extend(str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT / "hpc_scripts").glob("submit_innovation_pilot.sh")))
    files = sorted(set(files))
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in files:
            source = ROOT / rel
            data = source.read_bytes()
            info = zipfile.ZipInfo(rel, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    a = OUT / "v3_phase1_bundle_a.zip"
    b = OUT / "v3_phase1_bundle_b.zip"
    print("bundle_a_sha256=", build(a))
    print("bundle_b_sha256=", build(b))
    print("byte_identical=", a.read_bytes() == b.read_bytes())
