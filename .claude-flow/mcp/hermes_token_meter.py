#!/usr/bin/env python3
"""
Token Usage Metering and Cost Tracking for Hermes MCP sessions.

Replicates Claude Code's per-session token breakdown. Tracks input/output/cache tokens
per session with MiniMax model pricing, budget enforcement, and JSON persistence.

Usage:
    from hermes_token_meter import TokenMeter, PRICING
    meter = TokenMeter()
    meter.count_request(session_id="abc", model="MiniMax-Text-01",
                        prompt_tokens=500, completion_tokens=200,
                        cache_create_tokens=100, cache_read_tokens=50)
    print(meter.get_report("abc"))
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except Exception:
    _TIKTOKEN_AVAILABLE = False

# ── Pricing (USD per 1M tokens) ───────────────────────────────────────────────

PRICING = {
    # MiniMax models
    "MiniMax-Text-01": {"input": 0.07, "output": 0.28, "cache_create": 0.07, "cache_read": 0.007},
    "MiniMax-Text-01-v1.5": {"input": 0.07, "output": 0.28, "cache_create": 0.07, "cache_read": 0.007},
    "MiniMax-Text-01-mini": {"input": 0.02, "output": 0.10, "cache_create": 0.02, "cache_read": 0.002},
    "MiniMax-Text-01-large": {"input": 0.15, "output": 0.60, "cache_create": 0.15, "cache_read": 0.015},
    # Ollama local (free = $0)
    "ollama_chat/gemma3:12b": {"input": 0.0, "output": 0.0, "cache_create": 0.0, "cache_read": 0.0},
    "ollama_chat/llama3.3:70b": {"input": 0.0, "output": 0.0, "cache_create": 0.0, "cache_read": 0.0},
    "ollama_chat/llama3.2:3b": {"input": 0.0, "output": 0.0, "cache_create": 0.0, "cache_read": 0.0},
    # OpenRouter free/cheap fallbacks
    "openrouter/qwen/qwen3-coder:free": {"input": 0.0, "output": 0.0, "cache_create": 0.0, "cache_read": 0.0},
    "cerebras/qwen3-235b-a22b": {"input": 0.0, "output": 0.0, "cache_create": 0.0, "cache_read": 0.0},
    "zai/glm-4": {"input": 0.0, "output": 0.0, "cache_create": 0.0, "cache_read": 0.0},
    "groq/moonshotai/kimi-k2-instruct": {"input": 0.0, "output": 0.0, "cache_create": 0.0, "cache_read": 0.0},
    "gemini/gemini-2.0-flash": {"input": 0.0, "output": 0.0, "cache_create": 0.0, "cache_read": 0.0},
    # Default for unknown models
    "unknown": {"input": 0.0, "output": 0.0, "cache_create": 0.0, "cache_read": 0.0},
}

# ── Token Counter ─────────────────────────────────────────────────────────────

def _get_tiktoken_encoder():
    """Get tiktoken encoder, falling back to char-count estimation."""
    if not _TIKTOKEN_AVAILABLE:
        return None
    try:
        return tiktoken.encoding_for_model("gpt-4o")
    except Exception:
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None


_ENCODER = _get_tiktoken_encoder()


def count_tokens(text: str | list, model: str = "unknown") -> int:
    """
    Count tokens in text using tiktoken (cl100k_base) or fallback to char-count.

    Uses tiktoken as primary (cl100k_base covers most LLMs including MiniMax).
    Falls back to char-count / 4 estimation if tiktoken unavailable.

    Args:
        text: String or list of message dicts to count
        model: Model name (for future per-model encoders)

    Returns:
        Approximate token count
    """
    if not text:
        return 0

    if _ENCODER is not None:
        try:
            if isinstance(text, list):
                # Messages format - encode concatenated content
                content = " ".join(
                    m.get("content", "") if isinstance(m, dict) else str(m)
                    for m in text
                )
                return len(_ENCODER.encode(content))
            return len(_ENCODER.encode(text))
        except Exception:
            pass

    # Fallback: char-count / 4
    if isinstance(text, list):
        text = " ".join(m.get("content", "") if isinstance(m, dict) else str(m) for m in text)
    return max(1, len(text) // 4)


# ── TokenSession & Budget ─────────────────────────────────────────────────────

class TokenSession:
    """Holds all token counters for a single session."""

    __slots__ = (
        "budget_tokens",
        "cache_creation_tokens",
        "cache_read_tokens",
        "input_tokens",
        "model",
        "output_tokens",
        "session_id",
        "started_at",
        "total_cost_usd",
        "turn_count",
        "warnings_issued",
    )

    def __init__(
        self,
        session_id: str,
        model: str = "unknown",
        budget_tokens: int = 0,
    ):
        self.session_id = session_id
        self.started_at = time.time()
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_creation_tokens = 0
        self.cache_read_tokens = 0
        self.total_cost_usd = 0.0
        self.model = model
        self.turn_count = 0
        self.budget_tokens = budget_tokens
        self.warnings_issued: set[int] = set()  # tracks which % thresholds warned

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def budget_pct(self) -> float:
        if self.budget_tokens <= 0:
            return 0.0
        return min(100.0, self.total_tokens / self.budget_tokens * 100)

    def estimate_cost(self, model: str) -> float:
        """Calculate USD cost using PRICING table."""
        p = PRICING.get(model, PRICING["unknown"])
        cost = (
            self.input_tokens * p["input"]
            + self.output_tokens * p["output"]
            + self.cache_creation_tokens * p["cache_create"]
            + self.cache_read_tokens * p["cache_read"]
        ) / 1_000_000
        self.total_cost_usd = cost
        return cost

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "model": self.model,
            "turn_count": self.turn_count,
            "budget_tokens": self.budget_tokens,
            "budget_pct": round(self.budget_pct, 2),
        }


# ── TokenMeter ────────────────────────────────────────────────────────────────

class TokenMeter:
    """
    Per-session token tracking with persistence, budget enforcement, and reporting.

    Thread-safe. Stores session data to ~/.hermes/token_meter/ as JSON files.

    Example:
        meter = TokenMeter()

        # Count an LLM API call
        meter.count_request(
            session_id="sess-001",
            model="MiniMax-Text-01",
            prompt_tokens=500,
            completion_tokens=200,
            cache_create_tokens=100,
            cache_read_tokens=50,
        )

        # Get a report
        print(meter.get_report("sess-001"))

        # Set a token budget
        meter.set_budget("sess-001", budget_tokens=100_000)

        # Budget check
        result = meter.check_budget("sess-001")
        if result["blocked"]:
            print("Budget exceeded!")
    """

    SCHEMA = {
        "name": "hermes_token_meter",
        "description": "Token usage metering and cost tracking for Hermes sessions. "
                       "Tracks input/output/cache tokens per session, estimates USD cost, "
                       "and enforces optional token budgets.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get", "reset", "budget_set", "budget_check", "history"],
                    "description": "Action to perform",
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID. Empty returns all sessions summary.",
                },
                "budget_tokens": {
                    "type": "integer",
                    "description": "Token budget limit for budget_set action.",
                },
            },
            "required": ["action"],
        },
    }

    def __init__(self, storage_dir: str | None = None):
        if storage_dir is None:
            storage_dir = str(Path.home() / ".hermes" / "token_meter")
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        # session_id -> TokenSession
        self._sessions: dict[str, TokenSession] = {}
        # history of session_ids in creation order
        self._history: list[str] = []
        self._load_all()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _session_path(self, session_id: str) -> Path:
        return self._storage_dir / f"{session_id}.json"

    def _load_all(self) -> None:
        """Load all session JSON files from storage directory."""
        try:
            for path in self._storage_dir.glob("*.json"):
                try:
                    data = json.loads(path.read_text())
                    ts = TokenSession(
                        session_id=data["session_id"],
                        model=data.get("model", "unknown"),
                        budget_tokens=data.get("budget_tokens", 0),
                    )
                    ts.started_at = data.get("started_at", ts.started_at)
                    ts.input_tokens = data.get("input_tokens", 0)
                    ts.output_tokens = data.get("output_tokens", 0)
                    ts.cache_creation_tokens = data.get("cache_creation_tokens", 0)
                    ts.cache_read_tokens = data.get("cache_read_tokens", 0)
                    ts.total_cost_usd = data.get("total_cost_usd", 0.0)
                    ts.turn_count = data.get("turn_count", 0)
                    ts.warnings_issued = set(data.get("warnings_issued", []))
                    self._sessions[ts.session_id] = ts
                    self._history.append(ts.session_id)
                except Exception:
                    pass
        except Exception:
            pass

    def _persist(self, session: TokenSession) -> None:
        """Write a single session to disk."""
        try:
            path = self._session_path(session.session_id)
            path.write_text(json.dumps(session.to_dict(), indent=2))
        except Exception:
            pass

    def _load(self, session_id: str) -> TokenSession | None:
        """Load a single session from disk."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            ts = TokenSession(
                session_id=data["session_id"],
                model=data.get("model", "unknown"),
                budget_tokens=data.get("budget_tokens", 0),
            )
            ts.started_at = data.get("started_at", ts.started_at)
            ts.input_tokens = data.get("input_tokens", 0)
            ts.output_tokens = data.get("output_tokens", 0)
            ts.cache_creation_tokens = data.get("cache_creation_tokens", 0)
            ts.cache_read_tokens = data.get("cache_read_tokens", 0)
            ts.total_cost_usd = data.get("total_cost_usd", 0.0)
            ts.turn_count = data.get("turn_count", 0)
            ts.warnings_issued = set(data.get("warnings_issued", []))
            return ts
        except Exception:
            return None

    # ── Core Counting ─────────────────────────────────────────────────────────

    def count_request(
        self,
        session_id: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cache_create_tokens: int = 0,
        cache_read_tokens: int = 0,
        prompt_text: str = "",
        completion_text: str = "",
        save: bool = True,
    ) -> dict:
        """
        Record a single LLM API request's token usage.

        If prompt/completion texts are provided (and token counts are 0),
        they are used to estimate token counts via tiktoken.

        Args:
            session_id: Unique session identifier
            model: Model name (e.g. "MiniMax-Text-01")
            prompt_tokens: Tokens in the prompt/input (0 = use text estimation)
            completion_tokens: Tokens in the completion/output (0 = use text estimation)
            cache_create_tokens: Tokens in cache creation phase
            cache_read_tokens: Tokens read from cache
            prompt_text: Raw prompt string for tiktoken counting
            completion_text: Raw completion string for tiktoken counting
            save: Whether to persist to disk immediately

        Returns:
            Updated session dict
        """
        with self._lock:
            # Resolve model for pricing
            resolved_model = self._resolve_model(model)
            if resolved_model == "unknown" and model != "unknown":
                # Try exact match in pricing keys
                if model in PRICING:
                    resolved_model = model

            ts = self._sessions.get(session_id)
            if ts is None:
                ts = TokenSession(session_id=session_id, model=resolved_model)
                self._sessions[session_id] = ts
                if session_id not in self._history:
                    self._history.append(session_id)

            # Estimate from text if counts not provided
            if prompt_tokens == 0 and prompt_text:
                prompt_tokens = count_tokens(prompt_text)
            if completion_tokens == 0 and completion_text:
                completion_tokens = count_tokens(completion_text)

            ts.input_tokens += prompt_tokens
            ts.output_tokens += completion_tokens
            ts.cache_creation_tokens += cache_create_tokens
            ts.cache_read_tokens += cache_read_tokens
            ts.turn_count += 1

            # Update model if changed
            if resolved_model != "unknown":
                ts.model = resolved_model

            ts.estimate_cost(resolved_model)
            self._persist(ts)

            return ts.to_dict()

    def _resolve_model(self, model: str) -> str:
        """Resolve model to known pricing key."""
        if model in PRICING:
            return model
        # Try partial matches
        model_lower = model.lower()
        for key in PRICING:
            if key.lower() in model_lower or model_lower in key.lower():
                return key
        return "unknown"

    # ── Budget ────────────────────────────────────────────────────────────────

    def set_budget(self, session_id: str, budget_tokens: int) -> dict:
        """Set a token budget for a session (0 = no budget)."""
        with self._lock:
            ts = self._sessions.get(session_id)
            if ts is None:
                ts = TokenSession(session_id=session_id)
                self._sessions[session_id] = ts
                if session_id not in self._history:
                    self._history.append(session_id)

            ts.budget_tokens = budget_tokens
            self._persist(ts)
            return {
                "session_id": session_id,
                "budget_tokens": budget_tokens,
                "current_tokens": ts.total_tokens,
                "current_pct": round(ts.budget_pct, 2),
            }

    def check_budget(self, session_id: str) -> dict:
        """
        Check if session is within budget. Returns warning at 80%, blocks at 100%.

        Budget enforcement:
        - warning: 80-99% of budget consumed
        - blocked: >= 100% of budget consumed

        Returns:
            Dict with blocked (bool), warning (bool), pct (float), message (str)
        """
        with self._lock:
            ts = self._sessions.get(session_id)
            if ts is None:
                return {
                    "session_id": session_id,
                    "blocked": False,
                    "warning": False,
                    "message": "Session not found - no budget set.",
                }
            if ts.budget_tokens <= 0:
                return {
                    "session_id": session_id,
                    "blocked": False,
                    "warning": False,
                    "current_tokens": ts.total_tokens,
                    "message": "No budget set.",
                }

            pct = ts.budget_pct

            if pct >= 100:
                return {
                    "session_id": session_id,
                    "blocked": True,
                    "warning": False,
                    "pct": round(pct, 2),
                    "current_tokens": ts.total_tokens,
                    "budget_tokens": ts.budget_tokens,
                    "message": f"BUDGET EXCEEDED: {ts.total_tokens}/{ts.budget_tokens} tokens ({pct:.1f}%)",
                }

            warning_pct = 80
            if pct >= warning_pct and warning_pct not in ts.warnings_issued:
                ts.warnings_issued.add(warning_pct)
                self._persist(ts)
                return {
                    "session_id": session_id,
                    "blocked": False,
                    "warning": True,
                    "pct": round(pct, 2),
                    "current_tokens": ts.total_tokens,
                    "budget_tokens": ts.budget_tokens,
                    "message": f"WARNING: {ts.total_tokens}/{ts.budget_tokens} tokens ({pct:.1f}% of budget consumed)",
                }

            return {
                "session_id": session_id,
                "blocked": False,
                "warning": False,
                "pct": round(pct, 2),
                "current_tokens": ts.total_tokens,
                "budget_tokens": ts.budget_tokens,
                "message": f"Within budget: {ts.total_tokens}/{ts.budget_tokens} tokens ({pct:.1f}%)",
            }

    # ── Reports ───────────────────────────────────────────────────────────────

    def get_report(self, session_id: str = "") -> str:
        """
        Get token report for a session or all sessions.

        Args:
            session_id: Session ID. Empty = all sessions summary.

        Returns:
            JSON string with token breakdown and cost estimate.
        """
        with self._lock:
            if session_id:
                ts = self._sessions.get(session_id)
                if ts is None:
                    # Try loading from disk
                    ts = self._load(session_id)
                if ts is None:
                    return json.dumps({
                        "error": "session_not_found",
                        "session_id": session_id,
                        "message": f"No data for session '{session_id}'. "
                                  "Has the session made any LLM calls yet?",
                    })

                p = PRICING.get(ts.model, PRICING["unknown"])
                breakdown = {
                    "input_tokens_usd": round(ts.input_tokens * p["input"] / 1_000_000, 8),
                    "output_tokens_usd": round(ts.output_tokens * p["output"] / 1_000_000, 8),
                    "cache_create_usd": round(ts.cache_creation_tokens * p["cache_create"] / 1_000_000, 8),
                    "cache_read_usd": round(ts.cache_read_tokens * p["cache_read"] / 1_000_000, 8),
                }
                return json.dumps({
                    "session_id": ts.session_id,
                    "model": ts.model,
                    "started_at": ts.started_at,
                    "turn_count": ts.turn_count,
                    "tokens": {
                        "input": ts.input_tokens,
                        "output": ts.output_tokens,
                        "cache_creation": ts.cache_creation_tokens,
                        "cache_read": ts.cache_read_tokens,
                        "total": ts.total_tokens,
                    },
                    "cost_usd": round(ts.total_cost_usd, 6),
                    "cost_breakdown": breakdown,
                    "pricing": {
                        "input_per_1m": p["input"],
                        "output_per_1m": p["output"],
                        "cache_create_per_1m": p["cache_create"],
                        "cache_read_per_1m": p["cache_read"],
                    },
                    "budget": {
                        "tokens": ts.budget_tokens,
                        "pct": round(ts.budget_pct, 2),
                    } if ts.budget_tokens > 0 else None,
                }, indent=2)

            # All sessions
            sessions_data = []
            total_input = total_output = total_cache_cr = total_cache_rd = total_cost = 0

            for sid in self._history:
                ts = self._sessions.get(sid)
                if ts is None:
                    continue
                sessions_data.append(ts.to_dict())
                total_input += ts.input_tokens
                total_output += ts.output_tokens
                total_cache_cr += ts.cache_creation_tokens
                total_cache_rd += ts.cache_read_tokens
                total_cost += ts.total_cost_usd

            return json.dumps({
                "total_sessions": len(sessions_data),
                "total_tokens": total_input + total_output,
                "total_cost_usd": round(total_cost, 6),
                "aggregate": {
                    "input_tokens": total_input,
                    "output_tokens": total_output,
                    "cache_creation_tokens": total_cache_cr,
                    "cache_read_tokens": total_cache_rd,
                },
                "sessions": sessions_data,
            }, indent=2)

    def get_history(self, limit: int = 20) -> str:
        """Get session history (most recent first)."""
        with self._lock:
            recent = []
            for sid in reversed(self._history[-limit:]):
                ts = self._sessions.get(sid)
                if ts:
                    recent.append(ts.to_dict())
            return json.dumps({"history": recent, "count": len(recent)}, indent=2)

    # ── Reset ─────────────────────────────────────────────────────────────────

    def reset(self, session_id: str = "") -> str:
        """
        Reset token counters for a session (deletes from memory + disk).
        If session_id is empty, resets ALL sessions.
        """
        with self._lock:
            if not session_id:
                # Reset all
                for sid in list(self._sessions.keys()):
                    try:
                        self._session_path(sid).unlink(missing_ok=True)
                    except Exception:
                        pass
                self._sessions.clear()
                self._history.clear()
                return json.dumps({"success": True, "reset": "all_sessions"})

            if session_id in self._sessions:
                del self._sessions[session_id]
            if session_id in self._history:
                self._history.remove(session_id)
            try:
                self._session_path(session_id).unlink(missing_ok=True)
            except Exception:
                pass
            return json.dumps({"success": True, "reset": session_id})

    # ── MCP Tool Handler ───────────────────────────────────────────────────────

    def handle_mcp(self, action: str, session_id: str = "",
                   budget_tokens: int = 0) -> str:
        """
        MCP tool handler matching HERMES_TOKEN_METER_SCHEMA.

        Actions:
            get       - Get token report (session_id optional)
            reset     - Reset session counters
            budget_set - Set token budget for a session
            budget_check - Check budget status
            history   - Get session history

        Returns:
            JSON string response
        """
        try:
            if action == "get":
                return self.get_report(session_id)
            elif action == "reset":
                return self.reset(session_id)
            elif action == "budget_set":
                if not session_id:
                    return json.dumps({"error": "session_id required for budget_set"})
                return json.dumps(self.set_budget(session_id, budget_tokens))
            elif action == "budget_check":
                if not session_id:
                    return json.dumps({"error": "session_id required for budget_check"})
                return json.dumps(self.check_budget(session_id))
            elif action == "history":
                return self.get_history()
            else:
                return json.dumps({
                    "error": f"unknown_action: {action}",
                    "valid_actions": ["get", "reset", "budget_set", "budget_check", "history"],
                })
        except Exception as e:
            return json.dumps({"error": str(e)})


