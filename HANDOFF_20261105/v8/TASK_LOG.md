# v8 TASK_LOG — execution of NEXT_DEEPSEEK_PROMPT.md T1–T8

Project root: `C:\Users\Asus\Desktop\FYP code\MLFlu`
HPC: CityU Burgundy, user `sychan552`. All model work ran via `sbatch` on compute
nodes; the login node was used only for `squeue`/`sacct`/`scontrol`/`sinfo`/short
`ls`/`cat`/`date` (AGENTS.md RULE 1). No frozen CSV, raw prediction, checkpoint or
owner-edited PPTX was deleted.

Absolute time base: 2026-11-06, UTC = HKT − 8 h.

---

## T1 — Walk-forward missing 218 cells
status: COMPLETED (finalised 2026-11-06T14:23:47Z; the "IN PROGRESS" line above was stale)
start_utc: 2026-11-06T11:51:38Z (job 743850 LANE_START; inherited from prior turn)
end_utc: 2026-11-06T14:16:04Z (743850 LANE_END) / 2026-11-06T14:23:47Z (recompute verified)
commands:
  - `ssh ... 'squeue/sacct/grep'` (read-only login-node checks)
  - `743850 wf_fix218` — `sbatch wf_fix218_single.sbatch` → `lane.sh 0 1` →
    `master_task_v2.py run --task-id <id> --kind <kind> --model <m> --L <L> --seed <s> --env hpc --require-a100 1`
    for each of the 218 queued legacy task ids, on `stingy` / `gpu-a100-03` / A100-SXM4-80GB.
  - `743920 wf_probe` — `sbatch wf_probe.sbatch` on `tiny`, NPZ schema + MSE formula probe.
  - `744271 t1_wf_recompute_v8` — `sbatch --dependency=afterany:743850 wf_recompute.sbatch`
    (runs `wf_recompute.py` on `tiny` after 743850 ends).
  - `744334 t1_wf_recompute_v8b` — re-run after fixing an int-vs-str key bug in the
    baseline-diff logic of `wf_recompute.py` (the first report wrongly said
    `recovered_218_count=0`). The recompute itself was always correct; only the diff
    compare was wrong.
exit_codes: 743850=0:0 COMPLETED (2:24:27, stingy, gpu-a100-03); 743920=0:0 COMPLETED;
  744271=0:0 COMPLETED; 744334=0:0 COMPLETED
outputs: `HANDOFF_20261105/v8/evidence/{master_queue.tsv,queue_state.tsv,wf_fix218_todo.tsv}` sha256
  c5f6daa255c63f0a1ddbbe3c0bebfbe3fdd9da868c609858b074b8c371f057b7
  c91f2571175bf97fd5e15c1c8306019eb4e7719f3e0e638e6369558e7c57ac47
  9d853bcef7ed1b702a6f32b4312dc262ff28302e1f79ec87e22f3f30b40e0c94
  `v8/scripts/wf_recompute.py` sha256 532203c65c1a67b3fb8cb525639e47d933f0b877c0fbec54e5ed179191c20d98
  frozen baseline copies: `v8/evidence/WF_RECOMPUTED_v7_baseline.csv` sha256
  8eeb6cd709d738bbc93c36e9d36d857ef4312143be8a8cbc13b8f18f846a2f3a and
  `WF_RECOMPUTED_MEANS_v7_baseline.csv` sha256 8e2440a920e85e9912e03f7e8bf49dd08c4a6c80574307ec36595732b38bd0c5
evidence:
  - `final/WF_RECOMPUTED.csv` = 1020 rows, 802 `ok`, 218 `no_npz`.
  - Grouping of the 218: folds f5=72, f4=66, f3=60, f2=20; seeds 42=72, 43=73, 44=73;
    models itransformer 27, lstm 27, rnn 24, qwen_time_llm 23, gru 21, calf_llm/cnn/dnn/
    nlinear/patchtst 15 each, timecma_llm 12, miflu 9.
  - **Exact 1:1 mapping**: `wf_fix218_todo.tsv` (218 ids) == the 218 `no_npz` keys;
    all 218 are `SKIPPED` in `master_queue.tsv` AND `queue_state.tsv`,
    `attempts=2`, `last_job=729729`, note `skipped after 2 failed attempts; last
    branch=hw.cuda-busy reason: CUDA busy/unavailable on this node`,
    `skip.attempts-exhausted`. None are "never queued".
  - **Protocol decision**: ALL 1020 rows (including the 802 valid ones) use legacy
    N=3 seeds 42/43/44 with folds f1–f5. This is the legacy WF panel protocol, distinct
    from the new 28-arm national 10-seed (2021–2030) protocol. Rerunning the 218 with
    the SAME fold/model/L/seed/kind as their queue rows restores that legacy panel; it
    does not invent configurations → **no `protocol-mismatch` among the 218**.
  - 20 further `SKIPPED` rows `wf_f{1..5}_miflu_L{24,36,48,60}_s2021` exist in
    `master_queue.tsv` but are OUTSIDE the 1020 grid (rolling-origin reproduction
    protocol `--reps 10 --seed 2021`, note text). They are recorded as out-of-scope
    and were NOT run and NOT counted.
  - Probe 743920 established the NPZ schema and reproduced the frozen MSE exactly:
    `pred`/`target` shaped `(W,7,L)`, `space=standardized_train_fit_z`,
    `mse = mean((pred-target)^2)`; f1/miflu/L24/s42 = 2.5041660386981155 vs frozen
    2.504166039; f2/nlinear/L24/s42 = 1.5839308390441096 vs frozen 1.583930839.
    Artifact layouts: `<fold>/<model>_L<L>_s<seed>/pred_<model>_L<L>_s<seed>.npz` and
    `<fold>/L<L>_s<seed>/pred_miflu_L<L>_seed<seed>.npz`.
  - Job 743850 progress verified repeatedly; all completed cells `BRANCH=ok.done`,
    `rc=0`, real NPZ written with finite GATE values and window counts.
