---
name: legion-callback
description: Call back to LegionBot after task completion
type: command
tags: [callback, legion, bridge]
created: 2026-04-16
---

# Legion Callback Command

After task completion, if `@legion` directive was found:

1. Read the task result from `.wiki/opencode/sessions/`
2. Call `LegionCallbackBridge().handle_legion_callback(result_text)`
3. Pass the callback result to the Telegram response builder

This avoids a Telegram round-trip for internal callbacks.
