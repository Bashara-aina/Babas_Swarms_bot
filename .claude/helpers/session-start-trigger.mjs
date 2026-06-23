#!/usr/bin/env node
/**
 * Session Start Trigger — 6-Layer Memory Initialization
 * Runs at SessionStart to boot memory systems and restore context.
 *
 * Part of the memory_inject.md bootstrap — loads all memory layers
 * so the agent starts with full context from previous sessions.
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync, readdirSync, statSync } from 'fs';
import { join, dirname, extname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = join(__dirname, '../..');
const DATA_DIR = join(PROJECT_ROOT, '.claude-flow', 'data');
const SESSION_DIR = join(DATA_DIR, 'sessions');
const METRICS_DIR = join(PROJECT_ROOT, '.claude-flow', 'metrics');
const MEMORY_BOOTSTRAP = join(PROJECT_ROOT, '.claude', 'memory_bootstrap.md');
const SESSION_FILE = join(DATA_DIR, 'current.json');
const LAST_SESSION = join(METRICS_DIR, 'last-session.json');

const CYAN = '\x1b[0;36m';
const GREEN = '\x1b[0;32m';
const YELLOW = '\x1b[0;33m';
const DIM = '\x1b[2m';
const RESET = '\x1b[0m';

const log = (msg) => console.log(`${CYAN}[SessionStart] ${msg}${RESET}`);
const ok = (msg) => console.log(`${GREEN}[SessionStart] ✓ ${msg}${RESET}`);
const warn = (msg) => console.log(`${YELLOW}[SessionStart] ⚠ ${msg}${RESET}`);
const dim = (msg) => console.log(`  ${DIM}${msg}${RESET}`);

// ── Memory Layer Paths ──────────────────────────────────────────────────────
// Actual data locations (2026-05-28 audit):
const MEMORY_LAYERS = {
  l1_checkpoints: join(DATA_DIR, 'checkpoints'),   // empty dir — sessions moved to sessions/
  l2_chromadb: join(PROJECT_ROOT, 'data', 'legion_chroma', 'chroma.sqlite3'),  // SQLite file
  l3_langmem: join(PROJECT_ROOT, '.claude'),        // .md files (2 found)
  l4_observation: join(PROJECT_ROOT, 'data', 'observations.db'),  // SQLite file
  l5_graphrag: join(DATA_DIR, 'auto-memory-store.json'),  // JSON with entries
  l6_mem0cloud: join(DATA_DIR, 'auto-memory-store.json'),  // same as L5
};

// ── Session ID Generation ─────────────────────────────────────────────────
function generateSessionId() {
  const now = new Date();
  const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');
  const timeStr = now.toISOString().slice(11, 19).replace(/:/g, '').replace(/T/, '');
  return `session-${dateStr}-${timeStr}-${Math.random().toString(36).slice(2, 6)}`;
}

// ── Ensure Directories Exist ───────────────────────────────────────────────
function ensureDirectories() {
  const dirs = [
    DATA_DIR, SESSION_DIR, METRICS_DIR,
    ...Object.values(MEMORY_LAYERS).filter(p => !extname(p)),
  ];
  for (const dir of dirs) {
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  }
}

// ── Initialize Memory Layer Index ───────────────────────────────────────────
function initMemoryLayerIndex() {
  const index = {};
  let totalEntries = 0;

  for (const [layer, path] of Object.entries(MEMORY_LAYERS)) {
    try {
      let exists = false;
      let entryCount = 0;
      const stat = existsSync(path) ? statSync(path) : null;

      if (stat) {
        exists = true;

        if (path.endsWith('.json')) {
          // JSON file — parse for entries array
          try {
            const data = JSON.parse(readFileSync(path, 'utf-8'));
            if (Array.isArray(data)) entryCount = data.length;
            else if (data.entries) entryCount = data.entries.length;
            else if (data.patterns) entryCount = data.patterns.length;
            else if (data.memories) entryCount = data.memories.length;
          } catch (e) { /* parse failed */ }
        } else if (path.endsWith('.sqlite3') || path.endsWith('.db')) {
          // SQLite database — report size instead of count
          entryCount = Math.round(stat.size / 1024); // KB
        } else if (stat.isDirectory()) {
          // Directory — count .json and .md files
          const files = readdirSync(path).filter(f =>
            f.endsWith('.json') || f.endsWith('.md')
          );
          entryCount = files.length;
        }
      }

      const label = path.endsWith('.json') ? 'json' :
                    path.endsWith('.sqlite3') ? 'sqlite' :
                    path.endsWith('.db') ? 'db' : 'dir';
      index[layer] = { path, files: entryCount, exists, type: label };
      totalEntries += entryCount;
    } catch (e) {
      index[layer] = { path, files: 0, error: e.message };
    }
  }

  return { index, totalEntries };
}

