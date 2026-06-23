#!/usr/bin/env python3
"""Generate viral Threads posts with automatic language validation."""

import sys


def is_valid_indonesian_or_english(text: str) -> bool:
    """Check if text contains only Indonesian/English characters."""
    # Blocked scripts: Cyrillic, Chinese, Japanese, Korean, Arabic, Thai, etc.
    blocked_ranges = [
        (0x0400, 0x04FF),   # Cyrillic
        (0x4E00, 0x9FFF),   # Chinese
        (0x3040, 0x309F),   # Japanese Hiragana
        (0x30A0, 0x30FF),   # Japanese Katakana
        (0xAC00, 0xD7AF),   # Korean
        (0x0600, 0x06FF),   # Arabic
        (0x0E00, 0x0E7F),   # Thai
        (0x0900, 0x097F),   # Hindi/Devanagari
    ]

    for char in text:
        codepoint = ord(char)
        for start, end in blocked_ranges:
            if start <= codepoint <= end:
                return False
    return True


def validate_and_print(text: str) -> bool:
    """Validate text and print result."""
    if is_valid_indonesian_or_english(text):
        print(text)
        return True
    else:
        # Find and highlight blocked characters
        blocked = []
        script_names = {
            (0x0400, 0x04FF): "Cyrillic",
            (0x4E00, 0x9FFF): "Chinese",
            (0x3040, 0x309F): "Hiragana",
            (0x30A0, 0x30FF): "Katakana",
            (0xAC00, 0xD7AF): "Korean",
            (0x0600, 0x06FF): "Arabic",
        }
        for char in text:
            codepoint = ord(char)
            for (start, end), name in script_names.items():
                if start <= codepoint <= end:
                    blocked.append(f"{char} ({name})")
        blocked_chars = ", ".join(set(blocked))
        print(f"❌ POST DITOLAK: {blocked_chars}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: generate_threads.py <post_number> <text>")
        sys.exit(1)

    post_num = sys.argv[1]
    text = sys.argv[2] if len(sys.argv) > 2 else ""

    print(f"\n{'='*50}")
    print(f"POST {post_num}")
    print('='*50)

    if text:
        if validate_and_print(text):
            print("✅ Lolos validasi")
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # Read from stdin
        text = sys.stdin.read()
        if validate_and_print(text):
            print("✅ Lolos validasi")
            sys.exit(0)
        else:
            sys.exit(1)
