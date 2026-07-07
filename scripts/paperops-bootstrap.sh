#!/usr/bin/env bash
# Bootstrap a new academic paper from the paperops template.
# Usage: ./scripts/paperops-bootstrap.sh papers/my-new-paper
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <target-directory>"
    exit 1
fi

TARGET="$1"
TEMPLATE="tools/paperops-template"

if [ ! -d "$TEMPLATE" ]; then
    echo "ERROR: paperops template not found at $TEMPLATE"
    echo "Ensure the template is installed at tools/paperops-template/"
    exit 1
fi

if [ -d "$TARGET" ] && [ "$(ls -A "$TARGET" 2>/dev/null)" ]; then
    echo "ERROR: target directory '$TARGET' already exists and is not empty"
    exit 1
fi

mkdir -p "$TARGET"
# Copy all files including hidden ones, skip .git if present
rsync -a "$TEMPLATE"/ "$TARGET/" 2>/dev/null || cp -r "$TEMPLATE"/* "$TEMPLATE"/.[!.]* "$TARGET/" 2>/dev/null

cd "$TARGET"
make config

echo "✓ PaperOps template bootstrapped in '$TARGET'"
echo "  Next steps:"
echo "    cd $TARGET"
echo "    git init && git add -A && git commit -m 'Initial commit from paperops template'"
echo "    make  # build the manuscript"
