-- Phase 1: Workflow Engine & Business Brain Migrations

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: business_brains
-- Stores the deep business intelligence extracted for a given domain/tenant.
-- This acts as the reusable asset rather than just storing a static report.
CREATE TABLE IF NOT EXISTS business_brains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    industry TEXT,
    products JSONB DEFAULT '[]'::jsonb,
    icp JSONB DEFAULT '[]'::jsonb,
    buyer_personas JSONB DEFAULT '[]'::jsonb,
    competitors JSONB DEFAULT '[]'::jsonb,
    pain_points JSONB DEFAULT '[]'::jsonb,
    revenue_opportunities JSONB DEFAULT '[]'::jsonb,
    trust_audit JSONB DEFAULT '{}'::jsonb,
    growth_roadmap JSONB DEFAULT '{}'::jsonb,
    ai_scores JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    last_crawled TIMESTAMPTZ,
    ttl_expires_at TIMESTAMPTZ,
    schema_version TEXT DEFAULT '1.0',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for intelligent caching lookup
CREATE INDEX IF NOT EXISTS idx_business_brains_domain ON business_brains(domain);

-- Table: workflow_jobs
-- A generic job orchestration table that can handle any AI workflow.
CREATE TABLE IF NOT EXISTS workflow_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_type TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    user_id TEXT,
    priority INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'queued', -- queued, running, success, failed, cancelled
    payload JSONB DEFAULT '{}'::jsonb, -- Input payload
    progress JSONB DEFAULT '[]'::jsonb, -- Stream of progress steps
    current_step TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    cost NUMERIC(10, 6) DEFAULT 0,
    tokens INTEGER DEFAULT 0,
    result_id UUID REFERENCES business_brains(id) ON DELETE SET NULL,
    error TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: workflow_events
-- Telemetry and event log for every state transition in a workflow.
CREATE TABLE IF NOT EXISTS workflow_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES workflow_jobs(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- e.g., 'workflow_started', 'step_completed'
    step_name TEXT,
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to auto-update updated_at on workflow_jobs
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_workflow_jobs_modtime ON workflow_jobs;
CREATE TRIGGER update_workflow_jobs_modtime
BEFORE UPDATE ON workflow_jobs
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

DROP TRIGGER IF EXISTS update_business_brains_modtime ON business_brains;
CREATE TRIGGER update_business_brains_modtime
BEFORE UPDATE ON business_brains
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
