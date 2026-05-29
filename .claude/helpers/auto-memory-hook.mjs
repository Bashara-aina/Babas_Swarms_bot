#!/usr/bin/env node
/**
 * Auto Memory Bridge Hook (ADR-048/049)
 *
 * Wires AutoMemoryBridge + LearningBridge + MemoryGraph into Claude Code
 * session lifecycle. Called by settings.json SessionStart/SessionEnd hooks.
 *
 * Usage:
 *   node auto-memory-hook.mjs import   # SessionStart: import auto memory files into backend
 *   node auto-memory-hook.mjs sync     # SessionEnd: sync insights back to MEMORY.md
 *   node auto-memory-hook.mjs status   # Show bridge status
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = join(__dirname, '../..');
const DATA_DIR = join(PROJECT_ROOT, '.claude-flow', 'data');
const STORE_PATH = join(DATA_DIR, 'auto-memory-store.json');

// Colors
const GREEN = '\x1b[0;32m';
const CYAN = '\x1b[0;36m';
const DIM = '\x1b[2m';
const RESET = '\x1b[0m';

const log = (msg) => console.log(`${CYAN}[AutoMemory] ${msg}${RESET}`);
const success = (msg) => console.log(`${GREEN}[AutoMemory] ✓ ${msg}${RESET}`);
const dim = (msg) => console.log(`  ${DIM}${msg}${RESET}`);

// Ensure data dir
if (!existsSync(DATA_DIR)) mkdirSync(DATA_DIR, { recursive: true });

// ============================================================================
// FNV-1a 64-bit content fingerprint (mirrors intelligence.cjs)
// ============================================================================

function fingerprintContent(text) {
  if (!text) return '0_0_0';
  let h1 = 0x811c9dc5, h2 = 0xcbf29ce4;
  for (let i = 0; i < text.length; i++) {
    const c = text.charCodeAt(i);
    h1 ^= c; h1 = Math.imul(h1, 0x01000193) >>> 0;
    h2 ^= c; h2 = Math.imul(h2, 0x100000001b3 >>> 0) >>> 0;
  }
  return `${h1.toString(16)}_${h2.toString(16)}_${text.length}`;
}

function deduplicateByContent(entries) {
  if (!entries || !Array.isArray(entries)) return entries;
  const seen = new Map();
  for (const entry of entries) {
    const content = entry.content || entry.summary || entry.value || '';
    const fp = fingerprintContent(typeof content === 'string' ? content : JSON.stringify(content));
    if (!seen.has(fp)) {
      seen.set(fp, entry);
    } else {
      const existing = seen.get(fp);
      const existingAccess = existing.accessCount || existing.metadata?.accessCount || 0;
      const candidateAccess = entry.accessCount || entry.metadata?.accessCount || 0;
      if (candidateAccess > existingAccess) seen.set(fp, entry);
    }
  }
  return Array.from(seen.values());
}

// ============================================================================
// Simple JSON File Backend (implements IMemoryBackend interface)
// ============================================================================

class JsonFileBackend {
  constructor(filePath) {
    this.filePath = filePath;
    this.entries = new Map();
  }

  async initialize() {
    if (existsSync(this.filePath)) {
      try {
        const data = JSON.parse(readFileSync(this.filePath, 'utf-8'));
        if (Array.isArray(data)) {
          // Deduplicate by content fingerprint before loading
          const unique = deduplicateByContent(data);
          for (const entry of unique) this.entries.set(entry.id, entry);
          if (unique.length < data.length) {
            dim(`Deduped ${data.length - unique.length} duplicate entries`);
          }
        }
      } catch { /* start fresh */ }
    }
  }

  async shutdown() { this._persist(); }
  async store(entry) { this.entries.set(entry.id, entry); this._persist(); }
  async get(id) { return this.entries.get(id) ?? null; }
  async getByKey(key, ns) {
    for (const e of this.entries.values()) {
      if (e.key === key && (!ns || e.namespace === ns)) return e;
    }
    return null;
  }
  async update(id, updates) {
    const e = this.entries.get(id);
    if (!e) return null;
    if (updates.metadata) Object.assign(e.metadata, updates.metadata);
    if (updates.content !== undefined) e.content = updates.content;
    if (updates.tags) e.tags = updates.tags;
    e.updatedAt = Date.now();
    this._persist();
    return e;
  }
  async delete(id) { return this.entries.delete(id); }
  async query(opts) {
    let results = [...this.entries.values()];
    if (opts?.namespace) results = results.filter(e => e.namespace === opts.namespace);
    if (opts?.type) results = results.filter(e => e.type === opts.type);
    if (opts?.limit) results = results.slice(0, opts.limit);
    return results;
  }
  async search() { return []; } // No vector search in JSON backend
  async bulkInsert(entries) { for (const e of entries) this.entries.set(e.id, e); this._persist(); }
  async bulkDelete(ids) { let n = 0; for (const id of ids) { if (this.entries.delete(id)) n++; } this._persist(); return n; }
  async count() { return this.entries.size; }
  async listNamespaces() {
    const ns = new Set();
    for (const e of this.entries.values()) ns.add(e.namespace || 'default');
    return [...ns];
  }
  async clearNamespace(ns) {
    let n = 0;
    for (const [id, e] of this.entries) {
      if (e.namespace === ns) { this.entries.delete(id); n++; }
    }
    this._persist();
    return n;
  }
  async getStats() {
    return {
      totalEntries: this.entries.size,
      entriesByNamespace: {},
      entriesByType: { semantic: 0, episodic: 0, procedural: 0, working: 0, cache: 0 },
      memoryUsage: 0, avgQueryTime: 0, avgSearchTime: 0,
    };
  }
  async healthCheck() {
    return {
      status: 'healthy',
      components: {
        storage: { status: 'healthy', latency: 0 },
        index: { status: 'healthy', latency: 0 },
        cache: { status: 'healthy', latency: 0 },
      },
      timestamp: Date.now(), issues: [], recommendations: [],
    };
  }

  _persist() {
    try {
      const all = [...this.entries.values()];
      const unique = deduplicateByContent(all);
      writeFileSync(this.filePath, JSON.stringify(unique, null, 2), 'utf-8');
    } catch { /* best effort */ }
  }
}

