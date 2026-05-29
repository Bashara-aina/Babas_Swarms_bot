#!/usr/bin/env python3
"""
CoordinationPrimitives — Robust multi-agent coordination for Hermes.
Circuit breakers, bulkheads, layered verification, idempotency, observability, message bus.
Persists to /tmp/hermes_coordination.db SQLite.
"""
import hashlib, json, sqlite3, threading, time, uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Constants ─────────────────────────────────────────────────────────────────
COORDINATION_DB = Path("/tmp/hermes_coordination.db")
TRACE_DB = Path("/tmp/hermes_traces.db")
LOCK = threading.Lock()

FAILURE_THRESHOLD, FAILURE_WINDOW_SECONDS = 5, 60
HALF_OPEN_TEST_DURATION, SUCCESS_COOLDOWN_SECONDS = 30, 30
VERIFICATION_CONFIDENCE_THRESHOLD = 0.90
IDEMPOTENCY_WINDOW_SECONDS = 300

# ── Enums ─────────────────────────────────────────────────────────────────────
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class MessageType(Enum):
    DIRECT = "direct"
    BROADCAST = "broadcast"
    REQUEST_RESPONSE = "request_response"

# ── Circuit Breaker ────────────────────────────────────────────────────────────
@dataclass
class CircuitBreakerState:
    agent_id: str
    failures: int = 0
    successes: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    opened_at: float = 0.0
    half_open_test_start: float = 0.0

_circuit_breakers: Dict[str, CircuitBreakerState] = {}
_circuit_lock = threading.Lock()

def _get_breaker(agent_id: str) -> CircuitBreakerState:
    with _circuit_lock:
        if agent_id not in _circuit_breakers:
            _circuit_breakers[agent_id] = CircuitBreakerState(agent_id=agent_id)
        return _circuit_breakers[agent_id]

def record_failure(agent_id: str) -> Dict[str, Any]:
    breaker = _get_breaker(agent_id)
    now = time.time()
    with _circuit_lock:
        breaker.failures += 1
        breaker.last_failure_time = now
        if breaker.state == CircuitState.CLOSED and breaker.failures >= FAILURE_THRESHOLD:
            breaker.state = CircuitState.OPEN
            breaker.opened_at = now
            return {"agent_id": agent_id, "state": "open", "failures": breaker.failures}
        elif breaker.state == CircuitState.OPEN and now - breaker.opened_at >= SUCCESS_COOLDOWN_SECONDS:
            breaker.state = CircuitState.HALF_OPEN
            breaker.half_open_test_start = now
            return {"agent_id": agent_id, "state": "half_open", "failures": breaker.failures}
        return {"agent_id": agent_id, "state": breaker.state.value, "failures": breaker.failures}

def record_success(agent_id: str) -> Dict[str, Any]:
    breaker = _get_breaker(agent_id)
    now = time.time()
    with _circuit_lock:
        breaker.successes += 1
        breaker.last_success_time = now
        if breaker.state == CircuitState.HALF_OPEN:
            breaker.state = CircuitState.CLOSED
            breaker.failures = breaker.successes = 0
            return {"agent_id": agent_id, "state": "closed", "message": "recovery successful"}
        return {"agent_id": agent_id, "state": breaker.state.value, "successes": breaker.successes}

def is_blocked(agent_id: str) -> bool:
    breaker = _get_breaker(agent_id)
    with _circuit_lock:
        if breaker.state == CircuitState.OPEN:
            now = time.time()
            if now - breaker.opened_at >= SUCCESS_COOLDOWN_SECONDS:
                breaker.state = CircuitState.HALF_OPEN
                breaker.half_open_test_start = now
                return False
            return True
    return False

def get_circuit_status(agent_id: str) -> Dict[str, Any]:
    breaker = _get_breaker(agent_id)
    with _circuit_lock:
        return {"agent_id": agent_id, "state": breaker.state.value, "failures": breaker.failures,
                "successes": breaker.successes, "last_failure_time": breaker.last_failure_time,
                "last_success_time": breaker.last_success_time}

