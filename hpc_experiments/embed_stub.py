"""Unused author import compatibility shim.

The author's `models/GPT4TS_lora.py` imports `DataEmbedding` and
`DataEmbedding_wo_time` from `embed` but never instantiates them (verified: the
only other `embed` match in that file is an unrelated `.llmmodel(...)` call).
This shim satisfies the import so the module loads.

If a future code path DOES construct these, this raises loudly rather than
silently returning a wrong embedding.
"""
class _UnusedImport:
    def __init__(self, *a, **kw):
        raise RuntimeError(
            "Author imported embed.py but nothing should construct "
            "DataEmbedding in GPT4TS_lora; review the source before using this."
        )


DataEmbedding = _UnusedImport
DataEmbedding_wo_time = _UnusedImport
