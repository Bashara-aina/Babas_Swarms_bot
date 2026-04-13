# Build Guide 06: AI Agents with Swarms Framework

**Purpose:** Run all automated tasks — scraping, data processing, data loading, scheduling  
**Framework:** kyegomez/swarms (Python)  
**LLM Backend:** Groq (free tier, 30 req/min) or Ollama (local, fully free)  
**Cost:** IDR 0

---

## What the Agents Do

| Agent | Role | Runs When |
|-------|------|-----------|
| `PropertyScraperAgent` | Scrapes 99.co + Rumah123 | Monthly scheduled |
| `SalaryScraperAgent` | Scrapes JobStreet + Karir.com | Monthly scheduled |
| `NumbeoScraperAgent` | Scrapes cost of living data | Monthly scheduled |
| `WorldBankDataAgent` | Fetches PPP + GDP via API | Quarterly |
| `BPSDataAgent` | Parses BPS CSV downloads | After BPS releases update |
| `DataValidatorAgent` | Outlier detection, k-anonymity check | After each scrape run |
| `BenchmarkAggregatorAgent` | Builds P25/P50/P75 from raw data | After validation |
| `ContentGeneratorAgent` | Generates TikTok script drafts | Weekly |
| `MonitoringAgent` | Checks site health, DB status | Daily |

---

## Step 1: Environment Setup

`[MANUAL]` — First-time setup on your machine or Fly.io:

```bash
# Python 3.11+ recommended
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Core dependencies
pip install swarms playwright playwright-stealth
pip install supabase pandas openpyxl httpx
pip install python-dotenv schedule

# Install browser for Playwright
playwright install chromium

# Create .env file
cat > .env << EOF
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
GROQ_API_KEY=gsk_...    # Free at console.groq.com
GOOGLE_VISION_API_KEY=  # Free 1000/month at console.cloud.google.com
EOF
```

---

## Step 2: Swarms Project Structure

`[CURSOR]` — Create directory structure:

```
agents/
├── __init__.py
├── config.py
├── base_agent.py
├── scrapers/
│   ├── property_scraper.py       # 99.co + Rumah123 (guide_03)
│   ├── salary_scraper.py         # JobStreet + Karir.com (guide_02)
│   ├── numbeo_scraper.py         # Numbeo CoL (guide_04 + 05)
│   └── levelsfyi_scraper.py      # Tech salaries abroad (guide_04)
├── data_loaders/
│   ├── bps_loader.py             # BPS Sakernas + CPI
│   ├── umk_loader.py             # Kemnaker UMK data
│   ├── njop_loader.py            # BPN NJOP data
│   └── world_bank_loader.py      # World Bank API
├── processors/
│   ├── data_validator.py         # Outlier detection
│   ├── benchmark_aggregator.py   # Build P25/P50/P75
│   └── anonymity_checker.py      # k-anonymity
└── orchestrators/
    ├── monthly_data_refresh.py   # Monthly full pipeline
    └── scheduler.py              # Cron-style scheduler
```

---

## Step 3: Base Agent with Swarms

`[CURSOR]` — Create: `agents/base_agent.py`

```python
# agents/base_agent.py
from swarms import Agent
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Supabase client (shared across all agents)
def get_supabase() -> Client:
    return create_client(
        os.environ['SUPABASE_URL'],
        os.environ['SUPABASE_SERVICE_ROLE_KEY']
    )

class CekwajarBaseAgent(Agent):
    """Base class for all cekwajar.id agents"""
    
    def __init__(self, name: str, description: str, **kwargs):
        super().__init__(
            agent_name=name,
            system_prompt=f"""You are {name} for cekwajar.id — an Indonesian data intelligence platform.
            
Your role: {description}

Rules:
1. Only process publicly available data
2. Never bypass authentication or CAPTCHAs
3. Rate limit all HTTP requests (minimum 3-5 seconds between requests)
4. Log all errors to Supabase agent_logs table
5. Return structured JSON for all outputs
6. Add Indonesian locale context to all data interpretations
            """,
            max_loops=3,
            **kwargs
        )
        self.supabase = get_supabase()
    
    def log_run(self, agent_name: str, status: str, records_processed: int, error: str = None):
        """Log agent run to Supabase for monitoring"""
        try:
            self.supabase.table('agent_run_logs').insert({
                'agent_name': agent_name,
                'status': status,
                'records_processed': records_processed,
                'error_message': error,
                'run_at': 'now()',
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log agent run: {e}")
```

