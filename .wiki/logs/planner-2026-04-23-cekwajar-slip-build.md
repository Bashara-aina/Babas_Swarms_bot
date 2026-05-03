---
title: Planner 2026 04 23 Cekwajar Slip Build
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

### CONTRACT #1: Create API route app/api/slip/audit/route.ts

WHAT:
Create the Next.js App Router API route that accepts AuditInput, bridges to pph21-ter.ts calculateSlip engine, and returns a SlipResult-compatible response.

FILES:
  READ:
    - /home/newadmin/swarm-bot/cekwajar/cekwajar-20260413T050820Z-3-001/cekwajar/slip_cekwajar_id/types/slip.ts
    - /home/newadmin/swarm-bot/cekwajar/cekwajar-20260413T050820Z-3-001/cekwajar/slip_cekwajar_id/lib/pph21-ter.ts
    - /home/newadmin/swarm-bot/cekwajar/cekwajar-20260413T050820Z-3-001/cekwajar/slip_cekwajar_id/hooks/useAudit.ts
  WRITE:
    - /home/newadmin/swarm-bot/cekwajar/cekwajar-20260413T050820Z-3-001/cekwajar/slip_cekwajar_id/app/api/slip/audit/route.ts

DONE_WHEN:
  - File exists at exact path app/api/slip/audit/route.ts
  - File contains POST export named function
  - File imports calculateSlip from @/lib/pph21-ter.ts
  - File accepts AuditInput via Request JSON
  - File bridges AuditInput → SlipInput (gross pre-computed, extracts components from gross when needed)
  - File calls calculateSlip and returns SlipResult
  - File handles validation errors and returns 400 on bad input
  - File has proper Next.js App Router route.ts structure (export const runtime = 'edge')

PROOF_FORMAT:
  FILE_OP: `ls -la /home/newadmin/swarm-bot/cekwajar/cekwajar-20260413T050820Z-3-001/cekwajar/slip_cekwajar_id/app/api/slip/audit/`
  CODE: `grep -n "export async function POST\|calculateSlip\|AuditInput\|SlipInput" /home/newadmin/swarm-bot/cekwajar/cekwajar-20260413T050820Z-3-001/cekwajar/slip_cekwajar_id/app/api/slip/audit/route.ts | head -30`
  IMPORT: `cd /home/newadmin/swarm-bot/cekwajar/cekwajar-20260413T050820Z-3-001/cekwajar/slip_cekwajar_id && npx tsc --noEmit app/api/slip/audit/route.ts 2>&1 | head -20`

BLOCKER_IF:
  - lib/pph21-ter.ts calculateSlip not exported as named export
  - AuditInput type doesn't match types/slip.ts definition
  - SlipInput interface incompatible with calculateSlip parameter

DEPENDS_ON: none
