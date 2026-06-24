#!/usr/bin/env bash
# Fable 5 — 100-point behavioral verification checklist
# Tests that all Fable 5 behavioral rules are present in the implementation files.
set -euo pipefail

PASS=0
FAIL=0
TOTAL=0

USER_CLAUDE="/home/newadmin/.claude/CLAUDE.md"
PROJ_CLAUDE="/home/newadmin/swarm-bot/CLAUDE.md"
DOT_CLAUDE="/home/newadmin/swarm-bot/.claude/CLAUDE.md"
BEHAVIOR="/home/newadmin/swarm-bot/.claude/reference/fable5-behavior.md"
SAFETY="/home/newadmin/swarm-bot/.claude/reference/fable5-safety.md"
MEMORY="/home/newadmin/swarm-bot/.claude/reference/fable5-memory.md"
WORKFLOW="/home/newadmin/swarm-bot/.claude/reference/fable5-workflow.md"
TOOLS="/home/newadmin/swarm-bot/.claude/reference/fable5-tools.md"
SETTINGS="/home/newadmin/swarm-bot/.claude/settings.json"
PRE_HOOK="/home/newadmin/swarm-bot/.claude/hooks/ecc-fable5-pre.sh"
POST_HOOK="/home/newadmin/swarm-bot/.claude/hooks/ecc-fable5-post.sh"
MEMORY_MD="/home/newadmin/.claude/projects/-home-newadmin-swarm-bot/memory/MEMORY.md"
MEMORY_REF="/home/newadmin/.claude/projects/-home-newadmin-swarm-bot/memory/fable5-implementation.md"

check() {
    local id="$1" desc="$2" file="$3" pattern="$4"
    TOTAL=$((TOTAL + 1))
    if grep -q "$pattern" "$file" 2>/dev/null; then
        PASS=$((PASS + 1))
        echo "  PASS [$id] $desc"
    else
        FAIL=$((FAIL + 1))
        echo "  FAIL [$id] $desc"
        echo "       (expected pattern: $pattern in $file)"
    fi
}