---

## Step 4: Monthly Data Refresh Orchestrator

`[CURSOR]` — Create: `agents/orchestrators/monthly_data_refresh.py`

```python
# agents/orchestrators/monthly_data_refresh.py
"""
Main monthly pipeline — runs on 1st of each month.
Orchestrates all scrapers and loaders in sequence.
Can run via: python -m agents.orchestrators.monthly_data_refresh
Or schedule via Supabase pg_cron / Fly.io cron.
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.scrapers.property_scraper import run_property_scrapers
from agents.scrapers.salary_scraper import run_jobstreet_scraper
from agents.scrapers.numbeo_scraper import run_numbeo_scraper
from agents.processors.data_validator import run_validation
from agents.processors.benchmark_aggregator import run_aggregation
from agents.base_agent import get_supabase

supabase = get_supabase()


async def run_monthly_pipeline():
    """Full monthly data refresh pipeline"""
    start_time = datetime.now()
    log_id = None
    
    # Log pipeline start
    result = supabase.table('pipeline_runs').insert({
        'pipeline_name': 'monthly_full_refresh',
        'status': 'running',
        'started_at': start_time.isoformat(),
    }).execute()
    log_id = result.data[0]['id']
    
    steps_completed = []
    errors = []
    
    # Step 1: Property data (most critical for Wajar Tanah)
    print("=" * 50)
    print("STEP 1: Property Scraping (99.co + Rumah123)")
    print("=" * 50)
    try:
        listings_count = await run_property_scrapers()
        steps_completed.append(f"Property: {listings_count} listings")
        print(f"✅ Property scraping done: {listings_count} listings")
    except Exception as e:
        errors.append(f"Property scraping failed: {e}")
        print(f"❌ Property scraping error: {e}")
    
    # Step 2: Salary data (Wajar Gaji)
    print("\nSTEP 2: Salary Scraping (JobStreet)")
    try:
        salary_count = await run_jobstreet_scraper()
        steps_completed.append(f"Salaries: {salary_count} data points")
        print(f"✅ Salary scraping done: {salary_count} points")
    except Exception as e:
        errors.append(f"Salary scraping failed: {e}")
        print(f"❌ Salary scraping error: {e}")
    
    # Step 3: Cost of living data (Wajar Hidup + Wajar Kabur)
    print("\nSTEP 3: Numbeo Cost of Living Scraping")
    try:
        col_count = await run_numbeo_scraper()
        steps_completed.append(f"CoL: {col_count} cities")
        print(f"✅ Numbeo done: {col_count} cities")
    except Exception as e:
        errors.append(f"Numbeo failed: {e}")
        print(f"❌ Numbeo error: {e}")
    
    # Step 4: Validate and flag outliers
    print("\nSTEP 4: Data Validation")
    try:
        outliers_flagged = run_validation()
        steps_completed.append(f"Validation: {outliers_flagged} outliers flagged")
        print(f"✅ Validation done: {outliers_flagged} outliers flagged")
    except Exception as e:
        errors.append(f"Validation failed: {e}")
    
    # Step 5: Aggregate benchmarks
    print("\nSTEP 5: Benchmark Aggregation")
    try:
        benchmarks_updated = run_aggregation()
        steps_completed.append(f"Benchmarks: {benchmarks_updated} updated")
        print(f"✅ Aggregation done: {benchmarks_updated} benchmarks")
    except Exception as e:
        errors.append(f"Aggregation failed: {e}")
    
    # Update pipeline log
    end_time = datetime.now()
    duration_minutes = (end_time - start_time).seconds / 60
    
    supabase.table('pipeline_runs').update({
        'status': 'completed' if not errors else 'completed_with_errors',
        'completed_at': end_time.isoformat(),
        'duration_minutes': round(duration_minutes, 1),
        'steps_completed': steps_completed,
        'errors': errors,
    }).eq('id', log_id).execute()
    
    print(f"\n{'=' * 50}")
    print(f"Pipeline completed in {duration_minutes:.1f} minutes")
    print(f"Steps: {len(steps_completed)} completed, {len(errors)} errors")
    print("=" * 50)


if __name__ == '__main__':
    asyncio.run(run_monthly_pipeline())
```

