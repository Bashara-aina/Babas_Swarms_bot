---
title: Andrej Karpathy
type: person
project: general
status: active
tags: [ai, researcher, educator, neural-networks, karpathy]
created: 2026-04-13
updated: 2026-04-13
summary: Andrej Karpathy is an AI researcher and educator known for building LLM knowledge bases and educational content on neural networks.
wikilinks:
  - [[concepts/karpathy-kb-pattern]]
  - [[concepts/llm-cost-routing]]
  - [[concepts/self-improvement-loop]]
  - [[projects/legion-bot]]
confidence: high
source: external
---

# Andrej Karpathy

## TL;DR

Andrej Karpathy is a renowned AI researcher who served as Director of AI at Tesla Autopilot and Research Scientist at OpenAI before becoming one of the most influential AI educators on the internet. He pioneered the "LLM knowledge base pattern" that inspired Legion's wiki structure, characterized by frontmatter metadata, TL;DR summaries, and dense wikilink cross-referencing. His open source projects minGPT and nanoGPT remain canonical references for understanding transformer architecture from scratch.

## Background

**Former positions:**
- Director of AI at Tesla Autopilot (2017–2018): Led computer vision systems for lane recognition, traffic light detection, and autonomous driving decisions
- Research Scientist at OpenAI (2015–2017): Early member of OpenAI, contributed to foundational RL and language model research
- Lecturer at Stanford University: Taught CS231n (Convolutional Neural Networks for Visual Recognition), one of the most influential deep learning courses

**Current work:**
- Educational content creation via YouTube and Twitter/X with 1M+ followers
- LLM knowledge base system design and documentation
- Open source projects (minGPT, nanoGPT, school-of-ai)
- Occasional consulting on AI system architecture

## Contributions to Legion's Wiki

The [[concepts/karpathy-kb-pattern]] was directly inspired by Karpathy's approach to structuring AI knowledge bases. The pattern emphasizes:

**Structural elements that Legion adopted:**
- YAML frontmatter with type, status, confidence, and tags fields
- TL;DR summary as the first content section (before the first `##` heading)
- Dense wikilink cross-references (`[[article-name]]` syntax)
- AI-optimized knowledge storage enabling fast RAG retrieval
- Clear section hierarchy: TL;DR → Overview → Context → Key Properties → How It Works → Relationships → Current Status

**Technical inspiration:**
- His `nanoGPT` repository demonstrated minimal, readable GPT implementations that influenced Legion's approach to LLM cost routing
- The school-of-ai philosophy of accessible, distributed AI education influenced Legion's multi-agent orchestration design

## Notable Work

### minGPT (2020)
A minimal PyTorch implementation of a GPT model in ~300 lines of code. Purposefully educational rather than optimized. Demonstrates:
- Attention mechanism from first principles
- Autoregressive generation
- BPE tokenization basics

### nanoGPT (2022)
Simple GPU-accelerated GPT training pipeline. Designed to be the simplest way to train a GPT model on custom text data. This directly influenced [[concepts/llm-cost-routing]] decisions in Legion (training vs inference cost tradeoffs).

### CS231n Lectures (2016–2017)
Stanford's flagship deep learning course. Karpathy's lecture notes and assignments became the de facto standard for CNN education. The course structure (visual examples → mathematical foundation → code implementation) influenced Legion's [[concepts/self-improvement-loop]] design.

## The Karpathy LLM Wiki Pattern

Karpathy's approach to LLM knowledge bases separates two concerns:

1. **Storage format**: Obsidian-compatible Markdown with frontmatter (YAML)
2. **Retrieval strategy**: Embeddings + vector search for context injection

Legion's wiki implementation combines both:
- [[concepts/vector-search]] for semantic retrieval of relevant articles
- Dense [[concepts/intent-routing]] based on keyword matching
- Human-readable structure for debugging and manual editing

## Related Pages

- [[concepts/karpathy-kb-pattern]] — Pattern inspired by Karpathy's wiki approach
- [[concepts/llm-cost-routing]] — Cost optimization influenced by nanoGPT training economics
- [[concepts/self-improvement-loop]] — Learning loop design inspired by CS231n pedagogy
