"""Viral Thread Playbook — loaded into Threads campaign context.

Playbook source: .wiki/tools/threads-viral-secret-sauce.md
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

WIKI_PLAYBOOK_PATH = Path("/home/newadmin/swarm-bot/.wiki/tools/threads-viral-secret-sauce.md")
WIKI_NATURAL_GUIDE_PATH = Path("/home/newadmin/swarm-bot/.wiki/tools/threads-natural-language-guide.md")
WIKI_CONTROVERSY_HOOK_PATH = Path("/home/newadmin/swarm-bot/.wiki/tools/threads-fake-controversy-hook.md")

# Singleton cache
_cached_playbook: str | None = None
_cached_natural_guide: str | None = None
_cached_controversy_hook: str | None = None


def get_viral_playbook() -> str:
    """Return the full viral thread playbook content.

    Loaded once and cached for the lifetime of the process.
    Call invalidate_cache() if the wiki file is updated.
    """
    global _cached_playbook
    if _cached_playbook is not None:
        return _cached_playbook

    if not WIKI_PLAYBOOK_PATH.exists():
        _cached_playbook = "[PLAYBOOK NOT FOUND: .wiki/tools/threads-viral-secret-sauce.md]"
        return _cached_playbook

    raw = WIKI_PLAYBOOK_PATH.read_text(encoding="utf-8", errors="ignore")
    _cached_playbook = _strip_frontmatter(raw)
    return _cached_playbook


def get_natural_language_guide() -> str:
    """Return the full natural language guide content.

    Loaded once and cached for the lifetime of the process.
    Call invalidate_cache() if the wiki file is updated.
    """
    global _cached_natural_guide
    if _cached_natural_guide is not None:
        return _cached_natural_guide

    if not WIKI_NATURAL_GUIDE_PATH.exists():
        _cached_natural_guide = "[NATURAL LANGUAGE GUIDE NOT FOUND: .wiki/tools/threads-natural-language-guide.md]"
        return _cached_natural_guide

    raw = WIKI_NATURAL_GUIDE_PATH.read_text(encoding="utf-8", errors="ignore")
    _cached_natural_guide = _strip_frontmatter(raw)
    return _cached_natural_guide


def get_controversy_hook_guide() -> str:
    """Return the full fake controversy hook guide content.

    Loaded once and cached for the lifetime of the process.
    Call invalidate_cache() if the wiki file is updated.
    """
    global _cached_controversy_hook
    if _cached_controversy_hook is not None:
        return _cached_controversy_hook

    if not WIKI_CONTROVERSY_HOOK_PATH.exists():
        _cached_controversy_hook = "[CONTROVERSY HOOK GUIDE NOT FOUND: .wiki/tools/threads-fake-controversy-hook.md]"
        return _cached_controversy_hook

    raw = WIKI_CONTROVERSY_HOOK_PATH.read_text(encoding="utf-8", errors="ignore")
    _cached_controversy_hook = _strip_frontmatter(raw)
    return _cached_controversy_hook


def _strip_frontmatter(content: str) -> str:
    """Strip YAML frontmatter from markdown content."""
    return re.sub(r"\A---\n[\s\S]*?---\n", "", content).strip()


def invalidate_cache() -> None:
    """Clear the cached playbook, natural language guide, and controversy hook. Call after wiki updates."""
    global _cached_playbook, _cached_natural_guide, _cached_controversy_hook
    _cached_playbook = None
    _cached_natural_guide = None
    _cached_controversy_hook = None


def build_viral_thread_context() -> str:
    """Build the viral playbook context block for LLM prompts."""
    playbook = get_viral_playbook()
    natural_guide = get_natural_language_guide()
    controversy_hook = get_controversy_hook_guide()
    return (
        "## VIRAL THREAD PLAYBOOK — RUMAHLABUH.COM\n"
        "MANDATORY: Follow this playbook for ALL Threads content generation.\n\n"
        f"{playbook}\n\n"
        "## NATURAL LANGUAGE GUIDE — JANGAN DIABAIKAN\n"
        "MANDATORY: Follow this guide to make content sound HUMAN, not AI-generated.\n\n"
        f"{natural_guide}\n\n"
        "## KONTROVERSI SEMU HOOK GUIDE — GUNAKAN TEKNIK INI\n"
        "MANDATORY: Use this fake controversy hook technique to stop scrolls and drive replies.\n\n"
        f"{controversy_hook}\n"
    )


class ContentPillar:
    """Content pillars for rumahlabuh.com Threads."""

    MYTH_BUSTING: ClassVar[str] = "Myth-busting — break common assumptions about kost/property"
    MONEY_HACK: ClassVar[str] = "Money Hacks — save money without sacrificing quality"
    LOCATION_INTEL: ClassVar[str] = "Location Intel — reveal hidden gems in Solo neighborhoods"
    SURVIVAL_GUIDE: ClassVar[str] = "Survival Guide — tips for newbies navigating kost life"
    HORROR_STORIES: ClassVar[str] = "Horror Stories — common scams, red flags, bad deals"
    WIN_STORIES: ClassVar[str] = "Win Stories — success finds, good deals, happy endings"

    ALL: ClassVar[list[str]] = [
        MYTH_BUSTING,
        MONEY_HACK,
        LOCATION_INTEL,
        SURVIVAL_GUIDE,
        HORROR_STORIES,
        WIN_STORIES,
    ]

    RATIO: ClassVar[dict[str, float]] = {
        "value": 0.60,  # tips, guides, intel
        "engagement": 0.20,  # questions, polls
        "brand": 0.20,  # listings, promos
    }


class HookPattern:
    """4 hook patterns for tweet #1."""

    HOT_TAKE: ClassVar[str] = (
        "HOT_TAKE: Start with a controversial or bold opinion that makes people stop scrolling. "
        'Example: "Hot take: Kost 500rb/bulan di Solo itu MAHAL. Kost 1,5jt di Jakarta? Masih masuk akal."'
    )

    RELATABLE_PAIN: ClassVar[str] = (
        "RELATABLE_PAIN: Start with a shared frustration or pain point everyone recognizes. "
        'Example: "Gue udah 3x pindah kost. 3x semuanya karena alasan yang SAMA."'
    )

    BOLD_CLAIM: ClassVar[str] = (
        "BOLD_CLAIM: Make a specific claim with numbers that creates curiosity. "
        'Example: "98% anak kos di Solo masih kena RAJA ANGKA. Ini yang pertama kali lo denger."'
    )

    NUMBER_HOOK: ClassVar[str] = (
        "NUMBER_HOOK: Lead with a numbered list that promises specific value. "
        'Example: "3 hal yang gue baru sadar setelah ngekost 5 tahun di Solo: (no. 2 pasti lo pernah alamin)"'
    )

    ALL: ClassVar[list[str]] = [HOT_TAKE, RELATABLE_PAIN, BOLD_CLAIM, NUMBER_HOOK]


