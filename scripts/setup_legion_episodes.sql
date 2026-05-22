-- Episodic Store SQL Setup for Supabase
-- Run this in the Supabase SQL Editor (Dashboard > SQL Editor)

-- Create the legion_episodes table
CREATE TABLE IF NOT EXISTS legion_episodes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id text NOT NULL,
    episode_type text NOT NULL,
    summary text NOT NULL,
    detail text DEFAULT '',
    tags jsonb DEFAULT '[]'::jsonb,
    ts float8 NOT NULL,
    source text DEFAULT 'user',
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz DEFAULT now()
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_legion_episodes_user_id ON legion_episodes(user_id);
CREATE INDEX IF NOT EXISTS idx_legion_episodes_ts ON legion_episodes(ts DESC);
CREATE INDEX IF NOT EXISTS idx_legion_episodes_episode_type ON legion_episodes(episode_type);
CREATE INDEX IF NOT EXISTS idx_legion_episodes_user_ts ON legion_episodes(user_id, ts DESC);

-- Create the legion_profile table for key-value preferences
CREATE TABLE IF NOT EXISTS legion_profile (
    user_id text NOT NULL,
    key text NOT NULL,
    value jsonb NOT NULL,
    updated_at float8 DEFAULT EXTRACT(EPOCH FROM now()),
    PRIMARY KEY (user_id, key)
);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE legion_episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE legion_profile ENABLE ROW LEVEL SECURITY;

-- Allow anonymous read/write for now (adjust as needed)
CREATE POLICY "Allow all" ON legion_episodes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON legion_profile FOR ALL USING (true) WITH CHECK (true);

-- Enable pgvector extension for semantic search (if using embeddings)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Optional: Create a function to auto-consolidate old entries
CREATE OR REPLACE FUNCTION consolidate_old_memories(
    older_than_days int DEFAULT 90,
    keep_last int DEFAULT 500
) RETURNS void AS $$
DECLARE
    cutoff_ts float8;
    old_count int;
BEGIN
    cutoff_ts := EXTRACT(EPOCH FROM now()) - (older_than_days * 86400);

    SELECT COUNT(*) INTO old_count
    FROM legion_episodes
    WHERE ts < cutoff_ts
      AND episode_type != 'consolidated_summary';

    IF old_count > keep_last THEN
        -- Insert a consolidated summary entry
        INSERT INTO legion_episodes (user_id, episode_type, summary, detail, tags, ts, source, metadata)
        SELECT
            user_id,
            'consolidated_summary',
            'Consolidated ' || old_count || ' old memories from period before ' || older_than_days || ' days',
            (SELECT string_agg(summary, ' | ' ORDER BY ts) FROM legion_episodes WHERE ts < cutoff_ts AND user_id = legend_user_id),
            '["consolidated", "auto", "historical"]'::jsonb,
            cutoff_ts,
            'system',
            jsonb_build_object('entry_count', old_count, 'consolidation_type', 'auto_cleanup', 'older_than_days', older_than_days)
        WHERE old_count > 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Verify tables were created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('legion_episodes', 'legion_profile');