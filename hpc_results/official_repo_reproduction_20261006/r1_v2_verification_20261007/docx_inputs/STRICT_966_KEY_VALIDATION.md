# STRICT-966 KEY VALIDATION

Canonical key-set SHA-256: **`4ad79bb14b2cc11ec3ae1e07e13ae4bdcf41a87161d5149774ab1a94f95d1961`**

| L | Train | Validation | Test | Test keys/seed | expected |
|---|---:|---:|---:|---:|---:|
| 24 | 549 | 74 | 170 | 28560 | 28560 |
| 36 | 537 | 62 | 158 | 39816 | 39816 |
| 48 | 525 | 50 | 146 | 49056 | 49056 |
| 60 | 513 | 38 | 134 | 56280 | 56280 |

## Duplicate keys

**0 duplicates** across all 12 horizon×seed test key sets.

## Superseded invalid key set

SHA `0742b4ab…042a7` — split label derived from the input origin; one test origin per horizon was mislabelled as validation. Regenerated and excluded from all scoring.
