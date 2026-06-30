"""add_email_followup_tables

Revision ID: a8d8f3af5e6f
Revises: 9c20a8b8f363
Create Date: 2026-06-30 17:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a8d8f3af5e6f'
down_revision: Union[str, Sequence[str], None] = '9c20a8b8f363'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("""
    -- Connected mailboxes table
    CREATE TABLE IF NOT EXISTS connected_mailboxes (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        email VARCHAR(255) NOT NULL,
        provider VARCHAR(50) NOT NULL,
        connection_config TEXT NOT NULL, -- Encrypted JSON string
        is_default BOOLEAN DEFAULT FALSE,
        verification_status VARCHAR(50) DEFAULT 'pending',
        verification_token VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Email threads
    CREATE TABLE IF NOT EXISTS email_threads (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        lead_id UUID NOT NULL, -- references contacts(id)
        subject VARCHAR(255) NOT NULL,
        message_ids JSONB DEFAULT '[]'::jsonb,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Follow-up plans
    CREATE TABLE IF NOT EXISTS followup_plans (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        lead_id UUID NOT NULL,
        status VARCHAR(50) DEFAULT 'active',
        last_decision JSONB DEFAULT '{}'::jsonb,
        next_scheduled_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Reasoning logs
    CREATE TABLE IF NOT EXISTS reasoning_logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        lead_id UUID NOT NULL,
        input_context JSONB DEFAULT '{}'::jsonb,
        decision JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Enable RLS for new tables
    ALTER TABLE connected_mailboxes ENABLE ROW LEVEL SECURITY;
    ALTER TABLE email_threads ENABLE ROW LEVEL SECURITY;
    ALTER TABLE followup_plans ENABLE ROW LEVEL SECURITY;
    ALTER TABLE reasoning_logs ENABLE ROW LEVEL SECURITY;

    -- Add isolation policy
    CREATE POLICY tenant_isolation_policy ON connected_mailboxes USING (tenant_id = (current_setting('request.jwt.claims', true)::jsonb ->> 'tenant_id')::uuid);
    CREATE POLICY tenant_isolation_policy ON email_threads USING (tenant_id = (current_setting('request.jwt.claims', true)::jsonb ->> 'tenant_id')::uuid);
    CREATE POLICY tenant_isolation_policy ON followup_plans USING (tenant_id = (current_setting('request.jwt.claims', true)::jsonb ->> 'tenant_id')::uuid);
    CREATE POLICY tenant_isolation_policy ON reasoning_logs USING (tenant_id = (current_setting('request.jwt.claims', true)::jsonb ->> 'tenant_id')::uuid);
    """)

def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS reasoning_logs CASCADE;
    DROP TABLE IF EXISTS followup_plans CASCADE;
    DROP TABLE IF EXISTS email_threads CASCADE;
    DROP TABLE IF EXISTS connected_mailboxes CASCADE;
    """)
