# /commit — Structured Git Commit

Create a well-structured git commit for current changes.

## Steps
1. Run: git status → paste output
2. Run: git diff --stat → paste output
3. Determine commit type: feat | fix | refactor | docs | test | chore
4. Write commit message following: [type]: [short description]
   Body: what changed and why (if non-obvious)
5. Stage: git add [specific files — NOT git add -A unless all changes are intentional]
6. Commit: git commit -m "[type]: [message]"
7. Paste git commit output as proof

DO NOT commit: .env files, API keys, _old directories, >200 line changes without review.

Changes to commit: