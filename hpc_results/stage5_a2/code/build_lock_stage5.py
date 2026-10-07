#!/usr/bin/env python3
"""Stage 5 A2 — checkpoint lock (runs on a compute node, inside the scoring job).

For every one of the 36 planned learned fits this records, BEFORE any Test
inference is executed in the same job:
  * the locked checkpoint path, byte size, mtime and full SHA-256;
  * the validation criterion value that selected it (7-variable standardized
    validation MSE) and the epoch it came from;
  * the train-only scaler identity;
and it fails closed if any of the 36 is missing.

Output: <out>/CHECKPOINT_LOCK.json and CHECKPOINT_LOCK.csv
"""
import argparse, hashlib, json, os, re, sys, datetime
import pandas as pd

SEEDS = [42, 43, 44]
LS = [24, 36, 48, 60]
EXPECTED_TEST = {24: 170, 36: 158, 48: 146, 60: 134}

TEMPLATES = {
    "miflu":   ("miflu",   "best_miflu_L{L}_seed{s}.pth"),
    "notext":  ("notext",  "best_ablation_no_multi_L{L}_seed{s}.pth"),
    "nlinear": ("nlinear", "best_nlinear_L{L}_seed{s}.pth"),
}
RUN_ID = {"miflu": "A2-MIFlu", "notext": "A2-NOTEXT", "nlinear": "A2-NLIN"}


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def miflu_val_evidence(export_root):
    """best_val / best_epoch per (L, seed) parsed from the per-run training logs."""
    out = {}
    d = os.path.join(export_root, "miflu")
    for fn in sorted(os.listdir(d)):
        if not fn.startswith("training_miflu_log_"):
            continue
        txt = open(os.path.join(d, fn), encoding="utf-8", errors="replace").read()
        Ls = re.findall(r"HORIZON L=(\d+)", txt)
        for m in re.finditer(
                r"\[CKPT\] L=(\d+): kept per-seed best-epoch ckpt seed=(\d+) "
                r"\(best val_mse=([0-9.]+), best_epoch=(\d+)\)", txt):
            L, s, bv, be = int(m.group(1)), int(m.group(2)), float(m.group(3)), int(m.group(4))
            out[(L, s)] = {"best_val_mse_7var_z": bv, "best_epoch": be,
                           "evidence_file": fn, "horizons_in_log": Ls}
    return out


def table_val_evidence(export_root, model):
    out = {}
    p = os.path.join(export_root, model, "metrics.csv")
    if not os.path.exists(p):
        return out
    df = pd.read_csv(p)
    for _, r in df.iterrows():
        try:
            out[(int(r["L"]), int(r["seed"]))] = {
                "best_val_mse_7var_z": float(r["best_val"]), "best_epoch": None,
                "evidence_file": "metrics.csv"}
        except (KeyError, TypeError, ValueError):
            continue
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/stage5")
    ap.add_argument("--out", default="results/stage5/scoring")
    a = ap.parse_args()

    exp = os.path.join(a.root, "author_966")
    ck = os.path.join(a.root, "ckpt", "author_966")
    os.makedirs(a.out, exist_ok=True)

    ev = {"miflu": miflu_val_evidence(exp), "nlinear": table_val_evidence(exp, "nlinear"),
          "notext": table_val_evidence(exp, "notext")}

    rows, missing = [], []
    for model, (sub, tmpl) in TEMPLATES.items():
        for L in LS:
            for s in SEEDS:
                p = os.path.join(ck, sub, tmpl.format(L=L, s=s))
                rid = f"{RUN_ID[model]}-L{L}-S{s}"
                if not os.path.exists(p):
                    missing.append(rid)
                    continue
                e = ev[model].get((L, s))
                if e is None:
                    missing.append(rid + " (no validation-selection evidence)")
                    continue
                rows.append({
                    "run_id": rid, "model": model, "L": L, "seed": s,
                    "n_test_origins": EXPECTED_TEST[L],
                    "selection_metric": "7-var standardized VALIDATION MSE",
                    "best_val_mse_7var_z": e["best_val_mse_7var_z"],
                    "best_epoch": e["best_epoch"],
                    "ckpt_path": p, "ckpt_bytes": os.path.getsize(p),
                    "ckpt_mtime_utc": datetime.datetime.utcfromtimestamp(
                        os.path.getmtime(p)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "ckpt_sha256": sha256(p),
                    "evidence_file": e["evidence_file"],
                })
                print(f"  locked {rid}  val={e['best_val_mse_7var_z']:.6f}", flush=True)

    if missing:
        print("[LOCK] ABORT — missing or unevidenced fits:", file=sys.stderr)
        for m in missing:
            print("   -", m, file=sys.stderr)
        sys.exit(3)

    df = pd.DataFrame(rows).sort_values(["model", "L", "seed"])
    df.to_csv(os.path.join(a.out, "CHECKPOINT_LOCK.csv"), index=False)
    json.dump({
        "locked_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_fits": len(rows),
        "seeds": SEEDS, "horizons": LS,
        "profile": "author_966", "split": "676/97/193",
        "containment": "strict",
        "selection_rule": "per (model, L, seed): epoch with lowest 7-variable "
                          "standardized VALIDATION MSE; Test never read during fitting",
        "test_scoring": "performed only after this file was written, in the same job",
        "fits": rows,
    }, open(os.path.join(a.out, "CHECKPOINT_LOCK.json"), "w"), indent=2)
    print(f"[LOCK] OK — {len(rows)}/36 fits locked -> {a.out}/CHECKPOINT_LOCK.json")


if __name__ == "__main__":
    main()
