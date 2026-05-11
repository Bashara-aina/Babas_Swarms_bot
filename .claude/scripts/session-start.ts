#!/usr/bin/env node

/**
 * SessionStart Hook — obsidian-mind
 *
 * Runs at session start. Injects vault context into the session:
 * - Re-indexes QMD if available
 * - Reads North Star, active projects, recent changes
 * - Lists open tasks and vault file listing
 */

import { readFileSync, readdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const VAULT_ROOT = process.cwd();
const WIKI_DIR = join(VAULT_ROOT, '.wiki');

interface VaultManifest {
  qmd_index?: string;
  qmd_context?: string;
  [key: string]: unknown;
}

function readVaultManifest(): VaultManifest {
  const manifestPath = join(WIKI_DIR, 'vault-manifest.json');
  if (existsSync(manifestPath)) {
    return JSON.parse(readFileSync(manifestPath, 'utf-8'));
  }
  return {};
}

function readNote(notePath: string, maxLines = 50): string {
  if (existsSync(notePath)) {
    const content = readFileSync(notePath, 'utf-8');
    return content.split('\n').slice(0, maxLines).join('\n');
  }
  return '';
}

function getActiveProjects(): string[] {
  const activeDir = join(WIKI_DIR, 'work', 'active');
  if (existsSync(activeDir)) {
    return readdirSync(activeDir)
      .filter(f => f.endsWith('.md'))
      .map(f => f.replace('.md', ''));
  }
  return [];
}

function getRecentDecisions(): string[] {
  const decisionsPath = join(WIKI_DIR, 'brain', 'Key Decisions.md');
  return readNote(decisionsPath, 30).split('\n')
    .filter(l => l.includes('**') && l.includes('Decision:'))
    .slice(0, 5);
}

async function main() {
  console.log('[SessionStart] Loading vault context...');

  const manifest = readVaultManifest();

  // Read North Star
  const northStarPath = join(WIKI_DIR, 'brain', 'North Star.md');
  const northStar = readNote(northStarPath, 40);
  console.log('[SessionStart] North Star loaded:', northStar.split('\n')[0]);

  // Get active projects
  const projects = getActiveProjects();
  console.log(`[SessionStart] Active projects: ${projects.length}`);

  // Get recent decisions
  const decisions = getRecentDecisions();
  console.log(`[SessionStart] Recent decisions: ${decisions.length}`);

  // QMD re-index (if available and qmd command exists)
  try {
    const { execSync } = await import('child_process');
    const indexName = manifest.qmd_index || 'swarm-bot';
    execSync(`qmd --index ${indexName} embed 2>/dev/null || true`, { timeout: 30000 });
    console.log('[SessionStart] QMD re-index complete');
  } catch {
    console.log('[SessionStart] QMD not available, using grep fallback');
  }

  // Output context for Claude to inject
  const context = {
    northStar: northStar.substring(0, 500),
    activeProjects: projects,
    recentDecisions: decisions.slice(0, 3),
    vaultPath: WIKI_DIR
  };

  console.log('[SessionStart] Context loaded successfully');
  console.log(JSON.stringify(context, null, 2));
}

main().catch(console.error);
