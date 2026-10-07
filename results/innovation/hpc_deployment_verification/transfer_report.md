# Transfer report — frozen bundle → HPC

| Field | Value |
|---|---|
| Direction | local workstation → HPC |
| Host | `hpclogin02` (login node) |
| Command (redacted) | `scp -o BatchMode=yes <archive> <sidecar> sychan552@burgundy.hpc.cityu.edu.hk:/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/_incoming/` |
| Exit status | **0** |
| Elapsed | 3.9 s |
| Remote staging dir | `/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/_incoming/` |
| Isolated deployment root | `/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.1_dc7ee964` (did **not** previously exist) |
| Original reproduction dir touched | **no** |

## Files transferred (exactly two)

| File | Remote size | Local size | Match |
|---|---|---|---|
| `innovation_hpc_bundle.tar.gz` | 130,428 B | 130,428 B | ✅ |
| `innovation_hpc_bundle.tar.gz.sha256` | 95 B | — | — |

## Deliberately NOT transferred

SSH keys · credentials · local test artifacts (`test_predictions.csv`, `test_metrics.json`) ·
`frozen_winners.json` (absent) · `test_evaluations/**` · local model checkpoints ·
local caches (`.git/`, `.codebuddy/`, `__pycache__/`).

**No credentials appear in this report or in any command.**
