#!/usr/bin/env node
'use strict';

/**
 * instinct-cli.cjs — ECC-style instinct management for continuous learning (v2.1).
 *
 * Commands:
 *   consolidate     — Scan observations, find patterns, generate/update instincts
 *   status          — Print instinct status (for /instinct-status)
 *   evolve          — Cluster related instincts into higher-level patterns
 *   instinct-export — Export instincts as JSON (for /instinct-export)
 *   instinct-import — Import instincts from JSON (for /instinct-import)
 *   promote         — Promote project instincts to global (for /promote)
 *   projects        — List projects with instinct counts (for /projects)
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PROJECT_DIR = process.env.CLAUDE_PROJECT_DIR || '.';
const HOMUNCULUS_DIR = path.join(PROJECT_DIR, '.superpowers', 'homunculus');
const OBS_DIR = path.join(HOMUNCULUS_DIR, 'observations');
const INSTINCT_DIR = path.join(HOMUNCULUS_DIR, 'instincts');
const CURSOR_FILE = path.join(HOMUNCULUS_DIR, '.consolidation-cursor');

// XDG_DATA_HOME for global instincts
const DATA_HOME = process.env.XDG_DATA_HOME
  ? path.join(process.env.XDG_DATA_HOME, 'ecc-homunculus')
  : path.join(process.env.HOME || '/home/newadmin', '.local', 'share', 'ecc-homunculus');
const GLOBAL_INSTINCT_DIR = path.join(DATA_HOME, 'instincts');
const GLOBAL_PROJECTS_FILE = path.join(DATA_HOME, 'projects.json');

const CONFIDENCE_INITIAL = 0.3;
const CONFIDENCE_INCREMENT = 0.1;
const CONFIDENCE_MAX = 0.9;
const CONFIDENCE_PROMOTE = 0.8;

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function getProjectId() {
  try {
    const remote = require('child_process')
      .execSync('git remote get-url origin 2>/dev/null || echo "local"', { cwd: PROJECT_DIR })
      .toString().trim();
    return crypto.createHash('sha256').update(remote).digest('hex').slice(0, 16);
  } catch {
    return 'local-project';
  }
}

function getProjectName() {
  try {
    return path.basename(PROJECT_DIR);
  } catch {
    return 'unknown';
  }
}

function readObservations() {
  if (!fs.existsSync(OBS_DIR)) return [];
  const files = fs.readdirSync(OBS_DIR).filter(f => f.endsWith('.json'));
  const cursor = fs.existsSync(CURSOR_FILE)
    ? parseInt(fs.readFileSync(CURSOR_FILE, 'utf-8').trim(), 10) || 0
    : 0;

  // Process files after cursor (also check .jsonl observations)
  const newFiles = files.slice(cursor);
  const observations = [];
  for (const file of newFiles) {
    try {
      const data = JSON.parse(fs.readFileSync(path.join(OBS_DIR, file), 'utf-8'));
      observations.push(data);
    } catch { /* skip corrupt files */ }
  }

  // Also process JSONL files
  const jsonlFiles = fs.readdirSync(OBS_DIR).filter(f => f.endsWith('.jsonl'));
  for (const file of jsonlFiles) {
    try {
      const lines = fs.readFileSync(path.join(OBS_DIR, file), 'utf-8').trim().split('\n');
      for (const line of lines) {
        try {
          observations.push(JSON.parse(line));
        } catch { /* skip corrupt lines */ }
      }
    } catch { /* skip unreadable files */ }
  }

  // Update cursor
  fs.writeFileSync(CURSOR_FILE, String(files.length));
  return observations;
}

function readInstincts(dir) {
  const targetDir = dir || INSTINCT_DIR;
  if (!fs.existsSync(targetDir)) return [];
  const files = fs.readdirSync(targetDir).filter(f => f.endsWith('.json'));
  return files.map(f => {
    try {
      return JSON.parse(fs.readFileSync(path.join(targetDir, f), 'utf-8'));
    } catch { return null; }
  }).filter(Boolean);
}

function readGlobalInstincts() {
  return readInstincts(GLOBAL_INSTINCT_DIR);
}

function writeInstinct(instinct, targetDir) {
  const dir = targetDir || INSTINCT_DIR;
  ensureDir(dir);
  const id = crypto.createHash('sha256')
    .update(instinct.trigger + instinct.action_pattern)
    .digest('hex').slice(0, 12);
  const filePath = path.join(dir, `${id}.json`);
  fs.writeFileSync(filePath, JSON.stringify(instinct, null, 2));
  return id;
}

