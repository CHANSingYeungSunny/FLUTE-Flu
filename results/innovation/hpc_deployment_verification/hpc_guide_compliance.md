# HPC_GUIDE.md compliance (read before any HPC command)

## Guide identity

| Field | Value |
|---|---|
| Path | `C:\Users\Asus\Desktop\FYP code\MLFlu\HPC_GUIDE.md` |
| SHA-256 | `1cd21a655907d137914c695bf04637d8da2f09358a0732c961e739dd8e74c167` |
| mtime (UTC) | `2026-09-01T10:32:08Z` |
| Size / lines | 22,651 bytes / 322 lines |
| Read completely | yes (all 13 sections) |

## Operational requirements extracted

* **Login**: `ssh sychan552@burgundy.hpc.cityu.edu.hk` (backup IP `144.214.138.99`).
  **Passwordless ed25519 key auth is ACTIVE** → the assistant may drive `ssh`/`scp`
  non-interactively. The `cityu` alias is password-based → fallback only, not used.
* **VPN**: not required. **MFA**: not required for the key-based login.
* **Scratch**: `/home/sychan552/scratch/CHATTIME` (symlink → `/gpfs1/scratch/sychan552/CHATTIME`);
  project code at `.../CHATTIME/Chattime`; HF cache `/gpfs1/scratch/sychan552/CHATTIME/.cache`.
* **Environment**: module preamble `module unload default && module load old_modules`; conda env
  `mlflu_hpc` (Python 3.9.25) activated by **PATH-prepend** (NOT `conda activate`):
  `export PATH="/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH"`;
  `export HF_HOME=...`, `TRANSFORMERS_CACHE=$HF_HOME`, `HF_DATASETS_CACHE=$HF_HOME`.
* **Slurm**: default `--partition=stingy --gres=gpu:a100:1`; **hard 4h wall cap** on `stingy`;
  never bare `--gres=gpu:1`; `stingy` QOS `Jobs=1, Submit-Job=1` (max 1 pending);
  `gpu_a100` uncapped but congested. Slurm 23.11.10.
* **Resource red line**: never inflate resource requests (account-suspension risk) — self-check every `sbatch`.
* **Retention**: scratch has **no backup** and is purged → pull outputs back to local after each job.
* **Transfer**: rsync (Git Bash) preferred, PowerShell `scp` fallback; local edits do NOT auto-sync.
* Note: `statsmodels`/`patsy` were historically missing; **observed PRESENT now** (`statsmodels 0.14.6`).

## Conflicts with the generated `DEPLOY_AND_VERIFY.md`

| # | Conflict | Resolution (precedence) |
|---|---|---|
| C1 | The generated doc extracts **into the original reproduction dir** `.../CHATTIME/Chattime`, which would overwrite an existing project | **RESOLVED by isolation** — extracted into `.../MIFlu_innovation_deployments/innov-v2.1_dc7ee964`; the original `Chattime/` was not touched (isolation > HPC_GUIDE > deploy doc) |
| C2 | The generated doc specifies **no environment activation** | **RESOLVED** — followed HPC_GUIDE §4 (module preamble + PATH-prepend + HF cache exports) |
| C3 | The generated doc calls bare `python` | **RESOLVED** — used the `mlflu_hpc` interpreter (`/home/sychan552/.conda/envs/mlflu_hpc/bin/python`, 3.9.25) |

**Unresolved conflicts: none** → no `BLOCKED_HPC_GUIDE_CONFLICT`.

## Invariants preserved throughout

test sealed · source-hash verification enforced · pilot `selection_eligible=false` ·
no winner created · no model ranking · **no `sbatch` this turn** · full sweep blocked.

**No credentials** (passwords, private keys, tokens) are recorded in this report.
