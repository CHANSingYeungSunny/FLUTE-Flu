# PROTOCOL AMENDMENT — N=3, uniform, seeds 42/43/44 for every model (RATIFIED 2026-11-02)

**Status:** **RATIFIED by the user on 2026-11-02 (decision taken before 04:27 HKT; queue
executed 04:40–05:10).** This document is the decision record. It supersedes

  * `AGENTS.md` §2 rule 9 as written on 2026-11-01 (the "MIFlu gets 10 seeds, everyone
    else gets 3" exception), and
  * the intervening **N=10 uniform** proposal recorded in this file at 04:05 on
    2026-11-02 — kept in §5 below as a **rejected alternative**, with its rationale,
    because `R3` forbids deleting superseded reasoning.

`AGENTS.md` §2 rule 9's **text** is deliberately left untouched (the file is capped at
20,162 B and is not to be edited); **this document is the operative text**, and rule 9's
MIFlu-exception sentence is void.

**What this is.** The record of the final benchmark design: **every model in the
benchmark table is evaluated on the same three seeds, 42 / 43 / 44**, and reports
**mean ± sd over 3 seeds**, with the seed count stated in the caption.

**When to read it.** Before running, aggregating, tabulating or writing up any
benchmark number; before touching `AGENTS.md` §2 rule 9; before adding or re-prioritising
a row in `code/queue/master_queue.tsv`.

**Depends on.** `AGENTS.md` §2 rules 9–13, `04_详细说明文档/LLM_SEED_BUG.md` (the seed-passthrough
defect that made every pre-2026-11-02 03:57:47 LLM cell invalid), `04_详细说明文档/EXECUTION_PLAN_PART3.md`.

**Chain.** `AGENTS.md` → **this file** → `04_详细说明文档/WORK_BREAKDOWN.md` §13.F (execution state)
→ `04_详细说明文档/LEDGER.md` (dated rows).

---

## 1. THE RATIFIED DESIGN

| Item | Value |
|---|---|
| Seeds | **42, 43, 44 — identical for every model** |
| Repetitions per cell | **1** (one draw per seed) |
| Reported statistic | **mean ± sd over 3 seeds**, seed count in the caption |
| MIFlu reproduction (Table V) | **unchanged**: 10 repetitions, seeds 2021–2030, 40/40 verified, +4.5% on the 4-horizon mean |
| MIFlu benchmark cells | **new runs**, 4 horizons × 3 seeds = **12 cells** (≈2 A100-h), distinct from the 40 reproduction cells |
| Non-LLM arms | **192 existing cells on 42/43/44 — no re-run** |
| **LLM benchmark block** | **13 arms × 4 horizons × 3 seeds = 156 cells** = the 10 arms with local/OK weights (10 × 12 = 120) **+** the three scale-ladder rungs Qwen-7B / Llama-8B / Qwen-14B (3 × 12 = 36) |
| Paired sign-flip tests | **valid for every model**, because every model now shares the same seed set — the old MIFlu exclusion disappears |

**The rule-9 exception is gone.** The 2026-11-01 rule gave MIFlu 10 seeds (2021–2030)
and every other arm 3 (42/43/44), then excluded MIFlu from the paired tests because no
matched cells existed. The user's instruction removes that asymmetry in the simplest
possible way: **MIFlu's benchmark cells use 42/43/44 like everybody else**, produced by
new 1-rep runs. Table V's 10-rep result is a *different table* and is untouched.

### 1.1 Why the 12 MIFlu benchmark cells are a NEW run, not a slice of Table V

The cheap alternative — reuse MIFlu's existing 2021/2022/2023 repetitions as its "three
seeds" — was considered and **rejected (user decision, OPTION A, 2026-11-02)**:

1. It would make MIFlu's benchmark entry a **subset of Table V's 06_原始数据集** — the same runs
   sliced differently — so MIFlu's benchmark number would not be an independent
   measurement.
2. A reviewer's first question would be "is this an independent result or the same
   experiment reported twice?", which is exactly the ambiguity this amendment removes.
3. A fresh 12-cell run costs **≈2 A100-h** and buys a clean, independent entry.

Implementation: `master_task_v2.miflu_bench_cell()` trains one repetition at the requested
seed, exports the full 7-variable contract through `export_miflu_all7`, and gates on
`_npz_cell_gate(..., n_vars=7)` + `_bench_manifest_ok()` (seed/L/protocol label + a
**measured** A100 on `stingy`/`gpu_a100`). It is deliberately **not** `process_cell()`: that
path resolves the reproduction oracle, which by construction covers only 2021–2030, so
every 42/43/44 cell would have died as `skip.no-oracle` (measured on the first attempt).
The reproduction tree is never written.

## 2. WHY N=3 RATHER THAN N=10

The N=10 design was proposed and then rejected by the user for these measured reasons:

