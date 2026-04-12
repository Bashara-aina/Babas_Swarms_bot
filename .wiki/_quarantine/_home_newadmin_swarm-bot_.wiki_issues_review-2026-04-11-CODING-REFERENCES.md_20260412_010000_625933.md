---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/issues/review-2026-04-11-CODING-REFERENCES.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-12T01:00:00.625961"
}
---

### Review: CODING-REFERENCES.md

#### ✅ Passed
- YAML frontmatter is present and valid (lines 1-5)
- All 20 GitHub URLs are valid and resolve correctly
- Table formatting is consistent with proper alignment
- All 20 repos are present with descriptions

#### ⚠️ Warnings
- **Line 21**: Case mismatch — `Leandroercoli/SaasterKit` in markdown but URL uses lowercase `leandroercoli/SaasterKit`. GitHub handles this but should be consistent.

#### ❌ Blockers

1. **Line 16 — Hallucination**: `shadcn-ui/ui` description says "Component library powering cekwajar's UI" — **FALSE**. The actual repo description is "A set of beautifully-designed, accessible components and a code distribution platform." The phrase "cekwajar's UI" appears nowhere in the official repo and is a hallucination.

2. **Line 31 — Garbled text**: `supabase/supabase` description contains `Postgres深度` — the Chinese characters `深度` (meaning "depth") are clearly erroneous and were likely accidentally inserted. Should just be `Postgres`.

#### Recommended Fixes

```diff
- | 1 | [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | Component library powering cekwajar's UI | Accessible components, copy-paste installation, design system patterns |
+ | 1 | [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | Component library for accessible, copy-paste UI components | Accessible components, copy-paste installation, design system patterns |

- | 4 | [supabase/supabase](https://github.com/supabase/supabase) | Supabase monorepo | Backend-as-a-service, real-time subscriptions, Postgres深度 |
+ | 4 | [supabase/supabase](https://github.com/supabase/supabase) | Supabase monorepo | Backend-as-a-service, real-time subscriptions, Postgres |
```

#### Summary
**FAIL** — 2 blockers must be fixed before this file can be considered clean. The "cekwajar's UI" hallucination is particularly concerning as it suggests AI-generated content was not verified against source repositories.
