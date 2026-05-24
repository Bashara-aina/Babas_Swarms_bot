# Bug Report: bash tool blocked during compaction despite permissive config

**Version**: opencode 1.14.50
**Platform**: Linux x86_64 (64-bit ELF)
**Date**: 2026-05-24

## Severity
Medium — blocks practical compaction use cases

## Issue Summary
During compaction/summary generation, the `bash` tool is blocked with error:
"Tool call not allowed while generating summary: bash"

This occurs even though the compaction agent has `"*": "allow"` wildcard permissions in both global and project config files.

## Expected Behavior
When compaction agent has `"*": "allow"` permission, ALL tools should be allowed including bash.

## Actual Behavior
1. Compaction agent config (`opencode debug agent compaction`) shows:
   - "mode": "primary", "native": true
   - "permission": { "*": "allow" } via wildcard
2. Yet during compaction, bash is blocked with internal binary error
3. Other tools (read, glob, grep) ARE allowed during compaction

## Root Cause Analysis
The restriction appears to be embedded in the compiled binary's internal compaction logic, not in user-accessible config files. The binary has a SEPARATE internal allowlist for the "generating summary" code path that only includes {read, glob, grep} — explicitly excluding bash.

## Config Files Verified
- `~/.config/opencode/opencode.jsonc` — global config with "agent.compaction.permission.*": "allow"
- `swarm-bot/.opencode/opencode.json` — project config with same permissive settings

Both configs show "compaction": { "reserved": 4096 } and permissions are correctly set.

## Reproduction Steps
1. Set compaction agent permission to "*": "allow"
2. Run opencode for enough turns to trigger compaction
3. During compaction summary generation, attempt bash tool call
4. Observe: "Tool call not allowed while generating summary: bash"

## Workarounds Attempted
- Set compaction.threshold: 1.0 (disable auto-compaction)
- Set compaction.maxContext: 999999
- Set snapshot: true
- Added "*": "allow" to all agent blocks
- Added explicit "bash": true to tools map
None of these bypass the internal binary restriction.

## Proposed Fix
Allow configuration of which tools are permitted during compaction, or remove the hardcoded internal tool allowlist so that user permissions are respected.

## Contact
(prefer to be contacted for follow-up)