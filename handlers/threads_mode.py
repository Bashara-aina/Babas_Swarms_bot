"""Threads campaign mode toggle and prompt bridge."""

from __future__ import annotations

import html
import logging
from collections.abc import Awaitable, Callable

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import is_allowed
from tools.threads_mode_control import (
    is_enabled,
    open_workspace,
    set_enabled,
    toggle,
)
from tools.viral_thread_playbook import (
    PricingRule,
    build_viral_thread_context,
)

logger = logging.getLogger(__name__)
router = Router()

async def is_threads_mode_enabled() -> bool:
    """Return whether Threads campaign mode is active."""
    return await is_enabled()


async def set_threads_mode_enabled(enabled: bool) -> None:
    """Persist Threads campaign mode."""
    await set_enabled(enabled)


def build_threads_campaign_task(user_prompt: str, autopost: bool = False) -> str:
    """Build an operator-grade task for the computer agent loop.

    Injects the viral thread playbook as mandatory context so ALL Threads
    content follows the rumahlabuh.com viral playbook.
    """
    prompt = user_prompt.strip()
    playbook_context = build_viral_thread_context()

    return (
        "THREADS CAMPAIGN MODE (RUMAHLABUH)\n"
        "Objective: Execute the user's Threads content request end-to-end. "
        "Buat content yang garing-garing bisa lucu, relatable, dan definitely share-worthy.\n\n"
        f"User brief:\n{prompt}\n\n"
        f"{playbook_context}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "EXECUTION FLOW — IKUTI URUTAN INI:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "STEP 1A — RESEARCH RUMAHLABUH (WAJIB)\n"
        "Browse rumahlabuh.com duluan sebelum nulis apa-apa.\n"
        "Gunakan web_browse tool untuk https://rumahlabuh.com\n"
        "Kumpulkan:\n"
        "  - Nama kamar, harga, fasilitas (AC, WiFi, water heater, dll)\n"
        "  - Social proof: rating Google, jumlah ulasan, review snippets\n"
        "  - Lokasi advantage: deket kampus apa, pusat kota, dll\n"
        "  - Promo atau fakta unik yang bisa dijadiin hook\n"
        "DO NOT fabricate. Semua facts harus dari website.\n\n"
        "STEP 1B — RESEARCH VIRAL THREADS (WAJIB JIKA TOPIK BARU)\n"
        "Kalau user minta topik yang lo belum tau pattern viralnya:\n"
        "Gunakan web_search atau browse langsung ke:\n"
        "  - threads.com explore page\n"
        "  - reddit.com/r/ThreadsApp\n"
        "  - twitter.com (X) explore\n"
        "Cari post viral yang topiknya mirip. Amati:\n"
        "  - Hook apa yang dipake? (numbers, story, hot take, meme?)\n"
        "  - Format: single post atau thread series?\n"
        "  - Gaya bahasa: tone, slang, emoji usage\n"
        "  - Engagement: berapa likes/replies? Tanggal posting?\n"
        "  - Apa yang bikin orang reply + repost?\n\n"
        "Gunakan findings dari Step 1A + 1B untuk nentuin angle.\n\n"
        "STEP 2 — PILIH HOOK + STRATEGI\n"
        "Tentukan angle berdasarkan brief user + research results:\n"
        "  - Relatable pain point: situasi nyata yang bikin orang ngangguk\n"
        "  - Bold claim with numbers: spesifik biar credible\n"
        "  - Trend/meme reference: Aldi Taher, viral moment yang relate ke kost\n"
        "  - First-person story: gue/lu cerita pengalaman (paling engagement)\n"
        "  - SS promo mechanic: SS post ini ke admin → dapet diskon (verified converter)\n\n"
        "STEP 3 — DRAFT PACK\n"
        "Bikin draft dalam format Threads:\n"
        "  - Hook tweet: short, punchy, langsung stop-scrolling energy.\n"
        "    Gunakan 'gue/lu' style, bukan corporate. Spare emoji tapi sparingly.\n"
        "    NO bullet list seperti sales page. GPT-style prosing yang flow.\n"
        "  - Body tweets (kalau thread): story-driven, facts embedded naturally.\n"
        "  - Closing: natural CTA, jangan desperate. Link rumahlabuh.com sebagai penutup natural.\n"
        "  - Social proof: selipkan '4.8 ⭐ dari 93 ulasan Google Maps' atau similar.\n"
        "  - HARGANYA: jangan ngarang. Ambil dari hasil browsing Step 1.\n\n"
        "STEP 4 — AMAN MEGAH\n"
        "Sebelum publish, cek:\n"
        "  - SARA clean? (zero tolerance)\n"
        "  - Em dash '—' ada? Replace jadi '–' atau hapus\n"
        "  - Kanji/Hiragana/Katakana/Cyrillic ada? GANTI ke Latin semua — Indonesia pakai huruf Latin\n"
        "  - Harga sudah dari rumahlabuh.com? (NO fabrication)\n"
        "  - Terlalu sales-page vibe? Kalau iya, replace bullet points jadi prose\n"
        "  - Hook sudah kuat atau masih lemah?\n\n"
        f"{'STEP 5 — PUBLISH' if autopost else 'STEP 5 — PREVIEW + KONFIRMASI'}\n"
        + ("Publish the thread and report the live URL.\n" if autopost else
        "TUNGGU USER CONFIRM SEBELUM KLIK POST.\n"
        "Kirim draft lengkap ke user. Tanyain: 'Mau langsung post atau mau revisi dulu?'\n"
        "Baru klik Post kalau user udah approve.\n\n")
        + "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "PSIKOLOGI ENGAGEMENT (bonus tactics):\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        '1. First-person storytelling OUTPERFORMS opinion posts.\n'
        "   Bad: 'Unpopular opinion: hotel itu mahal'\n"
        "   Good: gue lagi di Solo, butuh kost 3 malam. Jujur ga masuk akal...\n"
        '2. SS-to-admin discount mechanic WORKS — klasik tapi terbukti:\n'
        "   SS post ini ke wa.me/xxx → dapet diskon 10%\n"
        '3. Meme/trend reference (Aldi Taher, dll) naikin share organic:\n'
        "   Semua kost milik Allah — Aldi Taher (numpang hype viral moment)\n"
        '4. Social proof dari Google Maps lebih credible daripada klaim sendiri:\n'
        "   4.8 bintang dari 93 ulasan Google Maps lebih credible\n"
        "5. Jangan menyerang identitas orang (hotel=scam = hostile).\n"
        "   Bikin perbandingan yang factual, jangan menghakimi.\n"
        "6. Jangan akhiri dengan pertanyaan lemek (atau gue yang salah?).\n"
        "   Akhiri dengan pernyataan percaya diri.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "HARGA RULE (WAJIB):\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(f"{r}" for r in [PricingRule.LEVEL_GENERAL, PricingRule.LEVEL_ROOM, PricingRule.LEVEL_BOOKING])
        + "\n"
        + f"{PricingRule.MANDATORY_LINK}\n"
        + "\n"
        "NEVER fabricate price. Kalau user minta harga spesifik tapi belum pilih kamar,\n"
        "guide mereka: 'Pilih kamar dulu, gue bisa kasih harga exact dari website.'\n"
        "Never claim 'Rp X' tanpa sumber dari rumahlabuh.com.\n"
    )


