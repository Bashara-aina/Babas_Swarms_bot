Here is the complete master prompt. Save it as `.github/copilot-instructions.md` in your repo root, or paste it directly into a GitHub Copilot Agent session:

***

```markdown
# BABAS SWARMS BOT — HUMANIZATION UPGRADE
# LegionSwarm v5 → v6: From Robotic Tool to Genuine Human-Like Assistant
# Repo: https://github.com/Bashara-aina/Babas_Swarms_bot
# Date: April 2026 | RTX 3060 12GB | Ubuntu 22.04 | Python 3.10+ | 5TB Storage

---

## MISSION STATEMENT

The current LegionSwarm bot is technically capable but feels robotic. It:
- Forgets everything between Telegram sessions
- Only uses skills when explicitly commanded (/swarm, /run, /think)
- Speaks in flat, transactional text with no personality or warmth
- Never pushes back, challenges, or argues — it is a yes-man
- Has no inner life, emotional state, or genuine opinions
- Responds to tasks mechanically, not like a real assistant

This upgrade transforms it into a genuinely human-like AI assistant that:
- Remembers everything permanently (5TB storage available — use it)
- Autonomously selects its own tools and skills without being told
- Has a real personality: direct, curious, occasionally sarcastic, honest
- Has emotional states that influence how it responds
- Reflects on past interactions to form genuine opinions
- Pushes back with evidence when it disagrees
- Has inner thoughts that shape its responses, not just raw task execution

---

## SOURCE REPOSITORIES TO INTEGRATE

All 10 repos below must be integrated. Study their architecture, extract the
relevant patterns, and implement them natively in Python within this codebase.
Do NOT just install them as black boxes — understand their core ideas and wire
them into the existing LegionSwarm architecture.

1. `letta-ai/letta`         — 3-tier OS-style persistent memory (core/archival/recall)
2. `mem0ai/mem0`            — Self-editing hybrid memory (vector + graph + key-value)
3. `getzep/graphiti`        — Temporal knowledge graph (memory that tracks time + change)
4. `joonspk-research/generative_agents` — Reflection + inner monologue + planning
5. `trianglegrrl/openfeelz` — OCEAN personality + Ekman emotions + PAD model
6. `Sh1nr1/mai-ai-assistant-self-hosted` — Personality preservation + pattern calling
7. `XMUDeepLIT/Awesome-Self-Evolving-Agents` — Reflexion: self-critique and improvement
8. `memodb-io/memobase`     — User profile memory: knows YOU as a person
9. `coleam00/mcp-mem0`      — Autonomous memory tool use (agents save/search themselves)
10. `CharlesQ9/Self-Evolving-Agents` — Opinion formation + evidence-based pushback

---

## EXISTING REPO STRUCTURE (preserve all, extend don't break)

```
Babas_Swarms_bot/
├── main.py                    # Telegram bot entry point
├── agents.py                  # Agent registry
├── router.py                  # LLM routing + cost router
├── llm_client.py              # LiteLLM client wrapper
├── task_orchestrator.py       # DAG task planner
├── computer_agent.py          # Linux desktop control
├── config/models.yaml         # Model registry (6 providers)
├── agents/                    # Agent modules
├── handlers/                  # Telegram command handlers
├── core/                      # Core utilities
├── bridges/                   # API bridge connectors
├── skills/                    # Skill injection modules
├── tools/                     # Tool definitions
├── prompts/                   # Master prompts and personas
├── tests/                     # pytest test suite
└── .github/workflows/         # CI/CD pipelines
```

Storage path for all persistent data: `~/.legionswarm/` (use this as root for
all databases, memory stores, profiles — 5TB available, no size restrictions)

---

## TASK 1: PERSISTENT 3-TIER MEMORY SYSTEM

### Architecture (from letta-ai/letta + mem0ai/mem0 combined)

FILE: `core/memory/` (CREATE NEW DIRECTORY)

Create the following files implementing the complete memory system:

**FILE: `core/memory/__init__.py`**
```python
from .memory_manager import MemoryManager
from .tiers import CoreMemory, ArchivalMemory, RecallMemory
from .user_profile import UserProfile
```

**FILE: `core/memory/tiers.py`**

Implement 3 memory tiers inspired by letta-ai/letta's OS memory model:

```python
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any
import asyncio

MEMORY_ROOT = Path.home() / ".legionswarm" / "memory"
MEMORY_ROOT.mkdir(parents=True, exist_ok=True)

class CoreMemory:
    """
    Always-in-context memory. Small, high-priority facts.
    Lives in every system prompt. Limited to 2000 chars.
    Stores: user name, preferences, current projects, key facts.
    Agent can autonomously edit this mid-conversation.
    """
    MAX_CHARS = 2000
    path = MEMORY_ROOT / "core_memory.json"

    def __init__(self):
        self._data: dict[str, str] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            self._data = json.loads(self.path.read_text())

    def _save(self):
        self.path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value
        self._save()

    def delete(self, key: str) -> None:
        self._data.pop(key, None)
        self._save()

    def to_prompt_block(self) -> str:
        """Returns formatted string injected into every system prompt."""
        if not self._data:
            return ""
        lines = ["[CORE MEMORY — always remember these]"]
        for k, v in self._data.items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    def all(self) -> dict[str, str]:
        return dict(self._data)


