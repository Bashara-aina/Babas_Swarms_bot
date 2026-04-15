# Stage 1 — Environment, MCP & Claude Code Setup
**cekwajar.id Vibe Coding Playbook**  
**Estimated time:** 2–3 hours  
**Goal:** Fully configured local dev environment, Claude Code ready, all external accounts created, project skeleton on Vercel.

---

## What You're Building in This Stage

A working Next.js 15 project that:
- Lives on GitHub
- Auto-deploys to Vercel on every push to `main`
- Connected to a Supabase project in Singapore region
- Has Claude Code configured with all MCP servers
- Has all API keys stored in Vercel + `.env.local`
- Passes a smoke test: homepage loads, Supabase ping works

This stage is **100% setup** — no product features yet. Do not skip steps.

---

## Part 1: Accounts & API Keys to Prepare

Create these accounts BEFORE opening Claude Code. Have all keys ready.

### 1.1 Required Accounts (Free Tier)

| Service | URL | Plan | Purpose |
|---------|-----|------|---------|
| GitHub | github.com | Free | Source control |
| Vercel | vercel.com | Hobby (free) | Hosting + Edge functions |
| Supabase | supabase.com | Free (500MB) | Database + Auth + Storage |
| Google Cloud | console.cloud.google.com | Free ($300 credit) | Vision API for OCR |
| Midtrans | dashboard.midtrans.com | Sandbox (free) | Payment gateway |
| Sentry | sentry.io | Developer (free) | Error monitoring |
| Uptime Robot | uptimerobot.com | Free | Uptime monitoring |

### 1.2 Optional Accounts (Add Week 3+)

| Service | URL | Purpose |
|---------|-----|---------|
| Resend | resend.com | Transactional email (3,000/month free) |
| Telegram | t.me/BotFather | Alert bot |
| TikTok Creator | tiktok.com | GTM content |

---

## Part 2: Keys to Collect

After creating accounts, collect these keys. You'll need them all before running Claude Code.

### Supabase Keys
Go to: Project → Settings → API

```
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...    ← NEVER public
SUPABASE_DB_URL=postgresql://postgres:[password]@db.xxxx.supabase.co:5432/postgres
```

**Critical:** Create Supabase project in **ap-southeast-1 (Singapore)** region. This is the closest to Indonesian users and affects latency significantly.

### Google Vision API Key
1. Go to: console.cloud.google.com
2. Create project: "cekwajar-ocr"
3. Enable: Cloud Vision API
4. Create credentials: API Key
5. Restrict key to: Cloud Vision API only

```
GOOGLE_VISION_API_KEY=AIzaSy...
```

### Midtrans Keys
1. Login to dashboard.midtrans.com
2. Settings → Access Keys (use Sandbox first)

```
MIDTRANS_SERVER_KEY=SB-Mid-server-...
MIDTRANS_CLIENT_KEY=SB-Mid-client-...
NEXT_PUBLIC_MIDTRANS_CLIENT_KEY=SB-Mid-client-...
MIDTRANS_IS_PRODUCTION=false
```

### Sentry DSN
1. sentry.io → New Project → Next.js
2. Copy the DSN

```
NEXT_PUBLIC_SENTRY_DSN=https://xxx@oyyy.ingest.sentry.io/zzzz
```

---

## Part 3: Local Machine Setup

Run these commands on your Mac/Windows/Linux before starting Claude Code.

### 3.1 Install Prerequisites

```bash
# Node.js 20+ (use nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20
node --version  # should show v20.x.x

# pnpm (faster than npm)
npm install -g pnpm
pnpm --version

# Supabase CLI
npm install -g supabase
supabase --version

# Python 3.11+ (for AI agents later)
python3 --version  # should be 3.11+

# Git
git --version

# Claude Code CLI
npm install -g @anthropic-ai/claude-code
claude --version
```

### 3.2 Verify GitHub SSH

```bash
ssh -T git@github.com
# Should show: Hi [username]! You've successfully authenticated
```

If not set up: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

---

## Part 4: MCP Servers to Configure in Claude Code

Claude Code uses MCP (Model Context Protocol) servers to access external tools. Configure these before your first coding session.

### 4.1 Open Claude Code Config

```bash
# Open Claude Code config file
claude config --global  # or find it at ~/.claude/claude.json
```

### 4.2 Required MCP Servers

