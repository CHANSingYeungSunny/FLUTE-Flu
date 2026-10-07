"""Generate wave1_report_artifact_manifest.json (SHA-256 + byte count) for Wave-1 outputs."""
import os, hashlib, json, datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "results", "v3_clean", "analysis"))
MANIFEST_NAME = "wave1_report_artifact_manifest.json"


def hash_file(path):
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


files = []
# reports dir
reports = os.path.join(BASE, "reports")
for name in sorted(os.listdir(reports)):
    if name == MANIFEST_NAME:
        continue
    p = os.path.join(reports, name)
    if os.path.isfile(p):
        sha, size = hash_file(p)
        files.append({"path": "results/v3_clean/analysis/reports/" + name, "sha256": sha, "bytes": size})
# figures dir
figdir = os.path.join(BASE, "figures")
for name in sorted(os.listdir(figdir)):
    p = os.path.join(figdir, name)
    if os.path.isfile(p):
        sha, size = hash_file(p)
        files.append({"path": "results/v3_clean/analysis/figures/" + name, "sha256": sha, "bytes": size})
# analysis root CSVs/JSONs (source tables)
for name in sorted(os.listdir(BASE)):
    p = os.path.join(BASE, name)
    if os.path.isfile(p) and name.lower().endswith((".csv", ".json")):
        sha, size = hash_file(p)
        files.append({"path": "results/v3_clean/analysis/" + name, "sha256": sha, "bytes": size})

manifest = {
    "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "file_count": len(files),
    "files": files,
}
out = os.path.join(reports, MANIFEST_NAME)
with open(out, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
print("wrote", out, "with", len(files), "files")
