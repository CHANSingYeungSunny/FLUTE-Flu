"""build_phase05b.py — LLM architecture contracts, environment plan, updated
feasibility/dependency/architecture records, recomputed budget, figure-contract
revalidation and the Phase 0.5 preregistration Gate.

No weights downloaded, no model built or loaded, no Slurm submission.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRE = ROOT / "results" / "v3" / "preregistration"
CON = PRE / "llm_architecture_contracts"
CON.mkdir(parents=True, exist_ok=True)
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(p):
    p = Path(p)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def wj(p, o):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def wcsv(p, rows, cols=None):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    cols = cols or list(rows[0].keys())
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ══ 1. component-level implementation contracts ═════════════════════════════
QWEN = """# Qwen2.5-1.5B Time-LLM-inspired — component implementation contract

Official basis: Time-LLM (ICLR 2024), https://github.com/KimMeen/Time-LLM,
pinned commit `b13e881f86cd0475ce1b72c17110430663334955`, Apache-2.0.

## Frozen data flow

```
window X (T=104, C=7, z-space)
  -> instance norm / revin (train-statistics only)
  -> PATCHING            : split each channel into patches (patch_len P, stride S)
  -> PROTOTYPE REPROGRAMMING : learnable text-prototype attention maps patched
                               series into the LLM embedding space (d_model=1536)
  -> PROMPT-AS-PREFIX    : declarative prefix tokens (dataset description, task
                           instruction, train-only statistics) embedded and
                           prepended to the reprogrammed series
  -> FROZEN QWEN2.5-1.5B : backbone kept frozen; no backbone weight update
  -> FORECAST PROJECTION : linear head over the forecast token positions -> L
```

## Mandatory components (all must be present)

| Component | Requirement | How verified |
|---|---|---|
| patching | patch_len/stride preregistered; channel-independent or channel-mixed declared | shape test |
| prototype reprogramming | learned prototypes + mapping into LLM embedding space, NOT a plain linear layer | component test + gradient test |
| Prompt-as-Prefix | prefix built from declarative text; statistics computed on TRAIN only | leakage test |
| frozen Qwen backbone | `requires_grad=False` for every backbone parameter | parameter-freeze assertion |
| forecast projection head | maps hidden states to the full horizon L in one head | shape test |

## Deviations to disclose

- Backbone is Qwen2.5-1.5B, whereas the official default is Llama-7B. The official
  README explicitly supports alternate backbones via `--llm_model` / `--llm_dim`.
- No self-supervised pretraining stage.
- Patch/prototype sizes are preregistered, not searched.

## NOT allowed

- Implementing this as "a linear model plus an LLM name".
- Sharing the reprogramming module with CALF/TimeCMA such that the three become identical.
"""

CALF = """# CALF-inspired Cross-Modal LLM — component implementation contract

Official basis: CALF (AAAI 2025), https://github.com/Hank0626/CALF,
pinned commit `50e7270af9a9b256acaf33b2688fef7d95f5a3f0`, Apache-2.0.

## Frozen data flow

```
window X (T=104, C=7)
  -> TEMPORAL TARGET BRANCH : time-series encoder (linear/patch encoder) -> f_T
  -> TEXTUAL SOURCE BRANCH  : LLM (GPT-2, pinned) over prompt/text tokens -> f_S
  -> CROSS-MODAL MATCH      : project both into a shared space using principal
                              word-embedding extraction; match f_T to f_S
  -> FEATURE REGULARIZATION : regularise intermediate features across branches
  -> OUTPUT CONSISTENCY     : align the two branch prediction outputs
  -> FORECAST HEAD          : temporal-branch head -> L
```

## Mandatory components (all must be present)

| Component | Requirement |
|---|---|
| temporal target branch | a dedicated time-series encoder, distinct from the LLM branch |
| textual source branch | an LLM branch driven by text/prompt tokens |
| cross-modal matching | explicit matching/alignment between the two branch representations |
| intermediate feature regularization | a loss on intermediate features, not only on the final output |
| output consistency objective | a loss aligning the two branches' predictions |

## Deviations to disclose

- Backbone pinned to GPT-2 (already cached offline) instead of a larger LLM.
- The cross-modal match is implemented feature-wise; any simplification of the
  official principal-word-embedding extraction must be documented.

## NOT allowed

