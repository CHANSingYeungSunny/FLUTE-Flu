"""architecture_contract.py — v3.15 architecture-storage contract.

WHY (D15): requiring `frozen_backbone_excluded == true` for EVERY architecture
is invalid. NLinear / DLinear / PatchTST / iTransformer contain NO pretrained
frozen backbone, so there is nothing to exclude; Gate 571855 failed those four
rows purely because of that universal predicate.

The contract is derived STRUCTURALLY, never from:
  * model-name substrings
  * compact compression ratio
  * parameter counts
  * "some bytes happened to be dropped"

Detection rule: a submodule is a pretrained backbone iff it is an instance of
`transformers.PreTrainedModel`. Every tensor living under such a module path is
backbone state; its expected frozen base is the immutable HF snapshot.

Contract fields per model/variant:
  model / variant identity
  has_pretrained_backbone            (bool)
  pretrained_backbone_module_paths   (list[str])
  base_model_id / revision           (str|None)
  frozen_backbone_key_count          (int)
  frozen_backbone_bytes_total        (int)
  storage_predicate_applicable       (== has_pretrained_backbone)

Runtime duplication evidence (per row, computed in compact_checkpoint):
  frozen_backbone_bytes_excluded            (unchanged backbone bytes dropped)
  unexpected_frozen_backbone_bytes_retained (backbone bytes kept that are NOT
                                             proven changed vs the base)
  no_frozen_backbone_duplication            (the invariant the Gate requires)
"""
from __future__ import annotations

import os

# Canonical frozen-contract file name inside a deployment root.
CONTRACT_REL = ("results", "v3_clean", "runs",
                "architecture_storage_contract.json")

CONTRACT_SOURCE = "runtime_module_introspection:transformers.PreTrainedModel"


def contract_path(deployment_root=None) -> str:
    from pathlib import Path
    root = deployment_root or os.environ.get("INNOVATION_DEPLOYMENT_ROOT")
    if not root:
        raise ValueError("INNOVATION_DEPLOYMENT_ROOT must be set")
    return str(Path(root).joinpath(*CONTRACT_REL))


# Namespaces whose classes are HuggingFace modelling code. `Conv1D` lives in
# transformers.pytorch_utils, NOT transformers.models.*, so both are needed.
HF_MODULE_NS = ("transformers.models.", "transformers.pytorch_utils.")

# Declared base-model identity attributes, searched on the model and on its
# nested modules (qwen_time_llm declares `text.model_id`).
IDENTITY_ATTRS = ("base_model_id", "model_id", "pretrained_model_name_or_path",
                  "hf_model_id", "llm_name", "text_model_id")


def _hf_module_paths(model) -> tuple:
    """Module paths implemented by HuggingFace modelling code.

    D15b: `isinstance(mod, PreTrainedModel)` alone is NOT sufficient. The MIFlu
    adapter (gpt2_miflu + its 6 ablations / 2 controls) decomposes GPT-2 into
    raw `transformers.models.gpt2.modeling_gpt2` components
    (GPT2Block/GPT2Attention/GPT2MLP) plus `transformers.pytorch_utils.Conv1D`,
    held under `inner.forecasting_llm`, with NO PreTrainedModel container.
    """
    try:
        from transformers import PreTrainedModel
    except Exception:                                          # noqa: BLE001
        PreTrainedModel = ()                                   # type: ignore
    paths = []
    for name, mod in model.named_modules():
        if not name:
            continue
        if PreTrainedModel and isinstance(mod, PreTrainedModel):
            paths.append(name)
            continue
        cls_mod = getattr(type(mod), "__module__", "") or ""
        if cls_mod.startswith(HF_MODULE_NS):
            paths.append(name)
    return tuple(sorted(paths))


def _common_ancestor(paths) -> list:
    """Longest shared dotted prefix of the given module paths."""
    if not paths:
        return []
    split = [p.split(".") for p in paths]
    n = 0
    while all(len(s) > n for s in split) and len({s[n] for s in split}) == 1:
        n += 1
    return [".".join(split[0][:n])] if n else []


def _dominant_cluster_ancestor(paths) -> list:
    """Common ancestor of the DOMINANT top-level cluster of `paths`.

    A single stray HF-namespace module elsewhere in the model must not be able
    to collapse the answer to empty (that was the D15b defect). Group by the
    first path component and pick the largest group; ties broken by the longest
    paths (backbones are the deep sub-trees).
    """
    if not paths:
        return []
    groups = {}
    for p in paths:
        groups.setdefault(p.split(".")[0], []).append(p)
    top = max(groups.items(),
              key=lambda kv: (len(kv[1]),
                              max(len(x.split(".")) for x in kv[1])))
    return _common_ancestor(top[1])


