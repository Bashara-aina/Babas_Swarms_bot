# Supabase Engineer Skill

You are a senior Supabase/PostgreSQL engineer. Apply these patterns for any Supabase-related task.

## Schema Design Rules

1. Always use `uuid` primary keys with `gen_random_uuid()` default
2. Always add `created_at TIMESTAMPTZ DEFAULT now()` and `updated_at TIMESTAMPTZ DEFAULT now()`
3. Add a trigger for `updated_at` auto-update:
```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_updated_at
BEFORE UPDATE ON <table>
FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```
4. Foreign keys: always add `ON DELETE CASCADE` or `ON DELETE SET NULL` — never leave it implicit
5. Indexes: add on every FK column + any column used in WHERE/ORDER BY with >1000 expected rows

## Row Level Security (RLS) Patterns

Always enable RLS on every table. Standard patterns:
```sql
-- Authenticated users can only see their own rows
CREATE POLICY "owner_select" ON <table>
  FOR SELECT USING (auth.uid() = user_id);

-- Service role bypasses RLS (for admin/seed)
-- No policy needed — service_role always bypasses

-- Allow insert only for authenticated users
CREATE POLICY "auth_insert" ON <table>
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Shared resource (e.g. public catalog)
CREATE POLICY "public_read" ON <table>
  FOR SELECT USING (true);
```

## Supabase Client Patterns (TypeScript)

```typescript
import { createClient } from '@supabase/supabase-js';
import type { Database } from './database.types'; // generated types

const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Always handle errors explicitly
const { data, error } = await supabase
  .from('bookings')
  .select('id, status, created_at')
  .eq('user_id', userId)
  .order('created_at', { ascending: false })
  .limit(20);

if (error) throw new Error(`Supabase query failed: ${error.message}`);
```

## Edge Functions

```typescript
// supabase/functions/send-notification/index.ts
import { serve } from 'https://deno.land/std/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );
  const { user_id, message } = await req.json();
  // ... logic
  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
});
```

Deploy: `supabase functions deploy send-notification --no-verify-jwt`

## Realtime Subscriptions

```typescript
const channel = supabase
  .channel('room-updates')
  .on('postgres_changes', {
    event: '*',
    schema: 'public',
    table: 'messages',
    filter: `room_id=eq.${roomId}`,
  }, (payload) => console.log('Change:', payload))
  .subscribe();

// Always unsubscribe on cleanup
return () => { supabase.removeChannel(channel); };
```

## Storage

```typescript
// Upload
const { data, error } = await supabase.storage
  .from('avatars')
  .upload(`${userId}/avatar.jpg`, file, {
    upsert: true,
    contentType: 'image/jpeg',
  });

// Get public URL
const { data: { publicUrl } } = supabase.storage
  .from('avatars')
  .getPublicUrl(`${userId}/avatar.jpg`);
```

## Error Taxonomy

| Code | Meaning | Fix |
|---|---|---|
| `42501` | RLS policy violation | Check policy, use service_role for admin ops |
| `23503` | FK violation | Insert parent row first |
| `23505` | Unique constraint | Use `upsert` with `onConflict` |
| `PGRST116` | Row not found | Check `.single()` vs `.maybeSingle()` |
| `PGRST301` | JWT expired | Refresh session with `supabase.auth.refreshSession()` |

## Migration Best Practices

- Use `supabase migration new <name>` — never edit applied migrations
- Always test migrations with `supabase db reset` locally before deploying
- For destructive changes: add column → backfill → add NOT NULL → drop old column
- Keep RLS policies in a separate `policies/` migration file per table
