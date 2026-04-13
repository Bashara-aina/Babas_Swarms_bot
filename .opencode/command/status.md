# /status — Project Status Report

Generate a current status report for the Legion bot project.

## Gather Status
1. git log --oneline -10 → recent commits
2. python3 -c "import json; print(json.dumps(json.load(open('wiki/_meta/compile_state.json')), indent=2))"
3. systemctl status swarm-bot.service 2>/dev/null | head -10 || echo "Service status unavailable"
4. find wiki/decisions/ -name "*.md" | sort -r | head -5 → recent decisions
5. python3 smoke tests from CLAUDE.md §12
6. cat wiki/_meta/audit_report_2026-04-13.md 2>/dev/null | head -30

## Output Format
### Legion Status — [date]
Bot service: ✅/❌
Wiki: [N articles, last compiled: date]
Recent work: [last 5 commits]
Open P-tasks: [which P2/P3 remain from CLAUDE.md §9]
Next priority: [what to do next]

Write status to: wiki/output/health/status-[YYYY-MM-DD].md
Verify: ls -la wiki/output/health/status-[date].md