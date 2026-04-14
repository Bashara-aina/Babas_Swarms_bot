"""tools/supabase_client.py — Async Supabase REST client for the bot.

Provides a thin async wrapper around the Supabase PostgREST + Auth + Storage
APIs using httpx (already a transitive dep via litellm/aiohttp). No extra
installation required.

Usage:
    from tools.supabase_client import SupabaseClient, get_client

    db = get_client()  # uses SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY from env
    rows = await db.query("bookings", select="id,status", eq={"user_id": uid})

Env vars required:
    SUPABASE_URL              e.g. https://xyzxyz.supabase.co
    SUPABASE_ANON_KEY         public anon key
    SUPABASE_SERVICE_ROLE_KEY service role key (bypasses RLS, for bot-internal ops)
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

try:
    import httpx

    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)

_INSTANCE: Optional["SupabaseClient"] = None


class SupabaseClient:
    """Async Supabase REST client (PostgREST v2, Auth v1, Storage v1)."""

    def __init__(
        self,
        url: str,
        anon_key: str,
        service_role_key: str = "",
    ) -> None:
        if not _HTTPX_AVAILABLE:
            raise ImportError("httpx is required for SupabaseClient. Run: pip install httpx")
        self.url = url.rstrip("/")
        self.anon_key = anon_key
        self.service_role_key = service_role_key or anon_key
        self._http = httpx.AsyncClient(timeout=20.0)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _rest_url(self, table: str) -> str:
        return f"{self.url}/rest/v1/{table}"

    def _headers(
        self,
        use_service_role: bool = False,
        extra: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        key = self.service_role_key if use_service_role else self.anon_key
        h: Dict[str, str] = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "return=representation",
        }
        if extra:
            h.update(extra)
        return h

    @staticmethod
    def _raise_for_status_with_detail(resp: Any) -> None:
        """Raise HTTPStatusError with Supabase JSON/body detail when available."""
        if resp.status_code < 400:
            return

        detail = ""
        try:
            payload = resp.json()
            if isinstance(payload, dict):
                detail = payload.get("message") or payload.get("error_description") or payload.get("error") or ""
            else:
                detail = str(payload)
        except Exception:
            try:
                detail = (resp.text or "").strip()
            except Exception:
                detail = ""

        try:
            resp.raise_for_status()
        except Exception as e:
            if detail:
                raise RuntimeError(f"Supabase HTTP {resp.status_code}: {detail}") from e
            raise

    @staticmethod
    def _build_filters(
        params: Dict[str, Any],
        eq: Optional[Dict[str, Any]],
        filters: Optional[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Merge eq shortcuts and raw filter params into query params."""
        p = dict(params)
        for col, val in (eq or {}).items():
            p[col] = f"eq.{val}"
        for col, expr in (filters or {}).items():
            p[col] = expr
        return p

    # ------------------------------------------------------------------ #
    # PostgREST CRUD
    # ------------------------------------------------------------------ #

    async def query(
        self,
        table: str,
        select: str = "*",
        eq: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, str]] = None,
        order: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        use_service_role: bool = True,
    ) -> List[Dict[str, Any]]:
        """SELECT rows from a table."""
        params: Dict[str, Any] = {
            "select": select,
            "limit": limit,
            "offset": offset,
        }
        if order:
            params["order"] = order
        params = self._build_filters(params, eq, filters)

        resp = await self._http.get(
            self._rest_url(table),
            headers=self._headers(use_service_role),
            params=params,
        )
        self._raise_for_status_with_detail(resp)
        return resp.json()  # type: ignore[return-value]

    async def insert(
        self,
        table: str,
        data: Any,
        upsert: bool = False,
        on_conflict: str = "",
        use_service_role: bool = True,
    ) -> List[Dict[str, Any]]:
        """INSERT (or UPSERT) rows."""
        prefer = "resolution=merge-duplicates,return=representation" if upsert else "return=representation"
        params: Dict[str, str] = {}
        if upsert and on_conflict:
            params["on_conflict"] = on_conflict
        resp = await self._http.post(
            self._rest_url(table),
            headers=self._headers(use_service_role, {"Prefer": prefer}),
            json=data,
            params=params,
        )
        self._raise_for_status_with_detail(resp)
        return resp.json()  # type: ignore[return-value]

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        eq: Dict[str, Any],
        use_service_role: bool = True,
    ) -> List[Dict[str, Any]]:
        """UPDATE rows matching eq filter."""
        params = {col: f"eq.{val}" for col, val in eq.items()}
        resp = await self._http.patch(
            self._rest_url(table),
            headers=self._headers(use_service_role),
            json=data,
            params=params,
        )
        self._raise_for_status_with_detail(resp)
        return resp.json()  # type: ignore[return-value]

    async def delete(
        self,
        table: str,
        eq: Dict[str, Any],
        use_service_role: bool = True,
    ) -> List[Dict[str, Any]]:
        """DELETE rows matching eq filter."""
        params = {col: f"eq.{val}" for col, val in eq.items()}
        resp = await self._http.delete(
            self._rest_url(table),
            headers=self._headers(use_service_role),
            params=params,
        )
        self._raise_for_status_with_detail(resp)
        return resp.json()  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # RPC
    # ------------------------------------------------------------------ #

    async def rpc(
        self,
        function_name: str,
        params: Optional[Dict[str, Any]] = None,
        use_service_role: bool = True,
    ) -> Any:
        """Call a Postgres function via PostgREST /rpc/<name>."""
        resp = await self._http.post(
            f"{self.url}/rest/v1/rpc/{function_name}",
            headers=self._headers(use_service_role),
            json=params or {},
        )
        self._raise_for_status_with_detail(resp)
        return resp.json()

    # ------------------------------------------------------------------ #
    # Auth
    # ------------------------------------------------------------------ #

    async def auth_sign_in(
        self,
        email: str,
        password: str,
    ) -> Dict[str, Any]:
        """Sign in a user with email+password. Returns session dict."""
        resp = await self._http.post(
            f"{self.url}/auth/v1/token?grant_type=password",
            headers={"apikey": self.anon_key, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )
        self._raise_for_status_with_detail(resp)
        return resp.json()  # type: ignore[return-value]

    async def auth_create_user(
        self,
        email: str,
        password: str,
        user_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a user via the admin API (service_role only)."""
        resp = await self._http.post(
            f"{self.url}/auth/v1/admin/users",
            headers=self._headers(use_service_role=True),
            json={
                "email": email,
                "password": password,
                "user_metadata": user_metadata or {},
                "email_confirm": True,
            },
        )
        self._raise_for_status_with_detail(resp)
        return resp.json()  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # Storage
    # ------------------------------------------------------------------ #

    async def storage_list(
        self,
        bucket: str,
        prefix: str = "",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List objects in a storage bucket."""
        resp = await self._http.post(
            f"{self.url}/storage/v1/object/list/{bucket}",
            headers=self._headers(use_service_role=True),
            json={"prefix": prefix, "limit": limit, "offset": 0},
        )
        self._raise_for_status_with_detail(resp)
        return resp.json()  # type: ignore[return-value]

    async def storage_upload(
        self,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        upsert: bool = True,
    ) -> Dict[str, Any]:
        """Upload a file to Supabase Storage."""
        resp = await self._http.post(
            f"{self.url}/storage/v1/object/{bucket}/{path}",
            headers={
                **self._headers(use_service_role=True),
                "Content-Type": content_type,
                "x-upsert": "true" if upsert else "false",
            },
            content=content,
        )
        self._raise_for_status_with_detail(resp)
        return resp.json()  # type: ignore[return-value]

    def storage_public_url(self, bucket: str, path: str) -> str:
        """Return the public URL for a storage object."""
        return f"{self.url}/storage/v1/object/public/{bucket}/{path}"

    # ------------------------------------------------------------------ #
    # Health
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # Schema introspection (one-time bootstrap for rumahlabuh skill)
    # ------------------------------------------------------------------ #

    async def introspect_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        """Read table/column definitions from PostgREST OpenAPI spec.

        Returns: {table_name: [{column, type, nullable}]}
        Requires service_role key for full visibility.
        """
        resp = await self._http.get(
            f"{self.url}/rest/v1/",
            headers=self._headers(use_service_role=True),
            timeout=15.0,
        )
        self._raise_for_status_with_detail(resp)
        spec = resp.json()

        definitions = spec.get("definitions", {}) if isinstance(spec, dict) else {}
        schema: Dict[str, List[Dict[str, Any]]] = {}

        for table_name, defn in definitions.items():
            if not isinstance(defn, dict):
                continue
            props = defn.get("properties", {})
            required = defn.get("required", [])
            columns: List[Dict[str, Any]] = []
            for col, col_def in props.items():
                columns.append(
                    {
                        "column": col,
                        "type": col_def.get("type", col_def.get("format", "unknown")),
                        "nullable": col not in required,
                        "description": col_def.get("description", ""),
                    }
                )
            schema[table_name] = columns

        return schema

    async def generate_skill_file(self, output_path: str = "skills/rumahlabuh-manager.md") -> str:
        """Introspect schema, pass to LLM, generate a skill markdown file.

        Returns the generated file path.
        """
        from llm_client import call_llm

        schema = await self.introspect_schema()
        if not schema:
            raise RuntimeError("introspect_schema() returned empty — check service_role key and project URL")

        schema_json = _json.dumps(schema, indent=2)[:8000]  # cap for LLM context

        prompt = (
            "You are documenting a Supabase database for an AI assistant called Legion. "
            "The AI needs to understand the database schema of rumahlabuh.com "
            "(a villa/accommodation rental business in Indonesia) to answer queries about it. "
            "Based on the schema below, write a markdown skill file that:\n"
            "1. Lists all tables with column names, types, and what they represent\n"
            "2. Describes common operations: check bookings, get revenue, find guests, update status\n"
            "3. Gives example PostgREST API queries for each common operation\n"
            "4. Notes any important relationships between tables\n\n"
            f"Database schema:\n```json\n{schema_json}\n```\n\n"
            "Format as clean markdown. Start with `# Skill: rumahlabuh.com Business Manager`"
        )

        content = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model="cerebras/qwen-3-235b-a22b",
            temperature=0.2,
            max_tokens=3000,
        )

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.info("[Supabase] Generated skill file: %s", output_path)
        return output_path

    # ------------------------------------------------------------------ #
    # Natural language query interface
    # ------------------------------------------------------------------ #

    async def query_natural(self, nl_query: str) -> str:
        """Convert natural language → PostgREST query → execute → return formatted result.

        Requires the skills/rumahlabuh-manager.md skill to be populated first
        (run /site_health to trigger schema bootstrap if missing).
        """
        import json as _json
        import re
        from llm_client import call_llm
        from pathlib import Path

        # Inject schema context from skill file if available
        skill_path = Path("skills/rumahlabuh-manager.md")
        schema_context = ""
        if skill_path.exists():
            schema_context = skill_path.read_text(encoding="utf-8")[:3000]
        else:
            # Fallback: introspect on demand
            try:
                schema = await self.introspect_schema()
                schema_context = _json.dumps(schema, indent=2)[:2000]
            except Exception:
                schema_context = "(schema not available)"

        prompt = (
            "You are a PostgREST query translator. Convert the user's natural language "
            "query into a PostgREST API call.\n\n"
            f"Database schema:\n{schema_context}\n\n"
            f"User query: {nl_query}\n\n"
            "Output ONLY valid JSON with these fields:\n"
            '{"table": "table_name", "select": "col1,col2", "filters": {"col": "eq.value"}, '
            '"order": "col.desc", "limit": 20}\n'
            "Use PostgREST filter syntax: eq.value, gt.value, lt.value, ilike.*search*\n"
            'If you cannot determine the query, output: {"error": "cannot determine query"}'
        )

        try:
            raw = await call_llm(
                messages=[{"role": "user", "content": prompt}],
                model="groq/llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=300,
            )
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not json_match:
                return f"Could not parse query: {raw[:200]}"
            query_params = _json.loads(json_match.group(0))
        except Exception as exc:
            return f"LLM query generation failed: {exc}"

        if "error" in query_params:
            return f"Query unclear: {query_params['error']}"

        table = query_params.get("table", "")
        if not table:
            return "Could not determine which table to query."

        try:
            rows = await self.query(
                table=table,
                select=query_params.get("select", "*"),
                filters=query_params.get("filters"),
                order=query_params.get("order"),
                limit=int(query_params.get("limit", 20)),
            )
        except Exception as exc:
            return f"Query failed: {exc}"

        if not rows:
            return f"No results found in `{table}` for that query."

        # Format as readable summary
        lines = [f"<b>{table}</b> — {len(rows)} result(s):"]
        for row in rows[:10]:
            row_str = "  " + ", ".join(f"{k}: {v}" for k, v in list(row.items())[:6])
            lines.append(row_str[:200])
        if len(rows) > 10:
            lines.append(f"  ... and {len(rows) - 10} more")
        return "\n".join(lines)

    async def health_check(self) -> Dict[str, Any]:
        """Check Supabase project health. Returns dict with ok/latency_ms."""
        t0 = time.monotonic()
        try:
            resp = await self._http.get(
                f"{self.url}/rest/v1/",
                headers=self._headers(use_service_role=False),
                timeout=5.0,
            )
            ok = resp.status_code < 500
        except Exception as e:
            return {"ok": False, "error": str(e), "latency_ms": None}
        latency = round((time.monotonic() - t0) * 1000)
        return {"ok": ok, "status_code": resp.status_code, "latency_ms": latency}

    async def list_accessible_tables(self) -> List[str]:
        """List table-like resources visible via PostgREST OpenAPI.

        Works with anon key and does not require service_role or custom RPC.
        """
        resp = await self._http.get(
            f"{self.url}/rest/v1/",
            headers=self._headers(use_service_role=False),
            timeout=10.0,
        )
        self._raise_for_status_with_detail(resp)

        payload = resp.json()
        paths = payload.get("paths", {}) if isinstance(payload, dict) else {}
        out: List[str] = []
        for raw in paths.keys():
            if not isinstance(raw, str):
                continue
            name = raw.lstrip("/")
            if not name or name.startswith("rpc/"):
                continue
            if "/" in name:
                name = name.split("/", 1)[0]
            if name and name not in out:
                out.append(name)
        return sorted(out)

    async def close(self) -> None:
        await self._http.aclose()


# ------------------------------------------------------------------ #
# Singleton accessor
# ------------------------------------------------------------------ #


def get_client(
    url: Optional[str] = None,
    anon_key: Optional[str] = None,
    service_role_key: Optional[str] = None,
) -> "SupabaseClient":
    """Return a shared SupabaseClient instance, reading from env if not provided.

    Raises ValueError if SUPABASE_URL or SUPABASE_ANON_KEY are not set.
    """
    global _INSTANCE
    if _INSTANCE is not None and url is None:
        return _INSTANCE

    _url = url or os.getenv("SUPABASE_URL", "")
    _anon = anon_key or os.getenv("SUPABASE_ANON_KEY", "")
    _svc = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    if not _url:
        raise ValueError(
            "SUPABASE_URL is not set. Add it to your .env file: SUPABASE_URL=https://<project>.supabase.co"
        )
    if not _anon:
        raise ValueError("SUPABASE_ANON_KEY is not set. Find it in: Supabase Dashboard → Project Settings → API.")

    _INSTANCE = SupabaseClient(_url, _anon, _svc)
    logger.info("SupabaseClient initialised: %s", _url)
    return _INSTANCE


def is_configured() -> bool:
    """Return True if Supabase env vars are present."""
    return bool(os.getenv("SUPABASE_URL")) and bool(os.getenv("SUPABASE_ANON_KEY"))