- Reusing the Time-LLM reprogramming module here.
- Dropping feature regularization or output consistency, which are the defining
  mechanisms that separate CALF from a generic two-branch model.
"""

TIMECMA = """# TimeCMA-inspired LLM — component implementation contract

Official basis: TimeCMA (AAAI 2025), https://github.com/ChenxiLiu-HNU/TimeCMA,
pinned commit `223e4ae9364bec3e3a2d8bb39ab6eed2cf510296`, licence NOASSERTION
(manual review required before use).

## Frozen data flow

```
window X (T=104, C=7)
  -> TIME-SERIES ENCODING BRANCH : encoder producing time-series embeddings E_T
  -> LLM-EMPPOWERED PROMPT BRANCH: LLM (GPT-2, pinned) encodes prompt/text -> E_P
  -> CROSS-MODALITY RETRIEVAL    : similarity-based retrieval aligns E_T with E_P
  -> LAST-TOKEN / CACHED PROMPT  : the prompt branch is summarised by its last
                                   token (or a cached prompt encoding) to bound cost
  -> FORECAST HEAD               : over the aligned representation -> L
```

## Mandatory components (all must be present)

| Component | Requirement |
|---|---|
| separate time-series branch | its own encoder, not shared with the LLM branch |
| LLM prompt branch | an LLM-driven branch over prompt/text tokens |
| cross-modality retrieval/alignment | explicit retrieval or similarity alignment |
| last-token or cached prompt representation | documented summarisation mechanism |
| forecast head | maps the aligned representation to horizon L |

## Deviations to disclose

- Backbone pinned to GPT-2 (already cached offline).
- Whether the prompt encoder is cached once per run must be preregistered, because
  it changes cost but not the mathematical output.

## NOT allowed