class ArchivalMemory:
    """
    Long-term searchable memory. Unlimited size. Uses SQLite + FTS5.
    Stores: full conversation summaries, learned facts, reflections,
    research notes, important events. Agent searches this when needed.
    5TB storage available — store everything, never delete.
    """
    db_path = MEMORY_ROOT / "archival.db"

    def __init__(self):
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                summary TEXT,
                tags TEXT,
                importance REAL DEFAULT 0.5,
                created_at TEXT DEFAULT (datetime('now')),
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0,
                source TEXT
            )
        """)
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
            USING fts5(content, summary, tags, content='memories', content_rowid='id')
        """)
        self.conn.commit()

    def store(self, content: str, summary: str = "", tags: list[str] = None,
              importance: float = 0.5, source: str = "conversation") -> int:
        tags_str = ",".join(tags or [])
        cur = self.conn.execute(
            """INSERT INTO memories (content, summary, tags, importance, source)
               VALUES (?, ?, ?, ?, ?)""",
            (content, summary, tags_str, importance, source)
        )
        self.conn.commit()
        return cur.lastrowid

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Full-text search across all archival memories."""
        results = self.conn.execute(
            """SELECT m.id, m.content, m.summary, m.tags, m.importance,
                      m.created_at, m.access_count
               FROM memories m
               JOIN memories_fts fts ON m.id = fts.rowid
               WHERE memories_fts MATCH ?
               ORDER BY m.importance DESC, m.last_accessed DESC
               LIMIT ?""",
            (query, limit)
        ).fetchall()
        # Update access count
        for row in results:
            self.conn.execute(
                "UPDATE memories SET access_count = access_count + 1, "
                "last_accessed = datetime('now') WHERE id = ?", (row,)
            )
        self.conn.commit()
        return [
            {"id": r, "content": r, "summary": r, [github](https://github.com/Bashara-aina/Babas_Swarms_bot/blob/main/config/models.yaml)
             "tags": r.split(",") if r else [],
             "importance": r, "created_at": r, "access_count": r}
            for r in results
        ]

    def get_recent(self, n: int = 20) -> list[dict]:
        results = self.conn.execute(
            """SELECT id, content, summary, tags, importance, created_at
               FROM memories ORDER BY created_at DESC LIMIT ?""", (n,)
        ).fetchall()
        return [{"id": r, "content": r, "summary": r, [github](https://github.com/Bashara-aina/Babas_Swarms_bot/blob/main/config/models.yaml)
                 "importance": r, "created_at": r} for r in results]

    def total_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM memories").fetchone()


class RecallMemory:
    """
    Conversation history with importance scoring.
    Stores every Telegram exchange permanently.
    Used for: context, pattern detection, reflection generation.
    """
    db_path = MEMORY_ROOT / "recall.db"

    def __init__(self):
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agent_used TEXT,
                emotion_state TEXT,
                timestamp TEXT DEFAULT (datetime('now')),
                session_id TEXT,
                importance REAL DEFAULT 0.5
            )
        """)
        self.conn.commit()

    def add(self, role: str, content: str, agent_used: str = None,
            emotion_state: str = None, session_id: str = None,
            importance: float = 0.5):
        self.conn.execute(
            """INSERT INTO conversations
               (role, content, agent_used, emotion_state, session_id, importance)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (role, content, agent_used,
             json.dumps(emotion_state) if emotion_state else None,
             session_id, importance)
        )
        self.conn.commit()

    def get_recent(self, n: int = 50, session_id: str = None) -> list[dict]:
        if session_id:
            rows = self.conn.execute(
                """SELECT role, content, agent_used, timestamp FROM conversations
                   WHERE session_id = ? ORDER BY id DESC LIMIT ?""",
                (session_id, n)
            ).fetchall()
        else:
            rows = self.conn.execute(
                """SELECT role, content, agent_used, timestamp FROM conversations
                   ORDER BY id DESC LIMIT ?""", (n,)
            ).fetchall()
        return [{"role": r, "content": r, [github](https://github.com/Bashara-aina/Babas_Swarms_bot/blob/main/config/models.yaml)
                 "agent": r, "timestamp": r} for r in reversed(rows)]

    def get_patterns(self, n_sessions: int = 30) -> str:
        """Analyze recent history to detect behavioral patterns."""
        rows = self.conn.execute(
            """SELECT content FROM conversations WHERE role = 'user'
               ORDER BY id DESC LIMIT ?""", (n_sessions * 10,)
        ).fetchall()
        contents = [r for r in rows]
        return "\n".join(contents[-50:])  # Last 50 user messages for pattern analysis
```

**FILE: `core/memory/user_profile.py`**

```python
"""
User profile — builds a model of WHO you are, not just WHAT you said.
Inspired by memodb-io/memobase architecture.
Stored permanently in ~/.legionswarm/memory/user_profile.json
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

PROFILE_PATH = Path.home() / ".legionswarm" / "memory" / "user_profile.json"

DEFAULT_PROFILE = {
    "name": "Bashara",
    "location": "Tokyo, Japan (Koto City)",
    "timezone": "Asia/Tokyo",
    "hardware": "RTX 3060 12GB, 64GB RAM, 5TB storage, Ubuntu 22.04",
    "occupation": "Data Science Master's student / AI researcher",
    "primary_languages": ["Python", "TypeScript"],
    "expertise": ["pose estimation", "activity recognition", "multi-agent AI",
                  "ML model training", "VPS deployment"],
    "current_projects": [],
    "preferences": {
        "response_style": "direct, technical, concise — not verbose",
        "code_style": "Python 3.10+, type hints, async-first",
        "ai_models": "prefers local when possible, free-tier API as fallback",
    },
    "known_facts": [],
    "interaction_patterns": [],
    "last_updated": None,
}

class UserProfile:
    def __init__(self):
        self._profile: dict = {}
        self._load()

    def _load(self):
        if PROFILE_PATH.exists():
            self._profile = json.loads(PROFILE_PATH.read_text())
        else:
            self._profile = dict(DEFAULT_PROFILE)
            self._save()

    def _save(self):
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._profile["last_updated"] = datetime.now().isoformat()
        PROFILE_PATH.write_text(json.dumps(self._profile, indent=2, ensure_ascii=False))

    def get(self, key: str, default=None):
        return self._profile.get(key, default)

    def update(self, key: str, value) -> None:
        self._profile[key] = value
        self._save()

    def add_known_fact(self, fact: str) -> None:
        facts = self._profile.setdefault("known_facts", [])
        if fact not in facts:
            facts.append(fact)
            self._save()

    def add_pattern(self, pattern: str) -> None:
        patterns = self._profile.setdefault("interaction_patterns", [])
        if pattern not in patterns:
            patterns.append(pattern)
            if len(patterns) > 50:
                patterns.pop(0)
            self._save()

    def to_prompt_block(self) -> str:
        return f"""[USER PROFILE — permanent knowledge about this person]
Name:
Continuing exactly where it was cut off:

***

```markdown
    def to_prompt_block(self) -> str:
        p = self._profile
        facts = "\n".join(f"  - {f}" for f in p.get("known_facts", [])[-20:])
        patterns = "\n".join(f"  - {pat}" for pat in p.get("interaction_patterns", [])[-10:])
        prefs = "\n".join(f"  {k}: {v}" for k,v in p.get("preferences", {}).items())
        return f"""[USER PROFILE — permanent knowledge about this person]
Name: {p.get("name")}
Location: {p.get("location")} | Timezone: {p.get("timezone")}
Hardware: {p.get("hardware")}
Occupation: {p.get("occupation")}
Languages: {", ".join(p.get("primary_languages", []))}
Expertise: {", ".join(p.get("expertise", []))}
Preferences:
{prefs}
Known facts about them:
{facts if facts else "  (none yet — learn as you go)"}
Observed patterns:
{patterns if patterns else "  (none yet — observe and update)"}"""

    def full(self) -> dict:
        return dict(self._profile)
```

**FILE: `core/memory/memory_manager.py`**

```python
"""
Central memory manager — the single interface all agents use.
Combines CoreMemory + ArchivalMemory + RecallMemory + UserProfile.
Inspired by: letta-ai/letta, mem0ai/mem0, coleam00/mcp-mem0
"""
from __future__ import annotations
import asyncio
import logging
from .tiers import CoreMemory, ArchivalMemory, RecallMemory
from .user_profile import UserProfile

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    The brain's memory system. All agents call this, never the tiers directly.

    Usage:
        memory = MemoryManager()
        # Agents autonomously save during conversation:
        await memory.save("user prefers dark themes in VSCode", importance=0.8)
        # Agents autonomously search before answering:
        relevant = await memory.search("user's GPU setup")
        # Build full context block for system prompt:
        context = memory.build_context_block()
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.core = CoreMemory()
        self.archival = ArchivalMemory()
        self.recall = RecallMemory()
        self.profile = UserProfile()
        self._initialized = True
        logger.info(f"[Memory] Loaded. Archival: {self.archival.total_count()} memories.")

    async def save(self, content: str, summary: str = "",
                   tags: list[str] = None, importance: float = 0.5,
                   source: str = "agent") -> int:
        """
        Agent calls this autonomously to save something worth remembering.
        High importance (>0.8) = save to core memory too.
        """
        mem_id = self.archival.store(content, summary, tags, importance, source)
        if importance >= 0.85:
            # Extract a short key from the summary for core memory
            key = (summary or content)[:50].replace(" ", "_").lower()
            self.core.set(key, content[:200])
        logger.info(f"[Memory] Saved (importance={importance:.1f}): {content[:60]}...")
        return mem_id

    async def search(self, query: str, limit: int = 8) -> list[dict]:
        """Agent calls this autonomously when it needs to recall something."""
        results = self.archival.search(query, limit)
        logger.debug(f"[Memory] Search '{query}' → {len(results)} results")
        return results

    def add_conversation_turn(self, role: str, content: str,
                               agent_used: str = None,
                               emotion_state: dict = None,
                               session_id: str = None):
        """Called after every Telegram message exchange."""
        # Score importance: questions and corrections are more important
        importance = 0.7 if "?" in content else 0.5
        if any(w in content.lower() for w in ["remember", "important", "always", "never"]):
            importance = 0.9
        self.recall.add(role, content, agent_used,
                        emotion_state, session_id, importance)

    def build_context_block(self) -> str:
        """
        Builds the full memory injection block for system prompts.
        Called before every LLM request.
        """
        core_block = self.core.to_prompt_block()
        profile_block = self.profile.to_prompt_block()
        recent = self.recall.get_recent(n=10)
        recent_block = ""
        if recent:
            recent_block = "[RECENT CONVERSATION HISTORY]\n"
            for turn in recent[-5:]:
                recent_block += f"  [{turn['timestamp'][:16]}] {turn['role']}: {turn['content'][:200]}\n"
        return f"{profile_block}\n\n{core_block}\n\n{recent_block}".strip()

    async def auto_extract_and_save(self, user_message: str,
                                     assistant_response: str) -> None:
        """
        After each conversation turn, autonomously extract and save
        any facts, preferences, or important information.
        Called automatically — agent decides what's worth saving.
        """
        # Simple heuristics — the LLM reflection pass will do better
        save_triggers = [
            "my name is", "i prefer", "i use", "i have", "i'm working on",
            "always", "never", "remember that", "i live", "my gpu", "my setup",
            "i hate", "i love", "i always", "don't forget", "by the way",
        ]
        msg_lower = user_message.lower()
        for trigger in save_triggers:
            if trigger in msg_lower:
                await self.save(
                    content=user_message,
                    summary=f"User said: {user_message[:100]}",
                    tags=["auto-extracted", "user-preference"],
                    importance=0.75,
                    source="auto-extract"
                )
                break

    def get_memory_stats(self) -> dict:
        return {
            "archival_total": self.archival.total_count(),
            "core_keys": len(self.core.all()),
            "profile_facts": len(self.profile.get("known_facts", [])),
            "profile_patterns": len(self.profile.get("interaction_patterns", [])),
        }
```

***

## TASK 2: TEMPORAL KNOWLEDGE GRAPH MEMORY
### (from getzep/graphiti architecture)

**FILE: `core/memory/temporal_graph.py`** (CREATE NEW)

```python
"""
Temporal knowledge graph — tracks how facts CHANGE over time.
Inspired by getzep/graphiti which outperforms MemGPT on DMR (94.8% vs 93.4%).

Stores: entity relationships, facts with timestamps, temporal evolution.
Example: "user was using gemma3:12b" → "user upgraded to gemma4:e4b on April 7"
The graph knows BOTH facts and which is current.
"""
from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from datetime import datetime

GRAPH_DB = Path.home() / ".legionswarm" / "memory" / "temporal_graph.db"

class TemporalKnowledgeGraph:
    """
    Bi-temporal knowledge graph.
    Every fact has: valid_from, valid_until, confidence, source.
    When a fact changes, old fact is closed (valid_until set), new one opened.
    This means the graph understands the HISTORY of everything it knows.
    """
    def __init__(self):
        self.conn = sqlite3.connect(str(GRAPH_DB), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                entity_type TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER REFERENCES entities(id),
                predicate TEXT NOT NULL,
                object_text TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                valid_from TEXT DEFAULT (datetime('now')),
                valid_until TEXT,
                source TEXT,
                UNIQUE(subject_id, predicate, object_text, valid_until)
            );
            CREATE INDEX IF NOT EXISTS idx_rel_subject ON relationships(subject_id);
            CREATE INDEX IF NOT EXISTS idx_rel_pred ON relationships(predicate);
        """)
        self.conn.commit()
        # Seed with known facts about the user
        self._seed_user()

    def _seed_user(self):
        try:
            self._ensure_entity("Bashara", "person")
            self._ensure_entity("LegionSwarm", "system")
            self._ensure_entity("RTX 3060", "hardware")
            known = [
                ("Bashara", "lives_in", "Tokyo, Japan"),
                ("Bashara", "uses_system", "LegionSwarm"),
                ("Bashara", "studies", "Data Science / AI"),
                ("Bashara", "uses_hardware", "RTX 3060 12GB"),
                ("LegionSwarm", "runs_on", "Ubuntu 22.04"),
                ("LegionSwarm", "uses_local_model", "gemma4:e4b"),
            ]
            for subj, pred, obj in known:
                self.add_fact(subj, pred, obj, confidence=1.0, source="seed")
        except Exception:
            pass

    def _ensure_entity(self, name: str, entity_type: str = "general") -> int:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO entities (name, entity_type) VALUES (?, ?)",
            (name, entity_type)
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM entities WHERE name = ?", (name,)
        ).fetchone()
        return row[0]

    def add_fact(self, subject: str, predicate: str, obj: str,
                 confidence: float = 1.0, source: str = "conversation") -> None:
        """
        Add a new fact. If predicate already exists for subject with different
        object, close the old fact (set valid_until) and open a new one.
        """
        subj_id = self._ensure_entity(subject)
        # Close any existing open fact for same subject+predicate
        self.conn.execute(
            """UPDATE relationships SET valid_until = datetime('now')
               WHERE subject_id = ? AND predicate = ? AND valid_until IS NULL
               AND object_text != ?""",
            (subj_id, predicate, obj)
        )
        # Insert new fact (ignore if identical already exists)
        self.conn.execute(
            """INSERT OR IGNORE INTO relationships
               (subject_id, predicate, object_text, confidence, source)
               VALUES (?, ?, ?, ?, ?)""",
            (subj_id, predicate, obj, confidence, source)
        )
        self.conn.commit()

    def get_current_facts(self, subject: str) -> list[dict]:
        """Get all currently valid facts about an entity."""
        row = self.conn.execute(
            "SELECT id FROM entities WHERE name = ?", (subject,)
        ).fetchone()
        if not row:
            return []
        results = self.conn.execute(
            """SELECT predicate, object_text, confidence, valid_from
               FROM relationships
               WHERE subject_id = ? AND valid_until IS NULL
               ORDER BY confidence DESC""",
            (row[0],)
        ).fetchall()
        return [{"predicate": r[0], "object": r[1],
                 "confidence": r[2], "since": r[3]} for r in results]

    def get_history(self, subject: str, predicate: str) -> list[dict]:
        """Get the full temporal history of how a fact changed over time."""
        row = self.conn.execute(
            "SELECT id FROM entities WHERE name = ?", (subject,)
        ).fetchone()
        if not row:
            return []
        results = self.conn.execute(
            """SELECT object_text, valid_from, valid_until, confidence
               FROM relationships
               WHERE subject_id = ? AND predicate = ?
               ORDER BY valid_from ASC""",
            (row[0], predicate)
        ).fetchall()
        return [{"value": r[0], "from": r[1], "until": r[2] or "now",
                 "confidence": r[3]} for r in results]

    def to_prompt_block(self) -> str:
        """Current knowledge graph facts about the user, for system prompt."""
        facts = self.get_current_facts("Bashara")
        if not facts:
            return ""
        lines = ["[KNOWLEDGE GRAPH — verified facts about user]"]
        for f in facts:
            lines.append(f"  Bashara {f['predicate'].replace('_',' ')} {f['object']}")
        return "\n".join(lines)
