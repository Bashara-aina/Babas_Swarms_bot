-- Enable pgvector extension
create extension if not exists vector with schema extensions;

-- Embeddings table for Legiona RAG
create table if not exists legiona_embeddings (
  id uuid primary key default gen_random_uuid(),
  file_path text not null,
  chunk_index integer not null,
  content text not null,
  embedding vector(1536),
  metadata jsonb,
  created_at timestamptz default now()
);

-- Fast cosine similarity index
create index if not exists legiona_embeddings_embedding_idx
  on legiona_embeddings
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- RPC function for similarity search
create or replace function match_legiona_embeddings(
  query_embedding vector(1536),
  match_threshold float default 0.78,
  match_count int default 5
)
returns table (
  id uuid,
  file_path text,
  content text,
  similarity float
)
language sql stable
as $$
  select id, file_path, content,
         1 - (embedding <=> query_embedding) as similarity
  from legiona_embeddings
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;
