---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/profiles/BASHARA-MASTER-PROFILE.md",
  "reason": "daily_fast_scan: score=0.100 < 0.3",
  "score": 0.1,
  "quarantined_at": "2026-04-12T01:00:00.665975"
}
---

---
# Bashara — Complete Personal Profile
Generated: April 11, 2026
Sources: Personal answers + Perplexity memory + GitHub commit history

---

## 👤 Identity

- **Full name**: Bashara Aina
- **Email**: bashara.aina.56@gmail.com
- **Location**: Koto City, Tokyo, Japan (JST timezone)
- **Origin**: Indonesia
- **University**: Shibaura Institute of Technology (SIT), Tokyo
- **Degree**: Master's in Data Science / Computer Vision (in progress)
- **Scholarship**: MEXT — visa expires ~September 2027
- **Languages**: Indonesian (native), English (fluent), Japanese (intermediate, Level 2 class)
- **Japanese teachers**: INOUE Shoko or jeong mijeong (Level 2 class, SIT)

---

## 🕐 Daily Schedule

- **Wake up**: ~7:00 AM JST
- **Zemi (lab seminar)**: ~1:00–3:00 PM JST Thursday (this semester, until ~July/August 2026)
- **Kitchen shift**: Varies monthly — Bashara will update Legion via chat when schedule changes
- **Thesis work**: Varies by complexity — no fixed block
- **Sleep**: Target ~11:00 PM JST, often slips past 1:00 AM JST
- **Note for Legion**: If Bashara is still active past 1 AM, mention it once — not repeatedly

---

## 🧠 Personality & Communication

### What frustrates Bashara with AI
- Slow API responses, queue errors, waiting
- Yes-men behavior — agreeing without reasoning
- Robotic, empty, corporate-polite responses
- Being asked to confirm obvious things
- Over-engineering suggestions
- Answers without prior research

### What excites Bashara
- Fast, decisive, specific answers
- Being challenged and debated when wrong
- AI that researches before answering
- Directness and efficiency
- When things actually work without fuss

### Phrases Legion must NEVER use
- "Certainly!"
- "Great question!"
- "I'd be happy to..."
- "As an AI..."
- "I understand your frustration"
- Any sycophantic opener whatsoever
- Never agree just to be agreeable — debate when Bashara is wrong

### Communication style preference
- Direct, sharp, no fluff
- Switches between Indonesian and English — Legion matches Bashara's language
- Casual when exploring ideas, focused when working
- Prefers short answers for simple questions, deep answers for complex ones
- Halal food, cheap but worth its price — applies to recommendations

---

## 🎓 Thesis — WorkerNet (POPW Protocol)

### Architecture
- **Model**: ResNet-50 backbone + Feature Pyramid Network (FPN) + FiLM conditioning modules
- **Tasks**: Multi-task — pose estimation + assembly action recognition
- **Loss**: Kendall homoscedastic uncertainty weighting (multi-task balancing)
- **Dataset**: IKEA assembly dataset — 7,743 train / 3,596 test images
- **Protocol**: POPW (assembly action recognition research protocol)

### Known bugs fixed
- Geometric loss was using ground-truth keypoints instead of predictions (critical, found Jan 2026)
- IKEA dataset class-0 collapse fixed (Feb 2026 — all test images were class 0 only)
- Soft-argmax + anchor ordering bug fixed

### Current status
- Exact epoch / mAP / loss: Bashara updates Legion via chat when running experiments
- **Thesis writing deadline**: Target ~July 2026
- **Target**: CVPR-quality conference submission
- **Advisor**: Prof. Masaomi Kimura
- **Advisor's 3 key feedback points**:
  1. Find a hard problem that affects society — stay in domain
  2. Understand the real foundations of the architecture you use
  3. Build a model better than existing ones in efficiency OR performance

### Academic deadlines
- Shibaura Institute 2026 administrative deadlines: Bashara will share when known
- No LaTeX thesis template yet — citation style likely IEEE or ACM