function consolidate() {
  const observations = readObservations();
  if (observations.length === 0) {
    console.log('[instinct-cli] No new observations to consolidate.');
    return;
  }

  // Group observations by tool + file pattern
  const groups = {};
  for (const obs of observations) {
    const tool = obs.tool || 'unknown';
    const fileInput = obs.tool_input || {};
    const filePath = fileInput.file_path || fileInput.filePath || '';
    const key = `${tool}::${filePath}`;
    if (!groups[key]) groups[key] = [];
    groups[key].push(obs);
  }

  const projectId = getProjectId();
  const existingInstincts = readInstincts();

  for (const [key, group] of Object.entries(groups)) {
    if (group.length < 2) continue;

    const [tool, filePath] = key.split('::');
    const count = group.length;
    const confidence = Math.min(CONFIDENCE_INITIAL + (count - 2) * CONFIDENCE_INCREMENT, CONFIDENCE_MAX);

    const existing = existingInstincts.find(
      i => i.trigger === `tool:${tool}` && i.action_pattern.includes(filePath)
    );

    const instinct = {
      trigger: `tool:${tool}`,
      action_pattern: filePath ? `edit:${filePath}` : `execute:${tool}`,
      confidence: Math.round(confidence * 100) / 100,
      scope: confidence >= CONFIDENCE_PROMOTE ? 'global' : 'project',
      project_id: projectId,
      project_name: getProjectName(),
      evidence_count: count,
      domain: classifyDomain(tool, filePath),
      last_observed: new Date().toISOString(),
      created: existing ? existing.created : new Date().toISOString(),
    };

    if (existing) {
      instinct.created = existing.created;
      instinct.confidence = Math.min(
        existing.confidence + CONFIDENCE_INCREMENT,
        CONFIDENCE_MAX
      );
      instinct.evidence_count = (existing.evidence_count || 0) + 1;
      if (instinct.confidence >= CONFIDENCE_PROMOTE && existing.scope === 'project') {
        instinct.scope = 'global';
      }
    }

    writeInstinct(instinct);
  }

  // Update project registry
  updateProjectRegistry();
  console.log(`[instinct-cli] Consolidated ${observations.length} observations into instincts.`);
}

function classifyDomain(tool, filePath) {
  if (!filePath) return 'workflow';
  if (filePath.includes('test')) return 'testing';
  if (filePath.includes('security') || filePath.includes('auth')) return 'security';
  if (filePath.includes('.py') || filePath.includes('.js') || filePath.includes('.ts')) return 'code-style';
  if (tool === 'Bash') return 'workflow';
  return 'architecture';
}

function updateProjectRegistry() {
  ensureDir(path.dirname(GLOBAL_PROJECTS_FILE));
  let registry = {};
  try {
    if (fs.existsSync(GLOBAL_PROJECTS_FILE)) {
      registry = JSON.parse(fs.readFileSync(GLOBAL_PROJECTS_FILE, 'utf-8'));
    }
  } catch { /* reset if corrupt */ }

  const projectId = getProjectId();
  registry[projectId] = {
    name: getProjectName(),
    path: PROJECT_DIR,
    last_active: new Date().toISOString(),
    instinct_count: readInstincts().length,
  };

  fs.writeFileSync(GLOBAL_PROJECTS_FILE, JSON.stringify(registry, null, 2));
}

function instinctStatus() {
  const instincts = readInstincts();
  if (instincts.length === 0) {
    console.log('No instincts yet. Observations accumulate and consolidate on PreCompact.');
    return;
  }

  instincts.sort((a, b) => b.confidence - a.confidence);

  console.log('\n=== Instinct Status ===\n');
  console.log(`${'Confidence'.padEnd(12)} ${'Scope'.padEnd(8)} ${'Domain'.padEnd(14)} ${'Count'.padEnd(6)} Trigger`);
  console.log('-'.repeat(70));
  for (const inst of instincts) {
    const conf = String(inst.confidence).padEnd(12);
    const scope = (inst.scope || 'project').padEnd(8);
    const domain = (inst.domain || 'workflow').padEnd(14);
    const count = String(inst.evidence_count || 1).padEnd(6);
    console.log(`${conf} ${scope} ${domain} ${count} ${inst.trigger} → ${inst.action_pattern}`);
  }
  console.log(`\nTotal: ${instincts.length} instincts`);
}

function evolve() {
  const instincts = readInstincts();
  if (instincts.length === 0) {
    console.log('No instincts to evolve. Run consolidate first.');
    return;
  }

  const clusters = {};
  for (const inst of instincts) {
    const domain = inst.domain || 'uncategorized';
    if (!clusters[domain]) clusters[domain] = [];
    clusters[domain].push(inst);
  }

  console.log('\n=== Evolved Clusters ===\n');
  for (const [domain, cluster] of Object.entries(clusters)) {
    const avgConf = (cluster.reduce((a, i) => a + i.confidence, 0) / cluster.length).toFixed(2);
    console.log(`Domain: ${domain} (${cluster.length} instincts, avg conf: ${avgConf})`);
    for (const inst of cluster.sort((a, b) => b.confidence - a.confidence)) {
      console.log(`  [${inst.confidence}] ${inst.trigger} → ${inst.action_pattern}`);
    }
    console.log();
  }
}

