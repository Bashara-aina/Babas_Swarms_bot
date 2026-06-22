#!/usr/bin/env python3
"""
GraphRAG Engine — Code-aware graph retrieval for Hermes.
Combines vector embeddings with call graph traversal for multi-hop reasoning.
Supports Python AST extraction, dependency graphs, and incremental indexing.
"""
import ast
import hashlib
import json
import sqlite3
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = Path("/home/newadmin/swarm-bot")
GRAPH_DB = Path("/home/newadmin/.hermes/graphrag/graphrag.db")
LOCK = threading.Lock()

# ---------------------------------------------------------------------------
# Embedding model (all-MiniLM-L6-v2 as fallback)
# ---------------------------------------------------------------------------
_Model = None

def _get_model():
    global _Model
    if _Model is not None:
        return _Model
    try:
        from sentence_transformers import SentenceTransformer
        for name in ["all-MiniLM-L6-v2", "paraphrase-MiniLM-L6-v2"]:
            try:
                _Model = SentenceTransformer(name, device="cuda:0")
                return _Model
            except Exception:
                try:
                    _Model = SentenceTransformer(name, device="cpu")
                    return _Model
                except Exception:
                    continue
    except ImportError:
        pass
    return None

def _embed(text: str) -> list[float] | None:
    m = _get_model()
    if not m:
        return None
    try:
        v = m.encode(text, normalize_embeddings=True)
        return v.tolist()
    except Exception:
        return None

