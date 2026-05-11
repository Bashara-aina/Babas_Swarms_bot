#!/usr/bin/env node

/**
 * UserPromptSubmit Hook — obsidian-mind
 *
 * Runs on every user message. Classifies content and injects routing hints.
 * Lightweight classifier — fast decision on what kind of note to create.
 */

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const VAULT_ROOT = process.cwd();
const WIKI_DIR = join(VAULT_ROOT, '.wiki');

interface Classification {
  type: 'decision' | 'incident' | 'win' | '1-1' | 'architecture' | 'person' | 'project-update' | 'general';
  confidence: number;
  routingHints: string[];
  suggestedNote?: string;
}

const CLASSIFICATION_PATTERNS = {
  decision: /\b(decided|decision|chose|agreed|will go with|best approach is)\b/i,
  incident: /\b(incident|outage|broken|failed|crash|alert|emergency|P1|P2)\b/i,
  win: /\b(won|praised|great work|exceeded|delighted|happy with|impressed)\b/i,
  '1-1': /\b(1:1|one-on-one|1on1|meeting|sync with)\b/i,
  architecture: /\b(architecture|design|system design|api contract|schema|refactor)\b/i,
  person: /\b(sarah|john|mike|tom|sarah|james|team lead|manager|peer)\b/i,
  projectUpdate: /\b(project|shipping|deployed|completed|released|milestone)\b/i
};

function classifyMessage(message: string): Classification {
  const scores: Record<string, number> = {
    decision: 0,
    incident: 0,
    win: 0,
    '1-1': 0,
    architecture: 0,
    person: 0,
    'project-update': 0,
    general: 0.1
  };

  for (const [type, pattern] of Object.entries(CLASSIFICATION_PATTERNS)) {
    if (pattern.test(message)) {
      scores[type] += 1;
    }
  }

  // Find highest scoring type
  let maxType = 'general';
  let maxScore = 0.1;
  for (const [type, score] of Object.entries(scores)) {
    if (score > maxScore) {
      maxScore = score;
      maxType = type;
    }
  }

  const hints: string[] = [];
  if (maxType === 'decision') {
    hints.push('Create decision record in brain/Key Decisions/');
    hints.push('Update brain/Memories.md');
  } else if (maxType === 'incident') {
    hints.push('Create incident note in work/incidents/');
    hints.push('Update brain/Gotchas.md if novel failure');
  } else if (maxType === 'win') {
    hints.push('Add to perf/Brag Doc.md');
    hints.push('Link to evidence in work/');
  } else if (maxType === '1-1') {
    hints.push('Create 1:1 note in work/1-1/');
    hints.push('Update org/people/ with context');
  } else if (maxType === 'architecture') {
    hints.push('Update reference/architecture/ if new design');
    hints.push('Consider creating decision record');
  } else if (maxType === 'person') {
    hints.push('Update org/people/[Name].md');
    hints.push('Link to relevant work notes');
  }

  return {
    type: maxType as Classification['type'],
    confidence: maxScore / (maxScore + 1),
    routingHints: hints,
    suggestedNote: maxType !== 'general' ? `${maxType}-template` : undefined
  };
}

async function main() {
  const message = process.argv[2] || '';

  if (!message) {
    console.log(JSON.stringify({ type: 'general', confidence: 0, routingHints: [], suggestedNote: undefined }));
    return;
  }

  const classification = classifyMessage(message);
  console.log(JSON.stringify(classification));
}

main().catch(console.error);
