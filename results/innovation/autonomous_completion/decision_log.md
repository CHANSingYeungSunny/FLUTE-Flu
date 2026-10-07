# Autonomous completion — decision log

## D1 — do not use `submit_innovation_pilot.sh` as a job (2026-09-15)

**Observation.** The chain driver is itself an `#SBATCH` job with `--gres=gpu:a100:1`.
`HPC_GUIDE.md` §3b/§11 states the `stingy` QOS caps `Jobs=1` **and** `Submit-Job=1`, i.e. a user
cannot have two jobs (running + pending) at once; a second submission is rejected with
`QOSMaxSubmitJobPerUserLimit`.

**Decision.** Do not submit the driver. Submit the four pilots **one at a time from the login
node**, waiting for each to reach a terminal state before submitting the next. This keeps at most
one job in the system and matches the documented queue policy. (The driver remains valid as a
reference implementation of the serial + `afterok` + FAIL-STOP contract, and its behaviour is
covered by `tests/innovation/test_script_safety.py::test_fail_stop_simulation`.)

## D2 — pilots are diagnostics, never results

All four pilots keep `selection_eligible=false`, `paper_result_eligible=false`,
`test_access_allowed=false`. No comparison across pilot validation scores will be produced; only
finiteness, schema, checkpoint save/restore, artifact completeness, metadata agreement and
resource limits are checked.

## D3 — source hash discipline

Every job re-verifies the deployment root at startup. If any file in `scripts/innovation/**` or
`tests/innovation/**` changes, the implementation source version is incremented and the full
snapshot → manifest → specs → bundle → deployment cascade is redone. v2.3 and v2.4 hashes are
never mixed. Autonomous repair cascades remaining: 4.

## D4 — persistent login-node controller is ALLOWED (2026-09-15)

**Question.** Before the first v2.5 Pilot, determine from `HPC_GUIDE.md` whether a persistent
login-node controller is permitted.

**Determination.** `HPC_GUIDE.md` §3b and §11 explicitly endorse a *background auto-submit loop*
on the login node: *"submit the next variant only AFTER the running one finishes (poll `squeue`
… or run a background auto-submit loop)"*. The hard rules (§10/§11) prohibit resource
inflation, **not** login-node polling/submit loops. A login-node controller requests **no GPU**
and never occupies the single `stingy` slot, so it does not conflict with the QOS
(`Jobs=1`/`Submit-Job=1`). **It is therefore allowed.** (The earlier `submit_innovation_pilot.sh`
chain driver that itself carries `#SBATCH --gres=gpu:a100:1` is NOT a valid controller — see D1;
the login-node controller replaces it.)

**Decision.** Implement the controller OUTSIDE the frozen model source. The frozen runtime hash
covers `scripts/innovation/**` and `tests/innovation/**`; the controller lives in
`hpc_scripts/autonomous/` (not in those globs) and is uploaded separately to the isolated
deployment root, so it never changes the snapshot aggregate.

**Design — the 12 hard requirements are mapped as follows:**
1. single-instance lock → `flock -n 9` on `.controller.lock` (`lib.sh acquire_lock`).
2. record job id before polling → `append_ledger(... "PD" ...)` immediately after `sbatch --parsable`.
3. at most one job at a time → `squeue_empty` gate before every `sbatch`.
4. poll terminal state → `poll_terminal` (sacct, 60s × up to 240).
5. validate artifacts before advancing → `state.py validate_run` (status=ok, no test leak,
   source-hash match, stage match, checkpoint manifest present).
6. fail-stop on defect → `fail_stop` on non-zero exit, source/metadata mismatch, test-access
   violation, or missing artifacts.
7. never silently retry → no retry loop anywhere; transient preemption is handled inside the
   worker (`--max-seconds` + checkpoint resume), not by the controller.
8. append-only ledger → `append_ledger_row` / `append_ledger`.
9. resumable without duplicate → `next_pending_job` skips any job whose `KEY=<...>` already has a
   terminal `COMPLETED` row; re-launch just re-reads the ledger and continues.
10. never beyond authorized stage → `stage_within_ceiling` + `authorization_ceiling="K"`; Test (L)
    is excluded from automatic scheduling.
