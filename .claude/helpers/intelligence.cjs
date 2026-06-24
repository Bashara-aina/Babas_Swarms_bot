#!/usr/bin/env node
/**
 * Intelligence Layer (ADR-050)
 *
 * Closes the intelligence loop by wiring PageRank-ranked memory into
 * the hook system. Pure CJS — no ESM imports of @claude-flow/memory.
 *
 * Data files (all under .claude-flow/data/):
 *   auto-memory-store.json  — written by auto-memory-hook.mjs
 *   graph-state.json        — serialized graph (nodes + edges + pageRanks)
 *   ranked-context.json     — pre-computed ranked entries for fast lookup
 *   pending-insights.jsonl  — append-only edit/task log
 */

'use strict';

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(process.cwd(), '.claude-flow', 'data');
const STORE_PATH = path.join(DATA_DIR, 'auto-memory-store.json');
const GRAPH_PATH = path.join(DATA_DIR, 'graph-state.json');
const RANKED_PATH = path.join(DATA_DIR, 'ranked-context.json');
const PENDING_PATH = path.join(DATA_DIR, 'pending-insights.jsonl');
const EMBEDDING_CACHE_PATH = path.join(DATA_DIR, 'embedding-cache.json');
const METRICS_PATH = path.join(process.cwd(), '.claude-flow', 'metrics', 'recall-metrics.jsonl');
const SESSION_DIR = path.join(process.cwd(), '.claude-flow', 'data', 'sessions');
// session-start-trigger.mjs writes to data/current.json, not sessions/
const SESSION_FILE = path.join(DATA_DIR, 'current.json');

// ── Safety limits (fixes #1530, #1531) ─────────────────────────────────────
const MAX_DATA_FILE_SIZE = 10 * 1024 * 1024; // 10 MB — skip files larger than this
const MAX_GRAPH_NODES = 5000;                 // skip PageRank if graph exceeds this

// ── Stop words for trigram matching ──────────────────────────────────────────

const STOP_WORDS = new Set([
  'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
  'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
  'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
  'before', 'after', 'and', 'but', 'or', 'nor', 'not', 'so', 'yet',
  'both', 'either', 'neither', 'each', 'every', 'all', 'any', 'few',
  'more', 'most', 'other', 'some', 'such', 'no', 'only', 'own', 'same',
  'than', 'too', 'very', 'just', 'because', 'if', 'when', 'which',
  'who', 'whom', 'this', 'that', 'these', 'those', 'it', 'its',
]);

// ── Embedding helpers (Ollama nomic-embed-text, 768-dim) ─────────────────────

const _EMBED_CACHE_TTL = 3600000; // 1 hour cache freshness
let _embeddingCache = null; // lazy-loaded from disk

function _loadEmbeddingCache() {
  if (_embeddingCache) return _embeddingCache;
  try {
    if (fs.existsSync(EMBEDDING_CACHE_PATH)) {
      _embeddingCache = JSON.parse(fs.readFileSync(EMBEDDING_CACHE_PATH, 'utf-8'));
      if (typeof _embeddingCache === 'object' && !Array.isArray(_embeddingCache)) return _embeddingCache;
    }
  } catch (e) { /* corrupted cache, rebuild */ }
  _embeddingCache = {};
  return _embeddingCache;
}

function _saveEmbeddingCache() {
  try {
    ensureDataDir();
    fs.writeFileSync(EMBEDDING_CACHE_PATH, JSON.stringify(_embeddingCache), 'utf-8');
  } catch (e) { /* non-critical */ }
}

function _ollamaEmbed(text) {
  try {
    const body = JSON.stringify({ model: 'nomic-embed-text', prompt: text });
    const { spawnSync } = require('child_process');
    const result = spawnSync('curl', [
      '-s', '-X', 'POST', 'http://localhost:11434/api/embeddings',
      '-H', 'Content-Type: application/json',
      '-d', body,
    ], { timeout: 3000, encoding: 'utf-8' });
    if (result.status === 0 && result.stdout) {
      const parsed = JSON.parse(result.stdout);
      if (parsed && parsed.embedding) return parsed.embedding;
    }
  } catch (e) { /* ollama unavailable */ }
  return null;
}

function _embedText(text) {
  if (!text || text.length < 3) return null;
  const cache = _loadEmbeddingCache();
  const key = text.replace(/\s+/g, ' ').trim().toLowerCase().slice(0, 256);
  const cached = cache[key];
  if (cached && (Date.now() - (cached.ts || 0)) < _EMBED_CACHE_TTL) return cached.vec;
  const vec = _ollamaEmbed(text);
  if (vec) { cache[key] = { vec, ts: Date.now() }; _saveEmbeddingCache(); return vec; }
  return null;
}

