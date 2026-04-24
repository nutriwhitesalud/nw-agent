CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS knowledge_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_uri TEXT NOT NULL UNIQUE,
  source_type TEXT NOT NULL,
  title TEXT NOT NULL,
  content_md TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
  corpus TEXT NOT NULL DEFAULT 'default',
  chunk_index INTEGER NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  source_uri TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  embedding VECTOR(1536),
  search_tsv TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, ''))
  ) STORED,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document_id
  ON knowledge_chunks (document_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_corpus
  ON knowledge_chunks (corpus);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_metadata
  ON knowledge_chunks USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_search_tsv
  ON knowledge_chunks USING GIN (search_tsv);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_hnsw
  ON knowledge_chunks USING HNSW (embedding vector_cosine_ops);