**MCP 1: Supabase MCP**
Allows Claude Code to directly query and manage your Supabase database.

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "@supabase/mcp-server-supabase@latest", "--access-token", "YOUR_SUPABASE_ACCESS_TOKEN"],
      "env": {}
    }
  }
}
```

Get your Supabase access token: supabase.com → Account → Access Tokens → Generate new token

**MCP 2: Vercel MCP**
Allows Claude Code to check deployment status and logs.

```json
"vercel": {
  "command": "npx",
  "args": ["-y", "@vercel/mcp-adapter@latest"],
  "env": {
    "VERCEL_TOKEN": "YOUR_VERCEL_TOKEN"
  }
}
```

Get Vercel token: vercel.com → Settings → Tokens → Create

**MCP 3: GitHub MCP**
Allows Claude Code to read files, create PRs, check CI.

```json
"github": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_GITHUB_PAT"
  }
}
```

Get GitHub PAT: github.com → Settings → Developer settings → Personal access tokens → Classic → Generate with `repo` scope

**MCP 4: File System MCP (built-in)**
Claude Code has this by default. Make sure it's not restricted.

**Full `claude.json` config:**

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "@supabase/mcp-server-supabase@latest", "--access-token", "sbp_xxxxxxxxxxxx"],
      "env": {}
    },
    "vercel": {
      "command": "npx",
      "args": ["-y", "@vercel/mcp-adapter@latest"],
      "env": {
        "VERCEL_TOKEN": "xxxxxxxxxxxxxxxx"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "github_pat_xxxxxxxxxxxx"
      }
    }
  },
  "permissions": {
    "allow": ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
  }
}
```

---

## Part 5: Project Initialization

Do this manually (not through Claude Code) to establish the base.

### 5.1 Create GitHub Repository

```bash
# On GitHub: New Repository
# Name: cekwajar-id
# Private: Yes (initially)
# Add .gitignore: Node
# Don't add README (Claude Code will do this)
```

### 5.2 Create Project Locally

```bash
# Clone empty repo
git clone git@github.com:YOUR_USERNAME/cekwajar-id.git
cd cekwajar-id

# Initialize Next.js 15 App Router project
npx create-next-app@latest . \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --use-pnpm \
  --no-turbopack
```

### 5.3 Install Base Dependencies

```bash
# Supabase client
pnpm add @supabase/supabase-js @supabase/ssr

# UI components
pnpm add @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-select
pnpm add @radix-ui/react-toast @radix-ui/react-tabs @radix-ui/react-progress
pnpm add lucide-react class-variance-authority clsx tailwind-merge

# shadcn/ui CLI
pnpm add -D @shadcn/ui
npx shadcn@latest init
# Choose: Default style, slate color, CSS variables

# Forms
pnpm add react-hook-form @hookform/resolvers zod

# Data fetching
pnpm add @tanstack/react-query

# Date utilities
pnpm add date-fns

# Error monitoring
pnpm add @sentry/nextjs

# Payment
pnpm add @midtrans/snap

# Type utilities
pnpm add -D @types/node
```

### 5.4 Install shadcn Components

```bash
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add label
npx shadcn@latest add select
npx shadcn@latest add card
npx shadcn@latest add dialog
npx shadcn@latest add toast
npx shadcn@latest add badge
npx shadcn@latest add tabs
npx shadcn@latest add progress
npx shadcn@latest add separator
npx shadcn@latest add sheet
npx shadcn@latest add skeleton
npx shadcn@latest add alert
npx shadcn@latest add form
```

### 5.5 Initialize Supabase CLI

```bash
# Initialize Supabase locally
supabase init

# Link to your remote project
supabase link --project-ref YOUR_PROJECT_REF
# Get project ref from: supabase.com → Project Settings → General → Reference ID

# Start local Supabase (for dev)
supabase start
# Note the local URLs it prints
```

### 5.6 Create `.env.local`

```bash
cat > .env.local << 'EOF'
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://uqgiarbjjuxmrvgfyyuj.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_Gn6pCNy6vycXzd_8vnpqcA_i-c5MyIg
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_DB_URL=postgresql://...

# Google Vision
GOOGLE_VISION_API_KEY=AIzaSy...

# Midtrans (Sandbox)
MIDTRANS_SERVER_KEY=SB-Mid-server-...
NEXT_PUBLIC_MIDTRANS_CLIENT_KEY=SB-Mid-client-...
MIDTRANS_IS_PRODUCTION=false

# Sentry
NEXT_PUBLIC_SENTRY_DSN=https://...

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
EOF
```