// ============================================================================
// Resolve memory package path (local dev or npm installed)
// ============================================================================

async function loadMemoryPackage() {
  // Strategy 1: Local dev (built dist)
  const localDist = join(PROJECT_ROOT, 'v3/@claude-flow/memory/dist/index.js');
  if (existsSync(localDist)) {
    try {
      return await import(`file://${localDist}`);
    } catch { /* fall through */ }
  }

  // Strategy 2: Use createRequire for CJS-style resolution (handles nested node_modules
  // when installed as a transitive dependency via npx ruflo / npx claude-flow)
  try {
    const { createRequire } = await import('module');
    const require = createRequire(join(PROJECT_ROOT, 'package.json'));
    return require('@claude-flow/memory');
  } catch { /* fall through */ }

  // Strategy 3: ESM import (works when @claude-flow/memory is a direct dependency)
  try {
    return await import('@claude-flow/memory');
  } catch { /* fall through */ }

  // Strategy 4: Walk up from PROJECT_ROOT looking for @claude-flow/memory in any node_modules
  let searchDir = PROJECT_ROOT;
  const { parse } = await import('path');
  while (searchDir !== parse(searchDir).root) {
    const candidate = join(searchDir, 'node_modules', '@claude-flow', 'memory', 'dist', 'index.js');
    if (existsSync(candidate)) {
      try {
        return await import(`file://${candidate}`);
      } catch { /* fall through */ }
    }
    searchDir = dirname(searchDir);
  }

  return null;
}

// ============================================================================
// Read config from .claude-flow/config.yaml
// ============================================================================

function readConfig() {
  const configPath = join(PROJECT_ROOT, '.claude-flow', 'config.yaml');
  const defaults = {
    learningBridge: { enabled: true, sonaMode: 'balanced', confidenceDecayRate: 0.005, accessBoostAmount: 0.03, consolidationThreshold: 10 },
    memoryGraph: { enabled: true, pageRankDamping: 0.85, maxNodes: 5000, similarityThreshold: 0.8 },
    agentScopes: { enabled: true, defaultScope: 'project' },
  };

  if (!existsSync(configPath)) return defaults;

  try {
    const yaml = readFileSync(configPath, 'utf-8');
    // Simple YAML parser for the memory section
    const getBool = (key) => {
      const match = yaml.match(new RegExp(`${key}:\\s*(true|false)`, 'i'));
      return match ? match[1] === 'true' : undefined;
    };

    const lbEnabled = getBool('learningBridge[\\s\\S]*?enabled');
    if (lbEnabled !== undefined) defaults.learningBridge.enabled = lbEnabled;

    const mgEnabled = getBool('memoryGraph[\\s\\S]*?enabled');
    if (mgEnabled !== undefined) defaults.memoryGraph.enabled = mgEnabled;

    const asEnabled = getBool('agentScopes[\\s\\S]*?enabled');
    if (asEnabled !== undefined) defaults.agentScopes.enabled = asEnabled;

    return defaults;
  } catch {
    return defaults;
  }
}