function _cosineSimilarity(a, b) {
  if (!a || !b || a.length !== b.length) return 0;
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i]; }
  const mag = Math.sqrt(na) * Math.sqrt(nb);
  return mag === 0 ? 0 : dot / mag;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function readJSON(filePath) {
  // Safety: skip files exceeding MAX_DATA_FILE_SIZE (#1531)
  try {
    const stat = fs.statSync(filePath);
    if (stat.size > MAX_DATA_FILE_SIZE) {
      process.stderr.write("[INTELLIGENCE] WARN: Skipping " + path.basename(filePath) + " (" + Math.round(stat.size / 1048576) + "MB exceeds 10MB limit)\n");
      return null;
    }
  } catch { /* file may not exist yet */ }
  try {
    if (fs.existsSync(filePath)) return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch { /* corrupt file — start fresh */ }
  return null;
}

function writeJSON(filePath, data) {
  try {
    ensureDataDir();
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
  } catch (e) {
    process.stderr.write('[INTELLIGENCE] WARN: Failed to write ' + path.basename(filePath) + ': ' + e.message + '\n');
  }
}

function tokenize(text) {
  if (!text) return [];
  return [...new Set(
    text.toLowerCase()
      // Preserve underscores, hyphens, dots for code identifiers (det_mAP50, train.py, cross-entropy)
      .replace(/[^a-z0-9\s_.-]/g, ' ')
      .split(/\s+/)
      .filter(w => w.length > 2 && !STOP_WORDS.has(w))
  )];
}

function trigrams(words) {
  const t = new Set();
  for (const w of words) {
    for (let i = 0; i <= w.length - 3; i++) t.add(w.slice(i, i + 3));
  }
  return t;
}

function jaccardSimilarity(setA, setB) {
  if (setA.size === 0 && setB.size === 0) return 0;
  let intersection = 0;
  for (const item of setA) { if (setB.has(item)) intersection++; }
  return intersection / (setA.size + setB.size - intersection);
}

// ── Deduplication helper (fixes #1518) ──────────────────────────────────────

function deduplicateById(entries) {
  if (!entries || !Array.isArray(entries)) return entries;
  const seen = new Map();
  for (const entry of entries) {
    const id = entry.id || entry.key;
    if (id) {
      seen.set(id, entry);
    } else {
      seen.set(`__no_id_${seen.size}`, entry);
    }
  }
  return Array.from(seen.values());
}

// ADR-095 G6 — content-hash dedup. The April audit measured 5,706 entries
// in the auto-memory store with only ~20 unique by content; 5,686 dupes
// were the same MEMORY.md sections imported from sibling project dirs
// with different IDs. deduplicateById can't catch these (the IDs really
// are different); we need a content fingerprint.
//
// Fast non-cryptographic fingerprint — collisions on 64-bit FNV-1a are
// vanishingly rare for human prose at the scale of an auto-memory store.
// Whitespace-normalized so trivially-different formatting doesn't bypass dedup.
function fingerprintContent(text) {
  if (typeof text !== 'string' || text.length === 0) return '0';
  const norm = text.replace(/\s+/g, ' ').trim().toLowerCase();
  // FNV-1a 64-bit (split into 32-bit halves to stay within Number safe int)
  let h1 = 0x811c9dc5, h2 = 0xcbf29ce4;
  for (let i = 0; i < norm.length; i++) {
    const c = norm.charCodeAt(i);
    h1 ^= c; h1 = Math.imul(h1, 0x01000193) >>> 0;
    h2 ^= c; h2 = Math.imul(h2, 0x100000001b3 & 0xffffffff) >>> 0;
  }
  return `${h1.toString(16)}_${h2.toString(16)}_${norm.length}`;
}

function deduplicateByContent(entries) {
  if (!entries || !Array.isArray(entries)) return entries;
  const seen = new Map();
  for (const entry of entries) {
    const content = entry.content || entry.summary || entry.value || '';
    const fp = fingerprintContent(typeof content === 'string' ? content : JSON.stringify(content));
    if (!seen.has(fp)) {
      seen.set(fp, entry);
    } else {
      // Keep the entry with the higher accessCount or earlier createdAt
      const existing = seen.get(fp);
      const existingAccess = existing.accessCount || 0;
      const candidateAccess = entry.accessCount || 0;
      if (candidateAccess > existingAccess) seen.set(fp, entry);
    }
  }
  return Array.from(seen.values());
}

// ADR-115 — semantic dedup via embedding cosine similarity.
// Catches near-duplicates that content-fingerprint misses:
// "API endpoint timeout" vs "REST API call timed out" have different
// fingerprints but similar meaning. Threshold 0.92 is conservative —
// only merges very close semantic matches.
function deduplicateByEmbedding(entries) {
  if (!entries || !Array.isArray(entries) || entries.length < 2) return entries;
  const SIM_THRESHOLD = 0.92;
  const merged = [];
  const skip = new Set();
  for (let i = 0; i < entries.length; i++) {
    if (skip.has(i)) continue;
    const a = entries[i];
    const aText = a.summary || a.content || '';
    if (!aText || aText.length < 10) { merged.push(a); continue; }
    const aEmb = _embedText(aText);
    for (let j = i + 1; j < entries.length; j++) {
      if (skip.has(j)) continue;
      const b = entries[j];
      const bText = b.summary || b.content || '';
      if (!bText || bText.length < 10) continue;
      const bEmb = aEmb ? _embedText(bText) : null;
      if (aEmb && bEmb && _cosineSimilarity(aEmb, bEmb) >= SIM_THRESHOLD) {
        // Merge: keep entry with higher accessCount, merge tags
        if ((b.accessCount || 0) > (a.accessCount || 0)) {
          entries[j].accessCount = (entries[j].accessCount || 0) + (a.accessCount || 0);
          entries[j].confidence = Math.max(entries[j].confidence || 0.5, a.confidence || 0.5);
          skip.add(i);
        } else {
          entries[i].accessCount = (entries[i].accessCount || 0) + (b.accessCount || 0);
          entries[i].confidence = Math.max(entries[i].confidence || 0.5, b.confidence || 0.5);
          skip.add(j);
        }
        break; // each entry merges with at most one other
      }
    }
    if (!skip.has(i)) merged.push(a);
  }
  return merged;
}

// ── Session state helpers ────────────────────────────────────────────────────

function sessionGet(key) {
  try {
    if (!fs.existsSync(SESSION_FILE)) return null;
    const session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8'));
    return key ? ((session.context || {})[key] ?? session[key] ?? null) : session.context;
  } catch { return null; }
}

function sessionSet(key, value) {
  try {
    if (!fs.existsSync(SESSION_DIR)) fs.mkdirSync(SESSION_DIR, { recursive: true });
    let session = {};
    if (fs.existsSync(SESSION_FILE)) {
      session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8'));
    }
    if (!session.context) session.context = {};
    session.context[key] = value;
    session.updatedAt = new Date().toISOString();
    fs.writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2), 'utf-8');
  } catch { /* best effort */ }
}

// ── PageRank ─────────────────────────────────────────────────────────────────

function computePageRank(nodes, edges, damping, maxIter) {
  damping = damping || 0.85;
  maxIter = maxIter || 30;

  const ids = Object.keys(nodes);
  const n = ids.length;
  if (n === 0) return {};

  // Build adjacency: outgoing edges per node
  const outLinks = {};
  const inLinks = {};
  for (const id of ids) { outLinks[id] = []; inLinks[id] = []; }
  for (const edge of edges) {
    if (outLinks[edge.sourceId]) outLinks[edge.sourceId].push(edge.targetId);
    if (inLinks[edge.targetId]) inLinks[edge.targetId].push(edge.sourceId);
  }

  // Initialize ranks
  const ranks = {};
  for (const id of ids) ranks[id] = 1 / n;

  // Power iteration (with dangling node redistribution)
  for (let iter = 0; iter < maxIter; iter++) {
    const newRanks = {};
    let diff = 0;

    // Collect rank from dangling nodes (no outgoing edges)
    let danglingSum = 0;
    for (const id of ids) {
      if (outLinks[id].length === 0) danglingSum += ranks[id];
    }

    for (const id of ids) {
      let sum = 0;
      for (const src of inLinks[id]) {
        const outCount = outLinks[src].length;
        if (outCount > 0) sum += ranks[src] / outCount;
      }
      // Dangling rank distributed evenly + teleport
      newRanks[id] = (1 - damping) / n + damping * (sum + danglingSum / n);
      diff += Math.abs(newRanks[id] - ranks[id]);
    }

    for (const id of ids) ranks[id] = newRanks[id];
    if (diff < 1e-6) break; // converged
  }

  return ranks;
}

// ── Edge building ────────────────────────────────────────────────────────────

