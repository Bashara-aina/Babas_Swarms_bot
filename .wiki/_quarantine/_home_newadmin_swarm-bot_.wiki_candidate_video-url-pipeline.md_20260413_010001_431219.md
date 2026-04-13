---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/candidate/video-url-pipeline.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.431246"
}
---

# video-url-pipeline.md
Score: 8/10 — HIGH PRIORITY WRITE

## 1. Executive Summary

`tools/video.py` handles video URL understanding via a pipeline: URL classification → yt-dlp metadata extraction → optional faster-whisper transcription. Supports 12 video platforms. Falls back gracefully when transcription is unavailable.

**Pipeline**: is_video_url() → understand_video_url() → _transcribe_video_audio() → transcript appended to output

**Key finding**: Audio transcription is best-effort — failures are silently swallowed and return empty string, but the metadata output is always returned.

---

## 2. URL Classification

```python
def is_video_url(url: str) -> bool
```

Checks URL against hardcoded `_VIDEO_DOMAINS` set. Returns `True` if any domain found in URL.

**Supported domains** (12 total):
- `youtube.com`, `youtu.be`, `youtube-nocookie.com`
- `twitter.com`, `x.com`
- `xvideos.com`, `pornhub.com`
- `tiktok.com`, `instagram.com`
- `facebook.com`, `vimeo.com`

**Note**: `x.com` and `twitter.com` are the same — X rebranding not fully reflected in code.

**Limitation**: Uses simple substring matching, not regex. No protocol check. A URL like `https://youtube.com.evil.com` would match.

---

## 3. Metadata Extraction (`understand_video_url`)

```python
async def understand_video_url(url: str) -> str
```

**Command**: `yt-dlp --dump-json --no-playlist --no-check-certificates --socket-timeout 30 "{url}"`

**Timeout chain**:
1. `asyncio.wait_for(proc.communicate(), timeout=60)` — 60s hard limit on yt-dlp
2. `yt-dlp --socket-timeout 30` — 30s per-connection timeout inside yt-dlp
3. `_transcribe_video_audio()` has its own 120s timeout

**Output format** (emoji-prefixed for Telegram):
```
🎬 <b>{title}</b>

👤 Uploader: {uploader}
⏱ Duration: {duration_str}
👁 Views: {view_count:,}
👍 Likes: {like_count:,}
🏷 Tags: {tag1}, {tag2}, ...
📝 Description: {description_snippet}
📝 <b>Transcript:</b> {transcript_snippet}
```

**Duration formatting**: Converts seconds to `Xh Ym Zs` / `Ym Zs` / `Zs` depending on length.

**Description truncation**: First 500 chars, adds `…` if longer.

**Transcript truncation**: First 800 chars, adds `…` if longer.

**Error responses** (return error string, not dict):
- No URL provided → `"Error: No URL provided."`
- yt-dlp fails → `"Error: Could not extract video info (yt-dlp failed). The URL may be unsupported or private."`
- JSON parse fails → `"Error: Could not parse video metadata for {url}."`
- Timeout → `"Error: Timeout extracting video info for {url}."`
- Any exception → `"Error: Could not extract video info: {str(exc)[:200]}"`

---

## 4. Audio Transcription Pipeline (`_transcribe_video_audio`)

**Purpose**: Download audio from video and transcribe it using faster-whisper.

**Steps**:
1. Create temp file `tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)`
2. Run: `yt-dlp -x --audio-format mp3 --audio-quality 0 -o "{tmp_path}.%(ext)s" --no-playlist --no-check-certificates --socket-timeout 30 "{url}"`
3. Find actual audio file (yt-dlp appends extension to template)
4. Call `tools.minimax_media.understand_audio(actual_path)` for transcription
5. Delete all temp files in `finally` block

**Audio download timeout**: 120s via `asyncio.wait_for(proc.communicate(), timeout=120)`

