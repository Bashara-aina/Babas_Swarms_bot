***
title: "Wajar Tanah — Land Price Benchmark — Full Spec"
***

# Wajar Tanah — Complete Technical Specification

## Purpose
Answers: "Apakah harga tanah ini wajar?"
Triangulates from 3 sources: NJOP (government), listings, crowdsourced.

## Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `province` | ✅ | Indonesian province |
| `city` | ✅ | City/Kabupaten |
| `district` | ✅ | Kecamatan |
| `address` | ❌ | Optional for street-level |
| `sizeSqm` | ✅ | Land area in m² |
| `landType` | ✅ | Residential/Commercial/Industrial/Agricultural |
| `zoneType` | ✅ | Urban/Suburban/Rural |
| `landStatus` | ✅ | SHM (Freehold)/HGB (Lease)/HGU (Agricultural) |
| `askingPrice` | ❌ | User's price to benchmark |

## Three-Source Triangulation

```
BENCHMARK_PRICE = w_NJOP × P_NJOP + w_Listing × P_Listing + w_Crowd × P_Crowd
```

| Source | Base Weight | Boost Condition |
|--------|-------------|----------------|
| NJOP (Bhumi/ATRBPN) | 35% | +20% if NJOP < 2 years old |
| Listings (Properti.com, OLX) | 40% | +15% if ≥ 5 comparables |
| Crowdsourced Transactions | 25% | +10% if ≥ 10 verified |

> Weights re-normalized to sum 1.0 after each adjustment.

## NJOP Regional Gap Multipliers

| City | NJOP-to-Market Gap | Min | Max |
|------|--------------------|-----|-----|
| Jakarta | 5.2× | 3.0× | 8.0× |
| Surabaya | 3.2× | 2.0× | 5.0× |
| Bandung | 2.8× | 2.0× | 4.0× |
| Medan | 2.1× | 1.5× | 3.0× |
| Yogyakarta | 1.8× | 1.2× | 2.5× |
| Default | 2.3× | 1.5× | 3.5× |

```
P_NJOP = NJOP_per_sqm × (1 + region_gap_avg) × land_size_sqm

Example — Jakarta Pusat, 500 sqm, NJOP IDR 40M/m²:
  P_NJOP = 40,000,000 × (1 + 5.2) × 500 = IDR 1,240,000,000
```

## Verdict Thresholds

| Gap vs Benchmark | Verdict |
|-----------------|---------|
| > +30% | 🚨 Terlalu Mahal |
| +15% to +30% | 🟠 Agak Mahal |
| −15% to +15% | ✅ Wajar |
| −30% to −15% | 🟡 Agak Murah |
| < −30% | 🟢 Murah (check legality!) |

## Confidence Score
```
confidence = 100 × sample_factor × recency_factor × variance_factor
sample_factor: min((n_NJOP + n_listings + n_crowd) / 15, 1.0)
recency_factor: 0.8^(months_since_data / 12)
variance_factor: 1 / (1 + CV)  where CV = stddev/mean
```

## Crowdsourced Transaction Acceptance Criteria

- Price within ±4σ of kelurahan median
- Document scan uploaded (SHM/HGB certificate)
- User reputation score ≥ 0.6
- Commercial transaction only (not inheritance/gift)

**Rejection triggers:** Artificially low price, duplicate IP, document fail