const express = require('express');
const https = require('https');

// ── Simple in-memory rate limiter (sliding window, no external deps) ──────────
const _rateLimitMap = new Map(); // key → [{ts, count}]
const RATE_LIMIT_WINDOW_MS = 60_000;  // 1 minute
const RATE_LIMIT_MAX = 30;            // max 30 requests per minute per IP

function rateLimit(ip) {
  const now = Date.now();
  const window = RATE_LIMIT_WINDOW_MS;
  const entry = _rateLimitMap.get(ip) ?? [];
  // Prune old entries
  const recent = entry.filter((e) => now - e.ts < window);
  const count = recent.reduce((s, e) => s + e.count, 0) + 1;
  if (count > RATE_LIMIT_MAX) return false;
  recent.push({ ts: now, count: 1 });
  _rateLimitMap.set(ip, recent);
  return true;
}

// ── Input validation helpers ───────────────────────────────────────────────────
const MAX_TASK_LEN = 200_000; // generous 200KB task limit
const MAX_TASK_DISPLAY = 80;  // for error messages

function sanitizeTask(task) {
  if (typeof task !== 'string') return null;
  if (task.length === 0 || task.length > MAX_TASK_LEN) return null;
  // Reject binary-looking content
  if (/[\x00-\x08\x0e-\x1f]/.test(task)) return null;
  return task;
}

function normalizeModel(model) {
  if (!model) {
    return 'openai/gpt-4o-mini';
  }
  if (model.startsWith('openrouter/')) {
    return model.slice('openrouter/'.length);
  }
  return model;
}

function callOpenRouter(task, agents, model) {
  return new Promise((resolve, reject) => {
    const apiKey = process.env.OPENROUTER_API_KEY;
    if (!apiKey) {
      reject(new Error('OPENROUTER_API_KEY not set for sidecar'));
      return;
    }

    const selectedModel = normalizeModel(model);
    const agentList = Array.isArray(agents) && agents.length > 0 ? agents.join(', ') : 'general';
    const prompt = `Task: ${task}\nAgents: ${agentList}\nReturn concise actionable output.`;
    const body = JSON.stringify({
      model: selectedModel,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.2,
    });

    const req = https.request(
      {
        hostname: 'openrouter.ai',
        port: 443,
        path: '/api/v1/chat/completions',
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
        },
      },
      (resp) => {
        let raw = '';
        resp.on('data', (chunk) => {
          raw += chunk;
        });
        resp.on('end', () => {
          if (resp.statusCode < 200 || resp.statusCode >= 300) {
            reject(new Error(`OpenRouter HTTP ${resp.statusCode}: ${raw}`));
            return;
          }
          try {
            const parsed = JSON.parse(raw);
            const content =
              parsed &&
              parsed.choices &&
              parsed.choices[0] &&
              parsed.choices[0].message &&
              parsed.choices[0].message.content;
            resolve(content || '');
          } catch (err) {
            reject(new Error(`OpenRouter parse error: ${err.message}`));
          }
        });
      }
    );

    req.on('error', (err) => reject(err));
    req.write(body);
    req.end();
  });
}

const app = express();
app.use(express.json());

app.post('/run', async (req, res) => {
  const ip = req.ip || req.socket.remoteAddress;
  if (!rateLimit(ip)) return res.json({ success: false, error: 'rate limit exceeded' });
  const { task, agents, model } = req.body || {};
  const clean = sanitizeTask(task);
  if (!clean) return res.json({ success: false, error: 'invalid task' });
  try {
    const result = await callOpenRouter(clean, agents, model);
    return res.json({ success: true, output: result });
  } catch (err) {
    return res.json({ success: false, error: err.message || String(err) });
  }
});

app.get('/health', (_req, res) => {
  res.json({ ok: true });
});

app.listen(7834, () => {
  console.log('ruflo sidecar running on :7834');
});
