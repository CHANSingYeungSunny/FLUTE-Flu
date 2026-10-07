# Canonical indicator implementation — prospective adoption

- repository-relative path: `scripts/compute_miflu_indicators.py`
- SHA-256: `bf72d37ce9eaa21cb052f18568764d913163caf237ba9ce0cf76f15d98f46c0f`
- file size: 24398 bytes
- adoption time: 2026-09-14T19:22:00Z
- scientific protocol: `innov-v2.0`
- implementation source: `innov-v2.2` → `innov-v2.3`

## Historical status (unchanged, NOT rewritten)

> The pre-incident byte identity of scripts/compute_miflu_indicators.py could not be established.

- `historical_integrity_status` = **UNRESOLVED**
- `original_reproduction_repository_integrity_verified` = **false**

Why no reference exists: The surviving pre-incident __pycache__ artefact was compiled from a 24236-byte revision while the current file is 24398 bytes, so it is stale and cannot certify the pre-incident content; the local git HEAD blob is an earlier ~13.4 kB revision; no dated pre-incident copy of the 24398-byte revision exists anywhere on HPC; and no output of this script dated after 2026-09-03 exists to reveal which revision was in use.

## Prospective adoption

> The adopted script is the canonical metric implementation from innov-v2.3 onwards. No claim is made that it is byte-identical to the pre-incident remote working copy.

- matches local working copy: **True**
- matches innov-v2.2 frozen copy: **True**
- canonical copy verified: **True**

## Provided metrics

- MSE
- MAE
- PTE
- PIE
- peak_hit_count
- n_true_peaks
- n_hit
- n_missed

Peak criterion: PTE <= 1 week AND PIE <= 25% (only one).

## Prohibited interpretation

> It must not be represented as proven identical to the pre-incident remote working copy, and size / mtime / pyc-header / bytecode equality must not be cited as proof of byte identity.
