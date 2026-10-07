#!/usr/bin/env python3
"""
execute_checkpoint_cleanup.py — remove ONLY proven-superseded full checkpoints.

Deletes a single explicit path at a time (never a blanket find/-delete/rm -rf).
A file is removed only when every one of these holds:

  1. its root is a superseded innovation_deploy_root_* (NOT the active root);
  2. a durable copy of the same run exists under innovation_durable/;
  3. that durable manifest reports reconstruction_exact == true;
  4. that durable manifest reports n_keys_unequal == 0;
  5. that durable manifest reports no missing and no unexpected keys;
  6. the durable copy holds predictions/validation_predictions.csv;
  7. the durable copy holds all four metric json files;
  8. the durable compact.safetensors exists and its sha256 matches the manifest;
  9. the file's size equals the manifest's recorded source_bytes.

Anything failing a guard is skipped and recorded as retained.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys

SCRATCH = "/scratch/sychan552"
HOMEDIR = "/gpfs1/home/sychan552"
DURABLE = [os.path.join(HOMEDIR, "innovation_durable", "screening"),
           os.path.join(HOMEDIR, "innovation_durable", "runs")]
ACTIVE_ROOT = "innovation_deploy_root_v3_clean14"
OUT = "/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1_v2_verification_20261007"


def sha256_file(p, cap=None):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_durable():
    idx = {}
    for base in DURABLE:
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            d = os.path.join(base, name)
            man = os.path.join(d, "compact_manifest.json")
            if os.path.isdir(d) and os.path.exists(man):
                try:
                    idx[name] = (d, json.load(open(man)))
                except Exception:
                    pass
    return idx


def main():
    execute = "--execute" in sys.argv
    dur = load_durable()
    print(f"[exec] durable manifests indexed: {len(dur)}")
    rows, freed, skipped = [], 0, 0

    for root in sorted(os.listdir(SCRATCH)):
        if not root.startswith("innovation_deploy_root_") or root == ACTIVE_ROOT:
            continue
        rootp = os.path.join(SCRATCH, root)
        for dirpath, _dirs, files in os.walk(rootp):
            for f in files:
                if not f.endswith(".pt"):
                    continue
                p = os.path.join(dirpath, f)
                parent = os.path.basename(dirpath)
                run = (os.path.basename(os.path.dirname(dirpath))
                       if parent == "checkpoints" else parent)
                st = os.stat(p)
                rec = {"path": p, "root": root, "run": run,
                       "bytes": st.st_size, "action": "retain", "reason": ""}
                ent = dur.get(run)
                if ent is None:
                    rec["reason"] = "no durable manifest for this run name"
                    rows.append(rec); skipped += 1; continue
                d, man = ent
                g = []
                if man.get("reconstruction_exact") is not True:
                    g.append("reconstruction_exact != true")
                if man.get("n_keys_unequal") != 0:
                    g.append(f"n_keys_unequal={man.get('n_keys_unequal')}")
                if man.get("missing_keys"):
                    g.append("missing_keys non-empty")
                if man.get("unexpected_keys"):
                    g.append("unexpected_keys non-empty")
                if not os.path.exists(os.path.join(d, "predictions",
                                                   "validation_predictions.csv")):
                    g.append("durable predictions missing")
                for mj in ("paper_aligned_full_output_metrics.json",
                           "ilitotal_fixed_step_metrics.json",
                           "ilitotal_full_horizon_metrics.json",
                           "pte_pie_metrics.json"):
                    if not os.path.exists(os.path.join(d, "metrics", mj)):
                        g.append(f"durable metric missing: {mj}")
                ck = os.path.join(d, "compact.safetensors")
                if not os.path.exists(ck):
                    g.append("durable compact.safetensors missing")
                elif sha256_file(ck) != man.get("compact_sha256"):
                    g.append("durable compact sha256 mismatch")
                src = man.get("source_bytes")
                if isinstance(src, int) and src != st.st_size:
                    g.append(f"size mismatch: file={st.st_size} manifest={src}")
                if g:
                    rec["reason"] = "; ".join(g)
                    rows.append(rec); skipped += 1; continue

                rec["action"] = "delete"
                rec["reason"] = ("reconstruction_exact=true, n_keys_unequal=0, "
                                 f"compact_sha256={man.get('compact_sha256')}, "
                                 f"durable_dir={d}")
                if execute:
                    os.remove(p)
                    rec["reason"] += " -- REMOVED"
                rows.append(rec)
                freed += st.st_size

    os.makedirs(OUT, exist_ok=True)
    tag = "EXECUTED" if execute else "DRYRUN"
    with open(os.path.join(OUT, f"HPC_CLEANUP_{tag}.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "root", "run", "bytes",
                                           "action", "reason"])
        w.writeheader(); w.writerows(rows)
    ndel = sum(1 for r in rows if r["action"] == "delete")
    print(f"[exec] mode={'EXECUTE' if execute else 'DRY RUN'}")
    print(f"[exec] would delete / deleted : {ndel} files, {freed/2**30:.2f} GiB")
    print(f"[exec] retained (guards failed): {skipped} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())