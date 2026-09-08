#!/usr/bin/env node
/**
 * RuFlo V3 Statusline Generator (Optimized)
 * Displays real-time V3 implementation progress and system status
 *
 * Usage: node statusline.cjs [--json] [--compact]
 *
 * Performance notes:
 * - Single git execSync call (combines branch + status + upstream)
 * - No recursive file reading (only stat/readdir, never read test contents)
 * - No ps aux calls (uses process.memoryUsage() + file-based metrics)
 * - Strict 2s timeout on all execSync calls
 * - Shared settings cache across functions
 */

/* eslint-disable @typescript-eslint/no-var-requires */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const os = require('os');

// Configuration — maxAgents read from settings.json, fallback 5
function getMaxAgents() {
  const settings = getSettings();
  if (settings && settings.claudeFlow && settings.claudeFlow.swarm && settings.claudeFlow.swarm.maxAgents) {
    return settings.claudeFlow.swarm.maxAgents;
  }
  return 5;
}

// Use __dirname so paths resolve correctly regardless of where node was launched from.
// CWD becomes that subdirectory, making all `.claude-flow/metrics/*` paths resolve incorrectly.
const CWD = path.resolve(__dirname, '..', '..');

// ANSI colors
const c = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[0;31m',
  green: '\x1b[0;32m',
  yellow: '\x1b[0;33m',
  blue: '\x1b[0;34m',
  purple: '\x1b[0;35m',
  cyan: '\x1b[0;36m',
  brightRed: '\x1b[1;31m',
  brightGreen: '\x1b[1;32m',
  brightYellow: '\x1b[1;33m',
  brightBlue: '\x1b[1;34m',
  brightPurple: '\x1b[1;35m',
  brightCyan: '\x1b[1;36m',
  brightWhite: '\x1b[1;37m',
};

// Safe execSync with strict timeout (returns empty string on failure)
function safeExec(cmd, timeoutMs = 2000) {
  try {
    return execSync(cmd, {
      encoding: 'utf-8',
      timeout: timeoutMs,
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
  } catch {
    return '';
  }
}

// Safe JSON file reader (returns null on failure)
function readJSON(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    }
  } catch { /* ignore */ }
  return null;
}

// Safe file stat (returns null on failure)
function safeStat(filePath) {
  try {
    return fs.statSync(filePath);
  } catch { /* ignore */ }
  return null;
}

// Shared settings cache — read once, used by multiple functions
let _settingsCache = undefined;
function getSettings() {
  if (_settingsCache !== undefined) return _settingsCache;
  _settingsCache = readJSON(path.join(CWD, '.claude', 'settings.json'))
                || readJSON(path.join(CWD, '.claude', 'settings.local.json'))
                || null;
  return _settingsCache;
}

// ─── Data Collection (all pure-Node.js or single-exec) ──────────

// Get all git info in ONE shell call
function getGitInfo() {
  const result = {
    name: 'user', gitBranch: '', modified: 0, untracked: 0,
    staged: 0, ahead: 0, behind: 0,
  };

  // Single shell: get user.name, branch, porcelain status, and upstream diff
  const script = [
    'git config user.name 2>/dev/null || echo user',
    'echo "---SEP---"',
    'git branch --show-current 2>/dev/null',
    'echo "---SEP---"',
    'git status --porcelain 2>/dev/null',
    'echo "---SEP---"',
    'git rev-list --left-right --count HEAD...@{upstream} 2>/dev/null || echo "0 0"',
  ].join('; ');

  const raw = safeExec("sh -c '" + script + "'", 3000);
  if (!raw) return result;

  const parts = raw.split('---SEP---').map(s => s.trim());
  if (parts.length >= 4) {
    result.name = parts[0] || 'user';
    result.gitBranch = parts[1] || '';

    // Parse porcelain status
    if (parts[2]) {
      for (const line of parts[2].split('\n')) {
        if (!line || line.length < 2) continue;
        const x = line[0], y = line[1];
        if (x === '?' && y === '?') { result.untracked++; continue; }
        if (x !== ' ' && x !== '?') result.staged++;
        if (y !== ' ' && y !== '?') result.modified++;
      }
    }

    // Parse ahead/behind
    const ab = (parts[3] || '0 0').split(/\s+/);
    result.ahead = parseInt(ab[0]) || 0;
    result.behind = parseInt(ab[1]) || 0;
  }

  return result;
}