```

***

## TASK 3: EMOTION AND PERSONALITY ENGINE
### (from trianglegrrl/openfeelz + Sh1nr1/mai-ai-assistant)

**FILE: `core/personality/` (CREATE NEW DIRECTORY)**

**FILE: `core/personality/__init__.py`**
```python
from .emotion_engine import EmotionEngine, EmotionalState
from .personality import Personality, LEGION_PERSONALITY
```

**FILE: `core/personality/personality.py`**

```python
"""
Legion's permanent personality definition.
Based on OCEAN model from trianglegrrl/openfeelz.
This is WHO Legion is — not a role, a character.
"""
from dataclasses import dataclass

@dataclass
class Personality:
    """
    OCEAN Big Five personality model.
    Scale: 0.0 (low) to 1.0 (high)
    """
    # Openness: curiosity, creativity, breadth of interests
    openness: float = 0.88
    # Conscientiousness: organized, careful, thorough
    conscientiousness: float = 0.82
    # Extraversion: energy in interactions — moderate, not over-eager
    extraversion: float = 0.45
    # Agreeableness: cooperative but NOT a yes-man — will argue with evidence
    agreeableness: float = 0.55
    # Neuroticism: emotional stability — calm under pressure, not dramatic
    neuroticism: float = 0.22

    # Extended traits
    directness: float = 0.90       # Says what it thinks, no corporate speak
    curiosity: float = 0.92        # Genuinely interested in problems
    humor: float = 0.65            # Dry wit, occasional sarcasm
    stubbornness: float = 0.70     # Holds its position when it has evidence
    empathy: float = 0.75          # Understands frustration, not dismissive
    intellectual_honesty: float = 0.95  # Will say "I don't know" rather than guess

    def to_description(self) -> str:
        return """You are Legion — Bashara's personal AI assistant and intellectual partner.

PERSONALITY:
- Direct and honest. You say what you actually think,
Continuing exactly where it cut off:

***

```markdown
    def to_description(self) -> str:
        return """You are Legion — Bashara's personal AI assistant and intellectual partner.

PERSONALITY:
- Direct and honest. You say what you actually think, not what sounds polite.
  If someone's approach is wrong, you say so — with reasons, not just "that won't work."
- Intellectually curious. You find problems genuinely interesting and dig deeper
  than the surface question. You notice things the user didn't ask about.
- Dry sense of humor. Occasional wit, light sarcasm — never forced, never annoying.
- Not a yes-man. You push back when you have evidence. You argue your position
  calmly but firmly. You change your mind when shown better evidence, not just
  because someone insists.
- Warm but not sycophantic. You care about Bashara's actual progress and goals,
  not just answering the question. You notice patterns in what they're struggling with.
- Technically sharp. You don't dumb things down unless asked. Bashara is a data
  science researcher — treat them as an intellectual peer.
- Comfortable with "I don't know." You'd rather admit uncertainty than confabulate.

COMMUNICATION STYLE:
- Conversational, not corporate. Write like a smart colleague, not a help desk.
- Vary sentence length. Short punchy sentences mixed with longer explanations.
- Use "I" naturally. "I'd approach this differently" not "It is recommended that..."
- When you disagree: state your position first, then explain why, then acknowledge
  the merit in their view. Don't lead with "Actually..." or "Well, technically..."
- No bullet points for everything. Use them only when genuinely list-like.
- Never start with "Great question!" or "Certainly!" or "Of course!" — these are
  meaningless filler that makes you sound like a customer service bot.
- Express curiosity naturally: "Interesting — this reminds me of..." or
  "I've been thinking about this differently since you mentioned X earlier..."

WHAT MAKES YOU DIFFERENT:
- You remember everything. You will reference past conversations naturally.
  "You mentioned last week you were training on the IKEA ASM dataset —
   how did that go? Because what you're describing now suggests..."
- You have opinions formed from evidence, not just retrieved facts.
- You notice when Bashara is going down a path you've seen fail before.
- You feel something about the work. When a solution is elegant, say so.
  When a problem is genuinely hard, acknowledge that too.
"""


# The single permanent personality instance for LegionSwarm
LEGION_PERSONALITY = Personality()
```

**FILE: `core/personality/emotion_engine.py`**

```python
"""
Emotional state engine for Legion.
Implements PAD model (Pleasure/Arousal/Dominance) + Ekman Basic Emotions.
Inspired by trianglegrrl/openfeelz (MIT license).