function buildEdges(entries) {
  const edges = [];
  const byCategory = {};

  for (const entry of entries) {
    const cat = entry.category || entry.namespace || 'default';
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(entry);
  }

  // Temporal edges: entries from same sourceFile
  const byFile = {};
  for (const entry of entries) {
    const file = (entry.metadata && entry.metadata.sourceFile) || null;
    if (file) {
      if (!byFile[file]) byFile[file] = [];
      byFile[file].push(entry);
    }
  }
  for (const file of Object.keys(byFile)) {
    const group = byFile[file];
    for (let i = 0; i < group.length - 1; i++) {
      edges.push({
        sourceId: group[i].id,
        targetId: group[i + 1].id,
        type: 'temporal',
        weight: 0.5,
      });
    }
  }

  // Similarity edges within categories (Jaccard > 0.55).
  // ADR-095 G6 perf: hoist the trigram computation outside the inner
  // loop. Previously we re-tokenized + re-trigrammed group[j] for every
  // i — O(n²) extra work for nothing. Now compute once per entry.
  for (const cat of Object.keys(byCategory)) {
    const group = byCategory[cat];
    if (group.length < 2) continue;

    // Cache trigram sets for every entry in the group.
    // Strip boilerplate from insight entries — the template "File X was edited N
    // times this session" produces 45-60 shared trigrams across all insight entries,
    // causing ~97% false-positive similarity edges at the default threshold.
    const triCache = new Array(group.length);
    for (let i = 0; i < group.length; i++) {
      let text = group[i].content || group[i].summary || '';
      if (cat === 'insights' && group[i].summary) {
        text = group[i].summary; // filename + count only, no boilerplate
      }
      triCache[i] = trigrams(tokenize(text));
    }

    for (let i = 0; i < group.length; i++) {
      const triA = triCache[i];
      for (let j = i + 1; j < group.length; j++) {
        const sim = jaccardSimilarity(triA, triCache[j]);
        if (sim > 0.70) {
          edges.push({
            sourceId: group[i].id,
            targetId: group[j].id,
            type: 'similar',
            weight: sim,
          });
        }
      }
    }
  }

  return edges;
}

// ── Bootstrap from MEMORY.md files ───────────────────────────────────────────

/**
 * If auto-memory-store.json is empty, bootstrap by parsing MEMORY.md and
 * topic files from the auto-memory directory. This removes the dependency
 * on @claude-flow/memory for the initial seed.
 */