### 5.7 Update `.gitignore`

```bash
cat >> .gitignore << 'EOF'

# Environment
.env
.env.local
.env.*.local

# Supabase
supabase/.branches
supabase/.temp

# Python
__pycache__/
*.pyc
agents/.env
agents/service_account.json
venv/
.venv/

# Editor
.cursor/
EOF
```

### 5.8 Connect to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Link project to Vercel
vercel link
# Follow prompts: link to your account, create new project "cekwajar-id"

# Push env vars to Vercel
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add SUPABASE_SERVICE_ROLE_KEY production
vercel env add MIDTRANS_SERVER_KEY production
vercel env add GOOGLE_VISION_API_KEY production
vercel env add NEXT_PUBLIC_MIDTRANS_CLIENT_KEY production
vercel env add NEXT_PUBLIC_SENTRY_DSN production
vercel env add NEXT_PUBLIC_APP_URL production
# Value for last one: https://cekwajar.id (or your vercel URL initially)

# First deploy
git add .
git commit -m "init: Next.js 15 scaffold"
git push origin main
# Vercel auto-deploys. Check vercel.com dashboard.
```

---

## Part 6: Open Claude Code

Now open Claude Code in the project folder:

```bash
# From your project root
cd cekwajar-id
claude
```

Verify MCP servers are connected:
```
/mcp
```
You should see: supabase ✓, vercel ✓, github ✓

---

## ═══════════════════════════════════════════════
## MASTER PROMPT — SEND THIS TO CLAUDE CODE
## (Stage 1 — Project Scaffold)
## ═══════════════════════════════════════════════

Copy everything between the `===START===` and `===END===` markers and paste into Claude Code.

```
===START===
You are building cekwajar.id — an Indonesian consumer data intelligence platform. 
This is a Next.js 15 App Router project using TypeScript, Tailwind CSS, and shadcn/ui.
Backend: Supabase (PostgreSQL + Auth + Storage). Hosting: Vercel. Payment: Midtrans.

The project has 5 tools:
1. Wajar Slip — payslip auditor (checks PPh21 + BPJS compliance)
2. Wajar Gaji — salary benchmark
3. Wajar Tanah — property price checker
4. Wajar Kabur — abroad salary comparison (PPP-adjusted)
5. Wajar Hidup — cost of living comparison between Indonesian cities

TARGET USERS: Indonesian salaried employees. Mobile-first (375px priority). 
Language: Bahasa Indonesia for all UI text.

YOUR TASK FOR STAGE 1:
Build the complete project scaffold — layout, navigation, placeholder pages for all 5 tools, 
Supabase client configuration, and environment validation.

════════════════════════════════════════════════════
DIRECTORY STRUCTURE TO CREATE:
════════════════════════════════════════════════════

src/
  app/
    layout.tsx                    ← Root layout with GlobalNav + Footer
    page.tsx                      ← Homepage (hero + 5 tool cards)
    wajar-slip/
      page.tsx                    ← Stub (placeholder)
    wajar-gaji/
      page.tsx                    ← Stub (placeholder)
    wajar-tanah/
      page.tsx                    ← Stub (placeholder)
    wajar-kabur/
      page.tsx                    ← Stub (placeholder)
    wajar-hidup/
      page.tsx                    ← Stub (placeholder)
    auth/
      callback/
        route.ts                  ← Supabase auth callback
    api/
      health/
        route.ts                  ← Health check endpoint
  components/
    layout/
      GlobalNav.tsx               ← Sticky nav bar
      Footer.tsx
      CookieConsent.tsx           ← Placeholder (implement later)
    shared/
      PremiumGate.tsx             ← Blur overlay + upgrade CTA
      DisclaimerBanner.tsx        ← Warning banners for tools
      ErrorCard.tsx               ← Error state component
      LoadingSpinner.tsx
  lib/
    supabase/
      client.ts                   ← Browser client
      server.ts                   ← Server client (cookies)
      middleware.ts               ← Session refresh
    utils.ts                      ← cn() utility + formatIDR()
    constants.ts                  ← Tool names, routes, feature flags
  types/
    index.ts                      ← Shared TypeScript types

════════════════════════════════════════════════════
EXACT IMPLEMENTATION REQUIREMENTS:
════════════════════════════════════════════════════

