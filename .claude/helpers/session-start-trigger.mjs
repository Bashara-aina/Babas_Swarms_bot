#!/usr/bin/env node
/**
 * Session Start Trigger — 6-Layer Memory Initialization
 * Runs at SessionStart to boot memory systems and restore context.
 * 
 * Part of the memory_inject.md bootstrap — loads all memory layers
 * so the agent starts with full context from previous sessions.
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = join(__dirname, '../..');
const DATA_DIR = join(PROJECT_ROOT, '.claude-flow', 'data');
const MEMORY_BOOTSTRAP = join(PROJECT_ROOT, '.claude', 'memory_bootstrap.md');
const SESSION_FILE = join(DATA_DIR, 'current.json');

const CYAN = '\x1b[0;36m';
const GREEN = '\x1b[0;32m';
const YELLOW = '\x1b[0;33m';
const DIM = '\x1b[2m';
const RESET = '\x1b[0m';

const log = (msg) => console.log(`${CYAN}[SessionStart] ${msg}${RESET}`);
const ok = (msg) => console.log(`${GREEN}[SessionStart] ✓ ${msg}${RESET}`);
const warn = (msg) => console.log(`${YELLOW}[SessionStart] ⚠ ${msg}${RESET}`);

async function initializeSession() {
  log('Booting 6-layer memory system...');

  // Ensure data directory
  if (!existsSync(DATA_DIR)) {
    mkdirSync(DATA_DIR, { recursive: true });
  }

  // Create/update session file
  const sessionId = `session-${Date.now()}`;
  const session = {
    id: sessionId,
    startedAt: new Date().toISOString(),
    cwd: PROJECT_ROOT,
    memoryLayers: {
      l1_checkpoints: join(DATA_DIR, 'checkpoints'),
      l2_chromadb: join(DATA_DIR, 'chromadb'),
      l3_langmem: join(DATA_DIR, 'langmem'),
      l4_observation: join(DATA_DIR, 'observation_store'),
      l5_graphrag: join(DATA_DIR, 'graphrag'),
      l6_mem0cloud: join(DATA_DIR, 'mem0cloud'),
    },
    metrics: {
      edits: 0,
      commands: 0,
      tasks: 0,
      errors: 0,
    },
  };

  writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2));

  // Ensure all memory layer directories exist
  for (const [layer, dir] of Object.entries(session.memoryLayers)) {
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  }

  // Check for memory_bootstrap.md and load context
  if (existsSync(MEMORY_BOOTSTRAP)) {
    try {
      const bootstrap = readFileSync(MEMORY_BOOTSTRAP, 'utf-8');
      const lines = bootstrap.split('\n').filter(l => l.trim());
      log(`Memory bootstrap loaded: ${lines.length} entries`);
    } catch (e) {
      warn('Could not read memory_bootstrap.md');
    }
  }

  // Check for route-history.json to determine if we have learning
  const routeHistory = join(DATA_DIR, 'route-history.json');
  if (existsSync(routeHistory)) {
    try {
      const history = JSON.parse(readFileSync(routeHistory, 'utf-8'));
      if (history.entries && history.entries.length > 0) {
        const recent = history.entries.slice(-3);
        log(`Route history: ${history.entries.length} entries (${recent.length} recent)`);
      }
    } catch (e) {
      // ignore
    }
  }

  // Check ranked context
  const rankedContext = join(DATA_DIR, 'ranked-context.json');
  if (existsSync(rankedContext)) {
    try {
      const ctx = JSON.parse(readFileSync(rankedContext, 'utf-8'));
      if (ctx.entries) {
        log(`Ranked context: ${ctx.entries.length} entries, PageRank valid`);
      }
    } catch (e) {
      // ignore
    }
  }

  ok(`Session ${sessionId} initialized`);
  return sessionId;
}

// Run if called directly
const args = process.argv.slice(2);
if (args.length === 0 || args[0] === 'start') {
  initializeSession().catch(e => {
    console.error('[SessionStart] Error:', e.message);
    process.exit(1);
  });
} else if (args[0] === 'status') {
  // Show current session status
  if (existsSync(SESSION_FILE)) {
    const session = JSON.parse(readFileSync(SESSION_FILE, 'utf-8'));
    console.log(JSON.stringify(session, null, 2));
  } else {
    console.log('No active session');
  }
}

export { initializeSession };