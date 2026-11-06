# STATISTICAL ANALYSIS PLAN

- Estimand: paired difference in forecast loss between two models on the same eligible unit.
- Historical family: 17 non-encoder models, 12 horizon×seed cells, exact two-sided sign-flip,
  Holm forward maximum over 136 pairs. Result: 0/136 survive; 128/136 raw p<0.05; min adjusted
  p ≈ 0.0664; NLinear–PatchTST 0.1172.
- Limitation: n=12 gives a p floor of 2/4096≈0.00049; overlap of horizons/seeds violates independence.
- New Track B plan: declare the dependence unit (season/origin), aggregate within unit, use a
  blocked/hierarchical procedure; report effect sizes and intervals; predeclare primary family.
- Non-significance is not equivalence; ten seeds estimate training variation, not epidemic uncertainty.


## RE-CHECK NOTE (2026-11-04)

The historical 0/136 and p=0.1172 values are OLD-SNAPSHOT facts. The new Track B matrix is incomplete (117/1120) and no new confirmatory family has been declared. Do not force new numbers onto the old Holm result, and do not treat non-significance as equivalence.
