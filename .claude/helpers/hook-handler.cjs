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
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      process.stderr.write("[WARN] Hook '" + label + "' exceeded " + timeoutMs + "ms, forcing exit\n");
      resolve({ timedOut: true });
    }, timeoutMs);
    timer.unref();
    try {
      Promise.resolve(fn()).then(r => {
        clearTimeout(timer);
        resolve(r);
      }).catch(e => {
        clearTimeout(timer);
        resolve({ error: e.message });
      });
    } catch (e) {
      clearTimeout(timer);
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
  const NO_STDIN_COMMANDS = ['pre-edit', 'compact-manual', 'compact-auto', 'compact-summarize', 'session-restore', 'session-end', 'status', 'notify', 'stats'];
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
          const ctx = await runWithTimeout(
            () => getIntelligence().getContext(prompt),
            'getIntelligence().getContext()'
          );
          if (ctx) console.log(ctx);
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
      if (intelligenceMod && intelligenceMod.recordEdit) {
        try {
          const file = hookInput.file_path || toolInput.file_path
            || process.env.TOOL_INPUT_file_path || args[0] || '';
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
            log(`[INTELLIGENCE] Consolidated: ${consResult.entries} entries, ${consResult.edges} edges${consResult.newEntries > 0 ? `, ${consResult.newEntries} new` : ''}, PageRank recomputed`);
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
      const intelligenceMod = getIntelligence();
      if (intelligenceMod && intelligenceMod.feedback) {
        try { intelligenceMod.feedback(true); } catch (e) { /* non-fatal */ }
      }
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
          log('[WARN] compact-summarize exited', proc.status);
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
    log('Usage: hook-handler.cjs <route|pre-bash|pre-edit|post-edit|session-restore|session-end|pre-task|post-task|compact-manual|compact-auto|compact-summarize|status|notify|stats>');
  }
}

main().catch((e) => {
  try { log(`[WARN] Hook handler error: ${e.message}`); } catch (_) {}
}).finally(() => {
  // Let event loop flush stdout naturally — don't force exit
  // process.exit() would discard buffered console.log output
});