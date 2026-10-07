# Original MIFlu split semantics vs clean-v3 implementation

Verdict summary: **MATCH** on all load-bearing settings; the paper is silent on
two low-level implementation details (marked `not specified in paper`), which the
clean-v3 implementation fills with the standard disjoint-window convention.

| Aspect | Original paper | clean-v3 implementation | Verdict |
|---|---|---|---|
| Dataset / country | National Illness, United States, 2002–2021, 7 variables | `data/raw/national_illness_raw.csv`, 1025 weeks, 7 vars (ILITOTAL index 4) | MATCH |
| Split ratio | 70:10:20 chronological | 717 / 102 / 206 timestamps (69.95 / 9.95 / 20.10%) | MATCH |
| Look-back T | 104 steps | T = 104 | MATCH |
| Horizons L | 24, 36, 48, 60 | 24, 36, 48, 60 | MATCH |
| Repetitions | mean of 10 | seeds 42–51, seed-mean | MATCH |
| Normalization | StandardScaler per input variable | z = (x − mean_train)/(std_train + 1e-8), float32, population std (ddof=0), fit on train only | MATCH |
| Metric space | MSE/MAE after normalization (z-space) | `paper_aligned_full_output` 7-var full-L z; primary `average_MSE_4L` | MATCH |
| Prediction output shape | L-step vector per origin (7 vars) | model output (L, 7), rolling origins stride 1 | MATCH |
| Test/val boundary | not stated explicitly | val_end = 819; first test target = 820 | not specified in paper |
| Window assembly | not stated explicitly | X[i] = data[i:i+T]; Y[i] = data[i+T:i+T+L]; split by target-start ts = i+T | not specified in paper |

The 70:10:20 rounding is `int(round(1025·0.7)) = 717`, `int(round(1025·0.1)) = 102`,
remainder 206 (20.1%). No authorized or unsupported deviation from the paper was
found on any load-bearing setting.
