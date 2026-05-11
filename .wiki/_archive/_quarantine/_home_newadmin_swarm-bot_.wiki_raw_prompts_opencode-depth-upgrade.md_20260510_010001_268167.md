---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/raw/prompts/opencode-depth-upgrade.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-10T01:00:01.268190"
}
---

---
title: Opencode Depth Upgrade
type: reference
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- prompts
created: '2026-04-14'
updated: '2026-04-14'
summary: '> Based directly on DEEP_AUDIT_2026-04-12.md by Claude Opus 4.6'
wikilinks: []
confidence: medium
source: research
---
# OPENCODE — DEPTH UPGRADE MASTER PROMPT
> Based directly on DEEP_AUDIT_2026-04-12.md by Claude Opus 4.6
> Overall score: 4.2/10. Target: 9/10.
> This is not a bug hunt. This is a depth upgrade.
> Paste this entire prompt into a new OpenCode session.

---

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  LEGION DEPTH UPGRADE — From 4.2/10 to 9/10                      ┃
┃  Source: Claude Opus 4.6 full repo audit, April 12 2026         ┃
┃  10 priorities. Work top to bottom. Do not skip.                ┃
┃  Every fix targets a specific file + function.                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

READ FIRST (before touching any code):
  SOUL.md
  DEEP_AUDIT_2026-04-12.md   ← THE AUDIT THAT GENERATED THIS PROMPT
  IMPLEMENTATION_STATUS.md
  main.py
  llm_client/__init__.py     ← 1809 lines, the LLM call heart
  core/system_prompt_builder.py  ← 13 injection layers

Do NOT touch: SOUL.md, CLAUDE.md, LEGION_MASTER.md

════════════════════════════════════════════════════════════════════
PRIORITY 1 — PRE-RESPONSE REASONING LOOP (Highest impact)
════════════════════════════════════════════════════════════════════

WHY: Claude found that every message follows the SAME path:
  classify intent → build context → single LLM call → send.
No thinking. No iteration. Legion cannot produce better output than the raw LLM.
This is the #1 fix that makes Legion go from chatbot to intelligent coworker.

CURRENT STATE:
  llm_client/__init__.py line ~1188: has "INTERNAL REASONING DISCIPLINE" in system
  prompt — but it\'s just TEXT telling the LLM to think. No code enforces it.
  core/cognition_pipeline.py: 117 lines, regex message shape detection. No decomposition.

TARGET: Create core/reasoning_loop.py

Implement this EXACT class:

  class ReasoningLoop:
      SKIP_THRESHOLD_WORDS = 15  # short simple questions skip reasoning
      SKIP_THRESHOLD_CONFIDENCE = 0.85  # high-confidence routing skips reasoning

      async def run(self, message: str, intent: str,
                    confidence: float) -> "ReasoningContext | None":
          """
          Returns None for simple questions (fast path).
          Returns ReasoningContext for complex questions (deep path).
          """
          word_count = len(message.split())
          is_simple = word_count < self.SKIP_THRESHOLD_WORDS and \
                      confidence >= self.SKIP_THRESHOLD_CONFIDENCE
          if is_simple:
              return None

          # Step 1: Decompose into sub-questions
          sub_questions = await self._decompose(message)

          # Step 2: Determine what sources are needed
          needs_search = self._needs_external(sub_questions, message)
          needs_memory = self._needs_memory(sub_questions, message)

          # Step 3: Gather in parallel
          search_ctx, memory_ctx = await asyncio.gather(
              self._gather_search(message) if needs_search else asyncio.sleep(0, result=""),
              self._gather_memory(message) if needs_memory else asyncio.sleep(0, result="")
          )

          return ReasoningContext(
              sub_questions=sub_questions,
              search_context=search_ctx,
              memory_context=memory_ctx,
              needs_search=needs_search,
              needs_memory=needs_memory
          )

      async def _decompose(self, message: str) -> list[str]:
          """Ask a cheap LLM to decompose the message into sub-questions.
          Use the cheapest/fastest available model. Return list of strings.
          Limit to max 3 sub-questions to avoid latency explosion."""
          ...

      def _needs_external(self, sub_questions: list, message: str) -> bool:
          """True if message contains: current/latest/today/news/price/weather
          or any sub-question requires external data."""
          EXTERNAL_KEYWORDS = {"latest", "current", "today", "news", "price",
                               "weather", "sekarang", "terbaru", "berita"}
          return any(kw in message.lower() for kw in EXTERNAL_KEYWORDS)

      def _needs_memory(self, sub_questions: list, message: str) -> bool:
          """True if message references past context: remember/told/said/before."""
          MEMORY_KEYWORDS = {"remember", "told", "said", "before", "earlier",
                             "sebelumnya", "tadi", "ingat", "bilang"}
          return any(kw in message.lower() for kw in MEMORY_KEYWORDS)

  @dataclass
  class ReasoningContext:
      sub_questions: list[str]
      search_context: str
      memory_context: str
      needs_search: bool
      needs_memory: bool