function instinctExport() {
  const instincts = readInstincts();
  if (instincts.length === 0) {
    console.log('No instincts to export.');
    return;
  }

  const exportData = {
    exported_at: new Date().toISOString(),
    project: getProjectName(),
    project_id: getProjectId(),
    instinct_count: instincts.length,
    instincts: instincts.map(i => ({
      trigger: i.trigger,
      action_pattern: i.action_pattern,
      confidence: i.confidence,
      domain: i.domain,
      evidence_count: i.evidence_count,
      created: i.created,
      last_observed: i.last_observed,
    })),
  };

  console.log(JSON.stringify(exportData, null, 2));
}

function instinctImport() {
  const input = fs.readFileSync('/dev/stdin', 'utf-8').trim();
  let data;
  try {
    data = JSON.parse(input);
  } catch {
    console.error('Invalid JSON input. Pipe export JSON to stdin.');
    process.exit(1);
  }

  if (!data.instincts || !Array.isArray(data.instincts)) {
    console.error('No instincts array found in input.');
    process.exit(1);
  }

  let imported = 0;
  const existing = readInstincts();
  for (const inst of data.instincts) {
    const exists = existing.some(
      e => e.trigger === inst.trigger && e.action_pattern === inst.action_pattern
    );
    if (!exists) {
      writeInstinct({
        trigger: inst.trigger,
        action_pattern: inst.action_pattern,
        confidence: inst.confidence || 0.3,
        scope: 'project',
        project_id: getProjectId(),
        project_name: getProjectName(),
        evidence_count: inst.evidence_count || 1,
        domain: inst.domain || 'workflow',
        last_observed: new Date().toISOString(),
        created: new Date().toISOString(),
      });
      imported++;
    }
  }

  console.log(`Imported ${imported} instincts (${data.instincts.length - imported} duplicates skipped).`);
}

function promote() {
  const projectInstincts = readInstincts();
  const highConf = projectInstincts.filter(i => i.confidence >= CONFIDENCE_PROMOTE);

  if (highConf.length === 0) {
    console.log(`No instincts at confidence >= ${CONFIDENCE_PROMOTE} to promote.`);
    return;
  }

  ensureDir(GLOBAL_INSTINCT_DIR);
  const globalInstincts = readGlobalInstincts();
  let promoted = 0;

  for (const inst of highConf) {
    const globalInst = {
      ...inst,
      scope: 'global',
      promoted_at: new Date().toISOString(),
      source_project: getProjectName(),
    };

    const exists = globalInstincts.some(
      g => g.trigger === inst.trigger && g.action_pattern === inst.action_pattern
    );

    if (!exists) {
      writeInstinct(globalInst, GLOBAL_INSTINCT_DIR);
      promoted++;
    }
  }

  console.log(`Promoted ${promoted} instincts to global (${highConf.length} eligible, ${highConf.length - promoted} already global).`);
}

function projects() {
  const projectsFile = GLOBAL_PROJECTS_FILE;
  if (!fs.existsSync(projectsFile)) {
    console.log('No tracked projects.');
    return;
  }

  try {
    const registry = JSON.parse(fs.readFileSync(projectsFile, 'utf-8'));
    const entries = Object.entries(registry);

    if (entries.length === 0) {
      console.log('No tracked projects.');
      return;
    }

    console.log('\n=== Tracked Projects ===\n');
    console.log(`${'Project'.padEnd(24)} ${'Instincts'.padEnd(10)} Last Active`);
    console.log('-'.repeat(55));
    for (const [, proj] of entries) {
      const name = (proj.name || 'unknown').padEnd(24);
      const count = String(proj.instinct_count || 0).padEnd(10);
      const active = (proj.last_active || '').slice(0, 19);
      console.log(`${name} ${count} ${active}`);
    }
    console.log(`\nTotal: ${entries.length} projects`);
  } catch {
    console.log('Error reading project registry.');
  }
}

// --- Main ---
const cmd = process.argv[2];
switch (cmd) {
  case 'consolidate':
    consolidate();
    break;
  case 'status':
    instinctStatus();
    break;
  case 'evolve':
    evolve();
    break;
  case 'instinct-export':
    instinctExport();
    break;
  case 'instinct-import':
    instinctImport();
    break;
  case 'promote':
    promote();
    break;
  case 'projects':
    projects();
    break;
  default:
    console.log('Usage: instinct-cli.cjs <consolidate|status|evolve|instinct-export|instinct-import|promote|projects>');
}
