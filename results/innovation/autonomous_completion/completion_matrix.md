# Innovation autonomous completion matrix

Protocol `innov-v2.0` · implementation source `innov-v2.5`.

`all_mandatory_resolved` is `false` until every mandatory item below is `resolved`.
The one-time Test evaluation (stage L) may run **only** when:

1. `all_mandatory_resolved = true`, **and**
2. the validation-only champion `freeze_audit.passed = true`.

It must **never** run merely because time remains. The controller enforces this
gate (`controller.sh` → `state.py test_gate_open`).

| id | mandatory validation item | resolved |
|---|---|---|
| deploy_verify | Isolated deployment root verified against source snapshot (explicit root, 69/69, exit 0) | no |
| pilot_infra | Four v2.5 pilots complete: finite, schema-valid, checkpoint save/restore, artifacts complete, metadata agree, no test leak | no |
| candidate_readiness | Candidate-readiness gate passes | no |
| screening | Screening stage complete and validated | no |
| full_eval | Full evaluation complete and validated | no |
| ablations | Required ablations / robustness analyses complete or explicitly unavailable with evidence | no |
| llm_tsfcrm | Feasible LLM/TSFM handling complete | no |
| robustness | Robustness and resource analysis complete | no |
| auc | AUC-Best-so-far complete | no |
| freeze_audit | Validation-only champion freeze audit passes; proven no Test access during selection | no |

**Test evaluation (`test_evaluation_allowed`)**: currently `false`.
