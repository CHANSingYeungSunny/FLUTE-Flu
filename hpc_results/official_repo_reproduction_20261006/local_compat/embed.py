"""Local-run shim: the released tree has no embed.py (only a stale .pyc).
Re-exports the reconstructions recorded in recovery/a0/a0_compat.py."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "recovery", "a0"))
from a0_compat import *  # noqa: F401,F403
from a0_compat import (DataEmbedding, DataEmbedding_wo_time,  # noqa: F401
                      DataEmbedding_wo_pos, PositionalEmbedding,
                      TokenEmbedding, FixedEmbedding, TemporalEmbedding,
                      TimeFeatureEmbedding)
