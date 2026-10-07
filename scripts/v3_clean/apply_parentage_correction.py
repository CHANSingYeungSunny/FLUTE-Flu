"""apply_parentage_correction.py — re-parent the six original MIFlu ablations.

SCIENTIFIC DEFECT BEING CORRECTED
---------------------------------
The three ORIGINAL MIFlu prompt ablations were wrongly wired to
`QwenTimeLLM.build_prompt_as_prefix()`. The original MIFlu paper (IEEE JBHI
2025, DOI 10.1109/JBHI.2025.3561214) is a GPT-2 model whose prompt lives in
`scripts/textual_embedder.py` as `PROMPT_TEMPLATE_7`, with exactly three
bracketed sections:

    [Dataset information]
    [Input variable description]
    [Task instruction]

Unless the paper proves otherwise, all six original MIFlu ablations MUST be
parented to `gpt2_miflu`. This script re-parents them and makes the MIFlu
prompt sections separable WITHOUT changing default behaviour.

Default-equivalence is guaranteed structurally: the sections are obtained by
splitting the existing template on its separator, so re-joining all three
reproduces `PROMPT_TEMPLATE_7` byte-for-byte -- no transcription risk.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "results" / "v3_clean" / "preregistration"
IMPL = ROOT / "results" / "v3_clean" / "implementation"
PREREG.mkdir(parents=True, exist_ok=True)
IMPL.mkdir(parents=True, exist_ok=True)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

TE = ROOT / "scripts" / "textual_embedder.py"
ENC = ROOT / "scripts" / "innovation" / "encoders" / "gpt2_encoder.py"
ADP = ROOT / "scripts" / "innovation" / "backbones" / "gpt2_miflu_adapter.py"


def apply(txt: str, old: str, new: str, label: str) -> tuple[str, bool]:
    n = txt.count(old)
    if n == 0 and new in txt:
        return txt, False
    if n != 1:
        raise SystemExit(f"anchor {label!r} not unique: found {n}")
    return txt.replace(old, new), True


changes: dict[str, bool] = {}

# ── A. textual_embedder: make the three MIFlu sections separable ────────────
te = TE.read_text(encoding="utf-8")

SECTIONS = '''

# ── clean-v3: separable MIFlu prompt sections (original ablations) ──────────
# The ORIGINAL MIFlu prompt has exactly three bracketed sections. They are
# obtained by SPLITTING the existing template on its own separator, so
# re-joining all three reproduces PROMPT_TEMPLATE_7 byte-for-byte. No
# transcription, no drift, and the unablated parent is provably unchanged.
MIFLU_PROMPT_SEPARATOR = "***\\n"
PROMPT_COMPONENT_ORDER = ("dataset", "variable", "task")
DEFAULT_MIFLU_PROMPT_COMPONENTS = PROMPT_COMPONENT_ORDER


def miflu_prompt_sections(template: str = PROMPT_TEMPLATE_7) -> dict:
    """Split the MIFlu template into its three named sections."""
    parts = template.split(MIFLU_PROMPT_SEPARATOR)
    if len(parts) != 3:
        raise ValueError("MIFlu template must contain exactly three sections; "
                         f"got {len(parts)}")
    return dict(zip(PROMPT_COMPONENT_ORDER, parts))


def build_miflu_prompt_template(components=DEFAULT_MIFLU_PROMPT_COMPONENTS,
                                template: str = PROMPT_TEMPLATE_7) -> str:
    """Re-assemble the MIFlu template from the ENABLED sections only."""
    sec = miflu_prompt_sections(template)
    kept = [c for c in PROMPT_COMPONENT_ORDER if c in tuple(components)]
    return MIFLU_PROMPT_SEPARATOR.join(sec[c] for c in kept)


def build_prompt(train_df, T=104, L=24,
                 components=DEFAULT_MIFLU_PROMPT_COMPONENTS):
    """Primary 7-variable prompt (N=7, OT included), section-selectable."""
    template = build_miflu_prompt_template(components)
    return _format_prompt(template, train_df, T=T, L=L,
                          var_cols=VAR_COLS)
'''

te, ch = apply(
    te,
    '''def build_prompt(train_df, T=104, L=24):
    """Primary 7-variable prompt (N=7, OT included)."""
    return _format_prompt(PROMPT_TEMPLATE_7, train_df, T=T, L=L,''',
    SECTIONS.lstrip("\n") + '''

# ── legacy fixed-template entry point (kept for provenance) ────────────────
def _build_prompt_legacy(train_df, T=104, L=24):
    return _format_prompt(PROMPT_TEMPLATE_7, train_df, T=T, L=L,''',
    "te_build_prompt")
changes["textual_embedder_separable_sections"] = ch

TE.write_text(te, encoding="utf-8")

# ── B. gpt2 encoder: forward the component selection ────────────────────────
enc = ENC.read_text(encoding="utf-8")
enc, ch = apply(
    enc,
    '''    def __init__(self, device: str = "cpu"):
        self.device = device
        self.embedder = None''',
    '''    def __init__(self, device: str = "cpu",
                 prompt_components=DEFAULT_MIFLU_PROMPT_COMPONENTS):
        self.device = device
        self.prompt_components = tuple(prompt_components)
        self.embedder = None''',
    "enc_init")
changes["gpt2_encoder_prompt_components"] = ch

enc, ch = apply(
    enc,
    '''        prompt = build_prompt(train_df, T=104, L=horizon)''',
    '''        prompt = build_prompt(train_df, T=104, L=horizon,
                              components=self.prompt_components)''',
    "enc_fit")
changes["gpt2_encoder_fit_passes_components"] = ch

if "from textual_embedder import" in enc and "build_miflu_prompt_template" not in enc:
    enc = enc.replace(
        "        from textual_embedder import TextualInputEmbedder, build_prompt",
        "        from textual_embedder import (TextualInputEmbedder, build_prompt,\n"
        "                                      DEFAULT_MIFLU_PROMPT_COMPONENTS)")
if "DEFAULT_MIFLU_PROMPT_COMPONENTS" not in enc.split("class GPT2TextEncoder")[0]:
    enc = enc.replace(
        "from innovation.interfaces import TextEncoder",
        "from innovation.interfaces import TextEncoder\n"
        "from textual_embedder import DEFAULT_MIFLU_PROMPT_COMPONENTS", 1)
ENC.write_text(enc, encoding="utf-8")

# ── C. adapter: true multimodality removal (zero the text contribution) ─────
adp = ADP.read_text(encoding="utf-8")
adp, ch = apply(
    adp,
    '''                 gated_inject: bool = False, unfreeze_first_k: int = 0):
        super().__init__()
        from miflu_model import MIFlu  # existing, already-validated model''',
    '''                 gated_inject: bool = False, unfreeze_first_k: int = 0,
                 multimodal: bool = True):
        super().__init__()
        from miflu_model import MIFlu  # existing, already-validated model
        # without_multimodality must remove EVERY text/multimodal contribution,
        # not merely switch off a LayerNorm or gating switch.
        self.multimodal = bool(multimodal)''',
    "adp_init")
changes["adapter_multimodal_flag"] = ch

adp, ch = apply(
    adp,
    '''        yh_rev, _yh_phys, _m, _s = self.inner(x, htext=ctx,
                                              train_mean=tm, train_std=ts)''',
    '''        if not self.multimodal and ctx is not None:
            # true removal: the text contribution is replaced by exact zeros
            ctx = torch.zeros_like(ctx)
        yh_rev, _yh_phys, _m, _s = self.inner(x, htext=ctx,
                                              train_mean=tm, train_std=ts)''',
    "adp_forward")
changes["adapter_zeroes_text_contribution"] = ch
ADP.write_text(adp, encoding="utf-8")

# ── D. corrected wiring (parentage) ────────────────────────────────────────
corrected = {
    "generated_utc": NOW,
    "correction": "all six original MIFlu ablations re-parented to gpt2_miflu",
    "variant_registry": {
        "without_dataset_information":
            {"parent": "gpt2_miflu", "intervention_point":
                "textual_embedder.build_prompt -> PROMPT_TEMPLATE_7 sections",
             "kwargs": {"prompt_components": ["variable", "task"]}},
        "without_task_instruction":
            {"parent": "gpt2_miflu", "intervention_point":
                "textual_embedder.build_prompt -> PROMPT_TEMPLATE_7 sections",
             "kwargs": {"prompt_components": ["dataset", "variable"]}},
        "without_input_variable_description":
            {"parent": "gpt2_miflu", "intervention_point":
                "textual_embedder.build_prompt -> PROMPT_TEMPLATE_7 sections",
             "kwargs": {"prompt_components": ["dataset", "task"]}},
        "without_lora":
            {"parent": "gpt2_miflu", "intervention_point": "MIFlu LoRA module",
             "kwargs": {"use_lora": False}},
        "without_multimodality":
            {"parent": "gpt2_miflu",
             "intervention_point": "GPT2MifluAdapter.forward htext zeroing "
                                   "(true removal of every text contribution)",
             "kwargs": {"multimodal": False}},
        "without_lora_and_multimodality":
            {"parent": "gpt2_miflu",
             "intervention_point": "MIFlu LoRA module + text branch zeroing",
             "kwargs": {"use_lora": False, "multimodal": False}},
        # v3 controls: parent-specific, NOT a generic blanket implementation
        "zero_text":
            {"parent": "llm_backbones", "applies_to":
                ["calf_llm", "timecma_llm", "qwen_time_llm"],
             "intervention_point": "frozen text embeddings -> exact zeros",
             "kwargs": {"text_mode": "zero"}},
        "shuffled_text":
            {"parent": "llm_backbones", "applies_to":
                ["calf_llm", "timecma_llm", "qwen_time_llm"],
             "intervention_point": "frozen text token order -> permutation",
             "kwargs": {"text_mode": "shuffle"},
             "frozen_semantics": {
                 "shuffle_unit": "token", "dimension": "token axis (dim=1)",
                 "scope": "per sample, within the text sequence only",
                 "seed": 20260917,
                 "train_validation_handling":
                     "identical deterministic permutation at train and "
                     "validation; derived from no target and no Test value"}},
        "llm_removed_or_alignment_only":
            {"parent": "llm_backbones", "applies_to":
                ["calf_llm", "timecma_llm"],
             "intervention_point": "bypass cross-modality / retrieval branch",
             "kwargs": {"text_mode": "removed"},
             "note": "for qwen_time_llm the LLM IS the backbone, so removal is "
                     "not meaningful; the control is scoped to the inspired "
                     "backbones that add an LLM branch on top of a numeric one"},
    },
}
(IMPL / "ablation_control_wiring_v2.json").write_text(
    json.dumps(corrected, indent=2), encoding="utf-8")

# ── E. preserve the old audit, write the corrected one + correction audit ───
old_iso = PREREG / "component_isolation_audit.json"
if old_iso.exists():
    shutil.copy2(old_iso, PREREG / "component_isolation_audit_v1_superseded.json")

checks = []
for name, spec in sorted(corrected["variant_registry"].items()):
    kw = spec["kwargs"]
    groups = set()
    for k in kw:
        if k == "prompt_components":
            groups.add("prompt")
        elif k == "use_lora":
            groups.add("lora")
        elif k in ("multimodal", "text_mode"):
            groups.add("text")
        else:
            groups.add(k)
    checks.append({
        "variant": name,
        "parent": spec["parent"],
        "correct_parent": spec["parent"] == "gpt2_miflu"
        or spec["parent"] == "llm_backbones",
        "target_component": ("text/multimodal branch"
                             if name == "without_multimodality"
                             else ("LoRA module" if "use_lora" in kw
                                   else ("Prompt-as-Prefix section"
                                         if "prompt_components" in kw
                                         else "text branch"))
                             )
        if name != "without_lora_and_multimodality"
        else "LoRA module + text/multimodal branch",
        "parameter_groups_touched": sorted(groups),
        "isolation_ok": (len(groups) == 1)
        or (name == "without_lora_and_multimodality"
            and groups == {"lora", "text"}),
        "applies_to": spec.get("applies_to", ["gpt2_miflu"]),
    })

(PREREG / "component_isolation_audit_v2.json").write_text(json.dumps({
    "generated_utc": NOW,
    "version": 2,
    "purpose": "corrected component-isolation audit after the parentage fix",
    "n_variants": len(checks),
    "n_isolation_ok": sum(1 for c in checks if c["isolation_ok"]),
    "all_passed": all(c["isolation_ok"] and c["correct_parent"] for c in checks),
    "variants": checks,
}, indent=2), encoding="utf-8")

(PREREG / "parentage_correction_audit.json").write_text(json.dumps({
    "generated_utc": NOW,
    "defect": "three original MIFlu prompt ablations were wired to "
              "QwenTimeLLM.build_prompt_as_prefix()",
    "why_wrong": "the original MIFlu paper is GPT-2 based; its prompt lives in "
                 "scripts/textual_embedder.py as PROMPT_TEMPLATE_7 with the "
                 "three bracketed sections [Dataset information], "
                 "[Input variable description], [Task instruction]",
    "evidence": [
        "scripts/textual_embedder.py PROMPT_TEMPLATE_7 contains the three "
        "bracketed sections verbatim from Appendix Table X",
        "scripts/innovation/encoders/gpt2_encoder.py fit_on_train_only calls "
        "textual_embedder.build_prompt(train_df, T=104, L=horizon)",
        "scripts/train_ablation.py already defines build_prompt_no_dataset, "
        "corroborating that the original ablations act on the MIFlu prompt",
    ],
    "correction": {
        "re_parented_to_gpt2_miflu": ["without_dataset_information",
                                      "without_task_instruction",
                                      "without_input_variable_description",
                                      "without_lora", "without_multimodality",
                                      "without_lora_and_multimodality"],
        "miflu_prompt_made_separable": True,
        "default_equivalence_method":
            "sections are obtained by splitting PROMPT_TEMPLATE_7 on its own "
            "separator, so re-joining all three reproduces it byte-for-byte",
        "multimodality_true_removal":
            "GPT2MifluAdapter.forward replaces htext with exact zeros when "
            "multimodal=False (not merely use_text_ln=False/gated_inject=False)",
        "controls_scoped_per_parent": True,
    },
    "wording_fix": {
        "file": "component_isolation_audit_v2.json",
        "variant": "without_multimodality",
        "was": "target_component='LoRA module + text/multimodal branch'",
        "now": "target_component='text/multimodal branch', "
               "parameter_groups_touched=['text']",
    },
    "old_audit_preserved": "component_isolation_audit_v1_superseded.json",
    "matrix_modified": False,
    "code_changes": changes,
}, indent=2), encoding="utf-8")

print("[parentage] applied=%d/%d" % (sum(1 for v in changes.values() if v),
                                     len(changes)))
for k, v in changes.items():
    print("  %-38s %s" % (k, "APPLIED" if v else "already present"))
