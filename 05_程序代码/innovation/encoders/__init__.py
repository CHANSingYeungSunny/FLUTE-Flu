"""encoders — registration of every text encoder plugin."""

from innovation.encoders.gpt2_encoder import GPT2TextEncoder
from innovation.encoders.none_encoder import NoneTextEncoder
from innovation.encoders.registry import (available_encoders, get_encoder,
                                          list_encoders, make_encoder,
                                          register_encoder)
from innovation.encoders.tfidf_svd import TfidfSvdEncoder

register_encoder("none", NoneTextEncoder, note="no text (always available)")
register_encoder("tfidf_svd", TfidfSvdEncoder,
                 note="TF-IDF+SVD fixed contextual embedding (train-only fit)")
register_encoder("gpt2", GPT2TextEncoder,
                 note="frozen GPT-2 textual embedder (needs local cache)")

__all__ = ["available_encoders", "get_encoder", "list_encoders",
           "make_encoder", "register_encoder"]
