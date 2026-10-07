"""Local-run shim: re-export the recorded a0_compat.rearrange (einops is not
installed in the local Windows interpreter; it IS installed in mlflu_hpc)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "recovery", "a0"))
from a0_compat import rearrange  # noqa: F401
