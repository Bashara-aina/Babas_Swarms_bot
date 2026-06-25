#!/usr/bin/env node
/**
 * Comprehensive MCP Smoke Test
 * Tests all MCP servers with live JSON-RPC protocol calls.
 * Usage: node smoke_test.mjs
 */

import { spawn } from 'child_process';
import { setTimeout } from 'timers/promises';
import { readFileSync } from 'fs';

const RESULTS = [];
const FAILED = [];
const PASSED = [];

async function call(proc, id, method, params = {}) {
  const req = JSON.stringify({ jsonrpc: '2.0', id, method, params });
  proc.stdin.write(req + '\n');
  await setTimeout(300);
}

async function readResponse(output, expectId) {
  const lines = output.split('\n').filter(l => l.trim().startsWith('{'));
  for (const l of lines) {
    try {
      const p = JSON.parse(l);
      if (p.id === expectId) return p;
    } catch {}
  }
  return null;
}

async function smokeTest(name, opts) {
  const { cmd, cwd, args = {}, wait = 4000 } = opts;
  let output = '';
  let stderr = '';

  const proc = spawn(cmd[0], cmd.slice(1), {
    cwd,
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env }
  });

  proc.stdout.on('data', d => { output += d.toString(); });
  proc.stderr.on('data', d => { stderr += d.toString(); });

  try {
    await setTimeout(wait);

    // Initialize
    await call(proc, 1, 'initialize', {
      protocolVersion: '0.1.0',
      capabilities: {},
      clientInfo: { name: 'smoke-test', version: '1.0.0' }
    });
    await setTimeout(400);
    await call(proc, 2, 'notifications/initialized', {});
    await setTimeout(400);

    // List tools
    await call(proc, 3, 'tools/list', {});
    await setTimeout(600);

    const initResp = await readResponse(output, 1);
    const listResp = await readResponse(output, 3);

    if (!initResp?.result) {
      throw new Error('initialize failed');
    }

    const tools = listResp?.result?.tools || [];
    const toolNames = tools.map(t => t.name);
    const toolCount = tools.length;

    // Call each tool with minimal args if it has no required params
    const callResults = [];
    for (const tool of tools.slice(0, 15)) { // cap at 15 per server for speed
      const schema = tool.inputSchema?.properties || {};
      const required = tool.inputSchema?.required || [];
      const hasRequired = required.length === 0;
      const hasParams = Object.keys(schema).length > 0;

      if (!hasRequired && hasParams) {
        // build minimal args
        const args = {};
        for (const [k, v] of Object.entries(schema)) {
          if (v.type === 'string') args[k] = 'test';
          else if (v.type === 'number') args[k] = 1;
          else if (v.type === 'boolean') args[k] = false;
          else if (v.type === 'array') args[k] = [];
          else if (v.type === 'object') args[k] = {};
        }
        await call(proc, 100 + callResults.length, 'tools/call', { name: tool.name, arguments: args });
        await setTimeout(400);
      } else if (!hasParams) {
        // no-arg tool
        await call(proc, 100 + callResults.length, 'tools/call', { name: tool.name, arguments: {} });
        await setTimeout(400);
      }
    }

    proc.kill();

    // Check responses
    const allLines = output.split('\n').filter(l => l.trim().startsWith('{'));
    const responses = allLines.map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
    const callResponses = responses.filter(r => r.id >= 100);

    const errors = callResponses.filter(r => r.error);
    const successes = callResponses.filter(r => r.result && !r.error);

    RESULTS.push({
      name,
      status: 'PASS',
      toolCount,
      toolNames: toolNames.slice(0, 5),
      calls: callResponses.length,
      errors: errors.length,
      errorDetails: errors.slice(0, 3).map(e => ({ name: e.method, code: e.error?.code, msg: e.error?.message?.slice(0, 80) }))
    });
    PASSED.push(name);
    console.log(`✅ ${name}: ${toolCount} tools, ${callResponses.length} calls, ${errors.length} errors`);

  } catch (err) {
    proc.kill();
    FAILED.push(name);
    RESULTS.push({ name, status: 'FAIL', error: err.message });
    console.log(`❌ ${name}: ${err.message}`);
  }
}

