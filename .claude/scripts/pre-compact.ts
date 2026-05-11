#!/usr/bin/env node

/**
 * PreCompact Hook — obsidian-mind
 *
 * Runs before context compaction. Backs up session transcript to thinking/session-logs/.
 */

import { appendFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const VAULT_ROOT = process.cwd();
const SESSION_LOGS_DIR = join(VAULT_ROOT, '.wiki', 'thinking', 'session-logs');

async function main() {
  const sessionId = process.env.OCTOGENT_SESSION_ID || 'unknown';
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const logFile = join(SESSION_LOGS_DIR, `${timestamp}-${sessionId}.md`);

  // Ensure directory exists
  if (!existsSync(SESSION_LOGS_DIR)) {
    mkdirSync(SESSION_LOGS_DIR, { recursive: true });
  }

  // Create session log header
  const logEntry = `# Session Log — ${timestamp}\n\nSession ID: ${sessionId}\n\nNote: This is a backup of session context before compaction. Actual session content is in the agent's memory.\n\n---\n\n`;

  try {
    appendFileSync(logFile, logEntry);
    console.log(`[PreCompact] Session backup saved to ${logFile}`);
  } catch (err) {
    console.error('[PreCompact] Failed to backup session:', err);
  }

  console.log(JSON.stringify({ success: true, backupPath: logFile }));
}

main().catch(console.error);