---

## Step 5: Data Validator Agent

`[CURSOR]` — Create: `agents/processors/data_validator.py`

```python
# agents/processors/data_validator.py
from agents.base_agent import get_supabase
import numpy as np

supabase = get_supabase()

def run_validation() -> int:
    """Flag outliers in property and salary data using IQR method"""
    flagged_total = 0
    
    # Property listings: flag price_per_m2 outliers
    flagged_total += _flag_property_outliers()
    
    # Salary submissions: flag salary outliers per job+city+experience
    flagged_total += _flag_salary_outliers()
    
    return flagged_total


def _flag_property_outliers() -> int:
    """Use IQR × 1.5 rule to flag outlier property prices"""
    # Get all recent unflagged listings
    result = supabase.table('property_listings').select(
        'id, city, property_type, price_per_m2'
    ).eq('is_outlier', False).gt('price_per_m2', 0).execute()
    
    listings = result.data
    if not listings:
        return 0
    
    flagged_count = 0
    
    # Group by city + property_type
    from collections import defaultdict
    groups = defaultdict(list)
    for listing in listings:
        key = f"{listing['city']}_{listing['property_type']}"
        groups[key].append(listing)
    
    for group_key, group_listings in groups.items():
        if len(group_listings) < 5:
            continue  # Not enough data to detect outliers
        
        prices = [l['price_per_m2'] for l in group_listings]
        q1 = np.percentile(prices, 25)
        q3 = np.percentile(prices, 75)
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        
        for listing in group_listings:
            if listing['price_per_m2'] < lower_fence or listing['price_per_m2'] > upper_fence:
                supabase.table('property_listings').update(
                    {'is_outlier': True}
                ).eq('id', listing['id']).execute()
                flagged_count += 1
    
    return flagged_count


def _flag_salary_outliers() -> int:
    """Flag salary submissions that are >3x or <0.3x city UMK"""
    result = supabase.table('salary_submissions').select(
        'id, city, monthly_gross_salary'
    ).eq('is_validated', True).execute()
    
    submissions = result.data
    if not submissions:
        return 0
    
    # Get UMK floors
    umk_result = supabase.table('salary_floors').select('city, umk_2024').execute()
    umk_map = {r['city']: r['umk_2024'] for r in umk_result.data}
    
    flagged_count = 0
    for sub in submissions:
        city = sub['city']
        salary = sub['monthly_gross_salary']
        umk = umk_map.get(city, 2_500_000)  # Default if not found
        
        # Flag extreme outliers: >30x UMK or <0.7x UMK
        if salary > umk * 30 or salary < umk * 0.7:
            supabase.table('salary_submissions').update(
                {'is_validated': False}
            ).eq('id', sub['id']).execute()
            flagged_count += 1
    
    return flagged_count
```

---

## Step 6: Benchmark Aggregator

`[CURSOR]` — Create: `agents/processors/benchmark_aggregator.py`

