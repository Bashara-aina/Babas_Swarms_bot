#!/usr/bin/env bash
# Wrapper for textidote LaTeX linter
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAR="$DIR/textidote.jar"

if [ ! -f "$JAR" ]; then
    echo "ERROR: textidote.jar not found at $JAR" >&2
    exit 1
fi

java -jar "$JAR" "$@"