FINAL RESULT (COMPLETED):
  - 743850 `LANE_END shard=0 processed=218` at 14:16:04Z; **218/218 `END ... rc=0`**,
    zero non-rc0 rows, all `BRANCH=ok.done`, real NPZ written.
  - `744334` recompute from raw NPZ: `grid_cells=1020`, `status_counts={"ok":1020}`.
    Corrected baseline diff: `recovered_218_count=218`,
    `changed_existing_ok_values=0`, `lost_existing_ok=0`, `still_missing=0`.
  - `final/WF_RECOMPUTED.csv` sha256 `53d0e0cb36e726db46c29066101be316bbf9e0de7ea1a228bf84ba7f885ef80b`
    (1020 rows, all `ok`); `final/WF_RECOMPUTED_MEANS.csv` sha256
    `c0e72f35f29d4df32762b9c0a03f69df576405ead495e91a43320dc0774d5813`.
    Frozen v7 baselines preserved in `v8/evidence/WF_RECOMPUTED_v7_baseline.csv` and
    `WF_RECOMPUTED_MEANS_v7_baseline.csv`; detailed NPZ provenance in
    `v8/evidence/WF_RECOMPUTED_DETAIL_v8.csv`; report in
    `v8/evidence/WF_RECOMPUTE_REPORT.json`.
  - 5 folds x 204 cells each. Full-panel per-model means (n=60 each):
    MIFlu 2.220289, PatchTST 3.039638, NLinear 3.211592, DNN 3.648969,
    GradientBoosting 3.915091, TimeCMA 3.924265, RandomForest 3.925170, KNN 3.967265,
    iTransformer 3.977386, CALF 4.391592, SVR 4.412095, DecisionTree 4.514915,
    CNN 4.515521, LSTM 4.655853, GRU 4.742699, RNN 4.785940, Qwen-Time 4.826157.
  - Provenance: this is the LEGACY 5-fold N=3 (seeds 42/43/44) walk-forward panel,
    a DIFFERENT scoring population from the 1120-cell national 28-arm panel.
remaining: none for the cells themselves. `RETURN_V8/final/WF_RECOMPUTED.csv` was
  stale (802/218) until the T8 re-package; the T8 re-run below fixes it.

---

## T2 — Numerical foundation models (Chronos, TimesFM)
status: COMPLETED (80/80 valid cells; documented rolling-origin protocol; finalised 2026-11-06T17:39:16Z — see T2 FULL80 UPDATE)
start_utc: 2026-11-06T13:21:18Z
end_utc: 2026-11-06T13:42:05Z
commands: pinned GitHub/PyPI/HF API verification; `huggingface_hub 2.4.0`
  `snapshot_download(revision=<pinned SHA>, allow_patterns=["config.json","README.md"])`
  probes ×3; `curl` HTTP status checks. rc=0 for all commands.
exit_codes: 0 (all probes). No ssh/sbatch used.
outputs: `v8/foundation/FOUNDATION_MODEL_PROVENANCE.md` sha256 0fd37415117c391297275eeacb48d9b14101941f2bf51b988d6882af4bb0f4b9;
  `v8/foundation/FOUNDATION_ROSTER.csv` sha256 4712fe6a4481e7a92e47296d5afa026f118b04d654951e16a32983f2a1f1c5bc;
  `v8/foundation/T2_VERDICT.md` sha256 7038de7fd5733a2197a31872018256067ae9de4669c6c2d72ef1ff79f8e3197c;
  `v8/evidence/foundation_all_files.sha256` sha256 7d2df0c07a764bd9d0e223fa7bd1aa33720677770954c028d10a82fcdabf1a8d
evidence:
  - Chronos `amazon-science/chronos-forecasting` Apache-2.0, v2.3.2 commit
    `0aba28e9360b6355d5a919596c90b16c25939f02`; `amazon/chronos-t5-small` rev
    `a971ba21945c4f1796b17a91fe69214b5f4ad472`; `amazon/chronos-bolt-base` rev
    `5d9f166d69f47aef3401367a7b842e78fe97b121`; `amazon/chronos-2` rev
    `29ec3766d36d6f73f0696f85560a422f50e8498c` (native multivariate).
  - TimesFM `google-research/timesfm` Apache-2.0 source; `timesfm 3.0.2` PyPI;
    v3.0.0 commit `331c6d33cb1ac2611de3056d0ac7164aab6301eb`;
    `google/timesfm-1.0-200m` rev `8775f7531211ac864b739fe776b0b255c277e2be`;
    `google/timesfm-2.0-500m-pytorch` rev `dc2443792ce5516872b89b37cf1bc058c3bf0c10`.
    `google/timesfm-2.0-500m` (the id in the prompt) is INVALID → HTTP 401.
    `google/timesfm-3.0-pytorch` rev `43046b85ec22d584a13f8098c2ed39c889e129c2`
    under `timesfm-non-commercial-license-v1.0`.
  - Named checkpoints are UNIVARIATE (official Chronos-2 model card: Multivariate ❌);
    T=104 and L=24–60 are within native limits (Chronos T5/Bolt max prediction 64;
    TimesFM 1.0/2.0 any horizon), but 7 channels require a documented per-channel
    adapter that discards cross-channel dependence → not a faithful multivariate control.
  - Pretraining corpora contain NO CDC ILI / influenza labels; Google Trends/Wiki
    pageviews create indirect domain proximity.
  - **BLOCKED because**: probes returned only 10841 / 8554 / 6906 bytes of metadata;
    exact missing inputs are `model.safetensors` (bolt-tiny, t5-small) and
    `checkpoints/checkpoint_1100000/{state/checkpoint,metadata/metadata,descriptor/descriptor.pbtxt}`.
    No tar created, no scp to `/gpfs1/scratch/sychan552/models/`, no isolated
    `/home/sychan552/.venvs/mlflu_fm`, therefore pilot (1×L24×seed2021) and the
    80-cell matrix are `NOT_EXECUTED`. No measured result is claimed.
