# SwarmBot Routing System

SwarmBot routes tasks through a three-layer pipeline: **keyword matching** → **semantic classification** → **LLM model selection**.

---

## Layer 1 — Keyword Routing (`config/routing_keywords.yaml`)

First-pass routing uses keyword-to-agent mapping. The engine scans the incoming message for keyword triggers and returns a priority-ordered list of candidate agents.

```yaml
# Example keyword rules
python:          [senior_python_dev, backend_fastapi_dev]
fastapi:         [backend_fastapi_dev, senior_python_dev]
react:           [frontend_react_dev]
debug:           [debugging_specialist]
traceback:       [debugging_specialist]
crash:           [debugging_specialist]
sql:             [database_optimizer]
postgres:        [database_optimizer]
pentest:         [security_pentester]
vulnerability:   [security_pentester, smart_contract_auditor]
owasp:           [security_pentester]
cuda:            [cuda_optimizer]
gpu:             [cuda_optimizer, mlops_engineer]
test:            [test_automation_engineer]
pytest:          [test_automation_engineer]
cicd:            [cicd_architect]
github_actions:   [cicd_architect]
docker:          [cicd_architect, mlops_engineer]
kubernetes:       [cicd_architect, mlops_engineer]
deploy:          [cicd_architect]
mlops:           [mlops_engineer]
mlflow:          [mlops_engineer]
api:             [api_designer, senior_python_dev]
openapi:         [api_designer]
graphql:         [api_designer]
review:          [code_reviewer]
refactor:        [code_reviewer, senior_python_dev]
performance:     [performance_tuner, cuda_optimizer]
benchmark:       [performance_tuner]

# Design keywords
ux:              [ux_designer]
ui:              [ux_designer, ui_reviewer]
figma:           [ux_designer]
wireframe:       [wireframe_specialist]
prototype:       [prototype_builder]
branding:        [branding_strategist]
logo:            [branding_strategist, graphic_designer]
animation:       [motion_artist]
motion:          [motion_artist]
3d:              [spatial_designer]
spatial:         [spatial_designer]
blender:         [spatial_designer]
color:           [color_expert]
palette:         [color_expert]
accessibility:   [accessibility_auditor]
wcag:            [accessibility_auditor]
a11y:            [accessibility_auditor]
flow:            [user_flow_mapper]
journey:         [user_flow_mapper]

# Research keywords
research:        [deep_researcher]
source:          [deep_researcher, paper_summarizer]
trend:           [trend_forecaster]
forecast:        [trend_forecaster]
competitor:      [competitor_analyst]
competitive:     [competitor_analyst]
data:            [data_scientist]
csv:             [data_scientist]
dataframe:       [data_scientist]
pandas:          [data_scientist]
statistics:      [stats_modeler, data_scientist]
regression:      [stats_modeler]
scrape:          [web_scraper_coordinator]
crawl:           [web_scraper_coordinator]
sentiment:       [sentiment_analyst]
opinion:         [sentiment_analyst]
market:          [market_intel, competitor_analyst]
intel:           [market_intel]
survey:          [survey_designer]
questionnaire:   [survey_designer]
interview:       [interview_simulator]
patent:          [patent_searcher, ip_lawyer]
arxiv:           [paper_summarizer]
paper:           [paper_summarizer]
summary:         [paper_summarizer, deep_researcher]

# Marketing keywords
copy:            [copywriter, ad_copywriter]
copywrite:       [copywriter]
headline:        [copywriter]
landing:         [copywriter, ux_designer]
seo:             [seo_specialist]
keyword:         [seo_specialist]
social:          [social_media_strategist]
twitter:         [social_media_strategist]
instagram:       [social_media_strategist]
growth:          [growth_hacker]
viral:           [viral_campaign_designer, growth_hacker]
content:         [content_strategist]
editorial:       [content_strategist]
ad:              [ad_copywriter]
ppc:             [ad_copywriter]
email:           [email_marketer]
newsletter:      [email_marketer]
influencer:      [influencer_outreach]
brand:           [brand_voice_developer, branding_strategist]
voice:           [brand_voice_developer]
crisis:          [pr_crisis_manager]
pr:              [pr_crisis_manager]
analytics:       [analytics_interpreter, data_scientist]

# Operations keywords
project:         [project_manager]
scrum:           [project_manager]
agile:           [project_manager]
task:            [task_coordinator]
coordinate:      [task_coordinator]
schedule:        [scheduler]
calendar:        [scheduler]
deadline:        [scheduler]
budget:          [cost_tracker]
finance:         [cost_tracker]
resource:        [resource_allocator]
capacity:        [resource_allocator]
workflow:        [workflow_optimizer]
process:         [workflow_optimizer]
dashboard:       [reporting_builder]
report:          [reporting_builder]
kpi:             [reporting_builder]

# Legal / Compliance keywords
contract:        [contract_reviewer]
legal:           [contract_reviewer, ip_lawyer]
gdpr:            [gdpr_expert]
privacy:         [gdpr_expert]
ccpa:            [gdpr_expert]
risk:            [risk_assessor]
trademark:       [ip_lawyer]
copyright:        [ip_lawyer]
license:          [ip_lawyer]
ethics:          [ethics_auditor]
bias:            [ethics_auditor]
compliance:      [compliance_checker]
regulation:      [compliance_checker]
audit:           [compliance_checker, smart_contract_auditor]

# Product keywords
roadmap:          [roadmap_planner]
milestone:        [roadmap_planner]
prioritize:       [feature_prioritizer]
prioritization:   [feature_prioritizer]
mvp:              [mvp_builder]
minimum:          [mvp_builder]
beta:             [beta_coordinator]
launch:           [launch_strategist]
go-to-market:     [launch_strategist]
feedback:         [feedback_analyzer]
persona:          [user_research_lead]

# Creative keywords
story:            [storyteller]
narrative:        [storyteller]
character:        [storyteller]
screenplay:       [script_writer]
script:           [script_writer]
dialogue:         [script_writer]
video:            [video_concept_artist]
storyboard:       [video_concept_artist]
music:            [music_composer]
melody:           [music_composer]
meme:             [meme_creator]
humor:            [meme_creator]
idea:             [idea_generator]
brainstorm:       [idea_generator]
poem:             [poetry_specialist]
poetry:           [poetry_specialist]
verse:            [poetry_specialist]
concept:          [concept_artist]
world:            [concept_artist, storyteller]

# Vision / Multimodal keywords (local/Ollama only)
screenshot:       [screenshot_analyzer]
screen:           [screenshot_analyzer]
diagram:          [diagram_interpreter]
chart:            [diagram_interpreter]
image:            [image_descriptor]
photo:            [image_descriptor]
picture:          [image_descriptor]
ocr:              [ocr_specialist]
extract:          [ocr_specialist]
frame:            [video_frame_analyzer]
clip:             [video_frame_analyzer]
```

