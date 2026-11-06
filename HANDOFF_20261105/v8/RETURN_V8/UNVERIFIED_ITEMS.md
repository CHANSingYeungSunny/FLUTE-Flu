# UNVERIFIED ITEMS

1. **Original paper full text and pinned official code commit** — not opened or
   pinned. `PAPER_TO_CODE.md` stays `verification_level = unverified`. Do not
   accuse the original authors of leakage, and do not assert the paper covers
   only two evaluation dimensions, without the PDF and a commit hash.
2. **IEEE JBHI current regular-author guidance, format, fees and AI-use
   disclosure** — not read from the official page. Unverified.
3. **The 1120-cell matrix** — submitted but NOT complete. 117/1120 cells have
   validated outputs at capture. No full-panel ranking, significance or
   equivalence claim is available from it.
4. **PROTOCOL_LOCK** — `frozen: false`; the matrix was submitted before the lock
   was frozen/hashed. Recorded as a deviation; nothing back-dated. All current
   comparisons are retrospective/exploratory, not prospective confirmation.
5. **Data calendar** — `epiweek`/`date` labels are synthetic; the real CDC
   epiweek mapping, release latency and revised-vintage values are not
   reconstructed. Only `retrospective final-vintage evaluation` may be claimed.
6. **Table VI regional and walk-forward** — 9 and 170 TODO rows remain in the
   legacy queue; the legacy driver is stopped. `post_all_v2.sh` hands off once
   `all/phase.done` exists. No external-validity conclusion is available.
7. **Track C** — >=3 eligible rolling origins and >=3 compatible regions,
   Chronos/TimesFM fixed versions, licences, context limits and pretraining
   overlap: not executed. Eligibility lists were not frozen from real dates.
   These are `blocked` / `not_executed`, not failures.
8. **Event-level peak detection** — detector parameters and monotonic 1:1
   matching were not pre-defined or executed; `PEAK_EVENTS.csv` is header-only
   by design. Step-level partial PTE/PIE exists in `AGGREGATION/`.
9. **Ablation depth trend** — 60/60 cells exist with manifests, but the
   7-variable aggregate trend has not been recomputed. Keep 27/60 vs 60/60 as
   a documented snapshot conflict, not a resolved trend.
10. **no-text** — 3 assertions passed, 0 skipped, on fixed weights in eval mode
    on CPU. This does NOT establish gradient/LoRA/text-branch reachability
    during training, nor an independent training trajectory.
11. **Statistical independence** — ten seeds estimate training variation, not
    epidemic uncertainty. Overlapping origins, horizons and regions are not
    independent. Non-significance is not equivalence.
12. **Resource completeness** — peak memory, inference latency and warm-up
    protocols were not measured for the full roster. Missing values are missing,
    not zero.
13. **Presentation artefacts** — the owner-edited PPTX is unchanged; suggested
    scientific sync points only, no silent overwrite.