# ---------------------------------------------------------------------------
# SQLite graph storage
# ---------------------------------------------------------------------------
def _db() -> sqlite3.Connection:
    GRAPH_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(GRAPH_DB), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, kind TEXT NOT NULL,
            file_path TEXT NOT NULL, line_number INTEGER DEFAULT 0, docstring TEXT,
            signature TEXT, content_hash TEXT, embedding BLOB, updated REAL,
            UNIQUE(name, kind, file_path)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT, source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL, edge_type TEXT NOT NULL, weight REAL DEFAULT 1.0,
            updated REAL, FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
            FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE,
            UNIQUE(source_id, target_id, edge_type)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS file_index (
            file_path TEXT PRIMARY KEY, content_hash TEXT, ast_hash TEXT, last_indexed REAL
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
            name, docstring, signature, file_path, tokenize='trigram'
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
    conn.commit()
    return conn

def _node(row) -> dict[str, Any]:
    return {"id": row[0], "name": row[1], "kind": row[2], "file_path": row[3],
            "line_number": row[4], "docstring": row[5], "signature": row[6]}

# ---------------------------------------------------------------------------
# Python AST extraction
# ---------------------------------------------------------------------------
class _Extractor(ast.NodeVisitor):
    def __init__(self, path: str):
        self.path = path
        self.nodes: list[dict] = []
        self.edges: list[tuple] = []
        self._ids: dict[tuple, int] = {}
        self._func: str | None = None
        self._cls: str | None = None

    def _add(self, name: str, kind: str, line: int = 0, doc: str = "", sig: str = "") -> int:
        key = (name, kind)
        if key in self._ids:
            return self._ids[key]
        self._ids[key] = len(self._ids) + 1
        self.nodes.append({"name": name, "kind": kind, "file_path": self.path,
                           "line_number": line, "docstring": doc, "signature": sig,
                           "content_hash": "", "embedding": None, "updated": time.time()})
        return self._ids[key]

    def _edge(self, src: str, tgt: str, etype: str, w: float = 1.0):
        self.edges.append((src, tgt, etype, w))

    def visit_FunctionDef(self, node):
        doc = ast.get_docstring(node) or ""
        sig = ast.unparse(node.args) if hasattr(ast, "unparse") else ""
        parent = self._cls or ""
        kind = "method" if parent else "function"
        name = f"{parent}.{node.name}" if parent else node.name
        nid = self._add(name, kind, node.lineno, doc, sig)
        self._ids[(node.name, kind)] = nid
        old, self._func = self._func, name
        self.generic_visit(node)
        self._func = old

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        old_cls = self._cls
        self._cls = node.name
        doc = ast.get_docstring(node) or ""
        self._add(node.name, "class", node.lineno, doc, "")
        for base in node.bases:
            if hasattr(ast, "unparse"):
                bn = ast.unparse(base)
                if bn:
                    self._edge(node.name, bn, "inherits")
        self.generic_visit(node)
        self._cls = old_cls

    def visit_Call(self, node):
        if self._func and hasattr(ast, "unparse"):
            fn = ast.unparse(node.func)
            base = fn.split(".")[0] if fn else ""
            if base:
                self._edge(self._func, base, "calls")
        self.generic_visit(node)

    def visit_Import(self, node):
        for a in node.names:
            pass  # Track imports if needed
    def visit_ImportFrom(self, node):
        pass

def _parse_file(path: str) -> tuple[list[dict], list[tuple]]:
    try:
        src = Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return [], []
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError:
        return [], []

    ex = _Extractor(path)
    ex.visit(tree)

    name_to_id = {(n["name"], n["kind"]): i + 1 for i, n in enumerate(ex.nodes)}
    resolved = []
    for src_n, tgt_n, etype, weight in ex.edges:
        sid = name_to_id.get((src_n, "function")) or name_to_id.get((src_n, "method"))
        tid = (name_to_id.get((tgt_n, "function")) or name_to_id.get((tgt_n, "method"))
               or name_to_id.get((tgt_n, "class")))
        if sid and tid:
            resolved.append((sid, tid, etype, weight))
    return ex.nodes, resolved

# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------
def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

def index_file(path: str, conn: sqlite3.Connection) -> dict:
    content = Path(path).read_text(encoding="utf-8", errors="ignore")
    h = _hash(content)
    row = conn.execute("SELECT content_hash FROM file_index WHERE file_path = ?",
                       (path,)).fetchone()
    if row and row[0] == h:
        return {"skipped": True, "reason": "unchanged", "file": path}

    nodes, edges = _parse_file(path)
    if not nodes:
        return {"skipped": True, "reason": "no nodes", "file": path}

    for n in nodes:
        n["embedding"] = _embed(f"{n['name']} {n.get('docstring','')} {n.get('signature','')}")
        n["content_hash"] = h

    for n in nodes:
        emb = json.dumps(n["embedding"]) if n["embedding"] else None
        conn.execute("""
            INSERT OR REPLACE INTO nodes (name, kind, file_path, line_number, docstring,
            signature, content_hash, embedding, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (n["name"], n["kind"], n["file_path"], n["line_number"], n["docstring"],
              n["signature"], n["content_hash"], emb, n["updated"]))
        conn.execute("INSERT OR REPLACE INTO nodes_fts (name, docstring, signature, file_path) "
                     "VALUES (?, ?, ?, ?)", (n["name"], n["docstring"], n["signature"], n["file_path"]))

    for src_id, tgt_id, etype, weight in edges:
        conn.execute("INSERT OR REPLACE INTO edges (source_id, target_id, edge_type, weight, updated) "
                     "VALUES (?, ?, ?, ?, ?)", (src_id, tgt_id, etype, weight, time.time()))

    conn.execute("INSERT OR REPLACE INTO file_index (file_path, content_hash, last_indexed) "
                 "VALUES (?, ?, ?)", (path, h, time.time()))
    conn.commit()
    return {"indexed": True, "file": path, "nodes": len(nodes), "edges": len(edges)}

def build_index(paths: list[str] = None) -> dict[str, Any]:
    if paths is None:
        paths = [str(PROJECT_ROOT)]
    files = []
    for base in paths:
        p = Path(base)
        if p.is_dir():
            for f in p.rglob("*.py"):
                if not any(s in str(f) for s in ["/.git/", "/.venv/", "/node_modules/",
                                                  "/__pycache__/", "/.claude/", "/.hermes/",
                                                  "/data/", "/build/", "/dist/"]):
                    files.append(str(f))
        elif p.is_file() and p.suffix == ".py":
            files.append(str(p))

    stats = {"files_found": len(files), "indexed": 0, "skipped": 0, "errors": []}
    with LOCK:
        conn = _db()
        for f in files:
            try:
                r = index_file(f, conn)
                stats["indexed" if r.get("indexed") else "skipped"] += 1
            except Exception as e:
                stats["errors"].append({"file": f, "error": str(e)})
                stats["skipped"] += 1
        try:
            conn.execute("INSERT INTO nodes_fts(nodes_fts) VALUES('rebuild')")
            conn.commit()
        except Exception:
            pass
        conn.close()
    return stats

# ---------------------------------------------------------------------------
# Query / retrieval
# ---------------------------------------------------------------------------
def _vector_search(query: str, top_k: int = 10) -> list[dict]:
    emb = _embed(query)
    if not emb:
        return []
    with LOCK:
        conn = _db()
        rows = conn.execute("SELECT id, name, kind, file_path, line_number, docstring, "
                            "signature, embedding FROM nodes WHERE embedding IS NOT NULL").fetchall()
        conn.close()
    if not rows:
        return []
    scored = []
    for row in rows:
        try:
            ne = json.loads(row[7])
            sim = sum(a * b for a, b in zip(emb, ne, strict=True))
            scored.append((sim, row))
        except Exception:
            pass
    scored.sort(reverse=True)
    return [{"vector_score": round(s, 4), **_node(r)} for s, r in scored[:top_k]]

def _traverse(node_id: int, depth: int = 2, etypes: list[str] = None,
              direction: str = "both") -> list[dict]:
    if etypes is None:
        etypes = ["calls", "inherits", "imports"]
    results = []
    visited = {node_id}
    with LOCK:
        conn = _db()
        row = conn.execute("SELECT id, name, kind, file_path, line_number, docstring, signature "
                           "FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if not row:
            conn.close()
            return []
        n = _node(row)
        n["depth"] = 0
        n["edge_type"] = None
        results.append(n)

        def bfs(curr: int, d: int):
            if d < 0:
                return
            for dir_clause, join_col in [("source_id", "target_id"), ("target_id", "source_id")]:
                if direction not in ("both", "backward" if join_col == "source_id" else "forward"):
                    continue
                rows = conn.execute(f"""
                    SELECT {join_col}, edge_type FROM edges
                    WHERE {dir_clause} = ? AND edge_type IN ({",".join("?" * len(etypes))})
                """, (curr, *etypes)).fetchall()
                for oid, et in rows:
                    if oid in visited:
                        continue
                    visited.add(oid)
                    nr = conn.execute("SELECT id, name, kind, file_path, line_number, docstring, signature "
                                      "FROM nodes WHERE id = ?", (oid,)).fetchone()
                    if nr:
                        res = _node(nr)
                        res["edge_type"] = et
                        res["depth"] = d
                        results.append(res)
                    bfs(oid, d - 1)

        bfs(node_id, depth)
        conn.close()
    return results

def _resolve(name: str, kind: str = None) -> int | None:
    with LOCK:
        conn = _db()
        if kind:
            row = conn.execute("SELECT id FROM nodes WHERE name = ? AND kind = ? LIMIT 1",
                               (name, kind)).fetchone()
        else:
            row = None
            for k in ("function", "method", "class"):
                row = conn.execute("SELECT id FROM nodes WHERE name = ? AND kind = ? LIMIT 1",
                                   (name, k)).fetchone()
                if row:
                    break
        conn.close()
        return row[0] if row else None

def _file_count() -> int:
    with LOCK:
        conn = _db()
        c = conn.execute("SELECT COUNT(*) FROM file_index").fetchone()[0]
        conn.close()
        return c

def _model_is_random() -> bool:
    """Check if embedding model is a random fallback (not a real pretrained model)."""
    global _Model
    if _Model is None:
        return True
    try:
        import sentence_transformers
        name = getattr(_Model, '_model_name', '') or getattr(_Model, '_model_card_text', '') or ''
        return 'random' in name.lower() or 'creating a new one' in str(type(_Model)).lower() or not name
    except Exception:
        return True

def _fts_search(query: str, top_k: int = 10) -> list[dict]:
    """FTS5 text search (always reliable, no external model needed)."""
    with LOCK:
        conn = _db()
        try:
            rows = conn.execute("""
                SELECT n.id, n.name, n.kind, n.file_path, n.line_number, n.docstring, n.signature
                FROM nodes_fts f JOIN nodes n ON f.rowid = n.id
                WHERE nodes_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, top_k)).fetchall()
            conn.close()
            return [{"vector_score": 0.5, "relevance": "fts", **_node(r)} for r in rows]
        except Exception:
            conn.close()
            return []