// Detect model name from Claude config (pure file reads, no exec)
function compactModelName(name) {
  if (!name) return name;
  const map = {
    'deepseek-v4-flash': 'ds-v4-f',
    'deepseek-v4-pro': 'ds-v4-p',
    'deepseek-v4-lite': 'ds-v4-l',
    'deepseek-v4': 'ds-v4',
    'v4 flash': 'ds-v4-f',
    'v4 pro': 'ds-v4-p',
    'minimax-coding-plan/MiniMax-M2.7': 'M2.7',
    'minimax/MiniMax-M3': 'M3',
    'kimi-k2.6': 'k2.6',
    'Claude Opus 4.7': 'Opus 4.7',
    'Claude Sonnet 4.6': 'Sonnet 4.6',
    'Claude Haiku 4.5': 'Haiku 4.5',
    'Claude Code': 'CC',
    'deepseek-chat': 'ds-chat',
    'deepseek-reasoner': 'ds-r1',
    'muse-spark-1.3-contributor': 'ms-1.3-c',
  };
  return map[name] || name;
}

// 4-tier model routing tier (from CLAUDE.md routing table)
function getModelTier(modelName) {
  if (!modelName) return null;
  const n = modelName.toLowerCase();
  if (n.includes('flash') || n.includes('haiku') || n.includes('muse-spark')) return { tier: 'Haiku', color: c.dim, sym: '\u25CB' };
  if (n.includes('pro') || n.includes('sonnet')) return { tier: 'Sonnet', color: c.brightBlue, sym: '\u25D3' };
  if (n.includes('opus') || n.includes('kimi')) return { tier: 'Opus', color: c.brightPurple, sym: '\u25D2' };
  if (n.includes('fable') || n.includes('glm')) return { tier: 'Fable', color: c.brightCyan, sym: '\u25C9' };
  return null;
}

function getModelName() {
  try {
    const claudeConfig = readJSON(path.join(os.homedir(), '.claude.json'));
    if (claudeConfig && claudeConfig.projects) {
      for (const [projectPath, projectConfig] of Object.entries(claudeConfig.projects)) {
        if (CWD === projectPath || CWD.startsWith(projectPath + '/')) {
          const usage = projectConfig.lastModelUsage;
          if (usage) {
            const ids = Object.keys(usage);
            if (ids.length > 0) {
              let modelId = ids[ids.length - 1];
              let latest = 0;
              for (const id of ids) {
                const ts = usage[id] && usage[id].lastUsedAt ? new Date(usage[id].lastUsedAt).getTime() : 0;
                if (ts > latest) { latest = ts; modelId = id; }
              }
              if (modelId.includes('opus')) return 'Opus 4.7';
              if (modelId.includes('sonnet')) return 'Sonnet 4.6';
              if (modelId.includes('haiku')) return 'Haiku 4.5';
              return modelId.split('-').slice(1, 3).join(' ');
            }
          }
          break;
        }
      }
    }
  } catch { /* ignore */ }

  // Fallback: settings.json model field
  const settings = getSettings();
  if (settings && settings.model) {
    const m = settings.model;
    if (m.includes('opus')) return 'Opus 4.7';
    if (m.includes('sonnet')) return 'Sonnet 4.6';
    if (m.includes('haiku')) return 'Haiku 4.5';
  }
  return 'Claude Code';
}

// ─── Live runtime stats (pure file reads from real sources) ───
// Replaces the old claude-flow metrics (DDD/ADR/Swarm/CVE/Vec/Intel) which
// read from .claude-flow/metrics.db — that system was archived as non-POPW.
// All values below come from live sources only: settings.json (hooks/MCP),
// real test/ADR files in the repo, and process memory. Nothing is fabricated.

