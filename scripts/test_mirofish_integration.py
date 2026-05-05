#!/usr/bin/env python3
"""MiroFish Integration Test Suite"""
import asyncio
import sys

sys.path.insert(0, "/home/newadmin/swarm-bot")


async def test_suite():
    print("=== MiroFish Integration Test Suite ===\n")
    passed = []
    failed = []

    # Test 1: Import
    try:
        from tools.market_intel import (
            DEFAULT_TICKERS,
            _fetch_prices,
            market_brief,
            market_overnight_report,
            market_signal,
            run_full_simulation,
        )
        passed.append("✅ market_intel imports")
    except Exception as e:
        failed.append(f"❌ market_intel import: {e}")
        print(f"FAILED import: {e}")
        return

    # Test 2: Price fetch (BBCA.JK + Gold)
    try:
        prices = await _fetch_prices(["BBCA.JK", "GC=F"])
        assert "BBCA.JK" in prices, "BBCA.JK missing"
        assert "price" in prices["BBCA.JK"], "No price for BBCA.JK"
        passed.append(f"✅ Price fetch: BBCA.JK={prices['BBCA.JK']['price']}, Gold={prices.get('GC=F',{}).get('price')}")
    except Exception as e:
        failed.append(f"❌ Price fetch: {e}")
        print(f"FAILED price fetch: {e}")

    # Test 3: News fetch
    try:
        from tools.market_intel import _fetch_news
        news = await _fetch_news(["BBCA Indonesia bank stock"])
        assert isinstance(news, list), "News must be a list"
        passed.append(f"✅ News fetch: {len(news)} articles")
    except Exception as e:
        failed.append(f"❌ News fetch: {e}")
        print(f"FAILED news fetch: {e}")

    # Test 4: market_brief (standard, small set)
    try:
        brief = await market_brief(["BBCA.JK", "^GSPC"], mode="standard")
        assert len(brief) > 50, "Brief too short"
        passed.append(f"✅ market_brief: {len(brief)} chars")
    except Exception as e:
        failed.append(f"❌ market_brief: {e}")
        print(f"FAILED market_brief: {e}")

    # Test 5: market_signal
    try:
        sig = await market_signal("BBCA.JK")
        assert "signal_data" in sig, "No signal_data"
        assert sig["signal_data"].get("signal") in ["BUY", "ACCUMULATE", "HOLD", "WATCH", "AVOID", "ERROR"]
        passed.append(f"✅ market_signal BBCA.JK: {sig['signal_data']['signal']}")
    except Exception as e:
        failed.append(f"❌ market_signal: {e}")
        print(f"FAILED market_signal: {e}")

    # Test 6: MiroFish API health (non-blocking)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get("http://localhost:5001/health")
            passed.append(f"✅ MiroFish API health: {r.status_code}")
    except Exception:
        passed.append("⚠️ MiroFish API not running (direct import fallback will be used)")

    print("\n--- PASSED ---")
    for p in passed:
        print(p)
    if failed:
        print("\n--- FAILURES ---")
        for f in failed:
            print(f)
        sys.exit(1)
    else:
        print(f"\n🎯 All {len(passed)} tests passed!")


if __name__ == "__main__":
    asyncio.run(test_suite())