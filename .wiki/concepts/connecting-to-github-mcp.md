---
title: Connecting to GitHub MCP
type: concept
status: active
tags: ["github", "mcp", "cli", "api"]
created: 2026-04-13
updated: 2026-04-13
summary: Connecting to GitHub MCP involves using the GitHub CLI or API to authenticate and access your GitHub account. This can be done using a personal access token or SSH keys. Once connected, you can manage your GitHub repositories and collaborate with others.
wikilinks:
  - [[./concepts/github-cli]]
  - [[./concepts/github-api]]
  - [[./entities/github]]
confidence: high
source: claude-code
---

Connecting to GitHub MCP allows you to manage your GitHub repositories and collaborate with others. To connect, you can use the GitHub CLI or API. The GitHub CLI provides a command-line interface for managing your GitHub repositories, while the GitHub API allows you to access your GitHub data programmatically. You can authenticate using a personal access token or SSH keys. Once connected, you can use the GitHub CLI or API to manage your repositories, create new ones, and collaborate with others. For example, you can use the GitHub CLI to create a new repository by running the command `gh repo create my-repo`. You can also use the GitHub API to create a new repository by sending a POST request to the `https://api.github.com/repos` endpoint.