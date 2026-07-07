#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const PROJECT_ROOT = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const DATA_DIR = path.join(PROJECT_ROOT, '.claude-flow', 'data');
const METRICS_DIR = path.join(PROJECT_ROOT, '.claude-flow', 'metrics');
const SESSION_FILE = path.join(DATA_DIR, 'current.json');
const LAST_SESSION_FILE = path.join(METRICS_DIR, 'last-session.json');
const MAX_SESSION_FILES = 30; // keep at most 30 archived sessions

let _session = null;

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function generateId() {
  const now = new Date();
  const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');
  const timeStr = now.toISOString().slice(11, 19).replace(/:/g, '');
  return `session-${dateStr}-${timeStr}-${Math.random().toString(36).slice(2, 6)}`;
}

function readJSON(filePath) {
  try {
    if (!fs.existsSync(filePath)) return null;
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch { return null; }
}

function writeJSON(filePath, data) {
  try {
    ensureDir(path.dirname(filePath));
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
    return true;
  } catch (e) {
    process.stderr.write(`[session] WARN: Failed to write ${path.basename(filePath)}: ${e.message}\n`);
    return false;
  }
}

function start() {
  if (_session) return _session;
  const existing = restore();
  if (existing) return _session;

  const prevSession = readJSON(LAST_SESSION_FILE);
  _session = {
    id: generateId(),
    startedAt: new Date().toISOString(),
    cwd: PROJECT_ROOT,
    previousSessionId: prevSession ? prevSession.id : null,
    context: { tasks: [], decisions: [], lastUserQuery: '', filesChanged: [] },
    metrics: { edits: 0, commands: 0, tasks: 0, errors: 0, filesEdited: [] },
  };
  writeJSON(SESSION_FILE, _session);
  // Write initial resume file so there's always something to resume
  writeResumeFile(_session, 0, 'session start');
  return _session;
}

function restore() {
  const data = readJSON(SESSION_FILE);
  if (data && data.id) {
    if (!data.context) data.context = { tasks: [], decisions: [], lastUserQuery: '', filesChanged: [] };
    if (!data.metrics) data.metrics = { edits: 0, commands: 0, tasks: 0, errors: 0, filesEdited: [] };
    if (!data.metrics.filesEdited) data.metrics.filesEdited = [];
    _session = data;
    return _session;
  }
  return null;
}

function prune() {
  const sessionsDir = path.join(DATA_DIR, 'sessions');
  if (!fs.existsSync(sessionsDir)) return;
  try {
    const files = fs.readdirSync(sessionsDir)
      .filter(f => f.endsWith('.json'))
      .map(f => ({ name: f, mtime: fs.statSync(path.join(sessionsDir, f)).mtimeMs }))
      .sort((a, b) => b.mtime - a.mtime);
    if (files.length > MAX_SESSION_FILES) {
      const toRemove = files.slice(MAX_SESSION_FILES);
      for (const f of toRemove) {
        fs.unlinkSync(path.join(sessionsDir, f.name));
      }
      process.stderr.write(`[session] Pruned ${toRemove.length} old session archives (kept ${MAX_SESSION_FILES})\n`);
    }
  } catch (e) {
    process.stderr.write(`[session] WARN: Session prune failed: ${e.message}\n`);
  }
}

function writeResumeFile(session, duration, label) {
  const sessionDataDir = path.join(os.homedir(), '.claude', 'session-data');
  ensureDir(sessionDataDir);
  const dateStr = new Date().toISOString().slice(0, 10);
  const shortId = Math.random().toString(36).slice(2, 10);
  const filePath = path.join(sessionDataDir, `${dateStr}-${shortId}-session.tmp`);

  const ctx = session.context || {};
  const metrics = session.metrics || {};
  const filesChanged = ctx.filesChanged || [];
  const filesEdited = metrics.filesEdited || [];
  const allFiles = [...new Set([...filesChanged, ...filesEdited])].filter(Boolean);
  const lastQuery = ctx.lastUserQuery || '';

  const lines = [];
  const startDate = session.startedAt ? new Date(session.startedAt).toLocaleString() : 'unknown';
  lines.push(`SESSION RESUME: ${dateStr}`);
  lines.push(`Session ID: ${session.id}`);
  if (label) lines.push(`Label: ${label}`);
  lines.push('');
  lines.push('## WHAT WAS WORKED ON');
  if (lastQuery) lines.push(`Last query: ${lastQuery}`);
  if (metrics.edits > 0) lines.push(`Edits: ${metrics.edits} files touched`);
  if (allFiles.length > 0) lines.push(`Files changed: ${allFiles.slice(0, 20).join(', ')}`);
  if (ctx.tasks && ctx.tasks.length > 0) {
    lines.push('');
    lines.push('## TASKS');
    for (const t of ctx.tasks) lines.push(`- ${typeof t === 'object' ? (t.subject || t.description || JSON.stringify(t)) : t}`);
  }
  if (ctx.decisions && ctx.decisions.length > 0) {
    lines.push('');
    lines.push('## DECISIONS');
    for (const d of ctx.decisions) lines.push(`- ${d}`);
  }
  if (metrics.errors > 0) {
    lines.push('');
    lines.push(`## ERRORS ENCOUNTERED: ${metrics.errors}`);
  }
  lines.push('');
  lines.push('## SESSION INFO');
  lines.push(`- Started: ${startDate}`);
  lines.push(`- Duration: ${Math.round(duration / 1000 / 60)} min`);
  lines.push(`- Commands: ${metrics.commands || 0}`);
  lines.push('---');
  lines.push(`_Auto-saved by session.js (${label || 'session end'})._`);

  try {
    fs.writeFileSync(filePath, lines.join('\n'), 'utf-8');
    process.stderr.write(`[session] Resume saved: ${filePath}\n`);
  } catch (e) {
    process.stderr.write(`[session] WARN: Failed to write resume file: ${e.message}\n`);
  }
}

function end() {
  if (!_session && !restore()) return;

  const endedAt = new Date().toISOString();
  const duration = _session.startedAt
    ? Date.now() - new Date(_session.startedAt).getTime()
    : 0;

  const lastSessionData = {
    id: _session.id,
    startedAt: _session.startedAt,
    endedAt,
    duration,
    metrics: {
      edits: _session.metrics.edits || 0,
      commands: _session.metrics.commands || 0,
      tasks: _session.metrics.tasks || 0,
      errors: _session.metrics.errors || 0,
      filesEdited: _session.metrics.filesEdited || [],
    },
  };
  writeJSON(LAST_SESSION_FILE, lastSessionData);

  // Write resume markdown file for /resume-session
  writeResumeFile(_session, duration, 'session end');

  // Archive to sessions/ subdirectory
  const sessionsDir = path.join(DATA_DIR, 'sessions');
  ensureDir(sessionsDir);
  writeJSON(
    path.join(sessionsDir, `${_session.id}.json`),
    { ..._session, endedAt, duration }
  );

  _session = null;

  // Prune old session archives
  prune();
}

function get(key) {
  if (!_session) restore();
  if (!_session) return null;
  if (!key) return { ..._session };
  return (_session.context && _session.context[key] !== undefined) ? _session.context[key] : _session[key];
}

function getAll() {
  if (!_session) restore();
  return _session ? { ..._session } : null;
}

function update(key, value) {
  if (!_session) start();
  if (key.startsWith('metrics.')) {
    const mKey = key.slice(8);
    if (mKey in _session.metrics) _session.metrics[mKey] = value;
  } else {
    _session.context[key] = value;
  }
  writeJSON(SESSION_FILE, _session);
}

function metric(type) {
  if (!_session) start();
  if (type in _session.metrics) _session.metrics[type] = (_session.metrics[type] || 0) + 1;
  writeJSON(SESSION_FILE, _session);
}

function trackFile(filePath) {
  if (!_session) start();
  if (!_session.metrics.filesEdited) _session.metrics.filesEdited = [];
  if (filePath && !_session.metrics.filesEdited.includes(filePath)) {
    _session.metrics.filesEdited.push(filePath);
    if (_session.metrics.filesEdited.length > 100) {
      _session.metrics.filesEdited = _session.metrics.filesEdited.slice(-100);
    }
  }
  _session.metrics.edits = (_session.metrics.edits || 0) + 1;
  writeJSON(SESSION_FILE, _session);
}

module.exports = { start, restore, end, get, getAll, update, metric, trackFile };
