# /hermes-status — Hermes Agent Integration Verification
## Phase 6: Hermes Verification
git submodule status ext/hermes-agent
test -d ext/hermes-agent/.venv && echo "Hermes venv exists ✓" || echo "Hermes venv MISSING ✗"
test -d ext/hermes-agent && echo "Hermes dir exists ✓" || echo "Hermes dir MISSING ✗"
grep -n "7777\|mcp_serve\|hermes" .opencode/agents/hermes-agent.md 2>/dev/null | head -5
echo "Hermes status check complete."