#!/bin/bash
# HITL (Human-in-the-Loop) Debug Harness Template
# Last resort when no automated repro is possible
# Usage: Copy to your project and customize

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Config - customize these
ITERATIONS=${ITERATIONS:-10}
SLEEP_BETWEEN=${SLEEP_BETWEEN:-1}
CAPTURE_DIR="./debug-capture-$(date +%Y%m%d-%H%M%S)"

# Create capture directory
mkdir -p "$CAPTURE_DIR"

echo -e "${YELLOW}=== HITL Debug Harness ===${NC}"
echo "Iterations: $ITERATIONS"
echo "Sleep between: ${SLEEP_BETWEEN}s"
echo "Capture dir: $CAPTURE_DIR"
echo ""

# Function to run your test/command
run_test() {
    local iteration=$1
    echo -e "${YELLOW}[ITER $iteration]${NC} Running test..."

    # Customize this with your actual test command
    # Example: curl the endpoint, run the script, etc.
    # Your command should output a pass/fail result
    if your-test-command-here; then
        echo -e "${GREEN}[ITER $iteration] PASS${NC}"
        return 0
    else
        echo -e "${RED}[ITER $iteration] FAIL${NC}"
        return 1
    fi
}

# Main loop
pass_count=0
fail_count=0

for i in $(seq 1 $ITERATIONS); do
    run_test $i
    result=$?

    if [ $result -eq 0 ]; then
        ((pass_count++))
    else
        ((fail_count++))
        # Capture state on failure
        timestamp=$(date +%Y%m%d-%H%M%S)
        echo "Capturing debug state to $CAPTURE_DIR/fail-$timestamp..."
        # Add your capture commands here:
        # - dmesg > "$CAPTURE_DIR/fail-$timestamp/dmesg.txt"
        # - process dump, log files, etc.
    fi

    if [ $i -lt $ITERATIONS ]; then
        sleep $SLEEP_BETWEEN
    fi
done

# Summary
echo ""
echo -e "${YELLOW}=== Summary ===${NC}"
echo -e "Passed: ${GREEN}$pass_count${NC}"
echo -e "Failed: ${RED}$fail_count${NC}"
echo -e "Success rate: $(echo "scale=2; $pass_count * 100 / $ITERATIONS" | bc)%"

if [ $fail_count -gt 0 ]; then
    echo -e "${RED}Bug reproduced${NC} - check $CAPTURE_DIR for failure artifacts"
    exit 1
else
    echo -e "${GREEN}All passed${NC} - bug not reproduced in $ITERATIONS iterations"
    exit 0
fi