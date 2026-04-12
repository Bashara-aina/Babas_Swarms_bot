---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/engineering/090-postgresql-performance.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-12T01:00:01.732982"
}
---

---
source_id: 090
title: "PostgreSQL Performance for SaaS: Indexing and Query Optimization"
source_type: ENGINEERING
authority: INDUSTRY
url: "https://oneuptime.com/blog/post/2026-01-26-postgresql-query-optimization/view"
last_verified: "2026-04-11"
tags: [postgresql, performance, indexing, query-optimization, supabase, saas]
cekwajar_impact: HIGH
legion_can_act: YES
---

# PostgreSQL Performance for SaaS: Indexing and Query Optimization

## Why This Matters for cekwajar.id
As the payroll SaaS grows:
- More employees per company
- More payslip history
- More companies onboarding
- Queries will slow down without proper indexing

A slow payroll calculation query = users staring at loading spinners during month-end rush.

## Core Knowledge

### EXPLAIN ANALYZE - Your Best Friend
```sql
-- Analyze a query execution plan
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT e.name, e.email, p.gross_salary, p.net_salary
FROM employees e
JOIN payslips p ON p.employee_id = e.id
WHERE e.company_id = 'uuid-here'
  AND p.period = '2024-01'
ORDER BY e.name;
```

**Key terms in EXPLAIN output:**
- `Seq Scan` — Scanning every row (often bad)
- `Index Scan` — Using an index (good)
- `Index Only Scan` — Data all from index (best)
- `Bitmap Heap Scan` — Multi-index combination
- `cost=X..Y` — Estimated cost (lower is better)
- `actual time=X..Y` — Real execution time (ms)

### Essential Indexes for cekwajar.id

```sql
-- Employee lookup by company (most common query)
CREATE INDEX CONCURRENTLY idx_employees_company_id 
ON employees(company_id);

-- Employee lookup by email (auth joins)
CREATE INDEX CONCURRENTLY idx_employees_email 
ON employees(email);

-- Payslip queries by employee and period
CREATE INDEX CONCURRENTLY idx_payslips_employee_period 
ON payslips(employee_id, period);

-- Payslip queries by company and period (bulk reports)
CREATE INDEX CONCURRENTLY idx_payslips_company_period 
ON payslips(company_id, period);

-- Active employees only (partial index)
CREATE INDEX CONCURRENTLY idx_employees_active 
ON employees(company_id) 
WHERE status = 'active';

-- RLS policy helper indexes
CREATE INDEX CONCURRENTLY idx_employees_user_id 
ON employees(user_id);
```

### Index Types

| Type | Use Case | Example |
|------|----------|---------|
| B-tree (default) | Equality, range queries | `WHERE status = 'active'` |
| Hash | Simple equality | `WHERE email = 'x'` |
| GIN | Full-text, JSONB | `WHERE data @> '{"type":"vip"}'` |
| BRIN | Large sequential data | Time-series logs |

### Composite Indexes
```sql
-- Order matters! Most selective first
CREATE INDEX idx_payslips_emp_period 
ON payslips(employee_id, period);

-- Query: WHERE employee_id = X AND period = Y (uses index)
-- Query: WHERE employee_id = X (uses index)
-- Query: WHERE period = Y (does NOT use index)
```

### Partial Indexes for Active Data
```sql
-- Only index active employees (smaller, faster)
CREATE INDEX idx_employees_active 
ON employees(company_id) 
WHERE status = 'active';

-- For payslip current period reports
CREATE INDEX idx_payslips_current_period 
ON payslips(employee_id, period) 
WHERE period = to_char(CURRENT_DATE, 'YYYY-MM');
```

### Query Optimization Patterns

**Good: Explicit filters that match RLS + indexes**
```sql
-- Fast: Uses both RLS and index
SELECT * FROM payslips
WHERE employee_id = auth.uid()  -- RLS + index
  AND period = '2024-01';       -- index
```

**Bad: No filters (relies only on RLS)**
```sql
-- Slow: RLS filters but no index optimization
SELECT * FROM payslips;  -- Full table scan
```

### Common Slow Queries to Fix

**N+1 Query Problem**
```sql
-- Bad: N+1 queries
SELECT * FROM employees WHERE company_id = X;
-- Then loop: SELECT * FROM payslips WHERE employee_id = Y;

-- Good: Single JOIN
SELECT e.id, e.name, p.period, p.net_salary
FROM employees e
LEFT JOIN payslips p ON p.employee_id = e.id
WHERE e.company_id = auth.uid()
ORDER BY e.name, p.period;
```

**Aggregation with indexes**
```sql
-- Slow: Full table aggregation
SELECT company_id, SUM(net_salary) 
FROM payslips 
GROUP BY company_id;

-- Fast: With covering index
CREATE INDEX idx_payslips_company_net 
ON payslips(company_id) 
INCLUDE (net_salary);

SELECT company_id, SUM(net_salary) 
FROM payslips 
GROUP BY company_id;  -- Uses index only
```

### Supabase-Specific Considerations

**RLS + Index Performance**
```sql
-- RLS policy with index
CREATE POLICY "Employees visible to own company"
ON employees FOR SELECT
TO authenticated
USING (
  (SELECT auth.uid()) = user_id
);

-- Required index for RLS performance
CREATE INDEX idx_employees_user_id 
ON employees(user_id);
```

### VACUUM and ANALYZE
```sql
-- Reclaim space and update statistics
VACUUM ANALYZE employees;
VACUUM ANALYZE payslips;

-- Check table bloat
SELECT tablename, 
       pg_size_pretty(pg_total_relation_size(tablename::regclass)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
```

### Monitoring Query Performance

```sql
-- Long-running queries
SELECT pid, now() - query_start AS duration, state, query
FROM pg_stat_activity
WHERE state != 'idle'
  AND query_start < now() - interval '5 seconds'
ORDER BY duration DESC;

-- Most time-consuming queries
SELECT query, calls, total_time, mean_time, rows
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 20;
```

## Edge Cases and Common Mistakes

### Common Mistakes
1. **Missing indexes on foreign keys**: Always index `user_id`, `company_id` columns
2. **Indexes on low-cardinality columns**: Don't index `status` with 2 values
3. **Too many indexes**: Each INSERT/UPDATE must update all indexes
4. **Not using CONCURRENTLY**: Regular CREATE INDEX locks table
5. **Ignoring EXPLAIN output**: Always check before assuming index is used

### When NOT to Index
- Columns with few distinct values
- Tables with frequent bulk inserts
- JSON columns (use GIN instead)
- Very small tables (< 1000 rows)

## cekwajar.id Implementation Notes

- **File to update**: `supabase/migrations/` for index changes
- **Function to modify/create**: Run EXPLAIN ANALYZE on payroll queries
- **Data source to query**: `employees`, `payslips`, `bpjs_contributions` tables
- **Update frequency**: Monthly review of slow queries
- **Legion action**: Can add indexes via migration, needs Bashara review for complex query optimization

## Monetization Angle
Fast queries = fast payroll processing:
- Better user experience during critical month-end processing
- Lower server costs (less CPU time)
- Can handle more companies without scaling infrastructure

## Sources and Cross-References
- Supabase Indexes: https://supabase.com/docs/guides/database/postgres/indexes
- PostgreSQL EXPLAIN: https://www.postgresql.org/docs/current/sql-explain.html
- pg_stat_statements: https://www.postgresql.org/docs/current/pgstatstatements.html
