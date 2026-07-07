#!/usr/bin/env node
/**
 * Claude Flow Hook Handler (Cross-Platform)
 * Dispatches hook events to the appropriate helper modules.
 *
 * Usage: node hook-handler.cjs <command> [args...]
 *
 * Commands:
 *   route           - Route a task to optimal agent (reads PROMPT from env/stdin)
 *   pre-bash        - Validate command safety before execution
 *   pre-edit        - Pre-edit validation/analysis
 *   post-edit       - Record edit outcome for learning
 *   session-restore - Restore previous session state
 *   session-end     - End session and persist state
 *   compact-manual  - Manual compaction hook
 *   compact-auto    - Auto compaction hook
 *   compact-summarize - LLM-based conversation summarizer (PreCompact payload)
 *   status          - Show hook/status info
 *   notify          - Send notification
 */

'use strict';

const path = require('path');
const fs = require('fs');

const helpersDir = __dirname;

// All diagnostic output goes to stderr — stdout is reserved for statusline,
// structured command output, and Claude Code's internal rendering.
// Concurrent stdout writes during agent deployment cause interleaved garbled text.
function log(msg = '') { process.stderr.write(msg + '\n'); }

// Safe require with stdout suppression
function safeRequire(modulePath) {
  try {
    if (fs.existsSync(modulePath)) {
      const origLog = console.log;
      const origError = console.error;
      console.log = () => {};
      console.error = () => {};
      try {
        return require(modulePath);
      } finally {
        console.log = origLog;
        console.error = origError;
      }
    }
  } catch (e) { /* silently fail */ }
  return null;
}

// ── Lazy-loading getters (no top-level require — saves tokens on simple hooks) ──
let _router, _session, _intelligence;
function getRouter() { return _router || (_router = safeRequire(path.join(helpersDir, 'router.js'))); }
function getSession() { return _session || (_session = safeRequire(path.join(helpersDir, 'session.js'))); }
function getIntelligence() { return _intelligence || (_intelligence = safeRequire(path.join(helpersDir, 'intelligence.cjs'))); }

// ── Intelligence timeout protection ────────────────────────────────────────
const INTELLIGENCE_TIMEOUT_MS = 3000;
function runWithTimeout(fn, label) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      process.stderr.write("[WARN] " + label + " timed out after " + INTELLIGENCE_TIMEOUT_MS + "ms, skipping\n");
      resolve(null);
    }, INTELLIGENCE_TIMEOUT_MS);
    try {
      const result = fn();
      clearTimeout(timer);
      resolve(result);
    } catch (e) {
      clearTimeout(timer);
      resolve(null);
    }
  });
}

// ── Global safety timeout ───────────────────────────────────────────────────
function withSafetyTimeout(fn, label = 'hook', timeoutMs = 5000) {
  const start = Date.now();
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      process.stderr.write("[WARN] Hook '" + label + "' exceeded " + timeoutMs + "ms, forcing exit\n");
      resolve({ timedOut: true });
    }, timeoutMs);
    timer.unref();
    try {
      Promise.resolve(fn()).then(r => {
        clearTimeout(timer);
        const elapsed = Date.now() - start;
        if (elapsed > 100) process.stderr.write("[TIMING] Hook '" + label + "' completed in " + elapsed + "ms\n");
        resolve(r);
      }).catch(e => {
        clearTimeout(timer);
        const elapsed = Date.now() - start;
        process.stderr.write("[TIMING] Hook '" + label + "' failed at " + elapsed + "ms: " + e.message + "\n");
        resolve({ error: e.message });
      });
    } catch (e) {
      clearTimeout(timer);
      const elapsed = Date.now() - start;
      process.stderr.write("[TIMING] Hook '" + label + "' threw at " + elapsed + "ms: " + e.message + "\n");
      resolve({ error: e.message });
    }
  });
}

// Get the command from argv
const [, , command, ...args] = process.argv;

// Read stdin with timeout
async function readStdin(timeoutMs = 500) {
  if (process.stdin.isTTY) return '';
  return new Promise((resolve) => {
    let data = '';
    let settled = false;
    const done = (val) => { if (!settled) { settled = true; resolve(val || data); } };
    const timer = setTimeout(() => {
      try { process.stdin.removeAllListeners(); } catch (_) {}
      try { process.stdin.destroy(); } catch (_) {}
      done();
    }, timeoutMs);
    timer.unref();
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => { clearTimeout(timer); done(); });
    process.stdin.on('error', () => { clearTimeout(timer); done(); });
    try { process.stdin.resume(); } catch (_) {}
  });
}

