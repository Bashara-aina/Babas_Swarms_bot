# AUDIT 06 — LLM Client Layer
> Paste this entire prompt into a new OpenCode session.
> Goal: one unified LLM client, proper tool_call handling, model fallback wired.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 06 — LLM Client Layer                             ║
║  Fix: unified client, tool calls returned, fallback wired       ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — FIND ALL LLM CLIENT FILES
Check both locations:
  llm_client.py (root level file)
  llm_client/ (directory)
Search codebase for all imports of either:
  from llm_client import ...
  import llm_client
  from llm_client. import ...

STEP 2 — CONSOLIDATE IF DUPLICATED
If both llm_client.py and llm_client/ exist and are used by different files:
  Make llm_client.py a shim:
    from llm_client.client import *
  Move all real logic into llm_client/client.py
  Update all imports to use llm_client/ version

STEP 3 — VERIFY THE INTERFACE
The canonical function signature should be:
  async def call_llm(
      messages: list[dict],
      model: str = None,
      tools: list = None,
      stream: bool = False,
      **kwargs
  ) -> str | dict

If the function has a different signature: check all callers and align them.
The return value must be:
  - A plain string (extracted message content) for normal calls
  - A dict with {"type": "tool_call", "name": ..., "args": ...} when LLM returns a tool_call
  Never return the raw litellm response object to callers.

STEP 4 — TOOL CALL RETURN
Find where litellm.acompletion() is called.
Check if the response is checked for tool_calls:
  if response.choices[0].message.tool_calls:
      # handle tool call
      return {"type": "tool_call", "name": ..., "args": ...}
If this check is missing: add it.
If tool_calls are silently discarded: fix to return them to the caller.

STEP 5 — MODEL FALLBACK
Verify OPENROUTER_API_KEY is loaded from environment.
Verify litellm is configured with:
  litellm.api_base = "https://openrouter.ai/api/v1"
  litellm.api_key = os.getenv("OPENROUTER_API_KEY")
Add fallback_models list:
  FALLBACK_CHAIN = [
      "anthropic/claude-3-5-haiku",
      "openai/gpt-4o-mini",
      "google/gemini-2.0-flash"
  ]
Use litellm.acompletion with fallbacks= parameter OR implement manual try/except chain.

STEP 6 — VERIFY
Run: python -c "from llm_client import call_llm; print('OK')"
Confirm no ImportError.
Confirm the function exists with correct signature.

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