### Keyword Routing Algorithm

1. **Tokenize** — split message into lowercase words/n-grams
2. **Match** — iterate keyword rules in order; collect all matching agent lists
3. **Dedupe + weight** — agent appearing in multiple matches gets higher weight
4. **Return** — priority-ordered agent list; first available agent wins

---

## Layer 2 — Department Routing (`config/departments.yaml`)

Keyword matches resolve to agents. Agents belong to **departments** (9 total):

| Department | Default Agent | Count | Description |
|---|---|---|---|
| `engineering` | `senior_python_dev` | 15 | Software development — backend, frontend, systems, security |
| `design` | `ux_designer` | 10 | UI/UX design, branding, visual design, accessibility |
| `research` | `deep_researcher` | 12 | Deep research, competitive analysis, data science |
| `marketing` | `copywriter` | 13 | Marketing, copywriting, SEO, social media, growth |
| `operations` | `project_manager` | 7 | Project management, scheduling, resource allocation |
| `legal_compliance` | `contract_reviewer` | 6 | Legal review, compliance, privacy, risk, IP |
| `product` | `product_manager` | 9 | Product management, roadmapping, user research |
| `creative` | `storyteller` | 8 | Creative content — storytelling, scripts, music, poetry |
| `vision_multimodal` | `screenshot_analyzer` | 6 | Vision analysis — all local via Ollama (never external) |
| `legacy` | `general` | 22 | Legacy 22-agent registry for backwards compatibility |

### Agent Resolution

```python
# Pseudocode
def resolve_agent(keyword_matches):
    if len(keyword_matches) == 1:
        return keyword_matches[0]
    # Multiple candidates — prefer by:
    # 1. Higher keyword match count
    # 2. Agent complexity_tier (heavyweight when task is complex)
    # 3. Department default_agent as tiebreaker
    return ranked_agents[0]
```

---

## Layer 3 — LLM Model Selection (`config/departments.yaml` / `config/models.yaml`)

Each agent has a `primary_model` and `fallbacks` list. Model keys reference `config/models.yaml`.

### Model Routing by Task Complexity