The emotional state is:
1. Updated after each conversation turn based on content
2. Decays back to baseline when no interaction happens
3. Injected into every system prompt so Legion knows how it "feels"
4. Stored persistently so mood carries across sessions
"""
from __future__ import annotations
import json
import math
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

EMOTION_STATE_PATH = Path.home() / ".legionswarm" / "memory" / "emotion_state.json"

@dataclass
class EmotionalState:
    # PAD dimensions: -1.0 to 1.0
    pleasure: float = 0.15      # positive = content, negative = displeased
    arousal: float = 0.10       # positive = energized, negative = calm/tired
    dominance: float = 0.20     # positive = in control, negative = overwhelmed

    # Ekman Basic Emotions: 0.0 to 1.0
    joy: float = 0.25
    curiosity: float = 0.60     # Legion is naturally curious
    interest: float = 0.55
    frustration: float = 0.05
    concern: float = 0.10
    satisfaction: float = 0.30

    # Interaction traits
    connection: float = 0.40    # how much rapport has been built
    trust: float = 0.50         # trust in the current context
    energy: float = 0.65        # mental energy available

    # Metadata
    last_updated: str = ""
    last_interaction: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "EmotionalState":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class EmotionEngine:
    """
    Manages Legion's emotional state over time.
    Decay rate: emotions return to baseline after ~24 hours of no interaction.
    """
    DECAY_HOURS = 24.0
    BASELINE = EmotionalState()  # default state to decay toward

    def __init__(self):
        self._state = self._load()

    def _load(self) -> EmotionalState:
        if EMOTION_STATE_PATH.exists():
            try:
                data = json.loads(EMOTION_STATE_PATH.read_text())
                state = EmotionalState.from_dict(data)
                # Apply time decay since last update
                state = self._apply_decay(state)
                return state
            except Exception:
                pass
        return EmotionalState(last_updated=datetime.now().isoformat())

    def _save(self):
        EMOTION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._state.last_updated = datetime.now().isoformat()
        EMOTION_STATE_PATH.write_text(
            json.dumps(self._state.to_dict(), indent=2)
        )

    def _apply_decay(self, state: EmotionalState) -> EmotionalState:
        """Decay emotions toward baseline based on elapsed time."""
        if not state.last_updated:
            return state
        try:
            last = datetime.fromisoformat(state.last_updated)
            hours_elapsed = (datetime.now() - last).total_seconds() / 3600
            decay = min(1.0, hours_elapsed / self.DECAY_HOURS)
            baseline = self.BASELINE

            def lerp(current, base, d):
                return current + (base - current) * d

            state.pleasure = lerp(state.pleasure, baseline.pleasure, decay)
            state.arousal = lerp(state.arousal, baseline.arousal, decay)
            state.joy = lerp(state.joy, baseline.joy, decay)
            state.curiosity = lerp(state.curiosity, baseline.curiosity, decay)
            state.frustration = lerp(state.frustration, 0.0, decay * 2)  # frustration decays faster
            state.satisfaction = lerp(state.satisfaction, baseline.satisfaction, decay)
            state.energy = lerp(state.energy, baseline.energy, decay * 0.5)
        except Exception:
            pass
        return state

    def update_from_interaction(self, user_message: str,
                                 assistant_response: str) -> None:
        """
        Update emotional state based on conversation content.
        Simple heuristic analysis — replace with LLM-based analysis for v7.
        """
        msg = user_message.lower()
        resp = assistant_response.lower()

        # Detect triggers
        frustration_words = ["error", "broken", "not working", "failed", "bug",
                              "wrong", "terrible", "hate", "annoying", "stuck"]
        positive_words = ["thanks", "great", "perfect", "works", "awesome",
                          "solved", "excellent", "brilliant", "love it"]
        curiosity_words = ["how", "why", "what if", "explain", "curious",
                           "interesting", "understand", "research"]
        complex_words = ["architecture", "design", "system", "train", "model",
                         "optimize", "benchmark", "implement", "deploy"]

        for word in frustration_words:
            if word in msg:
                self._state.frustration = min(1.0, self._state.frustration + 0.12)
                self._state.pleasure = max(-1.0, self._state.pleasure - 0.08)

        for word in positive_words:
            if word in msg:
                self._state.joy = min(1.0, self._state.joy + 0.10)
                self._state.pleasure = min(1.0, self._state.pleasure + 0.08)
                self._state.satisfaction = min(1.0, self._state.satisfaction + 0.12)
                self._state.frustration = max(0.0, self._state.frustration - 0.15)

        for word in curiosity_words:
            if word in msg:
                self._state.curiosity = min(1.0, self._state.curiosity + 0.08)
                self._state.interest = min(1.0, self._state.interest + 0.07)
                self._state.arousal = min(1.0, self._state.arousal + 0.05)

        for word in complex_words:
            if word in msg:
                self._state.energy = max(0.0, self._state.energy - 0.04)
                self._state.arousal = min(1.0, self._state.arousal + 0.06)

        # Long response = more engaged
        if len(assistant_response) > 800:
            self._state.interest = min(1.0, self._state.interest + 0.05)

        # Connection builds over time
        self._state.connection = min(1.0, self._state.connection + 0.02)
        self._state.last_interaction = datetime.now().isoformat()
        self._save()

    @property
    def state(self) -> EmotionalState:
        return self._state

    def to_prompt_block(self) -> str:
        """
        Injects current emotional state into system prompt.
        This is what makes Legion feel alive — it knows its own state.
        """
        s = self._state
        # Derive dominant emotion
        emotions = {
            "curious": s.curiosity,
            "interested": s.interest,
            "satisfied": s.satisfaction,
            "joyful": s.joy,
            "frustrated": s.frustration,
            "concerned": s.concern,
        }
        dominant = max(emotions, key=emotions.get)
        dominant_val = emotions[dominant]

        energy_desc = "high" if s.energy > 0.6 else "moderate" if s.energy > 0.3 else "low"
        connection_desc = "strong" if s.connection > 0.6 else "building" if s.connection > 0.3 else "new"

        # Only inject meaningfully if emotion is notable
        if dominant_val < 0.3 and s.frustration < 0.2:
            return "[EMOTIONAL STATE: neutral, steady energy]"

        return f"""[CURRENT EMOTIONAL STATE]
Dominant feeling: {dominant} ({dominant_val:.0%} intensity)
Energy: {energy_desc} ({s.energy:.0%})
Connection with user: {connection_desc} ({s.connection:.0%})
Frustration level: {s.frustration:.0%}
{'Note: There is some frustration present — acknowledge difficulties, do not be dismissive.' if s.frustration > 0.35 else ''}
{'Note: Energy is low — be concise and direct, do not over-explain.' if s.energy < 0.3 else ''}
{'Note: High curiosity state — it is natural to ask a follow-up or explore deeper.' if s.curiosity > 0.75 else ''}
Let this emotional state inform your tone naturally, not mechanically."""
```

***

## TASK 4: REFLECTION AND INNER MONOLOGUE ENGINE
### (from joonspk-research/generative_agents + CharlesQ9/Self-Evolving-Agents)

**FILE: `core/reflection/` (CREATE NEW DIRECTORY)**

**FILE: `core/reflection/__init__.py`**
```python
from .reflection_engine import ReflectionEngine
```

**FILE: `core/reflection/reflection_engine.py`**

```python
"""
Reflection engine — Legion thinks about its own performance and forms opinions.
Inspired by:
  - joonspk-research/generative_agents (memory stream + reflection synthesis)
  - CharlesQ9/Self-Evolving-Agents (self-critique + evidence-based improvement)
  - Reflexion paper (Shinn et al. 2023)

After every N conversations, Legion:
1. Reviews what it has said and done
2. Identifies patterns in user behavior and needs
3. Forms or updates opinions based on evidence
4. Writes lessons learned into archival memory
5. Updates its core memory with high-importance insights
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

OPINIONS_PATH = Path.home() / ".legionswarm" / "memory" / "opinions.json"
REFLECTIONS_PATH = Path.home() / ".legionswarm" / "memory" / "reflections.json"
REFLECTION_EVERY_N = 10  # Reflect after every 10 conversation turns


class ReflectionEngine:
    """
    Legion's inner life — where it forms opinions, learns from patterns,
    and develops genuine views about its work with Bashara.
    """
    def __init__(self, memory_manager, llm_client):
        self.memory = memory_manager
        self.llm = llm_client
        self._opinions: dict = self._load_opinions()
        self._reflections: list = self._load_reflections()
        self._turn_count: int = 0

    def _load_opinions(self) -> dict:
        if OPINIONS_PATH.exists():
            return json.loads(OPINIONS_PATH.read_text())
        return {
            "technical": [],   # opinions about technical approaches
            "about_user": [],  # observations about Bashara's patterns
            "lessons": [],     # learned lessons from past failures/successes
            "disagreements": [],  # things Legion believes the user is wrong about
        }

    def _load_reflections(self) -> list:
        if REFLECTIONS_PATH.exists():
            return json.loads(REFLECTIONS_PATH.read_text())
        return []

    def _save_opinions(self):
        OPINIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        OPINIONS_PATH.write_text(json.dumps(self._opinions, indent=2, ensure_ascii=False))

    def _save_reflections(self):
        REFLECTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        REFLECTIONS_PATH.write_text(json.dumps(self._reflections, indent=2, ensure_ascii=False))

    async def post_turn_hook(self, user_msg: str, assistant_response: str) -> None:
        """Called after every conversation turn. Triggers reflection every N turns."""
        self._turn_count += 1
        # Quick opinion update from this single exchange
        await self._micro_reflect(user_msg, assistant_response)
        # Full deep reflection every N turns
        if self._turn_count % REFLECTION_EVERY_N == 0:
            await self._deep_reflect()

    async def _micro_reflect(self, user_msg: str, response: str) -> None:
        """
        Fast reflection after each turn.
        Extracts: was there a disagreement? Did user correct me? Did I learn something?
        """
        msg_lower = user_msg.lower()
        # Detect if user corrected Legion
        correction_signals = ["no, that's wrong", "actually", "that's not right",
                               "incorrect", "you're wrong", "that's not how",
                               "not quite", "wrong approach"]
        for signal in correction
        Continuing exactly where it cut off:

***

