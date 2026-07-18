"""add_metadata_to_mission_artifacts

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-07-18 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'h2i3j4k5l6m7'
down_revision: Union[str, Sequence[str], None] = 'g1h2i3j4k5l6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    ALTER TABLE mission_artifacts ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
    ALTER TABLE mission_artifacts ADD COLUMN IF NOT EXISTS content JSONB DEFAULT '{}'::jsonb;
    """)

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
    ALTER TABLE mission_artifacts DROP COLUMN IF EXISTS metadata;
    ALTER TABLE mission_artifacts DROP COLUMN IF EXISTS content;
    """)