remaining: download full pinned weights locally → tar + SHA-256 → scp → isolated env
  in sbatch → 1-cell A100 pilot → only then 80 cells under a SEPARATE roster
  (`FOUNDATION_ROSTER.csv`), never merged into the 28-arm family.


### T2 FINAL UPDATE — 2026-11-06 (supersedes the BLOCKED verdict above)
status: COMPLETED_WITH_DOCUMENTED_SCOPE
commands: local Windows `huggingface_hub.snapshot_download(revision=<pinned sha>)` x4;
  `scp` 4 tars to `/gpfs1/scratch/sychan552/models/`; `sbatch t2_env_probe.sbatch` (744533),
  `t2_env_install.sbatch` (744574), `t2_env_finish.sbatch` (744576),
  `t2_pilot.sbatch` (744589), `t2_matrix.sbatch` (744607).
exit_codes: all 0:0 COMPLETED (744533/744574/744576 on `tiny` cpunode-034;
  744589/744607 on `stingy` gpu-a100-05, A100-SXM4-80GB).
outputs + sha256: 4 tars total 5,024,901,120 B —
  `chronos_bolt_tiny.tar` 34,652,160 `f28b41b19e9348c9a4a733eb208595b577509667035ca7a8c55e38a304b81c18`
  `chronos_t5_small.tar` 184,893,440 `d6df552e68fc0f2fbad20141d8b852870af76580d51c89508b2a221021f2da16`
  `timesfm_1_0_200m.tar` 814,376,960 `963d6d6adf8d91c8d8f0a7362eed981bcd147d6d766e7980622141fdd0ebeb13`
  `timesfm_2_0_500m_pytorch.tar` 3,990,978,560 `7fef382ad503bb8489966729250e790ac78bf9cc4b9966a32d6769667ab90363`
  ALL FOUR remote SHA-256 verified inside 744607 to match exactly; LFS oids
  `75068728…` (chronos safetensors) and `a3a1362c…` (timesfm torch_model.ckpt) also match.
  Evidence/docs: `v8/foundation/{T2_DOWNLOAD_RESULT.md,T2_PILOT_AND_MATRIX.md,T2_EVIDENCE_HASHES.txt,FOUNDATION_ROSTER.csv}`;
  8 prediction NPZ + all HPC logs under `v8/foundation/t2_hpc_evidence/`.
evidence:
  - Isolated env `/home/sychan552/.venvs/mlflu_fm`: Python 3.11.13, torch 2.6.0+cu124,
    chronos-forecasting 2.3.2, timesfm 1.3.0, pandas 2.3.3, transformers 5.22.1.
  - Pilot 744589: `PILOT_STATUS COMPLETED`, all_finite=true, MSE 0.391328494,
    MAE 0.383546002, load 0.4794 s, latency 10.191 +/- 0.446 ms (warm-up 1 / repeat 5),
    peak VRAM 596 MiB (28 samples), wall 27.35 s.
  - Matrix 744607: **8/8 cells `ok`, all finite**, 8 real NPZ, peak VRAM 2608 MiB (18 samples),
    wall 18.00 s. MSE_7var_z (L=24/36/48/60): foundation_chronos
    0.391328494 / 2.207397404 / 1.713535818 / 1.400230721; foundation_timesfm
    0.729752533 / 2.654955324 / 2.031110049 / 1.662973370.
  - Adapter limits recorded: both checkpoints UNIVARIATE; 7 channels passed as a batch of
    7 independent series (per-channel independent), DISCARDING cross-channel dependence,
    NOT information-set-matched; each model applies its own internal scaling; zero-shot,
    no training/fine-tuning. Separate roster `foundation_chronos` / `foundation_timesfm`,
    never merged into the 28-arm family.
  - Honesty caveat: TimesFM `wall_s=0.0` and 0.004/2.483/4.489/6.492 ms are loop/slicing
    timings of ONE shared `tfm.forecast` call, not four forward latencies; Chronos L24
    221.835 ms includes one-time CUDA init.
remaining: the requested `2 models x 4 L x 10 seeds = 80` expansion is
  **NOT_EXECUTED_BY_PROTOCOL** — frozen zero-shot models have NO training seed dimension,
  so 10 seeds would produce 10 identical predictions; the smallest faithful subset (8 cells)
  was run instead. Also not done: multivariate-native checkpoints, full-1120 comparison,
  z-space de-standardisation, and the two unexecuted checkpoints in FOUNDATION_ROSTER.csv.

---

