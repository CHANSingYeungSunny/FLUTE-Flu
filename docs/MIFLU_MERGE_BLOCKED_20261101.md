# MIFlu → champion tables: merge attempted, NOT applied (2026-11-01)

> Status: **🟡 blocked on data provenance, not on code.** The conversion tool and the
> NaN-tolerant analysis are finished and verified; the MIFlu *row* was deliberately
> **not** written. This note records why, with every number reproducible from the
> commands below.

## 1. What the task asked for

Fetch, for L ∈ {24, 36, 48, 60}:

```
/home/sychan552/stage5_a2_durable/author_runs/L<L>_s2021/predictions_miflu_L<L>_paper_protocol.csv
```

convert them into the `hpc_results/expanded_runs/` cell format, add `miflu` to
`paper_tables/BENCH_*.csv`, and regenerate the figures.

## 2. The HPC was unreachable — three attempts, all hard-timed out

Exact incantation from `AGENTS.md` §4, run three times with `WaitForExit(35 s)` and
20 s between attempts (`_hpc_retry.log`):

```
attempt 1: TIMEOUT(35s) | stdout=''
attempt 2: TIMEOUT(35s) | stdout=''
attempt 3: TIMEOUT(35s) | stdout=''
```

Diagnosis from `ssh -vv`: DNS resolves (144.214.138.99), TCP/22 connects,
**publickey auth succeeds** (`Authenticated to burgundy.hpc.cityu.edu.hk … using
"publickey"`), the exec request is accepted (`exec request accepted on channel 0`) —
and then **no bytes are ever returned**; every session (plain ssh, `-tt`, `sftp`)
hangs until killed. Port 22 is alive, the login shell is not. Not a credential
problem, so retrying did not help.

## 3. What *is* on this disk, and why none of it is the reproduction's export

`ssh` being down does not leave the project without MIFlu predictions — three
different exports exist locally, and **all three pass the protocol-alignment gate**
(same test windows, same `author_966` scaler, ground truth equal to the benchmark
`target[:, 4, :]` to ≤ 1e-6). The blocker is *which run* they came from.

| source | channels | seeds | 7-var z-MSE (L24/36/48/60) | ILITOTAL z-MSE | ILITOTAL z-MAE |
|---|---|---|---|---|---|
| `hpc_results/stage5_a2/scoring/predictions/pred_miflu_L*_s{42,43,44}.npz` | 7 | 3 | 2.4439 / 1.9360 / 1.7677 / 2.0184 | 4.9451 / 3.6583 / 3.2845 / 3.7074 | 1.4522 / 1.2773 / 1.2003 / 1.2166 |
| `results/v3_clean/analysis/peak_criteria/miflu/miflu_strict966__L*__seed{42,43,44}/*.csv` | 7 | 3 | 1.9686 / 1.9332 / 1.7547 / 1.8042 | 4.0132 / 3.6845 / 3.4266 / 3.6836 | 1.2871 / 1.2598 / 1.2331 / 1.2683 |
| `hpc_results/paper_exact/predictions_miflu_L*_paper_protocol.csv` | 1 (ILITOTAL) | 1 | — (not computable) | 4.2173 / 3.4626 / 2.8906 / 3.3995 | 1.3176 / 1.2348 / 1.1472 / 1.1185 |

Cross-check: the `stage5_a2` ILITOTAL column reproduces the stage-5 report table T1
(`hpc_results/stage5_a2/results_tables_zh.md`) to four decimals, and its `miflu`
per-rep 7-var MSEs match that report's T2 exactly — so the provenance of that export
is not in doubt, only its relation to the current reproduction claim.

### The problem

`AGENTS.md` §1.1 — the project's authoritative reproduction result — states MIFlu
7-variable MSE = **1.3045 / 1.3561 / 1.6543 / 1.6829** (4-horizon mean 1.4995,
jobs 714909/715984/717857, 10 reps, seed base 2021). Every local export is **25–87 %
worse** than that at L24:

- `stage5_a2` (3 seeds, 42–44): 2.4439 → **+87 %** vs 1.3045, and 1.42× the paper's
  Table V, i.e. it would put MIFlu **below PatchTST (1.9613)** in the champion table;
- `v3_clean strict966` (3 seeds): 1.9686 → **+51 %**, MIFlu ≈ NLinear (2.0495);
- `paper_exact` (1 rep, August run, `lr=5e-4` per its log): 7-var not even computable.

Whichever export is merged, the champion tables would then contain a MIFlu number that
**contradicts §1.1 in the same paper**: either "MIFlu reproduces Table V within +4.5 %
and beats every baseline" or "MIFlu is mid-table" — not both. That is a scientific
decision about the headline, not a formatting step, so it is escalated rather than
resolved silently. Note also that the task's expected ILITOTAL value (≈2.53, implied by
1.3045 × the 1.9–2.0 ILITOTAL/7-var ratio) is matched by **none** of the three exports
(closest: 2.8906 at L48) — which is itself evidence that the reproduction's own
predictions are not on this disk.

