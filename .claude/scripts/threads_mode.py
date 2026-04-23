#!/usr/bin/env python3
"""Threads mode management with language validation."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def is_valid_indonesian_or_english(text: str) -> bool:
    """Check if text contains only Indonesian/English characters and common punctuation."""
    # Allow: a-zA-Z0-9, Indonesian special chars (ă, ț, â, î, ş, ț, ſ, đ, ǀ, ǂ, ǃ, ʾ, ʿ, ː, ˈ, ˌ, ˈ, ʊ, ʋ, ɲ, ŋ, ɕ, ʑ, ɖ, ɗ, ʈ, ɣ, ɦ, ɭ, ɳ, ɽ, ʂ, ʐ, ɻ, ɽ, ɭ, ṇ, ɲ, ɟ, ʎ, ʝ, ɕ, ʑ, ç, ñ, ł, đ, ɾ, ʁ, ʕ, ʔ, ʜ, ʢ, ʡ, ɕ, ʑ, ɧ),
    # Common Indonesian Latin ext: àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžæøå
    # Basic Latin alphanum + common punctuation + currency symbols + Indonesian-specific
    # Also allow common emoji for engagement (limited set)
    allowed_pattern = re.compile(
        r'^[a-zA-Z0-9\s.,!?;:\'"()\-\u00C0-\u024F\u1E00-\u1EFF'
        r'\u00A0-\u00FF'  # Latin Extended
        r'Rp'  # Indonesian Rupiah
        r'/\-_+:;.@#'  # Additional allowed chars
        r'\d+'  # Numbers
        r']+$'
    )
    # Check if all lines are valid
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        if not allowed_pattern.match(line):
            # Check for Cyrillic (Russian, etc)
            if re.search(r'[\u0400-\u04FF]', line):
                return False
            # Check for Chinese
            if re.search(r'[\u4E00-\u9FFF]', line):
                return False
            # Check for Japanese/Hiragana/Katakana
            if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', line):
                return False
            # Check for Korean
            if re.search(r'[\uAC00-\uD7AF\u1100-\u11FF]', line):
                return False
            # Check for Arabic
            if re.search(r'[\u0600-\u06FF]', line):
                return False
            # Check for other non-Latin scripts
            if re.search(r'[^\u0000-\u024F\u1E00-\u1EFF\u00A0-\u00FFa-zA-Z0-9 Rp./,\-!?;:\'"()_+\d]', line):
                return False
    return True


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    state_file = root / ".claude" / ".threads_mode"

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        if state_file.exists():
            print("threads_mode=ON")
        else:
            print("threads_mode=OFF")
        return 0

    elif cmd in ("on", "enable"):
        state_file.write_text("on")
        print("threads mode enabled")
        return 0

    elif cmd in ("off", "disable"):
        if state_file.exists():
            state_file.unlink()
        print("threads mode disabled")
        return 0

    elif cmd == "toggle":
        if state_file.exists():
            state_file.unlink()
            print("threads mode disabled")
        else:
            state_file.write_text("on")
            print("threads mode enabled")
        return 0

    elif cmd == "validate":
        # Validate text from stdin
        text = sys.stdin.read()
        if is_valid_indonesian_or_english(text):
            print("VALID")
            return 0
        else:
            print("INVALID: contains non-Indonesian/English characters")
            return 1

    elif cmd == "generate":
        # Generate posts with validation
        prompt = sys.argv[2] if len(sys.argv) > 2 else "6 viral posts for rumahlabuh.com"
        print(f"Generating posts: {prompt}")
        print("Use: python threads_mode.py validate < text.txt")
        return 0

    else:
        print(f"Unknown command: {cmd}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
