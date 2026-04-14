---
title: Audit15 Tasks
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '> Planner output for @worker agents | Generated: 2026-04-12'
wikilinks: []
confidence: medium
source: research
---
# AUDIT 15 — Final Integration Test Plan
> Planner output for @worker agents | Generated: 2026-04-12
## Context
### Message Flow Architecture
1. **Entry**: `handlers/ai.py` (commands) + `handlers/message_handler.py` (plain text)
2. **Routing**: `AutonomousRouter.analyze_async()` → skill → handler
3. **Execution**: `_execute_chat()` (shared.py) → `llm_client.chat()` → `litellm.acompletion()`
4. **Response**: `send_chunked()` → `msg.answer()`
### Key Code Locations
- `llm_client/__init__.py` lines 963-1520: `chat()` builds messages[] (soul FIRST, user LAST)
- `llm_client/__init__.py` line 420: `await acompletion(**api_kwargs)` — THE LLM call
- `llm_client/__init__.py` lines 1025-1224: Soul/memory/wiki context injection
- `handlers/shared.py` lines 336-386: `_execute_chat()` — calls `llm_client.chat()`
- `handlers/message_handler.py` lines 129-364: `handle_plain_message()` — autonomous routing
- `core/soul_engine.py` lines 358-429: `build_enhanced_soul_context()` — soul injection
- `core/conversation_interface.py`: `add_to_conversation()` for history tracking
### What Must Be True (Invariant)
> **Soul must always be first in messages[]**  
> Verified at line 1026-1028: `_audit_messages.append({"role": "system", "content": _soul})`

## 10 Test Scenarios

### Scenario 1: Basic NL → LLM → Reply
**File**: `tests/test_integration.py::test_basic_nl_flow`  
**Flow**: User sends plain NL → `handle_plain_message` → `AutonomousRouter.analyze_async()` → `_execute_chat` → `chat()` → `acompletion` → `msg.answer`  
**Assertions**:
- A) `acompletion` was called (capture via mock)
- B) messages[0]["role"] == "system" and "Legion" in messages[0]["content"] (soul first)
- C) messages[-1]["role"] == "user" (user message last)
- D) `msg.answer` was called with non-empty text

**Mock**: `litellm.acompletion`  
**Real**: `AutonomousRouter`, `shared._execute_chat`, `llm_client.chat`

---

### Scenario 2: /think Command Flow
**File**: `tests/test_integration.py::test_think_command`  
**Flow**: `/think what is consciousness` → `cmd_think` → `agent_loop` → `chat` → `acompletion`  
**Assertions**:
- A) `acompletion` called with messages containing the think task
- B) Response is non-empty string
- C) `msg.answer` called

**Mock**: `litellm.acompletion`  
**Real**: `core.agent.cmd_think_impl`, `shared._execute_chat`

---

### Scenario 3: /run Command Flow
**File**: `tests/test_integration.py::test_run_command`  
**Flow**: `/run explain quantum entanglement` → `cmd_run` → `_execute_chat` → `chat` → `acompletion`  
**Assertions**:
- A) Agent key resolved to "coding" or similar
- B) `acompletion` called with agent-specific system prompt
- C) `msg.answer` called

---

### Scenario 4: AutonomousRouter Memory-Recall
**File**: `tests/test_integration.py::test_memory_recall_route`  
**Flow**: User says "remember what I said about Tokyo" → `AutonomousRouter.analyze_async` → skill=memory_recall → `memory.search()` → enriched prompt → `chat()` → `acompletion`  
**Assertions**:
- A) `acompletion` called with enriched prompt containing memory context
- B) Memory search returned results (verify by checking messages content)
- C) `msg.answer` called

**Setup**: Pre-seed memory with known fact about "Tokyo"

---

### Scenario 5: /swarm Multi-Agent Execution
**File**: `tests/test_integration.py::test_swarm_command`  
**Flow**: `/swarm design a web app` → `cmd_swarm` → `run_topology(concurrent)` → multiple `chat()` calls in parallel  
**Assertions**:
- A) `acompletion` called >= 4 times (general, coding, debug, architect agents)
- B) Final response aggregated from all agents
- C) `msg.answer` called with swarm result

**Note**: May be slow — mock LLM to return quickly

---

