"""Compat shim: re-export the recorded a0_compat.rearrange.

Used only when the real `einops` is unavailable. a0_compat implements exactly
the three patterns the released GPT4TS_lora.py uses and raises on any other, so
a silent wrong-permutation cannot masquerade as a faithful run.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a0_compat import rearrange  # noqa: F401
