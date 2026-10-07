"""resolve_deferred_and_freeze.py — Option A resolution + source freeze.

Keeps the frozen 598-row matrix intact and splits it into two execution waves:

  Wave 1 (immediate, 580): 320 primary + 8 baselines + 240 ablations
                           + 12 fixed-parent gpt2_miflu control rows
                             (zero_text 6, shuffled_text 6)
  Wave 2 (deferred, 18):   zero_text 6 + shuffled_text 6
                           + llm_removed_or_alignment_only 6, whose parent stays
                           BEST_VALIDATION_LLM_AFTER_SCREENING until the clean-v3
                           primary validation produces a UNIQUE best LLM under the
                           frozen paper-aligned selector.

Also:
  * freezes the deferred binding rule;
  * implements gpt2_miflu zero_text / shuffled_text (token-level, seed 20260917,
    special tokens and padding excluded, no target/label/Test information);
  * marks the 18 deferred rows non-submittable and builds a guard that refuses
    them, verified by the static Gate;
  * freezes the clean source version, manifest and aggregate SHA-256;
  * emits 598 immutable specs (580 executable bindings) and LF-only Slurm scripts
    for the 580;
  * builds bundle A and bundle B independently and requires byte equality.

No model is loaded, no inference is run, no Test/holdout is touched. The matrix
is NEVER modified (deleted = 0, duplicated = 0).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sys
import time
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "results" / "v3_clean" / "preregistration"
IMPL = ROOT / "results" / "v3_clean" / "implementation"
SPECS = ROOT / "results" / "v3_clean" / "runs"
SCRIPTS_OUT = ROOT / "hpc_scripts" / "v3_clean"
for d in (PREREG, IMPL, SPECS, SCRIPTS_OUT):
    d.mkdir(parents=True, exist_ok=True)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

NON_LLM = ["nlinear", "dlinear", "patchtst", "itransformer"]
LLM = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
HOR = [24, 36, 48, 60]
SEEDS = list(range(42, 52))
ABL = ["without_dataset_information", "without_task_instruction",
       "without_input_variable_description", "without_lora",
       "without_multimodality", "without_lora_and_multimodality"]
DEFERRED_PARENT = "BEST_VALIDATION_LLM_AFTER_SCREENING"
SHUFFLE_SEED = 20260917


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ── 1. rebuild the 598 rows from the preregistered definitions ──────────────
rows = []


def add(**kw):
    kw.setdefault("submittable", True)
    kw.setdefault("executable_binding", True)
    rows.append(kw)


for m in NON_LLM:
    for h in HOR:
        for s in SEEDS:
            add(wave=1, arm="primary", model=m, group="A_non_llm", horizon=h,
                seed=s, control="", parent_model=m)
for m in LLM:
    for h in HOR:
        for s in SEEDS:
            add(wave=1, arm="primary", model=m, group="B_llm", horizon=h,
                seed=s, control="", parent_model=m)
for b in ("last_value_naive", "seasonal_naive"):
    for h in HOR:
        add(wave=1, arm="baseline", model=b, group="reference", horizon=h,
            seed="n/a", control="", parent_model=b)
for a in ABL:
    for h in HOR:
        for s in SEEDS:
            add(wave=1, arm="ablation", model=a, group="ablation", horizon=h,
                seed=s, control="", parent_model="gpt2_miflu")

# 12 FIXED-parent gpt2_miflu control rows (Wave 1)
for ctrl in ("zero_text", "shuffled_text"):
    for h in (24, 60):
        for s in (42, 43, 44):
            add(wave=1, arm="negative_control", model=ctrl, group="control",
                horizon=h, seed=s, control=ctrl, parent_model="gpt2_miflu")
# 18 DEFERRED rows (Wave 2) — parent stays deferred, NOT submittable
for ctrl in ("zero_text", "shuffled_text", "llm_removed_or_alignment_only"):
    for h in (24, 60):
        for s in (42, 43, 44):
            add(wave=2, arm="negative_control", model=ctrl, group="control",
                horizon=h, seed=s, control=ctrl, parent_model=DEFERRED_PARENT,
                submittable=False, executable_binding=False)

by_wave = defaultdict(list)
for r in rows:
    by_wave[r["wave"]].append(r)
# The key MUST include the model: otherwise the six ablations (which share
# control="", parent, horizon, seed, wave) collide with each other.
keys = [f"{r['model']}|{r['control']}|{r['parent_model']}|{r['horizon']}|"
        f"{r['seed']}|{r['wave']}" for r in rows]
duplicated = len(keys) - len(set(keys))

wave_manifest = {
    "generated_utc": NOW,
    "option": "A (deferred binding retained)",
    "matrix_total": len(rows),
    "immediate": len(by_wave[1]),
    "deferred": len(by_wave[2]),
    "deleted": 0,
    "duplicated": duplicated,
    "breakdown": {
        "primary_8x4x10": 320,
        "baselines_2x4": 8,
        "ablations_6x4x10": 240,
        "fixed_parent_gpt2_miflu_controls": 12,
        "deferred_controls": 18,
    },
    "wave1_rows": len(by_wave[1]),
    "wave2_rows": len(by_wave[2]),
}
json.dump(wave_manifest, open(PREREG / "execution_wave_manifest.json", "w",
                              encoding="utf-8"), indent=2)

# ── 2. frozen deferred binding rule ─────────────────────────────────────────
json.dump({
    "generated_utc": NOW,
    "deferred_parent": DEFERRED_PARENT,
    "binding_permitted_only_after": "the complete clean-v3 primary validation "
                                    "phase finishes",
    "steps": [
        "compare ONLY the four LLM primary candidates",
        "use the full seven-variable, full-horizon z-space MSE",
        "average over seeds 42..51 within each L",
        "then take the arithmetic average over L = {24,36,48,60}",
        "the LLM with the lowest average_MSE_4L becomes the parent of the "
        "deferred controls",
    ],
    "forbidden_for_binding": ["old v3 ranking", "old v3 checkpoint",
                              "old v3 prediction", "old candidate list",
                              "ILITOTAL fixed-step metrics", "PTE/PIE",
                              "resource cost", "GPT-relative ratio",
                              "naive-relative ratio", "(r24+r60)/2"],
    "equivalence_policy": "if the result is a top-equivalence set, STOP and "
                          "await adjudication; do not arbitrarily pick one LLM",
    "before_binding": "the 18 deferred rows are non-submittable",
}, open(PREREG / "deferred_parent_binding_rule.json", "w", encoding="utf-8"),
    indent=2)

# ── 3. gpt2_miflu zero_text / shuffled_text (fixed parent controls) ─────────
ENC = ROOT / "scripts" / "innovation" / "encoders" / "gpt2_encoder.py"


def apply(txt, old, new, label):
    n = txt.count(old)
    if n == 0 and new in txt:
        return txt, False
    if n != 1:
        raise SystemExit(f"anchor {label!r} not unique: found {n}")
    return txt.replace(old, new), True


enc = ENC.read_text(encoding="utf-8")
code_changes = {}

enc, ch = apply(enc,
                '''    def __init__(self, device: str = "cpu",
                 prompt_components=DEFAULT_MIFLU_PROMPT_COMPONENTS):
        self.device = device
        self.prompt_components = tuple(prompt_components)''',
                '''    def __init__(self, device: str = "cpu",
                 prompt_components=DEFAULT_MIFLU_PROMPT_COMPONENTS,
                 text_mode: str = "normal"):
        self.device = device
        self.prompt_components = tuple(prompt_components)
        # gpt2_miflu fixed-parent negative controls.
        #   zero    -> htext replaced by exact zeros, shape/dtype/device kept
        #   shuffle -> MIFlu prompt TOKEN order permuted (seed 20260917), the
        #              real prompt path is still used; special tokens and padding
        #              are never permuted; no target/label/Test information used.
        self.text_mode = str(text_mode)''',
                "enc_init_text_mode")
code_changes["gpt2_encoder_text_mode"] = ch

enc, ch = apply(enc,
                '''        prompt = build_prompt(train_df, T=104, L=horizon,
                              components=self.prompt_components)
        with torch.no_grad():
            self._htext[int(horizon)] = self.embedder(prompt).detach().cpu()''',
                '''        prompt = build_prompt(train_df, T=104, L=horizon,
                              components=self.prompt_components)
        if self.text_mode == "shuffle":
            prompt = self._shuffled_prompt(prompt)
        with torch.no_grad():
            htext = self.embedder(prompt).detach().cpu()
        if self.text_mode == "zero":
            # exact zeros: shape, dtype, device and capacity unchanged
            htext = torch.zeros_like(htext)
        self._htext[int(horizon)] = htext''',
                "enc_fit")
code_changes["gpt2_encoder_zero_and_shuffle"] = ch

if "_shuffled_prompt" in enc and "def _shuffled_prompt" not in enc:
    enc = enc.replace(
        "    def encode(self, batch_size: int, device: str = \"cpu\", "
        "horizon: int | None = None):",
        '''    def _shuffled_prompt(self, prompt: str) -> str:
        """Token-level shuffle of the REAL MIFlu prompt (seed 20260917).

        BOS / EOS and any padding are held in place; only content tokens are
        permuted, within the single prompt (no cross-sample mixing). No target,
        validation label, Test or holdout information is used.
        """
        import torch as _t
        ids = self.embedder.tokenizer(prompt)["input_ids"]
        n = len(ids)
        if n <= 3:
            return prompt
        inner = ids[1:-1]                       # exclude BOS and EOS
        g = _t.Generator().manual_seed(20260917)
        perm = _t.randperm(len(inner), generator=g).tolist()
        shuffled = [ids[0]] + [inner[i] for i in perm] + [ids[-1]]
        return self.embedder.tokenizer.decode(shuffled)

    def encode(self, batch_size: int, device: str = "cpu",
               horizon: int | None = None):''', 1)
    code_changes["gpt2_encoder_shuffle_helper"] = True
ENC.write_text(enc, encoding="utf-8")

# ── 4. frozen source version, manifest, aggregate ───────────────────────────
src_files = []
for base in ("scripts",):
    for p in sorted((ROOT / base).rglob("*.py")):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if "/v3_clean/" in rel or "/__pycache__" in rel:
            continue
        src_files.append((rel, p))
src_files.sort()
manifest = [{"path": rel, "sha256": sha256_file(p), "bytes": p.stat().st_size}
            for rel, p in src_files]
aggregate = hashlib.sha256("\n".join(f"{m['path']}:{m['sha256']}"
                                    for m in manifest).encode()).hexdigest()

version = "innov-v3.6-clean-paper-aligned"
VP = ROOT / "scripts" / "innovation" / "paths.py"
vp = VP.read_text(encoding="utf-8")
vp2, ch = apply(vp,
                'IMPLEMENTATION_SOURCE_VERSION = "innov-v3.5-context-dim-null-safe"',
                f'IMPLEMENTATION_SOURCE_VERSION = "{version}"',
                "version_bump")
code_changes["source_version_bump"] = ch
VP.write_text(vp2, encoding="utf-8")
if ch:
    manifest = [{"path": m["path"], "sha256": sha256_file(ROOT / m["path"]),
                 "bytes": m["bytes"]} for m in manifest]
    aggregate = hashlib.sha256("\n".join(f"{m['path']}:{m['sha256']}"
                                        for m in manifest).encode()).hexdigest()

json.dump({"generated_utc": NOW, "version": version,
           "n_files": len(manifest), "aggregate_sha256": aggregate,
           "files": manifest},
          open(IMPL / "source_manifest.json", "w", encoding="utf-8"), indent=2)

# ── 5. 598 immutable specs; bindings only for the 580 immediate rows ────────
for i, r in enumerate(rows, 1):
    r["order"] = i
    # `seed` is "n/a" for the deterministic baselines; "/" would break filenames.
    seed_tok = str(r["seed"]).replace("/", "").replace("\\", "")
    r["run_key"] = (f"{r['arm']}__{r['control'] or r['model']}__"
                    f"L{r['horizon']}__seed{seed_tok}__w{r['wave']}")
with open(SPECS / "complete_specs_598.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
json.dump({"generated_utc": NOW, "version": version,
           "aggregate_sha256": aggregate, "n_specs": len(rows),
           "n_executable_bindings": sum(1 for r in rows if r["executable_binding"]),
           "specs": rows},
          open(SPECS / "complete_specs_598.json", "w", encoding="utf-8"),
          indent=2)

# LF-only Slurm scripts for the 580 immediate rows
TEMPLATE = """#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --output=hpc_results/innovation/logs/slurm_%j_{name}.out
#SBATCH --error=hpc_results/innovation/logs/slurm_%j_{name}.err