async function main() {
  console.log('═'.repeat(70));
  console.log('  MCP SMOKE TEST — All Servers');
  console.log('═'.repeat(70));
  console.log('');

  // ─── CONFIGURE EACH MCP SERVER HERE ───────────────────────────────────────
  const servers = [

    // 1. FILESYSTEM
    {
      name: 'filesystem',
      cmd: ['bash', 'tools/mcpServers/bootstrap/mcp_bootstrap.sh', '@modelcontextprotocol/server-filesystem', '/', '/home', '/tmp', '/media', '/mnt', '/opt', '/srv', '/var', '/root', '/nix', '/nix/store'],
      cwd: '/home/newadmin/swarm-bot',
      wait: 4000,
    },

    // 2. CRAWL4AI
    {
      name: 'crawl4ai',
      cmd: ['/home/newadmin/miniconda3/bin/python3', 'tools/mcpServers/crawl4ai_mcp/server.py'],
      cwd: '/home/newadmin/swarm-bot',
      wait: 4000,
    },

    // 3. EXA
    {
      name: 'exa',
      cmd: ['bash', 'tools/mcpServers/bootstrap/mcp_bootstrap.sh', '/home/newadmin/.local/node18/bin/exa-mcp-server'],
      cwd: '/home/newadmin/swarm-bot',
      wait: 4000,
    },

    // 4. OBSIDIAN
    {
      name: 'obsidian',
      cmd: ['node', 'mcp_servers/obsidian-patched/index.js'],
      cwd: '/home/newadmin/swarm-bot',
      wait: 4000,
    },

    // 5. GITNEXUS
    {
      name: 'gitnexus',
      cmd: ['/home/newadmin/.local/node18/bin/gitnexus', 'mcp'],
      cwd: '/home/newadmin/swarm-bot',
      wait: 4000,
    },

    // 6. RUFLO
    {
      name: 'ruflo',
      cmd: ['npx', 'ruflo', 'mcp', 'start'],
      cwd: '/home/newadmin/swarm-bot',
      wait: 5000,
    },

    // 7. SEQUENTIAL-THINKING
    {
      name: 'sequential-thinking',
      cmd: ['bash', 'tools/mcpServers/bootstrap/mcp_bootstrap.sh', '@modelcontextprotocol/server-sequential-thinking'],
      cwd: '/home/newadmin/swarm-bot',
      wait: 4000,
    },

    // 8. SYMPHONY OF ONE
    {
      name: 'symphony',
      cmd: ['node', 'mcp-server.js'],
      cwd: '/home/newadmin/swarm-bot/mcp_servers/symphony-of-one',
      env: { HUB_URL: 'http://localhost:3000', AGENT_NAME: 'SmokeTest' },
      wait: 4000,
    },

    // 9. HERMES
    {
      name: 'hermes',
      cmd: ['bash', 'tools/mcpServers/bootstrap/mcp_bootstrap.sh', 'hermes', 'mcp', 'serve'],
      cwd: '/home/newadmin/swarm-bot',
      wait: 4000,
    },

    // 10. LOCAL DEEP RESEARCH
    {
      name: 'local-deep-research',
      cmd: ['bash', 'tools/mcpServers/bootstrap/mcp_bootstrap.sh', '/home/newadmin/miniconda3/bin/python3', '-m', 'local_deep_research.mcp'],
      cwd: '/home/newadmin/swarm-bot',
      wait: 5000,
    },

    // 11. GIT MCP SERVER
    {
      name: 'git-mcp-server',
      cmd: ['bash', 'tools/mcpServers/bootstrap/mcp_bootstrap.sh', '@mseep/git-mcp-server'],
      cwd: '/home/newadmin/swarm-bot',
      wait: 4000,
    },

    // 12. BROWSER-USE
    {
      name: 'browser-use',
      cmd: ['/home/newadmin/miniconda3/bin/python3', '-m', 'tools.mcpServers.browser_use_mcp.server'],
      cwd: '/home/newadmin/swarm-bot',
      env: {
        BROWSER_USE_MODEL: 'minimax/MiniMax-M3',
        LITELLM_BASE_URL: 'http://localhost:4000'
      },
      wait: 5000,
    },

  ];
  // ────────────────────────────────────────────────────────────────────────────

  for (const s of servers) {
    try {
      await smokeTest(s.name, s);
    } catch (err) {
      console.log(`❌ ${s.name}: CRASH — ${err.message}`);
      FAILED.push(s.name);
    }
  }

  console.log('');
  console.log('═'.repeat(70));
  console.log('  RESULTS');
  console.log('═'.repeat(70));
  console.log(`  ✅ PASSED: ${PASSED.length}`);
  console.log(`  ❌ FAILED: ${FAILED.length}`);
  console.log('');

  if (FAILED.length > 0) {
    console.log('  Failed servers:');
    FAILED.forEach(n => console.log(`    - ${n}`));
  }

  console.log('');
  console.log('  Detail:');
  for (const r of RESULTS) {
    if (r.status === 'FAIL') {
      console.log(`    ${r.name}: FAIL — ${r.error}`);
    } else {
      const errInfo = r.errors > 0 ? `, ${r.errors} tool errors` : '';
      console.log(`    ${r.name}: ${r.toolCount} tools, ${r.calls} calls${errInfo}`);
    }
  }

  console.log('═'.repeat(70));

  // Exit with error if any failed
  process.exit(FAILED.length > 0 ? 1 : 0);
}

main().catch(err => {
  console.error('Smoke test crashed:', err);
  process.exit(1);
});