def graphrag_query(query: str, depth: int = 2, top_k: int = 10) -> dict[str, Any]:
    # FTS5 is primary (always reliable); vector is secondary (may be random)
    fts = _fts_search(query, top_k)
    vres = _vector_search(query, top_k) if not _model_is_random() else []
    if not vres:
        vres = fts
    if not vres:
        return {"query": query, "vector_results": [], "graph_results": [], "merged_results": []}
    gid = vres[0].get("id")
    gres = _traverse(gid, depth=depth)
    seen = set()
    merged = []
    for r in vres:
        if r["id"] not in seen:
            r["relevance"] = "vector"
            r["combined_score"] = r.get("vector_score", 0.5)
            merged.append(r)
            seen.add(r["id"])
    for r in gres:
        if r["id"] not in seen:
            r["relevance"] = "graph"
            r["combined_score"] = 0.3 - (r.get("depth", 0) * 0.05)
            merged.append(r)
            seen.add(r["id"])
    merged.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
    return {"query": query, "vector_results": vres, "graph_results": gres,
            "merged_results": merged[:top_k], "indexed_files": _file_count()}

def graphrag_get_dependencies(symbol: str, kind: str = None, depth: int = 2) -> dict:
    nid = _resolve(symbol, kind)
    if not nid:
        return {"error": f"symbol not found: {symbol}"}
    return {"symbol": symbol, "node_id": nid, "depth": depth,
            "related": _traverse(nid, depth=depth, etypes=["calls", "imports", "inherits"])}

