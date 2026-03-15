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
from typing import Any, Optional

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

    def _headers(self, use_service_role: bool = False, extra: dict | None = None) -> dict:
        key = self.service_role_key if use_service_role else self.anon_key
        h = {
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
    def _build_filters(params: dict, eq: dict | None, filters: dict | None) -> dict:
        """Merge eq shortcuts and raw filter params into query params."""
        p = dict(params)
        for col, val in (eq or {}).items():
            p[col] = f"eq.{val}"
        for col, expr in (filters or {}).items():
            p[col] = expr  # e.g. {"age": "gte.18"}
        return p

    # ------------------------------------------------------------------ #
    # PostgREST CRUD
    # ------------------------------------------------------------------ #

    async def query(
        self,
        table: str,
        select: str = "*",
        eq: dict | None = None,
        filters: dict | None = None,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
        use_service_role: bool = True,
    ) -> list[dict]:
        """SELECT rows from a table."""
        params: dict[str, Any] = {
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
        resp.raise_for_status()
        return resp.json()

    async def insert(
        self,
        table: str,
        data: dict | list[dict],
        upsert: bool = False,
        on_conflict: str = "",
        use_service_role: bool = True,
    ) -> list[dict]:
        """INSERT (or UPSERT) rows."""
        prefer = "resolution=merge-duplicates,return=representation" if upsert else "return=representation"
        if upsert and on_conflict:
            params = {"on_conflict": on_conflict}
        else:
            params = {}
        resp = await self._http.post(
            self._rest_url(table),
            headers=self._headers(use_service_role, {"Prefer": prefer}),
            json=data,
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    async def update(
        self,
        table: str,
        data: dict,
        eq: dict,
        use_service_role: bool = True,
    ) -> list[dict]:
        """UPDATE rows matching eq filter."""
        params = {col: f"eq.{val}" for col, val in eq.items()}
        resp = await self._http.patch(
            self._rest_url(table),
            headers=self._headers(use_service_role),
            json=data,
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    async def delete(
        self,
        table: str,
        eq: dict,
        use_service_role: bool = True,
    ) -> list[dict]:
        """DELETE rows matching eq filter."""
        params = {col: f"eq.{val}" for col, val in eq.items()}
        resp = await self._http.delete(
            self._rest_url(table),
            headers=self._headers(use_service_role),
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    # RPC (Postgres functions / Edge Functions)
    # ------------------------------------------------------------------ #

    async def rpc(
        self,
        function_name: str,
        params: dict | None = None,
        use_service_role: bool = True,
    ) -> Any:
        """Call a Postgres function via PostgREST /rpc/<name>."""
        resp = await self._http.post(
            f"{self.url}/rest/v1/rpc/{function_name}",
            headers=self._headers(use_service_role),
            json=params or {},
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    # Auth
    # ------------------------------------------------------------------ #

    async def auth_sign_in(
        self,
        email: str,
        password: str,
    ) -> dict:
        """Sign in a user with email+password. Returns session dict."""
        resp = await self._http.post(
            f"{self.url}/auth/v1/token?grant_type=password",
            headers={"apikey": self.anon_key, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )
        resp.raise_for_status()
        return resp.json()

    async def auth_create_user(
        self,
        email: str,
        password: str,
        user_metadata: dict | None = None,
    ) -> dict:
        """Create a user via the admin API (service_role only)."""
        resp = await self._http.post(
            f"{self.url}/auth/v1/admin/users",
            headers=self._headers(use_service_role=True),
            json={"email": email, "password": password,
                  "user_metadata": user_metadata or {},
                  "email_confirm": True},
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    # Storage
    # ------------------------------------------------------------------ #

    async def storage_list(
        self,
        bucket: str,
        prefix: str = "",
        limit: int = 100,
    ) -> list[dict]:
        """List objects in a storage bucket."""
        resp = await self._http.post(
            f"{self.url}/storage/v1/object/list/{bucket}",
            headers=self._headers(use_service_role=True),
            json={"prefix": prefix, "limit": limit, "offset": 0},
        )
        resp.raise_for_status()
        return resp.json()

    async def storage_upload(
        self,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        upsert: bool = True,
    ) -> dict:
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
        resp.raise_for_status()
        return resp.json()

    def storage_public_url(self, bucket: str, path: str) -> str:
        """Return the public URL for a storage object."""
        return f"{self.url}/storage/v1/object/public/{bucket}/{path}"

    # ------------------------------------------------------------------ #
    # Health
    # ------------------------------------------------------------------ #

    async def health_check(self) -> dict:
        """Check Supabase project health. Returns dict with ok/latency_ms."""
        import time
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

    async def close(self) -> None:
        await self._http.aclose()


# ------------------------------------------------------------------ #
# Singleton accessor
# ------------------------------------------------------------------ #

def get_client(
    url: str | None = None,
    anon_key: str | None = None,
    service_role_key: str | None = None,
) -> SupabaseClient:
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
            "SUPABASE_URL is not set. "
            "Add it to your .env file: SUPABASE_URL=https://<project>.supabase.co"
        )
    if not _anon:
        raise ValueError(
            "SUPABASE_ANON_KEY is not set. "
            "Find it in: Supabase Dashboard → Project Settings → API."
        )

    _INSTANCE = SupabaseClient(_url, _anon, _svc)
    logger.info("SupabaseClient initialised: %s", _url)
    return _INSTANCE


def is_configured() -> bool:
    """Return True if Supabase env vars are present."""
    return bool(os.getenv("SUPABASE_URL")) and bool(os.getenv("SUPABASE_ANON_KEY"))
