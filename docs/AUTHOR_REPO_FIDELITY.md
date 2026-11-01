# docs/AUTHOR_REPO_FIDELITY.md — what matches the author repo, what does not

> **What this is:** §3 of `AGENTS.md`, moved verbatim — the file/hash/parameter-level list of what was reproduced exactly, the table of deliberate/unavoidable deviations that **must be disclosed**, and the author-code defects that are publishable evidence.
> **When to read it:** when writing or reviewing the paper's reproduction/fidelity section, when a reviewer asks "is this the authors' setup?", and before changing any training default.
> **What it points to:** `docs/STATE.md` §1.1 (the numbers this setup produced), `docs/METHODOLOGY_METRICS_AND_SPLIT.md` (metric/split rationale), `docs/STATUS_20261031.md` (the reproduction fix log), `recovery/author_repo/` (the verbatim author code), `scripts/miflu_model.py` + `scripts/train_miflu.py` (our implementation).
> **Depends on:** `AGENTS.md` §2 rules 1, 4, 5, 7 (metric, validation-only selection, protocol separation, no "we beat the paper").
> **Chain:** `AGENTS.md` → `docs/STATE.md` → **this file** → `recovery/author_repo/` and `docs/STATUS_20261031.md`.

---

## 3. Author-repo fidelity: what matches, what does not

