# Stage F Full Evaluation — authorization request

- selected model keys: dlinear, nlinear, patchtst, itransformer
- exact job count: **160** (models 4 x horizons 4 x seeds 10)
- upper-bound GPU-hours (from observed Screening runtime): **2.72**
- expected wall-clock under stingy (serial): **~2.72 h**
- source version: `innov-v2.5`; root: `/scratch/sychan552/innovation_deploy_root_v2_8`
- Test seal: `test_access_allowed=false`, `frozen_winners.json` absent
- resumable queue-safe mechanism: the existing login-node controller (1 job at a time)

## Note on status

The overnight autonomous run (prior session authorization) ALREADY executed Stage F and stages G/H/I/J, then stopped at local stage K (champion freeze) because of the `select_best_model` baseline-slug defect described in the candidate decision. No Stage F job is submitted by this turn.