// ── Check Previous Session ─────────────────────────────────────────────────
function getPreviousSession() {
  try {
    if (existsSync(LAST_SESSION)) {
      const data = JSON.parse(readFileSync(LAST_SESSION, 'utf-8'));
      return data;
    }
  } catch (e) { /* ignore */ }
  return null;
}

// ── Get Recent Archives ────────────────────────────────────────────────────
function getRecentSessions(count = 3) {
  try {
    if (!existsSync(SESSION_DIR)) return [];
    const files = readdirSync(SESSION_DIR)
      .filter(f => f.startsWith('session-') && f.endsWith('.json'))
      .map(f => {
        const content = readFileSync(join(SESSION_DIR, f), 'utf-8');
        return JSON.parse(content);
      })
      .sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt))
      .slice(0, count);
    return files;
  } catch (e) { return []; }
}

// ── Generate Memory Bootstrap ────────────────────────────────────────────────
function generateMemoryBootstrap(session) {
  const bootstrap = [
    '---',
    `name: memory_bootstrap`,
    `description: Memory bootstrap — auto-injected at session start. Populates HOT memory from persistent stores. Generated by session-start-trigger.mjs. DO NOT edit manually.`,
    `mode: bootstrap`,
    `hidden: true`,
    '---',
    '',
    '# LEGION MEMORY BOOTSTRAP — AUTO-GENERATED',
    `_Generated at session start. Last refresh: ${new Date().toISOString()}_`,
    '',
    '## CURRENT SESSION',
    '',
    `- **Session ID**: ${session.id}`,
    `- **Started**: ${session.startedAt}`,
    `- **Previous Session**: ${session.previousSession ? `${session.previousSession.id} (${Math.round((session.previousSession.duration || 0) / 1000 / 60)}min)` : 'None'}`,
    `- **Recent Archives**: ${session.recentSessions.length} sessions`,
    '',
    '## MEMORY LAYERS (HOT → COLD)',
    '',
    '| Layer | Store | Entries | Status |',
    '|-------|-------|---------|--------|',
  ];

  for (const [layer, info] of Object.entries(session.memoryIndex || {})) {
    const layerName = layer.replace('l', 'L').replace('_', ' ');
    const entries = info.files || 0;
    const status = info.exists ? 'OK' : 'MISSING';
    const type = info.type || 'dir';
    const entryStr = type === 'sqlite' || type === 'db' ? `${entries}KB` : entries;
    bootstrap.push(`| ${layerName} | ${info.path.split('/').pop()} | ${entryStr} | ${status} |`);
  }

  // Add ranked context if available
  try {
    const rankedPath = join(DATA_DIR, 'ranked-context.json');
    if (existsSync(rankedPath)) {
      const ranked = JSON.parse(readFileSync(rankedPath, 'utf-8'));
      if (ranked.entries && ranked.entries.length > 0) {
        bootstrap.push('', '## HOT CONTEXT (from PageRank)', '');
        const top = ranked.entries.slice(0, 5);
        for (const entry of top) {
          const key = entry.key || entry.id || 'unknown';
          const score = entry.pageRank ? entry.pageRank.toFixed(4) : '?';
          bootstrap.push(`- \`${key}\` (PR: ${score})`);
        }
      }
    }
  } catch (e) { /* ignore */ }

  // Add route patterns if available
  try {
    const routePath = join(DATA_DIR, 'route-history.json');
    if (existsSync(routePath)) {
      const history = JSON.parse(readFileSync(routePath, 'utf-8'));
      if (history.entries && history.entries.length > 0) {
        bootstrap.push('', '## ROUTE PATTERNS', '');
        bootstrap.push(`${history.entries.length} patterns learned from previous sessions.`);
      }
    }
  } catch (e) { /* ignore */ }

  bootstrap.push('', '---');
  bootstrap.push('_This file is regenerated at every SessionStart._');

  return bootstrap.join('\n');
}

// ── Build Prior Session Content ─────────────────────────────────────────────
// Reads last user prompt + session state from previous session to populate
// the bootstrap with rich context for the new session.