// ============================================================================
// Commands
// ============================================================================

async function doImport() {
  log('Importing auto memory files into bridge...');

  const memPkg = await loadMemoryPackage();
  if (!memPkg || !memPkg.AutoMemoryBridge) {
    dim('Memory package not available — skipping auto memory import');
    return;
  }

  const config = readConfig();
  const backend = new JsonFileBackend(STORE_PATH);
  await backend.initialize();

  const bridgeConfig = {
    workingDir: PROJECT_ROOT,
    syncMode: 'on-session-end',
  };

  // Wire learning if enabled and available
  if (config.learningBridge.enabled && memPkg.LearningBridge) {
    bridgeConfig.learning = {
      sonaMode: config.learningBridge.sonaMode,
      confidenceDecayRate: config.learningBridge.confidenceDecayRate,
      accessBoostAmount: config.learningBridge.accessBoostAmount,
      consolidationThreshold: config.learningBridge.consolidationThreshold,
    };
  }

  // Wire graph if enabled and available
  if (config.memoryGraph.enabled && memPkg.MemoryGraph) {
    bridgeConfig.graph = {
      pageRankDamping: config.memoryGraph.pageRankDamping,
      maxNodes: config.memoryGraph.maxNodes,
      similarityThreshold: config.memoryGraph.similarityThreshold,
    };
  }

  const bridge = new memPkg.AutoMemoryBridge(backend, bridgeConfig);

  try {
    const result = await bridge.importFromAutoMemory();
    success(`Imported ${result.imported} entries (${result.skipped} skipped)`);
    dim(`├─ Backend entries: ${await backend.count()}`);
    dim(`├─ Learning: ${config.learningBridge.enabled ? 'active' : 'disabled'}`);
    dim(`├─ Graph: ${config.memoryGraph.enabled ? 'active' : 'disabled'}`);
    dim(`└─ Agent scopes: ${config.agentScopes.enabled ? 'active' : 'disabled'}`);
  } catch (err) {
    dim(`Import failed (non-critical): ${err.message}`);
  }

  await backend.shutdown();
}

async function doSync() {
  log('Syncing insights to auto memory files...');

  const memPkg = await loadMemoryPackage();
  if (!memPkg || !memPkg.AutoMemoryBridge) {
    dim('Memory package not available — skipping sync');
    return;
  }

  const config = readConfig();
  const backend = new JsonFileBackend(STORE_PATH);
  await backend.initialize();

  const entryCount = await backend.count();
  if (entryCount === 0) {
    dim('No entries to sync');
    await backend.shutdown();
    return;
  }

  const bridgeConfig = {
    workingDir: PROJECT_ROOT,
    syncMode: 'on-session-end',
  };

  if (config.learningBridge.enabled && memPkg.LearningBridge) {
    bridgeConfig.learning = {
      sonaMode: config.learningBridge.sonaMode,
      confidenceDecayRate: config.learningBridge.confidenceDecayRate,
      consolidationThreshold: config.learningBridge.consolidationThreshold,
    };
  }

  if (config.memoryGraph.enabled && memPkg.MemoryGraph) {
    bridgeConfig.graph = {
      pageRankDamping: config.memoryGraph.pageRankDamping,
      maxNodes: config.memoryGraph.maxNodes,
    };
  }

  const bridge = new memPkg.AutoMemoryBridge(backend, bridgeConfig);

  try {
    const syncResult = await bridge.syncToAutoMemory();
    success(`Synced ${syncResult.synced} entries to auto memory`);
    dim(`├─ Categories updated: ${syncResult.categories?.join(', ') || 'none'}`);
    dim(`└─ Backend entries: ${entryCount}`);

    // Curate MEMORY.md index with graph-aware ordering
    await bridge.curateIndex();
    success('Curated MEMORY.md index');
  } catch (err) {
    dim(`Sync failed (non-critical): ${err.message}`);
  }

  if (bridge.destroy) bridge.destroy();
  await backend.shutdown();
}

// ── doCapture: save verbatim last user prompt as highest-priority memory ──────
// Called before compaction. Saves to /tmp/legion_last_user_prompt.txt AND
// to the auto-memory store so it persists across sessions.

