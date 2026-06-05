"""Database Agent — natural language to SQL for Supabase.

Provides a safe, read-only natural language query interface to Supabase.
Only SELECT queries are allowed. Results are formatted as Telegram HTML.

Usage:
    db = DatabaseAgent()
    result = await db.execute_nl_query(
        "How many bookings did I get this week?",
        user_id="bashara"
    )
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

# ── Allowed tables (safe read-only list) ──────────────────────────────────────

_ALLOWED_TABLES = {"bookings", "guests", "rooms", "reviews", "payments"}

# ── Prompt template for NL → SQL ───────────────────────────────────────────────


def _build_nl_to_sql_prompt(nl_query: str, table_schemas: str) -> str:
    return f"""
You are a SQL expert for a homestay booking system (Supabase/PostgreSQL).

Convert the natural language query to a safe SQL SELECT statement.

Rules:
- Only SELECT queries — no INSERT, UPDATE, DELETE, DROP, TRUNCATE, or ALTER
- Always add LIMIT 20 to prevent large result sets
- Use proper SQL escaping — never concatenate user input directly
- Only query these tables: {", ".join(_ALLOWED_TABLES)}
- Table schemas:
{table_schemas}

Natural language query: {nl_query}

Output ONLY the SQL query (no markdown, no explanation).
"""


_TABLE_SCHEMAS = """
bookings: id, guest_name, guest_email, guest_phone, room_id, check_in_date, check_out_date, total_price, status, payment_status, created_at, updated_at
guests: id, name, email, phone, nationality, created_at
rooms: id, name, description, capacity, price_per_night, created_at
reviews: id, booking_id, rating, comment, created_at
payments: id, booking_id, amount, method, status, created_at
"""


async def _nl_to_sql(nl_query: str) -> str:
    """Convert natural language query to SQL using LLM."""
    try:
        import litellm

        prompt = _build_nl_to_sql_prompt(nl_query, _TABLE_SCHEMAS)
        resp = await litellm.acompletion(
            model=os.getenv("DEFAULT_MODEL", "minimax-coding-plan/MiniMax-M3"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=256,
        )
        sql = resp.choices[0].message.content or ""
        # Strip markdown formatting
        sql = re.sub(r"```(?:sql)?\n?", "", sql).strip()
        return sql
    except Exception as e:
        logger.warning("[DatabaseAgent] NL→SQL conversion failed: %s", e)
        return ""


def _is_safe_sql(sql: str) -> bool:
    """Validate that SQL is a read-only SELECT statement."""
    sql_upper = sql.upper()
    normalized = re.sub(r"\s+", " ", sql_upper).strip()

    # Must start with SELECT
    if not normalized.startswith("SELECT"):
        return False

    # Block dangerous keywords
    blocked = {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "TRUNCATE",
        "ALTER",
        "CREATE",
        "GRANT",
        "REVOKE",
        "EXEC",
        "EXECUTE",
    }
    for kw in blocked:
        # Check as whole word (with word boundaries)
        pattern = rf"\b{kw}\b"
        if re.search(pattern, normalized):
            return False

    return True


class DatabaseAgent:
    """
    Natural language to SQL interface for Supabase.

    Converts a NL query to SQL using LLM, validates the SQL is a
    safe SELECT statement, executes it against Supabase, and returns
    results formatted as Telegram HTML.
    """

    async def execute_nl_query(self, nl_query: str, user_id: str) -> str:
        """
        Execute a natural language query against Supabase (read-only).

        Args:
            nl_query: Natural language question about bookings/guests/revenue
            user_id: The user asking the query (logged for audit)

        Returns:
            Telegram HTML formatted result string.
        """
        sql = await _nl_to_sql(nl_query)
        if not sql:
            return "⚠️ Could not convert your query to SQL. Please try rephrasing."

        if not _is_safe_sql(sql):
            logger.warning(
                "[DatabaseAgent] Unsafe SQL blocked for user %s: %s",
                user_id,
                sql[:100],
            )
            return "⚠️ Query blocked — only SELECT queries are allowed."

        try:
            from tools.supabase_client import get_client

            client = get_client()
            if not client:
                return "⚠️ Supabase client not available. Check SUPABASE_URL and SUPABASE_KEY."

            # Extract table name for validation
            table_match = re.search(
                r"FROM\s+(\w+)",
                sql,
                re.IGNORECASE,
            )
            if table_match:
                table_name = table_match.group(1).lower()
                if table_name not in _ALLOWED_TABLES:
                    return f"⚠️ Querying table '{table_name}' is not allowed."

            # Execute
            result = client.query(sql).execute()
            rows = result.data if result and result.data else []

            if not rows:
                return f"🔍 <b>Query</b>: {nl_query}\n\nNo results found."

            return self._format_results_html(nl_query, rows)

        except Exception as e:
            logger.warning("[DatabaseAgent] query execution failed for user %s: %s", user_id, e)
            return f"⚠️ Query failed: {e}"

    def _format_results_html(self, nl_query: str, rows: list[dict[str, Any]]) -> str:
        """Format query results as Telegram HTML table."""
        if not rows:
            return f"🔍 <b>Query</b>: {nl_query}\n\nNo results."

        lines = [f"🔍 <b>Query</b>: {nl_query}\n"]
        lines.append(f"📊 <b>{len(rows)} result(s)</b>\n")

        # Build a simple HTML table
        headers = list(rows[0].keys())
        # Show first 6 columns to avoid huge messages
        visible_headers = headers[:6]

        # Header row
        header_line = "<b>" + " | ".join(visible_headers) + "</b>"
        lines.append(header_line)
        lines.append("—" * len(header_line))

        # Data rows (max 10 rows)
        for row in rows[:10]:
            cells = [str(row.get(h, ""))[:30] for h in visible_headers]
            lines.append(" | ".join(cells))

        if len(rows) > 10:
            lines.append(f"\n<i>…and {len(rows) - 10} more rows</i>")

        return "\n".join(lines)
