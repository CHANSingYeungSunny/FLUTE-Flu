# R1-C — ANTI-ACCURACY-HUNTING DECLARATION

Declared 2026-10-07, **before executing any R1-C fit**.

---

## What is declared

1. **The candidate set is closed at two entries** — the existing R1-B reference
   (C0, no new compute) and one evidence-supported change (C1, the released
   `type1` learning-rate schedule). No candidate may be added after execution.

2. **The candidate was not chosen because it looked promising.** It is the only
   unresolved setting where R1-B differs from a *recovered* released default
   without that difference being a declared repair of a released defect.
   Settings already matched (optimizer, T, epochs, batch, lr, LoRA) offer nothing
   to change. Settings where R1-B repairs a defect (checkpoint rule, pooling
   axes) were excluded **because reverting them would reproduce the defect**.
   Settings with no documentary instantiation (repetition aggregation, seed
   mechanism) were excluded because instantiating them would require inventing
   values.

3. **The success threshold is a criterion, not a target.** 5 % is the bar the
   brief sets. Reaching it is not the goal; determining honestly whether it is
   reachable is.

4. **Test is not used for refinement.** Each fit reads Test exactly once, after
   its checkpoint is frozen. Test is never read during training or selection, and
   the candidate list cannot change in response to a Test result.

5. **Poor candidates will be reported.** If C1 is worse than C0, that is the
   finding and it will be stated as such. No candidate will be dropped from the
   report, and the best-of-N will not be presented as *the* result.

6. **No post-hoc additions.** If C1 fails to reach 5 %, no "one more idea" will
   be introduced. The verdict scale already contains the honest outcomes
   (`NO_EVIDENCE_SUPPORTED_IMPROVEMENT`,
   `NOT_REPRODUCIBLE_WITHIN_5_PERCENT_FROM_RELEASED_ARTIFACTS`).

7. **Search space is bounded by evidence, not by preference.** One candidate, 4
   horizons, 3 seeds, 12 fits, ~1.6 GPU-hours. There is no sweep, no grid, no
   random search, and no early stopping that could stop a weak configuration
   before its Test number is recorded.

8. **The championship is unaffected.** Track C is frozen. Whatever R1-C finds,
   the Track C champion is not revisited, and the R1-C result must not be
   substituted into the championship ranking (different contract, different
   question).

## What would constitute accuracy hunting, and is therefore excluded

- adding a second candidate after seeing C1's result
- adjusting the LR schedule exponent, floor, or the epoch-3 boundary
- trying several checkpoints and reporting the best Test number
- selecting the seed set after seeing which seeds score well
- testing pooling variants until one lands near 1.4355
- widening to optimizers or architectures not named in the released code
- reporting the closest horizon instead of the four-horizon mean

None of the above will be done. If any becomes necessary to reach 5 %, then the
correct verdict is that 5 % is **not reachable from the released artifacts under
evidence-supported settings**, which is a legitimate and useful finding.

## Signed-off state

- candidate matrix frozen: `R1C_FROZEN_CANDIDATE_MATRIX.csv`
- selection rule frozen: `R1C_SELECTION_RULE.md`
- documentary evidence: `R1C_DOCUMENTARY_EVIDENCE.md`
- this declaration published before execution