"""
backbones — registration of every forecast backbone plugin.

Importing this package registers the built-in candidates. Nothing is downloaded:
`gpt2_miflu` is registered with an availability note, and building it will fail
loudly if the local gpt2 cache is absent (callers should check availability).
"""

from innovation.backbones.gpt2_miflu_adapter import (GPT2MifluAdapter,
                                                     gpt2_cache_available)
from innovation.backbones.dlinear import DLinear, NLinear
from innovation.backbones.fusion_forecaster import (NAME as FUSION_FORECASTER,
                                                    TextFusionForecaster)
from innovation.backbones.itransformer import ITransformer
from innovation.backbones.llm_inspired import (CALFInspired, QwenTimeLLM,
                                                TimeCMAInspired)
from innovation.backbones.patchtst import PatchTST
from innovation.backbones.registry import (available_backbones, get_backbone,
                                           list_backbones, make_backbone,
                                           register_backbone)

register_backbone("dlinear", DLinear,
                  note="DLinear (Zeng et al., AAAI 2023) — re-implementation")
register_backbone("nlinear", NLinear,
                  note="NLinear (Zeng et al., AAAI 2023) — re-implementation")
register_backbone("patchtst", PatchTST,
                  note="PatchTST supervised re-implementation (no pretraining)")
register_backbone("itransformer", ITransformer,
                  note="iTransformer (ICLR 2024) — re-implementation")
register_backbone(FUSION_FORECASTER, TextFusionForecaster,
                  note="generic plugin testbed (NOT a paper architecture)")
register_backbone("gpt2_miflu", GPT2MifluAdapter,
                  note=f"MIFlu control group; gpt2 cache available="
                       f"{gpt2_cache_available()}")
register_backbone("qwen_time_llm", QwenTimeLLM,
                  note="Time-LLM-inspired Qwen2.5 patch/prototype/Prompt-as-Prefix")
register_backbone("calf_llm", CALFInspired,
                  note="CALF-inspired dual branch with feature/output alignment")
register_backbone("timecma_llm", TimeCMAInspired,
                  note="clean-room TimeCMA-inspired retrieval/last-token branch")

__all__ = ["available_backbones", "get_backbone", "list_backbones",
           "make_backbone", "register_backbone", "gpt2_cache_available"]