```python
# agents/processors/benchmark_aggregator.py
from agents.base_agent import get_supabase
import numpy as np
from collections import defaultdict

supabase = get_supabase()

def run_aggregation() -> int:
    """Build P25/P50/P75 benchmarks from validated raw data"""
    updated = 0
    updated += _aggregate_property_benchmarks()
    updated += _aggregate_salary_benchmarks()
    return updated


def _aggregate_property_benchmarks() -> int:
    """Build property price benchmarks by city + type"""
    result = supabase.table('property_listings').select(
        'city, property_type, price_per_m2'
    ).eq('is_outlier', False).gt('price_per_m2', 0).execute()
    
    listings = result.data
    if not listings:
        return 0
    
    groups = defaultdict(list)
    for l in listings:
        key = (l['city'], l['property_type'])
        groups[key].append(l['price_per_m2'])
    
    updated = 0
    for (city, prop_type), prices in groups.items():
        if len(prices) < 3:
            continue
        
        benchmark = {
            'city': city,
            'property_type': prop_type,
            'p25_price_per_m2': float(np.percentile(prices, 25)),
            'p50_price_per_m2': float(np.percentile(prices, 50)),
            'p75_price_per_m2': float(np.percentile(prices, 75)),
            'sample_count': len(prices),
            'last_updated': 'now()',
        }
        
        supabase.table('property_benchmarks').upsert(benchmark).execute()
        updated += 1
    
    return updated


def _aggregate_salary_benchmarks() -> int:
    """Build salary benchmarks from crowdsource data (k-anonymity: min 10)"""
    result = supabase.table('salary_submissions').select('*').eq('is_validated', True).execute()
    submissions = result.data
    
    groups = defaultdict(list)
    for s in submissions:
        key = (s.get('city'), s.get('job_title'), s.get('industry'))
        groups[key].append(s['monthly_gross_salary'])
    
    updated = 0
    for (city, job_title, industry), salaries in groups.items():
        if len(salaries) < 10:  # k-anonymity threshold
            continue
        
        benchmark = {
            'city': city or 'Unknown',
            'province': 'Unknown',
            'job_title': job_title,
            'industry': industry,
            'p25_salary': float(np.percentile(salaries, 25)),
            'p50_salary': float(np.percentile(salaries, 50)),
            'p75_salary': float(np.percentile(salaries, 75)),
            'sample_count': len(salaries),
            'data_source': 'crowdsource',
            'confidence_level': 'high' if len(salaries) >= 50 else 'medium',
            'year': 2024,
        }
        
        supabase.table('salary_benchmarks').upsert(benchmark).execute()
        updated += 1
    
    return updated
```

---

## Step 7: Scheduler Setup

`[MANUAL]` — Two options for running agents:

### Option A: Local machine (for development)

```python
# agents/orchestrators/scheduler.py
import schedule
import time
import asyncio
from monthly_data_refresh import run_monthly_pipeline

# Run monthly on the 1st
schedule.every().month.at("02:00").do(lambda: asyncio.run(run_monthly_pipeline()))

# Run monitoring daily
schedule.every().day.at("09:00").do(run_daily_monitoring)

print("Scheduler running... Press Ctrl+C to stop")
while True:
    schedule.run_pending()
    time.sleep(60)
```

### Option B: Supabase pg_cron (no server needed — FREE)

`[SUPABASE]` — SQL Editor:

```sql
-- Call a Supabase Edge Function that triggers the Python pipeline
-- First create the Edge Function in Supabase dashboard
SELECT cron.schedule(
  'monthly-data-refresh',
  '0 2 1 * *',  -- 1st of month at 2am WIB
  $$
  SELECT net.http_post(
    url := 'https://your-project.supabase.co/functions/v1/trigger-pipeline',
    headers := '{"Authorization": "Bearer ' || current_setting('app.service_role_key') || '"}'::jsonb,
    body := '{"pipeline": "monthly_refresh"}'::jsonb
  );
  $$
);
```

### Option C: Fly.io free tier (recommended for production)

