#!/usr/bin/env node
/**
 * Unified Memory Recall (ADR-115)
 *
 * Queries all active memory layers, deduplicates, reranks, and returns
 * the best results. Single endpoint for the route hook.
 *
 * Layers queried:
 *   L2 — ChromaDB vector store (semantic via Ollama)
 *   L5 — intelligence.cjs graph (trigram + embedding + PageRank)
 *
 * Dreaming patterns (L3) fed via dreaming-store subprocess.
 *
 * Usage:
 *   node unified-recall.cjs query "<prompt>"   # recall from all layers
 *   node unified-recall.cjs status              # show metrics + cache state
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const DATA_DIR = path.join(process.cwd(), '.claude-flow', 'data');
const METRICS_DIR = path.join(process.cwd(), '.claude-flow', 'metrics');
const METRICS_PATH = path.join(METRICS_DIR, 'recall-metrics.jsonl');
const MAX_METRICS_LINES = 1000;
const CACHE_TTL = 60000; // 60s cache for identical prompts

// ── In-memory cache ─────────────────────────────────────────────────────────

let _cache = null;
let _cacheTime = 0;

function getCached(prompt) {
  if (_cache && Date.now() - _cacheTime < CACHE_TTL && _cache.prompt === prompt) {
    return _cache.results;
  }
  return null;
}

function setCache(prompt, results) {
  _cache = { prompt, results, ts: Date.now() };
  _cacheTime = Date.now();
}

// ── Content fingerprint (same algo as intelligence.cjs) ─────────────────────

function fingerprintContent(text) {
  if (typeof text !== 'string' || text.length === 0) return '0';
  const norm = text.replace(/\s+/g, ' ').trim().toLowerCase();
  let h1 = 0x811c9dc5, h2 = 0xcbf29ce4;
  for (let i = 0; i < norm.length; i++) {
    const c = norm.charCodeAt(i);
    h1 ^= c; h1 = Math.imul(h1, 0x01000193) >>> 0;
    h2 ^= c; h2 = Math.imul(h2, 0x100000001b3 & 0xffffffff) >>> 0;
  }
  return `${h1.toString(16)}_${h2.toString(16)}_${norm.length}`;
}

// ── Layer queries ───────────────────────────────────────────────────────────

function queryIntelligence(prompt) {
  const start = Date.now();
  try {
    const intel = require('./intelligence.cjs');
    const ctx = intel.getContext(prompt);
    if (!ctx) return { results: [], latency: Date.now() - start, source: 'intelligence' };
    // Parse the formatted string back into entries
    const lines = ctx.split('\n').filter(l => l.startsWith('  * ('));
    const results = lines.map(l => {
      const scoreMatch = l.match(/\(\d+\.\d+\)/);
      const contentMatch = l.match(/\) (.+?) \[rank/);
      const rankMatch = l.match(/rank #(\d+)/);
      const accessMatch = l.match(/(\d+)x accessed/);
      return {
        score: scoreMatch ? parseFloat(scoreMatch[0].slice(1, -1)) : 0,
        content: contentMatch ? contentMatch[1].trim() : l,
        rank: rankMatch ? parseInt(rankMatch[1]) : 0,
        accessCount: accessMatch ? parseInt(accessMatch[1]) : 0,
        source: 'graph',
      };
    });
    return { results, latency: Date.now() - start, source: 'intelligence' };
  } catch (e) {
    return { results: [], latency: Date.now() - start, source: 'intelligence', error: e.message };
  }
}

function _ollamaAlive() {
  try {
    const { spawnSync } = require('child_process');
    const r = spawnSync('curl', ['-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:11434/api/tags'], { timeout: 1000, encoding: 'utf-8' });
    return r.stdout && r.stdout.trim() === '200';
  } catch (e) { return false; }
}

function queryChroma(prompt, topK = 5) {
  const start = Date.now();
  // Skip if Ollama is down (saves 3s timeout per query)
  if (!_ollamaAlive()) return { results: [], latency: Date.now() - start, source: 'chroma' };
  try {
    const pyCode = `
import sys, json
try:
    from core.memory.store import MemoryStore
    store = MemoryStore()
    results = store.recall(${JSON.stringify(prompt)}, top_k=${topK}, min_score=0.25)
    if not results:
        print(json.dumps([]))
    else:
        out = []
        for r in results:
            if isinstance(r, dict):
                out.append({
                    "content": r.get("content", r.get("text", "")),
                    "score": r.get("score", r.get("relevance", 0)),
                    "source": "chroma",
                    "metadata": {k: v for k, v in r.items() if k not in ("content", "text", "score", "relevance")}
                })
        print(json.dumps(out))
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(0)
`;
    const result = spawnSync('python3', ['-c', pyCode], {
      cwd: process.cwd(),
      timeout: 5000,
      encoding: 'utf-8',
      env: { ...process.env, PYTHONPATH: process.cwd() },
    });
    if (result.status === 0 && result.stdout && result.stdout.trim()) {
      const parsed = JSON.parse(result.stdout.trim());
      if (Array.isArray(parsed)) {
        return { results: parsed.slice(0, topK), latency: Date.now() - start, source: 'chroma' };
      }
    }
  } catch (e) { /* chroma unavailable */ }
  return { results: [], latency: Date.now() - start, source: 'chroma' };
}

