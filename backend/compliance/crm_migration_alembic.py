"""Alembic Migration: Provision CRM Pipeline Tables

Revision ID: c3c0217b_crm_v1
Revises: c3c0217b_memory_v1
Create Date: 2026-05-24 22:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3c0217b_crm_v1'
down_revision = 'c3c0217b_memory_v1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Alter Contacts Table
    op.add_column('contacts', sa.Column('phone_e164', sa.String(length=20), nullable=True))
    op.add_column('contacts', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('contacts', sa.Column('full_name', sa.String(length=255), nullable=True))
    op.add_column('contacts', sa.Column('company_name', sa.String(length=255), nullable=True))
    op.add_column('contacts', sa.Column('linkedin_url', sa.String(length=255), nullable=True))
    op.add_column('contacts', sa.Column('lead_source', sa.String(length=100), nullable=True))
    op.add_column('contacts', sa.Column('lead_score', sa.Integer(), server_default='0', nullable=False))
    op.add_column('contacts', sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))
    op.add_column('contacts', sa.Column('custom_fields', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('contacts', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False))
    op.add_column('contacts', sa.Column('created_by', sa.String(length=100), nullable=True))

    # Backfill name/phone_number/company to CRM fields
    op.execute("UPDATE contacts SET full_name = name WHERE full_name IS NULL AND name IS NOT NULL")
    op.execute("UPDATE contacts SET phone_e164 = phone_number WHERE phone_e164 IS NULL AND phone_number IS NOT NULL")
    op.execute("UPDATE contacts SET company_name = company WHERE company_name IS NULL AND company IS NOT NULL")

    # Add Check constraint to lead_score
    op.create_check_constraint('ck_lead_score_range', 'contacts', sa.text('lead_score >= 0 AND lead_score <= 100'))

    # 2. Companies Table
    op.create_table(
        'companies',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('annual_revenue', sa.Numeric(), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_companies_tenant', 'companies', ['tenant_id'], unique=False)

    # 3. Pipeline Stages Table
    op.create_table(
        'pipeline_stages',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('probability_pct', sa.Integer(), nullable=False),
        sa.Column('is_terminal', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'position', name='uq_stage_position_tenant')
    )
    op.create_check_constraint('ck_probability_range', 'pipeline_stages', sa.text('probability_pct >= 0 AND probability_pct <= 100'))
    op.create_index('idx_stages_tenant', 'pipeline_stages', ['tenant_id'], unique=False)

    # 4. Deals Table
    op.create_table(
        'deals',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('contact_id', sa.UUID(), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('stage_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('value_usd', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='USD', nullable=False),
        sa.Column('close_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('owner_id', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('ai_next_action', sa.Text(), nullable=True),
        sa.Column('ai_sentiment', sa.String(length=20), server_default='unknown', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['stage_id'], ['pipeline_stages.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_check_constraint('ck_ai_sentiment_values', 'deals', sa.text("ai_sentiment IN ('positive', 'neutral', 'negative', 'unknown')"))
    op.create_index('idx_deals_tenant', 'deals', ['tenant_id'], unique=False)
    op.create_index('idx_deals_contact', 'deals', ['contact_id'], unique=False)
    op.create_index('idx_deals_company', 'deals', ['company_id'], unique=False)
    op.create_index('idx_deals_stage', 'deals', ['stage_id'], unique=False)

    # 5. Activities Table
    op.create_table(
        'activities',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('deal_id', sa.UUID(), nullable=True),
        sa.Column('contact_id', sa.UUID(), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('outcome', sa.String(length=255), nullable=True),
        sa.Column('transcript_url', sa.String(length=1024), nullable=True),
        sa.Column('recording_url', sa.String(length=1024), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('created_by_ai', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_check_constraint('ck_activity_type_values', 'activities', sa.text("type IN ('call', 'email', 'sms', 'note', 'task')"))
    op.create_index('idx_activities_tenant', 'activities', ['tenant_id'], unique=False)
    op.create_index('idx_activities_contact', 'activities', ['contact_id'], unique=False)
    op.create_index('idx_activities_deal', 'activities', ['deal_id'], unique=False)

    # 6. Deal Stage History Table
    op.create_table(
        'deal_stage_history',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('deal_id', sa.UUID(), nullable=False),
        sa.Column('from_stage_id', sa.UUID(), nullable=True),
        sa.Column('to_stage_id', sa.UUID(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('changed_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_stage_id'], ['pipeline_stages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['to_stage_id'], ['pipeline_stages.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_history_tenant', 'deal_stage_history', ['tenant_id'], unique=False)
    op.create_index('idx_history_deal', 'deal_stage_history', ['deal_id'], unique=False)

    # Note: RLS Policies are enabled at the database layer via direct SQL.


def downgrade() -> None:
    # Drop Tables
    op.drop_table('deal_stage_history')
    op.drop_table('activities')
    op.drop_table('deals')
    op.drop_table('pipeline_stages')
    op.drop_table('companies')

    # Revert Contacts alterations
    op.drop_constraint('ck_lead_score_range', 'contacts', type_='check')
    op.drop_column('contacts', 'created_by')
    op.drop_column('contacts', 'updated_at')
    op.drop_column('contacts', 'custom_fields')
    op.drop_column('contacts', 'tags')
    op.drop_column('contacts', 'lead_score')
    op.drop_column('contacts', 'lead_source')
    op.drop_column('contacts', 'linkedin_url')
    op.drop_column('contacts', 'company_name')
    op.drop_column('contacts', 'full_name')
    op.drop_column('contacts', 'email')
    op.drop_column('contacts', 'phone_e164')
