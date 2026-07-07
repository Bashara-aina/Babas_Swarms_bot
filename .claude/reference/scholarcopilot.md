# ScholarCopilot — Citation-Aware Academic Writing Assistant

## Overview

ScholarCopilot is a unified language model for citation-aware academic writing, accepted to COLM 2025. It integrates retrieval and generation through a dynamic switching mechanism: the model generates text until it decides a citation is needed, pauses to retrieve relevant papers using its own hidden states, inserts the reference, and resumes generation.

**Authors:** Yubo Wang, Xueguang Ma, Ping Nie, Huaye Zeng, Zhiheng Lyu, Yuxuan Zhang, Benjamin Schneider, Yi Lu, Xiang Yue, Wenhu Chen (TIGER-Lab, University of Waterloo)  
**Paper:** https://arxiv.org/abs/2504.00824  
**Code:** https://github.com/TIGER-AI-Lab/ScholarCopilot  
**Model:** https://huggingface.co/TIGER-Lab/ScholarCopilot-v1  
**Data:** https://huggingface.co/datasets/TIGER-Lab/ScholarCopilot-Data-v1  
**Demo:** https://huggingface.co/spaces/TIGER-Lab/ScholarCopilot  

## Architecture

### Unified Retrieval-Generation

The key insight is a **unified model** for both retrieval and generation, avoiding the need for separate retriever + generator components:

```
Text Generation → <|cite_start|> → Pause → 
  Hidden state → FAISS search → Retrieve abstract → 
  <|reference_start|>abstract<|reference_end|> → Resume generation
```

The model is trained with a **joint loss** = contrastive loss (for retrieval quality) + language modeling loss (for generation quality).

### Inference Pipeline (`scholar_copilot_model.py`)

1. `preprocess_input_text()` — Strips documentclass/packages, adds `<|paper_start|>` prefix
2. `single_complete_step()` — Calls `model.generate()` with `eos_token_id=<|cite_start|>`; returns generated text + hidden state at last token
3. `retrieve_reference()` — Uses FAISS to search HNSW index with the citation hidden state as query, returns top-k paper IDs
4. `llm_rerank()` — Takes the top retrieved abstract and formats it as `<|reference_start|>abstract<|reference_end|>`
5. `replace_citations()` — Maps `reference_id_list` to BibTeX citation keys, produces `\cite{citation_key}`
6. `post_process_output_text()` — Final cleanup: merges consecutive citations, removes special tokens

### Model Architecture (`arxivllm.py`)

`ArxivLLM(nn.Module)` extends a causal LLM with:
- `encode_query()` — Extracts last hidden state at `selected_cite_positions` for retrieval
- `encode_passage()` — Extracts last hidden state at EOS for passage encoding
- Both representations are L2-normalized
- Contrastive loss via in-batch negatives
- Generation loss via standard causal LM cross-entropy
- LoRA fine-tuning with DeepSpeed ZeRO-3

## Data Processing Pipeline

### arXiv metadata → Corpus (`process_arxiv_meta_data.py`)
1. Reads Kaggle arXiv metadata JSON
2. For each paper: extracts ID, title, abstract (wrapped in `<|reference_start|>...<|reference_end|>`)
3. Generates citation key from first author surname + year + first word of title
4. Generates full BibTeX entry
5. Outputs JSONL corpus with `corpus_id`, `paper_id`, `title`, `abstract`, `bibtex`, `citation_key`

### Corpus → Embeddings → HNSW Index
1. Run `encode_corpus.sh` to generate embeddings
2. Run `build_hnsw_index.py` to build FAISS HNSW index for efficient approximate search

## Installation in this project

**Directory:** `tools/scholarcopilot/`  
**Skill:** `/scholarcopilot`

### Files
- `run_demo/scholar_copilot_model.py` — Full inference pipeline (301 lines)
- `run_demo/scholar_copilot_gradio.py` — Gradio web UI (555 lines, streaming + citation management)
- `run_demo/download.sh` — Script to download model + corpus + index
- `train/src/arxivllm.py` — Model architecture (200 lines)
- `train/src/train.py` — Training entry point
- `utils/process_arxiv_meta_data.py` — arXiv → corpus pipeline
- `utils/build_hnsw_index.py` — HNSW index construction

### Requirements
- PyTorch + Transformers for model inference
- FAISS for approximate nearest neighbor search
- h5py for HDF5 embedding storage
- Gradio for web UI

## Key Design Patterns

1. **Dynamic citation token switching** — The `<|cite_start|>` token acts as both a generation stop signal and a retrieval query vector, elegantly unifying the two tasks.
2. **Hidden-state-as-query** — Rather than learning a separate query encoder, the model's own hidden state at citation positions serves as the retrieval query.
3. **Reference injection** — Retrieved abstracts are inserted as `<|reference_start|>...<|reference_end|>` text, allowing the generator to read and incorporate them in subsequent tokens.
4. **Iterative generation** — The inference loop alternates between generation (up to `<|cite_start|>` or `<|paper_end|>`) and retrieval (FAISS search + reference injection), naturally handling multiple citations.
5. **Post-processing** — Consecutive `\cite{key1}\cite{key2}` are merged to `\cite{key1, key2}` for clean output.

## Comparison with Other Paper Tools

| Aspect | ScholarCopilot | paperpal | paperdebugger |
|--------|---------------|----------|--------------|
| Primary function | Citation-aware generation | Paper search | Paper review |
| Uses LLM? | Yes (7B trained model) | No | Structural rules |
| Citation handling | Automatic retrieval + insertion | Search only | Verification |
| Generation? | Yes (text + citations) | No | No |
| Local inference | Requires GPU + model weights | No deps | stdlib only |

## References

- Wang et al., "ScholarCopilot: Training Large Language Models for Academic Writing with Accurate Citations", COLM 2025
- https://github.com/TIGER-AI-Lab/ScholarCopilot