function bootstrapFromMemoryFiles() {
  const entries = [];
  const cwd = process.cwd();

  // Search for auto-memory directories
  const candidates = [
    // Claude Code auto-memory (project-scoped)
    path.join(require('os').homedir(), '.claude', 'projects'),
    // Local project memory
    path.join(cwd, '.claude-flow', 'memory'),
    path.join(cwd, '.claude', 'memory'),
  ];

  // Find MEMORY.md in project-scoped dirs
  for (const base of candidates) {
    if (!fs.existsSync(base)) continue;

    // For the projects dir, scope to CURRENT project only (not all 51+ dirs)
    if (base.endsWith('projects')) {
      try {
        // Claude Code prepends '-' for absolute paths
        const projectSlug = '-' + cwd.replace(/^\//, '').replace(/\//g, '-');
        const memDir = path.join(base, projectSlug, 'memory');
        if (fs.existsSync(memDir)) {
          parseMemoryDir(memDir, entries);
        }
      } catch { /* skip */ }
    } else if (fs.existsSync(base)) {
      parseMemoryDir(base, entries);
    }
  }

  return entries;
}

function parseMemoryDir(dir, entries) {
  try {
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.md'));
    for (const file of files) {
      const filePath = path.join(dir, file);
      const content = fs.readFileSync(filePath, 'utf-8');
      if (!content.trim()) continue;

      // Parse markdown sections as separate entries
      const sections = content.split(/^##?\s+/m).filter(Boolean);
      for (let sIdx = 0; sIdx < sections.length; sIdx++) {
        const section = sections[sIdx];
        const lines = section.trim().split('\n');
        const title = lines[0].trim();
        const body = lines.slice(1).join('\n').trim();
        if (!body || body.length < 10) continue;

        const id = `mem-${file.replace('.md', '')}-${title.replace(/[^a-z0-9]/gi, '-').toLowerCase().slice(0, 30)}-${sIdx}`;
        entries.push({
          id,
          key: title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 50),
          content: body.slice(0, 500),
          summary: title,
          namespace: file === 'MEMORY.md' ? 'core' : file.replace('.md', ''),
          type: 'semantic',
          metadata: { sourceFile: filePath, bootstrapped: true },
          createdAt: Date.now(),
        });
      }
    }
  } catch { /* skip unreadable dirs */ }
}

// ── Exported functions ───────────────────────────────────────────────────────

/**
 * init() — Called from session-restore. Budget: <200ms.
 * Reads auto-memory-store.json, builds graph, computes PageRank, writes caches.
 * If store is empty, bootstraps from MEMORY.md files directly.
 */
function init() {
  ensureDataDir();

  // Check if graph-state.json is fresh (within 60s of store)
  const graphState = readJSON(GRAPH_PATH);
  let store = readJSON(STORE_PATH);

  // Bootstrap from MEMORY.md files if store is empty
  if (!store || !Array.isArray(store) || store.length === 0) {
    const bootstrapped = bootstrapFromMemoryFiles();
    if (bootstrapped.length > 0) {
      store = bootstrapped;
      writeJSON(STORE_PATH, store);
    } else {
      return { nodes: 0, edges: 0, message: 'No memory entries to index' };
    }
  }

  // Deduplicate store entries by ID (fixes #1518 — 194MB → ~79KB)
  let deduped = deduplicateById(store);
  // ADR-095 G6: also dedupe by content fingerprint. The April audit
  // measured 5,706 entries with only ~20 unique by content because the
  // same MEMORY.md sections get imported from sibling project dirs with
  // different IDs. deduplicateById can't catch that; deduplicateByContent
  // can. Cuts the graph from O(n²) over near-identical duplicates down
  // to O(unique²), which is the difference between a 100MB graph-state
  // and a kilobytes-scale one for typical workloads.
  const beforeContentDedup = deduped.length;
  deduped = deduplicateByContent(deduped);
  if (deduped.length < store.length) {
    process.stderr.write(
      `[INTELLIGENCE] Deduped store: ${store.length} -> ${deduped.length} entries ` +
      `(by-id: ${store.length - beforeContentDedup} dropped, by-content: ${beforeContentDedup - deduped.length} dropped)\n`
    );
    writeJSON(STORE_PATH, deduped);
  }

  // Ensure every entry has a summary — bootstrapped entries from auto-memory-hook.mjs
  // often lack them, making them invisible in ranked context display.
  for (const entry of deduped) {
    if (!entry.summary) {
      entry.summary = (entry.content || entry.value || '')
        .replace(/^[#\s\-*•]+/gm, '')
        .trim()
        .split('\n')
        .filter(l => l.trim().length > 0)
        .slice(0, 2)
        .join('; ')
        .slice(0, 100);
    }
  }

  // Skip rebuild if graph is fresh and store hasn't changed
  if (graphState && graphState.nodeCount === deduped.length) {
    const age = Date.now() - (graphState.updatedAt || 0);
    if (age < 3600000) {
      return {
        nodes: graphState.nodeCount || Object.keys(graphState.nodes || {}).length,
        edges: (graphState.edges || []).length,
        message: 'Graph cache hit',
      };
    }
  }

  // Build nodes from deduped entries (preserve accessCount from previous graph state)
  const nodes = {};
  for (const entry of deduped) {
    const id = entry.id || entry.key || `entry-${Math.random().toString(36).slice(2, 8)}`;
    const prevNode = (graphState && graphState.nodes && graphState.nodes[id]) || {};
    nodes[id] = {
      id,
      category: entry.namespace || entry.type || 'default',
      confidence: (entry.metadata && entry.metadata.confidence) || prevNode.confidence || 0.5,
      accessCount: (entry.metadata && entry.metadata.accessCount) || entry.accessCount || prevNode.accessCount || 0,
      lastDecayAt: prevNode.lastDecayAt || undefined,
      createdAt: entry.createdAt || Date.now(),
    };
    // Ensure entry has id for edge building
    entry.id = id;
  }

  // Build edges
  const edges = buildEdges(deduped);

  // Compute PageRank (skip if graph too large — #1531)
  const nodeCount = Object.keys(nodes).length;
  let pageRanks = {};
  if (nodeCount > MAX_GRAPH_NODES) {
    process.stderr.write("[INTELLIGENCE] WARN: Graph has " + nodeCount + " nodes (>" + MAX_GRAPH_NODES + "), skipping PageRank\n");
    for (const id of Object.keys(nodes)) pageRanks[id] = 1 / nodeCount;
  } else {
    pageRanks = computePageRank(nodes, edges, 0.85, 30);
  }

  // Write graph state
  const graph = {
    version: 1,
    updatedAt: Date.now(),
    nodeCount: Object.keys(nodes).length,
    nodes,
    edges,
    pageRanks,
  };
  writeJSON(GRAPH_PATH, graph);

  // Build ranked context for fast lookup
  const rankedEntries = deduped.map(entry => {
    const id = entry.id;
    const content = entry.content || entry.value || '';
    const summary = entry.summary || entry.key || '';
    const words = tokenize(content + ' ' + summary);
    return {
      id,
      content,
      summary,
      category: entry.namespace || entry.type || 'default',
      confidence: nodes[id] ? nodes[id].confidence : 0.5,
      pageRank: pageRanks[id] || 0,
      accessCount: nodes[id] ? nodes[id].accessCount : 0,
      words,
    };
  }).sort((a, b) => {
    const scoreA = 0.6 * a.pageRank + 0.4 * a.confidence;
    const scoreB = 0.6 * b.pageRank + 0.4 * b.confidence;
    return scoreB - scoreA;
  });

  const ranked = {
    version: 1,
    computedAt: Date.now(),
    entries: rankedEntries,
  };
  writeJSON(RANKED_PATH, ranked);

  return {
    nodes: Object.keys(nodes).length,
    edges: edges.length,
    message: 'Graph built and ranked',
  };
}

/**
 * getContext(prompt) — Called from route. Budget: <15ms.
 * Matches prompt to ranked entries, returns top-5 formatted context.
 */
function getContext(prompt) {
  if (!prompt) return null;

  const ranked = readJSON(RANKED_PATH);
  if (!ranked || !ranked.entries || ranked.entries.length === 0) return null;

  const promptWords = tokenize(prompt);
  if (promptWords.length === 0) return null;
  const promptTrigrams = trigrams(promptWords);

  const SEMANTIC_GAMMA = 0.35; // embedding similarity weight
  const MATCH_ALPHA = 0.25; // trigram content match weight
  const KEYWORD_BETA = 0.25; // word overlap weight
  const PAGERANK_DELTA = 0.15; // PageRank weight
  const MIN_THRESHOLD = 0.05;
  const TOP_K = 5;
  const FAST_PASS_THRESHOLD = 0.25; // skip embeddings if fast scoring already good

  // Fast pass: score by trigram + keyword + PageRank only (no embedding)
  const fastScores = [];
  for (const entry of ranked.entries) {
    const entryTrigrams = trigrams(entry.words || []);
    const contentMatch = jaccardSimilarity(promptTrigrams, entryTrigrams);
    const wordMatches = promptWords.filter(w => (entry.words || []).includes(w)).length;
    const wordOverlap = promptWords.length > 0 ? wordMatches / promptWords.length : 0;
    const fastScore = MATCH_ALPHA * contentMatch + KEYWORD_BETA * wordOverlap + PAGERANK_DELTA * (entry.pageRank || 0);
    fastScores.push(fastScore);
  }
  const bestFastScore = fastScores.length > 0 ? Math.max(...fastScores) : 0;

  // Only compute prompt embedding if fast scoring is weak (needs semantic help)
  // Saves ~150ms Ollama call per query when keywords already match well
  let promptEmbedding = null;
  if (bestFastScore < FAST_PASS_THRESHOLD) {
    promptEmbedding = _embedText(prompt);
  }

  // Score each entry with available signals
  const scored = [];
  for (let i = 0; i < ranked.entries.length; i++) {
    const entry = ranked.entries[i];
    const contentMatch = jaccardSimilarity(promptTrigrams, trigrams(entry.words || []));
    const wordMatches = promptWords.filter(w => (entry.words || []).includes(w)).length;
    const wordOverlap = promptWords.length > 0 ? wordMatches / promptWords.length : 0;
    let semanticSim = 0;
    if (promptEmbedding) {
      // Use pre-computed embedding from ranked context if available
      if (entry.embedding) {
        semanticSim = _cosineSimilarity(promptEmbedding, entry.embedding);
      } else {
        // Fallback: compute on demand (cold cache)
        const entryEmb = _embedText(entry.summary || entry.content || '');
        if (entryEmb) semanticSim = _cosineSimilarity(promptEmbedding, entryEmb);
      }
    }
    const score = MATCH_ALPHA * contentMatch + KEYWORD_BETA * wordOverlap + SEMANTIC_GAMMA * semanticSim + PAGERANK_DELTA * (entry.pageRank || 0);
    if (score >= MIN_THRESHOLD) {
      scored.push({ ...entry, score });
    }
  }

  if (scored.length === 0) return null;

  // Sort by score descending, take top-K
  scored.sort((a, b) => b.score - a.score);
  const topEntries = scored.slice(0, TOP_K);

  // Exploration: every ~20 queries, inject a random low-PageRank entry for discovery
  const explorationRoll = sessionGet('explorationRoll');
  const explorationCount = ((explorationRoll || 0) + 1) % 20;
  sessionSet('explorationRoll', explorationCount);
  if (explorationCount === 0 && scored.length > TOP_K) {
    const bottomHalf = scored.slice(TOP_K);
    const randomEntry = bottomHalf[Math.floor(Math.random() * bottomHalf.length)];
    if (randomEntry) {
      topEntries[TOP_K - 1] = randomEntry; // replace last slot
      topEntries.sort((a, b) => b.score - a.score); // re-sort
    }
  }

  // Boost previously matched patterns (implicit success: user continued working)
  const prevMatched = sessionGet('lastMatchedPatterns');

  // Store NEW matched IDs in session state for feedback
  const matchedIds = topEntries.map(e => e.id);
  sessionSet('lastMatchedPatterns', matchedIds);

  // Boost currently matched entries — being selected as relevant = evidence of utility.
  // This is the only positive feedback loop that moves confidence above the initial 0.5.
  boostConfidence(matchedIds, 0.02);

  // Only boost previous if they differ from current (avoid double-boosting)
  if (prevMatched && Array.isArray(prevMatched)) {
    const newSet = new Set(matchedIds);
    const toBoost = prevMatched.filter(id => !newSet.has(id));
    if (toBoost.length > 0) boostConfidence(toBoost, 0.03);
  }

  // Format output
  const lines = ['[INTELLIGENCE] Relevant patterns for this task:'];
  for (let i = 0; i < topEntries.length; i++) {
    const e = topEntries[i];
    const display = (e.summary || e.content || '').slice(0, 80);
    const accessed = e.accessCount || 0;
    lines.push(`  * (${e.score.toFixed(2)}) ${display} [rank #${i + 1}, ${accessed}x accessed]`);
  }

  // ── Skill auto-trigger suggestions ─────────────────────────────────────
  // Match prompt against known skill activation patterns (no LLM needed)
  const promptLower = (prompt || '').toLowerCase();
  const skillSignatures = [
    { skill: 'swarm-advanced', triggers: ['swarm', 'parallel', 'multi-agent', 'coordination', 'distributed', 'orchestrat', 'fan-out', 'hierarchical', 'mesh'] },
    { skill: 'gitnexus-impact-analysis', triggers: ['impact', 'blast radius', 'refactor', 'rename', 'what break', 'affects', 'caller', 'upstream', 'downstream'] },
    { skill: 'gitnexus-debugging', triggers: ['debug', 'trace', 'error', 'crash', 'stack trace', 'failing', 'exception', 'bug in'] },
    { skill: 'gitnexus-refactoring', triggers: ['extract', 'split', 'move code', 'inline', 'rename symbol', 'restructure'] },
    { skill: 'gitnexus-exploring', triggers: ['explore', 'understand', 'how does', 'find execution', 'call chain'] },
    { skill: 'frontend-design', triggers: ['design', 'ui', 'ux', 'component', 'layout', 'beautiful', 'tailwind', 'css', 'dark mode', 'animation', 'premium', 'linear-style'] },
    { skill: 'ui-ux-pro-max', triggers: ['gradient', 'button', 'card', 'dashboard', 'landing page', 'responsive', 'font', 'typography', 'color scheme'] },
    { skill: 'brainstorming', triggers: ['brainstorm', 'ideate', 'think', 'explore options', 'possible approaches', 'what if'] },
    { skill: 'debugging', triggers: ['bug', 'fix', 'error', 'not working', 'broken', 'issue', 'incorrect', 'unexpected'] },
    { skill: 'tdd', triggers: ['test first', 'tdd', 'write test', 'test-driven', 'red green refactor'] },
    { skill: 'code-review', triggers: ['review', 'check quality', 'security scan', 'best practice', 'lint'] },
    { skill: 'architecture', triggers: ['architect', 'system design', 'pattern', 'scalability', 'api design', 'schema'] },
    { skill: 'adr-architect', triggers: ['adr', 'decision record', 'architectural decision', 'adr-'] },
    { skill: 'deploy-to-vercel', triggers: ['deploy', 'vercel', 'production', 'hosting', 'publish'] },
    { skill: 'github-code-review', triggers: ['github', 'pull request', 'pr', 'code review', 'merge'] },
    { skill: 'mirofish_simulation', triggers: ['simulate', 'forecast', 'consensus', 'mirofish', 'scenario'] },
    { skill: 'web-search', triggers: ['search', 'find online', 'look up', 'google', 'research'] },
    { skill: 'brainstorming', triggers: ['brainstorm', 'ideate', 'explore options'] },
  ];

  const matched = [];
  const seen = new Set();
  for (const s of skillSignatures) {
    if (seen.has(s.skill)) continue;
    for (const t of s.triggers) {
      if (promptLower.includes(t)) { matched.push(s.skill); seen.add(s.skill); break; }
    }
  }
  if (matched.length > 0) {
    lines.push('');
    lines.push('[💡 Skill Auto-Trigger] Consider: ' + matched.join(', '));
  }

  return lines.join('\n');
}

/**
 * recordEdit(file) — Called from post-edit. Budget: <2ms.
 * Appends to pending-insights.jsonl.
 */
function recordEdit(file) {
  ensureDataDir();
  const entry = JSON.stringify({
    type: 'edit',
    file: file || 'unknown',
    timestamp: Date.now(),
    sessionId: sessionGet('id') || null,
  });
  fs.appendFileSync(PENDING_PATH, entry + '\n', 'utf-8');
}

/**
 * feedback(success) — Called from post-task. Budget: <10ms.
 * Boosts or decays confidence for last-matched patterns.
 */
function feedback(success) {
  const matchedIds = sessionGet('lastMatchedPatterns');
  if (!matchedIds || !Array.isArray(matchedIds)) return;

  const amount = success ? 0.05 : -0.02;
  boostConfidence(matchedIds, amount);
}

function boostConfidence(ids, amount) {
  const ranked = readJSON(RANKED_PATH);
  if (!ranked || !ranked.entries) return;

  let changed = false;
  for (const entry of ranked.entries) {
    if (ids.includes(entry.id)) {
      entry.confidence = Math.max(0, Math.min(1, (entry.confidence || 0.5) + amount));
      entry.accessCount = (entry.accessCount || 0) + 1;
      changed = true;
    }
  }

  if (changed) writeJSON(RANKED_PATH, ranked);

  // Also update graph-state confidence
  const graph = readJSON(GRAPH_PATH);
  if (graph && graph.nodes) {
    for (const id of ids) {
      if (graph.nodes[id]) {
        graph.nodes[id].confidence = Math.max(0, Math.min(1, (graph.nodes[id].confidence || 0.5) + amount));
        graph.nodes[id].accessCount = (graph.nodes[id].accessCount || 0) + 1;
      }
    }
    writeJSON(GRAPH_PATH, graph);

    // Also propagate accessCount + confidence back to the store entries
    // so boost data survives if graph-state.json is rebuilt from scratch
    const store = readJSON(STORE_PATH);
    if (store && Array.isArray(store)) {
      let storeChanged = false;
      for (const entry of store) {
        if (graph.nodes[entry.id]) {
          entry.accessCount = graph.nodes[entry.id].accessCount;
          entry.confidence = graph.nodes[entry.id].confidence;
          if (!entry.metadata) entry.metadata = {};
          entry.metadata.accessCount = entry.accessCount;
          entry.metadata.confidence = entry.confidence;
          storeChanged = true;
        }
      }
      if (storeChanged) writeJSON(STORE_PATH, store);
    }
  }
}

/**
 * consolidate() — Called from session-end. Budget: <500ms.
 * Processes pending insights, rebuilds edges, recomputes PageRank.
 */
function consolidate() {
  ensureDataDir();

  let store = readJSON(STORE_PATH);
  if (!store || !Array.isArray(store)) {
    return { entries: 0, edges: 0, newEntries: 0, message: 'No store to consolidate' };
  }

  // Deduplicate store entries by ID, content, and semantic embedding (fixes #1518, #auto9, ADR-115)
  const preDedupCount = store.length;
  store = deduplicateById(store);
  store = deduplicateByContent(store);
  store = deduplicateByEmbedding(store);

  // Generate summaries for entries that lack them (eg auto-memory entries)
  for (const entry of store) {
    if (!entry.summary) {
      entry.summary = (entry.content || entry.value || '')
        .replace(/^[#\s\-*•]+/gm, '')
        .trim()
        .split('\n')
        .filter(l => l.trim().length > 0)
        .slice(0, 2)
        .join('; ')
        .slice(0, 100);
    }
  }

  // 1. Process pending insights
  let newEntries = 0;
  if (fs.existsSync(PENDING_PATH)) {
    const lines = fs.readFileSync(PENDING_PATH, 'utf-8').trim().split('\n').filter(Boolean);
    const editCounts = {};
    for (const line of lines) {
      try {
        const insight = JSON.parse(line);
        if (insight.file) {
          editCounts[insight.file] = (editCounts[insight.file] || 0) + 1;
        }
      } catch { /* skip malformed */ }
    }

    // Create entries for frequently-edited files (5+ edits, was 3 — raised to reduce noise)
    for (const [file, count] of Object.entries(editCounts)) {
      if (count >= 5) {
        const exists = store.some(e =>
          (e.metadata && e.metadata.sourceFile === file && e.metadata.autoGenerated)
        );
        if (!exists) {
          store.push({
            id: `insight-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
            key: `frequent-edit-${path.basename(file)}`,
            content: `File ${file} was edited ${count} times this session — likely a hot path worth monitoring.`,
            summary: `Frequently edited: ${path.basename(file)} (${count}x)`,
            namespace: 'insights',
            type: 'procedural',
            metadata: { sourceFile: file, editCount: count, autoGenerated: true },
            createdAt: Date.now(),
          });
          newEntries++;
        }
      }
    }

    // Clear pending
    try { fs.writeFileSync(PENDING_PATH, '', 'utf-8'); } catch (e) { process.stderr.write('[INTELLIGENCE] WARN: Failed to clear pending: ' + e.message + '\n'); }
  }

  // 2. Confidence decay — proportional to accessCount so popular entries cool slower
  //    This prevents the rich-get-richer dynamic where 1 hit exempts from decay forever.
  //    accessCount=0 → -0.005/day, accessCount=50 → -0.001/day, accessCount=100+ → -0.0005/day
  const graph = readJSON(GRAPH_PATH);
  if (graph && graph.nodes) {
    const now = Date.now();
    for (const id of Object.keys(graph.nodes)) {
      const node = graph.nodes[id];
      const lastDecay = node.lastDecayAt || node.createdAt || now;
      const hoursSinceLastDecay = (now - lastDecay) / (1000 * 60 * 60);
      if (hoursSinceLastDecay > 24) {
        const decayDays = Math.floor(hoursSinceLastDecay / 24);
        const accessCount = node.accessCount || 0;
        const scale = Math.max(0.1, 1 - (Math.min(accessCount, 100) / 100 * 0.9));
        node.confidence = Math.max(0.05, (node.confidence || 0.5) - 0.005 * scale * decayDays);
        node.lastDecayAt = now;
      }
    }
  }

  // 2.5. Automatic curation: archive entries not accessed in 60+ days, low confidence, low access
  const archiveThreshold = Date.now() - 60 * 24 * 60 * 60 * 1000;
  const preCuration = store.length;
  store = store.filter(entry => {
    if (!entry.createdAt || entry.createdAt > archiveThreshold) return true;
    if ((entry.accessCount || 0) >= 2) return true;
    if ((entry.confidence || 0.5) >= 0.2) return true;
    entry.archived = true;
    entry.summary = '[ARCHIVED] ' + (entry.summary || entry.content || '').slice(0, 80);
    return false;
  });
  const curated = preCuration - store.length;
  if (curated > 0) process.stderr.write('[INTELLIGENCE] Curated ' + curated + ' stale entries\n');

  // 3. Rebuild edges with updated store
  for (const entry of store) {
    if (!entry.id) entry.id = `entry-${Math.random().toString(36).slice(2, 8)}`;
  }
  const edges = buildEdges(store);

  // 4. Build updated nodes
  const nodes = {};
  for (const entry of store) {
    nodes[entry.id] = {
      id: entry.id,
      category: entry.namespace || entry.type || 'default',
      confidence: (graph && graph.nodes && graph.nodes[entry.id])
        ? graph.nodes[entry.id].confidence
        : (entry.metadata && entry.metadata.confidence) || 0.5,
      accessCount: (graph && graph.nodes && graph.nodes[entry.id])
        ? graph.nodes[entry.id].accessCount
        : (entry.metadata && entry.metadata.accessCount) || 0,
      lastDecayAt: (graph && graph.nodes && graph.nodes[entry.id])
        ? graph.nodes[entry.id].lastDecayAt
        : undefined,
      createdAt: entry.createdAt || Date.now(),
    };
  }

  // 5. Recompute PageRank (skip if graph too large — #1531)
  const nodeCount = Object.keys(nodes).length;
  let pageRanks = {};
  if (nodeCount > MAX_GRAPH_NODES) {
    process.stderr.write("[INTELLIGENCE] WARN: Graph has " + nodeCount + " nodes (>" + MAX_GRAPH_NODES + "), skipping PageRank in consolidate\n");
    for (const id of Object.keys(nodes)) pageRanks[id] = 1 / nodeCount;
  } else {
    pageRanks = computePageRank(nodes, edges, 0.85, 30);
  }

  // 6. Write updated graph
  writeJSON(GRAPH_PATH, {
    version: 1,
    updatedAt: Date.now(),
    nodeCount: Object.keys(nodes).length,
    nodes,
    edges,
    pageRanks,
  });

  // 7. Write updated ranked context with pre-computed embeddings
  const rankedEntries = store.map(entry => {
    const id = entry.id;
    const content = entry.content || entry.value || '';
    const summary = entry.summary || entry.key || '';
    const words = tokenize(content + ' ' + summary);
    // Pre-compute embedding for fast recall (background, non-blocking)
    const entryText = (summary || content || '').slice(0, 256);
    const embedding = entryText.length > 10 ? _embedText(entryText) : null;
    return {
      id,
      content,
      summary,
      category: entry.namespace || entry.type || 'default',
      confidence: nodes[id] ? nodes[id].confidence : 0.5,
      pageRank: pageRanks[id] || 0,
      accessCount: nodes[id] ? nodes[id].accessCount : 0,
      words,
      embedding, // pre-computed for getContext semantic scoring
    };
  }).sort((a, b) => {
    const scoreA = 0.6 * a.pageRank + 0.4 * a.confidence;
    const scoreB = 0.6 * b.pageRank + 0.4 * b.confidence;
    return scoreB - scoreA;
  });

  writeJSON(RANKED_PATH, {
    version: 1,
    computedAt: Date.now(),
    entries: rankedEntries,
  });

  // 8. Prune stale entries (confidence < 0.15, never accessed, >7 days old)
  const now = Date.now();
  const storeBefore = store.length;
  const staleIds = new Set();
  for (const entry of store) {
    const node = nodes[entry.id];
    if (node) {
      const ageDays = (now - (node.createdAt || now)) / 86400000;
      if (node.accessCount === 0 && (node.confidence || 0.5) < 0.15 && ageDays > 7) {
        staleIds.add(entry.id);
      }
    }
  }
  if (staleIds.size > 0) {
    store = store.filter(e => !staleIds.has(e.id));
    for (const id of staleIds) delete nodes[id];
    process.stderr.write(`[INTELLIGENCE] [PRUNE] Removed ${staleIds.size} stale entries (never accessed, low confidence, >7d)\n`);
  }

  // 9. Propagate accessCount and confidence from graph nodes back to store entries
  // so boost/decay data survives future graph rebuilds (fixes persistence gap)
  for (const entry of store) {
    if (nodes[entry.id]) {
      entry.accessCount = nodes[entry.id].accessCount;
      entry.confidence = nodes[entry.id].confidence;
      if (!entry.metadata) entry.metadata = {};
      entry.metadata.accessCount = entry.accessCount;
      entry.metadata.confidence = entry.confidence;
    }
  }

  // 10. Persist updated store
  writeJSON(STORE_PATH, store);

  // 11. Save snapshot for delta tracking
  const updatedGraph = readJSON(GRAPH_PATH);
  const updatedRanked = readJSON(RANKED_PATH);
  saveSnapshot(updatedGraph, updatedRanked);

  return {
    entries: store.length,
    edges: edges.length,
    newEntries,
    pruned: staleIds.size,
    message: 'Consolidated',
  };
}

// ── Snapshot for delta tracking ─────────────────────────────────────────────

const SNAPSHOT_PATH = path.join(DATA_DIR, 'intelligence-snapshot.json');

function saveSnapshot(graph, ranked) {
  const snap = {
    timestamp: Date.now(),
    nodes: graph ? Object.keys(graph.nodes || {}).length : 0,
    edges: graph ? (graph.edges || []).length : 0,
    pageRankSum: 0,
    confidences: [],
    accessCounts: [],
    topPatterns: [],
  };

  if (graph && graph.pageRanks) {
    for (const v of Object.values(graph.pageRanks)) snap.pageRankSum += v;
  }
  if (graph && graph.nodes) {
    for (const n of Object.values(graph.nodes)) {
      snap.confidences.push(n.confidence || 0.5);
      snap.accessCounts.push(n.accessCount || 0);
    }
  }
  if (ranked && ranked.entries) {
    snap.topPatterns = ranked.entries.slice(0, 10).map(e => ({
      id: e.id,
      summary: (e.summary || '').slice(0, 60),
      confidence: e.confidence || 0.5,
      pageRank: e.pageRank || 0,
      accessCount: e.accessCount || 0,
    }));
  }

  // Keep history: append to array, cap at 50
  let history = readJSON(SNAPSHOT_PATH);
  if (!Array.isArray(history)) history = [];
  history.push(snap);
  if (history.length > 50) history = history.slice(-50);
  writeJSON(SNAPSHOT_PATH, history);
}

/**
 * stats() — Diagnostic report showing intelligence health and improvement.
 * Can be called as: node intelligence.cjs stats [--json]
 */
function stats(outputJson) {
  const graph = readJSON(GRAPH_PATH);
  const ranked = readJSON(RANKED_PATH);
  const history = readJSON(SNAPSHOT_PATH) || [];
  const pending = fs.existsSync(PENDING_PATH)
    ? fs.readFileSync(PENDING_PATH, 'utf-8').trim().split('\n').filter(Boolean).length
    : 0;

  // Current state
  const nodes = graph ? Object.keys(graph.nodes || {}).length : 0;
  const edges = graph ? (graph.edges || []).length : 0;
  const density = nodes > 1 ? (2 * edges) / (nodes * (nodes - 1)) : 0;

  // Confidence distribution
  const confidences = [];
  const accessCounts = [];
  if (graph && graph.nodes) {
    for (const n of Object.values(graph.nodes)) {
      confidences.push(n.confidence || 0.5);
      accessCounts.push(n.accessCount || 0);
    }
  }
  confidences.sort((a, b) => a - b);
  const confMin = confidences.length ? confidences[0] : 0;
  const confMax = confidences.length ? confidences[confidences.length - 1] : 0;
  const confMean = confidences.length ? confidences.reduce((s, c) => s + c, 0) / confidences.length : 0;
  const confMedian = confidences.length ? confidences[Math.floor(confidences.length / 2)] : 0;

  // Access stats
  const totalAccess = accessCounts.reduce((s, c) => s + c, 0);
  const accessedCount = accessCounts.filter(c => c > 0).length;

  // PageRank stats
  let prSum = 0, prMax = 0, prMaxId = '';
  if (graph && graph.pageRanks) {
    for (const [id, pr] of Object.entries(graph.pageRanks)) {
      prSum += pr;
      if (pr > prMax) { prMax = pr; prMaxId = id; }
    }
  }

  // Top patterns by composite score
  const topPatterns = (ranked && ranked.entries || []).slice(0, 10).map((e, i) => ({
    rank: i + 1,
    summary: (e.summary || '').slice(0, 60),
    confidence: (e.confidence || 0.5).toFixed(3),
    pageRank: (e.pageRank || 0).toFixed(4),
    accessed: e.accessCount || 0,
    score: (0.6 * (e.pageRank || 0) + 0.4 * (e.confidence || 0.5)).toFixed(4),
  }));

  // Edge type breakdown
  const edgeTypes = {};
  if (graph && graph.edges) {
    for (const e of graph.edges) {
      edgeTypes[e.type || 'unknown'] = (edgeTypes[e.type || 'unknown'] || 0) + 1;
    }
  }

  // Delta from previous snapshot
  let delta = null;
  if (history.length >= 2) {
    const prev = history[history.length - 2];
    const curr = history[history.length - 1];
    const elapsed = (curr.timestamp - prev.timestamp) / 1000;
    const prevConfMean = prev.confidences.length
      ? prev.confidences.reduce((s, c) => s + c, 0) / prev.confidences.length : 0;
    const currConfMean = curr.confidences.length
      ? curr.confidences.reduce((s, c) => s + c, 0) / curr.confidences.length : 0;
    const prevAccess = prev.accessCounts.reduce((s, c) => s + c, 0);
    const currAccess = curr.accessCounts.reduce((s, c) => s + c, 0);

    delta = {
      elapsed: elapsed < 3600 ? `${Math.round(elapsed / 60)}m` : `${(elapsed / 3600).toFixed(1)}h`,
      nodes: curr.nodes - prev.nodes,
      edges: curr.edges - prev.edges,
      confidenceMean: currConfMean - prevConfMean,
      totalAccess: currAccess - prevAccess,
    };
  }

  // Trend over all history
  let trend = null;
  if (history.length >= 3) {
    const first = history[0];
    const last = history[history.length - 1];
    const sessions = history.length;
    const firstConfMean = first.confidences.length
      ? first.confidences.reduce((s, c) => s + c, 0) / first.confidences.length : 0;
    const lastConfMean = last.confidences.length
      ? last.confidences.reduce((s, c) => s + c, 0) / last.confidences.length : 0;
    trend = {
      sessions,
      nodeGrowth: last.nodes - first.nodes,
      edgeGrowth: last.edges - first.edges,
      confidenceDrift: lastConfMean - firstConfMean,
      direction: lastConfMean > firstConfMean ? 'improving' :
                 lastConfMean < firstConfMean ? 'declining' : 'stable',
    };
  }

  const report = {
    graph: { nodes, edges, density: +density.toFixed(4) },
    confidence: {
      min: +confMin.toFixed(3), max: +confMax.toFixed(3),
      mean: +confMean.toFixed(3), median: +confMedian.toFixed(3),
    },
    access: { total: totalAccess, patternsAccessed: accessedCount, patternsNeverAccessed: nodes - accessedCount },
    pageRank: { sum: +prSum.toFixed(4), topNode: prMaxId, topNodeRank: +prMax.toFixed(4) },
    edgeTypes,
    pendingInsights: pending,
    snapshots: history.length,
    topPatterns,
    delta,
    trend,
  };

  if (outputJson) {
    console.log(JSON.stringify(report, null, 2));
    return report;
  }

  // Human-readable output
  const bar = '+' + '-'.repeat(62) + '+';
  console.log(bar);
  console.log('|' + '  Intelligence Diagnostics (ADR-050)'.padEnd(62) + '|');
  console.log(bar);
  console.log('');

  console.log('  Graph');
  console.log(`    Nodes:    ${nodes}`);
  console.log(`    Edges:    ${edges} (${Object.entries(edgeTypes).map(([t,c]) => `${c} ${t}`).join(', ') || 'none'})`);
  console.log(`    Density:  ${(density * 100).toFixed(1)}%`);
  console.log('');

  console.log('  Confidence');
  console.log(`    Min:      ${confMin.toFixed(3)}`);
  console.log(`    Max:      ${confMax.toFixed(3)}`);
  console.log(`    Mean:     ${confMean.toFixed(3)}`);
  console.log(`    Median:   ${confMedian.toFixed(3)}`);
  console.log('');

  console.log('  Access');
  console.log(`    Total accesses:     ${totalAccess}`);
  console.log(`    Patterns used:      ${accessedCount}/${nodes}`);
  console.log(`    Never accessed:     ${nodes - accessedCount}`);
  console.log(`    Pending insights:   ${pending}`);
  console.log('');

  console.log('  PageRank');
  console.log(`    Sum:      ${prSum.toFixed(4)} (should be ~1.0)`);
  console.log(`    Top node: ${prMaxId || '(none)'} (${prMax.toFixed(4)})`);
  console.log('');

  if (topPatterns.length > 0) {
    console.log('  Top Patterns (by composite score)');
    console.log('  ' + '-'.repeat(60));
    for (const p of topPatterns) {
      console.log(`    #${p.rank}  ${p.summary}`);
      console.log(`         conf=${p.confidence}  pr=${p.pageRank}  score=${p.score}  accessed=${p.accessed}x`);
    }
    console.log('');
  }

  if (delta) {
    console.log(`  Last Delta (${delta.elapsed} ago)`);
    const sign = v => v > 0 ? `+${v}` : `${v}`;
    console.log(`    Nodes:      ${sign(delta.nodes)}`);
    console.log(`    Edges:      ${sign(delta.edges)}`);
    console.log(`    Confidence: ${delta.confidenceMean >= 0 ? '+' : ''}${delta.confidenceMean.toFixed(4)}`);
    console.log(`    Accesses:   ${sign(delta.totalAccess)}`);
    console.log('');
  }

  if (trend) {
    console.log(`  Trend (${trend.sessions} snapshots)`);
    console.log(`    Node growth:       ${trend.nodeGrowth >= 0 ? '+' : ''}${trend.nodeGrowth}`);
    console.log(`    Edge growth:       ${trend.edgeGrowth >= 0 ? '+' : ''}${trend.edgeGrowth}`);
    console.log(`    Confidence drift:  ${trend.confidenceDrift >= 0 ? '+' : ''}${trend.confidenceDrift.toFixed(4)}`);
    console.log(`    Direction:         ${trend.direction.toUpperCase()}`);
    console.log('');
  }

  if (!delta && !trend) {
    console.log('  No history yet — run more sessions to see deltas and trends.');
    console.log('');
  }

  console.log(bar);
  return report;
}

/**
 * getTopRanked(n) — Read-path fix (Gap 1).
 * Returns top N entries from ranked-context.json by composite score (no prompt needed).
 * Used by session-restore to inject high-value context into every session.
 */
function getTopRanked(n = 5) {
  const ranked = readJSON(RANKED_PATH);
  if (!ranked || !ranked.entries || ranked.entries.length === 0) {
    return '[INTELLIGENCE] No ranked context available yet.';
  }

  const top = ranked.entries.slice(0, Math.min(n, ranked.entries.length));
  const lines = ['[INTELLIGENCE] Top-ranked context for this session:'];
  for (let i = 0; i < top.length; i++) {
    const e = top[i];
    const score = (0.6 * (e.pageRank || 0) + 0.4 * (e.confidence || 0.5)).toFixed(4);
    const summary = (e.summary || e.content || '(no summary)').slice(0, 100);
    const accessed = e.accessCount || 0;
    lines.push(`  ${i + 1}. [score=${score}] ${summary} [${accessed}x accessed]`);
  }
  lines.push(`  (${ranked.entries.length} total entries in ranked index)`);
  return lines.join('\n');
}

module.exports = { init, getContext, getTopRanked, recordEdit, feedback, consolidate, stats };

// ── CLI entrypoint ──────────────────────────────────────────────────────────
if (require.main === module) {
  const cmd = process.argv[2];
  const jsonFlag = process.argv.includes('--json');

  const cmds = {
    init: () => { const r = init(); console.log(JSON.stringify(r)); },
    stats: () => { stats(jsonFlag); },
    consolidate: () => { const r = consolidate(); console.log(JSON.stringify(r)); },
  };

  if (cmd && cmds[cmd]) {
    cmds[cmd]();
  } else {
    console.log('Usage: intelligence.cjs <stats|init|consolidate> [--json]');
    console.log('');
    console.log('  stats         Show intelligence diagnostics and trends');
    console.log('  stats --json  Output as JSON for programmatic use');
    console.log('  init          Build graph and rank entries');
    console.log('  consolidate   Process pending insights and recompute');
  }
}
