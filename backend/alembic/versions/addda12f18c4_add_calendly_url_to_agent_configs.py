"""add_calendly_url_to_agent_configs

Revision ID: addda12f18c4
Revises: h2i3j4k5l6m7
Create Date: 2026-07-18 22:48:03.331008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'addda12f18c4'
down_revision: Union[str, Sequence[str], None] = 'h2i3j4k5l6m7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS calendly_url TEXT;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
    ALTER TABLE agent_configs DROP COLUMN IF EXISTS calendly_url CASCADE;
    """)
