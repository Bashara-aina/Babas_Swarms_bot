-- Migration: Add pg_trgm extension and fuzzy search RPC function
-- Required for salary benchmark job title matching

-- Enable pg_trgm extension for fuzzy text matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Fuzzy search function for job categories
-- Returns up to 10 job categories matching the search term with similarity score
CREATE OR REPLACE FUNCTION search_job_categories_fuzzy(
  search_term TEXT,
  threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE (id UUID, title TEXT, similarity_score FLOAT) AS $$
  SELECT
    id,
    title,
    similarity(title, search_term) AS similarity_score
  FROM job_categories
  WHERE is_active = true
    AND similarity(title, search_term) > threshold
  ORDER BY similarity_score DESC
  LIMIT 10;
$$ LANGUAGE SQL SECURITY DEFINER;

-- Also create a trigram index for faster fuzzy search
CREATE INDEX IF NOT EXISTS idx_job_categories_trgm_search
ON job_categories USING GIN(title gin_trgm_ops)
WHERE is_active = true;
