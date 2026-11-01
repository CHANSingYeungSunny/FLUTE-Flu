# Methodology — reproduction vs benchmark metric design

> Draft material for the final report. Decisions recorded with their justification,
> so the report can state *why* rather than only *what*.
> Status of every claim marked: **[verified]** = checked against source code or
> paper text in this repo; **[to verify]** = needs the primary PDF before submission.

## 0. Linear-model rule (corrected 2026-11-01)

**The innovation benchmark keeps exactly one linear model: NLinear.**
DLinear is **excluded from the competition**, because the essay's own Table V already
benchmarks DLinear — re-running it adds no new baseline, it merely re-derives a number
the paper already reports. NLinear is absent from the essay, so it is the informative
linear arm.

The previous rule in this project ("keep DLinear, drop NLinear") had the reasoning
inverted and is superseded. DLinear's numbers under our protocol are still reported,
but in a **clearly labelled replication-reference row**, never inside the champion
ranking. They remain valuable as a reference point: in our 64-cell sweep DLinear was the
only model to meet the Kramer & Shaman peak criterion at all (3 cells), which is worth
stating precisely because it is the paper's own baseline.

## 0a. Cross-scale comparison statement (for the paper)

Mechanism: every LLM arm is a **frozen encoder** with the **same trainable head**
(`Linear(·, L)`) and the **same training budget**; only the frozen representation
differs. That is what makes a comparison across 1.5 B and 33 B legitimate — it compares
*representations*, not capacity.

Reported alongside: a **Pareto frontier** (MSE vs parameter count, log axis) and a
**scale-free column** (`rel_improve_vs_seasonal_pct`). Two rankings are given —
absolute performance and efficiency — and **no single champion is claimed across scale
classes**.

Sentence for the manuscript:

> "Absolute performance and efficiency are reported separately. We do not claim a
> single champion across scale classes; the Pareto frontier and the scale-free
> relative-improvement column make the trade-off explicit."

Supporting numbers (measured, see `docs/STATE.md` §1.2): MSE vs log₁₀(params) slope
**+0.117**, R² **0.022** — model size explains ~2 % of the variance and the sign is
*positive*; the Pareto set is **{NLinear (2,520 params), PatchTST (531,878 params)}**,
and PatchTST spends **211×** the parameters of NLinear for **11.2 %** lower MSE.
(Re-derived 2026-11-01 on the shared evaluation windows, §4a; the pre-ruling values were
slope +0.106, R² 0.021, 4.3 %.)

## 1. Two questions, two metrics

The study asks two different things, and they require different metrics. Conflating
them is the single most common way this literature mis-reports results.

| Question | Metric | Space | Why |
|---|---|---|---|
| Did we reproduce the paper? | **7-variable aggregate MSE / MAE** | z (StandardScaler) | It is the only quantity Table V reports, so it is the only comparable number |
| Which model is operationally better? | **ILITOTAL** peak timing/intensity (PTE/PIE) | physical (patients) | It is the quantity public health acts on |

**Reproduction must use the paper's metric.** Table V's MSE/MAE are averages over the
7 channels in z-space **[verified: paper L253 Table V; repo `Dataset_Custom` fits
`StandardScaler` on the train slice only]**. ILITOTAL-only MSE is ≈1.9–2.0× the
7-variable average on the same predictions, so reporting it against Table V would
understate performance by roughly a factor of two purely from metric scope.

## 2. The seven variables and their roles

| # | Variable | Unit | Role | Used as |
|---|---|---|---|---|
| 1 | `% WEIGHTED ILI` | % of visits | population-weighted ILI signal | one channel of the 7-var aggregate |
| 2 | `% UNWEIGHTED ILI` | % of visits | unweighted variant | one channel |
| 3 | `AGE 0-4` | patients | age-stratified burden | one channel |
| 4 | `AGE 5-24` | patients | age-stratified burden | one channel |
| 5 | **`ILITOTAL`** | **patients** | **total ILI visits — the burden decision-makers act on**; the essay's own Fig. 7 variable **[verified: paper L353]** | **benchmark target** |
| 6 | `NUM. OF PROVIDERS` | count | reporting coverage | one channel |
| 7 | `OT` | count | 7th channel; Time-Series-Library target-name leftover; train mean ≈493,629 | one channel |