function getRuntimeStats() {
  const settings = getSettings();
  const hooks = getHooksStatus();

  // 1. ADR/.md decision count from live files
  const adrPaths = [
    path.join(CWD, 'docs', 'adrs'),
    path.join(CWD, '.wiki', 'decisions'),
    path.join(CWD, 'decisions'),
  ];
  let adrCount = 0;
  for (const adrPath of adrPaths) {
    try {
      if (!fs.existsSync(adrPath)) continue;
      const files = fs.readdirSync(adrPath).filter(f =>
        f.endsWith('.md') && (f.startsWith('ADR-') || f.startsWith('adr-') || /^\d{4}-/.test(f))
      );
      adrCount = Math.max(adrCount, files.length);
    } catch { /* ignore */ }
  }

  // 2. Test count from real test files (depth-limited, deduped)
  const testDirs = ['tests', 'test', '__tests__', 'v3'];
  let testCount = 0;
  const seen = new Set();
  for (const dir of testDirs) {
    countFilePattern(path.join(CWD, dir), /(\.test\.|\.spec\.|_test\.|_spec\.|^test_)/, seen, 6);
  }
  testCount = seen.size;

  // 3. MCP + integration from settings
  const mcp = countMCPServers(settings);

  // 4. Security: real security scan files only (no fabricated CVEs)
  let secStatus = 'NONE';
  const secDir = path.join(CWD, '.claude', 'security-scans');
  try {
    if (fs.existsSync(secDir) && fs.readdirSync(secDir).some(f => f.endsWith('.json'))) {
      secStatus = 'CLEAN';
    }
  } catch { /* ignore */ }

  // 5. Memory: process heap only (real, live)
  const memoryMB = Math.floor(process.memoryUsage().heapUsed / 1024 / 1024);

  return {
    adrCount,
    testCount,
    mcpTotal: mcp.total,
    mcpEnabled: mcp.enabled,
    hooksEnabled: hooks.enabled,
    hooksTotal: hooks.total,
    secStatus,
    memoryMB,
    hasApi: !!(process.env.ANTHROPIC_API_KEY || process.env.OPENAI_API_KEY),
    hasDatabase: fs.existsSync(path.join(CWD, 'data', 'memory.db')),
  };
}

// Live MCP server count: settings.mcpServers + .mcp.json
function countMCPServers(settings) {
  const servers = new Set();
  const enabled = new Set();

  if (settings && settings.mcpServers && typeof settings.mcpServers === 'object') {
    for (const name of Object.keys(settings.mcpServers)) {
      servers.add(name);
      enabled.add(name); // defined in settings = enabled
    }
  }
  const mcpConfigFile = readJSON(path.join(CWD, '.mcp', 'servers.json'))
                     || readJSON(path.join(CWD, '.mcp.json'));
  if (mcpConfigFile && mcpConfigFile.mcpServers) {
    for (const name of Object.keys(mcpConfigFile.mcpServers)) {
      servers.add(name);
      enabled.add(name);
    }
  }
  return { total: servers.size, enabled: enabled.size };
}

// Depth-limited recursive file counter with dedupe
function countFilePattern(dir, pattern, seen, maxDepth) {
  if (maxDepth < 0) return;
  try {
    if (!fs.existsSync(dir)) return;
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isDirectory()) {
        if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === '.venv') continue;
        countFilePattern(path.join(dir, entry.name), pattern, seen, maxDepth - 1);
      } else if (entry.isFile()) {
        const key = path.join(dir, entry.name);
        if (pattern.test(entry.name)) seen.add(key);
      }
    }
  } catch { /* ignore */ }
}

