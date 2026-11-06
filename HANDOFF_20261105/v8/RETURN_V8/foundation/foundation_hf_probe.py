#!/usr/bin/env python3
"""TASK 2 foundation-model connectivity / revision-pin probe (LOCAL WINDOWS ONLY).

Deliberately fetches ONLY config.json + README.md via allow_patterns at an exact
pinned revision. It does NOT download model weights, does NOT import torch,
does NOT run from_pretrained, and does NOT perform any inference.

Purpose: prove (a) Hub connectivity, (b) that the pinned revision SHA resolves,
(c) the exact bytes/identifiers of the two tiny metadata files. Full weight
download is intentionally out of scope for this probe.
"""
import argparse
import hashlib
import os
import sys
import traceback


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-id", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--local-dir", required=True)
    ap.add_argument("--allow-patterns", nargs="*",
                    default=["config.json", "README.md"])
    args = ap.parse_args()

    print("probe_start")
    print("repo_id=%s" % args.repo_id)
    print("revision=%s" % args.revision)
    print("local_dir=%s" % args.local_dir)
    print("allow_patterns=%s" % args.allow_patterns)
    import huggingface_hub
    print("huggingface_hub_version=%s" % huggingface_hub.__version__, flush=True)

    rc = 0
    try:
        from huggingface_hub import snapshot_download
        p = snapshot_download(
            repo_id=args.repo_id,
            revision=args.revision,
            local_dir=args.local_dir,
            allow_patterns=args.allow_patterns,
            max_workers=1,
        )
        print("snapshot_download_returned=%s" % p)
        print("STATUS=OK")
    except Exception as exc:
        rc = 1
        print("STATUS=ERROR")
        print("EXC_TYPE=%s" % type(exc).__name__)
        print("EXC_STR=%r" % (str(exc),))
        traceback.print_exc(file=sys.stdout)

    print("--- files present under local_dir ---")
    total = 0
    count = 0
    if os.path.isdir(args.local_dir):
        for root, dirs, files in os.walk(args.local_dir):
            for name in sorted(files):
                fp = os.path.join(root, name)
                with open(fp, "rb") as fh:
                    data = fh.read()
                rel = os.path.relpath(fp, args.local_dir).replace("\\", "/")
                print("FILE rel=%s bytes=%d sha256=%s" %
                      (rel, len(data), hashlib.sha256(data).hexdigest()))
                total += len(data)
                count += 1
    else:
        print("LOCAL_DIR_MISSING")
    print("FILE_COUNT=%d" % count)
    print("TOTAL_BYTES=%d" % total)
    print("probe_end")
    return rc


if __name__ == "__main__":
    sys.exit(main())
