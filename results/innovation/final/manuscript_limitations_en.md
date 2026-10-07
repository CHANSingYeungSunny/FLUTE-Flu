# Limitations (manuscript-ready, English)

1. **Baseline seed count.** The frozen MIFlu baseline provides three seeds, so paired
   inference has an effective sample size of three per horizon. No broad statistical
   superiority is claimed; only one comparison survives Holm correction.
2. **Unavailable candidate families.** TimesNet, TimeMixer/ModernTCN, TF-IDF+SVD, fastText,
   BERT/MiniLM, zero-text and shuffled-text negative controls, Time-LLM-style reprogramming,
   CALF/TimeCMA-style alignment, and Chronos/TimesFM/Moirai were unavailable or not
   completed. Conclusions do not extend to them.
3. **Historical repository integrity.** The pre-incident byte identity of one indicator
   script could not be established; the current canonical script was adopted prospectively
   with a regression check against a trusted pre-incident prediction file. This is a
   reproducibility limitation, not a scientific result.
4. **Source-version repair history.** Ten implementation-source revisions (v2.1-v2.10) were
   required. None changed the scientific protocol, splits, scaler, prompt statistics,
   metrics, thresholds or early stopping.
5. **Login-node incident (2026-09-16).** The one-time Test was initially executed as a
   `nohup` process on a login node, which is prohibited; it entered D state and blocked new
   SSH sessions. It was terminated, and the remaining immutable Test cells were completed
   through a compliant `sbatch` job reusing the same receipt, manifest and evaluation ID.
   This is disclosed as a **process** incident in reproducibility materials; it did not alter
   any scientific input, checkpoint or metric.
6. **EvoForecast.** The optional AlphaEvolve-inspired arm was not attempted and must not be
   described as completed.
7. **COVID/pre-COVID splits.** Not pre-registered; not presented as confirmatory analysis.
