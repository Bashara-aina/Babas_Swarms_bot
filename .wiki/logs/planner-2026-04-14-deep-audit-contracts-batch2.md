### CONTRACT #6: Async Compliance & Memory Architecture

WHAT:
  Audit swarm-bot for async violations (blocking I/O, time.sleep, threading) and memory architecture (facade vs mem0 vs memory_manager confusion). Check if any blocking I/O remains in handlers/core/agents.

FILES:
  READ:
    - /home/newadmin/swarm-bot/core/memory/ (entire directory if exists)
    - /home/newadmin/swarm-bot/.wiki/concepts/memory-architecture.md
    - /home/newadmin/swarm-bot/.wiki/concepts/memory-system-architecture.md
    - /home/newadmin/swarm-bot/.wiki/architecture/memory-gaps-analysis.md
    - /home/newadmin/swarm-bot/.wiki/architecture/memory-system-architecture.md
    - /home/newadmin/swarm-bot/llm_client.py
    - /home/newadmin/swarm-bot/main.py (sample for I/O patterns)
    - /home/newadmin/swarm-bot/core/ (sample handlers for async patterns)
  RUN:
    - grep -rn "time\.sleep" /home/newadmin/swarm-bot --include="*.py" | grep -v ".pyc" | grep -v ".venv" | grep -v "node_modules"
    - grep -rn "threading" /home/newadmin/swarm-bot --include="*.py" | grep -v ".pyc" | grep -v ".venv"
    - grep -rn "import time" /home/newadmin/swarm-bot --include="*.py" | grep -v ".pyc" | grep -v ".venv"
    - grep -rn "facade\|mem0\|memory_manager" /home/newadmin/swarm-bot --include="*.py" | grep -v ".pyc" | grep -v ".venv"
    - ls /home/newadmin/swarm-bot/core/memory/ 2>/dev/null || echo "No memory/ subdir"
    - ls /home/newadmin/swarm-bot/core/

DONE_WHEN:
  - time.sleep occurrences: file:line list
  - threading usage: file:line list  
  - Any blocking I/O identified
  - Memory architecture: facade usage count, mem0 usage count, memory_manager usage count
  - Memory subsystem files listed
  - Findings written to audit report with >200 words

PROOF_FORMAT:
  FILE_OP: `grep -rn "time\.sleep" /home/newadmin/swarm-bot --include="*.py" | grep -v ".pyc" | grep -v ".venv" | wc -l`
  CONTENT: `grep -A 30 "## Async Compliance" /home/newadmin/swarm-bot/.wiki/logs/swarm-YYYY-MM-DD-deep-audit-opencode-claudecode-legionbot.md`

BLOCKER_IF:
  - core/ directory does not exist

DEPENDS_ON: none

---

### CONTRACT #7: Compile Final Audit Report

WHAT:
  Compile all audit findings from Contracts #1-#6 into a single comprehensive report at `/home/newadmin/swarm-bot/.wiki/logs/swarm-2026-04-14-deep-audit-opencode-claudecode-legionbot.md`. Report must have >500 words total, covering all 6 subsystems with Status, Key Findings, Open Issues, and Recommendations for each.

FILES:
  READ:
    - /home/newadmin/swarm-bot/.wiki/logs/planner-2026-04-14-deep-audit-opencode-claudecode-legionbot.md
    - All partial audit findings written by previous contracts
  RUN:
    - ls -la /home/newadmin/swarm-bot/.wiki/logs/
    - wc -l /home/newadmin/swarm-bot/.wiki/logs/swarm-2026-04-14-deep-audit-opencode-claudecode-legionbot.md

DONE_WHEN:
  - Final report file exists at `/home/newadmin/swarm-bot/.wiki/logs/swarm-2026-04-14-deep-audit-opencode-claudecode-legionbot.md`
  - Report contains all 6 subsystem sections: OpenCode, Claude Code, Codebase Health, Budget Guard, Wiki Health, Async+Memory
  - Each section has: Status, Key Findings, Open Issues, Recommendations
  - Total word count >500
  - Report is coherent and complete

PROOF_FORMAT:
  FILE_OP: `wc -l /home/newadmin/swarm-bot/.wiki/logs/swarm-2026-04-14-deep-audit-opencode-claudecode-legionbot.md && wc -w /home/newadmin/swarm-bot/.wiki/logs/swarm-2026-04-14-deep-audit-opencode-claudecode-legionbot.md`
  CONTENT: `head -60 /home/newadmin/swarm-bot/.wiki/logs/swarm-2026-04-14-deep-audit-opencode-claudecode-legionbot.md`

BLOCKER_IF:
  - Any of contracts #1-#6 failed to produce findings
  - Report file does not exist after compilation attempt

DEPENDS_ON: #1, #2, #3, #4, #5, #6
