# /preflight — Run Mandatory Pre-Flight Checks
## Phase 0: Pre-Flight
cd /home/newadmin/swarm-bot
python --version
node --version
pnpm --version
git status --short
python3 -c "
import os, sys
required = ['MINIMAX_API_KEY','LITELLM_API_BASE','TELEGRAM_BOT_TOKEN','SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY','FIRECRAWL_API_KEY','EXA_API_KEY']
missing = [k for k in required if not os.getenv(k)]
if missing: print('MISSING:', missing); sys.exit(1)
else: print('All env vars present ✓')
"
mkdir -p .opencode/health
echo "Session started: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .opencode/health/session.log
echo "Pre-flight complete."