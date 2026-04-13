---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/engineering/085-supabase-rls-patterns.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:02.009331"
}
---

---
source_id: 085
title: "Supabase RLS Production Patterns"
source_type: ENGINEERING
authority: INDUSTRY
url: "https://supabase.com/docs/guides/database/postgres/row-level-security"
last_verified: "2026-04-11"
tags: [supabase, rls, row-level-security, postgresql, multi-tenant, security]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# Supabase RLS Production Patterns

## Why This Matters for cekwajar.id
cekwajar.id stores employee payroll data, PPH 21 calculations, and BPJS contributions — all highly sensitive personal data protected under UU PDP. Without Row Level Security (RLS), any user with the `anon` key could read ALL company payroll data. RLS is the database-enforced access control that makes multi-tenant SaaS safe.

## Core Knowledge

### What is RLS?
Row Level Security (RLS) is a PostgreSQL feature that enforces access policies at the **database level**. Supabase exposes PostgreSQL directly to the browser via PostgREST, making RLS non-negotiable for any table in the `public` schema.

### RLS is NOT optional for cekwajar.id
- Without RLS, `anon` key gives full read/write to ALL rows
- RLS policies add implicit `WHERE` clauses to every query
- Works regardless of client (browser, mobile, direct API)
- Bugs in app code cannot bypass RLS

### Policy Types

| Operation | USING Clause | WITH CHECK Clause |
|-----------|--------------|-------------------|
| SELECT    | Filters visible rows | N/A |
| INSERT    | N/A | Validates new row data |
| UPDATE    | Filters rows to update | Validates new values |
| DELETE    | Filters rows to delete | N/A |

### Auth Helper Functions
- `auth.uid()` — Returns the authenticated user's UUID
- `auth.jwt()` — Returns the JWT claims (use `raw_app_meta_data` for authorization, NOT `raw_user_meta_data` which users can modify)

### Key Performance Patterns

**1. Always wrap auth functions in SELECT:**
```sql
-- SLOW: auth.uid() called for every row
create policy "Users read own" on documents
for select to authenticated
using (auth.uid() = user_id);

-- FAST: cached per statement
create policy "Users read own" on documents
for select to authenticated
using ((select auth.uid()) = user_id);
```

**2. Always index columns used in policies:**
```sql
create index ix_documents_user_id on public.documents using btree (user_id);
```

**3. Always specify role with TO clause:**
```sql
-- Prevents policy evaluation for anon users
create policy "Users read own" on documents
for select to authenticated
using ((select auth.uid()) = user_id);
```

### Multi-Tenant Pattern for Teams
```sql
-- Account memberships table
create table public.accounts_memberships (
  id uuid primary key default gen_random_uuid(),
  account_id uuid not null references public.accounts(id),
  user_id uuid not null references auth.users(id),
  account_role varchar(50) not null,
  created_at timestamptz default now()
);

-- Security definer function for permission checks
create or replace function public.has_role_on_account(
  p_account_id uuid,
  p_role varchar(50) default null
) returns boolean
language sql
security definer
set search_path = ''
as $$
  select exists(
    select 1 from public.accounts_memberships m
    where m.user_id = (select auth.uid())
      and m.account_id = p_account_id
      and (m.account_role = p_role or p_role is null)
  );
$$;

-- Policy using the function
create policy "Account members read documents"
on public.documents
for select to authenticated
using ((select public.has_role_on_account(account_id)));
```

## Exact Formulas / Numbers (if applicable)

### RLS Auto-Enable Trigger
```sql
CREATE OR REPLACE FUNCTION rls_auto_enable()
RETURNS EVENT_TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN
    SELECT * FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
    IF cmd.schema_name = 'public' THEN
      EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity);
    END IF;
  END LOOP;
END;
$$;

DROP EVENT TRIGGER IF EXISTS ensure_rls;
CREATE EVENT TRIGGER ensure_rls
ON ddl_command_end
WHEN TAG IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
EXECUTE FUNCTION rls_auto_enable();
```

## Edge Cases and Common Mistakes

### Silent Failures with NULL
When `auth.uid()` returns null (anonymous users):
```sql
-- This silently fails, returns nothing
using (auth.uid() = user_id)

-- Explicit check prevents confusion
using (auth.uid() IS NOT NULL AND auth.uid() = user_id)
```

### RLS with No Policies
Enabling RLS with zero policies makes the table **completely inaccessible**. Safe default, but often unintentional.

### UPDATE Requires SELECT Policy
UPDATE policies silently fail without a corresponding SELECT policy — the database needs to read the existing row first.

### JWT Modification Risk
Never use `raw_user_meta_data` for authorization — users can modify it. Use `raw_app_meta_data` instead.

## cekwajar.id Implementation Notes

- **File to update**: `supabase/migrations/YYYYMMDD_add_rls_policies.sql`
- **Function to modify/create**: Add `has_role_on_account()` and `has_permission()` security definer functions
- **Data source to query**: `auth.users`, `public.accounts`, `public.accounts_memberships`
- **Update frequency**: Migration-based; run on schema changes
- **Legion action**: Can write migration files, needs Bashara review for security-sensitive policies

## Monetization Angle
Proper RLS implementation enables trust for enterprise clients requiring data isolation guarantees — critical for premium pricing tiers.

## Sources and Cross-References
- Official URL: https://supabase.com/docs/guides/database/postgres/row-level-security
- Makerkit RLS Patterns: https://makerkit.dev/blog/tutorials/supabase-rls-best-practices
- Last regulation update: Continuous — PostgreSQL feature