## T3 — Legacy `final_llm_import`
status: COMPLETED (388/388 NPZ readable; the 2 quarantined cells were RESTORED — see T3 RESTORE UPDATE)
start_utc: 2026-11-06T13:16:21Z
end_utc: 2026-11-06T13:20:06Z
commands:
  - queue row: `master_queue.tsv:729 final_llm_import f5_llm_import - - - P4 hpc TODO 0 - re-armed for writer: cell signature changed`;
    `queue_state.tsv:2 final_llm_import TODO 0 0 - - sched.no-window 2026-11-03 11:20:38`.
  - handler `master_task_v2.py:944` `FINALISE_STEPS["final_llm_import"]` =
    `scripts/analysis_expanded.py`, `scripts/plot_bench.py`, `scripts/plot_pareto.py`;
    dispatch via `KIND_TO_ID["f5_llm_import"]="final_llm_import"` (line 958).
  - `744110 t3_llm_import_v8` (tiny): `QUEUE_FORCE_FINALISE=1 master_task_v2.py run
    --task-id final_llm_import --kind f5_llm_import --model - --L - --seed - --env hpc
    --require-a100 0` → rc=2, `BRANCH=d.no-table`, no table.
  - `744134 t3b_llm_import_v8` (tiny): same command after quarantining unreadable NPZ.
exit_codes: 744110=2; 744134=0:0 (COMPLETED, `ok: true`, all 3 steps rc=0).
outputs: `paper_tables/BENCH_MSE_BY_MODEL_L.csv` sha256 2e03b5109db03cfd4e1b9e89bd8e6069468fd4f7cd3671b367f7f632a0b6be29;
  `BENCH_PTE_PIE_BY_STEP.csv` sha256 32307527610db542c0382adc8f3d09c9bd8052b103db90590063d6bf7d2d2890;
  `BENCH_EFFICIENCY.csv` sha256 dfd1ff3524837b205f24ae65ab1083022e62989a9bbe2f5bf25dab8e220c63a7.
  Backup: `/gpfs1/home/sychan552/stage5_a2_durable/analysis/paper_tables.bak_T3_20261106T131621Z`
  (created BEFORE the run; hash diff recorded). Quarantine:
  `code/queue/finalise/T3_v8/quarantine_20261106T131834Z/QUARANTINE.json`.
evidence:
  - First run exact error: `EOFError: No data left in file` at `analysis_expanded.py:108`
    and `plot_bench.py:60`; `failures=['analysis_expanded.py rc=1','plot_bench.py rc=1']`,
    `proof_mtime_before == proof_mtime_after` (no table).
  - Scan of all 388 `pred_*.npz`: 386 readable, 2 unreadable —
    `expanded_runs/miflu_L36_s2021/pred_miflu_L36_s2021.npz` 0 B `EOFError`
    (sha256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855);
    `expanded_runs/miflu_L60_s2021/pred_miflu_L60_s2021.npz` 30977 B
    `BadZipFile: File is not a zip file`
    (sha256 965ff7b8001e6b5f4c0057044248431c869b930a9eb705a7b6fd672302c4d1b4).
    Both MOVED (archived, not deleted) into the quarantine dir with provenance.
  - Retry: `analysis_expanded.py rc=0 (1.6s)`, `plot_bench.py rc=0 (85.3s)`,
    `plot_pareto.py rc=0 (1.5s)`; `proof_mtime_before=1793632895.724701` →
    `proof_mtime_after=1793971118.806612`; `gate=n_cells=386;n_arms=17`.
    A real `BENCH_MSE_BY_MODEL_L.csv` was written (header + rows verified).
remaining: the rebuilt legacy table reflects 386 readable cells, not 388; the two
  corrupt legacy MIFlu NPZs remain quarantined and must be regenerated or explicitly
  excluded before any claim based on that legacy analysis tree. No table was faked.

---

## T4 — CDC calendar / vintage
status: COMPLETED (corrected 2026-11-06; earlier `PARTIAL / BLOCKED` verdict was erroneous — see note below)
start_utc: 2026-11-06T13:19:57Z
end_utc: 2026-11-06T13:33:59Z
correction_utc: 2026-11-06
commands: 16 exact URLs checked (CDC official pages, CDC EPI GitHub Pages, Delphi
  Epidata API, Wayback CDX, Software Heritage, GitHub mirrors); three live
  `https://api.delphi.cmu.edu/epidata/fluview/?...` fetches, all HTTP 200,
  `result:1`, exit 0. (ORIGINAL verification work; commands/exit codes/hashes retained
  verbatim in `v8/cdc_vintage/T4_VERDICT.md` §B/§C.)
exit_codes: 0 for all fetches.
outputs (FROZEN, read + hash-verified 2026-11-06; NOT modified):
  `02_数字表格/cdc_vintage_raw.csv` (7192 data rows) sha256 e0c5512b2b6889780f345927708fee3ac3006ff59d78881dc6b55fa31fc7e9c8;
  `02_数字表格/cdc_vintage.csv` (848 data rows) sha256 5a49e6be748aed251e82084a2b83d8c2f92ca23ef72ef8f442b10481c611b2c9;
  `02_数字表格/cdc_vintage_report.md` sha256 e2da6b377abc318a311535cd593180d5ea62cd11ee03c31c3ee3fb2e67afd2d7;
  `02_数字表格/cdc_peak_revintage.csv` sha256 7c9b5df808a1f78cb2e097aec114b3a735b075f6c2a991c24ae3db3883d7a504;
  `05_程序代码/cdc_vintage_build.py` sha256 8c1e4b1e31a4339e8d30d6c8f9e62fc181996d47fcea1cb9a5f2d2bceb2a079f;
  `v8/cdc_vintage/T4_CORRECTION.md` + corrected `T4_VERDICT.md` / `CDC_VINTAGE_REPORT.md`;
  the 20-row `v8/cdc_vintage/cdc_vintage.csv` (sha256 ffc960e5…) is a VERIFICATION SAMPLE
  ONLY, NOT a replacement for the frozen 7192-row table.
