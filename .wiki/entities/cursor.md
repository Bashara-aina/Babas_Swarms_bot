---
title: Cursor
type: entity
status: active
tags: [ide, cursor, editor, tool]
created: 2026-05-05
updated: 2026-05-05
summary: "Cursor is an AI-first code editor (cursor.com) built on the VS Code codebase with deep LLM integration."
wikilinks:
  - [[entities/vscode]]
  - [[tools/opencode]]
confidence: high
source: external
---
# Cursor — AI-First Code Editor

## Overview

Cursor is an AI-native code editor that integrates large language models directly into the coding workflow. Based on VS Code, it provides AI-assisted editing, code generation, and pair programming through built-in LLM capabilities.

## Key Features

- **AI Pair Programming**: Tab autocomplete, inline chat, and agent-mode code generation
- **Context Integration**: Combines codebase indexing with LLM reasoning for relevant suggestions
- **Multi-file Editing**: Agent mode can plan and execute multi-file refactors

## Relevance to Swarm-Bot

Swarm-bot uses Cursor as a code editing environment. When Bashara mentions "edit in Cursor" or refers to cursor-based workflows, the agent should understand cursor's features and limitation

## Notes

See [[entities/vscode]] for the underlying editor framework that Cursor extends.