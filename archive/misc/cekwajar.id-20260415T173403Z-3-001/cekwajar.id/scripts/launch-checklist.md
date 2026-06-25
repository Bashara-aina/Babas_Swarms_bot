# cekwajar.id — Launch Checklist

## Pre-Launch (do these before pointing domain)

- [ ] `pnpm tsc --noEmit` → zero errors
- [ ] `pnpm lint` → zero errors
- [ ] `pnpm build` → successful build, no build errors
- [ ] All 5 tool pages load and calculate correctly
- [ ] Auth (Google + email) works in production Supabase project
- [ ] Privacy Policy at /privacy-policy
- [ ] Terms of Service at /terms
- [ ] Cookie consent shows on first visit
- [ ] KJPP disclaimer shows on Wajar Tanah
- [ ] PPP disclaimer shows on Wajar Kabur
- [ ] Tax disclaimer shows on Wajar Slip
- [ ] UMK data loaded (SELECT COUNT(*) FROM umk_2026 >= 50)
- [ ] TER rate data loaded (SELECT COUNT(*) FROM pph21_ter_rates >= 30)
- [ ] BPJS rates loaded (SELECT COUNT(*) FROM bpjs_rates = 12)
- [ ] PTKP values loaded (SELECT COUNT(*) FROM ptkp_values = 12)
- [ ] Col indices loaded (SELECT COUNT(*) FROM col_indices = 20)
- [ ] PPP reference loaded (SELECT COUNT(*) FROM ppp_reference = 15)
- [ ] RLS enabled on ALL tables (check from Supabase Studio)
- [ ] payslips storage bucket is PRIVATE (not public)
- [ ] Security headers configured in next.config.ts
- [ ] Sentry DSN configured, error tracking working
- [ ] Uptime Robot configured and monitoring /api/health

## Payment Launch (only when ready to accept real money)

- [ ] PSE Kominfo registration completed
- [ ] Midtrans production keys in Vercel (not sandbox)
- [ ] Midtrans webhook URL updated to https://cekwajar.id/api/webhooks/midtrans
- [ ] Test one real payment (your own card/GoPay) for Rp 1 → verify subscription activates
- [ ] Test webhook with real Midtrans production event
- [ ] Confirm email arrives after payment

## Domain + DNS

- [ ] Domain cekwajar.id purchased (pandi.id or niagahoster.co.id)
- [ ] DNS A record → Vercel IPs: 76.76.21.21
- [ ] CNAME www → cekwajar.id.vercel-dns.com (or Vercel alias)
- [ ] Vercel project → Domains → Add custom domain
- [ ] SSL certificate active (Vercel handles this automatically)
- [ ] Update NEXT_PUBLIC_APP_URL in Vercel: https://cekwajar.id
- [ ] Update Supabase Site URL: https://cekwajar.id
- [ ] Update Supabase Redirect URLs: https://cekwajar.id/auth/callback

## Post-Launch Day 1

- [ ] Monitor Sentry for new errors (first 24h)
- [ ] Monitor Uptime Robot for any downtime
- [ ] Check Supabase Logs for unusual queries
- [ ] Post TikTok Week 1 Video 1
- [ ] Post launch on r/finansialku
- [ ] Share beta link in WhatsApp HRD group
- [ ] Monitor signup count in Supabase auth.users

## Production Secrets Switch (when going live)

Update Vercel env vars to production values:
- `MIDTRANS_SERVER_KEY`: replace SB-Mid-server-... with Mid-server-...
- `NEXT_PUBLIC_MIDTRANS_CLIENT_KEY`: replace SB-Mid-client-... with Mid-client-...
- `MIDTRANS_IS_PRODUCTION`: change to 'true'
- `NEXT_PUBLIC_MIDTRANS_IS_PRODUCTION`: add this as 'true'

Update Midtrans Dashboard → Settings → Configuration → Payment Notification URL:
`https://cekwajar.id/api/webhooks/midtrans`

Update CSP in next.config.ts to remove sandbox URL:
Replace `https://app.sandbox.midtrans.com` with `https://app.midtrans.com`
Keep both during transition period, then remove sandbox after confirmed working.