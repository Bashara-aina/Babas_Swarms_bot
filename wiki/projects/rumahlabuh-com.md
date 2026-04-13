---
title: rumahlabuh-com
type: project
status: active
tags: [indonesia, property, rental, web-app, nextjs, supabase]
created: 2026-04-13
updated: 2026-04-13
summary:: " rumahlabuh.com is an Indonesian property rental platform built with Next.js and Supabase, featuring property listings, inquiry management, and booking workflows. Target: property owners and renters in Indonesia seeking transparent rental processes."
wikilinks:
  - [[supabase]]
  - [[cekwajar-id]]
confidence: high
source: implementation
project: rumahlabuh
---

# rumahlabuh.com

## TL;DR
rumahlabuh.com is an Indonesian property rental platform with Next.js frontend and Supabase backend, featuring property listings, inquiries, and booking management.

## Goals

- Connect property owners with potential renters
- Streamline rental inquiries
- Manage property listings efficiently

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js |
| Database | Supabase |
| Auth | Supabase Auth |
| Payments | Midtrans |
| Deployment | Vercel |

## Features

- Property listing management
- Inquiry submission
- Contact management
- Basic analytics

## Database Schema

Properties, inquiries, and users tables in Supabase.

### Core Tables

```sql
-- Property listings
properties (
  id UUID PRIMARY KEY,
  owner_id UUID REFERENCES auth.users,
  title TEXT,
  description TEXT,
  property_type TEXT,  -- apartment, house, villa, land
  location TEXT,        -- city, district
  price_monthly BIGINT,
  currency TEXT DEFAULT 'IDR',
  amenities TEXT[],    -- AC, WiFi, parking, etc.
  photos TEXT[],       -- Supabase Storage URLs
  status TEXT DEFAULT 'active',  -- active, rented, inactive
  created_at TIMESTAMPTZ
)

-- Rental inquiries
inquiries (
  id UUID PRIMARY KEY,
  property_id UUID REFERENCES properties(id),
  renter_name TEXT,
  renter_email TEXT,
  renter_phone TEXT,
  message TEXT,
  status TEXT DEFAULT 'new',  -- new, contacted, visited, agreed, rejected
  created_at TIMESTAMPTZ
)
```

### Row Level Security (RLS)

Supabase RLS policies enforce:
- Owners can only edit their own listings
- Anyone can read active listings
- Inquiry data visible only to property owners

## Integration with Legion

rumahlabuh.com is one of Bashara's active projects alongside cekwajar.id. Legion can:
- Check platform health via `/rumahlabuh_status` (via Supabase query)
- Monitor inquiry volume from the database
- Research competitor properties for pricing analysis

## Development History

rumahlabuh.com was developed alongside cekwajar.id as part of Bashara's Indonesian market platform suite:

| Date | Milestone |
|------|-----------|
| 2025-Q4 | Initial Next.js project scaffold |
| 2026-01 | Supabase integration, RLS policies |
| 2026-02 | Property CRUD operations, photo uploads |
| 2026-03 | Inquiry management, owner dashboard |
| 2026-04 | SEO optimization, analytics |

## Planned Features

- **Property comparison**: Side-by-side comparison of multiple properties
- **Integrated payments**: Midtrans payment gateway for booking deposits
- **Mobile app**: React Native companion app
- **AI property matching**: Recommend properties based on user preferences
- **Multi-city expansion**: Jakarta → Surabaya, Bandung, Bali

## Current Status

As of 2026-04-13:
- MVP launched with core property listing and inquiry features
- Active property listings managed via Supabase dashboard
- Inquiry notifications sent to property owners
- SEO and basic analytics enabled via Vercel

## Related Pages

- [[supabase]] — Database provider
- [[cekwajar-id]] — Related project (salary benchmarking platform)
- [[projects/cekwajar-roadmap]] — Development roadmap
- [[timelines/cekwajar-phase-log]] — Phase history