In the released repo the seven are simply channels of a multivariate series
(`features='M'`, per-variable samples via `feat_id`), and the model predicts `N×L`.
**Neither the paper nor the code treats the average as a physical quantity** — it is a
loss, not a time series. Two consequences:

- The 7-variable average **cannot be de-normalised**: `OT`'s train mean is 493,629 and
  `% WEIGHTED ILI`'s is 1.74, so a naive average of physical values is ~97% the `OT`
  curve. Any "de-normalised 7-var aggregate" curve is dimensionally meaningless.
- That is why the essay plots a **single** variable for its only curve (Fig. 7:
  `ILITOTAL`) and why we do the same.

## 3. Why PTE/PIE for the benchmark

MSE/MAE are pointwise averages: they reward being close on average, are dominated by
the high-magnitude easy-to-fit parts of the curve, and can be won by a model that
still misses the epidemic peak. Peak **timing** determines *when* to act; peak
**intensity** determines *how hard*. An MSE-optimal forecast peaking three weeks late
is operationally useless.

- **PTE** (peak timing error) — absolute difference, in weeks, between forecast and
  observed peak week.
- **PIE** (peak intensity error) — relative difference in peak height.
- **Accepted criterion** — a forecast is actionable if **PTE ≤ 1 week AND PIE ≤ 25%**,
  following Kramer & Shaman, *PLoS Comput Biol* 15(2):e1006742 (2019)
  (<https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006742>).
  **[to verify]** — quote the definitions verbatim from the PDF before submission; the
  thresholds above are the criterion this project adopts, and must be attributed to a
  specific section/page.

**Why PTE/PIE ranks models better here.** (1) Aligned with use rather than with curve
fitting. (2) A **conjunctive** pass criterion: a 3-week timing miss cannot be
compensated by a good intensity estimate. (3) **Scale-free** — immune to the
variance domination that corrupts the 7-var aggregate. (4) It localises *where* in the
horizon a model degrades, which is the actual question of the benchmark.

**Caveat to state explicitly:** PTE/PIE complements, does not replace, MSE/MAE. We
report both. Where the MSE champion and the PTE/PIE champion differ, that disagreement
is itself a reported finding rather than something to be resolved away.

## 4. Data split and leakage control

Source: the author's `national_illness.csv`, **byte-identical** (SHA-256
`2a96dfed…`) **[verified]**.

| Split | Rows | Border | Windows (T=104, L=24) |
|---|---|---:|---:|
| Train | 0–675 | `[0, 676)` | 549 |
| Validation | 676–772 | `[572, 773)` | 74 |
| Test | 773–965 | `[669, 966)` | 170 |

Borders are the author's own: `num_train = int(966·0.7) = 676`,
`num_test = int(966·0.2) = 193`, validation = remainder **[verified:
`Dataset_Custom.__read_data__`]**. Strict containment (the whole target block must lie
inside its split) reproduces the author's per-slice enumeration exactly
(676−104−24+1 = 549; 201−104−24+1 = 74; 297−104−24+1 = 170).

**Five leakage guards**

1. **Scaler fit on train rows only**, then applied to validation and test — no test
   statistic enters normalisation.
2. **Validation selects the epoch only**; it never enters the loss or the gradients.
3. **Test is evaluated exactly once**, after the checkpoint is frozen.
4. **No shuffling across splits** (train/val shuffled within themselves; test never).
5. **Static text embedding** (the author's precomputed file, identical for every
   sample) cannot carry test information.

**Contrast with the released code.** The author's `main_ILI_lora.py` evaluates the
**test** set every epoch (L211) and keeps the checkpoint with the lowest test MSE
(L225). Its headline number is therefore a *minimum over epochs on the evaluation set*
— an optimistic bound. We select on validation instead, which is why our number is not
inflated and why the two should not be expected to coincide exactly. This is a
deliberate, disclosed deviation and a defensible improvement.

## 4a. The evaluation window set — one rule for every model (ruling 2026-11-01)

