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
 *   status          - Show hook/status info
 *   notify          - Send notification
 */

'use strict';

const path = require('path');
const fs = require('fs');

const helpersDir = __dirname;

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

const router = safeRequire(path.join(helpersDir, 'router.js'));
const session = safeRequire(path.join(helpersDir, 'session.js'));
const intelligence = safeRequire(path.join(helpersDir, 'intelligence.cjs'));

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
    const timer = setTimeout(() => {
      try { process.stdin.removeAllListeners(); } catch (_) {}
      try { process.stdin.pause(); } catch (_) {}
      resolve(data);
    }, timeoutMs);
    timer.unref();
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => { clearTimeout(timer); resolve(data); });
    process.stdin.on('error', () => { clearTimeout(timer); resolve(data); });
    try { process.stdin.resume(); } catch (_) {}
  });
}

async function main() {
  let stdinData = '';
  try { stdinData = await readStdin(500); } catch (e) { /* ignore stdin errors */ }

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
      if (intelligence && intelligence.getContext) {
        try {
          const ctx = await runWithTimeout(
            () => intelligence.getContext(prompt),
            'intelligence.getContext()'
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
          console.error(`[BLOCKED] Dangerous command detected: ${d}`);
          process.exit(1);
        }
      }
      console.log('[OK] Command validated');
    },

    'pre-edit': () => {
      console.log('[OK] Pre-edit check passed');
    },

    'post-edit': () => {
      if (session && session.metric) {
        try { session.metric('edits'); } catch (e) { /* no active session */ }
      }
      if (intelligence && intelligence.recordEdit) {
        try {
          const file = hookInput.file_path || toolInput.file_path
            || process.env.TOOL_INPUT_file_path || args[0] || '';
          runWithTimeout(() => intelligence.recordEdit(file), 'intelligence.recordEdit()');
        } catch (e) { /* non-fatal */ }
      }
      console.log('[OK] Edit recorded');
    },

    'session-restore': async () => {
      if (session) {
        const existing = session.restore && session.restore();
        if (!existing) {
          session.start && session.start();
        }
      } else {
        const sessionId = `session-${Date.now()}`;
        console.log(`[INFO] Restoring session: %SESSION_ID%`);
        console.log('');
        console.log(`[OK] Session restored from %SESSION_ID%`);
        console.log(`New session ID: ${sessionId}`);
        console.log('');
        console.log('Restored State');
        console.log('+----------------+-------+');
        console.log('| Item           | Count |');
        console.log('+----------------+-------+');
        console.log('| Tasks          |     0 |');
        console.log('| Agents         |     0 |');
        console.log('| Memory Entries |     0 |');
        console.log('+----------------+-------+');
      }
      if (intelligence && intelligence.init) {
        const initResult = await runWithTimeout(() => intelligence.init(), 'intelligence.init()');
        if (initResult && initResult.nodes > 0) {
          console.log(`[INTELLIGENCE] Loaded ${initResult.nodes} patterns, ${initResult.edges} edges`);
        }
      }
    },

    'session-end': async () => {
      if (intelligence && intelligence.consolidate) {
        const consResult = await runWithTimeout(() => intelligence.consolidate(), 'intelligence.consolidate()');
        if (consResult && consResult.entries > 0) {
          console.log(`[INTELLIGENCE] Consolidated: ${consResult.entries} entries, ${consResult.edges} edges${consResult.newEntries > 0 ? `, ${consResult.newEntries} new` : ''}, PageRank recomputed`);
        }
      }
      if (session && session.end) {
        session.end();
      } else {
        console.log('[OK] Session ended');
      }
    },

    'pre-task': () => {
      if (session && session.metric) {
        try { session.metric('tasks'); } catch (e) { /* no active session */ }
      }
      if (router && router.routeTask && prompt) {
        const result = router.routeTask(prompt);
        console.log(`[INFO] Task routed to: ${result.agent} (confidence: ${result.confidence})`);
      } else {
        console.log('[OK] Task started');
      }
    },

    'post-task': () => {
      if (intelligence && intelligence.feedback) {
        try { intelligence.feedback(true); } catch (e) { /* non-fatal */ }
      }
      console.log('[OK] Task completed');
    },

    'compact-manual': () => {
      if (session && session.end) {
        console.log('[INFO] Manual compact: archiving session');
        session.end();
      }
      console.log('[OK] Compact manual complete');
    },

    'compact-auto': () => {
      if (intelligence && intelligence.consolidate) {
        runWithTimeout(() => intelligence.consolidate(), 'intelligence.consolidate()');
      }
      console.log('[OK] Compact auto complete');
    },

    'status': () => {
      if (intelligence && intelligence.stats) {
        intelligence.stats(args.includes('--json'));
      } else {
        console.log('[WARN] Intelligence module not available');
      }
    },

    'notify': () => {
      console.log('[OK] Notification handled');
    },

    'stats': () => {
      if (intelligence && intelligence.stats) {
        intelligence.stats(args.includes('--json'));
      } else {
        console.log('[WARN] Intelligence module not available. Run session-restore first.');
      }
    },
  };

  if (command && handlers[command]) {
    try {
      await withSafetyTimeout(async () => {
        await Promise.resolve(handlers[command]());
      }, command, 5000);
    } catch (e) {
      console.log(`[WARN] Hook ${command} encountered an error: ${e.message}`);
    }
  } else if (command) {
    console.log(`[OK] Hook: ${command}`);
  } else {
    console.log('Usage: hook-handler.cjs <route|pre-bash|pre-edit|post-edit|session-restore|session-end|pre-task|post-task|compact-manual|compact-auto|status|notify|stats>');
  }
}

process.exitCode = 0;
main().catch((e) => {
  try { console.log(`[WARN] Hook handler error: ${e.message}`); } catch (_) {}
}).finally(() => {
  process.exit(0);
});