**Matches (verified at file/hash/parameter level):** data file byte-identical
(SHA `2a96dfed7db532f0…`), text embedding file `text_emb_label_0507_<L>.txt`
(317×768), **trainable params 1,673,496**, patching (42, ReplicationPad + unfold),
channel independence, text appended after patches, first-42-token slice, per-variable
head `Linear(42·768, L)`, LoRA r4/α4/p0.05/`c_attn`, 6 GPT-2 layers, `ln`+`wpe`
trainable, dropout 0.1 (attn/resid/**embd**), causal mask, `ln_f`, RevIN
`sqrt(var+1e-5)`, Adam, no grad clipping, MSE in global z-space, type-1 LR schedule
(0.9^k after epoch 3), batch 16 single-variable, `drop_last`, val `shuffle=True`,
seed base 2021, split 676/97/193 with strict containment (549/74/170 windows).

**Deliberate/unavoidable deviations (must be disclosed):**
| Item | Repo / paper | Ours | Why |
|---|---|---|---|
| Checkpoint selection | best **test** MSE / silent | best **validation** | leakage-free |
| Epochs | repo default 1 / paper table 20 | 20 | 1 epoch cannot converge; repo defaults (`PEFT=0,multimodal=0`) reproduce **GPT4TS (2.063)**, not MIFlu |
| Learning rate | repo 1e-4 / paper table 5e-4 / text says "empirical" | **1e-4** | follow code where paper is silent |
| Seed per rep | no repetition loop in repo | 2021…2030 | reconstruction |
| Init RNG order | author's order | ours differs | different draws for LoRA-A/heads |

**Author code defects found (publishable evidence):** test-MSE checkpoint
selection; test loader covers **1 variable** (`__len__` returns 170 not 170×7);
`freeze` is a no-op; defaults disable LoRA+text; text embedding is a constant vector
discarded after GPT-2; paper never states epochs/lr ("set empirically").

**`drop_last=True` on the TEST loader discards 10 of the 170 test windows.**
`train_miflu.train_L` builds
`el = DataLoader(TensorDataset(Xte, Yte), batch_size=16, shuffle=False, drop_last=True)`,
so 10 batches × 16 = **160 windows** are scored and the final 10 are silently
dropped: every reported test metric covers **91% of the test set**. Measured
severity — those 10 windows are **≈1.41× harder** than the rest (ratio
**1.3929–1.4423** across four L24 seeds, mean **1.4111**; e.g. seed 2022
1.201078 → 1.686578), so **published MIFlu numbers are optimistic by ≈40%
relative to a full-test-set evaluation**. Because the authors' released code uses
the same loader, the paper's Table V figures are on the same 160-window subset and
our reproduction remains a like-for-like comparison; the defect matters for
(a) any comparison against baselines evaluated on all 170 windows — the benchmark
row must therefore be reported as **`mse_7var_z_full170`** — and (b) as a finding
in its own right. Evidence: `docs/LEDGER_APPEND_20261101_miflu.md`,
`hpc_experiments/export_miflu_all7.py`.

> **SUPERSEDED 2026-11-01 (user ruling, non-negotiable) — one window set for
> everything.** The sentence above that says "the benchmark row must therefore be
> reported as `mse_7var_z_full170`" is **retired**. Rather than publish two
> different evaluation sets (MIFlu on 160, the 16 arms on 170 — which makes the
> table incomparable, since those discarded windows are ≈1.41× harder for MIFlu),
> the project adopts **the author's own window set for every model, every horizon,
> every table and every figure**: the first `(W // 16) * 16` test windows, i.e.
> **160 / 144 / 144 / 128** at L = 24/36/48/60. Consequences:
>
> * the single definition lives in `scripts/eval_windows.py::eval_slice`, and every
>   analysis/plot script imports it (never hard-codes 160);
> * every table row states `n_eval_windows`, asserted identical across all arms at
>   a horizon;
> * MIFlu's benchmark row therefore lands on its **reproduction values exactly**
>   (1.3045 / 1.3561 / 1.6543 / 1.6829), checked to 1e-5 against the per-seed
>   oracle by `scripts/verify_miflu_oracle.py`;
> * all benchmark numbers were re-derived under the rule; the pre-ruling tables are
>   frozen as `paper_tables/BENCH_*.pre_evalwindow16.csv` and the post-ruling ones
>   as `…post_evalwindow16.csv` (`docs/LEDGER.md`, 2026-11-01);
> * the defect itself is unchanged and still a publishable finding — what changes
>   is that we no longer *compare* across two different evaluation sets. If a
>   reviewer asks for the full-test-set number, it is re-derivable from the npz
>   (all 170 windows are stored) but it is not the paper's table.


---

## Dataset identity: the benchmark and the reproduction use the SAME numbers (verified 2026-11-01)

**Canonical source = the author repo's own file.** `data/raw/national_illness_author_repo_966.csv`
is byte-identical to the author's `national_illness.csv`, SHA256
`2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5`. Shape **966 x 8**:
columns `date` + `1, 2, 3, 4, 5, 6, OT` (7 numeric channels + weekly timestamp).
Column semantics are in `data/raw/COLUMN_MAP_national_illness.csv`:
`1` % WEIGHTED ILI, `2` % UNWEIGHTED ILI, `3` AGE 0-4, `4` AGE 5-24,
`5` ILITOTAL, `6` NUM. OF PROVIDERS, `OT` the 7th channel.

**Two profiles exist and they read different FILES:**

| half | profile | file read |
|---|---|---|
| reproduction | `author_repo_966` | `national_illness_author_repo_966.csv` -- the author's file, byte-for-byte |
| benchmark (all 204 cells) | `author_966` | `national_illness_raw_paper_exact.csv` -- a reprocessed copy (966 x 9, named columns + `epiweek`/`release_date`) |

**The 7 numeric channels are bit-identical between them.** Measured by mapping the author
columns onto the reprocessed names and differencing all 966 rows:

`
1 vs % WEIGHTED ILI       max|diff| = 0.000e+00   n_diff = 0
2 vs % UNWEIGHTED ILI     max|diff| = 0.000e+00   n_diff = 0
3 vs AGE 0-4              max|diff| = 0.000e+00   n_diff = 0
4 vs AGE 5-24             max|diff| = 0.000e+00   n_diff = 0
5 vs ILITOTAL             max|diff| = 0.000e+00   n_diff = 0
6 vs NUM. OF PROVIDERS    max|diff| = 0.000e+00   n_diff = 0
OT vs OT                  max|diff| = 0.000e+00   n_diff = 0
`

The only differences are **column names** and the metadata split into `epiweek` +
`release_date` (plus a dropped `release_date` column). **Those are not model inputs:**
every training script builds its channel list as
`[c for c in df.columns if c not in ("epiweek", "release_date", "date")]` -- the metadata
columns are explicitly excluded (`scripts/train_miflu.py`, `scripts/train_backbone_966.py`,
`scripts/train_classical_966.py` and the historical scripts under `hpc_results/`).

**Consequence.** The benchmark numbers are computed on exactly the same 7 series as the
reproduction, so **no re-run is needed for data-identity reasons**, and the two halves are
comparable. Going forward the **author file is the canonical source**: new runs should use
`--profile author_repo_966`. If literal file-level conformance is ever required for the
benchmark, re-running the 204 cells against `author_repo_966` would reproduce the same
numbers (the columns are identical) at the cost of GPU hours.