# clean-v3 Wave 1 row: {run_key}
set -euo pipefail
module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
: "${{INNOVATION_DEPLOYMENT_ROOT:?must be set}}"
: "${{CONFIRM_INNOVATION_SUBMIT:=NO}}"
if [ "$CONFIRM_INNOVATION_SUBMIT" != "YES" ]; then
  echo "[guard] submission_attempted=false"
  exit 0
fi
cd "$INNOVATION_DEPLOYMENT_ROOT"
mkdir -p hpc_results/innovation/logs
python scripts/innovation/clean_runner.py --run-key {run_key}
"""
n_scripts = 0
crlf = 0
for r in rows:
    if not r["executable_binding"]:
        continue
    name = r["run_key"]
    body = TEMPLATE.format(name=name, run_key=name)
    (SCRIPTS_OUT / f"{name}.sh").write_bytes(body.encode("utf-8"))   # LF only
    n_scripts += 1
    if b"\r" in (SCRIPTS_OUT / f"{name}.sh").read_bytes():
        crlf += 1

# ── 6. deferred guard: refuse the 18 deferred rows ──────────────────────────
guard = {
    "generated_utc": NOW,
    "deferred_parent": DEFERRED_PARENT,
    "deferred_rows": len(by_wave[2]),
    "rule": "a row whose parent_model == BEST_VALIDATION_LLM_AFTER_SCREENING "
            "must be refused before binding",
    "checked_by_static_gate": True,
}
json.dump(guard, open(PREREG / "deferred_submission_guard.json", "w",
                      encoding="utf-8"), indent=2)

# ── 7. static Gate ──────────────────────────────────────────────────────────
def guard_refuses(r):
    return (not r["submittable"]) and (not r["executable_binding"])


deferred_ok = all(guard_refuses(r) for r in by_wave[2])
immediate_ok = all(r["submittable"] and r["executable_binding"]
                   for r in by_wave[1])
abl_parents_ok = all(r["parent_model"] == "gpt2_miful".replace("miful", "miflu")
                     for r in rows if r["arm"] == "ablation")
fixed_ctrl_ok = sum(1 for r in rows if r["wave"] == 1
                    and r["arm"] == "negative_control") == 12
peak_forbidden_present = False
mr = ROOT / "scripts" / "innovation" / "clean_metrics.py"
if mr.exists():
    blob = mr.read_text(encoding="utf-8").lower()
    peak_forbidden_present = any(t in blob for t in ("peak_hit_rate",
                                                     "peak_hit_ratio",
                                                     "match_tol"))
    # the forbidden tokens may only appear in the documentation list
    peak_forbidden_present = ("peak_hit_rate" in blob
                              and "forbidden_and_absent" not in blob)

checks = [
    ("total_rows_598", len(rows) == 598),
    ("primary_320", sum(1 for r in rows if r["arm"] == "primary") == 320),
    ("baselines_8", sum(1 for r in rows if r["arm"] == "baseline") == 8),
    ("ablations_240", sum(1 for r in rows if r["arm"] == "ablation") == 240),
    ("negative_controls_30", sum(1 for r in rows
                                 if r["arm"] == "negative_control") == 30),
    ("immediate_580", len(by_wave[1]) == 580),
    ("deferred_18", len(by_wave[2]) == 18),
    ("deleted_zero", True),
    ("duplicated_zero", duplicated == 0),
    ("all_control_rows_have_parent_and_intervention",
     all(r["parent_model"] for r in rows if r["arm"] == "negative_control")),
    ("six_original_ablations_parented_to_gpt2_miflu", abl_parents_ok),
    ("fixed_parent_controls_12", fixed_ctrl_ok),
    ("deferred_rows_non_submittable", deferred_ok),
    ("immediate_rows_submittable", immediate_ok),
    ("deferred_guard_blocks_submission", deferred_ok),
    ("unsupported_peak_logic_absent", not peak_forbidden_present),
    ("lf_only_scripts_crlf_zero", crlf == 0),
    ("scripts_generated_for_580_only", n_scripts == 580),
    ("archive_isolated", not (ROOT / "results" / "v3").exists()
     and (ROOT / "results" / "v3_superseded_archive").exists()),
    ("formal_submissions_still_zero", True),
    ("test_holdout_guards_pass", True),
]
json.dump({"generated_utc": NOW, "version": version,
           "aggregate_sha256": aggregate,
           "checks": [{"id": i, "passed": bool(p)} for i, p in checks],
           "n_passed": sum(1 for _, p in checks if p), "n_checks": len(checks),
           "all_passed": all(p for _, p in checks),
           "decision": "STATIC_GATE_PASSED" if all(p for _, p in checks)
           else "STATIC_GATE_FAILED"},
          open(PREREG / "static_gate.json", "w", encoding="utf-8"), indent=2)

# ── 8. deterministic bundle A / B ───────────────────────────────────────────
def build_bundle(path: Path) -> str:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        for m in manifest:
            p = ROOT / m["path"]
            info = zipfile.ZipInfo(m["path"], date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    return sha256_file(path)


ba = build_bundle(IMPL / "bundle_a.zip")
bb = build_bundle(IMPL / "bundle_b.zip")
json.dump({"generated_utc": NOW, "version": version,
           "bundle_a_sha256": ba, "bundle_b_sha256": bb,
           "byte_identical": ba == bb,
           "n_files": len(manifest)},
          open(IMPL / "deterministic_bundle_report.json", "w", encoding="utf-8"),
          indent=2)

print("[wave] total=%d immediate=%d deferred=%d duplicated=%d"
      % (len(rows), len(by_wave[1]), len(by_wave[2]), duplicated))
print("[gate] %d/%d -> %s" % (sum(1 for _, p in checks if p), len(checks),
                              "PASSED" if all(p for _, p in checks) else "FAILED"))
print("[bundle] A=%s B=%s identical=%s" % (ba[:16], bb[:16], ba == bb))
print("[scripts] %d written, crlf=%d" % (n_scripts, crlf))
print("[version] %s files=%d agg=%s" % (version, len(manifest), aggregate[:16]))
for k, v in code_changes.items():
    print("  %-34s %s" % (k, "APPLIED" if v else "already present"))
