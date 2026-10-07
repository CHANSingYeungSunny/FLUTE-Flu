# F1 FINAL EXECUTION GATE

Generated 2026-10-06, immediately before execution.
**Authorization**: 0.60 GPU-h, new and independent; the previous round's 0.05639 remainder
is **not** carried over.

## Verdict after correction: **ALL 11 GATES PASS**

One gate **failed on the first pass** and required a fix. That failure, its diagnosis and
the correction are recorded in §2 rather than being hidden.

---

## 1. Gate results

| # | Gate | Result | Evidence |
|---|---|---|---|
| G1 | `squeue` empty | ✅ PASS | no rows returned |
| G2 | repository commit + git status recorded | ✅ PASS | HEAD `1f6563f7ea52620354a4fa0666b813b6a9f9cc51`, branch `recovery-stage4`, 49 M / 9 D / 179 ?? |
| G3 | scripts/configs match `F1_FILE_MANIFEST.csv` SHA-256 | ✅ PASS | **37/37 files match**, after regenerating the manifest to cover the gate-driven fix (§2) |
| G4 | final DLinear trainer-call check | ✅ PASS | see §3 |
| G5 | all output paths under `$HOME`, none on scratch | ✅ PASS | every `--output`/`--error` and every output variable points at `/gpfs1/home/sychan552/...`; the only scratch paths are `CODE_ROOT` (READ-ONLY). A grep for scratch **write** paths returned nothing |
| G6 | ≥ 1 GB safe home-quota margin | ✅ PASS | **23.13 GB** free (50 GB quota − 26.86 GB used) |
| G7 | no Historical Track B path in F1 inputs | ✅ PASS | grep for `innovation_deploy_root_v3|track_b|historical` across all F1 scripts and configs → **no matches**; the scorer additionally *rejects* Track-B-profile artefacts |
| G8 | NLinear / DLinear / Last Value / Seasonal Naive remain CPU-only | ✅ PASS | the CPU script contains **0** occurrences of `gres=gpu` |
| G9 | Seasonal Naive is the leakage-safe corrected version | ✅ PASS | the CPU script calls `f1_naive_runner.py`, which imports `naive_leakage_safe`; `train_naive_966.py` is never invoked |
| G10 | `scorer_f1.py` used as the acceptance wrapper | ✅ PASS | `f1_score_all.py` imports `scorer_f1 as S` and calls `load_cell_validated` |
| G11 | the plan cannot exceed 0.60 GPU-h | ✅ PASS | 8 fits × 0.0533 = **0.42640** base; +10 % 0.46904; +20 % 0.51168 — all ≤ 0.60. The launcher re-checks from `sacct` before **every** GPU submission and halts if the projection would exceed the cap |

---

## 2. The gate failure that was found, and the fix

### What failed

**G3/G4 (wiring)**: the prepared scripts wrote checkpoints to
`${F1_ROOT}/ckpt/f1__<model>__L<L>__seed<s>/best_...pth`, but the Phase-3 scorer
(`score_test_stage5.py`) resolves checkpoints as `<ckpt-root>/<sub>/<template>` with
`sub ∈ {miflu, notext, nlinear, dlinear}`. Under the prepared layout **the scorer would
have found no checkpoints at all** and F1 would have produced no predictions.

**A second, related gap**: the prepared CPU script trained NLinear/DLinear but never ran
the prediction-dump step, so those arms would also have produced no artefacts.

Both are wiring defects in scripts written during the preflight — not contract, model-set
or budget changes.

### How it was diagnosed

Reading `score_test_stage5.py`'s `specs` table (lines 284–291) and `dump_predictions`
(lines 206–224), then cross-checking the filename each trainer actually writes:
`train_miflu.py:302`, `train_ablation.py:453`, `train_nlinear_966.py:190`,
`train_backbone_966.py:149`. The **filenames** matched; the **directory layout** did not.

### The fix

1. checkpoint directories changed to `${F1_ROOT}/ckpt/{miflu,notext,nlinear,dlinear}/`;
2. `score_test_stage5.py` added as the explicit Phase-3 step, invoked with
   `--ckpt-root ${F1_ROOT}/ckpt --dump-dir ${F1_ROOT}/preds --containment strict --stage6`;
3. the launcher gained a hard budget guard that sums F1 GPU-hours from `sacct` before each
   submission.

`--stage6` also probes the six stage-6 backbones; only `dlinear` exists in the F1 ckpt
root, and the others are reported as **SKIP** — never silently averaged in.

### Append-only handling

The three corrected scripts are in this round's own append-only directory. Their previous
hashes are preserved in git history of the manifest; `F1_FILE_MANIFEST.csv` was
regenerated and now carries the marker
`CORRECTED after the final gate caught a wiring defect` on exactly those three rows.

---

## 3. The DLinear trainer-call check (completed)

| Item | Verified |
|---|---|
| entry point | `scripts/train_backbone_966.py` |
| `--backbone dlinear` valid | ✅ `dlinear` is in `BACKBONES` (line 78) |
| flags used | `--horizon`, `--seed`, `--profile author_966`, `--containment strict`, `--ckpt-dir`, `--export-dir` — **all exist** in the parser |
| strict-containment guard | ✅ the script exits if `A2_REQUIRE_STRICT=1` and `--containment != strict` |
| device | `"cuda" if torch.cuda.is_available() else "cpu"` → on a CPU-only job it runs on **CPU** ✅ |
| checkpoint written | `save_locked_ckpt()` → `best_dlinear_L{L}_seed{s}.pth` ✅ matches the scorer's expectation |
| device check in the CPU wave | the CPU job requests **no** `gres/gpu`, so `torch.cuda.is_available()` is False → CPU by construction ✅ |
| prediction dump | not done by the trainer (by design); done in Phase 3 by `score_test_stage5.py` ✅ |

**Result: the DLinear call is correct and complete.**

---

## 4. Budget enforcement

```
new F1 authorization        0.60000 GPU-h   (independent; 0.05639 NOT carried over)
projected base use          0.42640 GPU-h
projected +10 %             0.46904 GPU-h
projected +20 %             0.51168 GPU-h
headroom after base use     0.17360 GPU-h
```

Enforcement points:

1. **launcher** — before each GPU element, sums GPU-hours from `sacct` over F1 job ids in
   the launch ledger and refuses to submit if `used + 0.0533 > 0.60`;
2. **ledger** — every job appends to `f1/manifests/GPU_LEDGER_F1.tsv` with its elapsed time;
3. **stop rule** — any GPU element exceeding 288 s (1.5× expected) halts the wave;
4. **failure policy** — a failed GPU job is diagnosed before any retry, and retried only if
   the cumulative total stays below 0.60.

Failed, cancelled and retried jobs are all counted.

---

## 5. Remote environment (verified immediately before execution)

| Check | Result |
|---|---|
| 8 required project scripts readable on scratch | ✅ all present |
| author dataset readable | ✅ |
| GPT-2 in the local HF cache | ✅ |
| env | torch 2.5.1, transformers 4.57.6 |
| `$HOME/.../f1` writable | ✅ |

---

## 6. Decision

**All gates pass. Proceeding to execute F1** — Phase 2 (GPU arms), then Phase 1 tail +
Phase 3 (CPU arms, single Test evaluation, independent scoring, text-path probe).
No additional confirmation is requested, per the authorization.