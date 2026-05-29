#!/usr/bin/env node
/**
 * Claude Flow Session Manager
 * Handles session lifecycle: start, restore, end, metrics
 */

'use strict';

const fs = require('fs');
const path = require('path');

const SESSION_DIR = path.join(process.cwd(), '.claude-flow', 'sessions');
const SESSION_FILE = path.join(SESSION_DIR, 'current.json');
const METRICS_DIR = path.join(process.cwd(), '.claude-flow', 'metrics');

// Ensure directories exist
function ensureDirs() {
  if (!fs.existsSync(SESSION_DIR)) fs.mkdirSync(SESSION_DIR, { recursive: true });
  if (!fs.existsSync(METRICS_DIR)) fs.mkdirSync(METRICS_DIR, { recursive: true });
}

// Helper functions (defined before commands object to avoid hoisting issues)
function updateDaemonState(updates) {
  try {
    const daemonStatePath = path.join(process.cwd(), '.claude-flow', 'daemon-state.json');
    if (fs.existsSync(daemonStatePath)) {
      const state = JSON.parse(fs.readFileSync(daemonStatePath, 'utf-8'));
      Object.assign(state, updates);
      fs.writeFileSync(daemonStatePath, JSON.stringify(state, null, 2));
    }
  } catch (e) { /* ignore */ }
}

function listArchives() {
  try {
    const files = fs.readdirSync(SESSION_DIR)
      .filter(f => f.startsWith('session-') && f.endsWith('.json'))
      .map(f => {
        const data = fs.readFileSync(path.join(SESSION_DIR, f), 'utf-8');
        return JSON.parse(data);
      })
      .sort((a, b) => new Date(b.startedAt || 0) - new Date(a.startedAt || 0));
    return files;
  } catch (e) { return []; }
}

