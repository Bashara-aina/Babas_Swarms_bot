-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 003_subscription_tables.sql
-- Subscriptions and transactions
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  plan_type TEXT NOT NULL CHECK (plan_type IN ('basic', 'pro')),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled')),
  starts_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ends_at TIMESTAMPTZ NOT NULL,
  last_payment_order_id TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS transactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
  midtrans_order_id TEXT NOT NULL UNIQUE,
  plan_type TEXT NOT NULL,
  billing_period TEXT NOT NULL CHECK (billing_period IN ('monthly', 'annual')),
  gross_amount BIGINT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  fraud_status TEXT,
  midtrans_payload JSONB,
  is_webhook_processed BOOLEAN NOT NULL DEFAULT false,
  webhook_received_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);