Wire to llm_client/__init__.py:
  Before the main LLM call:
    reasoning_ctx = await reasoning_loop.run(message, intent, confidence)
    if reasoning_ctx:
        # Inject reasoning context into messages[]
        messages = inject_reasoning_context(messages, reasoning_ctx)

Verify:
  Send "Hei" → reasoning_loop.run returns None (fast path)
  Send "Analisis trade-offs antara PostgreSQL dan MongoDB untuk use case high-write"
  → reasoning_loop.run returns ReasoningContext with 3 sub-questions

════════════════════════════════════════════════════════════════════
PRIORITY 2 — UNIFY MEMORY TO 2 TIERS (Biggest structural fix)
════════════════════════════════════════════════════════════════════

WHY: 8 memory subsystems + 4 facades = context bloat + silent data loss +
non-semantic retrieval. Asking "What\'s my main project?" fails because there\'s
no cosine similarity search, only keyword FTS.

CURRENT STATE (read these files first):
  core/memory/memory_manager.py  ← primary facade
  core/memory/unified_context.py  ← concatenates 3+ backends, no ranking
  core/legion_memory_facade.py   ← overlapping with memory_manager
  core/memory_engine.py          ← old version, also still active
  core/memory/episodic_store.py line ~120:  self._local = self._local[-2000:]
                                             ↑ SILENT DATA LOSS. Fix this first.

TARGET: 2-tier model

TIER 1 — WORKING MEMORY (in-process, session-scoped, fast)
  Location: core/memory/working_memory.py (already exists, keep it)
  Scope: current session only, cleared on bot restart
  Storage: Python dict, keyed by user_id
  Max size: 50 exchanges per user
  Use for: conversation history, pending follow-ups, session focus

TIER 2 — LONG-TERM MEMORY (persistent, cross-session, semantic)
  Location: core/memory/long_term_memory.py (create this)
  Backed by: SQLite for storage + sentence-transformers for embedding
  Schema:
    CREATE TABLE memories (
      id INTEGER PRIMARY KEY,
      user_id INTEGER NOT NULL,
      content TEXT NOT NULL,
      embedding BLOB,            -- serialized numpy array
      tags TEXT,                 -- JSON list of tags
      importance FLOAT DEFAULT 0.5,
      created_at TIMESTAMP,
      last_accessed TIMESTAMP,
      access_count INTEGER DEFAULT 0
    );
  Retrieval: embed user query → cosine similarity against stored embeddings
  → return top-5 most relevant memories
  Use for: user facts, preferences, past conversations, skill results

IMPLEMENTATION STEPS:

