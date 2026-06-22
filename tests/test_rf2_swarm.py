"""Integration test for the RF2 monitoring swarm."""

from __future__ import annotations
import json
import sys
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC))

from rf2_swarm.main import build_agents  # noqa: E402
from rf2_swarm.coordinator import Coordinator  # noqa: E402
from rf2_swarm.data_sources import reload_all  # noqa: E402
from rf2_swarm.reporter import write_results, generate_report  # noqa: E402
from rf2_swarm.config import LOG, STATE, METRICS, CONFIG_FILE, RESULTS_JSON, REPORT_TXT  # noqa: E402


def test_agents_instantiate():
    """All 20 agents instantiate without error."""
    agents = build_agents()
    assert len(agents) == 20, f"Expected 20 agents, got {len(agents)}"
    names = [a.name for a in agents]
    assert len(set(names)) == 20, f"Duplicate agent names: {names}"
    print(f"✓ {len(agents)} agents instantiated: {', '.join(names)}")


def test_data_sources_load():
    """All data sources load without error."""
    ctx = reload_all(LOG, STATE, METRICS, CONFIG_FILE)
    assert "log_lines" in ctx
    assert "log_text" in ctx
    assert "state" in ctx
    assert "metrics" in ctx
    assert "config" in ctx
    print(f"✓ Data sources loaded: log={len(ctx['log_lines'])} lines, "
          f"state={len(ctx['state'])} fields, "
          f"metrics={len(ctx['metrics'])} records, "
          f"config={len(ctx['config'])} keys")


def test_all_agents_run():
    """All 20 agents run and produce results."""
    agents = build_agents()
    coordinator = Coordinator(agents, max_workers=40, agent_timeout=60)
    ctx = reload_all(LOG, STATE, METRICS, CONFIG_FILE)

    start = time.time()
    results = coordinator.run_cycle(ctx)
    elapsed = time.time() - start

    assert len(results) == 20, f"Expected 20 results, got {len(results)}"

    total_checks = sum(len(r.checks) for r in results)
    total_errors = sum(1 for r in results if r.error)

    print(f"✓ All agents ran in {elapsed:.1f}s: {total_checks} checks, {total_errors} errors")

    # Verify no agent errored
    for r in results:
        assert r.error is None, f"Agent {r.agent_name} error: {r.error}"
        assert len(r.checks) > 0, f"Agent {r.agent_name} produced 0 checks"
        for c in r.checks:
            assert c.uid, f"Agent {r.agent_name} has check without uid"
            assert c.verdict in ("PASS", "WARN", "FAIL", "INFO", "SKIP"), \
                f"Agent {r.agent_name} check {c.uid} has invalid verdict: {c.verdict}"

    return results, ctx


def test_output_writes(results, ctx):
    """Output files are written in backward-compatible format."""
    write_results(results, ctx["state"], RESULTS_JSON, REPORT_TXT)

    assert RESULTS_JSON.exists(), "JSON results not written"
    assert REPORT_TXT.exists(), "Text report not written"

    # Validate JSON schema
    with open(RESULTS_JSON) as f:
        data = json.load(f)

    required_keys = {"timestamp", "total", "pass", "warn", "fail", "info",
                     "blocking", "gate_passed", "epoch", "max_epochs", "results", "summary"}
    assert required_keys.issubset(data.keys()), f"Missing keys: {required_keys - data.keys()}"
    assert isinstance(data["results"], list), "results should be a list"
    assert data["total"] == len(data["results"]), "total count mismatch"

    # Verify each result entry
    for r in data["results"]:
        assert "uid" in r
        assert "verdict" in r
        assert "category" in r

    print(f"✓ Output written: {data['total']} checks, verdict={data['summary']}")


def test_report_generation(results, ctx):
    """Text report generates without error."""
    report = generate_report(results, ctx["state"], cycle=1)
    assert len(report) > 100, "Report too short"
    assert "RF2 SWARM REPORT" in report, "Missing report header"
    assert "VERDICT:" in report, "Missing verdict line"
    print(f"✓ Report generated ({len(report)} chars)")


if __name__ == "__main__":
    print("=" * 60)
    print("RF2 Swarm — Integration Tests")
    print("=" * 60)

    test_agents_instantiate()
    test_data_sources_load()
    results, ctx = test_all_agents_run()
    test_output_writes(results, ctx)
    test_report_generation(results, ctx)

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
