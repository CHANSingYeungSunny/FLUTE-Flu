# F1 STORAGE BUDGET

Generated 2026-10-06. **Scratch must not be used** (over quota, grace expired). All F1
output goes to `/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1/`.

---

## 1. Projected footprint

| Category | Count | Unit | Total |
|---|---:|---:|---:|
| best validation-selected checkpoints — MIFlu | 4 | ~3.9 MB | 15.6 MB |
| best validation-selected checkpoints — no-text MIFlu | 4 | ~3.9 MB | 15.6 MB |
| checkpoints — NLinear | 4 | < 1 MB | ~1 MB |
| checkpoints — DLinear | 4 | < 1 MB | ~1 MB |
| predictions (NPZ, compressed) | 24 | 110–265 KB | ~4.2 MB |
| targets | — | inside the same NPZ | (0 — stored together) |
| per-run logs | 16 fits | ~60 KB | ~1.0 MB |
| provenance + manifest files | 24 | ~1 KB | ~30 KB |
| scoring outputs (ranking, pairs, gate report) | ~8 | small | < 100 KB |
| **projected total** | | | **≈ 38 MB** |

**Rounding up for safety: 100 MB.**

### Why checkpoints are small

`save_locked_ckpt()` stores only tensors with `requires_grad=True`; the frozen GPT-2
backbone is **not** written because it is bit-identically reconstructible from the pinned
local snapshot, with a sidecar listing the frozen key set so the reconstruction can be
proven rather than trusted. For F1's GPT-2-based arms that means ~3.9 MB per checkpoint
instead of ~313 MB. (This is also why the four A0-R checkpoints were 331 MB each — the
released harness stores everything.)

### Temporary checkpoints

**None retained.** The trainers keep only the best-validation state and write it once. No
per-epoch checkpoint directory is used, so there is no temporary accumulation to clean.

---

## 2. Retention policy (minimal, as required)

| Artifact | Retained? | Reason |
|---|---|---|
| best validation-selected checkpoint | ✅ **yes**, one per (model, horizon) | required to re-derive predictions |
| final predictions | ✅ **yes** | independent scoring |
| final targets | ✅ yes (inside the NPZ) | independent scoring |
| configuration + parameter manifests | ✅ yes | provenance and trainable-parameter audit |
| logs | ✅ yes | failure diagnosis and ledger reconciliation |
| per-epoch checkpoints | ❌ **no** | not scientifically necessary; not produced |
| optimizer/scheduler state | ❌ no | not needed after selection |
| intermediate training tensors | ❌ no | not produced |

**No existing artifact is deleted by this policy.** The policy applies only to what F1
itself writes into its own new directory.

---

## 3. Pre-run quota guard

The brief requires the F1 scripts to *"refuse to run if the projected output would exceed
a safe home-quota margin."* Implemented as a guard clause:

```
projected            = 100 MB
required headroom    = 1 GB        (10x the projection, deliberately generous)
if (home_quota - home_used) < required_headroom:  refuse
```

**Current headroom: ≈ 22.6 GB** (50 GB quota − 26.9 GB used), i.e. **226×** the
projected requirement. The guard therefore passes comfortably, and it exists so that a
future run cannot silently fill the home filesystem.

The guard is documented in `F1_HOME_QUOTA_CHECK.md` along with the measurement that
supports it.

---

## 4. Scratch policy

| Rule | Status |
|---|---|
| no F1 output written to scratch | ✅ enforced — every path in the sbatch scripts points at `$HOME` |
| scratch used read-only for code and data | ✅ `CODE_ROOT=/scratch/sychan552/a2_stage5` is read-only |
| no redirection back to scratch | ✅ no such path exists in any F1 script |
| no scratch cleanup performed | ✅ nothing deleted |

---

## 5. Comparison with existing usage

| Tree | Size |
|---|---:|
| 19 `innovation_deploy_root_v3_*` (Track B, preserved) | **204.6 GiB** |
| F1 projected | **≈ 38 MB** |

F1 is roughly **1/5400** of the historical deployment's footprint. The storage pressure is
entirely historical, and — as `../postrun_audit_20261006/HISTORICAL_DEPLOYMENT_STORAGE_ACCOUNTING.md`
established — only **66.7 MiB** of that 204.6 GiB is byte-identical, so it cannot be
relieved by deduplication.