11. heartbeat + `current_state.json` → `heartbeat` writes pid/stage/last_job/utc every loop.
12. copy back durable artifacts → `copy_back` after each COMPLETED job (GPFS home, which has
    backup, unlike scratch).

**Per-stage budgeting.** On entering each new stage the controller computes job_count (from
`state.py generate_stage_jobs`), estimated GPU-hours, free storage, queue compliance, the required
source version, and dependency availability, records it in `budget_ledger.csv`, and **records the
stage as deferred and FAIL-STOPs** if it cannot fit the authorization.

**One-time Test gate.** Stage L is gated: `state.py test_gate_open` returns open only when the
completion matrix has no unresolved mandatory item AND the validation-only freeze audit passes.
Time remaining never triggers Test.

## D5 — three mechanical source repairs cascade v2.5 → v2.8 (2026-09-15)

Each is an ordinary defect within the authorized repair scope (§7): preserve the failed run and
logs, identify the root cause with evidence, bump the implementation source version, rebuild the
snapshot → manifest → specs → deterministic bundle, deploy to a NEW isolated root, verify, then
rerun. Old roots and evidence are preserved; hashes are never mixed.

**v2.6 — generator emitted literal `{{`/`}}`.** `scripts/innovation/hpc_specs.py` builds
`_WORKER` and `_pilot_script` by string CONCATENATION, but the bodies were written with
`.format()`-style escaping. The literal `|| {{ … }}` made `{{` a plain command, so the following
`exit 1` ran unconditionally and every worker would have failed. Fixed to real grouping braces;
the `_HEADER` (genuinely `.format()`-ed) and the f-string driver were left untouched.

**v2.7 — startup governance block was broken and pilot-only.** (a) The block did
`import json, sys` then used `os.environ` → `NameError: name 'os' is not defined`. (b) It
hard-asserted pilot-era flags (`selection_eligible is False`, `experiment_stage == "pilot"`) even
though the SAME worker runs screening/full jobs, and `nlinear` is not a pilot spec — so every
non-pilot job would abort. Fixed: `import json, os, sys`, plus the pilot assertions are now
conditional on `stage == "pilot"` (the worker exports `WORKER_STAGE`; pilot scripts substitute a
literal model/stage).

**v2.8 — `--skip-if-done` was not stage-scoped.** `runner.find_completed_run` matched only
`(model, text_encoder, fusion, horizon, seed)`. Because a Pilot (stage=`pilot`) and a Screening
(stage=`screening`) job share that tuple, the screening job was silently *skipped* (exit 0, no new
artifact), and the controller then saw a `stage_mismatch`. Fixed by also matching
`experiment_stage`, so a pilot run can never satisfy a screening/full job.

## D6 — controller-side + data provisioning repairs (outside the frozen hash) (2026-09-15)

These live in `hpc_scripts/autonomous/**` (NOT in the frozen scope) and therefore required **no**
version cascade:
- run directory resolved by the deterministic run-id PREFIX **and** the expected
  `experiment_stage` (`state.py resolve_run_dir`), because the runner's directory name carries an
  unpredictable UTC-timestamp + git suffix;
- local gate stages (A verify / C readiness / E select / K freeze) are now first-class steps that
  run in order and are recorded in the ledger (previously they were skipped because they emit no
  Slurm job);
- `squeue_empty` counts only numeric job-id lines (some login environments append a
  "Last update …" line that would otherwise deadlock the one-slot wait loop);
- heartbeat clears a prior `STOPPED`, so `current_state.json` never misreports a live controller.

**Dataset provisioning.** `runner.py` needs `data/raw/national_illness_raw.csv` (and the scaler /
predictions under `data/`). Data is intentionally excluded from the frozen bundle, so
`deploy_and_launch.sh` provisions `data/` into every new isolated root (idempotent `scp -r`). The
raw CSV is byte-identical across the local repo, `/gpfs1/scratch/sychan552/MLFLU/data/raw/`, and
the reproduction repo (`sha256 c2b983af…`).

## D7 — morning reconciliation: run overshot the continuation scope; select_best_model defect (2026-09-15)

