"""
tools/market_intel.py
MiroFish × Legion Market Intelligence Bridge
Covers: IDX, S&P 500, Gold, Crypto, any yfinance-supported ticker
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("market_intel")

MIROFISH_BACKEND = os.path.join(os.path.dirname(__file__), "mirofish", "backend")
if MIROFISH_BACKEND not in sys.path:
    sys.path.insert(0, MIROFISH_BACKEND)

MIROFISH_API = os.getenv("MIROFISH_API_URL", "http://localhost:5001")

DEFAULT_TICKERS = {
    "IDX": ["BBCA.JK", "BBRI.JK", "TLKM.JK", "ASII.JK", "BMRI.JK",
            "GOTO.JK", "BREN.JK", "PANI.JK"],
    "US":  ["^GSPC", "^NDX", "^DJI"],
    "COMMODITY": ["GC=F", "SI=F", "CL=F"],
    "CRYPTO": ["BTC-USD", "ETH-USD"],
    "FOREX": ["USDIDR=X", "USDJPY=X"],
}


@dataclass
class MarketIntelReport:
    timestamp: str
    tickers: list[str]
    price_data: dict = field(default_factory=dict)
    news_sentiment: dict = field(default_factory=dict)
    simulation_output: dict = field(default_factory=dict)
    signals: dict = field(default_factory=dict)
    narrative: str = ""
    error: str | None = None


async def _fetch_prices(tickers: list[str]) -> dict:
    """Fetch OHLCV + technicals via yfinance."""
    try:
        import yfinance as yf
        result = {}
        for t in tickers:
            try:
                ticker = yf.Ticker(t)
                hist = ticker.history(period="5d", interval="1d")
                info = ticker.fast_info
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else hist.iloc[-1]
                    result[t] = {
                        "price": round(float(latest["Close"]), 4),
                        "change_pct": round(
                            (float(latest["Close"]) - float(prev["Close"]))
                            / float(prev["Close"]) * 100, 2
                        ),
                        "volume": int(latest["Volume"]),
                        "high_5d": round(float(hist["High"].max()), 4),
                        "low_5d": round(float(hist["Low"].min()), 4),
                        "market_cap": getattr(info, "market_cap", None),
                    }
                else:
                    result[t] = {"error": "No data available"}
            except Exception as e:
                result[t] = {"error": str(e)}
        return result
    except ImportError:
        import subprocess
        venv_pip = os.path.join(MIROFISH_BACKEND, ".venv-mirofish", "bin", "pip")
        subprocess.run([venv_pip, "install", "yfinance>=0.2.54"], capture_output=True)
        return {"error": "yfinance installed, retry next call"}


async def _fetch_news(queries: list[str], max_results: int = 10) -> list[dict]:
    """Fetch news via DDGS."""
    try:
        from ddgs import DDGS
        all_news = []
        with DDGS() as ddgs:
            for query in queries[:3]:
                results = list(ddgs.news(query, max_results=max_results))
                all_news.extend(results)
        seen = set()
        deduped = []
        for item in all_news:
            url = item.get("url", "")
            if url not in seen:
                seen.add(url)
                deduped.append({
                    "title": item.get("title", ""),
                    "body": item.get("body", ""),
                    "source": item.get("source", ""),
                    "date": item.get("date", ""),
                    "url": url,
                })
        return deduped
    except Exception as e:
        logger.error(f"DDGS news fetch failed: {e}")
        return []


async def _call_mirofish_api(endpoint: str, payload: dict) -> dict:
    """
    Call MiroFish REST API on port 5001.
    Returns dict on success OR when API returns an error with success=false.
    Falls back to LLM simulation when API is unreachable or returns 4xx with no project.
    """
    try:
        import httpx
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{MIROFISH_API}{endpoint}", json=payload)
            if resp.status_code >= 500:
                resp.raise_for_status()
            resp_json = resp.json()
            if resp_json.get("success") is False:
                error_msg = resp_json.get("error", "")
                if any(key in error_msg.lower() for key in ("project", "graph", "not found", "require")):
                    return {"error": error_msg, "_fallback": True}
                return resp_json
            return resp_json
    except Exception as http_err:
        logger.warning(f"MiroFish API error ({http_err}), trying LLM fallback...")
        return {"error": str(http_err), "_fallback": True}


async def _call_mirofish_direct(endpoint: str, payload: dict) -> dict:
    """
    Directly import and call MiroFish services when server is offline.

    MiroFish classes discovered from source:
    - ReportAgent(graph_id, simulation_id, simulation_requirement,
                  llm_client=None, zep_tools=None)
      .generate_report(progress_callback=None, report_id=None) -> Report

    - SimulationRunner.start_simulation(
        simulation_id, platform="parallel", max_rounds=None,
        enable_graph_memory_update=False, graph_id=None
      ) -> SimulationRunState
    """
    try:
        import os as _os
        _os.chdir(MIROFISH_BACKEND)

        if "/report" in endpoint or "/analyze" in endpoint:
            from app.config import Config
            from app.services.report_agent import ReportAgent

            graph_id = payload.get("graph_id", f"graph_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            simulation_id = payload.get("simulation_id", f"sim_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            simulation_requirement = payload.get("requirement", payload.get("topic", "Market analysis"))

            agent = ReportAgent(
                graph_id=graph_id,
                simulation_id=simulation_id,
                simulation_requirement=simulation_requirement,
            )
            report = agent.generate_report()
            if hasattr(report, "to_dict"):
                return report.to_dict()
            return {"result": str(report)}

        if "/simulation" in endpoint or "/simulate" in endpoint:
            import uuid

            from app.services.simulation_runner import SimulationRunner

            simulation_id = payload.get("simulation_id", f"sim_{uuid.uuid4().hex[:12]}")
            result = SimulationRunner.start_simulation(
                simulation_id=simulation_id,
                platform=payload.get("platform", "parallel"),
                max_rounds=payload.get("rounds"),
                enable_graph_memory_update=payload.get("enable_graph_memory_update", False),
                graph_id=payload.get("graph_id"),
            )
            if hasattr(result, "to_dict"):
                return result.to_dict()
            if hasattr(result, "to_detail_dict"):
                return result.to_detail_dict()
            return {"result": str(result)}

        return {"error": f"No direct mapping for endpoint: {endpoint}"}
    except ImportError as e:
        return {"error": f"MiroFish import failed: {e}. Is submodule initialized?"}
    except Exception as e:
        logger.error(f"MiroFish direct call error: {e}")
        return {"error": str(e)}


def _score_sentiment(news_items: list[dict]) -> dict:
    """
    Simple keyword-based sentiment scorer for financial news.
    Returns score -1.0 (very bearish) to +1.0 (very bullish) per ticker mentioned.
    """
    BULLISH_WORDS = {
        "surge", "rally", "gain", "beat", "profit", "growth", "bullish",
        "upgrade", "outperform", "record", "strong", "positive", "breakout",
        "naik", "untung", "laba", "tumbuh",
    }
    BEARISH_WORDS = {
        "crash", "fall", "loss", "miss", "debt", "bearish", "downgrade",
        "underperform", "weak", "negative", "drop", "decline", "cut",
        "turun", "rugi", "merosot", "jatuh",
    }

    entity_scores = {}
    for item in news_items:
        text = (item.get("title", "") + " " + item.get("body", "")).lower()
        words = set(text.split())
        bull_score = len(words & BULLISH_WORDS)
        bear_score = len(words & BEARISH_WORDS)
        if bull_score + bear_score == 0:
            continue
        score = (bull_score - bear_score) / (bull_score + bear_score)
        for ticker_group in DEFAULT_TICKERS.values():
            for t in ticker_group:
                name = t.replace(".JK", "").replace("=F", "").replace("-USD", "").lower()
                if name in text or t.lower() in text:
                    if t not in entity_scores:
                        entity_scores[t] = []
                    entity_scores[t].append(score)

    return {
        t: round(sum(scores) / len(scores), 3)
        for t, scores in entity_scores.items()
        if scores
    }


def _generate_signals(prices: dict, sentiment: dict) -> dict:
    """
    Combine price momentum + sentiment score into actionable signal.
    Signal levels: BUY | ACCUMULATE | HOLD | WATCH | AVOID
    """
    signals = {}
    for ticker, pdata in prices.items():
        if "error" in pdata:
            signals[ticker] = {"signal": "ERROR", "reason": pdata["error"]}
            continue

        change = pdata.get("change_pct", 0)
        sent = sentiment.get(ticker, 0)

        if change > 2.0 and sent > 0.3:
            sig = "BUY"
        elif change > 0.5 and sent >= 0:
            sig = "ACCUMULATE"
        elif change < -3.0 and sent < -0.3:
            sig = "AVOID"
        elif change < -1.5:
            sig = "WATCH"
        else:
            sig = "HOLD"

        signals[ticker] = {
            "signal": sig,
            "price": pdata.get("price"),
            "change_pct": change,
            "sentiment_score": sent,
            "reason": f"{change:+.1f}% price, sentiment {sent:+.2f}",
        }
    return signals


async def market_brief(tickers: list[str] | None = None, mode: str = "standard") -> str:
    """
    Generate a market brief for given tickers (or default watchlist).
    mode: "standard" | "deep" (deep runs full MiroFish simulation)
    Returns: formatted string ready for Telegram delivery
    """
    if tickers is None:
        tickers = (
            DEFAULT_TICKERS["IDX"][:4] +
            DEFAULT_TICKERS["US"][:2] +
            DEFAULT_TICKERS["COMMODITY"][:1]
        )

    queries = []
    for t in tickers[:4]:
        clean = t.replace(".JK", "").replace("=F", "").replace("-USD", "")
        queries.append(f"{clean} stock news today")
    queries.append("Indonesia IDX stock market today")
    queries.append("S&P 500 market outlook")

    prices_task = asyncio.create_task(_fetch_prices(tickers))
    news_task = asyncio.create_task(_fetch_news(queries))
    prices, news = await asyncio.gather(prices_task, news_task)

    sentiment = _score_sentiment(news)
    signals = _generate_signals(prices, sentiment)

    if mode == "deep":
        topic = f"Market analysis for {', '.join(tickers[:4])}"
        sim_result = await _call_mirofish_api("/api/simulation/create", {
            "project_id": "legion_market",
            "topic": topic,
            "rounds": 10,
        })
        if sim_result.get("_fallback") or sim_result.get("error"):
            sim_result = await _llm_market_simulation(topic, 10)
    else:
        sim_result = {}

    now = datetime.now().strftime("%Y-%m-%d %H:%M WIB")
    lines = [f"📊 *Legion Market Brief* — {now}\n"]

    for ticker, sig_data in signals.items():
        emoji = {
            "BUY": "🟢", "ACCUMULATE": "🔵", "HOLD": "⚪",
            "WATCH": "🟡", "AVOID": "🔴", "ERROR": "❌"
        }.get(sig_data["signal"], "⚪")
        price_str = f"${sig_data['price']:,.4f}" if sig_data.get("price") else "N/A"
        lines.append(
            f"{emoji} *{ticker}* {price_str} "
            f"({sig_data.get('change_pct', 0):+.1f}%) — {sig_data['signal']}"
        )

    if sim_result and not sim_result.get("error"):
        lines.append("\n🧠 *MiroFish Simulation Insights:*")
        narrative = sim_result.get("narrative", sim_result.get("summary", ""))
        if narrative:
            lines.append(narrative[:500] + ("..." if len(narrative) > 500 else ""))

    lines.append(f"\n_Sources: {len(news)} news articles analyzed_")
    return "\n".join(lines)


async def market_signal(ticker: str) -> dict:
    """
    Get single-ticker deep signal. Returns structured dict.
    """
    prices = await _fetch_prices([ticker])
    queries = [
        f"{ticker.replace('.JK','')} stock news analysis",
        f"{ticker} earnings revenue outlook",
    ]
    news = await _fetch_news(queries, max_results=15)
    sentiment = _score_sentiment(news)
    signals = _generate_signals(prices, sentiment)
    return {
        "ticker": ticker,
        "signal_data": signals.get(ticker, {}),
        "price_data": prices.get(ticker, {}),
        "news_count": len(news),
        "top_headlines": [n["title"] for n in news[:5]],
        "timestamp": datetime.now().isoformat(),
    }


async def run_full_simulation(topic: str, rounds: int = 10) -> dict:
    """
    Run a full MiroFish OASIS simulation on a financial topic.
    Falls back to MiniMax LLM analysis when MiroFish server/project not configured.
    """
    payload = {
        "topic": topic,
        "rounds": rounds,
        "agent_count": 20,
        "context": {
            "market": "IDX + Global",
            "date": datetime.now().isoformat(),
        }
    }
    result = await _call_mirofish_api("/api/simulation/create", payload)
    if result.get("_fallback") or (result.get("error") and "project" in result["error"].lower()):
        result = await _llm_market_simulation(topic, rounds)
    return result


async def _llm_market_simulation(topic: str, rounds: int) -> dict:
    """
    Fallback: use MiniMax LLM directly via httpx to generate simulation-style analysis.
    Handles <thinking> tags by splitting on </think> then extracting JSON from the final part.
    """
    try:
        import re

        import httpx

        api_key = os.getenv("MINIMAX_API_KEY", "")
        base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")

        system_msg = (
            "You are a senior financial analyst running a social simulation. "
            "Generate a structured market analysis for the given topic, "
            "covering: key entities, sentiment, price projections, risk factors, "
            "and actionable signals. Output a JSON object with keys: "
            "answer (narrative string), confidence (HIGH/MEDIUM/LOW)."
        )
        user_msg = (
            f"Run a simulated market analysis on: {topic}\n\n"
            f"Consider {rounds} discussion rounds among simulated participants: "
            "bullish investors, bearish analysts, macro traders, and retail observers. "
            "Synthesize their debate into a final market narrative with signals."
        )

        async def _call() -> dict:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": os.getenv("MINIMAX_MODEL", "MiniMax-M2.7"),
                        "messages": [
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_msg},
                        ],
                        "max_tokens": 8000,
                        "temperature": 1.0,
                        "top_p": 0.95,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                raw = data["choices"][0]["message"]["content"]

                # Strip <think>...</thinking> tags — split on </think> and take the last part
                closing_tag = "</think>"
                if closing_tag in raw:
                    after_thinking = raw.split(closing_tag)[-1]
                    cleaned = after_thinking.strip()
                else:
                    cleaned = raw.strip()

                                # Strip markdown code fences first
                if cleaned.startswith("```"):
                    fence_end = cleaned.find("\n")
                    if fence_end != -1:
                        cleaned = cleaned[fence_end + 1:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3].strip()

                # Find JSON boundaries by locating the "answer" field specifically.
                # This avoids issues where the markdown/answer text contains { or }.
                answer_key = '"answer":'
                answer_pos = cleaned.find(answer_key)
                if answer_pos == -1:
                    return {"answer": cleaned[:500], "confidence": "MEDIUM"}

                # Back up to the opening {
                json_start = cleaned.rfind("{", 0, answer_pos + len(answer_key))
                if json_start == -1:
                    json_start = answer_pos

                # Find the closing "confidence": "..."} at the end
                conf_marker = '"confidence": "'
                conf_pos = cleaned.find(conf_marker, answer_pos)
                if conf_pos == -1:
                    # No confidence field — try generic parse
                    try:
                        parsed = json.loads(cleaned[json_start:])
                        return {
                            "answer": parsed.get("answer", cleaned[json_start:json_start + 500]),
                            "confidence": parsed.get("confidence", "MEDIUM"),
                        }
                    except Exception:
                        return {"answer": cleaned[json_start:json_start + 500], "confidence": "MEDIUM"}

                # confidence value: from after '"confidence": "' up to the next '"'
                conf_val_start = conf_pos + len(conf_marker)
                conf_end = cleaned.find('"', conf_val_start)
                confidence = cleaned[conf_val_start:conf_end] if conf_end != -1 else "MEDIUM"

                # answer value: from after '"answer": "' up to just before , "confidence"
                answer_val_start = answer_pos + len(answer_key) + 1
                # Skip whitespace
                while answer_val_start < len(cleaned) and cleaned[answer_val_start] in ' \t\n':
                    answer_val_start += 1
                # Skip opening quote
                if answer_val_start < len(cleaned) and cleaned[answer_val_start] == '"':
                    answer_val_start += 1
                # answer ends right before ', "confidence'
                answer_end = cleaned.rfind('", "confidence"', 0, conf_pos)
                if answer_end == -1:
                    answer_end = conf_pos - 1

                answer_text = cleaned[answer_val_start:answer_end]
                # Unescape common sequences
                answer_text = (
                    answer_text
                    .replace('\\"', '"')
                    .replace('\\n', '\n')
                    .replace('\\r', '\r')
                    .replace('\\\\', '\\')
                )
                return {
                    "answer": answer_text.strip(),
                    "confidence": confidence or "MEDIUM",
                }
                # Fallback: return cleaned text
                return {"answer": cleaned[:500], "confidence": "MEDIUM"}

        result = await asyncio.wait_for(_call(), timeout=300.0)
        return {
            "narrative": result["answer"],
            "confidence": result["confidence"],
            "source": "minimax-simulation",
            "topic": topic,
        }
    except TimeoutError:
        err_str = "LLM simulation timed out after 300s"
        logger.warning(err_str)
        return {"error": err_str}
    except Exception as e:
        err_str = str(e) or repr(e)
        if not err_str or len(err_str) < 3:
            err_str = f"LLM API error ({type(e).__name__})"
        logger.warning(f"LLM simulation failed ({type(e).__name__}): {err_str}")
        return {"error": f"Simulation unavailable: {err_str}"}


async def market_overnight_report() -> str:
    """
    Full overnight analysis: all default tickers, deep mode.
    Designed for scheduled overnight runs via Legion scheduler.
    """
    all_tickers = []
    for group in DEFAULT_TICKERS.values():
        all_tickers.extend(group)

    report = await market_brief(all_tickers, mode="deep")

    macro_sim = await run_full_simulation(
        "Global macro outlook: Fed policy, Indonesia BI rate, gold vs USD",
        rounds=15
    )
    if not macro_sim.get("error"):
        summary = macro_sim.get("narrative", macro_sim.get("summary", ""))
        if summary:
            report += f"\n\n🌍 *Macro Simulation:*\n{summary[:800]}"

    return report