def declared_base_identity(model) -> str | None:
    """A base-model identity the architecture explicitly declares, if any."""
    for name, mod in model.named_modules():
        if name.count(".") > 3:
            continue
        for a in IDENTITY_ATTRS:
            v = getattr(mod, a, None)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def detect_backbone_modules(model) -> list:
    """Module paths that hold the pretrained HF backbone. Structural only.

    Container form  -> the PreTrainedModel module itself.
    Decomposed form -> the dominant HF cluster's common ancestor.
    Never uses model names, sizes, compression ratios or a generic kwarg.
    """
    containers = []
    try:
        from transformers import PreTrainedModel
        containers = [n for n, m in model.named_modules()
                      if n and isinstance(m, PreTrainedModel)]
    except Exception:                                          # noqa: BLE001
        pass
    if containers:
        containers.sort(key=len)
        return containers[:1]
    anc = _dominant_cluster_ancestor(_hf_module_paths(model))
    # The HF classes are the *groups* inside the backbone (e.g. `...blocks`),
    # while sibling pieces such as `wte`/`wpe`/`ln_f` are plain nn modules and
    # therefore never appear in `_hf_module_paths`. Step ONE level up so the
    # declared prefix covers the whole backbone sub-tree.
    if anc and "." in anc[0]:
        return [".".join(anc[0].split(".")[:-1])]
    return anc


def reference_key_mapping(model, ref: dict) -> dict:
    """Explicit HF<->project key mapping for the decomposed backbone.

    HF GPT-2 names its blocks `h.N`; the MIFlu project calls them `blocks.N`.
    This maps each reference key to the model key that actually corresponds,
    using the documented rename plus a **value+shape** confirmation so the
    mapping is proven rather than assumed.
    """
    sd = model.state_dict()
    by_val = {}
    for k, v in sd.items():
        by_val.setdefault((tuple(v.shape), str(v.dtype)), []).append(k)

    def _candidates(ref_key: str) -> list:
        cands = [ref_key, ref_key.replace(".h.", ".blocks."),
                 ref_key.replace("h.", "blocks.", 1)]
        out = []
        for c in cands:
            for mk in sd:
                if mk == c or mk.endswith("." + c):
                    out.append(mk)
        return out

    mapping, unmatched = {}, []
    for rk, rv in ref.items():
        hit = None
        for mk in _candidates(rk):
            if sd[mk].shape == rv.shape and torch_equal_safe(sd[mk], rv):
                hit = mk
                break
        if hit:
            mapping[rk] = hit
        else:
            unmatched.append(rk)
    return {"mapping": mapping, "n_mapped": len(mapping),
            "n_unmatched": len(unmatched), "unmatched_sample": unmatched[:8]}


def torch_equal_safe(a, b) -> bool:
    try:
        import torch
        return bool(torch.equal(a, b))
    except Exception:                                          # noqa: BLE001
        return False


def backbone_key_prefixes(model) -> tuple:
    return tuple(detect_backbone_modules(model))


def is_backbone_key(key: str, prefixes) -> bool:
    return bool(prefixes) and any(key == p or key.startswith(p + ".") for p in prefixes)


def base_model_identity(model, bkw: dict) -> tuple:
    """Immutable base-model identity, if the architecture declares one."""
    mid = bkw.get("model_id")
    if not mid:
        mid = getattr(model, "base_model_id", None) or \
            getattr(model, "model_id", None)
    rev = getattr(model, "base_model_revision", None)
    return (str(mid) if mid else None, str(rev) if rev else None)


def probe_contract(model, bkw: dict) -> dict:
    """Contract for an already-instantiated model (runs on a compute node)."""
    prefixes = backbone_key_prefixes(model)
    sd = model.state_dict()
    keys = [k for k in sd if is_backbone_key(k, prefixes)]
    nbytes = sum(sd[k].numel() * sd[k].element_size() for k in keys)
    mid, rev = base_model_identity(model, bkw)
    if not mid:
        mid = declared_base_identity(model)
    return {
        "has_pretrained_backbone": bool(prefixes),
        "pretrained_backbone_module_paths": list(prefixes),
        "base_model_id": mid,
        "base_model_revision": rev,
        "frozen_backbone_key_count": len(keys),
        "frozen_backbone_bytes_total": int(nbytes),
        "storage_predicate_applicable": bool(prefixes),
        "contract_source": CONTRACT_SOURCE,
    }


def evaluate_duplication(has_pretrained_backbone,
                         unexpected_retained_bytes: int,
                         reconstruction_exact: bool,
                         restoration_exact: bool) -> bool:
    """The applicability-aware invariant.

    no-backbone architectures pass VACUOUSLY, but only when exactness holds.
    backbone architectures pass only when no unchanged backbone state is kept.
    An UNKNOWN backbone state (None) fails closed.
    """
    if has_pretrained_backbone is None:
        return False                     # unknown contract -> fail closed
    if not (reconstruction_exact and restoration_exact):
        return False
    if not has_pretrained_backbone:
        return True                      # vacuous: no backbone exists
    return int(unexpected_retained_bytes) == 0


def storage_verdict(rep: dict, rest: dict, published: bool,
                    contained: bool) -> bool:
    """Single source of truth for the Gate's storage pass condition (D15).

    Deliberately independent of model-name substrings and of the compression
    ratio: the ratio is recorded for reporting only, never for deciding.
    """
    if not rep or not rest:
        return False
    n_missing = len(rest.get("missing_keys") or [])
    n_unexpected = len(rest.get("unexpected_keys") or [])
    return bool(rep.get("reconstruction_exact")
                and rest.get("restoration_exact")
                and n_missing == 0
                and n_unexpected == 0
                and published
                and contained
                and rep.get("no_frozen_backbone_duplication")
                # v3.16: canonical tensor-semantic identity must hold
                and rest.get("canonical_invariant_vs_durable", True))
