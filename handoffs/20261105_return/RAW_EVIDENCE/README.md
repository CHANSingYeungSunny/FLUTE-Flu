# RAW EVIDENCE

This is a **consolidated raw-evidence handoff**, not metadata-only.

- `cells/core/export/` and `cells/all/export/`: real per-cell outputs pulled
  from Burgundy (676 files, ~151 MB uncompressed). Per-seed `.pth` checkpoints
  were EXCLUDED from the transfer and remain on HPC; retrieve them with the
  paths in `HPC_VALIDATED_CELLS.tsv`.
- `pilot_predictions_miflu_L24_s2021.csv` (1.75 MB) and the historical paired
  CSV are retained from the earlier snapshot.
- `encoder_registry.json` lists pinned model ids/revisions and weight presence.
- `HPC_VALIDATED_CELLS.tsv` enumerates all 277 cell directories (160 core +
  117 national) with a content digest and the original HPC path.
- `RUN_METRICS.csv` has 1,886 real per-run metric rows derived from those cells.
- `PROFILE_COMPARISON.md` records the measured data-profile equivalence.

If this directory is packaged as `RAW_EVIDENCE.zip`, extract it together with
`RETURN_TO_CHATGPT.zip` into one directory to recreate the consolidated tree.
Until both are extracted, raw integrity validation cannot pass.
