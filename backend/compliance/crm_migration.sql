-- Alembic Migration: Provision Core CRM Pipeline Tables
-- Revision ID: c3c0217b_crm_v1
-- Date: 2026-05-24

BEGIN;

-- 1. Alter Contacts Table to append new CRM properties while preserving backward compatibility
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS phone_e164 VARCHAR(20);
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(255);
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS lead_source VARCHAR(100);
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS lead_score INTEGER DEFAULT 0 CHECK (lead_score >= 0 AND lead_score <= 100);
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::JSONB;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS custom_fields JSONB DEFAULT '{}'::JSONB;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS created_by VARCHAR(100);

-- Backfill name/phone_number/company to their CRM equivalents
UPDATE contacts SET full_name = name WHERE full_name IS NULL AND name IS NOT NULL;
UPDATE contacts SET phone_e164 = phone_number WHERE phone_e164 IS NULL AND phone_number IS NOT NULL;
UPDATE contacts SET company_name = company WHERE company_name IS NULL AND company IS NOT NULL;

-- 2. Companies Table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    industry VARCHAR(100),
    employee_count INTEGER,
    annual_revenue NUMERIC,
    country VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_companies_tenant ON companies (tenant_id);

-- 3. Pipeline Stages Table
CREATE TABLE IF NOT EXISTS pipeline_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    position INTEGER NOT NULL,
    probability_pct INTEGER NOT NULL CHECK (probability_pct >= 0 AND probability_pct <= 100),
    is_terminal BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    created_by VARCHAR(100),
    CONSTRAINT uq_stage_position_tenant UNIQUE (tenant_id, position)
);

CREATE INDEX IF NOT EXISTS idx_stages_tenant ON pipeline_stages (tenant_id);

-- 4. Deals Table
CREATE TABLE IF NOT EXISTS deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    stage_id UUID REFERENCES pipeline_stages(id) ON DELETE RESTRICT NOT NULL,
    title VARCHAR(255) NOT NULL,
    value_usd NUMERIC(15, 2) DEFAULT 0.00 NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD' NOT NULL,
    close_date TIMESTAMP WITH TIME ZONE,
    owner_id VARCHAR(100),
    notes TEXT,
    ai_next_action TEXT,
    ai_sentiment VARCHAR(20) DEFAULT 'unknown' CHECK (ai_sentiment IN ('positive', 'neutral', 'negative', 'unknown')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_deals_tenant ON deals (tenant_id);
CREATE INDEX IF NOT EXISTS idx_deals_contact ON deals (contact_id);
CREATE INDEX IF NOT EXISTS idx_deals_company ON deals (company_id);
CREATE INDEX IF NOT EXISTS idx_deals_stage ON deals (stage_id);

-- 5. Activities Table
CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    deal_id UUID REFERENCES deals(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('call', 'email', 'sms', 'note', 'task')),
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    duration_seconds INTEGER DEFAULT 0 NOT NULL,
    outcome VARCHAR(255),
    transcript_url VARCHAR(1024),
    recording_url VARCHAR(1024),
    ai_summary TEXT,
    created_by_ai BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_activities_tenant ON activities (tenant_id);
CREATE INDEX IF NOT EXISTS idx_activities_contact ON activities (contact_id);
CREATE INDEX IF NOT EXISTS idx_activities_deal ON activities (deal_id);

-- 6. Deal Stage History Table
CREATE TABLE IF NOT EXISTS deal_stage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE NOT NULL,
    from_stage_id UUID REFERENCES pipeline_stages(id) ON DELETE SET NULL,
    to_stage_id UUID REFERENCES pipeline_stages(id) ON DELETE SET NULL,
    reason TEXT,
    changed_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_history_tenant ON deal_stage_history (tenant_id);
CREATE INDEX IF NOT EXISTS idx_history_deal ON deal_stage_history (deal_id);

-- ----------------------------------------------------
-- ENABLE RLS & DEFINE POLICIES
-- ----------------------------------------------------
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_stages ENABLE ROW LEVEL SECURITY;
ALTER TABLE deals ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE deal_stage_history ENABLE ROW LEVEL SECURITY;

-- Companies Policies
CREATE POLICY companies_tenant_isolation ON companies
    FOR ALL
    TO authenticated
    USING (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID)
    WITH CHECK (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID);

-- Pipeline Stages Policies
CREATE POLICY stages_tenant_isolation ON pipeline_stages
    FOR ALL
    TO authenticated
    USING (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID)
    WITH CHECK (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID);

-- Deals Policies
CREATE POLICY deals_tenant_isolation ON deals
    FOR ALL
    TO authenticated
    USING (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID)
    WITH CHECK (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID);

-- Activities Policies
CREATE POLICY activities_tenant_isolation ON activities
    FOR ALL
    TO authenticated
    USING (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID)
    WITH CHECK (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID);

-- Deal Stage History Policies
CREATE POLICY history_tenant_isolation ON deal_stage_history
    FOR ALL
    TO authenticated
    USING (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID)
    WITH CHECK (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID);

COMMIT;
