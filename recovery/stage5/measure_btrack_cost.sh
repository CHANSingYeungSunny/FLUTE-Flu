#!/bin/bash
# Aggregate MEASURED per-fit train_seconds from the B-track durable screening
# runs, per (model, horizon). Read-only; login node; touches ~600 small JSONs.
R=/home/sychan552/innovation_durable/screening
/home/sychan552/.conda/envs/mlflu_hpc/bin/python - "$R" <<'PY'
import json, os, sys, statistics, collections
R = sys.argv[1]


def _i(x, d=0):
    try:
        return int(x)
    except (TypeError, ValueError):
        return d


rows = []
for d in sorted(os.listdir(R)):
    p = os.path.join(R, d, "resource_usage.json")
    q = os.path.join(R, d, "run_status.json")
    if not (os.path.exists(p) and os.path.exists(q)):
        continue
    try:
        ru = json.load(open(p))
        st = json.load(open(q))
    except Exception:
        continue
    if st.get("state") != "COMPLETED":
        continue
    spec = st.get("spec", {})
    ts = ru.get("train_seconds")
    if ts is None:
        continue
    rows.append((spec.get("model"), _i(spec.get("horizon")),
                 _i(spec.get("seed")), float(ts),
                 ru.get("trainable_parameters")))
by = collections.defaultdict(list)
for m, L, s, ts, tp in rows:
    by[(m, L)].append((s, ts, tp))
print(f"{'model':<18}{'L':>4}{'n':>4}{'mean_s':>10}{'median_s':>10}{'min_s':>9}{'max_s':>9}  trainable")
agg = collections.defaultdict(dict)
for (m, L), v in sorted(by.items()):
    t = [x[1] for x in v]
    tp = v[0][2]
    print(f"{m:<18}{L:>4}{len(t):>4}{statistics.mean(t):>10.1f}"
          f"{statistics.median(t):>10.1f}{min(t):>9.1f}{max(t):>9.1f}  {tp}")
    agg[m][L] = statistics.mean(t)
print()
print("=== projected 4-L x 3-seed cost per model (12 fits), B-track measured means ===")
print(f"{'model':<18}{'sum_s':>10}{'GPU-h':>9}")
tot = 0.0
for m, d in sorted(agg.items()):
    s12 = sum(d.values()) * 3
    tot += s12
    print(f"{m:<18}{s12:>10.1f}{s12/3600:>9.4f}")
print(f"{'TOTAL(8 models)':<18}{tot:>10.1f}{tot/3600:>9.4f}")
print()
print("=== per-model average seconds per fit (all 4 L) ===")
for m, d in sorted(agg.items()):
    print(f"  {m:<18} {sum(d.values())/len(d):>8.1f} s/fit")
PY