async function main() {
  // Skip stdin for commands that don't need hookInput data (saves ~500ms per call)
  const NO_STDIN_COMMANDS = ['pre-edit', 'compact-manual', 'compact-auto', 'compact-summarize', 'session-restore', 'session-end', 'status', 'notify', 'stats', 'obsidian-sync', 'dreaming-consolidate', 'store-user-query', 'observation-capture'];
  let stdinData = '';
  if (!command || !NO_STDIN_COMMANDS.includes(command)) {
    try { stdinData = await readStdin(500); } catch (e) { /* ignore stdin errors */ }
  }

  let hookInput = {};
  if (stdinData && stdinData.trim()) {
    try { hookInput = JSON.parse(stdinData); } catch (e) { /* ignore parse errors */ }
  }

  // Normalize snake_case/camelCase
  const toolInput = hookInput.toolInput || hookInput.tool_input || {};

  // Merge stdin data into prompt resolution
  const prompt = hookInput.prompt || hookInput.command || toolInput.command
    || process.env.PROMPT || process.env.TOOL_INPUT_command || args.join(' ') || '';

  const handlers = {
    'route': async () => {
      const intelligence = getIntelligence();
      const router = getRouter();
      if (intelligence && intelligence.getContext) {
        try {
          // Use unified recall (queries graph + chroma + dreaming patterns)
          const unifiedRecall = require('./unified-recall.cjs');
          const results = await runWithTimeout(
            () => unifiedRecall.recall(prompt),
            'unifiedRecall.recall()'
          );
          if (results && results.length > 0) {
            const lines = ['[UNIFIED] Memory context (graph + vector + patterns):'];
            for (let i = 0; i < results.length; i++) {
              const r = results[i];
              const display = (r.content || '').slice(0, 80);
              lines.push(`  * (${r.score.toFixed(2)}) [${r.source}] ${display}`);
            }
            console.log(lines.join('\n'));
          } else {
            // Fallback to graph-only if unified returns nothing
            const ctx = getIntelligence().getContext(prompt);
            if (ctx) console.log(ctx);
          }
        } catch (e) { /* non-fatal */ }
      }
      if (router && router.routeTask) {
        const result = router.routeTask(prompt);
        const output = [
          `[INFO] Routing task: ${prompt.substring(0, 80) || '(no prompt)'}`,
          '',
          '+------------------- Primary Recommendation -------------------+',
          `| Agent: ${result.agent.padEnd(53)}|`,
          `| Confidence: ${(result.confidence * 100).toFixed(1)}%${' '.repeat(44)}|`,
          `| Reason: ${(result.reason || '').substring(0, 53).padEnd(53)}|`,
          '+--------------------------------------------------------------+',
        ];
        console.log(output.join('\n'));
      } else {
        console.log('[INFO] Router not available, using default routing');
      }
      // Skill auto-triggering: match prompt against known skill triggers
      const skillTriggers = [
        // Swarm / orchestration
        { name: 'swarm-advanced', patterns: ['swarm', 'parallel', 'agent team', 'coordination', 'distributed', 'orchestrat', 'multi-agent', 'fan-out', 'hierarchical'] },
        // GitNexus
        { name: 'gitnexus-impact-analysis', patterns: ['impact', 'blast radius', 'refactor', 'rename', 'what break', 'affects', 'caller'] },
        { name: 'gitnexus-debugging', patterns: ['debug', 'trace', 'error', 'crash', 'stack trace', 'failing', 'exception'] },
        { name: 'gitnexus-refactoring', patterns: ['extract', 'split', 'move', 'inline', 'rename symbol'] },
        // UI/UX
        { name: 'frontend-design', patterns: ['design', 'ui ', 'ux', 'component', 'layout', 'beautiful', 'tailwind', 'css', 'dark mode', 'animation', 'premium'] },
        { name: 'ui-ux-pro-max', patterns: ['linear-style', 'vercel-style', 'gradient', 'button', 'card', 'dashboard', 'landing page', 'responsive'] },
        // Process
        { name: 'brainstorming', patterns: ['brainstorm', 'ideate', 'think', 'explore options', 'possible approaches'] },
        { name: 'debugging', patterns: ['bug', 'fix', 'error', 'not working', 'broken', 'issue', 'incorrect'] },
        { name: 'tdd', patterns: ['test first', 'tdd', 'write test', 'test-driven'] },
        { name: 'code-review', patterns: ['review', 'check quality', 'security scan', 'best practice'] },
        // Architecture
        { name: 'architecture', patterns: ['architect', 'system design', 'pattern', 'scalability', 'api design'] },
        { name: 'adr-architect', patterns: ['adr', 'decision record', 'architectural decision'] },
        // Specialized
        { name: 'deploy-to-vercel', patterns: ['deploy', 'vercel', 'production', 'hosting'] },
        { name: 'git-workflow-automation', patterns: ['git ', 'commit', 'branch', 'pull request', 'merge', 'workflow'] },
        { name: 'github-code-review', patterns: ['github', 'pr ', 'pull request', 'code review'] },
      ];
      const promptLower = prompt.toLowerCase();
      const matchedSkills = [];
      for (const s of skillTriggers) {
        for (const p of s.patterns) {
          if (promptLower.includes(p)) {
            matchedSkills.push(s.name);
            break;
          }
        }
      }
      if (matchedSkills.length > 0) {
        console.log('');
        console.log('[💡 Skill Auto-Trigger] Consider: ' + matchedSkills.join(', '));
      }
    },

    'pre-bash': () => {
      const cmd = (hookInput.command || prompt).toLowerCase();
      const dangerous = ['rm -rf /', 'format c:', 'del /s /q c:\\', ':(){:|:&};:', 'mkfs'];
      for (const d of dangerous) {
        if (cmd.includes(d)) {
          log(`[BLOCKED] Dangerous command detected: ${d}`);
          process.exit(1);
        }
      }
    },

    'pre-edit': () => {},

    'post-edit': () => {
      const sessionMod = getSession();
      const intelligenceMod = getIntelligence();
      if (sessionMod && sessionMod.metric) {
        try { sessionMod.metric('edits'); } catch (e) { /* no active session */ }
      }
      const file = hookInput.file_path || toolInput.file_path
        || process.env.TOOL_INPUT_file_path || args[0] || '';
      if (file && sessionMod && sessionMod.trackFile) {
        try { sessionMod.trackFile(file); } catch (e) { /* no active session */ }
      }
      if (intelligenceMod && intelligenceMod.recordEdit) {
        try {
          runWithTimeout(() => intelligenceMod.recordEdit(file), 'intelligenceMod.recordEdit()');
        } catch (e) { /* non-fatal */ }
      }
    },

    'session-restore': async () => {
      const sessionMod = getSession();
      const intelligenceMod = getIntelligence();
      if (sessionMod) {
        const existing = sessionMod.restore && sessionMod.restore();
        if (!existing) {
          sessionMod.start && sessionMod.start();
        }
      } else {
        log(`[INFO] Session restored`);
      }
      if (intelligenceMod && intelligenceMod.init) {
        // Suppress intelligence.cjs internal console.log (it redundantly prints
        // JSON to stdout at module export level — agent deployment interleaves it).
        const origLog = console.log;
        console.log = () => {};
        try {
          const initResult = await runWithTimeout(() => intelligenceMod.init(), 'intelligenceMod.init()');
          if (initResult && initResult.nodes > 0) {
            log(`[INTELLIGENCE] Loaded ${initResult.nodes} patterns, ${initResult.edges} edges`);
          }
        } finally {
          console.log = origLog;
        }
      }
      // Inject top-ranked context into session (read-path fix)
      if (intelligenceMod && intelligenceMod.getTopRanked) {
        try {
          const topContext = intelligenceMod.getTopRanked(5);
          if (topContext) console.log(topContext);
        } catch (e) { /* non-fatal */ }
      }
    },

    'session-end': async () => {
      const intelligenceMod = getIntelligence();
      const sessionMod = getSession();
      if (intelligenceMod && intelligenceMod.consolidate) {
        // Suppress intelligence.cjs internal console.log (redundant JSON to stdout).
        const origLog = console.log;
        console.log = () => {};
        try {
          const consResult = await runWithTimeout(() => intelligenceMod.consolidate(), 'intelligenceMod.consolidate()');
          if (consResult && consResult.entries > 0) {
            log(`[INTELLIGENCE] Consolidated: ${consResult.entries} entries, ${consResult.edges} edges` +
              (consResult.newEntries > 0 ? `, ${consResult.newEntries} new` : '') +
              (consResult.pruned > 0 ? `, ${consResult.pruned} pruned` : '') +
              `, PageRank recomputed`);
          }
        } finally {
          console.log = origLog;
        }
      }
      if (sessionMod && sessionMod.end) {
        sessionMod.end();
      }
    },

    'pre-task': () => {
      const sessionMod = getSession();
      const routerMod = getRouter();
      if (sessionMod && sessionMod.metric) {
        try { sessionMod.metric('tasks'); } catch (e) { /* no active session */ }
      }
      if (routerMod && routerMod.routeTask && prompt) {
        const result = routerMod.routeTask(prompt);
        log(`[INFO] Task routed to: ${result.agent} (confidence: ${result.confidence})`);
      }
    },

    'post-task': () => {
      // Removed: feedback(true) always boosted confidence regardless of outcome.
      // getContext() already handles boosting in its call path, and consolidate()
      // applies decay during session-end. This avoids unbounded confidence inflation.
    },

    'compact-manual': () => {
      const sessionMod = getSession();
      if (sessionMod && sessionMod.end) {
        sessionMod.end();
      }
    },

    'compact-auto': () => {
      const intelligenceMod = getIntelligence();
      if (intelligenceMod && intelligenceMod.consolidate) {
        runWithTimeout(() => intelligenceMod.consolidate(), 'intelligenceMod.consolidate()');
      }
    },

    'compact-summarize': () => {
      // Real LLM-based summarizer. Subprocess Python so the JS hook stays thin.
      // Idempotent: identical conversation window returns dedup on second call.
      let spawn;
      try {
        spawn = require('child_process').spawnSync;
      } catch (e) {
        log('[WARN] compact-summarize: child_process unavailable');
        return;
      }
      const repoRoot = process.env.CLAUDE_PROJECT_DIR || '.';
      const proc = spawn('python3', ['-m', 'core.compaction_summarizer'], {
        cwd: repoRoot,
        encoding: 'utf-8',
        timeout: 25000,
        env: Object.assign({}, process.env, {
          COMPACTION_LOG_LEVEL: process.env.COMPACTION_LOG_LEVEL || 'WARNING',
        }),
      });
      if (proc.error) {
        log('[WARN] compact-summarize spawn failed:', proc.error.message);
        return;
      }
      const out = (proc.stdout || '').trim();
      if (!out) {
        if (proc.status !== 0) {
          const stderr = (proc.stderr || '').trim().slice(0, 200);
          log(`[WARN] compact-summarize exited ${proc.status}${stderr ? ': ' + stderr : ''}`);
        }
        return;
      }
      let result;
      try {
        result = JSON.parse(out);
      } catch (_) {
        return;
      }
      switch (result.status) {
        case 'ok':
          log(`[COMPACT] user=${result.user_id} saved=${result.chars_saved}ch msgs=${result.message_count} model=${result.model} time=${result.elapsed_ms}ms id=${result.id}`);
          break;
        case 'dedup':
          log(`[COMPACT] dedup: existing summary id=${result.id} user=${result.user_id} saved=${result.chars_saved}ch`);
          break;
        case 'no_users':
        case 'no_history':
        case 'empty_input':
        case 'empty_output':
        case 'error':
          log(`[COMPACT] ${result.status}${result.error ? ': ' + result.error : ''}`);
          break;
        default:
          log(`[COMPACT] ${result.status} user=${result.user_id || '?'}`);
      }
    },

    'status': () => {
      const intelligenceMod = getIntelligence();
      if (intelligenceMod && intelligenceMod.stats) {
        intelligenceMod.stats(args.includes('--json'));
      } else {
        log('[WARN] Intelligence module not available');
      }
    },

    'notify': () => {},

    'cleanup-orphans': () => {
      // Clean up orphan MCP processes and stale session caches
      const spawn = require('child_process').spawnSync;

      // Kill orphan MCP server instances (from previous sessions)
      spawn('bash', ['-c', `
        for p in firecrawl-mcp git-mcp-server sequential-thinking exa-mcp-server; do
          pkill -f "bunx.*$p" 2>/dev/null || true
        done
        pkill -f "python3.*hermes-mcp-server" 2>/dev/null || true
        pkill -f "python3.*claude-code-bridge" 2>/dev/null || true
        pkill -f "python3.*crawl4ai-mcp" 2>/dev/null || true
        pkill -f "node.*mcp-server-github" 2>/dev/null || true
        echo "done"
      `], { timeout: 5000 });

      // Clean stale session cache (keep newest 10 JSONL files, remove orphaned UUID dirs)
      const homedir = require('os').homedir();
      const cacheDir = require('path').join(homedir, '.claude', 'projects', '-home-newadmin-swarm-bot');
      try {
        const fs = require('fs');
        const items = fs.readdirSync(cacheDir);
        // Prune old JSONL files (keep newest 10)
        const jsonlFiles = items.filter(f => f.endsWith('.jsonl'))
          .map(f => ({ name: f, mtime: fs.statSync(require('path').join(cacheDir, f)).mtimeMs }))
          .sort((a, b) => b.mtime - a.mtime);
        if (jsonlFiles.length > 10) {
          const toRemove = jsonlFiles.slice(10);
          for (const f of toRemove) {
            fs.unlinkSync(require('path').join(cacheDir, f.name));
          }
          log(`[cleanup] Pruned ${toRemove.length} stale JSONL caches (kept newest 10)`);
        }
        // Prune orphaned UUID-named directories (compaction artifacts)
        const uuidDirPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
        let prunedDirs = 0;
        for (const item of items) {
          if (uuidDirPattern.test(item)) {
            try {
              const fullPath = require('path').join(cacheDir, item);
              const stat = fs.statSync(fullPath);
              if (stat.isDirectory()) {
                // Only remove if older than 24 hours (protects in-flight sessions)
                if (Date.now() - stat.mtimeMs > 86400000) {
                  fs.rmSync(fullPath, { recursive: true, force: true });
                  prunedDirs++;
                }
              }
            } catch (_) { /* skip inaccessible */ }
          }
        }
        if (prunedDirs > 0) log(`[cleanup] Pruned ${prunedDirs} orphaned UUID session dirs (>24h old)`);
      } catch (e) { process.stderr.write('[cleanup-orphans] Cache cleanup failed: ' + e.message + '\n'); }
    },

        'store-user-query': () => {
      // Use the already-captured prompt from scope (readStdin already captured
      // stdin and parsed it into hookInput → prompt before this handler runs).
      if (prompt && prompt.length > 10) {
        const sessionMod = getSession();
        if (sessionMod && sessionMod.update) {
          try { sessionMod.update('lastUserQuery', prompt.slice(0, 500)); } catch (e) { process.stderr.write('[store-user-query] session.update() failed: ' + e.message + '\n'); }
        }
      }
    },

    'dreaming-consolidate': () => {
      // Run dreaming consolidation (hippocampal replay) at session end
      const spawn = require('child_process').spawnSync;
      const repoRoot = process.env.CLAUDE_PROJECT_DIR || '.';
      const result = spawn('python3', [
        '-c', 'import importlib.util; spec=importlib.util.spec_from_file_location("dreaming", ".claude-flow/mcp/dreaming_consolidation.py"); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); print(mod.dreaming_run(force=True))',
      ], { cwd: repoRoot, encoding: 'utf-8', timeout: 30000 });
      if (result.stdout && result.stdout.trim()) {
        try {
          var report = JSON.parse(result.stdout.trim());
          log('[dreaming] Scanned ' + (report.sessions_scanned || 0) + ' sessions, ' + (report.patterns_found || 0) + ' patterns, ' + (report.dedup_merges || 0) + ' merges, ' + (report.elapsed_seconds || 0).toFixed(1) + 's');
        } catch (__e) {
          log('[dreaming] ' + result.stdout.trim());
        }
      }
      if (result.stderr && result.stderr.trim()) {
        log('[dreaming] stderr: ' + result.stderr.trim());
      }

      // Feed dreaming patterns back into active memory stores
      const storeResult = spawn('python3', [
        '-c', `
import json, os, glob, sys
from pathlib import Path

# Read dreaming briefings
cache_dir = Path("/tmp/hermes_dream_cache")
if not cache_dir.exists():
    print(json.dumps({"stored": 0, "source": "no_cache"}))
    sys.exit(0)

briefings = sorted(cache_dir.glob("*.md"), key=os.path.getmtime, reverse=True)[:3]
patterns = []
for b in briefings:
    text = b.read_text()[:500]
    # Extract pattern lines (lines starting with - [pattern_type])
    for line in text.split("\\n"):
        line = line.strip()
        if line.startswith("- [") and "]" in line:
            ptype = line[2:line.index("]")]
            pdesc = line[line.index("]")+1:].strip()
            if pdesc:
                patterns.append({"type": ptype, "desc": pdesc, "source": b.name})

# Store to ChromaDB via MemoryStore
try:
    sys.path.insert(0, "${repoRoot}")
    from core.memory.store import MemoryStore
    store = MemoryStore()
    stored_count = 0
    for p in patterns:
        content = f"[{p['type']}] {p['desc']}"
        store.remember(content, metadata={"source": "dreaming", "type": p["type"], "file": p["source"]})
        stored_count += 1
    print(json.dumps({"stored": stored_count, "patterns": len(patterns)}))
except Exception as e:
    print(json.dumps({"stored": 0, "error": str(e)[:100]}))
        `.strip(),
      ], { cwd: repoRoot, encoding: 'utf-8', timeout: 10000 });
      if (storeResult.stdout && storeResult.stdout.trim()) {
        try {
          const storeReport = JSON.parse(storeResult.stdout.trim());
          if (storeReport.stored > 0) {
            log('[dreaming] Stored ' + storeReport.stored + ' patterns to vector store');
          }
        } catch (e) {
          log('[dreaming] Store result: ' + storeResult.stdout.trim());
        }
      }
    },

    'obsidian-sync': () => {
      const spawn = require('child_process').spawnSync;
      const repoRoot = process.env.CLAUDE_PROJECT_DIR || '.';
      const sessionName = process.env.SESSION_NAME || 'Claude Code session';

      // 1. Write daily session log + summary (full sync)
      const logResult = spawn('python3', [
        'core/memory/obsidian_autosync.py',
        '--full-sync',
        '--session-name', sessionName,
      ], { cwd: repoRoot, encoding: 'utf-8', timeout: 15000 });
      if (logResult.stdout && logResult.stdout.trim()) {
        log(`[obsidian-sync] ${logResult.stdout.trim()}`);
      }

      // 2. Sync memory files to wiki
      const syncResult = spawn('bash', [
        '.claude/helpers/memory-to-wiki-sync.sh',
      ], { cwd: repoRoot, encoding: 'utf-8', timeout: 10000 });
      if (syncResult.stdout && syncResult.stdout.trim()) {
        log(`[obsidian-sync] ${syncResult.stdout.trim()}`);
      }
    },

    'observation-capture': () => {
      // Flush observation queue and store session summary at session end
      const spawn = require('child_process').spawnSync;
      const repoRoot = process.env.CLAUDE_PROJECT_DIR || '.';
      const result = spawn('python3', [
        '-c', `
import asyncio, json, sys
from pathlib import Path
try:
    from core.memory.observation_store import DB_PATH, ObservationStore
    from core.memory.observation_queue import get_observation_queue
    # Flush queue
    q = get_observation_queue()
    if q and hasattr(q, 'shutdown'):
        asyncio.run(q.shutdown())
    # Count observations
    obs_dir = Path("${repoRoot}") / ".superpowers/homunculus/observations"
    count = len(list(obs_dir.glob("*.json"))) if obs_dir.exists() else 0
    print(json.dumps({"flushed": True, "observations": count}))
except Exception as e:
    print(json.dumps({"flushed": False, "error": str(e)}))
        `.trim(),
      ], { cwd: repoRoot, encoding: 'utf-8', timeout: 5000 });
      if (result.stdout && result.stdout.trim()) {
        try {
          const report = JSON.parse(result.stdout.trim());
          log(`[observations] ${report.observations || 0} files, flushed: ${report.flushed}`);
        } catch (e) {
          log(`[observations] ${result.stdout.trim()}`);
        }
      }
    },

    'stats': () => {
      const intelligenceMod = getIntelligence();
      if (intelligenceMod && intelligenceMod.stats) {
        intelligenceMod.stats(args.includes('--json'));
      } else {
        log('[WARN] Intelligence module not available. Run session-restore first.');
      }
    },
  };

  if (command && handlers[command]) {
    // compact-summarize spawns a Python LLM call; give it more time than the
    // default 5s safety cap so the subprocess can finish or hit its own 25s.
    const safetyMs = command === 'compact-summarize' ? 30000 : 5000;
    try {
      await withSafetyTimeout(async () => {
        await Promise.resolve(handlers[command]());
      }, command, safetyMs);
    } catch (e) {
      log(`[WARN] Hook ${command} encountered an error: ${e.message}`);
    }
  } else if (command) {
    log(`[OK] Hook: ${command}`);
  } else {
    log('Usage: hook-handler.cjs <route|pre-bash|pre-edit|post-edit|session-restore|session-end|pre-task|post-task|compact-manual|compact-auto|compact-summarize|status|notify|cleanup-orphans|store-user-query|dreaming-consolidate|obsidian-sync|observation-capture|stats>');
  }
}

main().catch((e) => {
  try { log(`[WARN] Hook handler error: ${e.message}`); } catch (_) {}
}).finally(() => {
  // Let event loop flush stdout naturally — don't force exit
  // process.exit() would discard buffered console.log output
});