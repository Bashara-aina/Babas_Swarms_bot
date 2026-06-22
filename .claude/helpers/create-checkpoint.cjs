#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');

const PROJ = process.env.CLAUDE_PROJECT_DIR || '.';
const CP_DIR = path.join(PROJ, '.claude-flow', 'data', 'checkpoints');
const MAX_CPS = 10;

try { fs.mkdirSync(CP_DIR, {recursive: true}); } catch {}

const cp = {
  id: `cp-${Date.now()}`,
  timestamp: Date.now() / 1000,
  layers: { L1: 'checkpoint', L2: 'chromadb', L3: 'langmem', L4: 'observations', L5: 'graphrag', L6: 'mem0' },
  env: { cwd: PROJ },
};
const file = path.join(CP_DIR, `${cp.id}.json`);
fs.writeFileSync(file, JSON.stringify(cp, null, 2));

// Prune old checkpoints
const files = fs.readdirSync(CP_DIR).filter(f => f.endsWith('.json')).sort();
while (files.length > MAX_CPS) {
  const old = files.shift();
  try { fs.unlinkSync(path.join(CP_DIR, old)); } catch {}
}
console.log(`[CHECKPOINT] Created: ${cp.id}`);
