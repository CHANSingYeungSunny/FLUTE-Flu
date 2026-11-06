# Full paragraph and table diffs against the corrected upload

Deleted lines are historical source claims, not current assertions. Q01–Q25 restore the explanatory function of the original internal report.

```diff
--- report_internal_en corrected upload
+++ report_internal_en reviewed revision 4
@@ -1,320 +1,369 @@
-p0 FINAL-YEAR PROJECT · CITY UNIVERSITY OF HONG KONG · DEPARTMENT OF ELECTRICAL ENGINEERING
-p1 Reproducing MIFlu and Benchmarking Influenza Forecasting
-p2 Internal technical report — a leak-free reproduction, a 28-model benchmark, the peak-skill criterion, and 11 frozen LLM encoders
-p4 Contents
-p5 1. Data
-p6 2. Methodology
-p7 3. Reproduction of MIFlu's Table V
-p8 4. Benchmark 1 — accuracy (28 arms)
-p9 5. Benchmark 2 — peak skill on the Kramer & Shaman criterion
-p10 6. Benchmark 3 — the accuracy-efficiency frontier
-p11 7. Benchmark 4 — statistical significance
-p12 8. Frozen LLM encoders as feature extractors
-p13 9. The ablation ladder: design and current status
-p14 10. What the evidence does and does not support
-p15 11. Reproducibility
-p16 12. References
-p18 1. Data
-p19 The data are the CDC national influenza surveillance series distributed with MIFlu: 966 weekly rows x 7 numeric channels, bit-identical to the author's file (maximum absolute difference 0.000e+00). The split is chronological 70/10/20 — rows 0-675 train, 676-772 validation, 773-965 test (193 rows) — and every window is checked against a containment guard, so a window's input span always ends before its target span starts (minimum admitted test target-start row 773). Standardisation uses a StandardScaler fitted on the training block only.
-p20 Why 676/97/193 (70/10/20)? This is the standard protocol of the long-horizon forecasting benchmark family (Informer, AAAI 2023; DLinear, AAAI 2023; PatchTST, ICLR 2023; iTransformer, ICLR 2024) and the split used by the original MIFlu repository. The integer arithmetic is 966 x 0.7 = 676, 966 x 0.2 = 193, remainder 97. We follow it exactly so that the numbers are comparable.
-p21 Why (W//16)*16 evaluation windows? This is not a journal requirement. It is a side effect of the original code's DataLoader(batch_size=16, drop_last=True), which discards the final partial batch of test windows: 170 -> 160, 158 -> 144, 146 -> 144, 134 -> 128. The discarded windows are measurably harder (about 1.41x the retained mean), so scoring MIFlu on the cropped set while scoring every other arm on the full set would hand MIFlu an easier test. All 28 arms are therefore scored on the same cropped windows.
-p22 Table 1. The dataset, the split and the evaluation windows.
-p23 The scaling constants are why a 7-variable aggregate cannot be de-normalised: OT and ILITOTAL live four orders of magnitude apart, so the aggregate is a loss, not a series.
-p24 2. Methodology
-p25 Two protocols are used, and they are never mixed. (1) Reproduction: 10 repetitions, seeds 2021-2030, validation-selected checkpoint, 7-variable aggregate MSE — the protocol needed to compare with the paper's Table V. (2) Benchmark: 3 seeds (42/43/44), shared windows (W//16)*16 = 160/144/144/128 — the protocol used to compare 28 arms with each other. MIFlu is the only arm that appears under both, and its two numbers are not comparable to each other.
-p26 Table 2. The two evaluation protocols. They are never mixed and their numbers are never compared.
-p27 MIFlu is the only arm that appears under both protocols; its two numbers answer different questions and are not comparable to each other (see the reproduction section).
-p28 Why 3 seeds in the benchmark but 10 in the reproduction? The reproduction follows the paper's protocol (10 repetitions) so that a like-for-like comparison is possible. The benchmark follows the convention of the forecasting literature: PatchTST (ICLR 2023, arXiv:2211.14730) and iTransformer (ICLR 2024) both report three-seed means. Three seeds across 28 arms keeps the matrix at 28 x 4 x 3 = 336 cells, which is tractable on one A100 partition; ten seeds would be 1,120 cells for no gain in the comparisons that are made here.
-p29 Table 3. Reproduction: ours vs original paper/repo.
-p30 Two [DEVIATION] items are required by top-tier journal standards.
-p31 What are the two [DEVIATION] items, and why are they necessary? (1) Checkpoint selection: the original code selects the best epoch on the test set (main_ILI_lora.py, lines 211 and 225). That is data leakage — the test set is the final exam, and a model must not consult it while being chosen. We select on the validation block. (2) The 7-variable metric: the original test loader covers only 1 of the 7 variables (a bug), while Table V is defined on a 7-variable aggregate. We fix the loader. Both deviations are disclosed wherever a reproduction number appears.
-p32 Table 4. Benchmark protocol: ours vs the original repo (which uses fix_seed=2021, single seed).
-p33 The original paper has no benchmark — this is our contribution.
-p34 Why does PTE/PIE use ILITOTAL while MSE uses the 7-variable aggregate? The aggregate is a loss, not a time series: its seven channels have training means from 1.74 (% WEIGHTED ILI) to 493,629 (OT), so averaging them produces a number with no physical unit and no de-normalisation. Peak timing and peak height, by contrast, are statements about a single interpretable series in patient counts. PTE/PIE therefore use ILITOTAL de-normalised with the train-fit scaler (mean 9,439.84, sd 9,003.15 patients). The reproduction keeps the aggregate because Table V is defined on it.
-p35 3. Reproduction of MIFlu's Table V
-p36 The four-horizon mean is 1.4995 against the paper's 1.4355, i.e. 4.5 % worse, but the mean is the least informative part of the result. The sign flips with the horizon: at L=24 we are 15.4 % better than the paper (1.3045 against 1.542) and at L=36 4.6 % better (1.3561 against 1.422), while at L=48 we are 17.0 % worse (1.6543 against 1.414) and at L=60 23.4 % worse (1.6829 against 1.364). The MAE side shows the same crossover: 0.7482 / 0.7712 / 0.8381 / 0.8596 against 0.726 / 0.779 / 0.757 / 0.719, a four-horizon mean of 0.8043 against 0.7452 (+7.9 %).
-p37 Table 5. Reproduction of MIFlu's Table V — the sign crossover. 7-variable aggregate MSE in z-space, 10 repetitions, seeds 2021–2030.
-p38 A positive Δ means we are worse than the paper. We win L24 (−15.4 %) and L36 (−4.6 %) and lose L48 (+17.0 %) and L60 (+23.4 %); the 4-horizon mean is +4.5 % on MSE and +7.9 % on MAE. The only defensible claim is “reproduced within 4.5 % on the 4-horizon MSE mean, with a horizon-dependent sign” — never a claim of superiority over the original. Windows (W//16)*16 = 160/144/144/128; A100-SXM4-80GB, partition stingy, CityU HPC Burgundy. Source: ESSAY_VS_REPRODUCTION_TABLE_V.csv.
-p39 Two explanations are consistent with this pattern, and the data cannot yet separate them. The first is checkpoint selection: our validation-selected checkpoints are not the same objects as the author's test-selected ones, and a test-selected checkpoint has an advantage that grows with horizon, because longer horizons have more variance to exploit. The second is simply variance: the ten repetitions span 1.201-1.465 at L=24 and 1.401-1.984 at L=60, so a 17 % gap at L=48 and a 23 % gap at L=60 are large but not absurd given that spread — the run that produced 1.6829 at L=60 also produced 1.4108 on a different seed.
-p40 The only defensible claim is: reproduced within 4.5 % on the four-horizon MSE mean, with a horizon-dependent sign. It is not a claim of superiority over the original, and it is not “the paper is wrong”.
-p41 The per-seed oracle is included because a reproduction claim is only as strong as its provenance. Every later re-export of a MIFlu cell, including the benchmark instance, is gated against that table at |Δ| <= 1e-5 by 05_程序代码/verify_miflu_oracle.py; a cell that does not match is rejected rather than averaged in.
-p42 Table 6. Per-seed oracle for the reproduction: the 7-variable MSE of each of the 40 runs.
-p43 Every later re-export is gated against this table at |Δ| ≤ 1e-5; it is the provenance of every number in the reproduction table. verify_miflu_oracle.py recomputes these means and asserts they equal 1.3045 / 1.3561 / 1.6543 / 1.6829.
-p45 MIFLU at L=24. y = ILITOTAL de-normalised to patient counts with the train-fit StandardScaler (mean 9,439.84, sd 9,003.15 patients); x = test-set week. Black = ground truth; one line per fixed step 0/1/2/3 = 1/2/3/4 weeks ahead. Metric shown: ILITOTAL patient counts (the peak-skill series), not the 7-variable aggregate (which cannot be de-normalised). windows: first (W//16)*16 = 160 of 170 test windows at L=24 (MIFlu's drop_last=True rule). Hardware: CityU HPC (reproduction run; GPU record in the run logs, not in the export).
-p47 MIFLU at L=60. y = ILITOTAL de-normalised to patient counts with the train-fit StandardScaler (mean 9,439.84, sd 9,003.15 patients); x = test-set week. Black = ground truth; one line per fixed step 0/1/2/3 = 1/2/3/4 weeks ahead. Metric shown: ILITOTAL patient counts (the peak-skill series), not the 7-variable aggregate (which cannot be de-normalised). windows: first (W//16)*16 = 128 of 134 test windows at L=60 (MIFlu's drop_last=True rule). Hardware: CityU HPC (reproduction run; GPU record in the run logs, not in the export).
-p48 The curves show what the MSE gap is made of. At L=24 the step-0 curve tracks the ground truth through every rise and fall, and the degradation with step is visible but orderly. At L=60 the model still captures the seasonal shape — it is not a broken model — but it systematically under-shoots the three peaks, and the under-shoot is largest at the sharpest peak (the 2017-18 season). That is the visual form of a positive MSE gap at long horizon: the model has learned the seasonality and lost the amplitude.
-p49 4. Benchmark 1 — accuracy (28 arms)
-p50 The benchmark contains 28 arms across six families: (1) linear (NLinear) — the simplest baseline; (2) transformer (PatchTST, iTransformer) — the current long-horizon state of the art; (3) neural (DNN, CNN, RNN, LSTM, GRU); (4) classical machine learning (gradient boosting, random forest, decision tree, SVR, KNN); (5) LLM-based forecasters (MIFlu, TimeCMA, Qwen-Time, CALF) — the paper's approach and its published competitors; (6) frozen LLM encoders (11 arms: Qwen2.5, DeepSeek-R1-Distill at five sizes, Tencent Hunyuan and ContextPilot) — the question of whether pre-trained language representations transfer to an epidemiological series. The matrix is 28 x 4 horizons x 3 seeds = 336 cells, of which 204 (13 conventional + 3 published LLM-based + DLinear) carry measured A100 provenance and 132 are the encoder cells.
-p51 Table 7. The 28-arm benchmark: 7-variable aggregate MSE per horizon and as a four-horizon mean, plus the four-horizon MAE, in z-space. Mean over seeds 42/43/44, on the shared (W//16)*16 windows 160/144/144/128.
-p52 Lower is better. Per-horizon MAE is omitted for legibility; it is in 02_数字表格/BENCH_MSE_BY_MODEL_L.csv. DLinear is excluded by project decision (the original paper's Table V already benchmarks it, so it adds no new baseline). The seasonal-naive reference (52-week lag) scores 6.2132 on the same windows, so every one of the 28 arms beats it. Hardware: A100-SXM4-80GB, partition stingy, CityU HPC Burgundy — 204/204 cells of the 17 arms (13 conventional + 3 published LLM-based + DLinear) carry that measured provenance, and the MIFlu and encoder cells were run on the same partition with per-cell manifests on the cluster. Parameter counts are the trained-model totals from BENCH_EFFICIENCY.csv; classical learners and MIFlu are non-parametric in this sense (or not exported) and are left blank.
-p53 Three features of the table matter more than the ordering. First, MIFlu is the accuracy champion at 1.5574, followed by PatchTST (1.6621) and NLinear (1.8716): the paper's own model does win once it is placed on the same protocol as everyone else. Second, a linear model with 2,520 parameters is third of 28, ahead of every transformer except PatchTST — a result that should make a reader suspicious of the assumption that architectural sophistication is what buys accuracy on a 966-row series. Third, the spread is large: 1.5574 to 5.6155 is a factor of 3.6, so model choice dominates any hyper-parameter tuning reported in the papers being compared.
-p54 Finding F0 — accuracy alone does not identify a deployable model. The top three arms are separated by 20 % of MSE, and the remaining 25 arms span a further 3.0x. A ranking is therefore easy to produce and hard to act on: it says which model fits this test set best, not which model supports the decision the forecast exists for. Benchmarks 2-4 ask the questions the ranking cannot answer.
-p56 PATCHTST at L=24. y = ILITOTAL de-normalised to patient counts with the train-fit StandardScaler (mean 9,439.84, sd 9,003.15 patients); x = test-set week. Black = ground truth; one line per fixed step 0/1/2/3 = 1/2/3/4 weeks ahead. Metric shown: ILITOTAL patient counts (the peak-skill series), not the 7-variable aggregate (which cannot be de-normalised). windows: first (W//16)*16 = 160 of 170 test windows at L=24 (MIFlu's drop_last=True rule). Hardware: A100-SXM4-80GB | partition stingy | CityU HPC Burgundy.
-p58 NLINEAR at L=24. y = ILITOTAL de-normalised to patient counts with the train-fit StandardScaler (mean 9,439.84, sd 9,003.15 patients); x = test-set week. Black = ground truth; one line per fixed step 0/1/2/3 = 1/2/3/4 weeks ahead. Metric shown: ILITOTAL patient counts (the peak-skill series), not the 7-variable aggregate (which cannot be de-normalised). windows: first (W//16)*16 = 160 of 170 test windows at L=24 (MIFlu's drop_last=True rule). Hardware: A100-SXM4-80GB | partition stingy | CityU HPC Burgundy.
-p59 5. Benchmark 2 — peak skill on the Kramer & Shaman criterion
-p60 Peak skill replaces the question “how close is the curve” with the question “does the forecast support a decision”. On ILITOTAL de-normalised to patient counts we compute, per fixed step 0/1/2/3 = 1/2/3/4 weeks ahead, the peak-timing error (PTE, weeks) and the peak-intensity error (PIE, % of the observed peak). A cell passes the Kramer & Shaman criterion only if PTE <= 1 week AND PIE <= 25 % in the same cell. The two halves are a conjunction, and most arms fail one of them even when the other looks excellent.
-p61 Table 8. Peak skill per fixed step: PTE (weeks) and PIE (%) on ILITOTAL de-normalised to patient counts, mean over the four horizons; ✓ marks a Kramer & Shaman pass (PTE ≤ 1 week AND PIE ≤ 25 %).
-p62 Two arms pass, and they pass differently. NLinear passes all four step-0 cells (4 of 16): mean PTE 1.677 weeks and mean PIE 9.477 % over all 16 cells, with a step-0 PIE of 3.25 % — an order of magnitude inside the criterion. MIFlu also passes 4 of 16, but three of them are step-0 cells (L=48 fails at step 0 with PTE 1.222 weeks) and the fourth is L=48 at step 1; its mean PIE is 26.846 %, i.e. its passes sit close to the 25 % boundary rather than inside it. PatchTST has the best timing (mean PTE 1.240 weeks) but a mean PIE of 32.755 % and 0 passes: it misses the calibration half of the criterion in every cell. Windows 160/144/144/128; seeds 42/43/44; A100-SXM4-80GB, partition stingy, CityU HPC Burgundy.
-p63 Table 9. The same criterion cell by cell: every (horizon, step) pair for the three named arms. PASS requires PTE ≤ 1 week AND PIE ≤ 25 % in the same cell.
-p64 16 cells per model = 4 horizons × 4 steps, each a mean over seeds 42/43/44. NLinear passes 4 of 16, all at step 0 (PIE 2.4–4.2 %); MIFlu passes 4 of 16 — three at step 0 and one at L=48 step 1, with PIE 18.3–24.8 %, i.e. against the boundary; PatchTST passes none, because its PIE stays in the 26–35 % band at every step. Peak detection: find_peaks(prominence = 0.15 × range, distance = 15) with ±8-week matching — this study's engineering choice, not part of the published criterion. The 1-week / 25 % thresholds are attributed to Kramer & Shaman (2019) but remain [to verify] against the original text.
-p65 Two arms pass, and they pass differently. NLinear passes all four step-0 cells (4 of 16), with a mean PTE of 1.68 weeks and a mean PIE of 9.48 % over all 16 cells; at step 0 its mean PIE is 3.2 %, an order of magnitude inside the criterion. MIFlu also passes 4 of 16, but three are step-0 cells and the fourth is L=48 at step 1: at L=48 step 0 its PTE is 1.22 weeks, and its PIE values across the passing cells are 18.3-24.8 %, i.e. against the boundary rather than inside it. PatchTST passes none: its timing is the best in the study (mean PTE 1.24 weeks) but its PIE is 32.8 %, and it misses the calibration half in every cell.
-p67 Per-step peak skill, all 28 benchmark arms. Colour = mean over the four horizons of PTE (weeks, left) and PIE (%, right) at each fixed step 0/1/2/3 = 1/2/3/4 weeks ahead; rows are ordered by the four-horizon mean 7-variable MSE (best at the top), so the accuracy ranking reads top-down. A blue box marks a (model, step) whose four-horizon mean meets both halves of the Kramer & Shaman criterion (PTE ≤ 1 week AND PIE ≤ 25 %): only NLinear and MIFlu qualify, and only at step 0. The per-cell counts are 4/16 for NLinear (all step 0), 4/16 for MIFlu (three step-0 cells plus L=48 step 1) and 0/16 for PatchTST. Windows: shared (W//16)*16 = 160/144/144/128; seeds 42/43/44. Reproduced by plot_peak_skill.py. Hardware: A100-SXM4-80GB | partition stingy | CityU HPC Burgundy.
-p68 The mechanism is visible in the curves. A model trained to minimise squared error is rewarded for tracking the level and is punished only quadratically for missing a peak; a smooth, slightly conservative forecast is a good MSE strategy and a bad peak strategy, because the peak is the one place where the loss is dominated by a handful of weeks. NLinear, essentially a linear map with a per-window level correction, produces a sharper response at the peak: it over-shoots more often, which costs it MSE, and lands closer to the peak height more often, which is what PIE measures. This is a hypothesis consistent with the data, not a proven mechanism.
-p69 Finding F1 — the deployment ordering is not the accuracy ordering. Across all 28 arms, better MSE does go with better calibration (Spearman ρ = +0.74 against mean PIE): the two axes are not independent, and MSE is a useful screen. What fails is the ordering of the frontier. Among the three lowest-MSE arms the calibration order is inverted at both ends — NLinear (3rd on MSE) has the lowest PIE at 9.5 %, MIFlu (1st) sits at 26.8 % and PatchTST (2nd) at 32.8 % — and the pass indicator is negatively rank-correlated with MSE (ρ = -0.43, p = 0.023). The runner-up by MSE passes nothing; the third-best passes every horizon one week ahead. That is the finding a deployment decision turns on, and a leaderboard sorted by MSE cannot express it.
-p70 6. Benchmark 3 — the accuracy-efficiency frontier
-p71 The Pareto frontier answers a different question from the peak criterion: not “is this model good enough to deploy” but “how much accuracy does each additional parameter buy”. A model is Pareto-optimal if no other model achieves both lower error and fewer parameters. The frontier has exactly two members: NLinear (2,520 parameters, MSE 1.8716) and PatchTST (531,878 parameters, MSE 1.6621). Across the 11 parametric arms, a regression of the four-horizon mean MSE on log10(parameters) gives a slope of +0.1171 with R² = 0.0223.
-p72 Table 10. Accuracy–efficiency summary, and the rank association between accuracy and peak skill.
-p73 A positive slope means more parameters are associated with a higher (worse) MSE, and R² = 0.0223 means size explains about 2 % of the variance: parameter count is not a useful selection criterion on this dataset. The two Pareto rows should be read as a trade-off, not a ranking — PatchTST spends 211× the parameters for 11.2 % lower MSE. The last two rows keep the peak-skill claim honest: across all 28 arms, better MSE does go with better calibration (ρ = +0.74), so the two axes are not independent; what fails is the ordering of the frontier (the peak-skill tables) and the acceptance verdict, which is negatively rank-correlated with MSE (ρ = -0.43). Windows 160/144/144/128; seeds 42/43/44.
-p74 Both signs of that sentence matter. The slope is positive, so more parameters are associated with a higher (worse) MSE; and R² is 2 %, so size explains almost none of the variance. The two Pareto rows then read as a trade-off rather than a ranking: PatchTST spends 211x the parameters of NLinear for 11.2 % lower MSE. Whether that is a good trade depends on the deployment — and, given Finding F1, on whether the deployment needs peak skill, in which case the 11.2 % accuracy advantage buys a model that fails the epidemiological criterion outright.
-p76 Accuracy–efficiency Pareto frontier. x = parameter count (log scale), y = 4-horizon mean 7-variable z-space MSE; the step line is the Pareto set {NLinear, 2,520 parameters; PatchTST, 531,878 parameters}. PatchTST spends 211× the parameters of NLinear for 11.2 % lower MSE; the fitted slope of MSE against log₁₀(parameters) is +0.1171 with R² = 0.0223, i.e. size explains ~2 % of the variance and the sign is positive. Windows: shared (W//16)*16 = 160/144/144/128; seeds 42/43/44. Reproduced by plot_pareto.py. Hardware: A100-SXM4-80GB | partition stingy | CityU HPC Burgundy.
-p78 Step-0 peak skill for the three named arms. Left: peak-timing error (weeks) at step 0, mean over the four horizons, against the 1-week threshold (dashed). Right: peak-intensity error (%) at step 0 against the 25 % threshold (dashed). Green = inside the threshold, red = outside. MIFlu (0.35 wk, 18.9 %) and NLinear (0.21 wk, 3.2 %) stay inside both thresholds at the mean level, while PatchTST (0.68 wk, 30.6 %) misses the intensity half — the visual form of the decoupling between a good average error and a calibrated peak. Seeds 42/43/44; windows (W//16)*16 = 160/144/144/128.
-p79 Finding F2 — parameter count is not a proxy for accuracy. The slope is positive and R² is 0.0223: on this dataset, size is uninformative about accuracy, and what little signal there is points the wrong way. The frontier is a two-model trade-off, not a ranking, and the cheaper member of the frontier is the one that passes the domain criterion at every horizon.
-p80 7. Benchmark 4 — statistical significance
-p81 The Pareto analysis is descriptive: it says what the trade-off is, and needs no inference. The significance analysis is inferential: it asks whether the 11.2 % difference is distinguishable from seed noise at all. Both are needed, because a trade-off is only worth discussing if the difference being traded is real.
-p82 On the 12 matched (horizon x seed) cells we run exact paired sign-flip tests over all 136 pairs of the 17 non-encoder arms (MIFlu and the 11 encoders are outside this family), with Holm-Bonferroni correction, a bootstrap 95 % CI (10,000 resamples) and Cohen's d. 128 of 136 pairs are significant before correction; after proper Holm over 136 pairs none survives, because n = 12 makes the smallest attainable adjusted p 0.066. The pair the Pareto argument needs is NLinear vs PatchTST: mean Δ MSE +0.2095 in PatchTST's favour, NLinear lower in only 2 of 12 cells, raw p = 0.0059, p(Holm) = 0.117, d = 1.15.
-p83 Table 11. Paired sign-flip tests on the 12 matched (horizon × seed) cells, Holm-corrected over all 136 pairs (recomputed from the raw p-values). First row: the Pareto pair discussed in the text (bold). Remaining rows: the six smallest p-values, for contrast.
-p84 Positive Δ means model A has the larger MSE. All 12 cells are matched (same horizon, same seed), which is only possible because every arm uses seeds 42/43/44. The exported p_holm column was produced with a reverse cumulative minimum, which is not a valid Holm adjustment; the values here are recomputed from p_raw. With n = 12 the smallest attainable raw p is 2/2¹² ≈ 0.00049, so with m = 136 pairs the smallest attainable adjusted p is 0.066 and no pair survives at 0.05 (128/136 are significant before correction). Why the first row is not in the second block: NLinear vs PatchTST has adjusted p = 0.117, the 117th smallest of 136, so a table sorted by significance omits the one comparison the Pareto argument needs. The difference is not resolvable at this sample size; that is a failure to reject, not a demonstration of equivalence (d = 1.15, and PatchTST is lower in 10 of 12 cells).
-p85 Why the paired-test table looks like it is about other models: it is sorted by p, and the NLinear-PatchTST pair is the 117th smallest of 136 — a “strongest six” table would silently omit the one comparison the argument needs. The table therefore puts that pair in the first row and the six most significant pairs below it, so both facts are visible at once: before correction most of the roster separates; after correction the study cannot separate any pair — a statement about power, not about the models — and the frontier pair is the one the argument needs.
-p86 Finding F3 — the 211x parameter cost is not statistically distinguishable from noise. p(Holm) = 0.117 means we cannot reject equality of the two means at the 5 % level. Three qualifications keep this honest: with n = 12 the smallest attainable p is 2/2¹² ≈ 0.00049; non-significance is a failure to reject, not a demonstration of equivalence; and the effect size is d = 1.15 with PatchTST lower in 10 of 12 cells, so the direction is consistent even though the difference is not resolvable at this sample size. The correct conclusion is not “the models are equal” but “this benchmark does not establish an accuracy advantage for the 211x cost” — which, together with Finding F1, is enough to make NLinear the defensible default.
-p87 8. Frozen LLM encoders as feature extractors
-p88 The encoder axis asks whether a pre-trained language model is a useful feature extractor for an epidemiological series. Each arm is a frozen encoder plus one shared linear head, trained channel-independently; no encoder weight is updated, and the head is the only trainable part. This is deliberately the charitable version of the idea: if the representation carries usable information, a linear read-out is enough to expose it, and a failure cannot be blamed on fine-tuning instability. 132 of 156 cells are complete (11 arms x 4 horizons x 3 seeds); the 24 missing cells belong to two embedding-only models that cannot emit per-layer hidden states.
-p89 Table 12. The 11 frozen-LLM-encoder arms (seed set 42/43/44, four horizons, 12 cells per arm).
-p90 Every arm is a frozen encoder plus one shared linear head, trained channel-independently; no encoder weight is updated. Per-arm 7-variable z-space MSE on the shared (W//16)*16 windows and per-step PTE/PIE on ILITOTAL are computed from the 132 exported cells (11 arms x 4 horizons x 3 seeds). The two embedding-only arms and the five excluded arms are listed in the next table.
-p91 Table 13. Arms that are not in the roster table, and why.
-p92 “Skipped” means the model loads and runs but cannot expose per-layer hidden states, so it cannot feed the adapter — a property of the architecture, not a failure of the method. “Excluded” means the arm never reached a training step.
-p93 The result is uniform and negative. The best encoder (Hunyuan-1.8B) reaches 4.7374 and the worst (Qwen2.5-1.5B) 5.2049, i.e. 3.04x to 3.34x the MSE of MIFlu (1.5574), and every one of the 11 is worse than a decision tree (4.3198). None passes the Kramer & Shaman criterion in any cell. The ordering inside the family is not explained by size: a 1.8B model is the best and a 7B model of the same vendor is worse, so whatever the encoders carry, it is not a monotone function of capacity.
-p94 Finding F4 — frozen LLM representations do not transfer to this task. Eleven encoders, five model families, 1.5B to 32B parameters, 132 cells: none beats a decision tree and none passes the domain criterion. The negative result is informative because the protocol was designed to give the idea its best chance (frozen features, linear read-out, channel independence) and it still fails; it does not follow that an encoder can never help, but it does mean that a paper claiming a gain from frozen language features on this task owes a mechanism and a control.
-p95 9. The ablation ladder: design and current status
-p96 The ablation ladder asks where MIFlu's accuracy comes from. The paper's model is a GPT-2 backbone with low-rank adapters (LoRA), a text branch, and a linear head, so the two knobs that could carry the result are (a) the LoRA adaptation and (b) the depth of the stack. The ladder is therefore five variants: no LoRA, and K = 2, 4, 8, 12 transformer layers, each at four horizons and three seeds (5 x 12 = 60 cells), compared against the full K=6 arm already in the benchmark table.
-p97 The question each variant answers is worth stating, because “ablation” without a hypothesis is just extra runs. no_lora isolates the frozen backbone: if accuracy survives, the adaptation is not what carries it. K=2 and K=4 test whether depth is needed at all on a 966-row series; K=8 and K=12 test whether extra capacity helps or merely over-fits. The reference arm is the K=6 model already reported, so the ladder contains no duplicated run.
-p98 Table 14. The ablation ladder (called Table VIII in the project plan): five variants, 60 cells, and what each one is for.
-p99 Each variant is 4 horizons × 3 seeds = 12 cells; five variants = 60 cells; the reference arm is the 12 cells already reported in the benchmark table and is not counted twice. At the snapshot these documents are built from, 27 of 60 cells were complete (driver job 722968) and the per-variant export had not been pulled, so this document reports the design and the completion count and claims no depth trend. The --no-text variant is deliberately not a row: the text tokens sit behind the causal mask and the head reads only the time patches, so --no-text is bit-identical to the full arm — a structural verification (asserted by tests_archive/test_miflu_ablations.py), never an ablation effect.
-p100 One ablation result is already established, and it is a negative one about the text branch: the text tokens are appended after the time patches behind a causal mask, and the output head reads only the time-patch positions. Two different text tensors therefore give bit-identical predictions, and --no-text is bit-identical to the full arm with the same seed — asserted by tests_archive/test_miflu_ablations.py, not assumed. In the published architecture the text branch cannot change a number, so a “text ablation” row would be a structural verification, not an effect. That is why the modality claim of the original paper should be read carefully: whatever its text branch contributes, it is not visible in this implementation.
-p101 The remaining five variants are not yet reported. At the snapshot these documents are built from, 27 of 60 cells were complete (driver job 722968) and the per-variant export had not been pulled, so this section reports the design and the completion count and claims no depth trend. An earlier internal note that described the ladder as complete at 60/60 and “monotonic” is not supported by any artefact in this repository and has been removed from the reports.
-p102 Finding F5 (provisional) — the modality claim is not supported by the architecture as shipped. The text branch is masked out of the prediction path, so --no-text cannot move a number; the depth and LoRA questions remain open until the 60 cells are aggregated. This is reported as a design and a status, not as a result.
-p103 10. What the evidence does and does not support
-p104 Four claims are supported by the artefacts in this repository: (1) the reproduction lands within 4.5 % of the published four-horizon MSE mean with a horizon-dependent sign; (2) on one common protocol, MIFlu is the accuracy champion of 28 arms and NLinear is third with 2,520 parameters against PatchTST's 531,878; (3) the deployment ordering is not the accuracy ordering — the frontier is inverted on calibration and the pass indicator is negatively rank-correlated with MSE; (4) frozen LLM encoders do not transfer to this task under a protocol designed to favour them.
-p105 Five claims are not supported, and the reports do not make them. (1) Superiority over the original: the reproduction is 4.5 % worse on the mean, and the per-horizon wins do not survive as a claim because the protocol differs in two disclosed ways. (2) “MSE and peak skill are unrelated”: they are positively correlated across the roster (ρ = +0.74); the finding is about the frontier, not about independence. (3) “NLinear is the only arm that passes”: MIFlu also passes 4 of 16, by a different route and against the boundary. (4) “PatchTST's advantage is zero”: the test fails to reject equality, which is not the same statement. (5) “The ablation shows a monotonic depth trend”: the ladder is 27/60 and no per-variant number has been aggregated.
-p106 The threats to validity are worth naming. The K&S thresholds are attributed to Kramer & Shaman (2019) but remain [to verify] against the original text; the peak detector is this study's engineering choice. The benchmark has one dataset, one country and one target series, so nothing here establishes cross-dataset generality. The significance tests have n = 12, so their resolution is coarse by construction. There is no rolling-origin evaluation yet: every number is from a single chronological split, so a season that falls in the test block is seen once. Finally, the encoder axis is a frozen-feature test; it does not test generation, prompting or fine-tuning, and its negative result must not be over-read.
-p107 Table 15. Defects found during the campaign, and their effect on the measured numbers.
-p108 A1 is why the project refuses to quote any LLM ±sd measured before 2026-11-02 03:57:47: the seed never entered the training path before then, so sd was exactly 0 by construction. A6 (the attempt cap) is still open and is an operational, not a scientific, risk: it wastes GPU hours, it does not corrupt a completed cell.
-p109 The defect ledger is included because it is part of the evidence: eight defects were found and seven fixed during the campaign, and one of them (A1) is why no LLM ±sd measured before 2026-11-02 03:57:47 is quoted anywhere in these documents. A6 remains open and is an operational, not a scientific, risk: it wastes GPU hours without corrupting a completed cell.
-p110 11. Reproducibility
-p111 Every document in 01_最终报告/ is generated from the CSVs, not edited by hand. From the repository root:
-p112 •  python 01_最终报告/_build2/build_docs.py — writes the six DOCX and asserts every headline number on import of dlv/data.py.
-p113 •  python 01_最终报告/_build2/to_pdf.py — converts to PDF with the bundled LibreOffice kit and prints the page count of each file.
-p114 •  python 01_最终报告/_build2/verify_docs.py — reopens every DOCX, checks the Chinese round-trip on two independent paths, and confirms the reproduction table still shows the sign crossover.
-p115 •  python 01_最终报告/_build2/make_manifest.py — regenerates MANIFEST.md.
-p116 Table 16. Evidence map: which artefact carries which number.
-p117 No number in these documents was typed from memory: every one is read from the files above at build time, and dlv/data.py asserts the headline values.
-p118 12. References
-p119 •  Moon et al. “MIFlu: Large Language Model-Based Multimodal Influenza Forecasting.” IEEE Journal of Biomedical and Health Informatics, 2025. DOI: 10.1109/JBHI.2025.3561214.
-p120 •  Kramer & Shaman. “Development and validation of influenza forecasting for 64 temperate and tropical countries.” PLoS Computational Biology 15(2): e1006742, 2019. DOI: 10.1371/journal.pcbi.1006742 [thresholds to verify].
-p121 •  Nie et al. “A Time Series is Worth 64 Words: Long-term Forecasting with Transformers.” ICLR 2023. arXiv:2211.14730.
-p122 •  Liu et al. “iTransformer: Inverted Transformers Are Effective for Time Series Forecasting.” ICLR 2024.
-p123 •  Zeng et al. “Are Transformers Effective for Time Series Forecasting?” AAAI 2023.
-p124 •  Centers for Disease Control and Prevention. “FluView: Weekly U.S. Influenza Surveillance Report,” national ILI series (966 weekly rows, 7 channels).
-table1/row1 Document | Internal technical report (long form)
-table1/row2 Project | Independent reproduction of MIFlu and a 28-model influenza-forecasting benchmark
-table1/row3 Version / date | 1.1 — 3 November 2026
-table1/row4 Audience | Supervisor, assessor, and the next agent (CodeBuddy / ChatGPT) who continues the work
-table1/row5 Status | Reproduction complete (+4.5 %, sign crossover 2-2); 28-model benchmark complete; 11 frozen encoders complete; ablation ladder in progress (27/60 cells at this snapshot).
-table1/row6 Companion documents | progress_report_en.docx (short, school template) · ieee_manuscript_en.docx (journal draft) · MANIFEST.md (file inventory) · 04_详细说明文档/REPO_HYGIENE.md
-table1/row7 Rule | Every number below is read from 02_数字表格/*.csv at build time and asserted by dlv/data.py. Nothing is quoted from memory.
+p0 MIFlu reproduction and influenza forecasting audit
+p1 Internal technical report with explanatory questions and answers
+p2 Contents
+p3 1 Data and provenance
+p4 2 Methodology and literature
+p5 3 Reproduction of MIFlu
+p6 4 Benchmark accuracy
+p7 5 Peak timing and magnitude
+p8 6 Accuracy and parameter count
+p9 7 Statistical audit
+p10 8 Frozen language encoders
+p11 9 Ablation design and status
+p12 10 Interpretation and publication plan
+p13 11 Reproducibility and open checks
+p14 12 References
+p16 Reading purpose. This internal report supports supervision and explanation. Questions Q01–Q25 are placed beside the relevant evidence. Each answer connects named papers and reading locations to local evidence, explains the choice and gives a supervisor short answer. Accuracy and peak skill cover 28 arms; parameter exports cover 11, and paired tests 17.
+p17 1 Data and provenance
+p18 Run python scripts/verify_snapshot.py --raw-smoke and python -m pytest tests/test_snapshot_audit.py -q from the repository root. The audit re-derives headline aggregates, peak flags, correlations, regression, Holm adjustment and one raw prediction MSE. Seven newly added CPU audit tests passed; they are separate from the archived model suite. The corrected ZIP supplies tests_archive/. Collection fails under the historical layout and missing model dependencies. No archived-suite pass count or reliable collected total is claimed. Training, live HPC status and upstream code were not rerun. The original source CSVs are retained unchanged, with a separate corrected Holm export.
+p19 Table 1. Data and evaluation contract
+p20 Identity compares the two supplied 966-row files after selecting their seven matching numeric columns. It does not re-establish byte identity with an independently downloaded upstream file. Dates in the author-format file are synthetic labels.
+p21 Q01 Why use 676 training, 97 validation and 193 test rows?
+p22 Answer and local evidence. The supplied 966-row protocol reserves floor(966 × 0.7) = 676 rows for training and floor(966 × 0.2) = 193 for testing. The remaining 97 form validation. Training fits weights and scaling, validation chooses checkpoints, and the final test block estimates performance after that choice. Chronological order keeps later observations out of earlier training. This is the declared project protocol, not a universal journal requirement. The independently pinned upstream split is still unverified.
+p23 Paper-based reasoning. Tan et al. explicitly use 70/10/20 for Illness [13, §3.3], while iTransformer preserves chronological separation [5, App. A.1]. These provide a concrete forecasting precedent: retain enough training data, use validation for model selection, and reserve later observations for the final test. The exact 676/97/193 integers come from our 966 rows and rounding rule. The literature supports the design rationale; it does not prove that this ratio is optimal for every influenza season or that our upstream file identity is established.
+p24 Say to the supervisor. The split follows an Illness precedent in Tan et al.; chronological separation protects the final evaluation [13, 5].
+p25 Reading locator. Tan et al. [13], §3.3 Datasets and Evaluation Metrics; iTransformer [5], Appendix A.1.
+p26 Evidence. configs.py DATA_PROFILES[author_repo_966]; BENCH_MSE_BY_MODEL_L.csv; eval_windows.py
+p27 Q02 Why score 160 windows when 170 are available at L24?
+p28 Answer and local evidence. The local evaluation contract preserves complete batches of 16: (W//16)×16. Thus 170/158/146/134 available windows become 160/144/144/128 scored windows at L24/36/48/60. Using the same retained windows across models prevents a comparison of different test examples. Cropping can nevertheless change scores by removing a particular tail of time. It is a comparability choice inherited by this snapshot, not evidence that cropping is scientifically optimal. Full-window sensitivity remains necessary; a specific discarded-tail difficulty ratio was not independently reverified.
+p29 Paper-based reasoning. Tan et al. retain original data-loaders and training conditions during their reproduction checks [13, §3.1]. This supports disclosing exactly which examples are scored; it does not require cropping. Our complete-batch rule changes the scoring population. Giving every model the same retained windows removes a comparison unfairness, but deleting the tail can still alter the result. The necessary sensitivity analysis is to score every model on all available windows and compare rankings. A literature citation cannot establish our discarded-tail difficulty without its raw calculation.
+p30 Say to the supervisor. Cropping preserves a shared scoring population; full-window rescoring tests its effect [13].
+p31 Reading locator. Tan et al. [13], §3.1 Reproducibility Note; local eval_windows.py.
+p32 Evidence. BENCH_MSE_BY_MODEL_L.csv; eval_windows.py; scripts/verify_snapshot.py --raw-smoke
+p33 Q03 Why fit scaling on training data only?
+p34 Answer and local evidence. A mean or standard deviation fitted on the complete series would use information from the future test block. Train-only scaling keeps that information out of model preparation. Each channel is standardised separately. The local equality check compares seven matching numeric columns in the two supplied files and finds maximum absolute difference zero. That verifies numeric equality of these local copies, not byte identity with a newly downloaded author file.
+p35 Paper-based reasoning. Kapoor and Narayanan identify preprocessing across the training/test boundary as a leakage route [22, L1.2]. Here that means fitting channel means and standard deviations only on training, then reusing them. If future observations determine these constants, preparation has already adapted to the held-out distribution even without using test labels in gradient updates. This makes train-only scaling part of the experiment. The separate local file-equality check establishes matching inputs, not absence of every possible leakage route.
+p36 Say to the supervisor. Preprocessing is fitted on training only, following the leakage distinction in Kapoor and Narayanan [22].
+p37 Reading locator. Kapoor and Narayanan [22], Results, leakage taxonomy L1 and L1.2.
+p38 Evidence. 06_原始数据集/scaler_miflu_author966.json; scripts/verify_snapshot.py
+p39 2 Methodology and literature
+p40 Patching and linear baselines are established [3–5]. Time-LLM, CALF and TimeCMA use different alignment/adaptation designs [6–8]. Chronos, TimesFM, Moirai and Lag-Llama pretrain on numerical series and were not evaluated here [9–12]. Earlier LLM-removal work already questions the benefit of language pretraining [13], while a 2026 preprint reports conditional benefits under cross-dataset shifts [14]. The contribution here is the specific influenza protocol audit and multi-metric comparison.
+p41 Table 2. Separate reproduction and benchmark protocols
+p42 Three seeds are a compute-budget choice, not a universal venue rule. Reproduction and benchmark estimates use different seed sets. Do not substitute one for the other. Exact upstream protocol defects remain to be checked against a pinned author revision.
+p43 Q04 Why ten reproduction seeds but three benchmark seeds?
+p44 Answer and local evidence. They answer different questions. The supplied reproduction uses seeds 2021–2030 to compare with the transcribed paper table. The broader benchmark uses 42/43/44 to compare implementations under one shared protocol. The retained matrix is 28 models × 4 horizons × 3 seeds = 336 cells. Ten seeds would require 1,120 cells. Three reflects the project compute budget; it does not prove adequate power, and additional seeds can improve uncertainty estimation. Neither a universal three-seed venue rule nor zero benefit from more seeds is established.
+p45 Paper-based reasoning. The original three-seed citation is incorrect. PatchTST uses fixed-seed main results plus a five-seed supervised robustness check [3, App. A.6.1]; iTransformer reports five-run standard deviations [5, App. A.2, Table 5]. Neither passage establishes three seeds as their shared convention. Our choice is a compute compromise. Bouthillier et al. distinguish repeated-run precision from broader benchmark variation [19]. Extra seeds can improve the former; extra seasons/origins address different uncertainty. Ten reproduction repetitions do not make the separate three-seed benchmark equally precise.
+p46 Say to the supervisor. Three seeds are our compute compromise. Both cited papers provide five-seed robustness evidence, motivating stronger checks [3, 5].
+p47 Reading locator. PatchTST [3], Appendix A.6.1; iTransformer [5], Appendix A.2 and Table 5; Bouthillier et al. [19], Appendix C.3.
+p48 Evidence. ESSAY_VS_REPRODUCTION_TABLE_V.csv; BENCH_MSE_BY_MODEL_L.csv; dlv/data.py ORACLE
+p49 Q05 Which implementation differences are established?
+p50 Answer and local evidence. The local code selects checkpoints on validation and scores all seven standardised channels. Supplied notes attribute test-selected checkpoints and a one-channel loader to upstream code, but no independently inspected pinned author checkout supports that attribution here. Notes also describe differences in learning-rate and epoch settings. Consequently we disclose the local procedure and unresolved reference settings rather than claiming that exactly two repairs explain every score difference. A fair causal comparison would hold data, seeds and all other settings fixed while changing one factor.
+p51 Paper-based reasoning. A checkpoint is a model-selection choice. Selecting it by test error uses the final evaluation to fit that choice, contrary to clean separation [22, L1]. This justifies our validation-selected checkpoint independently of whether a particular upstream bug can be proved. Scoring all seven declared channels is a separate metric-consistency issue. Neither principle proves Moon et al. committed the alleged defects or that exactly two changes caused our gap. Causal attribution needs matched runs changing checkpoint selection, loader or another factor one at a time.
+p52 Say to the supervisor. Validation selection protects the held-out test; upstream defect attribution is a separate evidence question [22].
+p53 Reading locator. Kapoor and Narayanan [22], taxonomy L1, clean separation through modelling and evaluation.
+p54 Evidence. train_miflu.py; audit/REPO_AUDIT.md; audit/UNVERIFIED_ITEMS.md
+p55 We use a chronological split and train-only scaling. Validation selects checkpoints in this implementation. The handoff attributes test-set checkpoint selection and a one-variable loader to upstream code, but a pinned author checkout is absent and the public endpoint could not be opened. Those upstream allegations remain unverified. The notes also show learning-rate differences between code defaults and paper settings, so the comparison must not be described as differing in only two ways.
+p56 Peak timing error (PTE) is the absolute difference between predicted and observed peak weeks. Peak intensity error (PIE) is the absolute peak-height error divided by the observed peak, expressed as a percentage. Kramer–Shaman [2] verifies the separate one-week and 25% tolerances. We apply both to mean errors in each (model, L, step) cell. This joint screen and its peak detector are project choices, not a clinical acceptance standard. A mean-error pass is not an individual-season success probability.
+p57 Q06 Why use seven-variable MSE but ILITOTAL peak errors?
+p58 Answer and local evidence. Seven-variable MSE averages squared errors after each channel has been standardised, so it measures overall dimensionless forecast error. This average loss is not itself a patient-count time series and has no single inverse scaler. Peak timing and height require an actual series. We therefore compute them on ILITOTAL after its own training-fit inverse transform, with mean 9,439.84 and standard deviation 9,003.15 patients. A model can do well across seven channels while having worse ILITOTAL peaks. Different targets and loss functions help explain the different rankings.
+p59 Paper-based reasoning. Hyndman and Koehler explain why measurement scale matters [21, §2.1]; Kramer and Shaman define peaks on an observed disease series [2]. Our standardised aggregate divides each channel’s squared error in original units by its training variance. The result is a dimensionless loss, not a patient-count curve with one inverse scaler. For peaks, inverse-transform ILITOTAL predictions and observations first, then locate peaks. Taking a peak of the seven-channel loss would answer a different question. Literature motivates an interpretable endpoint; ILITOTAL is our explicit operational choice.
+p60 Say to the supervisor. Overall standardised error and an interpretable disease peak are different endpoints [21, 2].
+p61 Reading locator. Hyndman and Koehler [21], §2.1; Kramer and Shaman [2], Forecast accuracy and comparison.
+p62 Evidence. BENCH_MSE_BY_MODEL_L.csv; BENCH_PTE_PIE_BY_STEP.csv; scaler_miflu_author966.json
+p63 3 Reproduction of MIFlu
+p64 The reproduction CSV reports mean MSE 1.4995 versus 1.4355, a 4.5% increase. MSE is lower at L24 and L36 and higher at L48 and L60. Mean MAE is 0.8043 versus 0.7452 (+7.9%), but its signs are one lower and three higher; MAE does not share the MSE 2–2 crossover. Protocol and missing upstream provenance limit claims of exact replication.
+p65 Table 3. MIFlu reproduction compared with the paper
+p66 Source: ESSAY_VS_REPRODUCTION_TABLE_V.csv, lines 2–6. SD is recomputed from the code-transcribed ten-seed oracle; its raw run logs are not included. Positive differences mean higher error.
+p67 Reproduction conclusion. The observed MSE gap is +4.5% under disclosed implementation differences. This does not establish superiority over the paper.
+p68 Q07 Why is MIFlu 1.4995 here but 1.5574 in the benchmark?
+p69 Answer and local evidence. The first is the four-horizon mean from the ten-seed reproduction table. The second is the four-horizon mean under the three benchmark seeds. They summarise separate run sets. Compare 1.4995 with the reported paper mean 1.4355 for reproduction, and compare 1.5574 with other models in the benchmark for model selection. Their difference is not a demonstrated improvement, degradation or transcription error between two otherwise identical experiments. Full run configuration and raw provenance are required to attribute it.
+p70 Paper-based reasoning. Bouthillier et al. show that benchmark estimates depend on the sampled learning pipeline [19]. A mean is therefore an estimate over specified runs, not an immutable property of a model name. Our two MIFlu estimates summarise separate seed sets and serve different comparisons. The gap could combine seed variability with configuration differences; it does not isolate one cause. Explain each table’s run definition first, then request matched run-level configurations if the cause of the difference matters.
+p71 Say to the supervisor. They estimate separate run sets; the difference is not a controlled effect of one change [19].
+p72 Reading locator. Bouthillier et al. [19], §§2–3, benchmark estimators and sources of variation.
+p73 Evidence. ESSAY_VS_REPRODUCTION_TABLE_V.csv lines 2–6; BENCH_MSE_BY_MODEL_L.csv model=miflu
+p74 Q08 Why do MSE and MAE give different sign patterns?
+p75 Answer and local evidence. MSE squares errors and gives larger errors more weight. MAE averages absolute errors. Changing a few large errors can therefore alter MSE and MAE differently. Relative to the paper values, MSE is lower at L24/L36 and higher at L48/L60, whereas MAE is lower only at L36 and higher at the other three. The means are +4.5% MSE and +7.9% MAE. Calling both a two-versus-two crossover would misread the table.
+p76 Paper-based reasoning. The paper distinguishes squared and absolute errors and their sensitivity to large residuals [21]. As an algebraic illustration, not an observed run, doubling a residual doubles its absolute contribution but quadruples its squared contribution. A changed residual distribution can thus move MSE and MAE differently. Our CSV determines the actual horizon signs; the literature explains why different signs are possible. Per-channel and per-window residuals, rather than this general principle alone, are needed to identify the actual errors behind the gap.
+p77 Say to the supervisor. MSE weights large residuals more strongly than MAE, so the horizon signs must be read separately [21].
+p78 Reading locator. Hyndman and Koehler [21], §2.1, MSE/MAE and sensitivity to large residuals.
+p79 Evidence. ESSAY_VS_REPRODUCTION_TABLE_V.csv lines 2–6
+p80 Table 4. Code-transcribed reproduction oracle
+p81 Arithmetic checked against the reproduction CSV. The source is the ORACLE constant in dlv/data.py and verify_miflu_oracle.py. Raw ten-seed run logs were not supplied, so this is not an independent raw-prediction verification.
+p82 Q09 Do the seed oracle and plots prove a complete reproduction?
+p83 Answer and local evidence. The oracle is a code-transcribed record of ten seed scores. Its means and standard deviations can be checked arithmetically, but the corresponding raw ten-seed logs and predictions are not supplied for independent rescoring. The imported plots illustrate the benchmark series and are not independent traces of those ten reproduction runs. Checkpoint choice, seed variability and configuration differences are possible explanations for the horizon pattern, not isolated causal findings. The defensible result is a +4.5% mean-MSE gap under disclosed limits.
+p84 Paper-based reasoning. Repeated-run estimates and traceable evaluation address different weaknesses [19, 22]. The oracle checks the arithmetic of a transcribed record; saved predictions would check whether the pipeline produced it. The practical chain is run configuration → prediction → scoring code → cell → aggregate. A benchmark plot is another summary and cannot establish a ten-seed reproduction trajectory. Missing links limit the claim even when the mean is close. The imported panels remain useful illustrations if their true provenance is stated.
+p85 Say to the supervisor. The oracle establishes arithmetic; raw outputs establish provenance. Both evidence levels matter [19, 22].
+p86 Reading locator. Bouthillier et al. [19], variance analysis; Kapoor and Narayanan [22], model info sheets.
+p87 Evidence. dlv/data.py ORACLE; ESSAY_VS_REPRODUCTION_TABLE_V.csv; figure_captions.json
+p89 miflu, L=24. ILITOTAL in patient counts against the file’s test-week index. Black is the observed series; the other curves use fixed forecast steps s0–s3. Scored windows: 160. Imported illustrative figure; raw figure inputs were not independently regenerated in this audit.
+p91 miflu, L=60. ILITOTAL in patient counts against the file’s test-week index. Black is the observed series; the other curves use fixed forecast steps s0–s3. Scored windows: 128. Imported illustrative figure; raw figure inputs were not independently regenerated in this audit.
+p92 4 Benchmark accuracy
+p93 Table 5. Accuracy of all retained benchmark arms
+p94 Source: BENCH_MSE_BY_MODEL_L.csv, keyed by model and L. Each row averages three seeds on 160/144/144/128 windows. DLinear is excluded by project choice; that exclusion needs a documented sensitivity analysis. Names denote project implementations, whose equivalence to published methods is not established by this ranking.
+p95 Q10 What do the 28 models and different subsets mean?
+p96 Answer and local evidence. The retained roster is 13 conventional + 4 LLM-based + 11 frozen encoders. Accuracy and peak analysis cover all 28. Parameter exports support 11 arms, while paired tests cover 17 non-encoder models including MIFlu. DLinear is excluded from the retained roster and paired table by project choice. Its appearance in historical provenance does not make it a retained arm. A sensitivity analysis including DLinear would strengthen baseline coverage; prior appearance in the source paper is not by itself a scientific reason to omit it.
+p97 Paper-based reasoning. The families test different explanations: simple temporal mapping [4], patches and inverted variable tokens [3, 5], and explicit cross-modal alignment [7, 8]. This motivates diverse controls, not a claim that 28 is an optimal count. It also makes implementation fidelity important: a named adaptation may omit a paper’s decisive alignment or training component. DLinear is a relevant simple control in this literature. Its appearance in the source paper is not itself a scientific reason to omit it from a sensitivity analysis.
+p98 Say to the supervisor. The papers motivate different controls; the exports determine which models each analysis actually covers [3–5, 7, 8].
+p99 Reading locator. Zeng et al. [4], §4; PatchTST [3], §3.1; iTransformer [5], §3; CALF [7] and TimeCMA [8], author abstracts.
+p100 Evidence. BENCH_MSE_BY_MODEL_L.csv; BENCH_EFFICIENCY.csv; BENCH_PAIRED_TESTS.csv; BENCH_GPU_PROVENANCE.csv
+p101 Q11 Does the lowest MSE make MIFlu the deployment winner?
+p102 Answer and local evidence. MIFlu has the lowest observed benchmark MSE, 1.5574. That is a descriptive accuracy result under one national split. It does not measure the cost of missed peaks, false alarms, runtime, regional robustness or prospective benefit. The larger MSE spread also does not establish that hyperparameter tuning is unimportant, because tuning was not experimentally varied as an alternative factor. The later evaluation axes ask additional questions that the accuracy table alone cannot answer.
+p103 Paper-based reasoning. Peak timing/intensity are disease-specific endpoints [2], while interval scoring evaluates predictive uncertainty [18]. A seven-channel point-error ranking supplies neither automatically. Separate observed accuracy, peak trade-offs and operational cost. NLinear’s lower height error does not erase its worse mean timing; MIFlu’s lowest MSE does not establish calibrated intervals or prospective benefit. This lets us defend an evidence-based selection process before claiming a public-health deployment winner.
+p104 Say to the supervisor. MIFlu wins the observed point-error ranking; peak endpoints and uncertainty need their own evidence [2, 18].
+p105 Reading locator. Kramer and Shaman [2], Forecast accuracy and comparison; Bracher et al. [18], §§3–4.
+p106 Evidence. BENCH_MSE_BY_MODEL_L.csv; audit/GRADE_READINESS.md
+p107 F0 conclusion. MIFlu has the lowest observed MSE (1.5574), but MSE alone does not establish public-health utility. The top-three spread is 20.2% relative to MIFlu, not less than 20%.
+p108 The roster is 13 conventional models, MIFlu plus three other LLM-based implementations, and 11 frozen encoders. These sum to 28. All 28 have lower mean MSE than the seasonal-naive export (6.2132). No claim about hyperparameter tuning being less important is supported.
+p110 patchtst, L=24. ILITOTAL in patient counts against the file’s test-week index. Black is the observed series; the other curves use fixed forecast steps s0–s3. Scored windows: 160. Imported illustrative figure; raw figure inputs were not independently regenerated in this audit.
+p112 nlinear, L=24. ILITOTAL in patient counts against the file’s test-week index. Black is the observed series; the other curves use fixed forecast steps s0–s3. Scored windows: 160. Imported illustrative figure; raw figure inputs were not independently regenerated in this audit.
+p113 5 Peak timing and magnitude
+p114 Peak timing error (PTE) is the absolute difference between predicted and observed peak weeks. Peak intensity error (PIE) is the absolute peak-height error divided by the observed peak, expressed as a percentage. Kramer–Shaman [2] verifies the separate one-week and 25% tolerances. We apply both to mean errors in each (model, L, step) cell. This joint screen and its peak detector are project choices, not a clinical acceptance standard. A mean-error pass is not an individual-season success probability.
+p115 Table 6. Peak timing and intensity error
+p116 Means are across 16 (L, step) cells. Passes apply PTE ≤ 1 week and PIE ≤ 25% to each cell’s aggregated errors, not to each individual season. PIE is point-forecast magnitude error, not probabilistic calibration.
+p117 Table 7. Joint peak screen for each horizon and lead
+p118 Each entry gives PTE in weeks / PIE in percent. s0–s3 are the first to fourth forecast weeks. The detector uses prominence 0.15 × range, distance 15, and ±8-week matching. These detector settings and joint aggregation are project choices. Source: BENCH_PTE_PIE_BY_STEP.csv.
+p119 Q12 Why do MIFlu and NLinear both pass 4/16?
+p120 Answer and local evidence. A pass requires mean PTE ≤ 1 week and mean PIE ≤ 25% in the same (L, step) cell. NLinear passes step 0 at all four horizons. MIFlu passes step 0 at L24/L36/L60 and step 1 at L48. Equal counts therefore hide different locations and error magnitudes. Across all 16 cells, NLinear has lower PIE, 9.477% versus 26.846%, while MIFlu has lower PTE, 1.128 versus 1.677 weeks. The result is a timing–height trade-off, not dominance by either model.
+p121 Paper-based reasoning. The separate literature endpoints motivate inspecting timing and height before reducing them to a pass count [2]. Our equal four-pass counts hide different lead/horizon locations and distances from the thresholds. An application emphasising one-week-ahead height could favour a different trade-off from an application emphasising timing. That conditional interpretation comes from our table, not from a literature recommendation of NLinear. A binary pass is a coarse summary of continuous errors.
+p122 Say to the supervisor. Equal counts conceal different cells and a timing–height trade-off [2].
+p123 Reading locator. Kramer and Shaman [2], Forecast accuracy and comparison, separate timing/intensity tolerances.
+p124 Evidence. BENCH_PTE_PIE_BY_STEP.csv model in {miflu,nlinear}
+p125 Q13 Does 4/16 mean a 25% chance of a correct epidemic forecast?
+p126 Answer and local evidence. No. The denominator is four horizons times four fixed forecast steps, not 16 independent seasons. Each cell already averages errors across the available runs/events. Applying thresholds after averaging can give a different answer from counting individual successful events. The separate timing and intensity tolerances are supported by Kramer–Shaman [2]; our conjunction on aggregated cells and detector settings are project choices. They are not a clinical acceptance test or a calibrated probability.
+p127 Paper-based reasoning. Kramer and Shaman evaluate forecast-level peak accuracy by lead time [2]. Our sixteen configuration cells have a different denominator. Applying a threshold to an average is mathematically different from averaging event-level pass indicators. Thus 4/16 cannot be relabelled as season success probability. Bracher et al. discuss calibration of predictive distributions [18, §4.2]; small peak-height error does not establish it. Estimating event success requires retaining individual outcomes, defining the event denominator and accounting for dependence.
+p128 Say to the supervisor. Our denominator counts configurations after averaging, not successful seasons or calibrated probabilities [2, 18].
+p129 Reading locator. Kramer and Shaman [2], Forecast accuracy and comparison / Fig. 2; Bracher et al. [18], §4.2.
+p130 Evidence. BENCH_PTE_PIE_BY_STEP.csv; Kramer–Shaman [2]; analysis peak detector settings
+p131 F1 conclusion. NLinear and MIFlu each pass 4/16 aggregated cells, while PatchTST passes 0/16. NLinear has lower mean PIE (9.477% versus MIFlu 26.846%) but higher mean PTE (1.677 versus 1.128 weeks). This is a timing–magnitude trade-off, not dominance. The ordering is inverted at both ends among the three leaders: MSE orders MIFlu, PatchTST, NLinear; PIE orders NLinear, MIFlu, PatchTST.
+p133 Peak error heat map for all 28 retained arms. Cells display means across horizons at fixed steps. Mean-level highlighting must not be interpreted as every horizon passing; the detailed grid gives per-horizon passes. Source: BENCH_PTE_PIE_BY_STEP.csv.
+p134 The positive MSE–PIE rank correlation (+0.736) means lower MSE generally accompanies lower PIE. The negative MSE–pass-count correlation (−0.429) also has the expected direction: lower error tends to accompany more passes. Neither statistic proves decoupling. NLinear’s third-place MSE but first-place PIE provides a local mismatch between objectives.
+p135 Q14 Why can peak rankings differ without proving decoupling?
+p136 Answer and local evidence. The leading-three MSE order is MIFlu < PatchTST < NLinear; the PIE order is NLinear < MIFlu < PatchTST. Ordering is inverted at both ends, with different middle positions. Across all models, MSE–PIE correlation is positive (+0.736) and MSE–pass-count correlation negative (−0.429), both in the expected direction for generally better error. A local rank mismatch can coexist with those overall associations. We can claim that objectives change the ordering, not statistical independence or universal peak failure.
+p137 Paper-based reasoning. Zeng et al. describe NLinear’s last-value subtraction, linear map and addition back [4]. This gives a testable hypothesis about level handling, not a proven explanation for our peaks. The ranking mismatch itself follows a simpler distinction: MSE aggregates many points and seven channels, whereas PIE concentrates on detected ILITOTAL peak height [21 gives the error-measure context]. A model can improve many non-peak points yet worsen this endpoint. Controlled variants and peak/residual diagnostics are needed to attribute the observed trade-off to architecture.
+p138 Say to the supervisor. The objectives aggregate different errors; NLinear’s level correction is a hypothesis to test [4, 21].
+p139 Reading locator. Zeng et al. [4], §4 NLinear; Hyndman and Koehler [21], §2.1.
+p140 Evidence. BENCH_MSE_BY_MODEL_L.csv joined to BENCH_PTE_PIE_BY_STEP.csv; audit/verified_facts.json
+p141 6 Accuracy and parameter count
+p142 Table 8. Parameter analysis and rank associations
+p143 The Pareto analysis includes only 11 arms with parameter exports. MIFlu and the frozen encoders are not in that subset. Missing parameter counts are not zero. Parameter count is not a measurement of latency, memory or energy. Correlations are descriptive across models on one test set.
+p144 Q15 How should I explain the Pareto graph?
+p145 Answer and local evidence. The horizontal axis is parameter count and the vertical axis is MSE, so smaller values are preferred on both. A model is dominated within the measured subset if another has no more parameters and no higher MSE, with at least one strict improvement. The exported frontier contains NLinear and PatchTST: NLinear is smaller, while PatchTST has lower MSE. Neither dominates the other. This frontier covers only the 11 arms with parameter exports; MIFlu and the encoders are outside it, so a global frontier claim is unsupported.
+p146 Paper-based reasoning. iTransformer evaluates error alongside speed and memory [5, App. D], a precedent for considering performance with cost. Our cost axis is narrower: exported parameters. The two local frontier members follow from pairwise dominance in the eleven-model subset, not a paper’s recommendation of a universal winner. A Pareto graph removes dominated choices; the remaining choices still need a budget or acceptable-error preference. Missing MIFlu cost data prevents calling it the frontier of all 28 models.
+p147 Say to the supervisor. The frontier removes dominated choices within the measured subset; a decision preference still chooses among them [5].
+p148 Reading locator. iTransformer [5], Appendix D Model Efficiency; local BENCH_EFFICIENCY.csv.
+p149 Evidence. BENCH_EFFICIENCY.csv; fig_pareto_frontier.png
+p150 Q16 Does 211 times more parameters mean 211 times slower?
+p151 Answer and local evidence. No. 531,878 / 2,520 = 211.1 compares exported PatchTST and NLinear parameter counts. Their observed MSE reduction is (1.871583 − 1.662078) / 1.871583 ≈ 11.2%. Parameter storage, operations, hardware utilisation and batch size affect runtime differently. Latency, peak memory and energy require direct comparable measurements. We use the phrase parameter efficiency, and leave missing parameter counts missing rather than treating them as zero or describing MIFlu as non-parametric.
+p152 Paper-based reasoning. iTransformer measures speed and memory under stated input/prediction lengths and the same batch size [5, App. D]. Our parameter export does not supply those measurements. Parameters affect storage; operations, token counts and hardware utilisation affect elapsed time differently. Consequently 211× parameters cannot imply 211× latency, memory or energy. A useful next efficiency table records hardware, precision, batch size and whether training or inference is timed. These fields cannot be invented from the parameter ratio.
+p153 Say to the supervisor. I report a parameter ratio. The literature shows the matched runtime measurements needed for a speed claim [5].
+p154 Reading locator. iTransformer [5], Appendix D, Fig. 10, matched speed/memory measurements.
+p155 Evidence. BENCH_EFFICIENCY.csv; BENCH_MSE_BY_MODEL_L.csv model in {nlinear,patchtst}
+p156 Q17 What does R squared of 0.0223 actually mean?
+p157 Answer and local evidence. For the chosen fit of MSE against log10(parameter count) in 11 exported arms, parameter size alone accounts for little observed variation. This descriptive association does not isolate the effect of capacity: architectures, optimisation and training regimes also vary. A low R squared does not prove that capacity is irrelevant or that an observed accuracy gain is random noise. A causal capacity study would vary size within a controlled family and training protocol.
+p158 Paper-based reasoning. PatchTST varies layers and hidden dimension and specifically finds ILI sensitive to those settings [3, App. A.6.2]. This is relevant evidence against dismissing tuning on a small influenza series. Our cross-model R² mixes architecture, optimisation and size; it is not a controlled capacity effect. A stronger follow-up varies depth/width within one family under a fixed training protocol and repeats runs. The planned MIFlu depth ladder begins this question, but its unaggregated status provides no scientific trend yet.
+p159 Say to the supervisor. Low cross-model R² does not dismiss tuning; PatchTST explicitly reports ILI sensitivity [3].
+p160 Reading locator. PatchTST [3], Appendix A.6.2, Fig. 5, layers/width and ILI sensitivity.
+p161 Evidence. BENCH_EFFICIENCY.csv; scripts/verify_snapshot.py linregress
+p162 F2 conclusion. The fitted slope is +0.1171 and R² is 0.0223 across the 11 arms with exported parameter counts. Size alone explains little of their observed MSE variation. This subset result does not prove that capacity is irrelevant.
+p164 Accuracy–parameter trade-off among 11 models with exported parameter counts. MIFlu and frozen encoders are omitted from this subset. Parameter count is not a measured runtime or memory cost. Source: BENCH_EFFICIENCY.csv.
+p165 7 Statistical audit
+p166 The source table contains 136 pairs from 17 models. The other 11 models are absent, so this is not an all-pairs analysis of 28 models. Holm uses a forward cumulative maximum after sorting raw p-values. The source uses a reverse cumulative minimum. At n=12, the two-sided exact floor 2/4096 multiplied by 136 exceeds 0.05, so this family cannot yield a rejection under proper Holm adjustment. Overlapping targets and repeated horizons also make the cells dependent. Raw p-values and unadjusted bootstrap intervals remain exploratory.
+p167 Table 9. Paired comparisons with corrected Holm adjustment
+p168 136 pairs cover 17 models, not all 28. n = 12 matched horizon × seed cells. Forward cumulative-max Holm yields 0/136 rejections. The shown p values recover the exact 1/4096 enumeration grid from six-decimal exports; recomputing directly from rounded exports gives NLinear–PatchTST 0.117180 instead of 0.1171875. *The source effect uses pooled model SD, not paired-difference SD. Cell dependence limits inference.
+p169 Q18 Why does the paired table contain seemingly unrelated model pairs?
+p170 Answer and local evidence. The report deliberately shows the NLinear–PatchTST frontier comparison first, followed by six rows with the smallest raw p-values. This combines the question of interest with examples of the wider test family. The frontier pair is 117th by ascending raw p in the exported table, so an automatic smallest-six display would omit it. The full family still contains all 136 comparisons; displayed-row selection never changes the Holm family or makes the selected pair significant.
+p171 Paper-based reasoning. Demšar motivates controlling the comparison family when inspecting particular differences [20]. Here the first row keeps the substantive frontier question visible; the next six show smaller raw-p contrasts. All 136 still enter the correction. Rank 117 refers to ascending raw p, not a model’s accuracy rank. Choosing display rows cannot change that family. Because the article’s main setting is multiple datasets, it also does not licence treating our overlapping horizons and shared test series as independent datasets.
+p172 Say to the supervisor. The first row serves the research question; the full family still determines correction [20].
+p173 Reading locator. Demšar [20], §3.2.2 Post-hoc tests; local raw-p rank.
+p174 Evidence. BENCH_PAIRED_TESTS.csv model_a=nlinear/model_b=patchtst; audit/verified_facts.json pair_raw_rank
+p175 Q19 Why do 128 raw significant pairs become zero after Holm?
+p176 Answer and local evidence. Testing many pairs increases the opportunity for false positives. Proper Holm sorts raw p-values and applies a forward cumulative maximum to the ordered multiplicity factors. The original exported column used the wrong direction and is quarantined. Recomputing all 136 gives 0/136 rejections, with minimum adjusted p about 0.0664 and NLinear–PatchTST 0.1172. With the documented two-sided exact n=12 resolution, the smallest possible raw p is 2/4096, already too large for Holm’s first 0.05/136 threshold. Dependence between horizon–seed cells is an additional concern.
+p177 Paper-based reasoning. Demšar describes starting with the smallest p and stopping at the first failed Holm threshold [20]. Our first threshold is 0.05/136. The documented two-sided twelve-contribution sign-flip floor is 2/2^12; multiplying by 136 gives 0.06640625, so no pair can start the rejection sequence. This floor is local mathematical reasoning, not a result reported by Demšar for influenza. Holm permits dependence among valid p-values, but cannot repair invalid raw p-values from unjustified within-pair exchangeability. These are separate limitations.
+p178 Say to the supervisor. The exact-test floor exceeds Holm’s first threshold; that is a design-resolution limit [20].
+p179 Reading locator. Demšar [20], §3.2.2 Holm step-down; local exact-enumeration derivation.
+p180 Evidence. BENCH_PAIRED_TESTS.csv p_raw; analysis_postprocess.py; audit/HOLM_RECOMPUTATION.csv
+p181 Q20 Does p = 0.1172 show that NLinear and PatchTST are equivalent?
+p182 Answer and local evidence. No. PatchTST retains 11.2% lower observed mean MSE and lower error in 10/12 matched cells. Non-rejection means this familywise procedure does not establish a difference at the chosen threshold. It does not establish a small enough difference for practical equivalence. Equivalence needs a prespecified acceptable margin and a suitable uncertainty/test design. The table’s source effect also uses pooled model standard deviation rather than paired-difference standard deviation, so it is labelled as a source standardised effect.
+p183 Paper-based reasoning. Lakens distinguishes a nonsignificant difference test from equivalence with prespecified meaningful bounds [25]. Thus p = 0.1172 does not answer whether NLinear’s observed extra error is acceptable for an application. Define that acceptable difference first, then use an uncertainty design respecting time/season dependence. Choosing a generous bound after seeing this table would not be convincing confirmation. Until then, observed error reduction, parameter ratio and inferential uncertainty should be reported together; the extra parameters cannot be dismissed as buying only noise.
+p184 Say to the supervisor. Non-rejection is not equivalence; the observed trade-off and unresolved inference coexist [25].
+p185 Reading locator. Lakens [25], Introduction and Testing for Equivalence.
+p186 Evidence. BENCH_EFFICIENCY.csv; BENCH_PAIRED_TESTS.csv; audit/CLAIM_AUDIT.md C3
+p187 F3 conclusion. Proper Holm gives 0/136 rejections (128/136 before adjustment), with a minimum adjusted p of about 0.0664 and NLinear–PatchTST p ≈ 0.1172. PatchTST still has 11.2% lower observed MSE with 211× the parameters and lower MSE in 10/12 cells. Non-rejection does not establish equivalence or show that the gain is noise.
+p188 8 Frozen language encoders
+p189 Table 10. Frozen encoders with shared linear readout
+p190 11 retained encoders × 4 horizons × 3 seeds = 132 cells. The historical plan included two additional embedding-only arms, giving 156 planned cells; those 24 omitted cells are outside the 28-model roster. The result tests only this frozen-feature pipeline.
+p191 Q21 What can the frozen-encoder negative result explain?
+p192 Answer and local evidence. The tested pipeline freezes a language encoder and trains a linear readout. Its 11 encoder arms have MSE 4.7374–5.2049, all above decision tree 4.3198, with 0/16 joint passes each. This shows poor performance of these feature/readout configurations on this protocol. Distribution mismatch, frozen features and readout capacity are possible mechanisms, but the experiment does not separate them. Generation, prompting, fine-tuning and numerically pretrained time-series foundation models remain outside this test.
+p193 Paper-based reasoning. Time-LLM freezes its LLM but adds learned reprogramming and a prompt prefix [6]. Thus “frozen” alone does not define the same experiment as our feature/linear-readout pipeline. Chronos instead learns forecasting from numerical sequences [9]. These method differences justify keeping our negative finding narrow. To isolate a readout bottleneck, vary the readout/alignment while holding the encoder fixed; to isolate pretraining, compare matched pretrained and random backbones. Our eleven-arm result does not make those controlled separations.
+p194 Say to the supervisor. The failure concerns our feature/readout pipeline; Time-LLM and Chronos test other mechanisms [6, 9].
+p195 Reading locator. Time-LLM [6], author abstract; Chronos [9], §3.
+p196 Evidence. BENCH_MSE_BY_MODEL_L.csv family=llm_encoder; BENCH_PTE_PIE_BY_STEP.csv
+p197 F4 conclusion. The 11 tested frozen encoders score 4.7374–5.2049, or 3.04–3.34× MIFlu’s MSE. All exceed the decision tree’s 4.3198 and pass 0/16 cells. This is a negative result for this feature/readout configuration; prompting, fine-tuning and numerical foundation models remain untested.
+p198 Distribution mismatch, frozen capacity and the chosen readout are possible explanations. Their causal roles are not separated by these results. A linear readout does not guarantee that useful nonlinear features can be recovered.
+p199 9 Ablation design and status
+p200 Table 11. Ablation design and snapshot status
+p201 Owner-reported status at 3 November 2026: 27/60 additional cells, job 722968. No live HPC check or per-variant result export was available. The baseline 12 cells are not part of the additional 60. No trend is inferred.
+p202 F5 provisional conclusion. In miflu_model.py’s author_faithful path, text follows time tokens behind causal attention and the head reads the time tokens. Static inspection therefore predicts no text influence during deterministic evaluation. The supplied tests_archive/test_miflu_ablations.py explicitly asserts both text invariance and full/no-text equality with matched CPU initialisation. It was inspected statically, not executed here. Other fusion paths and training randomness require separate checks.
+p203 Q22 Why might no-text give identical outputs in the default path?
+p204 Answer and local evidence. In the inspected author_faithful path, time tokens precede text tokens. Causal attention permits each position to read only its own or earlier positions, and the head reads the time-token positions. Those positions therefore cannot use later text in a deterministic evaluation forward pass. The supplied archive explicitly asserts text invariance and matched-initialisation full/no-text CPU equality, but those model tests were not executed here. Other fusion paths, dropout and independently trained trajectories require separate checks. The exact files and commands are in audit/NO_TEXT_VERIFICATION.md.
+p205 Paper-based reasoning. The Transformer paper explains masking that prevents attention to subsequent positions [24, §3.1]. With the inspected ordering, time positions cannot acquire later text through these layers, and the head reads time positions. This is a structural argument about a fixed forward path, not certification of repository runtime or bitwise equality. The three archived assertions must control weights, inputs and evaluation randomness when comparing changed text and matched full/no-text outputs. They remain not executed. Independent training can consume randomness differently and requires its own test.
+p206 Say to the supervisor. Causal masking supports the structural argument; controlled runtime tests must establish bitwise equality here [24].
+p207 Reading locator. Vaswani et al. [24], §3.1 Decoder; local ForecastingLLM.forward and archived assertions.
+p208 Evidence. miflu_model.py ForecastingLLM; tests_archive/test_miflu_ablations.py; audit/NO_TEXT_VERIFICATION.md
+p209 Q23 What does 27/60 ablation completion allow us to say?
+p210 Answer and local evidence. It is an owner-reported operational snapshot as of 3 November, not a live scheduler result or an aggregated model comparison. The additional design has five arms, each with four horizons and three seeds: 60 cells beyond the 12-cell reference. Without per-arm result exports, completion is not evidence of a depth trend or a benefit of LoRA. Do not infer a completed no-text ablation from the presence of its test assertions. We need run-level outputs, status and provenance before reporting scientific results.
+p211 Paper-based reasoning. Tan et al. remove or replace the LLM while retaining the surrounding trainable forecaster [13, §3.2]. This asks whether the backbone contributes beyond the wrapper. Our no-LoRA/depth variants address narrower adaptation/capacity questions; they do not automatically answer the same removal/replacement question or isolate text use. Partial completion is an operational status. Interpreting a scientific trend requires the reported variants’ scores, repeated-run variability and a matched protocol. The literature supplies an experimental question, not a result for our unfinished ladder.
+p212 Say to the supervisor. The papers motivate removal/replacement controls; the incomplete ladder has not answered those causal questions [13].
+p213 Reading locator. Tan et al. [13], §3.2 Proposed Ablations, w/o LLM / LLM2Attn / LLM2Trsf.
+p214 Evidence. Owner snapshot; ablation design table; tests_archive/test_miflu_ablations.py
+p215 10 Interpretation and publication plan
+p216 One national series and one chronological split do not establish regional or prospective utility. Peak matching can use future observations to define events and is a retrospective evaluation tool. Synthetic date labels require a verified CDC calendar mapping before season-specific claims. Parameter exports omit MIFlu and encoders. The 27/60 ablation status is owner-reported, not a live cluster check. Modern numerical foundation baselines, regional results, rolling origins and validated uncertainty are missing.
+p217 Decision rule for future validation: specify an MSE budget B, an allowable peak-failure rate q, and decision costs before inspecting a new test period. Among models meeting B and q on validation seasons, minimise expected decision cost, then parameter count as a tie-breaker. For an escalate/wait decision, use costs c_FP for unnecessary escalation and c_FN for a missed surge, with zero cost for correct actions. Escalate when a validated surge probability exceeds c_FP/(c_FP+c_FN). Costs, B and q have not been elicited or validated, so no model is certified for deployment. NLinear is a low-cost candidate for further peak-height validation; MIFlu remains the observed MSE leader.
+p218 Recommendation O1: retain the evaluation contribution and repair its evidence base before adding a new mechanism. The current draft is oriented towards IEEE JBHI because its subject is health forecasting, but it is not submission-ready. Rolling origins, regional validation, stronger baselines and independent code provenance matter more than another architecture before the school deadline.
+p219 Q24 What is added beyond reproduction, and why keep O1?
+p220 Answer and local evidence. The study compares implementations across accuracy, peak skill, parameter efficiency and statistical evidence, with different declared subsets. We have not verified that the reference paper contains only the first two axes, so absence or first-ever claims are inappropriate. O1 develops this evaluation contribution through provenance repair, restored tests, rolling origins, regions and stronger controls. Optional O2 is validation-only peak-height recalibration: zero new GPU training if auditable validation/test predictions already exist. Such validation exports are not established here; CPU time and money are unmeasured, and a few working days is only a planning estimate.
+p221 Paper-based reasoning. Simple-linear and LLM-removal critiques predate this project [4, 13]; Qiu et al.’s preprint reports conditional gains in larger cross-dataset settings [14]. Our narrower contribution connects audited influenza accuracy, peak endpoints, a cost subset and corrected inference. O1 checks persistence across origins/regions; Tashman motivates rolling-origin evaluation [23]. O2 adds validation-fitted height adjustment only if suitable prediction exports exist. A new mechanism cannot replace those checks or establish a universal verdict about LLM forecasting.
+p222 Say to the supervisor. O1 tests the influenza-specific findings; prior negative and conditional-positive evidence rule out a universal conclusion [4, 13, 14].
+p223 Reading locator. Zeng et al. [4], §4; Tan et al. [13], §3.2; Qiu et al. [14], abstract and §§3–5 (preprint); Tashman [23], publisher-indexed abstract.
+p224 Evidence. audit/INNOVATION_DECISION.md; audit/LITERATURE_REVIEW.md; sources.json [1]
+p225 11 Reproducibility and open checks
+p226 Run python scripts/verify_snapshot.py --raw-smoke and python -m pytest tests/test_snapshot_audit.py -q from the repository root. The audit re-derives headline aggregates, peak flags, correlations, regression, Holm adjustment and one raw prediction MSE. Seven newly added CPU audit tests passed; they are separate from the archived model suite. The corrected ZIP supplies tests_archive/. Collection fails under the historical layout and missing model dependencies. No archived-suite pass count or reliable collected total is claimed. Training, live HPC status and upstream code were not rerun. The original source CSVs are retained unchanged, with a separate corrected Holm export.
+p227 Hardware provenance covers 204 rows, including the excluded DLinear and omitting MIFlu and all frozen encoders. It overlaps 192 retained cells. Complete per-cell hardware coverage is therefore not established. The original reproduce_all.py targets historical paths and is not the audited quickstart.
+p228 Unverified items: pinned upstream checkpoint/loader protocol and learning rate; archived suite execution and no-text runtime test; ten-seed raw reproduction logs; model revisions/licences; live ablation and regional status; real CDC calendar mapping; current JBHI author limits/JCR record and next-cycle venue dates. Each requires its primary artefact, not a further prose assertion.
+p229 Q25 What can a supervisor reproduce now, and what remains unexecuted?
+p230 Answer and local evidence. The documented CPU commands reproduce CSV headline arithmetic, correct Holm and one raw prediction-cell MSE. Seven new CPU audit checks passed. The historical archive was supplied, but collection failed and its model assertions are not counted as passed. Full GPU training, all-run raw rescoring, live HPC, pinned upstream identity and no-text runtime remain unexecuted or unverified. Hardware provenance also lacks complete retained-cell coverage. A polished document does not close those gaps. Use the exact follow-up commands in audit/EXECUTION_STATUS.md and audit/NO_TEXT_VERIFICATION.md.
+p231 Paper-based reasoning. Kapoor and Narayanan ask for explicit reporting arguments rather than equating code availability with a valid result [22]. Here distinguish document rebuilding, CSV arithmetic, raw prediction rescoring and model retraining. A supervisor can begin with the CSV audit; the full bundle supports one raw-cell smoke check. Model text invariance needs the three named runtime assertions without skips in a pinned environment. The useful deliverable is a traceable evidence chain with exact commands and status. Passing one evidence level does not certify all the others.
+p232 Say to the supervisor. I distinguish recomputed results from static inspection and give the command and status for each [22].
+p233 Reading locator. Kapoor and Narayanan [22], model info sheets; EXECUTION_STATUS.md and NO_TEXT_VERIFICATION.md.
+p234 Evidence. audit/EXECUTION_STATUS.md; audit/NO_TEXT_VERIFICATION.md; audit/REPO_AUDIT.md
+p235 12 References
+p236 [1] Jaeuk Moon, Jonghwa Shim, Eunbeen Kim and Eenjun Hwang, “MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme,” IEEE JBHI 29(10), 7790-7801, 2025. https://doi.org/10.1109/JBHI.2025.3561214
+p237 [2] Sarah C. Kramer and Jeffrey Shaman, “Development and validation of influenza forecasting for 64 temperate and tropical countries,” PLOS Computational Biology 15(2), e1006742, 2019. https://doi.org/10.1371/journal.pcbi.1006742
+p238 [3] Yuqi Nie, Nam H. Nguyen, Phanwadee Sinthong and Jayant Kalagnanam, “A Time Series is Worth 64 Words: Long-term Forecasting with Transformers,” ICLR, 2023. https://arxiv.org/abs/2211.14730
+p239 [4] Ailing Zeng, Muxi Chen, Lei Zhang and Qiang Xu, “Are Transformers Effective for Time Series Forecasting?,” AAAI (preprint record opened), 2023. https://arxiv.org/abs/2205.13504
+p240 [5] Yong Liu et al., “iTransformer: Inverted Transformers Are Effective for Time Series Forecasting,” ICLR (preprint record opened), 2024. https://arxiv.org/abs/2310.06625
+p241 [6] Ming Jin et al., “Time-LLM: Time Series Forecasting by Reprogramming Large Language Models,” ICLR, 2024. https://arxiv.org/abs/2310.01728
+p242 [7] Peiyuan Liu et al., “CALF: Aligning LLMs for Time Series Forecasting via Cross-modal Fine-Tuning,” arXiv:2403.07300, 2024. https://arxiv.org/abs/2403.07300
+p243 [8] Chenxi Liu et al., “TimeCMA: Towards LLM-Empowered Multivariate Time Series Forecasting via Cross-Modality Alignment,” AAAI, 2025. https://arxiv.org/abs/2406.01638
+p244 [9] Abdul Fatir Ansari et al., “Chronos: Learning the Language of Time Series,” Transactions on Machine Learning Research, 2024. https://arxiv.org/abs/2403.07815
+p245 [10] Abhimanyu Das, Weihao Kong, Rajat Sen and Yichen Zhou, “A decoder-only foundation model for time-series forecasting,” ICML, PMLR 235, 10148-10167, 2024. https://proceedings.mlr.press/v235/das24c.html
+p246 [11] Gerald Woo et al., “Unified Training of Universal Time Series Forecasting Transformers,” ICML, PMLR 235, 53140-53164, 2024. https://proceedings.mlr.press/v235/woo24a.html
+p247 [12] Kashif Rasul et al., “Lag-Llama: Towards Foundation Models for Probabilistic Time Series Forecasting,” arXiv:2310.08278, version 3, 2024. https://arxiv.org/abs/2310.08278
+p248 [13] Mingtian Tan, Mike A. Merrill, Vinayak Gupta, Tim Althoff and Thomas Hartvigsen, “Are Language Models Actually Useful for Time Series Forecasting?,” NeurIPS 37, 2024. https://arxiv.org/abs/2406.16964
+p249 [14] Xin Qiu et al., “Rethinking the Role of LLMs in Time Series Forecasting,” arXiv:2602.14744 v1, preprint, 2026. https://arxiv.org/abs/2602.14744
+p250 [15] Chen Xu and Yao Xie, “Conformal prediction interval for dynamic time-series,” ICML, PMLR 139, 11559-11569, 2021. https://proceedings.mlr.press/v139/xu21h.html
+p251 [16] Chen Xu and Yao Xie, “Sequential Predictive Conformal Inference for Time Series,” ICML, PMLR 202, 38707-38727, 2023. https://proceedings.mlr.press/v202/xu23r.html
+p252 [17] Isaac Gibbs and Emmanuel Candès, “Adaptive Conformal Inference Under Distribution Shift,” NeurIPS 34, 2021. https://arxiv.org/abs/2106.00170
+p253 [18] Johannes Bracher, Evan L. Ray, Tilmann Gneiting and Nicholas G. Reich, “Evaluating epidemic forecasts in an interval format,” PLOS Computational Biology 17(2), e1008618, 2021. https://doi.org/10.1371/journal.pcbi.1008618
+p254 [19] Xavier Bouthillier et al., “Accounting for Variance in Machine Learning Benchmarks,” Proceedings of Machine Learning and Systems 3, 2021. https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf
+p255 [20] Janez Demšar, “Statistical Comparisons of Classifiers over Multiple Data Sets,” Journal of Machine Learning Research 7, 1–30, 2006. https://jmlr.org/papers/volume7/demsar06a/demsar06a.pdf
+p256 [21] Rob J. Hyndman and Anne B. Koehler, “Another look at measures of forecast accuracy,” International Journal of Forecasting 22(4), 679–688, 2006. https://doi.org/10.1016/j.ijforecast.2006.03.001
+p257 [22] Sayash Kapoor and Arvind Narayanan, “Leakage and the reproducibility crisis in machine-learning-based science,” Patterns 4, article 100804, 2023. https://doi.org/10.1016/j.patter.2023.100804
+p258 [23] Leonard J. Tashman, “Out-of-sample tests of forecasting accuracy: an analysis and review,” International Journal of Forecasting 16(4), 437–450, 2000. https://doi.org/10.1016/S0169-2070(00)00065-0
+p259 [24] Ashish Vaswani et al., “Attention Is All You Need,” Advances in Neural Information Processing Systems 30, 2017. https://papers.neurips.cc/paper/7181-attention-is-all-you-need.pdf
+p260 [25] Daniël Lakens, “Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses,” Social Psychological and Personality Science 8(4), 355–362, 2017. https://doi.org/10.1177/1948550617697177
+table1/row1 Author | CHAN Sing Yeung
+table1/row2 Snapshot | 3 November 2026
+table1/row3 Reading guide | Four evaluation axes with Q01–Q25 for supervisor discussion
 table2/row1 Item | Value
-table2/row2 Source | CDC national influenza surveillance (US), weekly, as released with MIFlu
-table2/row3 Rows / channels | 966 weekly rows × 7 numeric channels
-table2/row4 Channels | % WEIGHTED ILI, % UNWEIGHTED ILI, AGE 0-4, AGE 5-24, ILITOTAL, NUM. OF PROVIDERS, OT
-table2/row5 Identity check | bit-identical to the author's file, max|diff| = 0.000e+00
-table2/row6 Split (chronological, 70/10/20) | train rows 0–675, validation 676–772, test 773–965 (193 rows)
-table2/row7 Leakage guard | containment = strict; minimum test target-start row = 773
-table2/row8 Scaling | StandardScaler fitted on the training block only (ILITOTAL mean 9,439.84, sd 9,003.15 patients; OT mean 493,629)
-table2/row9 Windows available / scored | L24 170/160 · L36 158/144 · L48 146/144 · L60 134/128  ((W//16)*16)
-table3/row1  | Reproduction protocol | Benchmark protocol
-table3/row2 Question | Does our re-implementation land where the paper's Table V lands? | Which of 28 arms is best, under one common protocol?
-table3/row3 Repetitions | 10 (seeds 2021–2030) | 3 (seeds 42/43/44)
-table3/row4 Reported as | mean over 10 repetitions | mean over 3 seeds
-table3/row5 Metric | 7-variable aggregate MSE/MAE in z-space | 7-var z-space MSE (accuracy) + ILITOTAL PTE/PIE (peak skill)
-table3/row6 Arms | MIFlu only | 28 arms: 13 conventional forecasters, 4 LLM-based forecasters (MIFlu + 3 published), and 11 frozen LLM encoders
-table3/row7 Why this size | it must match the original author's protocol, or it is not a reproduction | the norm in the literature: PatchTST (ICLR'23) and iTransformer (ICLR'24) both report 3-seed means
-table4/row1 Parameter | Ours | Original | Note
-table4/row2 Data | 966 weeks x 7 vars, CDC | Same | Byte-identical (SHA-256)
-table4/row3 Split | 676/97/193 (70/10/20) | Same | Time-ordered
-table4/row4 Input window T | 104 weeks | Same | 
-table4/row5 Horizon L | 24/36/48/60 | Same | Trained independently
-table4/row6 Seeds (repro) | 2021-2030 (10 reps) | fix_seed=2021 (1) | [DEVIATION] Paper claims 10 reps
-table4/row7 Epochs | 20 | default=1 | 1 epoch does not converge
-table4/row8 LR | 1e-4 | code 1e-4 / paper 5e-4 | Paper self-contradictory
-table4/row9 Batch size | 16 | Same | drop_last=True
-table4/row10 Optimizer | Adam | Same | 
-table4/row11 GPT-2 layers/d_model | 6/768 | Same | 
-table4/row12 LoRA | r=4, a=4, drop=0.05, c_attn | Same | 
-table4/row13 Trainable params | 1,673,496 | Same | LoRA+LN+head
-table4/row14 Checkpoint selection | VALIDATION MSE | TEST MSE | [DEVIATION] Test= data leakage
-table4/row15 Metric | 7-var aggregate MSE/MAE | Same (bug: 1 var) | [DEVIATION] Fix bug
-table4/row16 Eval windows | (W//16)*16 = 160/144/144/128 | Same (drop_last side effect) | Not a journal requirement
-table5/row1 Parameter | Ours (benchmark) | Original | Note
-table5/row2 Seeds | 42/43/44 (3 seeds) | fix_seed=2021 (1 run) | PatchTST/iTransformer convention
-table5/row3 Eval windows | (W//16)*16 = 160/144/144/128 | Same (drop_last) | Shared across all 28 models
-table5/row4 Metric | 7-var z-space MSE/MAE | Same | Comparable with Table V
-table5/row5 Peak metric | PTE/PIE on ILITOTAL | N/A | For deployment decisions
-table5/row6 Models | 28 (13 conventional + 4 LLM-based + 11 encoders) | 1 (MIFlu only) | Comprehensive benchmark
-table5/row7 Checkpoint selection | Validation MSE | N/A | Same fix as reproduction
-table5/row8 Hardware | A100-SXM4-80GB | Not disclosed | Provenance recorded
-table6/row1 Horizon | Ours (10-rep mean ± sd) | Paper | Δ MSE | Sign | Ours MAE | Paper MAE | Δ MAE
-table6/row2 L=24 | 1.3045 ± 0.0883 | 1.542 | -15.4 % | WIN | 0.7482 | 0.726 | +3.1 %
-table6/row3 L=36 | 1.3561 ± 0.1603 | 1.422 | -4.6 % | WIN | 0.7712 | 0.779 | -1.0 %
-table6/row4 L=48 | 1.6543 ± 0.1064 | 1.414 | +17.0 % | LOSS | 0.8381 | 0.757 | +10.7 %
-table6/row5 L=60 | 1.6829 ± 0.2109 | 1.364 | +23.4 % | LOSS | 0.8596 | 0.719 | +19.6 %
-table6/row6 4-horizon mean | 1.4995 | 1.435 | +4.5 % | LOSS | 0.8043 | 0.745 | +7.9 %
-table7/row1 Seed | L=24 | L=36 | L=48 | L=60
-table7/row2 s2021 | 1.240157 | 1.314358 | 1.482299 | 1.599641
-table7/row3 s2022 | 1.201078 | 1.306645 | 1.711215 | 1.664878
-table7/row4 s2023 | 1.284212 | 1.269466 | 1.663857 | 1.821282
-table7/row5 s2024 | 1.259462 | 1.154099 | 1.879495 | 1.915250
-table7/row6 s2025 | 1.464643 | 1.767328 | 1.723161 | 1.410785
-table7/row7 s2026 | 1.368497 | 1.312511 | 1.620327 | 1.984315
-table7/row8 s2027 | 1.392309 | 1.400796 | 1.628296 | 1.614602
-table7/row9 s2028 | 1.230425 | 1.302717 | 1.588157 | 1.401814
-table7/row10 s2029 | 1.231536 | 1.404061 | 1.570881 | 1.520661
-table7/row11 s2030 | 1.373057 | 1.328807 | 1.675020 | 1.895393
-table7/row12 mean | 1.3045 | 1.3561 | 1.6543 | 1.6829
-table7/row13 sd (n−1) | 0.0883 | 0.1603 | 0.1064 | 0.2109
-table8/row1 # | Model | Family | MSE L24 | MSE L36 | MSE L48 | MSE L60 | MSE 4L | MAE 4L | Params
-table8/row2 1 | MIFlu | LLM-based | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199 | —
-table8/row3 2 | PatchTST | Transformer | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786 | 531,878
-table8/row4 3 | NLinear | Linear | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183 | 2,520
-table8/row5 4 | DNN | Neural | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057 | 33,048
-table8/row6 5 | TimeCMA | LLM-based | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676 | 125,830,824
-table8/row7 6 | Gradient Boosting | Classical ML | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521 | —
-table8/row8 7 | KNN | Classical ML | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293 | —
-table8/row9 8 | Random Forest | Classical ML | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779 | —
-table8/row10 9 | iTransformer | Transformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476 | 75,672
-table8/row11 10 | Decision Tree | Classical ML | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798 | —
-table8/row12 11 | Hunyuan-1.8B | LLM enc. | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755 | —
-table8/row13 12 | Hunyuan-7B | LLM enc. | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685 | —
-table8/row14 13 | DeepSeek-R1-Qwen-1.5B | LLM enc. | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002 | —
-table8/row15 14 | DeepSeek-R1-Llama-8B | LLM enc. | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786 | —
-table8/row16 15 | GRU | Neural | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174 | 14,424
-table8/row17 16 | DeepSeek-R1-32B | LLM enc. | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935 | —
-table8/row18 17 | LSTM | Neural | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303 | 18,712
-table8/row19 18 | DeepSeek-R1-Qwen-14B | LLM enc. | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019 | —
-table8/row20 19 | DeepSeek-R1-Qwen-7B | LLM enc. | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133 | —
-table8/row21 20 | RNN | Neural | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634 | 5,848
-table8/row22 21 | ContextPilot-8B | LLM enc. | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255 | —
-table8/row23 22 | Hunyuan-4B | LLM enc. | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450 | —
-table8/row24 23 | ContextPilot-14B | LLM enc. | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407 | —
-table8/row25 24 | Qwen2.5-1.5B | LLM enc. | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725 | —
-table8/row26 25 | Qwen-Time | LLM-based | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794 | 1,544,084,680
-table8/row27 26 | SVR | Classical ML | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986 | —
-table8/row28 27 | CALF | LLM-based | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190 | 126,421,416
-table8/row29 28 | CNN | Neural | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720 | 22,488
-table9/row1 Model | PTE s0 (1 wk) | PIE s0 (%) | PTE s1 (2 wk) | PIE s1 (%) | PTE s2 (3 wk) | PIE s2 (%) | PTE s3 (4 wk) | PIE s3 (%) | Passes
-table9/row2 NLinear | 0.21 ✓ | 3.2 ✓ | 1.33 | 6.2 | 2.31 | 11.8 | 2.86 | 16.6 | 4/16
-table9/row3 MIFlu | 0.35 | 18.9 | 0.92 | 25.9 | 1.58 | 30.5 | 1.67 | 32.1 | 4/16
-table9/row4 PatchTST | 0.68 | 30.6 | 1.42 | 32.9 | 1.42 | 33.9 | 1.44 | 33.7 | 0/16
-table9/row5 RNN | 0.96 | 57.6 | 1.97 | 60.0 | 3.00 | 61.8 | 3.97 | 63.2 | 0/16
-table9/row6 GRU | 1.14 | 58.1 | 2.06 | 59.9 | 3.00 | 62.4 | 3.75 | 64.0 | 0/16
-table9/row7 TimeCMA | 1.54 | 50.0 | 2.03 | 51.4 | 2.97 | 55.6 | 2.78 | 57.5 | 0/16
-table9/row8 DNN | 1.92 | 37.8 | 2.64 | 40.1 | 2.78 | 43.7 | 2.86 | 44.9 | 0/16
-table9/row9 Qwen-Time | 2.10 | 40.5 | 3.08 | 50.3 | 3.14 | 55.9 | 3.75 | 61.6 | 0/16
-table9/row10 iTransformer | 2.19 | 67.7 | 2.25 | 68.6 | 2.11 | 69.9 | 1.92 | 71.1 | 0/16
-table9/row11 LSTM | 3.04 | 64.6 | 3.33 | 65.6 | 3.83 | 67.5 | 3.94 | 68.7 | 0/16
-table9/row12 KNN | 3.12 | 65.8 | 2.75 | 67.7 | 2.75 | 68.7 | 2.42 | 69.4 | 0/16
-table9/row13 DeepSeek-R1-32B | 3.14 | 77.3 | 3.19 | 77.7 | 3.86 | 78.1 | 5.36 | 77.7 | 0/16
-table9/row14 DeepSeek-R1-Qwen-14B | 3.54 | 75.4 | 4.08 | 76.3 | 4.50 | 76.6 | 4.47 | 77.2 | 0/16
-table9/row15 DeepSeek-R1-Qwen-7B | 3.69 | 76.0 | 4.44 | 76.7 | 4.47 | 76.2 | 5.22 | 76.6 | 0/16
-table9/row16 CALF | 3.75 | 80.0 | 3.42 | 80.5 | 3.92 | 80.6 | 4.42 | 80.8 | 0/16
-table9/row17 Hunyuan-4B | 3.88 | 79.4 | 3.08 | 79.3 | 2.22 | 78.7 | 2.83 | 78.0 | 0/16
-table9/row18 SVR | 3.92 | 77.3 | 3.50 | 79.9 | 3.33 | 80.4 | 2.75 | 80.6 | 0/16
-table9/row19 ContextPilot-14B | 4.11 | 76.8 | 4.75 | 77.8 | 5.44 | 78.1 | 5.56 | 78.4 | 0/16
-table9/row20 Hunyuan-1.8B | 4.26 | 69.7 | 4.81 | 70.7 | 4.19 | 71.9 | 4.36 | 73.4 | 0/16
-table9/row21 Qwen2.5-1.5B | 4.31 | 74.6 | 5.08 | 74.8 | 5.56 | 74.7 | 6.39 | 74.6 | 0/16
-table9/row22 Decision Tree | 4.54 | 55.1 | 5.06 | 53.8 | 5.64 | 50.2 | 4.75 | 56.7 | 0/16
-table9/row23 DeepSeek-R1-Llama-8B | 4.67 | 76.1 | 4.36 | 77.0 | 4.25 | 77.5 | 3.94 | 77.9 | 0/16
-table9/row24 ContextPilot-8B | 4.90 | 78.3 | 4.22 | 78.9 | 5.28 | 79.1 | 5.44 | 79.3 | 0/16
-table9/row25 Hunyuan-7B | 5.12 | 73.9 | 5.81 | 75.7 | 6.03 | 75.9 | 4.28 | 76.1 | 0/16
-table9/row26 Gradient Boosting | 5.33 | 52.0 | 4.67 | 58.7 | 4.75 | 62.8 | 5.08 | 65.4 | 0/16
-table9/row27 Random Forest | 5.35 | 65.9 | 5.19 | 66.5 | 5.58 | 67.0 | 5.64 | 67.6 | 0/16
-table9/row28 DeepSeek-R1-Qwen-1.5B | 5.83 | 77.4 | 5.44 | 78.0 | 5.78 | 78.3 | 6.11 | 78.5 | 0/16
-table9/row29 CNN | 6.28 | 81.1 | 6.78 | 81.9 | 6.22 | 82.2 | 7.14 | 82.6 | 0/16
-table10/row1 Model | L | step 0 (1 wk) | step 1 (2 wk) | step 2 (3 wk) | step 3 (4 wk)
-table10/row2 NLinear | L=24 | PASS (0.11 wk, 3.9 %) | fail (1.33 wk, 8.4 %) | fail (2.33 wk, 11.9 %) | fail (2.67 wk, 18.7 %)
-table10/row3 NLinear | L=36 | PASS (0.33 wk, 4.2 %) | fail (1.33 wk, 7.2 %) | fail (2.11 wk, 15.3 %) | fail (2.67 wk, 18.1 %)
-table10/row4 NLinear | L=48 | PASS (0.22 wk, 2.4 %) | fail (1.22 wk, 4.7 %) | fail (2.22 wk, 10.0 %) | fail (2.78 wk, 16.7 %)
-table10/row5 NLinear | L=60 | PASS (0.17 wk, 2.5 %) | fail (1.44 wk, 4.5 %) | fail (2.56 wk, 10.0 %) | fail (3.33 wk, 13.0 %)
-table10/row6 MIFlu | L=24 | PASS (0.00 wk, 18.3 %) | fail (0.89 wk, 26.7 %) | fail (1.22 wk, 30.5 %) | fail (1.33 wk, 31.6 %)
-table10/row7 MIFlu | L=36 | PASS (0.00 wk, 18.7 %) | fail (0.78 wk, 26.3 %) | fail (1.67 wk, 31.5 %) | fail (1.33 wk, 32.4 %)
-table10/row8 MIFlu | L=48 | fail (1.22 wk, 18.0 %) | PASS (0.67 wk, 24.8 %) | fail (1.22 wk, 30.1 %) | fail (1.33 wk, 33.2 %)
-table10/row9 MIFlu | L=60 | PASS (0.17 wk, 20.5 %) | fail (1.33 wk, 25.8 %) | fail (2.22 wk, 29.8 %) | fail (2.67 wk, 31.2 %)
-table10/row10 PatchTST | L=24 | fail (0.67 wk, 30.6 %) | fail (1.00 wk, 34.0 %) | fail (1.22 wk, 33.6 %) | fail (1.22 wk, 30.7 %)
-table10/row11 PatchTST | L=36 | fail (1.00 wk, 26.2 %) | fail (1.67 wk, 32.2 %) | fail (1.33 wk, 31.2 %) | fail (1.33 wk, 33.9 %)
-table10/row12 PatchTST | L=48 | fail (0.56 wk, 30.4 %) | fail (1.33 wk, 30.9 %) | fail (0.89 wk, 35.2 %) | fail (0.89 wk, 35.0 %)
-table10/row13 PatchTST | L=60 | fail (0.50 wk, 35.0 %) | fail (1.67 wk, 34.3 %) | fail (2.22 wk, 35.7 %) | fail (2.33 wk, 35.1 %)
-table11/row1 Quantity | Value
-table11/row2 Fitted slope of MSE against log₁₀(parameters) | +0.1171
-table11/row3 Coefficient of determination R² | 0.0223
-table11/row4 Models in the fit (parametric arms only) | 11
-table11/row5 Pareto set (non-dominated) | NLinear (2,520 parameters) · PatchTST (531,878 parameters)
-table11/row6 Parameter ratio PatchTST / NLinear | 211.1×
-table11/row7 MSE gain of PatchTST over NLinear | 11.2 %
-table11/row8 PatchTST improvement over seasonal naive | 73.17 %
-table11/row9 Spread of MSE across the 28 arms | 1.5574 (best) … 5.6155 (worst), i.e. 3.6×
-table11/row10 Spearman ρ, MSE against mean PIE (28 arms) | +0.736 (p < 1e-4)
-table11/row11 Spearman ρ, MSE against K&S passes (28 arms) | -0.429 (p = 0.023)
-table12/row1 Model A | Model B | n | mean Δ MSE | A wins | p (Holm) | effect d
-table12/row2 NLinear | PatchTST | 12 | +0.2095 | 2/12 | 0.1172 | 1.15
-table12/row3 Gradient Boosting | RNN | 12 | -1.4029 | 12/12 | 0.06637 | 4.86
-table12/row4 CALF | RNN | 12 | +0.5111 | 0/12 | 0.06637 | 1.65
-table12/row5 CALF | SVR | 12 | +0.2397 | 0/12 | 0.06637 | 1.82
-table12/row6 CALF | TimeCMA | 12 | +2.9704 | 0/12 | 0.06637 | 14.78
-table12/row7 CNN | Decision Tree | 12 | +1.2957 | 0/12 | 0.06637 | 2.69
-table12/row8 CNN | DNN | 12 | +3.4740 | 0/12 | 0.06637 | 6.43
-table13/row1 # | Encoder | Family | Size | Cells | Read-out
-table13/row2 1 | Qwen2.5-1.5B | Qwen2.5 (dense) | 1.5 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table13/row3 2 | DeepSeek-R1-Distill-Qwen-1.5B | DeepSeek-R1 distill (Qwen2) | 1.5 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table13/row4 3 | DeepSeek-R1-Distill-Qwen-7B | DeepSeek-R1 distill (Qwen2) | 7 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table13/row5 4 | DeepSeek-R1-Distill-Llama-8B | DeepSeek-R1 distill (Llama) | 8 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table13/row6 5 | DeepSeek-R1-Distill-Qwen-14B | DeepSeek-R1 distill (Qwen2) | 14 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table13/row7 6 | DeepSeek-R1-Distill-Qwen-32B | DeepSeek-R1 distill (Qwen2) | 32 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table13/row8 7 | Tencent ContextPilot-8B | Tencent ContextPilot | 8 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table13/row9 8 | Tencent ContextPilot-14B | Tencent ContextPilot | 14 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table13/row10 9 | Tencent Hunyuan-1.8B | Tencent Hunyuan | 1.8 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table13/row11 10 | Tencent Hunyuan-4B | Tencent Hunyuan | 4 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table13/row12 11 | Tencent Hunyuan-7B | Tencent Hunyuan | 7 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table13/row13 — | 11 arms | — | — | 132 / 156 | 24 cells skipped
-table14/row1 Status | Arm | Reason
-table14/row2 skipped (24 cells) | Tencent WeMM-Embedding-2B | embedding-only: cannot emit per-layer hidden states
-table14/row3 skipped (24 cells) | Tencent WeMM-Embedding-4B | embedding-only: cannot emit per-layer hidden states
-table14/row4 excluded | Tencent Penguin-Encoder | requires trust_remote_code; not loadable in the pinned stack
-table14/row5 excluded | Tencent Youtu-HiChunk | no per-layer hidden states exposed
-table14/row6 excluded | Tencent KaLM-Embedding-Gemma3-12B | weight download failed
-table14/row7 excluded | Qwen3.8-27B-FP8 | FP8 dequantises to ~54.7 GB bf16; not downloaded
-table14/row8 excluded | Llama-70B | does not fit an 80 GB A100
-table15/row1 Variant | Flag | Cells | Question | Status
-table15/row2 full (K=6) | default | — | Reference arm: the MIFlu benchmark instance itself (already in the benchmark table). | in the benchmark table
-table15/row3 no_lora | --no-lora | 12 | Is the accuracy carried by the LoRA adaptation, or by the frozen backbone? | not aggregated
-table15/row4 K=2 | --num-layers 2 | 12 | Depth ladder: does a 2-layer stack lose accuracy? | not aggregated
-table15/row5 K=4 | --num-layers 4 | 12 | Depth ladder: the paper's regional depth. | not aggregated
-table15/row6 K=8 | --num-layers 8 | 12 | Depth ladder: does extra depth help? | not aggregated
-table15/row7 K=12 | --num-layers 12 | 12 | Depth ladder: is there a capacity ceiling? | not aggregated
-table16/row1 # | Defect | Consequence if unfixed | State
-table16/row2 A1 | Seed never reached the LLM training path; the adapter reset the RNG | 36 LLM cells bit-identical across seeds; every ±sd exactly 0 | Fixed 2026-11-02 03:57:47
-table16/row3 A2 | Best-val snapshot cloned the frozen encoder instead of the trainable head | 7B arm OOM; the 32B arm could never complete on any 80 GB A100 | Fixed
-table16/row4 A3 | revision: null in the arm registry (no queue/p2/ directory) | every unblocked LLM cell terminated as skip.no-revision | Fixed
-table16/row5 A4 | Two different HuggingFace cache layouts | 10 of 13 arms invisible to from_pretrained, after the GPU was allocated | Fixed
-table16/row6 A5 | flock is not a cross-node mutex on GPFS | two lanes lost each other's DONE markers; replaced by a mkdir lock | Patched, unverified
-table16/row7 A6 | Attempt cap not enforced in the controller | rows reached attempts=26 against a stated maximum of 2 | Open
-table16/row8 A7 | Two pipelines could not have executed at all (dispatch branch missing) | Table VI / walk-forward rows would never have started | Fixed
-table16/row9 A8 | persistent_driver.sh died exactly when it had work (set -u expansion) | the queue stopped advancing with runnable rows left | Fixed
-table17/row1 Artefact | Contents | Used in
-table17/row2 02_数字表格/BENCH_MSE_BY_MODEL_L.csv | per model × horizon MSE/MAE (7-var, ILITOTAL, physical) | benchmark table
-table17/row3 02_数字表格/BENCH_EFFICIENCY.csv | parameters, Pareto flag, slope, R² | efficiency table, Pareto figure
-table17/row4 02_数字表格/BENCH_PTE_PIE_BY_STEP.csv | per model × horizon × step PTE/PIE/pass | peak-skill tables, heat map
-table17/row5 02_数字表格/BENCH_SEASONAL_NAIVE.csv | seasonal-naive reference | benchmark-table note
-table17/row6 02_数字表格/BENCH_PAIRED_TESTS.csv | paired sign-flip tests, Holm-corrected | paired-test table
-table17/row7 02_数字表格/BENCH_GPU_PROVENANCE.csv | 204 cells: GPU, partition, node, job id | hardware table
-table17/row8 02_数字表格/ESSAY_VS_REPRODUCTION_TABLE_V.csv | the paper's Table V values against an earlier ours | reproduction table
-table17/row9 04_详细说明文档/LEDGER.md (2026-11-01 rows) | the 40-run per-seed oracle | oracle table
-table17/row10 03_预测数据_证据/expanded_runs/**/pred_*.npz | raw per-window predictions — every number re-derivable | all tables
-table17/row11 05_程序代码/verify_bench_unchanged.py, 05_程序代码/verify_miflu_oracle.py | re-derivation gates | trust boundary
+table2/row2 Rows and channels | 966 × 7
+table2/row3 Chronological split | 676 / 97 / 193
+table2/row4 Train / validation / test indices | 0–675 / 676–772 / 773–965
+table2/row5 History and horizons | T=104; L=24/36/48/60
+table2/row6 Available / scored windows | 170/160; 158/144; 146/144; 134/128
+table2/row7 ILITOTAL train mean / SD | 9,439.84 / 9,003.15
+table2/row8 Local numeric identity | max |difference| = 0
+table3/row1 Item | Reproduction | Benchmark
+table3/row2 Seeds | 2021–2030 (10) | 42/43/44 (3)
+table3/row3 Models | MIFlu | 13 conventional + 4 LLM-based + 11 frozen encoders
+table3/row4 Selection | Validation checkpoint | Validation checkpoint
+table3/row5 Scores | 7-variable z-space MSE / MAE | 7-variable MSE / MAE; ILITOTAL PTE / PIE
+table3/row6 Windows | 160 / 144 / 144 / 128 | 160 / 144 / 144 / 128
+table4/row1 Horizon | Our MSE ± SD | Paper MSE | Δ MSE | Our MAE | Paper MAE | Δ MAE
+table4/row2 L=24 | 1.3045 ± 0.0883 | 1.5420 | -15.4% | 0.7482 | 0.7260 | +3.1%
+table4/row3 L=36 | 1.3561 ± 0.1603 | 1.4220 | -4.6% | 0.7712 | 0.7790 | -1.0%
+table4/row4 L=48 | 1.6543 ± 0.1064 | 1.4140 | +17.0% | 0.8381 | 0.7570 | +10.7%
+table4/row5 L=60 | 1.6829 ± 0.2109 | 1.3640 | +23.4% | 0.8596 | 0.7190 | +19.6%
+table4/row6 4-horizon mean | 1.4995 | 1.4355 | +4.5% | 0.8043 | 0.7452 | +7.9%
+table5/row1 Seed | L24 | L36 | L48 | L60
+table5/row2 2021 | 1.240157 | 1.314358 | 1.482299 | 1.599641
+table5/row3 2022 | 1.201078 | 1.306645 | 1.711215 | 1.664878
+table5/row4 2023 | 1.284212 | 1.269466 | 1.663857 | 1.821282
+table5/row5 2024 | 1.259462 | 1.154099 | 1.879495 | 1.915250
+table5/row6 2025 | 1.464643 | 1.767328 | 1.723161 | 1.410785
+table5/row7 2026 | 1.368497 | 1.312511 | 1.620327 | 1.984315
+table5/row8 2027 | 1.392309 | 1.400796 | 1.628296 | 1.614602
+table5/row9 2028 | 1.230425 | 1.302717 | 1.588157 | 1.401814
+table5/row10 2029 | 1.231536 | 1.404061 | 1.570881 | 1.520661
+table5/row11 2030 | 1.373057 | 1.328807 | 1.675020 | 1.895393
+table6/row1 # | Model | L24 | L36 | L48 | L60 | Mean MSE | Mean MAE
+table6/row2 1 | MIFlu | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199
+table6/row3 2 | PatchTST | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786
+table6/row4 3 | NLinear | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183
+table6/row5 4 | DNN | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057
+table6/row6 5 | TimeCMA | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676
+table6/row7 6 | Gradient Boosting | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521
+table6/row8 7 | KNN | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293
+table6/row9 8 | Random Forest | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779
+table6/row10 9 | iTransformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476
+table6/row11 10 | Decision Tree | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798
+table6/row12 11 | Hunyuan-1.8B | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755
+table6/row13 12 | Hunyuan-7B | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685
+table6/row14 13 | DeepSeek-R1-Qwen-1.5B | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002
+table6/row15 14 | DeepSeek-R1-Llama-8B | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786
+table6/row16 15 | GRU | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174
+table6/row17 16 | DeepSeek-R1-32B | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935
+table6/row18 17 | LSTM | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303
+table6/row19 18 | DeepSeek-R1-Qwen-14B | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019
+table6/row20 19 | DeepSeek-R1-Qwen-7B | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133
+table6/row21 20 | RNN | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634
+table6/row22 21 | ContextPilot-8B | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255
+table6/row23 22 | Hunyuan-4B | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450
+table6/row24 23 | ContextPilot-14B | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407
+table6/row25 24 | Qwen2.5-1.5B | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725
+table6/row26 25 | Qwen-Time | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794
+table6/row27 26 | SVR | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986
+table6/row28 27 | CALF | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190
+table6/row29 28 | CNN | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720
+table7/row1 Model | PTE (wk) | PIE (%) | Joint passes | s0 PTE | s0 PIE (%)
+table7/row2 MIFlu | 1.128 | 26.846 | 4/16 | 0.347 | 18.884
+table7/row3 PatchTST | 1.240 | 32.755 | 0/16 | 0.681 | 30.553
+table7/row4 NLinear | 1.677 | 9.477 | 4/16 | 0.208 | 3.250
+table8/row1 Model | L | s0 | s1 | s2 | s3
+table8/row2 NLinear | 24 | PASS 0.111 / 3.949 | fail 1.333 / 8.411 | fail 2.333 / 11.943 | fail 2.667 / 18.739
+table8/row3 NLinear | 36 | PASS 0.333 / 4.181 | fail 1.333 / 7.222 | fail 2.111 / 15.313 | fail 2.667 / 18.145
+table8/row4 NLinear | 48 | PASS 0.222 / 2.419 | fail 1.222 / 4.727 | fail 2.222 / 9.979 | fail 2.778 / 16.655
+table8/row5 NLinear | 60 | PASS 0.167 / 2.450 | fail 1.444 / 4.542 | fail 2.556 / 9.952 | fail 3.333 / 13.000
+table8/row6 MIFlu | 24 | PASS 0.000 / 18.307 | fail 0.889 / 26.686 | fail 1.222 / 30.472 | fail 1.333 / 31.638
+table8/row7 MIFlu | 36 | PASS 0.000 / 18.695 | fail 0.778 / 26.333 | fail 1.667 / 31.514 | fail 1.333 / 32.427
+table8/row8 MIFlu | 48 | fail 1.222 / 18.004 | PASS 0.667 / 24.795 | fail 1.222 / 30.133 | fail 1.333 / 33.236
+table8/row9 MIFlu | 60 | PASS 0.167 / 20.530 | fail 1.333 / 25.799 | fail 2.222 / 29.790 | fail 2.667 / 31.177
+table8/row10 PatchTST | 24 | fail 0.667 / 30.580 | fail 1.000 / 34.044 | fail 1.222 / 33.572 | fail 1.222 / 30.722
+table8/row11 PatchTST | 36 | fail 1.000 / 26.235 | fail 1.667 / 32.247 | fail 1.333 / 31.245 | fail 1.333 / 33.854
+table8/row12 PatchTST | 48 | fail 0.556 / 30.360 | fail 1.333 / 30.878 | fail 0.889 / 35.158 | fail 0.889 / 35.002
+table8/row13 PatchTST | 60 | fail 0.500 / 35.035 | fail 1.667 / 34.342 | fail 2.222 / 35.674 | fail 2.333 / 35.133
+table9/row1 Quantity | Value
+table9/row2 Regression slope / R² | +0.1171 / 0.0223
+table9/row3 Models with parameter exports | 11
+table9/row4 Subset Pareto set | NLinear 2,520; PatchTST 531,878
+table9/row5 Parameter ratio | 211.1×
+table9/row6 Descriptive MSE reduction | 11.2%
+table9/row7 ρ(MSE, PIE) | +0.736 (p < 0.0001)
+table9/row8 ρ(MSE, passes) | -0.429 (p = 0.023)
+table10/row1 Model A | Model B | Δ MSE | p raw | p Holm | Effect*
+table10/row2 NLinear | PatchTST | +0.2095 | 0.005859 | 0.1172 | 1.15
+table10/row3 Gradient Boosting | RNN | -1.4029 | 0.000488 | 0.0664 | 4.86
+table10/row4 KNN | NLinear | +1.9138 | 0.000488 | 0.0664 | 22.29
+table10/row5 KNN | MIFlu | +2.2280 | 0.000488 | 0.0664 | 9.89
+table10/row6 KNN | LSTM | -1.2234 | 0.000488 | 0.0664 | 5.28
+table10/row7 iTransformer | TimeCMA | +1.3863 | 0.000488 | 0.0664 | 7.02
+table10/row8 iTransformer | SVR | -1.3443 | 0.000488 | 0.0664 | 10.61
+table11/row1 Encoder | MSE | vs MIFlu | PTE | PIE (%) | Passes
+table11/row2 Hunyuan-1.8B | 4.7374 | 3.04× | 4.406 | 71.428 | 0/16
+table11/row3 Hunyuan-7B | 4.7596 | 3.06× | 5.309 | 75.399 | 0/16
+table11/row4 DeepSeek-R1-Qwen-1.5B | 4.7866 | 3.07× | 5.792 | 78.061 | 0/16
+table11/row5 DeepSeek-R1-Llama-8B | 4.8250 | 3.10× | 4.306 | 77.121 | 0/16
+table11/row6 DeepSeek-R1-32B | 4.9372 | 3.17× | 3.889 | 77.730 | 0/16
+table11/row7 DeepSeek-R1-Qwen-14B | 5.0166 | 3.22× | 4.149 | 76.350 | 0/16
+table11/row8 DeepSeek-R1-Qwen-7B | 5.0308 | 3.23× | 4.458 | 76.373 | 0/16
+table11/row9 ContextPilot-8B | 5.0843 | 3.26× | 4.962 | 78.918 | 0/16
+table11/row10 Hunyuan-4B | 5.1317 | 3.30× | 3.003 | 78.840 | 0/16
+table11/row11 ContextPilot-14B | 5.1949 | 3.34× | 4.965 | 77.764 | 0/16
+table11/row12 Qwen2.5-1.5B | 5.2049 | 3.34× | 5.333 | 74.650 | 0/16
+table12/row1 Variant | Flag | Cells | Status
+table12/row2 Reference K=6 | default | 12 | Already in benchmark
+table12/row3 no_lora | --no-lora | 12 | Not aggregated
+table12/row4 K=2 | --num-layers 2 | 12 | Not aggregated
+table12/row5 K=4 | --num-layers 4 | 12 | Not aggregated
+table12/row6 K=8 | --num-layers 8 | 12 | Not aggregated
+table12/row7 K=12 | --num-layers 12 | 12 | Not aggregated
--- report_internal_zh corrected upload
+++ report_internal_zh reviewed revision 4
@@ -1,320 +1,369 @@
-p0 毕业设计 · 香港城市大学 · 电子工程学系
-p1 复现 MIFlu 并基准评估流感预测
-p2 内部技术报告——无泄漏复现、28 模型基准、峰值技巧判据与 11 个冻结 LLM 编码器
-p4 目录
-p5 1. 数据
-p6 2. 方法
-p7 3. MIFlu 表 V 的复现
-p8 4. 基准一：精度（28 个模型）
-p9 5. 基准二：Kramer & Shaman 判据下的峰值技巧
-p10 6. 基准三：精度—效率前沿
-p11 7. 基准四：统计显著性
-p12 8. 作为特征提取器的冻结 LLM 编码器
-p13 9. 消融阶梯：设计与当前状态
-p14 10. 证据支持什么、不支持什么
-p15 11. 可复现性
-p16 12. 参考文献
-p18 1. 数据
-p19 数据是随 MIFlu 发布的美国 CDC 全国流感监测序列：966 个每周行 x 7 个数值通道，与作者文件逐字节相同（最大绝对差 0.000e+00）。切分为按时间 70/10/20——第 0-675 行训练、676-772 行验证、773-965 行测试（共 193 行）——每个窗口都通过严格包含约束检查，使输入区间总在目标区间开始之前结束（被接纳的测试目标起始行最小下标为 773）。标准化只使用在训练段上拟合的 StandardScaler。
-p20 为什么用 676/97/193（70/10/20）？ 这是长跨度预测基准家族的标准协议（Informer, AAAI 2023；DLinear, AAAI 2023；PatchTST, ICLR 2023；iTransformer, ICLR 2024），也是原 MIFlu 仓库使用的切分。整数算术为 966 x 0.7 = 676、966 x 0.2 = 193、余 97。我们完全遵循，以保证数字可比。
-p21 为什么用 (W//16)*16 评测窗口？ 这不是期刊要求，而是原代码 DataLoader(batch_size=16, drop_last=True) 的副作用：它会丢弃最后不完整的一批测试窗口，170 -> 160、158 -> 144、146 -> 144、134 -> 128。被丢弃的窗口实测更难（约为保留窗口均值的 1.41 倍），因此若 MIFlu 按裁剪后的集合计分、其他模型按全集计分，就等于给 MIFlu 一个更容易的测试集。所以 28 个模型统一在同一批裁剪窗口上计分。
-p22 表 1. 数据集、划分与评测窗口。
-p23 这些标准化常数正是 7 变量聚合无法反归一化的原因：OT 与 ILITOTAL 的量级相差四个数量级，所以聚合值是一个损失值，而不是一条序列。
-p24 2. 方法
-p25 本文使用两套协议，且从不混用。(1) 复现： 10 次重复、种子 2021-2030、验证集选择检查点、7 变量聚合 MSE——这是与论文表 V 比较所需的协议。(2) 基准： 3 个种子（42/43/44）、共享窗口 (W//16)*16 = 160/144/144/128——这是 28 个模型互比所用的协议。MIFlu 是唯一同时出现在两套协议下的模型，它的两个数值彼此不可比较。
-p26 表 2. 两套评测协议。二者从不混用，其数值也从不互相比较。
-p27 MIFlu 是唯一同时出现在两套协议下的模型；它的两个数值回答不同问题，彼此不可比较（见复现一节）。
-p28 为什么基准用 3 个种子而复现用 10 个？ 复现遵循论文协议（10 次重复），以便进行同条件比较。基准遵循预测文献的惯例：PatchTST（ICLR 2023, arXiv:2211.14730）与 iTransformer（ICLR 2024）均报告三种子均值。28 个模型用 3 个种子使矩阵为 28 x 4 x 3 = 336 个单元，在单个 A100 分区上可完成；若用 10 个种子则为 1,120 个单元，而对本文所做的比较没有额外收益。
-p29 表 3. 复现：本文 vs 原论文/仓库。
-p30 两项 [偏离] 为顶刊标准要求。
-p31 两处 [DEVIATION] 是什么，为什么必要？ (1) 检查点选择： 原代码在测试集上选最优 epoch（main_ILI_lora.py 第 211、225 行）。这是数据泄漏——测试集是期末考试，选模型时不能看它。我们改为在验证段上选择。(2) 7 变量指标： 原测试加载器只覆盖 7 个变量中的 1 个（bug），而表 V 定义在 7 变量聚合上。我们修复了加载器。两处偏离凡出现在复现数字处均予披露。
-p32 表 4. 基准协议：本文 vs 原论文仓库（原仓库用 fix_seed=2021，单种子）。
-p33 原论文无基准——这是我们的贡献。
-p34 为什么 PTE/PIE 用 ILITOTAL 而 MSE 用 7 变量聚合？ 聚合值是一个损失，不是时间序列：七个通道的训练均值从 1.74（% WEIGHTED ILI）到 493,629（OT），把它们平均得到的是一个没有物理单位、也无法反归一化的数。峰值时间与峰值高度则是对单一可解释序列（患者人数）的陈述。因此 PTE/PIE 使用经训练集 scaler 反归一化的 ILITOTAL（均值 9,439.84，标准差 9,003.15 人）。复现保留聚合指标，是因为表 V 如此定义。
-p35 3. MIFlu 表 V 的复现
-p36 四跨度均值为 1.4995，对比论文的 1.4355，即差 4.5 %，但均值是这个结果里信息量最小的部分。符号随跨度翻转：L=24 时本文比论文好 15.4 %（1.3045 对 1.542），L=36 时好 4.6 %（1.3561 对 1.422）；而 L=48 时差 17.0 %（1.6543 对 1.414），L=60 时差 23.4 %（1.6829 对 1.364）。MAE 一侧同样交叉：0.7482 / 0.7712 / 0.8381 / 0.8596 对 0.726 / 0.779 / 0.757 / 0.719，四跨度均值为 0.8043 对 0.7452（+7.9 %）。
-p37 表 5. MIFlu 表 V 的复现——符号反转。7 变量 z 空间聚合 MSE，10 次重复，种子 2021–2030。
-p38 Δ 为正表示本文比论文更差。本文在 L24（−15.4 %）与 L36（−4.6 %）更好，在 L48（+17.0 %）与 L60（+23.4 %）更差；4 个跨度的均值在 MSE 上为 +4.5 %、在 MAE 上为 +7.9 %。唯一可辩护的表述是“在 4 个跨度的 MSE 均值上复现到 4.5 % 以内，且符号随跨度翻转”，绝不能说“我们超过了论文”。窗口为 (W//16)*16 = 160/144/144/128；A100-SXM4-80GB、stingy 分区、CityU HPC Burgundy。来源：ESSAY_VS_REPRODUCTION_TABLE_V.csv。
-p39 有两种解释与该模式相符，而现有数据尚无法区分。其一是检查点选择：本文用验证集选出的检查点与作者用测试集选出的不是同一类对象，而测试集选出的检查点具有随跨度增长的优势，因为更长跨度有更多方差可利用。其二就是方差：十次重复在 L=24 的范围是 1.201-1.465，在 L=60 是 1.401-1.984，因此在如此离散度下，L=48 的 17 % 与 L=60 的 23 % 差距虽大却并不荒谬——产出 L=60 的 1.6829 的那次运行，在另一个种子上也产出过 1.4108。
-p40 唯一可辩护的表述是：在四跨度 MSE 均值上复现到 4.5 % 以内，且符号随跨度翻转。这不是“我们优于原论文”，也不是“论文错了”。
-p41 本报告给出逐种子 oracle，因为复现论断的强度不会超过其来源的强度。此后每一次 MIFlu 单元（包括基准实例）的重新导出，都由 05_程序代码/verify_miflu_oracle.py 以 |Δ| <= 1e-5 对照该表把关；不匹配的单元被拒绝，而不是被平均进去。
-p42 表 6. 复现的逐种子 oracle：40 次运行各自的 7 变量 MSE。
-p43 此后每一次重新导出都以本表为门限（|Δ| ≤ 1e-5）；复现表的每个数字都以本表为来源。05_程序代码/verify_miflu_oracle.py 会重算这些均值并断言其等于 1.3045 / 1.3561 / 1.6543 / 1.6829。
-p45 MIFLU，L=24。 y 为用训练集拟合的 StandardScaler 反归一化后的 ILITOTAL 患者人数（均值 9,439.84，标准差 9,003.15 人）；x 为测试集周次。黑线为真值，其余每步 0/1/2/3（即提前 1/2/3/4 周）一条预测线。图中指标为 ILITOTAL 患者人数（峰值技巧所用序列），不是无法反归一化的 7 变量聚合。评测窗口：L=24 时取前 (W//16)*16 = 160 个测试窗口（共 170 个），与 MIFlu 的 drop_last=True 规则一致。硬件：CityU HPC（复现运行；单次 GPU 记录见运行日志，未包含在该导出中）。
-p47 MIFLU，L=60。 y 为用训练集拟合的 StandardScaler 反归一化后的 ILITOTAL 患者人数（均值 9,439.84，标准差 9,003.15 人）；x 为测试集周次。黑线为真值，其余每步 0/1/2/3（即提前 1/2/3/4 周）一条预测线。图中指标为 ILITOTAL 患者人数（峰值技巧所用序列），不是无法反归一化的 7 变量聚合。评测窗口：L=60 时取前 (W//16)*16 = 128 个测试窗口（共 134 个），与 MIFlu 的 drop_last=True 规则一致。硬件：CityU HPC（复现运行；单次 GPU 记录见运行日志，未包含在该导出中）。
-p48 曲线展示了 MSE 差距由什么构成。L=24 时步 0 曲线在每一次起伏中都紧跟真值，随步退化可见但有秩序。L=60 时模型仍抓住季节形状——它不是坏掉的模型——但系统性地低估三个峰，且在最尖锐的峰（2017-18 季节）处低估最多。这就是长跨度下正 MSE 差距的视觉形态：模型学会了季节性，却丢掉了幅度。
-p49 4. 基准一：精度（28 个模型）
-p50 基准包含 6 个家族的 28 个模型：(1) 线性（NLinear）——最简基线；(2) Transformer（PatchTST、iTransformer）——当前长跨度预测的最先进方法；(3) 神经网络（DNN、CNN、RNN、LSTM、GRU）；(4) 经典机器学习（梯度提升、随机森林、决策树、SVR、KNN）；(5) 基于 LLM 的预测器（MIFlu、TimeCMA、Qwen-Time、CALF）——论文方法及其已发表的竞争者；(6) 冻结 LLM 编码器（11 个：Qwen2.5、五个尺寸的 DeepSeek-R1-Distill、腾讯 Hunyuan 与 ContextPilot）——检验预训练语言表征能否迁移到流行病学序列。矩阵为 28 x 4 个跨度 x 3 个种子 = 336 个单元，其中 204 个（17 个传统模型，含 DLinear）带实测 A100 来源，132 个为编码器单元。
-p51 表 7. 28 个模型的基准：逐跨度与四跨度均值的 7 变量 z 空间聚合 MSE，以及四跨度 MAE。种子 42/43/44 取均值，共享窗口 (W//16)*16 = 160/144/144/128。
-p52 越低越好。为版面清晰省略逐跨度 MAE，其值在 02_数字表格/BENCH_MSE_BY_MODEL_L.csv 中。DLinear 按项目决定被排除（原论文表 V 已给出它的结果，因此不构成新的基线）。季节朴素基线（52 周滞后）在同一批窗口上的 4 跨度均值为 6.2132，28 个模型全部优于它。硬件：A100-SXM4-80GB、stingy 分区、CityU HPC Burgundy——17 个传统模型中 204/204 个单元均带该实测来源，MIFlu 与编码器单元在同一分区运行并留有逐单元清单。参数量取自 BENCH_EFFICIENCY.csv 的训练后总数；经典学习器在此意义上无参数量、MIFlu 未导出，故留空。
-p53 这张表里有三点比排序本身更重要。第一，MIFlu 是精度冠军，1.5574，其后是 PatchTST（1.6621）与 NLinear（1.8716）：论文自己的模型在被放到与所有模型相同的协议上之后，确实胜出。第二，一个 2,520 参数的线性模型在 28 个模型中排第三，除 PatchTST 外领先所有 Transformer——这一结果应让读者怀疑“架构精巧才买到精度”这一假设，至少在这条 966 行的序列上不成立。第三，跨度很大：1.5574 到 5.6155 是 3.6 倍，因此模型选择的影响远大于被比较论文中报告的任何超参数调整。
-p54 发现 F0——仅凭精度无法确定一个可部署的模型。 前三名之间的 MSE 相差 20 %，其余 25 个模型又进一步跨越 3.0 倍。因此排名很容易产出、却很难据以行动：它说明哪个模型最拟合这个测试集，而不说明哪个模型支持预测本来要服务的那个决策。基准二至基准四正是要回答排名回答不了的问题。
-p56 PATCHTST，L=24。 y 为用训练集拟合的 StandardScaler 反归一化后的 ILITOTAL 患者人数（均值 9,439.84，标准差 9,003.15 人）；x 为测试集周次。黑线为真值，其余每步 0/1/2/3（即提前 1/2/3/4 周）一条预测线。图中指标为 ILITOTAL 患者人数（峰值技巧所用序列），不是无法反归一化的 7 变量聚合。评测窗口：L=24 时取前 (W//16)*16 = 160 个测试窗口（共 170 个），与 MIFlu 的 drop_last=True 规则一致。硬件：A100-SXM4-80GB，stingy 分区，CityU HPC Burgundy。
-p58 NLINEAR，L=24。 y 为用训练集拟合的 StandardScaler 反归一化后的 ILITOTAL 患者人数（均值 9,439.84，标准差 9,003.15 人）；x 为测试集周次。黑线为真值，其余每步 0/1/2/3（即提前 1/2/3/4 周）一条预测线。图中指标为 ILITOTAL 患者人数（峰值技巧所用序列），不是无法反归一化的 7 变量聚合。评测窗口：L=24 时取前 (W//16)*16 = 160 个测试窗口（共 170 个），与 MIFlu 的 drop_last=True 规则一致。硬件：A100-SXM4-80GB，stingy 分区，CityU HPC Burgundy。
-p59 5. 基准二：Kramer & Shaman 判据下的峰值技巧
-p60 峰值技巧把问题从“曲线有多接近”换成“预测能否支持决策”。在反归一化为患者人数的 ILITOTAL 上，我们按固定步 0/1/2/3（提前 1/2/3/4 周）计算峰值时间误差（PTE，周）与峰值强度误差（PIE，占观测峰值的百分比）。只有同一格内 PTE <= 1 周 且 PIE <= 25 % 才通过 Kramer & Shaman 判据。两半是合取关系，多数模型即使一半很好，也会在另一半上失败。
-p61 表 8. 逐固定步的峰值技巧：ILITOTAL 反归一化为患者人数后的 PTE（周）与 PIE（%），对四个跨度取均值；✓ 表示通过 Kramer & Shaman 判据（PTE ≤ 1 周且 PIE ≤ 25%）。
-p62 有两个模型通过，但通过的方式不同。NLinear 在步 0 的四个单元全部通过（16 个中 4 个）：全部 16 个单元的均值 PTE 1.677 周、均值 PIE 9.477 %，步 0 的 PIE 为 3.25 %——比判据宽松一个数量级。MIFlu 同样通过 4/16，但其中三个是步 0（L=48 在步 0 以 PTE 1.222 周失败），第四个是 L=48 的步 1；它的均值 PIE 为 26.846 %，即它的通过是贴着 25 % 边界，而不是落在判据内部。PatchTST 的时序最准（均值 PTE 1.240 周），但均值 PIE 为 32.755 %，通过数为 0：它在每个单元都未满足判据的校准一半。窗口 160/144/144/128；种子 42/43/44；A100-SXM4-80GB、stingy 分区、CityU HPC Burgundy。
-p63 表 9. 同一判据的逐格展开：三个具名模型的每个（跨度，步）组合。PASS 要求同一格内 PTE ≤ 1 周且 PIE ≤ 25 %。
-p64 每模型 16 格 = 4 个跨度 × 4 个步，每格为种子 42/43/44 的均值。NLinear 通过 4/16，全部在步 0（PIE 2.4–4.2 %）；MIFlu 通过 4/16——三个在步 0、一个在 L=48 步 1，PIE 为 18.3–24.8 %，即贴着边界；PatchTST 一个都不通过，因为其 PIE 在每个步都停在 26–35 % 区间。峰值检测：find_peaks(prominence = 0.15 × range, distance = 15) 与 ±8 周匹配——本研究的工程选择，不是已发表判据的一部分。1 周 / 25 % 阈值归因于 Kramer & Shaman (2019)，但仍标注 [to verify]，待与原文核对。
-p65 有两个模型通过，但通过的方式不同。NLinear 在步 0 的四个单元全部通过（4/16），全部 16 个单元的均值 PTE 为 1.68 周、均值 PIE 为 9.48 %；步 0 的均值 PIE 为 3.2 %，比判据宽松一个数量级。MIFlu 同样通过 4/16，但其中三个是步 0 单元、第四个是 L=48 的步 1：在 L=48 步 0 它的 PTE 为 1.22 周，而它通过的单元 PIE 为 18.3-24.8 %，即贴着边界而不是落在判据内部。PatchTST 一个都不通过：它的时序是本研究中最准的（均值 PTE 1.24 周），但 PIE 为 32.8 %，在每个单元都未满足校准一半。
-p67 全部 28 个基准模型的逐步峰值技巧。 颜色为四个预测跨度上 PTE（周，左）与 PIE（%，右）在固定步 0/1/2/3（提前 1/2/3/4 周）的均值；各行按四跨度 7 变量 MSE 均值排序（最好的在最上），因此精度排名可自上而下读出。蓝框标出四跨度均值同时满足 Kramer & Shaman 判据两半（PTE ≤ 1 周且 PIE ≤ 25 %）的（模型，步）组合：只有 NLinear 与 MIFlu 合格，且都只在步 0。逐格计数为：NLinear 4/16（全部在步 0）、MIFlu 4/16（三个步 0 加 L=48 步 1）、PatchTST 0/16。窗口为共享的 (W//16)*16 = 160/144/144/128；种子 42/43/44。由 plot_peak_skill.py 生成。硬件：A100-SXM4-80GB，stingy 分区，CityU HPC Burgundy。
-p68 机制在曲线中可见。以最小化平方误差训练的模型，因跟踪水平而受奖励，只在漏掉峰值时受到二次惩罚；平滑、略保守的预测是好的 MSE 策略、坏的峰值策略，因为峰值正是损失被少数几周主导的地方。NLinear 本质上是一个带逐窗口水平修正的线性映射，在峰值处反应更锐利：它更经常高估，这使 MSE 变差；也更经常落在接近峰值高度的位置，而这正是 PIE 度量的。这是与数据相符的假设，不是已被证明的机制。
-p69 发现 F1——部署排序不是精度排序。 在全部 28 个模型上，MSE 更好确实伴随校准更好（对均值 PIE 的 Spearman ρ = +0.74）：两个轴并非彼此独立，MSE 是有用的筛选。失效的是前沿内部的排序。在 MSE 最低的三个模型中，校准排序恰好相反——NLinear（MSE 第 3）的 PIE 最低，为 9.5 %；MIFlu（第 1）为 26.8 %；PatchTST（第 2）为 32.8 %——而且通过标记与 MSE 呈负秩相关（ρ = -0.43，p = 0.023）。MSE 第二名一个都不通过；第三名通过每个跨度的提前一周。这正是部署决策所依赖的发现，而按 MSE 排序的榜单无法表达它。
-p70 6. 基准三：精度—效率前沿
-p71 帕累托前沿回答的是与峰值判据不同的问题：不是“这个模型是否好到可以部署”，而是“每增加一些参数买到了多少精度”。若无其他模型同时具有更低误差和更少参数，则该模型是帕累托最优的。前沿恰好两个成员：NLinear（2,520 参数，MSE 1.8716）与 PatchTST（531,878 参数，MSE 1.6621）。在 11 个含参数模型上，把四跨度均值 MSE 对 log10(参数量) 做回归，斜率为 +0.1171，R² = 0.0223。
-p72 表 10. 精度—效率汇总，以及精度与峰值技巧之间的秩相关。
-p73 斜率为正意味着参数越多 MSE 反而越高（越差），R² = 0.0223 说明规模只能解释约 2% 的方差：在本数据集上参数量不是一个有用的选择准则。两条帕累托记录应读作权衡而不是排名——PatchTST 用 211 倍参数量换取 11.2% 的 MSE 下降。最后两行让峰值技巧的论断保持诚实：在全部 28 个模型上，MSE 更好确实伴随校准更好（ρ = +0.74），所以两个轴并非彼此独立；真正失效的是前沿内部的排序（见峰值技巧两表）与接受判定——后者与 MSE 呈负秩相关（ρ = -0.43）。窗口 160/144/144/128；种子 42/43/44。
-p74 这句话的两个符号都重要。斜率为正，即参数越多 MSE 反而越高（越差）；R² 只有 2 %，即规模几乎解释不了任何方差。于是两条帕累托记录应读作权衡而不是排名：PatchTST 用 211 倍于 NLinear 的参数量，换取 11.2 % 的 MSE 下降。这笔交易是否划算取决于部署场景——而且，鉴于发现 F1，还取决于部署是否需要峰值技巧；若需要，那 11.2 % 的精度优势换来的却是一个完全不能满足流行病学判据的模型。
-p76 精度—效率帕累托前沿。 x 为参数量（对数轴），y 为 4 个跨度的 7 变量 z 空间 MSE 均值；阶梯线为帕累托集合 {NLinear 2,520 参数；PatchTST 531,878 参数}。PatchTST 用 211 倍参数量换取 11.2% 的 MSE 下降；MSE 对 log₁₀(参数量) 的拟合斜率为 +0.1171，R² = 0.0223，即规模只能解释约 2% 的方差且符号为正。窗口为共享的 (W//16)*16 = 160/144/144/128；种子 42/43/44。由 plot_pareto.py 生成。硬件：A100-SXM4-80GB，stingy 分区，CityU HPC Burgundy。
-p78 三个具名模型的步 0 峰值技巧。 左：步 0 的峰值时间误差（周），对四个跨度取均值，虚线为 1 周阈值。右：步 0 的峰值强度误差（%），虚线为 25 % 阈值。绿色 = 在阈值内，红色 = 超出。MIFlu（0.35 周，18.9 %）与 NLinear（0.21 周，3.2 %）在均值层面同时位于两个阈值之内，而 PatchTST（0.68 周，30.6 %）未满足强度一半——这正是“平均误差好”与“峰值校准好”分离的视觉形态。种子 42/43/44；窗口 (W//16)*16 = 160/144/144/128。
-p79 发现 F2——参数量不是精度的代理。 斜率为正、R² = 0.0223：在本数据集上，规模对精度没有信息量，而仅有的那点信号还指向错误方向。前沿是两个模型之间的权衡，不是排名；而前沿中更便宜的那个，才是每个跨度都通过领域判据的模型。
-p80 7. 基准四：统计显著性
-p81 帕累托分析是描述性的：它说明权衡是什么，不需要推断。显著性分析是推断性的：它问的是那 11.2 % 的差异究竟能否与种子噪声区分开。两者都需要，因为只有当被交易的差异是真实的时候，讨论这笔交易才有意义。
-p82 在 12 个配对（跨度 x 种子）单元上，我们对全部 136 对模型做精确配对符号翻转检验，使用 Holm-Bonferroni 校正、bootstrap 95 % 置信区间（10,000 次重采样）与 Cohen's d。136 对中有 128 对在校正前显著；对 136 对做正确的 Holm 校正后无一存活，因为 n = 12 使最小可达校正 p 为 0.066。帕累托论证所需的那一对是 NLinear 对 PatchTST：平均 Δ MSE 为 +0.2095（对 PatchTST 有利），NLinear 只在 12 个单元中的 2 个更低，原始 p = 0.0059，p(Holm) = 0.117，d = 1.15。
-p83 表 11. 12 个配对（跨度 × 种子）单元上的配对符号翻转检验，对全部 136 对做 Holm 校正（由原始 p 值重算）。第一行（粗体）为正文讨论的帕累托对；其余为 p 值最小的六对，用作对照。
-p84 Δ 为正表示模型 A 的 MSE 更大。12 个单元全部配对（同跨度、同种子），这只有在所有模型统一使用 42/43/44 时才成立。导出的 p_holm 列由反向累积最小值生成，不是有效的 Holm 校正；本表的值由 p_raw 重算。n = 12 时最小可达原始 p 为 2/2¹² ≈ 0.00049，因此在 m = 136 对下最小可达校正 p 为 0.066，没有任何一对能在 0.05 水平存活（校正前有 128/136 对显著）。第一行为何不在第二块中：NLinear 对 PatchTST 的校正 p = 0.117，在 136 对中排第 117 小，因此按显著性排序的表会恰好省略帕累托论证所需的那一对。该差异在这个样本量下无法分辨；这是“未能拒绝”，不是“证明相等”（d = 1.15，且 PatchTST 在 12 个单元中有 10 个更低）。
-p85 为什么配对检验表看起来在讲别的模型：它按 p 排序，而 NLinear-PatchTST 这一对在 136 对中排第 117 小——“最强六项”式的表会恰好省略论证所需的那一个比较。因此本表把这一对放在第一行，把六个最显著的对放在下面，使两个事实同时可见：校正前榜单上的大多数模型彼此可分；校正后本研究无法分开任何一对——这是检验功效的陈述，不是关于模型的陈述——而前沿上的那一对正是论证所需。
-p86 发现 F3——211 倍参数成本在统计上与噪声不可区分。 p(Holm) = 0.117 意味着在 5 % 水平上无法拒绝两个均值相等。三点限定让它保持诚实：n = 12 时最小可达 p 为 2/2¹² ≈ 0.00049；不显著是“未能拒绝”，不是“证明相等”；效应量为 d = 1.15，且 PatchTST 在 12 个单元中的 10 个更低，因此方向一致，只是在这个样本量下差异无法分辨。正确的结论不是“两个模型相等”，而是“本基准未能为 211 倍成本确立精度优势”——结合发现 F1，这已足以让 NLinear 成为可辩护的默认选择。
-p87 8. 作为特征提取器的冻结 LLM 编码器
-p88 编码器这一轴问的是：预训练语言模型能否作为流行病学序列的有用特征提取器。每个模型是一个冻结编码器加一个共享线性头，按通道独立训练；不更新任何编码器权重，线性头是唯一可训练部分。这是该想法最宽容的版本：如果表征携带可用信息，线性读出就足以暴露它，失败也不能归咎于微调不稳定。156 个单元中完成 132 个（11 个模型 x 4 个跨度 x 3 个种子）；缺失的 24 个属于两个仅提供句向量、无法输出逐层隐藏状态的模型。
-p89 表 12. 11 个冻结 LLM 编码器模型（种子 42/43/44、四个跨度、每个模型 12 个单元）。
-p90 每个模型都是一个冻结编码器加一个共享线性头，按通道独立训练，不更新任何编码器权重。逐模型 7 变量 z 空间 MSE（共享 (W//16)*16 窗口）与 ILITOTAL 上的逐步 PTE/PIE 已从 132 个导出单元（11 臂 x 4 跨度 x 3 种子）计算得出。两个仅嵌入模型与五个被排除模型见下一张表。
-p91 表 13. 未列入编码器名单的模型及其原因。
-p92 “跳过”指模型可以加载与运行，但无法输出逐层隐藏状态，因而无法接入适配器——这是架构属性，不是方法失败。“排除”指该模型从未进入训练步骤。
-p93 结果一致且为负。最好的编码器（Hunyuan-1.8B）为 4.7374，最差（Qwen2.5-1.5B）为 5.2049，即 MIFlu（1.5574）MSE 的 3.04 至 3.34 倍，且 11 个全部差于决策树（4.3198）。没有任何一个在任何单元通过 Kramer & Shaman 判据。家族内部的排序也不能由规模解释：1.8B 的模型最好，而同厂商 7B 的模型更差，因此无论编码器携带了什么，它都不是容量的单调函数。
-p94 发现 F4——冻结 LLM 表征不能迁移到本任务。 11 个编码器、5 个模型家族、1.5B 至 32B 参数、132 个单元：没有一个胜过一个决策树，也没有一个通过领域判据。这一负面结果有信息量，因为协议被设计成给该想法最好的机会（冻结特征、线性读出、通道独立），而它仍然失败；这不能推出编码器永远不可能有帮助，但它确实意味着：任何声称在本任务上从冻结语言特征获得增益的论文，都需要给出机制与对照。
-p95 9. 消融阶梯：设计与当前状态
-p96 消融阶梯要问的是 MIFlu 的精度从何而来。论文模型是 GPT-2 主干 + 低秩适配（LoRA）+ 文本分支 + 线性头，因此可能承载结果的两个旋钮是 (a) LoRA 适配与 (b) 堆叠深度。阶梯因此为五个变体：去掉 LoRA，以及 K = 2、4、8、12 层，每个变体 4 个跨度、3 个种子（5 x 12 = 60 个单元），与已在基准表中的完整 K=6 臂比较。
-p97 每个变体要回答的问题值得写明，因为没有假设的“消融”只是多跑几次。no_lora 隔离出冻结主干：若精度仍在，则适配不是承载它的东西。K=2 与 K=4 检验在这条 966 行序列上是否根本需要深度；K=8 与 K=12 检验额外容量是有帮助还是仅仅过拟合。参考臂即已报告的 K=6 模型，因此阶梯中没有重复运行。
-p98 表 14. 消融阶梯（项目计划中称表 VIII）：五个变体、60 个单元，以及每个变体要回答的问题。
-p99 每个变体 4 跨度 × 3 种子 = 12 个单元；五个变体共 60 个单元；参考臂即基准表已报告的 12 个单元，不重复计数。在本文档所依据的快照中，60 个单元里已完成 27 个（驱动作业 722968），且逐变体导出尚未取回，因此本文档只报告设计与完成数，不声明任何深度趋势。--no-text 变体有意不列为一行：文本 token 位于因果掩码之后、输出头只读时间分片，故 --no-text 与完整臂逐位相同——这是结构验证（由 tests_archive/test_miflu_ablations.py 断言），绝不是消融效应。
-p100 有一项消融结果已经确立，而它是关于文本分支的负面结论：文本 token 被附加在时间分片之后并位于因果掩码之后，而输出头只读时间分片位置。因此两个不同文本张量给出逐位相同的预测，--no-text 与同种子的完整臂逐位相同——这一点由 tests_archive/test_miflu_ablations.py 断言，而非假设。在已发表的架构中，文本分支无法改变任何数字，所以“文本消融”一行只能是结构验证，不是效应。这正是原论文的多模态主张需要被仔细阅读的原因：无论其文本分支贡献了什么，在这个实现里都不可见。
-p101 其余五个变体尚未报告。在本文档所依据的快照中，60 个单元里完成 27 个（驱动作业 722968），且逐变体导出尚未取回，因此本节只报告设计与完成数，不声明任何深度趋势。早前一份内部记录称阶梯已 60/60 完成且“单调”，但本仓库没有任何产物支持该说法，已从报告中移除。
-p102 发现 F5（暂定）——按已交付的架构，多模态主张得不到支持。 文本分支位于预测路径之外，因此 --no-text 无法改变任何数字；深度与 LoRA 的问题要等 60 个单元聚合后才能回答。此处报告的是设计与状态，不是结果。
-p103 10. 证据支持什么、不支持什么
-p104 本仓库的产物支持四项主张：(1) 复现在已发表的四跨度 MSE 均值 4.5 % 以内，且符号随跨度翻转；(2) 在同一协议下，MIFlu 是 28 个模型中的精度冠军，NLinear 以比 PatchTST 少 211 倍的参数排第三；(3) 部署排序不是精度排序——前沿在校准上反转，且通过标记与 MSE 呈负秩相关；(4) 在有利于该想法的协议下，冻结 LLM 编码器不能迁移到本任务。
-p105 有五项主张不被支持，报告也不作这些主张。(1) 优于原论文：复现在均值上差 4.5 %，而逐跨度的胜出不能作为主张成立，因为协议在两处已披露的地方不同。(2) “MSE 与峰值技巧无关”：它们在榜单上正相关（ρ = +0.74）；发现针对的是前沿，而不是独立性。(3) “NLinear 是唯一通过的模型”：MIFlu 同样通过 4/16，只是路径不同且贴着边界。(4) “PatchTST 的优势为零”：检验未能拒绝相等，这与“相等”不是同一陈述。(5) “消融显示单调的深度趋势”：阶梯为 27/60，尚未聚合任何逐变体数字。
-p106 值得点明效度威胁。K&S 阈值归因于 Kramer & Shaman（2019），但仍标注 [to verify]，待与原文核对；峰值检测器是本研究的工程选择。基准只有一个数据集、一个国家、一条目标序列，因此本文不能确立跨数据集的普适性。显著性检验 n = 12，其分辨率在构造上就是粗的。目前没有滚动原点评测：每个数字都来自单一按时间切分，因此落在测试块中的季节只被看到一次。最后，编码器这一轴是冻结特征测试，不测试生成、提示或微调，其负面结果不可过度解读。
-p107 表 15. 本次工作中发现的缺陷及其对实测数字的影响。
-p108 A1 是项目拒绝引用 2026-11-02 03:57:47 之前任何 LLM 标准差的原因：在此之前种子从未进入训练路径，标准差恒为 0。A6（重试上限）仍未修复，属运行风险而非科学风险：它浪费 GPU 机时，但不会污染已完成的单元。
-p109 本报告收录缺陷清单，因为它本身就是证据的一部分：本次工作中发现八项缺陷、修复七项，其中 A1 正是这些文档拒绝引用 2026-11-02 03:57:47 之前任何 LLM 标准差的原因。A6 仍未修复，属运行风险而非科学风险：它浪费 GPU 机时，但不会污染已完成的单元。
-p110 11. 可复现性
-p111 01_最终报告/ 中的每一份文档都由 CSV 生成，而非手工编辑。在仓库根目录执行：
-p112 •  python 01_最终报告/_build2/build_docs.py——写出六份 DOCX，并在导入 dlv/data.py 时断言每个关键数字。
-p113 •  python 01_最终报告/_build2/to_pdf.py——用内置 LibreOffice kit 转 PDF，并打印每份文件的页数。
-p114 •  python 01_最终报告/_build2/verify_docs.py——重新打开每份 DOCX，用两条独立路径检查中文往返，并确认复现表仍显示符号交叉。
-p115 •  python 01_最终报告/_build2/make_manifest.py——重新生成 MANIFEST.md。
-p116 表 16. 证据映射：哪个数字由哪个产物承载。
-p117 本文档中没有任何数字是凭记忆输入的：每个数字都在构建时从上述文件读取，并由 dlv/data.py 断言关键值。
-p118 12. 参考文献
-p119 •  Moon 等，“MIFlu: Large Language Model-Based Multimodal Influenza Forecasting”，IEEE Journal of Biomedical and Health Informatics，2025。DOI: 10.1109/JBHI.2025.3561214。
-p120 •  Kramer & Shaman，“Development and validation of influenza forecasting for 64 temperate and tropical countries”，PLoS Computational Biology 15(2): e1006742，2019。DOI: 10.1371/journal.pcbi.1006742 [阈值待核实]。
-p121 •  Nie 等，“A Time Series is Worth 64 Words: Long-term Forecasting with Transformers”，ICLR 2023。arXiv:2211.14730。
-p122 •  Liu 等，“iTransformer: Inverted Transformers Are Effective for Time Series Forecasting”，ICLR 2024。
-p123 •  Zeng 等，“Are Transformers Effective for Time Series Forecasting?”，AAAI 2023。
-p124 •  美国疾病控制与预防中心，“FluView: Weekly U.S. Influenza Surveillance Report”，全国 ILI 序列（966 个每周行、7 个通道）。
-table1/row1 文档 | 内部技术报告（长篇）
-table1/row2 项目 | MIFlu 的独立复现，以及一个 28 模型的流感预测基准
-table1/row3 版本 / 日期 | 1.1 — 2026 年 11 月 3 日
-table1/row4 读者 | 导师、评阅人，以及接手本工作的下一个智能体（CodeBuddy / ChatGPT）
-table1/row5 状态 | 复现完成（+4.5%，符号交叉 2-2）；28 模型基准完成；11 个冻结编码器完成；消融阶梯进行中（本快照完成 27/60 个单元）。
-table1/row6 配套文档 | progress_report_en.docx（简短，学校模板）· ieee_manuscript_en.docx（期刊稿）· MANIFEST.md（文件清单）· 04_详细说明文档/REPO_HYGIENE.md
-table1/row7 原则 | 下文每个数字都在构建时从 02_数字表格/*.csv 读取，并由 dlv/data.py 断言。没有任何数字凭记忆引用。
-table2/row1 项目 | 取值
-table2/row2 来源 | 美国 CDC 全国流感监测数据，按周，随 MIFlu 一并发布
-table2/row3 行数 / 通道数 | 966 个每周行 × 7 个数值通道
-table2/row4 通道 | % WEIGHTED ILI, % UNWEIGHTED ILI, AGE 0-4, AGE 5-24, ILITOTAL, NUM. OF PROVIDERS, OT
-table2/row5 一致性校验 | 与作者原始文件逐位相同，最大绝对差 = 0.000e+00
-table2/row6 划分（按时间，70/10/20） | 训练 0–675 行，验证 676–772 行，测试 773–965 行（共 193 行）
-table2/row7 防泄漏约束 | containment = strict；测试集目标起始行的最小下标 = 773
-table2/row8 标准化 | StandardScaler 仅在训练段上拟合（ILITOTAL 均值 9,439.84，标准差 9,003.15 人；OT 均值 493,629）
-table2/row9 可用 / 实际计分窗口 | L24 170/160 · L36 158/144 · L48 146/144 · L60 134/128（(W//16)*16）
-table3/row1 项目 | 复现协议 | 基准协议
-table3/row2 要回答的问题 | 本文的重新实现是否落在论文表 V 的位置？ | 在同一套协议下，28 个模型中哪个最好？
-table3/row3 重复次数 | 10 次（种子 2021–2030） | 3 次（种子 42/43/44）
-table3/row4 报告方式 | 10 次重复的均值 | 3 个种子的均值
-table3/row5 指标 | 7 变量 z 空间聚合 MSE/MAE | 7 变量 z 空间 MSE（精度）+ ILITOTAL PTE/PIE（峰值技巧）
-table3/row6 参与模型 | 仅 MIFlu | 28 个模型：13 个传统预测模型、4 个基于 LLM 的预测器（MIFlu + 3 个已发表）、11 个冻结 LLM 编码器
-table3/row7 为何取此数量 | 必须与原作者的协议一致，否则不构成复现 | 文献惯例：PatchTST（ICLR'23）与 iTransformer（ICLR'24）均报告 3 个种子的均值
-table4/row1 参数 | 本文 | 原论文 | 说明
-table4/row2 数据 | 966 周 x 7 变量 | 相同 | 字节一致
-table4/row3 切分 | 676/97/193 | 相同 | 按时间
-table4/row4 输入窗口 T | 104 周 | 相同 | 
-table4/row5 跨度 L | 24/36/48/60 | 相同 | 独立训练
-table4/row6 种子（复现） | 2021-2030（10 次） | fix_seed=2021（1 次） | [偏离] 论文声称 10 次
-table4/row7 轮数 | 20 | 默认=1 | 1 轮不收敛
-table4/row8 学习率 | 1e-4 | 代码 1e-4 / 论文 5e-4 | 论文矛盾
-table4/row9 批大小 | 16 | 相同 | drop_last=True
-table4/row10 优化器 | Adam | 相同 | 
-table4/row11 GPT-2 层数/d_model | 6/768 | 相同 | 
-table4/row12 LoRA | r=4, a=4, drop=0.05 | 相同 | 
-table4/row13 可训练参数 | 1,673,496 | 相同 | LoRA+LN+头
-table4/row14 Checkpoint 选择 | 验证集 MSE | 测试集 MSE | [偏离] 测试=数据泄漏
-table4/row15 指标 | 7 变量聚合 MSE/MAE | 相同（bug: 1 变量） | [偏离] 修复 bug
-table4/row16 评测窗口 | (W//16)*16 | 相同 | 非期刊要求
-table5/row1 参数 | 本文（基准） | 原论文 | 说明
-table5/row2 种子 | 42/43/44（3 种子） | fix_seed=2021（1 次） | PatchTST/iTransformer 惯例
-table5/row3 评测窗口 | (W//16)*16 | 相同 | 28 模型共享
-table5/row4 指标 | 7 变量 z 空间 MSE/MAE | 相同 | 与 Table V 可比
-table5/row5 峰值指标 | ILITOTAL 的 PTE/PIE | 无 | 用于部署决策
-table5/row6 模型 | 28（13 常规 + 4 LLM + 11 编码器） | 1（仅 MIFlu） | 全面基准
-table5/row7 检查点选择 | 验证集 MSE | 无 | 与复现相同的修复
-table5/row8 硬件 | A100-SXM4-80GB | 未披露 | 记录来源
-table6/row1 跨度 | 本文（10 次均值 ± 标准差） | 论文 | Δ MSE | 符号 | 本文 MAE | 论文 MAE | Δ MAE
-table6/row2 L=24 | 1.3045 ± 0.0883 | 1.542 | -15.4 % | 胜 | 0.7482 | 0.726 | +3.1 %
-table6/row3 L=36 | 1.3561 ± 0.1603 | 1.422 | -4.6 % | 胜 | 0.7712 | 0.779 | -1.0 %
-table6/row4 L=48 | 1.6543 ± 0.1064 | 1.414 | +17.0 % | 负 | 0.8381 | 0.757 | +10.7 %
-table6/row5 L=60 | 1.6829 ± 0.2109 | 1.364 | +23.4 % | 负 | 0.8596 | 0.719 | +19.6 %
-table6/row6 4 跨度均值 | 1.4995 | 1.435 | +4.5 % | 负 | 0.8043 | 0.745 | +7.9 %
-table7/row1 种子 | L=24 | L=36 | L=48 | L=60
-table7/row2 s2021 | 1.240157 | 1.314358 | 1.482299 | 1.599641
-table7/row3 s2022 | 1.201078 | 1.306645 | 1.711215 | 1.664878
-table7/row4 s2023 | 1.284212 | 1.269466 | 1.663857 | 1.821282
-table7/row5 s2024 | 1.259462 | 1.154099 | 1.879495 | 1.915250
-table7/row6 s2025 | 1.464643 | 1.767328 | 1.723161 | 1.410785
-table7/row7 s2026 | 1.368497 | 1.312511 | 1.620327 | 1.984315
-table7/row8 s2027 | 1.392309 | 1.400796 | 1.628296 | 1.614602
-table7/row9 s2028 | 1.230425 | 1.302717 | 1.588157 | 1.401814
-table7/row10 s2029 | 1.231536 | 1.404061 | 1.570881 | 1.520661
-table7/row11 s2030 | 1.373057 | 1.328807 | 1.675020 | 1.895393
-table7/row12 均值 | 1.3045 | 1.3561 | 1.6543 | 1.6829
-table7/row13 标准差（n−1） | 0.0883 | 0.1603 | 0.1064 | 0.2109
-table8/row1 # | 模型 | 族 | MSE L24 | MSE L36 | MSE L48 | MSE L60 | MSE 4L | MAE 4L | 参数量
-table8/row2 1 | MIFlu | 基于 LLM | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199 | —
-table8/row3 2 | PatchTST | Transformer | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786 | 531,878
-table8/row4 3 | NLinear | 线性 | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183 | 2,520
-table8/row5 4 | DNN | 神经网络 | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057 | 33,048
-table8/row6 5 | TimeCMA | 基于 LLM | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676 | 125,830,824
-table8/row7 6 | Gradient Boosting | 经典机器学习 | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521 | —
-table8/row8 7 | KNN | 经典机器学习 | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293 | —
-table8/row9 8 | Random Forest | 经典机器学习 | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779 | —
-table8/row10 9 | iTransformer | Transformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476 | 75,672
-table8/row11 10 | Decision Tree | 经典机器学习 | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798 | —
-table8/row12 11 | Hunyuan-1.8B | 冻结 LLM 编码器 | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755 | —
-table8/row13 12 | Hunyuan-7B | 冻结 LLM 编码器 | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685 | —
-table8/row14 13 | DeepSeek-R1-Qwen-1.5B | 冻结 LLM 编码器 | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002 | —
-table8/row15 14 | DeepSeek-R1-Llama-8B | 冻结 LLM 编码器 | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786 | —
-table8/row16 15 | GRU | 神经网络 | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174 | 14,424
-table8/row17 16 | DeepSeek-R1-32B | 冻结 LLM 编码器 | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935 | —
-table8/row18 17 | LSTM | 神经网络 | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303 | 18,712
-table8/row19 18 | DeepSeek-R1-Qwen-14B | 冻结 LLM 编码器 | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019 | —
-table8/row20 19 | DeepSeek-R1-Qwen-7B | 冻结 LLM 编码器 | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133 | —
-table8/row21 20 | RNN | 神经网络 | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634 | 5,848
-table8/row22 21 | ContextPilot-8B | 冻结 LLM 编码器 | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255 | —
-table8/row23 22 | Hunyuan-4B | 冻结 LLM 编码器 | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450 | —
-table8/row24 23 | ContextPilot-14B | 冻结 LLM 编码器 | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407 | —
-table8/row25 24 | Qwen2.5-1.5B | 冻结 LLM 编码器 | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725 | —
-table8/row26 25 | Qwen-Time | 基于 LLM | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794 | 1,544,084,680
-table8/row27 26 | SVR | 经典机器学习 | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986 | —
-table8/row28 27 | CALF | 基于 LLM | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190 | 126,421,416
-table8/row29 28 | CNN | 神经网络 | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720 | 22,488
-table9/row1 模型 | PTE 步0（1 周） | PIE 步0（%） | PTE 步1（2 周） | PIE 步1（%） | PTE 步2（3 周） | PIE 步2（%） | PTE 步3（4 周） | PIE 步3（%） | 通过数
-table9/row2 NLinear | 0.21 ✓ | 3.2 ✓ | 1.33 | 6.2 | 2.31 | 11.8 | 2.86 | 16.6 | 4/16
-table9/row3 MIFlu | 0.35 | 18.9 | 0.92 | 25.9 | 1.58 | 30.5 | 1.67 | 32.1 | 4/16
-table9/row4 PatchTST | 0.68 | 30.6 | 1.42 | 32.9 | 1.42 | 33.9 | 1.44 | 33.7 | 0/16
-table9/row5 RNN | 0.96 | 57.6 | 1.97 | 60.0 | 3.00 | 61.8 | 3.97 | 63.2 | 0/16
-table9/row6 GRU | 1.14 | 58.1 | 2.06 | 59.9 | 3.00 | 62.4 | 3.75 | 64.0 | 0/16
-table9/row7 TimeCMA | 1.54 | 50.0 | 2.03 | 51.4 | 2.97 | 55.6 | 2.78 | 57.5 | 0/16
-table9/row8 DNN | 1.92 | 37.8 | 2.64 | 40.1 | 2.78 | 43.7 | 2.86 | 44.9 | 0/16
-table9/row9 Qwen-Time | 2.10 | 40.5 | 3.08 | 50.3 | 3.14 | 55.9 | 3.75 | 61.6 | 0/16
-table9/row10 iTransformer | 2.19 | 67.7 | 2.25 | 68.6 | 2.11 | 69.9 | 1.92 | 71.1 | 0/16
-table9/row11 LSTM | 3.04 | 64.6 | 3.33 | 65.6 | 3.83 | 67.5 | 3.94 | 68.7 | 0/16
-table9/row12 KNN | 3.12 | 65.8 | 2.75 | 67.7 | 2.75 | 68.7 | 2.42 | 69.4 | 0/16
-table9/row13 DeepSeek-R1-32B | 3.14 | 77.3 | 3.19 | 77.7 | 3.86 | 78.1 | 5.36 | 77.7 | 0/16
-table9/row14 DeepSeek-R1-Qwen-14B | 3.54 | 75.4 | 4.08 | 76.3 | 4.50 | 76.6 | 4.47 | 77.2 | 0/16
-table9/row15 DeepSeek-R1-Qwen-7B | 3.69 | 76.0 | 4.44 | 76.7 | 4.47 | 76.2 | 5.22 | 76.6 | 0/16
-table9/row16 CALF | 3.75 | 80.0 | 3.42 | 80.5 | 3.92 | 80.6 | 4.42 | 80.8 | 0/16
-table9/row17 Hunyuan-4B | 3.88 | 79.4 | 3.08 | 79.3 | 2.22 | 78.7 | 2.83 | 78.0 | 0/16
-table9/row18 SVR | 3.92 | 77.3 | 3.50 | 79.9 | 3.33 | 80.4 | 2.75 | 80.6 | 0/16
-table9/row19 ContextPilot-14B | 4.11 | 76.8 | 4.75 | 77.8 | 5.44 | 78.1 | 5.56 | 78.4 | 0/16
-table9/row20 Hunyuan-1.8B | 4.26 | 69.7 | 4.81 | 70.7 | 4.19 | 71.9 | 4.36 | 73.4 | 0/16
-table9/row21 Qwen2.5-1.5B | 4.31 | 74.6 | 5.08 | 74.8 | 5.56 | 74.7 | 6.39 | 74.6 | 0/16
-table9/row22 Decision Tree | 4.54 | 55.1 | 5.06 | 53.8 | 5.64 | 50.2 | 4.75 | 56.7 | 0/16
-table9/row23 DeepSeek-R1-Llama-8B | 4.67 | 76.1 | 4.36 | 77.0 | 4.25 | 77.5 | 3.94 | 77.9 | 0/16
-table9/row24 ContextPilot-8B | 4.90 | 78.3 | 4.22 | 78.9 | 5.28 | 79.1 | 5.44 | 79.3 | 0/16
-table9/row25 Hunyuan-7B | 5.12 | 73.9 | 5.81 | 75.7 | 6.03 | 75.9 | 4.28 | 76.1 | 0/16
-table9/row26 Gradient Boosting | 5.33 | 52.0 | 4.67 | 58.7 | 4.75 | 62.8 | 5.08 | 65.4 | 0/16
-table9/row27 Random Forest | 5.35 | 65.9 | 5.19 | 66.5 | 5.58 | 67.0 | 5.64 | 67.6 | 0/16
-table9/row28 DeepSeek-R1-Qwen-1.5B | 5.83 | 77.4 | 5.44 | 78.0 | 5.78 | 78.3 | 6.11 | 78.5 | 0/16
-table9/row29 CNN | 6.28 | 81.1 | 6.78 | 81.9 | 6.22 | 82.2 | 7.14 | 82.6 | 0/16
-table10/row1 模型 | 跨度 | 步0（1周） | 步1（2周） | 步2（3周） | 步3（4周）
-table10/row2 NLinear | L=24 | PASS (0.11 wk, 3.9 %) | fail (1.33 wk, 8.4 %) | fail (2.33 wk, 11.9 %) | fail (2.67 wk, 18.7 %)
-table10/row3 NLinear | L=36 | PASS (0.33 wk, 4.2 %) | fail (1.33 wk, 7.2 %) | fail (2.11 wk, 15.3 %) | fail (2.67 wk, 18.1 %)
-table10/row4 NLinear | L=48 | PASS (0.22 wk, 2.4 %) | fail (1.22 wk, 4.7 %) | fail (2.22 wk, 10.0 %) | fail (2.78 wk, 16.7 %)
-table10/row5 NLinear | L=60 | PASS (0.17 wk, 2.5 %) | fail (1.44 wk, 4.5 %) | fail (2.56 wk, 10.0 %) | fail (3.33 wk, 13.0 %)
-table10/row6 MIFlu | L=24 | PASS (0.00 wk, 18.3 %) | fail (0.89 wk, 26.7 %) | fail (1.22 wk, 30.5 %) | fail (1.33 wk, 31.6 %)
-table10/row7 MIFlu | L=36 | PASS (0.00 wk, 18.7 %) | fail (0.78 wk, 26.3 %) | fail (1.67 wk, 31.5 %) | fail (1.33 wk, 32.4 %)
-table10/row8 MIFlu | L=48 | fail (1.22 wk, 18.0 %) | PASS (0.67 wk, 24.8 %) | fail (1.22 wk, 30.1 %) | fail (1.33 wk, 33.2 %)
-table10/row9 MIFlu | L=60 | PASS (0.17 wk, 20.5 %) | fail (1.33 wk, 25.8 %) | fail (2.22 wk, 29.8 %) | fail (2.67 wk, 31.2 %)
-table10/row10 PatchTST | L=24 | fail (0.67 wk, 30.6 %) | fail (1.00 wk, 34.0 %) | fail (1.22 wk, 33.6 %) | fail (1.22 wk, 30.7 %)
-table10/row11 PatchTST | L=36 | fail (1.00 wk, 26.2 %) | fail (1.67 wk, 32.2 %) | fail (1.33 wk, 31.2 %) | fail (1.33 wk, 33.9 %)
-table10/row12 PatchTST | L=48 | fail (0.56 wk, 30.4 %) | fail (1.33 wk, 30.9 %) | fail (0.89 wk, 35.2 %) | fail (0.89 wk, 35.0 %)
-table10/row13 PatchTST | L=60 | fail (0.50 wk, 35.0 %) | fail (1.67 wk, 34.3 %) | fail (2.22 wk, 35.7 %) | fail (2.33 wk, 35.1 %)
-table11/row1 量 | 取值
-table11/row2 MSE 对 log₁₀(参数量) 的拟合斜率 | +0.1171
-table11/row3 决定系数 R² | 0.0223
-table11/row4 参与拟合的模型（仅含参数模型） | 11
-table11/row5 帕累托集合（非支配） | NLinear（2,520 参数）· PatchTST（531,878 参数）
-table11/row6 参数量之比 PatchTST / NLinear | 211.1 倍
-table11/row7 PatchTST 相对 NLinear 的 MSE 优势 | 11.2 %
-table11/row8 PatchTST 相对季节朴素基线的改进 | 73.17 %
-table11/row9 28 个模型的 MSE 跨度 | 1.5574（最好）……5.6155（最差），即 3.6 倍
-table11/row10 MSE 与均值 PIE 的 Spearman ρ（28 模型） | +0.736（p < 1e-4）
-table11/row11 MSE 与 K&S 通过数的 Spearman ρ（28 模型） | -0.429（p = 0.023）
-table12/row1 模型 A | 模型 B | n | 平均 Δ MSE | A 胜 | p（Holm） | 效应量 d
-table12/row2 NLinear | PatchTST | 12 | +0.2095 | 2/12 | 0.1172 | 1.15
-table12/row3 Gradient Boosting | RNN | 12 | -1.4029 | 12/12 | 0.06637 | 4.86
-table12/row4 CALF | RNN | 12 | +0.5111 | 0/12 | 0.06637 | 1.65
-table12/row5 CALF | SVR | 12 | +0.2397 | 0/12 | 0.06637 | 1.82
-table12/row6 CALF | TimeCMA | 12 | +2.9704 | 0/12 | 0.06637 | 14.78
-table12/row7 CNN | Decision Tree | 12 | +1.2957 | 0/12 | 0.06637 | 2.69
-table12/row8 CNN | DNN | 12 | +3.4740 | 0/12 | 0.06637 | 6.43
-table13/row1 # | 编码器 | 族 | 规模 | 单元数 | 读出方式
-table13/row2 1 | Qwen2.5-1.5B | Qwen2.5 (dense) | 1.5 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table13/row3 2 | DeepSeek-R1-Distill-Qwen-1.5B | DeepSeek-R1 distill (Qwen2) | 1.5 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table13/row4 3 | DeepSeek-R1-Distill-Qwen-7B | DeepSeek-R1 distill (Qwen2) | 7 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table13/row5 4 | DeepSeek-R1-Distill-Llama-8B | DeepSeek-R1 distill (Llama) | 8 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table13/row6 5 | DeepSeek-R1-Distill-Qwen-14B | DeepSeek-R1 distill (Qwen2) | 14 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table13/row7 6 | DeepSeek-R1-Distill-Qwen-32B | DeepSeek-R1 distill (Qwen2) | 32 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table13/row8 7 | Tencent ContextPilot-8B | Tencent ContextPilot | 8 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table13/row9 8 | Tencent ContextPilot-14B | Tencent ContextPilot | 14 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table13/row10 9 | Tencent Hunyuan-1.8B | Tencent Hunyuan | 1.8 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table13/row11 10 | Tencent Hunyuan-4B | Tencent Hunyuan | 4 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table13/row12 11 | Tencent Hunyuan-7B | Tencent Hunyuan | 7 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table13/row13 — | 11 arms | — | — | 132 / 156 | 24 个单元被跳过
-table14/row1 状态 | 模型 | 原因
-table14/row2 跳过（24 单元） | Tencent WeMM-Embedding-2B | 仅提供句向量嵌入，无法输出逐层隐藏状态
-table14/row3 跳过（24 单元） | Tencent WeMM-Embedding-4B | 仅提供句向量嵌入，无法输出逐层隐藏状态
-table14/row4 排除 | Tencent Penguin-Encoder | 需要 trust_remote_code，在锁定的环境中无法加载
-table14/row5 排除 | Tencent Youtu-HiChunk | 不暴露逐层隐藏状态
-table14/row6 排除 | Tencent KaLM-Embedding-Gemma3-12B | 权重下载失败
-table14/row7 排除 | Qwen3.8-27B-FP8 | FP8 反量化后约 54.7 GB（bf16），未下载
-table14/row8 排除 | Llama-70B | 无法放入 80 GB A100
-table15/row1 变体 | 开关 | 单元数 | 要回答的问题 | 状态
-table15/row2 full (K=6) | default | — | 参考臂：MIFlu 的基准实例本身（已见基准表）。 | 见基准表
-table15/row3 no_lora | --no-lora | 12 | 精度来自 LoRA 适配，还是来自冻结的主干？ | 未聚合
-table15/row4 K=2 | --num-layers 2 | 12 | 深度阶梯：2 层堆叠是否会损失精度？ | 未聚合
-table15/row5 K=4 | --num-layers 4 | 12 | 深度阶梯：论文区域模型的深度。 | 未聚合
-table15/row6 K=8 | --num-layers 8 | 12 | 深度阶梯：增加深度是否有帮助？ | 未聚合
-table15/row7 K=12 | --num-layers 12 | 12 | 深度阶梯：是否存在容量上限？ | 未聚合
-table16/row1 # | 缺陷 | 若不修复的后果 | 状态
-table16/row2 A1 | 种子从未进入 LLM 训练路径；适配器重置了随机数发生器 | 36 个 LLM 单元跨种子逐位相同；所有标准差恒为 0 | 已于 2026-11-02 03:57:47 修复
-table16/row3 A2 | 最优验证快照克隆了冻结的编码器，而不是可训练的头 | 7B 模型显存溢出；32B 模型在任何 80 GB A100 上都不可能完成 | 已修复
-table16/row4 A3 | 模型注册表中 revision 为空（缺少 queue/p2/ 目录） | 所有可运行的 LLM 单元以 skip.no-revision 终止 | 已修复
-table16/row5 A4 | 存在两种不同的 HuggingFace 缓存布局 | 13 个模型中有 10 个对 from_pretrained 不可见，且发生在分配 GPU 之后 | 已修复
-table16/row6 A5 | flock 在 GPFS 上不是跨节点互斥量 | 两条通道互相丢失对方的 DONE 标记；改用 mkdir 锁 | 已修补，未验证
-table16/row7 A6 | 控制器未强制执行重试次数上限 | 某些行达到 attempts=26，而上限声明为 2 | 未修复
-table16/row8 A7 | 两条流水线根本无法执行（缺少分发分支） | 表 VI / 滚动原点的行永远不会启动 | 已修复
-table16/row9 A8 | persistent_driver.sh 恰在有工作时退出（set -u 展开） | 队列在仍有可运行行时停止推进 | 已修复
-table17/row1 产物 | 内容 | 用于
-table17/row2 02_数字表格/BENCH_MSE_BY_MODEL_L.csv | 逐模型 × 跨度的 MSE/MAE（7 变量、ILITOTAL、物理单位） | 基准表
-table17/row3 02_数字表格/BENCH_EFFICIENCY.csv | 参数量、帕累托标记、斜率、R² | 效率表、帕累托图
-table17/row4 02_数字表格/BENCH_PTE_PIE_BY_STEP.csv | 逐模型 × 跨度 × 步的 PTE/PIE/通过标记 | 峰值技巧两表、热力图
-table17/row5 02_数字表格/BENCH_SEASONAL_NAIVE.csv | 季节朴素基线 | 基准表注
-table17/row6 02_数字表格/BENCH_PAIRED_TESTS.csv | 配对符号翻转检验，Holm 校正 | 配对检验表
-table17/row7 02_数字表格/BENCH_GPU_PROVENANCE.csv | 204 个单元：GPU、分区、节点、作业号 | 硬件表
-table17/row8 02_数字表格/ESSAY_VS_REPRODUCTION_TABLE_V.csv | 论文表 V 的取值与早期本文结果 | 复现表
-table17/row9 04_详细说明文档/LEDGER.md (2026-11-01 rows) | 40 次运行的逐种子 oracle | oracle 表
-table17/row10 03_预测数据_证据/expanded_runs/**/pred_*.npz | 逐窗口原始预测——所有数字都可重算 | 所有表格
-table17/row11 05_程序代码/verify_bench_unchanged.py, 05_程序代码/verify_miflu_oracle.py | 重算门限 | 可信边界
+p0 MIFlu 复现与流感预测审计
+p1 含解释性问答的内部技术报告
+p2 目录
+p3 1 数据与来源
+p4 2 方法与文献
+p5 3 MIFlu 复现
+p6 4 基准精度
+p7 5 峰值时间与幅度
+p8 6 精度与参数量
+p9 7 统计审计
+p10 8 冻结语言编码器
+p11 9 消融设计与状态
+p12 10 解释与发表计划
+p13 11 可复现性与待核实项
+p14 12 参考文献
+p16 阅读目的。 本内部报告用于导师交流及理解过程。Q01–Q25 放在相关证据旁：每题连接具名论文、阅读位置与本地证据，解释选择理由，并给出导师简答。精度与峰值覆盖 28 个模型，参数导出覆盖 11 个，配对检验覆盖 17 个。
+p17 1 数据与来源
+p18 在仓库根目录运行 python scripts/verify_snapshot.py --raw-smoke 及 python -m pytest tests/test_snapshot_audit.py -q。审计重算主要聚合值、峰值标记、相关系数、回归、Holm 校正和一个原始预测 MSE。七个新增 CPU 审计测试已通过，它们与归档模型测试分开。修正 ZIP 已提供 tests_archive/，但历史目录布局及模型依赖缺失导致收集失败。本次不主张归档测试通过数或可靠总数。本次未重跑训练、未查询实时 HPC，亦未运行上游代码。原 CSV 保持不变，Holm 修正另行导出。
+p19 表 1. 数据与评测约定
+p20 一致性是选择本包两个 966 行文件中相应七列后比较，不能重新证明与独立下载的作者文件逐字节相同。作者格式文件的日期为合成标签。
+p21 Q01 为什么采用 676 行训练、97 行验证、193 行测试？
+p22 直接回答与本地证据。 所附 966 行协议把 floor(966 × 0.7) = 676 行分给训练，floor(966 × 0.2) = 193 行分给测试，其余 97 行用于验证。训练段拟合权重和标准化参数，验证段选择检查点，最终测试段评价选择后的表现。按时间先后划分，可以避免用后来的观测训练较早的预测。这是本项目采用的协议，并非所有期刊统一要求；固定版本上游协议仍待独立核实。
+p23 文献依据与选择理由。 Tan 等明确对 Illness 使用 70/10/20 [13，第 3.3 节]，iTransformer 则保持按时间分离 [5，附录 A.1]。这是具体的预测研究先例：保留较多训练数据，以验证集选模，再用较晚观测做最终测试。676/97/193 的精确整数来自本项目 966 行及取整规则。文献支持设计理由，但不证明该比例对所有流感季最优，也不能证明本地文件与上游身份一致。
+p24 向导师简答。 这个划分有 Tan 等 Illness 实验的先例，时间分离用于保护最终评价 [13, 5]。
+p25 论文位置。 Tan et al. [13], §3.3 Datasets and Evaluation Metrics; iTransformer [5], Appendix A.1.
+p26 证据。 configs.py DATA_PROFILES[author_repo_966]; BENCH_MSE_BY_MODEL_L.csv; eval_windows.py
+p27 Q02 L24 明明有 170 个窗口，为什么只评 160 个？
+p28 直接回答与本地证据。 本地评测约定只保留完整的 16 个窗口一批，即 (W//16)×16。因此 L24/36/48/60 的 170/158/146/134 个可用窗口变成 160/144/144/128 个计分窗口。所有模型使用相同窗口，可避免拿不同测试样本比较。但裁剪会删去某一段时间尾部，仍可能改变分数。这是本快照为保持可比性采用的选择，不证明裁剪在科学上最优；仍需完整窗口敏感性分析。本次没有独立复核某个被删尾部的具体难度倍数。
+p29 文献依据与选择理由。 Tan 等复核时保留原数据加载器与训练条件 [13，第 3.1 节]，说明必须交代哪些样本进入计分，却不表示论文要求裁剪。本地完整批量规则改变了计分样本。各模型采用相同保留窗口，可消除比较不公平，但删去尾部仍可能改变结果。必要的敏感性分析是让所有模型在完整窗口重评分，再比较排名。文献不能代替被删尾部难度的原始计算。
+p30 向导师简答。 裁剪用于统一计分样本，完整窗口重评分用于检验裁剪影响 [13]。
+p31 论文位置。 Tan et al. [13], §3.1 Reproducibility Note; local eval_windows.py.
+p32 证据。 BENCH_MSE_BY_MODEL_L.csv; eval_windows.py; scripts/verify_snapshot.py --raw-smoke
+p33 Q03 为什么标准化参数只能从训练段计算？
+p34 直接回答与本地证据。 如果用完整序列计算均值或标准差，就会把未来测试段的信息带入模型准备过程。只在训练段拟合，可避免这类信息泄漏。七个通道分别标准化。本次一致性检查比较所附两个文件的七个对应数值列，最大绝对差为零。这只能核实本地副本数值一致，不能代替重新下载作者文件后核实字节一致。
+p35 文献依据与选择理由。 Kapoor 与 Narayanan 把跨越训练/测试边界的预处理列为泄漏路径 [22，L1.2]。用于这里，就是只在训练段拟合各通道均值和标准差，再原样复用。如果未来观测决定这些常数，预处理已适应留出分布，即使梯度更新没有使用测试标签。因此训练段标准化属于实验设计。本地文件相等检查则只证明输入一致，不能证明所有泄漏路径均不存在。
+p36 向导师简答。 依照 Kapoor 与 Narayanan 对泄漏的区分，预处理只在训练段拟合 [22]。
+p37 论文位置。 Kapoor and Narayanan [22], Results, leakage taxonomy L1 and L1.2.
+p38 证据。 06_原始数据集/scaler_miflu_author966.json; scripts/verify_snapshot.py
+p39 2 方法与文献
+p40 分块与线性基线已有研究 [3–5]。Time-LLM、CALF 与 TimeCMA 的对齐及适配设计不同 [6–8]。Chronos、TimesFM、Moirai、Lag-Llama 在数值序列上预训练，本次未评测 [9–12]。较早的 LLM 移除研究已质疑语言预训练收益 [13]，而 2026 年预印本报告跨数据集偏移下的条件性收益 [14]。本项目贡献在于特定流感任务的协议审计与多指标比较。
+p41 表 2. 分开的复现与基准协议
+p42 三个种子是算力预算选择，不是统一的会议规则。复现与基准采用不同种子集合，不能相互替换。作者上游具体协议缺陷仍须对照固定版本核实。
+p43 Q04 为什么复现用十个种子，基准却用三个种子？
+p44 直接回答与本地证据。 两者回答不同问题。所附复现以 2021–2030 十个种子对照转录的原文表格；更广的基准以 42/43/44 三个种子在统一协议下比较各实现。正式矩阵为 28 模型 × 4 跨度 × 3 种子 = 336 单元；十个种子则需要 1,120 单元。采用三个种子反映项目算力预算，不证明检验功效已经足够，更多种子也可能改善不确定性估计。本次没有证据支持所有场合均要求三个种子，或增加种子毫无收益。
+p45 文献依据与选择理由。 原来的三种子引用不正确。PatchTST 的主结果采用固定种子，另做五种子监督稳健性检查 [3，附录 A.6.1]；iTransformer 报告五次运行的标准差 [5，附录 A.2 表 5]。这些段落不能证明三种子是两文共同惯例。我们的选择属于算力折衷。Bouthillier 等区分重复运行精度和更广的基准变异 [19]：增加种子可改善前者，增加季节/原点处理另一类不确定性。十次复现不会让独立的三种子基准同样精确。
+p46 向导师简答。 三种子是算力折衷；两篇所引论文实际提供五种子稳健性证据，提示仍需加强检查 [3, 5]。
+p47 论文位置。 PatchTST [3], Appendix A.6.1; iTransformer [5], Appendix A.2 and Table 5; Bouthillier et al. [19], Appendix C.3.
+p48 证据。 ESSAY_VS_REPRODUCTION_TABLE_V.csv; BENCH_MSE_BY_MODEL_L.csv; dlv/data.py ORACLE
+p49 Q05 哪些实现差异已经核实，哪些仍只是待核实的说法？
+p50 直接回答与本地证据。 已检查的本地代码在验证段选择检查点，并对七个标准化通道计分。交接笔记把测试集选检查点和单通道加载问题归于上游代码，但本次没有独立检查到固定版本作者仓库来支持该归因。笔记还提到学习率和训练轮数设置差异。因此应披露本地流程与未核实的参考设置，不能声称只有两处修复就解释全部分数差异。若要确认因果，应固定数据、种子及其他设置，每次只改变一个因素。
+p51 文献依据与选择理由。 检查点属于选模选择；按测试误差挑选，就是用最终评价拟合该选择，不符合干净分离 [22，L1]。不论上游缺陷是否能证实，这个原则都支持本地验证集选检查点。按声明的七通道计分则是另一项指标一致性问题。这些原则不能证明 Moon 等犯了所指缺陷，也不能证明差距仅由两项改变造成。因果归因需要配对运行，每次只改变检查点、加载器或另一项因素。
+p52 向导师简答。 验证集选模保护留出测试；上游是否有缺陷，须另有证据 [22]。
+p53 论文位置。 Kapoor and Narayanan [22], taxonomy L1, clean separation through modelling and evaluation.
+p54 证据。 train_miflu.py; audit/REPO_AUDIT.md; audit/UNVERIFIED_ITEMS.md
+p55 本项目采用时序划分、仅训练段拟合标准化，并用验证集选择检查点。交接资料将测试集选检查点及单变量加载问题归于上游代码，但未提供固定版本作者仓库，公开端点也未能打开，因此上游指控仍未核实。笔记还列出代码默认学习率与原文设置的差异，不能称为仅有两处偏离。
+p56 峰值时间误差 PTE 是预测与观测峰值周的绝对差。峰值强度误差 PIE 为峰高绝对差除以观测峰高后乘百分比。Kramer–Shaman [2] 可核实分别为一周与 25% 的容差。项目把两者联合应用于（模型、L、step）单元的平均误差；该联合筛选及峰检测属于项目选择，不是临床接受标准。平均误差达标不等于逐季成功概率。
+p57 Q06 为什么 MSE 用七变量，而峰值误差只用 ILITOTAL？
+p58 直接回答与本地证据。 七变量 MSE 先逐通道标准化，再平均平方误差，衡量整体无量纲预测误差。这个平均损失不是患者人数时间序列，也没有一个统一的反标准化器。峰值时间与高度则必须针对一条真实序列。因此本项目对 ILITOTAL 使用其训练段标准化参数反变换，均值为 9,439.84、标准差为 9,003.15 人。一个模型可以在七通道总体误差上较好，但在 ILITOTAL 峰值上较差。评价对象与损失函数不同，是排名变化的一个解释。
+p59 文献依据与选择理由。 Hyndman 与 Koehler 解释尺度为何重要 [21，第 2.1 节]；Kramer 与 Shaman 在观测疾病序列上定义峰值 [2]。本项目标准化总体损失将各通道原单位平方误差除以训练方差，所得是无量纲损失，而非可用一组参数反变换的患者人数曲线。峰值评测应先反变换 ILITOTAL 预测和观测，再找峰；对七通道损失找峰会回答另一个问题。文献支持可解释端点，ILITOTAL 是明确的项目选择。
+p60 向导师简答。 标准化整体误差与可解释疾病峰值，是不同端点 [21, 2]。
+p61 论文位置。 Hyndman and Koehler [21], §2.1; Kramer and Shaman [2], Forecast accuracy and comparison.
+p62 证据。 BENCH_MSE_BY_MODEL_L.csv; BENCH_PTE_PIE_BY_STEP.csv; scaler_miflu_author966.json
+p63 3 MIFlu 复现
+p64 复现 CSV 的平均 MSE 为 1.4995，对照 1.4355，增加 4.5%。L24、L36 更低，L48、L60 更高。平均 MAE 为 0.8043，对照 0.7452（+7.9%），但逐跨度为一低三高；MAE 没有 MSE 的二比二符号交叉。协议差异与上游来源缺失限制了精确复现的主张。
+p65 表 3. MIFlu 复现与原文对照
+p66 来源：ESSAY_VS_REPRODUCTION_TABLE_V.csv 第 2–6 行。标准差由代码中转录的十种子 oracle 重算；原始运行日志未随包提供。正差表示误差更高。
+p67 复现结论。 在已披露实现差异下，观测 MSE 差为 +4.5%，不能据此主张优于原文。
+p68 Q07 为什么这里的 MIFlu 是 1.4995，基准表却是 1.5574？
+p69 直接回答与本地证据。 前者来自十种子复现表的四跨度均值，后者来自三个基准种子的四跨度均值，它们汇总的是不同运行集合。讨论复现时，应把 1.4995 与原文转录均值 1.4355 比较；讨论选模时，应把 1.5574 与同一基准中的其他模型比较。两数之差并不能证明在其他条件完全一致时模型进步、退步或抄错；归因还需要完整运行配置与原始来源。
+p70 文献依据与选择理由。 Bouthillier 等说明基准估计取决于被抽样的学习流程 [19]。均值是指定运行集合的估计，不是模型名称自带的不变属性。两项 MIFlu 估计汇总不同种子集合，服务不同对照。差值可能同时包含种子波动与配置差异，不能分离某一原因。应先解释两表运行定义；若关心成因，再取回匹配的逐运行配置。
+p71 向导师简答。 两数估计不同运行集合，不能把差值视为一项改变的受控效果 [19]。
+p72 论文位置。 Bouthillier et al. [19], §§2–3, benchmark estimators and sources of variation.
+p73 证据。 ESSAY_VS_REPRODUCTION_TABLE_V.csv lines 2–6; BENCH_MSE_BY_MODEL_L.csv model=miflu
+p74 Q08 为什么 MSE 与 MAE 的逐跨度方向不完全一致？
+p75 直接回答与本地证据。 MSE 对误差平方，因此更重视大误差；MAE 平均绝对误差。因此，少数大误差的变化可能对两者产生不同影响。相对原文转录值，MSE 在 L24/L36 较低、L48/L60 较高；MAE 只有 L36 较低，其他三个跨度较高。平均差为 MSE +4.5%、MAE +7.9%。不能把两者都说成两低两高。
+p76 文献依据与选择理由。 该文区分平方与绝对误差，以及两者对大残差的敏感性 [21]。作代数示例而非实测：残差翻倍，绝对贡献变两倍，平方贡献变四倍。因此残差分布改变时，MSE 与 MAE 可以不同向。CSV 确定实际逐跨度符号，文献解释为何可能不同。若要确定哪些误差造成差距，仍需逐通道、逐窗口残差，不能只靠一般原理。
+p77 向导师简答。 MSE 更重视大残差，逐跨度方向必须与 MAE 分开读取 [21]。
+p78 论文位置。 Hyndman and Koehler [21], §2.1, MSE/MAE and sensitivity to large residuals.
+p79 证据。 ESSAY_VS_REPRODUCTION_TABLE_V.csv lines 2–6
+p80 表 4. 代码中转录的复现 oracle
+p81 已核算其均值并与复现 CSV 对照。来源为 dlv/data.py 与 verify_miflu_oracle.py 的 ORACLE 常量。十种子原始运行日志未提供，因此不能称为独立原始预测验证。
+p82 Q09 种子 oracle 和预测曲线能证明已完整复现吗？
+p83 直接回答与本地证据。 oracle 是代码中转录的十种子分数记录，可以核算均值和标准差，但没有提供对应十种子的原始日志与预测供独立重评分。沿用曲线展示基准序列，不是这些十种子复现运行的独立轨迹。检查点选择、种子波动和配置差异都可能解释逐跨度表现，但尚未分离其因果作用。可辩护的结果是在明确限制下，平均 MSE 差为 +4.5%。
+p84 文献依据与选择理由。 重复运行估计与可追溯评测处理不同缺口 [19, 22]。oracle 核对转录记录的算术，保存预测才可核对流程是否产生该记录。实际链条是运行配置 → 预测 → 计分代码 → 单元 → 聚合。基准图是另一种摘要，不能建立十种子复现轨迹。即使均值接近，链条缺项仍限制主张；只要说明真实来源，沿用曲线仍可作示例。
+p85 向导师简答。 oracle 建立算术证据，原始输出建立来源证据，两者都重要 [19, 22]。
+p86 论文位置。 Bouthillier et al. [19], variance analysis; Kapoor and Narayanan [22], model info sheets.
+p87 证据。 dlv/data.py ORACLE; ESSAY_VS_REPRODUCTION_TABLE_V.csv; figure_captions.json
+p89 miflu，L=24。纵轴为 ILITOTAL 患者人数，横轴为文件测试周下标。黑线为观测，其余为固定预测步 s0–s3。计分窗口 160。此图沿用所附示例，本次未独立重建绘图原始输入。
+p91 miflu，L=60。纵轴为 ILITOTAL 患者人数，横轴为文件测试周下标。黑线为观测，其余为固定预测步 s0–s3。计分窗口 128。此图沿用所附示例，本次未独立重建绘图原始输入。
+p92 4 基准精度
+p93 表 5. 全部保留模型的精度
+p94 来源：BENCH_MSE_BY_MODEL_L.csv，按 model 和 L 定位。各行由三个种子在 160/144/144/128 个窗口上聚合。项目主动排除了 DLinear，发表前需补充理由与敏感性分析。名称指本项目实现，排名本身不能证明与原论文方法完全等价。
+p95 Q10 28 个模型与不同分析子集各指什么？
+p96 直接回答与本地证据。 正式名单为 13 个传统模型 + 4 个基于 LLM 的模型 + 11 个冻结编码器。精度和峰值分析覆盖全部 28 个；参数导出支持其中 11 个；配对检验覆盖包括 MIFlu 的 17 个非编码器模型。项目主动把 DLinear 排除于正式名单及配对表。它在历史硬件来源表中出现，不代表属于正式保留模型。补充含 DLinear 的敏感性分析可加强基线覆盖；它曾出现在原文，本身不足以构成科学排除理由。
+p97 文献依据与选择理由。 各家族检验不同解释：简单时间映射 [4]、patch 与反转变量词元 [3, 5]，以及明确的跨模态对齐 [7, 8]。这支持采用多样对照，不证明 28 是最优数量，也使实现忠实度很重要：同名适配可能省略原文关键对齐或训练组件。DLinear 是这条文献中的相关简单对照；它曾出现在原论文，本身不是在敏感性分析中省略它的科学理由。
+p98 向导师简答。 论文支持选择不同对照；导出文件决定每项分析实际覆盖哪些模型 [3–5, 7, 8]。
+p99 论文位置。 Zeng et al. [4], §4; PatchTST [3], §3.1; iTransformer [5], §3; CALF [7] and TimeCMA [8], author abstracts.
+p100 证据。 BENCH_MSE_BY_MODEL_L.csv; BENCH_EFFICIENCY.csv; BENCH_PAIRED_TESTS.csv; BENCH_GPU_PROVENANCE.csv
+p101 Q11 MIFlu 的 MSE 最低，是否就应直接选它部署？
+p102 直接回答与本地证据。 MIFlu 的观测基准 MSE 最低，为 1.5574。这是在单一全国划分下的描述性精度结果，没有直接测量漏峰、误报、运行时间、区域稳健性或前瞻效益。MSE 差距较大，也不能证明调参不重要，因为本实验没有把调参作为另一因素进行对照。后面的评价维度回答精度表单独无法回答的问题。
+p103 文献依据与选择理由。 峰值时间/强度是疾病领域端点 [2]，区间评分考查预测不确定性 [18]；七通道点误差排名不会自动提供这些证据。应分别看观测精度、峰值取舍与操作代价。NLinear 峰高误差低不能抹去平均时间误差更大；MIFlu 的 MSE 最低也不证明区间校准或前瞻效益。我们因此可先论证选模证据，再谈公共卫生部署赢家。
+p104 向导师简答。 MIFlu 赢的是观测点误差排名，峰值端点与不确定性须有各自证据 [2, 18]。
+p105 论文位置。 Kramer and Shaman [2], Forecast accuracy and comparison; Bracher et al. [18], §§3–4.
+p106 证据。 BENCH_MSE_BY_MODEL_L.csv; audit/GRADE_READINESS.md
+p107 F0 结论。 MIFlu 的观测 MSE 最低（1.5574），但仅靠 MSE 不能证明公共卫生效用。前三名相对 MIFlu 的跨度为 20.2%，并非小于 20%。
+p108 正式名单为 13 个传统模型、MIFlu 加另外三个基于 LLM 的实现，以及 11 个冻结编码器，总计 28。28 个模型平均 MSE 均低于季节朴素导出的 6.2132。现有证据不能判断超参数调优是否较不重要。
+p110 patchtst，L=24。纵轴为 ILITOTAL 患者人数，横轴为文件测试周下标。黑线为观测，其余为固定预测步 s0–s3。计分窗口 160。此图沿用所附示例，本次未独立重建绘图原始输入。
+p112 nlinear，L=24。纵轴为 ILITOTAL 患者人数，横轴为文件测试周下标。黑线为观测，其余为固定预测步 s0–s3。计分窗口 160。此图沿用所附示例，本次未独立重建绘图原始输入。
+p113 5 峰值时间与幅度
+p114 峰值时间误差 PTE 是预测与观测峰值周的绝对差。峰值强度误差 PIE 为峰高绝对差除以观测峰高后乘百分比。Kramer–Shaman [2] 可核实分别为一周与 25% 的容差。项目把两者联合应用于（模型、L、step）单元的平均误差；该联合筛选及峰检测属于项目选择，不是临床接受标准。平均误差达标不等于逐季成功概率。
+p115 表 6. 峰值时间与强度误差
+p116 均值跨越 16 个（L，step）单元。通过数是在各单元的聚合误差上应用 PTE ≤ 1 周且 PIE ≤ 25%，不是逐季达标率。PIE 衡量点预测的峰高误差，不是概率校准。
+p117 表 7. 各跨度与提前步的联合峰值筛选
+p118 每格为 PTE（周）/ PIE（%）。s0–s3 是预测的第 1–4 周。峰检测使用突出度 0.15 × 极差、间距 15、±8 周匹配。检测设置及联合聚合均为项目选择。来源：BENCH_PTE_PIE_BY_STEP.csv。
+p119 Q12 为什么 MIFlu 和 NLinear 都通过 4/16，却仍有不同结论？
+p120 直接回答与本地证据。 一次通过要求同一个（L，step）单元的平均 PTE ≤ 1 周且平均 PIE ≤ 25%。NLinear 在四个跨度的 step 0 均通过；MIFlu 在 L24/L36/L60 的 step 0，以及 L48 的 step 1 通过。因此，相同通过数会隐藏达标位置及误差大小的差异。跨全部 16 单元，NLinear 的 PIE 更低，为 9.477% 对 26.846%；MIFlu 的 PTE 更低，为 1.128 对 1.677 周。结论是时间与峰高之间存在取舍，任何一个都不是全面占优。
+p121 文献依据与选择理由。 文献分开评价时间与强度，支持先看两项误差，再压缩为通过数 [2]。相同四次通过隐藏不同步长/跨度位置，以及距阈值多远的差别。优先重视提前一周峰高的应用，可能与重视时间的应用选择不同取舍。这是对本地表格的条件式解释，不是文献推荐 NLinear。二元通过标签只是连续误差的粗略摘要。
+p122 向导师简答。 相同通过数隐藏不同位置与时间—峰高取舍 [2]。
+p123 论文位置。 Kramer and Shaman [2], Forecast accuracy and comparison, separate timing/intensity tolerances.
+p124 证据。 BENCH_PTE_PIE_BY_STEP.csv model in {miflu,nlinear}
+p125 Q13 4/16 是否表示预测流行季成功的概率为 25%？
+p126 直接回答与本地证据。 不是。分母是四个跨度乘四个固定预测步，不是 16 个独立流行季。每个单元本身已经聚合可用运行或事件的误差。先平均再应用阈值，与先判断每个事件成功再计数，可能得到不同结果。Kramer–Shaman [2] 支持分别采用时间和强度容差；把两者联合用于聚合单元，以及具体峰检测设置，属于本项目选择，不是临床接受检验或经校准的概率。
+p127 文献依据与选择理由。 Kramer 与 Shaman 按提前时间评价逐预测峰值准确性 [2]，我们的十六个配置单元是另一种分母。对均值应用阈值，与对逐事件通过指示值取平均，在数学上不同，所以 4/16 不能改名为流行季成功概率。Bracher 等讨论预测分布校准 [18，第 4.2 节]，峰高误差小不等于已校准。估计事件成功率需保留逐事件结果、定义事件分母并处理依赖。
+p128 向导师简答。 这里数的是平均后的配置，而非成功流行季或经校准概率 [2, 18]。
+p129 论文位置。 Kramer and Shaman [2], Forecast accuracy and comparison / Fig. 2; Bracher et al. [18], §4.2.
+p130 证据。 BENCH_PTE_PIE_BY_STEP.csv; Kramer–Shaman [2]; analysis peak detector settings
+p131 F1 结论。 NLinear 与 MIFlu 各通过 4/16 个聚合单元，PatchTST 为 0/16。NLinear 的平均 PIE 更低（9.477%，MIFlu 为 26.846%），但平均 PTE 更高（1.677 周，MIFlu 为 1.128 周）。这是时间与幅度的取舍，不是全面优越。前三模型的排序在两端倒置：MSE 顺序为 MIFlu、PatchTST、NLinear，PIE 顺序为 NLinear、MIFlu、PatchTST。
+p133 28 个保留模型的峰值误差热图。每格展示固定提前步上跨跨度的均值。均值层面的框选不能理解为每个跨度均通过，逐跨度通过情况见详细网格。来源：BENCH_PTE_PIE_BY_STEP.csv。
+p134 MSE 与 PIE 正秩相关（+0.736）意味着 MSE 较低时 PIE 通常也较低。MSE 与通过数负相关（−0.429）方向同样符合预期：误差较低通常伴随更多通过。两者都不能证明脱钩。NLinear 的 MSE 第三、PIE 第一，说明局部目标排序不一致。
+p135 Q14 为什么峰值排名会改变，却不能说已经证明脱钩？
+p136 直接回答与本地证据。 前三模型的 MSE 顺序为 MIFlu < PatchTST < NLinear，PIE 顺序为 NLinear < MIFlu < PatchTST。排序在两端倒置，中间位置也不同。跨全部模型，MSE–PIE 为正相关（+0.736），MSE–通过数为负相关（−0.429），都符合整体误差越低通常峰值表现越好的方向。局部排名不一致可以与整体相关同时存在。因此可主张评价目标改变排序，不能主张统计独立或所有模型都无法预测峰值。
+p137 文献依据与选择理由。 Zeng 等说明 NLinear 先减最后一个值，经过线性映射，再加回该值 [4]。这提供水平处理的可检验假设，却非本地峰值成因的证明。排名差别有更直接的区别：MSE 聚合许多点和七通道，PIE 聚焦 ILITOTAL 检测峰高 [21 提供误差指标背景]。模型可能改善非峰点却使该端点较差。若要归因于架构，须有受控变体和峰值/残差诊断。
+p138 向导师简答。 两种目标聚合不同误差，NLinear 水平校正是待检验的假设 [4, 21]。
+p139 论文位置。 Zeng et al. [4], §4 NLinear; Hyndman and Koehler [21], §2.1.
+p140 证据。 BENCH_MSE_BY_MODEL_L.csv joined to BENCH_PTE_PIE_BY_STEP.csv; audit/verified_facts.json
+p141 6 精度与参数量
+p142 表 8. 参数分析与秩相关
+p143 帕累托分析只纳入有参数量导出的 11 个模型，未包括 MIFlu 与冻结编码器。缺失参数量不等于零。参数量不等于延迟、内存或能耗。相关系数只是同一测试集上跨模型的描述性结果。
+p144 Q15 我该怎样向导师解释 Pareto 图？
+p145 直接回答与本地证据。 横轴是参数量，纵轴是 MSE，两者均偏向越小越好。如果子集中另一个模型的参数不更多、MSE 不更高，且至少一项严格更好，前者就受到支配。导出的前沿包含 NLinear 和 PatchTST：NLinear 更小，PatchTST 的 MSE 更低，因此互不支配。这个前沿只覆盖有参数导出的 11 个模型，MIFlu 与冻结编码器不在其中，不能称为全部模型的全局前沿。
+p146 文献依据与选择理由。 iTransformer 同时评价误差、速度和内存 [5，附录 D]，是把表现与代价并列考虑的先例。我们的代价轴更窄，只用导出参数。两个前沿成员来自十一模型子集的两两支配关系，并非论文推荐的通用赢家。Pareto 图排除被支配选择；余下选择仍需预算或可接受误差偏好。MIFlu 代价缺失，使它不能称为全部 28 模型前沿。
+p147 向导师简答。 前沿排除所测子集内的被支配选择，仍需决策偏好从中选模 [5]。
+p148 论文位置。 iTransformer [5], Appendix D Model Efficiency; local BENCH_EFFICIENCY.csv.
+p149 证据。 BENCH_EFFICIENCY.csv; fig_pareto_frontier.png
+p150 Q16 参数多 211 倍，是否就慢 211 倍？
+p151 直接回答与本地证据。 不是。531,878 / 2,520 = 211.1 比较的是导出的 PatchTST 与 NLinear 参数量。其观测 MSE 降幅为 (1.871583 − 1.662078) / 1.871583 ≈ 11.2%。参数存储、运算、硬件利用率及批量大小对运行时间有不同影响。延迟、峰值内存与能耗需要直接且可比的测量。因此使用“参数效率”这个表述；缺失参数继续记为缺失，不能当成零，更不能把 MIFlu 描述成无参数模型。
+p152 文献依据与选择理由。 iTransformer 在声明的输入/预测长度和统一批量下实测速度、内存 [5，附录 D]，我们的参数导出没有这些测量。参数影响存储，运算、词元数量与硬件利用率对耗时影响不同。因此参数多 211×，不能推出延迟、内存或能耗也多 211×。后续效率表应记录硬件、精度、批量，以及计时针对训练还是推理，不能用参数比猜这些字段。
+p153 向导师简答。 我报告的是参数比；文献展示了速度主张所需的匹配运行测量 [5]。
+p154 论文位置。 iTransformer [5], Appendix D, Fig. 10, matched speed/memory measurements.
+p155 证据。 BENCH_EFFICIENCY.csv; BENCH_MSE_BY_MODEL_L.csv model in {nlinear,patchtst}
+p156 Q17 R² = 0.0223 实际说明什么？
+p157 直接回答与本地证据。 在有参数导出的 11 个模型中，以 MSE 对 log10(参数量) 拟合，参数规模单独解释的观测变化很少。这种描述性关联没有隔离容量作用，因为架构、优化与训练设置也同时不同。较低 R² 不能证明容量不重要，更不能证明观测精度增益只是随机噪声。若要研究容量因果作用，需要在受控模型家族及训练协议内改变规模。
+p158 文献依据与选择理由。 PatchTST 改变层数和隐藏维度，并特别指出 ILI 对这些设置敏感 [3，附录 A.6.2]，这反对轻率否定小流感序列上的调参。我们的跨模型 R² 混合架构、优化和规模，不是受控容量作用。更强的后续是在一个家族内改变深度/宽度，固定训练协议并重复运行。MIFlu 深度阶梯开始提出这个问题，但未聚合状态不能提供科学趋势。
+p159 向导师简答。 跨模型 R² 低不能否定调参；PatchTST 明确报告 ILI 敏感性 [3]。
+p160 论文位置。 PatchTST [3], Appendix A.6.2, Fig. 5, layers/width and ILI sensitivity.
+p161 证据。 BENCH_EFFICIENCY.csv; scripts/verify_snapshot.py linregress
+p162 F2 结论。 在导出参数量的 11 个模型中，拟合斜率为 +0.1171，R² 为 0.0223。规模单独解释的观测 MSE 变化很少。该子集结果不能证明容量无关紧要。
+p164 11 个导出参数量模型的精度与参数取舍。此子集未包括 MIFlu 与冻结编码器。参数量不是实测运行时间或内存代价。来源：BENCH_EFFICIENCY.csv。
+p165 7 统计审计
+p166 源表有 17 个模型的 136 对，另外 11 个模型不在其中，因此并非 28 模型的全配对分析。Holm 在原始 p 值排序后取前向累计最大值；源代码却取反向累计最小值。n=12 时双侧精确检验下限 2/4096 乘 136 已超过 0.05，因此正确 Holm 校正下该检验族不可能拒绝任何原假设。重复目标及跨度也使单元相关。原始 p 值及未校正 bootstrap 区间只作探索性参考。
+p167 表 9. 使用正确 Holm 校正的配对比较
+p168 136 对来自 17 个模型，并未覆盖全部 28 个模型。n = 12 个配对跨度 × 种子单元。前向累计最大值 Holm 得到 0/136 个拒绝。所示 p 值由六位小数导出恢复 1/4096 枚举网格；直接从四舍五入导出重算时，NLinear–PatchTST 为 0.117180，而非 0.1171875。*源效应量采用模型合并标准差，不是配对差的标准差。单元相关性限制统计推断。
+p169 Q18 为什么配对检验表里会出现看起来不相关的模型对？
+p170 直接回答与本地证据。 报告有意把 NLinear–PatchTST 这对前沿比较放在第一行，再列原始 p 最小的六行，这样既展示核心问题，也展示更大检验族中的例子。该前沿对在导出表按原始 p 升序排列时位于第 117，因此自动只取最小六项会漏掉它。但完整检验族仍含全部 136 对；选择展示哪几行，不能改变 Holm 校正的检验族，更不能让选中比较变显著。
+p171 文献依据与选择理由。 Demšar 说明考查特定差异时须控制比较族 [20]。这里首行保留前沿核心问题，后六行展示原始 p 更小的对照，校正仍纳入全部 136 对。第 117 指原始 p 升序位置，不是模型精度排名。选择展示行不能改变检验族。该文主要讨论多数据集，也不许可把本地重叠跨度和共享测试序列当成独立数据集。
+p172 向导师简答。 首行服务研究问题，校正仍由完整检验族决定 [20]。
+p173 论文位置。 Demšar [20], §3.2.2 Post-hoc tests; local raw-p rank.
+p174 证据。 BENCH_PAIRED_TESTS.csv model_a=nlinear/model_b=patchtst; audit/verified_facts.json pair_raw_rank
+p175 Q19 为什么未校正有 128 对显著，Holm 后却是零？
+p176 直接回答与本地证据。 同时检验很多模型对会增加误报机会。正确 Holm 先排列原始 p，再按递减多重比较因子计算并取前向累计最大值。原导出列方向错误，因此保留作来源记录但不使用。重算全部 136 对后为 0/136 个拒绝，最小校正 p 约 0.0664，NLinear–PatchTST 为 0.1172。在已记录的双侧精确 n=12 分辨率下，原始 p 最低为 2/4096，已高于 Holm 第一步的 0.05/136 阈值。跨度–种子单元之间的依赖还带来另一层限制。
+p177 文献依据与选择理由。 Demšar 说明 Holm 从最小 p 开始，在首次未通过阈值处停止 [20]。本项目第一阈值为 0.05/136；按已记录的十二贡献双侧符号翻转下限 2/2^12，乘 136 得 0.06640625，所以无法启动拒绝序列。这是本地数学推导，不是 Demšar 报告的流感结果。Holm 可处理有效 p 值之间的依赖，却不能修复因配对内部交换性不合理而无效的原始 p；两者是不同限制。
+p178 向导师简答。 精确检验下限超过 Holm 第一步阈值，这是设计分辨率限制 [20]。
+p179 论文位置。 Demšar [20], §3.2.2 Holm step-down; local exact-enumeration derivation.
+p180 证据。 BENCH_PAIRED_TESTS.csv p_raw; analysis_postprocess.py; audit/HOLM_RECOMPUTATION.csv
+p181 Q20 p = 0.1172 是否说明 NLinear 与 PatchTST 等价？
+p182 直接回答与本地证据。 不是。PatchTST 的观测平均 MSE 仍低 11.2%，且在 10/12 个配对单元中误差更低。未拒绝只表示该检验族校正流程没有在选定阈值下确立差异，不表示差异已小到可视为实际等价。等价判断需要预先规定可接受差异界值，并采用适合的不确定性与检验设计。表中源效应量还使用模型合并标准差，而非配对差标准差，因此只能标成源标准化效应。
+p183 文献依据与选择理由。 Lakens 区分不显著差异检验与预先规定有意义界限的等价检验 [25]。因此 p = 0.1172 没回答 NLinear 额外观测误差是否可接受。应先定义可接受差异，再采用尊重时间/季节依赖的不确定性设计。看表后才挑宽松界限，不能构成有说服力的确认。在此之前应并列报告观测降幅、参数比和推断不确定性，不能说额外参数只换来噪声。
+p184 向导师简答。 未拒绝不等于等价，观测取舍与尚未解决的推断并存 [25]。
+p185 论文位置。 Lakens [25], Introduction and Testing for Equivalence.
+p186 证据。 BENCH_EFFICIENCY.csv; BENCH_PAIRED_TESTS.csv; audit/CLAIM_AUDIT.md C3
+p187 F3 结论。 正确 Holm 校正为 0/136 个拒绝（校正前 128/136），最小校正 p 约 0.0664，NLinear–PatchTST 的 p ≈ 0.1172。PatchTST 的观测 MSE 仍低 11.2%，参数多 211 倍，并在 10/12 单元中误差更低。未拒绝不能证明等价，也不能断言增益是噪声。
+p188 8 冻结语言编码器
+p189 表 10. 冻结编码器加共享线性读出
+p190 11 个保留编码器 × 4 跨度 × 3 种子 = 132 单元。历史计划还包含两个仅嵌入模型，总计 156 单元；未纳入的 24 单元不属于 28 模型正式名单。此结果只评价该冻结特征流程。
+p191 Q21 冻结编码器的负面结果能解释到哪一步？
+p192 直接回答与本地证据。 所测流程冻结语言编码器，再训练线性读出。11 个编码器的 MSE 为 4.7374–5.2049，均高于决策树的 4.3198，各自通过 0/16 联合单元。这说明这些特征与读出配置在当前协议中表现较差。分布不匹配、冻结特征和读出能力都可能解释结果，但实验没有分离其作用。生成、提示、微调及数值预训练时序基础模型均不属于这项测试。
+p193 文献依据与选择理由。 Time-LLM 也冻结 LLM，却加入可学习重编程和提示前缀 [6]，所以“冻结”不等同于本项目特征/线性读出流程。Chronos 则从数值序列学习预测 [9]。这些方法差异支持缩小负面结论。要分离读出瓶颈，应固定编码器后改变读出/对齐；要分离预训练作用，应比较匹配的预训练和随机骨干。十一模型结果没有完成这些受控分离。
+p194 向导师简答。 失败限定本地特征/读出流程，Time-LLM 与 Chronos 检验其他机制 [6, 9]。
+p195 论文位置。 Time-LLM [6], author abstract; Chronos [9], §3.
+p196 证据。 BENCH_MSE_BY_MODEL_L.csv family=llm_encoder; BENCH_PTE_PIE_BY_STEP.csv
+p197 F4 结论。 所测 11 个冻结编码器的 MSE 为 4.7374–5.2049，是 MIFlu 的 3.04–3.34 倍，全部高于决策树的 4.3198，且均通过 0/16 单元。这是该特征与读出配置的负面结果；提示、微调及数值时序基础模型仍未检验。
+p198 分布差异、冻结容量和所选读出均可能影响结果，但本结果未分离其因果作用。线性读出不能保证提取可用的非线性特征。
+p199 9 消融设计与状态
+p200 表 11. 消融设计与快照状态
+p201 用户报告截至 2026 年 11 月 3 日：新增 60 单元中完成 27，作业 722968。本次未连接 HPC，也无逐变体结果导出。参考 12 单元不计入新增 60 单元。不推断趋势。
+p202 F5 暂定结论。 miflu_model.py 的 author_faithful 路径将文本置于时间词元之后，使用因果注意力，预测头只读取时间词元。静态检查因此推断确定性评估时文本不影响输出。所附 tests_archive/test_miflu_ablations.py 明确断言文本不变性，以及匹配 CPU 初始化时完整与无文本模型相同。本次仅静态检查，未执行。其他融合路径及训练随机性须分别验证。
+p203 Q22 为什么默认路径下去掉文本可能得到完全相同的输出？
+p204 直接回答与本地证据。 已检查的 author_faithful 路径把时间词元放在文本词元前。因果注意力只允许每个位置读取自身或更早位置，预测头又只读取时间词元位置。因此在确定性评估前向过程中，这些位置无法利用后面的文本。所附归档明确断言文本不变性，以及匹配初始化的完整/无文本 CPU 输出相同，但本次没有执行这些模型测试。其他融合路径、dropout 和独立训练轨迹仍需分别检查。精确文件与命令见 audit/NO_TEXT_VERIFICATION.md。
+p205 文献依据与选择理由。 Transformer 原文说明遮罩如何阻止关注后续位置 [24，第 3.1 节]。按已检查顺序，时间位置不能通过这些层取得后方文本，预测头又只读时间位置。这是固定前向路径的结构论证，不是仓库运行或逐位相等认证。三项归档断言须控制权重、输入和评估随机性，再比较更换文本及匹配完整/无文本输出，当前仍未执行。独立训练可能不同地消耗随机数，须另测。
+p206 向导师简答。 因果遮罩支持结构论证，本地逐位相等须由受控运行测试建立 [24]。
+p207 论文位置。 Vaswani et al. [24], §3.1 Decoder; local ForecastingLLM.forward and archived assertions.
+p208 证据。 miflu_model.py ForecastingLLM; tests_archive/test_miflu_ablations.py; audit/NO_TEXT_VERIFICATION.md
+p209 Q23 消融完成 27/60，究竟可以说什么？
+p210 直接回答与本地证据。 这是截至 11 月 3 日用户报告的运行状态快照，不是实时调度器查询，也不是已聚合的模型比较。新增设计有五个变体，每个四跨度、三种子，合计 60 单元；参考模型另有 12 单元。没有逐变体结果导出，就不能从完成数量推断深度趋势或 LoRA 收益。存在 no-text 测试断言，也不代表已完成相应消融实验。报告科学结果前，需要逐运行输出、状态及来源。
+p211 文献依据与选择理由。 Tan 等保留周边可训练预测器，移除或替换 LLM [13，第 3.2 节]，以检验骨干是否额外贡献信息。本地 no-LoRA/深度变体只回答较窄的适配/容量问题，不会自动回答同样的移除/替换问题，也不能分离文本使用。部分完成是操作状态；解释科学趋势需各报告变体分数、重复运行波动及匹配协议。文献提供实验问题，不提供本地未完成阶梯的结果。
+p212 向导师简答。 文献支持移除/替换对照，未完成阶梯尚未回答这些因果问题 [13]。
+p213 论文位置。 Tan et al. [13], §3.2 Proposed Ablations, w/o LLM / LLM2Attn / LLM2Trsf.
+p214 证据。 Owner snapshot; ablation design table; tests_archive/test_miflu_ablations.py
+p215 10 解释与发表计划
+p216 单一全国序列与单次时序划分不能证明区域或前瞻效用。峰值匹配可使用未来观测定义事件，只能作为回顾性评测工具。合成日期标签必须与 CDC 日历核实映射后才能作逐季判断。参数导出缺少 MIFlu 与编码器。27/60 的消融状态来自用户报告，而非实时集群检查。现代数值基础模型、区域结果、滚动原点及经过验证的不确定性仍缺失。
+p217 后续验证的决策规则：在查看新测试期之前确定 MSE 预算 B、允许峰值失败率 q 与决策代价。在验证季同时满足 B 与 q 的模型中最小化期望决策代价，再以参数量打破平局。对升级响应 / 等待决策，误报代价为 c_FP，漏报代价为 c_FN，正确行动代价为零；仅当经过验证的高峰概率超过 c_FP/(c_FP+c_FN) 时升级。代价、B、q 尚未征询或验证，因此没有模型被认证可部署。NLinear 是低成本峰高验证候选，MIFlu 仍为观测 MSE 最优。
+p218 建议 O1：保留实证评估贡献，先补齐证据，再考虑新增机制。当前草稿面向 IEEE JBHI 的健康预测主题，但尚未达到投稿状态。在学校截止日前，滚动原点、区域验证、更强基线与独立代码来源比再加一个架构更重要。
+p219 Q24 除了复现，本项目增加了什么，为什么默认仍选 O1？
+p220 直接回答与本地证据。 本项目在明确不同子集的前提下，从精度、峰值技巧、参数效率和统计证据四个维度比较实现。本次没有核实参考论文是否只有前两项，因此不能断言原文缺失某项或声称首次发现。O1 通过补齐来源、恢复测试、滚动原点、区域和更强对照来发展实证贡献。可选 O2 是只在验证数据拟合的峰高再校准：若已有可审计的验证/测试预测，可不新增 GPU 训练。但本快照尚未确立这些验证导出；CPU 时间和费用未测量，几个工作日也仅为规划估计。
+p221 文献依据与选择理由。 简单线性及移除 LLM 的批评早已存在 [4, 13]，Qiu 等预印本又在更大跨数据集设置报告条件式收益 [14]。本地较窄贡献连接经审计流感精度、峰值端点、代价子集和正确推断。O1 检查跨原点/区域是否保持，Tashman 支持滚动原点评测 [23]。O2 仅在预测导出合适时加入验证集拟合峰高调整；新增机制不能替代检查，也不能确立对所有 LLM 的判决。
+p222 向导师简答。 O1 检验流感特定发现；已有负面和条件式正面证据，不支持通用结论 [4, 13, 14]。
+p223 论文位置。 Zeng et al. [4], §4; Tan et al. [13], §3.2; Qiu et al. [14], abstract and §§3–5 (preprint); Tashman [23], publisher-indexed abstract.
+p224 证据。 audit/INNOVATION_DECISION.md; audit/LITERATURE_REVIEW.md; sources.json [1]
+p225 11 可复现性与待核实项
+p226 在仓库根目录运行 python scripts/verify_snapshot.py --raw-smoke 及 python -m pytest tests/test_snapshot_audit.py -q。审计重算主要聚合值、峰值标记、相关系数、回归、Holm 校正和一个原始预测 MSE。七个新增 CPU 审计测试已通过，它们与归档模型测试分开。修正 ZIP 已提供 tests_archive/，但历史目录布局及模型依赖缺失导致收集失败。本次不主张归档测试通过数或可靠总数。本次未重跑训练、未查询实时 HPC，亦未运行上游代码。原 CSV 保持不变，Holm 修正另行导出。
+p227 硬件来源表共 204 行，其中包括被排除的 DLinear，但没有 MIFlu 与冻结编码器；与正式名单重叠的是 192 单元。因此不能证明逐单元硬件来源已齐。原 reproduce_all.py 面向历史路径，并非此次核实的快速入口。
+p228 待核实项：固定上游版本的检查点、加载器与学习率；归档测试执行与 no-text 运行测试；十种子原始复现日志；模型版本与许可；实时消融及区域状态；真实 CDC 日历映射；当前 JBHI 作者限制、JCR 记录及下一轮会议日期。每项都需原始证据，不能靠文字断言补足。
+p229 Q25 导师现在能复核什么，还有什么未执行？
+p230 直接回答与本地证据。 文档中的 CPU 命令可以重算 CSV 主要聚合、正确 Holm 和一个原始预测单元的 MSE；七个新增 CPU 审计检查已通过。历史归档已经提供，但收集失败，不能把其中模型断言算作通过。完整 GPU 训练、全运行原始重评分、实时 HPC、固定上游身份和 no-text 运行测试仍未执行或未核实，硬件来源也未完整覆盖正式单元。文档排版完善不能补足这些证据。精确后续命令见 audit/EXECUTION_STATUS.md 与 audit/NO_TEXT_VERIFICATION.md。
+p231 文献依据与选择理由。 Kapoor 与 Narayanan 要求明确报告论证，而非把代码可用等同于结果有效 [22]。这里应分开文档重建、CSV 算术、原始预测重评分与模型重训。导师可先运行 CSV 审计；完整包还支持一个原始单元 smoke 检查。模型文本不变性需在固定环境实际执行三项指定断言，且不能跳过。有用的交付是可追溯证据链、精确命令与状态，某一层通过不能认证其他所有层。
+p232 向导师简答。 我区分重算结果与静态检查，并为每层提供命令和状态 [22]。
+p233 论文位置。 Kapoor and Narayanan [22], model info sheets; EXECUTION_STATUS.md and NO_TEXT_VERIFICATION.md.
+p234 证据。 audit/EXECUTION_STATUS.md; audit/NO_TEXT_VERIFICATION.md; audit/REPO_AUDIT.md
+p235 12 参考文献
+p236 [1] Jaeuk Moon 等，基于大语言模型的多模态流感预测方案（中文译名），2025。https://doi.org/10.1109/JBHI.2025.3561214
+p237 [2] Sarah C. Kramer 等，针对温带及热带六十四国的流感预测开发与验证（中文译名），2019。https://doi.org/10.1371/journal.pcbi.1006742
+p238 [3] Yuqi Nie 等，一个时间序列相当于六十四个词的长期预测方法（中文译名），2023。https://arxiv.org/abs/2211.14730
+p239 [4] Ailing Zeng 等，Transformer 是否适用于时间序列预测（中文译名），2023。https://arxiv.org/abs/2205.13504
+p240 [5] Yong Liu et al. 等，反转维度的 Transformer 时间序列预测（中文译名），2024。https://arxiv.org/abs/2310.06625
+p241 [6] Ming Jin et al. 等，通过重编程大语言模型进行时间序列预测（中文译名），2024。https://arxiv.org/abs/2310.01728
+p242 [7] Peiyuan Liu et al. 等，通过跨模态微调对齐语言模型与时间序列（中文译名），2024。https://arxiv.org/abs/2403.07300
+p243 [8] Chenxi Liu et al. 等，通过跨模态对齐增强多变量时间序列预测（中文译名），2025。https://arxiv.org/abs/2406.01638
+p244 [9] Abdul Fatir Ansari et al. 等，学习时间序列语言的 Chronos 方法（中文译名），2024。https://arxiv.org/abs/2403.07815
+p245 [10] Abhimanyu Das 等，仅解码器时间序列预测基础模型（中文译名），2024。https://proceedings.mlr.press/v235/das24c.html
+p246 [11] Gerald Woo et al. 等，通用时间序列预测 Transformer 的统一训练（中文译名），2024。https://proceedings.mlr.press/v235/woo24a.html
+p247 [12] Kashif Rasul et al. 等，面向概率时间序列预测基础模型的 Lag Llama（中文译名），2024。https://arxiv.org/abs/2310.08278
+p248 [13] Mingtian Tan 等，语言模型真的有助于时间序列预测吗（中文译名），2024。https://arxiv.org/abs/2406.16964
+p249 [14] Xin Qiu et al. 等，重新思考大语言模型在时间序列预测中的作用（中文译名），2026。https://arxiv.org/abs/2602.14744
+p250 [15] Chen Xu 等，动态时间序列的共形预测区间（中文译名），2021。https://proceedings.mlr.press/v139/xu21h.html
+p251 [16] Chen Xu 等，时间序列的顺序预测共形推断（中文译名），2023。https://proceedings.mlr.press/v202/xu23r.html
+p252 [17] Isaac Gibbs 等，分布偏移下的自适应共形推断（中文译名），2021。https://arxiv.org/abs/2106.00170
+p253 [18] Johannes Bracher 等，以区间格式评估传染病预测（中文译名），2021。https://doi.org/10.1371/journal.pcbi.1008618
+p254 [19] Xavier Bouthillier et al. 等，Accounting for Variance in Machine Learning Benchmarks（英文原题），2021。https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf
+p255 [20] Janez Demšar 等，Statistical Comparisons of Classifiers over Multiple Data Sets（英文原题），2006。https://jmlr.org/papers/volume7/demsar06a/demsar06a.pdf
+p256 [21] Rob J. Hyndman 等，Another look at measures of forecast accuracy（英文原题），2006。https://doi.org/10.1016/j.ijforecast.2006.03.001
+p257 [22] Sayash Kapoor 等，Leakage and the reproducibility crisis in machine-learning-based science（英文原题），2023。https://doi.org/10.1016/j.patter.2023.100804
+p258 [23] Leonard J. Tashman 等，Out-of-sample tests of forecasting accuracy: an analysis and review（英文原题），2000。https://doi.org/10.1016/S0169-2070(00)00065-0
+p259 [24] Ashish Vaswani et al. 等，Attention Is All You Need（英文原题），2017。https://papers.neurips.cc/paper/7181-attention-is-all-you-need.pdf
+p260 [25] Daniël Lakens 等，Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses（英文原题），2017。https://doi.org/10.1177/1948550617697177
+table1/row1 作者 | CHAN Sing Yeung
+table1/row2 快照 | 3 November 2026
+table1/row3 阅读说明 | 四个评价维度，附 Q01–Q25 导师交流问答
+table2/row1 项目 | 数值
+table2/row2 行数与通道 | 966 × 7
+table2/row3 时序划分 | 676 / 97 / 193
+table2/row4 训练 / 验证 / 测试下标 | 0–675 / 676–772 / 773–965
+table2/row5 历史与跨度 | T=104; L=24/36/48/60
+table2/row6 可用 / 计分窗口 | 170/160; 158/144; 146/144; 134/128
+table2/row7 ILITOTAL 训练均值 / 标准差 | 9,439.84 / 9,003.15
+table2/row8 本地数值一致性 | 最大绝对差 = 0
+table3/row1 项目 | 复现 | 基准
+table3/row2 种子 | 2021–2030 (10) | 42/43/44 (3)
+table3/row3 模型 | MIFlu | 13 传统 + 4 基于 LLM + 11 冻结编码器
+table3/row4 选择 | 验证集检查点 | 验证集检查点
+table3/row5 指标 | 7-variable z-space MSE / MAE | 7-variable MSE / MAE; ILITOTAL PTE / PIE
+table3/row6 窗口 | 160 / 144 / 144 / 128 | 160 / 144 / 144 / 128
+table4/row1 跨度 | 本文 MSE ± 标准差 | 原文 MSE | Δ MSE | 本文 MAE | 原文 MAE | Δ MAE
+table4/row2 L=24 | 1.3045 ± 0.0883 | 1.5420 | -15.4% | 0.7482 | 0.7260 | +3.1%
+table4/row3 L=36 | 1.3561 ± 0.1603 | 1.4220 | -4.6% | 0.7712 | 0.7790 | -1.0%
+table4/row4 L=48 | 1.6543 ± 0.1064 | 1.4140 | +17.0% | 0.8381 | 0.7570 | +10.7%
+table4/row5 L=60 | 1.6829 ± 0.2109 | 1.3640 | +23.4% | 0.8596 | 0.7190 | +19.6%
+table4/row6 四跨度均值 | 1.4995 | 1.4355 | +4.5% | 0.8043 | 0.7452 | +7.9%
+table5/row1 Seed | L24 | L36 | L48 | L60
+table5/row2 2021 | 1.240157 | 1.314358 | 1.482299 | 1.599641
+table5/row3 2022 | 1.201078 | 1.306645 | 1.711215 | 1.664878
+table5/row4 2023 | 1.284212 | 1.269466 | 1.663857 | 1.821282
+table5/row5 2024 | 1.259462 | 1.154099 | 1.879495 | 1.915250
+table5/row6 2025 | 1.464643 | 1.767328 | 1.723161 | 1.410785
+table5/row7 2026 | 1.368497 | 1.312511 | 1.620327 | 1.984315
+table5/row8 2027 | 1.392309 | 1.400796 | 1.628296 | 1.614602
+table5/row9 2028 | 1.230425 | 1.302717 | 1.588157 | 1.401814
+table5/row10 2029 | 1.231536 | 1.404061 | 1.570881 | 1.520661
+table5/row11 2030 | 1.373057 | 1.328807 | 1.675020 | 1.895393
+table6/row1 # | 模型 | L24 | L36 | L48 | L60 | 平均 MSE | 平均 MAE
+table6/row2 1 | MIFlu | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199
+table6/row3 2 | PatchTST | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786
+table6/row4 3 | NLinear | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183
+table6/row5 4 | DNN | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057
+table6/row6 5 | TimeCMA | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676
+table6/row7 6 | Gradient Boosting | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521
+table6/row8 7 | KNN | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293
+table6/row9 8 | Random Forest | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779
+table6/row10 9 | iTransformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476
+table6/row11 10 | Decision Tree | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798
+table6/row12 11 | Hunyuan-1.8B | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755
+table6/row13 12 | Hunyuan-7B | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685
+table6/row14 13 | DeepSeek-R1-Qwen-1.5B | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002
+table6/row15 14 | DeepSeek-R1-Llama-8B | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786
+table6/row16 15 | GRU | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174
+table6/row17 16 | DeepSeek-R1-32B | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935
+table6/row18 17 | LSTM | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303
+table6/row19 18 | DeepSeek-R1-Qwen-14B | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019
+table6/row20 19 | DeepSeek-R1-Qwen-7B | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133
+table6/row21 20 | RNN | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634
+table6/row22 21 | ContextPilot-8B | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255
+table6/row23 22 | Hunyuan-4B | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450
+table6/row24 23 | ContextPilot-14B | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407
+table6/row25 24 | Qwen2.5-1.5B | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725
+table6/row26 25 | Qwen-Time | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794
+table6/row27 26 | SVR | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986
+table6/row28 27 | CALF | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190
+table6/row29 28 | CNN | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720
+table7/row1 模型 | PTE (wk) | PIE (%) | 联合通过 | s0 PTE | s0 PIE (%)
+table7/row2 MIFlu | 1.128 | 26.846 | 4/16 | 0.347 | 18.884
+table7/row3 PatchTST | 1.240 | 32.755 | 0/16 | 0.681 | 30.553
+table7/row4 NLinear | 1.677 | 9.477 | 4/16 | 0.208 | 3.250
+table8/row1 模型 | L | s0 | s1 | s2 | s3
+table8/row2 NLinear | 24 | PASS 0.111 / 3.949 | fail 1.333 / 8.411 | fail 2.333 / 11.943 | fail 2.667 / 18.739
+table8/row3 NLinear | 36 | PASS 0.333 / 4.181 | fail 1.333 / 7.222 | fail 2.111 / 15.313 | fail 2.667 / 18.145
+table8/row4 NLinear | 48 | PASS 0.222 / 2.419 | fail 1.222 / 4.727 | fail 2.222 / 9.979 | fail 2.778 / 16.655
+table8/row5 NLinear | 60 | PASS 0.167 / 2.450 | fail 1.444 / 4.542 | fail 2.556 / 9.952 | fail 3.333 / 13.000
+table8/row6 MIFlu | 24 | PASS 0.000 / 18.307 | fail 0.889 / 26.686 | fail 1.222 / 30.472 | fail 1.333 / 31.638
+table8/row7 MIFlu | 36 | PASS 0.000 / 18.695 | fail 0.778 / 26.333 | fail 1.667 / 31.514 | fail 1.333 / 32.427
+table8/row8 MIFlu | 48 | fail 1.222 / 18.004 | PASS 0.667 / 24.795 | fail 1.222 / 30.133 | fail 1.333 / 33.236
+table8/row9 MIFlu | 60 | PASS 0.167 / 20.530 | fail 1.333 / 25.799 | fail 2.222 / 29.790 | fail 2.667 / 31.177
+table8/row10 PatchTST | 24 | fail 0.667 / 30.580 | fail 1.000 / 34.044 | fail 1.222 / 33.572 | fail 1.222 / 30.722
+table8/row11 PatchTST | 36 | fail 1.000 / 26.235 | fail 1.667 / 32.247 | fail 1.333 / 31.245 | fail 1.333 / 33.854
+table8/row12 PatchTST | 48 | fail 0.556 / 30.360 | fail 1.333 / 30.878 | fail 0.889 / 35.158 | fail 0.889 / 35.002
+table8/row13 PatchTST | 60 | fail 0.500 / 35.035 | fail 1.667 / 34.342 | fail 2.222 / 35.674 | fail 2.333 / 35.133
+table9/row1 量 | 数值
+table9/row2 回归斜率 / R² | +0.1171 / 0.0223
+table9/row3 有参数量导出的模型 | 11
+table9/row4 子集帕累托集合 | NLinear 2,520; PatchTST 531,878
+table9/row5 参数比 | 211.1×
+table9/row6 描述性 MSE 降幅 | 11.2%
+table9/row7 ρ(MSE, PIE) | +0.736 (p < 0.0001)
+table9/row8 ρ(MSE, 通过数) | -0.429 (p = 0.023)
+table10/row1 模型 A | 模型 B | Δ MSE | p raw | p Holm | 效应*
+table10/row2 NLinear | PatchTST | +0.2095 | 0.005859 | 0.1172 | 1.15
+table10/row3 Gradient Boosting | RNN | -1.4029 | 0.000488 | 0.0664 | 4.86
+table10/row4 KNN | NLinear | +1.9138 | 0.000488 | 0.0664 | 22.29
+table10/row5 KNN | MIFlu | +2.2280 | 0.000488 | 0.0664 | 9.89
+table10/row6 KNN | LSTM | -1.2234 | 0.000488 | 0.0664 | 5.28
+table10/row7 iTransformer | TimeCMA | +1.3863 | 0.000488 | 0.0664 | 7.02
+table10/row8 iTransformer | SVR | -1.3443 | 0.000488 | 0.0664 | 10.61
+table11/row1 编码器 | MSE | 相对 MIFlu | PTE | PIE (%) | 通过
+table11/row2 Hunyuan-1.8B | 4.7374 | 3.04× | 4.406 | 71.428 | 0/16
+table11/row3 Hunyuan-7B | 4.7596 | 3.06× | 5.309 | 75.399 | 0/16
+table11/row4 DeepSeek-R1-Qwen-1.5B | 4.7866 | 3.07× | 5.792 | 78.061 | 0/16
+table11/row5 DeepSeek-R1-Llama-8B | 4.8250 | 3.10× | 4.306 | 77.121 | 0/16
+table11/row6 DeepSeek-R1-32B | 4.9372 | 3.17× | 3.889 | 77.730 | 0/16
+table11/row7 DeepSeek-R1-Qwen-14B | 5.0166 | 3.22× | 4.149 | 76.350 | 0/16
+table11/row8 DeepSeek-R1-Qwen-7B | 5.0308 | 3.23× | 4.458 | 76.373 | 0/16
+table11/row9 ContextPilot-8B | 5.0843 | 3.26× | 4.962 | 78.918 | 0/16
+table11/row10 Hunyuan-4B | 5.1317 | 3.30× | 3.003 | 78.840 | 0/16
+table11/row11 ContextPilot-14B | 5.1949 | 3.34× | 4.965 | 77.764 | 0/16
+table11/row12 Qwen2.5-1.5B | 5.2049 | 3.34× | 5.333 | 74.650 | 0/16
+table12/row1 变体 | 参数 | 单元 | 状态
+table12/row2 参考 K=6 | default | 12 | 已在基准中
+table12/row3 no_lora | --no-lora | 12 | 尚未聚合
+table12/row4 K=2 | --num-layers 2 | 12 | 尚未聚合
+table12/row5 K=4 | --num-layers 4 | 12 | 尚未聚合
+table12/row6 K=8 | --num-layers 8 | 12 | 尚未聚合
+table12/row7 K=12 | --num-layers 12 | 12 | 尚未聚合
--- progress_report_en corrected upload
+++ progress_report_en reviewed revision 4
@@ -1,170 +1,179 @@
-p0 SUBMISSION: FYP InfoNet, by 11:59 pm 20 November 2026
-p1 CITY UNIVERSITY OF HONG KONG
-p2 Department of Electrical Engineering   ·   FYP Progress Report, Semester A 2026/27
-p3 PART A
-p4 PART B
-p5 1. Project objectives
-p6 Problem statement. Influenza forecasting directly affects public-health resource allocation: when to escalate a response, how much capacity to prepare, and when to announce that a season has peaked. Moon et al. (IEEE JBHI 2025) proposed MIFlu, a multimodal model that pairs a GPT-2 time-series encoder with text embeddings, and reported the best accuracy on CDC national influenza data. The paper, however, compares against two simple baselines, reports a single random seed, and selects its checkpoint on the test set — data leakage. A public-health team therefore cannot answer the question that matters: is MIFlu the model we should deploy, and would we know if it were not?
-p7 Objectives.
-p8 1. Reproduce MIFlu's Table V under a rigorous protocol (10 seeds, validation-based checkpoint selection, 7-variable aggregate MSE) and quantify the gap against the published numbers, including its sign at each horizon.
-p9 2. Benchmark 28 forecasting models (13 conventional + 4 LLM-based, MIFlu and 3 published, + 11 frozen LLM encoders) on one protocol, scored on accuracy (MSE/MAE) and on peak-forecasting skill (PTE/PIE under the Kramer & Shaman criterion).
-p10 3. Determine which model a public-health team should deploy, and test empirically whether large language models improve epidemiological forecasting at all.
-p11 Scope. The project is an empirical evaluation, not a new architecture. Its contribution is the measurement: a leak-free protocol, a 28-arm matrix under one set of windows and seeds, and an evaluation that separates accuracy from deployment value. No new loss function or prompt mechanism is proposed, and none is needed for the claims that are made.
-p12 2. Original project planning chart
-p13 •  Sep 2026 (Weeks 1-4): data acquisition and verification (966-week CDC series, byte-level check). Milestone: dataset confirmed identical — done.
-p14 •  Oct 2026 (Weeks 5-8): MIFlu code reconstruction, reproduction runs (10 seeds x 4 horizons). Milestone: Table V reproduced with a disclosed sign crossover — done.
-p15 •  Nov 2026 (Weeks 9-12): 28-model benchmark and frozen-encoder axis; ablation ladder queued; progress report and presentation. Milestone: benchmark complete — benchmark done, ablation 27/60 and running.
-p16 •  Dec 2026 - Apr 2027: regional evaluation, rolling-origin evaluation, manuscript, submission. Milestone: submitted manuscript — planned.
-p17 The one schedule slip is the ablation ladder: it was planned for early November and is 27/60 at this report. It is a compute-queue delay, not a design change; the regional evaluation is gated behind it and has moved to late November.
-p18 3. Background study
-p19 Technical background. Influenza forecasting has moved from statistical models (ARIMA, Prophet) to deep learning (LSTM, Transformer) and recently to large language models. MIFlu represents the last group: it fine-tunes a GPT-2 backbone with LoRA adapters on the CDC series and reports the best aggregate accuracy. Its comparison set is thin and its protocol has two problems — test-set checkpoint selection and a single seed — which is exactly the space in which an independent reproduction and a wider benchmark become useful.
-p20 Contemporary and societal context. After COVID-19, governments invested heavily in AI-based epidemic forecasting, and agencies such as the WHO and CDC use forecasts to allocate vaccines and antivirals. A forecast is useful to those decisions only if its peak is placed and scaled correctly: a curve that is two weeks late on the peak, or 40 % low on its height, fails the decision even when its average error is small. Yet the literature ranks models by MSE. That gap between the metric and the decision is the problem this project measures.
-p21 Gap identified. Three things are missing from the current literature: (1) a reproduction of MIFlu that removes the test-set checkpoint leak; (2) a benchmark wide enough that the linear and classical baselines are represented; (3) an evaluation on the criterion public health actually applies, next to the criterion the literature reports. This project supplies all three.
-p22 4. Methodology
-p23 Design. Two protocols, never mixed. The reproduction protocol (10 seeds, 2021-2030; validation-selected checkpoint; 7-variable aggregate MSE) exists to compare with the paper's Table V. The benchmark protocol (3 seeds 42/43/44; shared windows (W//16)*16 = 160/144/144/128; one metric) exists to compare 28 models with each other. MIFlu is the only arm under both, and its two numbers are not comparable.
-p24 Table 1. Reproduction: ours vs original paper/repo.
-p25 Two [DEVIATION] items are required by top-tier journal standards.
-p26 Two deliberate deviations. (1) Checkpoint selection: the original code selects the best epoch on the test set (main_ILI_lora.py, lines 211 and 225), which is data leakage; we select on validation. (2) The 7-variable metric: the original test loader covers only 1 of 7 variables (a bug), while Table V is defined on the 7-variable aggregate; we fix the loader. Both are disclosed wherever a reproduction number appears.
-p27 Metrics and definitions. Horizon L = weeks predicted ahead (input window T = 104 weeks). Step s = which predicted week is scored (step 0 = one week ahead). PTE (peak timing error) = |predicted peak week - observed peak week| in weeks; PIE (peak intensity error) = |predicted - observed peak| / observed peak x 100 %. A cell passes the Kramer & Shaman criterion only if PTE <= 1 week and PIE <= 25 %; the thresholds are attributed to Kramer & Shaman (2019) and are marked [to verify] against the original text. The peak detector (find_peaks(prominence = 0.15 x range, distance = 15), ±8-week matching) is this project's engineering choice, not part of the published criterion. PTE/PIE use ILITOTAL de-normalised to patient counts, because the 7-variable aggregate is a loss, not a series, and cannot be de-normalised.
-p28 Design impact in a broader context. The evaluation is deliberately split into two questions that a deployment actually faces: how accurate is the curve (MSE) and can the forecast support a decision (PTE/PIE). Keeping them separate matters because they can rank models differently; a single leaderboard that collapses them would hide the choice. The benchmark is also built to be re-runnable: every cell records its GPU, partition, node and job id, so a public-health team can audit the numbers rather than trust them. That is a small contribution to reproducibility in a field where published forecasting results are rarely re-derived.
-p29 6. Progress
-p30 Work completed this semester.
-p31 •  Data verification: 966-week CDC series confirmed bit-identical to the author's file (SHA-256, max|diff| = 0); split 676/97/193 and the containment guard verified.
-p32 •  Code reconstruction: 17 fidelity fixes (RevIN, LayerNorm, three dropouts, drop_last, single-variable batch, seed, epsilon, and others), each recorded in the deviation ledger.
-p33 •  Reproduction: 40 runs (10 seeds x 4 horizons), every cell gated against the per-seed oracle at |Δ| <= 1e-5.
-p34 •  Benchmark: 28 models x 4 horizons x 3 seeds = 336 cells; 204 of them (the 17 conventional arms) carry recorded per-cell A100 provenance, and the 132 encoder cells ran on the same partition with per-cell manifests on the cluster.
-p35 •  Encoder axis: 11 frozen encoders x 12 cells = 132 cells, MSE and PTE/PIE aggregated.
-p36 •  Analysis: MSE/MAE, PTE/PIE, the Kramer & Shaman criterion, a Pareto frontier, a log-parameter regression, and 136 Holm-corrected paired tests.
-p37 •  Ablation ladder: designed, implemented behind flags, 27/60 cells complete at this report.
-p38 •  Documentation: six reports (DOCX + PDF, EN + ZH) generated from the CSVs with assertions.
-p39 Reproduction result (7-variable aggregate MSE, 10-seed mean):
-p40 Table 2. Reproduction of MIFlu's Table V — the sign crossover. 7-variable aggregate MSE in z-space, 10 repetitions, seeds 2021–2030.
-p41 A positive Δ means we are worse than the paper. We win L24 (−15.4 %) and L36 (−4.6 %) and lose L48 (+17.0 %) and L60 (+23.4 %); the 4-horizon mean is +4.5 % on MSE and +7.9 % on MAE. The only defensible claim is “reproduced within 4.5 % on the 4-horizon MSE mean, with a horizon-dependent sign” — never a claim of superiority over the original. Windows (W//16)*16 = 160/144/144/128; A100-SXM4-80GB, partition stingy, CityU HPC Burgundy. Source: ESSAY_VS_REPRODUCTION_TABLE_V.csv.
-p42 The paper reports 1.542 / 1.422 / 1.414 / 1.364 (mean 1.4355). We obtain 1.3045 / 1.3561 / 1.6543 / 1.6829 (mean 1.4995), i.e. 4.5 % worse on the mean, with a sign crossover 2-2: better at L=24 and L=36, worse at L=48 and L=60. The MAE side behaves the same way (0.8043 against 0.7452, +7.9 %).
-p43 Conclusion (reproduction). The reproduction is within 4.5 % on the four-horizon mean, with a horizon-dependent sign — a reproduction, not an improvement. Reporting only the mean would have hidden the structure, and the two disclosed deviations (validation checkpoint, 7-variable metric) mean the per-horizon wins cannot be claimed as superiority.
-p44 Benchmark result (28 arms, 3 seeds, shared windows):
-p45 Table 3. The 28-arm benchmark: 7-variable aggregate MSE per horizon and as a four-horizon mean, plus the four-horizon MAE, in z-space. Mean over seeds 42/43/44, on the shared (W//16)*16 windows 160/144/144/128.
-p46 Lower is better. Per-horizon MAE is omitted for legibility; it is in 02_数字表格/BENCH_MSE_BY_MODEL_L.csv. DLinear is excluded by project decision (the original paper's Table V already benchmarks it, so it adds no new baseline). The seasonal-naive reference (52-week lag) scores 6.2132 on the same windows, so every one of the 28 arms beats it. Hardware: A100-SXM4-80GB, partition stingy, CityU HPC Burgundy — 204/204 cells of the 17 arms (13 conventional + 3 published LLM-based + DLinear) carry that measured provenance, and the MIFlu and encoder cells were run on the same partition with per-cell manifests on the cluster. Parameter counts are the trained-model totals from BENCH_EFFICIENCY.csv; classical learners and MIFlu are non-parametric in this sense (or not exported) and are left blank.
-p47 MIFlu is the accuracy champion at 1.5574, followed by PatchTST (1.6621) and NLinear (1.8716); the spread across all 28 arms is 1.5574 to 5.6155, a factor of 3.6. The published LLM-based competitors are beaten by a nearest-neighbour baseline (KNN 3.7854 vs Qwen-Time 5.2557 and CALF 5.5785), and the 11 frozen encoders occupy the 4.74-5.20 band.
-p48 Finding F0 — accuracy alone does not identify a deployable model. The ranking is easy to produce and hard to act on: it says which model fits this test set best, not which model supports the decision the forecast exists for. The next three analyses ask the questions the ranking cannot answer.
-p49 Peak-skill result (PTE/PIE, Kramer & Shaman criterion; the grid shows the three named arms cell by cell):
-p50 Table 4. The same criterion cell by cell: every (horizon, step) pair for the three named arms. PASS requires PTE ≤ 1 week AND PIE ≤ 25 % in the same cell.
-p51 16 cells per model = 4 horizons × 4 steps, each a mean over seeds 42/43/44. NLinear passes 4 of 16, all at step 0 (PIE 2.4–4.2 %); MIFlu passes 4 of 16 — three at step 0 and one at L=48 step 1, with PIE 18.3–24.8 %, i.e. against the boundary; PatchTST passes none, because its PIE stays in the 26–35 % band at every step. Peak detection: find_peaks(prominence = 0.15 × range, distance = 15) with ±8-week matching — this study's engineering choice, not part of the published criterion. The 1-week / 25 % thresholds are attributed to Kramer & Shaman (2019) but remain [to verify] against the original text.
-p52 NLinear and MIFlu each pass 4 of 16 cells, but differently: NLinear passes all four step-0 cells with a PIE of 3.2 %, while MIFlu's four passes sit at PIE 18.3-24.8 %, against the 25 % boundary, and it misses L=48 at step 0. PatchTST passes none: its timing is the best in the study (mean PTE 1.24 weeks) but its PIE is 32.8 %.
-p53 Finding F1 — the deployment ordering is not the accuracy ordering. Across all 28 arms, better MSE does go with better calibration (Spearman ρ = +0.74 against mean PIE), so MSE is a useful screen; but the frontier is ordered the other way round. Among the three lowest-MSE arms the calibration order is inverted at both ends (NLinear 9.5 %, MIFlu 26.8 %, PatchTST 32.8 %), and the pass indicator is negatively rank-correlated with MSE (ρ = -0.43, p = 0.023). The runner-up by MSE passes nothing; the third-best passes every horizon one week ahead.
-p55 Step-0 peak skill for the three named arms. Left: peak-timing error (weeks) at step 0, mean over the four horizons, against the 1-week threshold (dashed). Right: peak-intensity error (%) at step 0 against the 25 % threshold (dashed). Green = inside the threshold, red = outside. MIFlu (0.35 wk, 18.9 %) and NLinear (0.21 wk, 3.2 %) stay inside both thresholds at the mean level, while PatchTST (0.68 wk, 30.6 %) misses the intensity half — the visual form of the decoupling between a good average error and a calibrated peak. Seeds 42/43/44; windows (W//16)*16 = 160/144/144/128.
-p56 Efficiency and significance. Across the 11 parametric arms, MSE against log10(parameters) has slope +0.1171 and R² = 0.0223: size explains about 2 % of the variance and its sign is unfavourable. The Pareto set is exactly {NLinear, 2,520 parameters; PatchTST, 531,878 parameters}, i.e. 211x the parameters for 11.2 % lower MSE. On the 12 matched cells of the 17 non-encoder arms, 128 of 136 pairs are significant before correction; after proper Holm none survives (smallest attainable adjusted p 0.066), and the NLinear-PatchTST pair has p(Holm) = 0.117.
-p57 Table 5. Paired sign-flip tests on the 12 matched (horizon × seed) cells, Holm-corrected over all 136 pairs (recomputed from the raw p-values). First row: the Pareto pair discussed in the text (bold). Remaining rows: the six smallest p-values, for contrast.
-p58 Positive Δ means model A has the larger MSE. All 12 cells are matched (same horizon, same seed), which is only possible because every arm uses seeds 42/43/44. The exported p_holm column was produced with a reverse cumulative minimum, which is not a valid Holm adjustment; the values here are recomputed from p_raw. With n = 12 the smallest attainable raw p is 2/2¹² ≈ 0.00049, so with m = 136 pairs the smallest attainable adjusted p is 0.066 and no pair survives at 0.05 (128/136 are significant before correction). Why the first row is not in the second block: NLinear vs PatchTST has adjusted p = 0.117, the 117th smallest of 136, so a table sorted by significance omits the one comparison the Pareto argument needs. The difference is not resolvable at this sample size; that is a failure to reject, not a demonstration of equivalence (d = 1.15, and PatchTST is lower in 10 of 12 cells).
-p59 Finding F2 (efficiency). Parameter count is not a proxy for accuracy: the slope is positive and R² is 0.0223. The frontier is a two-model trade-off, not a ranking.
-p60 Finding F3 (significance). The 211x cost buys an 11.2 % MSE difference that this benchmark cannot resolve at n = 12. This is a failure to reject equality, not a proof of equivalence (d = 1.15; PatchTST is lower in 10 of 12 cells), so the defensible conclusion is “no accuracy advantage is established for the 211x cost”, which together with F1 makes NLinear the defensible default.
-p62 Accuracy–efficiency Pareto frontier. x = parameter count (log scale), y = 4-horizon mean 7-variable z-space MSE; the step line is the Pareto set {NLinear, 2,520 parameters; PatchTST, 531,878 parameters}. PatchTST spends 211× the parameters of NLinear for 11.2 % lower MSE; the fitted slope of MSE against log₁₀(parameters) is +0.1171 with R² = 0.0223, i.e. size explains ~2 % of the variance and the sign is positive. Windows: shared (W//16)*16 = 160/144/144/128; seeds 42/43/44. Reproduced by plot_pareto.py. Hardware: A100-SXM4-80GB | partition stingy | CityU HPC Burgundy.
-p63 Frozen LLM encoders. Eleven encoders (Qwen2.5-1.5B, five DeepSeek-R1-Distill sizes, Hunyuan-1.8B/4B/7B, ContextPilot-8B/14B), each frozen with one shared linear head, 132 of 156 cells. The best is Hunyuan-1.8B at 4.7374 and the worst Qwen2.5-1.5B at 5.2049, i.e. 3.04x to 3.34x the MSE of MIFlu; every one is worse than a decision tree, and none passes the Kramer & Shaman criterion in any cell.
-p64 Finding F4 — frozen LLM representations do not transfer to this task. The protocol was built to give the idea its best chance (frozen features, linear read-out, channel independence) and it still fails. This does not prove that an encoder can never help, but it does mean that a claim of gain from frozen language features on this task owes a mechanism and a control.
-p65 Ablation ladder (Table VIII in the project plan). Five variants — no LoRA, and K = 2, 4, 8, 12 layers — at four horizons and three seeds (60 cells), compared against the full K=6 arm already in the benchmark table. The ladder answers where MIFlu's accuracy comes from: the LoRA adaptation or the depth of the stack. At this report 27 of 60 cells are complete, so no depth trend is claimed. One result is already established: the text tokens sit behind the causal mask and the head reads only the time patches, so --no-text is bit-identical to the full arm — a structural verification (asserted by tests_archive/test_miflu_ablations.py), not an ablation effect.
-p66 Finding F5 (provisional). The text branch is masked out of the prediction path, so the multimodal claim is not supported by the architecture as shipped; the depth and LoRA questions remain open until the 60 cells are aggregated. This is reported as a design and a status, not as a result.
-p67 Problems encountered. (1) The original code selects its checkpoint on the test set and scores only 1 of 7 variables in the test loader; both were identified and fixed, and are disclosed as deviations. (2) The evaluation-window rule is a side effect of drop_last=True; adopting it for all arms was necessary to avoid handing MIFlu an easier test. (3) Eight engineering defects were found in the training pipeline (seed not reaching the LLM path, snapshot cloning the frozen encoder, two cache layouts, a non-atomic lock); seven are fixed and one remains open as an operational risk. (4) The ablation ladder has slipped from early November to late November because of queue contention on the shared A100 partition.
-p68 7. Summary of objectives addressed and results achieved to date
-p69 Table 6. Objectives addressed and results achieved to date
-p70 Percentages are estimates of the work completed against each objective as of 3 November 2026.
-p72 8. Work schedule and expected results for the next one to two months
-p73 Table 7. Work schedule and expected results for the next one to two months
-p74 Dates are targets, not commitments; GPU-hour estimates are measured where stated and modelled otherwise.
-p75 Risks and mitigation. (1) Queue contention on the shared A100 partition is the reason the ablation slipped; the ladder is submitted as one 60-cell job so it cannot be starved cell by cell. (2) Criterion attribution: the 1-week / 25 % thresholds are marked [to verify] and will be checked against the Kramer & Shaman text before submission; the peak detector is stated as our own choice, so a reader can separate the criterion from the implementation. (3) Single dataset: the regional and rolling-origin evaluations are the mitigation, and if they do not finish in time the paper will state the limitation rather than generalise. (4) Scope: if the ablation or Table VI is still incomplete at submission, the manuscript reports them as design and status, exactly as this report does — no trend, no fabricated number.
-p76 The manuscript draft is already written against these results (IEEE structure, EN and ZH; a single-column review draft until submission); the remaining work is to fold in the ablation ladder, the regional table and, if the budget allows, the rolling-origin evaluation. The submission target is IEEE JBHI, with a CCF-B venue as the alternative if the rolling-origin results arrive in time.
-p77 Date: _____________    Signature of student: _____________
-table1/row1 Name of Student | ________________________________
-table1/row2 Student ID | ________________________________
-table1/row3 Programme-Major | BEng (Hons) Electrical Engineering / ______________
-table1/row4 Project Code and Title | ________  Reproducing MIFlu and Benchmarking Influenza Forecasting with Frozen LLM Encoders
+p0 CITY UNIVERSITY OF HONG KONG
+p1 Department of Electrical Engineering   Progress Report   2026/27 Semester A
+p2 PART A
+p3 PART B
+p4 1. Project objectives
+p5 Problem statement. An accurate national influenza curve can still have timing or peak-height errors. I am independently reproducing MIFlu and evaluating how model choice changes when peak errors and parameter count accompany average error. The project evaluates accuracy, peak skill, parameter efficiency and statistical evidence, with explicitly different model subsets.
+p6 Objectives. (1) Reproduce and explain Table V. (2) Compare 28 retained implementations under common windows. (3) assess peak timing, magnitude and parameter trade-offs. (4) Test the specific frozen-encoder transfer setup. (5) Validate findings across origins and regions before claiming deployment value.
+p7 2. Original project planning chart
+p8 Table 1. Original planning periods and current evidence
+p9 This is a reconstruction from the supplied plan, annotated at 3 November 2026. No contemporaneously signed September chart was available.
+p10 3. Background study
+p11 Patching and linear baselines are established [3–5]. Time-LLM, CALF and TimeCMA use different alignment/adaptation designs [6–8]. Chronos, TimesFM, Moirai and Lag-Llama pretrain on numerical series and were not evaluated here [9–12]. Earlier LLM-removal work already questions the benefit of language pretraining [13], while a 2026 preprint reports conditional benefits under cross-dataset shifts [14]. The contribution here is the specific influenza protocol audit and multi-metric comparison.
+p12 Global and societal context. Peak forecasts can inform preparedness and capacity planning, but retrospective national accuracy does not measure clinical benefit. Transparent evaluation can reduce unjustified spending on complex models and expose failure modes. No real-world resource-saving or patient-outcome effect was measured [2,18].
+p13 4. Methodology
+p14 Table 2. Separate reproduction and benchmark protocols
+p15 Three seeds are a compute-budget choice, not a universal venue rule. Reproduction and benchmark estimates use different seed sets. Do not substitute one for the other. Exact upstream protocol defects remain to be checked against a pinned author revision.
+p16 We use a chronological split and train-only scaling. Validation selects checkpoints in this implementation. The handoff attributes test-set checkpoint selection and a one-variable loader to upstream code, but a pinned author checkout is absent and the public endpoint could not be opened. Those upstream allegations remain unverified. The notes also show learning-rate differences between code defaults and paper settings, so the comparison must not be described as differing in only two ways.
+p17 Peak timing error (PTE) is the absolute difference between predicted and observed peak weeks. Peak intensity error (PIE) is the absolute peak-height error divided by the observed peak, expressed as a percentage. Kramer–Shaman [2] verifies the separate one-week and 25% tolerances. We apply both to mean errors in each (model, L, step) cell. This joint screen and its peak detector are project choices, not a clinical acceptance standard. A mean-error pass is not an individual-season success probability.
+p18 Design impact. All retained arms use the same cropped evaluation windows. Scaling is fitted on training data. The 7-variable average is dimensionless, while peak errors use ILITOTAL in patient counts. This allows transparent comparisons without pretending the joint screen certifies safe public-health use. Three benchmark seeds reflect compute limits; additional independent seasons are needed for uncertainty.
+p20 6. Progress
+p21 Progress against plan. The supplied exports contain the reproduction table and 28 × 4 × 3 benchmark cell means. The original suite is supplied under tests_archive/, but cannot be collected cleanly here. My audit now recomputes the CSV aggregates and has seven new CPU tests. The ablation remains owner-reported at 27/60 with no per-variant aggregation. Regional and rolling-origin evaluation are incomplete.
+p22 Table 3. MIFlu reproduction compared with the paper
+p23 Source: ESSAY_VS_REPRODUCTION_TABLE_V.csv, lines 2–6. SD is recomputed from the code-transcribed ten-seed oracle; its raw run logs are not included. Positive differences mean higher error.
+p24 The reproduction CSV reports mean MSE 1.4995 versus 1.4355, a 4.5% increase. MSE is lower at L24 and L36 and higher at L48 and L60. Mean MAE is 0.8043 versus 0.7452 (+7.9%), but its signs are one lower and three higher; MAE does not share the MSE 2–2 crossover. Protocol and missing upstream provenance limit claims of exact replication.
+p25 Reproduction conclusion. The observed mean-MSE gap is +4.5%. The remaining protocol and provenance differences prevent a claim of exact replication or superiority.
+p27 Table 4. Accuracy of all retained benchmark arms
+p28 Source: BENCH_MSE_BY_MODEL_L.csv, keyed by model and L. Each row averages three seeds on 160/144/144/128 windows. DLinear is excluded by project choice; that exclusion needs a documented sensitivity analysis. Names denote project implementations, whose equivalence to published methods is not established by this ranking.
+p29 F0 conclusion. MIFlu has the lowest observed MSE (1.5574), but MSE alone does not establish public-health utility. The top-three spread is 20.2% relative to MIFlu, not less than 20%.
+p30 Table 5. Joint peak screen for each horizon and lead
+p31 Each entry gives PTE in weeks / PIE in percent. s0–s3 are the first to fourth forecast weeks. The detector uses prominence 0.15 × range, distance 15, and ±8-week matching. These detector settings and joint aggregation are project choices. Source: BENCH_PTE_PIE_BY_STEP.csv.
+p32 F1 conclusion. NLinear and MIFlu each pass 4/16 aggregated cells, while PatchTST passes 0/16. NLinear has lower mean PIE (9.477% versus MIFlu 26.846%) but higher mean PTE (1.677 versus 1.128 weeks). This is a timing–magnitude trade-off, not dominance. The ordering is inverted at both ends among the three leaders: MSE orders MIFlu, PatchTST, NLinear; PIE orders NLinear, MIFlu, PatchTST.
+p34 Step-zero mean PTE and PIE across horizons for the three leading arms. Mean-level tolerances are illustrative; MIFlu still fails L48 at step zero. A mean error below a threshold is not a season-level success rate. Source: BENCH_PTE_PIE_BY_STEP.csv.
+p35 Table 6. Parameter analysis and rank associations
+p36 The Pareto analysis includes only 11 arms with parameter exports. MIFlu and the frozen encoders are not in that subset. Missing parameter counts are not zero. Parameter count is not a measurement of latency, memory or energy. Correlations are descriptive across models on one test set.
+p37 F2 conclusion. The fitted slope is +0.1171 and R² is 0.0223 across the 11 arms with exported parameter counts. Size alone explains little of their observed MSE variation. This subset result does not prove that capacity is irrelevant.
+p38 Table 7. Paired comparisons with corrected Holm adjustment
+p39 136 pairs cover 17 models, not all 28. n = 12 matched horizon × seed cells. Forward cumulative-max Holm yields 0/136 rejections. The shown p values recover the exact 1/4096 enumeration grid from six-decimal exports; recomputing directly from rounded exports gives NLinear–PatchTST 0.117180 instead of 0.1171875. *The source effect uses pooled model SD, not paired-difference SD. Cell dependence limits inference.
+p40 F3 conclusion. Proper Holm gives 0/136 rejections (128/136 before adjustment), with a minimum adjusted p of about 0.0664 and NLinear–PatchTST p ≈ 0.1172. PatchTST still has 11.2% lower observed MSE with 211× the parameters and lower MSE in 10/12 cells. Non-rejection does not establish equivalence or show that the gain is noise.
+p42 Accuracy–parameter trade-off among 11 models with exported parameter counts. MIFlu and frozen encoders are omitted from this subset. Parameter count is not a measured runtime or memory cost. Source: BENCH_EFFICIENCY.csv.
+p43 Table 8. Frozen encoders with shared linear readout
+p44 11 retained encoders × 4 horizons × 3 seeds = 132 cells. The historical plan included two additional embedding-only arms, giving 156 planned cells; those 24 omitted cells are outside the 28-model roster. The result tests only this frozen-feature pipeline.
+p45 F4 conclusion. The 11 tested frozen encoders score 4.7374–5.2049, or 3.04–3.34× MIFlu’s MSE. All exceed the decision tree’s 4.3198 and pass 0/16 cells. This is a negative result for this feature/readout configuration; prompting, fine-tuning and numerical foundation models remain untested.
+p46 Table 9. Ablation design and snapshot status
+p47 Owner-reported status at 3 November 2026: 27/60 additional cells, job 722968. No live HPC check or per-variant result export was available. The baseline 12 cells are not part of the additional 60. No trend is inferred.
+p48 F5 provisional conclusion. In miflu_model.py’s author_faithful path, text follows time tokens behind causal attention and the head reads the time tokens. Static inspection therefore predicts no text influence during deterministic evaluation. The supplied tests_archive/test_miflu_ablations.py explicitly asserts both text invariance and full/no-text equality with matched CPU initialisation. It was inspected statically, not executed here. Other fusion paths and training randomness require separate checks.
+p49 Problems encountered. The source exported Holm column remains defective; the corrected corpus recomputes the proper adjustment. The roster arithmetic, MAE crossover, hardware coverage and missing tests also needed correction. Queue status cannot be certified from this offline snapshot. I will freeze the corrected reporting path and keep all original CSVs for comparison.
+p50 7. Summary of objectives addressed and results achieved to date
+p51 Table 10. Objectives addressed and estimated completion
+p52 These are planning estimates supplied in the task, not measured research scores. 45% is 27/60. The other estimates are not independently measured.
+p53 8. Work schedule and expected results for the next one to two months
+p54 Table 11. Work schedule and expected outputs
+p55 Dates are targets. Queue availability, measured runtime and supervisor approval determine feasibility. No conference deadline is inferred from this schedule.
+p56 Risks and mitigation. Queue delays may prevent ablation completion, so retain explicit incomplete labels. Validate the date mapping and use season-level rolling origins to address temporal dependence. Restore the original tests and pin dependencies before publication. Confirm a presentation appointment with both supervisor and assessor. The school template requires both presentation and timely InfoNet submission.
+p57 Date ____________________    Signature of student ____________________
+p58 Key references used in the background and methodology are listed below. Numbering matches the internal report and manuscript.
+p59 [1] Jaeuk Moon, Jonghwa Shim, Eunbeen Kim and Eenjun Hwang, “MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme,” IEEE JBHI 29(10), 7790-7801, 2025. https://doi.org/10.1109/JBHI.2025.3561214
+p60 [2] Sarah C. Kramer and Jeffrey Shaman, “Development and validation of influenza forecasting for 64 temperate and tropical countries,” PLOS Computational Biology 15(2), e1006742, 2019. https://doi.org/10.1371/journal.pcbi.1006742
+p61 [9] Abdul Fatir Ansari et al., “Chronos: Learning the Language of Time Series,” Transactions on Machine Learning Research, 2024. https://arxiv.org/abs/2403.07815
+p62 [13] Mingtian Tan, Mike A. Merrill, Vinayak Gupta, Tim Althoff and Thomas Hartvigsen, “Are Language Models Actually Useful for Time Series Forecasting?,” NeurIPS 37, 2024. https://arxiv.org/abs/2406.16964
+p63 [14] Xin Qiu et al., “Rethinking the Role of LLMs in Time Series Forecasting,” arXiv:2602.14744 v1, preprint, 2026. https://arxiv.org/abs/2602.14744
+p64 [18] Johannes Bracher, Evan L. Ray, Tilmann Gneiting and Nicholas G. Reich, “Evaluating epidemic forecasts in an interval format,” PLOS Computational Biology 17(2), e1008618, 2021. https://doi.org/10.1371/journal.pcbi.1008618
+table1/row1 Name of Student | CHAN Sing Yeung
+table1/row2 Student ID | ____________________
+table1/row3 Programme Major | ____________________
+table1/row4 Project Code and Title | ________ MIFlu reproduction and influenza forecasting audit
 table1/row5 Name of Supervisor | Prof. Katie CHAN
-table1/row6 Name of Assessor | ________________________________
-table1/row7 Number of meetings with supervisor / assessor | ______ / ______
-table1/row8 Average number of hours spent on the project weekly | ________ hours/week
-table1/row9 Report date | 3 November 2026
-table2/row1 Parameter | Ours | Original | Note
-table2/row2 Data | 966 weeks x 7 vars, CDC | Same | Byte-identical (SHA-256)
-table2/row3 Split | 676/97/193 (70/10/20) | Same | Time-ordered
-table2/row4 Input window T | 104 weeks | Same | 
-table2/row5 Horizon L | 24/36/48/60 | Same | Trained independently
-table2/row6 Seeds (repro) | 2021-2030 (10 reps) | fix_seed=2021 (1) | [DEVIATION] Paper claims 10 reps
-table2/row7 Epochs | 20 | default=1 | 1 epoch does not converge
-table2/row8 LR | 1e-4 | code 1e-4 / paper 5e-4 | Paper self-contradictory
-table2/row9 Batch size | 16 | Same | drop_last=True
-table2/row10 Optimizer | Adam | Same | 
-table2/row11 GPT-2 layers/d_model | 6/768 | Same | 
-table2/row12 LoRA | r=4, a=4, drop=0.05, c_attn | Same | 
-table2/row13 Trainable params | 1,673,496 | Same | LoRA+LN+head
-table2/row14 Checkpoint selection | VALIDATION MSE | TEST MSE | [DEVIATION] Test= data leakage
-table2/row15 Metric | 7-var aggregate MSE/MAE | Same (bug: 1 var) | [DEVIATION] Fix bug
-table2/row16 Eval windows | (W//16)*16 = 160/144/144/128 | Same (drop_last side effect) | Not a journal requirement
-table3/row1 Horizon | Ours (10-rep mean ± sd) | Paper | Δ MSE | Sign | Ours MAE | Paper MAE | Δ MAE
-table3/row2 L=24 | 1.3045 ± 0.0883 | 1.542 | -15.4 % | WIN | 0.7482 | 0.726 | +3.1 %
-table3/row3 L=36 | 1.3561 ± 0.1603 | 1.422 | -4.6 % | WIN | 0.7712 | 0.779 | -1.0 %
-table3/row4 L=48 | 1.6543 ± 0.1064 | 1.414 | +17.0 % | LOSS | 0.8381 | 0.757 | +10.7 %
-table3/row5 L=60 | 1.6829 ± 0.2109 | 1.364 | +23.4 % | LOSS | 0.8596 | 0.719 | +19.6 %
-table3/row6 4-horizon mean | 1.4995 | 1.435 | +4.5 % | LOSS | 0.8043 | 0.745 | +7.9 %
-table4/row1 # | Model | Family | MSE L24 | MSE L36 | MSE L48 | MSE L60 | MSE 4L | MAE 4L | Params
-table4/row2 1 | MIFlu | LLM-based | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199 | —
-table4/row3 2 | PatchTST | Transformer | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786 | 531,878
-table4/row4 3 | NLinear | Linear | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183 | 2,520
-table4/row5 4 | DNN | Neural | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057 | 33,048
-table4/row6 5 | TimeCMA | LLM-based | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676 | 125,830,824
-table4/row7 6 | Gradient Boosting | Classical ML | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521 | —
-table4/row8 7 | KNN | Classical ML | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293 | —
-table4/row9 8 | Random Forest | Classical ML | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779 | —
-table4/row10 9 | iTransformer | Transformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476 | 75,672
-table4/row11 10 | Decision Tree | Classical ML | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798 | —
-table4/row12 11 | Hunyuan-1.8B | LLM enc. | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755 | —
-table4/row13 12 | Hunyuan-7B | LLM enc. | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685 | —
-table4/row14 13 | DeepSeek-R1-Qwen-1.5B | LLM enc. | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002 | —
-table4/row15 14 | DeepSeek-R1-Llama-8B | LLM enc. | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786 | —
-table4/row16 15 | GRU | Neural | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174 | 14,424
-table4/row17 16 | DeepSeek-R1-32B | LLM enc. | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935 | —
-table4/row18 17 | LSTM | Neural | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303 | 18,712
-table4/row19 18 | DeepSeek-R1-Qwen-14B | LLM enc. | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019 | —
-table4/row20 19 | DeepSeek-R1-Qwen-7B | LLM enc. | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133 | —
-table4/row21 20 | RNN | Neural | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634 | 5,848
-table4/row22 21 | ContextPilot-8B | LLM enc. | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255 | —
-table4/row23 22 | Hunyuan-4B | LLM enc. | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450 | —
-table4/row24 23 | ContextPilot-14B | LLM enc. | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407 | —
-table4/row25 24 | Qwen2.5-1.5B | LLM enc. | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725 | —
-table4/row26 25 | Qwen-Time | LLM-based | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794 | 1,544,084,680
-table4/row27 26 | SVR | Classical ML | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986 | —
-table4/row28 27 | CALF | LLM-based | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190 | 126,421,416
-table4/row29 28 | CNN | Neural | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720 | 22,488
-table5/row1 Model | L | step 0 (1 wk) | step 1 (2 wk) | step 2 (3 wk) | step 3 (4 wk)
-table5/row2 NLinear | L=24 | PASS (0.11 wk, 3.9 %) | fail (1.33 wk, 8.4 %) | fail (2.33 wk, 11.9 %) | fail (2.67 wk, 18.7 %)
-table5/row3 NLinear | L=36 | PASS (0.33 wk, 4.2 %) | fail (1.33 wk, 7.2 %) | fail (2.11 wk, 15.3 %) | fail (2.67 wk, 18.1 %)
-table5/row4 NLinear | L=48 | PASS (0.22 wk, 2.4 %) | fail (1.22 wk, 4.7 %) | fail (2.22 wk, 10.0 %) | fail (2.78 wk, 16.7 %)
-table5/row5 NLinear | L=60 | PASS (0.17 wk, 2.5 %) | fail (1.44 wk, 4.5 %) | fail (2.56 wk, 10.0 %) | fail (3.33 wk, 13.0 %)
-table5/row6 MIFlu | L=24 | PASS (0.00 wk, 18.3 %) | fail (0.89 wk, 26.7 %) | fail (1.22 wk, 30.5 %) | fail (1.33 wk, 31.6 %)
-table5/row7 MIFlu | L=36 | PASS (0.00 wk, 18.7 %) | fail (0.78 wk, 26.3 %) | fail (1.67 wk, 31.5 %) | fail (1.33 wk, 32.4 %)
-table5/row8 MIFlu | L=48 | fail (1.22 wk, 18.0 %) | PASS (0.67 wk, 24.8 %) | fail (1.22 wk, 30.1 %) | fail (1.33 wk, 33.2 %)
-table5/row9 MIFlu | L=60 | PASS (0.17 wk, 20.5 %) | fail (1.33 wk, 25.8 %) | fail (2.22 wk, 29.8 %) | fail (2.67 wk, 31.2 %)
-table5/row10 PatchTST | L=24 | fail (0.67 wk, 30.6 %) | fail (1.00 wk, 34.0 %) | fail (1.22 wk, 33.6 %) | fail (1.22 wk, 30.7 %)
-table5/row11 PatchTST | L=36 | fail (1.00 wk, 26.2 %) | fail (1.67 wk, 32.2 %) | fail (1.33 wk, 31.2 %) | fail (1.33 wk, 33.9 %)
-table5/row12 PatchTST | L=48 | fail (0.56 wk, 30.4 %) | fail (1.33 wk, 30.9 %) | fail (0.89 wk, 35.2 %) | fail (0.89 wk, 35.0 %)
-table5/row13 PatchTST | L=60 | fail (0.50 wk, 35.0 %) | fail (1.67 wk, 34.3 %) | fail (2.22 wk, 35.7 %) | fail (2.33 wk, 35.1 %)
-table6/row1 Model A | Model B | n | mean Δ MSE | A wins | p (Holm) | effect d
-table6/row2 NLinear | PatchTST | 12 | +0.2095 | 2/12 | 0.1172 | 1.15
-table6/row3 Gradient Boosting | RNN | 12 | -1.4029 | 12/12 | 0.06637 | 4.86
-table6/row4 CALF | RNN | 12 | +0.5111 | 0/12 | 0.06637 | 1.65
-table6/row5 CALF | SVR | 12 | +0.2397 | 0/12 | 0.06637 | 1.82
-table6/row6 CALF | TimeCMA | 12 | +2.9704 | 0/12 | 0.06637 | 14.78
-table6/row7 CNN | Decision Tree | 12 | +1.2957 | 0/12 | 0.06637 | 2.69
-table6/row8 CNN | DNN | 12 | +3.4740 | 0/12 | 0.06637 | 6.43
-table7/row1 # | Objective | Addressed | Achieved
-table7/row2 1 | Reproduce MIFlu's Table V under the author's protocol and report the result honestly, including a sign crossover | Yes | 100 %
-table7/row3 2 | Build a like-for-like benchmark of conventional forecasters on the same dataset, split and windows | Yes | 100 %
-table7/row4 3 | Evaluate the benchmark on the epidemiological acceptance criterion (PTE/PIE), not only on MSE | Yes | 100 %
-table7/row5 4 | Add a new evaluation axis: frozen LLM encoders as feature extractors | Yes: 11 arms complete, MSE/PTE/PIE aggregated and in the table | 100 %
-table7/row6 5 | Ablation ladder (Table VIII in the plan) and regional evaluation (Table VI) | Ablation 27/60 and running; regional queued behind it | 45 %
-table7/row7 6 | Rolling-origin (walk-forward) evaluation | Code ready, not run (155–360 A100-h) | 15 %
-table7/row8 7 | Manuscript and a stated contribution | Draft complete; contribution stated as an empirical evaluation | 70 %
-table8/row1 Date | Work | Expected result
-table8/row2 By 16 Nov 2026 | Ablation ladder drains (60/60); pull the per-variant export and add the table | Ablation table with a measured depth trend
-table8/row3 By 20 Nov 2026 | Submit the progress report and present to supervisor and assessor | Report submitted; presentation delivered
-table8/row4 By 30 Nov 2026 | Table VI regional (21 cells, ~22 min/cell) and Table IX from the cell manifests | Regional table, 21/21 cells
-table8/row5 By 31 Dec 2026 | Rolling-origin tranche (1020 cells, 155–360 A100-h); first folds land | Walk-forward results, 5 folds
-table8/row6 Jan–Apr 2027 | Manuscript revision, internal review, submission to IEEE JBHI | Submitted manuscript
+table1/row6 Name of Assessor | ____________________
+table1/row7 Meetings with supervisor and assessor | ______ / ______
+table1/row8 Average weekly project hours | ______ hours/week
+table2/row1 Period | Planned work | Snapshot status
+table2/row2 Sep 2026 | Read MIFlu and establish data contract | Local data equality checked
+table2/row3 Oct 2026 | Reproduce Table V | CSV and oracle arithmetic checked
+table2/row4 Nov 2026 | Benchmark and ablation; progress presentation | 28-arm CSV complete; ablation reported 27/60
+table2/row5 Nov–Dec 2026 | Regional and rolling-origin validation | Not completed in this snapshot
+table2/row6 Jan–Apr 2027 | Manuscript strengthening and submission decision | Planned, conditional on validation
+table3/row1 Item | Reproduction | Benchmark
+table3/row2 Seeds | 2021–2030 (10) | 42/43/44 (3)
+table3/row3 Models | MIFlu | 13 conventional + 4 LLM-based + 11 frozen encoders
+table3/row4 Selection | Validation checkpoint | Validation checkpoint
+table3/row5 Scores | 7-variable z-space MSE / MAE | 7-variable MSE / MAE; ILITOTAL PTE / PIE
+table3/row6 Windows | 160 / 144 / 144 / 128 | 160 / 144 / 144 / 128
+table4/row1 Horizon | Our MSE ± SD | Paper MSE | Δ MSE | Our MAE | Paper MAE | Δ MAE
+table4/row2 L=24 | 1.3045 ± 0.0883 | 1.5420 | -15.4% | 0.7482 | 0.7260 | +3.1%
+table4/row3 L=36 | 1.3561 ± 0.1603 | 1.4220 | -4.6% | 0.7712 | 0.7790 | -1.0%
+table4/row4 L=48 | 1.6543 ± 0.1064 | 1.4140 | +17.0% | 0.8381 | 0.7570 | +10.7%
+table4/row5 L=60 | 1.6829 ± 0.2109 | 1.3640 | +23.4% | 0.8596 | 0.7190 | +19.6%
+table4/row6 4-horizon mean | 1.4995 | 1.4355 | +4.5% | 0.8043 | 0.7452 | +7.9%
+table5/row1 # | Model | L24 | L36 | L48 | L60 | Mean MSE | Mean MAE
+table5/row2 1 | MIFlu | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199
+table5/row3 2 | PatchTST | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786
+table5/row4 3 | NLinear | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183
+table5/row5 4 | DNN | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057
+table5/row6 5 | TimeCMA | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676
+table5/row7 6 | Gradient Boosting | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521
+table5/row8 7 | KNN | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293
+table5/row9 8 | Random Forest | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779
+table5/row10 9 | iTransformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476
+table5/row11 10 | Decision Tree | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798
+table5/row12 11 | Hunyuan-1.8B | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755
+table5/row13 12 | Hunyuan-7B | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685
+table5/row14 13 | DeepSeek-R1-Qwen-1.5B | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002
+table5/row15 14 | DeepSeek-R1-Llama-8B | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786
+table5/row16 15 | GRU | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174
+table5/row17 16 | DeepSeek-R1-32B | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935
+table5/row18 17 | LSTM | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303
+table5/row19 18 | DeepSeek-R1-Qwen-14B | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019
+table5/row20 19 | DeepSeek-R1-Qwen-7B | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133
+table5/row21 20 | RNN | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634
+table5/row22 21 | ContextPilot-8B | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255
+table5/row23 22 | Hunyuan-4B | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450
+table5/row24 23 | ContextPilot-14B | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407
+table5/row25 24 | Qwen2.5-1.5B | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725
+table5/row26 25 | Qwen-Time | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794
+table5/row27 26 | SVR | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986
+table5/row28 27 | CALF | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190
+table5/row29 28 | CNN | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720
+table6/row1 Model | L | s0 | s1 | s2 | s3
+table6/row2 NLinear | 24 | PASS 0.111 / 3.949 | fail 1.333 / 8.411 | fail 2.333 / 11.943 | fail 2.667 / 18.739
+table6/row3 NLinear | 36 | PASS 0.333 / 4.181 | fail 1.333 / 7.222 | fail 2.111 / 15.313 | fail 2.667 / 18.145
+table6/row4 NLinear | 48 | PASS 0.222 / 2.419 | fail 1.222 / 4.727 | fail 2.222 / 9.979 | fail 2.778 / 16.655
+table6/row5 NLinear | 60 | PASS 0.167 / 2.450 | fail 1.444 / 4.542 | fail 2.556 / 9.952 | fail 3.333 / 13.000
+table6/row6 MIFlu | 24 | PASS 0.000 / 18.307 | fail 0.889 / 26.686 | fail 1.222 / 30.472 | fail 1.333 / 31.638
+table6/row7 MIFlu | 36 | PASS 0.000 / 18.695 | fail 0.778 / 26.333 | fail 1.667 / 31.514 | fail 1.333 / 32.427
+table6/row8 MIFlu | 48 | fail 1.222 / 18.004 | PASS 0.667 / 24.795 | fail 1.222 / 30.133 | fail 1.333 / 33.236
+table6/row9 MIFlu | 60 | PASS 0.167 / 20.530 | fail 1.333 / 25.799 | fail 2.222 / 29.790 | fail 2.667 / 31.177
+table6/row10 PatchTST | 24 | fail 0.667 / 30.580 | fail 1.000 / 34.044 | fail 1.222 / 33.572 | fail 1.222 / 30.722
+table6/row11 PatchTST | 36 | fail 1.000 / 26.235 | fail 1.667 / 32.247 | fail 1.333 / 31.245 | fail 1.333 / 33.854
+table6/row12 PatchTST | 48 | fail 0.556 / 30.360 | fail 1.333 / 30.878 | fail 0.889 / 35.158 | fail 0.889 / 35.002
+table6/row13 PatchTST | 60 | fail 0.500 / 35.035 | fail 1.667 / 34.342 | fail 2.222 / 35.674 | fail 2.333 / 35.133
+table7/row1 Quantity | Value
+table7/row2 Regression slope / R² | +0.1171 / 0.0223
+table7/row3 Models with parameter exports | 11
+table7/row4 Subset Pareto set | NLinear 2,520; PatchTST 531,878
+table7/row5 Parameter ratio | 211.1×
+table7/row6 Descriptive MSE reduction | 11.2%
+table7/row7 ρ(MSE, PIE) | +0.736 (p < 0.0001)
+table7/row8 ρ(MSE, passes) | -0.429 (p = 0.023)
+table8/row1 Model A | Model B | Δ MSE | p raw | p Holm | Effect*
+table8/row2 NLinear | PatchTST | +0.2095 | 0.005859 | 0.1172 | 1.15
+table8/row3 Gradient Boosting | RNN | -1.4029 | 0.000488 | 0.0664 | 4.86
+table8/row4 KNN | NLinear | +1.9138 | 0.000488 | 0.0664 | 22.29
+table8/row5 KNN | MIFlu | +2.2280 | 0.000488 | 0.0664 | 9.89
+table8/row6 KNN | LSTM | -1.2234 | 0.000488 | 0.0664 | 5.28
+table8/row7 iTransformer | TimeCMA | +1.3863 | 0.000488 | 0.0664 | 7.02
+table8/row8 iTransformer | SVR | -1.3443 | 0.000488 | 0.0664 | 10.61
+table9/row1 Encoder | MSE | vs MIFlu | PTE | PIE (%) | Passes
+table9/row2 Hunyuan-1.8B | 4.7374 | 3.04× | 4.406 | 71.428 | 0/16
+table9/row3 Hunyuan-7B | 4.7596 | 3.06× | 5.309 | 75.399 | 0/16
+table9/row4 DeepSeek-R1-Qwen-1.5B | 4.7866 | 3.07× | 5.792 | 78.061 | 0/16
+table9/row5 DeepSeek-R1-Llama-8B | 4.8250 | 3.10× | 4.306 | 77.121 | 0/16
+table9/row6 DeepSeek-R1-32B | 4.9372 | 3.17× | 3.889 | 77.730 | 0/16
+table9/row7 DeepSeek-R1-Qwen-14B | 5.0166 | 3.22× | 4.149 | 76.350 | 0/16
+table9/row8 DeepSeek-R1-Qwen-7B | 5.0308 | 3.23× | 4.458 | 76.373 | 0/16
+table9/row9 ContextPilot-8B | 5.0843 | 3.26× | 4.962 | 78.918 | 0/16
+table9/row10 Hunyuan-4B | 5.1317 | 3.30× | 3.003 | 78.840 | 0/16
+table9/row11 ContextPilot-14B | 5.1949 | 3.34× | 4.965 | 77.764 | 0/16
+table9/row12 Qwen2.5-1.5B | 5.2049 | 3.34× | 5.333 | 74.650 | 0/16
+table10/row1 Variant | Flag | Cells | Status
+table10/row2 Reference K=6 | default | 12 | Already in benchmark
+table10/row3 no_lora | --no-lora | 12 | Not aggregated
+table10/row4 K=2 | --num-layers 2 | 12 | Not aggregated
+table10/row5 K=4 | --num-layers 4 | 12 | Not aggregated
+table10/row6 K=8 | --num-layers 8 | 12 | Not aggregated
+table10/row7 K=12 | --num-layers 12 | 12 | Not aggregated
+table11/row1 Objective | Addressed | Estimated completion
+table11/row2 Reproduction arithmetic | Yes, source provenance limited | 100%
+table11/row3 28-arm benchmark export | Yes, arithmetic verified | 100%
+table11/row4 Peak and efficiency evaluation | Yes, interpretation corrected | 100%
+table11/row5 Frozen encoder axis | Yes, retained arms only | 100%
+table11/row6 Ablation | Partly, owner reports 27/60 | 45%
+table11/row7 Rolling origin | Code stage, not evaluated | 15%
+table11/row8 Manuscript | Draft; publication evidence incomplete | 70%
+table12/row1 Target date | Task | Expected output and fallback
+table12/row2 By 16 Nov 2026 | Pull and verify ablation exports | Measured table if complete; otherwise retain incomplete label
+table12/row3 16–20 Nov 2026 | Present to supervisor and assessor | Appointment and attendance must be confirmed by student
+table12/row4 20 Nov 2026 23:59 HKT | Submit through FYP InfoNet | Submission receipt; late penalties apply
+table12/row5 By 30 Nov 2026 | Regional table and timing provenance | Complete denominators and hardware details; no assumed trend
+table12/row6 By 31 Dec 2026 | Rolling origins and detector sensitivity | Season-level uncertainty and full-window sensitivity
+table12/row7 Jan–Apr 2027 | Publication decision | JBHI-oriented draft only if evidence and scope are adequate
--- progress_report_zh corrected upload
+++ progress_report_zh reviewed revision 4
@@ -1,170 +1,179 @@
-p0 提交：FYP InfoNet，2026 年 11 月 20 日 23:59 前
-p1 香港城市大学
-p2 电子工程学系   ·   毕业设计进度报告，2026/27 学年 A 学期
-p3 PART A
-p4 PART B
-p5 1. 项目目标
-p6 问题陈述。 流感预测直接影响公共卫生资源分配：何时升级响应、准备多少床位与疫苗、何时宣布某季已过峰值。Moon 等（IEEE JBHI 2025）提出 MIFlu——一个把 GPT-2 时间序列编码器与文本嵌入结合的多模态模型——并在 CDC 全国流感数据上报告了最佳精度。但该论文只与两个简单基线比较、只报告单一随机种子，且在测试集上选择检查点——这是数据泄漏。因此公共卫生团队无法回答真正重要的问题：MIFlu 是不是我们该部署的模型？如果不是，我们能否知道？
-p7 目标。
-p8 1. 用严格协议复现 MIFlu 的表 V（10 个种子、验证集选择检查点、7 变量聚合 MSE），量化与已发表数值的差距，包括每个跨度上的符号。
-p9 2. 在同一协议上基准评估 28 个预测模型（13 个传统模型 + 4 个基于 LLM 的预测器（MIFlu 与 3 个已发表）+ 11 个冻结 LLM 编码器），同时用精度（MSE/MAE）与峰值预测技巧（Kramer & Shaman 判据下的 PTE/PIE）计分。
-p10 3. 确定公共卫生团队应部署哪个模型，并用实验检验大语言模型是否真的改善流行病学预测。
-p11 范围。 本项目是实证评估，不是新架构。其贡献在于测量：无泄漏的协议、在同一窗口与种子下的 28 模型矩阵，以及把精度与部署价值分开的评估。本文不提出新的损失函数或提示机制，所主张的结论也不需要它们。
-p12 2. 原始项目规划图
-p13 •  2026 年 9 月（第 1-4 周）： 数据获取与验证（966 周 CDC 序列，逐字节校验）。里程碑：数据集确认一致——已完成。
-p14 •  2026 年 10 月（第 5-8 周）： MIFlu 代码重建、复现实验（10 个种子 x 4 个跨度）。里程碑：表 V 复现完成，并披露符号交叉——已完成。
-p15 •  2026 年 11 月（第 9-12 周）： 28 模型基准与冻结编码器维度；消融阶梯排队；进度报告与汇报。里程碑：基准完成——基准已完成，消融 27/60 运行中。
-p16 •  2026 年 12 月–2027 年 4 月： 区域评测、滚动原点评测、手稿、投稿。里程碑：已投稿手稿——计划中。
-p17 唯一的进度滑移是消融阶梯：原计划 11 月初完成，本报告时为 27/60。这是算力排队延迟，不是设计变更；区域评测排在其后，已移至 11 月下旬。
-p18 3. 背景研究
-p19 技术背景。 流感预测已从统计模型（ARIMA、Prophet）发展到深度学习（LSTM、Transformer），再到最近的大语言模型。MIFlu 属于最后一类：用 LoRA 适配器在 CDC 序列上微调 GPT-2 主干，并报告最佳聚合精度。它的比较集很薄，协议有两个问题——测试集选检查点与单一种子——而这正是独立复现与更广基准能发挥作用的空间。
-p20 当代与社会背景。 新冠疫情后，各国政府大量投资 AI 疫情预测，WHO 与 CDC 等机构用预测分配疫苗与抗病毒药物。只有当峰值的位置与幅度都正确时，预测才对这类决策有用：一条把峰值判断晚两周、或把峰值高度低估 40 % 的曲线，即使平均误差很小，也已经使决策失败。然而文献仍按 MSE 给模型排名。指标与决策之间的这道鸿沟，正是本项目要测量的对象。
-p21 识别的空白。 现有文献缺三样东西：(1) 一个移除测试集检查点泄漏的 MIFlu 复现；(2) 一个宽到足以包含线性与经典基线的基准；(3) 在公共卫生真正使用的判据上、与文献报告的判据并列的评估。本项目三者兼备。
-p22 4. 方法
-p23 设计。 两套协议，从不混用。复现协议（10 个种子 2021-2030；验证集选择检查点；7 变量聚合 MSE）用于与论文表 V 比较。基准协议（3 个种子 42/43/44；共享窗口 (W//16)*16 = 160/144/144/128；同一指标）用于 28 个模型互比。MIFlu 是唯一同时出现在两套协议下的模型，其两个数值不可比较。
-p24 表 1. 复现：本文 vs 原论文/仓库。
-p25 两项 [偏离] 为顶刊标准要求。
-p26 两处故意偏离。 (1) 检查点选择：原代码在测试集上选最优 epoch（main_ILI_lora.py 第 211、225 行），这是数据泄漏；我们改用验证集。(2) 7 变量指标：原测试加载器只覆盖 7 个变量中的 1 个（bug），而表 V 定义在 7 变量聚合上；我们修复加载器。两处偏离凡出现复现数字处均予披露。
-p27 指标与定义。 跨度 L = 预测未来周数（输入窗口 T = 104 周）。步 s = 计分第几个预测周（步 0 = 提前一周）。PTE（峰值时间误差）= |预测峰值周 - 观测峰值周|（周）；PIE（峰值强度误差）= |预测 - 观测峰值| / 观测峰值 x 100 %。只有 PTE <= 1 周且 PIE <= 25 % 时该格才通过 Kramer & Shaman 判据；阈值归因于 Kramer & Shaman（2019），并标注 [to verify] 待与原文核对。峰值检测器（find_peaks(prominence = 0.15 x range, distance = 15)，±8 周匹配）是本项目的工程选择，不是已发表判据的一部分。PTE/PIE 使用反归一化为患者人数的 ILITOTAL，因为 7 变量聚合是损失值而不是序列，无法反归一化。
-p28 更广背景下的设计影响。 评估被有意拆成部署真正面对的两个问题：曲线有多准（MSE）与预测能否支持决策（PTE/PIE）。把它们分开很重要，因为它们可能给出不同的排序；把二者合并成单一榜单会隐藏这个选择。基准也被设计为可重跑：每个单元记录 GPU、分区、节点与作业号，因此公共卫生团队可以审计这些数字，而不是只能相信它们。在一个已发表预测结果很少被重新推导的领域里，这是对可复现性的一点贡献。
-p29 6. 进度
-p30 本学期已完成的工作。
-p31 •  数据验证： 966 周 CDC 序列与作者文件逐字节相同（SHA-256，最大差 0）；切分 676/97/193 与包含约束已验证。
-p32 •  代码重建： 17 项保真修复（RevIN、LayerNorm、三个 dropout、drop_last、单变量 batch、seed、epsilon 等），每项都记录在偏离清单中。
-p33 •  复现： 40 次运行（10 个种子 x 4 个跨度），每个单元都以 |Δ| <= 1e-5 对照逐种子 oracle。
-p34 •  基准： 28 个模型 x 4 个跨度 x 3 个种子 = 336 个单元；其中 204 个（17 个传统模型）带逐单元 A100 来源记录，132 个编码器单元在同一分区运行并留有逐单元清单。
-p35 •  编码器维度： 11 个冻结编码器 x 12 个单元 = 132 个单元，MSE 与 PTE/PIE 已聚合。
-p36 •  分析： MSE/MAE、PTE/PIE、Kramer & Shaman 判据、帕累托前沿、对数参数回归，以及 136 对 Holm 校正配对检验。
-p37 •  消融阶梯： 已设计、以开关实现，本报告时完成 27/60 个单元。
-p38 •  文档： 六份报告（DOCX + PDF，中英）由 CSV 生成并带断言。
-p39 复现结果（7 变量聚合 MSE，10 种子均值）：
-p40 表 2. MIFlu 表 V 的复现——符号反转。7 变量 z 空间聚合 MSE，10 次重复，种子 2021–2030。
-p41 Δ 为正表示本文比论文更差。本文在 L24（−15.4 %）与 L36（−4.6 %）更好，在 L48（+17.0 %）与 L60（+23.4 %）更差；4 个跨度的均值在 MSE 上为 +4.5 %、在 MAE 上为 +7.9 %。唯一可辩护的表述是“在 4 个跨度的 MSE 均值上复现到 4.5 % 以内，且符号随跨度翻转”，绝不能说“我们超过了论文”。窗口为 (W//16)*16 = 160/144/144/128；A100-SXM4-80GB、stingy 分区、CityU HPC Burgundy。来源：ESSAY_VS_REPRODUCTION_TABLE_V.csv。
-p42 论文报告 1.542 / 1.422 / 1.414 / 1.364（均值 1.4355）。我们得到 1.3045 / 1.3561 / 1.6543 / 1.6829（均值 1.4995），即均值上差 4.5 %，符号交叉 2-2：L=24 与 L=36 更好，L=48 与 L=60 更差。MAE 一侧同样（0.8043 对 0.7452，+7.9 %）。
-p43 结论（复现）。 复现在四跨度均值上落在 4.5 % 以内，符号随跨度翻转——这是复现，不是改进。只报告均值会藏起这一结构；而两处已披露的偏离（验证集检查点、7 变量指标）意味着逐跨度的胜出不能主张为“优于原论文”。
-p44 基准结果（28 个模型，3 个种子，共享窗口）：
-p45 表 3. 28 个模型的基准：逐跨度与四跨度均值的 7 变量 z 空间聚合 MSE，以及四跨度 MAE。种子 42/43/44 取均值，共享窗口 (W//16)*16 = 160/144/144/128。
-p46 越低越好。为版面清晰省略逐跨度 MAE，其值在 02_数字表格/BENCH_MSE_BY_MODEL_L.csv 中。DLinear 按项目决定被排除（原论文表 V 已给出它的结果，因此不构成新的基线）。季节朴素基线（52 周滞后）在同一批窗口上的 4 跨度均值为 6.2132，28 个模型全部优于它。硬件：A100-SXM4-80GB、stingy 分区、CityU HPC Burgundy——17 个传统模型中 204/204 个单元均带该实测来源，MIFlu 与编码器单元在同一分区运行并留有逐单元清单。参数量取自 BENCH_EFFICIENCY.csv 的训练后总数；经典学习器在此意义上无参数量、MIFlu 未导出，故留空。
-p47 MIFlu 是精度冠军，1.5574，其后是 PatchTST（1.6621）与 NLinear（1.8716）；28 个模型的跨度为 1.5574 到 5.6155，即 3.6 倍。已发表的基于 LLM 的竞争者被最近邻基线击败（KNN 3.7854 对 Qwen-Time 5.2557、CALF 5.5785），11 个冻结编码器则位于 4.74-5.20 区间。
-p48 发现 F0——仅凭精度无法确定可部署的模型。 排名很容易产出、却很难据以行动：它说明哪个模型最拟合这个测试集，而不说明哪个模型支持预测本来要服务的决策。接下来的三项分析正是要回答排名回答不了的问题。
-p49 峰值技巧结果（PTE/PIE，Kramer & Shaman 判据；下表逐格展示三个具名模型）：
-p50 表 4. 同一判据的逐格展开：三个具名模型的每个（跨度，步）组合。PASS 要求同一格内 PTE ≤ 1 周且 PIE ≤ 25 %。
-p51 每模型 16 格 = 4 个跨度 × 4 个步，每格为种子 42/43/44 的均值。NLinear 通过 4/16，全部在步 0（PIE 2.4–4.2 %）；MIFlu 通过 4/16——三个在步 0、一个在 L=48 步 1，PIE 为 18.3–24.8 %，即贴着边界；PatchTST 一个都不通过，因为其 PIE 在每个步都停在 26–35 % 区间。峰值检测：find_peaks(prominence = 0.15 × range, distance = 15) 与 ±8 周匹配——本研究的工程选择，不是已发表判据的一部分。1 周 / 25 % 阈值归因于 Kramer & Shaman (2019)，但仍标注 [to verify]，待与原文核对。
-p52 NLinear 与 MIFlu 各通过 4/16，但方式不同：NLinear 通过全部四个步 0 单元，PIE 为 3.2 %；MIFlu 的四个通过点 PIE 为 18.3-24.8 %，贴着 25 % 边界，且在 L=48 步 0 失败。PatchTST 一个都不通过：它的时序是本研究最准的（均值 PTE 1.24 周），但 PIE 为 32.8 %。
-p53 发现 F1——部署排序不是精度排序。 在全部 28 个模型上，MSE 更好确实伴随校准更好（对均值 PIE 的 Spearman ρ = +0.74），所以 MSE 是有用的筛选；但前沿的排序正好相反。MSE 最低的三个模型中，校准排序完全反转（NLinear 9.5 %、MIFlu 26.8 %、PatchTST 32.8 %），且通过标记与 MSE 呈负秩相关（ρ = -0.43，p = 0.023）。MSE 第二名一个都不通过；第三名通过每个跨度的提前一周。
-p55 三个具名模型的步 0 峰值技巧。 左：步 0 的峰值时间误差（周），对四个跨度取均值，虚线为 1 周阈值。右：步 0 的峰值强度误差（%），虚线为 25 % 阈值。绿色 = 在阈值内，红色 = 超出。MIFlu（0.35 周，18.9 %）与 NLinear（0.21 周，3.2 %）在均值层面同时位于两个阈值之内，而 PatchTST（0.68 周，30.6 %）未满足强度一半——这正是“平均误差好”与“峰值校准好”分离的视觉形态。种子 42/43/44；窗口 (W//16)*16 = 160/144/144/128。
-p56 效率与显著性。 在 11 个含参数模型上，MSE 对 log10(参数量) 的斜率为 +0.1171、R² = 0.0223：规模只解释约 2 % 的方差，且符号不利。帕累托集合恰好 {NLinear 2,520 参数；PatchTST 531,878 参数}，即 211 倍参数换取 11.2 % 的 MSE 下降。在 12 个配对单元上，136 对中有 128 对在校正前显著；正确 Holm 校正后无一存活（最小可达校正 p 为 0.066），NLinear-PatchTST 的 p(Holm) = 0.117。
-p57 表 5. 12 个配对（跨度 × 种子）单元上的配对符号翻转检验，对全部 136 对做 Holm 校正（由原始 p 值重算）。第一行（粗体）为正文讨论的帕累托对；其余为 p 值最小的六对，用作对照。
-p58 Δ 为正表示模型 A 的 MSE 更大。12 个单元全部配对（同跨度、同种子），这只有在所有模型统一使用 42/43/44 时才成立。导出的 p_holm 列由反向累积最小值生成，不是有效的 Holm 校正；本表的值由 p_raw 重算。n = 12 时最小可达原始 p 为 2/2¹² ≈ 0.00049，因此在 m = 136 对下最小可达校正 p 为 0.066，没有任何一对能在 0.05 水平存活（校正前有 128/136 对显著）。第一行为何不在第二块中：NLinear 对 PatchTST 的校正 p = 0.117，在 136 对中排第 117 小，因此按显著性排序的表会恰好省略帕累托论证所需的那一对。该差异在这个样本量下无法分辨；这是“未能拒绝”，不是“证明相等”（d = 1.15，且 PatchTST 在 12 个单元中有 10 个更低）。
-p59 发现 F2（效率）。 参数量不是精度的代理：斜率为正、R² 只有 0.0223。前沿是两个模型之间的权衡，不是排名。
-p60 发现 F3（显著性）。 211 倍成本换来的 11.2 % MSE 差异，在本基准的 n = 12 下无法分辨。这是“未能拒绝相等”，不是“证明相等”（d = 1.15；PatchTST 在 12 个单元中的 10 个更低），因此可辩护的结论是“未能为 211 倍成本确立精度优势”，结合 F1，这使 NLinear 成为可辩护的默认选择。
-p62 精度—效率帕累托前沿。 x 为参数量（对数轴），y 为 4 个跨度的 7 变量 z 空间 MSE 均值；阶梯线为帕累托集合 {NLinear 2,520 参数；PatchTST 531,878 参数}。PatchTST 用 211 倍参数量换取 11.2% 的 MSE 下降；MSE 对 log₁₀(参数量) 的拟合斜率为 +0.1171，R² = 0.0223，即规模只能解释约 2% 的方差且符号为正。窗口为共享的 (W//16)*16 = 160/144/144/128；种子 42/43/44。由 plot_pareto.py 生成。硬件：A100-SXM4-80GB，stingy 分区，CityU HPC Burgundy。
-p63 冻结 LLM 编码器。 11 个编码器（Qwen2.5-1.5B、五个尺寸的 DeepSeek-R1-Distill、Hunyuan-1.8B/4B/7B、ContextPilot-8B/14B），每个冻结后接一个共享线性头，156 个单元中完成 132 个。最好的是 Hunyuan-1.8B，4.7374；最差的是 Qwen2.5-1.5B，5.2049，即 MIFlu 的 3.04 至 3.34 倍；每一个都差于决策树，且没有任何一个在任何单元通过 Kramer & Shaman 判据。
-p64 发现 F4——冻结 LLM 表征不能迁移到本任务。 协议被设计成给该想法最好的机会（冻结特征、线性读出、通道独立），而它仍然失败。这不能证明编码器永远不可能有帮助，但它确实意味着：任何声称在本任务上从冻结语言特征获得增益的主张，都需要给出机制与对照。
-p65 消融阶梯（项目计划中的表 VIII）。 五个变体——去掉 LoRA，以及 K = 2、4、8、12 层——在 4 个跨度与 3 个种子上共 60 个单元，与已在基准表中的完整 K=6 臂比较。阶梯回答 MIFlu 的精度从何而来：LoRA 适配，还是堆叠深度。本报告时 60 个单元中完成 27 个，因此不声明任何深度趋势。有一项结果已经确立：文本 token 位于因果掩码之后、输出头只读时间分片，因此 --no-text 与完整臂逐位相同——这是结构验证（由 tests_archive/test_miflu_ablations.py 断言），不是消融效应。
-p66 发现 F5（暂定）。 文本分支位于预测路径之外，因此按已交付的架构，多模态主张得不到支持；深度与 LoRA 的问题要等 60 个单元聚合后才能回答。此处报告的是设计与状态，不是结果。
-p67 遇到的问题。 (1) 原代码在测试集上选检查点，且测试加载器只对 7 个变量中的 1 个计分；两者均已识别并修复，并作为偏离披露。(2) 评测窗口规则是 drop_last=True 的副作用；为所有模型统一采用它是必要的，否则就等于给 MIFlu 一个更容易的测试。(3) 训练流水线中发现八项工程缺陷（种子未进入 LLM 路径、快照克隆了冻结编码器、两种缓存布局、非原子锁）；七项已修复，一项作为运行风险仍未解决。(4) 消融阶梯因共享 A100 分区排队从 11 月初滑至 11 月下旬。
-p68 7. 目标完成与成果总结
-p69 表 6. 已完成的目标与迄今取得的成果
-p70 百分比为截至 2026 年 11 月 3 日各目标的完成度估计。
-p72 8. 未来 1-2 个月的工作计划与预期成果
-p73 表 7. 未来一到两个月的工作安排与预期成果
-p74 日期为目标而非承诺；凡注明之处为实测 GPU 机时，其余为推算。
-p75 风险与应对。 (1) 共享 A100 分区的排队竞争是消融滑期的原因；阶梯以单个 60 单元作业提交，因此不会被逐单元饿死。(2) 判据归属：1 周 / 25 % 阈值标注 [to verify]，投稿前会对照 Kramer & Shaman 原文核对；峰值检测器明确声明为本研究的选择，使读者能把判据与实现分开。(3) 单一数据集：区域评测与滚动原点评测就是应对措施；若来不及完成，论文将陈述这一局限，而不是外推。(4) 范围：若投稿时消融或表 VI 仍未完成，手稿将像本报告一样只报告设计与状态——不写趋势，不编数字。
-p76 手稿草稿已按这些结果写好（IEEE 结构，中英两版；投稿前为单栏评审稿）；剩余工作是把消融阶梯、区域表以及（若预算允许）滚动原点评测并入。投稿目标为 IEEE JBHI；若滚动原点结果及时到位，则以 CCF-B 会议为备选。
-p77 日期：_____________    学生签名：_____________
-table1/row1 学生姓名 | ________________________________
-table1/row2 学生编号 | ________________________________
-table1/row3 课程—主修 | 电机工程工学士 / ______________
-table1/row4 项目编号与题目 | ________  复现 MIFlu 并以冻结 LLM 编码器基准评估流感预测
+p0 CITY UNIVERSITY OF HONG KONG
+p1 电子工程学系   进度报告   2026/27 学年 A 学期
+p2 PART A
+p3 PART B
+p4 1. 项目目标
+p5 问题陈述。 全国流感预测曲线即使平均误差较低，仍可能出现峰值时间或高度错误。本项目独立复现 MIFlu，并检验同时考虑峰值误差与参数量后模型选择如何变化。项目从精度、峰值技巧、参数效率和统计证据四个维度评估，并明确各维度覆盖的模型子集。
+p6 目标。 （1）复现并解释表 V。（2）在统一窗口下比较 28 个保留实现。（3）评估峰值时间、幅度与参数取舍。（4）测试特定冻结编码器迁移设置。（5）在声称部署价值前，以多个原点及区域验证结论。
+p7 2. 原始项目规划图
+p8 表 1. 原计划时段与当前证据
+p9 此表根据所附计划重构，并标注 2026 年 11 月 3 日状态；未提供当时签署的九月原始图表。
+p10 3. 背景研究
+p11 分块与线性基线已有研究 [3–5]。Time-LLM、CALF 与 TimeCMA 的对齐及适配设计不同 [6–8]。Chronos、TimesFM、Moirai、Lag-Llama 在数值序列上预训练，本次未评测 [9–12]。较早的 LLM 移除研究已质疑语言预训练收益 [13]，而 2026 年预印本报告跨数据集偏移下的条件性收益 [14]。本项目贡献在于特定流感任务的协议审计与多指标比较。
+p12 全球与社会背景。 峰值预测可能帮助准备及容量规划，但全国回顾性精度不能衡量临床收益。透明评估有助于减少对复杂模型的不当投入，并揭示失败方式。本项目未测量真实资源节省或患者结局效应 [2,18]。
+p13 4. 方法
+p14 表 2. 分开的复现与基准协议
+p15 三个种子是算力预算选择，不是统一的会议规则。复现与基准采用不同种子集合，不能相互替换。作者上游具体协议缺陷仍须对照固定版本核实。
+p16 本项目采用时序划分、仅训练段拟合标准化，并用验证集选择检查点。交接资料将测试集选检查点及单变量加载问题归于上游代码，但未提供固定版本作者仓库，公开端点也未能打开，因此上游指控仍未核实。笔记还列出代码默认学习率与原文设置的差异，不能称为仅有两处偏离。
+p17 峰值时间误差 PTE 是预测与观测峰值周的绝对差。峰值强度误差 PIE 为峰高绝对差除以观测峰高后乘百分比。Kramer–Shaman [2] 可核实分别为一周与 25% 的容差。项目把两者联合应用于（模型、L、step）单元的平均误差；该联合筛选及峰检测属于项目选择，不是临床接受标准。平均误差达标不等于逐季成功概率。
+p18 设计影响。 所有保留模型采用相同裁剪窗口，标准化仅在训练数据拟合。七变量均值无量纲，峰值误差则使用患者人数尺度的 ILITOTAL。这样能够透明比较，同时不把联合筛选误称为公共卫生安全认证。基准的三个种子反映算力限制，不确定性仍需更多独立季节。
+p20 6. 进度
+p21 对照计划的进度。 所附导出包含复现表和 28 × 4 × 3 基准单元聚合。原测试已包含在 tests_archive/，但本环境无法完整收集。本次审计重算 CSV 聚合，并新增七个 CPU 测试。消融仍为用户报告的 27/60，未逐变体聚合。区域与滚动原点评测尚未完成。
+p22 表 3. MIFlu 复现与原文对照
+p23 来源：ESSAY_VS_REPRODUCTION_TABLE_V.csv 第 2–6 行。标准差由代码中转录的十种子 oracle 重算；原始运行日志未随包提供。正差表示误差更高。
+p24 复现 CSV 的平均 MSE 为 1.4995，对照 1.4355，增加 4.5%。L24、L36 更低，L48、L60 更高。平均 MAE 为 0.8043，对照 0.7452（+7.9%），但逐跨度为一低三高；MAE 没有 MSE 的二比二符号交叉。协议差异与上游来源缺失限制了精确复现的主张。
+p25 复现结论。 观测平均 MSE 差为 +4.5%。尚存协议与来源差异，不能声称精确复现或优于原文。
+p27 表 4. 全部保留模型的精度
+p28 来源：BENCH_MSE_BY_MODEL_L.csv，按 model 和 L 定位。各行由三个种子在 160/144/144/128 个窗口上聚合。项目主动排除了 DLinear，发表前需补充理由与敏感性分析。名称指本项目实现，排名本身不能证明与原论文方法完全等价。
+p29 F0 结论。 MIFlu 的观测 MSE 最低（1.5574），但仅靠 MSE 不能证明公共卫生效用。前三名相对 MIFlu 的跨度为 20.2%，并非小于 20%。
+p30 表 5. 各跨度与提前步的联合峰值筛选
+p31 每格为 PTE（周）/ PIE（%）。s0–s3 是预测的第 1–4 周。峰检测使用突出度 0.15 × 极差、间距 15、±8 周匹配。检测设置及联合聚合均为项目选择。来源：BENCH_PTE_PIE_BY_STEP.csv。
+p32 F1 结论。 NLinear 与 MIFlu 各通过 4/16 个聚合单元，PatchTST 为 0/16。NLinear 的平均 PIE 更低（9.477%，MIFlu 为 26.846%），但平均 PTE 更高（1.677 周，MIFlu 为 1.128 周）。这是时间与幅度的取舍，不是全面优越。前三模型的排序在两端倒置：MSE 顺序为 MIFlu、PatchTST、NLinear，PIE 顺序为 NLinear、MIFlu、PatchTST。
+p34 三个领先模型在提前步零上跨跨度的平均 PTE 与 PIE。均值容差线仅用于说明；MIFlu 在 L48 提前步零仍未通过。平均误差小于阈值不等于逐季成功率。来源：BENCH_PTE_PIE_BY_STEP.csv。
+p35 表 6. 参数分析与秩相关
+p36 帕累托分析只纳入有参数量导出的 11 个模型，未包括 MIFlu 与冻结编码器。缺失参数量不等于零。参数量不等于延迟、内存或能耗。相关系数只是同一测试集上跨模型的描述性结果。
+p37 F2 结论。 在导出参数量的 11 个模型中，拟合斜率为 +0.1171，R² 为 0.0223。规模单独解释的观测 MSE 变化很少。该子集结果不能证明容量无关紧要。
+p38 表 7. 使用正确 Holm 校正的配对比较
+p39 136 对来自 17 个模型，并未覆盖全部 28 个模型。n = 12 个配对跨度 × 种子单元。前向累计最大值 Holm 得到 0/136 个拒绝。所示 p 值由六位小数导出恢复 1/4096 枚举网格；直接从四舍五入导出重算时，NLinear–PatchTST 为 0.117180，而非 0.1171875。*源效应量采用模型合并标准差，不是配对差的标准差。单元相关性限制统计推断。
+p40 F3 结论。 正确 Holm 校正为 0/136 个拒绝（校正前 128/136），最小校正 p 约 0.0664，NLinear–PatchTST 的 p ≈ 0.1172。PatchTST 的观测 MSE 仍低 11.2%，参数多 211 倍，并在 10/12 单元中误差更低。未拒绝不能证明等价，也不能断言增益是噪声。
+p42 11 个导出参数量模型的精度与参数取舍。此子集未包括 MIFlu 与冻结编码器。参数量不是实测运行时间或内存代价。来源：BENCH_EFFICIENCY.csv。
+p43 表 8. 冻结编码器加共享线性读出
+p44 11 个保留编码器 × 4 跨度 × 3 种子 = 132 单元。历史计划还包含两个仅嵌入模型，总计 156 单元；未纳入的 24 单元不属于 28 模型正式名单。此结果只评价该冻结特征流程。
+p45 F4 结论。 所测 11 个冻结编码器的 MSE 为 4.7374–5.2049，是 MIFlu 的 3.04–3.34 倍，全部高于决策树的 4.3198，且均通过 0/16 单元。这是该特征与读出配置的负面结果；提示、微调及数值时序基础模型仍未检验。
+p46 表 9. 消融设计与快照状态
+p47 用户报告截至 2026 年 11 月 3 日：新增 60 单元中完成 27，作业 722968。本次未连接 HPC，也无逐变体结果导出。参考 12 单元不计入新增 60 单元。不推断趋势。
+p48 F5 暂定结论。 miflu_model.py 的 author_faithful 路径将文本置于时间词元之后，使用因果注意力，预测头只读取时间词元。静态检查因此推断确定性评估时文本不影响输出。所附 tests_archive/test_miflu_ablations.py 明确断言文本不变性，以及匹配 CPU 初始化时完整与无文本模型相同。本次仅静态检查，未执行。其他融合路径及训练随机性须分别验证。
+p49 遇到的问题。 源 CSV 导出的 Holm 列仍有误；修正语料已重新计算正确校正。模型名单算术、MAE 交叉、硬件覆盖与测试缺失也需修正。离线快照不能认证实时排队状态。我将冻结修正后的报告路径，并保留所有原 CSV 便于对照。
+p50 7. 已处理目标与迄今成果总结
+p51 表 10. 已处理目标与估计完成度
+p52 这些是任务给定的项目进度估计，不是研究评分。45% 等于 27/60；其他比例未独立测量。
+p53 8. 未来一至两月安排及预期成果
+p54 表 11. 工作安排与预期产物
+p55 日期为目标，能否执行取决于排队、实测运行时间与导师决定；此表不推断会议截止日。
+p56 风险与应对。 排队可能妨碍消融完成，因此须保留明确未完成标签。验证日期映射并采用逐季滚动原点，以处理时间相关。发表前恢复原测试并固定依赖版本。与导师及评阅人确认汇报预约。学校模板要求完成汇报，并按时经 InfoNet 提交。
+p57 日期 ____________________    学生签名 ____________________
+p58 背景与方法使用的关键文献列于下方，编号与内部报告及手稿一致。
+p59 [1] Jaeuk Moon 等，基于大语言模型的多模态流感预测方案（中文译名），2025。https://doi.org/10.1109/JBHI.2025.3561214
+p60 [2] Sarah C. Kramer 等，针对温带及热带六十四国的流感预测开发与验证（中文译名），2019。https://doi.org/10.1371/journal.pcbi.1006742
+p61 [9] Abdul Fatir Ansari et al. 等，学习时间序列语言的 Chronos 方法（中文译名），2024。https://arxiv.org/abs/2403.07815
+p62 [13] Mingtian Tan 等，语言模型真的有助于时间序列预测吗（中文译名），2024。https://arxiv.org/abs/2406.16964
+p63 [14] Xin Qiu et al. 等，重新思考大语言模型在时间序列预测中的作用（中文译名），2026。https://arxiv.org/abs/2602.14744
+p64 [18] Johannes Bracher 等，以区间格式评估传染病预测（中文译名），2021。https://doi.org/10.1371/journal.pcbi.1008618
+table1/row1 学生姓名 | CHAN Sing Yeung
+table1/row2 学生编号 | ____________________
+table1/row3 课程主修 | ____________________
+table1/row4 项目编号与题目 | ________ MIFlu 复现与流感预测审计
 table1/row5 导师姓名 | Prof. Katie CHAN
-table1/row6 评阅人姓名 | ________________________________
-table1/row7 与导师 / 评阅人会面次数 | ______ / ______
-table1/row8 每周平均投入时数 | ________ 小时/周
-table1/row9 报告日期 | 2026 年 11 月 3 日
-table2/row1 参数 | 本文 | 原论文 | 说明
-table2/row2 数据 | 966 周 x 7 变量 | 相同 | 字节一致
-table2/row3 切分 | 676/97/193 | 相同 | 按时间
-table2/row4 输入窗口 T | 104 周 | 相同 | 
-table2/row5 跨度 L | 24/36/48/60 | 相同 | 独立训练
-table2/row6 种子（复现） | 2021-2030（10 次） | fix_seed=2021（1 次） | [偏离] 论文声称 10 次
-table2/row7 轮数 | 20 | 默认=1 | 1 轮不收敛
-table2/row8 学习率 | 1e-4 | 代码 1e-4 / 论文 5e-4 | 论文矛盾
-table2/row9 批大小 | 16 | 相同 | drop_last=True
-table2/row10 优化器 | Adam | 相同 | 
-table2/row11 GPT-2 层数/d_model | 6/768 | 相同 | 
-table2/row12 LoRA | r=4, a=4, drop=0.05 | 相同 | 
-table2/row13 可训练参数 | 1,673,496 | 相同 | LoRA+LN+头
-table2/row14 Checkpoint 选择 | 验证集 MSE | 测试集 MSE | [偏离] 测试=数据泄漏
-table2/row15 指标 | 7 变量聚合 MSE/MAE | 相同（bug: 1 变量） | [偏离] 修复 bug
-table2/row16 评测窗口 | (W//16)*16 | 相同 | 非期刊要求
-table3/row1 跨度 | 本文（10 次均值 ± 标准差） | 论文 | Δ MSE | 符号 | 本文 MAE | 论文 MAE | Δ MAE
-table3/row2 L=24 | 1.3045 ± 0.0883 | 1.542 | -15.4 % | 胜 | 0.7482 | 0.726 | +3.1 %
-table3/row3 L=36 | 1.3561 ± 0.1603 | 1.422 | -4.6 % | 胜 | 0.7712 | 0.779 | -1.0 %
-table3/row4 L=48 | 1.6543 ± 0.1064 | 1.414 | +17.0 % | 负 | 0.8381 | 0.757 | +10.7 %
-table3/row5 L=60 | 1.6829 ± 0.2109 | 1.364 | +23.4 % | 负 | 0.8596 | 0.719 | +19.6 %
-table3/row6 4 跨度均值 | 1.4995 | 1.435 | +4.5 % | 负 | 0.8043 | 0.745 | +7.9 %
-table4/row1 # | 模型 | 族 | MSE L24 | MSE L36 | MSE L48 | MSE L60 | MSE 4L | MAE 4L | 参数量
-table4/row2 1 | MIFlu | 基于 LLM | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199 | —
-table4/row3 2 | PatchTST | Transformer | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786 | 531,878
-table4/row4 3 | NLinear | 线性 | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183 | 2,520
-table4/row5 4 | DNN | 神经网络 | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057 | 33,048
-table4/row6 5 | TimeCMA | 基于 LLM | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676 | 125,830,824
-table4/row7 6 | Gradient Boosting | 经典机器学习 | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521 | —
-table4/row8 7 | KNN | 经典机器学习 | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293 | —
-table4/row9 8 | Random Forest | 经典机器学习 | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779 | —
-table4/row10 9 | iTransformer | Transformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476 | 75,672
-table4/row11 10 | Decision Tree | 经典机器学习 | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798 | —
-table4/row12 11 | Hunyuan-1.8B | 冻结 LLM 编码器 | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755 | —
-table4/row13 12 | Hunyuan-7B | 冻结 LLM 编码器 | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685 | —
-table4/row14 13 | DeepSeek-R1-Qwen-1.5B | 冻结 LLM 编码器 | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002 | —
-table4/row15 14 | DeepSeek-R1-Llama-8B | 冻结 LLM 编码器 | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786 | —
-table4/row16 15 | GRU | 神经网络 | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174 | 14,424
-table4/row17 16 | DeepSeek-R1-32B | 冻结 LLM 编码器 | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935 | —
-table4/row18 17 | LSTM | 神经网络 | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303 | 18,712
-table4/row19 18 | DeepSeek-R1-Qwen-14B | 冻结 LLM 编码器 | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019 | —
-table4/row20 19 | DeepSeek-R1-Qwen-7B | 冻结 LLM 编码器 | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133 | —
-table4/row21 20 | RNN | 神经网络 | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634 | 5,848
-table4/row22 21 | ContextPilot-8B | 冻结 LLM 编码器 | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255 | —
-table4/row23 22 | Hunyuan-4B | 冻结 LLM 编码器 | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450 | —
-table4/row24 23 | ContextPilot-14B | 冻结 LLM 编码器 | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407 | —
-table4/row25 24 | Qwen2.5-1.5B | 冻结 LLM 编码器 | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725 | —
-table4/row26 25 | Qwen-Time | 基于 LLM | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794 | 1,544,084,680
-table4/row27 26 | SVR | 经典机器学习 | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986 | —
-table4/row28 27 | CALF | 基于 LLM | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190 | 126,421,416
-table4/row29 28 | CNN | 神经网络 | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720 | 22,488
-table5/row1 模型 | 跨度 | 步0（1周） | 步1（2周） | 步2（3周） | 步3（4周）
-table5/row2 NLinear | L=24 | PASS (0.11 wk, 3.9 %) | fail (1.33 wk, 8.4 %) | fail (2.33 wk, 11.9 %) | fail (2.67 wk, 18.7 %)
-table5/row3 NLinear | L=36 | PASS (0.33 wk, 4.2 %) | fail (1.33 wk, 7.2 %) | fail (2.11 wk, 15.3 %) | fail (2.67 wk, 18.1 %)
-table5/row4 NLinear | L=48 | PASS (0.22 wk, 2.4 %) | fail (1.22 wk, 4.7 %) | fail (2.22 wk, 10.0 %) | fail (2.78 wk, 16.7 %)
-table5/row5 NLinear | L=60 | PASS (0.17 wk, 2.5 %) | fail (1.44 wk, 4.5 %) | fail (2.56 wk, 10.0 %) | fail (3.33 wk, 13.0 %)
-table5/row6 MIFlu | L=24 | PASS (0.00 wk, 18.3 %) | fail (0.89 wk, 26.7 %) | fail (1.22 wk, 30.5 %) | fail (1.33 wk, 31.6 %)
-table5/row7 MIFlu | L=36 | PASS (0.00 wk, 18.7 %) | fail (0.78 wk, 26.3 %) | fail (1.67 wk, 31.5 %) | fail (1.33 wk, 32.4 %)
-table5/row8 MIFlu | L=48 | fail (1.22 wk, 18.0 %) | PASS (0.67 wk, 24.8 %) | fail (1.22 wk, 30.1 %) | fail (1.33 wk, 33.2 %)
-table5/row9 MIFlu | L=60 | PASS (0.17 wk, 20.5 %) | fail (1.33 wk, 25.8 %) | fail (2.22 wk, 29.8 %) | fail (2.67 wk, 31.2 %)
-table5/row10 PatchTST | L=24 | fail (0.67 wk, 30.6 %) | fail (1.00 wk, 34.0 %) | fail (1.22 wk, 33.6 %) | fail (1.22 wk, 30.7 %)
-table5/row11 PatchTST | L=36 | fail (1.00 wk, 26.2 %) | fail (1.67 wk, 32.2 %) | fail (1.33 wk, 31.2 %) | fail (1.33 wk, 33.9 %)
-table5/row12 PatchTST | L=48 | fail (0.56 wk, 30.4 %) | fail (1.33 wk, 30.9 %) | fail (0.89 wk, 35.2 %) | fail (0.89 wk, 35.0 %)
-table5/row13 PatchTST | L=60 | fail (0.50 wk, 35.0 %) | fail (1.67 wk, 34.3 %) | fail (2.22 wk, 35.7 %) | fail (2.33 wk, 35.1 %)
-table6/row1 模型 A | 模型 B | n | 平均 Δ MSE | A 胜 | p（Holm） | 效应量 d
-table6/row2 NLinear | PatchTST | 12 | +0.2095 | 2/12 | 0.1172 | 1.15
-table6/row3 Gradient Boosting | RNN | 12 | -1.4029 | 12/12 | 0.06637 | 4.86
-table6/row4 CALF | RNN | 12 | +0.5111 | 0/12 | 0.06637 | 1.65
-table6/row5 CALF | SVR | 12 | +0.2397 | 0/12 | 0.06637 | 1.82
-table6/row6 CALF | TimeCMA | 12 | +2.9704 | 0/12 | 0.06637 | 14.78
-table6/row7 CNN | Decision Tree | 12 | +1.2957 | 0/12 | 0.06637 | 2.69
-table6/row8 CNN | DNN | 12 | +3.4740 | 0/12 | 0.06637 | 6.43
-table7/row1 # | 目标 | 是否完成 | 完成度
-table7/row2 1 | 按作者协议复现 MIFlu 表 V，并如实报告结果（包括符号反转） | 是 | 100 %
-table7/row3 2 | 在同一数据、同一划分、同一窗口上建立传统预测模型的同条件基准 | 是 | 100 %
-table7/row4 3 | 用流行病学接受判据（PTE/PIE）而非仅用 MSE 评估基准 | 是 | 100 %
-table7/row5 4 | 增加新的评测维度：以冻结 LLM 编码器作为特征提取器 | 是：11 个模型已完成，MSE/PTE/PIE 已聚合入表 | 100 %
-table7/row6 5 | 消融阶梯（计划中的表 VIII）与区域评测（表 VI） | 消融 27/60，运行中；区域评测排队其后 | 45 %
-table7/row7 6 | 滚动原点（walk-forward）评测 | 代码就绪，未运行（155–360 A100 机时） | 15 %
-table7/row8 7 | 论文手稿与明确的贡献 | 草稿完成；贡献定位为实证评估 | 70 %
-table8/row1 日期 | 工作 | 预期成果
-table8/row2 2026-11-16 前 | 消融阶梯跑完（60/60）；取回逐变体导出并补入表中 | 带实测深度趋势的消融表
-table8/row3 2026-11-20 前 | 提交进度报告，并向导师与评阅人汇报 | 报告已交；汇报已完成
-table8/row4 2026-11-30 前 | 表 VI 区域（21 个单元，约 22 分钟/单元）与据单元清单生成的表 IX | 区域表，21/21 个单元
-table8/row5 2026-12-31 前 | 滚动原点批次（1020 个单元，155–360 A100 机时）；首批折完成 | walk-forward 结果，5 折
-table8/row6 2027 年 1–4 月 | 手稿修订、内部评审、投稿 IEEE JBHI | 已投稿手稿
+table1/row6 评阅人姓名 | ____________________
+table1/row7 与导师及评阅人会面次数 | ______ / ______
+table1/row8 每周平均项目时数 | ______ hours/week
+table2/row1 时段 | 计划工作 | 快照状态
+table2/row2 2026 年 9 月 | 阅读 MIFlu 并确定数据约定 | 本地数据一致性已核实
+table2/row3 2026 年 10 月 | 复现表 V | CSV 与 oracle 算术已核实
+table2/row4 2026 年 11 月 | 基准、消融与进度汇报 | 28 模型 CSV 完整；消融报告为 27/60
+table2/row5 2026 年 11–12 月 | 区域与滚动原点验证 | 快照中尚未完成
+table2/row6 2027 年 1–4 月 | 强化手稿并决定投稿 | 计划中，取决于验证结果
+table3/row1 项目 | 复现 | 基准
+table3/row2 种子 | 2021–2030 (10) | 42/43/44 (3)
+table3/row3 模型 | MIFlu | 13 传统 + 4 基于 LLM + 11 冻结编码器
+table3/row4 选择 | 验证集检查点 | 验证集检查点
+table3/row5 指标 | 7-variable z-space MSE / MAE | 7-variable MSE / MAE; ILITOTAL PTE / PIE
+table3/row6 窗口 | 160 / 144 / 144 / 128 | 160 / 144 / 144 / 128
+table4/row1 跨度 | 本文 MSE ± 标准差 | 原文 MSE | Δ MSE | 本文 MAE | 原文 MAE | Δ MAE
+table4/row2 L=24 | 1.3045 ± 0.0883 | 1.5420 | -15.4% | 0.7482 | 0.7260 | +3.1%
+table4/row3 L=36 | 1.3561 ± 0.1603 | 1.4220 | -4.6% | 0.7712 | 0.7790 | -1.0%
+table4/row4 L=48 | 1.6543 ± 0.1064 | 1.4140 | +17.0% | 0.8381 | 0.7570 | +10.7%
+table4/row5 L=60 | 1.6829 ± 0.2109 | 1.3640 | +23.4% | 0.8596 | 0.7190 | +19.6%
+table4/row6 四跨度均值 | 1.4995 | 1.4355 | +4.5% | 0.8043 | 0.7452 | +7.9%
+table5/row1 # | 模型 | L24 | L36 | L48 | L60 | 平均 MSE | 平均 MAE
+table5/row2 1 | MIFlu | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199
+table5/row3 2 | PatchTST | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786
+table5/row4 3 | NLinear | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183
+table5/row5 4 | DNN | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057
+table5/row6 5 | TimeCMA | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676
+table5/row7 6 | Gradient Boosting | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521
+table5/row8 7 | KNN | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293
+table5/row9 8 | Random Forest | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779
+table5/row10 9 | iTransformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476
+table5/row11 10 | Decision Tree | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798
+table5/row12 11 | Hunyuan-1.8B | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755
+table5/row13 12 | Hunyuan-7B | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685
+table5/row14 13 | DeepSeek-R1-Qwen-1.5B | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002
+table5/row15 14 | DeepSeek-R1-Llama-8B | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786
+table5/row16 15 | GRU | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174
+table5/row17 16 | DeepSeek-R1-32B | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935
+table5/row18 17 | LSTM | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303
+table5/row19 18 | DeepSeek-R1-Qwen-14B | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019
+table5/row20 19 | DeepSeek-R1-Qwen-7B | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133
+table5/row21 20 | RNN | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634
+table5/row22 21 | ContextPilot-8B | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255
+table5/row23 22 | Hunyuan-4B | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450
+table5/row24 23 | ContextPilot-14B | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407
+table5/row25 24 | Qwen2.5-1.5B | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725
+table5/row26 25 | Qwen-Time | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794
+table5/row27 26 | SVR | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986
+table5/row28 27 | CALF | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190
+table5/row29 28 | CNN | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720
+table6/row1 模型 | L | s0 | s1 | s2 | s3
+table6/row2 NLinear | 24 | PASS 0.111 / 3.949 | fail 1.333 / 8.411 | fail 2.333 / 11.943 | fail 2.667 / 18.739
+table6/row3 NLinear | 36 | PASS 0.333 / 4.181 | fail 1.333 / 7.222 | fail 2.111 / 15.313 | fail 2.667 / 18.145
+table6/row4 NLinear | 48 | PASS 0.222 / 2.419 | fail 1.222 / 4.727 | fail 2.222 / 9.979 | fail 2.778 / 16.655
+table6/row5 NLinear | 60 | PASS 0.167 / 2.450 | fail 1.444 / 4.542 | fail 2.556 / 9.952 | fail 3.333 / 13.000
+table6/row6 MIFlu | 24 | PASS 0.000 / 18.307 | fail 0.889 / 26.686 | fail 1.222 / 30.472 | fail 1.333 / 31.638
+table6/row7 MIFlu | 36 | PASS 0.000 / 18.695 | fail 0.778 / 26.333 | fail 1.667 / 31.514 | fail 1.333 / 32.427
+table6/row8 MIFlu | 48 | fail 1.222 / 18.004 | PASS 0.667 / 24.795 | fail 1.222 / 30.133 | fail 1.333 / 33.236
+table6/row9 MIFlu | 60 | PASS 0.167 / 20.530 | fail 1.333 / 25.799 | fail 2.222 / 29.790 | fail 2.667 / 31.177
+table6/row10 PatchTST | 24 | fail 0.667 / 30.580 | fail 1.000 / 34.044 | fail 1.222 / 33.572 | fail 1.222 / 30.722
+table6/row11 PatchTST | 36 | fail 1.000 / 26.235 | fail 1.667 / 32.247 | fail 1.333 / 31.245 | fail 1.333 / 33.854
+table6/row12 PatchTST | 48 | fail 0.556 / 30.360 | fail 1.333 / 30.878 | fail 0.889 / 35.158 | fail 0.889 / 35.002
+table6/row13 PatchTST | 60 | fail 0.500 / 35.035 | fail 1.667 / 34.342 | fail 2.222 / 35.674 | fail 2.333 / 35.133
+table7/row1 量 | 数值
+table7/row2 回归斜率 / R² | +0.1171 / 0.0223
+table7/row3 有参数量导出的模型 | 11
+table7/row4 子集帕累托集合 | NLinear 2,520; PatchTST 531,878
+table7/row5 参数比 | 211.1×
+table7/row6 描述性 MSE 降幅 | 11.2%
+table7/row7 ρ(MSE, PIE) | +0.736 (p < 0.0001)
+table7/row8 ρ(MSE, 通过数) | -0.429 (p = 0.023)
+table8/row1 模型 A | 模型 B | Δ MSE | p raw | p Holm | 效应*
+table8/row2 NLinear | PatchTST | +0.2095 | 0.005859 | 0.1172 | 1.15
+table8/row3 Gradient Boosting | RNN | -1.4029 | 0.000488 | 0.0664 | 4.86
+table8/row4 KNN | NLinear | +1.9138 | 0.000488 | 0.0664 | 22.29
+table8/row5 KNN | MIFlu | +2.2280 | 0.000488 | 0.0664 | 9.89
+table8/row6 KNN | LSTM | -1.2234 | 0.000488 | 0.0664 | 5.28
+table8/row7 iTransformer | TimeCMA | +1.3863 | 0.000488 | 0.0664 | 7.02
+table8/row8 iTransformer | SVR | -1.3443 | 0.000488 | 0.0664 | 10.61
+table9/row1 编码器 | MSE | 相对 MIFlu | PTE | PIE (%) | 通过
+table9/row2 Hunyuan-1.8B | 4.7374 | 3.04× | 4.406 | 71.428 | 0/16
+table9/row3 Hunyuan-7B | 4.7596 | 3.06× | 5.309 | 75.399 | 0/16
+table9/row4 DeepSeek-R1-Qwen-1.5B | 4.7866 | 3.07× | 5.792 | 78.061 | 0/16
+table9/row5 DeepSeek-R1-Llama-8B | 4.8250 | 3.10× | 4.306 | 77.121 | 0/16
+table9/row6 DeepSeek-R1-32B | 4.9372 | 3.17× | 3.889 | 77.730 | 0/16
+table9/row7 DeepSeek-R1-Qwen-14B | 5.0166 | 3.22× | 4.149 | 76.350 | 0/16
+table9/row8 DeepSeek-R1-Qwen-7B | 5.0308 | 3.23× | 4.458 | 76.373 | 0/16
+table9/row9 ContextPilot-8B | 5.0843 | 3.26× | 4.962 | 78.918 | 0/16
+table9/row10 Hunyuan-4B | 5.1317 | 3.30× | 3.003 | 78.840 | 0/16
+table9/row11 ContextPilot-14B | 5.1949 | 3.34× | 4.965 | 77.764 | 0/16
+table9/row12 Qwen2.5-1.5B | 5.2049 | 3.34× | 5.333 | 74.650 | 0/16
+table10/row1 变体 | 参数 | 单元 | 状态
+table10/row2 参考 K=6 | default | 12 | 已在基准中
+table10/row3 no_lora | --no-lora | 12 | 尚未聚合
+table10/row4 K=2 | --num-layers 2 | 12 | 尚未聚合
+table10/row5 K=4 | --num-layers 4 | 12 | 尚未聚合
+table10/row6 K=8 | --num-layers 8 | 12 | 尚未聚合
+table10/row7 K=12 | --num-layers 12 | 12 | 尚未聚合
+table11/row1 目标 | 是否处理 | 估计完成度
+table11/row2 复现算术 | 是，原始来源仍有限 | 100%
+table11/row3 28 模型基准导出 | 是，算术已核实 | 100%
+table11/row4 峰值与效率评估 | 是，解释已修正 | 100%
+table11/row5 冻结编码器维度 | 是，仅保留模型 | 100%
+table11/row6 消融 | 部分，用户报告 27/60 | 45%
+table11/row7 滚动原点 | 代码阶段，未评测 | 15%
+table11/row8 手稿 | 草稿，发表证据未齐 | 70%
+table12/row1 目标日期 | 任务 | 预期输出与替代方案
+table12/row2 2026-11-16 前 | 取回并核实消融导出 | 完成则报告实测表，否则保留未完成标签
+table12/row3 2026-11-16 至 20 | 向导师及评阅人汇报 | 学生须确认预约及双方出席
+table12/row4 2026-11-20 香港时间 23:59 | 经 FYP InfoNet 提交 | 保存回执，迟交有扣分
+table12/row5 2026-11-30 前 | 区域结果及计时来源 | 报告完整分母与硬件，无预设趋势
+table12/row6 2026-12-31 前 | 滚动原点与检测敏感性 | 逐季不确定性与全窗口敏感性
+table12/row7 2027 年 1–4 月 | 决定投稿 | 证据与范围适当后才考虑 JBHI 投稿
--- ieee_manuscript_en corrected upload
+++ ieee_manuscript_en reviewed revision 4
@@ -1,206 +1,173 @@
-p0 Ranking by MSE Is Not Ranking for Deployment: A 28‑Model Reproduction and Benchmark of Influenza Forecasting
-p1 Author Name, Member, IEEE — Department of Electrical Engineering, City University of Hong Kong
Supervisor: Prof. Katie Chan — Assessor: Name
(Draft: author block and funding note are placeholders.)
-p2 Abstract—Influenza forecasts exist to support decisions, but the literature ranks them by mean squared error. We report an independent reproduction of MIFlu (Moon et al., IEEE JBHI 2025) on the CDC national influenza series (966 weekly rows, 7 channels, bit-identical to the author's file) and a 28-model benchmark the original work does not contain: 13 conventional forecasters, four LLM-based forecasters (MIFlu and three published ones), and 11 frozen large-language-model encoders. The reproduction lands within 4.5 % of the published four-horizon MSE mean (1.4995 against 1.4355) with a horizon-dependent sign: better at L=24 and L=36, worse at L=48 and L=60. On one common protocol (seeds 42/43/44; shared windows (W//16)*16 = 160/144/144/128) the accuracy champion is MIFlu (1.5574), ahead of PatchTST (1.6621) and NLinear (1.8716), and the spread across the roster is a factor of 3.6. On the epidemiological acceptance criterion of Kramer & Shaman (peak-timing error <= 1 week and peak-intensity error <= 25 % on ILITOTAL de-normalised to patient counts), NLinear and MIFlu each pass 4 of 16 cells, but differently: NLinear passes all four step-0 cells with a peak-intensity error of 3.2 %, while MIFlu's passes sit at 18.3-24.8 %, against the boundary. PatchTST passes none: its timing is the best in the study (mean 1.240 weeks) but its intensity error is 32.8 %. Accuracy and calibration are positively rank-correlated across all 28 arms (Spearman rho = +0.74), so MSE is a useful screen; but the frontier is ordered the other way round, and the pass indicator is negatively rank-correlated with MSE (rho = -0.43, p = 0.023). Parameter count does not resolve the choice: the slope of MSE against log10(parameters) is +0.1171 with R2 = 0.0223, the Pareto set is {NLinear, 2,520 parameters; PatchTST, 531,878 parameters}, and the 211x parameter cost buys an 11.2 % MSE difference that does not survive Holm correction over the 136 pairs (p = 0.117; with n = 12 no pair can). None of the 11 frozen encoders passes the criterion, and every one is worse than a decision tree. We argue that the acceptance criterion should be reported next to MSE, and that an MSE-sorted leaderboard can point a deployment decision the wrong way.
-p3 Index Terms—Influenza forecasting, reproduction study, benchmark, peak-timing error, peak-intensity error, evaluation protocol, model selection, frozen language-model encoders.
-p4 I. Introduction
-p5 Influenza forecasting exists to support decisions: when to escalate a response, how much capacity to prepare, and when to announce that a season has peaked. The loss behind those decisions is not squared error. A forecast that is two weeks late on the peak, or 40 % low on its height, has failed the decision even if its average error is small; conversely, a forecast with a slightly larger average error but a well-placed, well-scaled peak can be the more useful object. Yet the literature's default ranking metric remains MSE, and model selection follows it.
-p6 This paper tests that default on its own terms. We reproduce MIFlu (Moon et al., IEEE JBHI 2025), the current multimodal state of the art on CDC national influenza data, after removing the data leakage in its checkpoint selection; we place it in a 28-model benchmark under one set of windows and seeds; and we score every arm twice — once on the metric the literature reports (MSE) and once on the criterion public health applies (the Kramer & Shaman peak criterion). The two scorings do not agree, and the disagreement is systematic rather than marginal.
-p7 Contributions. (1) A leak-free reproduction of MIFlu that reports the per-horizon sign rather than a single mean, and therefore reports a crossover instead of an improvement. (2) A 28-arm benchmark under one protocol — 13 conventional forecasters, 4 LLM-based (MIFlu and 3 published), forecasters, and 11 frozen LLM encoders — with windows, seeds, metric and checkpoint rule held identical. (3) The finding that the deployment ordering is not the accuracy ordering: the frontier is inverted on peak calibration, and the acceptance verdict is negatively rank-correlated with MSE. (4) A parameter-cost and significance analysis showing that the 211x cost of the accuracy runner-up buys a difference this benchmark cannot resolve.
+p0 Auditing MIFlu and Comparing Influenza Forecasts Across Accuracy Peak Error and Parameter Count
+p1 CHAN Sing Yeung
Final Year Project, Department of Electrical Engineering, City University of Hong Kong
+p2 Single-column review draft oriented towards IEEE JBHI. Current submission rules and page limits remain unverified. This is an evaluation contribution and is not yet submission-ready.
+p3 Abstract
+p4 We audit an independent MIFlu reproduction and 28 forecasting implementations on a 966-row US national influenza series. The supplied reproduction table gives mean squared error (MSE) 1.4995 versus the published 1.4355, with lower MSE at two horizons and higher MSE at two. Under three benchmark seeds, MIFlu, PatchTST and NLinear achieve 1.5574, 1.6621 and 1.8716. A joint screen using literature-derived timing and intensity tolerances yields 4/16 passing aggregated cells for both NLinear and MIFlu and 0/16 for PatchTST. NLinear has lower mean peak-intensity error but higher mean timing error than MIFlu. Across 11 arms with parameter exports, the MSE–log-parameter fit has slope +0.1171 and R² 0.0223. An audit identifies an incorrect Holm routine in the supplied analysis: correcting 136 comparisons among 17 models yields no rejections, with NLinear–PatchTST p approximately 0.1172. This does not establish equivalence. Eleven frozen language encoders perform worse than a decision tree in the tested readout configuration. Ablation completion is owner-reported at 27/60 and is not aggregated. The findings are descriptive and limited to one split, retrospective peak detection and adapted implementations. We recommend reporting peak magnitude and timing alongside average error, then selecting on validation-defined costs and budgets before prospective deployment.
+p5 I. Introduction
+p6 Influenza forecasting supports preparedness, but lower average error does not ensure accurate peak magnitude or timing. We examine a supplied MIFlu reproduction [1] and a broader set of project implementations without treating the joint peak screen as clinical certification.
+p7 Contributions. (1) An audited reproduction comparison with a +4.5% mean-MSE gap. (2) A shared-window ranking of 28 implementations. (3) A peak timing–magnitude comparison revealing 4/16, 4/16 and 0/16 aggregate-cell passes for the leading three arms. (4) A parameter and statistical audit identifying low explained variance (R² 0.0223) and a defective Holm adjustment. The prescriptive addition is a validation-defined decision rule, not a tested new forecasting method.
 p8 II. Related Work
-p9 Long-horizon forecasting architectures. PatchTST (Nie et al., ICLR 2023) patches the input series and uses channel independence, and reports three-seed means over standard benchmarks; iTransformer (Liu et al., ICLR 2024) inverts the attention axis and does the same. Zeng et al. (AAAI 2023) argued that a linear model is competitive with transformer forecasters, a claim our benchmark reproduces in the influenza setting: NLinear is third of 28 arms with three orders of magnitude fewer parameters than the accuracy champion.
-p10 Epidemiological evaluation. Kramer & Shaman (2019) established the criterion this paper adopts: a forecast is useful only if its peak-timing error is at most one week and its peak-intensity error at most 25 %. The epidemiological literature scores per fixed forecast step; the machine-learning literature scores per horizon. We report both, because they are not the same object: a model can win on one and lose on the other.
-p11 Frozen foundation-model features. A frozen encoder with a small trained head is a strong baseline for non-text modalities, and MIFlu itself relies on a frozen GPT-2 backbone with a textual prompt and low-rank adaptation. Whether the choice of encoder matters at the scale of a 966-row epidemiological series has not been established. Section VI-F reports that experiment: eleven encoders, one shared linear head, and a negative result.
-p12 Reproduction and benchmark studies. Reproduction work is increasingly recognised as a contribution in its own right, because a benchmark is only as useful as its protocol. Our contribution is of that kind: we do not propose a new architecture, we make the existing comparison honest and then measure what the honest comparison says.
-p13 III. Data
-p14 The data are the CDC national influenza surveillance series distributed with MIFlu: 966 weekly rows and 7 numeric channels (% WEIGHTED ILI, % UNWEIGHTED ILI, AGE 0-4, AGE 5-24, ILITOTAL, NUM. OF PROVIDERS, OT). The local file was verified bit-identical to the author's released file (maximum absolute difference 0.000e+00) before any model was trained, because a single mis-joined week would move every number in this paper. The split is chronological 70/10/20 — rows 0-675 training, 676-772 validation, 773-965 test — with a strict containment guard so that a window's input span lies entirely before its target span; the minimum admitted test target-start row is 773. Standardisation uses a StandardScaler fitted on the training block only (ILITOTAL mean 9,439.84 patients, sd 9,003.15; OT mean 493,629).
-p15 The scaling constants decide the metric design. Seven channels whose training means span 1.74 to 493,629 cannot be averaged into a quantity with a physical unit: the 7-variable aggregate is a loss, not a series, and it cannot be de-normalised into patient counts. Peak-skill metrics therefore use ILITOTAL alone.
-p16 IV. Method
-p17 A. Two protocols
-p18 The reproduction uses 10 repetitions with seeds 2021-2030, matching the original author, and validation-selected checkpoints. The benchmark uses 3 seeds, 42/43/44, for every arm, and the same checkpoint rule. They are separate experiments and their numbers are never compared; MIFlu appears under both because a reproduction and a benchmark row impose incompatible requirements, and only the reproduction instance is quoted as a reproduction.
-p19 B. Evaluation windows
-p20 MIFlu's own loader uses DataLoader(batch_size=16, drop_last=True), which discards the final partial batch: 170→160, 158→144, 146→144, 134→128. The discarded windows are measurably harder (1.3929–1.4423 MSE, i.e. ~1.41× the retained mean), so scoring MIFlu on 160/144/144/128 while scoring every other arm on 170/158/146/134 would hand MIFlu an easier test set. All 17 arms are therefore scored on the same cropped windows.
-p21 C. Metrics
-p22 Accuracy is the 7-variable aggregate MSE and MAE in standardised space, averaged over channels and windows, reported per horizon and as a four-horizon mean. Peak skill de-normalises ILITOTAL to patient counts and measures, per season, the peak-timing error (PTE, weeks) and the peak-intensity error (PIE, % of the observed peak), at fixed steps 0/1/2/3 = 1/2/3/4 weeks ahead. A cell passes only if PTE <= 1 week and PIE <= 25 %. The thresholds are attributed to Kramer & Shaman (2019) and are marked [to verify] against the original text; peak detection (find_peaks(prominence = 0.15 x range, distance = 15), ±8-week matching) is this study's engineering choice, not part of the published criterion.
-p23 D. Checkpoint selection
-p24 Every model selects its checkpoint on the validation block. The author's code selects on the test set (main_ILI_lora.py, lines 211 and 225); that is data leakage and is not replicated. The deviation is disclosed wherever a reproduction number appears.
-p25 E. Statistics
-p26 Paired comparisons use exact sign-flip tests on the 12 matched (horizon x seed) cells, with Holm-Bonferroni correction over all 136 pairs of the 17 non-encoder arms (MIFlu and the 11 encoders are outside this family), a bootstrap 95 % CI (10,000 resamples), and Cohen's d. All arms share the same three seeds, which is what makes the 12 cells matched; with n = 12 the smallest attainable p is 2/2¹² ≈ 0.00049, and we state that floor rather than hide it. 128 of 136 pairs are significant before correction; after proper Holm none survives, because the smallest attainable adjusted p is 0.066.
-p27 F. Hardware and provenance
-p28 The 204 cells of the 17 arms (13 conventional, 3 published LLM-based, and DLinear) ran on an A100-SXM4-80GB in the stingy partition of CityU HPC Burgundy, with GPU model, partition, node and job id recorded per cell; the MIFlu and encoder cells ran on the same partition with per-cell manifests on the cluster. Twelve NLinear cells were first measured on a V100-SXM2-32GB and re-run on A100; the two agree to 1e-6, so no ranking depends on the hardware. No timing claim is made anywhere in this paper.
-p29 V. Experiments
-p30 Four analyses are reported, in this order. Reproduction (Table I): ten repetitions at four horizons against the published values. Accuracy (Table II): 28 arms x four horizons x three seeds, ranked by the four-horizon mean. Peak skill (Tables III-IV): the Kramer & Shaman criterion, per fixed step, on de-normalised patient counts. Efficiency and significance (Tables V-VI): a Pareto frontier and a log-parameter regression, then Holm-corrected paired tests. A fifth axis — frozen LLM encoders (Table VII) — and the ablation ladder (Table VIII) complete the matrix; the ladder is in progress and is reported as a design, not as a result.
-p31 VI. Results
-p32 A. The reproduction
-p33 The four-horizon mean is 1.4995 against the published 1.4355, i.e. 4.5 % worse, and the per-horizon sign flips: better at L=24 (1.3045 vs 1.542) and L=36 (1.3561 vs 1.422), worse at L=48 (1.6543 vs 1.414) and L=60 (1.6829 vs 1.364). The MAE side behaves the same way (0.8043 against 0.7452, +7.9 %). Reporting only the mean would have hidden the structure. Two explanations remain consistent with the pattern — validation-based checkpoint selection, and long-horizon variance (the ten repetitions span 1.401-1.984 at L=60) — and the data cannot yet separate them.
-p34 TABLE I. Reproduction of MIFlu's Table V — the sign crossover. 7-variable aggregate MSE in z-space, 10 repetitions, seeds 2021–2030.
-p35 A positive Δ means we are worse than the paper. We win L24 (−15.4 %) and L36 (−4.6 %) and lose L48 (+17.0 %) and L60 (+23.4 %); the 4-horizon mean is +4.5 % on MSE and +7.9 % on MAE. The only defensible claim is “reproduced within 4.5 % on the 4-horizon MSE mean, with a horizon-dependent sign” — never a claim of superiority over the original. Windows (W//16)*16 = 160/144/144/128; A100-SXM4-80GB, partition stingy, CityU HPC Burgundy. Source: ESSAY_VS_REPRODUCTION_TABLE_V.csv.
-p36 Takeaway. The reproduction is a reproduction, not an improvement: 4.5 % on the four-horizon mean, with a sign that depends on the horizon. The two disclosed deviations mean the per-horizon wins cannot be claimed as superiority over the original.
-p37 B. Accuracy: the 28-arm ranking
-p38 MIFlu is the accuracy champion at 1.5574, followed by PatchTST (1.6621) and NLinear (1.8716); the spread across all 28 arms is 1.5574 to 5.6155, a factor of 3.6, and all 28 beat the seasonal-naive reference (6.2132). The two published LLM-based forecasters are beaten by a nearest-neighbour baseline (KNN 3.7854 against Qwen-Time 5.2557 and CALF 5.5785). A linear model with 2,520 parameters is third of 28, ahead of every transformer except PatchTST.
-p39 TABLE II. The 28-arm benchmark: 7-variable aggregate MSE per horizon and as a four-horizon mean, plus the four-horizon MAE, in z-space. Mean over seeds 42/43/44, on the shared (W//16)*16 windows 160/144/144/128.
-p40 Lower is better. Per-horizon MAE is omitted for legibility; it is in 02_数字表格/BENCH_MSE_BY_MODEL_L.csv. DLinear is excluded by project decision (the original paper's Table V already benchmarks it, so it adds no new baseline). The seasonal-naive reference (52-week lag) scores 6.2132 on the same windows, so every one of the 28 arms beats it. Hardware: A100-SXM4-80GB, partition stingy, CityU HPC Burgundy — 204/204 cells of the 17 arms (13 conventional + 3 published LLM-based + DLinear) carry that measured provenance, and the MIFlu and encoder cells were run on the same partition with per-cell manifests on the cluster. Parameter counts are the trained-model totals from BENCH_EFFICIENCY.csv; classical learners and MIFlu are non-parametric in this sense (or not exported) and are left blank.
-p41 Takeaway. Accuracy alone does not identify a deployable model. The top three are within 20 % of each other in MSE, and the ranking says which model fits this test set best, not which supports the decision the forecast exists for.
-p42 C. Peak skill: the deployment ordering
-p43 On the Kramer & Shaman criterion the ranking changes. NLinear and MIFlu each pass 4 of 16 cells, but differently: NLinear passes all four step-0 cells with a peak-intensity error of 3.2 %, while MIFlu's four passes sit at PIE 18.3-24.8 %, against the 25 % boundary, and it misses L=48 at step 0 (PTE 1.22 weeks). PatchTST passes none: its timing is the best in the study (mean PTE 1.24 weeks) but its PIE is 32.8 %, so it fails the calibration half in every cell. Every other arm fails both halves.
-p44 TABLE III. Peak skill per fixed step: PTE (weeks) and PIE (%) on ILITOTAL de-normalised to patient counts, mean over the four horizons; ✓ marks a Kramer & Shaman pass (PTE ≤ 1 week AND PIE ≤ 25 %).
-p45 Two arms pass, and they pass differently. NLinear passes all four step-0 cells (4 of 16): mean PTE 1.677 weeks and mean PIE 9.477 % over all 16 cells, with a step-0 PIE of 3.25 % — an order of magnitude inside the criterion. MIFlu also passes 4 of 16, but three of them are step-0 cells (L=48 fails at step 0 with PTE 1.222 weeks) and the fourth is L=48 at step 1; its mean PIE is 26.846 %, i.e. its passes sit close to the 25 % boundary rather than inside it. PatchTST has the best timing (mean PTE 1.240 weeks) but a mean PIE of 32.755 % and 0 passes: it misses the calibration half of the criterion in every cell. Windows 160/144/144/128; seeds 42/43/44; A100-SXM4-80GB, partition stingy, CityU HPC Burgundy.
-p46 TABLE IV. The same criterion cell by cell: every (horizon, step) pair for the three named arms. PASS requires PTE ≤ 1 week AND PIE ≤ 25 % in the same cell.
-p47 16 cells per model = 4 horizons × 4 steps, each a mean over seeds 42/43/44. NLinear passes 4 of 16, all at step 0 (PIE 2.4–4.2 %); MIFlu passes 4 of 16 — three at step 0 and one at L=48 step 1, with PIE 18.3–24.8 %, i.e. against the boundary; PatchTST passes none, because its PIE stays in the 26–35 % band at every step. Peak detection: find_peaks(prominence = 0.15 × range, distance = 15) with ±8-week matching — this study's engineering choice, not part of the published criterion. The 1-week / 25 % thresholds are attributed to Kramer & Shaman (2019) but remain [to verify] against the original text.
-p48 Takeaway (Finding 1). The deployment ordering is not the accuracy ordering. Across all 28 arms better MSE does go with better calibration (Spearman ρ = +0.74 against mean PIE), so MSE is a useful screen; but among the three lowest-MSE arms the calibration order is inverted at both ends — NLinear (3rd) 9.5 %, MIFlu (1st) 26.8 %, PatchTST (2nd) 32.8 % — and the pass indicator is negatively rank-correlated with MSE (ρ = -0.43, p = 0.023). The MSE runner-up passes nothing; the third-best passes every horizon one week ahead.
-p49 D. Accuracy against efficiency
-p50 The slope of MSE against log10(parameters) across the 11 parametric arms is +0.1171 with R² = 0.0223: size explains about 2 % of the variance and its sign is unfavourable. The Pareto set is exactly two models — NLinear at 2,520 parameters and PatchTST at 531,878 — i.e. 211x the parameters for 11.2 % lower MSE. Whether that is a good trade depends on the deployment, and on whether the deployment needs peak skill: if it does, the 11.2 % advantage buys a model that fails the criterion outright.
-p51 TABLE V. Accuracy–efficiency summary, and the rank association between accuracy and peak skill.
-p52 A positive slope means more parameters are associated with a higher (worse) MSE, and R² = 0.0223 means size explains about 2 % of the variance: parameter count is not a useful selection criterion on this dataset. The two Pareto rows should be read as a trade-off, not a ranking — PatchTST spends 211× the parameters for 11.2 % lower MSE. The last two rows keep the peak-skill claim honest: across all 28 arms, better MSE does go with better calibration (ρ = +0.74), so the two axes are not independent; what fails is the ordering of the frontier (the peak-skill tables) and the acceptance verdict, which is negatively rank-correlated with MSE (ρ = -0.43). Windows 160/144/144/128; seeds 42/43/44.
-p53 E. Statistical significance
-p54 The pair the Pareto argument needs is NLinear vs PatchTST: mean Δ MSE +0.2095 in PatchTST's favour, NLinear lower in only 2 of 12 cells, raw p = 0.0059, and p(Holm) = 0.117 after correction over all 136 pairs; d = 1.15. That pair is the 117th smallest of the 136 p-values, so a table sorted by significance would omit it — which is why Table VI prints it first and the six most significant pairs below it.
-p55 TABLE VI. Paired sign-flip tests on the 12 matched (horizon × seed) cells, Holm-corrected over all 136 pairs (recomputed from the raw p-values). First row: the Pareto pair discussed in the text (bold). Remaining rows: the six smallest p-values, for contrast.
-p56 Positive Δ means model A has the larger MSE. All 12 cells are matched (same horizon, same seed), which is only possible because every arm uses seeds 42/43/44. The exported p_holm column was produced with a reverse cumulative minimum, which is not a valid Holm adjustment; the values here are recomputed from p_raw. With n = 12 the smallest attainable raw p is 2/2¹² ≈ 0.00049, so with m = 136 pairs the smallest attainable adjusted p is 0.066 and no pair survives at 0.05 (128/136 are significant before correction). Why the first row is not in the second block: NLinear vs PatchTST has adjusted p = 0.117, the 117th smallest of 136, so a table sorted by significance omits the one comparison the Pareto argument needs. The difference is not resolvable at this sample size; that is a failure to reject, not a demonstration of equivalence (d = 1.15, and PatchTST is lower in 10 of 12 cells).
-p57 Takeaway (Finding 2). The 211x cost buys an 11.2 % MSE difference that this benchmark cannot resolve at n = 12. This is a failure to reject equality, not a proof of equivalence (d = 1.15; PatchTST is lower in 10 of 12 cells). The defensible conclusion is “no accuracy advantage is established for the 211x cost”.
-p58 F. Frozen LLM encoders
-p59 Eleven encoders (Qwen2.5-1.5B; DeepSeek-R1-Distill-Qwen at 1.5B, 7B, 14B and 32B; DeepSeek-R1-Distill-Llama-8B; Hunyuan-1.8B/4B/7B; ContextPilot-8B/14B) were each frozen and paired with one shared linear head, trained channel-independently: 132 of 156 cells. The best is Hunyuan-1.8B at 4.7374 and the worst Qwen2.5-1.5B at 5.2049, i.e. 3.04x to 3.34x the MSE of MIFlu. Every one is worse than a decision tree (4.3198), and none passes the Kramer & Shaman criterion in any cell. The ordering inside the family is not a monotone function of size.
-p60 TABLE VII. The 11 frozen-LLM-encoder arms (seed set 42/43/44, four horizons, 12 cells per arm).
-p61 Every arm is a frozen encoder plus one shared linear head, trained channel-independently; no encoder weight is updated. Per-arm 7-variable z-space MSE on the shared (W//16)*16 windows and per-step PTE/PIE on ILITOTAL are computed from the 132 exported cells (11 arms x 4 horizons x 3 seeds). The two embedding-only arms and the five excluded arms are listed in the next table.
-p62 Takeaway (Finding 3). The protocol was designed to give the idea its best chance — frozen features, a linear read-out, channel independence — and it still fails. This does not prove that an encoder can never help, but a claimed gain from frozen language features on this task owes both a mechanism and a control.
-p63 G. The ablation ladder
-p64 The ladder asks where MIFlu's accuracy comes from: the LoRA adaptation, or the depth of the GPT-2 stack. It is five variants (no LoRA; K = 2, 4, 8, 12 layers) at four horizons and three seeds — 60 cells — compared against the full K=6 arm already in Table II. One result is established and it is negative about the text branch: the text tokens sit behind the causal mask and the head reads only the time patches, so --no-text is bit-identical to the full arm (asserted by tests_archive/test_miflu_ablations.py), which means a text ablation is a structural verification, not an effect. At the snapshot this draft is built from, 27 of the 60 cells for the remaining variants were complete, so no depth trend is claimed. The ladder is reported as a design and a status, not as a result.
-p65 TABLE VIII. The ablation ladder (called Table VIII in the project plan): five variants, 60 cells, and what each one is for.
-p66 Each variant is 4 horizons × 3 seeds = 12 cells; five variants = 60 cells; the reference arm is the 12 cells already reported in the benchmark table and is not counted twice. At the snapshot these documents are built from, 27 of 60 cells were complete (driver job 722968) and the per-variant export had not been pulled, so this document reports the design and the completion count and claims no depth trend. The --no-text variant is deliberately not a row: the text tokens sit behind the causal mask and the head reads only the time patches, so --no-text is bit-identical to the full arm — a structural verification (asserted by tests_archive/test_miflu_ablations.py), never an ablation effect.
-p67 VII. Threats to Validity
-p68 Single dataset. All results come from one 966-row national series in one country. Nothing here establishes cross-dataset or cross-region generality, and the regional and rolling-origin evaluations that would test it are not yet run.
-p69 Resolution of the tests. With n = 12 matched cells the smallest attainable p is 2/2¹² ≈ 0.00049, and a non-significant result is a failure to reject, not evidence of equivalence. We therefore phrase the Pareto conclusion as “no advantage established”, not “no advantage”.
-p70 Criterion attribution. The 1-week / 25 % thresholds are attributed to Kramer & Shaman (2019) but are marked [to verify] against the original text, and the peak detector is our own engineering choice. A different detector would move PTE/PIE, though it would not move the MSE ranking.
-p71 Scope of the encoder axis. The experiment tests frozen features with a linear read-out. It does not test generation, prompting or fine-tuning, and its negative result must not be read as a claim about LLM forecasters in general — MIFlu, which is fine-tuned, is the accuracy champion.
-p72 Incomplete ablation. The depth and LoRA questions are open until the 60 cells are aggregated. The manuscript reports the ladder's design and its completion count, and claims no trend.
-p73 The reproduction's two deviations. Validation-based checkpoint selection and the 7-variable metric are necessary for a leak-free, table-comparable result, but they mean the per-horizon wins are not a like-for-like claim of superiority.
-p74 VIII. Conclusion
-p75 We reproduced MIFlu within 4.5 % on the four-horizon MSE mean with a horizon-dependent sign, benchmarked 28 forecasters under one protocol, and showed that the deployment ordering is not the accuracy ordering: the accuracy champion is not the calibration champion, the MSE runner-up passes no cell of the epidemiological criterion, and the model that passes every horizon one week ahead has 2,520 parameters against the runner-up's 531,878 and is the cheaper member of the Pareto frontier. Parameter count is not a proxy for accuracy (slope +0.1171, R² 0.0223), and the 211x cost buys a difference this benchmark cannot resolve (p(Holm) = 0.117; no pair survives the 136-pair correction). Eleven frozen LLM encoders fail outright. The practical conclusion is that model selection for epidemiological forecasting should be made on the acceptance criterion, with MSE reported alongside it, and that a leaderboard sorted by MSE alone can point a deployment decision the wrong way.
-p76 IX. References
-p77 [1] J. Moon et al., “MIFlu: Large Language Model-Based Multimodal Influenza Forecasting,” IEEE J. Biomed. Health Inform., 2025, doi: 10.1109/JBHI.2025.3561214.
-p78 [2] Y. Nie, N. H. Nguyen, P. Sinthong, and J. Kalagnanam, “A Time Series is Worth 64 Words: Long-term Forecasting with Transformers,” in Proc. ICLR, 2023, arXiv:2211.14730.
-p79 [3] Y. Liu et al., “iTransformer: Inverted Transformers Are Effective for Time Series Forecasting,” in Proc. ICLR, 2024.
-p80 [4] A. Zeng, M. Chen, L. Zhang, and Q. Xu, “Are Transformers Effective for Time Series Forecasting?” in Proc. AAAI, 2023.
-p81 [5] A. M. Kramer and J. Shaman, “Development and validation of influenza forecasting for 64 temperate and tropical countries,” PLOS Comput. Biol., vol. 15, no. 2, e1006742, 2019, doi: 10.1371/journal.pcbi.1006742.
-p82 [6] Centers for Disease Control and Prevention, “FluView: Weekly U.S. Influenza Surveillance Report,” national ILI series (966 weekly rows, 7 channels).
-p83 [7] Qwen Team, “Qwen2.5 Technical Report,” 2024; DeepSeek-AI, “DeepSeek-R1,” 2025; Tencent Hunyuan and ContextPilot model cards, HuggingFace.
-p84 Volume, page and DOI details are to be completed at submission and checked against the publisher's record; author, title, venue and year are asserted in this draft.
-p86 Appendix A. Forecast panels
-p87 The panels below show step-wise forecasts against ground truth for three representative arms at the shortest horizon (L = 24). Black = ground truth; one line per fixed step 0/1/2/3 = 1/2/3/4 weeks ahead; the y-axis is ILITOTAL in patient counts. Complete panels for all 28 arms x 4 horizons are available in the supplementary material.
-p89 MIFLU at L=24. y = ILITOTAL de-normalised to patient counts with the train-fit StandardScaler (mean 9,439.84, sd 9,003.15 patients); x = test-set week. Black = ground truth; one line per fixed step 0/1/2/3 = 1/2/3/4 weeks ahead. Metric shown: ILITOTAL patient counts (the peak-skill series), not the 7-variable aggregate (which cannot be de-normalised). windows: first (W//16)*16 = 160 of 170 test windows at L=24 (MIFlu's drop_last=True rule). Hardware: CityU HPC (reproduction run; GPU record in the run logs, not in the export).
-p91 PATCHTST at L=24. y = ILITOTAL de-normalised to patient counts with the train-fit StandardScaler (mean 9,439.84, sd 9,003.15 patients); x = test-set week. Black = ground truth; one line per fixed step 0/1/2/3 = 1/2/3/4 weeks ahead. Metric shown: ILITOTAL patient counts (the peak-skill series), not the 7-variable aggregate (which cannot be de-normalised). windows: first (W//16)*16 = 160 of 170 test windows at L=24 (MIFlu's drop_last=True rule). Hardware: A100-SXM4-80GB | partition stingy | CityU HPC Burgundy.
-p93 NLINEAR at L=24. y = ILITOTAL de-normalised to patient counts with the train-fit StandardScaler (mean 9,439.84, sd 9,003.15 patients); x = test-set week. Black = ground truth; one line per fixed step 0/1/2/3 = 1/2/3/4 weeks ahead. Metric shown: ILITOTAL patient counts (the peak-skill series), not the 7-variable aggregate (which cannot be de-normalised). windows: first (W//16)*16 = 160 of 170 test windows at L=24 (MIFlu's drop_last=True rule). Hardware: A100-SXM4-80GB | partition stingy | CityU HPC Burgundy.
-table1/row1 Horizon | Ours (10-rep mean ± sd) | Paper | Δ MSE | Sign | Ours MAE | Paper MAE | Δ MAE
-table1/row2 L=24 | 1.3045 ± 0.0883 | 1.542 | -15.4 % | WIN | 0.7482 | 0.726 | +3.1 %
-table1/row3 L=36 | 1.3561 ± 0.1603 | 1.422 | -4.6 % | WIN | 0.7712 | 0.779 | -1.0 %
-table1/row4 L=48 | 1.6543 ± 0.1064 | 1.414 | +17.0 % | LOSS | 0.8381 | 0.757 | +10.7 %
-table1/row5 L=60 | 1.6829 ± 0.2109 | 1.364 | +23.4 % | LOSS | 0.8596 | 0.719 | +19.6 %
-table1/row6 4-horizon mean | 1.4995 | 1.435 | +4.5 % | LOSS | 0.8043 | 0.745 | +7.9 %
-table2/row1 # | Model | Family | MSE L24 | MSE L36 | MSE L48 | MSE L60 | MSE 4L | MAE 4L | Params
-table2/row2 1 | MIFlu | LLM-based | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199 | —
-table2/row3 2 | PatchTST | Transformer | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786 | 531,878
-table2/row4 3 | NLinear | Linear | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183 | 2,520
-table2/row5 4 | DNN | Neural | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057 | 33,048
-table2/row6 5 | TimeCMA | LLM-based | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676 | 125,830,824
-table2/row7 6 | Gradient Boosting | Classical ML | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521 | —
-table2/row8 7 | KNN | Classical ML | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293 | —
-table2/row9 8 | Random Forest | Classical ML | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779 | —
-table2/row10 9 | iTransformer | Transformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476 | 75,672
-table2/row11 10 | Decision Tree | Classical ML | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798 | —
-table2/row12 11 | Hunyuan-1.8B | LLM enc. | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755 | —
-table2/row13 12 | Hunyuan-7B | LLM enc. | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685 | —
-table2/row14 13 | DeepSeek-R1-Qwen-1.5B | LLM enc. | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002 | —
-table2/row15 14 | DeepSeek-R1-Llama-8B | LLM enc. | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786 | —
-table2/row16 15 | GRU | Neural | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174 | 14,424
-table2/row17 16 | DeepSeek-R1-32B | LLM enc. | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935 | —
-table2/row18 17 | LSTM | Neural | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303 | 18,712
-table2/row19 18 | DeepSeek-R1-Qwen-14B | LLM enc. | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019 | —
-table2/row20 19 | DeepSeek-R1-Qwen-7B | LLM enc. | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133 | —
-table2/row21 20 | RNN | Neural | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634 | 5,848
-table2/row22 21 | ContextPilot-8B | LLM enc. | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255 | —
-table2/row23 22 | Hunyuan-4B | LLM enc. | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450 | —
-table2/row24 23 | ContextPilot-14B | LLM enc. | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407 | —
-table2/row25 24 | Qwen2.5-1.5B | LLM enc. | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725 | —
-table2/row26 25 | Qwen-Time | LLM-based | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794 | 1,544,084,680
-table2/row27 26 | SVR | Classical ML | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986 | —
-table2/row28 27 | CALF | LLM-based | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190 | 126,421,416
-table2/row29 28 | CNN | Neural | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720 | 22,488
-table3/row1 Model | PTE s0 (1 wk) | PIE s0 (%) | PTE s1 (2 wk) | PIE s1 (%) | PTE s2 (3 wk) | PIE s2 (%) | PTE s3 (4 wk) | PIE s3 (%) | Passes
-table3/row2 NLinear | 0.21 ✓ | 3.2 ✓ | 1.33 | 6.2 | 2.31 | 11.8 | 2.86 | 16.6 | 4/16
-table3/row3 MIFlu | 0.35 | 18.9 | 0.92 | 25.9 | 1.58 | 30.5 | 1.67 | 32.1 | 4/16
-table3/row4 PatchTST | 0.68 | 30.6 | 1.42 | 32.9 | 1.42 | 33.9 | 1.44 | 33.7 | 0/16
-table3/row5 RNN | 0.96 | 57.6 | 1.97 | 60.0 | 3.00 | 61.8 | 3.97 | 63.2 | 0/16
-table3/row6 GRU | 1.14 | 58.1 | 2.06 | 59.9 | 3.00 | 62.4 | 3.75 | 64.0 | 0/16
-table3/row7 TimeCMA | 1.54 | 50.0 | 2.03 | 51.4 | 2.97 | 55.6 | 2.78 | 57.5 | 0/16
-table3/row8 DNN | 1.92 | 37.8 | 2.64 | 40.1 | 2.78 | 43.7 | 2.86 | 44.9 | 0/16
-table3/row9 Qwen-Time | 2.10 | 40.5 | 3.08 | 50.3 | 3.14 | 55.9 | 3.75 | 61.6 | 0/16
-table3/row10 iTransformer | 2.19 | 67.7 | 2.25 | 68.6 | 2.11 | 69.9 | 1.92 | 71.1 | 0/16
-table3/row11 LSTM | 3.04 | 64.6 | 3.33 | 65.6 | 3.83 | 67.5 | 3.94 | 68.7 | 0/16
-table3/row12 KNN | 3.12 | 65.8 | 2.75 | 67.7 | 2.75 | 68.7 | 2.42 | 69.4 | 0/16
-table3/row13 DeepSeek-R1-32B | 3.14 | 77.3 | 3.19 | 77.7 | 3.86 | 78.1 | 5.36 | 77.7 | 0/16
-table3/row14 DeepSeek-R1-Qwen-14B | 3.54 | 75.4 | 4.08 | 76.3 | 4.50 | 76.6 | 4.47 | 77.2 | 0/16
-table3/row15 DeepSeek-R1-Qwen-7B | 3.69 | 76.0 | 4.44 | 76.7 | 4.47 | 76.2 | 5.22 | 76.6 | 0/16
-table3/row16 CALF | 3.75 | 80.0 | 3.42 | 80.5 | 3.92 | 80.6 | 4.42 | 80.8 | 0/16
-table3/row17 Hunyuan-4B | 3.88 | 79.4 | 3.08 | 79.3 | 2.22 | 78.7 | 2.83 | 78.0 | 0/16
-table3/row18 SVR | 3.92 | 77.3 | 3.50 | 79.9 | 3.33 | 80.4 | 2.75 | 80.6 | 0/16
-table3/row19 ContextPilot-14B | 4.11 | 76.8 | 4.75 | 77.8 | 5.44 | 78.1 | 5.56 | 78.4 | 0/16
-table3/row20 Hunyuan-1.8B | 4.26 | 69.7 | 4.81 | 70.7 | 4.19 | 71.9 | 4.36 | 73.4 | 0/16
-table3/row21 Qwen2.5-1.5B | 4.31 | 74.6 | 5.08 | 74.8 | 5.56 | 74.7 | 6.39 | 74.6 | 0/16
-table3/row22 Decision Tree | 4.54 | 55.1 | 5.06 | 53.8 | 5.64 | 50.2 | 4.75 | 56.7 | 0/16
-table3/row23 DeepSeek-R1-Llama-8B | 4.67 | 76.1 | 4.36 | 77.0 | 4.25 | 77.5 | 3.94 | 77.9 | 0/16
-table3/row24 ContextPilot-8B | 4.90 | 78.3 | 4.22 | 78.9 | 5.28 | 79.1 | 5.44 | 79.3 | 0/16
-table3/row25 Hunyuan-7B | 5.12 | 73.9 | 5.81 | 75.7 | 6.03 | 75.9 | 4.28 | 76.1 | 0/16
-table3/row26 Gradient Boosting | 5.33 | 52.0 | 4.67 | 58.7 | 4.75 | 62.8 | 5.08 | 65.4 | 0/16
-table3/row27 Random Forest | 5.35 | 65.9 | 5.19 | 66.5 | 5.58 | 67.0 | 5.64 | 67.6 | 0/16
-table3/row28 DeepSeek-R1-Qwen-1.5B | 5.83 | 77.4 | 5.44 | 78.0 | 5.78 | 78.3 | 6.11 | 78.5 | 0/16
-table3/row29 CNN | 6.28 | 81.1 | 6.78 | 81.9 | 6.22 | 82.2 | 7.14 | 82.6 | 0/16
-table4/row1 Model | L | step 0 (1 wk) | step 1 (2 wk) | step 2 (3 wk) | step 3 (4 wk)
-table4/row2 NLinear | L=24 | PASS (0.11 wk, 3.9 %) | fail (1.33 wk, 8.4 %) | fail (2.33 wk, 11.9 %) | fail (2.67 wk, 18.7 %)
-table4/row3 NLinear | L=36 | PASS (0.33 wk, 4.2 %) | fail (1.33 wk, 7.2 %) | fail (2.11 wk, 15.3 %) | fail (2.67 wk, 18.1 %)
-table4/row4 NLinear | L=48 | PASS (0.22 wk, 2.4 %) | fail (1.22 wk, 4.7 %) | fail (2.22 wk, 10.0 %) | fail (2.78 wk, 16.7 %)
-table4/row5 NLinear | L=60 | PASS (0.17 wk, 2.5 %) | fail (1.44 wk, 4.5 %) | fail (2.56 wk, 10.0 %) | fail (3.33 wk, 13.0 %)
-table4/row6 MIFlu | L=24 | PASS (0.00 wk, 18.3 %) | fail (0.89 wk, 26.7 %) | fail (1.22 wk, 30.5 %) | fail (1.33 wk, 31.6 %)
-table4/row7 MIFlu | L=36 | PASS (0.00 wk, 18.7 %) | fail (0.78 wk, 26.3 %) | fail (1.67 wk, 31.5 %) | fail (1.33 wk, 32.4 %)
-table4/row8 MIFlu | L=48 | fail (1.22 wk, 18.0 %) | PASS (0.67 wk, 24.8 %) | fail (1.22 wk, 30.1 %) | fail (1.33 wk, 33.2 %)
-table4/row9 MIFlu | L=60 | PASS (0.17 wk, 20.5 %) | fail (1.33 wk, 25.8 %) | fail (2.22 wk, 29.8 %) | fail (2.67 wk, 31.2 %)
-table4/row10 PatchTST | L=24 | fail (0.67 wk, 30.6 %) | fail (1.00 wk, 34.0 %) | fail (1.22 wk, 33.6 %) | fail (1.22 wk, 30.7 %)
-table4/row11 PatchTST | L=36 | fail (1.00 wk, 26.2 %) | fail (1.67 wk, 32.2 %) | fail (1.33 wk, 31.2 %) | fail (1.33 wk, 33.9 %)
-table4/row12 PatchTST | L=48 | fail (0.56 wk, 30.4 %) | fail (1.33 wk, 30.9 %) | fail (0.89 wk, 35.2 %) | fail (0.89 wk, 35.0 %)
-table4/row13 PatchTST | L=60 | fail (0.50 wk, 35.0 %) | fail (1.67 wk, 34.3 %) | fail (2.22 wk, 35.7 %) | fail (2.33 wk, 35.1 %)
+p9 Patching and linear baselines are established [3–5]. Time-LLM, CALF and TimeCMA use different alignment/adaptation designs [6–8]. Chronos, TimesFM, Moirai and Lag-Llama pretrain on numerical series and were not evaluated here [9–12]. Earlier LLM-removal work already questions the benefit of language pretraining [13], while a 2026 preprint reports conditional benefits under cross-dataset shifts [14]. The contribution here is the specific influenza protocol audit and multi-metric comparison.
+p10 Time-series conformal methods [15–17] motivate future interval evaluation but do not automatically validate intervals for peaks selected retrospectively. WIS [18] evaluates distributions or intervals, while PIE measures point-forecast peak height. These quantities must be separated.
+p11 III. Data
+p12 The two supplied author-format and paper-exact files each contain 966 rows and seven matched numerical channels, with numeric maximum absolute difference zero. The original downloaded upstream file and its commit are absent. The chronological split is 676/97/193, with train-only scaling and test targets starting no earlier than row 773. Dates in the author-format file are synthetic.
+p13 IV. Method
+p14 A. Evaluation protocols
+p15 We use a chronological split and train-only scaling. Validation selects checkpoints in this implementation. The handoff attributes test-set checkpoint selection and a one-variable loader to upstream code, but a pinned author checkout is absent and the public endpoint could not be opened. Those upstream allegations remain unverified. The notes also show learning-rate differences between code defaults and paper settings, so the comparison must not be described as differing in only two ways.
+p16 Reproduction uses seeds 2021–2030. The benchmark uses seeds 42/43/44 and 160/144/144/128 windows at L24/36/48/60. Cropping reproduces the local drop_last rule; a full-window sensitivity analysis is still required. The two MIFlu estimates answer different questions.
+p17 B. Metrics
+p18 Peak timing error (PTE) is the absolute difference between predicted and observed peak weeks. Peak intensity error (PIE) is the absolute peak-height error divided by the observed peak, expressed as a percentage. Kramer–Shaman [2] verifies the separate one-week and 25% tolerances. We apply both to mean errors in each (model, L, step) cell. This joint screen and its peak detector are project choices, not a clinical acceptance standard. A mean-error pass is not an individual-season success probability.
+p19 C. Statistical analysis
+p20 The source table contains 136 pairs from 17 models. The other 11 models are absent, so this is not an all-pairs analysis of 28 models. Holm uses a forward cumulative maximum after sorting raw p-values. The source uses a reverse cumulative minimum. At n=12, the two-sided exact floor 2/4096 multiplied by 136 exceeds 0.05, so this family cannot yield a rejection under proper Holm adjustment. Overlapping targets and repeated horizons also make the cells dependent. Raw p-values and unadjusted bootstrap intervals remain exploratory.
+p21 D. Decision rule
+p22 Decision rule for future validation: specify an MSE budget B, an allowable peak-failure rate q, and decision costs before inspecting a new test period. Among models meeting B and q on validation seasons, minimise expected decision cost, then parameter count as a tie-breaker. For an escalate/wait decision, use costs c_FP for unnecessary escalation and c_FN for a missed surge, with zero cost for correct actions. Escalate when a validated surge probability exceeds c_FP/(c_FP+c_FN). Costs, B and q have not been elicited or validated, so no model is certified for deployment. NLinear is a low-cost candidate for further peak-height validation; MIFlu remains the observed MSE leader.
+p23 V. Experiments
+p24 The roster comprises 13 conventional models, MIFlu and three other LLM-based implementations, and 11 frozen language encoders. Accuracy uses seven-variable standardised MSE/MAE. Peak errors use de-normalised ILITOTAL. Parameter analysis has 11 models, paired tests 17, and frozen-feature analysis 11; these denominators must not be conflated. We do not present these adapted implementations as verified exact replications of each cited comparator.
+p25 VI. Results
+p26 A. Reproduction
+p27 The reproduction CSV reports mean MSE 1.4995 versus 1.4355, a 4.5% increase. MSE is lower at L24 and L36 and higher at L48 and L60. Mean MAE is 0.8043 versus 0.7452 (+7.9%), but its signs are one lower and three higher; MAE does not share the MSE 2–2 crossover. Protocol and missing upstream provenance limit claims of exact replication.
+p28 TABLE I. MIFlu reproduction compared with the paper
+p29 Source: ESSAY_VS_REPRODUCTION_TABLE_V.csv, lines 2–6. SD is recomputed from the code-transcribed ten-seed oracle; its raw run logs are not included. Positive differences mean higher error.
+p30 B. Benchmark accuracy
+p31 TABLE II. Accuracy of all retained benchmark arms
+p32 Source: BENCH_MSE_BY_MODEL_L.csv, keyed by model and L. Each row averages three seeds on 160/144/144/128 windows. DLinear is excluded by project choice; that exclusion needs a documented sensitivity analysis. Names denote project implementations, whose equivalence to published methods is not established by this ranking.
+p33 F0 conclusion. MIFlu has the lowest observed MSE (1.5574), but MSE alone does not establish public-health utility. The top-three spread is 20.2% relative to MIFlu, not less than 20%.
+p34 C. Peak timing and magnitude
+p35 TABLE III. Peak timing and intensity error
+p36 Means are across 16 (L, step) cells. Passes apply PTE ≤ 1 week and PIE ≤ 25% to each cell’s aggregated errors, not to each individual season. PIE is point-forecast magnitude error, not probabilistic calibration.
+p37 TABLE IV. Joint peak screen for each horizon and lead
+p38 Each entry gives PTE in weeks / PIE in percent. s0–s3 are the first to fourth forecast weeks. The detector uses prominence 0.15 × range, distance 15, and ±8-week matching. These detector settings and joint aggregation are project choices. Source: BENCH_PTE_PIE_BY_STEP.csv.
+p39 F1 conclusion. NLinear and MIFlu each pass 4/16 aggregated cells, while PatchTST passes 0/16. NLinear has lower mean PIE (9.477% versus MIFlu 26.846%) but higher mean PTE (1.677 versus 1.128 weeks). This is a timing–magnitude trade-off, not dominance. The ordering is inverted at both ends among the three leaders: MSE orders MIFlu, PatchTST, NLinear; PIE orders NLinear, MIFlu, PatchTST.
+p40 MSE correlates with PIE (ρ=+0.736, p<0.0001) and inversely with passes (ρ=−0.429, p=0.023). Both signs are consistent with generally better error accompanying better peak results. These associations coexist with NLinear’s lower PIE despite its third-place MSE. They do not imply independence or a complete rank reversal.
+p41 D. Parameters
+p42 TABLE V. Parameter analysis and rank associations
+p43 The Pareto analysis includes only 11 arms with parameter exports. MIFlu and the frozen encoders are not in that subset. Missing parameter counts are not zero. Parameter count is not a measurement of latency, memory or energy. Correlations are descriptive across models on one test set.
+p44 F2 conclusion. The fitted slope is +0.1171 and R² is 0.0223 across the 11 arms with exported parameter counts. Size alone explains little of their observed MSE variation. This subset result does not prove that capacity is irrelevant.
+p45 E. Statistical correction
+p46 TABLE VI. Paired comparisons with corrected Holm adjustment
+p47 136 pairs cover 17 models, not all 28. n = 12 matched horizon × seed cells. Forward cumulative-max Holm yields 0/136 rejections. The shown p values recover the exact 1/4096 enumeration grid from six-decimal exports; recomputing directly from rounded exports gives NLinear–PatchTST 0.117180 instead of 0.1171875. *The source effect uses pooled model SD, not paired-difference SD. Cell dependence limits inference.
+p48 F3 conclusion. Proper Holm gives 0/136 rejections (128/136 before adjustment), with a minimum adjusted p of about 0.0664 and NLinear–PatchTST p ≈ 0.1172. PatchTST still has 11.2% lower observed MSE with 211× the parameters and lower MSE in 10/12 cells. Non-rejection does not establish equivalence or show that the gain is noise.
+p49 F. Frozen language encoders
+p50 TABLE VII. Frozen encoders with shared linear readout
+p51 11 retained encoders × 4 horizons × 3 seeds = 132 cells. The historical plan included two additional embedding-only arms, giving 156 planned cells; those 24 omitted cells are outside the 28-model roster. The result tests only this frozen-feature pipeline.
+p52 F4 conclusion. The 11 tested frozen encoders score 4.7374–5.2049, or 3.04–3.34× MIFlu’s MSE. All exceed the decision tree’s 4.3198 and pass 0/16 cells. This is a negative result for this feature/readout configuration; prompting, fine-tuning and numerical foundation models remain untested.
+p53 G. Ablation design
+p54 TABLE VIII. Ablation design and snapshot status
+p55 Owner-reported status at 3 November 2026: 27/60 additional cells, job 722968. No live HPC check or per-variant result export was available. The baseline 12 cells are not part of the additional 60. No trend is inferred.
+p56 F5 provisional conclusion. In miflu_model.py’s author_faithful path, text follows time tokens behind causal attention and the head reads the time tokens. Static inspection therefore predicts no text influence during deterministic evaluation. The supplied tests_archive/test_miflu_ablations.py explicitly asserts both text invariance and full/no-text equality with matched CPU initialisation. It was inspected statically, not executed here. Other fusion paths and training randomness require separate checks.
+p57 VII. Threats to Validity
+p58 One national series and one chronological split do not establish regional or prospective utility. Peak matching can use future observations to define events and is a retrospective evaluation tool. Synthetic date labels require a verified CDC calendar mapping before season-specific claims. Parameter exports omit MIFlu and encoders. The 27/60 ablation status is owner-reported, not a live cluster check. Modern numerical foundation baselines, regional results, rolling origins and validated uncertainty are missing.
+p59 Source p-values are retained but their complete raw paired inputs were not independently rescored. Corrected Holm values recover the enumeration grid and retain provenance to the rounded export. The reported source effect uses pooled model SD rather than paired-difference SD. A seed ensemble with an arbitrary variance floor is not a validated predictive distribution. No prospective utility, equivalence margin or calibrated surge probability has been established.
+p60 VIII. Conclusion
+p61 MIFlu leads the observed MSE ranking. NLinear offers lower peak-height error at low parameter count but has worse mean peak timing than MIFlu. The joint screen therefore exposes trade-offs rather than a universal winner. Corrected significance analysis supports no familywise rejection at the present resolution. Further regional, rolling-origin and foundation-model controls are needed before submission or deployment.
+p62 IX. References
+p63 [1] Jaeuk Moon, Jonghwa Shim, Eunbeen Kim and Eenjun Hwang, “MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme,” IEEE JBHI 29(10), 7790-7801, 2025. https://doi.org/10.1109/JBHI.2025.3561214
+p64 [2] Sarah C. Kramer and Jeffrey Shaman, “Development and validation of influenza forecasting for 64 temperate and tropical countries,” PLOS Computational Biology 15(2), e1006742, 2019. https://doi.org/10.1371/journal.pcbi.1006742
+p65 [3] Yuqi Nie, Nam H. Nguyen, Phanwadee Sinthong and Jayant Kalagnanam, “A Time Series is Worth 64 Words: Long-term Forecasting with Transformers,” ICLR, 2023. https://arxiv.org/abs/2211.14730
+p66 [4] Ailing Zeng, Muxi Chen, Lei Zhang and Qiang Xu, “Are Transformers Effective for Time Series Forecasting?,” AAAI (preprint record opened), 2023. https://arxiv.org/abs/2205.13504
+p67 [5] Yong Liu et al., “iTransformer: Inverted Transformers Are Effective for Time Series Forecasting,” ICLR (preprint record opened), 2024. https://arxiv.org/abs/2310.06625
+p68 [6] Ming Jin et al., “Time-LLM: Time Series Forecasting by Reprogramming Large Language Models,” ICLR, 2024. https://arxiv.org/abs/2310.01728
+p69 [7] Peiyuan Liu et al., “CALF: Aligning LLMs for Time Series Forecasting via Cross-modal Fine-Tuning,” arXiv:2403.07300, 2024. https://arxiv.org/abs/2403.07300
+p70 [8] Chenxi Liu et al., “TimeCMA: Towards LLM-Empowered Multivariate Time Series Forecasting via Cross-Modality Alignment,” AAAI, 2025. https://arxiv.org/abs/2406.01638
+p71 [9] Abdul Fatir Ansari et al., “Chronos: Learning the Language of Time Series,” Transactions on Machine Learning Research, 2024. https://arxiv.org/abs/2403.07815
+p72 [10] Abhimanyu Das, Weihao Kong, Rajat Sen and Yichen Zhou, “A decoder-only foundation model for time-series forecasting,” ICML, PMLR 235, 10148-10167, 2024. https://proceedings.mlr.press/v235/das24c.html
+p73 [11] Gerald Woo et al., “Unified Training of Universal Time Series Forecasting Transformers,” ICML, PMLR 235, 53140-53164, 2024. https://proceedings.mlr.press/v235/woo24a.html
+p74 [12] Kashif Rasul et al., “Lag-Llama: Towards Foundation Models for Probabilistic Time Series Forecasting,” arXiv:2310.08278, version 3, 2024. https://arxiv.org/abs/2310.08278
+p75 [13] Mingtian Tan, Mike A. Merrill, Vinayak Gupta, Tim Althoff and Thomas Hartvigsen, “Are Language Models Actually Useful for Time Series Forecasting?,” NeurIPS 37, 2024. https://arxiv.org/abs/2406.16964
+p76 [14] Xin Qiu et al., “Rethinking the Role of LLMs in Time Series Forecasting,” arXiv:2602.14744 v1, preprint, 2026. https://arxiv.org/abs/2602.14744
+p77 [15] Chen Xu and Yao Xie, “Conformal prediction interval for dynamic time-series,” ICML, PMLR 139, 11559-11569, 2021. https://proceedings.mlr.press/v139/xu21h.html
+p78 [16] Chen Xu and Yao Xie, “Sequential Predictive Conformal Inference for Time Series,” ICML, PMLR 202, 38707-38727, 2023. https://proceedings.mlr.press/v202/xu23r.html
+p79 [17] Isaac Gibbs and Emmanuel Candès, “Adaptive Conformal Inference Under Distribution Shift,” NeurIPS 34, 2021. https://arxiv.org/abs/2106.00170
+p80 [18] Johannes Bracher, Evan L. Ray, Tilmann Gneiting and Nicholas G. Reich, “Evaluating epidemic forecasts in an interval format,” PLOS Computational Biology 17(2), e1008618, 2021. https://doi.org/10.1371/journal.pcbi.1008618
+p82 Appendix A Forecast panels
+p83 Illustrative panels from the supplied snapshot. The x-axis is the file’s test-week index, not independently verified CDC epidemiological dates. These figures do not establish causality or prospective performance.
+p85 miflu, L=24. ILITOTAL in patient counts against the file’s test-week index. Black is the observed series; the other curves use fixed forecast steps s0–s3. Scored windows: 160. Imported illustrative figure; raw figure inputs were not independently regenerated in this audit.
+p87 patchtst, L=24. ILITOTAL in patient counts against the file’s test-week index. Black is the observed series; the other curves use fixed forecast steps s0–s3. Scored windows: 160. Imported illustrative figure; raw figure inputs were not independently regenerated in this audit.
+p89 nlinear, L=24. ILITOTAL in patient counts against the file’s test-week index. Black is the observed series; the other curves use fixed forecast steps s0–s3. Scored windows: 160. Imported illustrative figure; raw figure inputs were not independently regenerated in this audit.
+table1/row1 Horizon | Our MSE ± SD | Paper MSE | Δ MSE | Our MAE | Paper MAE | Δ MAE
+table1/row2 L=24 | 1.3045 ± 0.0883 | 1.5420 | -15.4% | 0.7482 | 0.7260 | +3.1%
+table1/row3 L=36 | 1.3561 ± 0.1603 | 1.4220 | -4.6% | 0.7712 | 0.7790 | -1.0%
+table1/row4 L=48 | 1.6543 ± 0.1064 | 1.4140 | +17.0% | 0.8381 | 0.7570 | +10.7%
+table1/row5 L=60 | 1.6829 ± 0.2109 | 1.3640 | +23.4% | 0.8596 | 0.7190 | +19.6%
+table1/row6 4-horizon mean | 1.4995 | 1.4355 | +4.5% | 0.8043 | 0.7452 | +7.9%
+table2/row1 # | Model | L24 | L36 | L48 | L60 | Mean MSE | Mean MAE
+table2/row2 1 | MIFlu | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199
+table2/row3 2 | PatchTST | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786
+table2/row4 3 | NLinear | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183
+table2/row5 4 | DNN | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057
+table2/row6 5 | TimeCMA | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676
+table2/row7 6 | Gradient Boosting | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521
+table2/row8 7 | KNN | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293
+table2/row9 8 | Random Forest | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779
+table2/row10 9 | iTransformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476
+table2/row11 10 | Decision Tree | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798
+table2/row12 11 | Hunyuan-1.8B | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755
+table2/row13 12 | Hunyuan-7B | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685
+table2/row14 13 | DeepSeek-R1-Qwen-1.5B | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002
+table2/row15 14 | DeepSeek-R1-Llama-8B | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786
+table2/row16 15 | GRU | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174
+table2/row17 16 | DeepSeek-R1-32B | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935
+table2/row18 17 | LSTM | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303
+table2/row19 18 | DeepSeek-R1-Qwen-14B | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019
+table2/row20 19 | DeepSeek-R1-Qwen-7B | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133
+table2/row21 20 | RNN | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634
+table2/row22 21 | ContextPilot-8B | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255
+table2/row23 22 | Hunyuan-4B | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450
+table2/row24 23 | ContextPilot-14B | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407
+table2/row25 24 | Qwen2.5-1.5B | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725
+table2/row26 25 | Qwen-Time | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794
+table2/row27 26 | SVR | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986
+table2/row28 27 | CALF | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190
+table2/row29 28 | CNN | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720
+table3/row1 Model | PTE (wk) | PIE (%) | Joint passes | s0 PTE | s0 PIE (%)
+table3/row2 MIFlu | 1.128 | 26.846 | 4/16 | 0.347 | 18.884
+table3/row3 PatchTST | 1.240 | 32.755 | 0/16 | 0.681 | 30.553
+table3/row4 NLinear | 1.677 | 9.477 | 4/16 | 0.208 | 3.250
+table4/row1 Model | L | s0 | s1 | s2 | s3
+table4/row2 NLinear | 24 | PASS 0.111 / 3.949 | fail 1.333 / 8.411 | fail 2.333 / 11.943 | fail 2.667 / 18.739
+table4/row3 NLinear | 36 | PASS 0.333 / 4.181 | fail 1.333 / 7.222 | fail 2.111 / 15.313 | fail 2.667 / 18.145
+table4/row4 NLinear | 48 | PASS 0.222 / 2.419 | fail 1.222 / 4.727 | fail 2.222 / 9.979 | fail 2.778 / 16.655
+table4/row5 NLinear | 60 | PASS 0.167 / 2.450 | fail 1.444 / 4.542 | fail 2.556 / 9.952 | fail 3.333 / 13.000
+table4/row6 MIFlu | 24 | PASS 0.000 / 18.307 | fail 0.889 / 26.686 | fail 1.222 / 30.472 | fail 1.333 / 31.638
+table4/row7 MIFlu | 36 | PASS 0.000 / 18.695 | fail 0.778 / 26.333 | fail 1.667 / 31.514 | fail 1.333 / 32.427
+table4/row8 MIFlu | 48 | fail 1.222 / 18.004 | PASS 0.667 / 24.795 | fail 1.222 / 30.133 | fail 1.333 / 33.236
+table4/row9 MIFlu | 60 | PASS 0.167 / 20.530 | fail 1.333 / 25.799 | fail 2.222 / 29.790 | fail 2.667 / 31.177
+table4/row10 PatchTST | 24 | fail 0.667 / 30.580 | fail 1.000 / 34.044 | fail 1.222 / 33.572 | fail 1.222 / 30.722
+table4/row11 PatchTST | 36 | fail 1.000 / 26.235 | fail 1.667 / 32.247 | fail 1.333 / 31.245 | fail 1.333 / 33.854
+table4/row12 PatchTST | 48 | fail 0.556 / 30.360 | fail 1.333 / 30.878 | fail 0.889 / 35.158 | fail 0.889 / 35.002
+table4/row13 PatchTST | 60 | fail 0.500 / 35.035 | fail 1.667 / 34.342 | fail 2.222 / 35.674 | fail 2.333 / 35.133
 table5/row1 Quantity | Value
-table5/row2 Fitted slope of MSE against log₁₀(parameters) | +0.1171
-table5/row3 Coefficient of determination R² | 0.0223
-table5/row4 Models in the fit (parametric arms only) | 11
-table5/row5 Pareto set (non-dominated) | NLinear (2,520 parameters) · PatchTST (531,878 parameters)
-table5/row6 Parameter ratio PatchTST / NLinear | 211.1×
-table5/row7 MSE gain of PatchTST over NLinear | 11.2 %
-table5/row8 PatchTST improvement over seasonal naive | 73.17 %
-table5/row9 Spread of MSE across the 28 arms | 1.5574 (best) … 5.6155 (worst), i.e. 3.6×
-table5/row10 Spearman ρ, MSE against mean PIE (28 arms) | +0.736 (p < 1e-4)
-table5/row11 Spearman ρ, MSE against K&S passes (28 arms) | -0.429 (p = 0.023)
-table6/row1 Model A | Model B | n | mean Δ MSE | A wins | p (Holm) | effect d
-table6/row2 NLinear | PatchTST | 12 | +0.2095 | 2/12 | 0.1172 | 1.15
-table6/row3 Gradient Boosting | RNN | 12 | -1.4029 | 12/12 | 0.06637 | 4.86
-table6/row4 CALF | RNN | 12 | +0.5111 | 0/12 | 0.06637 | 1.65
-table6/row5 CALF | SVR | 12 | +0.2397 | 0/12 | 0.06637 | 1.82
-table6/row6 CALF | TimeCMA | 12 | +2.9704 | 0/12 | 0.06637 | 14.78
-table6/row7 CNN | Decision Tree | 12 | +1.2957 | 0/12 | 0.06637 | 2.69
-table6/row8 CNN | DNN | 12 | +3.4740 | 0/12 | 0.06637 | 6.43
-table7/row1 # | Encoder | Family | Size | Cells | Read-out
-table7/row2 1 | Qwen2.5-1.5B | Qwen2.5 (dense) | 1.5 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table7/row3 2 | DeepSeek-R1-Distill-Qwen-1.5B | DeepSeek-R1 distill (Qwen2) | 1.5 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table7/row4 3 | DeepSeek-R1-Distill-Qwen-7B | DeepSeek-R1 distill (Qwen2) | 7 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table7/row5 4 | DeepSeek-R1-Distill-Llama-8B | DeepSeek-R1 distill (Llama) | 8 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table7/row6 5 | DeepSeek-R1-Distill-Qwen-14B | DeepSeek-R1 distill (Qwen2) | 14 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table7/row7 6 | DeepSeek-R1-Distill-Qwen-32B | DeepSeek-R1 distill (Qwen2) | 32 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table7/row8 7 | Tencent ContextPilot-8B | Tencent ContextPilot | 8 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table7/row9 8 | Tencent ContextPilot-14B | Tencent ContextPilot | 14 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table7/row10 9 | Tencent Hunyuan-1.8B | Tencent Hunyuan | 1.8 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table7/row11 10 | Tencent Hunyuan-4B | Tencent Hunyuan | 4 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table7/row12 11 | Tencent Hunyuan-7B | Tencent Hunyuan | 7 B | 12 / 12 | frozen encoder + one nn.Linear(D, L)
-table7/row13 — | 11 arms | — | — | 132 / 156 | 24 cells skipped
-table8/row1 Variant | Flag | Cells | Question | Status
-table8/row2 full (K=6) | default | — | Reference arm: the MIFlu benchmark instance itself (already in the benchmark table). | in the benchmark table
-table8/row3 no_lora | --no-lora | 12 | Is the accuracy carried by the LoRA adaptation, or by the frozen backbone? | not aggregated
-table8/row4 K=2 | --num-layers 2 | 12 | Depth ladder: does a 2-layer stack lose accuracy? | not aggregated
-table8/row5 K=4 | --num-layers 4 | 12 | Depth ladder: the paper's regional depth. | not aggregated
-table8/row6 K=8 | --num-layers 8 | 12 | Depth ladder: does extra depth help? | not aggregated
-table8/row7 K=12 | --num-layers 12 | 12 | Depth ladder: is there a capacity ceiling? | not aggregated
+table5/row2 Regression slope / R² | +0.1171 / 0.0223
+table5/row3 Models with parameter exports | 11
+table5/row4 Subset Pareto set | NLinear 2,520; PatchTST 531,878
+table5/row5 Parameter ratio | 211.1×
+table5/row6 Descriptive MSE reduction | 11.2%
+table5/row7 ρ(MSE, PIE) | +0.736 (p < 0.0001)
+table5/row8 ρ(MSE, passes) | -0.429 (p = 0.023)
+table6/row1 Model A | Model B | Δ MSE | p raw | p Holm | Effect*
+table6/row2 NLinear | PatchTST | +0.2095 | 0.005859 | 0.1172 | 1.15
+table6/row3 Gradient Boosting | RNN | -1.4029 | 0.000488 | 0.0664 | 4.86
+table6/row4 KNN | NLinear | +1.9138 | 0.000488 | 0.0664 | 22.29
+table6/row5 KNN | MIFlu | +2.2280 | 0.000488 | 0.0664 | 9.89
+table6/row6 KNN | LSTM | -1.2234 | 0.000488 | 0.0664 | 5.28
+table6/row7 iTransformer | TimeCMA | +1.3863 | 0.000488 | 0.0664 | 7.02
+table6/row8 iTransformer | SVR | -1.3443 | 0.000488 | 0.0664 | 10.61
+table7/row1 Encoder | MSE | vs MIFlu | PTE | PIE (%) | Passes
+table7/row2 Hunyuan-1.8B | 4.7374 | 3.04× | 4.406 | 71.428 | 0/16
+table7/row3 Hunyuan-7B | 4.7596 | 3.06× | 5.309 | 75.399 | 0/16
+table7/row4 DeepSeek-R1-Qwen-1.5B | 4.7866 | 3.07× | 5.792 | 78.061 | 0/16
+table7/row5 DeepSeek-R1-Llama-8B | 4.8250 | 3.10× | 4.306 | 77.121 | 0/16
+table7/row6 DeepSeek-R1-32B | 4.9372 | 3.17× | 3.889 | 77.730 | 0/16
+table7/row7 DeepSeek-R1-Qwen-14B | 5.0166 | 3.22× | 4.149 | 76.350 | 0/16
+table7/row8 DeepSeek-R1-Qwen-7B | 5.0308 | 3.23× | 4.458 | 76.373 | 0/16
+table7/row9 ContextPilot-8B | 5.0843 | 3.26× | 4.962 | 78.918 | 0/16
+table7/row10 Hunyuan-4B | 5.1317 | 3.30× | 3.003 | 78.840 | 0/16
+table7/row11 ContextPilot-14B | 5.1949 | 3.34× | 4.965 | 77.764 | 0/16
+table7/row12 Qwen2.5-1.5B | 5.2049 | 3.34× | 5.333 | 74.650 | 0/16
+table8/row1 Variant | Flag | Cells | Status
+table8/row2 Reference K=6 | default | 12 | Already in benchmark
+table8/row3 no_lora | --no-lora | 12 | Not aggregated
+table8/row4 K=2 | --num-layers 2 | 12 | Not aggregated
+table8/row5 K=4 | --num-layers 4 | 12 | Not aggregated
+table8/row6 K=8 | --num-layers 8 | 12 | Not aggregated
+table8/row7 K=12 | --num-layers 12 | 12 | Not aggregated
--- ieee_manuscript_zh corrected upload
+++ ieee_manuscript_zh reviewed revision 4
@@ -1,206 +1,173 @@
-p0 以 MSE 排序不等于以部署为目标排序：流感预测的 28 模型复现与基准
-p1 作者姓名，IEEE 会员 —— 香港城市大学电子工程学系
导师：Prof. Katie Chan —— 评阅人：姓名
(草稿：作者信息与资助说明为占位内容。)
-p2 摘要——流感预测的存在是为了支持决策，但文献按均方误差给它们排名。本文报告对 MIFlu（Moon 等，IEEE JBHI 2025）在美国 CDC 全国流感序列（966 个每周行、7 个通道，与作者文件逐位相同）上的独立复现，以及原工作所没有的28 模型基准：16 个传统预测模型、MIFlu 本身、3 个已发表的基于 LLM 的预测器，以及 11 个冻结大语言模型编码器。复现落在已发表四跨度 MSE 均值的 4.5 % 以内（1.4995 对 1.4355），符号随跨度翻转：L=24 与 L=36 更好，L=48 与 L=60 更差。在统一协议下（种子 42/43/44；共享窗口 (W//16)*16 = 160/144/144/128），精度冠军是 MIFlu（1.5574），其后为 PatchTST（1.6621）与 NLinear（1.8716），全部模型的跨度为 3.6 倍。在 Kramer & Shaman 的流行病学接受判据下（反归一化为患者人数的 ILITOTAL 上，峰值时间误差 <= 1 周且峰值强度误差 <= 25 %），NLinear 与 MIFlu 各通过 4/16，但方式不同：NLinear 通过全部四个步 0 单元，峰值强度误差为 3.2 %；MIFlu 的通过点为 18.3-24.8 %，贴着边界。PatchTST 一个都不通过：其时序最准（均值 1.240 周），但强度误差为 32.8 %。在全部 28 个模型上，精度与校准呈正秩相关（Spearman rho = +0.74），因此 MSE 是有用的筛选；但前沿的排序正好相反，且通过标记与 MSE 呈负秩相关（rho = -0.43，p = 0.023）。参数量无法解决这一选择：MSE 对 log10(参数量) 的斜率为 +0.1171，R2 = 0.0223；帕累托集合为 {NLinear 2,520 参数；PatchTST 531,878 参数}；211 倍参数成本换来的 11.2 % MSE 差异在 136 对 Holm 校正后不显著（p = 0.117；n = 12 时没有任何一对能存活）。11 个冻结编码器无一通过判据，且每一个都差于决策树。我们主张：应把接受判据与 MSE 并列报告，而按 MSE 排序的榜单可能把部署决策引向错误方向。
-p3 关键词——流感预测；复现研究；基准；峰值时间误差；峰值强度误差；评测协议；模型选择；冻结语言模型编码器。
-p4 I. 引言
-p5 流感预测的存在是为了支持决策：何时升级响应、准备多少容量、何时宣布某季已过峰值。这些决策背后的损失不是平方误差。一个把峰值判断晚了两周、或把峰值高度低估 40 % 的预测，即使平均误差很小，也已经使决策失败；反之，平均误差略大但峰值位置与幅度都准确的预测，可能是更有用的对象。然而文献的默认排序指标仍是 MSE，模型选择也随之而行。
-p6 本文按该默认标准本身来检验它。我们复现 MIFlu（Moon 等，IEEE JBHI 2025）——CDC 全国流感数据上当前的多模态最先进方法——并移除其检查点选择中的数据泄漏；把它放进同一窗口与种子下的 28 模型基准；然后对每个模型计分两次：一次用文献报告的指标（MSE），一次用公共卫生采用的判据（Kramer & Shaman 峰值判据）。两种计分并不一致，而且这种不一致是系统性的，不是边际的。
-p7 贡献。 (1) 对 MIFlu 的无泄漏复现，报告逐跨度符号而非单一均值，因而报告的是符号交叉而不是改进。(2) 统一协议下的 28 模型基准——16 个传统预测模型、MIFlu、3 个已发表的基于 LLM 的预测器、11 个冻结 LLM 编码器——窗口、种子、指标与检查点规则完全一致。(3) 发现部署排序不是精度排序：前沿在峰值校准上反转，且接受判定与 MSE 呈负秩相关。(4) 参数成本与显著性分析，说明精度亚军 211 倍的成本换来的差异在本基准下无法分辨。
-p8 II. 相关工作
-p9 长跨度预测架构。 PatchTST（Nie 等，ICLR 2023）对输入序列做分片并采用通道独立性，在标准基准上报告三种子均值；iTransformer（Liu 等，ICLR 2024）反转注意力轴，同样如此。Zeng 等（AAAI 2023）主张线性模型可与 Transformer 预测器竞争，本文基准在流感场景中复现了这一主张：NLinear 在 28 个模型中排第三，参数量比精度冠军少三个数量级。
-p10 流行病学评估。 Kramer & Shaman（2019）确立了本文采用的判据：只有当峰值时间误差不超过一周、峰值强度误差不超过 25 % 时，预测才算有用。流行病学文献按固定预测步计分，机器学习文献按跨度计分。本文同时报告两者，因为它们不是同一对象：模型可以在一个上获胜、在另一个上失败。
-p11 冻结基础模型特征。 “冻结编码器 + 小训练头”是非文本模态的强基线，MIFlu 本身就依赖冻结的 GPT-2 主干、文本提示与低秩适配。尚未确立的是：在 966 行流行病学序列的规模上，编码器的选择是否有影响。第 VI-F 节报告该实验：十一个编码器、一个共享线性头，以及一个负面结果。
-p12 复现与基准研究。 复现工作正日益被视为独立的贡献，因为基准的价值不会超过其协议。本文的贡献属于这一类：我们不提出新架构，而是让现有比较变得诚实，然后测量这个诚实的比较说了什么。
-p13 III. 数据
-p14 数据是随 MIFlu 发布的美国 CDC 全国流感监测序列：966 个每周行、7 个数值通道（% WEIGHTED ILI、% UNWEIGHTED ILI、AGE 0-4、AGE 5-24、ILITOTAL、NUM. OF PROVIDERS、OT）。在任何模型训练之前，本地文件已被验证与作者发布文件逐位相同（最大绝对差 0.000e+00），因为只要有一周错位，本文的每个数字都会移动。划分为按时间 70/10/20——第 0-675 行训练、676-772 行验证、773-965 行测试——并带严格包含约束，使窗口的输入区间完全位于目标区间之前；被接纳的测试目标起始行最小下标为 773。标准化使用仅在训练段上拟合的 StandardScaler（ILITOTAL 均值 9,439.84 人，标准差 9,003.15；OT 均值 493,629）。
-p15 标准化常数决定了指标设计。七个通道的训练均值从 1.74 到 493,629，无法平均成一个具有物理单位的量：7 变量聚合是一个损失值而不是序列，无法反归一化为患者人数。因此峰值技巧指标只使用 ILITOTAL。
-p16 IV. 方法
-p17 A. 两套协议
-p18 复现使用 10 次重复、种子 2021-2030，与原作者的协议一致，并使用验证集选择的检查点。基准对每个模型使用 3 个种子 42/43/44，以及相同的检查点规则。它们是两个不同的实验，其数字从不互相比较；MIFlu 同时出现在两者之下，是因为“复现”与“基准行”提出了互不兼容的要求，而只有复现实例被作为复现引用。
-p19 B. 评测窗口
-p20 MIFlu 自己的数据加载器使用 DataLoader(batch_size=16, drop_last=True)，会丢弃最后一个不满的批次：170→160、158→144、146→144、134→128。被丢弃的窗口实测更难（MSE 1.3929–1.4423，约为保留窗口均值的 1.41 倍）。若 MIFlu 按 160/144/144/128 计分而其他模型按 170/158/146/134 计分，就等于给 MIFlu 一个更容易的测试集。因此全部 17 个模型统一在裁剪后的同一批窗口上计分。
-p21 C. 指标
-p22 精度是标准化空间下的 7 变量聚合 MSE 与 MAE，对通道与窗口取平均，按跨度报告并给出四跨度均值。峰值技巧把 ILITOTAL 反归一化为患者人数，逐季节度量峰值时间误差（PTE，周）与峰值强度误差（PIE，占观测峰值的百分比），在固定步 0/1/2/3（即提前 1/2/3/4 周）上评估。只有 PTE <= 1 周且 PIE <= 25 % 的单元才算通过。阈值归因于 Kramer & Shaman（2019），并标注 [to verify] 待与原文核对；峰值检测（find_peaks(prominence = 0.15 x range, distance = 15)，±8 周匹配）是本研究的工程选择，不是已发表判据的一部分。
-p23 D. 检查点选择
-p24 每个模型在验证段上选择检查点。作者的代码在测试集上选择（main_ILI_lora.py 第 211 与 225 行）；这属于泄漏，本文不复刻。凡出现复现数字之处均披露该偏离。
-p25 E. 统计
-p26 配对比较在 12 个配对（跨度 x 种子）单元上使用精确符号翻转检验，对全部 136 对模型做 Holm-Bonferroni 校正，并给出 bootstrap 95 % 置信区间（10,000 次重采样）与 Cohen's d。所有模型共享同三个种子，这正是 12 个单元可以配对的原因；n = 12 时最小可达 p 为 2/2¹² ≈ 0.00049，我们如实说明该下限而不隐藏。136 对中有 128 对在校正前显著；正确 Holm 校正后无一存活，因为最小可达校正 p 为 0.066。
-p27 F. 硬件与来源
-p28 17 个传统模型的 204 个单元在香港城市大学 Burgundy 集群 stingy 分区的 A100-SXM4-80GB 上运行，逐单元记录 GPU 型号、分区、节点与作业号；MIFlu 与编码器单元在同一分区运行，并在集群上留有逐单元清单。12 个 NLinear 单元最初在 V100-SXM2-32GB 上测得，后在 A100 上重跑；两者一致到 1e-6，因此没有任何排名依赖硬件。本文不作任何计时断言。
-p29 V. 实验
-p30 本文按以下顺序报告四项分析。复现（表 I）： 四个跨度各十次重复，对照已发表数值。精度（表 II）： 28 个模型 x 4 个跨度 x 3 个种子，按四跨度均值排序。峰值技巧（表 III-IV）： Kramer & Shaman 判据，按固定步，在反归一化后的患者人数上计算。效率与显著性（表 V-VI）： 帕累托前沿与对数参数回归，然后是 Holm 校正配对检验。第五条轴——冻结 LLM 编码器（表 VII）——与消融阶梯（表 VIII）补全矩阵；阶梯仍在进行中，作为设计而非结果报告。
-p31 VI. 结果
-p32 A. 复现
-p33 四跨度均值为 1.4995，对比已发表的 1.4355，即差 4.5 %，且逐跨度符号翻转：L=24（1.3045 对 1.542）与 L=36（1.3561 对 1.422）更好，L=48（1.6543 对 1.414）与 L=60（1.6829 对 1.364）更差。MAE 一侧同样（0.8043 对 0.7452，+7.9 %）。只报告均值会藏起这一结构。有两种解释仍与该模式相符——基于验证集的检查点选择，以及长跨度方差（十次重复在 L=60 的范围是 1.401-1.984）——现有数据尚无法区分。
-p34 表 1. MIFlu 表 V 的复现——符号反转。7 变量 z 空间聚合 MSE，10 次重复，种子 2021–2030。
-p35 Δ 为正表示本文比论文更差。本文在 L24（−15.4 %）与 L36（−4.6 %）更好，在 L48（+17.0 %）与 L60（+23.4 %）更差；4 个跨度的均值在 MSE 上为 +4.5 %、在 MAE 上为 +7.9 %。唯一可辩护的表述是“在 4 个跨度的 MSE 均值上复现到 4.5 % 以内，且符号随跨度翻转”，绝不能说“我们超过了论文”。窗口为 (W//16)*16 = 160/144/144/128；A100-SXM4-80GB、stingy 分区、CityU HPC Burgundy。来源：ESSAY_VS_REPRODUCTION_TABLE_V.csv。
-p36 要点。 这是一次复现，不是改进：四跨度均值差 4.5 %，且符号依赖跨度。两处已披露的偏离意味着逐跨度的胜出不能主张为“优于原论文”。
-p37 B. 精度：28 模型排名
-p38 MIFlu 是精度冠军，1.5574，其后是 PatchTST（1.6621）与 NLinear（1.8716）；28 个模型的跨度为 1.5574 到 5.6155，即 3.6 倍，且全部 28 个都优于季节朴素基线（6.2132）。两个已发表的基于 LLM 的预测器被最近邻基线击败（KNN 3.7854 对 Qwen-Time 5.2557、CALF 5.5785）。一个 2,520 参数的线性模型在 28 个模型中排第三，除 PatchTST 外领先所有 Transformer。
-p39 表 2. 28 个模型的基准：逐跨度与四跨度均值的 7 变量 z 空间聚合 MSE，以及四跨度 MAE。种子 42/43/44 取均值，共享窗口 (W//16)*16 = 160/144/144/128。
-p40 越低越好。为版面清晰省略逐跨度 MAE，其值在 02_数字表格/BENCH_MSE_BY_MODEL_L.csv 中。DLinear 按项目决定被排除（原论文表 V 已给出它的结果，因此不构成新的基线）。季节朴素基线（52 周滞后）在同一批窗口上的 4 跨度均值为 6.2132，28 个模型全部优于它。硬件：A100-SXM4-80GB、stingy 分区、CityU HPC Burgundy——17 个传统模型中 204/204 个单元均带该实测来源，MIFlu 与编码器单元在同一分区运行并留有逐单元清单。参数量取自 BENCH_EFFICIENCY.csv 的训练后总数；经典学习器在此意义上无参数量、MIFlu 未导出，故留空。
-p41 要点。 仅凭精度无法确定可部署的模型。前三名的 MSE 彼此相差在 20 % 以内，而排名说明的是哪个模型最拟合这个测试集，而不是哪个支持预测本来要服务的决策。
-p42 C. 峰值技巧：部署排序
-p43 在 Kramer & Shaman 判据下，排名发生变化。NLinear 与 MIFlu 各通过 4/16，但方式不同：NLinear 通过全部四个步 0 单元，峰值强度误差为 3.2 %；MIFlu 的四个通过点为 PIE 18.3-24.8 %，贴着 25 % 边界，且在 L=48 步 0 失败（PTE 1.22 周）。PatchTST 一个都不通过：其时序是本研究最准的（均值 PTE 1.24 周），但 PIE 为 32.8 %，在每个单元都未满足校准一半。其余每个模型在两半上都不通过。
-p44 表 3. 逐固定步的峰值技巧：ILITOTAL 反归一化为患者人数后的 PTE（周）与 PIE（%），对四个跨度取均值；✓ 表示通过 Kramer & Shaman 判据（PTE ≤ 1 周且 PIE ≤ 25%）。
-p45 有两个模型通过，但通过的方式不同。NLinear 在步 0 的四个单元全部通过（16 个中 4 个）：全部 16 个单元的均值 PTE 1.677 周、均值 PIE 9.477 %，步 0 的 PIE 为 3.25 %——比判据宽松一个数量级。MIFlu 同样通过 4/16，但其中三个是步 0（L=48 在步 0 以 PTE 1.222 周失败），第四个是 L=48 的步 1；它的均值 PIE 为 26.846 %，即它的通过是贴着 25 % 边界，而不是落在判据内部。PatchTST 的时序最准（均值 PTE 1.240 周），但均值 PIE 为 32.755 %，通过数为 0：它在每个单元都未满足判据的校准一半。窗口 160/144/144/128；种子 42/43/44；A100-SXM4-80GB、stingy 分区、CityU HPC Burgundy。
-p46 表 4. 同一判据的逐格展开：三个具名模型的每个（跨度，步）组合。PASS 要求同一格内 PTE ≤ 1 周且 PIE ≤ 25 %。
-p47 每模型 16 格 = 4 个跨度 × 4 个步，每格为种子 42/43/44 的均值。NLinear 通过 4/16，全部在步 0（PIE 2.4–4.2 %）；MIFlu 通过 4/16——三个在步 0、一个在 L=48 步 1，PIE 为 18.3–24.8 %，即贴着边界；PatchTST 一个都不通过，因为其 PIE 在每个步都停在 26–35 % 区间。峰值检测：find_peaks(prominence = 0.15 × range, distance = 15) 与 ±8 周匹配——本研究的工程选择，不是已发表判据的一部分。1 周 / 25 % 阈值归因于 Kramer & Shaman (2019)，但仍标注 [to verify]，待与原文核对。
-p48 要点（发现 1）。 部署排序不是精度排序。在全部 28 个模型上，MSE 更好确实伴随校准更好（对均值 PIE 的 Spearman ρ = +0.74），因此 MSE 是有用的筛选；但在 MSE 最低的三个模型中，校准排序完全反转——NLinear（第 3）9.5 %、MIFlu（第 1）26.8 %、PatchTST（第 2）32.8 %——且通过标记与 MSE 呈负秩相关（ρ = -0.43，p = 0.023）。MSE 第二名一个都不通过；第三名通过每个跨度的提前一周。
-p49 D. 精度与效率
-p50 在 11 个含参数模型上，MSE 对 log10(参数量) 的斜率为 +0.1171，R² = 0.0223：规模只解释约 2 % 的方差，且符号不利。帕累托集合恰好两个模型——2,520 参数的 NLinear 与 531,878 参数的 PatchTST——即 211 倍参数量换取 11.2 % 的 MSE 下降。这笔交易是否划算取决于部署场景，也取决于部署是否需要峰值技巧：若需要，那 11.2 % 的优势换来的却是一个完全不能满足判据的模型。
-p51 表 5. 精度—效率汇总，以及精度与峰值技巧之间的秩相关。
-p52 斜率为正意味着参数越多 MSE 反而越高（越差），R² = 0.0223 说明规模只能解释约 2% 的方差：在本数据集上参数量不是一个有用的选择准则。两条帕累托记录应读作权衡而不是排名——PatchTST 用 211 倍参数量换取 11.2% 的 MSE 下降。最后两行让峰值技巧的论断保持诚实：在全部 28 个模型上，MSE 更好确实伴随校准更好（ρ = +0.74），所以两个轴并非彼此独立；真正失效的是前沿内部的排序（见峰值技巧两表）与接受判定——后者与 MSE 呈负秩相关（ρ = -0.43）。窗口 160/144/144/128；种子 42/43/44。
-p53 E. 统计显著性
-p54 帕累托论证所需的那一对是 NLinear 对 PatchTST：平均 Δ MSE 为 +0.2095（对 PatchTST 有利），NLinear 只在 12 个单元中的 2 个更低，原始 p = 0.0059，而在全部 136 对上校正后 p(Holm) = 0.117；d = 1.15。这一对在 136 个 p 值中排第 117 小，因此按显著性排序的表会省略它——这正是表 VI 把它放在第一行、把六个最显著的对放在下面的原因。
-p55 表 6. 12 个配对（跨度 × 种子）单元上的配对符号翻转检验，对全部 136 对做 Holm 校正（由原始 p 值重算）。第一行（粗体）为正文讨论的帕累托对；其余为 p 值最小的六对，用作对照。
-p56 Δ 为正表示模型 A 的 MSE 更大。12 个单元全部配对（同跨度、同种子），这只有在所有模型统一使用 42/43/44 时才成立。导出的 p_holm 列由反向累积最小值生成，不是有效的 Holm 校正；本表的值由 p_raw 重算。n = 12 时最小可达原始 p 为 2/2¹² ≈ 0.00049，因此在 m = 136 对下最小可达校正 p 为 0.066，没有任何一对能在 0.05 水平存活（校正前有 128/136 对显著）。第一行为何不在第二块中：NLinear 对 PatchTST 的校正 p = 0.117，在 136 对中排第 117 小，因此按显著性排序的表会恰好省略帕累托论证所需的那一对。该差异在这个样本量下无法分辨；这是“未能拒绝”，不是“证明相等”（d = 1.15，且 PatchTST 在 12 个单元中有 10 个更低）。
-p57 要点（发现 2）。 211 倍成本换来的 11.2 % MSE 差异，在本基准的 n = 12 下无法分辨。这是“未能拒绝相等”，不是“证明相等”（d = 1.15；PatchTST 在 12 个单元中的 10 个更低）。可辩护的结论是“未能为 211 倍成本确立精度优势”。
-p58 F. 冻结 LLM 编码器
-p59 十一个编码器（Qwen2.5-1.5B；DeepSeek-R1-Distill-Qwen 的 1.5B、7B、14B、32B；DeepSeek-R1-Distill-Llama-8B；Hunyuan-1.8B/4B/7B；ContextPilot-8B/14B）各自冻结，并接同一个共享线性头、按通道独立训练：156 个单元中完成 132 个。最好是 Hunyuan-1.8B，4.7374；最差是 Qwen2.5-1.5B，5.2049，即 MIFlu 的 3.04 至 3.34 倍。每一个都差于决策树（4.3198），且没有任何一个在任何单元通过 Kramer & Shaman 判据。家族内部的排序不是规模的单调函数。
-p60 表 7. 11 个冻结 LLM 编码器模型（种子 42/43/44、四个跨度、每个模型 12 个单元）。
-p61 每个模型都是一个冻结编码器加一个共享线性头，按通道独立训练，不更新任何编码器权重。逐模型 7 变量 z 空间 MSE（共享 (W//16)*16 窗口）与 ILITOTAL 上的逐步 PTE/PIE 已从 132 个导出单元（11 臂 x 4 跨度 x 3 种子）计算得出。两个仅嵌入模型与五个被排除模型见下一张表。
-p62 要点（发现 3）。 协议被设计成给该想法最好的机会——冻结特征、线性读出、通道独立——而它仍然失败。这不能证明编码器永远不可能有帮助，但任何声称在本任务上从冻结语言特征获得增益的主张，都需要给出机制与对照。
-p63 G. 消融阶梯
-p64 阶梯要问 MIFlu 的精度从何而来：LoRA 适配，还是 GPT-2 堆叠的深度。它是五个变体（去掉 LoRA；K = 2、4、8、12 层）在 4 个跨度与 3 个种子上共 60 个单元，与表 II 中已有的完整 K=6 臂比较。有一项结果已经确立，而且是关于文本分支的负面结论：文本 token 位于因果掩码之后、输出头只读时间分片，因此 --no-text 与完整臂逐位相同（由 tests_archive/test_miflu_ablations.py 断言），这意味着文本消融是结构验证，不是效应。在本草稿所依据的快照中，其余变体的 60 个单元里完成 27 个，因此不声明任何深度趋势。阶梯作为设计与状态报告，不作为结果。
-p65 表 8. 消融阶梯（项目计划中称表 VIII）：五个变体、60 个单元，以及每个变体要回答的问题。
-p66 每个变体 4 跨度 × 3 种子 = 12 个单元；五个变体共 60 个单元；参考臂即基准表已报告的 12 个单元，不重复计数。在本文档所依据的快照中，60 个单元里已完成 27 个（驱动作业 722968），且逐变体导出尚未取回，因此本文档只报告设计与完成数，不声明任何深度趋势。--no-text 变体有意不列为一行：文本 token 位于因果掩码之后、输出头只读时间分片，故 --no-text 与完整臂逐位相同——这是结构验证（由 tests_archive/test_miflu_ablations.py 断言），绝不是消融效应。
-p67 VII. 效度威胁
-p68 单一数据集。 所有结果都来自一个国家的一条 966 行全国序列。本文不能确立跨数据集或跨区域的普适性，而本可检验它的区域评测与滚动原点评测尚未运行。
-p69 检验的分辨率。 在 n = 12 个配对单元下，最小可达 p 为 2/2¹² ≈ 0.00049；不显著的结果是“未能拒绝”，而不是“相等的证据”。因此我们把帕累托结论表述为“未能确立优势”，而不是“没有优势”。
-p70 判据归属。 1 周 / 25 % 阈值归因于 Kramer & Shaman（2019），但标注 [to verify] 待与原文核对；峰值检测器是我们自己的工程选择。不同的检测器会改变 PTE/PIE，但不会改变 MSE 排名。
-p71 编码器维度的范围。 该实验测试的是冻结特征加线性读出，不测试生成、提示或微调；其负面结果不可读作关于 LLM 预测器的一般性主张——经过微调的 MIFlu 恰恰是精度冠军。
-p72 消融未完成。 在 60 个单元聚合之前，深度与 LoRA 的问题仍未回答。本文报告阶梯的设计与完成数，不声明任何趋势。
-p73 复现的两处偏离。 基于验证集的检查点选择与 7 变量指标是无泄漏、可与表 V 比较的结果所必需的，但它们意味着逐跨度的胜出不是同条件的“优于”主张。
-p74 VIII. 结论
-p75 本文在四跨度 MSE 均值上把 MIFlu 复现到 4.5 % 以内（符号随跨度翻转），在统一协议下基准评估了 28 个预测模型，并证明部署排序不是精度排序：精度冠军不是校准冠军；MSE 亚军不通过任何一格流行病学判据；而每个跨度都提前一周通过的那个模型，参数量比亚军少 211 倍，并且是帕累托前沿中更便宜的一员。参数量不是精度的代理（斜率 +0.1171，R² 0.0223），而 211 倍成本换来的差异在本基准下无法分辨（p(Holm) = 0.117；136 对校正后无一存活）。十一个冻结 LLM 编码器则直接失败。实践结论是：流行病学预测的模型选择应基于接受判据，并把 MSE 并列报告；仅按 MSE 排序的榜单可能把部署决策引向错误方向。
-p76 IX. 参考文献
-p77 [1] J. Moon 等，“MIFlu: Large Language Model-Based Multimodal Influenza Forecasting”，IEEE J. Biomed. Health Inform.，2025，doi: 10.1109/JBHI.2025.3561214。
-p78 [2] Y. Nie, N. H. Nguyen, P. Sinthong, J. Kalagnanam，“A Time Series is Worth 64 Words: Long-term Forecasting with Transformers”，Proc. ICLR，2023，arXiv:2211.14730。
-p79 [3] Y. Liu 等，“iTransformer: Inverted Transformers Are Effective for Time Series Forecasting”，Proc. ICLR，2024。
-p80 [4] A. Zeng, M. Chen, L. Zhang, Q. Xu，“Are Transformers Effective for Time Series Forecasting?”，Proc. AAAI，2023。
-p81 [5] A. M. Kramer, J. Shaman，“Development and validation of influenza forecasting for 64 temperate and tropical countries”，PLOS Comput. Biol.，第 15 卷第 2 期，e1006742，2019，doi: 10.1371/journal.pcbi.1006742。
-p82 [6] 美国疾病控制与预防中心，“FluView: Weekly U.S. Influenza Surveillance Report”，全国 ILI 序列（966 个每周行、7 个通道）。
-p83 [7] Qwen 团队，“Qwen2.5 Technical Report”，2024；DeepSeek-AI，“DeepSeek-R1”，2025；腾讯 Hunyuan 与 ContextPilot 模型卡，HuggingFace。
-p84 卷号、页码与 DOI 将在投稿时补全并对照出版方记录核对；本草稿断言作者、标题、发表处与年份。
-p86 附录 A. 预测曲线
-p87 下图展示三个代表性模型在最短跨度（L = 24）上逐步预测与真值的对比。黑 = 真值；每步 0/1/2/3（提前 1/2/3/4 周）一条预测线；纵轴为 ILITOTAL 患者数。全部 28 个模型 x 4 个跨度的完整图见补充材料。
-p89 MIFLU，L=24。 y 为用训练集拟合的 StandardScaler 反归一化后的 ILITOTAL 患者人数（均值 9,439.84，标准差 9,003.15 人）；x 为测试集周次。黑线为真值，其余每步 0/1/2/3（即提前 1/2/3/4 周）一条预测线。图中指标为 ILITOTAL 患者人数（峰值技巧所用序列），不是无法反归一化的 7 变量聚合。评测窗口：L=24 时取前 (W//16)*16 = 160 个测试窗口（共 170 个），与 MIFlu 的 drop_last=True 规则一致。硬件：CityU HPC（复现运行；单次 GPU 记录见运行日志，未包含在该导出中）。
-p91 PATCHTST，L=24。 y 为用训练集拟合的 StandardScaler 反归一化后的 ILITOTAL 患者人数（均值 9,439.84，标准差 9,003.15 人）；x 为测试集周次。黑线为真值，其余每步 0/1/2/3（即提前 1/2/3/4 周）一条预测线。图中指标为 ILITOTAL 患者人数（峰值技巧所用序列），不是无法反归一化的 7 变量聚合。评测窗口：L=24 时取前 (W//16)*16 = 160 个测试窗口（共 170 个），与 MIFlu 的 drop_last=True 规则一致。硬件：A100-SXM4-80GB，stingy 分区，CityU HPC Burgundy。
-p93 NLINEAR，L=24。 y 为用训练集拟合的 StandardScaler 反归一化后的 ILITOTAL 患者人数（均值 9,439.84，标准差 9,003.15 人）；x 为测试集周次。黑线为真值，其余每步 0/1/2/3（即提前 1/2/3/4 周）一条预测线。图中指标为 ILITOTAL 患者人数（峰值技巧所用序列），不是无法反归一化的 7 变量聚合。评测窗口：L=24 时取前 (W//16)*16 = 160 个测试窗口（共 170 个），与 MIFlu 的 drop_last=True 规则一致。硬件：A100-SXM4-80GB，stingy 分区，CityU HPC Burgundy。
-table1/row1 跨度 | 本文（10 次均值 ± 标准差） | 论文 | Δ MSE | 符号 | 本文 MAE | 论文 MAE | Δ MAE
-table1/row2 L=24 | 1.3045 ± 0.0883 | 1.542 | -15.4 % | 胜 | 0.7482 | 0.726 | +3.1 %
-table1/row3 L=36 | 1.3561 ± 0.1603 | 1.422 | -4.6 % | 胜 | 0.7712 | 0.779 | -1.0 %
-table1/row4 L=48 | 1.6543 ± 0.1064 | 1.414 | +17.0 % | 负 | 0.8381 | 0.757 | +10.7 %
-table1/row5 L=60 | 1.6829 ± 0.2109 | 1.364 | +23.4 % | 负 | 0.8596 | 0.719 | +19.6 %
-table1/row6 4 跨度均值 | 1.4995 | 1.435 | +4.5 % | 负 | 0.8043 | 0.745 | +7.9 %
-table2/row1 # | 模型 | 族 | MSE L24 | MSE L36 | MSE L48 | MSE L60 | MSE 4L | MAE 4L | 参数量
-table2/row2 1 | MIFlu | 基于 LLM | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199 | —
-table2/row3 2 | PatchTST | Transformer | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786 | 531,878
-table2/row4 3 | NLinear | 线性 | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183 | 2,520
-table2/row5 4 | DNN | 神经网络 | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057 | 33,048
-table2/row6 5 | TimeCMA | 基于 LLM | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676 | 125,830,824
-table2/row7 6 | Gradient Boosting | 经典机器学习 | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521 | —
-table2/row8 7 | KNN | 经典机器学习 | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293 | —
-table2/row9 8 | Random Forest | 经典机器学习 | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779 | —
-table2/row10 9 | iTransformer | Transformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476 | 75,672
-table2/row11 10 | Decision Tree | 经典机器学习 | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798 | —
-table2/row12 11 | Hunyuan-1.8B | 冻结 LLM 编码器 | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755 | —
-table2/row13 12 | Hunyuan-7B | 冻结 LLM 编码器 | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685 | —
-table2/row14 13 | DeepSeek-R1-Qwen-1.5B | 冻结 LLM 编码器 | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002 | —
-table2/row15 14 | DeepSeek-R1-Llama-8B | 冻结 LLM 编码器 | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786 | —
-table2/row16 15 | GRU | 神经网络 | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174 | 14,424
-table2/row17 16 | DeepSeek-R1-32B | 冻结 LLM 编码器 | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935 | —
-table2/row18 17 | LSTM | 神经网络 | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303 | 18,712
-table2/row19 18 | DeepSeek-R1-Qwen-14B | 冻结 LLM 编码器 | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019 | —
-table2/row20 19 | DeepSeek-R1-Qwen-7B | 冻结 LLM 编码器 | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133 | —
-table2/row21 20 | RNN | 神经网络 | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634 | 5,848
-table2/row22 21 | ContextPilot-8B | 冻结 LLM 编码器 | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255 | —
-table2/row23 22 | Hunyuan-4B | 冻结 LLM 编码器 | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450 | —
-table2/row24 23 | ContextPilot-14B | 冻结 LLM 编码器 | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407 | —
-table2/row25 24 | Qwen2.5-1.5B | 冻结 LLM 编码器 | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725 | —
-table2/row26 25 | Qwen-Time | 基于 LLM | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794 | 1,544,084,680
-table2/row27 26 | SVR | 经典机器学习 | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986 | —
-table2/row28 27 | CALF | 基于 LLM | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190 | 126,421,416
-table2/row29 28 | CNN | 神经网络 | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720 | 22,488
-table3/row1 模型 | PTE 步0（1 周） | PIE 步0（%） | PTE 步1（2 周） | PIE 步1（%） | PTE 步2（3 周） | PIE 步2（%） | PTE 步3（4 周） | PIE 步3（%） | 通过数
-table3/row2 NLinear | 0.21 ✓ | 3.2 ✓ | 1.33 | 6.2 | 2.31 | 11.8 | 2.86 | 16.6 | 4/16
-table3/row3 MIFlu | 0.35 | 18.9 | 0.92 | 25.9 | 1.58 | 30.5 | 1.67 | 32.1 | 4/16
-table3/row4 PatchTST | 0.68 | 30.6 | 1.42 | 32.9 | 1.42 | 33.9 | 1.44 | 33.7 | 0/16
-table3/row5 RNN | 0.96 | 57.6 | 1.97 | 60.0 | 3.00 | 61.8 | 3.97 | 63.2 | 0/16
-table3/row6 GRU | 1.14 | 58.1 | 2.06 | 59.9 | 3.00 | 62.4 | 3.75 | 64.0 | 0/16
-table3/row7 TimeCMA | 1.54 | 50.0 | 2.03 | 51.4 | 2.97 | 55.6 | 2.78 | 57.5 | 0/16
-table3/row8 DNN | 1.92 | 37.8 | 2.64 | 40.1 | 2.78 | 43.7 | 2.86 | 44.9 | 0/16
-table3/row9 Qwen-Time | 2.10 | 40.5 | 3.08 | 50.3 | 3.14 | 55.9 | 3.75 | 61.6 | 0/16
-table3/row10 iTransformer | 2.19 | 67.7 | 2.25 | 68.6 | 2.11 | 69.9 | 1.92 | 71.1 | 0/16
-table3/row11 LSTM | 3.04 | 64.6 | 3.33 | 65.6 | 3.83 | 67.5 | 3.94 | 68.7 | 0/16
-table3/row12 KNN | 3.12 | 65.8 | 2.75 | 67.7 | 2.75 | 68.7 | 2.42 | 69.4 | 0/16
-table3/row13 DeepSeek-R1-32B | 3.14 | 77.3 | 3.19 | 77.7 | 3.86 | 78.1 | 5.36 | 77.7 | 0/16
-table3/row14 DeepSeek-R1-Qwen-14B | 3.54 | 75.4 | 4.08 | 76.3 | 4.50 | 76.6 | 4.47 | 77.2 | 0/16
-table3/row15 DeepSeek-R1-Qwen-7B | 3.69 | 76.0 | 4.44 | 76.7 | 4.47 | 76.2 | 5.22 | 76.6 | 0/16
-table3/row16 CALF | 3.75 | 80.0 | 3.42 | 80.5 | 3.92 | 80.6 | 4.42 | 80.8 | 0/16
-table3/row17 Hunyuan-4B | 3.88 | 79.4 | 3.08 | 79.3 | 2.22 | 78.7 | 2.83 | 78.0 | 0/16
-table3/row18 SVR | 3.92 | 77.3 | 3.50 | 79.9 | 3.33 | 80.4 | 2.75 | 80.6 | 0/16
-table3/row19 ContextPilot-14B | 4.11 | 76.8 | 4.75 | 77.8 | 5.44 | 78.1 | 5.56 | 78.4 | 0/16
-table3/row20 Hunyuan-1.8B | 4.26 | 69.7 | 4.81 | 70.7 | 4.19 | 71.9 | 4.36 | 73.4 | 0/16
-table3/row21 Qwen2.5-1.5B | 4.31 | 74.6 | 5.08 | 74.8 | 5.56 | 74.7 | 6.39 | 74.6 | 0/16
-table3/row22 Decision Tree | 4.54 | 55.1 | 5.06 | 53.8 | 5.64 | 50.2 | 4.75 | 56.7 | 0/16
-table3/row23 DeepSeek-R1-Llama-8B | 4.67 | 76.1 | 4.36 | 77.0 | 4.25 | 77.5 | 3.94 | 77.9 | 0/16
-table3/row24 ContextPilot-8B | 4.90 | 78.3 | 4.22 | 78.9 | 5.28 | 79.1 | 5.44 | 79.3 | 0/16
-table3/row25 Hunyuan-7B | 5.12 | 73.9 | 5.81 | 75.7 | 6.03 | 75.9 | 4.28 | 76.1 | 0/16
-table3/row26 Gradient Boosting | 5.33 | 52.0 | 4.67 | 58.7 | 4.75 | 62.8 | 5.08 | 65.4 | 0/16
-table3/row27 Random Forest | 5.35 | 65.9 | 5.19 | 66.5 | 5.58 | 67.0 | 5.64 | 67.6 | 0/16
-table3/row28 DeepSeek-R1-Qwen-1.5B | 5.83 | 77.4 | 5.44 | 78.0 | 5.78 | 78.3 | 6.11 | 78.5 | 0/16
-table3/row29 CNN | 6.28 | 81.1 | 6.78 | 81.9 | 6.22 | 82.2 | 7.14 | 82.6 | 0/16
-table4/row1 模型 | 跨度 | 步0（1周） | 步1（2周） | 步2（3周） | 步3（4周）
-table4/row2 NLinear | L=24 | PASS (0.11 wk, 3.9 %) | fail (1.33 wk, 8.4 %) | fail (2.33 wk, 11.9 %) | fail (2.67 wk, 18.7 %)
-table4/row3 NLinear | L=36 | PASS (0.33 wk, 4.2 %) | fail (1.33 wk, 7.2 %) | fail (2.11 wk, 15.3 %) | fail (2.67 wk, 18.1 %)
-table4/row4 NLinear | L=48 | PASS (0.22 wk, 2.4 %) | fail (1.22 wk, 4.7 %) | fail (2.22 wk, 10.0 %) | fail (2.78 wk, 16.7 %)
-table4/row5 NLinear | L=60 | PASS (0.17 wk, 2.5 %) | fail (1.44 wk, 4.5 %) | fail (2.56 wk, 10.0 %) | fail (3.33 wk, 13.0 %)
-table4/row6 MIFlu | L=24 | PASS (0.00 wk, 18.3 %) | fail (0.89 wk, 26.7 %) | fail (1.22 wk, 30.5 %) | fail (1.33 wk, 31.6 %)
-table4/row7 MIFlu | L=36 | PASS (0.00 wk, 18.7 %) | fail (0.78 wk, 26.3 %) | fail (1.67 wk, 31.5 %) | fail (1.33 wk, 32.4 %)
-table4/row8 MIFlu | L=48 | fail (1.22 wk, 18.0 %) | PASS (0.67 wk, 24.8 %) | fail (1.22 wk, 30.1 %) | fail (1.33 wk, 33.2 %)
-table4/row9 MIFlu | L=60 | PASS (0.17 wk, 20.5 %) | fail (1.33 wk, 25.8 %) | fail (2.22 wk, 29.8 %) | fail (2.67 wk, 31.2 %)
-table4/row10 PatchTST | L=24 | fail (0.67 wk, 30.6 %) | fail (1.00 wk, 34.0 %) | fail (1.22 wk, 33.6 %) | fail (1.22 wk, 30.7 %)
-table4/row11 PatchTST | L=36 | fail (1.00 wk, 26.2 %) | fail (1.67 wk, 32.2 %) | fail (1.33 wk, 31.2 %) | fail (1.33 wk, 33.9 %)
-table4/row12 PatchTST | L=48 | fail (0.56 wk, 30.4 %) | fail (1.33 wk, 30.9 %) | fail (0.89 wk, 35.2 %) | fail (0.89 wk, 35.0 %)
-table4/row13 PatchTST | L=60 | fail (0.50 wk, 35.0 %) | fail (1.67 wk, 34.3 %) | fail (2.22 wk, 35.7 %) | fail (2.33 wk, 35.1 %)
-table5/row1 量 | 取值
-table5/row2 MSE 对 log₁₀(参数量) 的拟合斜率 | +0.1171
-table5/row3 决定系数 R² | 0.0223
-table5/row4 参与拟合的模型（仅含参数模型） | 11
-table5/row5 帕累托集合（非支配） | NLinear（2,520 参数）· PatchTST（531,878 参数）
-table5/row6 参数量之比 PatchTST / NLinear | 211.1 倍
-table5/row7 PatchTST 相对 NLinear 的 MSE 优势 | 11.2 %
-table5/row8 PatchTST 相对季节朴素基线的改进 | 73.17 %
-table5/row9 28 个模型的 MSE 跨度 | 1.5574（最好）……5.6155（最差），即 3.6 倍
-table5/row10 MSE 与均值 PIE 的 Spearman ρ（28 模型） | +0.736（p < 1e-4）
-table5/row11 MSE 与 K&S 通过数的 Spearman ρ（28 模型） | -0.429（p = 0.023）
-table6/row1 模型 A | 模型 B | n | 平均 Δ MSE | A 胜 | p（Holm） | 效应量 d
-table6/row2 NLinear | PatchTST | 12 | +0.2095 | 2/12 | 0.1172 | 1.15
-table6/row3 Gradient Boosting | RNN | 12 | -1.4029 | 12/12 | 0.06637 | 4.86
-table6/row4 CALF | RNN | 12 | +0.5111 | 0/12 | 0.06637 | 1.65
-table6/row5 CALF | SVR | 12 | +0.2397 | 0/12 | 0.06637 | 1.82
-table6/row6 CALF | TimeCMA | 12 | +2.9704 | 0/12 | 0.06637 | 14.78
-table6/row7 CNN | Decision Tree | 12 | +1.2957 | 0/12 | 0.06637 | 2.69
-table6/row8 CNN | DNN | 12 | +3.4740 | 0/12 | 0.06637 | 6.43
-table7/row1 # | 编码器 | 族 | 规模 | 单元数 | 读出方式
-table7/row2 1 | Qwen2.5-1.5B | Qwen2.5 (dense) | 1.5 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table7/row3 2 | DeepSeek-R1-Distill-Qwen-1.5B | DeepSeek-R1 distill (Qwen2) | 1.5 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table7/row4 3 | DeepSeek-R1-Distill-Qwen-7B | DeepSeek-R1 distill (Qwen2) | 7 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table7/row5 4 | DeepSeek-R1-Distill-Llama-8B | DeepSeek-R1 distill (Llama) | 8 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table7/row6 5 | DeepSeek-R1-Distill-Qwen-14B | DeepSeek-R1 distill (Qwen2) | 14 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table7/row7 6 | DeepSeek-R1-Distill-Qwen-32B | DeepSeek-R1 distill (Qwen2) | 32 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table7/row8 7 | Tencent ContextPilot-8B | Tencent ContextPilot | 8 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table7/row9 8 | Tencent ContextPilot-14B | Tencent ContextPilot | 14 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table7/row10 9 | Tencent Hunyuan-1.8B | Tencent Hunyuan | 1.8 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table7/row11 10 | Tencent Hunyuan-4B | Tencent Hunyuan | 4 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table7/row12 11 | Tencent Hunyuan-7B | Tencent Hunyuan | 7 B | 12 / 12 | 冻结编码器 + 一个 nn.Linear(D, L)
-table7/row13 — | 11 arms | — | — | 132 / 156 | 24 个单元被跳过
-table8/row1 变体 | 开关 | 单元数 | 要回答的问题 | 状态
-table8/row2 full (K=6) | default | — | 参考臂：MIFlu 的基准实例本身（已见基准表）。 | 见基准表
-table8/row3 no_lora | --no-lora | 12 | 精度来自 LoRA 适配，还是来自冻结的主干？ | 未聚合
-table8/row4 K=2 | --num-layers 2 | 12 | 深度阶梯：2 层堆叠是否会损失精度？ | 未聚合
-table8/row5 K=4 | --num-layers 4 | 12 | 深度阶梯：论文区域模型的深度。 | 未聚合
-table8/row6 K=8 | --num-layers 8 | 12 | 深度阶梯：增加深度是否有帮助？ | 未聚合
-table8/row7 K=12 | --num-layers 12 | 12 | 深度阶梯：是否存在容量上限？ | 未聚合
+p0 MIFlu 审计及流感预测精度峰值误差与参数量比较
+p1 CHAN Sing Yeung
香港城市大学电子工程学系毕业设计
+p2 面向 IEEE JBHI 的单栏审阅草稿。当前投稿规则与页数限制仍待核实。贡献定位为实证评估，尚未达到投稿状态。
+p3 摘要
+p4 本文审计 MIFlu 的独立复现及美国全国流感 966 行序列上的 28 个预测实现。复现表平均 MSE 为 1.4995，原文为 1.4355，逐跨度两低两高。三种子基准中，MIFlu、PatchTST、NLinear 分别为 1.5574、1.6621、1.8716。采用文献容差的联合筛选下，NLinear 与 MIFlu 各通过 4/16 聚合单元，PatchTST 为 0/16。NLinear 峰高误差更低，但时间误差高于 MIFlu。11 个有参数导出的模型中，MSE 对对数参数的斜率为 +0.1171，R² 为 0.0223。源 Holm 程序存在错误；修正 17 模型的 136 配对后，没有拒绝，NLinear–PatchTST 的 p 约 0.1172，不能据此证明等价。11 个冻结语言编码器在所测读出配置中均差于决策树。消融仅有用户报告的 27/60 完成，尚未聚合。结论受单次划分、回顾性峰检测及适配实现限制。建议并列报告峰高、时间与平均误差，并在前瞻部署前依验证阶段确定的代价与预算选模。
+p5 I. 引言
+p6 流感预测可支持准备工作，但较低平均误差不能保证峰高与时间准确。本文检查所附 MIFlu 复现 [1] 与更广的项目实现，并不把联合峰值筛选当作临床认证。
+p7 贡献。 （1）审计平均 MSE 差为 +4.5% 的复现比较。（2）统一窗口下的 28 实现排名。（3）比较峰值时间与幅度，前三模型聚合单元通过数为 4/16、4/16、0/16。（4）参数及统计审计揭示较低解释度（R² 0.0223）与错误 Holm 校正。新增指导是验证阶段确定的决策规则，并非已测试的新预测方法。
+p8 II. 相关研究
+p9 分块与线性基线已有研究 [3–5]。Time-LLM、CALF 与 TimeCMA 的对齐及适配设计不同 [6–8]。Chronos、TimesFM、Moirai、Lag-Llama 在数值序列上预训练，本次未评测 [9–12]。较早的 LLM 移除研究已质疑语言预训练收益 [13]，而 2026 年预印本报告跨数据集偏移下的条件性收益 [14]。本项目贡献在于特定流感任务的协议审计与多指标比较。
+p10 时序共形方法 [15–17] 可启发后续区间评测，但不能自动保证回顾性选峰的区间有效。WIS [18] 评价分布或区间，PIE 则衡量点预测峰高，二者必须区分。
+p11 III. 数据
+p12 所附作者格式与 paper-exact 文件均含 966 行及七个对应数值通道，最大绝对数值差为零。原始独立下载文件与固定提交版本未提供。时序划分为 676/97/193，标准化仅拟合训练段，测试目标最早始于第 773 行。作者格式日期为合成标签。
+p13 IV. 方法
+p14 A. 评测协议
+p15 本项目采用时序划分、仅训练段拟合标准化，并用验证集选择检查点。交接资料将测试集选检查点及单变量加载问题归于上游代码，但未提供固定版本作者仓库，公开端点也未能打开，因此上游指控仍未核实。笔记还列出代码默认学习率与原文设置的差异，不能称为仅有两处偏离。
+p16 复现使用种子 2021–2030。基准使用 42/43/44，L24/36/48/60 对应 160/144/144/128 窗口。裁剪沿用本地 drop_last 规则，仍需完整窗口敏感性分析。两个 MIFlu 估计回答不同问题。
+p17 B. 指标
+p18 峰值时间误差 PTE 是预测与观测峰值周的绝对差。峰值强度误差 PIE 为峰高绝对差除以观测峰高后乘百分比。Kramer–Shaman [2] 可核实分别为一周与 25% 的容差。项目把两者联合应用于（模型、L、step）单元的平均误差；该联合筛选及峰检测属于项目选择，不是临床接受标准。平均误差达标不等于逐季成功概率。
+p19 C. 统计分析
+p20 源表有 17 个模型的 136 对，另外 11 个模型不在其中，因此并非 28 模型的全配对分析。Holm 在原始 p 值排序后取前向累计最大值；源代码却取反向累计最小值。n=12 时双侧精确检验下限 2/4096 乘 136 已超过 0.05，因此正确 Holm 校正下该检验族不可能拒绝任何原假设。重复目标及跨度也使单元相关。原始 p 值及未校正 bootstrap 区间只作探索性参考。
+p21 D. 决策规则
+p22 后续验证的决策规则：在查看新测试期之前确定 MSE 预算 B、允许峰值失败率 q 与决策代价。在验证季同时满足 B 与 q 的模型中最小化期望决策代价，再以参数量打破平局。对升级响应 / 等待决策，误报代价为 c_FP，漏报代价为 c_FN，正确行动代价为零；仅当经过验证的高峰概率超过 c_FP/(c_FP+c_FN) 时升级。代价、B、q 尚未征询或验证，因此没有模型被认证可部署。NLinear 是低成本峰高验证候选，MIFlu 仍为观测 MSE 最优。
+p23 V. 实验
+p24 模型名单包括 13 个传统模型、MIFlu 及另外三个基于 LLM 的实现、11 个冻结语言编码器。精度采用七变量标准化 MSE/MAE，峰值误差采用反标准化 ILITOTAL。参数分析为 11 模型，配对检验为 17，冻结特征分析为 11，分母不能混用。本文不将适配实现视为已核实的各参考方法精确复现。
+p25 VI. 结果
+p26 A. 复现
+p27 复现 CSV 的平均 MSE 为 1.4995，对照 1.4355，增加 4.5%。L24、L36 更低，L48、L60 更高。平均 MAE 为 0.8043，对照 0.7452（+7.9%），但逐跨度为一低三高；MAE 没有 MSE 的二比二符号交叉。协议差异与上游来源缺失限制了精确复现的主张。
+p28 表 1. MIFlu 复现与原文对照
+p29 来源：ESSAY_VS_REPRODUCTION_TABLE_V.csv 第 2–6 行。标准差由代码中转录的十种子 oracle 重算；原始运行日志未随包提供。正差表示误差更高。
+p30 B. 基准精度
+p31 表 2. 全部保留模型的精度
+p32 来源：BENCH_MSE_BY_MODEL_L.csv，按 model 和 L 定位。各行由三个种子在 160/144/144/128 个窗口上聚合。项目主动排除了 DLinear，发表前需补充理由与敏感性分析。名称指本项目实现，排名本身不能证明与原论文方法完全等价。
+p33 F0 结论。 MIFlu 的观测 MSE 最低（1.5574），但仅靠 MSE 不能证明公共卫生效用。前三名相对 MIFlu 的跨度为 20.2%，并非小于 20%。
+p34 C. 峰值时间与幅度
+p35 表 3. 峰值时间与强度误差
+p36 均值跨越 16 个（L，step）单元。通过数是在各单元的聚合误差上应用 PTE ≤ 1 周且 PIE ≤ 25%，不是逐季达标率。PIE 衡量点预测的峰高误差，不是概率校准。
+p37 表 4. 各跨度与提前步的联合峰值筛选
+p38 每格为 PTE（周）/ PIE（%）。s0–s3 是预测的第 1–4 周。峰检测使用突出度 0.15 × 极差、间距 15、±8 周匹配。检测设置及联合聚合均为项目选择。来源：BENCH_PTE_PIE_BY_STEP.csv。
+p39 F1 结论。 NLinear 与 MIFlu 各通过 4/16 个聚合单元，PatchTST 为 0/16。NLinear 的平均 PIE 更低（9.477%，MIFlu 为 26.846%），但平均 PTE 更高（1.677 周，MIFlu 为 1.128 周）。这是时间与幅度的取舍，不是全面优越。前三模型的排序在两端倒置：MSE 顺序为 MIFlu、PatchTST、NLinear，PIE 顺序为 NLinear、MIFlu、PatchTST。
+p40 MSE 与 PIE 正相关（ρ=+0.736，p<0.0001），与通过数负相关（ρ=−0.429，p=0.023）。两种符号均符合整体误差较低伴随较好峰值结果的趋势；同时 NLinear 虽 MSE 第三，PIE 却更低。该现象不能证明独立或排序完全反转。
+p41 D. 参数
+p42 表 5. 参数分析与秩相关
+p43 帕累托分析只纳入有参数量导出的 11 个模型，未包括 MIFlu 与冻结编码器。缺失参数量不等于零。参数量不等于延迟、内存或能耗。相关系数只是同一测试集上跨模型的描述性结果。
+p44 F2 结论。 在导出参数量的 11 个模型中，拟合斜率为 +0.1171，R² 为 0.0223。规模单独解释的观测 MSE 变化很少。该子集结果不能证明容量无关紧要。
+p45 E. 统计修正
+p46 表 6. 使用正确 Holm 校正的配对比较
+p47 136 对来自 17 个模型，并未覆盖全部 28 个模型。n = 12 个配对跨度 × 种子单元。前向累计最大值 Holm 得到 0/136 个拒绝。所示 p 值由六位小数导出恢复 1/4096 枚举网格；直接从四舍五入导出重算时，NLinear–PatchTST 为 0.117180，而非 0.1171875。*源效应量采用模型合并标准差，不是配对差的标准差。单元相关性限制统计推断。
+p48 F3 结论。 正确 Holm 校正为 0/136 个拒绝（校正前 128/136），最小校正 p 约 0.0664，NLinear–PatchTST 的 p ≈ 0.1172。PatchTST 的观测 MSE 仍低 11.2%，参数多 211 倍，并在 10/12 单元中误差更低。未拒绝不能证明等价，也不能断言增益是噪声。
+p49 F. 冻结语言编码器
+p50 表 7. 冻结编码器加共享线性读出
+p51 11 个保留编码器 × 4 跨度 × 3 种子 = 132 单元。历史计划还包含两个仅嵌入模型，总计 156 单元；未纳入的 24 单元不属于 28 模型正式名单。此结果只评价该冻结特征流程。
+p52 F4 结论。 所测 11 个冻结编码器的 MSE 为 4.7374–5.2049，是 MIFlu 的 3.04–3.34 倍，全部高于决策树的 4.3198，且均通过 0/16 单元。这是该特征与读出配置的负面结果；提示、微调及数值时序基础模型仍未检验。
+p53 G. 消融设计
+p54 表 8. 消融设计与快照状态
+p55 用户报告截至 2026 年 11 月 3 日：新增 60 单元中完成 27，作业 722968。本次未连接 HPC，也无逐变体结果导出。参考 12 单元不计入新增 60 单元。不推断趋势。
+p56 F5 暂定结论。 miflu_model.py 的 author_faithful 路径将文本置于时间词元之后，使用因果注意力，预测头只读取时间词元。静态检查因此推断确定性评估时文本不影响输出。所附 tests_archive/test_miflu_ablations.py 明确断言文本不变性，以及匹配 CPU 初始化时完整与无文本模型相同。本次仅静态检查，未执行。其他融合路径及训练随机性须分别验证。
+p57 VII. 有效性威胁
+p58 单一全国序列与单次时序划分不能证明区域或前瞻效用。峰值匹配可使用未来观测定义事件，只能作为回顾性评测工具。合成日期标签必须与 CDC 日历核实映射后才能作逐季判断。参数导出缺少 MIFlu 与编码器。27/60 的消融状态来自用户报告，而非实时集群检查。现代数值基础模型、区域结果、滚动原点及经过验证的不确定性仍缺失。
+p59 保留了源 p 值，但未从全部原始配对输入独立重评分。修正 Holm 值恢复枚举网格，并保留与四舍五入导出的来源关系。源效应量采用模型合并标准差，而非配对差标准差。带任意方差下限的种子集成不是已验证的预测分布。前瞻效用、等价界值及经校准的高峰概率均未确立。
+p60 VIII. 结论
+p61 MIFlu 在观测 MSE 排名中领先。NLinear 参数较少、峰高误差较低，但平均峰值时间差于 MIFlu。联合筛选揭示的是取舍，而非通用赢家。正确显著性分析在当前分辨率下没有检验族拒绝。投稿或部署前仍需区域、滚动原点与基础模型对照。
+p62 IX. 参考文献
+p63 [1] Jaeuk Moon 等，基于大语言模型的多模态流感预测方案（中文译名），2025。https://doi.org/10.1109/JBHI.2025.3561214
+p64 [2] Sarah C. Kramer 等，针对温带及热带六十四国的流感预测开发与验证（中文译名），2019。https://doi.org/10.1371/journal.pcbi.1006742
+p65 [3] Yuqi Nie 等，一个时间序列相当于六十四个词的长期预测方法（中文译名），2023。https://arxiv.org/abs/2211.14730
+p66 [4] Ailing Zeng 等，Transformer 是否适用于时间序列预测（中文译名），2023。https://arxiv.org/abs/2205.13504
+p67 [5] Yong Liu et al. 等，反转维度的 Transformer 时间序列预测（中文译名），2024。https://arxiv.org/abs/2310.06625
+p68 [6] Ming Jin et al. 等，通过重编程大语言模型进行时间序列预测（中文译名），2024。https://arxiv.org/abs/2310.01728
+p69 [7] Peiyuan Liu et al. 等，通过跨模态微调对齐语言模型与时间序列（中文译名），2024。https://arxiv.org/abs/2403.07300
+p70 [8] Chenxi Liu et al. 等，通过跨模态对齐增强多变量时间序列预测（中文译名），2025。https://arxiv.org/abs/2406.01638
+p71 [9] Abdul Fatir Ansari et al. 等，学习时间序列语言的 Chronos 方法（中文译名），2024。https://arxiv.org/abs/2403.07815
+p72 [10] Abhimanyu Das 等，仅解码器时间序列预测基础模型（中文译名），2024。https://proceedings.mlr.press/v235/das24c.html
+p73 [11] Gerald Woo et al. 等，通用时间序列预测 Transformer 的统一训练（中文译名），2024。https://proceedings.mlr.press/v235/woo24a.html
+p74 [12] Kashif Rasul et al. 等，面向概率时间序列预测基础模型的 Lag Llama（中文译名），2024。https://arxiv.org/abs/2310.08278
+p75 [13] Mingtian Tan 等，语言模型真的有助于时间序列预测吗（中文译名），2024。https://arxiv.org/abs/2406.16964
+p76 [14] Xin Qiu et al. 等，重新思考大语言模型在时间序列预测中的作用（中文译名），2026。https://arxiv.org/abs/2602.14744
+p77 [15] Chen Xu 等，动态时间序列的共形预测区间（中文译名），2021。https://proceedings.mlr.press/v139/xu21h.html
+p78 [16] Chen Xu 等，时间序列的顺序预测共形推断（中文译名），2023。https://proceedings.mlr.press/v202/xu23r.html
+p79 [17] Isaac Gibbs 等，分布偏移下的自适应共形推断（中文译名），2021。https://arxiv.org/abs/2106.00170
+p80 [18] Johannes Bracher 等，以区间格式评估传染病预测（中文译名），2021。https://doi.org/10.1371/journal.pcbi.1008618
+p82 附录 A 预测曲线
+p83 以下为所附快照的示例曲线。横轴为文件中的测试周下标，未独立核实为 CDC 流行病学日期。图形不能证明因果或前瞻表现。
+p85 miflu，L=24。纵轴为 ILITOTAL 患者人数，横轴为文件测试周下标。黑线为观测，其余为固定预测步 s0–s3。计分窗口 160。此图沿用所附示例，本次未独立重建绘图原始输入。
+p87 patchtst，L=24。纵轴为 ILITOTAL 患者人数，横轴为文件测试周下标。黑线为观测，其余为固定预测步 s0–s3。计分窗口 160。此图沿用所附示例，本次未独立重建绘图原始输入。
+p89 nlinear，L=24。纵轴为 ILITOTAL 患者人数，横轴为文件测试周下标。黑线为观测，其余为固定预测步 s0–s3。计分窗口 160。此图沿用所附示例，本次未独立重建绘图原始输入。
+table1/row1 跨度 | 本文 MSE ± 标准差 | 原文 MSE | Δ MSE | 本文 MAE | 原文 MAE | Δ MAE
+table1/row2 L=24 | 1.3045 ± 0.0883 | 1.5420 | -15.4% | 0.7482 | 0.7260 | +3.1%
+table1/row3 L=36 | 1.3561 ± 0.1603 | 1.4220 | -4.6% | 0.7712 | 0.7790 | -1.0%
+table1/row4 L=48 | 1.6543 ± 0.1064 | 1.4140 | +17.0% | 0.8381 | 0.7570 | +10.7%
+table1/row5 L=60 | 1.6829 ± 0.2109 | 1.3640 | +23.4% | 0.8596 | 0.7190 | +19.6%
+table1/row6 四跨度均值 | 1.4995 | 1.4355 | +4.5% | 0.8043 | 0.7452 | +7.9%
+table2/row1 # | 模型 | L24 | L36 | L48 | L60 | 平均 MSE | 平均 MAE
+table2/row2 1 | MIFlu | 1.3323 | 1.2632 | 1.7774 | 1.8567 | 1.5574 | 0.8199
+table2/row3 2 | PatchTST | 1.4402 | 1.6154 | 1.9288 | 1.6640 | 1.6621 | 0.8786
+table2/row4 3 | NLinear | 1.7971 | 1.7950 | 1.9574 | 1.9368 | 1.8716 | 0.9183
+table2/row5 4 | DNN | 1.8920 | 1.7684 | 2.2603 | 2.6451 | 2.1415 | 1.0057
+table2/row6 5 | TimeCMA | 2.3281 | 2.5794 | 2.7104 | 2.8146 | 2.6081 | 1.0676
+table2/row7 6 | Gradient Boosting | 3.5658 | 3.6867 | 3.6533 | 3.7521 | 3.6645 | 1.2521
+table2/row8 7 | KNN | 3.7231 | 3.7623 | 3.7740 | 3.8820 | 3.7854 | 1.3293
+table2/row9 8 | Random Forest | 3.5486 | 3.8251 | 4.0159 | 4.1710 | 3.8901 | 1.2779
+table2/row10 9 | iTransformer | 3.7656 | 4.0596 | 4.0438 | 4.1088 | 3.9945 | 1.3476
+table2/row11 10 | Decision Tree | 4.5340 | 4.1380 | 4.2186 | 4.3884 | 4.3198 | 1.3798
+table2/row12 11 | Hunyuan-1.8B | 4.5629 | 4.5877 | 4.7111 | 5.0879 | 4.7374 | 1.4755
+table2/row13 12 | Hunyuan-7B | 4.3438 | 4.6624 | 4.9201 | 5.1120 | 4.7596 | 1.4685
+table2/row14 13 | DeepSeek-R1-Qwen-1.5B | 4.6012 | 4.6242 | 4.9245 | 4.9963 | 4.7866 | 1.5002
+table2/row15 14 | DeepSeek-R1-Llama-8B | 4.4337 | 4.7715 | 4.8929 | 5.2019 | 4.8250 | 1.4786
+table2/row16 15 | GRU | 4.2895 | 5.3099 | 5.1751 | 4.7736 | 4.8870 | 1.5174
+table2/row17 16 | DeepSeek-R1-32B | 4.4401 | 4.8565 | 5.0136 | 5.4386 | 4.9372 | 1.4935
+table2/row18 17 | LSTM | 4.4965 | 5.1359 | 5.2088 | 5.1939 | 5.0088 | 1.5303
+table2/row19 18 | DeepSeek-R1-Qwen-14B | 4.4976 | 4.9164 | 5.1687 | 5.4838 | 5.0166 | 1.5019
+table2/row20 19 | DeepSeek-R1-Qwen-7B | 4.5551 | 4.9991 | 5.2417 | 5.3272 | 5.0308 | 1.5133
+table2/row21 20 | RNN | 4.4222 | 5.2893 | 5.3424 | 5.2157 | 5.0674 | 1.5634
+table2/row22 21 | ContextPilot-8B | 4.6094 | 5.1318 | 5.2895 | 5.3065 | 5.0843 | 1.5255
+table2/row23 22 | Hunyuan-4B | 4.7383 | 5.0535 | 5.2876 | 5.4474 | 5.1317 | 1.5450
+table2/row24 23 | ContextPilot-14B | 4.7674 | 5.1566 | 5.2168 | 5.6388 | 5.1949 | 1.5407
+table2/row25 24 | Qwen2.5-1.5B | 4.7840 | 5.0587 | 5.4546 | 5.5224 | 5.2049 | 1.5725
+table2/row26 25 | Qwen-Time | 4.7190 | 5.1325 | 5.6894 | 5.4818 | 5.2557 | 1.5794
+table2/row27 26 | SVR | 5.2248 | 5.3581 | 5.3781 | 5.3940 | 5.3388 | 1.4986
+table2/row28 27 | CALF | 5.3624 | 5.5113 | 5.6442 | 5.7962 | 5.5785 | 1.6190
+table2/row29 28 | CNN | 5.5021 | 5.3098 | 5.2801 | 6.3698 | 5.6155 | 1.6720
+table3/row1 模型 | PTE (wk) | PIE (%) | 联合通过 | s0 PTE | s0 PIE (%)
+table3/row2 MIFlu | 1.128 | 26.846 | 4/16 | 0.347 | 18.884
+table3/row3 PatchTST | 1.240 | 32.755 | 0/16 | 0.681 | 30.553
+table3/row4 NLinear | 1.677 | 9.477 | 4/16 | 0.208 | 3.250
+table4/row1 模型 | L | s0 | s1 | s2 | s3
+table4/row2 NLinear | 24 | PASS 0.111 / 3.949 | fail 1.333 / 8.411 | fail 2.333 / 11.943 | fail 2.667 / 18.739
+table4/row3 NLinear | 36 | PASS 0.333 / 4.181 | fail 1.333 / 7.222 | fail 2.111 / 15.313 | fail 2.667 / 18.145
+table4/row4 NLinear | 48 | PASS 0.222 / 2.419 | fail 1.222 / 4.727 | fail 2.222 / 9.979 | fail 2.778 / 16.655
+table4/row5 NLinear | 60 | PASS 0.167 / 2.450 | fail 1.444 / 4.542 | fail 2.556 / 9.952 | fail 3.333 / 13.000
+table4/row6 MIFlu | 24 | PASS 0.000 / 18.307 | fail 0.889 / 26.686 | fail 1.222 / 30.472 | fail 1.333 / 31.638
+table4/row7 MIFlu | 36 | PASS 0.000 / 18.695 | fail 0.778 / 26.333 | fail 1.667 / 31.514 | fail 1.333 / 32.427
+table4/row8 MIFlu | 48 | fail 1.222 / 18.004 | PASS 0.667 / 24.795 | fail 1.222 / 30.133 | fail 1.333 / 33.236
+table4/row9 MIFlu | 60 | PASS 0.167 / 20.530 | fail 1.333 / 25.799 | fail 2.222 / 29.790 | fail 2.667 / 31.177
+table4/row10 PatchTST | 24 | fail 0.667 / 30.580 | fail 1.000 / 34.044 | fail 1.222 / 33.572 | fail 1.222 / 30.722
+table4/row11 PatchTST | 36 | fail 1.000 / 26.235 | fail 1.667 / 32.247 | fail 1.333 / 31.245 | fail 1.333 / 33.854
+table4/row12 PatchTST | 48 | fail 0.556 / 30.360 | fail 1.333 / 30.878 | fail 0.889 / 35.158 | fail 0.889 / 35.002
+table4/row13 PatchTST | 60 | fail 0.500 / 35.035 | fail 1.667 / 34.342 | fail 2.222 / 35.674 | fail 2.333 / 35.133
+table5/row1 量 | 数值
+table5/row2 回归斜率 / R² | +0.1171 / 0.0223
+table5/row3 有参数量导出的模型 | 11
+table5/row4 子集帕累托集合 | NLinear 2,520; PatchTST 531,878
+table5/row5 参数比 | 211.1×
+table5/row6 描述性 MSE 降幅 | 11.2%
+table5/row7 ρ(MSE, PIE) | +0.736 (p < 0.0001)
+table5/row8 ρ(MSE, 通过数) | -0.429 (p = 0.023)
+table6/row1 模型 A | 模型 B | Δ MSE | p raw | p Holm | 效应*
+table6/row2 NLinear | PatchTST | +0.2095 | 0.005859 | 0.1172 | 1.15
+table6/row3 Gradient Boosting | RNN | -1.4029 | 0.000488 | 0.0664 | 4.86
+table6/row4 KNN | NLinear | +1.9138 | 0.000488 | 0.0664 | 22.29
+table6/row5 KNN | MIFlu | +2.2280 | 0.000488 | 0.0664 | 9.89
+table6/row6 KNN | LSTM | -1.2234 | 0.000488 | 0.0664 | 5.28
+table6/row7 iTransformer | TimeCMA | +1.3863 | 0.000488 | 0.0664 | 7.02
+table6/row8 iTransformer | SVR | -1.3443 | 0.000488 | 0.0664 | 10.61
+table7/row1 编码器 | MSE | 相对 MIFlu | PTE | PIE (%) | 通过
+table7/row2 Hunyuan-1.8B | 4.7374 | 3.04× | 4.406 | 71.428 | 0/16
+table7/row3 Hunyuan-7B | 4.7596 | 3.06× | 5.309 | 75.399 | 0/16
+table7/row4 DeepSeek-R1-Qwen-1.5B | 4.7866 | 3.07× | 5.792 | 78.061 | 0/16
+table7/row5 DeepSeek-R1-Llama-8B | 4.8250 | 3.10× | 4.306 | 77.121 | 0/16
+table7/row6 DeepSeek-R1-32B | 4.9372 | 3.17× | 3.889 | 77.730 | 0/16
+table7/row7 DeepSeek-R1-Qwen-14B | 5.0166 | 3.22× | 4.149 | 76.350 | 0/16
+table7/row8 DeepSeek-R1-Qwen-7B | 5.0308 | 3.23× | 4.458 | 76.373 | 0/16
+table7/row9 ContextPilot-8B | 5.0843 | 3.26× | 4.962 | 78.918 | 0/16
+table7/row10 Hunyuan-4B | 5.1317 | 3.30× | 3.003 | 78.840 | 0/16
+table7/row11 ContextPilot-14B | 5.1949 | 3.34× | 4.965 | 77.764 | 0/16
+table7/row12 Qwen2.5-1.5B | 5.2049 | 3.34× | 5.333 | 74.650 | 0/16
+table8/row1 变体 | 参数 | 单元 | 状态
+table8/row2 参考 K=6 | default | 12 | 已在基准中
+table8/row3 no_lora | --no-lora | 12 | 尚未聚合
+table8/row4 K=2 | --num-layers 2 | 12 | 尚未聚合
+table8/row5 K=4 | --num-layers 4 | 12 | 尚未聚合
+table8/row6 K=8 | --num-layers 8 | 12 | 尚未聚合
+table8/row7 K=12 | --num-layers 12 | 12 | 尚未聚合
```
