---
title: Midtrans
type: entity
status: active
tags: [payment, gateway, indonesia, rumahlabuh]
created: 2026-05-16
updated: 2026-05-16
summary: "Midtrans is an Indonesian payment gateway service supporting credit cards, bank transfers, e-wallets, and other payment methods."
wikilinks:
  - [[projects/rumahlabuh-com]]
confidence: high
source: external
---
# Midtrans — Payment Gateway

## Overview

Midtrans is an Indonesian payment gateway that provides payment processing for e-commerce and web applications. It supports credit cards (Visa/MasterCard/JCB), bank transfers (VA), e-wallets (GoPay/OVO/ Dana), and other payment methods common in Indonesia.

## Key Features

- **Snap Payment**: Hosted payment page with redirect flow
- **Core API**: Direct API integration for custom checkout flows
- **HTTP Notification**: Webhook-based payment status updates
- **Dashboard**: Real-time transaction monitoring

## Usage in Swarm-Bot

Midtrans is used in the rumahlabuh-com project for payment processing. When working on payment integration tasks, understand the Snap redirect flow and webhook notification pattern.

## Relevant Files

- `cekwajar.id/app/api/midtrans/webhook/route.ts` — webhook handler
- `cekwajar.id/app/api/midtrans/snap/route.ts` — Snap API integration