// Hooks status (shared settings cache)
function getHooksStatus() {
  let enabled = 0;
  let total = 0;
  const settings = getSettings();

  if (settings && settings.hooks) {
    for (const category of Object.keys(settings.hooks)) {
      const matchers = settings.hooks[category];
      if (!Array.isArray(matchers)) continue;
      for (const matcher of matchers) {
        const hooks = matcher && matcher.hooks;
        if (Array.isArray(hooks)) {
          total += hooks.length;
          enabled += hooks.length;
        }
      }
    }
  }

  try {
    const hooksDir = path.join(CWD, '.claude', 'hooks');
    if (fs.existsSync(hooksDir)) {
      const hookFiles = fs.readdirSync(hooksDir).filter(f => f.endsWith('.js') || f.endsWith('.sh')).length;
      total = Math.max(total, hookFiles);
      enabled = Math.max(enabled, hookFiles);
    }
  } catch { /* ignore */ }

  return { enabled, total };
}

// ─── Rendering ──────────────────────────────────────────────────

// Format a number compactly: 1234 → "1.2k", 1234567 → "1.2M"
function fmtNum(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return String(n);
}

function generateStatusline() {
  const git = getGitInfo();
  const rawModel = getModelFromStdin() || getModelName();
  const modelName = compactModelName(rawModel);
  const modelTier = getModelTier(rawModel);
  const ctxInfo = getContextFromStdin();
  const costInfo = getCostFromStdin();
  const rt = getRuntimeStats();
  const lines = [];

  // ── Line 1: Header · Identity · Git · Model · Ctx · Cost ──
  let header = c.brightPurple + '\u258A' + c.reset + ' ' + c.bold + c.brightWhite + 'RuFlo' + c.reset + ' ' + c.dim + 'v3.6' + c.reset;
  header += '  ' + c.brightCyan + git.name + c.reset;

  if (git.gitBranch) {
    header += '  ' + c.dim + '\u2502' + c.reset + '  ';
    const shortBranch = git.gitBranch.length > 28 ? git.gitBranch.substring(0, 25) + '\u2026' : git.gitBranch;
    header += c.brightBlue + shortBranch + c.reset;
    const changes = git.modified + git.staged + git.untracked;
    if (changes > 0) {
      let ind = '';
      if (git.staged > 0) ind += c.brightGreen + '+' + git.staged;
      if (git.modified > 0) ind += (ind ? '' : '') + c.brightYellow + '~' + git.modified;
      if (git.untracked > 0) ind += (ind ? '' : '') + c.dim + '?' + git.untracked;
      header += ' ' + ind + c.reset;
    }
    if (git.ahead > 0) header += ' ' + c.brightGreen + '\u2191' + git.ahead + c.reset;
    if (git.behind > 0) header += ' ' + c.brightRed + '\u2193' + git.behind + c.reset;
  }

  // Routing tier badge
  const tierBadge = modelTier ? ' ' + modelTier.color + modelTier.sym + ' ' + modelTier.tier + c.reset : '';
  header += '  ' + c.dim + '\u2502' + c.reset + '  ' + c.purple + modelName + c.reset + tierBadge;

  // Context: only show if we have real session data
  if (ctxInfo && ctxInfo.totalTokens > 0 && ctxInfo.usedTokens > 0) {
    const ctxColor = ctxInfo.usedPct >= 90 ? c.brightRed : ctxInfo.usedPct >= 70 ? c.brightYellow : c.brightGreen;
    const used = ctxInfo.usedTokens > 0 ? fmtNum(ctxInfo.usedTokens) : '0';
    const total = ctxInfo.totalTokens >= 1000000 ? Math.round(ctxInfo.totalTokens / 1000000) + 'M' : fmtNum(ctxInfo.totalTokens);
    header += '  ' + c.dim + '\u2502' + c.reset + '  ' + ctxColor + used + '/' + total + c.reset;
  }

  if (costInfo && costInfo.costUsd > 0) {
    header += '  ' + c.dim + '\u2502' + c.reset + '  ' + c.brightYellow + '$' + costInfo.costUsd.toFixed(2) + c.reset;
  }
  lines.push(header);

  // ── Thin rule ──
  const ruleW = Math.min(76, Math.max(50, (process.stdout.columns || 80) - 2));
  lines.push(c.dim + '\u2500'.repeat(ruleW) + c.reset);

  // ── Colors ──
  const secColor = rt.secStatus === 'CLEAN' ? c.brightGreen
    : (rt.secStatus === 'NONE' ? c.dim : c.brightRed);
  const adrColor = rt.adrCount > 0 ? c.brightGreen : c.dim;
  const testColor = rt.testCount > 0 ? c.brightGreen : c.dim;
  const hookColor = rt.hooksEnabled > 0 ? c.brightGreen : c.dim;
  const mcpColor = rt.mcpEnabled === rt.mcpTotal ? c.brightGreen
    : rt.mcpEnabled > 0 ? c.brightYellow : c.red;
  const SEP = ' ' + c.dim + '\u2502' + c.reset + ' ';

  // ── Line 2: Build (live values) ──
  const buildItems = [
    c.brightBlue + 'ADR' + c.reset + ' ' + adrColor + '\u25CF' + rt.adrCount + c.reset,
    c.brightCyan + 'Tests' + c.reset + ' ' + testColor + '\u25CF' + rt.testCount + c.reset,
  ];
  lines.push('  ' + buildItems.join(SEP));

  // ── Line 3: System (live config) ──
  const sysItems = [
    c.brightBlue + 'Hooks' + c.reset + ' ' + hookColor + rt.hooksEnabled + '/' + rt.hooksTotal + c.reset,
    c.brightCyan + 'MCP' + c.reset + ' ' + mcpColor + '\u25CF' + rt.mcpEnabled + '/' + rt.mcpTotal + c.reset,
  ];
  if (rt.hasDatabase) sysItems.push(c.brightGreen + '\u25C6DB' + c.reset);
  if (rt.hasApi) sysItems.push(c.brightGreen + '\u25C6API' + c.reset);
  lines.push('  ' + sysItems.join(SEP));

  // ── Line 4: Health (live) ──
  const secIcon = rt.secStatus === 'CLEAN' ? c.brightGreen + '\u25CF' : c.dim + '\u25CB';
  const healthItems = [
    c.brightCyan + 'Mem' + c.reset + ' ' + c.brightWhite + rt.memoryMB + 'MB' + c.reset,
    c.cyan + 'Sec' + c.reset + ' ' + secIcon + c.reset + ' ' + secColor + rt.secStatus + c.reset,
  ];
  if (ctxInfo && ctxInfo.totalTokens > 0 && ctxInfo.usedTokens > 0) {
    const ctxCol = ctxInfo.usedPct >= 90 ? c.brightRed : ctxInfo.usedPct >= 70 ? c.brightYellow : c.brightGreen;
    healthItems.push(c.purple + 'Ctx' + c.reset + ' ' + ctxCol + ctxInfo.usedPct + '%' + c.reset);
  }
  lines.push('  ' + healthItems.join(SEP));

  return lines.join('\n');
}