function queryWiki(prompt, topK = 3) {
  const start = Date.now();
  const WIKI_DIR = path.join(process.cwd(), '.wiki');
  try {
    if (!fs.existsSync(WIKI_DIR)) return { results: [], latency: Date.now() - start, source: 'wiki' };
    // Directories to search (active content only)
    const searchDirs = ['', 'Sessions', 'memories', 'knowledge', 'decisions', 'architecture', 'legion', 'projects', 'conversations', 'self-knowledge', 'health', 'raw', 'logs'];
    const promptLower = prompt.toLowerCase();
    const keywords = promptLower.split(/\s+/).filter(w => w.length > 3);
    if (keywords.length === 0) return { results: [], latency: Date.now() - start, source: 'wiki' };

    const scored = [];
    for (const dir of searchDirs) {
      const dirPath = path.join(WIKI_DIR, dir);
      if (!fs.existsSync(dirPath)) continue;
      let files;
      try { files = fs.readdirSync(dirPath).filter(f => f.endsWith('.md')); } catch (e) { continue; }
      for (const file of files) {
        const filePath = path.join(dirPath, file);
        try {
          const content = fs.readFileSync(filePath, 'utf-8').slice(0, 2000);
          const matches = keywords.filter(w => content.toLowerCase().includes(w)).length;
          if (matches > 0) {
            const score = matches / keywords.length;
            // Find matching excerpt
            const lines = content.split('\n');
            let excerpt = '';
            for (const line of lines) {
              const lc = line.toLowerCase();
              if (keywords.some(w => lc.includes(w))) { excerpt = line.slice(0, 100); break; }
            }
            scored.push({
              content: excerpt || content.slice(0, 100),
              score: score * 0.3, // discount — wiki is supplementary
              source: 'wiki',
              file: dir ? `${dir}/${file}` : file,
            });
          }
        } catch (e) { /* skip unreadable */ }
      }
    }
    const top = scored.sort((a, b) => b.score - a.score).slice(0, topK);
    return { results: top, latency: Date.now() - start, source: 'wiki' };
  } catch (e) {
    return { results: [], latency: Date.now() - start, source: 'wiki', error: e.message };
  }
}

