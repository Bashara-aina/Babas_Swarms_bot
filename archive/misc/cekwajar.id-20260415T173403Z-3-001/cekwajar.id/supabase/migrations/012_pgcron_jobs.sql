-- ══════════════════════════════════════════════════════════════════════════════
-- cekwajar.id — 012_pgcron_jobs.sql
-- pg_cron scheduled jobs
-- ══════════════════════════════════════════════════════════════════════════════

-- Purge payslip file paths before expiry
SELECT cron.schedule(
  'purge-payslip-records',
  '5 17 * * *',
  $$UPDATE payslip_audits SET payslip_file_path = NULL WHERE delete_at < now() AND payslip_file_path IS NOT NULL$$
);

-- Purge anonymous audits older than 7 days
SELECT cron.schedule(
  'purge-anon-audits',
  '10 17 * * *',
  $$DELETE FROM payslip_audits WHERE user_id IS NULL AND created_at < now() - INTERVAL '7 days'$$
);

-- Check and expire subscriptions
SELECT cron.schedule(
  'subscription-expiry-check',
  '0 18 * * *',
  $$
  UPDATE user_profiles up SET subscription_tier = 'free', updated_at = now()
  FROM subscriptions s
  WHERE s.user_id = up.id AND s.status = 'active' AND s.ends_at < now() - INTERVAL '1 day'
  AND up.subscription_tier != 'free';
  UPDATE subscriptions SET status = 'expired' WHERE status = 'active' AND ends_at < now() - INTERVAL '1 day';
  $$
);

-- Cleanup anonymous sessions
SELECT cron.schedule(
  'cleanup-anon-sessions',
  '0 16 * * *',
  $$DELETE FROM payslip_audits WHERE user_id IS NULL AND created_at < now() - INTERVAL '7 days'$$
);
