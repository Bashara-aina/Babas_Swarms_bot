# Anti-Slop Defense System — Task Decomposition
> Planner: Bashara | Date: 2026-04-11 | Project: Babas_Swarms_bot (Legion)

## Context
Implement a full anti-slop defense stack into Babas_Swarms_bot. Every LLM response must pass through quality gates before reaching the user. This builds on the existing `core/wiki_quality_gate.py` pattern but extends it to all bot output.

## Directory Structure
```
legion/                          # NEW — anti-slop module root
  anti_slop/
    __init__.py
    core.py                      # 4-guard pipeline (guard_1-4)
    nemo_config/
      config.yml                # NeMo Guardrails config
      rails.co                  # Rails configuration
    integration.py             # Drop-in wrapper for llm_client
    monitor.py                 # Slop detection monitor
tests/
  test_legion_quality.py       # DeepEval test suite
.github/
  workflows/
    quality-gate.yml           # CI quality gate workflow
```

---

## STAGE 0: Safety Checkpoint
**Subtask 0.1**: Create git tag `anti-slop-start` before beginning work
- Run: `git tag anti-slop-start && git push origin anti-slop-start`
- Log to `.wiki/logs/anti-slop-progress.md`

---

## STAGE 1: Document Dependencies
**Subtask 1.1**: Document required dependencies in requirements.txt
- Document: `deepspeed`, `triton`, `vllm` (if using NeMo), or `langchain-community` (alternative)
- Document: `deepeval` (for testing), `numpy`, `scipy`
- DO NOT run pip install — document only
- Target: `requirements.txt` append-only

---

## STAGE 2: Create `legion/anti_slop/core.py`
**Subtask 2.1**: Create `legion/anti_slop/__init__.py`
- Empty init with module docstring

**Subtask 2.2**: Create `legion/anti_slop/core.py` — 4-guard pipeline
```
Guard 1 (filler): Detect filler phrases (as you know, it goes without saying, etc.)
Guard 2 (toxicity): Basic toxicity/severity check
Guard 3 (repetition): Detect slop patterns (>10x same char, >50% caps, etc.)
Guard 4 (grounding): LLM verify response relevance to user query
```
- Follow existing `core/wiki_quality_gate.py` patterns (async, dataclass result, latency_ms)
- Use existing `llm_client.py` for Guard 4
- Export: `run_quality_gate(content, task) -> QualityResult`

---

## STAGE 3: Create `legion/anti_slop/nemo_config/`
**Subtask 3.1**: Create `legion/anti_slop/nemo_config/config.yml`
- NeMo Guardrails config with:
  - `input_checks` (filler detection, caps limit, repetition)
  - `output_checks` (groundedness, relevance)
  - Model config (reference existing llm_client setup)

**Subtask 3.2**: Create `legion/anti_slop/nemo_config/rails.co`
- Rails config for content barriers
- Reference patterns from `core/character/` for voice/style

---

## STAGE 4: Create `tests/test_legion_quality.py`
**Subtask 4.1**: Create DeepEval test suite
```
Test cases:
- filler_phrase_rejection
- caps_spam_rejection  
- repetition_spam_rejection
- valid_response_pass
- short_content_rejection
- grounding_pass
- grounding_fail_irrelevant
```
- Use `pytest --asyncio-mode=auto`
- Follow existing test patterns in `tests/test_wiki_manager.py`

---

## STAGE 5: Create `legion/anti_slop/integration.py`
**Subtask 5.1**: Create drop-in wrapper for llm_client
- `LegionQualityGateway` class
- Wraps `llm_client.chat()` with 4-guard pipeline
- Exposes `chat_with_quality(text, task, agent_key)` async method
- Returns: `(response_text, QualityResult)`

---

## STAGE 6: Create `legion/anti_slop/monitor.py`
**Subtask 6.1**: Create slop monitor
- `SlopMonitor` class with sliding window counter
- Track: rejection rate, guard_3 (repetition) hits, guard_4 (grounding) fails
- Expose: `get_stats() -> dict`, `log_event(event)`
- Integrate with existing `swarms_bot/observability/` patterns

---

## STAGE 7: Add Telegram Commands
**Subtask 7.1**: Identify handler file for command registration
- Check `handlers/ecc_compat.py` (has `/quality_gate`)
- Check `main.py` bot command registration
- Find best location for new `/slop_stats`, `/anti_slop_off`, `/anti_slop_on` commands

**Subtask 7.2**: Add new Telegram commands
- `/slop_stats` — show slop monitor stats
- `/anti_slop_off` — disable anti-slop for session
- `/anti_slop_on` — re-enable anti-slop
- Register in `main.py` BotCommand list

---

## STAGE 8: Create `.github/workflows/quality-gate.yml`
**Subtask 8.1**: Create GitHub Actions workflow
```
Triggers: pull_request, push to main
Jobs:
  - quality-gate: run pytest tests/test_legion_quality.py
  - lint: run ruff check
  - typecheck: run mypy legion/anti_slop/
```
- Follow existing workflow patterns in `.github/workflows/`

---

## STAGE 9: Final Verification + Commit
**Subtask 9.1**: Run full test suite
- `pytest tests/ -x --asyncio-mode=auto -q`
- Fix any failures

**Subtask 9.2**: Run lint
- `ruff check legion/anti_slop/ tests/test_legion_quality.py`

**Subtask 9.3**: Git commit with tag
- Conventional commit: `feat(anti-slop): add 4-guard quality pipeline`
- Tag: `anti-slop-complete`
- Push tags

---

## Workers Assigned
| Stage | Worker | Task |
|-------|--------|------|
| 0 | @worker | Git tag |
| 1 | @worker | Document dependencies |
| 2 | @worker | Create core.py |
| 3 | @worker | Create nemo_config |
| 4 | @worker | Create test suite |
| 5 | @worker | Create integration.py |
| 6 | @worker | Create monitor.py |
| 7 | @worker | Add Telegram commands |
| 8 | @worker | Create GitHub workflow |
| 9 | @reviewer | Final review + commit |

---

## Decisions (ADR)
Write to `.wiki/decisions/ADR-001-anti-slop-system.md`:
- Why 4 guards (not 2 or 6)
- NeMo vs langchain-community choice
- Integration point (llm_client wrapping vs middleware)
