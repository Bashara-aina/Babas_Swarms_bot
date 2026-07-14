#!/usr/bin/env bash
# build-textidote.sh — one-shot builder for textidote.jar
#
# Textidote ships only as source. This script installs OpenJDK 17 + Apache Ant,
# clones textidote, runs its ant build, and installs the JAR at the path the
# textidote_mcp server expects (~swarm-bot/tools/textidote/textidote.jar).
#
# Usage:
#   ./bin/build-textidote.sh     # interactive (sudo may prompt for password)
#
# Idempotent: re-running skips work that's already done.
#
# Requires: sudo access (or root). If sudo is unavailable, see README.md
# for manual steps.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${PROJECT_ROOT}/tools/textidote/textidote.jar"
SRC_DIR="${TXT_SRC_DIR:-/tmp/textidote}"

# ─── 1. JDK + ant ─────────────────────────────────────────────────────────
if ! command -v javac >/dev/null 2>&1; then
  echo "[build-textidote] installing OpenJDK 17 ..."
  sudo apt-get update -qq
  sudo apt-get install -y openjdk-17-jdk-headless
fi

if ! command -v ant >/dev/null 2>&1; then
  echo "[build-textidote] installing Apache Ant ..."
  sudo apt-get install -y ant
fi

# ─── 2. Clone source ──────────────────────────────────────────────────────
if [ ! -d "${SRC_DIR}" ]; then
  echo "[build-textidote] cloning textidote source to ${SRC_DIR} ..."
  git clone --depth=1 https://github.com/sylvainhalle/textidote.git "${SRC_DIR}"
fi

# ─── 3. Build ─────────────────────────────────────────────────────────────
cd "${SRC_DIR}"
echo "[build-textidote] running ant download-deps ..."
ant -q download-deps
echo "[build-textidote] running ant ..."
ant -q

# ─── 4. Install ───────────────────────────────────────────────────────────
if [ ! -f "${SRC_DIR}/textidote-0.9.jar" ]; then
  echo "[build-textidote] ERROR: expected textidote-0.9.jar not found after build"
  ls -la "${SRC_DIR}/"*.jar 2>&1 | head -5
  exit 1
fi

mkdir -p "$(dirname "${DEST}")"
cp -f "${SRC_DIR}/textidote-0.9.jar" "${DEST}"

echo "[build-textidote] OK — installed $(file "${DEST}" | head -1)"
echo "[build-textidote] verify: java -jar ${DEST} --help"
