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
  };
  return map[name] || name;
}

// 4-tier model routing tier (from CLAUDE.md routing table)
function getModelTier(modelName) {
  if (!modelName) return null;
  const n = modelName.toLowerCase();
  if (n.includes('flash') || n.includes('haiku')) return { tier: 'Haiku', color: c.dim, sym: '\u25CB' };
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

// Get learning stats from real data sources (no heuristics)
function getLearningStats() {
  let patterns = 0;
  let sessions = 0;

  // 1. Count real patterns from intelligence pattern store
  const patternStorePath = path.join(CWD, '.claude-flow', 'data', 'patterns.json');
  try {
    if (fs.existsSync(patternStorePath)) {
      const data = JSON.parse(fs.readFileSync(patternStorePath, 'utf-8'));
      if (Array.isArray(data)) patterns = data.length;
      else if (data && data.patterns) patterns = Array.isArray(data.patterns) ? data.patterns.length : Object.keys(data.patterns).length;
    }
  } catch { /* ignore */ }

  // 2. Count patterns from auto-memory-store (real entries, not file size)
  if (patterns === 0) {
    const autoStorePath = path.join(CWD, '.claude-flow', 'data', 'auto-memory-store.json');
    try {
      if (fs.existsSync(autoStorePath)) {
        const data = JSON.parse(fs.readFileSync(autoStorePath, 'utf-8'));
        if (Array.isArray(data)) patterns = data.length;
        else if (data && data.entries) patterns = data.entries.length;
      }
    } catch { /* ignore */ }
  }

  // 3. Count patterns from memory.db using row count (sqlite header bytes 28-31)
  if (patterns === 0) {
    const memoryPaths = [
      path.join(CWD, '.claude-flow', 'memory.db'),
      path.join(CWD, 'data', 'memory.db'),
      path.join(CWD, '.swarm', 'memory.db'),
    ];
    for (const dbPath of memoryPaths) {
      try {
        if (fs.existsSync(dbPath)) {
          // Read SQLite header: page count at offset 28 (4 bytes big-endian)
          const fd = fs.openSync(dbPath, 'r');
          const buf = Buffer.alloc(4);
          fs.readSync(fd, buf, 0, 4, 28);
          fs.closeSync(fd);
          const pageCount = buf.readUInt32BE(0);
          // Each page typically holds ~10-50 rows; use page count as conservative estimate
          // But report 0 if DB exists but has only schema pages (< 3)
          patterns = pageCount > 2 ? pageCount - 2 : 0;
          break;
        }
      } catch { /* ignore */ }
    }
  }

  // 4. Count real session files from claude-flow (167 entries) — checked first (more populated)
  try {
    const cfSessDir = path.join(CWD, '.claude-flow', 'sessions');
    if (fs.existsSync(cfSessDir)) {
      sessions = fs.readdirSync(cfSessDir).filter(f => f.endsWith('.json')).length;
    }
  } catch { /* ignore */ }

  // 5. Fallback: count session files from ~/.claude/sessions
  if (sessions === 0) {
    try {
      const sessDir = path.join(CWD, '.claude', 'sessions');
      if (fs.existsSync(sessDir)) {
        sessions = fs.readdirSync(sessDir).filter(f => f.endsWith('.json')).length;
      }
    } catch { /* ignore */ }
  }

  return { patterns, sessions };
}

// V3 progress from metrics files (pure file reads)
function getV3Progress() {
  const learning = getLearningStats();

  const dddData = readJSON(path.join(CWD, '.claude-flow', 'metrics', 'ddd-progress.json'));
  let dddProgress = dddData ? (dddData.progress || 0) : 0;
  let domainsCompleted = 0;
  let totalDomains = 0;

  // Compute completed from actual domain scores when available (threshold >= 50)
  if (dddData && dddData.domains && typeof dddData.domains === 'object') {
    const scores = Object.values(dddData.domains).filter(v => typeof v === 'number');
    totalDomains = scores.length;
    domainsCompleted = scores.filter(s => s >= 50).length;
    dddProgress = totalDomains > 0 ? Math.floor((domainsCompleted / totalDomains) * 100) : 0;
  } else if (dddData && typeof dddData.total === 'number') {
    // Fallback to explicit completed/total fields from file
    domainsCompleted = typeof dddData.completed === 'number' ? dddData.completed : 0;
    totalDomains = dddData.total;
  }
  // else: both stay 0 — no fabricated data
  return {
    domainsCompleted, totalDomains, dddProgress,
    patternsLearned: learning.patterns,
    sessionsCompleted: learning.sessions,
  };
}

// Security status (pure file reads)
function getSecurityStatus() {
  const auditData = readJSON(path.join(CWD, '.claude-flow', 'security', 'audit-status.json'));
  if (auditData) {
    const auditDate = auditData.lastAudit || auditData.lastScan;
    const totalCves = auditData.totalCves || 0;
    if (!auditDate) {
      return { status: 'PENDING', cvesFixed: 0, totalCves };
    }
    const auditAge = Date.now() - new Date(auditDate).getTime();
    const isStale = auditAge > 7 * 24 * 60 * 60 * 1000;
    return {
      status: isStale ? 'STALE' : (auditData.status || 'PENDING'),
      cvesFixed: auditData.cvesFixed || 0,
      totalCves,
    };
  }

  let scanCount = 0;
  try {
    const scanDir = path.join(CWD, '.claude', 'security-scans');
    if (fs.existsSync(scanDir)) {
      scanCount = fs.readdirSync(scanDir).filter(f => f.endsWith('.json')).length;
    }
  } catch { /* ignore */ }

  return {
    status: scanCount > 0 ? 'SCANNED' : 'NONE',
    cvesFixed: 0,
    totalCves: 0,
  };
}

// Swarm status (pure file reads, NO ps aux)
function getSwarmStatus() {
  const staleThresholdMs = 5 * 60 * 1000;
  const now = Date.now();

  const swarmStatePath = path.join(CWD, '.claude-flow', 'swarm', 'swarm-state.json');
  const swarmState = readJSON(swarmStatePath);
  if (swarmState && swarmState.swarms) {
    const swarms = Object.values(swarmState.swarms);
    const running = swarms.filter(s => s.status === 'running' && s.agents && s.agents.length > 0);
    const totalEver = swarms.length;
    const activeNow = running.length;
    const updatedAt = swarms[0] && (swarms[0].updatedAt || swarms[0].createdAt);
    const age = updatedAt ? now - new Date(updatedAt).getTime() : Infinity;
    if (activeNow > 0 || age < staleThresholdMs) {
      return {
        activeAgents: running.reduce((sum, s) => sum + (s.agents ? s.agents.length : 0), 0),
        maxAgents: swarmState.maxAgents || getMaxAgents(),
        coordinationActive: activeNow > 0,
        totalSwarms: totalEver,
        runningSwarms: activeNow,
      };
    }
    // Historical swarms exist but are stale — show total count
    return {
      activeAgents: 0,
      maxAgents: swarmState.maxAgents || getMaxAgents(),
      coordinationActive: false,
      totalSwarms: totalEver,
      runningSwarms: 0,
    };
  }

  const activityData = readJSON(path.join(CWD, '.claude-flow', 'metrics', 'swarm-activity.json'));
  if (activityData && activityData.swarm) {
    const updatedAt = activityData.timestamp || (activityData.swarm && activityData.swarm.timestamp);
    const age = updatedAt ? now - new Date(updatedAt).getTime() : Infinity;
    if (age < staleThresholdMs) {
      return {
        activeAgents: activityData.swarm.agent_count || 0,
        maxAgents: getMaxAgents(),
        coordinationActive: activityData.swarm.coordination_active || activityData.swarm.active || false,
      };
    }
  }

  return { activeAgents: 0, maxAgents: getMaxAgents(), coordinationActive: false };
}

// System metrics (uses process.memoryUsage() — no shell spawn)
function getSystemMetrics() {
  const memoryMB = Math.floor(process.memoryUsage().heapUsed / 1024 / 1024);
  const learning = getLearningStats();
  const agentdb = getAgentDBStats();

  // Intelligence from learning.json (has real scores) or real data
  const learningData = readJSON(path.join(CWD, '.claude-flow', 'metrics', 'learning.json'));
  let intelligencePct = 0;
  let contextPct = 0;

  if (learningData && learningData.intelligence && learningData.intelligence.score !== undefined) {
    intelligencePct = Math.min(100, Math.floor(learningData.intelligence.score));
  } else if (learning.patterns > 0 || agentdb.vectorCount > 0) {
    // Use real data — patterns from actual store, vectors from actual DB
    const fromPatterns = learning.patterns > 0 ? Math.min(100, Math.floor(learning.patterns / 20)) : 0;
    const fromVectors = agentdb.vectorCount > 0 ? Math.min(100, Math.floor(agentdb.vectorCount / 20)) : 0;
    intelligencePct = Math.max(fromPatterns, fromVectors);
  }
  // 0% means no real learning data exists

  if (learningData && learningData.sessions && learningData.sessions.total > 0) {
    contextPct = Math.min(100, learningData.sessions.total * 5);
  } else if (learning.sessions > 0) {
    // Use log scale so large session counts don't max out instantly
    contextPct = Math.min(100, Math.floor(Math.log(learning.sessions) * 15));
  }

  // Sub-agents from file metrics (no ps aux)
  let subAgents = 0;
  const activityData = readJSON(path.join(CWD, '.claude-flow', 'metrics', 'swarm-activity.json'));
  if (activityData && activityData.processes && activityData.processes.estimated_agents) {
    subAgents = activityData.processes.estimated_agents;
  }

  return { memoryMB, contextPct, intelligencePct, subAgents };
}

// ADR status (count files only — don't read contents)
function getADRStatus() {
  // Count actual ADR files first — compliance JSON may be stale
  const adrPaths = [
    path.join(CWD, 'v3', 'implementation', 'adrs'),
    path.join(CWD, 'docs', 'adrs'),
    path.join(CWD, '.claude-flow', 'adrs'),
    path.join(CWD, '.wiki', 'decisions'),
  ];

  for (const adrPath of adrPaths) {
    try {
      if (fs.existsSync(adrPath)) {
        const files = fs.readdirSync(adrPath).filter(f =>
          f.endsWith('.md') && (f.startsWith('ADR-') || f.startsWith('adr-') || /^\d{4}-/.test(f))
        );
        if (files.length > 0) {
          return { count: files.length, implemented: files.length, compliance: 0 };
        }
      }
    } catch { /* ignore */ }
  }

  return { count: 0, implemented: 0, compliance: 0 };
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

// AgentDB stats — count real entries from all data stores
function getAgentDBStats() {
  let vectorCount = 0;
  let dbSizeKB = 0;
  let namespaces = 0;
  let hasHnsw = false;

  // 1. Count real entries from auto-memory-store.json
  const storePath = path.join(CWD, '.claude-flow', 'data', 'auto-memory-store.json');
  const storeStat = safeStat(storePath);
  if (storeStat) {
    dbSizeKB += storeStat.size / 1024;
    try {
      const store = JSON.parse(fs.readFileSync(storePath, 'utf-8'));
      if (Array.isArray(store)) vectorCount += store.length;
      else if (store && store.entries) vectorCount += store.entries.length;
    } catch { /* fall back */ }
  }

  // 2. Count entries from hooks memory store (.claude-flow/memory/store.json)
  const hooksStorePath = path.join(CWD, '.claude-flow', 'memory', 'store.json');
  const hooksStoreStat = safeStat(hooksStorePath);
  if (hooksStoreStat) {
    dbSizeKB += hooksStoreStat.size / 1024;
    try {
      const store = JSON.parse(fs.readFileSync(hooksStorePath, 'utf-8'));
      if (store && store.entries) {
        const entryCount = Object.keys(store.entries).length;
        vectorCount = Math.max(vectorCount, entryCount);
        if (entryCount > 0) namespaces++;
      }
    } catch { /* fall back */ }
  }

  // 3. Count entries from ranked-context.json
  try {
    const ranked = readJSON(path.join(CWD, '.claude-flow', 'data', 'ranked-context.json'));
    if (ranked && ranked.entries && ranked.entries.length > vectorCount) vectorCount = ranked.entries.length;
  } catch { /* ignore */ }

  // 3. Add DB file sizes
  const dbFiles = [
    path.join(CWD, 'data', 'memory.db'),
    path.join(CWD, '.claude-flow', 'memory.db'),
    path.join(CWD, '.swarm', 'memory.db'),
  ];
  for (const f of dbFiles) {
    const stat = safeStat(f);
    if (stat) {
      dbSizeKB += stat.size / 1024;
      namespaces++;
    }
  }

  // 4. Graph data size
  const graphStat = safeStat(path.join(CWD, 'data', 'memory.graph'));
  if (graphStat) dbSizeKB += graphStat.size / 1024;

  // 5. HNSW index or memory package
  const hnswPaths = [
    path.join(CWD, '.swarm', 'hnsw.index'),
    path.join(CWD, '.claude-flow', 'hnsw.index'),
  ];
  for (const p of hnswPaths) {
    if (safeStat(p)) { hasHnsw = true; break; }
  }
  if (!hasHnsw) {
    const memPkgPaths = [
      path.join(CWD, 'v3', '@claude-flow', 'memory', 'dist'),
      path.join(CWD, 'node_modules', '@claude-flow', 'memory'),
    ];
    for (const p of memPkgPaths) {
      if (fs.existsSync(p)) { hasHnsw = true; break; }
    }
  }

  return { vectorCount, dbSizeKB: Math.floor(dbSizeKB), namespaces, hasHnsw };
}

// Test stats (count files only — NO reading file contents)
function getTestStats() {
  let testFiles = 0;

  function countTestFiles(dir, depth) {
    if (depth === undefined) depth = 0;
    if (depth > 10) return;
    try {
      if (!fs.existsSync(dir)) return;
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules' && !entry.name.includes('.venv')) {
          countTestFiles(path.join(dir, entry.name), depth + 1);
        } else if (entry.isFile()) {
          const n = entry.name;
          if (n.includes('.test.') || n.includes('.spec.') || n.includes('_test.') || n.includes('_spec.') || n.startsWith('test_')) {
            testFiles++;
          }
        }
      }
    } catch { /* ignore */ }
  }

  var testDirNames = ['tests', 'test', '__tests__', 'src', 'v3'];
  for (var i = 0; i < testDirNames.length; i++) {
    countTestFiles(path.join(CWD, testDirNames[i]));
  }

  return { testFiles };
}

