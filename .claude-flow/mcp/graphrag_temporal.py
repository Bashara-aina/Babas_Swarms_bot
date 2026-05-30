#!/usr/bin/env python3
"""GraphRAG Temporal Versioning — Time-aware graph storage. Extends graphrag_engine.py."""
import ast
import hashlib
import json
import sqlite3
import threading
import time
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

HERMES_HOME = Path("/home/newadmin/.hermes")
GRAPH_DB = HERMES_HOME / "graphrag" / "graphrag_temporal.db"
GRAPH_DB.parent.mkdir(parents=True, exist_ok=True)
LOCK = threading.Lock()

# ---------------------------------------------------------------------------
# DB schema with temporal fields
# ---------------------------------------------------------------------------
def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(GRAPH_DB), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""CREATE TABLE IF NOT EXISTS nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, kind TEXT NOT NULL,
        file_path TEXT NOT NULL, line_number INTEGER DEFAULT 0, docstring TEXT,
        signature TEXT, content_hash TEXT, embedding BLOB, updated REAL,
        valid_from REAL NOT NULL DEFAULT (strftime('%s', 'now')),
        valid_until REAL DEFAULT NULL, created_by TEXT DEFAULT 'unknown',
        superseded_by INTEGER DEFAULT NULL,
        UNIQUE(name, kind, file_path, valid_from))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT, source_id INTEGER NOT NULL,
        target_id INTEGER NOT NULL, edge_type TEXT NOT NULL, weight REAL DEFAULT 1.0,
        updated REAL, valid_from REAL NOT NULL DEFAULT (strftime('%s', 'now')),
        valid_until REAL DEFAULT NULL, created_by TEXT DEFAULT 'unknown',
        superseded_by INTEGER DEFAULT NULL,
        FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
        FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_valid ON nodes(valid_from, valid_until)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name, kind)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_superseded ON nodes(superseded_by)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_valid ON edges(valid_from, valid_until)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_superseded ON edges(superseded_by)")
    conn.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
        name, docstring, signature, file_path, tokenize='trigram')""")
    conn.commit()
    return conn

def _now() -> float:
    return time.time()

def _ts(ts: float | None) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).isoformat() if ts else "NULL"

def _nr(row) -> dict:
    return {"id": row[0], "name": row[1], "kind": row[2], "file_path": row[3],
            "line_number": row[4], "docstring": row[5], "signature": row[6],
            "valid_from": row[10], "valid_until": row[11], "created_by": row[12], "superseded_by": row[13]}

def _er(row) -> dict:
    return {"id": row[0], "source_id": row[1], "target_id": row[2],
            "edge_type": row[3], "weight": row[4], "updated": row[5],
            "valid_from": row[6], "valid_until": row[7], "created_by": row[8], "superseded_by": row[9]}

# ---------------------------------------------------------------------------
# Temporal insert with contradiction detection
# ---------------------------------------------------------------------------
def _insert_node(conn, node: dict, agent: str = "unknown") -> int:
    now = _now()
    # Check active node with same key for contradiction
    old = conn.execute("""SELECT id FROM nodes WHERE name=? AND kind=? AND file_path=?
        AND valid_until IS NULL""", (node["name"], node["kind"], node["file_path"])).fetchone()
    if old:
        conn.execute("UPDATE nodes SET valid_until=?, superseded_by=-1 WHERE id=?", (now, old[0]))
    emb = json.dumps(node.get("embedding")) if node.get("embedding") else None
    cur = conn.execute("""INSERT INTO nodes (name,kind,file_path,line_number,docstring,
        signature,content_hash,embedding,updated,valid_from,created_by) VALUES
        (?,?,?,?,?,?,?,?,?,?,?)""",
        (node["name"],node["kind"],node["file_path"],node.get("line_number",0),
         node.get("docstring",""),node.get("signature",""),node.get("content_hash",""),
         emb,node.get("updated",now),now,agent))
    new_id = cur.lastrowid
    if old:
        conn.execute("UPDATE nodes SET superseded_by=? WHERE id=?", (new_id, old[0]))
    return new_id

def _insert_edge(conn: sqlite3.Connection, src: int, tgt: int, etype: str, w: float = 1.0, agent: str = "unknown") -> int:
    now = _now()
    old = conn.execute("""SELECT id FROM edges WHERE source_id=? AND target_id=?
        AND edge_type=? AND valid_until IS NULL""", (src, tgt, etype)).fetchone()
    if old:
        conn.execute("UPDATE edges SET valid_until=?, superseded_by=-1 WHERE id=?", (now, old[0]))
    cur = conn.execute("""INSERT INTO edges (source_id,target_id,edge_type,weight,updated,
        valid_from,created_by) VALUES (?,?,?,?,?,?,?)""",
        (src, tgt, etype, w, now, now, agent))
    new_id = cur.lastrowid
    if old:
        conn.execute("UPDATE edges SET superseded_by=? WHERE id=?", (new_id, old[0]))
    return new_id

# ---------------------------------------------------------------------------
# Temporal queries
# ---------------------------------------------------------------------------
def graphrag_query_at_time(query: str, timestamp: float, depth: int = 2, top_k: int = 10) -> dict:
    with LOCK:
        conn = _db()
        rows = conn.execute("""SELECT id,name,kind,file_path,line_number,docstring,signature,
            valid_from,valid_until,created_by,superseded_by FROM nodes
            WHERE valid_from<=? AND (valid_until IS NULL OR valid_until>?)
            ORDER BY valid_from DESC""", (timestamp, timestamp)).fetchall()
        if not rows:
            conn.close()
            return {"query": query, "timestamp": _ts(timestamp), "results": [], "message": "no facts at this time"}
        name_map = {}
        for row in rows:
            key = (row[1], row[2], row[3])
            if key not in name_map:
                name_map[key] = _nr(row)
        nodes = list(name_map.values())
        edge_rows = conn.execute("""SELECT id,source_id,target_id,edge_type,weight,updated,
            valid_from,valid_until,created_by,superseded_by FROM edges
            WHERE valid_from<=? AND (valid_until IS NULL OR valid_until>?)""",
            (timestamp, timestamp)).fetchall()
        edges = [_er(r) for r in edge_rows]
        conn.close()
        return {"query": query, "timestamp": _ts(timestamp), "nodes": nodes[:top_k], "edges": edges,
                "indexed_files": len(set(n["file_path"] for n in nodes))}

def graphrag_query_current(query: str, top_k: int = 10) -> dict:
    with LOCK:
        conn = _db()
        rows = conn.execute("""SELECT id,name,kind,file_path,line_number,docstring,signature,
            valid_from,valid_until,created_by,superseded_by FROM nodes WHERE valid_until IS NULL
            ORDER BY valid_from DESC""").fetchall()
        name_map = {}
        for row in rows:
            key = (row[1], row[2], row[3])
            if key not in name_map:
                name_map[key] = _nr(row)
        nodes = list(name_map.values())
        edge_rows = conn.execute("""SELECT id,source_id,target_id,edge_type,weight,updated,
            valid_from,valid_until,created_by,superseded_by FROM edges WHERE valid_until IS NULL
            AND source_id IN (SELECT id FROM nodes WHERE valid_until IS NULL)
            AND target_id IN (SELECT id FROM nodes WHERE valid_until IS NULL)""").fetchall()
        edges = [_er(r) for r in edge_rows]
        conn.close()
        return {"query": query, "timestamp": _ts(_now()), "nodes": nodes[:top_k], "edges": edges,
                "indexed_files": len(set(n["file_path"] for n in nodes))}

def graphrag_history(symbol: str, kind: str | None = None) -> dict:
    with LOCK:
        conn = _db()
        q = "SELECT id,name,kind,file_path,line_number,docstring,signature,valid_from,valid_until,created_by,superseded_by FROM nodes WHERE name=?"
        p = [symbol]
        if kind:
            q += " AND kind=?"
            p.append(kind)
        q += " ORDER BY valid_from ASC"
        rows = conn.execute(q, p).fetchall()
        conn.close()
        if not rows:
            return {"symbol": symbol, "kind": kind, "versions": [], "message": "not found"}
        versions = [_nr(r) for r in rows]
        return {"symbol": symbol, "kind": kind, "versions": versions, "total_versions": len(versions),
                "current":versions[-1] if versions else None}

def graphrag_diff(symbol: str, from_time: float, to_time: float, kind: str | None = None) -> dict:
    before = graphrag_query_at_time(symbol, from_time)
    after = graphrag_query_at_time(symbol, to_time)
    with LOCK:
        conn = _db()
        q = "SELECT id,name,kind,file_path,line_number,docstring,signature,valid_from,valid_until,created_by,superseded_by FROM nodes WHERE name=? AND valid_from<=? AND valid_from>?"
        p = [symbol, from_time, 0]
        if kind:
            q += " AND kind=?"
            p.append(kind)
        born_rows = conn.execute(q, p).fetchall()
        conn.close()
        born = [_nr(r) for r in born_rows]
        return {"symbol": symbol, "kind": kind, "from": _ts(from_time), "to": _ts(to_time),
                "before_count": len(before.get("nodes", [])), "after_count": len(after.get("nodes", [])),
                "version_chain": born, "current_facts": after.get("nodes", [])}

# ---------------------------------------------------------------------------
# AST extraction
# ---------------------------------------------------------------------------
def _embed(text: str) -> list[float] | None:
    try:
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer("all-MiniLM-L6-v2", device="cuda:0")
        return m.encode(text, normalize_embeddings=True).tolist()
    except Exception:
        pass
    try:
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        return m.encode(text, normalize_embeddings=True).tolist()
    except Exception:
        return None

class _Ex(ast.NodeVisitor):
    def __init__(self, p): self.p=p; self.ns=[]; self.es=[]; self._ids={}; self._f=None; self._c=None
    def _a(self,n,k,l=0,d="",s=""):
        key=(n,k)
        if key in self._ids: return self._ids[key]
        self._ids[key]=len(self._ids)+1
        self.ns.append({"name":n,"kind":k,"file_path":self.p,"line_number":l,"docstring":d,"signature":s})
        return self._ids[key]
    def visit_FunctionDef(self,node):
        d=ast.get_docstring(node) or ""; s=ast.unparse(node.args) if hasattr(ast,"unparse") else ""
        p=self._c or ""; k="method" if p else "function"
        nm=f"{p}.{node.name}" if p else node.name
        nid=self._a(nm,k,node.lineno,d,s); self._ids[(node.name,k)]=nid
        o,self._f=self._f,nm; self.generic_visit(node); self._f=o
    visit_AsyncFunctionDef=visit_FunctionDef
    def visit_ClassDef(self,node):
        o=self._c; self._c=node.name; d=ast.get_docstring(node) or ""
        self._a(node.name,"class",node.lineno,d,"")
        for b in node.bases:
            if hasattr(ast,"unparse") and ast.unparse(b): self.es.append((node.name,ast.unparse(b),"inherits"))
        self.generic_visit(node); self._c=o
    def visit_Call(self,node):
        if self._f and hasattr(ast,"unparse"):
            fn=ast.unparse(node.func); base=fn.split(".")[0] if fn else ""
            if base: self.es.append((self._f,base,"calls"))
        self.generic_visit(node)

def _parse(path: str) -> tuple[list[dict], list[tuple]]:
    try: src=Path(path).read_text(encoding="utf-8",errors="ignore")
    except: return [],[]
    try: tree=ast.parse(src,filename=path)
    except SyntaxError: return [],[]
    ex=_Ex(path); ex.visit(tree)
    n2i={(n["name"],n["kind"]):i+1 for i,n in enumerate(ex.ns)}
    res=[]
    for s,t,et,w in ex.es:
        sid=n2i.get((s,"function")) or n2i.get((s,"method"))
        tid=n2i.get((t,"function")) or n2i.get((t,"method")) or n2i.get((t,"class"))
        if sid and tid: res.append((sid,tid,et,w))
    return ex.ns, res

def index_file_temporal(path: str, agent: str="unknown") -> dict:
    h=hashlib.sha256(Path(path).read_text(encoding="utf-8",errors="ignore").encode()).hexdigest()[:16]
    nodes,edges=_parse(path)
    if not nodes: return {"skipped":True,"reason":"no nodes","file":path}
    with LOCK:
        conn=_db(); now=_now()
        for n in nodes:
            n["embedding"]=_embed(f"{n['name']} {n.get('docstring','')} {n.get('signature','')}")
            n["content_hash"]=h; _insert_node(conn,n,agent)
        id_rows=conn.execute("SELECT name,kind,file_path,id FROM nodes WHERE valid_from=? AND valid_until IS NULL",(now,)).fetchall()
        n2i={(r[0],r[1],r[2]):r[3] for r in id_rows}
        for s,t,et,w in edges:
            sid=n2i.get((s,"function",path)) or n2i.get((s,"method",path))
            tid=n2i.get((t,"function",path)) or n2i.get((t,"method",path)) or n2i.get((t,"class",path))
            if sid and tid: _insert_edge(conn,sid,tid,et,w,agent)
        conn.commit(); conn.close()
        return {"indexed":True,"file":path,"nodes":len(nodes),"edges":len(edges)}

def build_index_temporal(paths: list[str]=None, agent: str="unknown") -> dict:
    if paths is None: paths=["/home/newadmin/swarm-bot"]
    files=[]
    for base in paths:
        p=Path(base)
        if p.is_dir():
            for f in p.rglob("*.py"):
                if not any(s in str(f) for s in ["/.git/","/.venv/","/node_modules/","/__pycache__/","/.claude/","/.hermes/","/data/"]):
                    files.append(str(f))
        elif p.is_file() and p.suffix==".py": files.append(str(p))
    stats={"files_found":len(files),"indexed":0,"skipped":0,"errors":[]}
    for f in files:
        try: r=index_file_temporal(f,agent); stats["indexed" if r.get("indexed") else "skipped"]+=1
        except Exception as e: stats["errors"].append({"file":f,"error":str(e)}); stats["skipped"]+=1
    return stats

# ---------------------------------------------------------------------------
# MCP handler
# ---------------------------------------------------------------------------
def handle_graphrag_temporal(args: dict[str, Any]) -> str:
    a=args.get("action","query_current")
    if a=="query_at_time": result=graphrag_query_at_time(args.get("query",""),args.get("timestamp",_now()),args.get("depth",2),args.get("top_k",10))
    elif a=="query_current": result=graphrag_query_current(args.get("query",""),args.get("top_k",10))
    elif a=="history": result=graphrag_history(args.get("symbol",""),args.get("kind"))
    elif a=="diff": result=graphrag_diff(args.get("symbol",""),args.get("from_time",_now()-86400),args.get("to_time",_now()),args.get("kind"))
    elif a=="build_index": result=build_index_temporal(args.get("paths"),args.get("agent_id","unknown"))
    elif a=="status":
        with LOCK:
            conn=_db()
            nc=conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            na=conn.execute("SELECT COUNT(*) FROM nodes WHERE valid_until IS NULL").fetchone()[0]
            ec=conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            ea=conn.execute("SELECT COUNT(*) FROM edges WHERE valid_until IS NULL").fetchone()[0]
            conn.close()
        result={"total_nodes":nc,"active_nodes":na,"total_edges":ec,"active_edges":ea}
    else: result={"error":f"unknown action: {a}"}
    return json.dumps(result,indent=2)

GRAPHRAG_TEMPORAL_SCHEMA={
    "name":"graphrag_temporal",
    "description":"Time-aware graph retrieval with version history. Supports: query_at_time, query_current, history, diff, build_index, status.",
    "parameters":{"type":"object","properties":{
        "action":{"type":"string","enum":["query_at_time","query_current","history","diff","build_index","status"]},
        "query":{"type":"string"},"timestamp":{"type":"number"},"from_time":{"type":"number"},"to_time":{"type":"number"},
        "symbol":{"type":"string"},"kind":{"type":"string"},"depth":{"type":"integer","default":2},
        "top_k":{"type":"integer","default":10},"paths":{"type":"array","items":{"type":"string"}},"agent_id":{"type":"string"}
    }}
}
