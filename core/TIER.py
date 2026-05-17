"""
core/TIER.py
============
Memory pyramid tier constants for Legion's 5-tier memory architecture.
Maps information type → storage location + access pattern.

TIER 1 — HOT MEMORY:  /tmp/legion_*.txt  (session-scoped, auto-read at boot)
TIER 2 — WORKING:     core/memory/memory_manager.py facade (in-process)
TIER 3 — EPISODIC:    aiosqlite episodic store (30-day window)
TIER 4 — SEMANTIC:    mem0ai vector store (permanent, hermes MCP)
TIER 5 — STRUCTURAL:  .wiki/ Obsidian vault (permanent, obsidian MCP)
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

# ── TIER 1: HOT MEMORY — /tmp/ files ────────────────────────────────────────

TMP_ROOT = Path("/tmp")

# Core session files (always read at boot)
SESSION_CONTEXT = TMP_ROOT / "legion_session_context.txt"     # mem0 memories
HERMES_SKILLS  = TMP_ROOT / "legion_hermes_skills.txt"      # hermes skill list
TEMPORAL_CTX   = TMP_ROOT / "legion_temporal_context.txt"    # gitnexus recent
AVAILABLE_SKILLS = TMP_ROOT / "legion_available_skills.txt"  # skill index

# Swarm state files (written/read by agents)
PLAN_MD        = TMP_ROOT / "legion_plan.md"        # @planner → @worker
BUILD_RESULT   = TMP_ROOT / "legion_build_result.md" # @worker → @reviewer
REVIEW_MD      = TMP_ROOT / "legion_review.md"      # @reviewer output
VERIFY_MD      = TMP_ROOT / "legion_verify.md"      # @verifier output
RESEARCH_MD    = TMP_ROOT / "legion_research.md"   # @hermes-researcher

# Session lifecycle
SESSION_SUMMARY = TMP_ROOT / "legion_session_summary.txt"    # end-of-session write
PRECOMPACT     = TMP_ROOT / "legion_precompact_checkpoint.md" # pre-compaction
PENDING_SKILLS = TMP_ROOT / "legion_pending_skills.jsonl"   # hermes offline cache

HOT_MEMORY_FILES = [
    SESSION_CONTEXT,
    HERMES_SKILLS,
    TEMPORAL_CTX,
    AVAILABLE_SKILLS,
    PLAN_MD,
    BUILD_RESULT,
    REVIEW_MD,
    VERIFY_MD,
    RESEARCH_MD,
    SESSION_SUMMARY,
    PRECOMPACT,
]

# ── TIER 2: WORKING MEMORY ──────────────────────────────────────────────────

WORKING_MEMORY_FACADE = "core.memory.memory_manager"  # import path for facade
# Read/write via: from core.memory.memory_manager import SwarmBotMemoryManager
# Never access working_memory.py directly from agent code

# ── TIER 3: EPISODIC MEMORY ─────────────────────────────────────────────────

EPISODIC_DB_PATH = Path.home() / ".legion" / "episodic.db"
EPISODIC_WINDOW_DAYS = 30

# ── TIER 4: SEMANTIC MEMORY ──────────────────────────────────────────────────

MEM0_DB_PATH = Path.home() / ".legion" / "mem0_history.db"
HERMES_SKILL_NAMESPACE = "legion-skills"
HERMES_SESSION_NAMESPACE = "legion-sessions"

# ── TIER 5: STRUCTURAL MEMORY — Obsidian vault ───────────────────────────────

WIKI_ROOT = Path("/home/newadmin/swarm-bot/.wiki")

WIKI_ARCHITECTURE  = WIKI_ROOT / "architecture"
WIKI_CONCEPTS      = WIKI_ROOT / "concepts"
WIKI_DECISIONS    = WIKI_ROOT / "decisions"
WIKI_ENTITIES      = WIKI_ROOT / "entities"
WIKI_BUGS          = WIKI_ROOT / "bugs"
WIKI_RESEARCH      = WIKI_ROOT / "research"
WIKI_HEALTH        = WIKI_ROOT / "health"
WIKI_PROJECTS      = WIKI_ROOT / "projects"
WIKI_SESSIONS      = WIKI_ROOT / "sessions"

WIKI_FOLDERS = {
    "architecture": WIKI_ARCHITECTURE,
    "concepts":    WIKI_CONCEPTS,
    "decisions":   WIKI_DECISIONS,
    "entities":     WIKI_ENTITIES,
    "bugs":        WIKI_BUGS,
    "research":     WIKI_RESEARCH,
    "health":       WIKI_HEALTH,
    "projects":     WIKI_PROJECTS,
    "sessions":     WIKI_SESSIONS,
}

# ── INFORMATION TYPE → WRITE DESTINATION ──────────────────────────────────────

WRITE_ROUTING: dict[str, tuple[str, str | None]] = {
    # (information_type, destination, extra_note)
    "recurring_bug":      ("hermes + obsidian", ".wiki/bugs/"),
    "architecture_decision": ("obsidian", ".wiki/decisions/adr-[date]-[slug].md"),
    "research_synthesis":  ("hermes + obsidian", ".wiki/research/"),
    "new_module":         ("obsidian", ".wiki/architecture/"),
    "session_facts":      ("hermes", "tags: [bashara, session]"),
    "api_key_secret":     (".env ONLY", "never in wiki/memory"),
    "code_pattern":       ("hermes", "tags: [pattern, python]"),
    "test_results":       ("/tmp", "/tmp/legion_verify.md"),
    "current_plan":       ("/tmp", "/tmp/legion_plan.md"),
}


class InformationTier(StrEnum):
    HOT      = "TIER1"   # /tmp/ files
    WORKING  = "TIER2"   # in-process facade
    EPISODIC = "TIER3"   # SQLite episodic
    SEMANTIC = "TIER4"   # mem0 vector
    STRUCTURAL = "TIER5" # Obsidian vault


def tier_for(info_type: str) -> InformationTier:
    """Return the correct tier for an information type."""
    routing = WRITE_ROUTING.get(info_type)
    if routing is None:
        return InformationTier.WORKING
    dest, path = routing
    if "hermes" in dest or "mem0" in dest:
        return InformationTier.SEMANTIC
    # path (second element) contains ".wiki" for Obsidian-bound writes
    if path and ".wiki" in str(path):
        return InformationTier.STRUCTURAL
    if "/tmp" in dest:
        return InformationTier.HOT
    return InformationTier.WORKING