def get_callers(symbol: str) -> dict:
    nid = _resolve(symbol)
    if not nid:
        return {"error": f"symbol not found: {symbol}"}
    with LOCK:
        conn = _db()
        rows = conn.execute("""
            SELECT DISTINCT n.id, n.name, n.kind, n.file_path, n.line_number
            FROM edges e JOIN nodes n ON e.source_id = n.id
            WHERE e.target_id = ? AND e.edge_type = 'calls'
        """, (nid,)).fetchall()
        conn.close()
    return {"symbol": symbol, "callers": [_node(r) for r in rows]}

def get_symbol_context(symbol: str, kind: str = None) -> dict:
    nid = _resolve(symbol, kind)
    if not nid:
        return {"error": f"symbol not found: {symbol}"}
    with LOCK:
        conn = _db()
        row = conn.execute("SELECT id, name, kind, file_path, line_number, docstring, signature "
                           "FROM nodes WHERE id = ?", (nid,)).fetchone()
        callers = conn.execute("""
            SELECT n.id, n.name, n.kind, n.file_path, n.line_number
            FROM edges e JOIN nodes n ON e.source_id = n.id
            WHERE e.target_id = ? AND e.edge_type = 'calls'
        """, (nid,)).fetchall()
        callees = conn.execute("""
            SELECT n.id, n.name, n.kind, n.file_path, n.line_number
            FROM edges e JOIN nodes n ON e.target_id = n.id
            WHERE e.source_id = ? AND e.edge_type = 'calls'
        """, (nid,)).fetchall()
        conn.close()
    return {"symbol": symbol, "node": _node(row) if row else None,
            "callers": [_node(r) for r in callers], "callees": [_node(r) for r in callees]}

def get_execution_path(from_sym: str, to_sym: str) -> dict:
    from_id = _resolve(from_sym)
    to_id = _resolve(to_sym)
    if not from_id or not to_id:
        return {"error": "one or both symbols not found", "from": from_sym, "to": to_sym}
    with LOCK:
        conn = _db()
        queue = [(from_id, [from_id])]
        visited = {from_id}
        while queue:
            curr, path = queue.pop(0)
            if curr == to_id:
                conn.close()
                return {"from": from_sym, "to": to_sym, "path_found": True,
                        "path_length": len(path) - 1, "path": path}
            rows = conn.execute("SELECT target_id FROM edges WHERE source_id = ? AND edge_type = 'calls'",
                                (curr,)).fetchall()
            for row in rows:
                nid = row[0]
                if nid not in visited:
                    visited.add(nid)
                    queue.append((nid, path + [nid]))
        conn.close()
    return {"from": from_sym, "to": to_sym, "path_found": False,
            "message": "no path found between symbols"}

# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------
def handle_graphrag(args: dict[str, Any]) -> str:
    action = args.get("action", "query")
    if action == "query":
        result = graphrag_query(args.get("query", ""), args.get("depth", 2), args.get("top_k", 10))
    elif action == "build_index":
        result = build_index(args.get("paths"))
    elif action == "get_dependencies":
        result = graphrag_get_dependencies(args.get("symbol", ""), args.get("kind"), args.get("depth", 2))
    elif action == "get_callers":
        result = get_callers(args.get("symbol", ""))
    elif action == "get_context":
        result = get_symbol_context(args.get("symbol", ""), args.get("kind"))
    elif action == "execution_path":
        result = get_execution_path(args.get("from_symbol", ""), args.get("to_symbol", ""))
    elif action == "status":
        with LOCK:
            conn = _db()
            nc = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            ec = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            fc = conn.execute("SELECT COUNT(*) FROM file_index").fetchone()[0]
            conn.close()
        result = {"nodes": nc, "edges": ec, "indexed_files": fc,
                  "embedding_model": "all-MiniLM-L6-v2" if _get_model() else "unavailable"}
    else:
        result = {"error": f"unknown action: {action}"}
    return json.dumps(result, indent=2)

GRAPHRAg_SCHEMA = {
    "name": "graphrag_engine",
    "description": (
        "Code-aware graph retrieval with multi-hop reasoning. "
        "Supports call graph extraction, dependency analysis, and execution path tracing. "
        "Use for: 'Find all places that call this function', 'What depends on this module', "
        "'Trace execution path from A to B'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["query", "build_index", "get_dependencies",
                                                  "get_callers", "get_context", "execution_path", "status"]},
            "query": {"type": "string"},
            "depth": {"type": "integer", "default": 2},
            "top_k": {"type": "integer", "default": 10},
            "paths": {"type": "array", "items": {"type": "string"}},
            "symbol": {"type": "string"},
            "kind": {"type": "string"},
            "from_symbol": {"type": "string"},
            "to_symbol": {"type": "string"},
        },
    },
}