The author's test loader is `DataLoader(..., batch_size=16, shuffle=False,
drop_last=True)` (`train_miflu.train_L`), so the **last partial batch is silently
discarded** and only `(W // 16) * 16` test windows are ever scored:

| L | test windows available | windows evaluated `(W//16)*16` | discarded |
|---|---:|---:|---:|
| 24 | 170 | **160** | 10 |
| 36 | 158 | **144** | 14 |
| 48 | 146 | **144** | 2 |
| 60 | 134 | **128** | 6 |

Those discarded windows are **anomalously hard**: measured on four L=24 MIFlu seeds the
full-170 MSE is **1.4111×** the first-160 MSE (per-seed ratios 1.3929–1.4423). Scoring
MIFlu on 160 and the 15 other arms on 170 would therefore make the table
incomparable — a ~40 % handicap for whichever side is scored on the full set.

**The rule.** Every model, every horizon, every table and every figure is scored on the
**first `(W // 16) * 16` test windows** — the author's set. One definition
(`scripts/eval_windows.py::eval_slice`), imported by every analysis and plotting script;
the window axis is axis 0 of the stored `(W, 7, L)` arrays and is asserted before
slicing. Every table row carries `n_eval_windows`, which must be identical for all arms
at a horizon (asserted) and equal to MIFlu's. The manuscript states the count in the
caption.

**Effect (measured, `scripts/compare_evalwindow.py`).** All 16 MSE values fall for the
learned arms (full-window / window-set ratio up to 1.18) and rise slightly for the four
sklearn arms whose dropped windows happened to be easy; the MSE ordering of the 16 arms
and both champions are **unchanged**, while the K&S cells move (PatchTST's PTE ≤ 1 wk
count 7 → 6). The pre-ruling tables are frozen as `BENCH_*.pre_evalwindow16.csv`.


## 5. What is identical to the author's code, and what is not

Identical (verified at file/hash/parameter level): data file; text embedding file;
**1,673,496 trainable parameters**; patching (42); channel independence; text appended
after patches; first-42-token slice; per-variable head `Linear(42·768, L)`; LoRA
(r=4, α=4, dropout 0.05, `c_attn`); 6 GPT-2 layers; `ln` + `wpe` trainable; dropout 0.1
(attn / resid / **embd**); causal mask; `ln_f`; MLP dropout; RevIN
`sqrt(var+1e-5)`; Adam; no gradient clipping; MSE in global z-space; type-1 LR
schedule; batch 16 single-variable; `drop_last`; validation `shuffle=True`;
seed base 2021.

Deliberate or unavoidable deviations, all to be disclosed:

| Item | Repo / paper | Ours | Reason |
|---|---|---|---|
| Checkpoint selection | best **test** MSE (repo); paper silent | best **validation** | leakage-free |
| Epochs | repo default 1; paper table 20 | 20 | 1 epoch is unconverged; the repo defaults (`PEFT=0`, `multimodal=0`) reproduce **GPT4TS (2.063)**, not MIFlu |
| Learning rate | repo 1e-4; paper table 5e-4; paper text says "empirical" | 1e-4 | follow the code where the paper is silent |
| Seed per repetition | repo has **no** repetition loop | 2021…2030 | reconstruction |
| Module construction order | author's order | ours differs | RNG consumption differs → different random draws for LoRA-A and heads from the same seed |

## 6. Open items to resolve before the report

1. **[to verify]** Verbatim PTE/PIE definitions and thresholds from Kramer & Shaman
   (2019), with page numbers.
2. Explain why the reproduction lands **below** the published L=24 value (6-rep mean
   1.3030 vs 1.542, −15.5%, every rep below). A consistent improvement is a protocol
   signature, not a win; candidates are epoch count, val-vs-test selection, and the
   evaluation window subset. **The window subset is now settled** (§4a): the author's
   own `(W//16)*16` set is used for every model, so it cannot explain a residual gap;
   the surviving candidates are epoch count and checkpoint selection.
3. Decide whether to report the 7-variable aggregate denormalised per variable
   (`MSE_z,j·σ_j²`) as a supplementary panel; the aggregate itself must stay in z-space.

---

**中文摘要**：复现用论文原口径（7 变量 z 空间聚合 MSE/MAE）；基准比较用 ILITOTAL（患者人数）
的 PTE/PIE，判据为 PTE ≤ 1 周且 PIE ≤ 25%。7 变量聚合是"损失量"不是时间序列，无法去归一化
（OT 均值 493,629 vs %ILI 1.74），故曲线图只画 ILITOTAL。数据按 676/97/193 切分且严格包含，
五道防泄漏措施；与作者代码的唯一协议性差异是"用验证集而非测试集选模型"。
