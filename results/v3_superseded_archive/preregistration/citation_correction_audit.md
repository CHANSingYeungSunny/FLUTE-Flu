# Citation and factual correction audit

Generated 2026-09-15T19:59:40Z.
Scope: **active v3 documents only**. Immutable v2 evidence was not rewritten.

| ID | Subject | Before | After | Severity |
|---|---|---|---|---|
| C1 | Time-LLM venue | ICML 2024 | ICLR 2024 | factual citation error |
| C2 | raw-data latest observation date | raw data extends to 2023-10-06 (inferred from release_date) | release_date is the dataset release stamp, NOT the observation date; the observation axis is epiweek, whose maximum is 202152 (2021 week 52) | material factual error that created a phantom unused interval |
| C3 | LTSF-Linear (NLinear/DLinear) license | MIT (pending live verification) | Apache-2.0 | license misstatement |
| C4 | PatchTST license | MIT (pending live verification) | Apache-2.0 | license misstatement |
| C5 | iTransformer license | MIT (pending live verification) | MIT (confirmed) | confirmation |
| C6 | TimeCMA license | pending live verification | NOASSERTION (Other) - manual review required | blocks unconditional use |

## Evidence

**C1 — Time-LLM venue**
- GitHub API repo description: '[ICLR 2024] Official implementation of "Time-LLM: Time Series Forecasting by Reprogramming Large Language Models"'
- https://proceedings.iclr.cc/paper_files/paper/2024/hash/680b2a8135b9c71278a09cafb605869e-Abstract-Conference.html
- https://mlanthology.org/iclr/2024/jin2024iclr-timellm/
- corrected in: `results/v3/preregistration/candidate_feasibility_matrix.json`, `results/v3/preregistration/candidate_feasibility_matrix.md`, `results/v3/preregistration/architecture_fidelity_matrix.md`, `results/v3/preregistration/dependency_and_license_audit.json`, `results/v3/preregistration/official_source_ledger.json`, `results/v3/preregistration/official_source_ledger.md`

**C2 — raw-data latest observation date**
- release_date has only 8 distinct values over 1025 rows
- epiweek has 1025 distinct values, range 200201..202152
- no row has epiweek > 202152 (count = 0)
- corrected in: `results/v3/preregistration/untouched_holdout_feasibility.json`

**C3 — LTSF-Linear (NLinear/DLinear) license**
- https://api.github.com/repos/cure-lab/LTSF-Linear -> license.spdx_id = Apache-2.0
- corrected in: `results/v3/preregistration/dependency_and_license_audit.json`, `results/v3/preregistration/official_source_ledger.json`

**C4 — PatchTST license**
- https://api.github.com/repos/yuqinie98/PatchTST -> license.spdx_id = Apache-2.0
- corrected in: `results/v3/preregistration/dependency_and_license_audit.json`, `results/v3/preregistration/official_source_ledger.json`

**C5 — iTransformer license**
- https://api.github.com/repos/thuml/iTransformer -> license.spdx_id = MIT
- corrected in: `results/v3/preregistration/dependency_and_license_audit.json`

**C6 — TimeCMA license**
- https://api.github.com/repos/ChenxiLiu-HNU/TimeCMA -> license.key = other, spdx_id = NOASSERTION
- corrected in: `results/v3/preregistration/dependency_and_license_audit.json`, `results/v3/preregistration/model_access_action_items.md`

## Note on C2

The previous turn treated `release_date` as the observation date. It is not: it is the
dataset release stamp and has only 8 distinct values across 1025 rows. The real time
axis is `epiweek` (200201..202152). This error created the appearance of an unused
2022-2023 interval that does not exist in the file.
