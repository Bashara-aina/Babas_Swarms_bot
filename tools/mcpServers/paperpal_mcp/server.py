"""PaperPal MCP Server — search and discover academic papers.

Provides unified access to three academic paper sources:
- arXiv (search + fetch details via arxiv-txt.org)
- HuggingFace Papers (semantic search)
- Semantic Scholar (search with citations)

Original upstream: https://github.com/mila-iqia/paperpal (MIT License)
Enhanced with additional tools and fallbacks.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from typing import Any
from pydantic import BaseModel


# ── MCP Protocol Helpers ──────────────────────────────────────────────

def mcp_log(msg: str) -> None:
    print(json.dumps({"jsonrpc": "2.0", "method": "log", "params": {"message": msg}}), file=sys.stderr, flush=True)


def respond(id: int | None, result: Any = None, error: dict | None = None) -> None:
    body: dict[str, Any] = {"jsonrpc": "2.0"}
    if id is not None:
        body["id"] = id
    if error:
        body["error"] = error
    else:
        body["result"] = result
    print(json.dumps(body), flush=True)


TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "search_arxiv_papers",
        "description": "Search for papers on arXiv by query. Returns titles, authors, abstracts, and arXiv IDs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (e.g. 'attention is all you need' or 'reinforcement learning robotics')"},
                "max_results": {"type": "integer", "description": "Max results (1-50, default 10)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_paper_details_from_arxiv",
        "description": "Get detailed information about specific arXiv papers by their IDs, including BibTeX. Use after search_arxiv_papers to get full details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "arxiv_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "arXiv paper IDs (e.g. ['2503.01469', '2401.12345'])"
                }
            },
            "required": ["arxiv_ids"]
        }
    },
    {
        "name": "semantic_search_papers_on_huggingface",
        "description": "Search for papers on HuggingFace Papers using semantic search. Good for finding trending ML papers with community upvote signals.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (keywords or natural language)"},
                "top_n": {"type": "integer", "description": "Number of results (default 10)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_semantic_scholar",
        "description": "Search for papers on Semantic Scholar. Returns structured metadata including citation info, TLDR summaries, and author details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default 10)"}
            },
            "required": ["query"]
        }
    },
]


# ── Data Models ───────────────────────────────────────────────────────

class Paper(BaseModel):
    title: str = ""
    summary: str = ""
    authors: list[str] = []
    arxiv_id: str = ""
    url: str = ""
    source: str = ""
    extra: dict[str, Any] = {}

    def __str__(self) -> str:
        parts = [f"Title: {self.title or 'Unknown'}"]
        if self.authors:
            parts.append(f"Authors: {', '.join(self.authors[:5])}{' et al.' if len(self.authors) > 5 else ''}")
        if self.summary:
            parts.append(f"Abstract: {self.summary[:300]}...")
        if self.url:
            parts.append(f"URL: {self.url}")
        if self.arxiv_id:
            parts.append(f"arXiv: {self.arxiv_id}")
        if self.source:
            parts.append(f"Source: {self.source}")
        if self.extra:
            for k, v in self.extra.items():
                parts.append(f"{k}: {v}")
        return "\n".join(parts)


def _format_papers(papers: list[Paper | dict]) -> str:
    formatted = []
    for i, p in enumerate(papers, 1):
        if isinstance(p, dict):
            p = Paper(**{k: v for k, v in p.items() if k in Paper.model_fields}, extra={k: v for k, v in p.items() if k not in Paper.model_fields})
        formatted.append(f"[{i}] {str(p)}")
    return "\n\n---\n\n".join(formatted) if formatted else "No papers found."


# ── arXiv API ─────────────────────────────────────────────────────────

def _search_arxiv_api(query: str, max_results: int = 10) -> list[dict]:
    """Search arXiv via the official arXiv API."""
    url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&max_results={max_results}&sortBy=relevance"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperPal/1.0 (MCP)", "Accept": "application/xml"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read().decode("utf-8")
        root = ET.fromstring(data)
        ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        papers = []
        for entry in root.findall("a:entry", ns):
            title_el = entry.find("a:title", ns)
            summary_el = entry.find("a:summary", ns)
            id_el = entry.find("a:id", ns)
            published_el = entry.find("a:published", ns)
            authors_el = entry.findall("a:author", ns)

            title = title_el.text.strip().replace("\n", " ") if title_el is not None else ""
            summary = summary_el.text.strip().replace("\n", " ") if summary_el is not None else ""
            raw_id = id_el.text.split("/abs/")[-1] if id_el is not None else ""
            published = published_el.text[:10] if published_el is not None else ""
            authors = [au.find("a:name", ns).text for au in authors_el if au.find("a:name", ns) is not None]

            # Extract categories
            cats = entry.findall("arxiv:primary_category", ns)
            category = cats[0].attrib.get("term", "") if cats else ""

            papers.append({
                "title": title,
                "summary": summary,
                "authors": authors,
                "arxiv_id": raw_id,
                "url": f"https://arxiv.org/abs/{raw_id}",
                "published": published,
                "category": category,
                "source": "arXiv"
            })
        return papers
    except Exception as e:
        mcp_log(f"arXiv API search failed: {e}")
        return []


def _fetch_arxiv_details(arxiv_ids: list[str]) -> list[dict]:
    """Fetch paper details from arxiv-txt.org, with arXiv API fallback."""
    papers = []

    for aid in arxiv_ids:
        aid = aid.strip().replace("arXiv:", "").replace("http://arxiv.org/abs/", "").replace("https://arxiv.org/abs/", "")
        # Try arxiv-txt.org first (rich format with BibTeX)
        try:
            url = f"https://www.arxiv-txt.org/raw/abs/{aid}"
            req = urllib.request.Request(url, headers={"User-Agent": "PaperPal/1.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            raw = resp.text
            paper = _parse_arxiv_txt(raw, aid)
            papers.append(paper)
        except Exception:
            # Fallback: arXiv API
            try:
                url = f"http://export.arxiv.org/api/query?id_list={aid}"
                req = urllib.request.Request(url, headers={"User-Agent": "PaperPal/1.0"})
                resp = urllib.request.urlopen(req, timeout=10)
                data = resp.read().decode("utf-8")
                root = ET.fromstring(data)
                ns = {"a": "http://www.w3.org/2005/Atom"}
                entry = root.find("a:entry", ns)
                if entry is not None:
                    title = entry.find("a:title", ns)
                    summary = entry.find("a:summary", ns)
                    authors = [au.find("a:name", ns).text for au in entry.findall("a:author", ns) if au.find("a:name", ns) is not None]
                    papers.append({
                        "title": title.text.strip().replace("\n", " ") if title is not None else "",
                        "summary": summary.text.strip().replace("\n", " ") if summary is not None else "",
                        "authors": authors,
                        "arxiv_id": aid,
                        "url": f"https://arxiv.org/abs/{aid}",
                        "source": "arXiv API (fallback)"
                    })
                else:
                    papers.append({"title": f"Paper {aid} not found", "arxiv_id": aid, "error": "not found", "source": "arXiv"})
            except Exception as e:
                papers.append({"title": f"Error fetching {aid}", "arxiv_id": aid, "error": str(e), "source": "arXiv"})

    return papers


def _parse_arxiv_txt(raw: str, arxiv_id: str) -> dict:
    """Parse arxiv-txt.org markdown format into a paper dict."""
    lines = raw.strip().split("\n")
    current_section = None
    data: dict[str, Any] = {"title": "", "summary": "", "authors": [], "arxiv_id": arxiv_id, "url": f"https://arxiv.org/abs/{arxiv_id}", "source": "arxiv-txt.org", "extra": {}}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            current_section = line[2:].lower()
            continue
        if current_section == "title":
            data["title"] = line
        elif current_section == "authors":
            data["authors"] = [a.strip() for a in line.split(",")]
        elif current_section == "abstract":
            data["summary"] += line + " "
        elif current_section == "categories":
            data["extra"]["categories"] = [c.strip() for c in line.split(",")]
        elif current_section == "publication details":
            if "Published:" in line:
                data["extra"]["published"] = line.split("Published:")[1].strip()
        elif current_section == "bibtex":
            if "bibtex" not in data["extra"]:
                data["extra"]["bibtex"] = ""
            data["extra"]["bibtex"] += line + "\n"

    data["summary"] = data["summary"].strip()
    return data


# ── HuggingFace Papers API ────────────────────────────────────────────

def _search_huggingface(query: str, top_n: int = 10) -> list[dict]:
    """Search HuggingFace Papers via semantic search API."""
    url = f"https://huggingface.co/api/papers/search?q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperPal/1.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        papers_json = json.loads(resp.read().decode("utf-8"))
        papers = []
        for paper in papers_json[:top_n]:
            p = paper.get("paper", paper)
            papers.append({
                "title": p.get("title", ""),
                "summary": p.get("summary", ""),
                "arxiv_id": p.get("id", ""),
                "url": f"https://arxiv.org/abs/{p.get('id', '')}",
                "authors": p.get("authors", []),
                "source": "HuggingFace Papers",
                "extra": {"upvotes": p.get("upvotes", 0), "trending_score": p.get("trendingScore", 0)}
            })
        return papers
    except Exception as e:
        mcp_log(f"HuggingFace search failed: {e}")
        return []


# ── Semantic Scholar API ──────────────────────────────────────────────

def _search_semantic_scholar(query: str, limit: int = 10) -> list[dict]:
    """Search Semantic Scholar API."""
    fields = "title,authors,url,abstract,tldr,citationStyles,externalIds,venue,year,citationCount"
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit={limit}&fields={fields}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperPal/1.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode("utf-8"))
        papers = []
        for paper in data.get("data", []):
            authors = [a.get("name", "") for a in paper.get("authors", [])]
            ext_ids = paper.get("externalIds", {}) or {}
            arxiv_id = ext_ids.get("ArXiv", "")
            papers.append({
                "title": paper.get("title", ""),
                "summary": paper.get("abstract", "") or (paper.get("tldr") or {}).get("text", ""),
                "authors": authors,
                "url": paper.get("url", f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""),
                "arxiv_id": arxiv_id,
                "source": "Semantic Scholar",
                "extra": {
                    "venue": paper.get("venue", ""),
                    "year": paper.get("year", ""),
                    "citations": paper.get("citationCount", 0),
                    "tldr": (paper.get("tldr") or {}).get("text", "")
                }
            })
        return papers
    except Exception as e:
        mcp_log(f"Semantic Scholar search failed: {e}")
        return []


# ── Tool Dispatch ─────────────────────────────────────────────────────

def _execute_tool(name: str, args: dict) -> Any:
    if name == "search_arxiv_papers":
        papers = _search_arxiv_api(args["query"], min(args.get("max_results", 10), 50))
        return {"papers": papers, "count": len(papers), "formatted": _format_papers(papers)}

    elif name == "fetch_paper_details_from_arxiv":
        arxiv_ids = args["arxiv_ids"]
        if isinstance(arxiv_ids, str):
            arxiv_ids = [arxiv_ids]
        papers = _fetch_arxiv_details(arxiv_ids)
        return {"papers": papers, "count": len(papers), "formatted": _format_papers(papers)}

    elif name == "semantic_search_papers_on_huggingface":
        papers = _search_huggingface(args["query"], args.get("top_n", 10))
        return {"papers": papers, "count": len(papers), "formatted": _format_papers(papers)}

    elif name == "search_semantic_scholar":
        papers = _search_semantic_scholar(args["query"], min(args.get("limit", 10), 50))
        return {"papers": papers, "count": len(papers), "formatted": _format_papers(papers)}

    raise ValueError(f"Unknown tool: {name}")


# ── MCP Request Handler ───────────────────────────────────────────────

def handle_request(msg: dict) -> None:
    msg_id = msg.get("id")
    method = msg.get("method", "")
    params = msg.get("params", {})

    if method == "initialize":
        respond(msg_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "paperpal-mcp", "version": "1.0.0"}
        })
    elif method == "notifications/initialized":
        respond(None, {})
    elif method == "tools/list":
        respond(msg_id, {"tools": TOOL_DEFS})
    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})
        try:
            result = _execute_tool(tool_name, args)
            respond(msg_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})
        except Exception as e:
            respond(msg_id, error={"code": -32000, "message": f"{type(e).__name__}: {e}"})
    else:
        respond(msg_id, error={"code": -32601, "message": f"Method not found: {method}"})


# ── Main ──────────────────────────────────────────────────────────────

def main():
    mcp_log("PaperPal MCP server starting...")
    buf = ""
    for line in sys.stdin:
        buf += line
        try:
            msg = json.loads(buf)
            buf = ""
            handle_request(msg)
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    main()
