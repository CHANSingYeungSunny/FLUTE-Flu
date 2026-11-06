#!/usr/bin/env python3
"""TASK 2 — local FULL pinned-weight downloader (Windows, CPU-only).

Calls huggingface_hub.snapshot_download at a PINNED revision into a local_dir
(WITHOUT allow_patterns -> downloads the actual weight tensors), then emits a
per-file SHA-256 + byte-size manifest.

No torch / transformers / from_pretrained / inference is used anywhere. Run with
PYTHONPATH pointing at an isolated `pip install --target` of huggingface_hub,
wrapped by `timeout` in the shell.
"""
import argparse
import hashlib
import json
import os
import sys
import time


def sha256_of(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-id", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--local-dir", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--evidence-dir", required=True)
    args = ap.parse_args()

    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print("START_UTC=" + started)
    print("REPO_ID=" + args.repo_id)
    print("REVISION=" + args.revision)
    print("LOCAL_DIR=" + args.local_dir)
    print("NAME=" + args.name)
    try:
        import huggingface_hub
        print("HFHUB_VERSION=" + huggingface_hub.__version__)
        print("HFHUB_LOADED_FROM=" + huggingface_hub.__file__)
    except Exception as e:
        print("IMPORT_ERROR=%s: %s" % (type(e).__name__, e))
        print("STATUS=IMPORT_FAILED")
        return 2

    from huggingface_hub import snapshot_download
    tree_url = "https://huggingface.co/%s/tree/%s" % (args.repo_id, args.revision)
    print("TREE_URL=" + tree_url)
    try:
        path = snapshot_download(
            repo_id=args.repo_id,
            revision=args.revision,
            local_dir=args.local_dir,
            # full download: deliberately NO allow_patterns
        )
        print("SNAPSHOT_RETURNED=" + str(path))
    except Exception as e:
        print("DOWNLOAD_ERROR=%s: %s" % (type(e).__name__, e))
        print("DOWNLOAD_ERROR_REPR=%r" % (e,))
        print("FAILED_URL=" + tree_url)
        print("FAILED_REVISION=" + args.revision)
        print("STATUS=DOWNLOAD_FAILED")
        return 3

    rows = []
    for root, dirs, files in os.walk(args.local_dir):
        for fn in sorted(files):
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, args.local_dir).replace(os.sep, "/")
            try:
                size = os.path.getsize(fp)
                digest = sha256_of(fp)
                rows.append((rel, size, digest))
            except OSError as e:
                rows.append((rel, -1, "ERROR:%s" % e))
    rows.sort()
    total = sum(r[1] for r in rows if isinstance(r[1], int) and r[1] >= 0)
    ended = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    os.makedirs(args.evidence_dir, exist_ok=True)
    manifest = os.path.join(
        args.evidence_dir, "foundation_t2_manifest_%s.txt" % args.name
    )
    with open(manifest, "w", encoding="utf-8", newline="\n") as f:
        f.write("# TASK 2 local full-weight download manifest\n")
        f.write("repo_id=%s\n" % args.repo_id)
        f.write("revision=%s\n" % args.revision)
        f.write("local_dir=%s\n" % args.local_dir)
        f.write("name=%s\n" % args.name)
        f.write("start_utc=%s\n" % started)
        f.write("end_utc=%s\n" % ended)
        f.write("file_count=%d\n" % len(rows))
        f.write("total_bytes=%d\n" % total)
        f.write("huggingface_hub_version=%s\n" % huggingface_hub.__version__)
        for rel, size, digest in rows:
            f.write("%s  %s  %s\n" % (digest, size, rel))
    print("MANIFEST=" + manifest)
    print("FILE_COUNT=%d" % len(rows))
    print("TOTAL_BYTES=%d" % total)
    print("END_UTC=" + ended)
    for rel, size, digest in rows:
        print("FILE %s %s %s" % (size, digest, rel))
    print("STATUS=OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
