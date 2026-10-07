# CURRENT REPOSITORY IDENTITY

Generated 2026-10-06. Append-only.

---

## 1. The project repository (this work)

| Item | Value |
|---|---|
| `pwd` | `C:\Users\Asus\Desktop\FYP code\MLFlu` |
| `git remote -v` | `origin https://github.com/CHANSingYeungSunny/FLUTE-Flu.git` (fetch and push) |
| `git branch --show-current` | `recovery-stage4` |
| `git rev-parse HEAD` | `1f6563f7ea52620354a4fa0666b813b6a9f9cc51` |
| `git log -5 --oneline` | **one commit only**: `1f6563f FLUTE-Flu: MIFlu reproduction docs, scripts, figures (checkpoints excluded)` |
| `git status --short` | 179 `??` · 49 `M` · 9 `D` — identical to the start of the previous round |
| `git diff --stat` | 57 files changed, 149,959 insertions(+), 148,767 deletions(-) — all pre-existing |

### The consequence that governs several conclusions

**The project repository has exactly one commit.** Therefore:

- experiment ordering cannot be reconstructed from git history;
- `scripts/miflu_model.py` carries **uncommitted** changes, so the code version actually
  used at training time **cannot be recovered from git**;
- this is a standing reproducibility gap and is reported as such.

---

## 2. The author's official repository (the reproduction target)

| Item | Value | Verdict |
|---|---|---|
| local checkout (Windows) | `recovery/author_repo/` | — |
| remote | `https://github.com/Jmoon3108/MIFlu.git` | ✅ **the author's own repository** — not a fork, not a mirror |
| commit | `6ed210150b8819313947cf607eb1821c87b1bee3` | — |
| commit metadata | `Fri Mar 21 15:24:23 2025 +0900`, message `Initial commit` | — |
| clone type | partial (`[blob:none]`) — blobs fetched on demand | ⚠️ noted |
| matches the recovery-plan candidate? | plan records `6ed210150b8819313947cf607eb1821c87b1bee3` | ✅ **exact match** |
| **clone timestamp** | `recovery/author_repo/.git/logs/HEAD` line 1: `clone: from https://github.com/Jmoon3108/MIFlu.git` at `1790214853` = **2026-09-24 09:54:29 +0800** | ✅ **filesystem-proven lineage boundary** |

### HPC checkout of the same repository

| Item | Value |
|---|---|
| path | `/scratch/sychan552/a0_replay` |
| `git rev-parse HEAD` | `6ed210150b8819313947cf607eb1821c87b1bee3` — **same commit** ✅ |
| directory created | `2026-09-26 18:29:05 +0800`; `.git/HEAD` mtime `2026-09-26 17:15:28 +0800` — **after every `innovation_deploy_root_v3_*` directory** |
| source modifications | `git status --porcelain` (excluding `.pyc`) shows only `?? results/` — the output directory the released code needs to write its summary CSV. `git diff --stat` = 9 files, **0 insertions, 0 deletions** (all binary `.pyc`) |
| verdict | **author source untouched**; compatibility layer lives on a separate `sys.path` |

### What the author's tree does NOT contain

No `README`, no `LICENSE`, no `requirements` file, no config file, and **no `embed.py`**
(only a stale `__pycache__/embed.cpython-39.pyc`). Consequences: `README_EXPLICIT` cannot
be a source for the author contract, and an `embed.py` reconstruction was required.

---

## 3. Data identity

| File | Rows | SHA-256 | Role |
|---|---:|---|---|
| `recovery/author_repo/dataset/illness/national_illness.csv` | 966 | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` | the file the released code loads by default; **the file the four A0-R runs used** |
| `recovery/author_repo/dataset/illness/national_illness_orig.csv` | 966 | `8594cecb98c6f2f9dc014eca11c4d5d1e38ad5ce6ed0592d4abe65b146fce395` | the author's other copy (values agree) |
| `data/raw/national_illness_raw_paper_exact.csv` | 966 | `31ffc1693de205ca8de5e966d40c93252e0a0076a212fffc54d1418e1a13b87a` | **the A2 / stage5 / stage6 analysis file** |
| `data/raw/national_illness_raw.csv` | 1025 | (July-2026 snapshot) | **July-2026 dataset track only** |

**Track rule**: the 966-row files belong to A0-R / A1-P / A2-F; the 1025-row file belongs to
the July-2026 dataset track. They must never share a ranking or an average
(`TRACK_SEPARATION_RULES.md`).

---

## 4. Summary

| Question | Answer |
|---|---|
| is the author repository genuinely the author's? | ✅ yes |
| is the commit the one the recovery plan names? | ✅ yes |
| is the author source tree modified? | ✅ no (only `.pyc` and an output directory) |
| is the project's own history usable for ordering? | ❌ no — one commit |
| is the lineage boundary provable? | ✅ yes — the clone log, corroborated by directory mtimes |