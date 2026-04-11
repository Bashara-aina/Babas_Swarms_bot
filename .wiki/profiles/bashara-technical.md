# Bashara — Technical Deep Dive
Generated: April 11, 2026
Source: BASHARA-MASTER-PROFILE + swarm-bot codebase

---

## Hardware

### Main Machine (24/7 swarm server)
- **Hostname**: takamatsu-System-Product-Name
- **OS**: Ubuntu Linux
- **GPU**: NVIDIA RTX 3060 12GB
- **RAM**: 64GB
- **Storage**: 5TB
- **Network**: 1Gbps WiFi
- **Shell**: bash with conda (base) active
- **Node.js**: v20.20.2 via nvm

### Secondary Machine
- MacBook M1 (used for OpenCode/local development)

---

## AI Tool Subscriptions (April 2026)
| Tool | Plan | Cost | Status |
|---|---|---|---|
| Perplexity Pro | Education | ~$20/month? | Active until Sept 2026 |
| Claude | $20/month | $20/month | Sonnet 4.6 primary |
| MiniMax Plus | Coding Plan Plus | $20/month | 4,500 req/5hrs, M2.7 |
| Cursor | Replaced | — | MiniMax API + OpenCode |
| **Total** | | **~$40/month** | |

---

## OpenCode Setup
- **Version**: v1.4.3 at ~/swarm-bot
- **Node**: v20.20.2 via nvm
- **Plugins installed**:
  - oh-my-opencode
  - opencode-mem
  - opencode-background-agents
  - opencode-snip
  - opencode-supermemory
  - opencode-notify
- **Custom agents**: @planner, @worker, @reviewer, @wikibot
- **Wiki**: ~/swarm-bot/.wiki/

---

## Python Environment
- **Version**: Python 3.13
- **ML frameworks**: PyTorch, CUDA
- **Key packages**: aiofiles, aiosqlite, httpx, litellm 1.57+

---

## Git Workflow
- **Commit style**: Conventional commits — `feat(scope):`, `fix(scope):`, `docs:`, `ci:`
- **Branching**: Primarily pushes to main — feature work done in-branch occasionally
- **Tools**: Cursor (Made-with: Cursor tag), Claude Code (Made-with: Claude)
- **CI/CD**: GitHub Actions — actions/checkout v6, setup-python v6, codecov v6
- **Deployment**: deploy.sh + docker-compose.yml + restart.sh scripts

---

## API Registry (by name — values NOT included)

### LLM Providers
| Provider | API Key Env Var | Purpose |
|---|---|---|
| MiniMax | MINIMAX_API_KEY | Primary LLM (M2.7) |
| Anthropic | ANTHROPIC_API_KEY | Fallback LLM |
| Groq | GROQ_API_KEY | Free tier fallback |
| OpenAI | OPENAI_API_KEY | Optional |
| Gemini | GEMINI_API_KEY | Optional |
| OpenRouter | OPENROUTER_API_KEY | Optional multi-model |

### Data & Storage
| Service | Env Var | Purpose |
|---|---|---|
| Supabase | SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY | rumahlabuh.com DB |
| Mem0 Cloud | MEM0_API_KEY | Semantic memory (optional) |
| ChromaDB | CHROMADB_HOST, CHROMADB_PORT | Vector store |

### Integrations
| Service | Env Var | Purpose |
|---|---|---|
| Composio | COMPOSIO_API_KEY | Gmail/Calendar/GitHub/WhatsApp |
| Google Places | GOOGLE_PLACES_API_KEY | Restaurant/hotel recommendations |
| OpenWeatherMap | OPENWEATHER_API_KEY | Weather |
| Browser Use | BROWSER_USE_MODEL | Autonomous browsing |
| n8n | N8N_WEBHOOK_PORT | Workflow automation |
| Screenpipe | SCREENPIPE_ENABLED | Screen/audio recall |

### Voice & Audio
| Service | Env Var | Purpose |
|---|---|---|
| Kokoro | KOKORO_VOICE, KOKORO_SPEED | TTS |
| Whisper | WHISPER_MODEL, WHISPER_DEVICE | STT |

---

## Recent Debug Sessions (Most Significant)
1. **Personality duplication bug** (April 8, 2026): SystemPromptBuilder injecting PERSONALITY_WRAPPER 2–3x — fixed by passing include_personality=False flag
2. **Conversation history flattening** (April 8): Replaced text-dump summary with real role/message objects — Legion now has proper multi-turn dialogue
3. **Soul transplant v9** (April 8): Wired 8-phase upgrade — soul engine, intent router, debate engine, ML sentiment, Composio, browser agent, proactive curiosity
4. **IKEA dataset class-0 collapse** (Feb 2026): All 3,596 test images had no valid annotations — fixed by rebuilding test split
5. **Geometric loss bug** (Jan 2026): Using GT keypoints instead of predictions in geometric loss

---

## Legion v10 Smoke Tests
```bash
# Soul engine
python -c "from core.soul_engine import build_soul_context; print(build_soul_context()[:100])"

# Intent router
python -c "from core.intent_router import IntentRouter; r = IntentRouter(); print(r.classify('write me code'))"

# Memory engine
python -c "from core.memory_engine import MemoryEngine; me = MemoryEngine(); print(me.get_stats())"

# All imports
python -c "from core.soul_engine import SoulEngine; from core.memory_engine import MemoryEngine; from core.intent_router import IntentRouter; print('Core OK')"

# Run tests
pytest tests/ -x --asyncio-mode=auto -q
```

---

## Related Wiki Files
- `.wiki/profiles/BASHARA-MASTER-PROFILE.md` — full profile
- `.wiki/projects/legion-roadmap.md` — Legion architecture