// Count MCP servers from all possible config locations
function getMCPCount() {
  const servers = new Set();
  const enabled = new Set();

  // 1. Check settings.mcp (legacy format)
  const settings = getSettings();
  if (settings && settings.mcp && typeof settings.mcp === 'object') {
    for (const name of Object.keys(settings.mcp)) { servers.add(name); }
    const enabledList = settings.enabledMcpServers;
    if (Array.isArray(enabledList)) {
      for (const name of enabledList) { enabled.add(name); }
    } else {
      for (const name of servers) { enabled.add(name); }
    }
  }

  // 2. Check settings.mcpServers (Claude Code native format)
  if (settings && settings.mcpServers && typeof settings.mcpServers === 'object') {
    for (const name of Object.keys(settings.mcpServers)) {
      servers.add(name);
      enabled.add(name); // defined in settings = enabled
    }
  }

  // 3. Check .mcp/servers.json / .mcp.json / ~/.claude/mcp.json
  const mcpConfigFile = readJSON(path.join(CWD, '.mcp', 'servers.json'))
                     || readJSON(path.join(CWD, '.mcp.json'))
                     || readJSON(path.join(os.homedir(), '.claude', 'mcp.json'));
  if (mcpConfigFile && mcpConfigFile.mcpServers) {
    for (const name of Object.keys(mcpConfigFile.mcpServers)) {
      servers.add(name);
      enabled.add(name);
    }
  }

  // 4. Check config/mcp_config.json (OpenCode format with servers array)
  const openCodeMCP = readJSON(path.join(CWD, 'config', 'mcp_config.json'));
  if (openCodeMCP && Array.isArray(openCodeMCP.servers)) {
    for (const sv of openCodeMCP.servers) {
      if (sv && sv.name) {
        servers.add(sv.name);
        if (sv.enabled !== false) enabled.add(sv.name);
      }
    }
  }

  // 5. Count Claude Code plugin MCP servers from ~/.claude/settings.json
  const homeSettings = readJSON(path.join(os.homedir(), '.claude', 'settings.json'));
  if (homeSettings) {
    const enabledPlugins = homeSettings.enabledPlugins || {};
    const pluginMcps = {
      'playwright@claude-plugins-official': true,
      'telegram@claude-plugins-official': true,
      'context7@claude-plugins-official': true,
      'chrome-devtools-mcp@claude-plugins-official': true,
      'firecrawl@claude-plugins-official': true,
      'tavily@claude-plugins-official': true,
      'ddg-mcp-search@claude-plugins-official': true,
    };
    for (const [plugin, isMcp] of Object.entries(pluginMcps)) {
      if (isMcp && enabledPlugins[plugin]) {
        servers.add(plugin);
        enabled.add(plugin);
      }
    }
  }

  return { total: servers.size, enabled: enabled.size };
}

