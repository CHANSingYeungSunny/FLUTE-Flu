#!/usr/bin/env python3
"""Track-B cell completeness check, by runner kind. No fabrication.

Usage:
  cellok.py check <cell_dir> <route>
  cellok.py count <export_root> <cells.tsv>
  cellok.py pending <export_root> <cells.tsv> <out.tsv>
Routes: miflu | backbone | encoder | classical
Exit 0=complete, 1=incomplete, 2=bad usage.
"""
import sys, os, glob, json, math, csv, zipfile

CLASSICAL = {"decision_tree", "gradient_boosting", "knn", "random_forest", "svr"}
BAD = {"nan", "inf", "-inf", "+inf", "infinity", "-infinity", "na", "n/a", "null", "none"}

def route_of(model, kind):
    if model == "miflu" or kind == "miflu":
        return "miflu"
    if model in CLASSICAL:
        return "classical"
    if kind == "encoder":
        return "encoder"
    return "backbone"

def finite_csv(path):
    try:
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            rows = [r for r in csv.reader(f) if r]
    except OSError:
        return False, "unreadable"
    if len(rows) < 2:
        return False, "no data rows"
    numeric = 0
    for r in rows[1:]:
        for v in r:
            s = v.strip().lower()
            if s in BAD:
                return False, "non-finite token %r" % v
            try:
                x = float(v)
            except ValueError:
                continue
            if not math.isfinite(x):
                return False, "non-finite float"
            numeric += 1
    if numeric == 0:
        return False, "no numeric values"
    return True, ""

def npz_ok(path):
    if not os.path.isfile(path) or os.path.getsize(path) < 1000:
        return False, "npz missing/tiny"
    if not zipfile.is_zipfile(path):
        return False, "npz not a valid archive"
    return True, ""

def check(cell, route):
    if not os.path.isdir(cell):
        return False, "no cell dir"
    if route == "miflu":
        res = glob.glob(os.path.join(cell, "results_*.csv"))
        plain = [p for p in res if "_table_" not in os.path.basename(p)]
        table = [p for p in res if "_table_" in os.path.basename(p)]
        # match by trailing YYYYMMDD_HHMMSS token
        import re
        def tok(p):
            m = re.search(r"(\d{8}_\d{6})\.csv$", os.path.basename(p))
            return m.group(1) if m else None
        pairs = [t for t in (tok(p) for p in plain) if t and t in {tok(q) for q in table}]
        if not pairs:
            return False, "no matched results pair"
        t = sorted(pairs)[-1]
        p_plain = [p for p in plain if tok(p) == t][0]
        p_table = [p for p in table if tok(p) == t][0]
        for p in (p_plain, p_table):
            ok, why = finite_csv(p)
            if not ok:
                return False, "results %s: %s" % (os.path.basename(p), why)
        preds = [p for p in glob.glob(os.path.join(cell, "predictions_*.csv")) if os.path.getsize(p) > 1000]
        if not preds:
            return False, "no predictions csv"
        ok, why = finite_csv(preds[0])
        if not ok:
            return False, "predictions: %s" % why
        mans = glob.glob(os.path.join(cell, "manifest_*.json"))
        if not mans:
            return False, "no manifest"
        try:
            with open(mans[0], encoding="utf-8") as f:
                m = json.load(f)
            if not isinstance(m, dict) or "slurm" not in m:
                return False, "manifest incomplete"
        except Exception as e:
            return False, "manifest bad json: %s" % e
        if not glob.glob(os.path.join(cell, "training_*log*.txt")):
            return False, "no training log"
        return True, ""
    if route == "classical":
        mj = os.path.join(cell, "metrics.json")
        if not os.path.isfile(mj):
            return False, "no metrics.json"
        try:
            with open(mj, encoding="utf-8") as f:
                m = json.load(f)
            if not isinstance(m, dict) or "test_mse_7var_z" not in m:
                return False, "metrics.json incomplete"
            for k in ("val_mse_7var_z", "test_mse_7var_z", "test_mse_ilitotal_z"):
                if k in m and (not isinstance(m[k], (int, float)) or not math.isfinite(float(m[k]))):
                    return False, "non-finite %s" % k
        except Exception as e:
            return False, "metrics.json bad: %s" % e
        nps = glob.glob(os.path.join(cell, "pred_*.npz"))
        return (npz_ok(nps[0]) if nps else (False, "no npz"))
    # backbone / encoder
    mc = os.path.join(cell, "metrics.csv")
    if not os.path.isfile(mc):
        return False, "no metrics.csv"
    ok, why = finite_csv(mc)
    if not ok:
        return False, "metrics.csv: %s" % why
    nps = glob.glob(os.path.join(cell, "pred_*.npz"))
    return (npz_ok(nps[0]) if nps else (False, "no npz"))

def read_cells(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            c = line.split("\t")
            model, L, seed = c[0], c[1], c[2]
            kind = c[3] if len(c) > 3 else "backbone"
            mid = c[4] if len(c) > 4 else ""
            rev = c[5] if len(c) > 5 else ""
            rows.append((model, L, seed, kind, mid, rev, route_of(model, kind)))
    return rows

def main():
    if len(sys.argv) < 2:
        return 2
    cmd = sys.argv[1]
    if cmd == "check":
        ok, why = check(sys.argv[2], sys.argv[3])
        print(("OK " if ok else "INCOMPLETE ") + why)
        return 0 if ok else 1
    if cmd == "route":
        print(route_of(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "backbone"))
        return 0
    if cmd not in ("count", "pending"):
        return 2
    root, cells = sys.argv[2], sys.argv[3]
    rows = read_cells(cells)
    complete, incomplete = [], []
    for (model, L, seed, kind, mid, rev, route) in rows:
        d = os.path.join(root, model, "L%s_s%s" % (L, seed))
        ok, why = check(d, route)
        (complete if ok else incomplete).append((model, L, seed, kind, mid, rev, route, why))
    sys.stdout.write("COMPLETE %d / %d\n" % (len(complete), len(rows)))
    if cmd == "pending":
        with open(sys.argv[4], "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            for r in incomplete:
                w.writerow(r[:7])
    else:
        from collections import Counter
        sys.stdout.write("BY_REASON %s\n" % json.dumps(dict(Counter(r[7] for r in incomplete)), sort_keys=True))
    return 0

if __name__ == "__main__":
    sys.exit(main())