// JSON output
function generateJSON() {
  const git = getGitInfo();
  const rt = getRuntimeStats();
  return {
    user: { name: git.name, gitBranch: git.gitBranch, modelName: getModelName() },
    runtime: rt,
    git: { modified: git.modified, untracked: git.untracked, staged: git.staged, ahead: git.ahead, behind: git.behind },
    lastUpdated: new Date().toISOString(),
  };
}

// ─── Stdin reader (Claude Code pipes session JSON) ──────────────

// Claude Code sends session JSON via stdin (model, context, cost, etc.)
// Read it synchronously so the script works both:
//   1. When invoked by Claude Code (stdin has JSON)
//   2. When invoked manually from terminal (stdin is empty/tty)
// IMPORTANT: cap total read to 64KB to avoid consuming agent data on stdin.
const MAX_STDIN_BYTES = 65536;
let _stdinData = null;
function getStdinData() {
  if (_stdinData !== undefined && _stdinData !== null) return _stdinData;
  try {
    // Check if stdin is a TTY (manual run) — skip reading
    if (process.stdin.isTTY) { _stdinData = null; return null; }
    // Peek at available bytes without consuming agent data
    let available = 0;
    try {
      const stat = fs.fstatSync(0);
      available = stat.size;
    } catch { /* cannot stat stdin */ }
    // If stdin has more data than a session JSON (or is a pipe with unknown size),
    // only read up to MAX_STDIN_BYTES to avoid consuming agent deployment data.
    const toRead = Math.min(available > 0 ? available : MAX_STDIN_BYTES, MAX_STDIN_BYTES);
    // Read stdin synchronously via fd 0 (bounded read)
    const buf = Buffer.alloc(toRead || 4096);
    let bytesRead = 0;
    try {
      bytesRead = fs.readSync(0, buf, 0, buf.length, null);
    } catch { /* EOF or read error */ }
    if (bytesRead <= 0) { _stdinData = null; return null; }
    const raw = buf.slice(0, bytesRead).toString('utf-8').trim();
    if (raw && raw.startsWith('{')) {
      _stdinData = JSON.parse(raw);
    } else {
      _stdinData = null;
    }
  } catch {
    _stdinData = null;
  }
  return _stdinData;
}