const commands = {
  start: () => {
    ensureDirs();
    const sessionId = `session-${Date.now()}`;
    // Load up to 5 most recent archived sessions for context
    const archives = listArchives();
    const recentSessions = archives.slice(0, 5).map(s => ({
      id: s.id,
      startedAt: s.startedAt,
      endedAt: s.endedAt,
      duration: s.duration,
    }));
    const session = {
      id: sessionId,
      startedAt: new Date().toISOString(),
      cwd: process.cwd(),
      context: {},
      recentSessions,
      metrics: {
        edits: 0,
        commands: 0,
        tasks: 0,
        errors: 0,
        filesEdited: [],
      },
      memory: {
        checkpoints: 0,
        observations: 0,
        insightsGained: 0,
      },
    };

    fs.writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2));
    updateDaemonState({ lastSessionStart: session.startedAt });

    console.log(`Session started: ${sessionId}`);
    return session;
  },

  restore: () => {
    ensureDirs();
    if (!fs.existsSync(SESSION_FILE)) {
      console.log('No session to restore');
      return null;
    }

    try {
      const session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8'));
      // Handle legacy sessions without required fields
      if (!session.startedAt) session.startedAt = session.createdAt || new Date().toISOString();
      if (!session.metrics) session.metrics = { edits: 0, commands: 0, tasks: 0, errors: 0, filesEdited: [] };
      if (!session.context) session.context = {};

      session.restoredAt = new Date().toISOString();

      // Load archived sessions for context
      const archives = listArchives();
      session.recentSessions = archives.slice(0, 5).map(s => ({
        id: s.id,
        startedAt: s.startedAt,
        endedAt: s.endedAt,
        duration: s.duration,
      }));

      fs.writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2));
      console.log(`Session restored: ${session.id}`);
      return session;
    } catch (e) {
      console.log('Failed to restore session:', e.message);
      return null;
    }
  },

  end: () => {
    ensureDirs();
    if (!fs.existsSync(SESSION_FILE)) {
      console.log('No active session');
      return null;
    }

    try {
      const session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8'));
      // Handle legacy sessions
      if (!session.startedAt) session.startedAt = session.createdAt || new Date().toISOString();
      if (!session.metrics) session.metrics = { edits: 0, commands: 0, tasks: 0, errors: 0, filesEdited: [] };

      session.endedAt = new Date().toISOString();
      session.duration = Date.now() - new Date(session.startedAt).getTime();
      session.metrics.duration = session.duration;

      // Archive session
      const archivePath = path.join(SESSION_DIR, `${session.id}.json`);
      fs.writeFileSync(archivePath, JSON.stringify(session, null, 2));
      fs.unlinkSync(SESSION_FILE);

      // Persist session summary for memory bootstrap
      const summaryPath = path.join(METRICS_DIR, 'last-session.json');
      fs.writeFileSync(summaryPath, JSON.stringify({
        id: session.id,
        startedAt: session.startedAt,
        endedAt: session.endedAt,
        duration: session.duration,
        metrics: session.metrics,
      }, null, 2));

      console.log(`Session ended: ${session.id}`);
      console.log(`Duration: ${Math.round(session.duration / 1000 / 60)} minutes`);
      console.log(`Metrics: edits=${session.metrics.edits}, commands=${session.metrics.commands}, tasks=${session.metrics.tasks}`);

      return session;
    } catch (e) {
      console.log('Failed to end session:', e.message);
      return null;
    }
  },

  status: () => {
    ensureDirs();
    if (!fs.existsSync(SESSION_FILE)) {
      console.log('No active session');
      return null;
    }

    try {
      const session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8'));
      const startedAt = session.startedAt || session.createdAt || new Date().toISOString();
      const duration = Date.now() - new Date(startedAt).getTime();

      console.log(`Session: ${session.id || 'unknown'}`);
      console.log(`Started: ${startedAt}`);
      console.log(`Duration: ${Math.round(duration / 1000 / 60)} minutes`);
      if (session.metrics) {
        console.log(`Metrics: ${JSON.stringify(session.metrics, null, 2)}`);
      }
      return session;
    } catch (e) {
      console.log('Failed to get session status:', e.message);
      return null;
    }
  },

  update: (key, value) => {
    ensureDirs();
    if (!fs.existsSync(SESSION_FILE)) {
      console.log('No active session');
      return null;
    }

    try {
      const session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8'));
      if (!session.metrics) session.metrics = { edits: 0, commands: 0, tasks: 0, errors: 0 };
      if (!session.context) session.context = {};

      if (key.includes('.')) {
        const keys = key.split('.');
        let obj = session;
        for (let i = 0; i < keys.length - 1; i++) {
          if (!obj[keys[i]]) obj[keys[i]] = {};
          obj = obj[keys[i]];
        }
        obj[keys[keys.length - 1]] = value;
      } else {
        session.context[key] = value;
      }
      session.updatedAt = new Date().toISOString();
      fs.writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2));
      return session;
    } catch (e) {
      console.log('Failed to update session:', e.message);
      return null;
    }
  },

  get: (key) => {
    if (!fs.existsSync(SESSION_FILE)) return null;
    try {
      const session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8'));
      if (!key) return session.context || {};
      const keys = key.split('.');
      let obj = session;
      for (const k of keys) {
        if (obj[k] === undefined) return null;
        obj = obj[k];
      }
      return obj;
    } catch (e) { return null; }
  },

  metric: (name, value) => {
    ensureDirs();
    if (!fs.existsSync(SESSION_FILE)) return null;

    try {
      const session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8'));
      if (!session.metrics) session.metrics = { edits: 0, commands: 0, tasks: 0, errors: 0 };

      if (session.metrics[name] !== undefined) {
        if (typeof value === 'number') {
          session.metrics[name] += value;
        } else {
          session.metrics[name]++;
        }
        session.lastActivity = new Date().toISOString();
        fs.writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2));
      }
      return session;
    } catch (e) { return null; }
  },

  trackFile: (filePath) => {
    if (!fs.existsSync(SESSION_FILE)) return null;
    try {
      const session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8'));
      if (!session.metrics) session.metrics = { edits: 0, commands: 0, tasks: 0, errors: 0, filesEdited: [] };
      if (!session.metrics.filesEdited) session.metrics.filesEdited = [];
      if (!session.metrics.filesEdited.includes(filePath)) {
        session.metrics.filesEdited.push(filePath);
        fs.writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2));
      }
      return session;
    } catch (e) { return null; }
  },
};

// CLI — only run when executed directly
if (require.main === module) {
  const [, , command, ...args] = process.argv;
  if (command && commands[command]) {
    commands[command](...args);
  } else {
    console.log('Usage: session.js <start|restore|end|status|update|metric|trackFile> [args]');
  }
}

module.exports = commands;