# Innovation decision

**Recommendation: O1, evaluation first.** A new forecasting mechanism is not needed to state the corrected descriptive findings. It also does not repair the current Holm error, archived test execution errors, single split or missing baseline fidelity. Repair those before adding another hypothesis before 20 November. This recommendation does not say that the present paper is ready for JBHI.

## Targets and risks

| Target | Current desk or scope risk | Risk of a request for a method | Highest-value missing evidence |
|---|---|---|---|
| IEEE JBHI regular | High as a narrow one-series audit with incomplete independent provenance. Current author limits are unverified. Health forecasting is a plausible subject fit. | Moderate; a method is not automatically required, but original insight and health relevance must be strong. | Regional/rolling-origin validation with meaningful event uncertainty and a health decision context. |
| CIKM regular, CCF-B target | High: generality and novelty remain limited, despite evaluation/benchmark topics in the official call. | Moderate to high if the audit remains a single-dataset leaderboard. | A generalisable protocol/selection lesson tested across settings and strong foundation baselines. |
| WSDM regular, CCF-B target | High topic-fit risk for a purely national influenza study without a Web/data-mining connection. Current full-paper deadline is closed. | Secondary to scope fit. | A genuine in-scope research question; do not add a method solely to mimic scope. |
| KDD ADS | Very high without quantified deployment evidence or an officially applicable exception. | Low relative to the deployment requirement. A new loss does not supply deployment. | A real partner/system and measured post-launch performance. |
| Focused four-page short | Potentially defensible after correction, with high selectivity and scope risk; never a safe hit. | Lower for a focused, empirically validated audit, but a strong insight is still required. | One sharply bounded claim with independently reproducible evidence. WSDM/CIKM short does not automatically count as CCF-B regular-paper recognition. |

These are qualitative reviewer-risk assessments, not measured acceptance probabilities. Sources and limits are in LITERATURE_REVIEW.md. Current official JBHI scope details/length could not be fully opened. The KDD ADS call is clear that deployment evidence matters. The CIKM short call explicitly includes evaluation and performance studies.

## Options

| Option | Proposed work | Cost and execution status | Expected effect and limitation |
|---|---|---|---|
| O1 evaluation only | Correct statistics; restore original tests; re-score full windows; detector/season sensitivity; rolling origins and regional results; decomposition of timing versus magnitude; validated decision-cost analysis | No new model proposed. Existing analysis is CPU work; exporting missing validation/rolling-origin predictions may require HPC. Engineering estimate: several working days, not a measured runtime. No A100-hours are invented. | Addresses evidence gaps directly. Cannot claim cross-setting generality until those runs exist. |
| O2 CPU post-hoc mechanism | Candidate chosen for later consideration: validation-season peak-height linear recalibration, with an identity-map control. It changes magnitude but cannot inherently fix peak timing. Reject a test-fitted blend or switch. | Zero GPU training if validation and test predictions exist. This snapshot supplies test exports, not an auditable validation calibration set, so fitting was not attempted. Expected engineering cost: a few working days, an estimate. | May make a prescriptive result but is not intrinsically novel. EnbPI/SPCI/ACI and epidemic ensembles already exist. Compare MSE/MAE/PTE/PIE, joint passes and corrected tests against NLinear/PatchTST. No claimed gain. |
| O3 trained mechanism | Move text to an accessible prefix or use the existing gated injection as a controlled architectural repair, with time-only and shuffled-text controls | Exact new matrix for one repaired arm: 4 horizons × seeds 42/43/44 = 12 cells. Including time-only and shuffled-text controls gives 36 new cells. A100-hours = 36 × measured per-cell hours, currently not measured for this repair. Do a single-cell pilot before a budget commitment. | Tests a causal text hypothesis; it changes the method and requires a new preregistered experiment. It is more expensive and could have no benefit. |

A100-hour estimates cannot responsibly be numerical without per-cell runtime evidence; the exact formula and cells are supplied instead. Cost estimates in working days are planning judgements, not measured results.

## Why O1 now

O1 is accepted by the owner as the default. The school report and presentation carry the immediate deadline. A correct audit is more valuable than a speculative gain added to a defective inference pipeline. Finish statistical/provenance repair and freeze the school deliverables. After that, use O2 only if independently exported validation seasons exist and it answers a clearly prespecified question. O3 is justified only if the text-path hypothesis, rather than cosmetic novelty, becomes the project’s question.

## Exact prescriptive rule for O1

Before opening a new test season, the stakeholder sets an MSE budget B, maximum peak-failure rate q and costs c_FP and c_FN. The cost matrix is: correct escalation and correct wait cost zero; unnecessary escalation costs c_FP; missed surge costs c_FN. These are symbolic, not fabricated clinical prices. Require validated surge probabilities to use the threshold c_FP/(c_FP+c_FN).

Among candidates satisfying B and q on validation seasons, choose the smallest expected validation cost, breaking ties by parameter count. If no candidate qualifies, abstain. Freeze all values and the choice before evaluating the new test season. The present table can suggest candidates, but cannot retrospectively validate this rule or certify a model. No cost, threshold or budget has yet been elicited.

## Minimum defensible units

- **School FYP:** accurate template-compliant report, disclosed audit failures, genuine evidence of the student’s explanation, verified build path and a rehearsed talk. Complete ablation is not necessary if honestly incomplete.
- **JBHI regular:** pinned provenance and restored tests; rolling origins and regions; detector sensitivity and event-level uncertainty; modern numerical foundation controls; clear health relevance with a validated utility question; compliance with current author instructions. O1 may suffice, but no acceptance guarantee follows.
- **CIKM regular:** the above plus a broader, generalisable evaluation contribution or validated selection principle. Merely adding O2 does not guarantee novelty.
- **WSDM:** an authentic scope connection is prerequisite. A technique alone does not cure a topic mismatch.
- **KDD ADS:** deployment evidence or an explicit, justified exception from the official call. An offline audit alone is currently weak.
- **Four-page short:** one audit finding, its reproducible protocol and limitations, not six compressed claims. Verify track recognition separately from conference rank.

Because O1 is recommended, §14’s conditional mechanism code and EXPERIMENT_PLAN.md are not required. No untested “new method” or empty mechanism-results table is added to the manuscript.

## O2 cost shown separately for decision

Chosen optional mechanism: a validation-season linear peak-height recalibration with an identity-map control. It can change peak height, not the peak week. New GPU training cost is **0 A100-hours if auditable validation and test predictions already exist**. They have not been established in this snapshot. CPU wall time and money are **not measured**. Planning estimate: a few working days for input validation, calibration, leakage controls, metric recomputation and reporting; this is an engineering judgement, not a run result. If validation predictions need exporting, owner-side inference costs are additional and must be measured in a pilot.

Do not fit on the current test seasons. Freeze the calibration and comparison family before the next independent test period. Stop if validation origins are too few or non-independent. A useful positive result must improve a prespecified peak-height/decision endpoint without unacceptable MSE or timing loss, with identity-map and NLinear/PatchTST controls. If it fails, report no benefit. O2 remains an option, not the adopted method, and no mechanism code or result is claimed.