evidence:
  - **ERROR CORRECTION:** the earlier `PARTIAL` / `BLOCKED: no release-calendar/vintage
    source found` / peak-re-scoring `BLOCKED` verdict was ERRONEOUS. It fetched only 20
    sample rows from the Delphi Epidata `fluview` endpoint and FAILED to inspect
    `02_数字表格/`, which ALREADY contained a complete CDC ILINet vintage reconstruction
    built by `05_程序代码/cdc_vintage_build.py` from that SAME Delphi endpoint. The
    project owner caught the error; the old verdict is SUPERSEDED (`T4_CORRECTION.md`).
  - 1025 panel epiweeks; **848** with weekly release records; 177 without; **7192**
    `(epiweek, issue)` rows with lag<=8; **836/848** revised (98.6%); |ILITOTAL revision|
    p10 5.2% / median 21.8% / p90 51.8%.
  - Season-peak FINAL vs AS-OF: **18 seasons scored, 7 peak weeks move = 38.9%**
    (`cdc_peak_revintage.csv`). Peak re-scoring of the REFERENCE assignment is COMPLETE.
  - Archived `06_原始数据集/raw/national_illness_raw.csv` has only 8 distinct annual bulk
    snapshot `release_date` values and is NOT a vintage.
  - Delphi URL/status evidence (16 URLs, HTTP 200 except an attempted 404) retained as
    provenance in `v8/cdc_vintage/CDC_VINTAGE_REPORT.md` §2–§3 / `http_evidence/`.
remaining (scientific limits, NOT blockers): Delphi `release_date` is a Delphi-ingest
  proxy, NOT a CDC-issued official revision number; re-scoring is of the REFERENCE peak
  assignment on as-of data and does NOT re-score the 1120-cell model panel (model peak
  metrics remain retrospective); 2002 weeks have no real-time vintage; archived final
  CSVs are not a vintage. No official CDC release calendar is claimed. Do NOT call the
  manuscript submission-ready.

---

## T5 — JBHI verification
status: COMPLETED (dated verification record; template class-file download UNVERIFIED)
start_utc: 2026-11-06T13:20:29Z
end_utc: 2026-11-06T13:29:00Z (archived 13:33:47Z)
commands: `curl -s -o /dev/null -w "%{http_code}"` and content fetches on the official
  EMBS JBHI author page, IEEE Author Center AI policy, IEEE Open AI guidance, IEEE
  Article Templates page and the template-selector endpoints; exit 0.
exit_codes: 0 (all probes).
outputs: `v8/JBHI_VERIFICATION_20261106.md` sha256 24e2f553c17977d67f0743b811ea7f1d6699a22bdbacb86001395967ac3f9259;
  `v8/JBHI_PROVENANCE_PATCH.md` sha256 724d5b98041bce028a711e86670b5a67c006c427a883bcabb7c6757e46219d4c;
  `v8/T5_VERDICT.md` sha256 e311fb201c21bfd3ce5f0cb2298a2905b7f69e6441337a1677d3ce8e3160a9c8.
evidence (VERIFIED, exact quotes in the record):
  - `https://www.embs.org/jbhi/prepare-and-submit-your-manuscript/` HTTP 200:
    14 pages regular / 16 review INCLUDING supplementary; abstract ≤250 words;
    IEEE single-spaced double-column with embedded figures/tables; hybrid OA;
    APC US$2,800 for 2026; IEEE member 5% / society 20% discounts not combinable;
    voluntary page charges $110/$250/$350.
  - AI disclosure is IEEE-wide policy, not a JBHI clause:
    `https://journals.ieeeauthorcenter.ieee.org/.../submission-and-peer-review-policies/`
    HTTP 200 — disclosure in acknowledgments of AI system, sections and level of use;
    grammar/editing exception. `https://open.ieee.org/author-guidelines-for-artificial-intelligence-ai-generated-text/` 200.
  - UNVERIFIED: no official `.cls`/Word class file could be downloaded. Measured:
    template selector root 200 (SPA shell only);
    `.../secure/templateSelector/publicationType` 404 with browser UA / **418** with
    full python-requests default headers (WAF bot block, NOT a missing page);
    `.../api/ieee-template-selector` 302 → 502 when following redirects;
    `.../secure/downloadTemplate` 404; third-party zip link 404.
  - Version drift recorded: `https://eshukan.com/bd_show.aspx?cid=1&id=20553` 200
    still states an outdated 12-page regular limit.
  - `submission-ready: NO` — the manuscript is NOT called submission-ready.
remaining: obtain the official template class file in a browser session, pin its
  filename + SHA-256; owner must paste `JBHI_PROVENANCE_PATCH.md` into
  `PAPER_TO_CODE.md` and the manuscript provenance.

---

## T6 — Resource measurements
status: COMPLETED (all 6 representative models have measured peak VRAM; see T6 FINAL SWEEP UPDATE)
        Three models still lack an isolated single-forward latency (explicitly NOT_MEASURED).
start_utc: 2026-11-06 (see `v8/T6_VERDICT.md` for exact window)
end_utc: 2026-11-06
commands: `744239 t6_res_cpu` (`sbatch`, `tiny`, CPU, `/usr/bin/time -v`,
  NPZ scoring-path latency warm-up 5 + repeat 50, version probe, wall-time extraction);
  `744253 t6_res_gpu` (gpu_a100) PENDING→CANCELLED by the owner of that job, never
  started; two `stingy` GPU submissions rejected by `QOSMaxSubmitJobPerUserLimit`.
