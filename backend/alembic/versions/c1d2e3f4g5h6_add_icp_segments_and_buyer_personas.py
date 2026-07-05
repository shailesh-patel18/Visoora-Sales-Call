"""add_icp_segments_and_buyer_personas

Revision ID: c1d2e3f4g5h6
Revises: 90c574973a7d
Create Date: 2026-07-04 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4g5h6'
down_revision: Union[str, Sequence[str], None] = '90c574973a7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    -- ICP segments table
    CREATE TABLE IF NOT EXISTS icp_segments (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        segment VARCHAR(255) NOT NULL,
        confidence INT DEFAULT 100,
        rationale TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Buyer personas table
    CREATE TABLE IF NOT EXISTS buyer_personas (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        title VARCHAR(255) NOT NULL,
        confidence INT DEFAULT 100,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Enable RLS
    ALTER TABLE icp_segments ENABLE ROW LEVEL SECURITY;
    ALTER TABLE buyer_personas ENABLE ROW LEVEL SECURITY;

    -- Add isolation policies
    CREATE POLICY tenant_isolation_policy ON icp_segments USING (tenant_id = (current_setting('request.jwt.claims', true)::jsonb ->> 'tenant_id')::uuid);
    CREATE POLICY tenant_isolation_policy ON buyer_personas USING (tenant_id = (current_setting('request.jwt.claims', true)::jsonb ->> 'tenant_id')::uuid);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
    DROP TABLE IF EXISTS buyer_personas CASCADE;
    DROP TABLE IF EXISTS icp_segments CASCADE;
    """)