function queryGraphify(prompt, topK = 3) {
  const start = Date.now();
  const GRAPH_PATH = path.join(process.cwd(), 'graphify-out', 'graph.json');
  try {
    if (!fs.existsSync(GRAPH_PATH)) return { results: [], latency: Date.now() - start, source: 'graphify' };
    const graph = JSON.parse(fs.readFileSync(GRAPH_PATH, 'utf-8'));
    const nodes = graph.nodes || [];
    const promptLower = prompt.toLowerCase();
    const keywords = promptLower.split(/\s+/).filter(w => w.length > 2);

    const scored = [];
    for (const node of nodes) {
      const name = (node.name || node.id || node.label || '').toLowerCase();
      const file = (node.file || node.path || '').toLowerCase();
      const combined = name + ' ' + file;
      const matches = keywords.filter(w => combined.includes(w)).length;
      if (matches > 0) {
        const score = matches / keywords.length * 0.2; // discount — code structure is reference
        scored.push({
          content: `${node.name || node.id || '?'} — ${file || '?'}`,
          score,
          source: 'graphify',
          file: file || '',
        });
      }
    }
    const top = scored.sort((a, b) => b.score - a.score).slice(0, topK);
    return { results: top, latency: Date.now() - start, source: 'graphify' };
  } catch (e) {
    return { results: [], latency: Date.now() - start, source: 'graphify', error: e.message };
  }
}

function queryDreamingPatterns(prompt, topK = 3) {
  const start = Date.now();
  try {
    const cacheDir = '/tmp/hermes_dream_cache';
    if (!fs.existsSync(cacheDir)) return { results: [], latency: Date.now() - start, source: 'dreaming' };
    const files = fs.readdirSync(cacheDir).filter(f => f.endsWith('.md')).sort().reverse().slice(0, 3);
    const results = [];
    const promptLower = prompt.toLowerCase();
    for (const file of files) {
      const content = fs.readFileSync(path.join(cacheDir, file), 'utf-8').slice(0, 500);
      // Simple keyword overlap score
      const words = promptLower.split(/\s+/).filter(w => w.length > 3);
      const matches = words.filter(w => content.toLowerCase().includes(w) && !w.match(/^(session|summary|generated|briefing|active|patterns|unknown)$/)).length;
      // Discount dreaming scores — they're supplementary context, not primary
      const score = words.length > 1 ? 0.3 * (matches / words.length) : 0;
      if (score > 0.1) {
        results.push({ content: content.slice(0, 200), score, source: 'dreaming', file });
      }
    }
    return { results, latency: Date.now() - start, source: 'dreaming' };
  } catch (e) {
    return { results: [], latency: Date.now() - start, source: 'dreaming', error: e.message };
  }
}

// ── Merge and rerank ────────────────────────────────────────────────────────

function dedupAndRerank(allResults, prompt) {
  // Dedup by content fingerprint
  const seen = new Map();
  for (const r of allResults) {
    const content = r.content || '';
    if (!content) continue;
    const fp = fingerprintContent(content);
    if (!seen.has(fp) || r.score > seen.get(fp).score) {
      seen.set(fp, r);
    }
  }

  // Sort by score descending
  return Array.from(seen.values()).sort((a, b) => b.score - a.score).slice(0, 5);
}

// ── Metrics logging ─────────────────────────────────────────────────────────

function logMetrics(entry) {
  try {
    if (!fs.existsSync(METRICS_DIR)) fs.mkdirSync(METRICS_DIR, { recursive: true });
    let lines = [];
    if (fs.existsSync(METRICS_PATH)) {
      lines = fs.readFileSync(METRICS_PATH, 'utf-8').trim().split('\n').filter(Boolean);
    }
    lines.push(JSON.stringify(entry));
    // Prune to max lines
    if (lines.length > MAX_METRICS_LINES) lines = lines.slice(lines.length - MAX_METRICS_LINES);
    fs.writeFileSync(METRICS_PATH, lines.join('\n') + '\n', 'utf-8');
  } catch (e) { /* non-critical */ }
}

// ── Main recall function ────────────────────────────────────────────────────