// Integration status (shared settings + file checks)
function getIntegrationStatus() {
  const mcpServers = getMCPCount();

  const hasDatabase = ['.swarm/memory.db', '.claude-flow/memory.db', 'data/memory.db']
    .some(p => fs.existsSync(path.join(CWD, p)));
  const hasApi = !!(process.env.ANTHROPIC_API_KEY || process.env.OPENAI_API_KEY);

  return { mcpServers, hasDatabase, hasApi };
}

// Session stats (pure file reads)
function getSessionStats() {
  var sessionPaths = ['.claude-flow/session.json', '.claude/session.json'];
  for (var i = 0; i < sessionPaths.length; i++) {
    const data = readJSON(path.join(CWD, sessionPaths[i]));
    if (data && data.startTime) {
      const diffMs = Date.now() - new Date(data.startTime).getTime();
      const mins = Math.floor(diffMs / 60000);
      const duration = mins < 60 ? mins + 'm' : (mins / 60).toFixed(1) + 'h';
      return { duration: duration };
    }
  }
  return { duration: '' };
}

// ─── Rendering ──────────────────────────────────────────────────

// Compact sparkline bar: 5-segment filled/empty (no brackets)
function sparkBar(current, total) {
  const w = 5;
  const filled = Math.max(0, Math.min(w, Math.round((current / Math.max(1, total)) * w)));
  return c.brightGreen + '\u25CF'.repeat(filled) + c.dim + '\u25CB'.repeat(w - filled) + c.reset;
}

