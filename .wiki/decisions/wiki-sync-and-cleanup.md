---
title: Wiki Sync and Cleanup
type: decision
status: active
tags: ["wiki", "sync", "cleanup"]
created: 2026-04-13
updated: 2026-04-13
summary: Decided to sync wiki content to .wiki directory, fix remaining YAML failures, and run wiki health pulse. Considered deleting /wiki directory, but decided to keep it for future reference.
wikilinks:
  - [[concepts/wiki-sync]]
  - [[entities/conda-environment]]
confidence: high
source: claude-code
---

To ensure consistency and ease of maintenance, it's recommended to sync wiki content to the .wiki directory. This involves fixing remaining pre-existing YAML failures in the old content and running a wiki health pulse to identify any issues. While it might seem redundant to keep the /wiki directory, it's better to err on the side of caution and maintain a record of the original wiki content for future reference.