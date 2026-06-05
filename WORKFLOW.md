name: Legion Swarm Workflow
description: Multi-agent orchestration for the swarm-bot stack with MiniMax-native browser intelligence

version: "1.0"

projects:
  - name: swarm-bot
    linear_team_id: null
    default_branch: main

agents:
  - name: planner
    role: Task decomposition and planning
    model: minimax/MiniMax-M3
    tools:
      - sequential_thinking
      - ruflo_task_create
      - memory_search

  - name: worker
    role: Execute implementation tasks
    model: minimax/MiniMax-M3
    tools:
      - browser_open
      - browser_run_task
      - crawl4ai_crawl
      - filesystem_write
      - bash

  - name: browser-automation
    role: Autonomous browser tasks
    model: minimax/MiniMax-M3
    tools:
      - browser_open
      - browser_click
      - browser_fill
      - browser_screenshot
      - browser_get_text
      - browser_run_task

  - name: web-researcher
    role: Web content discovery and synthesis
    model: minimax/MiniMax-M3
    tools:
      - exa_web_search_exa
      - crawl4ai_crawl
      - browser_run_task

  - name: reviewer
    role: Code and plan quality review
    model: minimax/MiniMax-M3
    tools:
      - sequential_thinking

poll_interval_ms: 5000
max_concurrent_agents: 3

browser_task_workflow:
  - step: plan
    agent: planner
    prompt: "Use sequential-thinking to plan multi-step browser tasks before execution."

  - step: route
    agent: worker
    prompt: "Decide routing: browser-use for interactive tasks, crawl4ai for static content."

  - step: execute
    agent: browser-automation
    prompt: "Execute browser task via MCP browser_run_task tool."

  - step: save
    prompt: "Save screenshots and artifacts to .opencode/logs/browser-artifacts/"

  - step: remember
    agent: worker
    prompt: "Store significant findings in mem0ai for cross-session memory."
