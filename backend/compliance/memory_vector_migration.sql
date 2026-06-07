-- Alembic Migration: Provision Memory, RAG & pgvector Tables
-- Revision ID: c3c0217b_memory_v1
-- Date: 2026-05-24

BEGIN;

-- 1. Enable pgvector extension for high-performance semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Structured Contacts / Lead Telemetry Table
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    company VARCHAR(255),
    phone_number VARCHAR(20) NOT NULL,
    budget_signal VARCHAR(255),
    timeline_signal VARCHAR(255),
    decision_maker_status VARCHAR(255),
    pain_points TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
    objections TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    CONSTRAINT uq_contact_phone_tenant UNIQUE (phone_number, tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_contacts_lookup ON contacts (phone_number, tenant_id);

-- 3. Structured Call Summaries Table (Runs async post-call)
CREATE TABLE IF NOT EXISTS call_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE NOT NULL,
    call_id UUID REFERENCES call_logs(id) ON DELETE CASCADE NOT NULL,
    summary_text TEXT NOT NULL,
    outcome VARCHAR(50) NOT NULL, -- interested, not interested, booked, callback requested
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_summaries_contact ON call_summaries (contact_id);
CREATE INDEX IF NOT EXISTS idx_summaries_call ON call_summaries (call_id);

-- 4. Conversational Chunks Semantics Table (pgvector)
CREATE TABLE IF NOT EXISTS call_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE NOT NULL,
    call_id UUID REFERENCES call_logs(id) ON DELETE CASCADE NOT NULL,
    embedding vector(1536) NOT NULL, -- 1536 dim (fits OpenAI text-embedding-3-small)
    chunk_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_embeddings_lookup ON call_embeddings (contact_id);

-- 5. IVFFLAT Index for Optimized Cosine-similarity ANN Search
-- Standard approximate nearest neighbor index mapping
CREATE INDEX IF NOT EXISTS idx_call_embeddings_vector 
ON call_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

COMMIT;
