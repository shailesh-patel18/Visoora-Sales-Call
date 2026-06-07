"""init_schema

Revision ID: 9c20a8b8f363
Revises: 
Create Date: 2026-05-25 07:45:28.397001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c20a8b8f363'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    -- Enable required extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Tenants master table
    CREATE TABLE IF NOT EXISTS tenants (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name VARCHAR(255) NOT NULL,
        plan VARCHAR(50) DEFAULT 'starter',
        twilio_phone VARCHAR(50),
        twilio_subaccount_sid VARCHAR(255),
        storage_bucket_name VARCHAR(255),
        stripe_customer_id VARCHAR(255),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Contacts table
    CREATE TABLE IF NOT EXISTS contacts (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        phone_e164 VARCHAR(50),
        phone_number VARCHAR(50),
        email VARCHAR(255),
        full_name VARCHAR(255),
        name VARCHAR(255),
        title VARCHAR(255),
        company_name VARCHAR(255),
        company VARCHAR(255),
        lead_score INTEGER DEFAULT 0,
        tags JSONB DEFAULT '[]'::jsonb,
        custom_fields JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        created_by VARCHAR(255)
    );

    -- Companies table
    CREATE TABLE IF NOT EXISTS companies (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        name VARCHAR(255) NOT NULL,
        domain VARCHAR(255),
        industry VARCHAR(255),
        employee_count INTEGER,
        annual_revenue NUMERIC(15,2),
        country VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        created_by VARCHAR(255)
    );

    -- Pipeline Stages
    CREATE TABLE IF NOT EXISTS pipeline_stages (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        name VARCHAR(255) NOT NULL,
        position INTEGER NOT NULL,
        probability_pct INTEGER DEFAULT 0,
        is_terminal BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        created_by VARCHAR(255)
    );

    -- Deals
    CREATE TABLE IF NOT EXISTS deals (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        contact_id UUID REFERENCES contacts(id),
        company_id UUID REFERENCES companies(id),
        stage_id UUID REFERENCES pipeline_stages(id),
        title VARCHAR(255) NOT NULL,
        value_usd NUMERIC(15,2) DEFAULT 0.0,
        close_date TIMESTAMP WITH TIME ZONE,
        ai_next_action VARCHAR(255),
        ai_sentiment VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        created_by VARCHAR(255)
    );

    -- Activities
    CREATE TABLE IF NOT EXISTS activities (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        deal_id UUID REFERENCES deals(id),
        contact_id UUID REFERENCES contacts(id),
        type VARCHAR(50) NOT NULL,
        occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        duration_seconds INTEGER DEFAULT 0,
        outcome VARCHAR(255),
        ai_summary TEXT,
        created_by_ai BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        created_by VARCHAR(255)
    );

    -- Deal Stage History
    CREATE TABLE IF NOT EXISTS deal_stage_history (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        deal_id UUID REFERENCES deals(id),
        from_stage_id UUID REFERENCES pipeline_stages(id),
        to_stage_id UUID REFERENCES pipeline_stages(id),
        changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        changed_by VARCHAR(255),
        reason TEXT,
        ai_triggered BOOLEAN DEFAULT FALSE
    );

    -- DNC Numbers
    CREATE TABLE IF NOT EXISTS dnc_numbers (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        phone_number VARCHAR(50) NOT NULL,
        phone_e164 VARCHAR(50),
        added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        added_by VARCHAR(255)
    );

    -- Call Consents
    CREATE TABLE IF NOT EXISTS call_consents (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        phone_number VARCHAR(50) NOT NULL,
        consent_token UUID,
        granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        consent_type VARCHAR(50),
        granted_by_ip VARCHAR(50),
        expires_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Agent Configs
    CREATE TABLE IF NOT EXISTS agent_configs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        persona TEXT,
        company_description TEXT,
        value_proposition TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Call Logs
    CREATE TABLE IF NOT EXISTS call_logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        contact_id UUID REFERENCES contacts(id),
        call_sid VARCHAR(255),
        duration_seconds INTEGER,
        status VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Call Summaries
    CREATE TABLE IF NOT EXISTS call_summaries (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        contact_id UUID REFERENCES contacts(id),
        call_id UUID REFERENCES call_logs(id),
        summary TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Agent Availability
    CREATE TABLE IF NOT EXISTS agent_availability (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        agent_user_id VARCHAR(255),
        agent_name VARCHAR(255),
        is_available BOOLEAN DEFAULT TRUE,
        last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Tenant Compliance Settings
    CREATE TABLE IF NOT EXISTS tenant_compliance_settings (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        recording_disclosure_enabled BOOLEAN DEFAULT TRUE,
        recording_disclosure_text TEXT,
        ai_disclosure_enabled BOOLEAN DEFAULT TRUE,
        ai_disclosure_text TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Call Embeddings
    CREATE TABLE IF NOT EXISTS call_embeddings (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        contact_id UUID REFERENCES contacts(id),
        call_id UUID REFERENCES call_logs(id),
        embedding vector(1536),
        chunk_text TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- IVFFlat Index
    CREATE INDEX IF NOT EXISTS call_embeddings_embedding_idx ON call_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

    -- Callback Tasks
    CREATE TABLE IF NOT EXISTS callback_tasks (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        phone_number VARCHAR(50),
        status VARCHAR(50) DEFAULT 'pending',
        callback_window VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Vector Search RPC
    CREATE OR REPLACE FUNCTION match_call_embeddings(
        query_embedding vector(1536),
        match_threshold float,
        match_count int,
        p_tenant_id uuid,
        p_contact_id uuid
    )
    RETURNS TABLE (
        id uuid,
        chunk_text text,
        similarity float
    )
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN QUERY
        SELECT
            call_embeddings.id,
            call_embeddings.chunk_text,
            1 - (call_embeddings.embedding <=> query_embedding) AS similarity
        FROM call_embeddings
        WHERE call_embeddings.tenant_id = p_tenant_id AND call_embeddings.contact_id = p_contact_id
          AND 1 - (call_embeddings.embedding <=> query_embedding) > match_threshold
        ORDER BY call_embeddings.embedding <=> query_embedding
        LIMIT match_count;
    END;
    $$;

    -- Enable Row Level Security
    ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
    ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
    ALTER TABLE pipeline_stages ENABLE ROW LEVEL SECURITY;
    ALTER TABLE deals ENABLE ROW LEVEL SECURITY;
    ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
    ALTER TABLE dnc_numbers ENABLE ROW LEVEL SECURITY;
    ALTER TABLE call_consents ENABLE ROW LEVEL SECURITY;
    ALTER TABLE agent_configs ENABLE ROW LEVEL SECURITY;
    ALTER TABLE call_logs ENABLE ROW LEVEL SECURITY;
    ALTER TABLE call_summaries ENABLE ROW LEVEL SECURITY;
    ALTER TABLE agent_availability ENABLE ROW LEVEL SECURITY;
    ALTER TABLE tenant_compliance_settings ENABLE ROW LEVEL SECURITY;
    ALTER TABLE call_embeddings ENABLE ROW LEVEL SECURITY;
    ALTER TABLE callback_tasks ENABLE ROW LEVEL SECURITY;

    -- Create common policy for all tables
    DO $$ 
    DECLARE 
        t_name text;
    BEGIN 
        FOR t_name IN 
            SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version' AND tablename != 'tenants' AND tablename != 'deal_stage_history'
        LOOP
            EXECUTE format('
                CREATE POLICY tenant_isolation_policy ON %I 
                USING (tenant_id = (current_setting(''request.jwt.claims'', true)::jsonb ->> ''tenant_id'')::uuid);
            ', t_name);
        END LOOP;
    END $$;

    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
    DROP TABLE IF EXISTS callback_tasks CASCADE;
    DROP TABLE IF EXISTS call_embeddings CASCADE;
    DROP TABLE IF EXISTS tenant_compliance_settings CASCADE;
    DROP TABLE IF EXISTS agent_availability CASCADE;
    DROP TABLE IF EXISTS call_summaries CASCADE;
    DROP TABLE IF EXISTS call_logs CASCADE;
    DROP TABLE IF EXISTS agent_configs CASCADE;
    DROP TABLE IF EXISTS call_consents CASCADE;
    DROP TABLE IF EXISTS dnc_numbers CASCADE;
    DROP TABLE IF EXISTS deal_stage_history CASCADE;
    DROP TABLE IF EXISTS activities CASCADE;
    DROP TABLE IF EXISTS deals CASCADE;
    DROP TABLE IF EXISTS pipeline_stages CASCADE;
    DROP TABLE IF EXISTS companies CASCADE;
    DROP TABLE IF EXISTS contacts CASCADE;
    DROP TABLE IF EXISTS tenants CASCADE;
    """)
