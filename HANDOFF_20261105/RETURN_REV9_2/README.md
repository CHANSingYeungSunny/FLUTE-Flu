# rev9.2 evidence return — 2026-11-05T16:30:00Z / 2026-11-06 00:30 HKT

**IN-PROGRESS**. Structural/hash PASS below is NOT scientific certification
(`scientific_readiness: NOT_ASSESSED`).

Required readable files and 10 AGGREGATION files are all present. The aggregation
files contain explicit `BLOCKED` rows with exact reasons rather than invented numbers;
`RETURN_STATUS.json` declares every blocked output and every NOT_EXECUTED command.

Base packages (SHA-256):
- `MIFlu_Full_Project_Rev9_2_20261105.zip` = 1f8b4cdcee6a68aac04ffdf2705ddc92b65ee6374cdf49f74b64f70a50f7821b
- `MIFlu_DeepSeek_Handoff_Rev9_2_20261105.zip` = 9b53135a7a773eb3c2183e05e4dc2c50bc5fb768c6f8b9ead6a64d0c5d8bc77d

Monitor / resume:
```
ssh sychan552@burgundy.hpc.cityu.edu.hk 'squeue -u sychan552;   python /gpfs1/scratch/sychan552/trackB_20261104/cellok.py count   /gpfs1/scratch/sychan552/trackB_20261104/all/export   /gpfs1/scratch/sychan552/trackB_20261104/all/cells_all.tsv'
```
Do NOT submit a duplicate lane or a second controller while one is alive.
Do NOT run inference on the login node — see `code/HPC_LOGIN_NODE_DSTATE_RECOVERY.md`.