function buildPriorSessionContent(prevSessionId) {
  let lastPrompt = "";
  let sessionSummary = "";
  let inProgressFiles = [];
  let decisions = [];

  // 1. Read last user prompt from pre-compact checkpoint
  try {
    const promptPath = '/tmp/legion_last_user_prompt.txt';
    if (existsSync(promptPath)) {
      const content = readFileSync(promptPath, 'utf-8').trim();
      if (content && content !== 'NO_USER_PROMPT' && content.length > 5) {
        lastPrompt = content;
      }
    }
  } catch (e) { /* ignore */ }

  // 2. Read compaction checkpoint for last prompt + decisions
  try {
    const ckptPath = '/tmp/legion_compaction_checkpoint.json';
    if (existsSync(ckptPath)) {
      const ckpt = JSON.parse(readFileSync(ckptPath, 'utf-8'));
      if (ckpt.last_user_prompt && ckpt.last_user_prompt.length > 5) {
        lastPrompt = ckpt.last_user_prompt;
      }
    }
  } catch (e) { /* ignore */ }

  // 3. Read prior session summary from Obsidian Sessions dir
  try {
    const sessionsDir = join(PROJECT_ROOT, '.wiki', 'Sessions');
    if (existsSync(sessionsDir)) {
      const files = readdirSync(sessionsDir)
        .filter(f => f.endsWith('.md') && !f.includes('-'))
        .map(f => ({ f, mtime: statSync(join(sessionsDir, f)).mtime.getTime() }))
        .sort((a, b) => b.mtime - a.mtime);
      if (files.length > 0) {
        const latest = files[0].f;
        const content = readFileSync(join(sessionsDir, latest), 'utf-8');
        // Extract user query field from frontmatter or body
        const queryMatch = content.match(/User Query\n(.+)/);
        if (queryMatch) sessionSummary = queryMatch[1].trim().slice(0, 500);
      }
    }
  } catch (e) { /* ignore */ }

  return { lastPrompt, sessionSummary, inProgressFiles, decisions };
}

// ── Generate Rich Memory Inject ────────────────────────────────────────────
// Builds memory_inject.md from prior session content + session notes.
// This is the authoritative session context for the new session.

function buildMemoryInject(session, priorContent) {
  const injectPath = join(PROJECT_ROOT, '.session_state', 'memory_inject.md');
  const { lastPrompt, sessionSummary } = priorContent;

  const lines = [
    '---',
    'name: memory_inject',
    `description: Session context bootstrap — auto-injected at session start from prior session. Generated by session-start-trigger.mjs.`,
    `session: ${session.id}`,
    `previous: ${session.previousSession?.id || 'none'}`,
    'mode: bootstrap',
    'hidden: true',
    '---',
    '',
    '# MEMORY INJECT — SESSION BOOTSTRAP',
    `_Generated at session start: ${new Date().toISOString()}_`,
    '',
    '## PRIOR SESSION CONTEXT',
    '',
    `**Previous Session:** ${session.previousSession?.id || 'none'} (${session.previousSession ? Math.round((session.previousSession.duration || 0) / 1000 / 60) + 'min)' : 'unknown)'}`,
    '',
  ];

  // Verbatim last user prompt — always include if available
  if (priorContent.lastPrompt && priorContent.lastPrompt.length > 5) {
    lines.push('## LAST USER PROMPT (AUTHORITATIVE)', '');
    lines.push('> ' + priorContent.lastPrompt.replace(/\n/g, '\n> '), '');
    lines.push('_This is the explicit user request being worked on._', '');
    lines.push('');
  }

  // Recent sessions summary
  if (priorContent.sessionSummary) {
    lines.push('## PRIOR SESSION SUMMARY', '');
    lines.push(priorContent.sessionSummary, '');
    lines.push('');
  }

  // In-progress files from prior session
  if (priorContent.inProgressFiles && priorContent.inProgressFiles.length > 0) {
    lines.push('## IN-PROGRESS FILES (carry-over)', '');
    for (const f of priorContent.inProgressFiles) {
      lines.push(`- ${f}`);
    }
    lines.push('');
  }

  // Decisions if captured
  if (priorContent.decisions && priorContent.decisions.length > 0) {
    lines.push('## KEY DECISIONS (carry-over)', '');
    for (const d of priorContent.decisions) {
      lines.push(`- ${d}`);
    }
    lines.push('');
  }

  // Read latest session note from obsidian if available
  try {
    const sessionsDir = join(PROJECT_ROOT, '.wiki', 'Sessions');
    if (existsSync(sessionsDir)) {
      const files = readdirSync(sessionsDir)
        .filter(f => f.match(/^\d{8}-\d{4}/))
        .map(f => ({ f, mtime: statSync(join(sessionsDir, f)).mtime.getTime() }))
        .sort((a, b) => b.mtime - a.mtime)
        .slice(0, 1);
      if (files.length > 0) {
        const latestSessionNote = files[0].f;
        const content = readFileSync(join(sessionsDir, latestSessionNote), 'utf-8');
        lines.push('## RECENT SESSION NOTE', '');
        lines.push(`_From: ${latestSessionNote}_`, '');
        lines.push(content.slice(0, 1500), '');
        lines.push('');
      }
    }
  } catch (e) { /* ignore */ }

  lines.push('---');
  lines.push('_This file is regenerated at every SessionStart._');

  const result = lines.join('\n');
  try {
    writeFileSync(injectPath, result);
    log(`Memory inject: ${result.length} chars written`);
  } catch (e) {
    warn(`Failed to write memory_inject.md: ${e.message}`);
  }
  return result;
}