class ThreadStyle:
    """Style guardrails for Threads content."""

    # Language rules
    BAN_WORDS: ClassVar[list[str]] = [
        "SARA",  # suku, agama, ras, antargolongan
        "—",  # em dash — use "–" or remove
    ]

    ALLOWED_EMOJI: ClassVar[list[str]] = [
        "🙏", "🔥", "💯", "⚡", "❌", "🚩", "🙌", "🏠", "💰", "📊", "🌐",
    ]

    # Posting schedule
    BEST_TIMES_WIB: ClassVar[list[str]] = [
        "07:00-08:00 WIB — morning scroll",
        "12:00-13:00 WIB — lunch break",
        "20:00-21:30 WIB — evening wind-down",
    ]

    # Engagement rules
    CLOSING_CTA_PATTERNS: ClassVar[list[str]] = [
        "Lo udah pernah ngerasain?",
        "Menurut lo, mana yang lebih penting?",
        "Yang pernah ngalamin, raise your hand 🙌",
        "Setuju nggak sama statement ini?",
        "Kalau lo mau tau more,",
    ]

    # Hashtags
    PRIMARY_HASHTAGS: ClassVar[list[str]] = [
        "#Koskosan",
        "#KosSolo",
        "#Ngekost",
        "#MahasiswaBaru",
        "#RumahLabuh",
    ]

    SECONDARY_HASHTAGS: ClassVar[list[str]] = [
        "#KostImpian",
        "#TipsKost",
        "#HematKost",
        "#KostTerbaik",
        "#KostLife",
    ]

    @classmethod
    def is_safe(cls, text: str) -> tuple[bool, str]:
        """Check if text passes style guardrails. Returns (passes, reason)."""
        for word in cls.BAN_WORDS:
            if word.lower() in text.lower():
                return False, f"BANNED word found: {word}"
        return True, "ok"

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Remove banned patterns and clean up text."""
        # Remove em dash and replace with en dash
        text = text.replace("—", "–")
        # Remove multiple spaces
        text = re.sub(r"  +", " ", text)
        return text


class PricingRule:
    """Mandatory pricing accuracy rules for rumahlabuh.com Threads content.

    ALL posts that mention price MUST follow this tiered flow.
    """

    LEVEL_GENERAL: ClassVar[str] = (
        "HARGA UMUM/KISARAN — boleh mention tanpa check dates:\n"
        "  Harga kost di Solo mulai dari Rp 500rb - 2jt/bulan\n"
        "  Tergantung lokasi dan fasilitas.\n"
        "  Cukup info umum, tidak perlu konfirmasi tanggal."
    )

    LEVEL_ROOM: ClassVar[str] = (
        "HARGA KAMAR SPESIFIK — perlu pilih kamar dulu:\n"
        "  1. User pilih kamar (AC, non-AC, kamar mandi dalam/luar, dll)\n"
        "  2. Ambil screenshot/prices dari rumahlabuh.com\n"
        "  3. Sertakan: Pilih kamar yang lo mau, gue bisa kasih harga exact."
    )

    LEVEL_BOOKING: ClassVar[str] = (
        "HARGA BOOKING (dengan tanggal) — paling spesifik:\n"
        "  1. User pilih kamar\n"
        "  2. User kasih tanggal check-in DAN check-out\n"
        "  3. Hitung: (harga kamar x jumlah malam) + pajak/biaya lain\n"
        "  4. Sertakan breakdown harga, bukan hanya total\n"
        "  5. CTA: Mau langsung di-booking?"
    )

    # Website base URL for price links
    BASE_URL: ClassVar[str] = "rumahlabuh.com"

    # Mandatory phrasing when mentioning prices
    MANDATORY_LINK: ClassVar[str] = (
        "SELALU sertakan link ke rumahlabuh.com setiap kali mention harga.\n"
        "  Contoh: 'Lihat harga terbaru: rumahlabuh.com/[halaman-kamar]'"
    )

    # Never fabricate prices
    BAN_PHRASES: ClassVar[list[str]] = [
        "Rp ",  # Can't say "Rp X" without sourcing
    ]

    @classmethod
    def format_price_mention(cls, price: str, room_url: str = "") -> str:
        """Format a price mention with mandatory link."""
        link = f"\nLihat harga terbaru: {cls.BASE_URL}/{room_url}" if room_url else ""
        return f"{price}{link}"

    @classmethod
    def get_price_level(cls, has_room: bool, has_dates: bool) -> str:
        """Determine price detail level based on available info."""
        if has_room and has_dates:
            return cls.LEVEL_BOOKING
        elif has_room:
            return cls.LEVEL_ROOM
        return cls.LEVEL_GENERAL