async function doCapture() {
  const memPkg = await loadMemoryPackage();

  // 1. Read last user prompt from /tmp/legion_conversation.txt
  const conversationPath = '/tmp/legion_conversation.txt';
  let lastPrompt = '';
  let sessionDuration = 0;

  try {
    if (existsSync(conversationPath)) {
      const content = readFileSync(conversationPath, 'utf-8');

      // Extract last user message block
      const matches = content.matchAll(/(?:^|\n)(?:>|\*)(.*?)(?=\n\n|\Z)/gs);
      let last = '';
      for (const m of matches) {
        const cleaned = m[1].trim();
        if (cleaned.length > 10) last = cleaned;
      }
      lastPrompt = last.slice(0, 2000);
      sessionDuration = content.length;
    }
  } catch (err) {
    dim(`Prompt extraction: ${err.message}`);
  }

  // 2. Write to /tmp/legion_last_user_prompt.txt (L0 layer reads this)
  const promptPath = '/tmp/legion_last_user_prompt.txt';
  if (lastPrompt && lastPrompt.length > 5) {
    writeFileSync(promptPath, lastPrompt, 'utf-8');
    dim(`Last prompt captured: ${lastPrompt.length} chars`);
  } else {
    writeFileSync(promptPath, 'NO_USER_PROMPT', 'utf-8');
    dim('No user prompt found in conversation');
  }

  // 3. Write compaction checkpoint (read by session-start-trigger.mjs)
  try {
    const checkpoint = {
      timestamp: new Date().toISOString(),
      sessionDuration,
      contextSize: sessionDuration,
      lastUserPrompt: lastPrompt || '',
    };
    writeFileSync('/tmp/legion_compaction_checkpoint.json', JSON.stringify(checkpoint, null, 2), 'utf-8');
  } catch (err) {
    dim(`Checkpoint write: ${err.message}`);
  }

  // 4. Save to auto-memory store if package available
  if (memPkg && memPkg.AutoMemoryBridge) {
    const config = readConfig();
    const backend = new JsonFileBackend(STORE_PATH);
    await backend.initialize();

    const bridgeConfig = { workingDir: PROJECT_ROOT, syncMode: 'on-session-end' };
    const bridge = new memPkg.AutoMemoryBridge(backend, bridgeConfig);

    if (lastPrompt && lastPrompt.length > 5) {
      const id = `last-prompt-${Date.now()}`;
      const entry = {
        id,
        type: 'episodic',
        namespace: 'session',
        content: lastPrompt,
        metadata: {
          capturedAt: Date.now(),
          accessCount: 0,
          lastAccessedAt: Date.now(),
          tags: ['last-prompt', 'source-of-truth'],
          sessionDuration,
        },
        tags: ['last-prompt', 'source-of-truth'],
        confidence: 0.99,
      };
      await backend.store(entry);
      success(`Saved last prompt (${lastPrompt.length} chars) to memory store`);
    }

    if (bridge.destroy) bridge.destroy();
    await backend.shutdown();
  } else {
    dim('Memory package not available — prompt saved to /tmp only');
  }

  success('Capture complete');
}

async function doStatus() {
  const memPkg = await loadMemoryPackage();
  const config = readConfig();

  console.log('\n=== Auto Memory Bridge Status ===\n');
  console.log(`  Package:        ${memPkg ? '✅ Available' : '❌ Not found'}`);
  console.log(`  Store:          ${existsSync(STORE_PATH) ? '✅ ' + STORE_PATH : '⏸ Not initialized'}`);
  console.log(`  LearningBridge: ${config.learningBridge.enabled ? '✅ Enabled' : '⏸ Disabled'}`);
  console.log(`  MemoryGraph:    ${config.memoryGraph.enabled ? '✅ Enabled' : '⏸ Disabled'}`);
  console.log(`  AgentScopes:    ${config.agentScopes.enabled ? '✅ Enabled' : '⏸ Disabled'}`);

  if (existsSync(STORE_PATH)) {
    try {
      const data = JSON.parse(readFileSync(STORE_PATH, 'utf-8'));
      console.log(`  Entries:        ${Array.isArray(data) ? data.length : 0}`);
    } catch { /* ignore */ }
  }

  console.log('');
}

// ============================================================================
// Main
// ============================================================================

const command = process.argv[2] || 'status';

// Suppress unhandled rejection warnings from dynamic import() failures
process.on('unhandledRejection', () => {});

try {
  switch (command) {
    case 'import': await doImport(); break;
    case 'sync': await doSync(); break;
    case 'capture': await doCapture(); break;
    case 'status': await doStatus(); break;
    default:
      console.log('Usage: auto-memory-hook.mjs <import|sync|capture|status>');
      break;
  }
} catch (err) {
  // Hooks must never crash Claude Code - fail silently
  try { dim(`Error (non-critical): ${err.message}`); } catch (_) {}
}
// Force clean exit — process.exitCode alone isn't enough if async errors override it
process.exit(0);