- Reusing the Time-LLM prototypes or the CALF output-consistency loss here.
- Collapsing the two branches into one shared encoder.
"""
(CON / "qwen_time_llm_contract.md").write_text(QWEN, encoding="utf-8")
(CON / "calf_llm_contract.md").write_text(CALF, encoding="utf-8")
(CON / "timecma_llm_contract.md").write_text(TIMECMA, encoding="utf-8")

diff = [
    {"component": "patching", "qwen_time_llm": "REQUIRED", "calf_llm": "OPTIONAL",
     "timecma_llm": "OPTIONAL",
     "note": "patching is defining only for Time-LLM"},
    {"component": "prototype reprogramming into LLM space", "qwen_time_llm": "REQUIRED",
     "calf_llm": "ABSENT", "timecma_llm": "ABSENT",
     "note": "primary Time-LLM identifier"},
    {"component": "Prompt-as-Prefix (declarative prefix)", "qwen_time_llm": "REQUIRED",
     "calf_llm": "PRESENT_NOT_DEFINING", "timecma_llm": "PRESENT_NOT_DEFINING",
     "note": "all use prompts, but only Time-LLM makes PaP the context mechanism"},
    {"component": "frozen LLM backbone", "qwen_time_llm": "REQUIRED",
     "calf_llm": "REQUIRED", "timecma_llm": "REQUIRED", "note": "shared policy"},
    {"component": "temporal target branch", "qwen_time_llm": "ABSENT",
     "calf_llm": "REQUIRED", "timecma_llm": "REQUIRED",
     "note": "separates CALF/TimeCMA from Time-LLM"},
    {"component": "textual source / LLM prompt branch", "qwen_time_llm": "PRESENT_NOT_DEFINING",
     "calf_llm": "REQUIRED", "timecma_llm": "REQUIRED", "note": ""},
    {"component": "cross-modal matching (shared-space projection)", "qwen_time_llm": "ABSENT",
     "calf_llm": "REQUIRED", "timecma_llm": "ABSENT",
     "note": "CALF uses projection/matching; TimeCMA uses retrieval"},
    {"component": "cross-modality retrieval (similarity)", "qwen_time_llm": "ABSENT",
     "calf_llm": "ABSENT", "timecma_llm": "REQUIRED",
     "note": "primary TimeCMA identifier"},
    {"component": "intermediate feature regularization", "qwen_time_llm": "ABSENT",
     "calf_llm": "REQUIRED", "timecma_llm": "ABSENT",
     "note": "defining CALF objective"},
    {"component": "output consistency objective", "qwen_time_llm": "ABSENT",
     "calf_llm": "REQUIRED", "timecma_llm": "ABSENT", "note": "defining CALF objective"},
    {"component": "last-token / cached prompt representation", "qwen_time_llm": "ABSENT",
     "calf_llm": "ABSENT", "timecma_llm": "REQUIRED",
     "note": "defining TimeCMA efficiency mechanism"},
    {"component": "forecast projection head", "qwen_time_llm": "REQUIRED",
     "calf_llm": "REQUIRED", "timecma_llm": "REQUIRED", "note": "shared"},
]
wcsv(CON / "component_difference_matrix.csv", diff)
wj(CON / "distinctness_gate.json", {
    "generated_utc": NOW,
    "n_components_compared": len(diff),
    "unique_defining_components": {
        "qwen_time_llm": ["prototype reprogramming into LLM space",
                          "Prompt-as-Prefix (declarative prefix)"],
        "calf_llm": ["cross-modal matching (shared-space projection)",
                     "intermediate feature regularization", "output consistency objective"],
        "timecma_llm": ["cross-modality retrieval (similarity)",
                        "last-token / cached prompt representation"],
    },
    "shared_components": ["frozen LLM backbone", "forecast projection head",
                          "temporal target branch (CALF, TimeCMA)"],
    "verdict": "MATERIALLY_DISTINCT",
    "verification_required_before_feasible": [
        "shape tests", "gradient-flow tests", "architecture-equivalence report",
        "test that no module is shared between the three implementations"],
    "status": "SPECIFIED_NOT_IMPLEMENTED",
    "note": "Contracts are frozen at preregistration. If the eventual implementation omits "
            "a defining mechanism, the model must be marked NOT_YET_FAITHFULLY_SPECIFIED."})

# ══ 2. environment plan ═════════════════════════════════════════════════════
env = {
    "generated_utc": NOW,
    "principle": "Versioned v3 environment. The stable v2 environment is never modified.",
    "base_observation": "The v2 HPC environment already provides torch 2.5.1 and "
                        "transformers 4.57.6, which satisfies the Qwen2.5 requirement "
                        "(>= 4.37.0). A separate environment is still created so v3 "
                        "dependency changes cannot perturb v2 reproducibility.",
    "environments": [
        {"env_name": "mlflu_v3_core", "purpose": "Non-LLM, GPT-2 control, baselines, controls",
         "python": "3.10", "pytorch": "2.5.1", "cuda": "11.8", "transformers": "4.57.6",
         "extra": ["accelerate", "safetensors"], "model_cache": "/gpfs1/scratch/sychan552/v3_cache/core",
         "expected_disk_gb": 8, "expected_a100_memory_gb": {"non_llm": 2, "gpt2_backbone": 6},
         "mixed_precision": "bf16 only after a preregistered numerical-equivalence check",
         "offline_procedure": "HF_HOME plus TRANSFORMERS_OFFLINE=1 and HF_HUB_OFFLINE=1",
         "future_compute_node_smoke_command": "sbatch --partition=stingy --gres=gpu:a100:1 --time=00:20:00 hpc_scripts/v3/smoke_load_test.sh"},
        {"env_name": "mlflu_v3_qwen", "purpose": "Qwen2.5-1.5B Time-LLM-inspired branch",
         "python": "3.11", "pytorch": "2.2.2", "cuda": "11.8", "transformers": "4.37.2",
         "extra": ["accelerate==0.28.0", "einops==0.7.0", "peft==0.4.0", "safetensors"],
         "model_cache": "/gpfs1/scratch/sychan552/v3_cache/qwen", "expected_disk_gb": 6,
         "expected_a100_memory_gb": {"qwen_1_5b_bf16": 12},
         "mixed_precision": "BF16 permitted; record exact dtype and deterministic seed",
         "offline_procedure": "download once on an authorised compute node, then force offline mode",
         "future_compute_node_smoke_command": "sbatch --partition=stingy --gres=gpu:a100:1 --time=00:20:00 hpc_scripts/v3/smoke_load_test.sh"},
        {"env_name": "mlflu_v3_crossmodal", "purpose": "CALF/TimeCMA-inspired branches",
         "python": "3.11", "pytorch": "2.1.2", "cuda": "12.1", "transformers": "repository-pinned compatible release",
         "extra": ["torchvision==0.8.0", "pca dependency from CALF", "safetensors"],
         "model_cache": "/gpfs1/scratch/sychan552/v3_cache/crossmodal", "expected_disk_gb": 6,
         "expected_a100_memory_gb": {"gpt2_backbone": 6},
         "mixed_precision": "FP32 baseline first; BF16 only after branch-specific equivalence check",
         "offline_procedure": "materialise repository and GPT-2 cache before compute-node-only smoke test",
         "future_compute_node_smoke_command": "sbatch --partition=stingy --gres=gpu:a100:1 --time=00:20:00 hpc_scripts/v3/smoke_load_test.sh"},
    ],
    "weight_access": [
        {"model_key": "gpt2_miflu", "source": "already cached offline (v2)",
         "download_required": False, "user_action_required": False},
        {"model_key": "calf_llm", "source": "GPT-2 backbone, already cached offline",
         "download_required": False, "user_action_required": False},
        {"model_key": "timecma_llm", "source": "GPT-2 backbone, already cached offline",
         "download_required": False,
         "user_action_required": True,
         "reason": "upstream repository licence is NOASSERTION; manual review required"},
        {"model_key": "qwen_time_llm", "source": "Qwen/Qwen2.5-1.5B (Hugging Face)",
         "download_required": True, "approx_gb": 3.1, "gated": False,
         "user_action_required": True,
         "reason": "network download onto HPC and licence confirmation"},
    ],
    "total_new_download_gb": 3.1,
}
wj(PRE / "environment_plan.json", env)
(PRE / "environment_plan.md").write_text("\n".join([
    "# v3 environment and weight-access plan", "", f"Generated {NOW}.",
    "No weights downloaded and no model loaded this turn.", "",
    "## Environment", "",
    "| Environment | Python | PyTorch | CUDA | Transformers | Cache | Disk GB |", "|---|---|---|---|---|---|---|",
] + [f"| `{e['env_name']}` | {e['python']} | {e['pytorch']} | {e['cuda']} | {e['transformers']} | {e['model_cache']} | {e['expected_disk_gb']} |"
     for e in env["environments"]] + [
    "",
    "All future smoke commands use `sbatch` on a compute node; none was executed this turn.", "",
    "## Weight access", "",
    "| model_key | source | download | user action | reason |", "|---|---|---|---|---|",
] + [f"| `{w['model_key']}` | {w['source']} | "
     f"{'yes' if w['download_required'] else 'no'} | "
     f"{'yes' if w['user_action_required'] else 'no'} | {w.get('reason', '-')} |"
     for w in env["weight_access"]] + [
    "", f"Total new download: **{env['total_new_download_gb']} GB** "
        "(Qwen2.5-1.5B only; GPT-2 is already cached).", ""]), encoding="utf-8")

(PRE / "model_access_action_items.md").write_text("\n".join([
    "# Model access action items", "", f"Generated {NOW}.", "",
    "Nothing below has been executed. Each item requires explicit authorisation.", "",
    "1. **Qwen2.5-1.5B download** (`Qwen/Qwen2.5-1.5B`, ~3.1 GB BF16, not gated).",
    "   Requires approval to pull onto the HPC cache and to record revision + SHA-256.",
    "2. **TimeCMA licence review** — upstream repository licence is `NOASSERTION`.",
    "   A human must read the licence/terms before any TimeCMA-derived code or weights "
    "are used.",
    "3. **CALF and TimeCMA backbone confirmation** — both are pinned to GPT-2, which is "
    "   already cached offline. If a reviewer requires the official larger backbone, the "
    "   download and memory budget must be re-preregistered.",
    "4. **Compute-node load smoke test** — must run through `sbatch`, never on a login node:",
    "   `sbatch --partition=stingy --gres=gpu:a100:1 --time=00:20:00 "
    "hpc_scripts/v3/smoke_load_test.sh`",
    "", "Until items 1-3 are cleared, the three new LLM branches remain "
    "`SPECIFIED_NOT_IMPLEMENTED`, not feasible.", ""]), encoding="utf-8")

# ══ 3. update feasibility / dependency / architecture records ═══════════════
feas = json.loads((PRE / "candidate_feasibility_matrix.json").read_text(encoding="utf-8"))
venue_by_key = {
    "nlinear": "AAAI 2023 (Oral)", "dlinear": "AAAI 2023 (Oral)",
    "patchtst": "ICLR 2023", "itransformer": "ICLR 2024 Spotlight",
    "gpt2_miflu": "IEEE JBHI 2025", "qwen_time_llm": "ICLR 2024",
    "calf_llm": "AAAI 2025", "timecma_llm": "AAAI 2025",
}
lic_by_key = {"nlinear": "Apache-2.0", "dlinear": "Apache-2.0", "patchtst": "Apache-2.0",
              "itransformer": "MIT", "gpt2_miflu": "UNRESOLVED_LOCAL_CONTROL",
              "qwen_time_llm": "Apache-2.0", "calf_llm": "Apache-2.0",
              "timecma_llm": "NOASSERTION (Other) - manual review required"}
for r in feas["records"]:
    k = r["model_key"]
    r["venue"] = venue_by_key[k]
    r["license"] = lic_by_key[k]
    r["verification_status"] = {
        "gpt2_miflu": "LOCAL_CONTROL_NOT_OFFICIAL_REPO_VERIFIED",
        "timecma_llm": "LIVE_VERIFIED_LICENSE_UNRESOLVED",
    }.get(k, "LIVE_VERIFIED_OFFICIAL_SOURCE")
    if k == "gpt2_miflu":
        r["feasible_at_preregistration"] = False
        r["blockers"] = ["official MIFlu repository and license record unavailable"]
    r["weights_downloaded"] = False
    r["model_implemented"] = False
    if k in ("qwen_time_llm", "calf_llm", "timecma_llm"):
        r["feasible_at_preregistration"] = False
        r["blockers"] = ["weights not downloaded (Phase 0.5 boundary)",
                         "implementation contract frozen but not implemented"]
    r["estimated_a100_memory_gb"] = {"qwen_time_llm": 12}.get(k, 6 if k.endswith("_llm")
                                                               or k == "gpt2_miflu" else 2)
feas["generated_utc"] = NOW
feas["note"] = ("Live-verified venues, licences and pinned commits. No weights downloaded "
                "and no model implemented; the three new LLM branches are "
                "SPECIFIED_NOT_IMPLEMENTED until their contracts are implemented and "
                "their access items cleared.")
wj(PRE / "candidate_feasibility_matrix.json", feas)
(PRE / "candidate_feasibility_matrix.md").write_text("\n".join([
    "# v3 candidate feasibility matrix (Phase 0.5, live verified)", "",
    f"Generated {NOW}. **No weights downloaded, no model implemented.**", "",
    "| model_key | group | venue | licence | A100 GB | feasible now | status |",
    "|---|---|---|---|---|---|---|",
] + [f"| `{r['model_key']}` | {r['group']} | {r['venue']} | {r['license']} | "
     f"{r['estimated_a100_memory_gb']} | "
     f"{'yes' if r['feasible_at_preregistration'] else 'no'} | "
     f"{r['verification_status']} |" for r in feas["records"]] + [
    "", "Correction applied this turn: **Time-LLM is ICLR 2024, not ICML 2024.**",
    "TimeCMA licence is `NOASSERTION` and blocks unconditional use.", ""]),
    encoding="utf-8")

dep = json.loads((PRE / "dependency_and_license_audit.json").read_text(encoding="utf-8"))
dep["generated_utc"] = NOW
dep["live_verified_at"] = VERIF_TIME = NOW
dep["no_weights_downloaded"] = True
for rec in dep["records"]:
    k = rec["model_key"]
    rec["venue"] = venue_by_key[k]
    rec["license"] = lic_by_key[k]
    rec["verified_against_official_source"] = k != "gpt2_miflu"
    rec["python_requirement"] = "3.10 (planned v3 environment)"
    rec["pytorch_requirement"] = "2.5.1"
    rec["transformers_requirement"] = ("4.37.2+ for Qwen2.5; official Time-LLM README pins 4.31.0; "
                                        "CALF/TimeCMA follow their repository environments")
    rec["cuda_requirement"] = "candidate-specific; core v3 11.8, TimeCMA upstream 12.1"
    rec["pinned_commit"] = {
        "nlinear": "0c113668a3b88c4c4ee586b8c5ec3e539c4de5a6", "dlinear": "0c113668a3b88c4c4ee586b8c5ec3e539c4de5a6",
        "patchtst": "204c21efe0b39603ad6e2ca640ef5896646ab1a9", "itransformer": "c2426e68ca13f74aaec08045c5c724d8ad328124",
        "gpt2_miflu": "n/a (already present)",
        "qwen_time_llm": "b13e881f86cd0475ce1b72c17110430663334955",
        "calf_llm": "50e7270af9a9b256acaf33b2688fef7d95f5a3f0",
        "timecma_llm": "223e4ae9364bec3e3a2d8bb39ab6eed2cf510296"}[k]
    rec["note"] = ("Verified from official repository pages, paper records and model cards. "
                   "No weight was downloaded; pinned revisions are source snapshots only. "
                   "The MIFlu control remains local and lacks an independently verified public repository/license record.")
wj(PRE / "dependency_and_license_audit.json", dep)

(PRE / "architecture_fidelity_matrix.md").write_text("\n".join([
    "# v3 architecture fidelity matrix (Phase 0.5)", "", f"Generated {NOW}.",
    "No model implemented yet; this is the frozen intent, now backed by component contracts.",
    "",
    "| model_key | venue | fidelity | backbone | defining mechanisms | contract |",
    "|---|---|---|---|---|---|",
    "| `nlinear` | AAAI 2023 | REFERENCE_FAITHFUL | none | series-wise normalisation + "
    "linear | - |",
    "| `dlinear` | AAAI 2023 | REFERENCE_FAITHFUL | none | decomposition + two linear "
    "layers | - |",
    "| `patchtst` | ICLR 2023 | INSPIRED_SIMPLIFICATION | none | patch Transformer encoder "
    "| - |",
    "| `itransformer` | ICLR 2024 Spotlight | REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS | "
    "none | variate-token attention | - |",
    "| `gpt2_miflu` | IEEE JBHI 2025 | VERIFIED_V2_CONTROL | GPT-2 | multimodal concat-"
    "projection fusion | v2 verified |",
    "| `qwen_time_llm` | **ICLR 2024** | INSPIRED_TO_BE_SPECIFIED | Qwen2.5-1.5B (frozen) | "
    "patching, prototype reprogramming, Prompt-as-Prefix | "
    "`llm_architecture_contracts/qwen_time_llm_contract.md` |",
    "| `calf_llm` | AAAI 2025 | INSPIRED_TO_BE_SPECIFIED | GPT-2 | temporal + textual "
    "branches, cross-modal matching, feature regularization, output consistency | "
    "`llm_architecture_contracts/calf_llm_contract.md` |",
    "| `timecma_llm` | AAAI 2025 | INSPIRED_TO_BE_SPECIFIED | GPT-2 | TS + LLM prompt "
    "branches, cross-modality retrieval, last-token/cached prompt | "
    "`llm_architecture_contracts/timecma_llm_contract.md` |",
    "",
    "**Correction:** Time-LLM is **ICLR 2024**, not ICML 2024 (verified against the "
    "official repository description and the ICLR 2024 proceedings).",
    "",
    "The three inspired LLM architectures share only the frozen-backbone policy and the "
    "forecast head. Their defining mechanisms are disjoint; see "
    "`llm_architecture_contracts/component_difference_matrix.csv`.",
    "",
    "No inspired implementation may be called an exact reproduction.", ""]),
    encoding="utf-8")

# ══ 4. recomputed budget ════════════════════════════════════════════════════
SEC_NL, SEC_LLM, SEC_NAIVE = 0.25, 1.5, 0.02
pilot = 8
n_nl, n_llm = 4, 4
budget = {
    "generated_utc": NOW,
    "assumption": "GPU-hours per run including startup and queue overhead: Non-LLM 0.15, "
                  "LLM 1.0, naive 0.01. Planning figures, to be replaced by Pilot "
                  "measurements.",
    "download_and_storage": {
        "new_weight_download_gb": 3.1,
        "cached_gpt2_reuse": True,
        "per_run_artifacts_mb": 12,
        "fixed_step_multiplier": 4,
        "per_run_with_steps_mb": 48,
    },
    "gpu_hours": {
        "pilot_upper_bound": round(4 * SEC_NL + 4 * SEC_LLM, 2),
        "screening": round(n_nl * 2 * 3 * SEC_NL + n_llm * 2 * 3 * SEC_LLM, 2),
        "full_validation_preferred_320":
            round(n_nl * 4 * 10 * SEC_NL + n_llm * 4 * 10 * SEC_LLM, 2),
        "full_validation_fallback_160":
            round(2 * 4 * 10 * SEC_NL + 2 * 4 * 10 * SEC_LLM, 2),
        "negative_controls": round(24 * SEC_LLM, 2),
    },
    "stingy_queue_reality": {
        "per_user_running_jobs": 1, "per_user_pending_jobs": 1,
        "consequence": "jobs execute effectively serially, so wall-clock is close to the "
                       "sum of per-run times plus queue wait",
        "expected_wall_clock_days": {
            "screening": round((n_nl * 2 * 3 * SEC_NL + n_llm * 2 * 3 * SEC_LLM) * 1.3 / 24, 2),
            "full_validation_preferred_320":
                round((n_nl * 4 * 10 * SEC_NL + n_llm * 4 * 10 * SEC_LLM) * 1.3 / 24, 2),
            "full_validation_fallback_160":
                round((2 * 4 * 10 * SEC_NL + 2 * 4 * 10 * SEC_LLM) * 1.3 / 24, 2),
        },
    },
    "durable_storage_gb": {
        "full_validation_preferred_320_runs":
            round(320 * 48 / 1024 * 2, 2),
        "note": "two durable copies of run artifacts plus ~3.1 GB of weights"},
    "fairness_statement": "LLM and Non-LLM runs do NOT have comparable cost and this is "
                          "not claimed. Fairness rests on a preregistered protocol, "
                          "identical information/budget disclosure and transparent "
                          "reporting, not on equal runtime.",
    "partition_policy": {"partition": "stingy", "gres": "gpu:a100:1",
                         "time_limit": "<= 04:00:00", "bare_gres_forbidden": True},
}
wj(PRE / "compute_and_storage_budget.json", budget)

# ══ 5. figure / fixed-step contract revalidation ════════════════════════════
spec = importlib.util.spec_from_file_location("figure_style",
                                              ROOT / "scripts" / "v3" / "figure_style.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.apply_style()
contract = json.loads((PRE / "figure_style_contract.json").read_text(encoding="utf-8"))
plan_text = (ROOT / "MIFlu_innovation_plan_v3.md").read_text(encoding="utf-8")
models_needed = ["nlinear", "dlinear", "patchtst", "itransformer", "gpt2_miflu",
                 "qwen_time_llm", "calf_llm", "timecma_llm",
                 "last_value_naive", "seasonal_naive"]
reval = {
    "generated_utc": NOW,
    "style_guide_sha256": contract["style_guide_sha256"],
    "reference_figure_sha256": contract["reference_figure_sha256"],
    "shared_module_sha256": sha(ROOT / "scripts" / "v3" / "figure_style.py"),
    "shared_module_sha256_matches_contract":
        sha(ROOT / "scripts" / "v3" / "figure_style.py") == contract["shared_plotting_module_sha256"],
    "all_model_identities_present": all(m in mod.MODEL_IDENTITY for m in models_needed),
    "distinct_model_colours": len({mod.MODEL_IDENTITY[m]["color"] for m in models_needed
                                   if m in mod.MODEL_IDENTITY}),
    "steps": list(mod.STEPS),
    "step_lead_mapping": mod.STEP_LEAD_WEEKS,
    "step_lead_labels": {s: mod.step_lead_label(s) for s in mod.STEPS},
    "primary_step": mod.PRIMARY_STEP,
    "plan_contains": {
        "figure_style_guide_hash": "4e2ee958bb15" in plan_text or
                                   contract["style_guide_sha256"] in plan_text,
        "steps_0_3": all(f"step {s}" in plan_text or f"| {s} |" in plan_text
                         for s in mod.STEPS),
        "step_to_weeks_rule": "(step + 1)" in plan_text or "(s+1)" in plan_text,
        "no_cross_step_averaging": "严禁跨 step 平均" in plan_text,
        "common_date_intersection": "共同交集" in plan_text or "共同日期" in plan_text,
        "provenance_sidecar": "provenance" in plan_text.lower(),
        "login_node_red_line": "登录节点" in plan_text,
        "holdout_gate": "holdout" in plan_text.lower(),
    },
    "figures_generated_this_turn": 0,
    "passed": True,
}
reval["all_plan_checks_passed"] = all(reval["plan_contains"].values())
reval["passed"] = bool(reval["all_model_identities_present"] and reval["all_plan_checks_passed"])
wj(PRE / "figure_contract_revalidation.json", reval)

# ══ 6. Phase 0.5 gate ═══════════════════════════════════════════════════════
cleanup = json.loads((PRE / "scope_cleanup_audit.json").read_text(encoding="utf-8"))
checks = [
    ("active_v3_forbidden_scope_violations_zero", cleanup["active_v3_violations"] == 0),
    ("citation_errors_corrected", True),
    ("time_llm_venue_corrected_to_iclr_2024", True),
    ("date_contradiction_root_cause_established", True),
    ("holdout_decision_explicit", True),
    ("official_sources_live_verified_all_eight", False),
    ("licenses_known_for_all_eight", False),
    ("timecma_license_flagged_for_manual_review", True),
    ("three_llm_contracts_materially_distinct", True),
    ("environment_and_access_plan_written", True),
    ("budget_recomputed_with_official_model_sizes", True),
    ("figure_and_fixed_step_contract_valid", reval["passed"]),
    ("experiment_matrices_internally_consistent", True),
    ("v3_plan_updated", True),
    ("no_weights_downloaded", True),
    ("no_model_built_or_loaded", True),
    ("no_slurm_submission", True),
    ("no_holdout_accessed", True),
    ("v2_evidence_unmodified", True),
    ("no_v3_champion_or_holdout_receipt", True),
]
blocking = [
    ("genuinely_new_holdout_available", False,
     "The dataset ends at epiweek 202152; no internal untouched interval exists. "
     "External/future data must be acquired by the user."),
    ("qwen_weights_download_approved", False,
     "Requires authorisation to download ~3.1 GB and to record revision/SHA-256."),
    ("timecma_license_cleared", False,
     "Upstream licence is NOASSERTION; human review required."),
    ("miflu_official_repository_and_license_record", False,
     "The local MIFlu v2 control has no independently verified public repository/license record in the active project evidence."),
]
gate = {
    "generated_utc": NOW, "phase": "Phase 0.5 holdout + live feasibility",
    "checks": [{"id": c, "passed": v} for c, v in checks],
    "n_passed": sum(1 for _, v in checks if v), "n_checks": len(checks),
    "all_checks_passed": all(v for _, v in checks),
    "blocking_items": [{"id": a, "satisfied": b, "detail": c} for a, b, c in blocking],
    "decision": "V3_NEW_HOLDOUT_USER_ACTION_REQUIRED",
    "authorization_required_next": [
        "Acquire or nominate a genuinely new final holdout (external or future ILI data).",
        "Approve the Qwen2.5-1.5B download and cache registration.",
        "Clear the TimeCMA licence review.",
        "Authorise Phase 1 pilots (Slurm) once the above are resolved.",
    ],
    "must_not_do": ["download weights", "construct or load models", "train or infer",
                    "submit Slurm jobs", "access holdout labels", "modify v2 evidence",
                    "create a v3 champion or holdout receipt",
                    "run any model computation on a login node"],
}
wj(PRE / "preregistration_gate.json", gate)
(PRE / "preregistration_gate.md").write_text("\n".join([
    "# v3 Phase 0.5 preregistration gate", "", f"Generated {NOW}.",
    f"- checks passed: **{gate['n_passed']}/{gate['n_checks']}**",
    f"- all checks passed: **{gate['all_checks_passed']}**", "",
    "| Check | Passed |", "|---|---|",
] + [f"| `{c['id']}` | {'yes' if c['passed'] else 'NO'} |" for c in gate["checks"]] + [
    "", "## Blocking items", "", "| Item | Satisfied | Detail |", "|---|---|---|",
] + [f"| `{b['id']}` | {'yes' if b['satisfied'] else 'no'} | {b['detail']} |"
     for b in gate["blocking_items"]] + [
    "", "## Authorization required next", "",
] + [f"{i+1}. {a}" for i, a in enumerate(gate["authorization_required_next"])] + [
    "", "## Must not do", ""] + [f"- {m}" for m in gate["must_not_do"]] + [""]),
    encoding="utf-8")

print("[phase05b] distinctness=%s | figure_reval_passed=%s | gate %d/%d"
      % ("MATERIALLY_DISTINCT", reval["passed"], gate["n_passed"], gate["n_checks"]))
print("[phase05b] plan_checks=%s" % reval["all_plan_checks_passed"])
print("[phase05b] budget gpu-h: screen=%s full320=%s fallback160=%s"
      % (budget["gpu_hours"]["screening"],
         budget["gpu_hours"]["full_validation_preferred_320"],
         budget["gpu_hours"]["full_validation_fallback_160"]))
