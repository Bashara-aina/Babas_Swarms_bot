# Regression Evaluation Set
**Project:** Babas Agency Swarm | **File:** EVAL_SET.md
**Purpose:** M2.7 Self-Evolution Regression Tests — derived from FAILURES.md after ≥5 entries.
Run relevant checks at start of related tasks to prevent repeated failure patterns.

---

## Template

```markdown
## [Test ID]: [Short Description]
Source: ADR-[N] or FAILURES.md entry
Trigger: When does this test apply?
Command: How to run this test
Expected: What correct behavior looks like
```

---

## Placeholder (populate after ≥5 FAILURES.md entries)

Once FAILURES.md accumulates 5+ entries, group by root cause category and convert each category into a test case here.

Example structure when populated:

```markdown
## TEST-001: Telegram HTML escape verification
Source: FAILURES.md 2026-04-13 — TelegramBadRequest
Trigger: Any new handler that sends Telegram messages
Command: python -c "
  import html
  test_strings = ['<script>', 'a & b', 'price: Rp 1.000', 'a\nb']
  for s in test_strings:
      escaped = html.escape(s)
      assert '&lt;' in escaped or '&amp;' in escaped or escaped == s
  print('escape ok')
"
Expected: All user-sourced strings are HTML-escaped before parse_mode="HTML"

---

## TEST-002: Ollama VRAM cleanup before model swap
Source: FAILURES.md 2026-04-13 — Ollama VRAM overflow
Trigger: Before running any Ollama model chain
Command: bash -c "ollama list && ollama stop $(ollama list | grep 'NAME' -v | awk '{print $1}')"
Expected: No model loaded when starting a new Ollama chain on RTX 3060

---

[... more tests derived from failure patterns ...]
```

---

## Running the Evaluation Set

```bash
# Run all eval tests
python -c "
import subprocess, sys
tests = [
    ('html_escape', 'python -c \"import html; assert html.escape(\\\"<test&>\\\") == \\\"&lt;test&amp;&gt;\\\"\"'),
    # add more...
]
failed = []
for name, cmd in tests:
    r = subprocess.run(cmd, shell=True, capture_output=True)
    if r.returncode != 0:
        failed.append(name)
        print(f'FAIL: {name}')
        print(r.stderr.decode())
if not failed:
    print('ALL TESTS PASSED')
    sys.exit(0)
else:
    print(f'{len(failed)} tests failed')
    sys.exit(1)
"
```

---

## Accumulated Tests (append new tests below)

<!-- Tests get added here after FAILURES.md reaches 5+ entries and patterns emerge. -->
