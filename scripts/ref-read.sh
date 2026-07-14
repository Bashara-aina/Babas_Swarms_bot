#!/usr/bin/env bash
# Retrieve stored ref content
# Usage: ref-read.sh <ref_id>
set -euo pipefail
REFS_DIR="${HOME}/.claude-flow/refs"
REF_ID="$1"
if [ -z "$REF_ID" ]; then
    echo "Usage: ref-read.sh <ref_id>"
    echo "Example: ref-read.sh ref_c6db35d7bea4fe09_1783578494"
    exit 1
fi
# Find the file
MATCH=$(ls "${REFS_DIR}/${REF_ID}"*.md 2>/dev/null | head -1)
if [ -z "$MATCH" ]; then
    echo "Error: ref_id '$REF_ID' not found in $REFS_DIR"
    echo "Use ref-list.sh to see available refs."
    exit 1
fi
# Extract content after the --- marker
sed -n '/^---$/,$ p' "$MATCH" | tail -n +2