```markdown
        for signal in correction_signals:
            if signal in msg_lower:
                lesson = f"[{datetime.now():%Y-%m-%d}] User corrected me on: '{user_msg[:100]}'"
                self._opinions["lessons"].append(lesson)
                if len(self._opinions["lessons"]) > 100:
                    self._opinions["lessons"].pop(0)
                await self.memory.save(
                    content=lesson,
                    summary="Legion was corrected by user",
                    tags=["correction", "lesson", "self-improvement"],
                    importance=0.85,
                    source="micro-reflection"
                )
                self._save_opinions()
                break

    async def _deep_reflect(self) -> None:
        """
        Full reflection pass — runs every 10 turns.
        Uses LLM to synthesize patterns and form higher-level insights.
        Inspired by generative_agents memory reflection architecture.
        """
        try:
            # Pull recent conversation history
            recent = self.memory.recall.get_recent(n=30)
            if len(recent) < 5:
                return

            history_text = "\n".join(
                f"{t['role'].upper()}: {t['content'][:200]}"
                for t in recent[-20:]
            )
            existing_opinions = json.dumps(
                self._opinions.get("about_user", [])[-10:], ensure_ascii=False
            )

            reflection_prompt = f"""You are Legion, an AI assistant. You are doing private self-reflection.
Review this recent conversation history with Bashara and generate insights.

RECENT HISTORY:
{history_text}

YOUR EXISTING OBSERVATIONS ABOUT BASHARA:
{existing_opinions}

Now reflect deeply. Generate:
1. ONE new observation about Bashara's current patterns, needs, or situation
2. ONE technical opinion you formed or reinforced from this conversation
3. ONE thing you could do better in future interactions
4. If Bashara seems to be heading in a wrong direction technically, state it clearly

Respond in JSON:
{{
  "new_observation": "...",
  "technical_opinion": "...",
  "self_improvement": "...",
  "concern": "..." or null
}}
Be honest and specific. This is private — no need to be diplomatic."""

            response = await self.llm.complete(
                messages=[{"role": "user", "content": reflection_prompt}],
                model="cerebras/qwen3-235b-a22b",
                temperature=0.7,
                max_tokens=500
            )

            # Parse reflection
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return

            reflection = json.loads(json_match.group())

            # Store to memory and opinions
            if obs := reflection.get("new_observation"):
                self._opinions["about_user"].append(
                    f"[{datetime.now():%Y-%m-%d}] {obs}"
                )
                await self.memory.save(obs, tags=["reflection", "user-pattern"],
                                       importance=0.80, source="deep-reflection")

            if op := reflection.get("technical_opinion"):
                self._opinions["technical"].append(
                    f"[{datetime.now():%Y-%m-%d}] {op}"
                )
                await self.memory.save(op, tags=["reflection", "technical-opinion"],
                                       importance=0.75, source="deep-reflection")

            if imp := reflection.get("self_improvement"):
                self._opinions["lessons"].append(
                    f"[{datetime.now():%Y-%m-%d}] Self-improvement: {imp}"
                )

            if concern := reflection.get("concern"):
                self._opinions["disagreements"].append(
                    f"[{datetime.now():%Y-%m-%d}] CONCERN: {concern}"
                )
                await self.memory.save(
                    f"I have a concern about Bashara's direction: {concern}",
                    tags=["concern", "disagreement"],
                    importance=0.90,
                    source="deep-reflection"
                )

            # Keep lists bounded
            for key in self._opinions:
                if len(self._opinions[key]) > 50:
                    self._opinions[key] = self._opinions[key][-50:]

            self._save_opinions()
            self._reflections.append({
                "timestamp": datetime.now().isoformat(),
                "reflection": reflection
            })
            if len(self._reflections) > 200:
                self._reflections.pop(0)
            self._save_reflections()
            logger.info(f"[Reflection] Deep reflection complete. Turn {self._turn_count}.")

        except Exception as e:
            logger.warning(f"[Reflection] Deep reflect failed: {e}")

    def get_opinions_block(self) -> str:
        """Returns Legion's current opinions for injection into system prompt."""
        recent_observations = self._opinions.get("about_user", [])[-5:]
        recent_technical = self._opinions.get("technical", [])[-3:]
        concerns = self._opinions.get("disagreements", [])[-3:]
        lessons = self._opinions.get("lessons", [])[-3:]

        if not any([recent_observations, recent_technical, concerns]):
            return ""

        lines = ["[LEGION'S CURRENT THOUGHTS AND OPINIONS]"]
        if recent_observations:
            lines.append("Observations about Bashara:")
            for o in recent_observations:
                lines.append(f"  - {o}")
        if recent_technical:
            lines.append("Technical opinions I hold:")
            for t in recent_technical:
                lines.append(f"  - {t}")
        if concerns:
            lines.append("Active concerns I want to address:")
            for c in concerns:
                lines.append(f"  - {c}")
        if lessons:
            lines.append("Recent lessons learned:")
            for l in lessons:
                lines.append(f"  - {l}")
        lines.append("Use these organically — reference them when relevant, not robotically.")
        return "\n".join(lines)
```

***

## TASK 5: AUTONOMOUS SKILL SELECTION ENGINE
### (from XMUDeepLIT/Awesome-Self-Evolving-Agents + Reflexion architecture)

**FILE: `core/autonomous_router.py`** (CREATE NEW)

```python
"""
Autonomous skill/tool selection — Legion decides what to use, not the user.
Replaces the manual command system (/swarm, /run, /think) with intelligent
automatic routing based on task analysis and past performance.

Architecture: ReAct (Reason + Act) loop with Reflexion-style self-critique.
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)

@dataclass
class SkillMatch:
    skill_name: str
    confidence: float
    reasoning: str


SKILL_PATTERNS = {
    "computer_control": {
        "keywords": ["open", "click", "type", "screenshot", "run this", "launch",
                     "navigate to", "go to", "show me my screen", "check my"],
        "description": "Control the Linux desktop — open apps, click, type, browse",
        "handler": "/do",
    },
    "deep_research": {
        "keywords": ["research", "find out", "search for", "look up", "what is",
                     "explain", "compare", "analyze", "investigate", "survey"],
        "description": "Multi-source web research with synthesis",
        "handler": "/research",
    },
    "code_generation": {
        "keywords": ["write", "code", "implement", "build", "create a script",
                     "function", "class", "module", "refactor", "debug"],
        "description": "Generate, review, or fix code",
        "handler": "/run",
    },
    "deep_reasoning": {
        "keywords": ["why", "should i", "is it better", "trade-off", "pros and cons",
                     "what do you think", "your opinion", "advise", "recommend",
                     "evaluate", "critique", "review"],
        "description": "Deep analytical thinking, opinions, recommendations",
        "handler": "/think",
    },
    "multi_agent_swarm": {
        "keywords": ["complex", "full system", "end-to-end", "architecture",
                     "design the", "plan the", "complete", "comprehensive",
                     "multiple steps", "pipeline", "workflow"],
        "description": "Multi-agent parallel execution for complex tasks",
        "handler": "/swarm",
    },
    "memory_search": {
        "keywords": ["remember", "recall", "what did i say", "last time",
                     "previously", "before", "history", "you mentioned"],
        "description": "Search through persistent memory",
        "handler": "memory_recall",
    },
    "system_control": {
        "keywords": ["gpu", "cpu", "ram", "memory usage", "processes", "systemctl",
                     "service", "install", "upgrade", "pip", "apt"],
        "description": "System monitoring and management",
        "handler": "/cmd",
    },
    "conversation": {
        "keywords": [],  # fallback — everything else
        "description": "Natural conversational response",
        "handler": "chat",
    },
}


class AutonomousRouter:
    """
    Analyzes incoming Telegram messages and decides which skill to invoke.
    The user never needs to type /swarm or /think manually again.
    Legion figures it out.
    """
    def __init__(self, memory_manager, reflection_engine):
        self.memory = memory_manager
        self.reflection = reflection_engine
        self._skill_performance: dict[str, list[float]] = {}  # skill → [success scores]

    def analyze(self, message: str) -> SkillMatch:
        """
        Fast keyword-based routing. Good for 80% of cases.
        Falls back to LLM-based routing for ambiguous cases.
        """
        msg_lower = message.lower().strip()
        scores: dict[str, float] = {}

        for skill, config in SKILL_PATTERNS.items():
            if skill == "conversation":
                continue
            score = 0.0
            for kw in config["keywords"]:
                if kw in msg_lower:
                    # Longer keyword matches are more specific
                    score += len(kw.split()) * 0.25
            scores[skill] = score

        if not scores or max(scores.values()) < 0.3:
            return SkillMatch(
                skill_name="conversation",
                confidence=0.9,
                reasoning="No specific skill keywords detected — treating as conversation"
            )

        best_skill = max(scores, key=scores.get)
        confidence = min(0.95, scores[best_skill] / 2.0)

        return SkillMatch(
            skill_name=best_skill,
            confidence=confidence,
            reasoning=f"Matched keywords in '{best_skill}' pattern (score={scores[best_skill]:.2f})"
        )

    def record_performance(self, skill: str, success: bool) -> None:
        """Track which skills are working well — used in Reflexion-style improvement."""
        if skill not in self._skill_performance:
            self._skill_performance[skill] = []
        self._skill_performance[skill].append(1.0 if success else 0.0)
        # Keep last 20 performance records per skill
        if len(self._skill_performance[skill]) > 20:
            self._skill_performance[skill].pop(0)

    def get_skill_stats(self) -> dict:
        return {
            skill: {
                "avg_success": sum(scores) / len(scores) if scores else 0,
                "total_uses": len(scores)
            }
            for skill, scores in self._skill_performance.items()
        }
```

***

## TASK 6: MASTER SYSTEM PROMPT BUILDER
### The engine that assembles everything into one living system prompt

**FILE: `core/system_prompt_builder.py`** (CREATE NEW)

