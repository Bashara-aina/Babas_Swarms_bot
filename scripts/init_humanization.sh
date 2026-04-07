#!/bin/bash
set -euo pipefail

echo "Initializing Legion v6 humanization storage..."
MEMORY_ROOT="$HOME/.legionswarm/memory"
mkdir -p "$MEMORY_ROOT"

echo "Storage path: $MEMORY_ROOT"
echo "Available space:"
df -h "$HOME/.legionswarm" 2>/dev/null || df -h "$HOME"

echo ""
echo "Legion will store:"
echo "  - archival.db        (unlimited conversation memories)"
echo "  - recall.db          (full conversation history)"
echo "  - temporal_graph.db  (knowledge graph with time tracking)"
echo "  - core_memory.json   (high-priority always-in-context facts)"
echo "  - user_profile.json  (permanent profile of Bashara)"
echo "  - emotion_state.json (Legion's emotional state)"
echo "  - opinions.json      (Legion's formed opinions)"
echo "  - reflections.json   (deep reflection history)"
echo ""
echo "With 5TB storage, Legion does not need to forget anything."
echo "Done. Run: python3 main.py"
