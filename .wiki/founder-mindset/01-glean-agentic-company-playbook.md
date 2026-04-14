---
title: Glean Agentic Company Playbook
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- founder-mindset
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Source: https://marketcurve.substack.com/p/how-to-build-an-ai-agent-company'
wikilinks: []
confidence: medium
source: research
---
# Glean $7.2B Agentic Company Playbook

Source: https://marketcurve.substack.com/p/how-to-build-an-ai-agent-company

## Core Principle
"Enterprises don't adopt agentic software because it's cool.
They adopt it when it's boringly reliable."
Capability < Reliability. Always.

## The 5-Step Playbook
1. **Start vertical** — pick ONE language-heavy niche with unstructured text pain
2. **Solve one workflow** — the most frustrating, repetitive task first
3. **Build connectors** — integrate with tools already in the niche's stack
4. **Bundle over time** — start narrow, add adjacent automations to build moat
5. **Move upmarket** — PLG first → then sales-led as you mature

## The RAG Principle (Critical for Legion)
Never rely on LLM training data for domain work.
Always retrieve → then generate.
If answer isn't in retrieved docs → say "I don't know".
Reduces hallucination. Builds trust.

## What Makes an Agent Worth $7B
- Permission-aware (knows who can see what)
- Citation-backed (every answer has a source)
- Knows when to say "I don't know"
- Survives contact with messy organizational reality

## Applied to Legion Bot
- Wiki = Glean's Knowledge Graph
- _wiki_layer() = Glean's RAG retrieval
- SOUL.md = Glean's enterprise context
- Goal: make Legion boringly reliable before adding new features
