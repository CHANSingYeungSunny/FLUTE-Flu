"""Compat shim for the released tree's missing embed.py (only a stale .pyc
survives in the author repo). Re-exports the reconstructions recorded in
recovery/a0/a0_compat.py.

The released model imports DataEmbedding/DataEmbedding_wo_time and then NEVER
uses them: the real input projection is nn.Linear(patch_size, d_model).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a0_compat import *  # noqa: F401,F403
from a0_compat import (DataEmbedding, DataEmbedding_wo_time,  # noqa: F401
                       DataEmbedding_wo_pos, PositionalEmbedding,
                       TokenEmbedding, FixedEmbedding, TemporalEmbedding,
                       TimeFeatureEmbedding)