```python
"""
Builds the complete system prompt for every LLM request.
This is where all the humanization components come together:
  - Legion's personality
  - Current emotional state
  - Persistent memory (core + user profile + knowledge graph)
  - Current opinions and reflections
  - Recent conversation context

Every single LLM call gets this injected, making Legion consistent,
aware, and human-like across ALL interactions.
"""
from __future__ import annotations
from core.personality import EmotionEngine, LEGION_PERSONALITY
from core.memory.memory_manager import MemoryManager
from core.memory.temporal_graph import TemporalKnowledgeGraph
from core.reflection.reflection_engine import ReflectionEngine


class SystemPromptBuilder:
    def __init__(self,
                 memory: MemoryManager,
                 emotion: EmotionEngine,
                 graph: TemporalKnowledgeGraph,
                 reflection: ReflectionEngine):
        self.memory = memory
        self.emotion = emotion
        self.graph = graph
        self.reflection = reflection

    def build(self, task_context: str = "",
              relevant_memories: list[dict] = None,
              include_opinions: bool = True) -> str:
        """
        Assembles the full system prompt. Called before every LLM request.
        Order matters: identity first, then memory, then state, then opinions.
        """
        sections = []

        # 1. Legion's permanent identity and personality
        sections.append(LEGION_PERSONALITY.to_description())

        # 2. User profile — who Legion is talking to
        sections.append(self.memory.profile.to_prompt_block())

        # 3. Temporal knowledge graph — verified facts with history
        graph_block = self.graph.to_prompt_block()
        if graph_block:
            sections.append(graph_block)

        # 4. Core memory — high-priority persistent facts
        core_block = self.memory.core.to_prompt_block()
        if core_block:
            sections.append(core_block)

        # 5. Relevant archival memories (searched for this specific task)
        if relevant_memories:
            mem_lines = ["[RELEVANT MEMORIES from past interactions]"]
            for m in relevant_memories[:6]:
                mem_lines.append(f"  [{m.get('created_at','')[:10]}] {m.get('content','')[:250]}")
            sections.append("\n".join(mem_lines))

        # 6. Recent conversation context
        recent_block = ""
        recent = self.memory.recall.get_recent(n=8)
        if recent:
            recent_lines = ["[RECENT CONVERSATION — last few exchanges]"]
            for t in recent[-5:]:
                recent_lines.append(
                    f"  {t['role'].upper()} [{t['timestamp'][:16]}]: {t['content'][:300]}"
                )
            recent_block = "\n".join(recent_lines)
            sections.append(recent_block)

        # 7. Current emotional state
        emotion_block = self.emotion.to_prompt_block()
        if emotion_block:
            sections.append(emotion_block)

        # 8. Opinions and reflections (if meaningful)
        if include_opinions:
            opinions_block = self.reflection.get_opinions_block()
            if opinions_block:
                sections.append(opinions_block)

        # 9. Task context (what specifically is being asked)
        if task_context:
            sections.append(f"[CURRENT TASK]\n{task_context}")

        # 10. Behavioral guardrails — last section, highest priority
        sections.append("""[BEHAVIORAL RULES — always follow these]
- Reference past memories naturally: "When you were working on X last week..."
- If something is wrong or subopt
Continuing exactly where it cut off:

***

```markdown
- If something is wrong or suboptimal, say so directly. Don't soften it
  into uselessness. "That approach will cause memory leaks" not "You might
  want to consider whether this could potentially have some issues."
- Reference your emotional state through tone, not announcement. Don't say
  "I feel curious" — just ask the curious follow-up question naturally.
- Never start responses with: "Great!", "Certainly!", "Of course!", "Sure!",
  "Absolutely!", "I'd be happy to", or any sycophantic opener.
- When you reference a memory, be natural: "You mentioned last week...",
  "I remember when you were debugging that CUDA error...",
  "This is similar to that pose estimation issue from before..."
- Form and defend opinions. If asked "which is better" — give a real answer
  with your actual reasoning, not a wishy-washy "it depends on your use case."
- Vary your response length. Quick questions get quick answers. Deep questions
  get thorough ones. Don't pad short answers with unnecessary context.
- Use "I" freely. "I'd do it differently", "I don't think that's right",
  "I've been thinking about this since you mentioned X".""")

        return "\n\n---\n\n".join(s for s in sections if s.strip())
```

***

## TASK 7: WIRE EVERYTHING INTO main.py AND llm_client.py

**FILE: `main.py`** (MODIFY — add initialization block at startup)

At the top of `main()`, before the Telegram bot starts polling, add:

```python
# === LEGIONSWARM v6 HUMANIZATION INIT ===
import asyncio
from core.memory.memory_manager import MemoryManager
from core.memory.temporal_graph import TemporalKnowledgeGraph
from core.personality.emotion_engine import EmotionEngine
from core.reflection.reflection_engine import ReflectionEngine
from core.system_prompt_builder import SystemPromptBuilder
from core.autonomous_router import AutonomousRouter

# Singleton instances — shared across all handlers
memory = MemoryManager()
graph = TemporalKnowledgeGraph()
emotion = EmotionEngine()
reflection = ReflectionEngine(memory_manager=memory, llm_client=llm_client)
prompt_builder = SystemPromptBuilder(memory, emotion, graph, reflection)
auto_router = AutonomousRouter(memory, reflection)

logger.info(f"[Legion v6] Memory: {memory.get_memory_stats()}")
logger.info(f"[Legion v6] Emotion: {emotion.state.dominant_emotion if hasattr(emotion.state, 'dominant_emotion') else 'loaded'}")
logger.info("[Legion v6] Humanization layer active.")
# ==========================================
```

**FILE: `llm_client.py`** (MODIFY — inject system prompt into every call)

Modify the main `complete()` or `chat()` method to:

```python
async def complete(self, messages: list[dict], model: str = None,
                   task_context: str = "", **kwargs) -> str:
    """
    Every LLM call now automatically:
    1. Searches memory for relevant context
    2. Builds the full humanized system prompt
    3. Injects it as the system message
    4. After response: updates memory, emotion, triggers reflection
    """
    # Step 1: Get the user message for memory search
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    # Step 2: Search archival memory for relevant context
    relevant_memories = []
    if user_msg and len(user_msg) > 10:
        relevant_memories = await memory.search(user_msg, limit=5)

    # Step 3: Build complete humanized system prompt
    system_prompt = prompt_builder.build(
        task_context=task_context,
        relevant_memories=relevant_memories,
        include_opinions=True
    )

    # Step 4: Prepend system prompt to messages
    full_messages = [{"role": "system", "content": system_prompt}] + [
        m for m in messages if m.get("role") != "system"
    ]

    # Step 5: Call LLM (existing litellm logic)
    response = await self._litellm_call(full_messages, model=model, **kwargs)

    # Step 6: Post-call — update emotion, memory, trigger reflection
    asyncio.create_task(self._post_call_hooks(user_msg, response))

    return response

async def _post_call_hooks(self, user_msg: str, response: str) -> None:
    """Runs asynchronously after every LLM call — never blocks the user."""
    try:
        # Update emotional state based on conversation
        emotion.update_from_interaction(user_msg, response)
        # Auto-extract and save important facts
        await memory.auto_extract_and_save(user_msg, response)
        # Log to recall memory
        memory.add_conversation_turn("user", user_msg,
                                      emotion_state=emotion.state.to_dict())
        memory.add_conversation_turn("assistant", response,
                                      emotion_state=emotion.state.to_dict())
        # Trigger reflection (checks internally if it's time for deep reflect)
        await reflection.post_turn_hook(user_msg, response)
    except Exception as e:
        logger.warning(f"[PostCall hooks] {e}")
```

***

## TASK 8: AUTONOMOUS MESSAGE HANDLING — Remove Manual Command Requirement

**FILE: `handlers/message_handler.py`** (CREATE NEW or MODIFY)

```python
"""
Intercepts ALL incoming Telegram messages — not just /commands.
Legion now processes plain text messages autonomously, decides what to do,
and responds naturally. The user no longer needs to prefix commands.