1. **Cost with no benefit at N=3's precision.** 16 arms × 4 horizons × 10 seeds = 640
   non-LLM cells, i.e. **10–40 A100-h**, to re-run 192 cells that already exist and are
   already on the shared evaluation windows. The sd over 3 seeds is what the caption
   needs; the extra 7 seeds tighten a standard error nobody quotes.
2. **The 192 existing non-LLM cells become valid again.** Under N=10 they had to be
   relabelled "pilot, not for publication"; under N=3 they are the reported cells as-is.
3. **Uniformity is achieved without touching Table V.** MIFlu keeps its 10-rep
   reproduction row *and* gets a comparable 3-seed benchmark row, so the paper reports
   one instance of MIFlu per table and one seed protocol per table.

## 3. THE RATIFIED WALK ORDER (what must be true on disk — verified 2026-11-02 05:0x)

The controller walks the queue by priority band, cheapest-and-most-valuable first. The
bands, the cell counts and the tool that proves each one:

| Band | Kind | Cells | Cost | Why here |
|---|---|---|---|---|
| **P1** | `llm_cell` | **156** = 13 × 4 × 3 | ≈0.7 A100-h | cheapest per cell; makes the LLM-vs-trained comparison quotable |
| **P2** | `miflu_cell` | **12** = 4 × 3 | ≈2 A100-h | completes MIFlu's benchmark row independently of Table V |
| **P3** | `table8_cell` | **60** (already queued) | ≈4 A100-h | the ablation table |
| **P4** | `table6_cell` | **21** = 7 horizons × 3 | ≈8 A100-h **measured** (≈22 min/cell) | one complete new table, but 10× the original estimate |
| **P5** | `wf_*` | **1020** (660 arm + 300 classical + 60 MIFlu) | 120–270 A100-h | rolling origin — LAST, never ahead of the four bands above |

| Requirement | Evidence (re-runnable) |
|---|---|
| no runnable row carries a 2021–2030 seed | `n3_queue_audit.py` / `n3_verify_walk.py`: every TODO cell row has seed ∈ {42,43,44} |
| the 22 DONE MIFlu reproduction rows are untouched | state/attempts/note unchanged; 40 `.miflu_verify` markers on disk |
| every 2021–2030 work row is retired, not deleted | 589+403 rows `SKIPPED`/`SUPERSEDED` with the reason in the note; no row deleted |
| every priority band contains exactly its kind | `n3_verify_walk.py` prints the first runnable row of each band and asserts the kind |
| the walk is monotone P1→P5 | `n3_verify_walk.py` simulates `scan_pending`+`pick_next` for both compute lanes |
| MIFlu benchmark cells are *runs*, not re-exports | `master_task_v2.miflu_bench_cell()` + `_bench_manifest_ok()` |
| the F1–F5 finalisation rows are not starved | they belong to the writer lane (`is_mine()` returns 0 for a compute lane), so no compute band can block them |

**The bands are not ordered by priority alone.** `master_controller_v2.sh::pick_next`
gates P1 by this lane's P0 count, P2 by this lane's P0+P1, and **P3/P4/P5 by one shared
global gate** (`P012_ANY == 0`), so among P3/P4/P5 the winner is simply the first match in
**file order**. That is why Table VIII must physically precede Table VI, which must
physically precede the rolling-origin block — a property `n3_verify_walk.py` checks and
`n3_apply_rows.py` enforces.

## 4. THE ONE-LINE TEST FOR ANY FUTURE TABLE

**If two models in one table were trained on different seed sets, or on different numbers
of seeds, that table is invalid — regardless of how good the numbers look.** Under this
amendment every benchmark table passes that test by construction; a table that mixes the
Table V reproduction protocol with a benchmark row still fails it, because those are two
different experiments.

## 5. REJECTED ALTERNATIVE — uniform N=10 (2021–2030), recorded 2026-11-02 04:05

Kept verbatim in substance so the reasoning is not lost (`R3`). The proposal was: every
model on the same **10** seeds 2021–2030, mean ± sd over repetitions.

| Argument | Why it did not win |
|---|---|
| Fairness — equal draws for every model | N=3 on 42/43/44 is equally fair; the seeds are shared, only the count differs |
| One-protocol caption | achieved by N=3 as well |
| Statistical power — paired sign-flip tests valid for all arms including MIFlu | **also achieved by N=3**: matched cells exist for every arm, so MIFlu is no longer excluded |
| Cost — 640 non-LLM cells, 10–40 A100-h | rejected: 192 cells already exist and are already correct on the shared windows; 10–40 A100-h buys precision the paper does not quote |
| Price — the existing 192 cells become "pilot" | rejected: that discards 192 verified A100 cells for no reporting gain |

**Decision:** N=3. The N=10 material is superseded, with this date and reason, and must
not be re-proposed without a measured argument that the 3-seed sd is inadequate for a
specific claim.
