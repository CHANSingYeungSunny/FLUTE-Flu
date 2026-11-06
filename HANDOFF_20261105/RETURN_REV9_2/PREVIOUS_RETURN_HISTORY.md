# Previous return history — preserved, not silently rewritten

The 2026-11-04 23:49 HKT return package occupied the same two paths that this
rev9.2 return now uses. Its exact identity is recorded here so the history is not
lost:

| File | Bytes | SHA-256 | Built |
|---|---:|---|---|
| `RETURN_TO_CHATGPT.zip` | 7,299,432 | `40391f43d712bb98cf4f6e97131feaada95fbcf4d9e29786f3db3a6bb0152841` | 2026-11-04 23:49:10 |
| `RAW_EVIDENCE.zip` | 65,761,420 | `3b7f116bd591bc7ac81dfdf79659df500a1a8b4c4196e6e4dfcf2f254df7f0ee` | 2026-11-04 23:49:19 |

That older package had 900 members, `integrity_status: PASS`,
`run_status_counts {completed: 117, queued: 1003}`,
`check_status_counts {passed: 18, failed: 1, not_executed: 4}`,
`errors: []`, `scientific_readiness: NOT_ASSESSED`.

It contained **one unlisted transient prediction file** while all 896
manifest-listed hashes matched. That fact is retained here verbatim and is NOT
rewritten: this rev9.2 return uses the official `validate_result_handoff.py`,
which rejects unlisted files, and quarantines transient files in
`QUARANTINE_REVIEW_COPY/QUARANTINE_RECORD.md`.

The older `RETURN_SUMMARY.md`, `VALIDATION_RESULT.json`, `RAW_EVIDENCE/`,
`code/`, `logs/` and `AGGREGATION/` directory content from that package is still
on disk under `HANDOFF_20261105/` where it was not overwritten; the rev9.2
package is built in the separate `HANDOFF_20261105/RETURN_REV9_2/` tree.