1. SUPABASE CLIENT (src/lib/supabase/client.ts):
Use @supabase/ssr package. Two clients:
- Browser client: createBrowserClient(url, anonKey)
- Server client: createServerClient(url, anonKey, { cookies }) — reads from Next.js cookies()

2. MIDDLEWARE (src/middleware.ts):
Use Supabase SSR middleware to refresh sessions on every request.
Protect NO routes yet — all pages public.

3. GLOBAL NAV (src/components/layout/GlobalNav.tsx):
- Sticky (top-0 z-50)
- Logo: "cekwajar.id" in bold, links to "/"
- 5 nav links: Wajar Slip, Wajar Gaji, Wajar Tanah, Wajar Kabur, Wajar Hidup
- Mobile: hamburger menu using Sheet component from shadcn
- Right side: Login button (links to /auth/login for now, implement auth in Stage 3)
- Active link: highlighted (use usePathname)
- Height: 56px mobile, 64px desktop
- Background: white with shadow on scroll

4. HOMEPAGE (src/app/page.tsx):
Hero section:
  - H1: "Audit Slip Gaji, Benchmark Gaji & Harga Properti — Gratis"
  - Subtext: "5 alat gratis untuk karyawan Indonesia. Tidak perlu login."
  - Two CTAs: [Cek Slip Gaji Gratis] → /wajar-slip, [Lihat Semua Alat ↓] → scroll

5 Tool cards below hero (in a grid: 1 col mobile, 2-3 col desktop):
Each card has: icon, name, tagline, "Mulai Gratis →" button

Tool data:
  { name: "Wajar Slip", icon: "📋", tag: "Audit PPh21 & BPJS dalam 30 detik", href: "/wajar-slip" }
  { name: "Wajar Gaji", icon: "💰", tag: "Benchmark gaji 12.000+ karyawan", href: "/wajar-gaji" }
  { name: "Wajar Tanah", icon: "🏠", tag: "Cek harga properti vs pasar", href: "/wajar-tanah" }
  { name: "Wajar Kabur", icon: "✈️", tag: "Kerja di LN — daya beli riil", href: "/wajar-kabur" }
  { name: "Wajar Hidup", icon: "🏙️", tag: "Gaji setara pindah kota?", href: "/wajar-hidup" }

5. EACH TOOL STUB PAGE:
Each tool page at /wajar-[name]/page.tsx should show:
- Tool name as H1
- Coming soon text (Bahasa Indonesia)
- "Sedang dibangun — Stage [2-5] dari 10"
- Link back to homepage

6. FORMAT UTILITIES (src/lib/utils.ts):
// cn() for Tailwind class merging (using clsx + tailwind-merge)
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }

