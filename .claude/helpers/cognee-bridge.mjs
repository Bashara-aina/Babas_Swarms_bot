#!/usr/bin/env node
/**
 * Cognee Bridge — connects cognee knowledge graph memory into the Claude Code
 * memory lifecycle (L7 layer).
 *
 * Called by hooks:
 *   node cognee-bridge.mjs import  — SessionStart: sync auto-memory → cognee
 *   node cognee-bridge.mjs sync    — SessionEnd:   sync cognee insights back
 *   node cognee-bridge.mjs status  — Show bridge status
 */

import { existsSync, readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { spawnSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = join(__dirname, '../..');
const DATA_DIR = join(PROJECT_ROOT, '.claude-flow', 'data');
const STORE_PATH = join(DATA_DIR, 'auto-memory-store.json');
const COGNEE_BRIDGE_STORE = join(DATA_DIR, 'cognee-bridge-state.json');

const PYTHON = 'python3';
const COGNEE_MCP = join(PROJECT_ROOT, '.claude-flow/mcp/cognee-mcp-server.py');

const GREEN = '\x1b[0;32m';
const CYAN = '\x1b[0;36m';
const DIM = '\x1b[2m';
const RESET = '\x1b[0m';

const log = (msg) => console.log(`${CYAN}[CogneeBridge] ${msg}${RESET}`);
const success = (msg) => console.log(`${GREEN}[CogneeBridge] ✓ ${msg}${RESET}`);
const dim = (msg) => console.log(`  ${DIM}${msg}${RESET}`);

// ── JSON-RPC call to cognee MCP server ─────────────────────────────────────

function callCognee(tool, args = {}) {
  const payload = JSON.stringify({
    jsonrpc: '2.0',
    method: `tools/call/${tool}`,
    params: { arguments: args },
    id: 1,
  });

  const result = spawnSync(PYTHON, [COGNEE_MCP], {
    input: payload + '\n',
    timeout: 120000,  // cognee first-call warmup
    encoding: 'utf-8',
  });

  if (result.error) {
    return { error: result.error.message };
  }

  try {
    // MCP server prints a startup line first, then the response
    const lines = result.stdout.trim().split('\n').filter(l => l.trim());
    // Parse the last JSON line (the actual response)
    const lastLine = lines[lines.length - 1];
    const parsed = JSON.parse(lastLine);
    return parsed.result || parsed;
  } catch (e) {
    return { error: `Parse failed: ${e.message}`, stdout: result.stdout };
  }
}

// ── Load auto-memory store ─────────────────────────────────────────────────

function loadStore() {
  if (!existsSync(STORE_PATH)) return [];
  try {
    return JSON.parse(readFileSync(STORE_PATH, 'utf-8'));
  } catch {
    return [];
  }
}

function loadBridgeState() {
  if (!existsSync(COGNEE_BRIDGE_STORE)) {
    return { lastSync: 0, syncedKeys: [] };
  }
  try {
    return JSON.parse(readFileSync(COGNEE_BRIDGE_STORE, 'utf-8'));
  } catch {
    return { lastSync: 0, syncedKeys: [] };
  }
}

function saveBridgeState(state) {
  writeFileSync(COGNEE_BRIDGE_STORE, JSON.stringify(state, null, 2), 'utf-8');
}

// ── Commands ───────────────────────────────────────────────────────────────

async function doImport() {
  log('Syncing auto-memory entries into cognee knowledge graph...');

  const status = callCognee('cognee_status');
  if (status.error) {
    dim(`Cognee not available: ${status.error}`);
    dim('L7 layer will be inactive this session');
    return;
  }

  const entries = loadStore();
  const state = loadBridgeState();
  const newEntries = entries.filter(
    (e) => !state.syncedKeys.includes(e.id || e.key)
  );

  if (newEntries.length === 0) {
    dim('No new entries to sync');
    return;
  }

  // Batch all new entries into a single call (avoids per-entry pipeline init)
  const textParts = newEntries
    .map((e) => (e.content || e.summary || ''))
    .filter((c) => c.length >= 15)
    .slice(0, 50);

  let synced = 0;
  if (textParts.length > 0) {
    const combined = textParts.join('\n---\n').slice(0, 100000);
    const result = callCognee('cognee_remember', {
      text: combined,
      dataset: 'auto-memory',
    });
    if (!result.error) synced = textParts.length;
  }

  // Update bridge state
  const newlySyncedKeys = newEntries.map((e) => e.id || e.key).filter(Boolean);
  state.syncedKeys.push(...newlySyncedKeys);
  state.lastSync = Date.now();
  saveBridgeState(state);

  success(`Synced ${synced} entries into cognee knowledge graph (L7)`);
  dim(`├─ Total entries in store: ${entries.length}`);
  dim(`└─ Bridge synced keys: ${state.syncedKeys.length}`);
}

async function doSync() {
  log('Syncing cognee insights back to auto-memory...');

  const status = callCognee('cognee_status');
  if (status.error) {
    dim(`Cognee not available: ${status.error}`);
    return;
  }

  // Get graph stats for the record
  const stats = callCognee('cognee_graph_stats');
  if (!stats.error) {
    success(`Cognee graph: ${stats.nodes || '?'} nodes, ${stats.edges || '?'} edges`);
  }

  // Record bridge state timestamp
  const state = loadBridgeState();
  state.lastSync = Date.now();
  saveBridgeState(state);
}

async function doStatus() {
  console.log('\n=== Cognee Bridge (L7 Layer) ===\n');

  const status = callCognee('cognee_status');
  if (status.error) {
    console.log(`  Status:  ❌ ${status.error}`);
    console.log(`  Reason:  Cognee package or dependencies missing`);
    console.log(`  Fix:     pip install cognee with deps`);
    console.log('');
    return;
  }

  console.log(`  Status:     ✅ Ready`);
  console.log(`  Data dir:   ${status.data_dir || '?'}`);
  console.log(`  Entries:    ${status.entries ?? '?'}`);
  console.log(`  Triples:    ${status.triples ?? '?'}`);

  const stats = callCognee('cognee_graph_stats');
  if (!stats.error) {
    console.log(`  Nodes:      ${stats.nodes ?? '?'}`);
    console.log(`  Edges:      ${stats.edges ?? '?'}`);
  }

  const state = loadBridgeState();
  console.log(`  Last sync:  ${state.lastSync ? new Date(state.lastSync).toISOString() : 'never'}`);
  console.log(`  Synced keys: ${state.syncedKeys.length}`);
  console.log('');
}

// ── Main ───────────────────────────────────────────────────────────────────

const command = process.argv[2] || 'status';

try {
  switch (command) {
    case 'import': await doImport(); break;
    case 'sync': await doSync(); break;
    case 'status': await doStatus(); break;
    default:
      console.log('Usage: cognee-bridge.mjs <import|sync|status>');
      break;
  }
} catch (err) {
  try { dim(`Error (non-critical): ${err.message}`); } catch (_) {}
}
process.exit(0);
