# -*- coding: utf-8 -*-
"""Stage 5 — fix FIT/EVAL classification, freeze the protocol, emit hashes (CPU only)."""
import csv
import hashlib
import io
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S4 = os.path.join(ROOT, "recovery", "stage4")
S5 = os.path.join(ROOT, "recovery", "stage5")
os.makedirs(S5, exist_ok=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- 1. matrix
src = os.path.join(S4, "reduced_run_matrix.csv")
with io.open(src, "r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

LEARNED = {"corrected_miflu", "no_text", "nlinear"}
NAIVE = {"last_value", "seasonal_naive"}

for r in rows:
    v = r["variant"]
    if v in LEARNED:
        r["class"] = "NEW_FIT"
    elif v in NAIVE:
        r["class"] = "NEW_EVAL"
    else:
        r["class"] = "UNKNOWN"
    # D-adapter / D-nlinear are resolved in Stage 4; only D-compute remains gating.
    r["status"] = "PREPARED"
    r["blocked_by"] = "D-compute (GPU-hour ceiling + queue not yet authorized)"
    r["containment"] = "strict"

n_fit = sum(1 for r in rows if r["class"] == "NEW_FIT")
n_eval = sum(1 for r in rows if r["class"] == "NEW_EVAL")
assert n_fit == 36 and n_eval == 8, (n_fit, n_eval)

ids = [r["run_id"] for r in rows]
assert len(ids) == len(set(ids)), "duplicate run_id"

seeds = sorted({r["seed"] for r in rows if r["class"] == "NEW_FIT"})
assert seeds == ["42", "43", "44"], seeds

fields = list(rows[0].keys())
out_csv = os.path.join(S5, "final_run_matrix.csv")
with io.open(out_csv, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

# A0 stays separate and blocked
a0 = {
    "run_id": "A0-01", "track": "A", "variant": "author_released_code",
    "scientific_question": "Does the released author code reproduce its own Table V?",
    "horizon": 24, "seed": 42, "T": 104, "data_profile": "author_966",
    "split_convention": "author_676_97_193", "selection": "author Test MSE (as released)",
    "entry_point": "recovery/author_repo/main_ILI_lora.py", "class": "BLOCKED",
    "status": "BLOCKED", "blocked_by": "D-a0-env (GPU node + author gpt2 cache + author repo data path)",
    "containment": "n/a (released code)", "gpu_hours_est": "unknown (full fine-tune, never run)",
    "notes": "quoted-field fix retained; not counted in the 44-row A2 matrix",
}
with io.open(os.path.join(S5, "a0_diagnostic_record.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(a0.keys()))
    w.writeheader()
    w.writerow(a0)

print("matrix rows: %d (%d NEW_FIT + %d NEW_EVAL); A0 separate BLOCKED" % (len(rows), n_fit, n_eval))

# ---------------------------------------------------------------- 2. hashes
code_dir = os.path.join(ROOT, "scripts")
code_files = ["configs.py", "train_miflu.py", "train_ablation.py", "train_nlinear_966.py",
              "train_naive_966.py", "textual_embedder.py", "scaler_utils.py", "cdc_calendar.py"]
code_hashes = {}
for name in code_files:
    p = os.path.join(code_dir, name)
    if os.path.exists(p):
        code_hashes[name] = sha256(p)

data_files = {
    "author_processed_966": "recovery/author_repo/dataset/illness/national_illness.csv",
    "author_orig_966": "recovery/author_repo/dataset/illness/national_illness_orig.csv",
    "project_raw_1025": "data/raw/national_illness_raw.csv",
    "paper_exact_966": "data/raw/national_illness_raw_paper_exact.csv",
}
data_hashes = {}
for key, rel in data_files.items():
    p = os.path.join(ROOT, rel)
    if os.path.exists(p):
        data_hashes[key] = {"path": rel, "sha256": sha256(p),
                            "n_rows": sum(1 for _ in io.open(p, "r", encoding="utf-8")) - 1}

proto_files = {
    "a2_frozen_protocol": "recovery/stage3/configs/a2_frozen_protocol.json",
    "author_966_profile": "recovery/stage3/configs/author_966_profile.json",
}
proto_hashes = {}
for key, rel in proto_files.items():
    p = os.path.join(ROOT, rel)
    if os.path.exists(p):
        proto_hashes[key] = {"path": rel, "sha256": sha256(p)}

h = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "note": "full SHA-256 values; abbreviated hashes in earlier reports must not be reused",
    "code": code_hashes,
    "data": data_hashes,
    "protocol_config": proto_hashes,
    "window_containment": "strict (Stage 5 section 2.2); legacy 'start' retained as default for old runs",
    "window_counts_author_966": {"24": [549, 74, 170], "36": [537, 62, 158],
                                 "48": [525, 50, 146], "60": [513, 38, 134]},
}
with io.open(os.path.join(S5, "hashes_stage5.json"), "w", encoding="utf-8") as f:
    json.dump(h, f, indent=2)
print("hashes written for %d code files, %d data files" % (len(code_hashes), len(data_hashes)))