exit_codes: 744239=0:0 COMPLETED (cpunode-034, 14 s); GPU attempts rc=1 / cancelled.
outputs: `v8/RESOURCE_MEASUREMENTS.csv` sha256 bde9031f4fb2b91aa0321f71fc285cbe3df8f254d2f2f631379d4eb2f73252cd;
  `v8/T6_VERDICT.md` sha256 015ae57a75f206c9fc0f804f30f0f1bf4e7311e0a23e35e9f1085d4628e5ebb3;
  `v8/resource_logs/SHA256SUMS.txt` sha256 6ee6c7e464032fbb6e4e7e7d29a3fa6466b5b19e4cf7524c0a137c60a965f890
  (36 raw logs, 0 hash mismatch).
evidence:
  - REAL training wall times from `master_queue.tsv` note fields with line numbers:
    MIFlu 581 s, NLinear 6 s, PatchTST 7 s, frozen encoder
    DeepSeek-R1-Distill-Qwen-1.5B 24 s; 1082-row extraction table plus 148 UTC
    START/END pairs from `wf_fix218/logs/shard0.log`.
  - REAL NPZ scoring-path latency 0.0287–0.0297 ms (std 0.0014–0.0018) on
    `(170,7,24)` float32, warm-up 5 / repeat 50 — explicitly labelled as the scoring
    path, NOT a model forward pass.
  - Software versions measured INSIDE the sbatch job: Python 3.9.25, numpy 2.0.1,
    pandas 2.3.3, torch 2.5.1, GNU time 1.9.
  - `peak_vram_mib` = NOT_MEASURED for all 6 rows: no GPU was allocated (tiny job);
    GPU job A was scheduled for 2026-11-08 past its time limit and cancelled;
    GPU job B hit `QOSMaxSubmitJobPerUserLimit`. No VRAM number was invented.
  - Chronos / TimesFM rows = BLOCKED / NOT_EXECUTED (T2 blocked: no pinned weights,
    no isolated env, no pilot). Real model-forward latency NOT_MEASURED.
  - Every row `scope=subset_only_not_full_1120`; no full-1120 Pareto claim.
remaining: rerun `t6_res_gpu.sbatch` when an A100 is allocatable and QOS allows, then
  complete T2 to unblock the two foundation rows.


### T6 UPDATE — 2026-11-06 (GPU measurement COMPLETED for MIFlu)
commands: `sbatch t6_gpu_v8b.sbatch` → job **744532** `t6_res_gpu_v8b`, `stingy`,
  gpu-a100-05, A100-SXM4-80GB, driver 580.167.08. `/usr/bin/time -v` + real
  `export_miflu_all7.py --cells 36:2023 --device cuda` from an existing checkpoint,
  with `nvidia-smi --query-gpu=memory.used -l 1` sampling.
exit_codes: 0:0 COMPLETED; all logged sub-steps rc=0.
evidence: `[PASS] all requested cells exported`, `test MSE_7var_z=1.624383`,
  **peak_vram_mib=4816** (63 samples, min 16), forward wall **62.94 s**, 15:30:57Z → 15:32:01Z.
outputs: `v8/RESOURCE_MEASUREMENTS.csv` sha256
  `D609D57DCEB5FCBA6656A40A4576D87971F5371AC46AD6589754515C95BFCFCC`;
  `v8/T6_GPU_UPDATE.md`; 12 new raw logs in `v8/resource_logs/` (hashes appended to
  `SHA256SUMS.txt`); `v8/T6_VERDICT.md` status PARTIAL (IMPROVED).
remaining: peak VRAM / real forward latency still NOT_MEASURED for the other 5 models;
  Chronos/TimesFM resource rows remain BLOCKED; no full-1120 Pareto claim.

---

## T7 — v8 documents
status: COMPLETED
start_utc: 2026-11-06T14:31:13Z
end_utc: 2026-11-06T14:51:07Z
commands:
  - `python "HANDOFF_20261105/v8/docs/build_v8_verify.py"` (with a 480 s timeout
    after a first 120 s timeout was hit) — rebuilds + converts + audits all v8 DOCX/PDF.
  - LibreOffice-kit CLI `node cli.js render --pages 1 --dpi 36` for page counts
    (pdfium), cross-validated against `render --pages all`.
exit_codes: all document builds, PDF conversions and audits = 0 (only one
  non-fatal 120 s timeout on the first verify attempt, retried successfully).
outputs (all in `01_最终报告/v8/`, sha256):
  `ieee_manuscript_en_v8.docx` 672cb12d046f5711ae700a358a8accaf10656113bd50650b9aa4c34e0c2e0443
  `ieee_manuscript_en_v8.pdf`  9f7b52fe233a9782883077179805068f2ea31e7d4a98d80d8642bf5f7af44a07  (7 pages)
  `report_internal_zh_v8.docx` 6c597a751f8874ca70677c7e03906a047ab15cc3cc7aafb81bfca713460900af
  `report_internal_zh_v8.pdf`  b8c255263efef5160a71ad2e7eab78628fe93fa61e569575ea3bf203077bd4fb  (6 pages)
  `report_internal_qa_zh_v8.docx` c40253ecc2aa29b0d6b212748ac171ae80345d4a966fde74602ed86b5a8e4db3
  `report_internal_qa_zh_v8.pdf`  5fb7be2347ee1f8ef69e4b9ff23321a516d12e0010c55e16c7d442b2000351ed (14 pages)
  Also `HANDOFF_20261105/v8/docs/{V8_SCIENTIFIC_ADDENDUM.md,V8_CHANGELOG.md,V8_BUILD_RESULTS.json}`
  and updated `v8/{DOCUMENT_UPDATE_MAP.csv,SCIENTIFIC_AUDIT.md,BLOCKED_AND_UNVERIFIED.md}`.