# ── Convenience wrappers ──────────────────────────────────────────────────────

# Global singleton
_METER: TokenMeter | None = None
_METER_LOCK = threading.Lock()


def get_meter() -> TokenMeter:
    """Get or create the global TokenMeter singleton."""
    global _METER
    if _METER is None:
        with _METER_LOCK:
            if _METER is None:
                _METER = TokenMeter()
    return _METER


def count_turn(
    session_id: str,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cache_create_tokens: int = 0,
    cache_read_tokens: int = 0,
    prompt_text: str = "",
    completion_text: str = "",
) -> dict:
    """
    Convenience function: count a single LLM turn.

    Use this in hermes-mcp-server.py to wrap LLM calls.
    """
    return get_meter().count_request(
        session_id=session_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cache_create_tokens=cache_create_tokens,
        cache_read_tokens=cache_read_tokens,
        prompt_text=prompt_text,
        completion_text=completion_text,
    )


def token_meter_get(session_id: str = "") -> str:
    """MCP tool: get token report for a session or all sessions."""
    return get_meter().handle_mcp(action="get", session_id=session_id)


def token_meter_reset(session_id: str = "") -> str:
    """MCP tool: reset session(s)."""
    return get_meter().handle_mcp(action="reset", session_id=session_id)


def token_meter_budget(session_id: str, budget_tokens: int = 0) -> str:
    """MCP tool: set token budget for a session."""
    return get_meter().handle_mcp(action="budget_set", session_id=session_id, budget_tokens=budget_tokens)


