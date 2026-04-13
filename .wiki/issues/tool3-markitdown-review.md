### Review: Tool 3 - markitdown doc_parser

#### ✅ Passed
- `parse_file()` has proper fallback when markitdown unavailable (pdfplumber fallback)
- `parse_telegram_document()` handles errors with try/except and returns structured error dict
- `SKILL_META` contains all required fields (name, description, triggers, execute, requires_internet, avg_latency_seconds, cost_tier)
- `doc_parser` is properly imported in `core/skills/__init__.py`
- `requirements.txt` has `markitdown[all]>=0.1.0` correctly added
- `.env.example` documents `MARKITDOWN_LLM_VISION` env var
- `python scripts/verify_wiring.py` — **ALL CHECKS PASS**

#### ⚠️ Warnings
- `parse_file()` accepts `use_llm_for_images` parameter but **never uses it** — it's ignored and always set to `False`
- `MARKITDOWN_LLM_VISION` env var is documented in `.env.example` but **never read** in `doc_parser.py`
- Line 78: bare `except:` clause — should be `except Exception as e:` for clarity and to match project standards

#### ❌ Blockers
- **None** — wiring verification passes, core functionality works

---

**Verdict: PASS**

The implementation is functional. The unused `use_llm_for_images` parameter and unwired `MARKITDOWN_LLM_VISION` are cosmetic issues (feature not fully wired), not blockers. The bare `except` is a minor style deviation.
