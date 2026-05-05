# MiroFish — Market Intelligence & Financial Simulation

Owns the financial market analysis pipeline: news ingestion, sentiment scoring,
price signal generation, OASIS social simulation, and Telegram market briefings.
This tentacle wraps the MiroFish submodule (tools/mirofish/) through the bridge
at tools/market_intel.py.

## What this area owns
- tools/market_intel.py — the Legion bridge (primary file to edit)
- tools/mirofish/ — git submodule (READ ONLY — never modify files inside)
- tools/mirofish/backend/ — FastAPI server, venv at .venv-mirofish
- scripts/start_mirofish.sh — server lifecycle manager
- scripts/test_mirofish_integration.py — integration test suite

## Architecture
```
Telegram /market /signal /simulate
     ↓
tools/market_intel.py
     ├── _fetch_prices()      → yfinance (IDX .JK tickers, ^GSPC, GC=F, BTC-USD)
     ├── _fetch_news()        → DDGS (Bahasa Indonesia + English)
     ├── _score_sentiment()   → keyword scorer (fast, pre-filter)
     ├── _generate_signals()  → BUY / ACCUMULATE / HOLD / WATCH / AVOID
     └── _call_mirofish_api() → MiroFish REST API (localhost:8001)
                                 fallback: direct import from services/
```

## Monitored tickers
IDX: BBCA.JK, BBRI.JK, TLKM.JK, ASII.JK, BMRI.JK, GOTO.JK, BREN.JK, PANI.JK
US: ^GSPC, ^NDX, ^DJI
Commodities: GC=F (Gold), SI=F (Silver), CL=F (Oil)
Crypto: BTC-USD, ETH-USD
Forex: USDIDR=X, USDJPY=X

## Scheduled jobs (APScheduler, Asia/Jakarta)
- 06:30 WIB — morning pre-IDX brief (all tickers, standard mode)
- 16:30 WIB — post-IDX close brief (IDX tickers only)

## Constraints
- MiroFish venv isolated: tools/mirofish/backend/.venv-mirofish
- Never import MiroFish into the main Legion Python process directly
- yfinance rate limit: ~2000 req/day free — cache for 5 min
- IDX hours: 09:00–15:30 WIB Mon–Fri — no heavy simulation during hours
- All Telegram output must be under 4096 chars (truncate if needed)
- tools/mirofish/ is a READ-ONLY submodule

## Required env vars
- ZEP_API_KEY — Zep knowledge graph (getzep.com or self-hosted)
- NEWSAPI_KEY — optional, richer news (newsapi.org free tier)
- ALPHA_VANTAGE_KEY — optional, fundamentals (alphavantage.co)
- MIROFISH_API_URL — defaults to http://localhost:8001

<!-- octogent:suggested-skills:start -->
<!-- octogent:suggested-skills:end -->