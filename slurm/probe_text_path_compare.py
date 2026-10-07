#!/usr/bin/env python3
"""Compare the CPU and GPU text-path probe JSONs and emit the comparison CSV.

Run this on the login node ONLY if it stays trivial; otherwise submit it as a
CPU-only job. It is pure JSON reading, no model, no GPU.
"""
import argparse, csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE),
                   "hpc_results", "official_repo_reproduction_20261006")

_ap = argparse.ArgumentParser()
_ap.add_argument("--out", default=OUT, help="directory holding the probe JSONs")
OUT = _ap.parse_args().out

FIELDS = [
    ("device", lambda r: r["device_name"]),
    ("dtype", lambda r: r["dtype"]),
    ("torch", lambda r: r["torch"]),
    ("author_commit", lambda r: r.get("author_commit")),
    ("all_parameters_sha256", lambda r: r.get("all_parameters_sha256")),
    ("input_sha256", lambda r: r["input"]["sha256"]),
    ("model_eval_mode", lambda r: r["model_eval_mode"]),
    ("any_dropout_training", lambda r: r["any_dropout_training"]),
    ("patch_num", lambda r: r["sequence_layout"]["patch_num"]),
    ("text_len", lambda r: r["sequence_layout"]["text_len"]),
    ("head_positions_read", lambda r: r["head"]["head_positions_read"]),
    ("max_abs_diff_equal_length_text_swap",
     lambda r: max(v["max_abs_prediction_difference"]
                   for v in r["prediction_differences"].values())),
    ("text_embedding_grad_norm", lambda r: r["gradients"]["text_embedding_grad_norm"]),
    ("time_series_embedding_grad_norm",
     lambda r: r["gradients"]["time_series_embedding_grad_norm"]),
    ("flag_control_max_abs_diff",
     lambda r: r.get("flag_control", {}).get("max_abs_prediction_difference")),
    ("positive_control_max_abs_diff",
     lambda r: r.get("positive_control", {}).get("max_abs_prediction_difference")),
    ("verdict", lambda r: r["verdict"]),
]


def main():
    paths = [("cpu", os.path.join(OUT, "text_path_probe_cpu.json")),
             ("gpu", os.path.join(OUT, "text_path_probe_gpu.json"))]
    # fall back to the locally produced names so the comparison table is still
    # useful (and honestly labelled MISSING) before the HPC halves exist
    if not os.path.exists(paths[0][1]):
        alt = os.path.join(OUT, "text_path_probe_cpu_local.json")
        if os.path.exists(alt):
            paths[0] = ("cpu", alt)
    rows = []
    for label, p in paths:
        if not os.path.exists(p):
            rows.append({"run": label, "status": "MISSING", "path": p})
            continue
        r = json.load(open(p))
        row = {"run": label, "status": "OK", "path": p}
        for name, fn in FIELDS:
            try:
                row[name] = fn(r)
            except Exception as e:
                row[name] = f"ERR:{e}"
        rows.append(row)

    out = os.path.join(OUT, "text_path_probe_comparison.csv")
    keys = ["run", "status", "path"] + [n for n, _ in FIELDS]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}")
    for row in rows:
        print(row.get("run"), row.get("status"), row.get("verdict"))

    ok = [r for r in rows if r["status"] == "OK"]
    if len(ok) == 2:
        same = (ok[0]["verdict"] == ok[1]["verdict"])
        print(f"CPU/GPU verdicts {'AGREE' if same else 'DISAGREE'}: "
              f"{ok[0]['verdict']} vs {ok[1]['verdict']}")
        if not same:
            print("DISAGREEMENT -> localise via: parameters_sha256, input_sha256, "
                  "dtype, dropout state, head_positions_read, torch version")
            sys.exit(1)


if __name__ == "__main__":
    main()
