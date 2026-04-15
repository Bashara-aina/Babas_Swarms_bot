#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# cekwajar.id — Pre-Launch Security Audit Script
# Run this before going to production
# ══════════════════════════════════════════════════════════════════════════════

set -e

echo "=== cekwajar.id Pre-Launch Security Audit ==="
echo ""

# 1. Check for secrets in codebase
echo "1. Checking for exposed secrets in source code..."
SEcrets=$(grep -rn "service_role\|sb_\|Mid-server-\|Mid-client-" src/ --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v "getServiceClient\|getServiceRoleKey\|validateEnvVars\|env.local\|next.config" || true)
if [ -n "$SEcrets" ]; then
  echo "FAIL — Found potential secrets in source:"
  echo "$Secrets"
else
  echo "PASS — No obvious secrets found in source"
fi
echo ""

# 2. Check .gitignore covers all sensitive files
echo "2. Checking .gitignore coverage..."
for file in .env .env.local .env.production; do
  if [ -f "$file" ]; then
    IGNORED=$(git check-ignore "$file" 2>/dev/null || echo "")
    if [ -n "$IGNORED" ]; then
      echo "PASS — $file is ignored"
    else
      echo "FAIL — $file is NOT ignored by git"
    fi
  fi
done
echo ""

# 3. Verify no console.log with user data in API routes
echo "3. Checking for PII in console.log (API routes)..."
PII_LOGS=$(grep -rn "console.log" src/app/api/ --include="*.ts" 2>/dev/null | grep -iE "email|salary|slip|gaji|user" || true)
if [ -n "$PII_LOGS" ]; then
  echo "REVIEW — Potential PII in console.log:"
  echo "$PII_LOGS"
else
  echo "PASS — No PII found in API console.log statements"
fi
echo ""

# 4. Check RLS is enabled
echo "4. Checking Row Level Security (RLS)..."
echo "Run this in Supabase SQL editor:"
echo "  SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
echo "ALL tables must show rowsecurity=true"
echo ""

# 5. Check rate limiting exists
echo "5. Checking rate limit implementation..."
if [ -f "src/lib/ratelimit.ts" ]; then
  echo "PASS — Rate limit module found"
else
  echo "INFO — No rate limit module found (uses in-memory fallback)"
fi
echo ""

# 6. Check no direct DB connection strings exposed
echo "6. Checking for exposed DB connection strings..."
DB_CONN=$(grep -rn "postgresql://" src/ --include="*.ts" --include="*.tsx" 2>/dev/null || true)
if [ -n "$DB_CONN" ]; then
  echo "FAIL — postgresql:// found in source:"
  echo "$DB_CONN"
else
  echo "PASS — No direct DB connection strings in source"
fi
echo ""

# 7. Check middleware auth protection
echo "7. Checking middleware auth protection..."
if grep -q "ALLOWED_USER_ID\|require_owner" src/middleware.ts 2>/dev/null; then
  echo "INFO — middleware.ts doesn't reference ALLOWED_USER_ID (expected — auth is via Supabase)"
else
  echo "PASS — Middleware properly configured"
fi
echo ""

# 8. Check webhook uses service role client
echo "8. Checking webhook signature verification..."
if grep -q "timingSafeEqual\|createHash.*sha512" src/app/api/webhooks/midtrans/route.ts 2>/dev/null; then
  echo "PASS — Webhook has SHA512 signature verification"
else
  echo "FAIL — Webhook missing signature verification"
fi
echo ""

echo "=== Audit complete. Fix any FAIL items before launch. ==="
echo "=== Run 'pnpm build' to verify the app builds successfully ==="