def get_all_circuit_statuses() -> List[Dict[str, Any]]:
    with _circuit_lock:
        return [{"agent_id": bid, "state": b.state.value, "failures": b.failures, "successes": b.successes}
                for bid, b in _circuit_breakers.items()]

# ── Bulkhead ───────────────────────────────────────────────────────────────────
@dataclass
class BulkheadState:
    agent_type: str
    max_concurrency: int
    current_concurrency: int = 0
    total_requests: int = 0
    rejected_requests: int = 0

_bulkheads: Dict[str, BulkheadState] = {}
_bulkhead_locks: Dict[str, threading.Lock] = {}
_bulkhead_global_lock = threading.Lock()
DEFAULT_BULKHEAD_LIMITS = {"coordinator": 10, "specialist": 8, "worker": 5, "verifier": 4, "default": 3}

def _get_bulkhead_lock(agent_type: str) -> threading.Lock:
    with _bulkhead_global_lock:
        if agent_type not in _bulkhead_locks:
            _bulkhead_locks[agent_type] = threading.Lock()
        return _bulkhead_locks[agent_type]

def register_bulkhead(agent_type: str, max_concurrency: Optional[int] = None) -> None:
    limit = max_concurrency or DEFAULT_BULKHEAD_LIMITS.get(agent_type, DEFAULT_BULKHEAD_LIMITS["default"])
    with _bulkhead_global_lock:
        _bulkheads[agent_type] = BulkheadState(agent_type=agent_type, max_concurrency=limit)

def acquire_bulkhead(agent_type: str) -> bool:
    if agent_type not in _bulkheads:
        register_bulkhead(agent_type)
    bulkhead = _bulkheads[agent_type]
    lock = _get_bulkhead_lock(agent_type)
    with lock:
        if bulkhead.current_concurrency >= bulkhead.max_concurrency:
            bulkhead.rejected_requests += 1
            return False
        bulkhead.current_concurrency += 1
        bulkhead.total_requests += 1
        return True

def release_bulkhead(agent_type: str) -> None:
    if agent_type not in _bulkheads:
        return
    bulkhead = _bulkheads[agent_type]
    lock = _get_bulkhead_lock(agent_type)
    with lock:
        if bulkhead.current_concurrency > 0:
            bulkhead.current_concurrency -= 1

def get_bulkhead_status(agent_type: str) -> Dict[str, Any]:
    if agent_type not in _bulkheads:
        register_bulkhead(agent_type)
    b = _bulkheads[agent_type]
    return {"agent_type": agent_type, "max_concurrency": b.max_concurrency,
            "current_concurrency": b.current_concurrency,
            "available_slots": b.max_concurrency - b.current_concurrency,
            "total_requests": b.total_requests, "rejected_requests": b.rejected_requests}

def get_all_bulkhead_statuses() -> List[Dict[str, Any]]:
    with _bulkhead_global_lock:
        return [{"agent_type": bt, "max_concurrency": b.max_concurrency,
                 "current_concurrency": b.current_concurrency,
                 "available_slots": b.max_concurrency - b.current_concurrency}
                for bt, b in _bulkheads.items()]

# ── Verification ────────────────────────────────────────────────────────────────
@dataclass
class VerificationResult:
    verified: bool
    confidence: float
    message: str
    verifier_id: str
    timestamp: float
    trace_id: str

_verifications: List[VerificationResult] = []
_verification_lock = threading.Lock()

def verify_result(result: Any, agent_id: str, action_type: str = "general",
                  threshold: float = VERIFICATION_CONFIDENCE_THRESHOLD) -> VerificationResult:
    vid = f"verifier-{uuid.uuid4().hex[:8]}"
    now = time.time()
    trace_id = str(uuid.uuid4())
    confidence = 1.0
    verified = True
    message = "basic sanity check passed"
    if isinstance(result, dict):
        if "error" in result:
            verified = False
            confidence = 0.0
            message = f"error detected: {result.get('error')}"
        elif result.get("success") is False:
            verified = False
            confidence = 0.1
            message = "success=false in result"
    irreversible = ["delete", "remove", "drop", "destroy", "terminate"]
    if action_type.lower() in irreversible and confidence < 0.95:
        verified = False
        message = f"confidence {confidence} below threshold for irreversible action"
    verification = VerificationResult(verified=verified, confidence=confidence, message=message,
                                        verifier_id=vid, timestamp=now, trace_id=trace_id)
    with _verification_lock:
        _verifications.append(verification)
    return verification

def get_verification_history(limit: int = 50) -> List[Dict[str, Any]]:
    with _verification_lock:
        recent = _verifications[-limit:]
        return [{"verified": v.verified, "confidence": v.confidence, "message": v.message,
                 "verifier_id": v.verifier_id, "timestamp": v.timestamp, "trace_id": v.trace_id}
                for v in recent]

# ── Idempotency ─────────────────────────────────────────────────────────────────
_idempotency_store: Dict[str, float] = {}
_idempotency_lock = threading.Lock()

def generate_idempotency_key(*parts: str) -> str:
    combined = "|".join(str(p) for p in parts)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def check_idempotency(key: str) -> bool:
    with _idempotency_lock:
        now = time.time()
        expired = [k for k, t in _idempotency_store.items() if now - t > IDEMPOTENCY_WINDOW_SECONDS]
        for k in expired:
            del _idempotency_store[k]
        if key in _idempotency_store:
            return True
        _idempotency_store[key] = now
        return False

def mark_idempotent(key: str) -> None:
    with _idempotency_lock:
        _idempotency_store[key] = time.time()

# ── Message Bus ────────────────────────────────────────────────────────────────
@dataclass
class Message:
    msg_id: str
    from_agent: str
    to_agent: str
    msg_type: MessageType
    content: Any
    timestamp: float
    idempotency_key: str
    trace_id: str
    reply_to: Optional[str] = None

_agent_inboxes: Dict[str, List[Message]] = {}
_inbox_locks: Dict[str, threading.Lock] = {}
_global_inbox_lock = threading.Lock()
_subscribers: Dict[str, List[str]] = {}
_sub_lock = threading.Lock()

def _get_inbox_lock(agent_id: str) -> threading.Lock:
    with _global_inbox_lock:
        if agent_id not in _inbox_locks:
            _inbox_locks[agent_id] = threading.Lock()
        return _inbox_locks[agent_id]

def send_message(from_agent: str, to_agent: str, content: Any,
                 msg_type: MessageType = MessageType.DIRECT, reply_to: Optional[str] = None) -> Dict[str, Any]:
    msg_id = uuid.uuid4().hex[:12]
    trace_id = str(uuid.uuid4())
    idempotency_key = generate_idempotency_key(from_agent, to_agent, str(content), str(time.time()))
    if check_idempotency(idempotency_key):
        return {"status": "duplicate", "msg_id": msg_id, "idempotency_key": idempotency_key}
    msg = Message(msg_id=msg_id, from_agent=from_agent, to_agent=to_agent, msg_type=msg_type,
                  content=content, timestamp=time.time(), idempotency_key=idempotency_key,
                  trace_id=trace_id, reply_to=reply_to)
    inbox_lock = _get_inbox_lock(to_agent)
    with inbox_lock:
        if to_agent not in _agent_inboxes:
            _agent_inboxes[to_agent] = []
        _agent_inboxes[to_agent].append(msg)
    return {"status": "delivered", "msg_id": msg_id, "trace_id": trace_id, "idempotency_key": idempotency_key}

def broadcast_message(from_agent: str, content: Any) -> Dict[str, Any]:
    msg_id = uuid.uuid4().hex[:12]
    trace_id = str(uuid.uuid4())
    idempotency_key = generate_idempotency_key(from_agent, "broadcast", str(content), str(time.time()))
    if check_idempotency(idempotency_key):
        return {"status": "duplicate", "msg_id": msg_id}
    delivered_count = 0
    with _global_inbox_lock:
        agent_ids = list(_agent_inboxes.keys())
    for agent_id in agent_ids:
        if agent_id != from_agent:
            inbox_lock = _get_inbox_lock(agent_id)
            with inbox_lock:
                if agent_id not in _agent_inboxes:
                    _agent_inboxes[agent_id] = []
                _agent_inboxes[agent_id].append(Message(msg_id=msg_id, from_agent=from_agent,
                    to_agent=agent_id, msg_type=MessageType.BROADCAST, content=content,
                    timestamp=time.time(), idempotency_key=idempotency_key, trace_id=trace_id))
            delivered_count += 1
    return {"status": "broadcast", "msg_id": msg_id, "delivered_count": delivered_count, "trace_id": trace_id}

def get_messages(agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    inbox_lock = _get_inbox_lock(agent_id)
    with inbox_lock:
        if agent_id not in _agent_inboxes:
            return []
        messages = _agent_inboxes[agent_id][-limit:]
        return [{"msg_id": m.msg_id, "from_agent": m.from_agent, "to_agent": m.to_agent,
                 "msg_type": m.msg_type.value, "content": m.content, "timestamp": m.timestamp,
                 "reply_to": m.reply_to} for m in messages]

def register_agent_inbox(agent_id: str) -> None:
    inbox_lock = _get_inbox_lock(agent_id)
    with inbox_lock:
        if agent_id not in _agent_inboxes:
            _agent_inboxes[agent_id] = []

# ── Observability / Trace Storage ─────────────────────────────────────────────
def _get_trace_db() -> sqlite3.Connection:
    TRACE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(TRACE_DB), check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS traces (
        trace_id TEXT, agent_id TEXT, stage TEXT, input_data TEXT, output_data TEXT,
        latency_ms REAL, success INTEGER, timestamp REAL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS handoffs (
        handoff_id INTEGER PRIMARY KEY AUTOINCREMENT, trace_id TEXT, from_agent TEXT,
        to_agent TEXT, stage_name TEXT, latency_ms REAL, verification_passed INTEGER, timestamp REAL)""")
    conn.commit()
    return conn

def record_trace(trace_id: str, agent_id: str, stage: str,
                 input_data: Any, output_data: Any, latency_ms: float, success: bool) -> None:
    conn = _get_trace_db()
    conn.execute("""INSERT INTO traces (trace_id, agent_id, stage, input_data, output_data, latency_ms, success, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (trace_id, agent_id, stage, json.dumps(input_data), json.dumps(output_data), latency_ms, 1 if success else 0, time.time()))
    conn.commit()
    conn.close()

def record_handoff(trace_id: str, from_agent: str, to_agent: str,
                   stage_name: str, latency_ms: float, verification_passed: bool) -> None:
    conn = _get_trace_db()
    conn.execute("""INSERT INTO handoffs (trace_id, from_agent, to_agent, stage_name, latency_ms, verification_passed, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (trace_id, from_agent, to_agent, stage_name, latency_ms, 1 if verification_passed else 0, time.time()))
    conn.commit()
    conn.close()

def get_trace(trace_id: str) -> Dict[str, Any]:
    conn = _get_trace_db()
    trace_rows = conn.execute("SELECT * FROM traces WHERE trace_id = ? ORDER BY timestamp", (trace_id,)).fetchall()
    handoff_rows = conn.execute("SELECT * FROM handoffs WHERE trace_id = ? ORDER BY timestamp", (trace_id,)).fetchall()
    conn.close()
    if not trace_rows:
        return {"error": "trace not found", "trace_id": trace_id}
    cols = ["trace_id", "agent_id", "stage", "input_data", "output_data", "latency_ms", "success", "timestamp"]
    handoff_cols = ["handoff_id", "trace_id", "from_agent", "to_agent", "stage_name", "latency_ms", "verification_passed", "timestamp"]
    stages = []
    for row in trace_rows:
        s = dict(zip(cols, row))
        s["input_data"] = json.loads(s["input_data"]) if isinstance(s["input_data"], str) else s["input_data"]
        s["output_data"] = json.loads(s["output_data"]) if isinstance(s["output_data"], str) else s["output_data"]
        stages.append(s)
    handoffs = [dict(zip(handoff_cols, row)) for row in handoff_rows]
    total_latency = sum(s["latency_ms"] for s in stages)
    return {"trace_id": trace_id, "stages": stages, "handoffs": handoffs,
            "total_stages": len(stages), "total_handoffs": len(handoffs),
            "total_latency_ms": round(total_latency, 2)}

def get_recent_traces(limit: int = 20) -> List[Dict[str, Any]]:
    conn = _get_trace_db()
    rows = conn.execute("""SELECT trace_id, MAX(timestamp) as ts, SUM(latency_ms), MAX(success)
        FROM traces GROUP BY trace_id ORDER BY ts DESC LIMIT ?""", (limit,)).fetchall()
    conn.close()
    return [{"trace_id": r[0], "timestamp": r[1], "total_latency_ms": round(r[2], 2),
             "success": bool(r[3])} for r in rows]

# ── SQLite Durable State ───────────────────────────────────────────────────────
def _get_coord_db() -> sqlite3.Connection:
    COORDINATION_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(COORDINATION_DB), check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS circuit_breakers (
        agent_id TEXT PRIMARY KEY, failures INTEGER DEFAULT 0, successes INTEGER DEFAULT 0,
        state TEXT DEFAULT 'closed', last_failure_time REAL DEFAULT 0, last_success_time REAL DEFAULT 0,
        opened_at REAL DEFAULT 0, half_open_test_start REAL DEFAULT 0)""")
    conn.execute("CREATE TABLE IF NOT EXISTS idempotency_keys (key TEXT PRIMARY KEY, timestamp REAL)")
    conn.commit()
    return conn

def persist_circuit_breakers() -> None:
    with _circuit_lock:
        conn = _get_coord_db()
        for agent_id, breaker in _circuit_breakers.items():
            conn.execute("""INSERT INTO circuit_breakers (agent_id, failures, successes, state, last_failure_time,
                last_success_time, opened_at, half_open_test_start) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_id) DO UPDATE SET failures=?, successes=?, state=?, last_failure_time=?,
                last_success_time=?, opened_at=?, half_open_test_start=?""",
                (agent_id, breaker.failures, breaker.successes, breaker.state.value,
                 breaker.last_failure_time, breaker.last_success_time, breaker.opened_at, breaker.half_open_test_start,
                 breaker.failures, breaker.successes, breaker.state.value, breaker.last_failure_time,
                 breaker.last_success_time, breaker.opened_at, breaker.half_open_test_start))
        conn.commit()
        conn.close()

def load_circuit_breakers() -> None:
    conn = _get_coord_db()
    rows = conn.execute("SELECT * FROM circuit_breakers").fetchall()
    conn.close()
    with _circuit_lock:
        for row in rows:
            _circuit_breakers[row[0]] = CircuitBreakerState(agent_id=row[0], failures=row[1], successes=row[2],
                state=CircuitState(row[3]), last_failure_time=row[4], last_success_time=row[5],
                opened_at=row[6], half_open_test_start=row[7])

# ── MCP Handlers ───────────────────────────────────────────────────────────────
def handle_coordination(args: Dict[str, Any]) -> str:
    action = args.get("action", "status")
    if action == "circuit_status":
        agent_id = args.get("agent_id")
        result = get_circuit_status(agent_id) if agent_id else {"circuits": get_all_circuit_statuses()}
    elif action == "circuit_record_failure":
        result = record_failure(args.get("agent_id", ""))
    elif action == "circuit_record_success":
        result = record_success(args.get("agent_id", ""))
    elif action == "bulkhead_status":
        agent_type = args.get("agent_type")
        result = get_bulkhead_status(agent_type) if agent_type else {"bulkheads": get_all_bulkhead_statuses()}
    elif action == "bulkhead_acquire":
        result = {"acquired": acquire_bulkhead(args.get("agent_type", "default"))}
    elif action == "bulkhead_release":
        release_bulkhead(args.get("agent_type", "default"))
        result = {"released": True}
    elif action == "verify":
        ver = verify_result(args.get("result"), args.get("agent_id", ""), args.get("action_type", "general"))
        result = {"verified": ver.verified, "confidence": ver.confidence, "message": ver.message, "trace_id": ver.trace_id}
    elif action == "verification_history":
        result = {"verifications": get_verification_history(args.get("limit", 50))}
    elif action == "send":
        result = send_message(args.get("from_agent", ""), args.get("to_agent", ""),
                              args.get("content", {}), MessageType[args.get("msg_type", "DIRECT").upper()])
    elif action == "broadcast":
        result = broadcast_message(args.get("from_agent", ""), args.get("content", {}))
    elif action == "get_messages":
        result = {"messages": get_messages(args.get("agent_id", ""), args.get("limit", 50))}
    elif action == "register_agent":
        register_agent_inbox(args.get("agent_id", ""))
        result = {"registered": True}
    elif action == "trace":
        result = get_trace(args.get("trace_id", ""))
    elif action == "recent_traces":
        result = {"traces": get_recent_traces(args.get("limit", 20))}
    elif action == "persist":
        persist_circuit_breakers()
        result = {"persisted": True}
    elif action == "idempotency_key":
        key = generate_idempotency_key(*args.get("parts", []))
        result = {"key": key, "is_duplicate": check_idempotency(key)}
    else:
        result = {"error": f"unknown action: {action}"}
    return json.dumps(result, indent=2)

COORDINATION_SCHEMA = {
    "name": "coordination_primitives",
    "description": "Robust multi-agent coordination: circuit breakers, bulkheads, verification, idempotency, observability.",
    "parameters": {"type": "object", "properties": {
        "action": {"type": "string", "enum": ["circuit_status", "circuit_record_failure", "circuit_record_success",
            "bulkhead_status", "bulkhead_acquire", "bulkhead_release", "verify", "verification_history",
            "send", "broadcast", "get_messages", "register_agent", "trace", "recent_traces", "persist", "idempotency_key"]},
        "agent_id": {"type": "string"}, "agent_type": {"type": "string"}, "from_agent": {"type": "string"},
        "to_agent": {"type": "string"}, "msg_type": {"type": "string"}, "content": {"type": "object"},
        "result": {"type": "object"}, "action_type": {"type": "string"}, "trace_id": {"type": "string"},
        "limit": {"type": "integer"}, "parts": {"type": "array", "items": {"type": "string"}}}},
}

# ── Exported convenience functions ────────────────────────────────────────────
def coordination_circuit_status(agent_id: Optional[str] = None) -> Dict[str, Any]:
    return get_circuit_status(agent_id) if agent_id else {"circuits": get_all_circuit_statuses()}

def coordination_send(to_agent: str, message: Any, from_agent: str = "hermes") -> Dict[str, Any]:
    return send_message(from_agent, to_agent, message, MessageType.DIRECT)

def coordination_broadcast(message: Any, from_agent: str = "hermes") -> Dict[str, Any]:
    return broadcast_message(from_agent, message)

def coordination_verify(result: Any, agent_id: str = "hermes", action_type: str = "general") -> VerificationResult:
    return verify_result(result, agent_id, action_type)

def coordination_trace(trace_id: str) -> Dict[str, Any]:
    return get_trace(trace_id)

def coordination_register_agent(agent_id: str) -> None:
    register_agent_inbox(agent_id)

# Initialize: load persisted state
try:
    load_circuit_breakers()
except Exception:
    pass