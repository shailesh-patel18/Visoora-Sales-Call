"""add_background_jobs_and_business_brain

Revision ID: 90c574973a7d
Revises: a8d8f3af5e6f
Create Date: 2026-07-02 08:17:13.199351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90c574973a7d'
down_revision: Union[str, Sequence[str], None] = 'a8d8f3af5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    -- Background jobs table
    CREATE TABLE IF NOT EXISTS background_jobs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        job_type VARCHAR(50) NOT NULL,
        status VARCHAR(50) DEFAULT 'queued',
        payload JSONB DEFAULT '{}'::jsonb,
        result JSONB DEFAULT '{}'::jsonb,
        error TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Enable RLS
    ALTER TABLE background_jobs ENABLE ROW LEVEL SECURITY;

    -- Add isolation policy
    CREATE POLICY tenant_isolation_policy ON background_jobs USING (tenant_id = (current_setting('request.jwt.claims', true)::jsonb ->> 'tenant_id')::uuid);

    -- Extend agent_configs with Business Brain columns
    ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS icp_industries JSONB DEFAULT '[]'::jsonb;
    ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS icp_company_sizes JSONB DEFAULT '[]'::jsonb;
    ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS icp_regions JSONB DEFAULT '[]'::jsonb;
    ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS decision_maker_titles JSONB DEFAULT '[]'::jsonb;
    ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS avoid_list JSONB DEFAULT '[]'::jsonb;
    ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS competitors JSONB DEFAULT '[]'::jsonb;
    ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS objections_list JSONB DEFAULT '[]'::jsonb;
    ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS brand_voice_tone TEXT;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
    DROP TABLE IF EXISTS background_jobs CASCADE;
    ALTER TABLE agent_configs DROP COLUMN IF EXISTS icp_industries CASCADE;
    ALTER TABLE agent_configs DROP COLUMN IF EXISTS icp_company_sizes CASCADE;
    ALTER TABLE agent_configs DROP COLUMN IF EXISTS icp_regions CASCADE;
    ALTER TABLE agent_configs DROP COLUMN IF EXISTS decision_maker_titles CASCADE;
    ALTER TABLE agent_configs DROP COLUMN IF EXISTS avoid_list CASCADE;
    ALTER TABLE agent_configs DROP COLUMN IF EXISTS competitors CASCADE;
    ALTER TABLE agent_configs DROP COLUMN IF EXISTS objections_list CASCADE;
    ALTER TABLE agent_configs DROP COLUMN IF EXISTS brand_voice_tone CASCADE;
    """)