evidence:
  - English manuscript BODY (not only an addendum), Chinese internal report and
    Q&A companion all rebuilt; Q01–Q25 original answers preserved.
  - Each document contains an explicit "V8 — old snapshot vs new panels" separation
    section; old claims appear ONLY framed as superseded (verified by DOCX text audit).
  - Nine superseded claims documented: WF partial -> 1020/1020; Table VI 51/53 -> 53/53;
    `final_llm_import` TODO -> real table; NLinear K&S champion -> MIFlu 252 / PatchTST 215
    / NLinear 57 of 1680; monotonic depth -> non-monotonic; resources NOT EXECUTED ->
    PARTIAL subset; JBHI UNVERIFIED -> dated verification; CDC vintage unreconstructed ->
    complete frozen vintage; v7 DOCX/PDF NOT EXECUTED -> rebuilt.
  - Old 28-arm frozen snapshot (`02_数字表格/`) kept separate; foundation models on a
    separate roster; legacy WF panel flagged as a different scoring population.
  - `submission-ready: NO`. No frozen CSV / raw prediction / checkpoint / owner PPTX touched.
remaining: non-fatal `missingFonts:["Courier"]` substitution in PDF conversion;
  owner must paste `JBHI_PROVENANCE_PATCH.md` into `PAPER_TO_CODE.md`.

---

## T8 — Final package
status: COMPLETED (final re-package; see exact command + hashes in `v8/T8_VERDICT.md` and
  `v8/packaging/v8_package_report.json`)
start_utc / end_utc: recorded in `v8/packaging/v8_package_report.json`
commands:
  ```
  python "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/packaging/build_v8_return.py"
  ```
  (builder internally runs the two official tools: `make_return_manifest.py RETURN_V8
  --exclude VALIDATION_RESULT.json` and `validate_return.py RETURN_V8 --out
  RETURN_V8/VALIDATION_RESULT.json`, then rebuilds both ZIPs.)
exit_codes: recorded in `v8/packaging/{make_return_manifest,validate_return}.exit_code.txt`
  and `v8/packaging/v8_package_report.json`.
outputs: `v8/RETURN_V8/`, `v8/RETURN_TO_CHATGPT.zip`, `v8/RAW_EVIDENCE.zip`,
  `v8/MESSAGE_TO_CHATGPT.md`, `v8/T8_VERDICT.md`.
evidence: the FINAL pass was run AFTER `final/WF_RECOMPUTED.csv` reached 1020/1020,
  AFTER the three v8b DOCX/PDF were rebuilt, and AFTER the T2/T4/T6 evidence and
  corrected audit docs landed. `RETURN_V8/final/WF_RECOMPUTED.csv` shows 1020 `ok`;
  `RETURN_V8/DOCUMENTS/v8/` contains the 6 v8b files; validator
  `integrity_status: PASS` with `scientific_readiness: NOT_ASSESSED`; manifest coverage
  diff empty (no unlisted files).
remaining: a structural PASS is NOT scientific validation; the explicitly blocked items
  in `v8/BLOCKED_AND_UNVERIFIED.md` remain (80-cell expansion NOT_EXECUTED_BY_PROTOCOL,
  T5 template class file UNVERIFIED, T6 five VRAM rows NOT_MEASURED, T3 two quarantined
  NPZ, confirmatory dependence-aware statistics). The manuscript is NOT submission-ready.

---

## FINAL v8c UPDATES — 2026-11-06 (supersedes the interim records above)

### T2 FULL80 UPDATE
status: COMPLETED
commands: `sbatch t2_full80.sbatch` -> job **744886** `t2_fm_full80`, `stingy` /
  A100-SXM4-80GB; `/usr/bin/time -v ... t2_full80.py`; nvidia-smi 1 s sampling.
exit_codes: 0:0 COMPLETED; wall 50.71 s; Max RSS 5,088,224 KB.
outputs: `v8/foundation/T2_FULL80.md`,
  `v8/foundation/t2_hpc_evidence/full80_out/FOUNDATION_80_CELLS.csv`,
  `FOUNDATION_80_REPORT.json`, 80 `pred_*.npz`,
  `v8/foundation/T2_EVIDENCE_HASHES_FULL80.txt`.
evidence: **80/80 cells `ok`, all finite, 80 real NPZ**; 2 models x 4 L x
  10 DISTINCT FORECAST ORIGINS (rows 773-782). peak VRAM 2608 MiB (51 samples);
  Chronos 10.229 +/- 1.074 ms (warm-up 1 / repeat 10), TimesFM 50.906 +/- 4.459 ms
  (warm-up 1 / repeat 5). `seed_semantics=NOT_APPLICABLE`.
remaining: the literal `2 x 4 L x 10 seeds` expansion is `NOT_EXECUTED_BY_PROTOCOL`
  (frozen zero-shot models have no training seed dimension); no multivariate-native
  checkpoint, no full-1120 comparison; per-channel univariate adapter limits remain.

### T3 RESTORE UPDATE
status: COMPLETED
commands: `sbatch t3_restore_final.sbatch` -> job **744884** `t3_restore_final`,
  `tiny` / cpunode-034. COPY-restored the 2 corrupt NPZ from their existing valid
  7-channel copies, validated all 388 NPZ with numpy inside sbatch, then re-ran the
  exact `final_llm_import` task with `QUEUE_FORCE_FINALISE=1`.