// Format IDR currency
export function formatIDR(amount: number, compact = false): string {
  if (compact && amount >= 1_000_000) {
    return `Rp ${(amount / 1_000_000).toFixed(1)}M`
  }
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

7. CONSTANTS (src/lib/constants.ts):
export const TOOLS = [
  { id: 'wajar-slip', name: 'Wajar Slip', href: '/wajar-slip', emoji: '📋' },
  { id: 'wajar-gaji', name: 'Wajar Gaji', href: '/wajar-gaji', emoji: '💰' },
  { id: 'wajar-tanah', name: 'Wajar Tanah', href: '/wajar-tanah', emoji: '🏠' },
  { id: 'wajar-kabur', name: 'Wajar Kabur', href: '/wajar-kabur', emoji: '✈️' },
  { id: 'wajar-hidup', name: 'Wajar Hidup', href: '/wajar-hidup', emoji: '🏙️' },
]

export const SUBSCRIPTION_TIERS = {
  free: { name: 'Gratis', price: 0 },
  basic: { name: 'Basic', price: 29000 },
  pro: { name: 'Pro', price: 79000 },
}

export const FREE_TOOLS_LIMIT = {
  auditPerDay: 3,           // anonymous: 3 audits/day
  historyMonths: 0,         // free: no history
}

8. HEALTH CHECK (src/app/api/health/route.ts):
GET endpoint that:
- Pings Supabase (SELECT 1 FROM user_profiles LIMIT 1)
- Returns JSON: { status: 'ok', supabase: 'connected', timestamp: ISO }
- Returns 500 if Supabase unreachable

9. ROOT LAYOUT (src/app/layout.tsx):
- Import GlobalNav and Footer
- Set <html lang="id"> (Indonesian)
- Set metadata: { title: 'cekwajar.id', description: 'Audit slip gaji, benchmark gaji & harga properti Indonesia' }
- Import global CSS

10. TYPESCRIPT TYPES (src/types/index.ts):
Define these types:
  type SubscriptionTier = 'free' | 'basic' | 'pro'
  type PtkpStatus = 'TK/0' | 'TK/1' | 'TK/2' | 'TK/3' | 'K/0' | 'K/1' | 'K/2' | 'K/3' | 'K/I/0' | 'K/I/1' | 'K/I/2' | 'K/I/3'
  type PropertyType = 'RUMAH' | 'TANAH' | 'APARTEMEN' | 'RUKO'
  type PropertyVerdict = 'MURAH' | 'WAJAR' | 'MAHAL' | 'SANGAT_MAHAL'
  type ViolationCode = 'V01' | 'V02' | 'V03' | 'V04' | 'V05' | 'V06' | 'V07'
  type ViolationSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  interface Violation { code: ViolationCode; severity: ViolationSeverity; titleID: string; descriptionID: string; differenceIDR: number | null; actionID: string }
  interface UserProfile { id: string; email: string; full_name?: string; subscription_tier: SubscriptionTier; created_at: string }

════════════════════════════════════════════════════
NEXT.JS CONFIG:
════════════════════════════════════════════════════
Update next.config.ts to add:
- images: { domains: ['lh3.googleusercontent.com', 'xxxx.supabase.co'] }
- experimental: { serverActions: { allowedOrigins: ['localhost:3000', 'cekwajar.id'] } }

════════════════════════════════════════════════════
VERIFICATION:
════════════════════════════════════════════════════
After building, run:
  pnpm dev
  
Test:
1. Homepage loads at localhost:3000
2. All 5 tool links in nav work
3. Each tool page shows its stub
4. GET localhost:3000/api/health returns { status: 'ok' }
5. No TypeScript errors: pnpm tsc --noEmit
6. No ESLint errors: pnpm lint

Fix any errors before completing this stage.
===END===
```

---

## Part 7: Verification Checklist

Run these after Claude Code finishes Stage 1:

```bash
# In your project directory:

# 1. TypeScript clean
pnpm tsc --noEmit
# Expected: no errors

# 2. Lint clean
pnpm lint
# Expected: no errors

# 3. Dev server runs
pnpm dev
# Expected: Server starts on localhost:3000

# 4. Health check
curl localhost:3000/api/health
# Expected: {"status":"ok","supabase":"connected","timestamp":"..."}

# 5. All routes accessible
curl -I localhost:3000/wajar-slip
curl -I localhost:3000/wajar-gaji
# Expected: 200 OK for all

# 6. Vercel deploy succeeds
git add . && git commit -m "stage 1: scaffold + nav + tool stubs" && git push
# Check vercel.com dashboard for green deployment
```

---

## Part 8: Python Agent Environment (Prepare Now, Use in Stage 6+)

Create the Python environment now so it's ready when you need the scraper agents.

```bash
# From project root, create agents directory
mkdir -p agents
cd agents

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install swarms playwright playwright-stealth supabase python-dotenv
pip install openpyxl pandas numpy httpx asyncio aiohttp
pip install pytest pytest-asyncio

# Install Playwright browsers
playwright install chromium

# Create agents .env
cat > .env << 'EOF'
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
EOF

# Verify install
python -c "import swarms; print('swarms ok')"
python -c "from playwright.sync_api import sync_playwright; print('playwright ok')"
python -c "from supabase import create_client; print('supabase ok')"

cd ..
```

---

## Stage 1 Completion Criteria

You have successfully completed Stage 1 when:

- [ ] `pnpm dev` runs without errors
- [ ] `pnpm tsc --noEmit` passes
- [ ] `pnpm lint` passes
- [ ] Homepage shows hero + 5 tool cards
- [ ] All 5 tool routes work
- [ ] GlobalNav has hamburger menu on mobile
- [ ] `/api/health` returns 200 + Supabase connected
- [ ] Vercel deployment is green (check vercel.com)
- [ ] `.env.local` has all keys (check nothing is missing)
- [ ] Python agent environment works
- [ ] Claude Code MCP servers connected (run `/mcp` to verify)

**Next:** Stage 2 — Database Schema + All Migrations