> **Update 2026-11-01 (evaluation-window ruling) — the comparison targets in this
> section moved, the conclusion did not.** Every arm is now scored on the author's own
> `(W//16)*16` test windows, so the numbers quoted above are the pre-ruling ones: the
> current champion table reads PatchTST **1.6621** and NLinear **1.8716** (not 1.9613 /
> 2.0495), and the naive baseline is 5.5768 at L24 (not 5.3175). **Measured on the
> quarantined `stage5_a2` export under the new rule** (`hpc_results/stage5_a2/scoring/predictions/pred_miflu_L*_s{42,43,44}.npz`,
> 3 seeds): L24 **2.4439 → 2.0255** (full-170 / first-160 ratio 1.2175), L36 1.9360 →
> 1.6591 (1.1817), L48 1.7677 → 1.7215 (1.0274), L60 2.0184 → 1.7106 (1.1811) — so the
> old export also moves when the windows are matched, and any comparison of it with the
> 16 arms must be re-derived first. What is unchanged — and what blocked the merge — is
> that **1.3045 is the only number consistent with §1.1**, and the ruling now makes that
> the exact target: MIFlu's merged row must equal the reproduction values to 1e-5,
> asserted by `scripts/verify_miflu_oracle.py`. See `docs/LEDGER.md` (2026-11-01) and
> `docs/AUTHOR_REPO_FIDELITY.md` (the SUPERSEDED note).

## 4. What was delivered instead

| artefact | purpose |
|---|---|
| `scripts/import_miflu_predictions.py` | converts any of the three schemas into a benchmark cell; **refuses to write** unless the windows and ground truth match an existing cell of the same horizon (`--check` verifies without writing) |
| `scripts/analysis_expanded.py` | NaN-tolerant: `mse_7var_z`/`mae_7var_z` are forced to NaN whenever a cell has `< 7` channels, new `n_channels_used` + `partial_export` columns, family/side aggregates NaN-safe, DLinear asserted absent from every table written |
| `scripts/verify_bench_unchanged.py` | proves the 16 pre-existing models are **bit-identical** to `paper_tables/*.pre_miflu.csv` (exact `==`, 1 408 value comparisons) and that DLinear appears nowhere |
| `paper_tables/BENCH_*.pre_miflu.csv` | frozen pre-MIFlu backups of all five tables |

Verified output of the two scripts:

```
$ python scripts/import_miflu_predictions.py --check \
      --csv-pattern "hpc_results/paper_exact/predictions_miflu_L{L}_paper_protocol.csv"
  [ok] max |GT(ch4) - benchmark target| = 5.925e-07   (tol 0.0001)
  [ok] channels filled = 1/7  partial=True
$ python scripts/import_miflu_predictions.py --check \
      --csv-pattern "results/v3_clean/analysis/peak_criteria/miflu/miflu_strict966__L{L}__seed{S}/test_predictions_miflu_strict966__L{L}__seed{S}.csv" \
      --seeds 42 --resolve-seed-from-path
  [ok] max |GT(ch4) - benchmark target| = 9.537e-07
  [ok] channels filled = 7/7  partial=False
$ python scripts/import_miflu_predictions.py --check \
      --npz-dir hpc_results/stage5_a2/scoring/predictions --seeds 42
  [ok] max |GT(ch4) - benchmark target| = 0.000e+00
$ python scripts/verify_bench_unchanged.py
  RESULT: PASS -- all pre-existing numbers are unchanged and DLinear is absent
```

## 5. The one command that finishes the job, once the source is decided

```powershell
# (a) the reproduction export, when the HPC is back (writes 1-channel cells, partial=True)
python scripts/import_miflu_predictions.py `
    --csv-pattern "author_runs/L{L}_s2021/predictions_miflu_L{L}_paper_protocol.csv"
# (b) or an already-aligned 7-variable set, e.g. the A2 stage arm (3 seeds)
python scripts/import_miflu_predictions.py --npz-dir hpc_results/stage5_a2/scoring/predictions `
    --seeds 42 43 44
# then, either way:
python scripts/analysis_expanded.py
python scripts/verify_bench_unchanged.py
python scripts/plot_bench.py
```

## 6. Recommendation

1. First reconcile §1.1 (1.4995) with the stage-5 A2 arm (2.0415) — same data, same
   split, same containment, so the gap is a **training-config difference** and one of
   the two numbers is not describing the same model. Until that is settled, no MIFlu
   row can be defended.
2. Then merge the export produced by *the run that §1.1 describes* (the `author_runs`
   CSVs, `--seeds 2021`), so the champion table and Table V quote the same model.
3. If the merge must happen before the HPC returns, use `--npz-dir
   hpc_results/stage5_a2/scoring/predictions --seeds 42 43 44` and **state in the
   caption** that MIFlu's benchmark row is the 3-seed A2 arm (2.0415), not the
   10-rep reproduction (1.4995).

---

## UPDATE 2026-11-01 19:00 (HKT) — `L24_s2021_pred` CSV is **SUPERSEDED**

`author_runs/L24_s2021_pred/predictions_miflu_L24_paper_protocol.csv` **must not enter
the merge path.** It is retained on disk for the audit trail only.

