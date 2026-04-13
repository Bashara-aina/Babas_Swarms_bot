# /audit — Implementation Audit

Run a targeted audit of the component specified below.
Output: write findings to .wiki/output/health/audit-[YYYY-MM-DD]-[component].md

## Audit Steps
1. Read relevant .wiki/architecture/ article for the component
2. Read relevant .wiki/concepts/ articles
3. Run structural checks: find, grep, wc -l as appropriate
4. Check for: missing files, broken imports, dead code references, test coverage
5. Check all pasted outputs — never trust claims without evidence

## Output Format
### Audit: [Component] — [Date]
PASS ✅ / WARN ⚠️ / FAIL ❌ for each check
Evidence: paste actual command output
Fix Plan: exact commands to resolve each FAIL

Verify output written: ls -la .wiki/output/health/audit-[date]-[component].md

Component to audit: