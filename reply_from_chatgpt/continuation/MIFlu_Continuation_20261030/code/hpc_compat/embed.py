"""Unused author import compatibility. No embedding implementation substituted."""
class _UnusedImport:
    def __init__(self,*a,**kw):
        raise RuntimeError('Author imported embed.py but should not call it in GPT4TS_lora; review source')
DataEmbedding=_UnusedImport
DataEmbedding_wo_time=_UnusedImport
