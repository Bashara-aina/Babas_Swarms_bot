const express = require('express');
const https = require('https');

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
  const { task, agents, model } = req.body || {};
  if (!task || typeof task !== 'string') {
    return res.json({ success: false, error: 'task is required' });
  }
  try {
    const result = await callOpenRouter(task, agents, model);
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