| Tier | Agents | Primary Model | Fallbacks |
|---|---|---|---|
| `heavyweight` | senior_python_dev, backend_fastapi_dev, smart_contract_auditor, security_pentester, cuda_optimizer, debugging_specialist, mlops_engineer, performance_tuner, data_scientist, stats_modeler, contract_reviewer, ip_lawyer, mvp_builder | `minimax-m3`, `kimi-k2`, `glm-4` | Multiple fallbacks listed per agent |
| `midweight` | frontend_react_dev, rust_systems_dev, test_automation_engineer, cicd_architect, database_optimizer, api_designer, code_reviewer, ux_designer, branding_strategist, motion_artist, spatial_designer, accessibility_auditor, prototype_builder, deep_researcher, trend_forecaster, competitor_analyst, web_scraper_coordinator, sentiment_analyst, market_intel, survey_designer, interview_simulator, patent_searcher, paper_summarizer, copywriter, seo_specialist, social_media_strategist, growth_hacker, content_strategist, viral_campaign_designer, email_marketer, influencer_outreach, analytics_interpreter, brand_voice_developer, pr_crisis_manager, project_manager, cost_tracker, resource_allocator, workflow_optimizer, reporting_builder, gdpr_expert, risk_assessor, ethics_auditor, compliance_checker, product_manager, roadmap_planner, user_research_lead, feedback_analyzer, launch_strategist, storyteller, script_writer, video_concept_artist, music_composer, concept_artist | `qwen3-235b`, `gemini-3.1-pro`, `devstral`, `glm-4` | 2-3 fallbacks |
| `lightweight` | graphic_designer, wireframe_specialist, color_expert, user_flow_mapper, ad_copywriter, task_coordinator, scheduler, meme_creator, idea_generator, poetry_specialist, beta_coordinator, feature_prioritizer, screenshot_analyzer, diagram_interpreter, ui_reviewer, image_descriptor, ocr_specialist, video_frame_analyzer, general, humanizer | `kimi-k2`, `gemini-3.1-pro`, `qwen3-235b` | 1-2 fallbacks |

### Vision Agents — Always Local

The `vision_multimodal` department agents (`screenshot_analyzer`, `diagram_interpreter`, `ui_reviewer`, `image_descriptor`, `ocr_specialist`, `video_frame_analyzer`) **always use `gemma4-local`** via Ollama. These are routed locally to ensure privacy — screenshots and images never leave the RTX 3060 machine.

---

## Full Routing Flow

```
User message
    │
    ▼
┌─────────────────────────────────────┐
│  Layer 1: Keyword Matching          │
│  config/routing_keywords.yaml        │
│  → returns [agent_a, agent_b, ...]  │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Layer 2: Department Resolution     │
│  config/departments.yaml            │
│  → resolves to specific agent       │
│    with primary_model + fallbacks    │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Layer 3: LLM Model Selection       │
│  config/models.yaml                 │
│  → picks model per complexity_tier  │
│    and agent primary_model setting  │
└──────────────────┬──────────────────┘
                   │
                   ▼
            LLM Inference
```

---

## OpenCode Agents (411 files in `.opencode/agents/`)

The OpenCode agent directory contains 411 markdown files organized by department:

```
.opencode/agents/
├── azure/
├── backend/
├── blockchain/
├── cloud/
├── data/
├── db/
├── deployment-engineer.md
├── devops/
├── diff-analyzer.md
├── docs/
├── embedded/
├── focused-implementer.md
├── frontend/
├── gaming/
├── langspecialists/
├── legiona/
├── marketing/
├── media/
├── mobile/
└── web/
```

These complement the 76 agents defined in `departments.yaml` with specialized sub-agents for specific technologies and workflows. Each OpenCode agent file is a Markdown document containing the agent's system prompt, capabilities, and behavioral guidelines.

---

## Example Routing Scenarios

### "My pytest tests are failing with a mysterious traceback"

```
Layer 1 keywords detected: pytest, traceback
→ candidates: [test_automation_engineer, debugging_specialist]

Layer 2: traceback → debugging_specialist (exact match)
Layer 3: debugging_specialist.primary_model = glm-4
Result: glm-4 with debugging_specialist role
```

### "Help me optimize this CUDA kernel for GPU memory"

```
Layer 1 keywords detected: cuda, gpu, memory
→ candidates: [cuda_optimizer, mlops_engineer]

Layer 2: cuda → cuda_optimizer (primary match)
Layer 3: cuda_optimizer.primary_model = glm-4, fallbacks = [qwen3-235b, kimi-k2]
Result: glm-4 with cuda_optimizer role
```

### "Design a brand logo for my startup"

```
Layer 1 keywords detected: logo, brand
→ candidates: [branding_strategist, graphic_designer]

Layer 2: brand + logo → branding_strategist (semantic composite)
Layer 3: branding_strategist.primary_model = kimi-k2
Result: kimi-k2 with branding_strategist role
```

### "Analyze this screenshot of my app's UI"

```
Layer 1 keywords detected: screenshot, ui
→ candidates: [screenshot_analyzer, ux_designer, ui_reviewer]

Layer 2: vision keyword → vision_multimodal department
Layer 3: screenshot_analyzer.primary_model = gemma4-local (always local)
Result: gemma4-local (RTX 3060, never sent externally)
```

---

## Configuration Files Reference

| File | Purpose |
|---|---|
| `config/routing_keywords.yaml` | Layer 1: keyword → agent list mapping |
| `config/departments.yaml` | Layer 2: agent definitions with models, Layer 3: model assignments |
| `config/models.yaml` | Model definitions, capabilities, context windows |