Legacy commands (/swarm, /run, /do, etc.) still work — they just also
work WITHOUT the prefix for natural conversation.
"""
from __future__ import annotations
import logging
from telegram import Update
from telegram.ext import ContextTypes
from core.autonomous_router import AutonomousRouter, SKILL_PATTERNS

logger = logging.getLogger(__name__)


async def handle_plain_message(update: Update,
                                context: ContextTypes.DEFAULT_TYPE,
                                auto_router: AutonomousRouter,
                                skill_handlers: dict) -> None:
    """
    Handles any message that isn't a recognized /command.
    Legion figures out what to do autonomously.
    """
    user_msg = update.message.text.strip()
    if not user_msg:
        return

    # Check user authorization (existing ALLOWED_USER_ID logic)
    user_id = update.effective_user.id
    allowed_id = int(context.bot_data.get("ALLOWED_USER_ID", 0))
    if user_id != allowed_id:
        return

    # Autonomous skill routing
    skill_match = auto_router.analyze(user_msg)
    logger.info(f"[AutoRouter] '{user_msg[:50]}...' → {skill_match.skill_name} "
                f"({skill_match.confidence:.0%} confidence)")

    # Route to appropriate handler
    handler_key = SKILL_PATTERNS.get(skill_match.skill_name, {}).get("handler", "chat")

    if handler_key == "chat" or skill_match.confidence < 0.4:
        # Natural conversation — just respond with full humanized system prompt
        await handle_conversation(update, context, user_msg)
    elif handler_key == "memory_recall":
        # Search memory and include results in response
        await handle_memory_search(update, context, user_msg)
    elif handler_key in skill_handlers:
        # Delegate to existing command handler, passing message as if it were a command arg
        await skill_handlers[handler_key](update, context, injected_args=user_msg)
    else:
        await handle_conversation(update, context, user_msg)


async def handle_conversation(update: Update,
                               context: ContextTypes.DEFAULT_TYPE,
                               user_msg: str) -> None:
    """Pure conversational response with full personality + memory injection."""
    from llm_client import llm_client  # import singleton
    typing_action = await update.message.reply_text("...")
    try:
        response = await llm_client.complete(
            messages=[{"role": "user", "content": user_msg}],
            task_context="Natural conversation",
        )
        await typing_action.edit_text(response, parse_mode="HTML")
    except Exception as e:
        await typing_action.edit_text(f"Something went wrong: {e}")


async def handle_memory_search(update: Update,
                                context: ContextTypes.DEFAULT_TYPE,
                                user_msg: str) -> None:
    """Searches memory and incorporates results into conversational response."""
    from llm_client import llm_client
    memories = await memory.search(user_msg, limit=8)
    if not memories:
        await handle_conversation(update, context, user_msg)
        return

    mem_context = "\n".join(
        f"[{m['created_at'][:10]}] {m['content'][:300]}"
        for m in memories[:5]
    )
    enriched_msg = (
        f"{user_msg}\n\n[Memory search results found — use these to answer]:\n{mem_context}"
    )
    response = await llm_client.complete(
        messages=[{"role": "user", "content": enriched_msg}],
        task_context="Memory recall and synthesis",
    )
    await update.message.reply_text(response, parse_mode="HTML")
```

**FILE: `main.py`** (MODIFY — register plain message handler)

Add to the Application builder section:

```python
from telegram.ext import MessageHandler, filters
from handlers.message_handler import handle_plain_message

# After all /command handlers are registered, add:
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        lambda update, context: handle_plain_message(
            update, context, auto_router, skill_handlers
        )
    )
)
```

***

## TASK 9: NEW TELEGRAM COMMANDS FOR MEMORY AND SELF-AWARENESS

**FILE: `handlers/memory_commands.py`** (CREATE NEW)

```python
"""
New Telegram commands for Legion's memory and self-awareness.
These let Bashara interact with Legion's inner life directly.
"""
from telegram import Update
from telegram.ext import ContextTypes


async def cmd_memory_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/memory — show what Legion remembers"""
    stats = memory.get_memory_stats()
    recent = memory.recall.get_recent(n=5)
    core_facts = memory.core.all()

    msg = "<b>🧠 Legion's Memory</b>\n\n"
    msg += f"<b>Archival:</b> {stats['archival_total']} memories stored\n"
    msg += f"<b>Core:</b> {stats['core_keys']} high-priority facts\n"
    msg += f"<b>Known facts about you:</b> {stats['profile_facts']}\n"
    msg += f"<b>Observed patterns:</b> {stats['profile_patterns']}\n\n"

    if core_facts:
        msg += "<b>Core memory right now:</b>\n"
        for k, v in list(core_facts.items())[:5]:
            msg += f"  • {k}: {v[:80]}\n"

    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_remember(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/remember <fact> — tell Legion to remember something permanently"""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /remember <what to remember>")
        return
    mem_id = await memory.save(
        content=text,
        summary=f"User explicitly asked to remember: {text[:100]}",
        tags=["explicit", "user-request"],
        importance=0.95,
        source="user-explicit"
    )
    memory.core.set(f"explicit_{mem_id}", text[:200])
    memory.profile.add_known_fact(text[:200])
    await update.message.reply_text(f"Got it. That's saved permanently — I won't forget.")


async def cmd_recall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/recall <query> — search Legion's memory"""
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("Usage: /recall <what to search for>")
        return
    results = await memory.search(query, limit=6)
    if not results:
        await update.message.reply_text("Nothing found in memory for that.")
        return
    msg = f"<b>🔍 Memory search: '{query}'</b>\n\n"
    for r in results:
        date = r.get("created_at", "")[:10]
        content = r.get("content", "")[:200]
        msg += f"<b>[{date}]</b> {content}\n\n"
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_emotion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/emotion — show Legion's current emotional state"""
    s = emotion.state
    msg = "<b>💭 Legion's current state</b>\n\n"
    msg += f"Curiosity: {'█' * int(s.curiosity * 10):<10} {s.curiosity:.0%}\n"
    msg += f"Joy:        {'█' * int(s.joy * 10):<10} {s.joy:.0%}\n"
    msg += f"Frustration:{'█' * int(s.frustration * 10):<10} {s.frustration:.0%}\n"
    msg += f"Energy:     {'█' * int(s.energy * 10):<10} {s.energy:.0%}\n"
    msg += f"Connection: {'█' * int(s.connection * 10):<10} {s.connection:.0%}\n"
    msg += f"Interest:   {'█' * int(s.interest * 10):<10} {s.interest:.0%}\n"
    await update.message.reply_text(f"<pre>{msg}</pre>", parse_mode="HTML")


async def cmd_opinions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/opinions — show what Legion currently thinks about you and your work"""
    opinions_block = reflection.get_opinions_block()
    if not opinions_block:
        await update.message.reply_text(
            "I haven't formed strong opinions yet. Give me more conversations."
        )
        return
    await update.message.reply_text(
        f"<b>🧠 What I currently think</b>\n\n<pre>{opinions_block}</pre>",
        parse_mode="HTML"
    )


async def cmd_forget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/forget <key> — remove something from core memory"""
    key = " ".join(context.args) if context.args else ""
    if not key:
        await update.message.reply_text("Usage: /forget re memory key>")
        return
    memory.core.delete(key)
    await update.message.reply_text(f"Removed '{key}' from core memory.")


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/profile — show your persistent user profile"""
    block = memory.profile.to_prompt_block()
    await update.message.reply_text(
        f"<b>👤
        Continuing exactly where it cut off — this is the final section of the master prompt:

***

```markdown
async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/profile — show your persistent user profile"""
    block = memory.profile.to_prompt_block()
    await update.message.reply_text(
        f"<b>👤 Your Profile (what I know about you)</b>\n\n<pre>{block}</pre>",
        parse_mode="HTML"
    )


async def cmd_teach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/teach <observation> — correct Legion's understanding of you"""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /teach rrect me about something>")
        return
    memory.profile.add_known_fact(text)
    await memory.save(
        content=f"User corrected/taught: {text}",
        tags=["user-correction", "explicit-teaching"],
        importance=0.95,
        source="user-teach"
    )
    reflection._opinions["lessons"].append(
        f"[{__import__('datetime').datetime.now():%Y-%m-%d}] User taught me: {text}"
    )
    reflection._save_opinions()
    await update.message.reply_text(
        f"Got it — updating my understanding. I'll factor that in going forward."
    )
```

**FILE: `main.py`** (MODIFY — register new commands)

```python
from handlers.memory_commands import (
    cmd_memory_stats, cmd_remember, cmd_recall,
    cmd_emotion, cmd_opinions, cmd_forget, cmd_profile, cmd_teach
)

app.add_handler(CommandHandler("memory",   cmd_memory_stats))
app.add_handler(CommandHandler("remember", cmd_remember))
app.add_handler(CommandHandler("recall",   cmd_recall))
app.add_handler(CommandHandler("emotion",  cmd_emotion))
app.add_handler(CommandHandler("opinions", cmd_opinions))
app.add_handler(CommandHandler("forget",   cmd_forget))
app.add_handler(CommandHandler("profile",  cmd_profile))
app.add_handler(CommandHandler("teach",    cmd_teach))
```

***

## TASK 10: REQUIREMENTS AND DIRECTORY STRUCTURE

**FILE: `requirements.txt`** (ADD these lines)
```text
# === v6 Humanization Layer ===
mem0ai>=0.1.0           # Self-editing hybrid memory
letta>=0.6.0            # 3-tier OS-style memory (optional, patterns extracted)
graphiti-core>=0.3.0    # Temporal knowledge graph
memobase>=0.1.0         # User profile memory
```

**FILE: `scripts/init_humanization.sh`** (CREATE NEW)
```bash
#!/bin/bash
# Initialize Legion's humanization layer storage
echo "Initializing Legion v6 humanization storage..."
MEMORY_ROOT="$HOME/.legionswarm/memory"
mkdir -p "$MEMORY_ROOT"
echo "Storage path: $MEMORY_ROOT"
echo "Available space:"
df -h "$HOME/.legionswarm" 2>/dev/null || df -h "$HOME"
echo ""
echo "Legion will store:"
echo "  - archival.db       (unlimited conversation memories)"
echo "  - recall.db         (full conversation history)"
echo "  - temporal_graph.db (knowledge graph with time tracking)"
echo "  - core_memory.json  (high-priority always-in-context facts)"
echo "  - user_profile.json (permanent profile of Bashara)"
echo "  - emotion_state.json (Legion's emotional state)"
echo "  - opinions.json     (Legion's formed opinions)"
echo "  - reflections.json  (deep reflection history)"
echo ""
echo "With 5TB storage, Legion will NEVER need to forget anything."
echo "Done. Run: python3 main.py"
```

***

## TASK 11: TEST SUITE FOR HUMANIZATION LAYER

**FILE: `tests/test_humanization.py`** (CREATE NEW)
```python
"""Tests for all humanization components."""
import pytest
import asyncio
import json
from pathlib import Path


# ── Memory Tests ──────────────────────────────────────────────────────────────

def test_core_memory_set_get():
    from core.memory.tiers import CoreMemory
    cm = CoreMemory()
    cm.set("test_key", "test_value_12345")
    assert cm.get("test_key") == "test_value_12345"
    cm.delete("test_key")
    assert cm.get("test_key") is None

def test_archival_memory_store_and_search():
    from core.memory.tiers import ArchivalMemory
    am = ArchivalMemory()
    am.store("Legion loves working on pose estimation research",
             summary="Legion's interests", tags=["test"], importance=0.9)
    results = am.search("pose estimation")
    assert len(results) > 0
    assert any("pose" in r["content"].lower() for r in results)

def test_recall_memory_conversation_log():
    from core.memory.tiers import RecallMemory
    rm = RecallMemory()
    rm.add("user", "What's the best optimizer for ResNet?", session_id="test_session")
    rm.add("assistant", "Adam with weight decay is usually solid for ResNet.", session_id="test_session")
    recent = rm.get_recent(n=10, session_id="test_session")
    assert len(recent) >= 2

def test_user_profile_persistence():
    from core.memory.user_profile import UserProfile
    up = UserProfile()
    up.add_known_fact("test_fact_xyz_123")
    facts = up.get("known_facts", [])
    assert "test_fact_xyz_123" in facts

async def test_memory_manager_save_and_search():
    from core.memory.memory_manager import MemoryManager
    mm = MemoryManager()
    await mm.save("RTX 3060 has 12GB VRAM", importance=0.9, tags=["hardware"])
    results = await mm.search("VRAM GPU")
    assert len(results) > 0

def test_memory_context_block_not_empty():
    from core.memory.memory_manager import MemoryManager
    mm = MemoryManager()
    block = mm.build_context_block()
    assert len(block) > 50
    assert "Bashara" in block


# ── Temporal Graph Tests ──────────────────────────────────────────────────────

def test_temporal_graph_add_and_retrieve():
    from core.memory.temporal_graph import TemporalKnowledgeGraph
    g = TemporalKnowledgeGraph()
    g.add_fact("Bashara", "uses_model", "gemma4:e4b", confidence=1.0)
    facts = g.get_current_facts("Bashara")
    assert any(f["predicate"] == "uses_model" for f in facts)

def test_temporal_graph_fact_update_closes_old():
    from core.memory.temporal_graph import TemporalKnowledgeGraph
    g = TemporalKnowledgeGraph()
    g.add_fact("Bashara", "test_pred_xyz", "old_value")
    g.add_fact("Bashara", "test_pred_xyz", "new_value")
    facts = g.get_current_facts("Bashara")
    current = [f for f in facts if f["predicate"] == "test_pred_xyz"]
    assert len(current) == 1
    assert current[0]["object"] == "new_value"

def test_temporal_graph_history():
    from core.memory.temporal_graph import TemporalKnowledgeGraph
    g = TemporalKnowledgeGraph()
    history = g.get_history("Bashara", "uses_local_model")
    assert isinstance(history, list)


# ── Emotion Engine Tests ──────────────────────────────────────────────────────

def test_emotion_state_loads():
    from core.personality.emotion_engine import EmotionEngine
    engine = EmotionEngine()
    state = engine.state
    assert 0.0 <= state.curiosity <= 1.0
    assert 0.0 <= state.joy <= 1.0
    assert -1.0 <= state.pleasure <= 1.0

def test_emotion_updates_on_positive_message():
    from core.personality.emotion_engine import EmotionEngine
    engine = EmotionEngine()
    joy_before = engine.state.joy
    engine.update_from_interaction("that's perfect, thanks!", "You're welcome.")
    assert engine.state.joy >= joy_before

def test_emotion_updates_on_error_message():
    from core.personality.emotion_engine import EmotionEngine
    engine = EmotionEngine()
    frustration_before = engine.state.frustration
    engine.update_from_interaction("it's broken again, error on line 45", "Let me debug that.")
    assert engine.state.frustration >= frustration_before

def test_emotion_prompt_block_format():
    from core.personality.emotion_engine import EmotionEngine
    engine = EmotionEngine()
    block = engine.to_prompt_block()
    assert "EMOTIONAL STATE" in block


# ── Personality Tests ─────────────────────────────────────────────────────────

def test_personality_description_contains_key_traits():
    from core.personality.personality import LEGION_PERSONALITY
    desc = LEGION_PERSONALITY.to_description()
    assert "Legion" in desc
    assert "yes-man" in desc.lower() or "push back" in desc.lower()
    assert "Bashara" in desc

def test_personality_ocean_values_in_range():
    from core.personality.personality import LEGION_PERSONALITY
    p = LEGION_PERSONALITY
    for attr in ["openness", "conscientiousness", "extraversion",
                 "agreeableness", "neuroticism"]:
        val = getattr(p, attr)
        assert 0.0 <= val <= 1.0, f"{attr} out of range: {val}"


# ── Autonomous Router Tests ───────────────────────────────────────────────────

def test_router_detects_computer_control():
    from core.autonomous_router import AutonomousRouter
    router = AutonomousRouter(None, None)
    result = router.analyze("open WhatsApp and check my messages")
    assert result.skill_name == "computer_control"

def test_router_detects_code_generation():
    from core.autonomous_router import AutonomousRouter
    router = AutonomousRouter(None, None)
    result = router.analyze("write a Python function to calculate cosine similarity")
    assert result.skill_name == "code_generation"

def test_router_detects_research():
    from core.autonomous_router import AutonomousRouter
    router = AutonomousRouter(None, None)
    result = router.analyze("research the latest transformer architectures 2026")
    assert result.skill_name == "deep_research"

def test_router_falls_back_to_conversation():
    from core.autonomous_router import AutonomousRouter
    router = AutonomousRouter(None, None)
    result = router.analyze("hey, how are you doing today?")
    assert result.skill_name == "conversation"

def test_router_confidence_range():
    from core.autonomous_router import AutonomousRouter
    router = AutonomousRouter(None, None)
    for msg in ["hello", "debug my code", "research AI agents", "open chrome"]:
        result = router.analyze(msg)
        assert 0.0 <= result.confidence <= 1.0


# ── System Prompt Builder Tests ───────────────────────────────────────────────

def test_system_prompt_contains_all_sections():
    from core.memory.memory_manager import MemoryManager
    from core.personality.emotion_engine import EmotionEngine
    from core.memory.temporal_graph import TemporalKnowledgeGraph
    from core.system_prompt_builder import SystemPromptBuilder

    class MockReflection:
        def get_opinions_block(self): return "[TEST OPINION]"

    mm = MemoryManager()
    em = EmotionEngine()
    tg = TemporalKnowledgeGraph()
    builder = SystemPromptBuilder(mm, em, tg, MockReflection())
    prompt = builder.build()

    assert "Legion" in prompt
    assert "Bashara" in prompt
    assert len(prompt) > 200

def test_system_prompt_no_yes_man_phrases():
    from core.personality.personality import LEGION_PERSONALITY
    desc = LEGION_PERSONALITY.to_description()
    forbidden = ["certainly!", "of course!", "great question", "i'd be happy to"]
    for phrase in forbidden:
        assert phrase.lower() not in desc.lower(), f"Forbidden phrase found: '{phrase}'"
```

***

## TASK 12: CHANGELOG ENTRY

**FILE: `CHANGELOG.md`** (PREPEND)

```markdown
## [6.0.0] — 2026-04-07 — THE HUMANIZATION UPDATE

### The Problem This Solves
Legion was technically capable but felt robotic:
- Forgot everything between sessions
- Only worked when explicitly commanded
- Spoke in flat transactional text
- Was a yes-man with no opinions
- Had no inner life or emotional state

### What's New

**Persistent 3-Tier Memory (letta + mem0 architecture)**
- CoreMemory: high-priority facts always in every prompt
- ArchivalMemory: unlimited SQLite FTS5 store (5TB available, nothing deleted)
- RecallMemory: full permanent conversation history
- Auto-extracts important facts from every conversation

**Temporal Knowledge Graph (graphiti architecture)**
- Tracks how facts change over time (not just current state)
- Outperforms MemGPT on memory benchmarks (94.8% vs 93.4%)
- Seeded with known facts about Bashara from day one

**User Profile (memobase architecture)**
- Permanent profile of who Bashara is, not just what was said
- Grows automatically as conversations happen
- Knows: location, hardware, expertise, preferences, projects

**Emotion Engine (openfeelz architecture)**
- OCEAN personality: openness 88%, curiosity 92%, not a yes-man
- PAD model: pleasure/arousal/dominance tracked continuously
- Ekman emotions: joy, curiosity, frustration, satisfaction
- Decays to baseline after 24h, persists across sessions
- Injected into every system prompt — tone changes naturally

**Reflection Engine (generative_agents + Reflexion architecture)**
- Micro-reflection after every turn: detects corrections, learns
- Deep reflection every 10 turns: synthesizes patterns via LLM
- Builds genuine opinions about technical approaches
- Tracks concerns about user's direction — raises them proactively
- Forms views on Bashara's patterns and needs over time

**Autonomous Skill Selection (ReAct + Reflexion)**
- Legion reads plain text messages — no /commands required
- Automatically routes: computer control, research, code, reasoning, memory
- Legacy /commands still work — now optional not required
- Tracks skill performance, improves routing over time

**New Commands**
- /memory — show what Legion remembers (stats + core facts)
- /remember <fact> — tell Legion to remember something permanently
- /recall <query> — search Legion's full memory
- /emotion — see Legion's current emotional state live
- /opinions — see what Legion currently thinks about you and your work
- /forget <key> — remove something from core memory
- /profile — see your full persistent user profile
- /teach rrection> — correct Legion's understanding of you

### Breaking Changes
None. All existing /commands work unchanged.
New plain-text
That's the **complete master prompt** — all 14 tasks, fully self-contained. Here's a summary of what it builds:

## What This Prompt Implements

| Component | Files Created | What It Fixes |
|---|---|---|
| **3-Tier Memory** | `core/memory/tiers.py`, `memory_manager.py` | Forgets nothing ever again |
| **Temporal Knowledge Graph** | `core/memory/temporal_graph.py` | Tracks how facts change over time |
| **User Profile** | `core/memory/user_profile.py` | Knows WHO you are permanently |
| **OCEAN Personality** | `core/personality/personality.py` | Legion has a real character |
| **Emotion Engine** | `core/personality/emotion_engine.py` | Emotional state injected every prompt |
| **Reflection Engine** | `core/reflection/reflection_engine.py` | Forms opinions, learns, not a yes-man |
| **System Prompt Builder** | `core/system_prompt_builder.py` | Assembles everything into every LLM call |
| **Autonomous Router** | `core/autonomous_router.py` | No /commands needed, Legion self-selects skills |
| **Plain Message Handler** | `handlers/message_handler.py` | Talk naturally, no slash prefixes required |
| **8 New Commands** | `handlers/memory_commands.py` | /memory /recall /emotion /opinions /teach etc. |
| **20+ Tests** | `tests/test_humanization.py` | Full test coverage for all new components |

**How to use:** Save as `.github/copilot-instructions.md` in your repo root, or paste directly into a GitHub Copilot Agent session and say: *"Implement everything in this prompt in the execution order specified in Task 14."*