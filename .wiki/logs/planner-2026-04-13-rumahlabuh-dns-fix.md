## Plan: Fix Telegram bot DNS resolution failure for rumahlabuh.com

Date: 2026-04-13
Type: BUG_FIX
Context gathered:
- DNS resolution for rumahlabuh.com works via `dig` (returns 64.29.17.65, 216.198.79.65)
- Python `socket.gethostbyname` works in current environment
- aiohttp and httpx connections to rumahlabuh.com work in current environment
- Error "Cannot connect to host rumahlabuh.com:443 ssl:default [No address associated with hostname]" is aiohttp DNS failure
- The bot likely runs in a different environment (server/VPS) with misconfigured DNS resolver
- Multiple places use aiohttp to connect: scheduler.py, rumahlabuh_crew.py, business_handler.py, proactive_engine.py, curiosity_engine.py

Risk assessment:
- If the fix uses explicit DNS servers (1.1.1.1, 8.8.8.8), it may not respect corporate VPN DNS settings
- The fix should be robust and fall back gracefully

Approach:
- Add DNS resolver configuration to all aiohttp ClientSession connections to rumahlabuh.com
- Use aiohttp's TCPConnector with family=AF_UNSPEC to handle both IPv4/IPv6
- Configure resolver with 1.1.1.1 and 8.8.8.8 as fallback DNS servers
- Focus on the three main files that ping rumahlabuh.com: scheduler.py, rumahlabuh_crew.py, business_handler.py
