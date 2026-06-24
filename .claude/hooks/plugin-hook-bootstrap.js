#!/usr/bin/env node
/**
 * ECC Plugin Hook Bootstrap — Dynamic hook path resolver
 *
 * Resolves plugin hook paths by checking multiple locations:
 * 1. CLAUDE_PLUGIN_ROOT env var
 * 2. Multiple plugin paths (~/.claude/plugins/ecc, etc.)
 * 3. Cache directories
 * Falls back to project-local hooks if no plugin found.
 *
 * Usage:
 *   const bootstrap = require('./plugin-hook-bootstrap.js');
 *   const hookPath = bootstrap.resolve('ecc-governance-capture.sh');
 *   const allHooks = bootstrap.listHooks();
 */

const fs = require('fs');
const path = require('path');

const PLUGIN_ROOTS = [
  process.env.CLAUDE_PLUGIN_ROOT,
  path.join(process.env.HOME || '/home/newadmin', '.claude', 'plugins', 'ecc'),
  path.join(process.env.HOME || '/home/newadmin', '.claude', 'plugins'),
  path.join(process.env.XDG_DATA_HOME || path.join(process.env.HOME || '/home/newadmin', '.local', 'share'), 'ecc-homunculus'),
];

const PROJECT_HOOKS_DIR = path.resolve(__dirname);

/**
 * Resolve a hook script path.
 * Checks plugin roots first, falls back to project hooks directory.
 */
function resolve(hookName) {
  // First check plugin roots
  for (const root of PLUGIN_ROOTS) {
    if (!root) continue;
    const candidate = path.join(root, 'hooks', hookName);
    if (fs.existsSync(candidate)) return candidate;
    // Also check root directly
    const candidate2 = path.join(root, hookName);
    if (fs.existsSync(candidate2)) return candidate2;
  }

  // Fall back to project hooks directory
  const local = path.join(PROJECT_HOOKS_DIR, hookName);
  if (fs.existsSync(local)) return local;

  return null;
}

/**
 * List all available hook scripts across all roots.
 */
function listHooks() {
  const hooks = new Set();

  // Add project hooks
  if (fs.existsSync(PROJECT_HOOKS_DIR)) {
    fs.readdirSync(PROJECT_HOOKS_DIR).forEach(f => {
      if (f.endsWith('.sh') || f.endsWith('.js') || f.endsWith('.cjs') || f.endsWith('.mjs')) {
        hooks.add(f);
      }
    });
  }

  // Add plugin hooks
  for (const root of PLUGIN_ROOTS) {
    if (!root) continue;
    const hooksDir = path.join(root, 'hooks');
    if (fs.existsSync(hooksDir)) {
      fs.readdirSync(hooksDir).forEach(f => {
        if (f.endsWith('.sh') || f.endsWith('.js')) {
          hooks.add(f);
        }
      });
    }
  }

  return Array.from(hooks).sort();
}

/**
 * Get the ECC homunculus data directory.
 */
function getDataDir() {
  return process.env.XDG_DATA_HOME
    ? path.join(process.env.XDG_DATA_HOME, 'ecc-homunculus')
    : path.join(process.env.HOME || '/home/newadmin', '.local', 'share', 'ecc-homunculus');
}

module.exports = { resolve, listHooks, getDataDir };

// CLI usage
if (require.main === module) {
  const cmd = process.argv[2] || 'list';
  switch (cmd) {
    case 'resolve':
      console.log(resolve(process.argv[3]) || 'NOT FOUND');
      break;
    case 'list':
      console.log(listHooks().join('\n'));
      break;
    case 'datadir':
      console.log(getDataDir());
      break;
    default:
      console.log('Usage: plugin-hook-bootstrap.js <resolve|list|datadir> [name]');
  }
}