function recall(prompt) {
  if (!prompt || prompt.length < 3) return [];

  // Check cache
  const cached = getCached(prompt);
  if (cached) return cached;

  // Query all layers
  const graphResult = queryIntelligence(prompt);
  const chromaResult = queryChroma(prompt);
  const wikiResult = queryWiki(prompt);
  const graphifyResult = queryGraphify(prompt);
  const dreamingResult = queryDreamingPatterns(prompt);

  // Merge all results
  const allResults = [
    ...graphResult.results,
    ...chromaResult.results,
    ...wikiResult.results,
    ...graphifyResult.results,
    ...dreamingResult.results,
  ];

  // Dedup and rerank
  const top = dedupAndRerank(allResults, prompt);

  // Log metrics
  logMetrics({
    ts: Date.now(),
    prompt: prompt.slice(0, 100),
    results: top.length,
    layers: {
      graph: { count: graphResult.results.length, latency: graphResult.latency },
      chroma: { count: chromaResult.results.length, latency: chromaResult.latency },
      wiki: { count: wikiResult.results.length, latency: wikiResult.latency },
      graphify: { count: graphifyResult.results.length, latency: graphifyResult.latency },
      dreaming: { count: dreamingResult.results.length, latency: dreamingResult.latency },
    },
    dedupedFrom: allResults.length,
  });

  // Cache
  setCache(prompt, top);

  return top;
}

// ── Status dashboard ────────────────────────────────────────────────────────

function status() {
  // Read metrics
  let totalQueries = 0;
  let avgLatency = 0;
  let layerStats = { graph: 0, chroma: 0, dreaming: 0 };
  let cacheHits = 0;

  try {
    if (fs.existsSync(METRICS_PATH)) {
      const lines = fs.readFileSync(METRICS_PATH, 'utf-8').trim().split('\n').filter(Boolean);
      totalQueries = lines.length;
      for (const line of lines.slice(-100)) {  // last 100 queries for averages
        try {
          const m = JSON.parse(line);
          if (m.layers) {
            if (m.layers.graph) layerStats.graph += m.layers.graph.latency;
            if (m.layers.chroma) layerStats.chroma += m.layers.chroma.latency;
            if (m.layers.dreaming) layerStats.dreaming += m.layers.dreaming.latency;
          }
        } catch (e) { /* skip */ }
      }
      const sample = Math.min(lines.length, 100);
      if (sample > 0) {
        for (const key of Object.keys(layerStats)) {
          layerStats[key] = Math.round(layerStats[key] / sample);
        }
      }
    }
  } catch (e) { /* no metrics yet */ }

  // Count store entries
  let storeEntries = 0;
  try {
    const store = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'auto-memory-store.json'), 'utf-8'));
    storeEntries = Array.isArray(store) ? store.length : (store.entries ? store.entries.length : 0);
  } catch (e) { /* no store */ }

  // Count stale entries (>7d no access)
  let stale = 0;
  try {
    const graph = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'graph-state.json'), 'utf-8'));
    if (graph && graph.nodes) {
      const now = Date.now();
      for (const id of Object.keys(graph.nodes)) {
        const node = graph.nodes[id];
        if (node.accessCount === 0 && node.createdAt && (now - node.createdAt) > 7 * 86400000) {
          stale++;
        }
      }
    }
  } catch (e) { /* no graph */ }

  return {
    queriesLogged: totalQueries,
    avgLayerLatencyMs: layerStats,
    storeEntries,
    staleEntries: stale,
    cacheActive: !!_cache,
    cacheAge: _cache ? Math.round((Date.now() - _cacheTime) / 1000) + 's' : 'none',
  };
}

// ── CLI ─────────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
if (args[0] === 'query' && args[1]) {
  const results = recall(args[1]);
  console.log(JSON.stringify(results, null, 2));
} else if (args[0] === 'status') {
  console.log(JSON.stringify(status(), null, 2));
} else if (args.length > 0) {
  console.log('Usage: unified-recall.cjs query "<prompt>" | status');
}

module.exports = { recall, status };
