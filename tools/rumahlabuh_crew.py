"""
Rumahlabuh.com Business Management Crew — CrewAI powered.

A dedicated AI crew running 24/7 in the background to manage
Bashara's homestay booking business:

  BookingMonitorAgent   — watches new bookings, flags anomalies
  GuestReplyAgent       — drafts replies to guest inquiries
  BusinessIntelAgent    — weekly revenue/occupancy analytics
  UptimeAgent           — monitors rumahlabuh.com website health

Usage:
  crew = get_rumahlabuh_crew()
  result = await crew.run_task("check new bookings today")

Setup:
  pip install crewai
  Requires SUPABASE_URL + SUPABASE_KEY in .env
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ── Optional CrewAI import ────────────────────────────────────────────────────
try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool

    _CREWAI_AVAILABLE = True
except ImportError:
    try:
        from crewai import Agent, Task, Crew, Process  # type: ignore

        _CREWAI_AVAILABLE = True
    except ImportError:
        _CREWAI_AVAILABLE = False
        logger.warning("CrewAI not installed. Run: pip install crewai")

_crew_instance: Any | None = None


# ── Supabase query helper (uses existing tools/supabase_client.py) ────────────


async def _query_supabase(query_description: str) -> str:
    """Delegate Supabase queries to the existing supabase_client tool."""
    try:
        from tools.supabase_client import query_table, get_client

        client = get_client()
        if not client:
            return "Supabase client not available — check SUPABASE_URL and SUPABASE_KEY"
        # Interpret common query patterns
        desc_lower = query_description.lower()
        if "booking" in desc_lower and "today" in desc_lower:
            import datetime

            today = datetime.date.today().isoformat()
            result = client.table("bookings").select("*").gte("created_at", today).execute()
            return str(result.data[:20]) if result.data else "No bookings today"
        elif "booking" in desc_lower and "recent" in desc_lower:
            result = client.table("bookings").select("*").order("created_at", desc=True).limit(10).execute()
            return str(result.data) if result.data else "No recent bookings"
        elif "revenue" in desc_lower or "pendapatan" in desc_lower:
            result = client.table("bookings").select("total_price, status, created_at").limit(50).execute()
            if result.data:
                total = sum(float(r.get("total_price", 0) or 0) for r in result.data if r.get("status") == "confirmed")
                return f"Confirmed revenue (last 50 bookings): Rp {total:,.0f}"
            return "No revenue data found"
        elif "guest" in desc_lower or "tamu" in desc_lower:
            result = client.table("bookings").select("guest_name, guest_email, guest_phone, status").limit(10).execute()
            return str(result.data) if result.data else "No guest data"
        else:
            # Generic: list all tables or count bookings
            result = client.table("bookings").select("id, status, created_at").limit(5).execute()
            return str(result.data) if result.data else "Query executed — no results"
    except Exception as e:
        return f"Supabase query error: {e}"


async def check_website_uptime(url: str = "https://rumahlabuh.com") -> dict[str, Any]:
    """Check if rumahlabuh.com is up and responding."""
    import time

    from tools.rumahlabuh_http import get_resilient_session

    try:
        start = time.time()
        async with get_resilient_session() as session:
            async with session.get(url) as resp:
                elapsed = round((time.time() - start) * 1000, 1)
                return {
                    "url": url,
                    "status": resp.status,
                    "ok": resp.status < 400,
                    "latency_ms": elapsed,
                    "message": f"✅ Up ({resp.status}) in {elapsed}ms"
                    if resp.status < 400
                    else f"⚠️ Status {resp.status} in {elapsed}ms",
                }
    except asyncio.TimeoutError:
        return {"url": url, "ok": False, "message": "⛔ Timeout (>10s) — site may be down"}
    except Exception as e:
        return {"url": url, "ok": False, "message": f"⛔ Error: {e}"}


async def draft_guest_reply(guest_message: str, guest_name: str = "Guest") -> str:
    """
    Draft a professional reply to a guest inquiry for rumahlabuh.com.
    Returns a draft message in Indonesian (primary) with English option.
    """
    try:
        from tools.mem0_client import mem0_search

        # Search for any past context about this guest or similar inquiries
        memories = await mem0_search(
            user_id="bashara", query=f"rumahlabuh guest {guest_name} {guest_message[:50]}", limit=3
        )
        memory_context = ""
        if memories:
            memory_context = "\n".join(m.get("memory", "") for m in memories[:2])
    except Exception:
        memory_context = ""

    # Build a prompt for the draft
    prompt = f"""You are a professional but friendly homestay manager at Rumahlabuh (rumahlabuh.com), a homestay in Indonesia.
