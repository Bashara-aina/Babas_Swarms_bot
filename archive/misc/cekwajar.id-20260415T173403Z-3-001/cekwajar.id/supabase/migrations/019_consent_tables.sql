-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 019_consent_tables.sql
-- User consent tracking for privacy policy
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS user_consents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  policy_version TEXT NOT NULL,
  privacy_policy_accepted BOOLEAN NOT NULL DEFAULT false,
  terms_accepted BOOLEAN NOT NULL DEFAULT false,
  marketing_accepted BOOLEAN NOT NULL DEFAULT false,
  accepted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ip_hash TEXT
);

ALTER TABLE user_consents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_select_own_consents" ON user_consents
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_consents" ON user_consents
  FOR INSERT WITH CHECK (auth.uid() = user_id);
