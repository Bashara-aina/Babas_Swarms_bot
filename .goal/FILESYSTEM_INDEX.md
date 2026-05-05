# /goal Meta-Harness Filesystem

## Layout
- .goal/traces/          -- Full execution traces per goal run (NOT summaries)
- .goal/harnesses/       -- Harness candidates (code that wraps mini-SWE-agent)
  - candidates/          -- All evaluated harnesses with scores
  - current/             -- Active harness being used
  - pareto_frontier/     -- Best accuracy/cost tradeoff harnesses
- .goal/logs/            -- Raw mini-SWE-agent stdout per task
- .goal/plans/           -- PLAN.md files per goal (timestamped)
- .goal/reports/         -- JSON audit reports per phase
- .goal/checkpoints/     -- Task completion state (survives crashes)

## How to Read History (Meta-Harness pattern)
grep -r "score:" .goal/harnesses/candidates/ | sort -t: -k3 -n | tail -20
cat .goal/traces/<goal_id>/phase_1_task_T1.1.trace
cat .goal/harnesses/candidates/<id>/harness.py
diff .goal/harnesses/candidates/<id1>/harness.py .goal/harnesses/candidates/<id2>/harness.py

## Key Insight
Do NOT read compressed summaries. Read raw traces to understand WHY a
harness failed -- not just THAT it failed. Meta-Harness paper shows this
is the difference between 34.6 and 50.0 median accuracy.