### Scenario 6: /multi_execute Comparison
**File**: `tests/test_integration.py::test_multi_execute`  
**Flow**: `/multi_execute analyze this data` → `cmd_multi_execute` → 3x `chat()` in parallel (coding, architect, analyst) → synthesis → `verify_and_repair` → `msg.answer`  
**Assertions**:
- A) `acompletion` called exactly 4 times (3 agents + synthesis)
- B) Synthesis LLM call received outputs from all 3 agents
- C) Final report contains quality gate info

---

### Scenario 7: Soul First Invariant (CRITICAL)
**File**: `tests/test_integration.py::test_soul_always_first`  
**Flow**: ANY message → `chat()` → `acompletion`  
**Assertions**:
- For EACH of 5 different input types (plain NL, /run, /think, /swarm, /multi_execute):
  - messages[0]["role"] == "system"
  - "Legion" in messages[0]["content"] (identity marker)
  - messages[-1]["role"] == "user" (user message last)
- This is the KEY invariant — must hold across ALL code paths

**Method**: Create 5 parameterized sub-tests, capture messages[] for each

---

### Scenario 8: Message Memory Storage
**File**: `tests/test_integration.py::test_memory_stored_after_chat`  
**Flow**: User sends message → `chat()` completes → `_post_call_hooks()` → `MemoryEngine.store()`  
**Assertions**:
- A) `acompletion` called
- B) After chat completes, `MemoryEngine` has stored the turn
- C) Verify stored turn has `user` and `assistant` fields

**Setup**: Use in-memory MemoryEngine (no DB setup needed)

---

### Scenario 9: Jarvis Full-Context Bundle
**File**: `tests/test_integration.py::test_jarvis_bundle`  
**Flow**: User sends plain text that triggers jarvis handler → `gather_jarvis_bundle()` → multiple context sources → `compose_jarvis_response()` → `chat()` → `acompletion` → `msg.answer`  
**Assertions**:
- A) `acompletion` called
- B) Response is HTML-formatted bundle
- C) `msg.answer` called with chunked output

**Setup**: Mock LEGION_JARVIS_AUTOROUTE_ENABLED=1

---

### Scenario 10: End-to-End Complex Task
**File**: `tests/test_integration.py::test_e2e_complex_task`  
**Flow**: Full user scenario: "research the latest AI developments and summarize for me" → AutonomousRouter routes to "research" → `chat(agent=researcher)` → `acompletion` with web search context → `msg.answer`  
**Assertions**:
- A) LLM called with research-mode system prompt
- B) Response contains structured research output
- C) `msg.answer` called

---

## Mock Strategy

### What to Mock (ONLY external I/O)
```python
# LLM — mock at litellm.acompletion level
with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mocked Legion response with soul context properly injected"
    mock_response.choices[0].message.tool_calls = None
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    mock_llm.return_value = mock_response
    
    # Test code here — capture messages by examining call_args
```

### What NOT to Mock (real components)
- `AutonomousRouter` — real routing logic
- `shared._execute_chat` — real handler glue
- `llm_client.chat` — real message building (must test soul-first invariant)
- `MemoryEngine` — real storage (in-memory)
- `SoulEngine` — real identity

### Capture messages[] for verification
```python
captured_messages = []

async def capture_acompletion(*args, **kwargs):
    captured_messages.extend(kwargs.get("messages", args[0] if args else []))
    return mock_response

mock_llm.side_effect = capture_acompletion
```

---

## Implementation Order (Task Dependency Graph)

```
Phase 1: Foundation (Tasks 1-3)
├── Task 1: Create test_integration.py skeleton + fixtures
├── Task 2: Implement test_basic_nl_flow (validates mock setup)
└── Task 3: Implement test_soul_always_first (validates soul-first invariant)

Phase 2: Command Handlers (Tasks 4-6)
├── Task 4: Implement test_think_command
├── Task 5: Implement test_run_command  
└── Task 6: Implement test_memory_recall_route

Phase 3: Multi-Agent (Tasks 7-8)
├── Task 7: Implement test_swarm_command
└── Task 8: Implement test_multi_execute

Phase 4: Memory + E2E (Tasks 9-10)
├── Task 9: Implement test_memory_stored_after_chat
└── Task 10: Implement test_jarvis_bundle + test_e2e_complex_task

Review: All tasks → @reviewer
```

---

## Subtask Briefs for @worker

### Task 1: Create skeleton + fixtures
**File**: `tests/test_integration.py`  
**What**: 
- Create `TestIntegration` class
- Add `@pytest.fixture` for `mock_llm_with_capture()` that patches `litellm.acompletion` and captures messages
- Add helper `async def send_test_message(text, mock_msg)` fixture
- Import all needed modules at top

