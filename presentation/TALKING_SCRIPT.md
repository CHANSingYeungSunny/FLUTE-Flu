# Talking script for a planned five-minute presentation

Re-evaluating Multimodal LLMs for Influenza Forecasting
A 28-Model Benchmark of Accuracy, Peak Skill, Parameter Efficiency and Statistical Evidence

Revision 8: 13 segments total 300 seconds. The spoken script contains 606 whitespace-delimited words; speaking numbers aloud can add words. Actual human delivery is not executed. Rehearse with slide changes against 5:00 ±20 seconds. Chinese guidance and follow-up answers are preparation material outside this pacing budget.

## [0:00–0:15] Slide 1 Re-evaluating Multimodal LLMs for Influenza Forecasting

My project re-evaluates multimodal LLMs for influenza forecasting. I examine MIFlu and compare twenty-eight implementations. The question is how model choice changes when average accuracy, peak errors, model size and statistical evidence are considered together.

## [0:15–0:40] Slide 2 Four evaluation axes ask different questions

I use four evaluation axes. Accuracy measures overall prediction error. Peak skill measures timing and height. Parameter efficiency compares model size with error. Statistical evidence asks what differences the test design can support. Their coverage differs: twenty-eight, twenty-eight, eleven and seventeen models. Those denominators must stay separate.

## [0:40–1:05] Slide 3 Reproduction and benchmarking use separate run sets

The historical reproduction uses ten seeds, while the wider benchmark uses three under shared cropped windows. Its twenty-eight implementations comprise thirteen conventional models, four LLM-based models and eleven frozen encoders. A new ten-seed expansion is underway. I keep its execution status separate from these historical results.

## [1:05–1:35] Slide 4 Reproduction differs by horizon and error measure

The reproduction’s mean MSE is four point five percent higher than the paper table. It is lower at horizons twenty-four and thirty-six, but higher at forty-eight and sixty. MAE is seven point nine percent higher overall, with only one lower horizon. The two error measures need separate explanations, and the causes of the gaps remain unresolved.

## [1:35–2:00] Slide 5 MIFlu leads the observed average-error ranking

MIFlu has the lowest observed mean MSE, about one point five five seven four. PatchTST and NLinear follow in that order, and MAE gives the same leading three. This comparison concerns project implementations on one national split. It does not show that the multimodal component caused MIFlu’s advantage.

## [2:00–2:25] Slide 6 Peak skill separates timing from height

Peak errors use ILITOTAL in patient counts, rather than the seven-channel standardised loss. The joint screen requires timing error within one week and height error within twenty-five percent in the same aggregated cell. MIFlu and NLinear each pass four of sixteen cells. These are horizon–lead combinations, not independent seasons.

## [2:25–2:50] Slide 7 Equal pass counts hide different passing cells

The grid shows different passing locations. NLinear passes the first lead at all four horizons. MIFlu passes three first-lead cells and the second lead at horizon forty-eight. Across all cells, NLinear has lower peak-height error, while MIFlu has better timing. The leading-three ordering is inverted at both ends between MSE and peak-height error.

## [2:50–3:15] Slide 8 The parameter frontier exposes a size–error trade-off

The parameter frontier covers eleven exported arms. NLinear is smaller, while PatchTST has lower MSE. PatchTST uses about two hundred and eleven times as many parameters for eleven point two percent lower observed MSE. The size fit explains only about two percent of observed MSE variation. Parameter count remains a size proxy, with runtime unmeasured.

## [3:15–3:45] Slide 9 Correct Holm supports no familywise rejection

The paired family has seventeen models, including MIFlu. Proper Holm rejects zero of one hundred and thirty-six pairs. The NLinear–PatchTST p-value is zero point one one seven two. Coarse exact-test resolution already blocks the first Holm threshold, and dependent cells add concern. The observed gain remains. Equivalence is unproven.

## [3:45–4:05] Slide 10 Frozen-feature encoders underperform in this protocol

Eleven frozen encoders with a linear readout all perform worse than the decision tree and pass zero joint cells. This is a negative result for the tested feature pipeline. Generation, prompting, fine-tuning and numerical time-series foundation models remain outside this test.

## [4:05–4:25] Slide 11 CPU tests confirm the inspected no-text invariant

The returned CPU log records three no-text assertions passed, with zero skips, under fixed-weight evaluation. This supports the inspected causal-mask explanation. It does not establish training-time text effects. The ablation queue reports sixty of sixty cells done, with per-variant analysis pending.

## [4:25–4:45] Slide 12 The ten-seed expansion remains in progress

Core outputs are complete for one hundred and sixty cells. The national expansion remains unfinished: the package records one hundred and seventeen, followed by an owner report of one hundred and forty-one. Scoring windows still differ. O1 prioritises harmonisation, regional validation and stronger controls.

## [4:45–5:00] Slide 13 Model choice depends on the evaluation objective

The historical results show different choices for average error, peak height and parameter count. The new run must be scored consistently before changing those conclusions. I propose completing that comparison and validating across origins and regions. O1 remains the next supervision decision.

## If interrupted

**At the peak comparison:** Both MIFlu and NLinear pass four cells. The difference is their timing–height trade-off, not a claim of NLinear dominance.

**At the statistical result:** Correct Holm gives no rejection at this resolution. That does not establish equivalence. I will return to the paired design in the questions.

## Delivery check

Not executed: an uninterrupted spoken rehearsal. Record the complete talk including slide changes, measure elapsed time, and adjust pauses before changing any scientific caveat. The slide durations are a budget, not measured speech.