`[MANUAL]` — Deploy Python agents to Fly.io:

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Create Fly app (free tier: 256MB RAM, shared CPU)
fly launch --name cekwajar-agents --region sin  # Singapore region

# Create fly.toml
cat > fly.toml << EOF
app = "cekwajar-agents"
primary_region = "sin"

[build]
  dockerfile = "Dockerfile.agents"

[processes]
  scheduler = "python agents/orchestrators/scheduler.py"

[mounts]
  source = "agent_data"
  destination = "/app/data"
EOF

# Dockerfile for agents
cat > Dockerfile.agents << EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.agents.txt .
RUN pip install -r requirements.agents.txt
RUN playwright install chromium --with-deps
COPY agents/ ./agents/
CMD ["python", "agents/orchestrators/scheduler.py"]
EOF

fly deploy
```

---

## Step 8: Supabase Monitoring Schema

`[SUPABASE]`:

```sql
CREATE TABLE public.agent_run_logs (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  agent_name TEXT NOT NULL,
  status TEXT CHECK (status IN ('running', 'completed', 'failed')),
  records_processed INTEGER DEFAULT 0,
  error_message TEXT,
  run_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.pipeline_runs (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  pipeline_name TEXT NOT NULL,
  status TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  duration_minutes NUMERIC(8,2),
  steps_completed TEXT[],
  errors TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Only admins can see agent logs (you as service_role)
ALTER TABLE public.agent_run_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pipeline_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "No public access" ON public.agent_run_logs FOR SELECT USING (false);
CREATE POLICY "No public access" ON public.pipeline_runs FOR SELECT USING (false);
```

---

## LLM Backend for Agents (Free Options)

Swarms agents need an LLM backend for reasoning tasks. For pure data processing (scraping, loading, aggregating), you don't need an LLM. But for tasks like "analyze this data and flag anomalies" or "generate TikTok content drafts," you need one.

| Option | Free Tier | Speed | Use Case |
|--------|-----------|-------|----------|
| Groq API | 30 req/min, 14,400 tokens/min | Fast | Content generation, analysis |
| Ollama (local) | Unlimited | Slow (depends on GPU) | Any agent task, offline |
| Google Gemini API | 15 req/min, 1M tokens/day | Fast | Data analysis agents |
| Anthropic Claude via Claude.ai | Your subscription | Fast | One-off analysis |

**Setup for Groq (recommended — fastest free tier):**

```python
# agents/config.py
import os

def get_llm():
    """Get free LLM for agent reasoning tasks"""
    from swarms import LiteLLM
    
    return LiteLLM(
        model_name="groq/llama3-8b-8192",  # Or groq/mixtral-8x7b-32768
        api_key=os.environ.get('GROQ_API_KEY'),
    )
```

**For data processing agents (no LLM needed):**
Most of the scraping, loading, and aggregation logic above is pure Python — no LLM calls. Reserve LLM calls for: content generation, anomaly interpretation, user query analysis.

---

## Reality Check for Agents

| Issue | Reality | Fix |
|-------|---------|-----|
| Playwright on Fly.io free tier runs OOM (256MB) | Yes, headless Chrome needs ~300-500MB | Use Fly.io $3/month plan with 512MB, or use requests+BeautifulSoup for simpler pages |
| Scrapers fail when site structure changes | Happens 2-4x/year | Check `records_processed` in pipeline logs. If 0: re-inspect selectors |
| Monthly scrape window: some sites detect VPS IPs | True — many sites block Fly.io/AWS IPs | Use residential proxies (FreeProxyList.net for low-scale), or run scraper from local machine monthly |
| Swarms framework overhead | Library adds ~200MB dependencies | Alternative: just use plain Python + asyncio for scrapers (no LLM needed for most data tasks) |

**Simplification option:** For MVP (Month 1–3), you DON'T need Swarms framework. Just run plain Python scripts as scheduled jobs. Use Swarms only if you want LLM-assisted tasks like content generation or anomaly detection.