**Verified state (not the continuation prompt's assumption).** The overnight autonomous run
(under D4's authorization, ceiling `K`) advanced far past Screening: the ledger (276 rows,
**275 unique job ids, 0 duplicates**) records A(1)/B(4)/C(1)/**D(24)**/E(1)/**F(160)**/G(24)/
H(12)/I(24)/J(24) terminal `COMPLETED 0:0`, plus one `CONTROLLER` STOPPED row. The controller
process is gone (`NO_CONTROLLER_PROC`), `squeue` is empty, and there is no second controller.

**Stage D is COMPLETE and audited** (`results/innovation/screening/`): expected 24 cells
(4 backbones × L{24,60} × seeds{42,43,44}); completed 24, failed 0, missing 0, duplicate 0;
metadata chain 24/24; checkpoint-restore 24/24; all runs carry source prefix `ff9e3d8f`;
Test access 0, Test artifacts 0 (`test_evaluations/` absent, no `test_predictions.csv` /
`test_metrics.json`), `frozen_winners.json` absent → **sealed**. Preliminary validation-only
observed rank (3 seeds, absolute val MSE): patchtst 1.0520 < nlinear 1.0750 < dlinear 1.1687 <
itransformer 1.2311.

**Defect (blocks Stage E ranking and Stage K freeze).** `scripts/innovation/select_best_model.py
::build_audit` selects the baseline with the UN-SLUGGED key `"gpt2_miflu"`, but `parse_run_id`
returns the SLUGGED `"gpt2-miflu"`, so `baseline_val_mse_by_L` is all `null`, `candidates` is
empty and `status="no_eligible_candidate"`. This is why controller stage K (champion freeze)
FAIL-STOPped (`LOCAL_STAGE_FAILED: K`): no winner → `write_freeze_audit` passed=False. It is a
pure naming/comparison defect in the SELECTION script; it does not alter any run's training,
artifacts, split, scaler, metrics or early stopping. Fixing it needs a frozen-source change +
cascade and is **submitted for authorization** rather than applied this turn.

**This turn did NOT submit Stage F / ablations / LLM-TSFM / Test** (as constrained). It produced
the Screening audit package (`results/innovation/screening/`, 8 + 3 files) and the Stage F
readiness package (`results/innovation/full_evaluation/readiness/`, 4 files). Stage F is
pre-registered at 160 jobs (4 backbones × L{24,36,48,60} × seeds 42..51); observed per-job wall
time from the D ledger gives an upper bound ≈ 2.72 GPU-hours (~2.72 h serial on `stingy`); pure
training time is tiny (~2.9 s/run).

## D8 — v2.9 selection repair; champion freeze blocked by cross-stage population ambiguity (2026-09-15)

**Repair (authorized).** One canonical normaliser `paths.canonical_model_key()` (underscore
canonical vs slugged run-ID spelling; e.g. `gpt2-miflu` → `gpt2_miflu`) is now used by
`select_best_model.scan_runs` (prefers `run_status.model_key`, else normalises the parsed slug),
so the baseline lookup, candidate grouping and display mapping all agree. Also fixed a latent
Test-isolation hole in the same file: `_TEST_PATH_RE` used `test(evaluations)?`, which never
matched the `test_evaluations` segment; now `test(_evaluations)?`. Added explicit diagnostics
(`baseline_horizon_missing`, `duplicate_cells`, `no_eligible_candidate` reason), a
`--require-winner` diagnostic-failure exit, and a Stage-E `--screening-rank` mode. New tests:
`tests/innovation/test_selection_model_key.py` (10 cases). **No** architecture / split / scaler /
prompt-statistics / metric / threshold / early-stopping / candidate-set / budget change; the
scientific protocol stays `innov-v2.0`.

**Cascade.** `implementation_source_version = innov-v2.9`; snapshot 79 files, aggregate
`8941335bbf58a213d2269f20a72bdb75761d290a017cd937ddc09361175759be`; bundle
`17bf295403478329e16e67f58a0d24ae3004e3f069eee45bbb919db777ff55ca` (byte-deterministic, 104
members, local extract 79/79). Deployed to `/scratch/sychan552/innovation_deploy_root_v2_9`
(explicit-root verify 79/79, exit 0). The v2.8 runs are reused by SYMLINK (non-destructive):
`runs/` and `data/` link to the v2.8 root; `registry_v2.csv` copied. The A–J reconciliation is
exact: **272 Slurm completions, 0 duplicate job ids, Test access 0, Test artifacts 0**.

**Stage E (repaired).** Preliminary validation-only observed Screening rank (24 eligible
screening runs): patchtst 1.0520 < nlinear 1.0750 < dlinear 1.1687 < itransformer 1.2311.

**Stage K — freeze NOT lawful.** The repaired selector produced `status=ok` and a winner
(`nlinear`, primary 1.4804; `patchtst` 1.4746 disqualified because its validation literature-peak
hit ratio 0.130 < baseline 0.167). **However** the controller had assigned
`experiment_stage="full"` to stages F, G, H, I AND J, so the same `(model, horizon, seed)` spec
was run in multiple stages (**36 cross-stage spec overlaps**; e.g. `dlinear` L24/seed42 has 5
eligible runs). The selector's eligible population therefore contains 2–5 runs per mandatory
Full-Evaluation cell, violating the v2.9 precondition **"no duplicate mandatory cells"**. A
lawful champion therefore requires a scientific decision on the champion POPULATION (scope to
the pre-registered Stage-F matrix). The premature `frozen_winners.json` was DELETED (remote and
local) so the Test seal stays lawful; **Test remains sealed**.

## D9 — v2.10 Stage-F provenance cohort + LAWFUL champion freeze (2026-09-15)

**Scientific ruling applied.** The Stage-K champion population is ONLY the pre-registered Stage-F
Full-Evaluation matrix (4 models × L{24,36,48,60} × seeds 42..51 = 160). G/H/I/J are excluded by
provenance, never by performance.

**Provenance reconstruction.** Cohort built from the immutable chain: `stage_plan.json` (F
expansion) → `job_ledger.csv` rows with `stage=F` (job_id, spec, submitted_utc) → Slurm worker log
`[runner] <run_id>` (exact job→run artifact link) → `registry_v2.csv` hashes. Result:
**resolved 160/160, duplicate 0, unresolved 0, 40 cells per model**. The MIFlu baseline is NOT in
the Stage-F matrix, so the manifest carries a separate `baseline_cohort` (12 runs, provenance =
stage H gpt2_miflu). External annotation written to
`results/innovation/governance/stage_provenance/` (annotation + cohort manifest + evidence map +
reconstruction audit); NO historical run artifact or registry row was modified.

**v2.10 repair.** `select_best_model.py` now REQUIRES `--cohort-manifest` (+
`--require-complete-cohort`, `--expect-cohort-sha`): it scans ONLY listed run ids, unions the
manifest's `baseline_cohort`, rejects unlisted `full`-labelled runs, rejects duplicate/missing
cells and manifest tampering, and has NO fallback to scanning all `full` runs. New tests:
`tests/innovation/test_stage_f_cohort.py` (10 cases). Cascade: snapshot 80 files, aggregate
`47a1404c8151539578d596f83742b2a7cc2d74607436a705a303e3c7d0d27fa4`; deployed to
`/scratch/sychan552/innovation_deploy_root_v2_10` (explicit-root verify 80/80); v2.8 runs reused
by symlink (verified targets recorded).

**Stage E (authoritative).** Preliminary validation-only observed Screening rank (24 Stage-D runs):
patchtst 1.0520 < nlinear 1.0750 < dlinear 1.1687 < itransformer 1.2311.

**Stage K (lawful).** With the explicit cohort (`scanned=172 eligible=172 excluded=0`,
`cohort_complete=True`, `resolved_cells=160`, `duplicate_cells=0`), the champion rule selects
**nlinear** (normalized primary 1.47917; patchtst 1.4746 disqualified by the literature-peak
criterion 0.130 < baseline 0.167). Freeze preconditions all pass: missing/duplicate/unresolved = 0,
checkpoint/metadata failures = 0, Test access/artifacts = 0, selection trace contains no Test path.
Artifacts: `frozen_winners.json`, `frozen_model_manifest.json`
(sha256 `558d2e388225bc143e2e48b99b8ae796cab0f18dff3f7a9eacff03f60c7485b5`),
`freeze_audit.json` (passed), cohort manifest sha256
`8695b8ea6151c5dd350411449141e4e547c7bd0aaa263e402695279477e0327d`. The one-time Test readiness
package (`results/innovation/test_readiness/`, default-deny command) was generated; **Test was NOT
accessed or executed**.





