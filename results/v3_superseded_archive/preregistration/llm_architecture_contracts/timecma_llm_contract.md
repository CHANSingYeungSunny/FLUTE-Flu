# TimeCMA-inspired LLM — component implementation contract

Official basis: TimeCMA (AAAI 2025), https://github.com/ChenxiLiu-HNU/TimeCMA,
pinned commit `223e4ae9364bec3e3a2d8bb39ab6eed2cf510296`, licence NOASSERTION
(manual review required before use).

## Frozen data flow

```
window X (T=104, C=7)
  -> TIME-SERIES ENCODING BRANCH : encoder producing time-series embeddings E_T
  -> LLM-EMPPOWERED PROMPT BRANCH: LLM (GPT-2, pinned) encodes prompt/text -> E_P
  -> CROSS-MODALITY RETRIEVAL    : similarity-based retrieval aligns E_T with E_P
  -> LAST-TOKEN / CACHED PROMPT  : the prompt branch is summarised by its last
                                   token (or a cached prompt encoding) to bound cost
  -> FORECAST HEAD               : over the aligned representation -> L
```

## Mandatory components (all must be present)

| Component | Requirement |
|---|---|
| separate time-series branch | its own encoder, not shared with the LLM branch |
| LLM prompt branch | an LLM-driven branch over prompt/text tokens |
| cross-modality retrieval/alignment | explicit retrieval or similarity alignment |
| last-token or cached prompt representation | documented summarisation mechanism |
| forecast head | maps the aligned representation to horizon L |

## Deviations to disclose

- Backbone pinned to GPT-2 (already cached offline).
- Whether the prompt encoder is cached once per run must be preregistered, because
  it changes cost but not the mathematical output.

## NOT allowed

- Reusing the Time-LLM prototypes or the CALF output-consistency loss here.
- Collapsing the two branches into one shared encoder.
