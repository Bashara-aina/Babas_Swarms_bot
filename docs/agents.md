# Legion v4 — Agent Reference

## Agent Keys & Models

| Key | Primary Model | Use Case | Trigger Keywords |
|---|---|---|---|
| `computer` | groq/llama-3.3-70b | Desktop control, tool use | (used by /do only) |
| `coding` | cerebras/qwen-3-235b | Write/review code | code, function, class, bug, implement, refactor |
| `debug` | zai/glm-4 | Debugging, reasoning | debug, error, traceback, why, fix, qwq |
| `vision` | ollama/gemma3:12b | Screenshot analysis | screenshot, image, see, look, screen |
| `math` | zai/glm-4 | Math, ML theory | tensor, gradient, loss, matrix, equation, proof |
| `architect` | groq/llama-3.3-70b | System design | design, architecture, structure, diagram, scalab |
| `analyst` | cerebras/qwen-3-235b | Data analysis | analyze, chart, metrics, compare, statistics |
| `general` | groq/llama-3.3-70b | Everything else | (default fallback) |

## Fallback Chain (per agent)

Each agent has its own fallback chain defined in `agents.py`.
If a provider is rate-limited, the next one in the chain is tried automatically.

Example for `general`:
```
ZAI → Groq → Cerebras → Gemini → OpenRouter
```

## Adding a New Agent

See [CONTRIBUTING.md](../CONTRIBUTING.md#adding-a-new-agent).

## Thread Memory

- Each user can have named threads (`/thread <name>`)
- Every response is saved to the active thread via `add_to_thread()`
- Threads are listed with `/threads`
- Context is injected into subsequent calls via `get_thread_context()`
