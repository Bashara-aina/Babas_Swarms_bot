/**
 * Legion WhatsApp Sidecar — bridges whatsapp-web.js to the Python bot via HTTP.
 *
 * Endpoints:
 *   GET  /health           → {status: "ok"|"initialising"|"qr_pending"}
 *   GET  /qr               → PNG QR code image (for first-time auth)
 *   GET  /messages?limit=N → [{from, name, body, timestamp, chatId}]
 *   POST /send             → {chatId, body} → {ok: true}
 *
 * Rate limit: 1 outgoing message / 10s (reduces ban risk).
 * Session persisted to .wwebjs_auth/ (survives restarts without re-scan).
 *
 * Start: node index.js
 * Default port: 3002 (override with WA_SIDECAR_PORT env var)
 */

const { Client, LocalAuth } = require("whatsapp-web.js");
const express = require("express");
const qrcode = require("qrcode");
const path = require("path");

const PORT = parseInt(process.env.WA_SIDECAR_PORT || "3002", 10);
const app = express();
app.use(express.json());

// ── State ─────────────────────────────────────────────────────────────────────
let status = "initialising";   // initialising | qr_pending | ready | disconnected
let qrDataUrl = null;           // PNG data URL for QR code
const messages = [];            // Ring buffer: last 100 unread messages
const MAX_MESSAGES = 100;
let lastSentAt = 0;             // Epoch ms — for rate limiting
const SEND_COOLDOWN_MS = 10000; // 10 seconds between outgoing messages

// ── WhatsApp client ───────────────────────────────────────────────────────────
const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: path.join(__dirname, ".wwebjs_auth"),
    }),
    puppeteer: {
        headless: true,
        args: [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
    },
});

client.on("qr", async (qr) => {
    status = "qr_pending";
    try {
        qrDataUrl = await qrcode.toDataURL(qr);
        console.log("[WA Sidecar] QR code ready — scan via /qr");
    } catch (err) {
        console.error("[WA Sidecar] QR generation error:", err.message);
    }
});

client.on("ready", () => {
    status = "ready";
    qrDataUrl = null;
    console.log("[WA Sidecar] WhatsApp client ready");
});

client.on("disconnected", (reason) => {
    status = "disconnected";
    console.warn("[WA Sidecar] Disconnected:", reason);
});

client.on("message", async (msg) => {
    if (msg.fromMe) return;
    try {
        const contact = await msg.getContact();
        const entry = {
            from: msg.from,
            name: contact.pushname || contact.name || msg.from,
            body: msg.body,
            timestamp: msg.timestamp,
            chatId: msg.from,
            isGroup: msg.isGroupMsg || false,
        };
        messages.unshift(entry);
        if (messages.length > MAX_MESSAGES) messages.pop();
    } catch (err) {
        console.error("[WA Sidecar] message handler error:", err.message);
    }
});

client.initialize().catch((err) => {
    console.error("[WA Sidecar] Client init failed:", err.message);
    status = "disconnected";
});

// ── HTTP API ──────────────────────────────────────────────────────────────────
app.get("/health", (_req, res) => {
    res.json({ status, message_count: messages.length });
});

app.get("/qr", async (_req, res) => {
    if (status === "ready") {
        return res.status(200).json({ status: "ready", message: "Already authenticated" });
    }
    if (!qrDataUrl) {
        return res.status(202).json({ status, message: "QR not yet generated — try again in 5s" });
    }
    // Return PNG image
    const base64 = qrDataUrl.replace(/^data:image\/png;base64,/, "");
    const img = Buffer.from(base64, "base64");
    res.set("Content-Type", "image/png");
    res.send(img);
});

app.get("/messages", (req, res) => {
    const limit = Math.min(parseInt(req.query.limit || "20", 10), 100);
    res.json(messages.slice(0, limit));
});

app.post("/send", async (req, res) => {
    if (status !== "ready") {
        return res.status(503).json({ ok: false, error: `Client not ready (status: ${status})` });
    }

    const { chatId, body } = req.body || {};
    if (!chatId || !body) {
        return res.status(400).json({ ok: false, error: "chatId and body are required" });
    }

    // Rate limit
    const now = Date.now();
    const wait = SEND_COOLDOWN_MS - (now - lastSentAt);
    if (wait > 0) {
        return res.status(429).json({ ok: false, error: `Rate limited — wait ${Math.ceil(wait / 1000)}s` });
    }

    try {
        await client.sendMessage(chatId, body);
        lastSentAt = Date.now();
        res.json({ ok: true });
    } catch (err) {
        res.status(500).json({ ok: false, error: err.message });
    }
});

app.listen(PORT, "127.0.0.1", () => {
    console.log(`[WA Sidecar] Listening on http://127.0.0.1:${PORT}`);
});