// ── Initialize Session ───────────────────────────────────────────────────
async function initializeSession() {
  log('Booting 6-layer memory system...');
  ensureDirectories();

  // Check if session.js already created a session in the session-restore hook
  let existingSession = null;
  try {
    if (existsSync(SESSION_FILE)) {
      const raw = JSON.parse(readFileSync(SESSION_FILE, 'utf-8'));
      if (raw.id && raw.startedAt) existingSession = raw;
    }
  } catch { /* no existing session — fresh start */ }

  const sessionId = existingSession ? existingSession.id : generateSessionId();
  const startedAt = existingSession ? existingSession.startedAt : new Date().toISOString();
  const prevSession = getPreviousSession();
  const recentSessions = getRecentSessions(3);
  const memLayerInfo = initMemoryLayerIndex();

  const session = {
    id: sessionId,
    startedAt,
    cwd: PROJECT_ROOT,
    previousSession: prevSession ? {
      id: prevSession.id,
      endedAt: prevSession.endedAt,
      duration: prevSession.duration,
    } : null,
    recentSessions: recentSessions.map(s => ({
      id: s.id,
      startedAt: s.startedAt,
      duration: s.duration,
    })),
    memoryLayers: MEMORY_LAYERS,
    memoryIndex: memLayerInfo.index,
    context: existingSession?.context || { tasks: [], decisions: [], lastUserQuery: '', filesChanged: [] },
    metrics: existingSession?.metrics || { edits: 0, commands: 0, tasks: 0, errors: 0 },
  };

  writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2));

  // Update memory bootstrap with current session context
  const bootstrap = generateMemoryBootstrap(session);
  writeFileSync(MEMORY_BOOTSTRAP, bootstrap);

  // Build prior session content for rich memory inject
  const priorContent = buildPriorSessionContent();
  buildMemoryInject(session, priorContent);

  // Log startup info
  log(`Session: ${sessionId}`);
  if (prevSession) {
    dim(`Previous: ${prevSession.id} (${Math.round((prevSession.duration || 0) / 1000 / 60)}min)`);
  }
  dim(`Memory layers: ${memLayerInfo.totalEntries} entries indexed`);
  dim('Bootstrap: regenerated');

  // Check for memory bootstrap content
  if (existsSync(MEMORY_BOOTSTRAP)) {
    try {
      const bootstrap = readFileSync(MEMORY_BOOTSTRAP, 'utf-8');
      const sections = bootstrap.split('## ').filter(s => s.trim());
      dim(`Bootstrap: ${sections.length} sections`);
    } catch (e) {
      warn('Could not read memory_bootstrap.md');
    }
  }

  // Load route history for learned patterns
  const routeHistory = join(DATA_DIR, 'route-history.json');
  if (existsSync(routeHistory)) {
    try {
      const history = JSON.parse(readFileSync(routeHistory, 'utf-8'));
      if (history.entries && history.entries.length > 0) {
        dim(`Route patterns: ${history.entries.length} learned`);
      }
    } catch (e) { /* ignore */ }
  }

  // Load ranked context
  const rankedContext = join(DATA_DIR, 'ranked-context.json');
  if (existsSync(rankedContext)) {
    try {
      const ctx = JSON.parse(readFileSync(rankedContext, 'utf-8'));
      if (ctx.entries) {
        dim(`Ranked context: ${ctx.entries.length} entries`);
      }
    } catch (e) { /* ignore */ }
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
  if (existsSync(SESSION_FILE)) {
    const session = JSON.parse(readFileSync(SESSION_FILE, 'utf-8'));
    console.log(JSON.stringify(session, null, 2));
  } else {
    console.log('No active session');
  }
}

export { initializeSession };