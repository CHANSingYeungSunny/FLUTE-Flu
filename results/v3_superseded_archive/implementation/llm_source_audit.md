# LLM source audit

The three implementations are separate classes with separate defining mechanisms.

- Qwen: patching, prototype-bank reprogramming, train-only Prompt-as-Prefix statistics, frozen Qwen contract, forecast projection.
- CALF: temporal target branch, textual source branch, cross-modal matching, feature regularization, and output consistency. The trainer now adds the auxiliary loss to the forecast MSE.
- TimeCMA: independent time-series branch, independent prompt branch, retrieval alignment over the last prompt token, and forecast head. It is clean-room paper-derived and does not copy upstream source.

All actual Transformers loading is opt-in and must be performed through a compute-node Slurm job. No real model was loaded during this audit.
