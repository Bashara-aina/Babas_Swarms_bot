# /fix — Targeted Bug Fix

Fix the specific bug described below. Do not fix anything else.

## Steps
1. Read the error message or failure description carefully
2. Identify the exact file(s) involved: grep -r "[error text]" . --include="*.py" | head -5
3. Read the file: cat [file] | head -80
4. Identify the root cause — do not guess
5. Fix ONLY the identified root cause — no scope creep
6. Verify fix:
   - For code: python3 -m py_compile [file] → must exit 0
   - For logic: run the failing test → must pass
   - Paste actual test/compile output
7. Smoke test: python3 -c "from [module] import [thing]; print('ok')"

Report: FIX STATUS: ✅ RESOLVED | ❌ STILL FAILING
Evidence: paste test/compile output

Bug to fix: