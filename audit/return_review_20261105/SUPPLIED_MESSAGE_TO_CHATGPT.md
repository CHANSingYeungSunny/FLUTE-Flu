# Handoff to ChatGPT — 2026-11-05 00:15 HKT

**中文摘要**：這個資料夾是完整交接包。`RETURN_TO_CHATGPT.zip` 是可讀的 return package，`RAW_EVIDENCE.zip` 是真實逐格證據（兩個 zip 解壓到同一目錄還原完整樹）。`MESSAGE_TO_CHATGPT.md` 是給 ChatGPT 的指示；`VALIDATION_RESULT.json` 是 validator 結果（PASS，只代表結構/哈希，不代表科學驗證）。

## Files

| File | Size | SHA-256 |
|---|---:|---|
| `RETURN_TO_CHATGPT.zip` | 7,299,432 B | `40391F43D712BB98CF4F6E97131FEAADA95FBCF4D9E29786F3DB3A6BB0152841` |
| `RAW_EVIDENCE.zip` | 65,761,420 B | `3B7F116BD591BC7AC81DFDF79659DF500A1A8B4C4196E6E4DFCF2F254DF7F0EE` |

## English prompt (copy the block below to ChatGPT)

```text
You are receiving the 2026-11-05 return package for the MIFlu / MLFlu FYP.

FILES
- RETURN_TO_CHATGPT.zip (7,299,432 B, sha256 40391f43…52841)
- RAW_EVIDENCE.zip (65,761,420 B, sha256 3b7f116b…df7f0ee)
Unzip both into the same directory to restore the full tree.

WHAT IS VERIFIED AND SHOULD BE TREATED AS CURRENT
1. DOCUMENTS/v6/ contains the rebuilt six bilingual reports (DOCX + PDF), built from the
   repaired build_revised.py. Ablation status is 60/60; there is no 27/60 left.
2. Core Track B (MIFlu/NLinear/PatchTST/DLinear, 4 L x 10 seeds) is COMPLETE: 160/160,
   independently checked by cellok.py; both core lanes wrote .done sentinels.
3. The corrected statistics remain: 0/136 Holm rejections, 128/136 raw p<0.05, smallest
   adjusted p ≈ 0.0664, NLinear–PatchTST 0.1172; families 13 conventional + 4 LLM-based +
   11 frozen encoders; paired family = 17 non-encoder models including MIFlu, C(17,2)=136.
4. no-text three runtime assertions were executed: 3 passed, 0 skipped.
5. Validator: integrity_status PASS, errors [], scientific_readiness NOT_ASSESSED.
   PASS means structure/hash/status consistency only, not scientific validation.

WHAT IS NOT COMPLETE — DO NOT CLAIM IT
6. The 1120-cell common benchmark is IN PROGRESS, not finished. The package ledger is a
   snapshot with 117 completed / 1003 queued; the live HPC count at handoff is 141/1120
   and rising. Use LIVE_STATUS_DRIFT.md and label the matrix "in progress".
7. Thirteen decision_tree cells are empty partial directories; they will only be retried
   when their GPU stripe actually starts. Two gpu_a100 lanes are still PENDING.
8. Peak metrics are only partial (AGGREGATION/TRACKB_PEAK_PARTIAL.csv); the full 1120
   peak table does not exist yet. The export column prediction_ili is ILITOTAL, so
   PTE/PIE are computable — but only the completed cells are aggregated.
9. Table VI (19 TODO) and walk-forward (170 TODO) have not started in the v2 chain; the
   post-all adapter will start the legacy driver only after all/phase.done.
10. Scratch is at 306/300 GB soft (grace 10 days, hard 1024 GB); large encoder caches may
    push it further. No final prune has been run.

WHAT TO DO NOW
A. Use DOCUMENTS/v6 as the baseline; do not rebuild from the old v5 text.
B. Add an execution-status section (or a v7 addendum) stating:
   - core 160/160 complete;
   - common 1120 in progress at 141/1120 at handoff;
   - 13 partial decision_tree cells and 2 pending GPU lanes;
   - Table VI / WF not started;
   - quota 306/300 GB soft, grace 10 days.
C. Keep all old-snapshot scientific numbers (reproduction, 28-arm accuracy, peak,
   efficiency, Holm) unchanged. Only update execution status and limitations.
D. Add the Track B pending subsection with the aggregation commands:
   python cellok.py count all/export all/cells_all.tsv
   python aggregate_core.py ; python aggregate_peak.py
E. Produce CHANGES.md keyed to the return-package files, listing which claims changed and
   which are still blocked/not_executed.
F. Do not write "1120 completed", "full Track B panel", or new peak numbers beyond the
   partial tables until the HPC run actually finishes.

KNOWN DEVIATIONS TO DISCLOSE
- PROTOCOL_LOCK.json still has frozen:false while the matrix was submitted; do not
  backdate it, disclose it as a deviation, and do not call it prospective confirmation.
- author_966 and author_repo_966 have different byte hashes but were verified numerically
  identical across all 7 channels (max abs diff 0.0); state this in provenance.
- The package's ledger snapshot (117) and the live count (141+) differ; LIVE_STATUS_DRIFT.md
  explains the drift.

RETURN
Please return updated DOCX/PDF (or a patch), CHANGES.md, and a short list of items that
must wait for the completed 1120 matrix.
```
