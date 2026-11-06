# v8 TASK_LOG — execution of NEXT_DEEPSEEK_PROMPT.md T1–T8

Project root: `C:\Users\Asus\Desktop\FYP code\MLFlu`
HPC: CityU Burgundy, user `sychan552`. All model work ran via `sbatch` on compute
nodes; the login node was used only for `squeue`/`sacct`/`scontrol`/`sinfo`/short
`ls`/`cat`/`date` (AGENTS.md RULE 1). No frozen CSV, raw prediction, checkpoint or
owner-edited PPTX was deleted.

Absolute time base: 2026-11-06, UTC = HKT − 8 h.

---

## T1 — Walk-forward missing 218 cells
status: IN PROGRESS (see final update at end of this file)
start_utc: 2026-11-06T11:51:38Z (job 743850 LANE_START; inherited from prior turn)
commands:
  - `ssh ... 'squeue/sacct/grep'` (read-only login-node checks)
  - `743850 wf_fix218` — `sbatch wf_fix218_single.sbatch` → `lane.sh 0 1` →
    `master_task_v2.py run --task-id <id> --kind <kind> --model <m> --L <L> --seed <s> --env hpc --require-a100 1`
    for each of the 218 queued legacy task ids, on `stingy` / `gpu-a100-03` / A100-SXM4-80GB.
  - `743920 wf_probe` — `sbatch wf_probe.sbatch` on `tiny`, NPZ schema + MSE formula probe.
  - `744271 t1_wf_recompute_v8` — `sbatch --dependency=afterany:743850 wf_recompute.sbatch`
    (runs `wf_recompute.py` on `tiny` after 743850 ends).
exit_codes: 743920=0:0 (COMPLETED); 743850 RUNNING; 744271 PENDING (Dependency)
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
remaining: final 15 cells of 743850 → 744271 recompute → update
  `final/WF_RECOMPUTED.csv` / `WF_RECOMPUTED_MEANS.csv` (old copies preserved in
  `v8/evidence/`), then mark COMPLETED/BLOCKED per cell.

---

## T2 — Numerical foundation models (Chronos, TimesFM)
status: BLOCKED (with exact evidence; provenance + separate roster COMPLETED)
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

---

## T3 — Legacy `final_llm_import`
status: COMPLETED (real output table; with a documented 2-cell quarantine caveat)
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
status: PARTIAL — main goal BLOCKED with evidence; proxy vintage table built;
        peak re-scoring BLOCKED (exact missing input)
start_utc: 2026-11-06T13:19:57Z
end_utc: 2026-11-06T13:33:59Z
commands: 16 exact URLs checked (CDC official pages, CDC EPI GitHub Pages, Delphi
  Epidata API, Wayback CDX, Software Heritage, GitHub mirrors); three live
  `https://api.delphi.cmu.edu/epidata/fluview/?...` fetches, all HTTP 200,
  `result:1`, exit 0.
exit_codes: 0 for all fetches.
outputs: `v8/cdc_vintage/cdc_vintage.csv` sha256 ffc960e5654291d0b5517ec894f59aad02ebbf463392aa280fe5eae97fa870f2;
  `v8/cdc_vintage/CDC_VINTAGE_REPORT.md` sha256 fe139859a3cb74f470a1316d9bd894e785965c1acb1c5e292eeee0b6c2ef1bdf;
  `v8/cdc_vintage/T4_VERDICT.md` sha256 180f383ee2f09e2aa4a252a4adad821e1116a0a9a5a84b32cff1d664e837faf1;
  raw HTTP bodies/status TSVs under `v8/cdc_vintage/http_evidence/`.
evidence:
  - CDC official pages (`fluview/surveillance/past-reports.html` 200,
    `fluview/index.html` 200 "All data are preliminary", `stacks.cdc.gov/view/cdc/120452`
    200 "may change as more data are received") contain ONLY week-ending + final values:
    **no release calendar, no revision id**. Archived final CSV snapshots are not a vintage.
  - CDC EPI `https://cdcepi.github.io/flu/data.html` provides `Release_Week` (YYWW)
    for 2009/10–2014/15 only — a publication-epiweek proxy, not a calendar date or
    official revision id.
  - Delphi Epidata `issue`/`release_date` is a reproducible PROXY: live query
    `?regions=nat&epiweeks=201501&issues=201501-201510` returned successive
    release dates 2015-01-16 … 2015-03-20 with changing `wili`
    4.360939 → 4.334367 → 4.290917 → 4.268201. 20 de-duplicated
    `(epiweek, issue)` rows were fetched and written; affected weeks
    `201449;201450;201451;201452;201453;201501`; `cdc_official_revision_id=NOT_AVAILABLE`
    for every row. V3/V4 stopped receiving new data 2026-09-22.
  - Peak re-scoring BLOCKED: frozen peak tables use `step`/row-index `gt_week` (e.g. 801),
    scaler JSON has only mean/std/split indices, manifest only first/last summaries, and
    the only date-like column is a synthetic 7-day date aligning to 2002-01-01↔200240
    (not CDC MMWR weeks). Missing input = `step → absolute row → CDC MMWR epiweek`
    mapping + an official CDC release date. No mapping invented, no peak CSV rewritten.
remaining: recover `score_common.py` / `peak_events.py` `test_window → absolute row →
  date` alignment and confirm the week convention before any as-of re-score; optionally
  pull the full 1997w40→2026 Delphi issue history, always labelled as a proxy.

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
status: PARTIAL — measured subset delivered; peak VRAM and foundation-model rows
        explicitly NOT_MEASURED / BLOCKED with evidence
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
