# MIFlu paper/configuration equivalence audit

The local paper record and canonical GPT-2/MIFlu sources agree on the National-Illness core: 2002-2021, seven variables, chronological 70:10:20 split, horizons 24/36/48/60, `T=104`, `Lp=24`, `S=2`, national forecasting GPT-2 layers `K=6`, LoRA rank `r=4`, and StandardScaler-normalized national MSE/MAE.

The local configuration is `scripts/configs.py` (`NATIONAL_CONFIG`) and the model implementation is `scripts/miflu_model.py`. The verified run manifest records `train_end=717`, `val_end=819`, `test_end=1025`, seven channels, train-only scaler fitting, and train-only prompt statistics.

The model is seven-variable (`N=7`) and produces `N x L` output. `ILITOTAL` is channel index 4 and is the primary reported target channel. This is not a single-output model. The v3 runner reports primary ILITOTAL z-space MSE/MAE and supplementary physical ILITOTAL metrics while retaining the seven-channel output for training. The paper's equations define generic M-point MSE/MAE; therefore the local per-channel reporting convention is disclosed as a reproducibility choice rather than claimed as an exact hidden Table-V aggregation.

Ten formal seeds `42..51` reproduce the paper's ten repetitions as a deterministic local seed convention. Fixed steps 0-3 are v3 supplementary exports and are never averaged across steps.

No scientific blocker was found for the authorized Pilot protocol.