Chain of evidence (all measured, jobs 719042 + the A100 controller 719030):

1. **The weights are identical.** `md5sum` of
   `ckpt_L24_s2021/_rep_miflu_L24_seed2021.pth` and
   `ckpt_L24_s2021_pred/best_miflu_L24.pth` → both
   `7cad20b30763f65b3b091f00109b02e7`. State-dict bisection: 104 tensors, same keys,
   **104/104 bit-identical**, per-tensor `max|delta| = 0.000000e+00`, identical
   per-tensor sha256.
2. **The new all-7 export is faithful.** It reproduces the logged per-rep
   `test_mse_all` oracle to **<= 4.3e-07** on the matching window subset, for four
   independent seeds (2022-2025).
3. **Therefore the legacy CSV disagrees with the same weights.** Comparing it to the
   new export gave `dGT = 1.776e-15` (alignment perfect) but `dPRED = 1.993`.
   With identical weights and a validated forward pass, the only remaining cause is
   the legacy file's **row set**: it was written on 2026-10-31 by a run that was
   cancelled and restarted four times (logs 18:57, 19:30, 19:45, 19:57), against an
   older `train_miflu.py`.

**Authoritative replacement**: `author_runs/L{L}_all7/predictions_miflu_L{L}_seed{S}.csv`
plus its `.npz` / `results` / `manifest` companions, produced by
`hpc_experiments/export_miflu_all7.py` (forward pass only).

### Related defect: the test loader drops 10 of 170 windows

`train_miflu.train_L` uses `drop_last=True` on the **test** loader, so every reported
test metric covers **160 of the 170** test windows. See the ledger rows in
`docs/LEDGER_APPEND_20261101_miflu.md`. MIFlu must therefore be reported against two
named metrics (`mse_7var_z_author160` for Table V, `mse_7var_z_full170` for the
benchmark axis).

---

## 2026-11-01 (19:45) - The `dPRED=1.99` mystery is SOLVED: a `find_ckpt` trust-order bug, not the legacy CSV

The earlier note in this file concluded from the bit-identical checkpoint comparison that the legacy
`L24_s2021_pred/predictions_miflu_L24_paper_protocol.csv` was the outlier. **That conclusion was
wrong**, and the evidence is in job 719030's own log:

```text
=== L=24 seed=2021 ===
  [legacy] vs training-run ILI export: 19032 rows, max|dGT|=1.776e-15 max|dPRED|=1.993e+00
  [ERROR] L=24 s=2021: AssertionError: ... disagrees with the validated ILI-only export
```

`max|dGT|=1.776e-15` proves the alignment was perfect, so the disagreement was in the *predictions*.
The cause: `export_miflu_all7.find_ckpt` preferred
`ckpt_L{L}_s{seed}/best_miflu_L{L}.pth` over the per-rep file. For seed 2021 that path is the
**best-val rep of the 10-rep reproduction run** - L24/L36 -> seed 2024, L48 -> seed 2021,
L60 -> seed 2025 (read off the run logs: `[CKPT] L=24: kept rep seed=2024`). So the export loaded
sha `a81849e2...` (seed 2024) instead of `43470e5d...` (`_rep_miflu_L24_seed2021.pth`), and the
`dPRED=1.99` is the distance between two *different reps*, not a corrupt legacy file.

The same bug had already corrupted a cell silently: **`manifest_miflu_L36_seed2021.json` records
`ckpt_L36_s2021/best_miflu_L36.pth` (sha `bf05503c...`), which the L36 run log says is
`kept rep seed=2024`** - i.e. the npz on disk labelled seed 2021 holds seed 2024's predictions.
`BENCH_*` never saw it because the row is not merged yet.

### Trust order now enforced (and re-checked per cell)

1. `ckpt_L{L}_s2021/_rep_miflu_L{L}_seed{S}.pth` - the original 10-rep run's per-rep file.
2. `ckpt_best_repro/best_miflu_L{L}.pth` (a safety copy of the original best-val file) - **only when
   `S == BEST_SEED[L]`**, i.e. only for the seed that file actually is.
3. `ckpt_retrain/L{L}_s{S}/best_miflu_L{L}.pth` - a 1-rep retrain this controller wrote.
4. `ckpt_L{L}_s{S}/best_miflu_L{L}.pth` - an earlier fresh run, trusted **only** when its own log
   reproduces that seed's oracle to <= 1e-5.

`ckpt_retrain/` is used for all retrains so the original tree can never be overwritten, and
`author_runs/ckpt_best_repro/` holds the four original best checkpoints (they are the only weights
for L24/L36 seed 2024, L48 seed 2021, L60 seed 2025).

### Evidence that the fix is right

Re-exported with the corrected trust order and checked against the per-seed oracle on the first
`(W//16)*16` windows: **L24 seed 2021 = 1.240157 (|d|=1.51e-07)** - the exact cell that used to fail;
the legacy cross-check now passes instead of asserting. The other export-only cells agree too:
L36 s2024 1.154099 (2.4e-08), L48 s2021 1.482299 (3.7e-07), L60 s2025 1.410785 (3.6e-07).

