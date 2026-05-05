# Todo

- [ ] Fill _call_mirofish_direct() stubs by reading report_agent.py class signatures
- [ ] Fill _call_mirofish_direct() stubs by reading simulation_runner.py class signatures
- [ ] Add 5-minute price cache using functools.lru_cache or aiosqlite
- [ ] Add IDX-specific Bahasa Indonesia news sources to _fetch_news() (Kontan, Bisnis)
- [ ] Add fundamental data layer: P/E ratio, EPS via Alpha Vantage for top IDX tickers
- [ ] Implement /watchlist command — personalized ticker list per Telegram user
- [ ] Add portfolio tracking: /portfolio BBCA:100 TLKM:200 (tracks your holdings)
- [ ] Write market_intel_test.py full integration test and add to CI
- [ ] Add Gold/IDR correlation analysis to overnight report
- [ ] Implement alert system: notify when signal changes BUY→AVOID for watched ticker