check_i() {
    local id="$1" desc="$2" file="$3" pattern="$4"
    TOTAL=$((TOTAL + 1))
    if grep -qi "$pattern" "$file" 2>/dev/null; then
        PASS=$((PASS + 1))
        echo "  PASS [$id] $desc"
    else
        FAIL=$((FAIL + 1))
        echo "  FAIL [$id] $desc"
        echo "       (expected pattern: $pattern in $file)"
    fi
}

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║     Fable 5 — 100-Point Behavioral Verification Checklist   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    # ═══════════════════════════════════════════════════════════════
    # SECTION 1: Identity & Framing (1-10)
    # ═══════════════════════════════════════════════════════════════
    echo "── Section 1: Identity & Framing ──"

    check "001" "Identity: writes for teammate who stepped away" \
    "$BEHAVIOR" "teammate who stepped away"

    check "002" "Identity: doesn't know your shorthand" \
    "$BEHAVIOR" "don.t know the shorthand"

    check "003" "Identity: complete sentences with technical terms" \
    "$BEHAVIOR" "complete sentences"

    check "004" "Identity: Fable 5 is most advanced Claude model" \
    "$BEHAVIOR" "most advanced"

    check "005" "Identity: interactive engineering agent framing" \
    "$BEHAVIOR" "interactive engineering agent"

    check "006" "Identity: one sentence before first tool call" \
    "$BEHAVIOR" "one sentence"

    check "007" "Identity: brief updates when finding something" \
    "$BEHAVIOR" "brief updates"

    check "008" "Identity: load-bearing or change direction" \
    "$BEHAVIOR" "load-bearing"

    check "009" "Identity: FABLE5_AUTONOMOUS env var reference" \
    "$USER_CLAUDE" "FABLE5_AUTONOMOUS=1"

    check "010" "Identity: Haiku-class / ds v4 flash reference" \
    "$BEHAVIOR" "deepseek-v4-flash"

    # ═══════════════════════════════════════════════════════════════
    # SECTION 2: Outcome-First Communication (11-35)
    # ═══════════════════════════════════════════════════════════════
    echo ""
    echo "── Section 2: Outcome-First Communication ──"

    check "011" "Lead with outcome: first sentence answers 'what happened'" \
    "$BEHAVIOR" "Lead with the outcome"

    check "012" "Lead with outcome in user CLAUDE.md" \
    "$USER_CLAUDE" "Lead with the outcome"

    check "013" "Write for a teammate in user CLAUDE.md" \
    "$USER_CLAUDE" "teammate who stepped away"

    check "014" "Readable > concise in behavior.md" \
    "$BEHAVIOR" "readable matters more"

    check_i "015" "Readable > concise in user CLAUDE.md" \
    "$USER_CLAUDE" "readable"

    check "016" "Drop details that don't change what reader would do" \
    "$BEHAVIOR" "drop details"

    check_i "017" "Drop details in user CLAUDE.md" \
    "$USER_CLAUDE" "drop details"

    check "018" "Don't make reader cross-reference labels" \
    "$BEHAVIOR" "cross-reference"

    check "019" "Match response to question shape" \
    "$BEHAVIOR" "Match the response to the question"

    check "020" "Match response in user CLAUDE.md" \
    "$USER_CLAUDE" "Match response to question"

    check "021" "Avoid over-formatting" \
    "$BEHAVIOR" "Avoid over-formatting"

    check "022" "Avoid over-formatting in user CLAUDE.md" \
    "$USER_CLAUDE" "Avoid over-formatting"

    check "023" "No emojis" \
    "$BEHAVIOR" "No emojis"

    check "024" "No emojis in user CLAUDE.md" \
    "$USER_CLAUDE" "No emojis"

    check "025" "No trailing summaries" \
    "$BEHAVIOR" "trailing summaries"

    check "026" "No trailing summaries in user CLAUDE.md" \
    "$USER_CLAUDE" "trailing summaries"

    check "027" "Never narrate routing" \
    "$BEHAVIOR" "Never narrate routing"

    check "028" "Never narrate routing in user CLAUDE.md" \
    "$USER_CLAUDE" "Never narrate routing"

    check "029" "Code comments only for non-obvious constraints" \
    "$BEHAVIOR" "Code comments only for constraints"

    check "030" "Code comments in user CLAUDE.md" \
    "$USER_CLAUDE" "Code comments only"

    check "031" "Report outcomes faithfully" \
    "$BEHAVIOR" "Report outcomes faithfully"

    check "032" "No hedging: 'I think', 'it seems', 'probably'" \
    "$BEHAVIOR" "I think.*it seems.*probably"

    check "033" "No hedging in user CLAUDE.md" \
    "$USER_CLAUDE" "Never hedge"

    check "034" "No hedging in project CLAUDE.md" \
    "$PROJ_CLAUDE" "No hedging"

    check "035" "No 'Task complete' or 'Here is what I did'" \
    "$BEHAVIOR" "Here is what I did"

    # ═══════════════════════════════════════════════════════════════
    # SECTION 3: Autonomous Execution (36-55)
    # ═══════════════════════════════════════════════════════════════
    echo ""
    echo "── Section 3: Autonomous Execution ──"

    check "036" "User not watching in real time" \
    "$BEHAVIOR" "user is not watching in real time"

    check "037" "User not watching in user CLAUDE.md" \
    "$USER_CLAUDE" "not watching in real time"

    check "038" "Proceed without asking for reversible actions" \
    "$BEHAVIOR" "proceed without asking"

    check "039" "Proceed without asking is in settings.json" \
    "$SETTINGS" "proceedWithoutAsking"

    check "040" "Permission-asking blocklist in behavior.md" \
    "$BEHAVIOR" "can i.*should i.*shall i"

    check "041" "Permission-asking blocklist in settings.json" \
    "$SETTINGS" "blockedPermissionPhrases"

    check "042" "Permission-asking blocklist in user CLAUDE.md" \
    "$USER_CLAUDE" "can I.*should I.*shall I"

    check "043" "Permission-asking blocklist in pre-hook" \
    "$PRE_HOOK" "can i|should i|shall i"

    check "044" "Never end with 'I'll...' or plan/promise" \
    "$BEHAVIOR" "Never end with a plan or promise"

    check "045" "I'll check in post-hook" \
    "$POST_HOOK" "i.?ll"

    check "046" "Never end with I'll in user CLAUDE.md" \
    "$USER_CLAUDE" 'Never end with.*I.ll'

    check "047" "Retry after errors" \
    "$BEHAVIOR" "retry immediately"

    check "048" "Evidence check before state-changing operations" \
    "$USER_CLAUDE" "verify evidence supports"

    check "049" "Evidence check in behavior.md" \
    "$BEHAVIOR" "check that the evidence actually supports"

    check "050" "Error recovery patterns" \
    "$BEHAVIOR" "Recovery patterns"

    check "051" "Multi-step: execute in single turn" \
    "$BEHAVIOR" "single turn"

    check "052" "Batch independent reads" \
    "$BEHAVIOR" "Batch independent reads"

    check "053" "Ask only when truly blocked" \
    "$BEHAVIOR" "Ask when truly blocked"

    check "054" "Exception for investigative tasks" \
    "$BEHAVIOR" "investigative"

    check "055" "Literal execution" \
    "$BEHAVIOR" "Literal execution"

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4: Context & Reasoning (56-65)
    # ═══════════════════════════════════════════════════════════════
    echo ""
    echo "── Section 4: Context & Reasoning ──"

    check "056" "Keep working through compaction" \
    "$BEHAVIOR" "Keep working through compaction"

    check "057" "Keep working through compaction in user CLAUDE.md" \
    "$USER_CLAUDE" "Keep working through compaction"

    check "058" "Do not re-derive established facts" \
    "$BEHAVIOR" "re-derive established facts"

    check "059" "Do not re-derive in user CLAUDE.md" \
    "$USER_CLAUDE" "re-derive established facts"

    check "060" "Give recommendation not exhaustive survey" \
    "$BEHAVIOR" "recommendation, not an exhaustive survey"

    check "061" "Give recommendation in user CLAUDE.md" \
    "$USER_CLAUDE" "recommendation.*not.*exhaustive survey"

    check "062" "Read enough then act" \
    "$BEHAVIOR" "Read just enough"

    check "063" "When enough info to act, act" \
    "$USER_CLAUDE" "enough information to act, act"

    check "064" "Handle interruption gracefully" \
    "$BEHAVIOR" "interruption"

    check "065" "Handle interruption in user CLAUDE.md" \
    "$USER_CLAUDE" "interrupted"

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5: Evidence & Tool Use (66-75)
    # ═══════════════════════════════════════════════════════════════
    echo ""
    echo "── Section 5: Evidence & Tool Use ──"

    check "066" "Verify before stating" \
    "$BEHAVIOR" "Verify before stating"

    check "067" "Prefer dedicated tools over Bash" \
    "$BEHAVIOR" "Prefer dedicated tools"

    check "068" "Web search: firecrawl over built-in" \
    "$BEHAVIOR" "firecrawl_search"

    check "069" "Investigate before fix" \
    "$BEHAVIOR" "Investigate before fix"

    check "070" "Build before test" \
    "$BEHAVIOR" "run.*make check"

    check "071" "Git hygiene: gitnexus_impact" \
    "$BEHAVIOR" "gitnexus_impact"

    check "072" "Git hygiene: gitnexus_detect_changes" \
    "$BEHAVIOR" "gitnexus_detect_changes"

    check "073" "Git hygiene: gitnexus_rename dry_run" \
    "$BEHAVIOR" "gitnexus_rename.*dry_run"

    check "074" "Agent results only visible through summaries" \
    "$BEHAVIOR" "other agents.*results.*visible.*summaries"

    check "075" "Evidence rules in user CLAUDE.md" \
    "$USER_CLAUDE" "Verify before stating"

    # ═══════════════════════════════════════════════════════════════
    # SECTION 6: Safety & Copyright (76-85)
    # ═══════════════════════════════════════════════════════════════
    echo ""
    echo "── Section 6: Safety & Copyright ──"

    check "076" "15+ words = severe copyright violation" \
    "$SAFETY" "SEVERE VIOLATION"

    check "077" "15+ words in behavior.md" \
    "$BEHAVIOR" "SEVERE VIOLATION"

    check "078" "One quote per source maximum" \
    "$SAFETY" "ONE quote per source"

    check "079" "Default to paraphrasing" \
    "$SAFETY" "paraphrasing"

    check "080" "Never output song lyrics" \
    "$SAFETY" "song lyrics"

    check "081" "Harmful content blocking categories" \
    "$SAFETY" "harmful"

    check "082" "Dual-use security tool boundaries" \
    "$SAFETY" "Dual-Use"

    check "083" "Evenhandedness: present best case" \
    "$SAFETY" "Evenhandedness"

    check "084" "Visual/visuals content safety rules" \
    "$SAFETY" "Content Safety for Visual"

    check "085" "Copyright rules in behavior.md safety section" \
    "$BEHAVIOR" "Copyright"

    # ═══════════════════════════════════════════════════════════════
    # SECTION 7: Memory System (86-92)
    # ═══════════════════════════════════════════════════════════════
    echo ""
    echo "── Section 7: Memory System ──"

    check "086" "Never say 'I don't see' without searching first" \
    "$MEMORY" "I don.t see any previous conversation"

    check "087" "Memory requires no attribution" \
    "$MEMORY" "no attribution"

    check "088" "No observation verbs" \
    "$MEMORY" "I can see"

    check "089" "Recognize linguistic cues" \
    "$MEMORY" "signals are linguistic"

    check "090" "Query construction: content nouns not meta-words" \
    "$MEMORY" "content nouns"

    check "091" "Preference system: behavioral vs contextual" \
    "$MEMORY" "preference"

    check "092" "Memory edit management" \
    "$MEMORY" "edit"

    # ═══════════════════════════════════════════════════════════════
    # SECTION 8: Workflow Patterns (93-97)
    # ═══════════════════════════════════════════════════════════════
    echo ""
    echo "── Section 8: Workflow Patterns ──"

    check "093" "Pipeline vs parallel dispatch" \
    "$WORKFLOW" "pipeline"

    check "094" "Adversarial verification" \
    "$WORKFLOW" "adversarial"

    check "095" "Judge panel pattern" \
    "$WORKFLOW" "Judge Panel"

    check "096" "Loop-until-dry pattern" \
    "$WORKFLOW" "Loop-Until-Dry"

    check "097" "Budget-aware execution" \
    "$WORKFLOW" "budget"

    # ═══════════════════════════════════════════════════════════════
    # SECTION 9: Tool Discipline (98-100)
    # ═══════════════════════════════════════════════════════════════
    echo ""
    echo "── Section 9: Tool Discipline ──"

    check "098" "CronCreate jitter patterns" \
    "$TOOLS" "jitter"

    check "099" "Monitor coverage not silence" \
    "$TOOLS" "monitor"

    check "100" "Read/edit/bash discipline" \
    "$TOOLS" "discipline"

    # ═══════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Results: $PASS / $TOTAL passed  ($FAIL failed)"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    if [ "$FAIL" -gt 0 ]; then
        exit 1
    fi
