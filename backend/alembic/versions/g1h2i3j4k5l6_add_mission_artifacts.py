"""add_mission_artifacts

Revision ID: g1h2i3j4k5l6
Revises: f6ce4dd12f32
Create Date: 2026-07-05 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'g1h2i3j4k5l6'
down_revision: Union[str, Sequence[str], None] = 'f6ce4dd12f32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    -- Mission Artifacts table
    CREATE TABLE IF NOT EXISTS mission_artifacts (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES tenants(id),
        type VARCHAR(50) NOT NULL, -- e.g. 'EMAIL_DRAFT'
        status VARCHAR(50) NOT NULL DEFAULT 'WAITING_APPROVAL',
        created_by VARCHAR(255) NOT NULL,
        mission_id VARCHAR(255) NOT NULL,
        confidence INT,
        cost_usd NUMERIC(10, 4),
        prospect_name VARCHAR(255),
        company_name VARCHAR(255),
        pain_points JSONB DEFAULT '[]'::jsonb,
        reason_selected TEXT,
        email_body TEXT,
        expected_reply_rate VARCHAR(50),
        expected_meeting_prob VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Enable RLS
    ALTER TABLE mission_artifacts ENABLE ROW LEVEL SECURITY;

    -- Add isolation policy
    CREATE POLICY tenant_isolation_policy ON mission_artifacts 
        USING (tenant_id = (current_setting('request.jwt.claims', true)::jsonb ->> 'tenant_id')::uuid);
    """)

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
    DROP TABLE IF EXISTS mission_artifacts CASCADE;
    """)