def token_meter_check(session_id: str) -> str:
    """MCP tool: check budget status."""
    return get_meter().handle_mcp(action="budget_check", session_id=session_id)


def token_meter_history(limit: int = 20) -> str:
    """MCP tool: get session history."""
    return get_meter().handle_mcp(action="history")


# ── CLI / Self-test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    meter = TokenMeter()

    print("=== TokenMeter Self-Test ===")

    # Count some turns
    meter.count_request(
        session_id="test-session-001",
        model="MiniMax-Text-01",
        prompt_tokens=512,
        completion_tokens=128,
        cache_create_tokens=256,
        cache_read_tokens=64,
    )

    meter.count_request(
        session_id="test-session-001",
        model="MiniMax-Text-01",
        prompt_tokens=1024,
        completion_tokens=512,
    )

    # Count with text estimation
    meter.count_request(
        session_id="test-session-002",
        model="ollama_chat/gemma3:12b",
        prompt_text="This is a test prompt for the local model." * 20,
        completion_text="This is a generated response from the model." * 10,
    )

    print("\n--- Report for test-session-001 ---")
    print(meter.get_report("test-session-001"))

    print("\n--- Report for test-session-002 ---")
    print(meter.get_report("test-session-002"))

    print("\n--- All sessions ---")
    print(meter.get_report(""))

    # Budget test
    meter.set_budget("test-session-001", budget_tokens=2000)
    print("\n--- Budget check ---")
    print(meter.check_budget("test-session-001"))

    # Count more to trigger warning
    meter.count_request(
        session_id="test-session-001",
        model="MiniMax-Text-01",
        prompt_tokens=800,
        completion_tokens=400,
    )
    print("\n--- Budget check after more usage ---")
    print(meter.check_budget("test-session-001"))

    print("\n--- History ---")
    print(meter.get_history())

    print("\n=== Self-Test Complete ===")