#!/bin/bash
# Claude Flow V3 - DDD Progress Tracker Worker
# Tracks Domain-Driven Design implementation progress

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
METRICS_DIR="$PROJECT_ROOT/.claude-flow/metrics"
DDD_FILE="$METRICS_DIR/ddd-progress.json"
V3_PROGRESS="$METRICS_DIR/v3-progress.json"
LAST_RUN_FILE="$METRICS_DIR/.ddd-last-run"

mkdir -p "$METRICS_DIR"

# V3 Target Domains — mapped to actual swarm-bot structure
DOMAINS=("orchestration" "memory" "agent" "skills" "swarm")

should_run() {
  if [ ! -f "$LAST_RUN_FILE" ]; then return 0; fi
  local last_run=$(cat "$LAST_RUN_FILE" 2>/dev/null || echo "0")
  local now=$(date +%s)
  [ $((now - last_run)) -ge 600 ]  # 10 minutes
}

check_domain() {
  local domain="$1"
  # Map domain name to actual file/folder locations in swarm-bot structure
  local domain_path="$PROJECT_ROOT/core/${domain}.py"
  local alt_path="$PROJECT_ROOT/core/${domain}_*.py"
  local alt_dir="$PROJECT_ROOT/core/${domain}"
  local glob_files

  local score=0
  local max_score=100

  # Check if domain has files in core/ (20 points)
  # agent domain → core/agent.py, core/agent_*.py, core/agent_registry.py, etc.
  # swarm domain → core/swarm.py, core/swarm_*.py, core/legion_swarm.py, etc.
  local glob_expr=""
  case "$domain" in
    orchestration) glob_expr="orchestrat" ;;
    memory) glob_expr="memory" ;;
    agent) glob_expr="agent" ;;
    skills) glob_expr="skill" ;;
    swarm) glob_expr="swarm" ;;
  esac

  local match_count
  # Use grep instead of find -name for regex-like patterns (find -name doesn't support ^ $ anchors)
  match_count=$(ls "$PROJECT_ROOT/core"/ 2>/dev/null | grep -E "${glob_expr}.*\.py$" | wc -l)
  if [ "$match_count" -gt 0 ]; then
    score=$((score + 20))

    # Check for explicit domain/ subdir (15 points)
    [ -d "$PROJECT_ROOT/core/${domain}" ] && score=$((score + 15))

    # Check for domain module with explicit sub-structure (15 points each)
    [ -d "$PROJECT_ROOT/core/${domain}/domain" ] || [ -d "$PROJECT_ROOT/core/${domain}/src/domain" ] && score=$((score + 15))
    [ -d "$PROJECT_ROOT/core/${domain}/application" ] || [ -d "$PROJECT_ROOT/core/${domain}/src/application" ] && score=$((score + 15))
    [ -d "$PROJECT_ROOT/core/${domain}/infrastructure" ] || [ -d "$PROJECT_ROOT/core/${domain}/src/infrastructure" ] && score=$((score + 15))
    [ -d "$PROJECT_ROOT/core/${domain}/api" ] || [ -d "$PROJECT_ROOT/core/${domain}/src/api" ] && score=$((score + 10))

    # Check for DDD layer markers in agent files (10 pts — @dataclass for entity/value object)
    local ddd_marker_count
    ddd_marker_count=$(ls "$PROJECT_ROOT/core"/ 2>/dev/null | grep -E "agent.*\.py$" | while read f; do grep -l "@dataclass\|class.*Entity\|class.*Value" "$PROJECT_ROOT/core/$f" 2>/dev/null; done | wc -l)
    [ "$ddd_marker_count" -gt 0 ] && score=$((score + 10))

    # Check for tests (15 points)
    local test_count
    test_count=$(ls "$PROJECT_ROOT/core"/ 2>/dev/null | grep -E "agent.*_test\.py$|agent.*\.test\.py$" | wc -l)
    [ "$test_count" -gt 0 ] && score=$((score + 15))

    # Check for module index (10 points)
    [ -f "$PROJECT_ROOT/core/${domain}/__init__.py" ] || [ -f "$PROJECT_ROOT/core/${domain}/src/__init__.py" ] && score=$((score + 10))
  fi

  echo "$score"
}

count_entities() {
  local pattern="$1"
  local count
  count=$(find "$PROJECT_ROOT/core" "$PROJECT_ROOT/v3" "$PROJECT_ROOT/src" -name "*.py" -type f 2>/dev/null | \
    xargs grep -lE "$pattern" 2>/dev/null | \
    grep -vE "node_modules|\.test\." | \
    awk 'END {print (NR ? NR : 0)}')
  printf '%s' "${count:-0}"
}

track_ddd() {
  echo "[$(date +%H:%M:%S)] Tracking DDD progress..."

  local total_score=0
  local domain_scores=""
  local completed_domains=0

  for domain in "${DOMAINS[@]}"; do
    local score=$(check_domain "$domain")
    total_score=$((total_score + score))
    domain_scores="$domain_scores\"$domain\": $score, "

    [ "$score" -ge 30 ] && completed_domains=$((completed_domains + 1))
  done

  # Calculate overall progress
  local max_total=$((${#DOMAINS[@]} * 100))
  local progress=$((total_score * 100 / max_total))

  # Count DDD artifacts (Python patterns)
  local entities=$(count_entities "class \w+.*:")
  local value_objects=$(count_entities "@dataclass|class \w+Value")
  local aggregates=$(count_entities "class \w+Aggregate")
  local repositories=$(count_entities "class \w+Repo|Repository")
  local services=$(count_entities "class \w+Service|async def|def handle_")
  local events=$(count_entities "class \w+Event|DomainEvent")

  # Write DDD metrics
  cat > "$DDD_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "progress": $progress,
  "domains": {
    ${domain_scores%,*}
  },
  "completed": $completed_domains,
  "total": ${#DOMAINS[@]},
  "artifacts": {
    "entities": $entities,
    "valueObjects": $value_objects,
    "aggregates": $aggregates,
    "repositories": $repositories,
    "services": $services,
    "domainEvents": $events
  }
}
EOF

  # Update v3-progress.json
  if [ -f "$V3_PROGRESS" ] && command -v jq &>/dev/null; then
    jq --argjson progress "$progress" --argjson completed "$completed_domains" \
      '.ddd.progress = $progress | .domains.completed = $completed' \
      "$V3_PROGRESS" > "$V3_PROGRESS.tmp" && mv "$V3_PROGRESS.tmp" "$V3_PROGRESS"
  fi

  echo "[$(date +%H:%M:%S)] ✓ DDD: ${progress}% | Domains: $completed_domains/${#DOMAINS[@]} | Entities: $entities | Services: $services"

  date +%s > "$LAST_RUN_FILE"
}

case "${1:-check}" in
  "run"|"track") track_ddd ;;
  "check") should_run && track_ddd || echo "[$(date +%H:%M:%S)] Skipping (throttled)" ;;
  "force") rm -f "$LAST_RUN_FILE"; track_ddd ;;
  "status")
    if [ -f "$DDD_FILE" ]; then
      jq -r '"Progress: \(.progress)% | Domains: \(.completed)/\(.total) | Entities: \(.artifacts.entities) | Services: \(.artifacts.services)"' "$DDD_FILE"
    else
      echo "No DDD data available"
    fi
    ;;
  *) echo "Usage: $0 [run|check|force|status]" ;;
esac
