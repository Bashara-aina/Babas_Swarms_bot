-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 004_rls_phase1.sql
-- Row Level Security for user_profiles and subscriptions
-- ══════════════════════════════════════════════════════════════════════════════

-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- user_profiles policies
CREATE POLICY "users_select_own" ON user_profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "users_update_own" ON user_profiles
  FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

-- subscriptions policies
CREATE POLICY "users_select_own_subscription" ON subscriptions
  FOR SELECT USING (auth.uid() = user_id);

-- transactions policies
CREATE POLICY "users_select_own_transactions" ON transactions
  FOR SELECT USING (auth.uid() = user_id);
