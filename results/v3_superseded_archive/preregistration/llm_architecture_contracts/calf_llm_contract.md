# CALF-inspired Cross-Modal LLM — component implementation contract

Official basis: CALF (AAAI 2025), https://github.com/Hank0626/CALF,
pinned commit `50e7270af9a9b256acaf33b2688fef7d95f5a3f0`, Apache-2.0.

## Frozen data flow

```
window X (T=104, C=7)
  -> TEMPORAL TARGET BRANCH : time-series encoder (linear/patch encoder) -> f_T
  -> TEXTUAL SOURCE BRANCH  : LLM (GPT-2, pinned) over prompt/text tokens -> f_S
  -> CROSS-MODAL MATCH      : project both into a shared space using principal
                              word-embedding extraction; match f_T to f_S
  -> FEATURE REGULARIZATION : regularise intermediate features across branches
  -> OUTPUT CONSISTENCY     : align the two branch prediction outputs
  -> FORECAST HEAD          : temporal-branch head -> L
```

## Mandatory components (all must be present)

| Component | Requirement |
|---|---|
| temporal target branch | a dedicated time-series encoder, distinct from the LLM branch |
| textual source branch | an LLM branch driven by text/prompt tokens |
| cross-modal matching | explicit matching/alignment between the two branch representations |
| intermediate feature regularization | a loss on intermediate features, not only on the final output |
| output consistency objective | a loss aligning the two branches' predictions |

## Deviations to disclose

- Backbone pinned to GPT-2 (already cached offline) instead of a larger LLM.
- The cross-modal match is implemented feature-wise; any simplification of the
  official principal-word-embedding extraction must be documented.

## NOT allowed

- Reusing the Time-LLM reprogramming module here.
- Dropping feature regularization or output consistency, which are the defining
  mechanisms that separate CALF from a generic two-branch model.
