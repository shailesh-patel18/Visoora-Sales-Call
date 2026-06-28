-- Phase A AI Sales Employee additive schema.
-- Every new table includes tenant_id from creation time.

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    persona_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_tenant_id ON agents(tenant_id);

CREATE TABLE IF NOT EXISTS agent_knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    source_file TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding_vector JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_knowledge_chunks_tenant_agent
ON agent_knowledge_chunks(tenant_id, agent_id);

ALTER TABLE contacts ADD COLUMN IF NOT EXISTS website TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS research_brief JSONB;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS research_confidence NUMERIC DEFAULT 0;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS needs_review BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    company_name TEXT NOT NULL,
    website TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    linkedin_url TEXT,
    notes TEXT,
    research_brief JSONB,
    research_confidence NUMERIC DEFAULT 0,
    needs_review BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_tenant_agent ON leads(tenant_id, agent_id);

CREATE TABLE IF NOT EXISTS interaction_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    lead_id UUID NOT NULL,
    channel TEXT NOT NULL CHECK (channel IN ('call', 'email')),
    direction TEXT NOT NULL CHECK (direction IN ('outbound', 'inbound')),
    content_ref TEXT,
    status TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    call_log_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_interaction_history_tenant_lead
ON interaction_history(tenant_id, lead_id, created_at);

CREATE TABLE IF NOT EXISTS outreach_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    lead_id UUID NOT NULL,
    decision JSONB NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outreach_decisions_tenant_lead
ON outreach_decisions(tenant_id, lead_id, created_at);