async def handle_threads_mode_prompt(
    msg: Message,
    task: str,
    run_agent_loop_fn: Callable[[Message, str], Awaitable[None]],
    autopost: bool = False,
) -> bool:
    """Route plain text into computer agent when Threads mode is enabled."""
    if not task or task.startswith("/"):
        return False
    enriched_task = build_threads_campaign_task(task, autopost=autopost)
    await run_agent_loop_fn(msg, enriched_task)
    return True


@router.message(Command("threads_mode"))
async def cmd_threads_mode(msg: Message) -> None:
    """Toggle Threads campaign mode on/off/status."""
    if not is_allowed(msg):
        return

    raw = (msg.text or "").removeprefix("/threads_mode").strip().lower()
    if not raw:
        enabled = await is_threads_mode_enabled()
        state = "ON" if enabled else "OFF"
        await msg.answer(
            "<b>Threads campaign mode</b>: "
            f"<code>{state}</code>\n\n"
            "Usage: <code>/threads_mode on|off|toggle|status</code>",
            parse_mode="HTML",
        )
        return

    if raw == "status":
        enabled = await is_threads_mode_enabled()
        state = "ON" if enabled else "OFF"
        await msg.answer(f"Threads campaign mode: <b>{state}</b>", parse_mode="HTML")
        return

    if raw == "toggle":
        target = await toggle()
    elif raw == "on":
        target = True
    elif raw == "off":
        target = False
    else:
        await msg.answer(
            "usage: <code>/threads_mode on|off|toggle|status</code>",
            parse_mode="HTML",
        )
        return

    if raw in {"on", "off"}:
        await set_threads_mode_enabled(target)
    if not target:
        await msg.answer("🧵 Threads campaign mode OFF. Routing kembali normal.")
        return

    open_result = ""
    try:
        open_result = await open_workspace()
    except Exception as exc:
        logger.warning("Failed to open Threads workspace: %s", exc)
        open_result = f"failed to open browser: {exc}"

    await msg.answer(
        "<b>🧵 Threads campaign mode ON</b>\n"
        "Chrome workspace dibuka. Sekarang kirim prompt biasa (tanpa slash) untuk workflow Threads.\n\n"
        "Mode lain tetap bisa dipakai via slash command seperti biasa.\n"
        f"<i>{html.escape(open_result)[:300]}</i>",
        parse_mode="HTML",
    )
