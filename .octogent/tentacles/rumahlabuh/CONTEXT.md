# Rumahlabuh — Rental & Boarding House Platform (Solo, Indonesia)

A real estate marketplace platform focused on kos (boarding houses) and rental
properties in Solo (Surakarta) and surrounding areas. Aggregates listings,
provides price analysis, and connects landlords with tenants.

## What this area owns
- Full-stack Next.js 14 + Supabase platform
- Property listing CRUD with photo upload (Supabase Storage)
- Price per area analysis using scraped market data
- Landlord dashboard and tenant search/filter interface
- rumahlabuh.com domain

## Target market
- Students (UNS, UMS, ISI Solo) — kos, monthly rental
- Young professionals relocating to Solo
- Landlords wanting digital listings without Mamikos' fee structure

## Stack
- Next.js 14 App Router + TypeScript
- Supabase (Postgres + Auth + Realtime + Storage)
- Tailwind CSS + shadcn/ui
- Vercel deployment

## Constraints
- Property data scraping must respect robots.txt
- Photos stored in Supabase Storage, never third-party CDN
- IDR currency throughout — no USD conversion
- Mobile-first design (most users on Android)
- Bahasa Indonesia as primary language, English optional

<!-- octogent:suggested-skills:start -->
<!-- octogent:suggested-skills:end -->