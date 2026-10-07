# F1 GPU BUDGET REQUEST

Generated 2026-10-06. **This is a request for authorisation, not a submission.**
No GPU job has been submitted and the remaining 0.05639 GPU-h is untouched.

---

## 1. The ask

| Item | Value |
|---|---|
| **Requested additional GPU quota** | **0.60 GPU-hours** |
| Fits requiring GPU | **8** (corrected MIFlu × 4 horizons, matched no-text MIFlu × 4 horizons) |
| Fits requiring CPU only | **16** (NLinear, DLinear, Last Value, Seasonal Naive × 4 horizons each) |
| Base estimate | **0.42664 GPU-h** |
| With 10 % retry buffer | **0.46930 GPU-h** |
| With 20 % retry buffer | **0.51197 GPU-h** |
| Recommended request | **0.60 GPU-h** (covers the 20 % buffer, a failed-job allowance, and queue/measurement variance) |
| Expected wall clock @ MaxSubmit=1 / MaxJobsPU=1 | **≈ 34 minutes** (9 jobs submitted sequentially) |
| Existing remaining allowance | 0.05639 GPU-h (insufficient, preserved, **not used**) |

---

## 2. How the estimate was built

Measured inputs, not assumptions:

| Input | Value | Source |
|---|---|---|
| MIFlu fit cost | **162 s** for 20 epochs | `recovery/stage3/resource_estimate.md`: *"20 epochs × ~8 s = ~160 s ≈ 2.7 min per fit"*, where the ~8 s/epoch figure is recorded as **measured** |
| per-job startup | ~30 s | python + torch import, GPT-2 load from the local cache, data load |
| DLinear / NLinear fit | **4 s** median for 20 epochs | derived from the stage6 run ledger timestamps |
| naive references | < 1 s + startup | pure numpy, deterministic |
| scoring | ~60 s total | one CPU pass over 24 artefacts |

**Why the linear models are on CPU**: stage6 measured ~4 s per DLinear fit. Putting them
on a GPU slot would waste an A100-minute for no benefit, and stingy allows only one job at
a time, so they cost nothing in wall clock when batched into the single CPU wave.

---

## 3. The brief asks specifically about the earlier 0.35 GPU-hour figure

The earlier estimate was **0.35 GPU-h**. Checked against its five sub-questions:

| Question | Answer |
|---|---|
| does it include all four horizons? | **yes** — 4 horizons × the model set |
| does it include a failed-job allowance? | **no** — it assumed every fit succeeded |
| does it include checkpoint reload and Test inference? | **not explicitly** — it used a per-fit average that omitted the reload/predict pass now budgeted at ~30 s per job |
| does it incorrectly assign GPU time to naive references? | **yes, partly** — it did not separate the deterministic references, which need **zero** GPU |
| does it use measured or assumed times? | **measured, but a single average** — 0.0146 h/fit was the stage6 mean across six *different* backbones, most of which are far cheaper than MIFlu |

**Conclusion**: the 0.35 figure is **too low and too coarse**. It averaged expensive
MIFlu fits together with cheap backbone fits, and it carried no failure allowance. The
model-specific estimate above (0.42664 base) supersedes it.

Two effects pushed in opposite directions and the net is an increase of ~0.08 GPU-h:

- **upward**: separating out MIFlu's true 162 s cost (vs the 0.0146 h = 52 s blended mean);
- **downward**: moving NLinear/DLinear off the GPU entirely (they contribute 0 GPU-h here).

---

## 4. What the 0.60 GPU-h buys

| Deliverable | Value |
|---|---|
| a complete one-seed pilot across six models and four horizons | 24 scored (model, horizon) cells |
| verified forecast-key consistency across all six models | gate G4 |
| verified text-path functionality on the corrected implementation | inherits `text_active`, re-verifiable on the selected checkpoint |
| an independently scored preliminary ranking | `f1_score_all.py` |
| model-level cost measurements at the pilot scale | feeds the F2/F3 budget |

**It does NOT buy**: significance, seed robustness, a "best model" claim, or any
LLM-vs-non-LLM superiority statement. One seed cannot support those
(`F1_SUCCESS_GATES.md`, `F1_POST_PILOT_EXPANSION_PLAN.md`).

---

## 5. Cost comparison against the alternatives

| Option | GPU-h | Verdict |
|---|---:|---|
| **F1 core pilot (this request)** | **0.60** | ✅ recommended — contract-complete, answers the project objective |
| P1 A1-P minimum pilot | ~1.11 | blocked (G2–G4 open) |
| P3 released-code 10 repetitions | ~11.08 | not recommended — 8 of 9 contract items fail to match |

---

## 6. Conditions attached to the request

1. Submission only after explicit quota approval.
2. Submission strictly one array element at a time (`MaxSubmit=1`).
3. All outputs to `/gpfs1/home/…`; scratch remains over quota and is read-only.
4. Every job appends to `f1/manifests/GPU_LEDGER_F1.tsv`, reconciled against `sacct`.
5. A stop rule: if any element exceeds **1.5×** its expected elapsed time (i.e. > 288 s
   for a GPU fit), stop the wave and report before continuing.
6. The pilot is reported as **"A2-F Core Fair-Benchmark Pilot, One Seed"**, never as the
   final A2-F comparison.

## 7. Confirmation

**No GPU job was submitted for this preflight.** The 0.05639 GPU-h remaining is
unspent. All work in this round was local CPU plus zero-HPC-execution static auditing.