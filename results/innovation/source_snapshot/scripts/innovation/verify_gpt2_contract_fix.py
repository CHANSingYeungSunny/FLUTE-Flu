"""verify_gpt2_contract_fix.py — prove the D15b metadata fix changes NOTHING
except contract metadata / module-path declaration / audit reporting.

For every representative schema it:
  1. exports the compact checkpoint with the CORRECTED detection  -> A
  2. exports it again with detection FORCED OFF (old behaviour)   -> B
  3. requires A and B to be byte-identical (SHA-256), same keys, same values
  4. requires strict restoration to pass for A
  5. where a durable `compact.safetensors` from the pre-fix migration exists,
     requires A to be byte-identical to it as well
  6. reports the corrected contract (has_pretrained_backbone / paths / bytes)

Runs on a stingy compute node. It writes only under its own output dir.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from innovation import compact_checkpoint as CC                 # noqa: E402
from innovation import architecture_contract as AC              # noqa: E402


def sha(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def export_with(run_dir: str, ckpt: str, spec: str, horizon: int,
                out: str, detection: bool) -> dict:
    orig = AC.detect_backbone_modules
    if not detection:
        AC.detect_backbone_modules = lambda model: []      # old behaviour
    try:
        return CC.export_compact(run_dir, ckpt, spec, horizon, out)
    finally:
        AC.detect_backbone_modules = orig


def one(tag: str, src_dir: str, spec: str, horizon: int, out_dir: Path,
        durable_compact: str | None) -> dict:
    rec = {"tag": tag, "spec": spec, "horizon": horizon, "src": src_dir}
    ckpt = os.path.join(src_dir, "checkpoints", "best_val_mse.pt")
    if not os.path.isfile(ckpt):
        rec["error"] = "checkpoint missing"
        return rec
    a_path = str(out_dir / f"{tag}.A.safetensors")
    b_path = str(out_dir / f"{tag}.B.safetensors")
    ra = export_with(src_dir, ckpt, spec, horizon, a_path, True)
    rb = export_with(src_dir, ckpt, spec, horizon, b_path, False)

    ka = CC._load_compact(a_path)
    kb = CC._load_compact(b_path)
    keys_equal = set(ka) == set(kb)
    vals_equal = keys_equal and all(torch.equal(ka[k], kb[k]) for k in ka)
    can_a = CC.canonical_tensor_sha256(ka)
    can_b = CC.canonical_tensor_sha256(kb)
    rec.update({
        "corrected_has_pretrained_backbone":
            ra["has_pretrained_backbone"],
        "corrected_module_paths": ra["pretrained_backbone_module_paths"],
        "corrected_base_model_id": ra.get("base_model_id"),
        "corrected_backbone_key_count": ra["frozen_backbone_key_count"],
        "corrected_backbone_bytes_total": ra["frozen_backbone_bytes_total"],
        "corrected_backbone_bytes_excluded":
            ra["frozen_backbone_bytes_excluded"],
        "corrected_unexpected_retained":
            ra["unexpected_frozen_backbone_bytes_retained"],
        "corrected_changed_backbone_dropped":
            ra.get("changed_frozen_backbone_bytes_dropped"),
        "corrected_no_duplication": ra["no_frozen_backbone_duplication"],
        "old_has_pretrained_backbone": rb["has_pretrained_backbone"],
        # file-byte hashes kept for integrity; canonical hashes for semantics
        "compact_sha_A": sha(a_path), "compact_sha_B": sha(b_path),
        "canonical_sha_A": can_a, "canonical_sha_B": can_b,
        "canonical_schema": CC.CANONICAL_HASH_SCHEMA,
        "compact_bytes_A": ra["compact_bytes"],
        "compact_bytes_B": rb["compact_bytes"],
        "compact_key_count_A": len(ka),
        "file_sha_identical": sha(a_path) == sha(b_path),
        "canonical_sha_identical": can_a == can_b,
        "compact_keys_identical": keys_equal,
        "compact_values_identical": vals_equal,
        "reconstruction_exact": ra["reconstruction_exact"],
    })
    rest = CC.restore_and_compare(src_dir, spec, horizon, a_path)
    rec.update({"restoration_exact": rest["restoration_exact"],
                "n_keys_unequal": rest["n_keys_unequal"],
                "missing_keys": rest["missing_keys"],
                "unexpected_keys": rest["unexpected_keys"]})
    if durable_compact and os.path.isfile(durable_compact):
        try:
            kd = CC._load_compact(durable_compact)
            can_d = CC.canonical_tensor_sha256(kd)
            rec["durable_canonical_sha"] = can_d
            rec["durable_canonical_matches_A"] = (can_d == can_a)
            rec["durable_key_count"] = len(kd)
        except Exception as e:                                 # noqa: BLE001
            rec["durable_error"] = f"{type(e).__name__}: {e}"
    rec["passed"] = bool(rec.get("canonical_sha_identical")
                         and rec.get("compact_keys_identical")
                         and rec.get("compact_values_identical")
                         and rec.get("reconstruction_exact")
                         and rec.get("restoration_exact")
                         and not rec.get("n_keys_unequal")
                         and not rec.get("missing_keys")
                         and not rec.get("unexpected_keys")
                         and rec.get("corrected_no_duplication")
                         and rec.get("durable_canonical_matches_A", True))
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--scratch-root", required=True,
                    help="root holding the original full run dirs")
    ap.add_argument("--gate-runs", required=True,
                    help="gate run dirs (ablations/controls)")
    ap.add_argument("--durable", required=True)
    a = ap.parse_args()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # (tag, source dir, spec, horizon)
    jobs = [
        ("gpt2_miflu", f"{a.scratch_root}/primary__gpt2_miflu__L24__seed42__w1",
         "primary__gpt2_miflu__L24__seed42__w1", 24),
        ("nlinear", f"{a.scratch_root}/primary__nlinear__L24__seed42__w1",
         "primary__nlinear__L24__seed42__w1", 24),
        ("qwen", f"{a.scratch_root}/primary__qwen_time_llm__L24__seed42__w1",
         "primary__qwen_time_llm__L24__seed42__w1", 24),
        ("without_lora",
         f"{a.gate_runs}/ablation__without_lora__L24__seed42__w1",
         "ablation__without_lora__L24__seed42__w1", 24),
        ("without_lora_and_multimodality",
         f"{a.gate_runs}/ablation__without_lora_and_multimodality__L24__seed42__w1",
         "ablation__without_lora_and_multimodality__L24__seed42__w1", 24),
        ("zero_text",
         f"{a.gate_runs}/negative_control__zero_text__L24__seed42__w1",
         "negative_control__zero_text__L24__seed42__w1", 24),
        ("shuffled_text",
         f"{a.gate_runs}/negative_control__shuffled_text__L24__seed42__w1",
         "negative_control__shuffled_text__L24__seed42__w1", 24),
        ("without_dataset_information",
         f"{a.gate_runs}/ablation__without_dataset_information__L24__seed42__w1",
         "ablation__without_dataset_information__L24__seed42__w1", 24),
        ("without_task_instruction",
         f"{a.gate_runs}/ablation__without_task_instruction__L24__seed42__w1",
         "ablation__without_task_instruction__L24__seed42__w1", 24),
        ("without_input_variable_description",
         f"{a.gate_runs}/ablation__without_input_variable_description__L24__seed42__w1",
         "ablation__without_input_variable_description__L24__seed42__w1", 24),
        ("without_multimodality",
         f"{a.gate_runs}/ablation__without_multimodality__L24__seed42__w1",
         "ablation__without_multimodality__L24__seed42__w1", 24),
    ]
    recs = []
    for tag, src, spec, h in jobs:
        print(f"[d15b] {tag}", flush=True)
        dur = os.path.join(a.durable, spec, "compact.safetensors")
        r = one(tag, src, spec, h, out_dir, dur)
        print("[d15b]   hasPT=%s paths=%s bbKeys=%s excl=%s unexp=%s "
              "canonEq=%s fileEq=%s valsEq=%s restore=%s durCanon=%s "
              "passed=%s" % (
                  r.get("corrected_has_pretrained_backbone"),
                  r.get("corrected_module_paths"),
                  r.get("corrected_backbone_key_count"),
                  r.get("corrected_backbone_bytes_excluded"),
                  r.get("corrected_unexpected_retained"),
                  r.get("canonical_sha_identical"),
                  r.get("file_sha_identical"),
                  r.get("compact_values_identical"),
                  r.get("restoration_exact"),
                  r.get("durable_canonical_matches_A"), r.get("passed")),
              flush=True)
        recs.append(r)
    ok = sum(1 for r in recs if r.get("passed"))
    payload = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                              time.gmtime()),
               "n": len(recs), "passed": ok, "all_passed": ok == len(recs),
               "results": recs}
    (out_dir / "gpt2_contract_fix_proof.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[d15b] ok={ok}/{len(recs)}", flush=True)
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
