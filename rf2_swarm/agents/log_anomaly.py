"""Agent 18: LogAnomalyAgent — warning patterns, error frequency, unexpected log lines."""

from __future__ import annotations
import re
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict

WARNING_RE = re.compile(r"\b(?:warning|WARNING|warn)\b")
ERROR_RE = re.compile(r"\b(?:error|ERROR|Error|exception|EXCEPTION)\b")
CRITICAL_RE = re.compile(r"\b(?:CRITICAL|critical|FATAL|fatal)\b")
STACK_TRACE_RE = re.compile(r"Traceback.*|File.*line \d+.*\n.*Error", re.MULTILINE)
ASSERT_RE = re.compile(r"AssertionError|assert.*failed", re.IGNORECASE)


class LogAnomalyAgent(BaseAgent):
    """Scans training log for warning/error patterns and anomalies."""

    def __init__(self):
        super().__init__("LogAnomaly")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        log_lines = ctx.get("log_lines", [])
        log_text = ctx.get("log_text", "")
        checks: list[CheckResult] = []

        warnings = WARNING_RE.findall(log_text)
        errors = ERROR_RE.findall(log_text)
        criticals = CRITICAL_RE.findall(log_text)
        stack_traces = STACK_TRACE_RE.findall(log_text)
        asserts = ASSERT_RE.findall(log_text)

        # LA01: Low warning count
        if warnings:
            checks.append(CheckResult("LA01", "LogAnomaly", "Low warning count in log",
                                      Verdict.PASS if len(warnings) < 20 else Verdict.WARN,
                                      f"{len(warnings)} warnings"))
        else:
            checks.append(CheckResult("LA01", "LogAnomaly", "Low warning count in log",
                                      Verdict.PASS, "0 warnings"))

        # LA02: No errors in log
        if errors:
            # Deduplicate common expected errors (e.g., "old checkpoint format")
            known_ok = {"old checkpoint", "deprecated", "non-fatal"}
            real_errors = [e for e in errors if not any(k in e.lower() for k in known_ok)]
            checks.append(CheckResult("LA02", "LogAnomaly", "No errors in log",
                                      Verdict.WARN if real_errors else Verdict.PASS,
                                      f"{len(errors)} error occurrences"))
        else:
            checks.append(CheckResult("LA02", "LogAnomaly", "No errors in log",
                                      Verdict.PASS, "0 errors"))

        # LA03: No critical/fatal errors
        checks.append(CheckResult("LA03", "LogAnomaly", "No critical/fatal errors",
                                  Verdict.FAIL if criticals else Verdict.PASS,
                                  f"{len(criticals)} critical" if criticals else "No critical errors",
                                  blocking=bool(criticals)))

        # LA04: No stack traces (non-blocking — historical traces may exist from shutdowns)
        checks.append(CheckResult("LA04", "LogAnomaly", "No stack traces",
                                  Verdict.WARN if stack_traces else Verdict.PASS,
                                  f"{len(stack_traces)} stack trace(s)" if stack_traces else "No stack traces"))

        # LA05: No assertion errors
        checks.append(CheckResult("LA05", "LogAnomaly", "No assertion errors",
                                  Verdict.FAIL if asserts else Verdict.PASS,
                                  "Assertion failed" if asserts else "No asserts",
                                  blocking=bool(asserts)))

        # LA06: Log line frequency anomaly (gaps / silence)
        if log_lines:
            recent = log_lines[-min(1000, len(log_lines)):]
            timestamps = []
            for line in recent:
                m = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", line)
                if m:
                    timestamps.append(m.group(1))
            if len(timestamps) >= 2:
                # Check for gaps > 5 min
                gaps = 0
                for i in range(1, min(len(timestamps), 50)):
                    try:
                        from datetime import datetime
                        t1 = datetime.strptime(timestamps[i - 1], "%Y-%m-%d %H:%M:%S")
                        t2 = datetime.strptime(timestamps[i], "%Y-%m-%d %H:%M:%S")
                        if (t2 - t1).total_seconds() > 300:
                            gaps += 1
                    except ValueError:
                        pass
                checks.append(CheckResult("LA06", "LogAnomaly", "No log silence gaps >5min",
                                          Verdict.WARN if gaps > 3 else Verdict.PASS,
                                          f"{gaps} silence gap(s) in recent log"))

        return AgentResult(self.name, checks)
