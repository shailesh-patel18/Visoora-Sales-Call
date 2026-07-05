"""add_ai_platform_tables

Revision ID: f6ce4dd12f32
Revises: c1d2e3f4g5h6
Create Date: 2026-07-04 16:47:44.389068

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6ce4dd12f32'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4g5h6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ai_prompt_versions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('owner', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('expected_schema', sa.JSON(), nullable=True),
        sa.Column('supported_capabilities', sa.JSON(), nullable=True),
        sa.Column('system_instruction', sa.Text(), nullable=False),
        sa.Column('evaluation_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('name', 'version', name='uix_prompt_name_version')
    )

    op.create_table(
        'ai_provider_health',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    op.create_table(
        'ai_requests',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('workflow_id', sa.String(), nullable=True),
        sa.Column('step_id', sa.String(), nullable=True),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('task_name', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('prompt_version_id', sa.UUID(as_uuid=True), sa.ForeignKey('ai_prompt_versions.id'), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retries', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    op.create_table(
        'ai_usage',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('feature_name', sa.String(), nullable=False),
        sa.Column('total_requests', sa.Integer(), default=0),
        sa.Column('total_tokens', sa.Integer(), default=0),
        sa.Column('total_cost_usd', sa.Float(), default=0.0),
        sa.UniqueConstraint('tenant_id', 'date', 'feature_name', name='uix_usage_tenant_date_feature')
    )

    op.create_table(
        'ai_feedback',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('request_id', sa.UUID(as_uuid=True), sa.ForeignKey('ai_requests.id'), nullable=False),
        sa.Column('user_rating', sa.Integer(), nullable=False),
        sa.Column('user_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ai_feedback')
    op.drop_table('ai_usage')
    op.drop_table('ai_requests')
    op.drop_table('ai_provider_health')
    op.drop_table('ai_prompt_versions')