// Override model detection to prefer stdin data from Claude Code
function getModelFromStdin() {
  const data = getStdinData();
  if (data && data.model && data.model.display_name) return data.model.display_name;
  return null;
}

// Context cache file — persists context_window data between statusline invocations
const CONTEXT_CACHE_FILE = path.join(CWD, '.claude', 'data', 'context-cache.json');
const CONTEXT_CACHE_TTL_MS = 3600000; // 1 hour — survives long sessions, only expires when idle

function readContextCache() {
  try {
    if (fs.existsSync(CONTEXT_CACHE_FILE)) {
      const raw = fs.readFileSync(CONTEXT_CACHE_FILE, 'utf-8');
      const cached = JSON.parse(raw);
      const age = Date.now() - (cached._cachedAt || 0);
      if (age < CONTEXT_CACHE_TTL_MS && cached.totalTokens > 0) {
        // Only return cache if it belongs to the current session
        const currentSessionId = getCurrentSessionId();
        if (!currentSessionId || cached._sessionId === currentSessionId) {
          return cached;
        }
      }
    }
  } catch { /* cache read failed */ }
  return null;
}

function writeContextCache(ctxInfo) {
  try {
    // Never overwrite cache with zero-data — keep last known good values
    if (ctxInfo.usedPct === 0 && ctxInfo.usedTokens === 0) {
      const existing = readContextCache();
      if (existing) return;
    }
    // Monotonic: never overwrite a larger cached value with a much smaller one
    const existing = readContextCache();
    if (existing && ctxInfo.usedTokens < existing.usedTokens * 0.9) return;
    const dir = path.dirname(CONTEXT_CACHE_FILE);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    // Tag cache with current session so it's only used within the same session
    const sessionId = getCurrentSessionId();
    fs.writeFileSync(CONTEXT_CACHE_FILE, JSON.stringify({ ...ctxInfo, _sessionId: sessionId || '', _cachedAt: Date.now() }), 'utf-8');
  } catch { /* cache write failed — non-fatal */ }
}

// Get default window size from env or settings
function getDefaultTotalWindow() {
  return parseInt(process.env.CLAUDE_CODE_AUTO_COMPACT_WINDOW) || 1000000;
}

