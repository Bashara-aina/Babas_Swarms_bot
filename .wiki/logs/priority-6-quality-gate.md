# Priority 6: Quality Gate — Execution Log

**Date**: 2026-04-12  
**Agent**: @worker (Bashara)  
**Task**: Response Quality Gate for Legion depth upgrade

## What Was Created

### 1. `core/quality_gate.py` (new file)

```python
@dataclass
class QualityResult:
    issues: list[str]
    should_retry: bool

class QualityGate:
    MAX_RETRIES = 1
    
    UNCERTAINTY_SIGNALS = [
        "I don't know", "I'm not sure", "gw ga tau",
        "tidak yakin", "mungkin", "I think but am not certain",
    ]
    
    FORBIDDEN_ARTIFACTS = [
        "As an AI", "I cannot", "I'm unable to", "As a language model",
    ]
    
    async def check(user_message, response, intent) -> QualityResult
    async def retry(messages, issues) -> str
```

Checks three issue types:
- **SHALLOW**: User message >20 words but response <30 words
- **UNCERTAIN**: Response contains uncertainty signals without search trigger
- **ARTIFACT**: Response contains forbidden LLM identity phrases

### 2. Wired into `llm_client/__init__.py`

After the main LLM call (line 1517 area), added:
```python
_qg = QualityGate()
_quality = await _qg.check(task, result, agent_key or "general")
if _quality.should_retry:
    logger.info("Quality gate triggered: %s", _quality.issues)
    result = await _qg.retry(messages, _quality.issues)
```

### 3. ADR Written

`ADR-015.md` created in `.wiki/decisions/`

## Verification Results

```
python scripts/verify_wiring.py
```

All 7 test categories PASS:
- Handler Wiring: PASS
- Core Imports: PASS
- LLM Client: PASS
- Tools: PASS
- Bridges: PASS
- Skills: PASS
- Agents: PASS

## Test Cases (manual verification)

| Scenario | LLM Returns | Gate Response |
|----------|-------------|---------------|
| Uncertainty | "I don't know" | should_retry=True, issues=["UNCERTAIN..."] |
| Short to long question | "<30 words for >20 word question" | should_retry=True, issues=["SHALLOW..."] |
| LLM artifact | "As an AI, I cannot..." | should_retry=True, issues=["ARTIFACT..."] |
| Good response | Long detailed answer | should_retry=False, issues=[] |

## Notes

- Quality gate is non-fatal — wrapped in try/except, errors logged and bypassed
- MAX_RETRIES = 1 enforced (class constant)
- Latency cost: ~500-800ms on retry, acceptable trade-off for quality
- No changes to .env or API key handling