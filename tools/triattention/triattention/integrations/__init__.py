"""
TriAttention integrations for local inference engines.

This package provides integrations for:
- transformers: HuggingFace models with TriAttention KV compression
- llama.cpp: Python bindings for llama.cpp with TriAttention scoring
- vLLM: Custom attention processor for vLLM inference

Example:
    from transformers import AutoModelForCausalLM
    from triattention.integrations import create_triattention_wrapper

    model = AutoModelForCausalLM.from_pretrained("llama-2-7b")
    tri_model = create_triattention_wrapper(model, kv_budget=2048)
"""

from .transformers_integration import (
    TriAttentionModel,
    TriAttentionAttention,
    LayerCalibrationData,
    create_triattention_wrapper,
)

from .llama_cpp_integration import (
    TriAttentionScorer,
    LlamaCppTriAttention,
    LlamaKVEntry,
)

from .vllm_integration import (
    TriAttentionProcessor,
    TriAttentionCacheManager,
    VLLMTriAttentionConfig,
    create_vllm_processor,
)

__all__ = [
    # transformers
    "TriAttentionModel",
    "TriAttentionAttention",
    "LayerCalibrationData",
    "create_triattention_wrapper",
    # llama.cpp
    "TriAttentionScorer",
    "LlamaCppTriAttention",
    "LlamaKVEntry",
    # vLLM
    "TriAttentionProcessor",
    "TriAttentionCacheManager",
    "VLLMTriAttentionConfig",
    "create_vllm_processor",
]
