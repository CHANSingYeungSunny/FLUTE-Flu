"""fusion — registration of every fusion module plugin."""

from innovation.fusion.concat_projection import ConcatProjectionFusion
from innovation.fusion.cross_attention import CrossAttentionFusion
from innovation.fusion.film_gate import FilmGateFusion
from innovation.fusion.identity import IdentityFusion
from innovation.fusion.registry import (available_fusions, get_fusion,
                                        list_fusions, make_fusion,
                                        register_fusion)

register_fusion("identity", IdentityFusion, note="no-text passthrough")
register_fusion("concat_projection", ConcatProjectionFusion,
                note="mean-pool text + concat + linear projection")
register_fusion("film_gate", FilmGateFusion, note="FiLM (gamma, beta) modulation")
register_fusion("cross_attention", CrossAttentionFusion,
                note="multi-head cross-attention (time queries, text keys/values)")

__all__ = ["available_fusions", "get_fusion", "list_fusions", "make_fusion",
           "register_fusion"]
