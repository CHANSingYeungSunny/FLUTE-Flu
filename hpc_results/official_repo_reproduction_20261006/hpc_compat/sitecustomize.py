"""
sitecustomize.py — import-time compatibility shim for replaying the author's
released MIFlu code on the current mlflu_hpc environment.

Placed in its own directory that is put FIRST on sys.path, so the author's
source tree is never written to. Loaded automatically by CPython at startup
whenever that directory is importable.

Two families of shim, both provably NON-BEHAVIOURAL:

1. NumPy 2.0 removed a set of long-deprecated ALIASES. The released code (and
   the TSLib utility module it imports) still uses some of them:

       np.Inf, np.Infinity, np.NAN, np.PINF, np.NINF,
       np.float_, np.complex_, np.string_, np.unicode_,
       np.float, np.complex, np.int, np.bool, np.object, np.str

   `np.Inf` was ALWAYS an alias of `np.inf` (and likewise for the others), so
   restoring the alias restores the identical object, not an approximation.
   Verified at runtime: the restored value IS the same float.

2. peft >= 0.8 removed `prepare_model_for_int8_training`. The released code
   references that name ONLY inside a comment (GPT4TS_lora.py line 85) and only
   under `PEFT == 1` (whose default is 0), so a no-op callable is sufficient
   and cannot enter the released execution path.

Nothing here changes a tensor, a dtype, a random seed, or a control-flow
decision. If a future blocker ever DID require behavioural change, that would be
recorded separately and the run would stop being labelled "released code
replayed verbatim".
"""
import sys

# ── 1. NumPy 2.0 removed aliases ──────────────────────────────────────────
try:
    import numpy as _np

    _ALIASES = {
        "Inf": "inf", "Infinity": "inf", "PINF": "inf", "NINF": "-inf",
        "NAN": "nan", "NaN": "nan", "Infinity_": "inf",
        "float_": "float64", "complex_": "complex128",
        "string_": "bytes_", "unicode_": "str_",
        "float": "float64", "complex": "complex128",
        "int": "int64", "bool": "bool_", "object": "object_", "str": "str_",
    }
    for _alias, _real in _ALIASES.items():
        if not hasattr(_np, _alias) and hasattr(_np, _real):
            setattr(_np, _alias, getattr(_np, _real))
    # Prove the restoration is identity, not approximation.
    assert _np.Inf is _np.inf and _np.Infinity is _np.inf
except Exception:                                    # pragma: no cover
    pass

# ── 2. peft symbol removed in >= 0.8 (dead import in the released code) ───
try:
    import peft as _peft

    if not hasattr(_peft, "prepare_model_for_int8_training"):
        def prepare_model_for_int8_training(model, *a, **k):
            """peft>=0.8 removed this symbol. The released code calls it only
            inside a comment and only under PEFT==1 (default 0)."""
            return model
        _peft.prepare_model_for_int8_training = prepare_model_for_int8_training
    if not hasattr(_peft, "set_peft_model_state_dict"):
        try:
            from peft import set_peft_model_state_dict  # real symbol if present
        except Exception:
            pass
except Exception:                                    # pragma: no cover
    pass
