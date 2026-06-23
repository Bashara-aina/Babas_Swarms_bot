#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');

const PROJ = process.env.CLAUDE_PROJECT_DIR || '.';
const DATA_DIR = path.join(PROJ, '.claude-flow', 'data');
const CP_DIR = path.join(DATA_DIR, 'checkpoints');
const MAX_CPS = 10;

try { fs.mkdirSync(CP_DIR, {recursive: true}); } catch (e) { process.stderr.write('[CHECKPOINT] Failed to create checkpoint dir: ' + e.message + '\n'); return; }

function tryRead(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      const raw = fs.readFileSync(filePath, 'utf-8');
      return JSON.parse(raw);
    }
  } catch (e) { process.stderr.write('[CHECKPOINT] Failed to read ' + path.basename(filePath) + ': ' + e.message + '\n'); }
  return null;
}

const store = tryRead(path.join(DATA_DIR, 'auto-memory-store.json'));
const graph = tryRead(path.join(DATA_DIR, 'graph-state.json'));
const ranked = tryRead(path.join(DATA_DIR, 'ranked-context.json'));

const cp = {
  id: `cp-${Date.now()}`,
  timestamp: Date.now() / 1000,
  layers: { L1: 'checkpoint', L2: 'chromadb', L3: 'langmem', L4: 'observations', L5: 'graphrag', L6: 'mem0' },
  env: { cwd: PROJ },
  snapshot: {
    storeSize: store ? (Array.isArray(store) ? store.length : Object.keys(store).length) : 0,
    graphNodes: graph ? (graph.nodes ? Object.keys(graph.nodes).length : 0) : 0,
    graphEdges: graph ? (graph.edges ? graph.edges.length : 0) : 0,
    rankedEntries: ranked ? (ranked.entries ? ranked.entries.length : 0) : 0,
    store: store,
    graph: graph,
    rankedContext: ranked,
  },
};

const file = path.join(CP_DIR, `${cp.id}.json`);
fs.writeFileSync(file, JSON.stringify(cp, null, 2));
console.log(`[CHECKPOINT] Created: ${cp.id} (${cp.snapshot.storeSize} store entries, ${cp.snapshot.graphNodes} graph nodes, ${cp.snapshot.graphEdges} edges)`);

// Prune old checkpoints
const files = fs.readdirSync(CP_DIR).filter(f => f.endsWith('.json')).sort();
while (files.length > MAX_CPS) {
  const old = files.shift();
  try { fs.unlinkSync(path.join(CP_DIR, old)); } catch (e) { process.stderr.write('[CHECKPOINT] Failed to remove old checkpoint ' + old + ': ' + e.message + '\n'); }
}
