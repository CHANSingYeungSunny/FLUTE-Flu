# English supervisor explanation guide

Reference numbering follows the internal report. Each answer retains its named-paper reasoning and reading locator.

## Q01  Why use 676 training, 97 validation and 193 test rows?

**Answer and local evidence.** The supplied 966-row protocol reserves floor(966 × 0.7) = 676 rows for training and floor(966 × 0.2) = 193 for testing. The remaining 97 form validation. Training fits weights and scaling, validation chooses checkpoints, and the final test block estimates performance after that choice. Chronological order keeps later observations out of earlier training. This is the declared project protocol, not a universal journal requirement. The independently pinned upstream split is still unverified.

**Paper-based reasoning.** Tan et al. explicitly use 70/10/20 for Illness [13, §3.3], while iTransformer preserves chronological separation [5, App. A.1]. These provide a concrete forecasting precedent: retain enough training data, use validation for model selection, and reserve later observations for the final test. The exact 676/97/193 integers come from our 966 rows and rounding rule. The literature supports the design rationale; it does not prove that this ratio is optimal for every influenza season or that our upstream file identity is established.

**Supervisor short answer.** The split follows an Illness precedent in Tan et al.; chronological separation protects the final evaluation [13, 5].

Reading locator: Tan et al. [13], §3.3 Datasets and Evaluation Metrics; iTransformer [5], Appendix A.1.

Local evidence: configs.py DATA_PROFILES[author_repo_966]; BENCH_MSE_BY_MODEL_L.csv; eval_windows.py

## Q02  Why score 160 windows when 170 are available at L24?