// Format a number compactly: 1234 → "1.2k", 1234567 → "1.2M"
function fmtNum(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return String(n);
}

// Pad a string to a fixed width, accounting for ANSI escape sequences
function visLen(s) { return s.replace(/\x1b\[[0-9;]*m/g, '').length; }
function padVis(s, width) {
  const v = visLen(s);
  return s + (v < width ? ' '.repeat(width - v) : '');
}

function generateStatusline() {
  const git = getGitInfo();
  const rawModel = getModelFromStdin() || getModelName();
  const modelName = compactModelName(rawModel);
  const modelTier = getModelTier(rawModel);
  const ctxInfo = getContextFromStdin();
  const costInfo = getCostFromStdin();
  const progress = getV3Progress();
  const security = getSecurityStatus();
  const swarm = getSwarmStatus();
  const system = getSystemMetrics();
  const adrs = getADRStatus();
  const hooks = getHooksStatus();
  const agentdb = getAgentDBStats();
  const tests = getTestStats();
  const session = getSessionStats();
  const integration = getIntegrationStatus();
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
  if (ctxInfo && ctxInfo.totalTokens > 0) {
    const ctxColor = ctxInfo.usedPct >= 90 ? c.brightRed : ctxInfo.usedPct >= 70 ? c.brightYellow : c.brightGreen;
    const used = ctxInfo.usedTokens > 0 ? fmtNum(ctxInfo.usedTokens) : '?';
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
  const dddColor = progress.dddProgress >= 50 ? c.brightGreen : progress.dddProgress > 0 ? c.yellow : c.red;
  const secColor = security.status === 'CLEAN' ? c.brightGreen
    : (security.status === 'IN_PROGRESS' || security.status === 'STALE') ? c.brightYellow
    : (security.status === 'NONE' ? c.dim : c.brightRed);
  const adrColor = adrs.count > 0 ? c.brightGreen : c.dim;
  const testColor = tests.testFiles > 0 ? c.brightGreen : c.dim;
  const vecColor = agentdb.vectorCount > 0 ? c.brightGreen : c.dim;
  const hookColor = hooks.enabled > 0 ? c.brightGreen : c.dim;
  const mcpColor = integration.mcpServers.enabled === integration.mcpServers.total ? c.brightGreen
    : integration.mcpServers.enabled > 0 ? c.brightYellow : c.red;
  const intelColor = system.intelligencePct >= 80 ? c.brightGreen : system.intelligencePct >= 40 ? c.brightYellow : c.dim;
  const SEP = ' ' + c.dim + '\u2502' + c.reset + ' ';

  // ── Line 2: Build ──
  const buildItems = [
    c.cyan + 'DDD' + c.reset + ' ' + sparkBar(progress.domainsCompleted, progress.totalDomains) + ' ' + dddColor + progress.domainsCompleted + '/' + progress.totalDomains + c.reset,
    c.brightBlue + 'ADR' + c.reset + ' ' + adrColor + '\u25CF' + adrs.count + c.reset,
    c.brightCyan + 'Tests' + c.reset + ' ' + testColor + '\u25CF' + tests.testFiles + c.reset,
    c.purple + 'Vec' + c.reset + ' ' + vecColor + '\u25CF' + agentdb.vectorCount + c.reset + (agentdb.hasHnsw ? c.brightGreen + '\u26A1' + c.reset : ''),
    c.brightYellow + 'Learn' + c.reset + ' ' + c.brightWhite + (getLearningStats().patterns || 0) + c.reset,
  ];
  lines.push('  ' + buildItems.join(SEP));

  // ── Line 3: System ──
  const swarmInd = swarm.coordinationActive ? c.brightGreen + '\u25C9' : c.dim + '\u25CB';
  const swarmDisp = swarm.coordinationActive && swarm.runningSwarms > 0
    ? swarm.runningSwarms + '/' + (swarm.totalSwarms || swarm.maxAgents)
    : (swarm.totalSwarms || swarm.activeAgents || 0);
  const swarmLbl = swarm.coordinationActive ? 'active' : 'total';
  const swarmCol = swarm.coordinationActive ? c.brightGreen : (swarm.totalSwarms > 0 ? c.yellow : c.dim);

  const sysItems = [
    c.brightYellow + 'Swarm' + c.reset + ' ' + swarmInd + c.reset + ' ' + swarmCol + swarmDisp + c.reset + ' ' + c.dim + swarmLbl + c.reset,
    c.brightPurple + 'Agents' + c.reset + ' ' + c.brightWhite + system.subAgents + c.reset,
    c.brightBlue + 'Hooks' + c.reset + ' ' + hookColor + hooks.enabled + '/' + hooks.total + c.reset,
    c.brightCyan + 'MCP' + c.reset + ' ' + mcpColor + '\u25CF' + integration.mcpServers.enabled + '/' + integration.mcpServers.total + c.reset,
  ];
  if (integration.hasDatabase) sysItems.push(c.brightGreen + '\u25C6DB' + c.reset);
  if (integration.hasApi) sysItems.push(c.brightGreen + '\u25C6API' + c.reset);
  lines.push('  ' + sysItems.join(SEP));

  // ── Line 4: Health ──
  const secIcon = security.status === 'CLEAN' ? c.brightGreen + '\u25CF'
    : (security.status === 'IN_PROGRESS' || security.status === 'STALE') ? c.brightYellow + '\u25CF'
    : (security.status === 'NONE' ? c.dim + '\u25CB' : c.brightRed + '\u25CF');

  const cveColor = security.cvesFixed >= security.totalCves ? c.brightGreen
    : security.cvesFixed > 0 ? c.brightYellow : c.brightRed;

  const healthItems = [
    c.brightRed + 'CVE' + c.reset + ' ' + cveColor + security.cvesFixed + '/' + security.totalCves + c.reset,
    c.brightCyan + 'Mem' + c.reset + ' ' + c.brightWhite + system.memoryMB + 'MB' + c.reset,
    c.brightGreen + 'Intel' + c.reset + ' ' + intelColor + system.intelligencePct + '%' + c.reset,
    c.cyan + 'Sec' + c.reset + ' ' + secIcon + c.reset + ' ' + secColor + security.status + c.reset,
  ];
  if (ctxInfo && ctxInfo.totalTokens > 0) {
    const ctxCol = ctxInfo.usedPct >= 90 ? c.brightRed : ctxInfo.usedPct >= 70 ? c.brightYellow : c.brightGreen;
    healthItems.push(c.purple + 'Ctx' + c.reset + ' ' + ctxCol + ctxInfo.usedPct + '%' + c.reset);
  }
  lines.push('  ' + healthItems.join(SEP));

  return lines.join('\n');
}

// JSON output
function generateJSON() {
  const git = getGitInfo();
  return {
    user: { name: git.name, gitBranch: git.gitBranch, modelName: getModelName() },
    v3Progress: getV3Progress(),
    security: getSecurityStatus(),
    swarm: getSwarmStatus(),
    system: getSystemMetrics(),
    adrs: getADRStatus(),
    hooks: getHooksStatus(),
    agentdb: getAgentDBStats(),
    tests: getTestStats(),
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

// Get context window info from Claude Code session
function getContextFromStdin() {
  const data = getStdinData();
  if (data && data.context_window) {
    const usedPct = Math.floor(data.context_window.used_percentage || 0);
    const totalTokens = data.context_window.total_tokens
                     || data.context_window.max_tokens
                     || (process.env.CLAUDE_CODE_AUTO_COMPACT_WINDOW ? parseInt(process.env.CLAUDE_CODE_AUTO_COMPACT_WINDOW) : 0)
                     || 0;
    let usedTokens = data.context_window.used_tokens || 0;
    // If Claude Code doesn't report token counts, compute from percentage
    if (usedTokens === 0 && totalTokens > 0 && usedPct > 0) {
      usedTokens = Math.round((usedPct / 100) * totalTokens);
    }
    return {
      usedPct,
      remainingPct: Math.floor(data.context_window.remaining_percentage || 100),
      usedTokens,
      totalTokens,
    };
  }
  return null;
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
