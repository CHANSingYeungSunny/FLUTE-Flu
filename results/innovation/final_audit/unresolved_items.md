# Unresolved and incomplete items

## Not completed (explicitly, not to be reported as results)

- **TimesNet** — not implemented; not present in any run
- **TimeMixer or ModernTCN** — neither implemented
- **text encoder: TF-IDF+SVD** — not implemented
- **text encoder: fastText** — not implemented
- **text encoder: BERT/MiniLM** — not implemented
- **negative control: zero-text** — not run
- **negative control: shuffled-text** — not run
- **LLM/TSFM: Time-LLM-style** — not implemented
- **LLM/TSFM: CALF/TimeCMA-style** — not implemented
- **TSFM: Chronos** — unavailable locally
- **TSFM: TimesFM** — unavailable locally
- **TSFM: Moirai** — unavailable locally
- **COVID-period analysis** — not separately pre-registered or reported
- **pre-COVID analysis** — not pre-registered; must not be retroactively presented as confirmatory
- **EvoForecast** — optional extension; deferred, not attempted
- **optional extension deferred** — EvoForecast

## Other unresolved items

- **Historical original-repository integrity**: the pre-incident byte identity of `scripts/compute_miflu_indicators.py` could not be established; `historical_original_repository_integrity_verified=false` is retained permanently.
- **COVID / pre-COVID split analysis**: not pre-registered; deliberately not presented as confirmatory analysis.
- **Receipt location**: the single-use receipt originally existed only on HPC and has now been synchronised to the local project; there is still exactly one.
- **Stage-L ledger entry**: the compliant Test resume (job 560659) was submitted outside the autonomous controller and therefore does not appear in `job_ledger.csv`; it is recorded in `execution_reconciliation.json`.
- **Statistical power**: with three baseline seeds, paired inference cannot support a superiority claim; this is a permanent limitation of the current evidence.

## Prohibited future actions without new authorisation

- another Test evaluation; retraining; post-Test reselection; changing the champion;
- adding baseline seeds after seeing Test; changing metrics or thresholds;
- executing EvoForecast; retroactive confirmatory analyses;
- any model computation on a login node.
