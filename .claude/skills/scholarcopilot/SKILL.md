---
name: scholarcopilot
description: "Citation-aware academic writing assistant from TIGER-Lab (COLM 2025). Trained on arXiv full papers for context-aware text generation with dynamic citation retrieval via special token switching. Use when writing introduction/related work sections and needing an AI co-writer that automatically grounds claims in real papers."
trigger: /scholarcopilot
---

# /scholarcopilot

ScholarCopilot is a unified LLM for citation-aware academic writing (COLM 2025, by TIGER-Lab @ University of Waterloo). It uses a novel architecture where the model dynamically switches between text generation and citation retrieval using special tokens.

**Paper:** https://arxiv.org/abs/2504.00824  
**Project:** https://tiger-ai-lab.github.io/ScholarCopilot/  
**Model:** https://huggingface.co/TIGER-Lab/ScholarCopilot-v1 (7B parameters)  
**License:** MIT

## How It Works

ScholarCopilot uses a unified model that integrates retrieval and generation through dynamic switching:

1. **Generation mode** — The model generates coherent academic text until it determines a citation is needed
2. **Citation token** — When the model emits `<|cite_start|>`, generation pauses
3. **Retrieval** — The hidden state from the citation token is used as a query to search a FAISS index of arXiv papers
4. **Reference insertion** — The retrieved abstract is injected as `<|reference_start|>...<|reference_end|>`
5. **Resume generation** — The model continues generating, now grounded in real references

## Key Files

All code is installed at `tools/scholarcopilot/`:

| File | Purpose |
|------|---------|
| `run_demo/scholar_copilot_model.py` | Full inference pipeline (model loading, retrieval, citation processing, post-processing) |
| `run_demo/scholar_copilot_gradio.py` | Gradio web UI with streaming generation, citation search, BibTeX export |
| `run_demo/download.sh` | Download model weights + corpus data from HuggingFace |
| `train/src/arxivllm.py` | Model architecture: dual-encoder for retrieval-augmented generation with contrastive loss + LM loss |
| `train/src/train.py` | Training entry point |
| `utils/process_arxiv_meta_data.py` | arXiv metadata → corpus (title, abstract, BibTeX, citation key) |
| `utils/encode_corpus.sh` | Generate embeddings for the corpus |
| `utils/build_hnsw_index.py` | Build HNSW index from embeddings for fast retrieval |

## Special Token System

ScholarCopilot uses 6 special tokens for the citation-aware generation pipeline:

| Token | Purpose |
|-------|---------|
| `<|paper_start|>` | Start of paper content |
| `<|paper_end|>` | End of paper content |
| `<|cite_start|>` | Model determines citation needed here; hidden state used for retrieval |
| `<|cite_end|>` | End of citation block |
| `<|reference_start|>` | Start of retrieved reference abstract |
| `<|reference_end|>` | End of retrieved reference abstract |

## Running the Demo

```bash
cd tools/scholarcopilot/run_demo
pip install -r requirements.txt
bash download.sh  # downloads model + corpus + index (~15GB)
# Edit the paths in scholar_copilot_gradio.py to point to downloaded data
python3 scholar_copilot_gradio.py
```

## Usage With Claude

Without downloading the model weights, you can use ScholarCopilot's approach:

1. **Citation-aware writing pattern**: When drafting a paper, explicitly identify citation points and retrieve real papers (using `/paperpal` or `/aris arxiv`), then insert them as `\cite{...}`.
2. **Next-3-sentence completion**: Ask Claude to complete your paragraph with 3 sentences, explicitly citing relevant papers from your bibliography.
3. **Section auto-completion**: Use the `"paper-from-zero" → "paper-write"` or `/paper` pipeline, but add an explicit citation verification step.

## Response Modes

The Gradio demo defines two modes:

- **Complete 3 sentences** (`stream_complete_3_sentence`): Generates exactly 3 more sentences, retrieving citations as needed, yielding output token-by-token.
- **Generate to the end** (`stream_generate`): Generates until `<|paper_end|>`, retrieving citations at each `<|cite_start|>` token.

Both modes use `single_complete_step` which calls `model.generate()` with `eos_token_id=<|cite_start|>` — generation stops at each citation point to retrieve.

## Citation Workflow

The demo implements a complete citation workflow:
1. Click "Search citations" → FAISS retrieval from corpus → ranked candidates shown
2. Select citations → inserted as `\cite{key}` into text
3. "Update BibTeX" → exports all used citations as BibTeX entries

## Training (for reference)

The model was trained on the complete arXiv full-paper corpus:
- **Loss**: Contrastive loss (for retrieval) + language modeling loss (for generation)
- **Architecture**: 7B LLM base + LoRA adapters
- **Data**: arXiv papers processed with special tokens for citation positions
- **Hardware**: 32 GPUs (4 machines × 8 GPUs)
- **Config**: `train/src/ds_zero3_config.json` (DeepSpeed ZeRO-3)

`arxivllm.py` implements `ArxivLLM(nn.Module)` class with:
- `encode_query()` — extracts hidden states at citation token positions for retrieval
- `encode_passage()` — encodes reference abstracts
- `forward()` — computes both contrastive and generation loss

## Integration

- **/paperpal** — search for papers to cite (arXiv, Semantic Scholar)
- **/paperdebugger verify_citations** — verify citations are real
- **/aris paper-write** — full paper writing pipeline
- **/genai-proofreader** — review the generated text for quality