exit_codes: 0:0 COMPLETED; all 3 analysis scripts rc=0, `ok=true`.
outputs: `v8/T3_RESTORE.md`, `v8/evidence/t3_restore/restore_20261106T173725Z/*`.
evidence: **388/388 NPZ readable, 0 unreadable**, `(W,7,L)`, all finite.
  `BENCH_MSE_BY_MODEL_L.csv` hash `2e03b510...` -> **`a7d98ad84a72c5b82610e076f64cabecdda8ebe64099ef7e8a078161a4541e46`**
  (69 lines). The 2 original corrupt files remain archived, not deleted.
remaining: this is still a LEGACY analysis-tree table, a different scoring
  population from the 1120 national panel and the LEGACY WF panel.

### T5 PROVENANCE UPDATE
status: COMPLETED (step 4)
commands: created `v8/PAPER_TO_CODE.md` (v7 content + the dated JBHI guidance
  verification block); patched `v8/packaging/build_v8_return.py` so
  `RETURN_V8/PAPER_TO_CODE.md` prefers the v8 copy over the frozen v7 skeleton.
exit_codes: 0 (Python file writes).
evidence: the v7 original at `HANDOFF_20261105/v7/RETURN_V7/PAPER_TO_CODE.md`
  remains byte-identical; `v8/JBHI_PROVENANCE_PATCH.md` is now applied.
remaining: the official template class file itself stays UNVERIFIED
  (404 / WAF 418 / API 302->502).

### T6 FINAL SWEEP UPDATE
status: COMPLETED (all 6 representative models measured)
commands: `sbatch t6_sweep.sbatch` -> job **744897** `t6_final_sweep`;
  `sbatch t6_miflu_fix.sbatch` -> job **744899** `t6_miflu_fix`
  (fixes the rc=126 `Permission denied` of the sweep's MIFlu step).
exit_codes: 744897 = 0:0 COMPLETED; 744899 = 0:0 COMPLETED.
outputs: `v8/T6_FINAL_SWEEP.md`, `v8/RESOURCE_MEASUREMENTS.csv` sha256
  `9574eeff6f0e39ddba6488b2e8fe8ef09b763c90fdd27223d7960b8f886b1117`,
  `v8/resource_logs/final_sweep/*`, `v8/resource_logs/t6sweep_744897.out`.
evidence: peak VRAM (A100-SXM4-80GB) MIFlu **4816 MiB** (46+63 samples),
  NLinear **558** (36), PatchTST **720** (7), GPT-2 frozen encoder **1070** (11),
  Chronos **596** (6), TimesFM **2594** (11). Warm-up+repeated REAL forward
  latencies: GPT-2 6.98 +/- 0.097 ms, Chronos 9.854 +/- 0.337 ms,
  TimesFM 48.273 +/- 3.531 ms. Cross-checked by 744886 and 744532.
remaining: MIFlu / NLinear / PatchTST isolated single-forward latency is
  explicitly NOT_MEASURED (their measured quantity was a real full cell export or
  training job); all rows `scope=subset_only_not_full_1120`; no full-1120 Pareto.

### T7 v8c REBUILD and T8 FINAL PACKAGE
T7: the 3 v8 DOCX/PDF pairs were rebuilt again (v8c) so their BODIES carry the
  final 80-cell T2, 388-cell T3, T5 provenance and 6-model T6 results; old
  claims are marked SUPERSEDED. See `v8/docs/V8C_REBUILD_LOG.md`.
T8: the final package was rebuilt AFTER all v8c outputs landed. See
  `v8/T8_VERDICT.md` and `v8/packaging/FINAL_HASHES.txt` for the authoritative
  file count, ZIP sizes and SHA-256 (kept outside RETURN_V8 because the package
  mirrors its own documentation and ZIP hashes therefore change on each rebuild).

### stdout / stderr / exit-code paths for the FINAL v8c runs

| Task | job | stdout | stderr | exit code / record |
|---|---|---|---|---|
| T1 recompute | 744271 / 744334 | `code/queue/wf_fix218/logs/recompute_*.out` | `.../recompute_*.err` | `v8/evidence/WF_RECOMPUTE_REPORT.json` |
| T2 full80 | 744886 | `v8/foundation/t2_hpc_evidence/logs/full80_744886.out`, `full80_stdout.txt` | `.../full80_stderr.txt` | `v8/foundation/T2_FULL80.md` |
| T3 restore | 744884 | `v8/evidence/t3_restore/restore_20261106T173725Z/final_llm_import.stdout` | `.../final_llm_import.stderr` | `v8/T3_RESTORE.md` |
| T6 final sweep | 744897 / 744899 | `v8/resource_logs/t6sweep_744897.out`, `v8/resource_logs/final_sweep/*.stdout` | `v8/resource_logs/final_sweep/*.stderr` | `v8/T6_FINAL_SWEEP.md` |
| T7 v8c rebuild | local | `v8/docs/V8C_REBUILD_LOG.md` | same file | `v8/docs/V8C_BUILD_RESULTS.json` |
| T8 final package | local | `v8/packaging/V8C_FINAL_BUILD.stdout.txt` | same file | `v8/packaging/v8_package_report.json` |

Authoritative FINAL ZIP sizes and SHA-256: `v8/packaging/FINAL_HASHES.txt`
and `v8/packaging/v8_package_report.json` (both OUTSIDE `RETURN_V8/` by design —
the package mirrors its own documentation, so ZIP hashes necessarily change on
each rebuild). Validator `PASS` with `scientific_readiness: NOT_ASSESSED`.