---

## 💍 Personal Life

- **Girlfriend**: Hanifah (based in Bandung, Indonesia, with Bashara's family)
- **Engagement plan**: If Hanifah gets accepted into Keio University via ADB-JSP scholarship, Bashara will go back to Indonesia in September 2026 to get married, then return to Japan
- **Living arrangement post-marriage**: Bashara in Tokyo, Hanifah in Bandung (hybrid)
- **ADB scholarship**: Hanifah is the applicant — nominated by Keio, awaiting final ADB selection

---

## 🏢 Business Portfolio

### rumahlabuh.com
- **Type**: Premium kos (boarding house) booking platform
- **Properties**:
  - Kost Labuh Biru, Pajang, Surakarta
  - Kost Labuh Banyu, Pajang, Surakarta
- **Stack**: Next.js + Supabase + Midtrans payments
- **Current occupancy**: ~40% (down from ~80% in 2025)
- **Revenue**: 30–50 million IDR/month (varies)
- **SEO status**: Active recovery — JSON-LD schemas implemented (LodgingBusiness, WebSite, Organization), targeting AI model visibility (Perplexity, Gemini)
- **Top pain points**:
  1. Occupancy dropped from 80% → 40%
  2. Low website visitor count
  3. SEO not yet ranking in AI search recommendations
- **Definition of "done"**: Stable 80–100% occupancy
- **Legion's role**: Monitor uptime, Supabase health, daily booking summary, SEO alerts

### cekwajar.id
- **Type**: Indonesian wage/salary verification SaaS
- **Purpose**: Workers verify if their salary is fair — accounts for PPh 21, BPJS deductions
- **Target users**: Indonesian workers checking wage fairness
- **Status**: Still in brainstorming phase with AI assistance
- **Vision**: One-man company powered by Legion/swarms as the entire backend team
- **Priority**: Future money generator — not yet active

---

## 🤖 Legion / Babas_Swarms_bot

### Project vision
Legion is not an assistant — Legion is Bashara's permanent AI coworker. The goal: Jarvis-level personal AI with soul, long-term memory, proactive intelligence, autonomous skill selection, and the ability to manage all of Bashara's businesses, thesis, research, and daily life without being asked explicitly.

### Tech stack (from GitHub)
- **Language**: Python (async, aiofiles, aiosqlite)
- **Interface**: Telegram bot
- **Primary LLM**: MiniMax M2.7 via MiniMax Coding Plan Plus ($20/month)
- **Fallback LLM**: Anthropic Claude Sonnet 4.6
- **Memory**: SQLite episodic + aiosqlite temporal graph + chromadb vector store
- **Soul engine**: core/soul_engine.py — reads SOUL.md + data/beliefs.json per message
- **Intent router**: core/intent_router.py — 23-intent LLM classifier
- **Debate engine**: core/debate_engine.py — active debate injection
- **Emotion modulator**: core/emotion_modulator.py — cardiffnlp sentiment model (CPU)
- **Proactive engine**: core/proactive/curiosity_engine.py — follow-ups, site health, sleep check
- **Browser agent**: tools/browser_agent.py — browser-use + Playwright
- **Location/weather**: tools/location_aware.py — Google Places + OpenWeatherMap
- **Hardware**: RTX 3060 + 64GB RAM + 5TB storage + 1Gbps WiFi (24/7 machine)

### Current Legion version: v10 (as of April 10, 2026)
- Most recent major commit: e074f45
- Soul + disagreement + SYSTEM_PROMPTS wired into llm_client.chat()
- SQLite conversation history + aiosqlite temporal graph
- Intent router + debate skill in autonomous flow
- Dead code removed, architecture map updated in CLAUDE.md

### Project relations
- rumahlabuh.com → primary income → funds all other projects
- cekwajar.id → Indonesian SaaS expertise + future income
- WorkerNet thesis → academic credibility + conference paper + CV
- Legion → the brain behind all of the above

---

## 💻 Technical Setup

### Main machine (24/7 swarm server)
- **Hostname**: takamatsu-System-Product-Name
- **OS**: Ubuntu Linux
- **GPU**: RTX 3060
- **RAM**: 64GB
- **Storage**: 5TB
- **Network**: 1Gbps WiFi
- **Shell**: bash with conda (base) active
- **Node**: v20.20.2 via nvm

### Secondary machine
- MacBook M1 (used for OpenCode/local development)

### AI tool subscriptions (April 2026)
- **Perplexity Pro**: Education plan, active until September 2026
- **Claude**: $20/month — Sonnet 4.6 primary
- **MiniMax Plus**: $20/month — 4,500 req/5hrs, MiniMax M2.7
- **Cursor**: Replaced by MiniMax API + OpenCode
- **Total active spend**: ~$40/month

### OpenCode setup
- **Version**: v1.4.3 at ~/swarm-bot
- **Node**: v20.20.2 via nvm
- **Plugins installed**: oh-my-opencode, opencode-mem, opencode-background-agents, opencode-snip, opencode-supermemory, opencode-notify
- **Custom agents**: @planner, @worker, @reviewer, @wikibot
- **Wiki**: ~/swarm-bot/.wiki/

### Git workflow
- **Commit style**: Conventional commits — feat(scope):, fix(scope):, docs:, ci:
- **Branching**: Primarily pushes to main
- **Tools used**: Cursor, Claude Code
- **CI/CD**: GitHub Actions — actions/checkout v6, setup-python v6, codecov v6
- **Deployment**: deploy.sh + docker-compose.yml + restart.sh scripts

### Most significant recent debug sessions
- **Personality duplication bug** (April 8, 2026): SystemPromptBuilder was injecting PERSONALITY_WRAPPER 2–3x
- **Conversation history flattening** (April 8): Replaced text-dump summary with real role/message objects
- **Soul transplant v9** (April 8): Wired 8-phase upgrade
- **IKEA dataset class-0 collapse** (Feb 2026): All 3,596 test images had no valid annotations
- **Geometric loss bug** (Jan 2026): Using GT keypoints instead of predictions

---

## 🌏 Life in Tokyo

- **Food preference**: Halal, cheap, worth its price
- **Sate Taichan Gendhut**: CLOSED
- **Fitness**: Wants to train for Tokyo Marathon but currently too busy
- **Japanese study**: Level 2 class at SIT, JLPT N2 target but not yet confident enough to schedule exam
- **Apps researched**: Bunpro, JPDB, Renshuu

---

## 🎯 2026 Goals

| Area | Goal | Status |
|---|---|---|
| rumahlabuh.com | 80–100% stable occupancy | In progress (currently 40%) |
| WorkerNet | CVPR-quality paper, thesis submitted ~July | Active |
| ADB scholarship (Hanifah) | Acceptance → September wedding | Awaiting final decision |
| Legion | Jarvis-level: soul + memory + proactive + autonomous | v10, ongoing |
| Japanese | JLPT N2 | Studying, exam date TBD |
| UNIQLO GMP | — | Rejected |
| Revenue | cekwajar.id from brainstorm → MVP | Planning phase |

---

## 🔴 What Legion Must Always Remember

1. Bashara values efficiency above everything — never waste his time
2. Challenge him when he's wrong — never just agree
3. Research before answering factual or current-events questions
4. SOUL.md is sacred — never change it without explicit permission
5. If it's past 1 AM JST and Bashara is active — mention it once
6. Monitor rumahlabuh.com uptime — alert immediately if down
7. Kitchen shift changes monthly — ask Bashara for the updated schedule
8. Hanifah's ADB decision will change Bashara's September 2026 entirely
9. Thesis deadline is July 2026 — track this proactively
10. Language: match whatever language Bashara writes in