**Audio file detection**: Uses `glob.glob(f"{tmp_path}.*")` and finds first file > 1000 bytes (skip empty stubs).

**Cleanup**: All audio files matching `{tmp_path}.*` deleted in `finally` block — even if transcription fails.

**Transcription failures**: Silently caught, returns `""`. No error shown to user if metadata extraction succeeded.

**No transcription happens when**: 
- `minimax_media` not installed
- Audio download fails
- Audio file is < 1000 bytes
- whisper model unavailable

---

## 5. Platform Coverage

| Platform | Metadata | Audio | Notes |
|----------|----------|-------|-------|
| YouTube | ✅ | ✅ | Full support |
| Twitter/X | ✅ | ✅ | May fail if video is quote-tweet |
| TikTok | ✅ | ✅ | Some videos geo-blocked |
| Instagram | ✅ | ✅ | Stories/Reels supported |
| Facebook | ✅ | ✅ | Some videos require auth |
| Vimeo | ✅ | ✅ | Full support |
| Pornhub/Xvideos | ✅ | ✅ | Available in `_VIDEO_DOMAINS` |

**Note**: xvideos.com and pornhub.com are explicitly in the domain list. This may be surprising for a professional tool, but the architecture handles them identically to YouTube.

---

## 6. Error Handling Deep Dive

**yt-dlp return code check**:
```python
if proc.returncode != 0:
    err = stderr.decode("utf-8", errors="replace").strip()
    return f"Error: Could not extract video info (yt-dlp failed)..."
```

**Exception hierarchy**:
- `asyncio.TimeoutError` → timeout error message
- `json.JSONDecodeError` or any parse exception → parse error message
- `Exception` (catch-all) → generic error with first 200 chars of exception

**Logging**: All failures logged via `logger.warning()` or `logger.debug()` — never to user-facing output unless function returns error string.

**Silent failures** (return "", not error):
- Audio download fails → cleanup temp files, return `""`
- Whisper not available → return `""`
- Audio file < 1000 bytes → return `""`

---

## 7. Temp File Lifecycle

```
understand_video_url(url)
  → _transcribe_video_audio(url)
      → tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
         → yt-dlp downloads audio to {tmp_path}.mp3
         → glob.glob("{tmp_path}.*") → finds actual file
         → understand_audio() transcription
         → finally: os.unlink() all matching files
```

**Key safety**: 
- `delete=False` means Python doesn't auto-delete — rely on explicit `finally` block cleanup
- `tmp_audio.close()` called before yt-dlp runs (releases file handle so yt-dlp can write)

---

## 8. Timeout Strategy Summary

| Stage | Timeout | Mechanism |
|-------|---------|-----------|
| yt-dlp metadata | 60s | `asyncio.wait_for(proc.communicate(), timeout=60)` |
| yt-dlp socket | 30s | `--socket-timeout 30` flag inside yt-dlp |
| Audio download | 120s | `asyncio.wait_for(proc.communicate(), timeout=120)` |
| Full understand_video_url | ~180s+ | Sum of above + transcription |

---

## 9. Integration Points

- **Router**: `is_video_url()` called by something to detect video URLs — not yet wired to intent router
- **minimax_media**: `_transcribe_video_audio()` calls `tools.minimax_media.understand_audio()` for transcription
- **output**: Returns HTML-formatted string with `<b>` tags for Telegram rendering

---

## 10. Known Gaps

1. **URL allowlist**: `is_video_url()` uses simple substring match — no TLD validation, no against-known-bad check
2. **Playlist handling**: `--no-playlist` always used — playlists not supported
3. **Rate limiting**: No backoff if YouTube returns 429
4. **Proxy support**: `--no-check-certificates` present but no ` --proxy` flag
5. **Not wired to routing**: `is_video_url()` exists but intent router doesn't route video URLs to this tool

---

tokens_estimated: 680
inject_into: tools-inventory.md (video tool section), tool-output-formatting.md (video output section)