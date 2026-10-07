"""
innovation — reproducible infrastructure for the MIFlu innovation experiments.
==============================================================================

Minimal-intrusion package: it imports the existing MIFlu machinery
(configs / scaler_utils / miflu_model / textual_embedder / cdc_calendar) rather
than modifying it, and adds:

  * ForecastBackbone / TextEncoder / FusionModule plugin interfaces,
  * candidate backbones (dlinear, nlinear, patchtst, itransformer, gpt2_miflu)
    and a generic fusion testbed,
  * text encoders (none, tfidf_svd, gpt2) and fusions (identity,
    concat_projection, film_gate, cross_attention),
  * create-only per-run artifact trees + append-only registry + checkpoint
    manifests with SHA-256 and a restore test,
  * a validation-only champion selector with a hard test-access guard.

This round implements infrastructure + local smoke only. Performance rankings
from smoke runs are explicitly meaningless and must not be reported.
"""

__version__ = "0.1.0-infra-smoke"