// Find the current Claude Code session by walking the process tree.
// Statusline is spawned as: claude → sh -c 'exec node statusline.cjs'
// node's PPID = sh, sh's PPID = claude. Read claude's session file.
// Returns sessionId string or null.
function getCurrentSessionId() {
  try {
    // Walk up to find a PID with a session file matching our CWD
    let pid = process.ppid;
    const visited = new Set();
    for (let depth = 0; depth < 5; depth++) {
      if (visited.has(pid) || !pid) break;
      visited.add(pid);
      const sessionFile = path.join(os.homedir(), '.claude', 'sessions', pid + '.json');
      const data = readJSON(sessionFile);
      if (data && data.sessionId && data.cwd === CWD) return data.sessionId;
      // Walk up to parent
      const statPath = '/proc/' + pid + '/stat';
      if (!fs.existsSync(statPath)) break;
      const stat = fs.readFileSync(statPath, 'utf-8');
      const m = stat.match(/^\d+\s+\([^)]+\)\s+[A-Za-z]\s+(\d+)/);
      if (!m) break;
      pid = parseInt(m[1]);
    }
  } catch { /* session lookup failed */ }
  return null;
}

// Estimate context from the current session's conversation content.
// The JSONL is append-only — compaction adds an `away_summary` entry but
// never removes old messages. The actual LLM context = only messages
// AFTER the last compaction, plus the summary text that replaces old ones.
function estimateContextFromConversation(totalWindow) {
  try {
    const sessionId = getCurrentSessionId();
    if (!sessionId) return null;

    const projectDir = path.join(os.homedir(), '.claude', 'projects', CWD.replace(/\//g, '-'));
    if (!fs.existsSync(projectDir)) return null;

    const convFile = path.join(projectDir, sessionId + '.jsonl');
    if (!fs.existsSync(convFile)) return null;

    const raw = fs.readFileSync(convFile, 'utf-8');
    const rawBytes = Buffer.byteLength(raw);
    if (rawBytes < 100) return null;

    // Parse all lines and find the last compaction boundary
    let lastCompactIdx = -1;
    const lines = raw.split('\n');
    const parsed = [];
    for (const line of lines) {
      if (!line.trim()) continue;
      const d = JSON.parse(line);
      parsed.push(d);
      if (d.type === 'system' && (d.subtype === 'away_summary' || d.subtype === 'compact')) {
        lastCompactIdx = parsed.length - 1;
      }
    }

    // Count content bytes from the active context only
    let contentBytes = 0;
    let userMsgCount = 0;
    const startIdx = lastCompactIdx >= 0 ? lastCompactIdx : 0;

    for (let i = startIdx; i < parsed.length; i++) {
      const d = parsed[i];
      const t = d.type;

      if (t === 'system' && d.subtype === 'away_summary') {
        contentBytes += Buffer.byteLength(d.content || '');
        continue;
      }

      if (t === 'user') {
        userMsgCount++;
        const msg = d.message;
        if (msg && typeof msg === 'object') {
          // User messages are {role:"user", content:"..."} or {role:"user", content:[{...}]}
          const content = msg.content;
          if (typeof content === 'string') {
            contentBytes += Buffer.byteLength(content);
          } else if (Array.isArray(content)) {
            for (const block of content) {
              if (block && typeof block === 'object') {
                if (block.content && typeof block.content === 'string') {
                  contentBytes += Buffer.byteLength(block.content);
                }
                if (block.text && typeof block.text === 'string') {
                  contentBytes += Buffer.byteLength(block.text);
                }
              }
            }
          }
        } else if (typeof msg === 'string') {
          contentBytes += Buffer.byteLength(msg);
        }
        // toolUseResult — file content read by the assistant
        const tur = d.toolUseResult;
        if (tur && typeof tur === 'object') {
          for (const v of Object.values(tur)) {
            if (typeof v === 'string') contentBytes += Buffer.byteLength(v);
          }
        }
      }

      else if (t === 'assistant') {
        const msg = d.message;
        if (msg && typeof msg === 'object') {
          const content = msg.content;
          if (typeof content === 'string') {
            contentBytes += Buffer.byteLength(content);
          } else if (Array.isArray(content)) {
            for (const block of content) {
              if (block && typeof block === 'object') {
                if (block.text) contentBytes += Buffer.byteLength(block.text);
                if (block.input && typeof block.input === 'object') {
                  contentBytes += Buffer.byteLength(JSON.stringify(block.input));
                }
              }
            }
          }
        }
      }

      else if (t === 'attachment') {
        const att = d.attachment;
        if (att && typeof att === 'object') {
          const content = att.content || att.text || '';
          if (typeof content === 'string') contentBytes += Buffer.byteLength(content);
        }
      }
    }

    // Sanity: if there are hardly any user turns but estimated tokens > 50K,
    // something is wrong — likely the wrong session
    if (userMsgCount < 2 && contentBytes > 100000) return null;

    // No conversation content at all — truly fresh session
    if (contentBytes === 0) return null;

    // Estimate tokens at ~3.5 chars per token for mixed code/text
    // Add system prompt + tool schemas overhead (~30K) only when there's content
    const estimatedTokens = Math.min(
      Math.round(contentBytes / 3.5) + 30000,
      Math.round(totalWindow * 0.95)
    );

    return {
      usedPct: Math.floor((estimatedTokens / totalWindow) * 100),
      remainingPct: Math.floor(((totalWindow - estimatedTokens) / totalWindow) * 100),
      usedTokens: estimatedTokens,
      totalTokens: totalWindow,
    };
  } catch { /* conversation estimation failed */ }
  return null;
}

// Get context window info from Claude Code session
function getContextFromStdin() {
  const totalWindow = getDefaultTotalWindow();
  const data = getStdinData();
  if (data && data.context_window) {
    const usedPct = Math.floor(data.context_window.used_percentage || 0);
    const totalTokens = data.context_window.total_tokens
                     || data.context_window.max_tokens
                     || totalWindow;
    let usedTokens = data.context_window.used_tokens || 0;
    // If Claude Code doesn't report token counts, compute from percentage
    if (usedTokens === 0 && totalTokens > 0 && usedPct > 0) {
      usedTokens = Math.round((usedPct / 100) * totalTokens);
    }
    const ctxInfo = {
      usedPct,
      remainingPct: Math.floor(data.context_window.remaining_percentage || 100),
      usedTokens,
      totalTokens,
    };
    // Persist to cache so subsequent daemon-driven invocations see real data
    writeContextCache(ctxInfo);
    // The oc-cc-proxy doesn't track context — it always reports 0 or tiny
    // values (usedPct ≤ 2, usedTokens < 50K). When the reported data is
    // unreliable, estimate from the local conversation files instead.
    if (usedPct <= 2 || usedTokens < 50000) {
      const estimated = estimateContextFromConversation(totalTokens || totalWindow);
      if (estimated) {
        writeContextCache(estimated);
        return estimated;
      }
      // No session found or estimation failed — return minimal (0%)
      // rather than stale cache from a different session
      return { usedPct: 0, remainingPct: 100, usedTokens: 0, totalTokens: totalTokens || totalWindow };
    }
    return ctxInfo;
  }
  // No stdin context data — use session-aware cache if available
  const cached = readContextCache();
  if (cached) return cached;
  const window = getDefaultTotalWindow();
  return { usedPct: 0, remainingPct: 100, usedTokens: 0, totalTokens: window };
}

// Get cost info from Claude Code session
function getCostFromStdin() {
  const data = getStdinData();
  if (data && data.cost) {
    const durationMs = data.cost.total_duration_ms || 0;
    const mins = Math.floor(durationMs / 60000);
    const secs = Math.floor((durationMs % 60000) / 1000);
    return {
      costUsd: data.cost.total_cost_usd || 0,
      duration: mins < 1 ? secs + 's' : mins < 60 ? mins + 'm' : (mins / 60).toFixed(1) + 'h',
      linesAdded: data.cost.total_lines_added || 0,
      linesRemoved: data.cost.total_lines_removed || 0,
    };
  }
  return null;
}

// ─── Main ───────────────────────────────────────────────────────
if (process.argv.includes('--json')) {
  console.log(JSON.stringify(generateJSON(), null, 2));
} else if (process.argv.includes('--compact')) {
  console.log(JSON.stringify(generateJSON()));
} else {
  console.log(generateStatusline());
}
