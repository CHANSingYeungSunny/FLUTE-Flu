# Early-stopping audit (revision 2)

**Question asked before reuse:** does `scripts/early_stopping.py` depend on
ANYTHING other than validation MSE for (a) checkpoint saving and (b) patience?

**Verdict: YES, it depends exclusively on validation loss → REUSED.**

## Evidence (file:line)

| Concern | Evidence | Result |
|---|---|---|
| Improvement test | `early_stopping.py:85` `improved = val_loss < (self.best_val_loss - self.min_delta)` | val-loss only |
| Patience test | `early_stopping.py:100` `stop = self.num_bad_epochs >= self.patience` | val-loss only |
| Checkpoint save | `early_stopping.py:88-96` saves `model.state_dict()` **iff `improved`** | val-loss only |
| Peak / PTE / PIE refs | grep `peak|hit|PTE|PIE` inside the file → only the PROVENANCE docstring noting the old dual gate was REMOVED (`:20-33`) | none in code |
| Serialisation | `state_dict()` `:116-123`, `save_report()` `:125-129` (there is no `to_dict`) | — |

The old `PeakAwareEarlyStopping` dual gate (val_loss AND peak_hit_rate > 0.7)
was removed in 2026-09 with the peak_hit_rate indicator; nothing of it remains
in the code path.

## How the innovation runner uses it

`scripts/innovation/trainer.py` reuses `EarlyStopping(patience=7,
save_dir=<run>/checkpoints, filename="best_val_mse.pt")`, monitoring
**validation MSE in z-space (all channels)** — the main-protocol metric. PTE/PIE
are computed AFTER training and never influence stopping or checkpoint choice.

## Conclusion

No innovation-specific early stopper was necessary; the existing, audited
implementation satisfies the requirement exactly.
