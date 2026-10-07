# Stage 4 — remaining launch decisions (exact, none invented)

All implementation and CPU-preflight work is complete. What remains before any
compute-node run is a **recorded authorization** for the specific items below.
This prompt does not supply them; I have not invented any approval.

| ID | Decision | State | Effect if unresolved |
| --- | --- | --- | --- |
| D-split | Adopt 676/97/193 (author `num_vali=remainder`) as the A2 profile, or keep historical 676/96/194 | **OPEN** (676/97/193 recommended by documented author convention; 676/96/194 retained as historical) | All 36 A2 learned fits are gated; naive/rows unaffected |
| D-target | Freeze `average_MSE_4L` (7-var z-space) as the selection metric | recorded in `a2_frozen_protocol.json`, not yet supervisor-approved | gates A2 reporting |
| D-compute | GPU-hour ceiling + which compute node/queue | **OPEN** (8 s/epoch, 0.88 GB, ≈1.2 GPU-h evidence is to be verified, not assumed) | gates all GPU fits |
| D-holdout / evaluation scope | Authorization to score the (already-exposed) author Test once after selection | **OPEN** | gates the Test-evaluation step for all A2 rows incl. naive |
| D-a0-env | A0 replay env: GPU node + author gpt2 cache + author-repo data path | **OPEN** | gates A0-01 only |

## What is done and needs no further decision

- `D-adapter` (apply the author-966 adapter) — **done**; implemented directly
  (the illustrative patch did not apply), hash-pinned, 1025-guard preserved.
- `D-nlinear` (authorize/implement the NLinear + naive runners) — **done**;
  both thin runners implemented and CPU-preflight-verified.
- `D-naming`, `D-scope` — no expansion added; core scope unchanged (national,
  MIFlu/no-text/NLinear/naive, no DeepSeek/Qwen, no regional sweep).

## Recommended order once authorized

1. Record D-split (recommended: 676/97/193) and D-target (average_MSE_4L).
2. Confirm D-compute ceiling and the GPT-2 cache on the compute node.
3. Run a bounded development preflight on the node (text-tensor sensitivity
   check #7, currently BLOCKED on CPU for lack of the GPT-2 cache).
4. Dispatch the 36 learned fits + 8 deterministic evals (the 44-row reduced
   matrix); keep Test scoring as a separate step after selection.
5. A0-01 only after D-a0-env.