1. Fix data loss FIRST (quick win, 30 min):
   core/memory/episodic_store.py line ~120:
   WRONG: self._local = self._local[-2000:]
   RIGHT:
     if len(self._local) > 2000:
         # Summarize oldest 500 entries instead of deleting them
         old_entries = self._local[:500]
         summary = await self._summarize_batch(old_entries)
         self._local = [{\'type\': \'summary\', \'content\': summary,
                          \'timestamp\': old_entries[-1][\'timestamp\']}] + self._local[500:]

2. Create core/memory/long_term_memory.py with:
   - LongTermMemory class
   - store(user_id, content, tags=[]) → embed + insert
   - retrieve(user_id, query, top_k=5) → embed query + cosine similarity
   - forget(user_id, memory_id) → soft delete (importance = 0)
   - get_profile(user_id) → top 10 highest importance memories

3. Deprecate (do NOT delete yet — archive):
   Move core/legion_memory_facade.py → _archive/legion_memory_facade.py
   Move core/memory_engine.py → _archive/memory_engine.py
   Leave stubs that import from long_term_memory for backward compat.

4. Update core/memory/unified_context.py:
   REMOVE: fetching from 3+ backends and concatenating all
   REPLACE WITH:
     async def get_context(user_id, query, max_tokens=400) -> str:
         working = working_memory.get_recent(user_id, last_n=5)
         long_term = await long_term_memory.retrieve(user_id, query, top_k=5)
         profile = await long_term_memory.get_profile(user_id)
         # Build context with token budget, most relevant first
         context = build_with_budget([profile, long_term, working], max_tokens)
         return context

5. Ensure per-user isolation:
   All memory operations MUST take user_id as first argument.
   Run: grep -n "def store\|def retrieve\|def read\|def write" core/memory/*.py
   For any function missing user_id parameter: add it.

Verify:
  Store: ltm.store(12345, "I\'m building a rental website called rumahlabuh")
  Retrieve: ltm.retrieve(12345, "What is my main project?")  → should return the above
  Token budget: unified_context.get_context() never exceeds 400 tokens

════════════════════════════════════════════════════════════════════
PRIORITY 3 — WIRE SELF-IMPROVEMENT LOOP (Quickest win: code exists)
════════════════════════════════════════════════════════════════════

WHY: core/self_improvement.py already exists with maybe_run_self_review()
and buffer_conversation(). They are DEAD CODE — never called anywhere.
This is a 2-4 hour fix that makes Legion actually grow from conversations.

CURRENT STATE:
  Read core/self_improvement.py fully.
  Run: grep -rn "self_improvement\|maybe_run_self_review\|buffer_conversation" . --include="*.py"
  Confirm: 0 call sites outside of core/self_improvement.py itself.

TARGET: Wire to the main message pipeline.

1. In the main message handler (find where response is finalized and sent):
   Add AFTER response is sent to user:

   # Non-blocking: don\'t await, don\'t slow down response
   asyncio.create_task(
       self_improvement.buffer_conversation(
           user_id=user_id,
           user_message=user_message,
           legion_response=response,
           intent=intent
       )
   )

2. Set up periodic self-review:
   In main.py scheduler section (or create one):

   # Every 50 messages, run a self-review
   # Track message count in memory or simple counter file
   MESSAGE_COUNT_FILE = "data/message_count.json"

   async def maybe_trigger_self_review():
       count = load_message_count()
       count += 1
       save_message_count(count)
       if count % 50 == 0:
           asyncio.create_task(self_improvement.maybe_run_self_review())

3. Read what maybe_run_self_review() does:
   Does it update SOUL.md? Update beliefs.json? Update a knowledge file?
   Verify it does something meaningful. If it\'s also a stub: implement it:

   async def maybe_run_self_review():
       """Analyze last 50 conversations. Extract:
       - Topics Bashara frequently asks about → add to wiki
       - Questions Legion answered poorly (user corrected) → log for improvement
       - New facts about Bashara → store in long-term memory with high importance
       - Recurring intents with low confidence → update intent router keywords
       """
       recent = await get_recent_conversations(n=50)
       analysis = await call_llm(messages=build_self_review_prompt(recent),
                                 model="cheapest_available")
       await apply_self_review_learnings(analysis)
       logger.info(f"Self-review complete: {analysis[:200]}")

Verify:
  Send 3 messages to bot.
  Check that buffer_conversation was called 3 times (add log line to confirm).
  Check data/message_count.json increments.

════════════════════════════════════════════════════════════════════
PRIORITY 4 — KILL FAKE SPECIALTIES, DEEPEN REAL ONES
════════════════════════════════════════════════════════════════════

WHY: 76 agents declared, ~15 real. Empty __init__.py files for design, legal,
marketing, ML. This is theater that adds complexity without value.
Better 15 agents at 9/10 than 76 at 2/10.

STEP 1 — Read config/departments.yaml fully.
For each department listed, check if corresponding agents/ directory has real code:
  python -c "
  import os, yaml
  with open(\'config/departments.yaml\') as f:
      depts = yaml.safe_load(f)
  for dept in depts.get(\'departments\', []):
      name = dept.get(\'name\', dept) if isinstance(dept, dict) else dept
      path = f\'agents/{name}\'
      if os.path.exists(path):
          files = [f for f in os.listdir(path) if f.endswith(\'.py\')] 
          total = sum(os.path.getsize(os.path.join(path, f)) for f in files)
          print(f\'{name}: {len(files)} files, {total} bytes\')
      else:
          print(f\'{name}: DIRECTORY MISSING\')
  "

STEP 2 — Archive departments with 0 real implementation:
  Based on Claude\'s audit, these are NONEXISTENT (confirm then act):
  - design/     (empty __init__.py)
  - legal/      (empty __init__.py)
  - marketing/  (empty __init__.py)
  - ml/         (config entry only)
  - strategy/   (config entry only)
  For each: move to _archive/agents/{name}/ and remove from departments.yaml

STEP 3 — Keep and note the REAL ones:
  Based on Claude\'s audit, these are real or partial:
  - research    (tools/deep_research.py has 5-layer pipeline → DEEPEN)
  - debate      (core/debate_engine.py, stances, opinion injection → DEEPEN)
  - coding      (separate model + prompt → add sandbox execution)
  - computer    (tool-calling + screenshot loop → keep)
  - web_search  (Brave Search, solid → add memory storage)

STEP 4 — Deepen Research agent (highest value for Bashara):
  tools/deep_research.py already has 5-layer pipeline.
  Add to it:
    a. After research completes: store summary in long_term_memory
       with tags=["research", topic, date]
    b. Before research: check long_term_memory for past research on same topic
       If found within 7 days: include as baseline context
    c. Add /research <topic> command that directly invokes deep_research pipeline
       and returns formatted findings in Telegram message

STEP 5 — Deepen Debate agent:
  core/debate_engine.py has one-turn opinion injection.
  Make it multi-turn:
    a. When user pushes back on Legion\'s stated opinion:
       detect_counter_argument(user_message, previous_legion_opinion) → bool
    b. If counter detected: enter DEBATE MODE:
       - Legion gathers 2-3 supporting evidence points for its position
       - Legion acknowledges the strongest part of user\'s counter
       - Legion either defends or updates its stance
       - If stance updates: record in data/beliefs.json
    c. Add /debate <topic> command: Legion states its position, invites rebuttal

Verify:
  python -c "import yaml; d = yaml.safe_load(open(\'config/departments.yaml\')); print(len(d.get(\'departments\',d)))"
  Count should decrease from 76+ to <= 20.
  Run: python scripts/verify_wiring.py  → must still pass.

════════════════════════════════════════════════════════════════════
PRIORITY 5 — CLARIFYING QUESTIONS (Make Legion feel thoughtful)
════════════════════════════════════════════════════════════════════

WHY: When intent confidence < 0.4, Legion defaults to "conversation" skill.
This means ambiguous messages get generic chatbot responses instead of
Legion asking what the user actually needs.

CURRENT STATE:
  core/intent_router.py: Read it. Find the fallback/low-confidence path.
  Find the exact condition where it falls through to default.

TARGET: Create core/clarification.py

  AMBIGUITY_THRESHOLD = 0.4  # confidence below this triggers clarification
  SHORT_MESSAGE_THRESHOLD = 8  # words

  async def should_clarify(message: str, intent: str,
                            confidence: float) -> bool:
      """Return True if we should ask a clarifying question."""
      word_count = len(message.split())
      is_short = word_count < SHORT_MESSAGE_THRESHOLD
      is_low_confidence = confidence < AMBIGUITY_THRESHOLD

      # Don\'t clarify if: greeting, single-word command, continuation of prior topic
      NEVER_CLARIFY = {"hei", "hai", "hi", "hello", "oke", "ok", "thanks",
                       "makasih", "yes", "no", "ya", "nope"}
      if message.lower().strip() in NEVER_CLARIFY:
          return False

      return is_short and is_low_confidence

  async def generate_clarification(message: str, intent: str) -> str:
      """Generate a SINGLE specific clarifying question. Not a list. Not vague.
      Examples:
        User: \'fix this\' → \'Fix what exactly? Paste the code or error.\'  
        User: \'translate\' → \'Translate what, and to which language?\'  
        User: \'search\' → \'Search for what topic?\'  
      Keep the question to 1 sentence maximum. Legion\'s voice: direct, no fluff."""
      ...

Wire to core/intent_router.py:
  After intent classification, before routing to handler:
    if await clarification.should_clarify(message, intent, confidence):
        question = await clarification.generate_clarification(message, intent)
        await update.message.reply_text(question)
        return  # Don\'t proceed. Wait for user\'s clarified message.

Verify:
  Send "fix this" → Legion asks a clarifying question, not a generic LLM answer
  Send "Hei" → Legion responds normally (not a clarifying question)
  Send "Analisis sistem memory yang terbaik untuk AI agent" → Legion proceeds normally

════════════════════════════════════════════════════════════════════
PRIORITY 6 — RESPONSE QUALITY GATE
════════════════════════════════════════════════════════════════════

WHY: Currently if LLM returns a shallow/vague/wrong answer, it gets sent.
No system checks response quality before sending.

Create core/quality_gate.py:

  class QualityGate:
      MAX_RETRIES = 1  # never retry more than once — latency matters

      async def check(self, user_message: str, response: str,
                      intent: str) -> QualityResult:
          issues = []

          # Issue 1: Too short for complex question
          if len(user_message.split()) > 20 and len(response.split()) < 30:
              issues.append("SHALLOW: complex question got < 30 word answer")

          # Issue 2: Explicit uncertainty without search trigger
          UNCERTAINTY_SIGNALS = ["I don\'t know", "I\'m not sure", "gw ga tau",
                                  "tidak yakin", "mungkin", "I think but am not certain"]
          if any(s.lower() in response.lower() for s in UNCERTAINTY_SIGNALS):
              issues.append("UNCERTAIN: response contains uncertainty without search")

          # Issue 3: Response contains forbidden LLM artifacts
          FORBIDDEN = ["As an AI", "I cannot", "I\'m unable to", "As a language model"]
          if any(f.lower() in response.lower() for f in FORBIDDEN):
              issues.append("ARTIFACT: LLM identity artifact in response")

          return QualityResult(issues=issues, should_retry=len(issues) > 0)

      async def retry(self, messages: list, issues: list) -> str:
          """One retry with explicit instruction to fix the issues."""
          retry_instruction = (
              "Your previous response had these issues: " + ", ".join(issues) +
              ". Fix them. Be concrete, specific, and stay in Legion\'s voice."
          )
          messages = messages + [{"role": "user", "content": retry_instruction}]
          return await call_llm(messages=messages)

Wire to main message pipeline:
  response = await call_llm(messages)
  quality = await quality_gate.check(user_message, response, intent)
  if quality.should_retry:
      logger.info(f"Quality gate triggered: {quality.issues}")
      response = await quality_gate.retry(messages, quality.issues)
  await update.message.reply_text(response)

Verify:
  Mock LLM to return "I don\'t know" → quality gate triggers retry
  Mock LLM to return short answer to long question → quality gate triggers retry
  Mock LLM to return "As an AI" → quality gate catches the artifact

════════════════════════════════════════════════════════════════════
PRIORITY 7 — CONSOLIDATE 4 ORCHESTRATORS INTO 1
════════════════════════════════════════════════════════════════════

WHY: 4 orchestrators with unclear ownership:
  task_orchestrator.py  (492 lines)
  core/legion_swarm.py  (322 lines) ← THE REAL ONE (hardcodes 11-agent LEGION_TEAM)
  core/nexus_orchestrator.py  (semantic routing)
  core/jarvis_orchestrator.py (context bundling)

The problem: legion_swarm.py ignores the 76-agent registry entirely.
  Its LEGION_TEAM is hardcoded.

TARGET: Single orchestrator that uses the REAL agent registry.

FILE: core/orchestrator.py (create as consolidation)

STEP 1: Read all 4 orchestrator files completely.
Map what each one uniquely provides:
  task_orchestrator: task decomposition, SwarmDebateOrchestrator with 6 personas
  legion_swarm: 3-phase execution (propose → debate → synthesize), 11-agent team
  nexus: 3-layer routing (keyword → semantic → LLM), sentence-transformers
  jarvis: context bundling (memory + Screenpipe + WhatsApp + calendar)

STEP 2: Create core/orchestrator.py merging the unique value of each:

  class LegionOrchestrator:
      def __init__(self):
          self.agent_registry = AgentRegistry()  # from core/agent_registry.py
          self.router = NexusRouter()  # merge nexus routing logic

      async def run(self, task: str, user_id: int) -> str:
          # Phase 1: Route and select team from REAL registry
          team = await self.agent_registry.select_team(
              task_description=task,
              max_agents=5
          )

          if len(team) == 1:
              # Simple: single agent
              return await self._run_single(team[0], task, user_id)
          else:
              # Complex: multi-agent debate
              return await self._run_debate(team, task, user_id)

      async def _run_debate(self, team, task, user_id) -> str:
          # Phase 1: Propose (all agents respond in parallel)
          proposals = await asyncio.gather(*[
              self._agent_respond(agent, task) for agent in team
          ])

          # Phase 2: Debate (each agent sees others\' proposals)
          debate_prompt = self._build_debate_prompt(proposals)
          rebuttals = await asyncio.gather(*[
              self._agent_respond(agent, debate_prompt) for agent in team
          ])

          # Phase 3: Synthesize (supervisor picks best + synthesizes)
          return await self._synthesize(task, proposals, rebuttals)

STEP 3: Archive old orchestrators:
  Move to _archive/: task_orchestrator.py, core/nexus_orchestrator.py,
  core/jarvis_orchestrator.py, core/legion_swarm.py
  Leave stubs that import from core/orchestrator.py

STEP 4: Add select_team() to core/agent_registry.py:
  async def select_team(self, task_description: str,
                        max_agents: int = 5) -> list[AgentDef]:
      # Embed task description
      # Cosine similarity against each agent\'s capabilities list (also embedded)
      # Return top-k agents sorted by similarity score
      ...

Verify:
  python -c "from core.orchestrator import LegionOrchestrator; print(\'OK\')"
  Send /swarm <complex task> → confirm it uses core/orchestrator.py

════════════════════════════════════════════════════════════════════
PRIORITY 8 — FIX FAKE SKILLS (Timer + Code Review)
════════════════════════════════════════════════════════════════════

WHY: Claude scored Timer 1/10 and Code Review 0/10 — they\'re theater.
If a user sets a timer and it doesn\'t fire, they never trust the bot again.

FIX TIMER (core/skills/timer.py or equivalent):

  async def execute(self, user_id: int, context: CallbackContext,
                    duration_seconds: int, reminder_text: str) -> str:
      """Actually set a real async timer that sends a Telegram message."""

      async def send_reminder():
          await asyncio.sleep(duration_seconds)
          try:
              await context.bot.send_message(
                  chat_id=user_id,
                  text=f"⏰ Timer! {reminder_text}"
              )
          except Exception as e:
              logger.error(f"Timer failed for user {user_id}: {e}")

      asyncio.create_task(send_reminder())
      minutes = duration_seconds // 60
      return f"✅ Timer set for {minutes} minute(s). I\'ll ping you."

FIX CODE REVIEW (core/skills/code_review.py or equivalent):

  async def execute(self, code: str, language: str = "auto") -> str:
      """Actually review the provided code using the coding LLM."""
      if not code or len(code.strip()) < 10:
          return "Paste the code you want me to review."

      review_prompt = f"""
      Review this {language} code. Be specific and actionable.
      Format your review as:
      1. BUGS: Any actual bugs or errors (not style)
      2. PERFORMANCE: Any O(n²) or unnecessary operations
      3. SECURITY: Any injection, auth, or exposure risks
      4. IMPROVEMENTS: Top 2-3 concrete improvements
      5. VERDICT: Ship it / Needs work / Rewrite (pick one)

      Code:
      {code}
      """
      return await call_llm(
          messages=[{"role": "user", "content": review_prompt}],
          model="coding_model"  # use the coding-specialized model
      )

Verify:
  /timer 1 Test reminder → wait 60 seconds → bot sends reminder message
  /review followed by a code block → bot returns structured BUGS/PERFORMANCE/etc.

════════════════════════════════════════════════════════════════════
PRIORITY 9 — ADD /CAPABILITIES AND /SELF_REPORT COMMANDS
════════════════════════════════════════════════════════════════════

WHY: Legion can\'t explain itself. No /capabilities. No honest status.
core/capability_audit.py exists but its output is never surfaced to user.

ADD to handlers/admin_handlers.py or handlers/capabilities.py:

  async def handle_capabilities(update, context):
      """Returns honest list of what works vs what\'s partial vs what\'s stub."""
      from core.capability_audit import CapabilityAudit
      audit = CapabilityAudit()
      results = await audit.run_all()  # runs the 16 capability checks

      lines = ["*Legion Capabilities — Honest Status*\n"]
      for cap in results:
          if cap.status == "working":
              lines.append(f"✅ {cap.name}")
          elif cap.status == "partial":
              lines.append(f"⚠️ {cap.name} (partial)")
          else:
              lines.append(f"❌ {cap.name} (not ready)")

      await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

  async def handle_self_report(update, context):
      """24h activity report — what Legion did, failed at, learned."""
      # Pull from:
      # - message count file (how many convos)
      # - self_improvement buffer (what was learned)
      # - quality gate retry log (what responses were retried)
      report = await build_self_report_24h()
      await update.message.reply_text(report)

Register in main.py:
  app.add_handler(CommandHandler("capabilities", handle_capabilities))
  app.add_handler(CommandHandler("self_report", handle_self_report))

Verify:
  /capabilities → returns list with ✅ ⚠️ ❌ icons, honest status
  /self_report → returns 24h summary with message count and learnings

════════════════════════════════════════════════════════════════════
PRIORITY 10 — CONTEXT WINDOW BUDGET MANAGEMENT
════════════════════════════════════════════════════════════════════

WHY: All 13 prompt injection layers concatenated linearly.
1500+ token memory block per turn when all layers are full.
No priority pruning. No compression when context is tight.

FILE: core/system_prompt_builder.py (377 lines, modify)

Add token counting and priority-based budget:

  import tiktoken  # or use rough estimate: len(text) // 4

  MODEL_CONTEXT_LIMITS = {
      "default": 16000,
      "gpt-4o": 128000,
      "claude-3-5-haiku": 200000,
  }
  CONTEXT_BUDGET_RATIO = 0.35  # use max 35% of context for system prompt

  # Priority order (highest to lowest):
  LAYER_PRIORITY = [
      "soul",           # ALWAYS included, never compressed
      "user_profile",   # ALWAYS included (top 5 facts only)
      "working_memory", # Last 5 exchanges, compressed if tight
      "relevant_memory",# Top-3 semantic results, dropped if very tight
      "wiki_context",   # Only if directly relevant to query
      "search_results", # Only if search was triggered
      "personality",    # Compressed to key traits if tight
      "skill_context",  # Only if skill was triggered
  ]

  async def build_system_prompt(user_id, query, model="default",
                                 extras={}) -> str:
      budget_tokens = int(MODEL_CONTEXT_LIMITS.get(model, 16000)
                          * CONTEXT_BUDGET_RATIO)
      used_tokens = 0
      sections = []

      for layer_name in LAYER_PRIORITY:
          content = await get_layer_content(layer_name, user_id, query, extras)
          if not content:
              continue
          layer_tokens = estimate_tokens(content)
          if used_tokens + layer_tokens > budget_tokens:
              # Try compressing
              compressed = await compress_section(content, target_tokens=200)
              if used_tokens + 200 <= budget_tokens:
                  sections.append(compressed)
                  used_tokens += 200
              # If still over budget: skip this layer
          else:
              sections.append(content)
              used_tokens += layer_tokens

      logger.debug(f"System prompt: {used_tokens}/{budget_tokens} tokens, "
                   f"{len(sections)}/{len(LAYER_PRIORITY)} layers")
      return "\n\n".join(sections)

Verify:
  Build system prompt for 5 different message types
  Confirm: token count never exceeds budget
  Confirm: soul is always first
  Confirm: log line appears for each build

════════════════════════════════════════════════════════════════════
FINAL GATE: Run after all 10 priorities are done
════════════════════════════════════════════════════════════════════

  # 1. Import check
  python -c "
  from core.reasoning_loop import ReasoningLoop
  from core.memory.long_term_memory import LongTermMemory
  from core.quality_gate import QualityGate
  from core.clarification import should_clarify
  from core.orchestrator import LegionOrchestrator
  print(\'All new modules import OK ✅\')
  "

  # 2. Wiring check
  python scripts/verify_wiring.py

  # 3. Integration tests
  python -m pytest tests/ -v --tb=short

  # 4. Combined gate
  python scripts/verify_wiring.py && pytest tests/ -v -q && \
  echo "🟢 Legion: 4.2/10 → Target 9/10 — Upgrades applied"

════════════════════════════════════════════════════════════════════
HARD RULES
════════════════════════════════════════════════════════════════════

1. Work ONE priority at a time. Do not start Priority 2 until Priority 1 passes verify.
2. After EACH priority: run python scripts/verify_wiring.py to confirm nothing broke.
3. Do NOT delete files — always move to _archive/ first.
4. Do NOT touch SOUL.md, CLAUDE.md, LEGION_MASTER.md.
5. If a priority would take > 8 hours to do correctly: do 70% of it correctly
   rather than 100% of it poorly. Partial is better than fake.
6. Every new file must have: proper imports, async def, try/except, logger calls.
7. The goal is not completing all 10. The goal is:
   “After this session, Legion does 3-5 things DEEPLY that it currently does shallowly.”
```