**Answer and local evidence.** The local evaluation contract preserves complete batches of 16: (W//16)×16. Thus 170/158/146/134 available windows become 160/144/144/128 scored windows at L24/36/48/60. Using the same retained windows across models prevents a comparison of different test examples. Cropping can nevertheless change scores by removing a particular tail of time. It is a comparability choice inherited by this snapshot, not evidence that cropping is scientifically optimal. Full-window sensitivity remains necessary; a specific discarded-tail difficulty ratio was not independently reverified.

**Paper-based reasoning.** Tan et al. retain original data-loaders and training conditions during their reproduction checks [13, §3.1]. This supports disclosing exactly which examples are scored; it does not require cropping. Our complete-batch rule changes the scoring population. Giving every model the same retained windows removes a comparison unfairness, but deleting the tail can still alter the result. The necessary sensitivity analysis is to score every model on all available windows and compare rankings. A literature citation cannot establish our discarded-tail difficulty without its raw calculation.

**Supervisor short answer.** Cropping preserves a shared scoring population; full-window rescoring tests its effect [13].

Reading locator: Tan et al. [13], §3.1 Reproducibility Note; local eval_windows.py.

Local evidence: BENCH_MSE_BY_MODEL_L.csv; eval_windows.py; scripts/verify_snapshot.py --raw-smoke

## Q03  Why fit scaling on training data only?

**Answer and local evidence.** A mean or standard deviation fitted on the complete series would use information from the future test block. Train-only scaling keeps that information out of model preparation. Each channel is standardised separately. The local equality check compares seven matching numeric columns in the two supplied files and finds maximum absolute difference zero. That verifies numeric equality of these local copies, not byte identity with a newly downloaded author file.

**Paper-based reasoning.** Kapoor and Narayanan identify preprocessing across the training/test boundary as a leakage route [22, L1.2]. Here that means fitting channel means and standard deviations only on training, then reusing them. If future observations determine these constants, preparation has already adapted to the held-out distribution even without using test labels in gradient updates. This makes train-only scaling part of the experiment. The separate local file-equality check establishes matching inputs, not absence of every possible leakage route.

**Supervisor short answer.** Preprocessing is fitted on training only, following the leakage distinction in Kapoor and Narayanan [22].

Reading locator: Kapoor and Narayanan [22], Results, leakage taxonomy L1 and L1.2.

Local evidence: 06_原始数据集/scaler_miflu_author966.json; scripts/verify_snapshot.py

## Q04  Why ten reproduction seeds but three benchmark seeds?

**Answer and local evidence.** They answer different questions. The supplied reproduction uses seeds 2021–2030 to compare with the transcribed paper table. The broader benchmark uses 42/43/44 to compare implementations under one shared protocol. The retained matrix is 28 models × 4 horizons × 3 seeds = 336 cells. Ten seeds would require 1,120 cells. Three reflects the project compute budget; it does not prove adequate power, and additional seeds can improve uncertainty estimation. Neither a universal three-seed venue rule nor zero benefit from more seeds is established.

**Paper-based reasoning.** The original three-seed citation is incorrect. PatchTST uses fixed-seed main results plus a five-seed supervised robustness check [3, App. A.6.1]; iTransformer reports five-run standard deviations [5, App. A.2, Table 5]. Neither passage establishes three seeds as their shared convention. Our choice is a compute compromise. Bouthillier et al. distinguish repeated-run precision from broader benchmark variation [19]. Extra seeds can improve the former; extra seasons/origins address different uncertainty. Ten reproduction repetitions do not make the separate three-seed benchmark equally precise.

**Supervisor short answer.** Three seeds are our compute compromise. Both cited papers provide five-seed robustness evidence, motivating stronger checks [3, 5].

Reading locator: PatchTST [3], Appendix A.6.1; iTransformer [5], Appendix A.2 and Table 5; Bouthillier et al. [19], Appendix C.3.

Local evidence: ESSAY_VS_REPRODUCTION_TABLE_V.csv; BENCH_MSE_BY_MODEL_L.csv; dlv/data.py ORACLE

## Q05  Which implementation differences are established?

**Answer and local evidence.** The local code selects checkpoints on validation and scores all seven standardised channels. Supplied notes attribute test-selected checkpoints and a one-channel loader to upstream code, but no independently inspected pinned author checkout supports that attribution here. Notes also describe differences in learning-rate and epoch settings. Consequently we disclose the local procedure and unresolved reference settings rather than claiming that exactly two repairs explain every score difference. A fair causal comparison would hold data, seeds and all other settings fixed while changing one factor.

**Paper-based reasoning.** A checkpoint is a model-selection choice. Selecting it by test error uses the final evaluation to fit that choice, contrary to clean separation [22, L1]. This justifies our validation-selected checkpoint independently of whether a particular upstream bug can be proved. Scoring all seven declared channels is a separate metric-consistency issue. Neither principle proves Moon et al. committed the alleged defects or that exactly two changes caused our gap. Causal attribution needs matched runs changing checkpoint selection, loader or another factor one at a time.

**Supervisor short answer.** Validation selection protects the held-out test; upstream defect attribution is a separate evidence question [22].

Reading locator: Kapoor and Narayanan [22], taxonomy L1, clean separation through modelling and evaluation.

Local evidence: train_miflu.py; audit/REPO_AUDIT.md; audit/UNVERIFIED_ITEMS.md

## Q06  Why use seven-variable MSE but ILITOTAL peak errors?

**Answer and local evidence.** Seven-variable MSE averages squared errors after each channel has been standardised, so it measures overall dimensionless forecast error. This average loss is not itself a patient-count time series and has no single inverse scaler. Peak timing and height require an actual series. We therefore compute them on ILITOTAL after its own training-fit inverse transform, with mean 9,439.84 and standard deviation 9,003.15 patients. A model can do well across seven channels while having worse ILITOTAL peaks. Different targets and loss functions help explain the different rankings.

**Paper-based reasoning.** Hyndman and Koehler explain why measurement scale matters [21, §2.1]; Kramer and Shaman define peaks on an observed disease series [2]. Our standardised aggregate divides each channel’s squared error in original units by its training variance. The result is a dimensionless loss, not a patient-count curve with one inverse scaler. For peaks, inverse-transform ILITOTAL predictions and observations first, then locate peaks. Taking a peak of the seven-channel loss would answer a different question. Literature motivates an interpretable endpoint; ILITOTAL is our explicit operational choice.

**Supervisor short answer.** Overall standardised error and an interpretable disease peak are different endpoints [21, 2].

Reading locator: Hyndman and Koehler [21], §2.1; Kramer and Shaman [2], Forecast accuracy and comparison.

Local evidence: BENCH_MSE_BY_MODEL_L.csv; BENCH_PTE_PIE_BY_STEP.csv; scaler_miflu_author966.json

## Q07  Why is MIFlu 1.4995 here but 1.5574 in the benchmark?

**Answer and local evidence.** The first is the four-horizon mean from the ten-seed reproduction table. The second is the four-horizon mean under the three benchmark seeds. They summarise separate run sets. Compare 1.4995 with the reported paper mean 1.4355 for reproduction, and compare 1.5574 with other models in the benchmark for model selection. Their difference is not a demonstrated improvement, degradation or transcription error between two otherwise identical experiments. Full run configuration and raw provenance are required to attribute it.

**Paper-based reasoning.** Bouthillier et al. show that benchmark estimates depend on the sampled learning pipeline [19]. A mean is therefore an estimate over specified runs, not an immutable property of a model name. Our two MIFlu estimates summarise separate seed sets and serve different comparisons. The gap could combine seed variability with configuration differences; it does not isolate one cause. Explain each table’s run definition first, then request matched run-level configurations if the cause of the difference matters.

**Supervisor short answer.** They estimate separate run sets; the difference is not a controlled effect of one change [19].

Reading locator: Bouthillier et al. [19], §§2–3, benchmark estimators and sources of variation.

Local evidence: ESSAY_VS_REPRODUCTION_TABLE_V.csv lines 2–6; BENCH_MSE_BY_MODEL_L.csv model=miflu

## Q08  Why do MSE and MAE give different sign patterns?

**Answer and local evidence.** MSE squares errors and gives larger errors more weight. MAE averages absolute errors. Changing a few large errors can therefore alter MSE and MAE differently. Relative to the paper values, MSE is lower at L24/L36 and higher at L48/L60, whereas MAE is lower only at L36 and higher at the other three. The means are +4.5% MSE and +7.9% MAE. Calling both a two-versus-two crossover would misread the table.

**Paper-based reasoning.** The paper distinguishes squared and absolute errors and their sensitivity to large residuals [21]. As an algebraic illustration, not an observed run, doubling a residual doubles its absolute contribution but quadruples its squared contribution. A changed residual distribution can thus move MSE and MAE differently. Our CSV determines the actual horizon signs; the literature explains why different signs are possible. Per-channel and per-window residuals, rather than this general principle alone, are needed to identify the actual errors behind the gap.

**Supervisor short answer.** MSE weights large residuals more strongly than MAE, so the horizon signs must be read separately [21].

Reading locator: Hyndman and Koehler [21], §2.1, MSE/MAE and sensitivity to large residuals.

Local evidence: ESSAY_VS_REPRODUCTION_TABLE_V.csv lines 2–6

## Q09  Do the seed oracle and plots prove a complete reproduction?

**Answer and local evidence.** The oracle is a code-transcribed record of ten seed scores. Its means and standard deviations can be checked arithmetically, but the corresponding raw ten-seed logs and predictions are not supplied for independent rescoring. The imported plots illustrate the benchmark series and are not independent traces of those ten reproduction runs. Checkpoint choice, seed variability and configuration differences are possible explanations for the horizon pattern, not isolated causal findings. The defensible result is a +4.5% mean-MSE gap under disclosed limits.

**Paper-based reasoning.** Repeated-run estimates and traceable evaluation address different weaknesses [19, 22]. The oracle checks the arithmetic of a transcribed record; saved predictions would check whether the pipeline produced it. The practical chain is run configuration → prediction → scoring code → cell → aggregate. A benchmark plot is another summary and cannot establish a ten-seed reproduction trajectory. Missing links limit the claim even when the mean is close. The imported panels remain useful illustrations if their true provenance is stated.

**Supervisor short answer.** The oracle establishes arithmetic; raw outputs establish provenance. Both evidence levels matter [19, 22].

Reading locator: Bouthillier et al. [19], variance analysis; Kapoor and Narayanan [22], model info sheets.

Local evidence: dlv/data.py ORACLE; ESSAY_VS_REPRODUCTION_TABLE_V.csv; figure_captions.json

## Q10  What do the 28 models and different subsets mean?

**Answer and local evidence.** The retained roster is 13 conventional + 4 LLM-based + 11 frozen encoders. Accuracy and peak analysis cover all 28. Parameter exports support 11 arms, while paired tests cover 17 non-encoder models including MIFlu. DLinear is excluded from the retained roster and paired table by project choice. Its appearance in historical provenance does not make it a retained arm. A sensitivity analysis including DLinear would strengthen baseline coverage; prior appearance in the source paper is not by itself a scientific reason to omit it.

**Paper-based reasoning.** The families test different explanations: simple temporal mapping [4], patches and inverted variable tokens [3, 5], and explicit cross-modal alignment [7, 8]. This motivates diverse controls, not a claim that 28 is an optimal count. It also makes implementation fidelity important: a named adaptation may omit a paper’s decisive alignment or training component. DLinear is a relevant simple control in this literature. Its appearance in the source paper is not itself a scientific reason to omit it from a sensitivity analysis.

**Supervisor short answer.** The papers motivate different controls; the exports determine which models each analysis actually covers [3–5, 7, 8].

Reading locator: Zeng et al. [4], §4; PatchTST [3], §3.1; iTransformer [5], §3; CALF [7] and TimeCMA [8], author abstracts.

Local evidence: BENCH_MSE_BY_MODEL_L.csv; BENCH_EFFICIENCY.csv; BENCH_PAIRED_TESTS.csv; BENCH_GPU_PROVENANCE.csv

## Q11  Does the lowest MSE make MIFlu the deployment winner?

**Answer and local evidence.** MIFlu has the lowest observed benchmark MSE, 1.5574. That is a descriptive accuracy result under one national split. It does not measure the cost of missed peaks, false alarms, runtime, regional robustness or prospective benefit. The larger MSE spread also does not establish that hyperparameter tuning is unimportant, because tuning was not experimentally varied as an alternative factor. The later evaluation axes ask additional questions that the accuracy table alone cannot answer.

**Paper-based reasoning.** Peak timing/intensity are disease-specific endpoints [2], while interval scoring evaluates predictive uncertainty [18]. A seven-channel point-error ranking supplies neither automatically. Separate observed accuracy, peak trade-offs and operational cost. NLinear’s lower height error does not erase its worse mean timing; MIFlu’s lowest MSE does not establish calibrated intervals or prospective benefit. This lets us defend an evidence-based selection process before claiming a public-health deployment winner.

**Supervisor short answer.** MIFlu wins the observed point-error ranking; peak endpoints and uncertainty need their own evidence [2, 18].

Reading locator: Kramer and Shaman [2], Forecast accuracy and comparison; Bracher et al. [18], §§3–4.

Local evidence: BENCH_MSE_BY_MODEL_L.csv; audit/GRADE_READINESS.md

## Q12  Why do MIFlu and NLinear both pass 4/16?

**Answer and local evidence.** A pass requires mean PTE ≤ 1 week and mean PIE ≤ 25% in the same (L, step) cell. NLinear passes step 0 at all four horizons. MIFlu passes step 0 at L24/L36/L60 and step 1 at L48. Equal counts therefore hide different locations and error magnitudes. Across all 16 cells, NLinear has lower PIE, 9.477% versus 26.846%, while MIFlu has lower PTE, 1.128 versus 1.677 weeks. The result is a timing–height trade-off, not dominance by either model.

**Paper-based reasoning.** The separate literature endpoints motivate inspecting timing and height before reducing them to a pass count [2]. Our equal four-pass counts hide different lead/horizon locations and distances from the thresholds. An application emphasising one-week-ahead height could favour a different trade-off from an application emphasising timing. That conditional interpretation comes from our table, not from a literature recommendation of NLinear. A binary pass is a coarse summary of continuous errors.

**Supervisor short answer.** Equal counts conceal different cells and a timing–height trade-off [2].

Reading locator: Kramer and Shaman [2], Forecast accuracy and comparison, separate timing/intensity tolerances.

Local evidence: BENCH_PTE_PIE_BY_STEP.csv model in {miflu,nlinear}

## Q13  Does 4/16 mean a 25% chance of a correct epidemic forecast?

**Answer and local evidence.** No. The denominator is four horizons times four fixed forecast steps, not 16 independent seasons. Each cell already averages errors across the available runs/events. Applying thresholds after averaging can give a different answer from counting individual successful events. The separate timing and intensity tolerances are supported by Kramer–Shaman [2]; our conjunction on aggregated cells and detector settings are project choices. They are not a clinical acceptance test or a calibrated probability.

**Paper-based reasoning.** Kramer and Shaman evaluate forecast-level peak accuracy by lead time [2]. Our sixteen configuration cells have a different denominator. Applying a threshold to an average is mathematically different from averaging event-level pass indicators. Thus 4/16 cannot be relabelled as season success probability. Bracher et al. discuss calibration of predictive distributions [18, §4.2]; small peak-height error does not establish it. Estimating event success requires retaining individual outcomes, defining the event denominator and accounting for dependence.

**Supervisor short answer.** Our denominator counts configurations after averaging, not successful seasons or calibrated probabilities [2, 18].

Reading locator: Kramer and Shaman [2], Forecast accuracy and comparison / Fig. 2; Bracher et al. [18], §4.2.

Local evidence: BENCH_PTE_PIE_BY_STEP.csv; Kramer–Shaman [2]; analysis peak detector settings

## Q14  Why can peak rankings differ without proving decoupling?

**Answer and local evidence.** The leading-three MSE order is MIFlu < PatchTST < NLinear; the PIE order is NLinear < MIFlu < PatchTST. Ordering is inverted at both ends, with different middle positions. Across all models, MSE–PIE correlation is positive (+0.736) and MSE–pass-count correlation negative (−0.429), both in the expected direction for generally better error. A local rank mismatch can coexist with those overall associations. We can claim that objectives change the ordering, not statistical independence or universal peak failure.

**Paper-based reasoning.** Zeng et al. describe NLinear’s last-value subtraction, linear map and addition back [4]. This gives a testable hypothesis about level handling, not a proven explanation for our peaks. The ranking mismatch itself follows a simpler distinction: MSE aggregates many points and seven channels, whereas PIE concentrates on detected ILITOTAL peak height [21 gives the error-measure context]. A model can improve many non-peak points yet worsen this endpoint. Controlled variants and peak/residual diagnostics are needed to attribute the observed trade-off to architecture.

**Supervisor short answer.** The objectives aggregate different errors; NLinear’s level correction is a hypothesis to test [4, 21].

Reading locator: Zeng et al. [4], §4 NLinear; Hyndman and Koehler [21], §2.1.

Local evidence: BENCH_MSE_BY_MODEL_L.csv joined to BENCH_PTE_PIE_BY_STEP.csv; audit/verified_facts.json

## Q15  How should I explain the Pareto graph?

**Answer and local evidence.** The horizontal axis is parameter count and the vertical axis is MSE, so smaller values are preferred on both. A model is dominated within the measured subset if another has no more parameters and no higher MSE, with at least one strict improvement. The exported frontier contains NLinear and PatchTST: NLinear is smaller, while PatchTST has lower MSE. Neither dominates the other. This frontier covers only the 11 arms with parameter exports; MIFlu and the encoders are outside it, so a global frontier claim is unsupported.

**Paper-based reasoning.** iTransformer evaluates error alongside speed and memory [5, App. D], a precedent for considering performance with cost. Our cost axis is narrower: exported parameters. The two local frontier members follow from pairwise dominance in the eleven-model subset, not a paper’s recommendation of a universal winner. A Pareto graph removes dominated choices; the remaining choices still need a budget or acceptable-error preference. Missing MIFlu cost data prevents calling it the frontier of all 28 models.

**Supervisor short answer.** The frontier removes dominated choices within the measured subset; a decision preference still chooses among them [5].

Reading locator: iTransformer [5], Appendix D Model Efficiency; local BENCH_EFFICIENCY.csv.

Local evidence: BENCH_EFFICIENCY.csv; fig_pareto_frontier.png

## Q16  Does 211 times more parameters mean 211 times slower?

**Answer and local evidence.** No. 531,878 / 2,520 = 211.1 compares exported PatchTST and NLinear parameter counts. Their observed MSE reduction is (1.871583 − 1.662078) / 1.871583 ≈ 11.2%. Parameter storage, operations, hardware utilisation and batch size affect runtime differently. Latency, peak memory and energy require direct comparable measurements. We use the phrase parameter efficiency, and leave missing parameter counts missing rather than treating them as zero or describing MIFlu as non-parametric.

**Paper-based reasoning.** iTransformer measures speed and memory under stated input/prediction lengths and the same batch size [5, App. D]. Our parameter export does not supply those measurements. Parameters affect storage; operations, token counts and hardware utilisation affect elapsed time differently. Consequently 211× parameters cannot imply 211× latency, memory or energy. A useful next efficiency table records hardware, precision, batch size and whether training or inference is timed. These fields cannot be invented from the parameter ratio.

**Supervisor short answer.** I report a parameter ratio. The literature shows the matched runtime measurements needed for a speed claim [5].

Reading locator: iTransformer [5], Appendix D, Fig. 10, matched speed/memory measurements.

Local evidence: BENCH_EFFICIENCY.csv; BENCH_MSE_BY_MODEL_L.csv model in {nlinear,patchtst}

## Q17  What does R squared of 0.0223 actually mean?

**Answer and local evidence.** For the chosen fit of MSE against log10(parameter count) in 11 exported arms, parameter size alone accounts for little observed variation. This descriptive association does not isolate the effect of capacity: architectures, optimisation and training regimes also vary. A low R squared does not prove that capacity is irrelevant or that an observed accuracy gain is random noise. A causal capacity study would vary size within a controlled family and training protocol.

**Paper-based reasoning.** PatchTST varies layers and hidden dimension and specifically finds ILI sensitive to those settings [3, App. A.6.2]. This is relevant evidence against dismissing tuning on a small influenza series. Our cross-model R² mixes architecture, optimisation and size; it is not a controlled capacity effect. A stronger follow-up varies depth/width within one family under a fixed training protocol and repeats runs. The planned MIFlu depth ladder begins this question, but its unaggregated status provides no scientific trend yet.

**Supervisor short answer.** Low cross-model R² does not dismiss tuning; PatchTST explicitly reports ILI sensitivity [3].

Reading locator: PatchTST [3], Appendix A.6.2, Fig. 5, layers/width and ILI sensitivity.

Local evidence: BENCH_EFFICIENCY.csv; scripts/verify_snapshot.py linregress

## Q18  Why does the paired table contain seemingly unrelated model pairs?

**Answer and local evidence.** The report deliberately shows the NLinear–PatchTST frontier comparison first, followed by six rows with the smallest raw p-values. This combines the question of interest with examples of the wider test family. The frontier pair is 117th by ascending raw p in the exported table, so an automatic smallest-six display would omit it. The full family still contains all 136 comparisons; displayed-row selection never changes the Holm family or makes the selected pair significant.

**Paper-based reasoning.** Demšar motivates controlling the comparison family when inspecting particular differences [20]. Here the first row keeps the substantive frontier question visible; the next six show smaller raw-p contrasts. All 136 still enter the correction. Rank 117 refers to ascending raw p, not a model’s accuracy rank. Choosing display rows cannot change that family. Because the article’s main setting is multiple datasets, it also does not licence treating our overlapping horizons and shared test series as independent datasets.

**Supervisor short answer.** The first row serves the research question; the full family still determines correction [20].

Reading locator: Demšar [20], §3.2.2 Post-hoc tests; local raw-p rank.

Local evidence: BENCH_PAIRED_TESTS.csv model_a=nlinear/model_b=patchtst; audit/verified_facts.json pair_raw_rank

## Q19  Why do 128 raw significant pairs become zero after Holm?

**Answer and local evidence.** Testing many pairs increases the opportunity for false positives. Proper Holm sorts raw p-values and applies a forward cumulative maximum to the ordered multiplicity factors. The original exported column used the wrong direction and is quarantined. Recomputing all 136 gives 0/136 rejections, with minimum adjusted p about 0.0664 and NLinear–PatchTST 0.1172. With the documented two-sided exact n=12 resolution, the smallest possible raw p is 2/4096, already too large for Holm’s first 0.05/136 threshold. Dependence between horizon–seed cells is an additional concern.

**Paper-based reasoning.** Demšar describes starting with the smallest p and stopping at the first failed Holm threshold [20]. Our first threshold is 0.05/136. The documented two-sided twelve-contribution sign-flip floor is 2/2^12; multiplying by 136 gives 0.06640625, so no pair can start the rejection sequence. This floor is local mathematical reasoning, not a result reported by Demšar for influenza. Holm permits dependence among valid p-values, but cannot repair invalid raw p-values from unjustified within-pair exchangeability. These are separate limitations.

**Supervisor short answer.** The exact-test floor exceeds Holm’s first threshold; that is a design-resolution limit [20].

Reading locator: Demšar [20], §3.2.2 Holm step-down; local exact-enumeration derivation.

Local evidence: BENCH_PAIRED_TESTS.csv p_raw; analysis_postprocess.py; audit/HOLM_RECOMPUTATION.csv

## Q20  Does p = 0.1172 show that NLinear and PatchTST are equivalent?

**Answer and local evidence.** No. PatchTST retains 11.2% lower observed mean MSE and lower error in 10/12 matched cells. Non-rejection means this familywise procedure does not establish a difference at the chosen threshold. It does not establish a small enough difference for practical equivalence. Equivalence needs a prespecified acceptable margin and a suitable uncertainty/test design. The table’s source effect also uses pooled model standard deviation rather than paired-difference standard deviation, so it is labelled as a source standardised effect.

**Paper-based reasoning.** Lakens distinguishes a nonsignificant difference test from equivalence with prespecified meaningful bounds [25]. Thus p = 0.1172 does not answer whether NLinear’s observed extra error is acceptable for an application. Define that acceptable difference first, then use an uncertainty design respecting time/season dependence. Choosing a generous bound after seeing this table would not be convincing confirmation. Until then, observed error reduction, parameter ratio and inferential uncertainty should be reported together; the extra parameters cannot be dismissed as buying only noise.

**Supervisor short answer.** Non-rejection is not equivalence; the observed trade-off and unresolved inference coexist [25].

Reading locator: Lakens [25], Introduction and Testing for Equivalence.

Local evidence: BENCH_EFFICIENCY.csv; BENCH_PAIRED_TESTS.csv; audit/CLAIM_AUDIT.md C3

## Q21  What can the frozen-encoder negative result explain?

**Answer and local evidence.** The tested pipeline freezes a language encoder and trains a linear readout. Its 11 encoder arms have MSE 4.7374–5.2049, all above decision tree 4.3198, with 0/16 joint passes each. This shows poor performance of these feature/readout configurations on this protocol. Distribution mismatch, frozen features and readout capacity are possible mechanisms, but the experiment does not separate them. Generation, prompting, fine-tuning and numerically pretrained time-series foundation models remain outside this test.

**Paper-based reasoning.** Time-LLM freezes its LLM but adds learned reprogramming and a prompt prefix [6]. Thus “frozen” alone does not define the same experiment as our feature/linear-readout pipeline. Chronos instead learns forecasting from numerical sequences [9]. These method differences justify keeping our negative finding narrow. To isolate a readout bottleneck, vary the readout/alignment while holding the encoder fixed; to isolate pretraining, compare matched pretrained and random backbones. Our eleven-arm result does not make those controlled separations.

**Supervisor short answer.** The failure concerns our feature/readout pipeline; Time-LLM and Chronos test other mechanisms [6, 9].

Reading locator: Time-LLM [6], author abstract; Chronos [9], §3.

Local evidence: BENCH_MSE_BY_MODEL_L.csv family=llm_encoder; BENCH_PTE_PIE_BY_STEP.csv

## Q22  Why might no-text give identical outputs in the default path?

**Answer and local evidence.** In the inspected author_faithful path, time tokens precede text tokens. Causal attention permits each position to read only its own or earlier positions, and the head reads the time-token positions. Those positions therefore cannot use later text in a deterministic evaluation forward pass. The supplied archive explicitly asserts text invariance and matched-initialisation full/no-text CPU equality, and the supplied JUnit now records those three fixed-weight CPU model assertions passed with zero skips; this review did not rerun them. Other fusion paths, dropout and independently trained trajectories require separate checks. The exact files and commands are in audit/NO_TEXT_VERIFICATION.md.

**Paper-based reasoning.** The Transformer paper explains masking that prevents attention to subsequent positions [24, §3.1]. With the inspected ordering, time positions cannot acquire later text through these layers, and the head reads time positions. This is a structural argument about a fixed forward path, not certification of repository runtime or bitwise equality. The three archived assertions must control weights, inputs and evaluation randomness when comparing changed text and matched full/no-text outputs. The supplied JUnit now records three CPU assertions passed with zero skips; they were not rerun in this review. Independent training can consume randomness differently and requires its own test.

**Supervisor short answer.** Causal masking supports the structural argument; controlled runtime tests must establish bitwise equality here [24].

Reading locator: Vaswani et al. [24], §3.1 Decoder; local ForecastingLLM.forward and archived assertions.

Local evidence: miflu_model.py ForecastingLLM; tests_archive/test_miflu_ablations.py; audit/NO_TEXT_VERIFICATION.md

## Q23  What does 60/60 ablation completion allow us to say?

**Answer and local evidence.** It is queue-completion evidence in the returned 4 November records, not an aggregated model comparison or an independently rerun ablation study. The additional design has five arms, each with four horizons and three seeds: 60 cells beyond the 12-cell reference. Without per-arm result exports, completion is not evidence of a depth trend or a benefit of LoRA. Do not infer a completed no-text ablation from the presence of its test assertions. We need run-level outputs, status and provenance before reporting scientific results.

**Paper-based reasoning.** Tan et al. remove or replace the LLM while retaining the surrounding trainable forecaster [13, §3.2]. This asks whether the backbone contributes beyond the wrapper. Our no-LoRA/depth variants address narrower adaptation/capacity questions; they do not automatically answer the same removal/replacement question or isolate text use. Partial completion is an operational status. Interpreting a scientific trend requires the reported variants’ scores, repeated-run variability and a matched protocol. The literature supplies an experimental question, not a result for our unfinished ladder.

**Supervisor short answer.** The papers motivate removal/replacement controls; the incomplete ladder has not answered those causal questions [13].

Reading locator: Tan et al. [13], §3.2 Proposed Ablations, w/o LLM / LLM2Attn / LLM2Trsf.

Local evidence: Owner snapshot; ablation design table; tests_archive/test_miflu_ablations.py

## Q24  What is added beyond reproduction, and why keep O1?

**Answer and local evidence.** The study compares implementations across accuracy, peak skill, parameter efficiency and statistical evidence, with different declared subsets. We have not verified that the reference paper contains only the first two axes, so absence or first-ever claims are inappropriate. O1 develops this evaluation contribution through provenance repair, restored tests, rolling origins, regions and stronger controls. Optional O2 is validation-only peak-height recalibration: zero new GPU training if auditable validation/test predictions already exist. Such validation exports are not established here; CPU time and money are unmeasured, and a few working days is only a planning estimate.

**Paper-based reasoning.** Simple-linear and LLM-removal critiques predate this project [4, 13]; Qiu et al.’s preprint reports conditional gains in larger cross-dataset settings [14]. Our narrower contribution connects audited influenza accuracy, peak endpoints, a cost subset and corrected inference. O1 checks persistence across origins/regions; Tashman motivates rolling-origin evaluation [23]. O2 adds validation-fitted height adjustment only if suitable prediction exports exist. A new mechanism cannot replace those checks or establish a universal verdict about LLM forecasting.

**Supervisor short answer.** O1 tests the influenza-specific findings; prior negative and conditional-positive evidence rule out a universal conclusion [4, 13, 14].

Reading locator: Zeng et al. [4], §4; Tan et al. [13], §3.2; Qiu et al. [14], abstract and §§3–5 (preprint); Tashman [23], publisher-indexed abstract.

Local evidence: audit/INNOVATION_DECISION.md; audit/LITERATURE_REVIEW.md; sources.json [1]

## Q25  What can a supervisor reproduce now, and what remains unexecuted?

**Answer and local evidence.** The documented CPU commands reproduce CSV headline arithmetic, correct Holm and one raw prediction-cell MSE. Seven new CPU audit checks passed. Whole-archive collection still failed. The supplied JUnit records three fixed-weight CPU no-text assertions passed with zero skips, while returned core artefacts satisfy 160/160 completeness checks. The national 1120 matrix remains in progress. Full common-panel scoring, pinned upstream identity and independent-training text effects remain unresolved; this review did not rerun GPU training or connect to live HPC. Hardware provenance also lacks complete retained-cell coverage. A polished document does not close those gaps. Use the exact follow-up commands in audit/EXECUTION_STATUS.md and audit/NO_TEXT_VERIFICATION.md.

**Paper-based reasoning.** Kapoor and Narayanan ask for explicit reporting arguments rather than equating code availability with a valid result [22]. Here distinguish document rebuilding, CSV arithmetic, raw prediction rescoring and model retraining. A supervisor can begin with the CSV audit; the full bundle supports one raw-cell smoke check. Model text invariance needs the three named runtime assertions without skips in a pinned environment. The useful deliverable is a traceable evidence chain with exact commands and status. Passing one evidence level does not certify all the others.

**Supervisor short answer.** I distinguish recomputed results from static inspection and give the command and status for each [22].

Reading locator: Kapoor and Narayanan [22], model info sheets; EXECUTION_STATUS.md and NO_TEXT_VERIFICATION.md.

Local evidence: audit/EXECUTION_STATUS.md; audit/NO_TEXT_VERIFICATION.md; audit/REPO_AUDIT.md

## References

[1] Jaeuk Moon, Jonghwa Shim, Eunbeen Kim and Eenjun Hwang, “MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme,” IEEE JBHI 29(10), 7790-7801, 2025. https://doi.org/10.1109/JBHI.2025.3561214
[2] Sarah C. Kramer and Jeffrey Shaman, “Development and validation of influenza forecasting for 64 temperate and tropical countries,” PLOS Computational Biology 15(2), e1006742, 2019. https://doi.org/10.1371/journal.pcbi.1006742
[3] Yuqi Nie, Nam H. Nguyen, Phanwadee Sinthong and Jayant Kalagnanam, “A Time Series is Worth 64 Words: Long-term Forecasting with Transformers,” ICLR, 2023. https://arxiv.org/abs/2211.14730
[4] Ailing Zeng, Muxi Chen, Lei Zhang and Qiang Xu, “Are Transformers Effective for Time Series Forecasting?,” AAAI (preprint record opened), 2023. https://arxiv.org/abs/2205.13504
[5] Yong Liu et al., “iTransformer: Inverted Transformers Are Effective for Time Series Forecasting,” ICLR (preprint record opened), 2024. https://arxiv.org/abs/2310.06625
[6] Ming Jin et al., “Time-LLM: Time Series Forecasting by Reprogramming Large Language Models,” ICLR, 2024. https://arxiv.org/abs/2310.01728
[7] Peiyuan Liu et al., “CALF: Aligning LLMs for Time Series Forecasting via Cross-modal Fine-Tuning,” arXiv:2403.07300, 2024. https://arxiv.org/abs/2403.07300
[8] Chenxi Liu et al., “TimeCMA: Towards LLM-Empowered Multivariate Time Series Forecasting via Cross-Modality Alignment,” AAAI, 2025. https://arxiv.org/abs/2406.01638
[9] Abdul Fatir Ansari et al., “Chronos: Learning the Language of Time Series,” Transactions on Machine Learning Research, 2024. https://arxiv.org/abs/2403.07815
[10] Abhimanyu Das, Weihao Kong, Rajat Sen and Yichen Zhou, “A decoder-only foundation model for time-series forecasting,” ICML, PMLR 235, 10148-10167, 2024. https://proceedings.mlr.press/v235/das24c.html
[11] Gerald Woo et al., “Unified Training of Universal Time Series Forecasting Transformers,” ICML, PMLR 235, 53140-53164, 2024. https://proceedings.mlr.press/v235/woo24a.html
[12] Kashif Rasul et al., “Lag-Llama: Towards Foundation Models for Probabilistic Time Series Forecasting,” arXiv:2310.08278, version 3, 2024. https://arxiv.org/abs/2310.08278
[13] Mingtian Tan, Mike A. Merrill, Vinayak Gupta, Tim Althoff and Thomas Hartvigsen, “Are Language Models Actually Useful for Time Series Forecasting?,” NeurIPS 37, 2024. https://arxiv.org/abs/2406.16964
[14] Xin Qiu et al., “Rethinking the Role of LLMs in Time Series Forecasting,” arXiv:2602.14744 v1, preprint, 2026. https://arxiv.org/abs/2602.14744
[15] Chen Xu and Yao Xie, “Conformal prediction interval for dynamic time-series,” ICML, PMLR 139, 11559-11569, 2021. https://proceedings.mlr.press/v139/xu21h.html
[16] Chen Xu and Yao Xie, “Sequential Predictive Conformal Inference for Time Series,” ICML, PMLR 202, 38707-38727, 2023. https://proceedings.mlr.press/v202/xu23r.html
[17] Isaac Gibbs and Emmanuel Candès, “Adaptive Conformal Inference Under Distribution Shift,” NeurIPS 34, 2021. https://arxiv.org/abs/2106.00170
[18] Johannes Bracher, Evan L. Ray, Tilmann Gneiting and Nicholas G. Reich, “Evaluating epidemic forecasts in an interval format,” PLOS Computational Biology 17(2), e1008618, 2021. https://doi.org/10.1371/journal.pcbi.1008618
[19] Xavier Bouthillier et al., “Accounting for Variance in Machine Learning Benchmarks,” Proceedings of Machine Learning and Systems 3, 2021. https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf
[20] Janez Demšar, “Statistical Comparisons of Classifiers over Multiple Data Sets,” Journal of Machine Learning Research 7, 1–30, 2006. https://jmlr.org/papers/volume7/demsar06a/demsar06a.pdf
[21] Rob J. Hyndman and Anne B. Koehler, “Another look at measures of forecast accuracy,” International Journal of Forecasting 22(4), 679–688, 2006. https://doi.org/10.1016/j.ijforecast.2006.03.001
[22] Sayash Kapoor and Arvind Narayanan, “Leakage and the reproducibility crisis in machine-learning-based science,” Patterns 4, article 100804, 2023. https://doi.org/10.1016/j.patter.2023.100804
[23] Leonard J. Tashman, “Out-of-sample tests of forecasting accuracy: an analysis and review,” International Journal of Forecasting 16(4), 437–450, 2000. https://doi.org/10.1016/S0169-2070(00)00065-0
[24] Ashish Vaswani et al., “Attention Is All You Need,” Advances in Neural Information Processing Systems 30, 2017. https://papers.neurips.cc/paper/7181-attention-is-all-you-need.pdf
[25] Daniël Lakens, “Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses,” Social Psychological and Personality Science 8(4), 355–362, 2017. https://doi.org/10.1177/1948550617697177