Draft a warm, helpful reply to this guest message:

Guest name: {guest_name}
Guest message: {guest_message}

{f"Relevant context: {memory_context}" if memory_context else ""}

Requirements:
- Reply in Indonesian (primary language for Indonesian market)
- Warm but professional tone
- Address their specific question or concern
- Include a call to action (book now / contact us / visit website)
- Keep it concise (under 150 words)
- End with: "Salam, Tim Rumahlabuh"

Draft:"""

    try:
        import litellm
        import asyncio

        response = await asyncio.to_thread(
            litellm.completion,
            model=os.getenv("DEFAULT_MODEL", "groq/llama-3.3-70b-versatile"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("draft_guest_reply LLM call failed: %s", e)
        return (
            f"Halo {guest_name},\n\nTerima kasih sudah menghubungi Rumahlabuh! "
            f"Kami akan segera membalas pertanyaan Anda.\n\nSalam, Tim Rumahlabuh"
        )


async def check_booking_alerts() -> list[str]:
    """
    Check Supabase for new bookings since last check, failed payments,
    and overbooking anomalies. Returns a list of alert strings.
    """
    alerts: list[str] = []
    try:
        from tools.supabase_client import get_client
        import datetime

        client = get_client()
        if not client:
            return ["⚠️ Supabase client not available"]

        now = datetime.datetime.now(datetime.timezone.utc)
        thirty_min_ago = (now - datetime.timedelta(minutes=30)).isoformat()

        # New bookings since last check (last 30 min)
        try:
            new_bookings = client.table("bookings").select("*").gte("created_at", thirty_min_ago).execute()
            if new_bookings.data:
                count = len(new_bookings.data)
                alerts.append(
                    f"🏠 <b>New Booking(s)</b>: {count} new booking(s) in the last 30 min — check inbox for details."
                )
                # First booking details
                first = new_bookings.data[0]
                guest = first.get("guest_name", "Unknown guest")
                checkin = first.get("check_in_date", "?")
                alerts.append(f"   Latest: {guest} | Check-in: {checkin}")
        except Exception as e:
            logger.debug("[Rumahlabuh] new booking check failed: %s", e)

        # Failed payments
        try:
            failed = (
                client.table("bookings")
                .select("id, guest_name, total_price")
                .eq("payment_status", "failed")
                .gte("created_at", thirty_min_ago)
                .execute()
            )
            if failed.data:
                alerts.append(
                    f"⚠️ <b>Failed Payment(s)</b>: {len(failed.data)} booking(s) with failed payment — review immediately."
                )
        except Exception:
            pass  # payment_status column may not exist

        # Overbookings — same room double-booked for overlapping dates
        try:
            confirmed = (
                client.table("bookings")
                .select("id, room_id, check_in_date, check_out_date, guest_name")
                .eq("status", "confirmed")
                .execute()
            )
            if confirmed.data and len(confirmed.data) > 1:
                by_room: dict[str, list[dict]] = {}
                for b in confirmed.data:
                    rid = b.get("room_id") or "unknown"
                    by_room.setdefault(rid, []).append(b)
                for room_id, bookings in by_room.items():
                    if len(bookings) < 2:
                        continue
                    # Simple overlap check
                    for i in range(len(bookings)):
                        for j in range(i + 1, len(bookings)):
                            ci_i = bookings[i].get("check_in_date", "")
                            co_i = bookings[i].get("check_out_date", "")
                            ci_j = bookings[j].get("check_in_date", "")
                            co_j = bookings[j].get("check_out_date", "")
                            if ci_i and co_i and ci_j and co_j:
                                # rough overlap: one starts before the other ends
                                if ci_i <= co_j and ci_j <= co_i:
                                    alerts.append(
                                        f"🚨 <b>Overbooking Detected</b> — Room {room_id} "
                                        f"has overlapping confirmed bookings: "
                                        f"{bookings[i].get('guest_name')} ({ci_i}–{co_i}) and "
                                        f"{bookings[j].get('guest_name')} ({ci_j}–{co_j})"
                                    )
        except Exception as e:
            logger.debug("[Rumahlabuh] overbooking check failed: %s", e)

    except Exception as e:
        logger.warning("[Rumahlabuh] check_booking_alerts failed: %s", e)
        alerts.append(f"⚠️ Booking alert check failed: {e}")

    return alerts


async def get_business_summary() -> str:
    """Generate a business summary for Bashara — bookings, revenue, uptime."""
    results: list[str] = ["📊 **Rumahlabuh Business Summary**\n"]

    # Uptime check
    uptime = await check_website_uptime()
    results.append(f"🌐 Website: {uptime.get('message', 'unknown')}")

    # Recent bookings
    bookings = await _query_supabase("recent bookings")
    results.append(f"📅 Recent bookings: {bookings[:200]}")

    # Revenue
    revenue = await _query_supabase("revenue")
    results.append(f"💰 Revenue: {revenue}")

    return "\n".join(results)


# ── CrewAI Crew (optional — requires crewai installed) ────────────────────────


def build_rumahlabuh_crew() -> Any | None:
    """Build the CrewAI crew for Rumahlabuh business management."""
    if not _CREWAI_AVAILABLE:
        logger.warning("CrewAI not available — using direct async functions instead")
        return None

    try:
        llm_model = os.getenv("CREWAI_MODEL", "groq/llama-3.3-70b-versatile")

        booking_agent = Agent(
            role="Booking Monitor",
            goal="Monitor rumahlabuh.com bookings, detect anomalies, and alert Bashara to important events",
            backstory=(
                "You are the watchful eye on Rumahlabuh's booking system. "
                "You know the Supabase database schema and can detect when something is wrong: "
                "duplicate bookings, payment failures, overbookings, or suspicious patterns."
            ),
            llm=llm_model,
            verbose=False,
            allow_delegation=False,
        )

        guest_agent = Agent(
            role="Guest Relations Manager",
            goal="Draft professional, warm replies to guest inquiries in Indonesian and English",
            backstory=(
                "You are the friendly face of Rumahlabuh. You understand Indonesian hospitality culture, "
                "know the property well, and always make guests feel welcome while maintaining professionalism."
            ),
            llm=llm_model,
            verbose=False,
            allow_delegation=False,
        )

        intel_agent = Agent(
            role="Business Intelligence Analyst",
            goal="Analyze booking trends, revenue, occupancy rates and provide weekly business insights",
            backstory=(
                "You are Bashara's data analyst for Rumahlabuh. You turn raw Supabase data into "
                "actionable insights: which months are busiest, what's the average booking value, "
                "where guests come from, and what's driving or hurting revenue."
            ),
            llm=llm_model,
            verbose=False,
            allow_delegation=False,
        )

        crew = Crew(
            agents=[booking_agent, guest_agent, intel_agent],
            process=Process.sequential,
            verbose=False,
        )

        logger.info("✅ Rumahlabuh CrewAI crew built (3 agents)")
        return crew
    except Exception as e:
        logger.warning("Failed to build Rumahlabuh crew: %s", e)
        return None


def get_rumahlabuh_crew() -> Any | None:
    global _crew_instance
    if _crew_instance is None:
        _crew_instance = build_rumahlabuh_crew()
    return _crew_instance


async def run_crew_task(task_description: str) -> str:
    """
    Run a task through the Rumahlabuh crew.
    Falls back to direct async functions if CrewAI is not available.
    """
    # Direct dispatch for known task types (faster, no CrewAI overhead)
    task_lower = task_description.lower()

    if any(w in task_lower for w in ["uptime", "website", "down", "up?"]):
        result = await check_website_uptime()
        return result.get("message", str(result))

    if any(w in task_lower for w in ["summary", "ringkasan", "business", "bisnis"]):
        return await get_business_summary()

    if any(w in task_lower for w in ["booking", "reservasi", "pemesanan"]):
        return await _query_supabase(task_description)

    if any(w in task_lower for w in ["revenue", "pendapatan", "uang", "money"]):
        return await _query_supabase("revenue")

    if any(w in task_lower for w in ["reply", "draft", "balas", "guest", "tamu"]):
        return await draft_guest_reply(task_description)

    # Fallback: use CrewAI if available
    crew = get_rumahlabuh_crew()
    if crew and _CREWAI_AVAILABLE:
        try:
            from crewai import Task

            task = Task(
                description=task_description,
                expected_output="A clear, actionable response to the business request",
                agent=crew.agents[0],
            )
            result = await asyncio.to_thread(crew.kickoff, inputs={"task": task_description})
            return str(result)
        except Exception as e:
            logger.warning("CrewAI task execution failed: %s", e)

    # Final fallback: direct Supabase query
    return await _query_supabase(task_description)