**Assertions to implement**: None yet — just scaffolding

**Dependencies**: None

---

### Task 2: test_basic_nl_flow
**File**: `tests/test_integration.py::TestIntegration::test_basic_nl_flow`  
**What**: 
- Call `handle_plain_message(mock_msg, auto_router)` with plain NL
- Verify `mock_llm.call_count >= 1`
- Verify `captured_messages[0]["role"] == "system"` and "Legion" in content
- Verify `captured_messages[-1]["role"] == "user"`

**Dependencies**: Task 1

---

### Task 3: test_soul_always_first
**File**: `tests/test_integration.py::TestIntegration::test_soul_always_first`  
**What**: 
- Parameterized over 5 message types: plain NL, /run, /think, /swarm trigger, /multi_execute trigger
- For each: send message → capture messages[] → assert [0] is soul, [-1] is user
- This is the CRITICAL invariant test

**Dependencies**: Tasks 1, 2

---

### Task 4: test_think_command
**File**: `tests/test_integration.py::TestIntegration::test_think_command`  
**What**: 
- Simulate `/think what is consciousness` message
- Call through `cmd_think` handler path
- Verify LLM called, response non-empty, answer sent

**Dependencies**: Task 1

---

### Task 5: test_run_command
**File**: `tests/test_integration.py::TestIntegration::test_run_command`  
**What**: 
- Simulate `/run explain quantum entanglement` message
- Call through `cmd_run` handler path
- Verify LLM called with coding agent prompt, answer sent

**Dependencies**: Task 1

---

### Task 6: test_memory_recall_route
**File**: `tests/test_integration.py::TestIntegration::test_memory_recall_route`  
**What**: 
- Pre-seed MemoryEngine with known fact about "Tokyo"
- Send message "what did I say about Tokyo?"
- Verify AutonomousRouter routes to memory_recall
- Verify LLM called with enriched memory context
- Verify answer sent

**Dependencies**: Tasks 1, 2

---

### Task 7: test_swarm_command
**File**: `tests/test_integration.py::TestIntegration::test_swarm_command`  
**What**: 
- Simulate `/swarm design a web app` message
- Verify `acompletion` called >= 4 times (4 agents in concurrent topology)
- Verify final response aggregated

**Dependencies**: Task 1

---

### Task 8: test_multi_execute
**File**: `tests/test_integration.py::TestIntegration::test_multi_execute`  
**What**: 
- Simulate `/multi_execute analyze this data` message
- Verify exactly 4 LLM calls (3 agents + synthesis)
- Verify quality gate info in response

**Dependencies**: Task 1

---

### Task 9: test_memory_stored_after_chat
**File**: `tests/test_integration.py::TestIntegration::test_memory_stored_after_chat`  
**What**: 
- Send any message through chat
- After chat completes, verify MemoryEngine stored the turn
- Query memory and verify turn is retrievable

**Dependencies**: Task 1

---

### Task 10: test_jarvis_bundle + test_e2e_complex_task
**File**: `tests/test_integration.py::TestIntegration::test_jarvis_bundle` + `test_e2e_complex_task`  
**What**: 
- Jarvis: Mock jarvis env vars, send message triggering jarvis route, verify bundle response
- E2E: Send research request, verify full research-mode flow with answer

**Dependencies**: Tasks 1-9

---

## Review Criteria

After all tasks complete, @reviewer verifies:
1. All 10 tests pass with `pytest tests/test_integration.py -x --asyncio-mode=auto -q`
2. Soul is first in messages[] for ALL test scenarios (captured in test 3)
3. No handler modules are mocked — only external I/O (acompletion, Telegram API)
4. Each test asserts: A) data reaches LLM, B) LLM called, C) reply sent
5. Test file is properly formatted (ruff check passes)

---

## Key Files Reference

| Purpose | File |
|---------|------|
| Message building (soul first) | `llm_client/__init__.py` lines 1019-1224 |
| LLM call | `llm_client/__init__.py` line 420 |
| _execute_chat | `handlers/shared.py` lines 336-386 |
| handle_plain_message | `handlers/message_handler.py` lines 129-364 |
| Soul engine | `core/soul_engine.py` lines 358-429 |
| Memory engine | `core/memory_engine.py` lines 376-398 |
| conftest fixtures | `tests/conftest.py` |
| Existing test patterns | `tests/test_legion_wiring.py` |